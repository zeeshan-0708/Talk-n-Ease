import google.generativeai as genai
import streamlit as st
import os
from dotenv import load_dotenv
import speech_recognition as sr
import PyPDF2
from PIL import Image
import pytesseract
from io import StringIO

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    raise ValueError("Gemini API key not found. Please set it in the .env file.")

def get_gemini_response(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

def capture_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening for your question...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        question = recognizer.recognize_google(audio)
        st.write(f"Question recognized: {question}")
        return question
    except sr.UnknownValueError:
        st.error("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError:
        st.error("Could not request results from Google Speech Recognition service.")
        return None

def process_uploaded_file(uploaded_file):
    file_content = ""
    if uploaded_file.type == "text/plain":
        file_content = uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            file_content += page.extract_text()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        from docx import Document
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            file_content += para.text + "\n"
    elif uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
        img = Image.open(uploaded_file)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        text_from_image = pytesseract.image_to_string(img)
        file_content = text_from_image
        st.image(img, caption="Uploaded Image", use_container_width=True)
        image_details = {
            "Image Type": uploaded_file.type,
            "Image Size (bytes)": len(uploaded_file.getvalue()),
            "Image Dimensions": f"{img.width}x{img.height}",
            "Extracted Text (if any)": text_from_image if text_from_image else "No text found"
        }
        st.write("**Image Details**:")
        for key, value in image_details.items():
            st.write(f"{key}: {value}")
    return file_content

st.set_page_config(page_title="Talk-n-Ease", page_icon="🤖")

st.markdown("""
    <style>
        body {
            background-color: #f7f7f7;
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
        }
        .stButton>button {
            background-color: #009688;
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 15px 30px;
            border-radius: 30px;
            border: none;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            transition: background-color 0.3s ease, transform 0.2s ease;
        }
        .stButton>button:hover {
            background-color: #00796b;
            transform: translateY(-2px);
        }
        .stTextInput>div>input {
            border-radius: 15px;
            padding: 18px;
            border: 1px solid #ccc;
            font-size: 18px;
            width: 80%;
            margin: 20px auto;
            transition: border-color 0.3s ease;
        }
        .stTextInput>div>input:focus {
            border-color: #009688;
            outline: none;
        }
        .stError {
            color: #f44336;
            font-size: 14px;
            margin-top: 20px;
        }
        .stSuccess {
            color: #4caf50;
            font-size: 14px;
            margin-top: 20px;
        }
        .stTitle {
            font-size: 32px;
            text-align: center;
            color: #333;
            font-weight: bold;
        }
        .stMarkdown {
            color: #333;
            font-size: 18px;
            text-align: center;
        }
        .response-text {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            color: #333;
            font-size: 18px;
            margin-top: 20px;
            line-height: 1.5;
        }
        .response-error {
            background-color: #f8d7da;
            padding: 15px;
            border-radius: 15px;
            color: #721c24;
            font-size: 16px;
            margin-top: 20px;
        }
        .microphone-button {
            background-color: #009688;
            border-radius: 50%;
            padding: 20px;
            color: white;
            font-size: 24px;
            border: none;
            cursor: pointer;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
            transition: background-color 0.3s ease, transform 0.2s ease;
        }
        .microphone-button:hover {
            background-color: #00796b;
            transform: translateY(-2px);
        }
        .input-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .input-container > * {
            margin: 0 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Talk-n-Ease")

uploaded_file = st.file_uploader("Upload a file (PDF, Text, JPG, PNG, etc.):", type=["pdf", "txt", "docx", "jpg", "png", "jpeg"])
file_content = ""

if uploaded_file is not None:
    file_content = process_uploaded_file(uploaded_file)

input_container = st.container()
with input_container:
    user_input = st.text_area("Ask your question (you can also upload a file above):", height=100, placeholder="Type your question here...")

mic_button = st.button("Start Speech Recognition", key="mic_button", use_container_width=True)

if mic_button:
    user_input = capture_speech()

submit = st.button("Submit")

if submit or user_input:
    if user_input.strip() or file_content:
        with st.spinner("Generating response..."):
            st.subheader("Response:")
            prompt = user_input if user_input.strip() else file_content
            response = get_gemini_response(prompt)
            if response:
                st.markdown(f"<div class='response-text'>{response}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='response-error'>Sorry, something went wrong. Please try again later.</div>", unsafe_allow_html=True)
    else:
        st.error("Please enter a question or upload a file to get a response.")
