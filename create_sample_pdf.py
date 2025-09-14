"""
Create a sample PDF file for testing PDF excerpt functionality
"""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create uploads directory if it doesn't exist
os.makedirs('frontend-service/uploads', exist_ok=True)

# Create a sample PDF file
pdf_path = 'frontend-service/uploads/8A16.pdf'

# Create PDF with sample contract data that matches the JSON structure
c = canvas.Canvas(pdf_path, pagesize=letter)
width, height = letter

# Title
c.setFont("Helvetica-Bold", 16)
c.drawString(50, height - 50, "CONTRACT DOCUMENT - 8A16")

# Contract content matching JSON fields (including Russian text from the actual JSON)
content = [
    "",
    "ДОГОВОР № 24022311 от « 2 » _04_2024",
    "",
    "ПРОДАВЕЦ:",
    "ОАО «БМЗ управляющая компания холдинга «БМК»",
    "г. Жлобин, Республика Беларусь",
    "Представитель: Чаус В.А., заместитель генерального директора",
    "Доверенность №8/355 от 12.12.2023",
    "",
    "ПОКУПАТЕЛЬ:",
    "ТОО «АзияМетизКомплект» (ТОО «Азия Метиз Комплект»)",
    "г. Астана, Республика Казахстан",
    "Директор: Кирдяев Иван Викторович",
    "Устав",
    "",
    "ПРЕДМЕТ ДОГОВОРА:",
    "Продажа товара согласно приложениям к Договору",
    "для вывоза в Республику Узбекистан",
    "Страна происхождения: Республика Беларусь",
    "",
    "ЦЕНА И СТОИМОСТЬ:",
    "Цена определяется конъюнктурой рынка и условиями поставки",
    "Валюта: российские рубли",
    "Общая стоимость: 100 000 000,00 рос. руб",
    "",
    "КАЧЕСТВО, УПАКОВКА И МАРКИРОВКА:",
    "должно соответствовать стандартам или техническим условиям",
    "упаковка согласно приложениям",
    "сертификатом, выданным Продавцом",
    "",
    "ДОКУМЕНТЫ ПОСТАВКИ:",
    "Срок: в течение 24 часов после отгрузки",
    "- счет-фактура",
    "- сертификат качества",
    "- сертификат происхождения",
    "- международная накладная формы CMR",
    "",
    "ПРИЕМКА ТОВАРА:",
    "по качеству - по сертификату качества",
    "по количеству - по весу и/или количеству единиц",
    "Положение о приемке товаров по количеству и качеству"
]

# Write content to PDF
y_position = height - 100
line_height = 20

c.setFont("Helvetica", 12)
for line in content:
    if line.strip():
        if line.isupper() and ":" not in line:
            c.setFont("Helvetica-Bold", 12)
        else:
            c.setFont("Helvetica", 12)
        c.drawString(50, y_position, line)
    y_position -= line_height
    
    # Start new page if needed
    if y_position < 50:
        c.showPage()
        y_position = height - 50

c.save()
print(f"Sample PDF created: {pdf_path}")