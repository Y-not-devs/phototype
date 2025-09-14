from io import BytesIO
import re
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, status # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from pydantic import BaseModel, Field # type: ignore
from langdetect import detect_langs, DetectorFactory # type: ignore
from PyPDF2 import PdfReader # type: ignore
from fastapi.middleware.cors import CORSMiddleware
# deterministic results
DetectorFactory.seed = 0

app = FastAPI(title="LangDetect Microservice", version="1.1.0")

# ---------- models ----------
class LanguageScore(BaseModel):
    lang: str = Field(..., description="ISO 639-1 code (best effort)")
    prob: float = Field(..., ge=0.0, le=1.0)

class ChunkLanguage(BaseModel):
    chunk_index: int
    start_char: int
    end_char: int
    text_preview: str = Field(..., description="first ~120 chars of the chunk")
    languages: List[LanguageScore]

class DetectionResponse(BaseModel):
    document_languages: List[LanguageScore]
    top_language: Optional[str] = None
    per_chunk: Optional[List[ChunkLanguage]] = None
    meta: Dict[str, Any] = {}

# ---------- helpers ----------
_WS = re.compile(r"\s+")
_SOFT_WRAP = re.compile(r"(?<![.!?…:;])\n(?!\n)")  # linebreak not following sentence end, not a blank line
_BLANKS = re.compile(r"\n{2,}")                     # paragraph separators
_SPACE_FIX = re.compile(r"[ \t]+")

def _clean(s: str) -> str:
    return _SPACE_FIX.sub(" ", s or "").strip()

def _normalize(scores) -> List[LanguageScore]:
    pairs = [(str(s.lang), float(s.prob)) for s in scores]
    total = sum(p for _, p in pairs) or 1.0
    out = [LanguageScore(lang=lang, prob=p/total) for lang, p in pairs]
    out.sort(key=lambda x: x.prob, reverse=True)
    return out

def _detect_text(text: str, min_chars: int) -> List[LanguageScore]:
    t = _clean(text)
    if len(t) < min_chars:
        return []
    try:
        return _normalize(detect_langs(t))
    except Exception:
        return []

def _extract_all_text(pdf_bytes: bytes, char_limit: int) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    texts = []
    for i in range(len(reader.pages)):
        try:
            texts.append(reader.pages[i].extract_text() or "")
        except Exception:
            continue
    full = "\n".join(texts)
    return full[:char_limit]

def _reflow_paragraphs(raw: str) -> List[str]:
    """
    Turn PDF 'ragged' lines into paragraphs:
    - merge single newlines that look like soft wraps
    - keep blank lines as paragraph separators
    """
    if not raw:
        return []
    # Merge soft wraps into spaces
    merged = _SOFT_WRAP.sub(" ", raw)
    # Normalize Windows/Mac line endings
    merged = merged.replace("\r\n", "\n").replace("\r", "\n")
    # Split by blank lines into paragraphs
    paras = [p.strip() for p in _BLANKS.split(merged)]
    # Drop empty and overly tiny noise chunks
    return [p for p in paras if _clean(p)]

def _build_chunk_objects(paras: List[str], min_chars: int) -> List[ChunkLanguage]:
    out: List[ChunkLanguage] = []
    cursor = 0
    for i, p in enumerate(paras):
        # find start/end offsets in a reconstructed doc string
        start = cursor
        end = start + len(p)
        cursor = end + 2  # account for the blank line separator we conceptually inserted
        langs = _detect_text(p, min_chars=min_chars)
        out.append(
            ChunkLanguage(
                chunk_index=i,
                start_char=start,
                end_char=end,
                text_preview=(p[:120] + ("…" if len(p) > 120 else "")),
                languages=langs,
            )
        )
    return out

def _doc_lang_from_chunks(chunks: List[ChunkLanguage]) -> List[LanguageScore]:
    # simple voting by averaging probs over non-empty chunks
    agg: Dict[str, float] = {}
    for ch in chunks:
        if not ch.languages:
            continue
        for s in ch.languages:
            agg[s.lang] = agg.get(s.lang, 0.0) + s.prob
    if not agg:
        return []
    # normalize to 1
    total = sum(agg.values())
    scores = [LanguageScore(lang=k, prob=v / total) for k, v in agg.items()]
    return sorted(scores, key=lambda s: s.prob, reverse=True)

