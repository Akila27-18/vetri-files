import os
import io
import json
import uuid
import zipfile
import tempfile
import subprocess

from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from django.conf import settings

GS_PATH = settings.GS_PATH


# ===============================
# HOME
# ===============================
def home(request):
    tools = [
        {"name": "Merge PDF", "desc": "Combine PDFs", "icon": "https://cdn.lordicon.com/ivhjpjsw.json", "url": "/merge/"},
        {"name": "Split PDF", "desc": "Split PDF pages", "icon": "https://cdn.lordicon.com/fhtaantg.json", "url": "/split/"},
        {"name": "Compress PDF", "desc": "Reduce PDF size", "icon": "https://cdn.lordicon.com/aklfruoc.json", "url": "/compress/"},
        {"name": "Rotate PDF", "desc": "Rotate pages", "icon": "https://cdn.lordicon.com/puvaffet.json", "url": "/rotate/"},
        {"name": "Protect PDF", "desc": "Add password", "icon": "https://cdn.lordicon.com/lxotnbfa.json", "url": "/protect/"},
        {"name": "Unlock PDF", "desc": "Remove password", "icon": "https://cdn.lordicon.com/tdrtiskw.json", "url": "/unlock/"},
        {"name": "Watermark", "desc": "Add watermark", "icon": "https://cdn.lordicon.com/ygvjgdmk.json", "url": "/watermark/"},
        {"name": "OCR PDF", "desc": "Scanned PDF to text", "icon": "https://cdn.lordicon.com/kkvxgpti.json", "url": "/ocr/"},
        {"name": "PDF → Word", "desc": "Convert PDF to DOCX", "icon": "https://cdn.lordicon.com/wzwygmng.json", "url": "/pdf-to-word/"},
        {"name": "Word → PDF", "desc": "Convert DOCX to PDF", "icon": "https://cdn.lordicon.com/qhgmphtg.json", "url": "/word-to-pdf/"},
        {"name": "PDF → Image", "desc": "PDF pages to images", "icon": "https://cdn.lordicon.com/rwotyanb.json", "url": "/pdf-to-image/"},
        {"name": "Image → PDF", "desc": "Images to PDF", "icon": "https://cdn.lordicon.com/iltqorsz.json", "url": "/image-to-pdf/"},
        {"name": "PDF → Excel", "desc": "Extract tables", "icon": "https://cdn.lordicon.com/puvaffet.json", "url": "/pdf-to-excel/"},
        {"name": "Excel → PDF", "desc": "Spreadsheet to PDF", "icon": "https://cdn.lordicon.com/jjoolpwc.json", "url": "/excel-to-pdf/"},
        {"name": "PPT → PDF", "desc": "Slides to PDF", "icon": "https://cdn.lordicon.com/iawrhwdo.json", "url": "/ppt-to-pdf/"},
        {"name": "PDF → PPT", "desc": "PDF to slides", "icon": "https://cdn.lordicon.com/nocovwne.json", "url": "/pdf-to-ppt/"},
    ]
    return render(request, "home.html", {"tools": tools})


# ===============================
# MERGE PDF
# ===============================
def merge_pdf(request):
    if request.method == "POST":
        merger = PdfMerger()
        for f in request.FILES.getlist("pdfs"):
            merger.append(f)

        buffer = io.BytesIO()
        merger.write(buffer)
        buffer.seek(0)

        return HttpResponse(buffer.read(), content_type="application/pdf")
    return render(request, "merge.html")


# ===============================
# SPLIT PDF
# ===============================
def split_pdf(request):
    if request.method == "POST":
        pdf = request.FILES.get("pdf")
        ranges = json.loads(request.POST.get("ranges", "[]"))

        reader = PdfReader(pdf)
        writer = PdfWriter()

        for r in ranges:
            for i in range(r["from"] - 1, r["to"]):
                writer.add_page(reader.pages[i])

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        return HttpResponse(buffer.read(), content_type="application/pdf")

    return render(request, "split.html")


