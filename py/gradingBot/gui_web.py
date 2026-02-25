"""
Streamlit frontend for the Grading Bot.

Run with: streamlit run gradingBot/app.py
"""

# Adding so that .env credentials are loaded
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import time
import tempfile
from typing import Dict, List
import sys

from dotenv import load_dotenv
from pathlib import Path

import os

# Load .env from py/ directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Ensure parent directory (py/) is in Python path for package imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    
from gradingBot.gradingBot import GradingBot

# Page configuration
st.set_page_config(
    page_title="Grading Bot",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'bot' not in st.session_state:
    st.session_state.bot = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = "discrete_math_ta_001"
if 'model' not in st.session_state:
    st.session_state.model = "4o-mini"
if 'uploaded_docs' not in st.session_state:
    st.session_state.uploaded_docs = []


def initialize_bot(session_id: str, model: str):
    """Initialize the grading bot."""
    try:
        bot = GradingBot(
            session_id=session_id,
            model=model
        )
        return bot, None
    except Exception as e:
        return None, str(e)


def main():
    # Auto-initialize bot on first load if not already initialized
    if st.session_state.bot is None:
        try:
            st.session_state.bot = GradingBot(
                session_id=st.session_state.session_id,
                model=st.session_state.model
            )
            # Clear any previous init errors
            if hasattr(st.session_state, 'init_error'):
                del st.session_state.init_error
        except Exception as e:
            # If initialization fails, bot will remain None and error will be shown
            st.session_state.bot = None
            st.session_state.init_error = str(e)
    
    # Header
    st.markdown('<div class="main-header">📝 Grading Bot</div>', unsafe_allow_html=True)
    st.markdown("**AI-Powered Grading System with RAG** - Grade student submissions using course materials")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Show initialization error if any
        if hasattr(st.session_state, 'init_error'):
            st.error(f"⚠️ Initialization Error: {st.session_state.init_error}")
            st.info("Please check your .env file and try refreshing the page.")
        
        # Session ID input
        session_id = st.text_input(
            "Session ID",
            value=st.session_state.session_id,
            help="Unique identifier for your session. Each TA/Professor should use a different ID."
        )
        
        # Model selection
        model_options = ["4o-mini", "gpt-4", "gpt-3.5-turbo"]
        current_model_index = model_options.index(st.session_state.model) if st.session_state.model in model_options else 0
        model = st.selectbox(
            "LLM Model",
            options=model_options,
            index=current_model_index,
            help="Select the LLM model to use for grading"
        )
        
        # Reinitialize bot if settings changed
        settings_changed = (session_id != st.session_state.session_id) or (model != st.session_state.model)
        
        if settings_changed:
            if st.button("🔄 Update Settings", type="primary", use_container_width=True):
                bot, error = initialize_bot(session_id, model)
                if error:
                    st.error(f"Error initializing bot: {error}")
                else:
                    st.session_state.bot = bot
                    st.session_state.session_id = session_id
                    st.session_state.model = model
                    st.session_state.uploaded_docs = []
                    if hasattr(st.session_state, 'init_error'):
                        del st.session_state.init_error
                    st.success("Settings updated successfully!")
                    st.rerun()
        
        # Display current status
        if st.session_state.bot:
            st.markdown("---")
            st.success("✅ Bot Active")
            st.caption(f"Session: {st.session_state.session_id}")
            st.caption(f"Model: {st.session_state.model}")
        else:
            st.warning("⚠️ Bot not initialized")
            st.caption("Check configuration and refresh page")
    
    # Main content area
    if not st.session_state.bot:
        st.error("❌ Bot initialization failed. Please check your configuration in the sidebar.")
        if hasattr(st.session_state, 'init_error'):
            st.error(f"Error: {st.session_state.init_error}")
        return
    
    # Tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["📚 Upload Materials", "✏️ Grade Submission", "💬 Interactive Review"])
    
    # Tab 1: Upload Materials
    with tab1:
        st.markdown('<div class="sub-header">Upload Course Materials</div>', unsafe_allow_html=True)
        st.markdown("Upload your course materials to enable RAG-powered grading.")
        
        # Document type selection
        doc_type = st.selectbox(
            "Document Type",
            options=["Syllabus", "Homework Assignment", "Homework Solution", "Lecture Material", "Textbook"],
            help="Select the type of document you're uploading"
        )
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a text-based PDF file (recommended max size: 10MB)"
        )
        
        # Display file size if file is selected
        if uploaded_file is not None:
            # Get file size without consuming the buffer
            uploaded_file.seek(0, 2)  # Seek to end
            file_size_bytes = uploaded_file.tell()
            uploaded_file.seek(0)  # Reset to beginning
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            st.info(f"📄 File: {uploaded_file.name} ({file_size_mb:.2f} MB)")
            
            # Warn if file is very large
            if file_size_mb > 10:
                st.warning(f"⚠️ File is large ({file_size_mb:.2f} MB). Large files may fail to upload due to server limits. Consider splitting the document or using a smaller file.")
            elif file_size_mb > 5:
                st.info("💡 File size is moderate. If upload fails, try splitting the document into smaller parts.")
        
        # Additional metadata
        col1, col2 = st.columns(2)
        with col1:
            assignment_name = st.text_input(
                "Assignment/Lecture Name (optional)",
                help="e.g., 'HW1', 'Lecture 1', etc."
            )
        with col2:
            description = st.text_input(
                "Description (optional)",
                help="Additional description for the document"
            )
        
        # Upload button
        if st.button("📤 Upload Document", type="primary", use_container_width=True):
            if not uploaded_file:
                st.error("Please select a file to upload.")
            else:
                with st.spinner("Uploading document..."):
                    # Save uploaded file temporarily
                    temp_dir = Path(tempfile.gettempdir())
                    temp_path = temp_dir / uploaded_file.name
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    print("DEBUG: Saved temp file. Size (MB):",
                          Path(temp_path).stat().st_size / (1024 * 1024))


                    try:
                        # Upload based on document type
                        if doc_type == "Syllabus":
                            result = st.session_state.bot.upload_syllabus(temp_path, description)
                        elif doc_type == "Homework Assignment":
                            result = st.session_state.bot.upload_homework_assignment(
                                temp_path, assignment_name, description
                            )
                        elif doc_type == "Homework Solution":
                            result = st.session_state.bot.upload_homework_solution(
                                temp_path, assignment_name, description
                            )
                        elif doc_type == "Lecture Material":
                            result = st.session_state.bot.upload_lecture_material(
                                temp_path, assignment_name, description
                            )
                        elif doc_type == "Textbook":
                            result = st.session_state.bot.upload_textbook(temp_path, description)
                        
                        if "error" in result.get("result", {}):
                            error_msg = result['error']
                            # Check for HTTP 413 (Request Too Long)
                            if "413" in error_msg or "Too Long" in error_msg or "Too Large" in error_msg:
                                # Get file size
                                uploaded_file.seek(0, 2)
                                file_size_bytes = uploaded_file.tell()
                                uploaded_file.seek(0)
                                file_size_mb = file_size_bytes / (1024 * 1024)
                                st.error(f"❌ Upload failed: File too large!")
                                st.error(f"**File size:** {file_size_mb:.2f} MB")
                                st.warning("""
                                **Solutions:**
                                1. **Split the document**: Break large PDFs into smaller sections (e.g., split by chapters)
                                2. **Compress the PDF**: Use a PDF compressor to reduce file size
                                3. **Extract text**: If possible, extract just the text content and upload as a smaller file
                                4. **Use multiple uploads**: Upload different sections separately
                                
                                **Recommended:** Keep individual files under 5-10 MB for best results.
                                """)
                            else:
                                st.error(f"Upload failed: {error_msg}")
                        else:
                            # Successful upload: always show chunks info
                            chunks = result.get("chunks", [])
                            st.success(f"✅ Document uploaded successfully!")
                            st.info(f"Number of chunks created: {len(chunks)}")
                            if chunks:
                                st.info("Chunks: " + ", ".join(chunks))
                            st.info("⏳ Please wait 20-30 seconds for the document to be processed before grading.")

                            # Update uploaded docs list
                            st.session_state.uploaded_docs.append({
                                "type": doc_type,
                                "name": uploaded_file.name,
                                "assignment": assignment_name,
                                "description": description
                            })

                            # Clean up temp file
                            temp_path.unlink()

                    except Exception as e:
                        st.error(f"Error during upload: {str(e)}")
                        if temp_path.exists():
                            temp_path.unlink()
        
        # Show uploaded documents
        if st.session_state.uploaded_docs:
            st.markdown("---")
            st.subheader("📋 Uploaded Documents")
            for i, doc in enumerate(st.session_state.uploaded_docs, 1):
                with st.expander(f"{i}. {doc['type']}: {doc['name']}"):
                    if doc.get('assignment'):
                        st.write(f"**Assignment/Lecture:** {doc['assignment']}")
                    if doc.get('description'):
                        st.write(f"**Description:** {doc['description']}")
    
    # Tab 2: Grade Single Submission
    with tab2:
        st.markdown('<div class="sub-header">Grade Student Submission</div>', unsafe_allow_html=True)
        
        # Assignment info
        col1, col2 = st.columns(2)
        with col1:
            assignment_name = st.text_input("Assignment Name", help="e.g., 'HW1', 'Quiz 2'")
        with col2:
            max_points = st.number_input("Maximum Points", min_value=0.0, value=10.0, step=0.5)
        
        # Question input
        question = st.text_area(
            "Question/Problem Statement",
            height=150,
            help="Enter the question or problem statement that the student answered"
        )
        
        # Student answer input
        answer_input_method = st.radio(
            "Answer Input Method",
            options=["Type/Paste Text", "Upload File"],
            horizontal=True
        )
        
        student_answer = ""
        if answer_input_method == "Type/Paste Text":
            student_answer = st.text_area(
                "Student Answer",
                height=200,
                help="Enter or paste the student's answer"
            )
        else:
            answer_file = st.file_uploader("Upload Student Answer File", type=['txt', 'pdf'])
            if answer_file:
                if answer_file.type == 'text/plain':
                    student_answer = str(answer_file.read(), "utf-8")
                else:
                    st.warning("PDF files are not yet supported for answer upload. Please use text files or paste the answer.")
        
        # Optional rubric
        rubric = st.text_area(
            "Grading Rubric (Optional)",
            height=100,
            help="Additional grading instructions or rubric"
        )
        
        # Grade button
        if st.button("🎯 Grade Submission", type="primary", use_container_width=True):
            if not question or not student_answer:
                st.error("Please provide both a question and student answer.")
            else:
                with st.spinner("Grading submission... This may take a moment."):
                    try:
                        result = st.session_state.bot.grade_submission(
                            question=question,
                            student_answer=student_answer,
                            max_points=max_points if max_points > 0 else None,
                            rubric=rubric if rubric else None,
                            assignment_name=assignment_name if assignment_name else None
                        )
                        
                        if "error" in result:
                            st.error(f"Grading failed: {result['error']}")
                        else:
                            # Display results
                            st.markdown("---")
                            st.markdown('<div class="sub-header">Grading Result</div>', unsafe_allow_html=True)
                            
                            # Score display
                            if result.get("score") is not None:
                                score = result["score"]
                                max_pts = result.get("max_points", max_points)
                                percentage = (score / max_pts) * 100
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Score", f"{score:.2f} / {max_pts:.2f}")
                                with col2:
                                    st.metric("Percentage", f"{percentage:.1f}%")
                                with col3:
                                    # Color code based on score
                                    if percentage >= 90:
                                        st.metric("Grade", "A", delta="Excellent")
                                    elif percentage >= 80:
                                        st.metric("Grade", "B", delta="Good")
                                    elif percentage >= 70:
                                        st.metric("Grade", "C", delta="Fair")
                                    else:
                                        st.metric("Grade", "Below C", delta="Needs Improvement")
                            
                            # Feedback
                            st.subheader("📝 Feedback")
                            st.markdown(result.get("feedback", "No feedback available"))

                            #Sources used for response
                            st.subheader("Sources Used")
                            if "sources" in result:
                                for source in result["sources"]:
                                    st.write(f"- {source}")
                            
                            # RAG context used
                            with st.expander("View RAG Context Used"):
                                rag_context = result.get("rag_context_used")

                                if rag_context:
                                    st.text_area(
                                        "Retrieved Context",
                                        rag_context,
                                        height=200,
                                        disabled=True
                                    )
                                else:
                                    st.info("No relevant context was retrieved from course materials.")
                    except Exception as e:
                        st.error(f"Error during grading: {str(e)}")
    # Tab 3: Interactive Q&A
    with tab3:
        st.markdown('<div class="sub-header">💬 Interactive Q&A</div>', unsafe_allow_html=True)
        st.markdown(
            "Students can ask questions about assignments or course material. "
            "The bot will provide feedback, counterexamples, or prompts for deeper thinking without giving away the answer."
        )

        # Assignment info
        col1, col2 = st.columns(2)
        with col1:
            interactive_assignment = st.text_input(
                "Assignment Name (optional)",
                help="Specify the assignment if applicable, e.g., 'HW1', 'Quiz 2'"
            )

        # Question and student answer
        question_input = st.text_area(
            "Question/Problem Statement (optional)",
            height=120,
            help="You can provide the question/problem statement here to give context"
        )

        student_answer_input = st.text_area(
            "Student Answer",
            height=150,
            help="Enter or paste the student's answer"
        )

        # Initialize conversation history
        if 'interactive_history' not in st.session_state:
            st.session_state.interactive_history = []

        # Send button with unique key
        if st.button("💡 Submit to Bot", key="interactive_submit", type="primary", use_container_width=True):
            if not student_answer_input:
                st.error("Please provide a student answer to continue.")
            else:
                with st.spinner("Bot is thinking..."):
                    # Build conversation: full history + new student message
                    conversation = st.session_state.interactive_history.copy()
                    conversation.append({
                        "role": "student",
                        "content": (
                            (f"Question: {question_input}\n\n" if question_input else "") +
                            student_answer_input
                        )
                    })

                    # Call the interactive response method
                    response = st.session_state.bot.generate_interactive_response(
                        conversation=conversation,
                        assignment_name=interactive_assignment if interactive_assignment else None,
                    )

                    if "error" in response:
                        st.error(f"Error generating response: {response['error']}")
                    else:
                        # Append bot response to conversation history
                        conversation.append({
                            "role": "bot",
                            "content": response.get("response_text", "No response available")
                        })

                        # Save updated conversation to session
                        st.session_state.interactive_history = conversation

        # Display latest bot feedback first
        if st.session_state.interactive_history:
            latest_bot_msg = next(
                (msg for msg in reversed(st.session_state.interactive_history) if msg["role"] == "bot"),
                None
            )

            if latest_bot_msg:
                st.markdown("---")
                st.subheader("📝 Latest Feedback")
                st.markdown(latest_bot_msg["content"])

            # Then show full conversation history (optional)
            st.markdown("---")
            st.subheader("Conversation History")
            for message in st.session_state.interactive_history:
                role = "Student" if message["role"] == "student" else "Bot"
                st.markdown(f"**{role}:** {message['content']}")
if __name__ == "__main__":
    main()

