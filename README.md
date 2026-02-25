# Grading Bot

A prototype grading system that uses the `llmproxy` client with RAG (Retrieval Augmented Generation) to grade student submissions based on course materials.

## Features

- **Document Management**: Upload course materials (syllabus, assignments, solutions, lectures, textbooks). Large textbooks are automatically split into smaller chunks before upload.
- **RAG‑Powered Grading**: Automatically retrieves relevant context from uploaded course materials when grading.
- **Session‑Based**: Each TA/Professor uses a unique `session_id` to maintain separate document collections.
- **Interactive Web UI**: Streamlit app with tabs for uploading materials, grading a single submission, and interactive Q&A/tutoring.
- **Tool‑Augmented Grading**: Optional calculator and web lookup tools automatically verify basic computations and factual claims in student answers.
- **Detailed Feedback**: Returns a numeric score (when `max_points` is provided) plus rich natural‑language feedback and the RAG context used.

## Requirements

- Python 3.9+
- `llmproxy` package (this repo, installed from the `py/` directory with `pip install .`)
- `.env` file with:
  - `LLMPROXY_ENDPOINT`
  - `LLMPROXY_API_KEY`
- For the Streamlit frontend: `streamlit` (`pip install streamlit`)

**Environment note:**  
The underlying `LLMProxy` client reads environment variables from a `.env` file in the **current working directory**. The Streamlit app additionally loads `.env` from the `py/` directory. The simplest setup is:

```bash
cd py/
cp .env.example .env   # or create .env with your keys
```

and always run Python/Streamlit commands from within `py/`.

## Web Interface (Streamlit)

The easiest way to use the Grading Bot is through the Streamlit web interface.

### Launch the Web App

```bash
# IMPORTANT: Run from the py/ directory
cd py/
streamlit run gradingBot/gui_web.py

# Or use the provided script (also run from py/)
./gradingBot/run_app.sh
```

**Note:** You should run from the `py/` directory (not from inside `gradingBot/`) so that:

- Python can import the `gradingBot` and `llmproxy` packages, and  
- the `.env` file in `py/` is picked up correctly.

### What the web app provides

- **📚 Upload Materials** (tab: “Upload Course Materials”)
  - Upload syllabus, homework assignments, solutions, lecture slides, and textbooks (PDFs).
  - Textbooks are automatically split into multiple PDF chunks when they are large.
  - Previously uploaded documents for this session are listed in the “Uploaded Documents” section.

- **✏️ Grade Submission** (tab: “Grade Student Submission”)
  - Enter the assignment name, maximum points, question text, and student answer (typed/pasted or from a `.txt` file).
  - Optionally provide a free‑form grading rubric.
  - Displays:
    - Numeric score and percentage (if `max_points` is provided),
    - A coarse letter‑grade indicator,
    - Detailed feedback text,
    - RAG context used (expandable panel),
    - Any sources returned by the backend.

- **💬 Interactive Q&A** (tab: “Interactive Q&A”)
  - Students (or TAs) can paste an answer and optionally the question.
  - The bot responds as an interactive tutor: asking probing questions, suggesting counterexamples, and giving hints without revealing full solutions.
  - Conversation history is stored in the current Streamlit session.

> **Note:** Batch grading and JSON download are **not** currently implemented. The app focuses on single‑submission grading and interactive review.

## Quick Start (Python API)

### 1. Initialize the Grading Bot

Run your Python code from the `py/` directory so `.env` is found:

```python
from gradingBot.gradingBot import GradingBot

# Each TA/Professor should use a unique session_id
bot = GradingBot(
    session_id="discrete_math_ta_001",
    model="4o-mini",
)
```

Internally, the bot uses fixed RAG and temperature settings tuned for grading:

- `rag_threshold = 0.3`
- `rag_k = 2`
- `temperature = 0.0`

### 2. Upload Course Materials

```python
# Upload syllabus
bot.upload_syllabus("syllabus.pdf", "Discrete Math Syllabus")

# Upload homework assignment
bot.upload_homework_assignment(
    "hw1.pdf",
    assignment_name="HW1",
    description="Homework 1: Logic and Proofs",
)

# Upload homework solution
bot.upload_homework_solution(
    "hw1_solution.pdf",
    assignment_name="HW1",
    description="Homework 1 Solutions",
)

# Upload lecture materials
bot.upload_lecture_material(
    "lecture1.pdf",
    lecture_name="Lecture 1: Introduction",
)

# Upload textbook (large PDFs are split into multiple chunks automatically)
bot.upload_textbook("textbook.pdf", "Discrete Mathematics Textbook")

# Wait for documents to be processed on the backend
bot.wait_for_processing(seconds=20)
```

### 3. Grade a Student Submission

```python
result = bot.grade_submission(
    question="Prove that for any integer n, if n is even, then n² is even.",
    student_answer="Let n be an even integer. Then n = 2k for some integer k...",
    max_points=10.0,
    assignment_name="HW1",
    rubric="Evaluate: correctness, clarity, notation.",
)

print(f"Score: {result['score']} / {result['max_points']}")
print(f"Feedback:\n{result['feedback']}")
```

The returned `result` dictionary includes:

- `score` (`float | None`): Parsed numeric score if `max_points` was provided.
- `max_points` (`float | None`): Maximum points used for scoring.
- `feedback` (`str`): Full textual response from the model (includes score line and feedback).
- `tools_used` (`list[str]`): Names of tools used (e.g., `["calculator", "web_api"]`), if any.
- `rag_enabled` (`bool`): Whether RAG was enabled (always `True` for grading).
- `rag_context_used` (`str`): Textual RAG context string (or empty if none).
- `rag_sources` (`list`): Any source metadata returned by the backend.
- `raw_response` (`dict`): Full raw response from the `llmproxy` server.

## Command Line Interface

The grading bot also includes a CLI for quick operations.  
Run these commands from the `py/` directory so that imports and `.env` resolution work correctly.

### Upload a document

```bash
cd py/
python -m gradingBot.gradingBot \
    --session-id "discrete_math_ta_001" \
    --upload syllabus \
    --file "syllabus.pdf" \
    --description "Discrete Math Syllabus" \
    --wait 20
```

Valid `--upload` types are:

- `syllabus`
- `assignment`
- `solution`
- `lecture`
- `textbook`

### Grade a submission

```bash
cd py/
python -m gradingBot.gradingBot \
    --session-id "discrete_math_ta_001" \
    --grade \
    --question "Prove that if n is even, then n² is even." \
    --answer "student_answer.txt" \
    --max-points 10.0 \
    --assignment "HW1"
```

Notes:

- `--answer` can be either a path to a text file or a literal string. If the path exists, the file is read.
- `--rubric` can also be a path to a text file or an inline string.
- You can override the default model with `--model` (e.g., `--model gpt-4`).

## API Reference

### `GradingBot(session_id, model="4o-mini")`

Initialize the grading bot.

**Parameters:**

- `session_id` (`str`): Unique identifier for this TA/Professor's session. All uploads and RAG retrievals for this ID are kept separate from other sessions.
- `model` (`str`): LLM model name to use (default: `"4o-mini"`).

Internally, the bot sets:

- `rag_threshold` (`float`): `0.3`
- `rag_k` (`int`): `2`
- `temperature` (`float`): `0.0`

These are not currently configurable via the public constructor but can be changed in code if needed.

### Document upload methods

- `upload_syllabus(file_path, description=None)`
- `upload_homework_assignment(file_path, assignment_name=None, description=None)`
- `upload_homework_solution(file_path, assignment_name=None, description=None)`
- `upload_lecture_material(file_path, lecture_name=None, description=None)`
- `upload_textbook(file_path, description=None)`

All upload methods:

- Expect `file_path` to point to a PDF file.
- Call `LLMProxy.upload_file(...)` with `strategy="smart"`.
- Append basic metadata to `self.uploaded_docs` when the upload succeeds.

`upload_textbook(...)` additionally:

- Automatically splits large PDFs into chunks (default `max_pages_per_chunk=150`) and uploads each chunk separately.
- Returns a dictionary of the form:

