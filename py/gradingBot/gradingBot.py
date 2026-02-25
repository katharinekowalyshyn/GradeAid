"""
Grading Bot - A prototype grading system using LLM Proxy with RAG.

This system allows TAs/Professors to:
1. Upload course materials (syllabus, assignments, solutions, lectures, textbook)
2. Grade student submissions using RAG to retrieve relevant context
3. Get detailed feedback and scores based on course materials

Users are distinguished by session_id to maintain separate document collections.
"""
from .tools import calculator_tool, web_api_tool
from pathlib import Path
from typing import Dict, List, Optional, Union
from time import sleep
import re
from llmproxy import LLMProxy
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import re

load_dotenv()


class GradingBot:
    """
    A grading bot that uses LLM Proxy with RAG to grade student submissions
    based on course materials.
    """
    
    def __init__(
        self,
        session_id: str,
        model: str = "4o-mini",
    ):
        """
        Initialize the GradingBot.
        
        Args:
            session_id: Unique identifier for this TA/Professor's session.
                       Documents uploaded will be associated with this session.
            model: LLM model to use for grading (default: "4o-mini")
        """
        self.client = LLMProxy()
        self.session_id = session_id
        self.model = model
        # Fixed RAG and temperature parameters
        self.rag_threshold = 0.3
        self.rag_k = 2
    
        self.temperature = 0.0
        
        # Track uploaded documents
        self.uploaded_docs: List[Dict[str, str]] = []

        self.tools = {
            "calculator": calculator_tool,
            "web_api": web_api_tool
        }

    def use_tool(self, tool_name: str, **kwargs) -> Dict:
        """
        Execute a registered tool by name.
        """
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            return self.tools[tool_name](**kwargs)
        except Exception as e:
            return {"error": str(e)}
    
    
    def upload_syllabus(self, file_path: Union[str, Path], description: Optional[str] = None) -> Dict:
        """
        Upload the course syllabus.
        
        Args:
            file_path: Path to the syllabus PDF file
            description: Optional description of the document
            
        Returns:
            Response from upload operation
        """
        result = self.client.upload_file(
            file_path=file_path,
            session_id=self.session_id,
            description=description or "Course Syllabus",
            strategy="smart"
        )
        if "error" not in result:
            self.uploaded_docs.append({
                "type": "syllabus",
                "path": str(file_path),
                "description": description or "Course Syllabus"
            })
        return result
    
    def upload_homework_assignment(
        self,
        file_path: Union[str, Path],
        assignment_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Upload a homework assignment.
        
        Args:
            file_path: Path to the assignment PDF file
            assignment_name: Name of the assignment (e.g., "HW1", "Homework 2")
            description: Optional description
            
        Returns:
            Response from upload operation
        """
        desc = description or f"Homework Assignment: {assignment_name or Path(file_path).stem}"
        result = self.client.upload_file(
            file_path=file_path,
            session_id=self.session_id,
            description=desc,
            strategy="smart"
        )
        if "error" not in result:
            self.uploaded_docs.append({
                "type": "homework_assignment",
                "path": str(file_path),
                "assignment_name": assignment_name,
                "description": desc
            })
        return result
    
    def upload_homework_solution(
        self,
        file_path: Union[str, Path],
        assignment_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Upload a homework solution/answer key.
        
        Args:
            file_path: Path to the solution PDF file
            assignment_name: Name of the assignment this solution corresponds to
            description: Optional description
            
        Returns:
            Response from upload operation
        """
        desc = description or f"Homework Solution: {assignment_name or Path(file_path).stem}"
        result = self.client.upload_file(
            file_path=file_path,
            session_id=self.session_id,
            description=desc,
            strategy="smart"
        )
        if "error" not in result:
            self.uploaded_docs.append({
                "type": "homework_solution",
                "path": str(file_path),
                "assignment_name": assignment_name,
                "description": desc
            })
        return result
    
    def upload_lecture_material(
        self,
        file_path: Union[str, Path],
        lecture_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Upload lecture slides or reading materials.
        
        Args:
            file_path: Path to the lecture PDF file
            lecture_name: Name/title of the lecture
            description: Optional description
            
        Returns:
            Response from upload operation
        """
        desc = description or f"Lecture Material: {lecture_name or Path(file_path).stem}"
        result = self.client.upload_file(
            file_path=file_path,
            session_id=self.session_id,
            description=desc,
            strategy="smart"
        )
        if "error" not in result:
            self.uploaded_docs.append({
                "type": "lecture_material",
                "path": str(file_path),
                "lecture_name": lecture_name,
                "description": desc
            })
        return result
    
    # def upload_textbook(self, file_path: Union[str, Path], description: Optional[str] = None) -> Dict:
    #     """
    #     Upload the course textbook.
        
    #     Args:
    #         file_path: Path to the textbook PDF file
    #         description: Optional description
            
    #     Returns:
    #         Response from upload operation
    #     """
    #     result = self.client.upload_file(
    #         file_path=file_path,
    #         session_id=self.session_id,
    #         description=description or "Course Textbook",
    #         strategy="smart"
    #     )
    #     if "error" not in result:
    #         self.uploaded_docs.append({
    #             "type": "textbook",
    #             "path": str(file_path),
    #             "description": description or "Course Textbook"
    #         })
    #     return result
    
    # Updated to automatically split up large uploads
    def upload_textbook(self, file_path: Union[str, Path], description: Optional[str] = None) -> Dict:
        """
        Upload the course textbook.
        
        Args:
            file_path: Path to the textbook PDF file
            description: Optional description
            
        Returns:
            Response from upload operation
        """
        # Debug
        print("DEBUG: upload_textbook received file size (MB):",
              Path(file_path).stat().st_size / (1024 * 1024))


        file_path = Path(file_path)

        chunks = self._split_large_pdfs(file_path)

        uploaded_chunk_names = []
        results = []

        for chunk in chunks:
            result = self.client.upload_file(
                file_path=chunk,
                session_id=self.session_id,
                description=description or "Course Textbook",
                strategy="smart"
            )

            results.append(result)

            if "error" not in result:
                uploaded_chunk_names.append(chunk.name)

        return {
            "result": results[-1] if results else {"error": "No upload"},
            "chunks": uploaded_chunk_names
        }

            

    

    # For PDFs exceeding max upload size, split automatically
    def _split_large_pdfs(self, filepath: Path, max_pages_per_chunk: int = 150):

        reader = PdfReader(str(filepath))
        total_pages = len(reader.pages)

        chunk_files = []

        for start in range(0, total_pages, max_pages_per_chunk):
            end = min(start + max_pages_per_chunk, total_pages)
            writer = PdfWriter()

            for i in range(start, end): 
                writer.add_page(reader.pages[i])

            temp_file = Path(tempfile.gettempdir()) / f"{filepath.stem}_part{start//max_pages_per_chunk + 1}.pdf"

            with open(temp_file, "wb") as f:
                writer.write(f)

            chunk_files.append(temp_file)

        return chunk_files



    def wait_for_processing(self, seconds: int = 20):
        """
        Wait for uploaded documents to be processed by the backend.
        
        Args:
            seconds: Number of seconds to wait (default: 20)
        """
        sleep(seconds)
    
    def _format_rag_context(self, rag_context: List[Dict]) -> str:
        """
        Format RAG context into a readable string for the LLM.
        
        Args:
            rag_context: List of retrieved context chunks from RAG
            
        Returns:
            Formatted context string
        """
        if not rag_context:
            return ""
        
        context_string = "The following context from course materials may be helpful:\n\n"
        
        for i, collection in enumerate(rag_context, 1):
            doc_summary = collection.get('doc_summary', '')
            chunks = collection.get('chunks', [])
            
            if doc_summary:
                context_string += f"[Document {i}]: {doc_summary}\n"
            
            for j, chunk in enumerate(chunks, 1):
                context_string += f"  {i}.{j}. {chunk}\n"
            
            context_string += "\n"
        
        return context_string
    
    def grade_submission(
        self,
        question: str,
        student_answer: str,
        max_points: Optional[float] = None,
        rubric: Optional[str] = None,
        assignment_name: Optional[str] = None,
        wait_after_upload: bool = True
    ) -> Dict:
        """
        Grade a student submission using RAG to retrieve relevant course materials.
        
        Args:
            question: The question or problem statement
            student_answer: The student's answer to grade
            max_points: Maximum points for this question (optional)
            rubric: Additional grading rubric or instructions (optional)
            assignment_name: Name of the assignment (for context)
            wait_after_upload: Whether to wait after uploading (if student_answer is a file)
            
        Returns:
            Dictionary containing:
                - score: Numerical score (if max_points provided)
                - feedback: Detailed feedback
                - rag_context_used: Context retrieved from course materials
                - raw_response: Full LLM response
        """



        # Build the grading query with context
        query_parts = []
        
        if assignment_name:
            query_parts.append(f"Assignment: {assignment_name}")
        
        query_parts.append(f"Question: {question}")
        query_parts.append(f"\nStudent Answer:\n{student_answer}")
        
        if rubric:
            query_parts.append(f"\nGrading Rubric:\n{rubric}")
        
        if max_points:
            query_parts.append(f"\nMaximum Points: {max_points}")
        
        query = "\n".join(query_parts)

        #tool detection
        tool_result = self._run_tools_for_submission(student_answer)
        tool_context = tool_result["tool_context"]
        tools_used = tool_result["tools_used"]

        full_query_parts = []

        if tool_context:
            full_query_parts.append("TOOL VERIFICATION RESULTS:\n" + tool_context)

        full_query_parts.append(query)

        full_query = "\n\n".join(full_query_parts)
        
        system_prompt = """
You are an expert teaching assistant grading a student submission.

GRADING RULES (follow strictly):
- Compare the student's answers to the official solutions in the course materials. Assign points based on what is actually correct or incorrect.
- Grade by problem or section: assign points per part (e.g. Problem 1: 8/10, Problem 2a: 5/5, Problem 2b: 0/5), then sum to get the total score. Do NOT give the same score to every submission unless it makes sense to do so.
- Vary scores: strong submissions should get high scores (e.g. 90–100), partial work should get mid scores (e.g. 50–75), weak or wrong answers should get low scores (e.g. 0–40). Never default.
- Use the maximum points given; the final SCORE must be a real number between 0 and that maximum, reflecting correctness.

You MUST:
- Use retrieved course materials (RAG context) when relevant.
- Cite sources using this format: [Source X]
- Only cite sources that appear in retrieved materials.
- If no course material is relevant, state: "No relevant textbook material found."

You must remain strictly focused on:
- The assignment question
- The student's submission
- The provided rubric

If the query is unrelated to grading, mathematics, or course content,
refuse the request.

If the user asks something unrelated to the assignment or course materials,
respond with:

"This request is outside the scope of the assignment and course materials."

Format response as:

SCORE: X/Y
FEEDBACK:
Detailed explanation.

If RAG context is provided:
- Quote exact short phrases from the retrieved material.
- Do not invent source numbers.
- Do not fabricate citations.
- Include page number or source filename if available.
- Only reference content that appears in the retrieved context.
- If no RAG context is provided, explicitly state:
  "No relevant textbook material found."

"""

        response = self.client.generate(
            model=self.model,
            system=system_prompt,
            query=full_query,
            temperature=self.temperature,
            session_id=self.session_id,
            rag_usage=True,   #Rag retention enabled 
            rag_threshold=self.rag_threshold,
            rag_k=self.rag_k
        )

        #Debugging
        print("FULL RESPONSE:", response)
        print("RESPONSE KEYS:", response.keys())

        if "error" in response:
            return {"error": response["error"]}

        result_text = response.get("result", "")

        score = None
        if max_points and result_text:
            match = re.search(r'(\d+\.?\d*)\s*/\s*(\d+\.?\d*)', result_text)
            if match:
                score = float(match.group(1))

        rag_context = response.get("rag_context", [])
        if rag_context:
            rag_context = rag_context.strip()
        rag_sources = response.get("sources", [])

        return {
            "score": score,
            "max_points": max_points,
            "feedback": result_text,
            "tools_used": tools_used,
            "rag_enabled": True,
            "rag_context_used": rag_context,
            "rag_sources": rag_sources,
            "raw_response": response
        }
    

    ## New method to generate interactive response
    def generate_interactive_response(
        self,
        conversation: list[dict],
        assignment_name: str = None,
        rubric: str = None
    ) -> dict:
        """
        Generate an interactive response to a student's submission, 
        using RAG context and conversation history.

        Args:
            conversation: List of messages in order, each dict with:
                - 'role': 'student' or 'bot'
                - 'content': the message text
            assignment_name: Optional assignment name for context

        Returns:
            Dict containing:
                - response_text: Bot's message
                - rag_context_used: Context retrieved from course materials
                - raw_response: Full LLM response
        """

        if not conversation:
            return {"error": "Conversation is empty."}

        # Build combined query
        student_messages = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation]
        )

        query_parts = []
        if assignment_name:
            query_parts.append(f"Assignment: {assignment_name}")

        query_parts.append(student_messages)
        query = "\n\n".join(query_parts)

        # Tool detection for latest student message
        latest_student_msg = conversation[-1]['content'] if conversation[-1]['role'] == 'student' else ""
        tool_context = self._run_tools_for_submission(latest_student_msg)

        # Retrieve relevant RAG context
        rag_result = self.client.retrieve(
            query=query,
            session_id=self.session_id,
            rag_threshold=self.rag_threshold,
            rag_k=self.rag_k
        )

        if "error" in rag_result:
            return {
                "error": f"RAG retrieval failed: {rag_result['error']}",
                "raw_response": rag_result
            }

        rag_context = rag_result.get("rag_context", []) if isinstance(rag_result, dict) else []
        formatted_context = self._format_rag_context(rag_context)

        # Build system prompt for interactive tutoring
        system_prompt = """You are an expert teaching assistant for a Discrete Math course.
    Your goal is to interactively guide the student:

    - Evaluate correctness, clarity, and logic of their answer
    - Ask probing questions to make the student think deeper
    - Provide hints or counterexamples if the answer is partially wrong
    - Avoid giving the full solution away
    - Encourage the student and explain reasoning clearly

    Format the response as plain text. Do not include numerical scores."""
        
        # Combine all context
        full_query_parts = []
        if formatted_context:
            full_query_parts.append(formatted_context)
        if tool_context:
            full_query_parts.append("\nTOOL VERIFICATION RESULTS:\n" + tool_context)
        full_query_parts.append(query)

        full_query = "\n\n".join(full_query_parts)

        # Generate response using LLM
        response = self.client.generate(
            model=self.model,
            system=system_prompt,
            query=full_query,
            temperature=0.5,  # Slightly more creative for interaction
            session_id=self.session_id,
            rag_usage=False
        )

        response_text = response.get("result", "")

        return {
            "response_text": response_text,
            "rag_context_used": formatted_context if formatted_context else "No relevant context retrieved",
            "raw_response": response
        }
    
    def grade_from_file(
        self,
        question: str,
        student_answer_file: Union[str, Path],
        max_points: Optional[float] = None,
        rubric: Optional[str] = None,
        assignment_name: Optional[str] = None
    ) -> Dict:
        """
        Grade a student submission from a file.
        
        Args:
            question: The question or problem statement
            student_answer_file: Path to file containing student's answer
            max_points: Maximum points for this question (optional)
            rubric: Additional grading rubric or instructions (optional)
            assignment_name: Name of the assignment (for context)
            
        Returns:
            Same as grade_submission()
        """
        path = Path(student_answer_file)
        if not path.exists():
            return {"error": f"File not found: {path}"}
        
        # Read the file content
        try:
            with open(path, 'r', encoding='utf-8') as f:
                student_answer = f.read()
        except Exception as e:
            return {"error": f"Error reading file: {e}"}
        
        return self.grade_submission(
            question=question,
            student_answer=student_answer,
            max_points=max_points,
            rubric=rubric,
            assignment_name=assignment_name
        )
    
    def get_uploaded_documents(self) -> List[Dict[str, str]]:
        """
        Get list of documents that have been uploaded to this session.
        
        Returns:
            List of document metadata dictionaries
        """
        return self.uploaded_docs.copy()
    
    def _run_tools_for_submission(self, student_answer: str) -> str:
        """
        Automatically detects when tools are needed.
        Returns tool-generated context to assist grading.
        """
        tool_context = ""

        tools_used = []

        #Calculator detection
        math_matches = re.findall(r"\b\d+\s*[\+\-\*\/\^]\s*\d+\b", student_answer)

        for expr in math_matches:
            result = self.use_tool("calculator", expression=expr.replace("^", "**"))
            if "result" in result:
                tool_context += f"\nVerified Calculation: {expr} = {result['result']}\n"
                if "calculator" not in tools_used:
                    tools_used.append("calculator")

        #URL detection
        urls = re.findall(r"(https?://[^\s]+)", student_answer)

        for url in urls:
            web_result = self.use_tool("web_api", query=url)
            if "result" in web_result:
                tool_context += f"\nWeb Verification Result:\n{web_result['result'][:500]}\n"
                if "web_api" not in tools_used:
                    tools_used.append("web_api")

        #research style claims
        trigger_keywords = ["according to", "research shows", "study", "wikipedia"]

        if any(keyword in student_answer.lower() for keyword in trigger_keywords):
            web_result = self.use_tool("web_api", query=student_answer[:200])
            if "result" in web_result:
                tool_context += f"\nWeb Fact Check:\n{web_result['result'][:500]}\n"
                if "web_api" not in tools_used:
                    tools_used.append("web_api")

        return {
            "tool_context": tool_context.strip(),
            "tools_used": tools_used
        }

        


