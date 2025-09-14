import os, sys, math, shutil, subprocess, json
import numpy as np
from fastapi import FastAPI, UploadFile, File
from pdf2image import convert_from_bytes
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from pdf2image import convert_from_path
from PIL import Image
import cv2
from tempfile import NamedTemporaryFile

app = FastAPI()

OUTPUT_DIR = Path("processed")
OUTPUT_DIR.mkdir(exist_ok=True)

# ───────────────────────────
# Utility functions (copied from your servcie_1.py)
# ───────────────────────────

def pil_to_cv2(pil_img):
    arr = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def cv2_to_pil(cv_img):
    rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)

def rotate_image(img, angle):
    (h, w) = img.shape[:2]
    center = (w / 2.0, h / 2.0)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def estimate_skew_angle(gray):
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180.0, threshold=80,
                            minLineLength=min(gray.shape)//4, maxLineGap=20)
    if lines is None:
        return 0.0
    angles = []
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        dx, dy = x2 - x1, y2 - y1
        angle = 90.0 if dx == 0 else math.degrees(math.atan2(dy, dx))
        if abs(angle) < 45:  # keep near-horizontal
            angles.append(angle)
    return float(np.median(angles)) if angles else 0.0

def upscale_if_small_text(bgr, target_char_px=28, max_scale=4.0):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((3,3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in contours if 5 < cv2.boundingRect(c)[2] < bgr.shape[1]*0.8]
    if not heights: return bgr
    median_h = float(np.median(heights))
    if median_h >= target_char_px: return bgr
    scale = min(max_scale, max(1.0, target_char_px / (median_h+1e-6)))
    return cv2.resize(bgr, (int(bgr.shape[1]*scale), int(bgr.shape[0]*scale)), interpolation=cv2.INTER_CUBIC)

def denoise_image(bgr):
    return cv2.fastNlMeansDenoisingColored(bgr, None, 10, 10, 7, 21)

def adaptive_binarize(gray):
    blurred = cv2.medianBlur(gray, 3)
    block_size = 31 if max(gray.shape) >= 1000 else 21
    if block_size % 2 == 0: block_size += 1
    bin_img = cv2.adaptiveThreshold(blurred, 255,
                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, block_size, 10)
    if np.mean(bin_img) < 127:
        bin_img = cv2.bitwise_not(bin_img)
    return bin_img

def post_cleanup(binary):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    return cv2.morphologyEx(cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1),
                            cv2.MORPH_CLOSE, kernel, iterations=1)

def process_page_image(pil_page):
    bgr = pil_to_cv2(pil_page)
    bgr = upscale_if_small_text(bgr, 28)
    denoised = denoise_image(bgr)
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    angle = estimate_skew_angle(gray)
    if abs(angle) > 0.2:
        denoised = rotate_image(denoised, angle)
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    bin_img = adaptive_binarize(gray)
    bin_img = post_cleanup(bin_img)
    return cv2.cvtColor(bin_img, cv2.COLOR_GRAY2BGR), angle

def process_pdf_file(pdf_path, out_root, dpi=400, poppler_path=None):
    pdf_name = Path(pdf_path).stem
    out_dir = Path(out_root) / pdf_name
    out_dir.mkdir(parents=True, exist_ok=True)
    if poppler_path:
        pages = convert_from_path(str(pdf_path), dpi=dpi, poppler_path=poppler_path)
    else:
        pages = convert_from_path(str(pdf_path), dpi=dpi)
    results = []
    for i, page in enumerate(pages, 1):
        processed_bgr, angle = process_page_image(page)
        out_path = out_dir / f"page_{i:03d}.png"
        cv2.imwrite(str(out_path), processed_bgr)
        results.append((str(out_path), angle))
    return results

def process_all_pdfs(upload_dir, processed_dir, dpi=400, poppler_path=None):
    pdf_files = sorted(Path(upload_dir).glob("*.pdf"))
    summary = {}
    for pdf in pdf_files:
        try:
            results = process_pdf_file(pdf, processed_dir, dpi, poppler_path)
            summary[pdf.name] = {
                "pages": len(results),
                "angles": [float(a) for (_,a) in results],
                "status": "success"
            }
        except Exception as e:
            summary[pdf.name] = {"status": "failed", "error": str(e)}
    return summary

def find_poppler_path():
    if shutil.which("pdfinfo"): return None
    candidates = [
        r"C:\poppler\poppler-25.07.0\Library\bin",
        r"C:\poppler\poppler-0.68.0\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\Program Files (x86)\poppler\bin"
    ]
    for p in candidates:
        if os.path.isfile(os.path.join(p, "pdfinfo.exe")): return p
    return None

def check_pdfinfo(poppler_path=None):
    exe = "pdfinfo" if poppler_path is None else os.path.join(poppler_path, "pdfinfo")
    try:
        proc = subprocess.run([exe, "-v"], capture_output=True, text=True, timeout=10)
        return proc.returncode == 0, proc.stdout.strip() or proc.stderr.strip()
    except Exception as e:
        return False, str(e)
    
def segment_page_paragraphs(pil_img, base_name: str, page_num: int):
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Step 1: Dilate horizontally to connect words in a line
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    dilated_h = cv2.dilate(thresh, kernel_h, iterations=1)

    # Step 2: Dilate vertically to connect lines into paragraphs
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 30))
    dilated = cv2.dilate(dilated_h, kernel_v, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blocks, out_files = [], []

    heights = [cv2.boundingRect(c)[3] for c in contours if cv2.boundingRect(c)[3] > 20]
    median_h = np.median(heights) if heights else 30

    for i, c in enumerate(sorted(contours, key=lambda c: cv2.boundingRect(c)[1])):
        x, y, w, h = cv2.boundingRect(c)
        if w < 50 or h < 30:
            continue

        crop = pil_img.crop((x, y, x + w, y + h))
        out_path = OUTPUT_DIR / f"{base_name}_page{page_num}_block{i}.png"
        crop.save(out_path, format="PNG")

        block_type = "title" if h > 2 * median_h else "paragraph"

        blocks.append({
            "id": i,
            "type": block_type,
            "bbox": [int(x), int(y), int(w), int(h)],
            "image": str(out_path)
        })
        out_files.append(str(out_path))

    return blocks, out_files



# ───────────────────────────
# FastAPI Endpoint
# ───────────────────────────

@app.post("/preprocess/")
async def preprocess(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    images = convert_from_bytes(pdf_bytes)

    all_blocks, all_files = [], []
    base_name = Path(file.filename).stem

    for i, img in enumerate(images, start=1):
        blocks, out_files = segment_page_paragraphs(img, base_name, i)
        all_blocks.append({"page": i, "blocks": blocks})
        all_files.extend(out_files)

    metadata = {
        "filename": file.filename,
        "pages": len(images),
        "segments": all_blocks,
        "saved_files": all_files
    }

    meta_path = OUTPUT_DIR / f"{base_name}_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata