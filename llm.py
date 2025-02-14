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
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and 'GROQ_API_KEY' in st.secrets:
    GROQ_API_KEY = st.secrets['GROQ_API_KEY']

if not GROQ_API_KEY:
    st.error("Groq API key not found. Please set the GROQ_API_KEY environment variable or add it to Streamlit secrets.")
    st.stop()
client = Groq(api_key=GROQ_API_KEY)

def edit_resume_with_llm(current_json, instructions):
    system_prompt = """You are an expert resume editor. Modify resumes according to user instructions while maintaining professional standards and accuracy."""
    
    user_prompt = f"""Current Resume:
{json.dumps(current_json, indent=2)}

Instructions for modification:
{instructions}

Return the modified resume as valid JSON. Preserve existing information unless explicitly told to modify it."""

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
        
        return json.loads(completion.choices[0].message.content)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse modified JSON: {str(e)}")
        return current_json
    except Exception as e:
        st.error(f"Error modifying resume: {str(e)}")
        return current_json

def generate_resume_suggestions(resume_json):
    system_prompt = """You are an expert resume consultant. Analyze resumes and provide actionable improvements."""
    
    user_prompt = f"""Analyze this resume and provide 3-5 specific suggestions for improvement:
{json.dumps(resume_json, indent=2)}

Focus on content, impact, and presentation. Be specific and actionable."""

    try:
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating suggestions: {str(e)}")
        return "Unable to generate suggestions at this time."