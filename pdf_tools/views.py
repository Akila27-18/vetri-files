import os
import io
import json
import uuid
import subprocess

from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\Library\bin"


# ===============================
# CONFIG
# ===============================
GS_PATH = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"


# ===============================
# HOME
# ===============================
def home(request):
    tools = [
        {
            "name": "Merge PDF",
            "desc": "Combine PDFs in the order you want",
            "icon": "https://cdn.lordicon.com/ivhjpjsw.json",
            "url": "/merge/"
        },
        {
            "name": "Split PDF",
            "desc": "Separate one PDF into multiple files",
            "icon": "https://cdn.lordicon.com/fhtaantg.json",
            "url": "/split/"
        },
        {
            "name": "Compress PDF",
            "desc": "Reduce file size while optimizing quality",
            "icon": "https://cdn.lordicon.com/aklfruoc.json",
            "url": "/compress/"
        },
        {
            "name": "PDF to Word",
            "desc": "Convert PDF to editable Word",
            "icon": "https://cdn.lordicon.com/wzwygmng.json",
            "url": "/pdf-to-word/"
        },
        {
            "name": "Word to PDF",
            "desc": "Convert Word to PDF",
            "icon": "https://cdn.lordicon.com/qhgmphtg.json",
            "url": "/word-to-pdf/"
        },
        {
            "name": "PDF to Image",
            "desc": "Convert PDF pages to images",
            "icon": "https://cdn.lordicon.com/rwotyanb.json",
            "url": "/pdf-to-image/"
        },
        {
            "name": "Image to PDF",
            "desc": "Convert images to PDF",
            "icon": "https://cdn.lordicon.com/iltqorsz.json",
            "url": "/image-to-pdf/"
        },
        {
            "name": "Rotate PDF",
            "desc": "Rotate PDF pages",
            "icon": "https://cdn.lordicon.com/puvaffet.json",
            "url": "/rotate/"
        },
        {
            "name": "Unlock PDF",
            "desc": "Remove PDF password",
            "icon": "https://cdn.lordicon.com/tdrtiskw.json",
            "url": "/unlock/"
        },
        {
            "name": "Protect PDF",
            "desc": "Add password to PDF",
            "icon": "https://cdn.lordicon.com/lxotnbfa.json",
            "url": "/protect/"
        },
        {
            "name": "Watermark",
            "desc": "Add watermark to PDF",
            "icon": "https://cdn.lordicon.com/ygvjgdmk.json",
            "url": "/watermark/"
        },
        {
            "name": "OCR PDF",
            "desc": "Convert scanned PDF to text",
            "icon": "https://cdn.lordicon.com/kkvxgpti.json",
            "url": "/ocr/"
        },
        {
            "name": "PDF → Excel",
            "desc": "Extract tables from PDF into Excel spreadsheets",
            "icon": "https://cdn.lordicon.com/puvaffet.json",
            "url": "/pdf-to-excel/"
        },

        {
            "name": "Excel → PDF",
            "desc": "Convert Excel spreadsheets to PDF format",
            "icon": "https://cdn.lordicon.com/jjoolpwc.json",
            "url": "/excel-to-pdf/"
        },

        {
                "name": "PowerPoint → PDF",
            "desc": "Convert PowerPoint presentations to PDF",
            "icon": "https://cdn.lordicon.com/iawrhwdo.json",
            "url": "/ppt-to-pdf/"
        },
        {
            "name": "PDF → PowerPoint",
            "desc": "Convert PDF pages into PowerPoint slides",
            "icon": "https://cdn.lordicon.com/nocovwne.json",
            "url": "/pdf-to-ppt/"
        },
 
    ]
    return render(request, "home.html", {"tools": tools})



