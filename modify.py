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


def modify_pdf(original_pdf, modifications):
    """Apply modifications to the PDF"""
    try:
        temp_pdf = BytesIO()
        c = canvas.Canvas(temp_pdf, pagesize=letter)
        for mod in modifications:
            if isinstance(mod['new_value'], list):
                text = ", ".join(mod['new_value'])
            else:
                text = str(mod['new_value'])
            y_position = letter[1] - mod['position'][1]
            c.drawString(mod['position'][0], y_position, text)
        
        c.save()
        temp_pdf.seek(0)
        output_pdf = PdfWriter()
        original_reader = PdfReader(original_pdf)
        temp_reader = PdfReader(temp_pdf)
        
        for i in range(len(original_reader.pages)):
            page = original_reader.pages[i]
            if i == 0:
                page.merge_page(temp_reader.pages[0])
            output_pdf.add_page(page)
        
        output_stream = BytesIO()
        output_pdf.write(output_stream)
        output_stream.seek(0)
        return output_stream
    except Exception as e:
        st.error(f"Error modifying PDF: {str(e)}")
        return None

def modify_image(original_image, modifications):
    """Apply modifications to the image"""
    try:
        img = Image.open(original_image)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        for mod in modifications:
            if isinstance(mod['new_value'], list):
                text = ", ".join(mod['new_value'])
            else:
                text = str(mod['new_value'])
            
            draw.text(mod['position'], text, fill='black', font=font)
        
        output_stream = BytesIO()
        img.save(output_stream, format=img.format if img.format else 'PNG')
        output_stream.seek(0)
        return output_stream
    except Exception as e:
        st.error(f"Error modifying image: {str(e)}")
        return None

def get_modifications_from_json_diff(original_json, modified_json):
    """Calculate modifications needed based on JSON differences"""
    modifications = []
    positions = {
        'name': (50, 50),
        'email': (50, 80),
        'phone': (50, 110),
        'summary': (50, 150),
        'skills': (50, 200),
        'experience': (50, 250),
        'education': (50, 400),
        'projects': (50, 500),
        'certifications': (50, 600)
    }
    
    for key in modified_json:
        if key in original_json and original_json[key] != modified_json[key]:
            modifications.append({
                'field': key,
                'old_value': original_json[key],
                'new_value': modified_json[key],
                'position': positions.get(key, (50, 50))
            })
    
    return modifications