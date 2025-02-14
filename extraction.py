import os
import tempfile
import streamlit as st
from groq import Groq
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import json


def extract_text_from_file(uploaded_file):
    text = ""
    
    if uploaded_file.type == "application/pdf":
        try:
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
            if text.strip(): 
                return text
        except Exception as e:
            st.warning(f"PDF text extraction failed, falling back to OCR: {str(e)}")
        uploaded_file.seek(0)
        
        try:
            pdf_images = convert_from_bytes(uploaded_file.read())
            for image in pdf_images:
                text += pytesseract.image_to_string(image)
        except Exception as e:
            st.error(f"Error processing PDF images: {str(e)}")
    else:
        try:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)
        except Exception as e:
            st.error(f"Error processing image file: {str(e)}")
    
    return text

def extract_text_and_positions_from_pdf(pdf_file):
    """Extract text and their positions from PDF"""
    text_positions = []
    try:
        pdf_reader = PdfReader(pdf_file)
        for page_num, page in enumerate(pdf_reader.pages):
            text_extract = page.extract_text()
            text_positions.append({
                'page': page_num,
                'text': text_extract,
                'position': (50, 50)
            })
    except Exception as e:
        st.error(f"Error extracting text positions from PDF: {str(e)}")
    return text_positions