# ===============================
# MERGE PDF
# ===============================
def merge_pdf(request):
    if request.method == "POST":
        pdf_files = request.FILES.getlist("pdfs")

        if not pdf_files:
            return HttpResponse("No files uploaded", status=400)

        merger = PdfMerger()
        temp_files = []

        for pdf in pdf_files:
            tmp_path = default_storage.save(
                f"tmp/{uuid.uuid4()}.pdf",
                ContentFile(pdf.read())
            )
            temp_files.append(tmp_path)
            merger.append(default_storage.path(tmp_path))

        base_name = os.path.splitext(pdf_files[0].name)[0]
        output_path = default_storage.path(
            f"tmp/{base_name}_merged.pdf"
        )

        merger.write(output_path)
        merger.close()

        for f in temp_files:
            default_storage.delete(f)

        with open(output_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="{base_name}_merged.pdf"'
            )

        os.remove(output_path)
        return response

    return render(request, "merge.html")


# ===============================
# SPLIT PDF
# ===============================
def split_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")
        ranges_json = request.POST.get("ranges")

        if not pdf_file or not ranges_json:
            return HttpResponse("Invalid request", status=400)

        try:
            ranges = json.loads(ranges_json)
        except json.JSONDecodeError:
            return HttpResponse("Invalid range format", status=400)

        reader = PdfReader(pdf_file)
        writer = PdfWriter()
        total_pages = len(reader.pages)

        for r in ranges:
            start = max(1, int(r["from"]))
            end = min(total_pages, int(r["to"]))

            if start > end:
                continue

            for i in range(start - 1, end):
                writer.add_page(reader.pages[i])

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        ranges_text = "_".join(
            f"{r['from']}-{r['to']}" for r in ranges
        )
        filename = (
            os.path.splitext(pdf_file.name)[0]
            + f"_split_{ranges_text}.pdf"
        )

        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )
        return response

    return render(request, "split.html")


# ===============================
# COMPRESS PDF (GHOSTSCRIPT)
# ===============================
def compress_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")
        level = request.POST.get("level", "recommended")

        if not pdf_file:
            return HttpResponse("No file uploaded", status=400)

        compression_map = {
            "extreme": "/screen",
            "recommended": "/ebook",
            "less": "/printer",
        }
        gs_level = compression_map.get(level, "/ebook")

        input_path = default_storage.save(
            f"tmp/{uuid.uuid4()}_input.pdf",
            ContentFile(pdf_file.read())
        )

        base_name = os.path.splitext(pdf_file.name)[0]
        output_path = default_storage.path(
            f"tmp/{base_name}_compressed.pdf"
        )

        subprocess.run(
            [
                GS_PATH,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS={gs_level}",
                "-dNOPAUSE",
                "-dBATCH",
                "-dSAFER",
                f"-sOutputFile={output_path}",
                default_storage.path(input_path),
            ],
            check=True,
        )

        with open(output_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="{base_name}_compressed.pdf"'
            )

        default_storage.delete(input_path)
        os.remove(output_path)
        return response

    return render(request, "compress.html")

from PyPDF2 import PdfReader, PdfWriter
from django.http import HttpResponse
from django.shortcuts import render
import io
import os

def rotate_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")
        rotation = int(request.POST.get("rotation", 90))

        if not pdf_file:
            return HttpResponse("No PDF uploaded", status=400)

        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        for page in reader.pages:
            page.rotate(rotation)
            writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        base_name = os.path.splitext(pdf_file.name)[0]
        filename = f"{base_name}_rotated.pdf"

        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return render(request, "rotate.html")

from django.shortcuts import render
from django.http import HttpResponse
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import gray
import io
import os

def watermark_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")
        text = request.POST.get("text", "VetriFiles")
        opacity = float(request.POST.get("opacity", 0.2))
        position = request.POST.get("position", "center")

        if not pdf_file:
            return HttpResponse("No PDF uploaded", status=400)

        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        for page in reader.pages:
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=A4)

            width, height = A4
            c.setFillColor(gray, alpha=opacity)
            c.setFont("Helvetica-Bold", 40)

            if position == "center":
                c.drawCentredString(width/2, height/2, text)
            elif position == "top":
                c.drawCentredString(width/2, height - 100, text)
            else:
                c.drawCentredString(width/2, 100, text)

            c.save()
            packet.seek(0)

            watermark = PdfReader(packet).pages[0]
            page.merge_page(watermark)
            writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        base = os.path.splitext(pdf_file.name)[0]
        filename = f"{base}_watermarked.pdf"

        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return render(request, "watermark.html")