# Example usage and CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Grading Bot - Grade student submissions using LLM with RAG")
    parser.add_argument("--session-id", type=str, required=True,
                       help="Session ID for this TA/Professor (e.g., 'ta_john_doe')")
    parser.add_argument("--upload", type=str, choices=["syllabus", "assignment", "solution", "lecture", "textbook"],
                       help="Upload a document type")
    parser.add_argument("--file", type=str, help="Path to PDF file to upload")
    parser.add_argument("--description", type=str, help="Description for uploaded document")
    parser.add_argument("--grade", action="store_true", help="Grade a submission")
    parser.add_argument("--question", type=str, help="Question/problem statement")
    parser.add_argument("--answer", type=str, help="Student's answer (text or file path)")
    parser.add_argument("--max-points", type=float, help="Maximum points for the question")
    parser.add_argument("--rubric", type=str, help="Grading rubric (text or file path)")
    parser.add_argument("--assignment", type=str, help="Assignment name")
    parser.add_argument("--model", type=str, default="4o-mini", help="LLM model to use")
    parser.add_argument("--wait", type=int, default=20, help="Seconds to wait after upload")
    
    args = parser.parse_args()
    
    bot = GradingBot(session_id=args.session_id, model=args.model)
    
    if args.upload:
        if not args.file:
            print("Error: --file required when using --upload")
            exit(1)
        
        print(f"Uploading {args.upload} from {args.file}...")
        
        if args.upload == "syllabus":
            result = bot.upload_syllabus(args.file, args.description)
        elif args.upload == "assignment":
            result = bot.upload_homework_assignment(args.file, args.assignment, args.description)
        elif args.upload == "solution":
            result = bot.upload_homework_solution(args.file, args.assignment, args.description)
        elif args.upload == "lecture":
            result = bot.upload_lecture_material(args.file, args.assignment, args.description)
        elif args.upload == "textbook":
            result = bot.upload_textbook(args.file, args.description)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            exit(1)
        else:
            print(f"Success! Waiting {args.wait} seconds for processing...")
            bot.wait_for_processing(args.wait)
            print("Upload complete!")
    
    elif args.grade:
        if not args.question or not args.answer:
            print("Error: --question and --answer required when using --grade")
            exit(1)
        
        # Check if answer is a file path
        answer_path = Path(args.answer)
        if answer_path.exists():
            student_answer = answer_path.read_text(encoding='utf-8')
        else:
            student_answer = args.answer
        
        # Check if rubric is a file path
        rubric_text = None
        if args.rubric:
            rubric_path = Path(args.rubric)
            if rubric_path.exists():
                rubric_text = rubric_path.read_text(encoding='utf-8')
            else:
                rubric_text = args.rubric
        
        print("Grading submission...")
        result = bot.grade_submission(
            question=args.question,
            student_answer=student_answer,
            max_points=args.max_points,
            rubric=rubric_text,
            assignment_name=args.assignment
        )
        
        if "error" in result:
            print(f"Error: {result['error']}")
            exit(1)
        
        print("\n" + "="*60)
        print("GRADING RESULT")
        print("="*60)
        if result.get("score") is not None:
            print(f"\nSCORE: {result['score']:.2f} / {result['max_points']:.2f} points")
        print(f"\nFEEDBACK:\n{result['feedback']}")
        print("\n" + "="*60)
        print(f"\nRAG Context Used:\n{result['rag_context_used']}")
    
    else:
        print("Uploaded documents:")
        for doc in bot.get_uploaded_documents():
            print(f"  - {doc['type']}: {doc.get('description', 'N/A')}")