# ---------- endpoints ----------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/detect-language", response_model=DetectionResponse,  responses={
        415: {
            "description": "Unsupported Media Type",
            "content": {"application/json": {"example": {"detail": "Only PDF is supported."}}},
        },
        422: {
            "description": "Unprocessable Entity (no extractable text)",
            "content": {"application/json": {"example": {"detail": "No extractable text layer in PDF. Use OCR and call /detect-text."}}},
        },
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "document_languages": [{"lang": "en", "prob": 0.84}, {"lang": "ru", "prob": 0.10}, {"lang": "kk", "prob": 0.06}],
                        "top_language": "en",
                        "per_chunk": [
                            {
                                "chunk_index": 0,
                                "start_char": 0,
                                "end_char": 142,
                                "text_preview": "This is the first paragraph…",
                                "languages": [{"lang": "en", "prob": 0.99}]
                            },
                            {
                                "chunk_index": 1,
                                "start_char": 144,
                                "end_char": 268,
                                "text_preview": "Бұл екінші абзац қазақ тілінде…",
                                "languages": [{"lang": "kk", "prob": 0.97}]
                            }
                        ],
                        "meta": {
                            "file_name": "sample.pdf",
                            "paragraphs_detected": 12,
                            "chunk_min_chars": 40,
                            "doc_char_limit": 300000,
                            "has_text_layer": True,
                            "note": "Image-only PDFs yield empty text; run OCR and use /detect-text."
                        }
                    }
                }
            },
        },
    },
)
async def detect_language_pdf(
    file: UploadFile = File(...),
    chunk_min_chars: int = 40,     # ignore micro-chunks like figure captions
    doc_char_limit: int = 300_000, # cap total text processed
    include_chunks: bool = True,   # return per-chunk section
):
    """
    Upload a PDF, get document-level and per-paragraph language predictions.
    Paragraphs are derived by reflowing soft-wrapped lines and splitting on blank lines.
    """
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Only PDF is supported.")
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty file.")

    raw = _extract_all_text(payload, doc_char_limit)

    if not raw.strip():
        raise HTTPException(
        status_code=422,
        detail="No extractable text layer in PDF. Use OCR and call /detect-text."
    )

    # Heuristic reflow into paragraphs
    paragraphs = _reflow_paragraphs(raw)

    # Per-paragraph detection
    chunks = _build_chunk_objects(paragraphs, min_chars=chunk_min_chars) if include_chunks else None

    # Document-level by aggregating chunks (more robust than whole-text for PDFs)
    doc_langs = _doc_lang_from_chunks(chunks or [])
    top = doc_langs[0].lang if doc_langs else None

    resp = DetectionResponse(
        document_languages=doc_langs,
        top_language=top,
        per_chunk=chunks,
        meta={
            "file_name": file.filename,
            "paragraphs_detected": len(paragraphs),
            "chunk_min_chars": chunk_min_chars,
            "doc_char_limit": doc_char_limit,
            "note": "Image-only PDFs yield empty text; run OCR upstream and send text to /detect-text instead."
        },
    )
    return JSONResponse(content=resp.dict())

# Fallback endpoint in case OCR already produced plain text
class TextIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=1_000_000)

@app.post("/detect-text", response_model=DetectionResponse)
def detect_from_text(body: TextIn, chunk_min_chars: int = 40, include_chunks: bool = True):
    raw = body.text
    paragraphs = _reflow_paragraphs(raw)
    chunks = _build_chunk_objects(paragraphs, min_chars=chunk_min_chars) if include_chunks else None
    doc_langs = _doc_lang_from_chunks(chunks or [])
    top = doc_langs[0].lang if doc_langs else None
    return DetectionResponse(
        document_languages=doc_langs,
        top_language=top,
        per_chunk=chunks,
        meta={"paragraphs_detected": len(paragraphs), "chunk_min_chars": chunk_min_chars}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # можно указать конкретные ["http://localhost:3000"] и т.д.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