# ===============================
# COMPRESS PDF (Ghostscript)
# ===============================
def compress_pdf(request):
    if request.method == "POST":
        GS_PATH = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"
        pdf = request.FILES.get("pdf")

        with tempfile.TemporaryDirectory() as tmp:
            in_p = os.path.join(tmp, "in.pdf")
            out_p = os.path.join(tmp, "out.pdf")
            open(in_p, "wb").write(pdf.read())

            subprocess.run([
                GS_PATH, "-sDEVICE=pdfwrite",
                "-dPDFSETTINGS=/ebook",
                "-dNOPAUSE", "-dBATCH",
                f"-sOutputFile={out_p}", in_p
            ], check=True)

            return HttpResponse(open(out_p, "rb").read(), content_type="application/pdf")

    return render(request, "compress.html")


# ===============================
# ROTATE PDF
# ===============================
def rotate_pdf(request):
    if request.method == "POST":
        pdf = request.FILES.get("pdf")
        rotation = int(request.POST.get("rotation", 90))

        reader = PdfReader(pdf)
        writer = PdfWriter()

        for p in reader.pages:
            p.rotate(rotation)
            writer.add_page(p)

        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        return HttpResponse(buf.read(), content_type="application/pdf")

    return render(request, "rotate.html")


# ===============================
# WATERMARK
# ===============================
def watermark_pdf(request):
    if request.method == "POST":
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import gray

        pdf = request.FILES.get("pdf")
        text = request.POST.get("text", "VetriFiles")

        reader = PdfReader(pdf)
        writer = PdfWriter()

        for page in reader.pages:
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=A4)
            c.setFillColor(gray, alpha=0.2)
            c.setFont("Helvetica-Bold", 40)
            c.drawCentredString(300, 400, text)
            c.save()

            packet.seek(0)
            watermark = PdfReader(packet).pages[0]
            page.merge_page(watermark)
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        return HttpResponse(buf.read(), content_type="application/pdf")

    return render(request, "watermark.html")


# ===============================
# OCR PDF
# ===============================
def ocr_pdf(request):
    if request.method == "POST":
        from pdf2image import convert_from_bytes
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        POPPLER_PATH = r"C:\poppler\Library\bin"

        pdf = request.FILES.get("pdf")
        images = convert_from_bytes(pdf.read(), poppler_path=POPPLER_PATH)

        writer = PdfWriter()
        for img in images:
            b = pytesseract.image_to_pdf_or_hocr(img, extension="pdf")
            r = PdfReader(io.BytesIO(b))
            writer.add_page(r.pages[0])

        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        return HttpResponse(buf.read(), content_type="application/pdf")

    return render(request, "ocr.html")


# ===============================
# PDF → WORD
# ===============================
def pdf_to_word(request):
    if request.method == "POST":
        from pdf2docx import Converter

        pdf = request.FILES.get("file")
        with tempfile.TemporaryDirectory() as tmp:
            pdf_p = os.path.join(tmp, "in.pdf")
            docx_p = os.path.join(tmp, "out.docx")
            open(pdf_p, "wb").write(pdf.read())

            cv = Converter(pdf_p)
            cv.convert(docx_p)
            cv.close()

            return HttpResponse(
                open(docx_p, "rb").read(),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    return render(request, "pdf_to_word.html")


# ===============================
# WORD → PDF
# ===============================
def word_to_pdf(request):
    if request.method == "POST":
        from docx2pdf import convert

        doc = request.FILES.get("file")
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, doc.name)
            p = d.replace(".docx", ".pdf")
            open(d, "wb").write(doc.read())
            convert(d, p)
            return HttpResponse(open(p, "rb").read(), content_type="application/pdf")

    return render(request, "word_to_pdf.html")


# ===============================
# PDF → IMAGE
# ===============================
def pdf_to_image(request):
    if request.method == "POST":
        import fitz

        pdf = request.FILES.get("pdf")
        doc = fitz.open(stream=pdf.read(), filetype="pdf")

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            for i in range(len(doc)):
                pix = doc[i].get_pixmap()
                z.writestr(f"page_{i+1}.png", pix.tobytes("png"))

        zip_buf.seek(0)
        return HttpResponse(zip_buf.read(), content_type="application/zip")

    return render(request, "pdf_to_image.html")