import io
import os
import zipfile
import fitz  # PyMuPDF
from django.http import HttpResponse
from django.shortcuts import render

def pdf_to_image(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")
        img_format = request.POST.get("format", "png")

        if not pdf_file:
            return HttpResponse("No PDF uploaded", status=400)

        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        zip_buffer = io.BytesIO()
        zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)

        base_name = os.path.splitext(pdf_file.name)[0]

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # high quality

            img_bytes = pix.tobytes(img_format)
            img_name = f"{base_name}_page_{page_num+1}.{img_format}"
            zip_file.writestr(img_name, img_bytes)

        zip_file.close()
        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer.read(), content_type="application/zip")
        response["Content-Disposition"] = (
            f'attachment; filename="{base_name}_images.zip"'
        )
        return response

    return render(request, "pdf_to_image.html")
import io
import os
from PIL import Image
from django.http import HttpResponse
from django.shortcuts import render

def image_to_pdf(request):
    if request.method == "POST":
        images = request.FILES.getlist("images")

        if not images:
            return HttpResponse("No images uploaded", status=400)

        pil_images = []
        for img in images:
            im = Image.open(img).convert("RGB")
            pil_images.append(im)

        buffer = io.BytesIO()
        pil_images[0].save(
            buffer,
            format="PDF",
            save_all=True,
            append_images=pil_images[1:]
        )
        buffer.seek(0)

        base = os.path.splitext(images[0].name)[0]
        filename = f"{base}_images.pdf"

        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return render(request, "image_to_pdf.html")

import io
import os
from PyPDF2 import PdfReader, PdfWriter
from django.http import HttpResponse
from django.shortcuts import render

def protect_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")
        password = request.POST.get("password")

        if not pdf_file or not password:
            return HttpResponse("Missing file or password", status=400)

        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        filename = os.path.splitext(pdf_file.name)[0] + "_protected.pdf"

        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return render(request, "protect.html")
import io
import os
from PyPDF2 import PdfReader, PdfWriter
from django.http import HttpResponse
from django.shortcuts import render

def unlock_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")
        password = request.POST.get("password")

        if not pdf_file or not password:
            return HttpResponse("Missing file or password", status=400)

        reader = PdfReader(pdf_file)

        if reader.is_encrypted:
            if not reader.decrypt(password):
                return HttpResponse("Wrong password", status=403)

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        filename = os.path.splitext(pdf_file.name)[0] + "_unlocked.pdf"

        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return render(request, "unlock.html")
import io
import os
from django.http import HttpResponse
from django.shortcuts import render
from pdf2image import convert_from_bytes
import pytesseract
from PyPDF2 import PdfWriter, PdfReader

def ocr_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")

        if not pdf_file:
            return HttpResponse("No file uploaded", status=400)

        images = convert_from_bytes(
            pdf_file.read(),
            poppler_path=POPPLER_PATH
        )

        writer = PdfWriter()

        for img in images:
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                img, extension="pdf"
            )
            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer.add_page(reader.pages[0])

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        base = os.path.splitext(pdf_file.name)[0]
        filename = f"{base}_ocr.pdf"

        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return render(request, "ocr.html")
    import os
import tempfile
from django.shortcuts import render
from django.http import HttpResponse
from docx2pdf import convert
from pdf2docx import Converter

