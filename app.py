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
from extraction import extract_text_from_file
from llm import edit_resume_with_llm, generate_resume_suggestions
from modify import modify_pdf, modify_image
from preview import get_modifications_from_json_diff, text_to_json

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and 'GROQ_API_KEY' in st.secrets:
    GROQ_API_KEY = st.secrets['GROQ_API_KEY']

if not GROQ_API_KEY:
    st.error("Groq API key not found. Please set the GROQ_API_KEY environment variable or add it to Streamlit secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)


def main():
    st.title("AI-Powered Resume Editor")
    st.markdown("""
    📄 Upload your resume (PDF or Image) to get started
    ✏️ Edit and enhance your resume with AI assistance
    💡 Get personalized improvement suggestions
    """)

    uploaded_file = st.file_uploader("Upload Resume (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        if 'original_file' not in st.session_state:
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            st.session_state.original_file = BytesIO(file_bytes)
            st.session_state.file_type = uploaded_file.type
        
        with st.spinner("Processing your resume..."):
            raw_text = extract_text_from_file(uploaded_file)
            resume_json = text_to_json(raw_text)
            st.session_state.original_json = resume_json

        tabs = st.tabs(["Extracted Data", "Edit Resume", "AI Suggestions"])
        
        with tabs[0]:
            st.subheader("Original Text")
            with st.expander("Show extracted text"):
                st.write(raw_text)
            
            st.subheader("Structured Data")
            st.json(resume_json)

        with tabs[1]:
            st.subheader("Edit Resume")
            instructions = st.text_area(
                "Enter your editing instructions:",
                placeholder="Example: Add a new skill 'Python', Update my job title at Google to 'Senior Developer'"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Preview Changes", type="primary"):
                    with st.spinner("Generating preview..."):
                        modified_json = edit_resume_with_llm(resume_json, instructions)
                        st.session_state.modified_json = modified_json
                        st.json(modified_json)
            
            with col2:
                if st.button("Apply Changes") and 'modified_json' in st.session_state:
                    with st.spinner("Applying changes to document..."):
                        modifications = get_modifications_from_json_diff(
                            st.session_state.original_json,
                            st.session_state.modified_json
                        )
                        
                        st.session_state.original_file.seek(0)
                        if st.session_state.file_type == "application/pdf":
                            output_stream = modify_pdf(st.session_state.original_file, modifications)
                        else:
                            output_stream = modify_image(st.session_state.original_file, modifications)
                        
                        if output_stream:
                            st.success("Changes applied successfully! 🎉")
                            
                            # Provide download button for modified file
                            file_extension = "pdf" if st.session_state.file_type == "application/pdf" else "png"
                            st.download_button(
                                label=f"Download Modified Resume",
                                data=output_stream,
                                file_name=f"modified_resume.{file_extension}",
                                mime=st.session_state.file_type
                            )

        with tabs[2]:
            st.subheader("AI Suggestions")
            if st.button("Get Resume Suggestions"):
                with st.spinner("Analyzing your resume..."):
                    suggestions = generate_resume_suggestions(resume_json)
                    st.write(suggestions)

if __name__ == "__main__":
    main()