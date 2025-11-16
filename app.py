import os
import time
import logging
import streamlit as st
import google.generativeai as genai
from file_processing import process_file
from export_utils import export_as_pdf, export_as_markdown
from gemini_utils import (
    configure_gemini,
    extract_summary,
    split_into_paragraphs,
    generate_questions
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup Gemini API key
gemini_api_key = st.secrets.get("GEMINI_API_KEY")
model = st.secrets.get("MODEL", "gemini-1.5-flash")

# Check for API key
if not gemini_api_key:
    st.error("GEMINI_API_KEY is not set. Please add it to your secrets file.")
    st.stop()

# Initialize session state
if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = []
if 'paragraph_index' not in st.session_state:
    st.session_state.paragraph_index = 0
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "upload"
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'paragraphs' not in st.session_state:
    st.session_state.paragraphs = []
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'api_error' not in st.session_state:
    st.session_state.api_error = None
if 'quiz_mode' not in st.session_state:
    st.session_state.quiz_mode = False
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []


# Helper Functions
def summarize_text(text):
    """Summarize the extracted text using Gemini."""
    st.session_state.api_error = None
    
    try:
      
        status, model_instance = configure_gemini(gemini_api_key, model)
        if not status:
            logger.error(f"Failed to configure Gemini API: {model_instance}")
            st.session_state.api_error = "Gemini API configuration failed. Please check your API key."
            return None
            
        # Extract summary
        summary = extract_summary(text, model_instance)
        return summary
    except Exception as e:
        logger.error(f"Error in summarize_text: {str(e)}")
        st.session_state.api_error = f"Error generating summary: {str(e)}"
        return None

def process_paragraphs(text):
    """Split the text into paragraphs."""
    st.session_state.api_error = None
    
    try:
        status, model_instance = configure_gemini(gemini_api_key, model)
        if not status:
            logger.error(f"Failed to configure Gemini API: {model_instance}")
            st.session_state.api_error = "Gemini API configuration failed. Please check your API key."
            return []
            
        # Split into paragraphs
        paragraphs = split_into_paragraphs(text, model_instance)
        return paragraphs
    except Exception as e:
        logger.error(f"Error in process_paragraphs: {str(e)}")
        st.session_state.api_error = f"Error processing paragraphs: {str(e)}"
        return []

def create_questions(paragraph):
    """Create questions and answers from the paragraph."""
    st.session_state.api_error = None
    
    try:
        # Configure Gemini with API key
        status, model_instance = configure_gemini(gemini_api_key, model)
        if not status:
            logger.error(f"Failed to configure Gemini API: {model_instance}")
            st.session_state.api_error = "Gemini API configuration failed. Please check your API key."
            return []
            
        # Generate questions
        questions = generate_questions(paragraph, model_instance)
        return questions
    except Exception as e:
        logger.error(f"Error in create_questions: {str(e)}")
        st.session_state.api_error = f"Error generating questions: {str(e)}"
        return []

def next_paragraph():
    """Move to the next paragraph."""
    st.session_state.paragraph_index += 1
    st.session_state.show_answer = False
    st.session_state.generated_questions = []

def previous_paragraph():
    """Move to the previous paragraph."""
    st.session_state.paragraph_index -= 1
    st.session_state.show_answer = False
    st.session_state.generated_questions = []

def toggle_answer():
    """Toggle showing the answer."""
    st.session_state.show_answer = not st.session_state.show_answer

def switch_tab(tab_name):
    """Switch to a different tab."""
    st.session_state.active_tab = tab_name


def start_quiz():
    """Start the interactive quiz."""
    st.session_state.quiz_mode = True
    st.session_state.current_question_index = 0
    st.session_state.user_answers = ["" for _ in st.session_state.generated_questions]


def display_quiz():
    """Display the interactive quiz."""
    q_index = st.session_state.current_question_index
    qa_pair = st.session_state.generated_questions[q_index]

    st.markdown(f"**Question {q_index + 1}: {qa_pair['question']}**")

    st.session_state.user_answers[q_index] = st.text_input("Your Answer", value=st.session_state.user_answers[q_index])

    if st.button("Submit Answer"):
        st.markdown(f"**Correct Answer:** {qa_pair['answer']}")

    col1, col2 = st.columns(2)
    if q_index > 0 and col1.button("Previous Question"):
        st.session_state.current_question_index -= 1

    if q_index < len(st.session_state.generated_questions) - 1 and col2.button("Next Question"):
        st.session_state.current_question_index += 1

    if st.button("Finish Quiz"):
        st.session_state.quiz_mode = False


def format_questions_for_export(questions):
    """Format questions and answers for export."""
    text = ""
    for i, qa in enumerate(questions):
        text += f"Q{i+1}: {qa['question']}\n"
        text += f"A{i+1}: {qa['answer']}\n\n"
    return text


# UI
st.title("DOC-SUM")

# Main navigation buttons
col1, col2, col3 = st.columns(3)
if col1.button("📄 Upload Content"):
    switch_tab("upload")
if col2.button("📝 Review Summary"):
    switch_tab("summary")
if col3.button("❓ Practice Questions"):
    switch_tab("practice")

# Upload Tab
if st.session_state.active_tab == "upload":
    st.header("Upload Your Study Material")
    
    uploaded_file = st.file_uploader("Choose a PDF, DOCX, TXT, or image file", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"])
    
    col1, col2 = st.columns(2)
    process_button = col1.button("Process File")
    clear_button = col2.button("Clear")
    
    if process_button and uploaded_file is not None:
        with st.spinner("Processing file..."):
            # Extract text from file
            text = process_file(uploaded_file)
            if text:
                st.session_state.extracted_text = text
                
                # Generate summary
                with st.spinner("Generating summary..."):
                    summary = summarize_text(text)
                    if summary:
                        st.session_state.summary = summary
                    
                # Split into paragraphs
                with st.spinner("Processing paragraphs..."):
                    paragraphs = process_paragraphs(text)
                    if paragraphs:
                        st.session_state.paragraphs = paragraphs
                        st.session_state.paragraph_index = 0
                
                # Switch to summary tab
                switch_tab("summary")
            else:
                logger.error("Failed to extract text from the uploaded file.")
    
    if clear_button:
        st.session_state.extracted_text = ""
        st.session_state.summary = ""
        st.session_state.paragraphs = []
        st.session_state.generated_questions = []
        st.session_state.paragraph_index = 0
        st.session_state.show_answer = False
        st.session_state.api_error = None

# Summary Tab
elif st.session_state.active_tab == "summary":
    st.header("Document Summary")
    
    if st.session_state.summary:
        st.markdown(st.session_state.summary)
        
        # Add export buttons
        col1, col2 = st.columns(2)
        col1.markdown(export_as_pdf(st.session_state.summary, "summary"), unsafe_allow_html=True)
        col2.markdown(export_as_markdown(st.session_state.summary, "summary"), unsafe_allow_html=True)

        if st.button("Continue to Practice Questions"):
            switch_tab("practice")
    else:
        st.info("No summary available. Please upload and process a file first.")
        if st.button("Go to Upload"):
            switch_tab("upload")

# Practice Questions Tab
elif st.session_state.active_tab == "practice":
    st.header("Practice Questions")
    
    if not st.session_state.paragraphs:
        st.info("No content to generate questions from. Please upload and process a file first.")
        if st.button("Go to Upload"):
            switch_tab("upload")
    else:
        # Display paragraph navigation
        total_paragraphs = len(st.session_state.paragraphs)
        st.markdown(f"**Paragraph {st.session_state.paragraph_index + 1} of {total_paragraphs}**")
        
        # Display current paragraph
        current_paragraph = st.session_state.paragraphs[st.session_state.paragraph_index]
        st.markdown("### Content")
        st.write(current_paragraph)
        
        # Generate questions button
        if st.button("Generate Questions for this Paragraph"):
            with st.spinner("Generating questions..."):
                questions = create_questions(current_paragraph)
                if questions:
                    st.session_state.generated_questions = questions
                    st.experimental_rerun()
        
        # Display questions
        if st.session_state.generated_questions:
            st.markdown("### Questions")
            
            # Add a button to start the quiz
            if not st.session_state.quiz_mode and st.button("Start Quiz"):
                start_quiz()

            if st.session_state.quiz_mode:
                display_quiz()
            else:
                for i, qa_pair in enumerate(st.session_state.generated_questions):
                    st.markdown(f"**Q{i+1}: {qa_pair['question']}**")

                    if st.session_state.show_answer:
                        st.markdown(f"**A{i+1}:** {qa_pair['answer']}")

                # Show/Hide answer button
                if st.button("Show/Hide Answers"):
                    toggle_answer()

        # Add export buttons for questions
        if st.session_state.generated_questions:
            questions_text = format_questions_for_export(st.session_state.generated_questions)
            col1, col2 = st.columns(2)
            col1.markdown(export_as_pdf(questions_text, "questions"), unsafe_allow_html=True)
            col2.markdown(export_as_markdown(questions_text, "questions"), unsafe_allow_html=True)
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        if st.session_state.paragraph_index > 0:
            if col1.button("Previous Paragraph"):
                previous_paragraph()
        
        if st.session_state.paragraph_index < total_paragraphs - 1:
            if col2.button("Next Paragraph"):
                next_paragraph() 
