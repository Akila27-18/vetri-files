from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('merge/', views.merge_pdf, name='merge_pdf'),
    path('split/', views.split_pdf, name='split_pdf'),
    path('compress/', views.compress_pdf, name='compress_pdf'),
    path("rotate/", views.rotate_pdf, name="rotate_pdf"),
    path("watermark/", views.watermark_pdf, name="watermark_pdf"),
    path("pdf-to-image/", views.pdf_to_image, name="pdf_to_image"),
    path("image-to-pdf/", views.image_to_pdf, name="image_to_pdf"),
    path("protect/", views.protect_pdf, name="protect_pdf"),
    path("unlock/", views.unlock_pdf, name="unlock_pdf"),
    path("ocr/", views.ocr_pdf, name="ocr_pdf"),
    path("pdf-to-word/", views.pdf_to_word, name="pdf_to_word"),
    path("word-to-pdf/", views.word_to_pdf, name="word_to_pdf"),
    path("pdf-to-excel/", views.pdf_to_excel, name="pdf_to_excel"),
    path("excel-to-pdf/", views.excel_to_pdf, name="excel_to_pdf"),
    path("pdf-to-ppt/", views.pdf_to_ppt, name="pdf_to_ppt"),
    path("ppt-to-pdf/", views.ppt_to_pdf, name="ppt_to_pdf"),

]