# ===============================
# IMAGE → PDF
# ===============================
def image_to_pdf(request):
    from PIL import Image

    if request.method == "POST":
        imgs = [Image.open(f).convert("RGB") for f in request.FILES.getlist("images")]
        buf = io.BytesIO()
        imgs[0].save(buf, save_all=True, append_images=imgs[1:], format="PDF")
        buf.seek(0)
        return HttpResponse(buf.read(), content_type="application/pdf")

    return render(request, "image_to_pdf.html")


# ===============================
# PDF → EXCEL
# ===============================
def pdf_to_excel(request):
    if request.method == "POST":
        import pandas as pd
        import tabula

        pdf = request.FILES.get("file")
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "in.pdf")
            x = os.path.join(tmp, "out.xlsx")
            open(p, "wb").write(pdf.read())

            tables = tabula.read_pdf(p, pages="all", multiple_tables=True)
            with pd.ExcelWriter(x) as w:
                for i, t in enumerate(tables):
                    t.to_excel(w, sheet_name=f"Sheet{i+1}", index=False)

            return HttpResponse(open(x, "rb").read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    return render(request, "pdf_to_excel.html")


# ===============================
# EXCEL → PDF
# ===============================
def excel_to_pdf(request):
    if request.method == "POST":
        import pandas as pd
        import pdfkit

        excel = request.FILES.get("file")
        with tempfile.TemporaryDirectory() as tmp:
            e = os.path.join(tmp, excel.name)
            p = os.path.join(tmp, "out.pdf")
            open(e, "wb").write(excel.read())

            xl = pd.ExcelFile(e)
            html = "".join(xl.parse(s).to_html(index=False) for s in xl.sheet_names)
            pdfkit.from_string(html, p)

            return HttpResponse(open(p, "rb").read(), content_type="application/pdf")

    return render(request, "excel_to_pdf.html")


# ===============================
# PPT → PDF
# ===============================
def ppt_to_pdf(request):
    if request.method == "POST":
        ppt = request.FILES.get("file")
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, ppt.name)
            open(p, "wb").write(ppt.read())

            subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", p, "--outdir", tmp], check=True)
            return HttpResponse(open(p.replace(".pptx", ".pdf"), "rb").read(), content_type="application/pdf")

    return render(request, "ppt_to_pdf.html")


# ===============================
# PDF → PPT
# ===============================
def pdf_to_ppt(request):
    if request.method == "POST":
        from pdf2image import convert_from_bytes
        from pptx import Presentation

        pdf = request.FILES.get("file")
        prs = Presentation()
        imgs = convert_from_bytes(pdf.read(), dpi=150)

        for img in imgs:
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            slide.shapes.add_picture(buf, 0, 0, width=prs.slide_width, height=prs.slide_height)

        out = io.BytesIO()
        prs.save(out)
        out.seek(0)

        return HttpResponse(
            out.read(),
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

    return render(request, "pdf_to_ppt.html")

# ===============================   
# PROTECT PDF
# ===============================
def protect_pdf(request):
    if request.method == "POST":
        pdf = request.FILES.get("pdf")
        password = request.POST.get("password")

        reader = PdfReader(pdf)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        return HttpResponse(
            buffer.read(),
            content_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=protected.pdf"
            }
        )

    return render(request, "protect.html")
# ===============================
# UNLOCK PDF
# ===============================
def unlock_pdf(request):
    if request.method == "POST":
        pdf = request.FILES.get("pdf")
        password = request.POST.get("password")

        reader = PdfReader(pdf)

        if reader.is_encrypted:
            try:
                reader.decrypt(password)
            except:
                return HttpResponse("Invalid password", status=400)

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        return HttpResponse(
            buffer.read(),
            content_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=unlocked.pdf"
            }
        )

    return render(request, "unlock.html")