```python
{
    "result": <last-upload-result-or-error>,
    "chunks": ["textbook_part1.pdf", "textbook_part2.pdf", ...],
}
```

### Grading methods

- `grade_submission(question, student_answer, max_points=None, rubric=None, assignment_name=None)`

  Builds a grading prompt that includes:

  - The assignment name (if provided),
  - The question text,
  - The student's answer,
  - An optional rubric,
  - Optional `max_points`.

  It also:

  - Runs built‑in tools (calculator and web API) on the student answer when appropriate.
  - Sends a grading‑specific system prompt with RAG enabled to the `llmproxy` backend.

  **Returns** a dictionary with the fields described in the “Quick Start” section:

  - `score`, `max_points`, `feedback`, `tools_used`, `rag_enabled`, `rag_context_used`, `rag_sources`, `raw_response`.

- `grade_from_file(question, student_answer_file, max_points=None, rubric=None, assignment_name=None)`

  Same as `grade_submission`, but reads the student answer from a text file on disk.

### Interactive tutoring

- `generate_interactive_response(conversation: list[dict], assignment_name: str | None = None, rubric: str | None = None) -> dict`

  Uses conversation history plus retrieved RAG context to generate an interactive tutoring response.  
  Each conversation item is a dict with:

  - `"role"`: `"student"` or `"bot"`
  - `"content"`: message text

  Returns:

  - `response_text`: Bot’s message for the latest turn.
  - `rag_context_used`: Human‑readable RAG context string (or `"No relevant context retrieved"`).
  - `raw_response`: Full response from `llmproxy`.

This method underpins the “Interactive Q&A” tab in the Streamlit UI.

### Utility methods

- `wait_for_processing(seconds=20)`: Sleep helper to give the backend time to index uploaded documents.
- `get_uploaded_documents() -> list[dict]`: Returns a shallow copy of the internal `uploaded_docs` list.

## How It Works

1. **Document upload**: Course materials are uploaded to the `llmproxy` backend and associated with a `session_id`.
2. **RAG retrieval**:
   - For grading calls, RAG is enabled directly through `LLMProxy.generate(...)` with `rag_usage=True`, `rag_threshold`, and `rag_k`.
   - For interactive Q&A, RAG context is fetched explicitly via `LLMProxy.retrieve(...)` and formatted for the model.
3. **Tool‑assisted analysis**:
   - The bot scans student answers for simple arithmetic expressions and URLs or “research‑style” claims.
   - It uses the built‑in `calculator` and `web_api` tools (DuckDuckGo Instant Answer API) to cross‑check those claims.
   - Tool results are added to the grading prompt so the model can see verified calculations or fact‑checks.
4. **Grading**:
   - The LLM receives:
     - The assignment name and question,
     - The student’s answer,
     - Optional rubric and `max_points`,
     - RAG context,
     - Tool output (if any).
   - It returns a textual response that starts with a `SCORE: X/Y` line followed by detailed feedback.
   - The `GradingBot` parses out the numeric score when possible.
5. **Feedback**:
   - The caller receives structured data plus the full textual feedback for display in a UI or for further processing.

## Notes

- Documents must be **text‑based PDFs** for best RAG performance.
- Each TA/Professor should use a unique `session_id` to maintain separate document collections.
- After uploading documents, waiting 20–30 seconds before grading is recommended so indexing can complete.
- The system assumes users (TAs/Professors) are experts and can review/override LLM grading decisions.
- Although tuned for a Discrete Math course, the system can be adapted to other subjects by changing the course materials.

## Installation

From the root of the repository:

```bash
cd py/

# Install the llmproxy client and gradingBot package
pip install .

# (Optional) Install Streamlit for the web interface
pip install streamlit
```

Then ensure your `.env` file in `py/` contains `LLMPROXY_ENDPOINT` and `LLMPROXY_API_KEY`.

### Run Streamlit App

```bash
cd py/
streamlit run gradingBot/gui_web.py
```

The app will open in your browser at `http://localhost:8501`.

