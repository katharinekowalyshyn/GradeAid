# Grading Bot

A prototype grading system that uses LLM Proxy with RAG (Retrieval Augmented Generation) to grade student submissions based on course materials.

## Features

- **Document Management**: Upload course materials (syllabus, assignments, solutions, lectures, textbook)
- **RAG-Powered Grading**: Automatically retrieves relevant context from course materials when grading
- **Session-Based**: Each TA/Professor uses a unique session ID to maintain separate document collections
- **Flexible Grading**: Grade individual submissions or batch grade multiple submissions
- **Detailed Feedback**: Provides scores and constructive feedback based on course materials

## Requirements

- Python 3.7+
- `llmproxy` package installed (from parent directory: `pip install .`)
- `.env.` file with `LLMPROXY_ENDPOINT` and `LLMPROXY_API_KEY`
- For Streamlit frontend: `streamlit` (install with `pip install streamlit`)

## Web Interface (Streamlit)

The easiest way to use the Grading Bot is through the Streamlit web interface:

### Launch the Web App

```bash
# IMPORTANT: Run from the py/ directory
cd py/
streamlit run gradingBot/app.py

# Or use the provided script
./gradingBot/run_app.sh
```

**Note:** You must run from the `py/` directory (not from inside `gradingBot/`) so Python can find the package correctly.

The web interface provides:
- **📚 Upload Materials**: Easy document upload with drag-and-drop
- **✏️ Grade Submission**: Interactive grading interface with real-time feedback
- **📊 Batch Grading**: Upload JSON files to grade multiple submissions
- **📋 History & Docs**: View uploaded documents and grading history

### Features:
- Visual score display with grade indicators
- RAG context viewer to see what course materials were used
- Session management in the sidebar
- Configurable RAG parameters
- Download grading results as JSON

## Quick Start (Python API)

### 1. Initialize the Grading Bot

```python
from gradingBot import GradingBot

# Each TA/Professor should use a unique session_id
bot = GradingBot(
    session_id="discrete_math_ta_001",
    model="4o-mini",
    rag_threshold=0.3,
    rag_k=5
)
```

### 2. Upload Course Materials

```python
# Upload syllabus
bot.upload_syllabus("syllabus.pdf", "Discrete Math Syllabus")

# Upload homework assignment
bot.upload_homework_assignment(
    "hw1.pdf",
    assignment_name="HW1",
    description="Homework 1: Logic and Proofs"
)

# Upload homework solution
bot.upload_homework_solution(
    "hw1_solution.pdf",
    assignment_name="HW1",
    description="Homework 1 Solutions"
)

# Upload lecture materials
bot.upload_lecture_material(
    "lecture1.pdf",
    lecture_name="Lecture 1: Introduction"
)

# Upload textbook
bot.upload_textbook("textbook.pdf", "Discrete Mathematics Textbook")

# Wait for documents to be processed
bot.wait_for_processing(seconds=20)
```

### 3. Grade a Student Submission

```python
result = bot.grade_submission(
    question="Prove that for any integer n, if n is even, then n² is even.",
    student_answer="Let n be an even integer. Then n = 2k for some integer k...",
    max_points=10.0,
    assignment_name="HW1",
    rubric="Evaluate: correctness, clarity, notation."
)

print(f"Score: {result['score']} / {result['max_points']}")
print(f"Feedback: {result['feedback']}")
```

## Command Line Interface

The grading bot also includes a CLI for quick operations:

### Upload a document:

```bash
python gradingBot.py \
    --session-id "discrete_math_ta_001" \
    --upload syllabus \
    --file "syllabus.pdf" \
    --description "Discrete Math Syllabus"
```

### Grade a submission:

```bash
python gradingBot.py \
    --session-id "discrete_math_ta_001" \
    --grade \
    --question "Prove that if n is even, then n² is even." \
    --answer "student_answer.txt" \
    --max-points 10.0 \
    --assignment "HW1"
```

## API Reference

### `GradingBot(session_id, model="4o-mini", rag_threshold=0.3, rag_k=5, temperature=0.0)`

Initialize the grading bot.

**Parameters:**
- `session_id` (str): Unique identifier for this TA/Professor's session
- `model` (str): LLM model to use (default: "4o-mini")
- `rag_threshold` (float): Similarity threshold for RAG retrieval (default: 0.3)
- `rag_k` (int): Number of chunks to retrieve (default: 5)
- `temperature` (float): Temperature for LLM generation (default: 0.0)

### Document Upload Methods

- `upload_syllabus(file_path, description=None)`
- `upload_homework_assignment(file_path, assignment_name=None, description=None)`
- `upload_homework_solution(file_path, assignment_name=None, description=None)`
- `upload_lecture_material(file_path, lecture_name=None, description=None)`
- `upload_textbook(file_path, description=None)`

### Grading Methods

- `grade_submission(question, student_answer, max_points=None, rubric=None, assignment_name=None)`
  - Returns: `{"score": float, "max_points": float, "feedback": str, "rag_context_used": str, "raw_response": dict}`
  
- `grade_from_file(question, student_answer_file, max_points=None, rubric=None, assignment_name=None)`
  - Same as `grade_submission` but reads answer from a file

### Utility Methods

- `wait_for_processing(seconds=20)`: Wait for uploaded documents to be processed
- `get_uploaded_documents()`: Get list of uploaded documents

## How It Works

1. **Document Upload**: Course materials are uploaded to the LLM Proxy backend and associated with a session ID
2. **RAG Retrieval**: When grading, the bot queries the course materials using RAG to find relevant context
3. **Grading**: The LLM grades the submission using:
   - The student's answer
   - The question/problem statement
   - Relevant context from course materials (via RAG)
   - Optional rubric and point values
4. **Feedback**: Returns detailed feedback and scores based on the course materials

## Notes

- Documents must be text-based PDFs
- Each TA/Professor should use a unique `session_id` to maintain separate document collections
- After uploading documents, wait 20+ seconds for processing before grading
- The system assumes users (TAs/Professors) are experts and can review/override LLM grading decisions
- This is a prototype designed for Discrete Math but can be adapted for other courses

## Example

See `example_usage.py` for a complete working example.

## Installation

### Install Dependencies

```bash
# Install llmproxy package
cd py/
pip install .

# Install Streamlit for web interface (optional but recommended)
pip install streamlit
```

### Run Streamlit App

```bash
cd py/
streamlit run gradingBot/app.py
```

The app will open in your browser at `http://localhost:8501`

