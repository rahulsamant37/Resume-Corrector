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
from llm import client

def create_preview(original_file, modifications, file_type):
    """Create a preview of the modified document"""
    try:
        if file_type == "application/pdf":
            output = modify_pdf(original_file, modifications)
            if output:
                pdf_images = convert_from_bytes(output.getvalue())
                if pdf_images:
                    img_byte_arr = BytesIO()
                    pdf_images[0].save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    return img_byte_arr
        else:
            output = modify_image(original_file, modifications)
            if output:
                return output
    except Exception as e:
        st.error(f"Error creating preview: {str(e)}")
        return None

def text_to_json(text):
    system_prompt = """You are an expert resume parser. You must return ONLY valid JSON without any explanation, comments, or markdown formatting."""
    
    user_prompt = f"""Convert this resume text into JSON with this exact schema, adding no extra text or formatting:
    {{
        "name": "string",
        "email": "string",
        "phone": "string",
        "summary": "string",
        "skills": ["string"],
        "experience": [{{
            "company": "string",
            "position": "string",
            "duration": "string",
            "achievements": ["string"]
        }}],
        "education": [{{
            "degree": "string",
            "institution": "string",
            "year": "string",
            "gpa": "string (optional)"
        }}],
        "projects": [{{
            "name": "string",
            "description": "string",
            "technologies": ["string"]
        }}],
        "certifications": [{{
            "name": "string",
            "issuer": "string",
            "year": "string"
        }}]
    }}

    Resume Text:
    {text}"""

    try:
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000,
        )
        
        response_text = completion.choices[0].message.content
        def extract_json_from_text(text):
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON object found in response")
            json_str = text[start_idx:end_idx + 1]
            json_str = json_str.replace('```json', '').replace('```', '')
            
            return json_str.strip()
        json_str = extract_json_from_text(response_text)
        parsed_json = json.loads(json_str)
        required_fields = ['name', 'email', 'phone', 'skills', 'experience', 'education']
        missing_fields = [field for field in required_fields if field not in parsed_json]
        
        if missing_fields:
            st.warning(f"Missing required fields: {', '.join(missing_fields)}")
            for field in missing_fields:
                if field in ['skills', 'experience', 'education']:
                    parsed_json[field] = []
                else:
                    parsed_json[field] = ""
        
        return parsed_json
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON response. Error: {str(e)}")
        st.write("Response received:", response_text)  # For debugging
        return {field: "" if field not in ['skills', 'experience', 'education'] else [] 
                for field in ['name', 'email', 'phone', 'summary', 'skills', 'experience', 'education', 'projects', 'certifications']}
    except Exception as e:
        st.error(f"Error generating JSON: {str(e)}")
        return {field: "" if field not in ['skills', 'experience', 'education'] else [] 
                for field in ['name', 'email', 'phone', 'summary', 'skills', 'experience', 'education', 'projects', 'certifications']}

def get_modifications_from_json_diff(original_json, modified_json):
    """Calculate modifications needed based on JSON differences"""
    modifications = []
    for key in modified_json:
        if key in original_json and original_json[key] != modified_json[key]:
            modifications.append({
                'field': key,
                'old_value': original_json[key],
                'new_value': modified_json[key],
                'position': (50, 50)
            })
    
    return modifications