# WORD → PDF
def word_to_pdf(request):
    if request.method == "POST":
        docx_file = request.FILES.get("file")
        if not docx_file:
            return HttpResponse("No file uploaded", status=400)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, docx_file.name)
            output_path = os.path.join(tmp, os.path.splitext(docx_file.name)[0]+".pdf")
            with open(input_path, "wb") as f:
                f.write(docx_file.read())

            convert(input_path, output_path)

            with open(output_path, "rb") as f:
                response = HttpResponse(f.read(), content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="{os.path.basename(output_path)}"'
                return response
    return render(request, "word_to_pdf.html")

# PDF → WORD
def pdf_to_word(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return HttpResponse("No file uploaded", status=400)

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = os.path.join(tmp, pdf_file.name)
            docx_path = os.path.join(tmp, os.path.splitext(pdf_file.name)[0]+".docx")
            with open(pdf_path, "wb") as f:
                f.write(pdf_file.read())

            cv = Converter(pdf_path)
            cv.convert(docx_path)
            cv.close()

            with open(docx_path, "rb") as f:
                response = HttpResponse(f.read(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                response["Content-Disposition"] = f'attachment; filename="{os.path.basename(docx_path)}"'
                return response
    return render(request, "pdf_to_word.html")

import os
import tempfile
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
import tabula  # pip install tabula-py

def pdf_to_excel(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return HttpResponse("No file uploaded", status=400)

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = os.path.join(tmp, pdf_file.name)
            excel_path = os.path.join(tmp, os.path.splitext(pdf_file.name)[0] + ".xlsx")
            with open(pdf_path, "wb") as f:
                f.write(pdf_file.read())

            # Extract tables into a list of DataFrames
            tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True)

            # Write to Excel
            with pd.ExcelWriter(excel_path) as writer:
                for idx, table in enumerate(tables):
                    table.to_excel(writer, sheet_name=f"Sheet{idx+1}", index=False)

            with open(excel_path, "rb") as f:
                response = HttpResponse(
                    f.read(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                response["Content-Disposition"] = f'attachment; filename="{os.path.basename(excel_path)}"'
                return response

    return render(request, "pdf_to_excel.html")

import pandas as pd
import pdfkit

def excel_to_pdf(request):
    if request.method == "POST":
        excel_file = request.FILES.get("file")
        if not excel_file:
            return HttpResponse("No file uploaded", status=400)

        with tempfile.TemporaryDirectory() as tmp:
            excel_path = os.path.join(tmp, excel_file.name)
            pdf_path = os.path.join(tmp, os.path.splitext(excel_file.name)[0] + ".pdf")
            with open(excel_path, "wb") as f:
                f.write(excel_file.read())

            # Convert Excel sheet(s) to HTML
            xl = pd.ExcelFile(excel_path)
            htmls = [xl.parse(sheet).to_html(index=False) for sheet in xl.sheet_names]
            full_html = "<br><hr><br>".join(htmls)

            pdfkit.from_string(full_html, pdf_path)

            with open(pdf_path, "rb") as f:
                response = HttpResponse(f.read(), content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                return response
    return render(request, "excel_to_pdf.html")
import subprocess

def ppt_to_pdf(request):
    if request.method == "POST":
        ppt_file = request.FILES.get("file")
        if not ppt_file:
            return HttpResponse("No file uploaded", status=400)

        with tempfile.TemporaryDirectory() as tmp:
            ppt_path = os.path.join(tmp, ppt_file.name)
            pdf_path = os.path.join(tmp, os.path.splitext(ppt_file.name)[0] + ".pdf")
            with open(ppt_path, "wb") as f:
                f.write(ppt_file.read())

            # Using LibreOffice CLI (cross-platform)
            subprocess.run([
                "libreoffice", "--headless", "--convert-to", "pdf", ppt_path, "--outdir", tmp
            ])

            with open(pdf_path, "rb") as f:
                response = HttpResponse(f.read(), content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                return response
    return render(request, "ppt_to_pdf.html")


from pdf2image import convert_from_bytes
from pptx import Presentation
from pptx.util import Inches
import io

def pdf_to_ppt(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return HttpResponse("No file uploaded", status=400)

        prs = Presentation()
        images = convert_from_bytes(pdf_file.read(), dpi=150)
        for img in images:
            slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank slide
            with io.BytesIO() as img_bytes:
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                slide.shapes.add_picture(img_bytes, 0, 0, width=prs.slide_width, height=prs.slide_height)

        with io.BytesIO() as buffer:
            prs.save(buffer)
            buffer.seek(0)
            response = HttpResponse(
                buffer.read(),
                content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
            response["Content-Disposition"] = f'attachment; filename="{os.path.splitext(pdf_file.name)[0]}.pptx"'
            return response

    return render(request, "pdf_to_ppt.html")
