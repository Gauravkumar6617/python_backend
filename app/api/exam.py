from fastapi import APIRouter ,File ,Form ,UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import pdfplumber
import os 
import io
import logging
import re
from app.services.web_service import extract_text_from_url
from app.services.gemini_service import generate_questions_stream
from app.prompts.exam_prompt import exam_prompt
from app.services.pdf_service import extract_text_from_pdf
router = APIRouter(prefix="/exam", tags=["Exam"])

# Define the request structure
class ExamRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    total_questions: int = 10
    q_types: List[str] = ["MCQ"] # Default to standard MCQ

@router.post("/generate")
def generate_exam(request: ExamRequest):
    # Pass q_types to your prompt generator
    prompt = exam_prompt(
        request.topic, 
        request.difficulty, 
        request.total_questions, 
        request.q_types
    )
    return StreamingResponse(
        generate_questions_stream(prompt), 
        media_type="text/plain"
    )



@router.post("/generate-from-pdf")
async def generate_from_pdf(
    file: UploadFile = File(...),
    difficulty: str = Form(...),
    total_questions: int = Form(...),
    q_types: str = Form(...) 
):
    pdf_bytes = await file.read()
    context_text = extract_text_from_pdf(pdf_bytes)
    
    # MASTER PDF PROMPT: Forces JSON and kills conversational noise
    pdf_prompt = f"""
    [SYSTEM INSTRUCTION]: You are a JSON-only generator. No preamble. No conversational text.
    
    [CONTEXT]: 
    {context_text[:1000000]}
    
    [TASK]: 
    Generate exactly {total_questions} questions based ONLY on the context above.
    Difficulty: {difficulty}
    Allowed Types: {q_types}

    [OUTPUT RULES]:
    1. Start your response immediately with '[' and end with ']'.
    2. Do NOT use markdown code blocks (No ```json).
    3. Ensure every object has: "type", "question", "options", "answer", "explanation".
    4. For Figure Logic, use the "matrix" field with Unicode symbols ONLY.
    """
    
    return StreamingResponse(
        generate_questions_stream(pdf_prompt), 
        media_type="text/plain"
    )
logger = logging.getLogger(__name__)

def get_diagram_crop(page):
    """Detects only the actual diagram area by filtering out full-page artifacts."""
    # We only care about images and vector curves (dice/patterns)
    visuals = page.images + page.curves
    
    # Filter out elements that are likely watermarks or borders 
    # (e.g., anything wider than 80% of the page or very tiny)
    valid_visuals = [
        v for v in visuals 
        if (v['x1'] - v['x0']) < (page.width * 0.8) and (v['x1'] - v['x0']) > 20
    ]
    
    if valid_visuals:
        try:
            x0 = min(obj['x0'] for obj in valid_visuals)
            top = min(obj['top'] for obj in valid_visuals)
            x1 = max(obj['x1'] for obj in valid_visuals)
            bottom = max(obj['bottom'] for obj in valid_visuals)
            
            # Tighter padding to avoid catching text below the image
            padding = 5 
            bbox = (
                max(0, x0 - padding), 
                max(0, top - padding), 
                min(page.width, x1 + padding), 
                min(page.height, bottom + padding)
            )
            
            # Check if the cropped area is still too large (e.g., more than half the page)
            # If it's too big, it's probably not a single diagram
            if (bottom - top) > (page.height * 0.5):
                return None

            return page.within_bbox(bbox).to_image(resolution=300)
        except Exception as e:
            return None
    return None

# Ensure the static directory exists for images
IMG_DIR = "static/exam_images"
os.makedirs(IMG_DIR, exist_ok=True)

def normalize_text(text: str) -> str:
    """Cleans extracted PDF text for better LLM parsing."""
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\s+\n', '\n', text)
    return text.strip()

QUESTION_START_REGEX = re.compile(
    r'(?m)^(Q\.\d+|\d+[\.\)\s])'
)

def mark_question_starts(text: str) -> str:
    """
    Marks each question with:
    - @@QUESTION_START@@
    - @@QIDX:<global_index>@@
    Works with SSC PDFs where numbering may be 'Q.1', '1.', '1)', or just '1 '
    """
    pattern = re.compile(
        r'(?m)^(?:\s*Q\.\s*|\s*)(\d{1,3})[\.\)]?\s+'
    )

    counter = 0

    def replacer(match):
        nonlocal counter
        counter += 1
        printed_num = match.group(1)
        return f"\n@@QUESTION_START@@ @@QIDX:{counter}@@ Q.{printed_num} "

    return pattern.sub(replacer, text)


# -------------------------------
# API Endpoint
# -------------------------------

@router.post("/api/extract-pyq")
async def extract_pyq(
    file: UploadFile = File(...),
    questions_limit: int = Form(20),
    start_at: int = Form(1)
):
    """
    Extracts exactly `questions_limit` MCQs starting from the question
    labeled with number `start_at`, regardless of section resets.
    """

    pdf_bytes = await file.read()
    raw_text = ""

    # -------------------------------
    # PDF TEXT EXTRACTION
    # -------------------------------
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            page_text = normalize_text(text)
            page_text = mark_question_starts(page_text)

            raw_text += f"\n--- PAGE {i + 1} ---\n{page_text}"

    logger.info(
        f"🚀 PYQ Extraction | Anchor Q.{start_at} | Limit {questions_limit} | Size {len(raw_text)} chars"
    )

    # -------------------------------
    # 🔍 DEBUG 1: DETECT QUESTION LABELS
    # -------------------------------
    detected_numbers = re.findall(
        r'@@QUESTION_START@@\s*(?:Q\.)?(\d{1,3})\b',
        raw_text
    )

    unique_numbers = sorted(set(detected_numbers), key=int)

    logger.warning(
        f"🧩 Detected question numbers (sample): {unique_numbers[:30]} "
        f"(total={len(unique_numbers)})"
    )

    # -------------------------------
    # 🎯 DEBUG 2: CHECK ANCHOR EXISTENCE
    # -------------------------------
    anchor_pattern = rf'@@QUESTION_START@@\s*@@QIDX:{start_at}@@'
    anchor_found = re.search(anchor_pattern, raw_text)

    logger.warning(
        f"🎯 Anchor @@QUESTION_START@@ Q.{start_at} found: {bool(anchor_found)}"
    )

    # ❌ FAIL LOUDLY IF ANCHOR NOT FOUND
    if not anchor_found:
        logger.error(
            f"❌ Anchor question Q.{start_at} NOT FOUND in document"
        )
        return {
            "error": f"Anchor question Q.{start_at} not found in PDF",
            "detected_question_numbers": unique_numbers[:50]
        }

    # -------------------------------
    # MASTER EXTRACTION PROMPT (SAFE)
    # -------------------------------
    extraction_prompt = f"""
[SYSTEM ROLE]
You are a deterministic competitive-exam question extractor.
You NEVER explain.
You NEVER guess.
You NEVER hallucinate.
You ONLY extract what explicitly exists.

[TASK]
Extract exactly {questions_limit} multiple-choice questions starting from
the FIRST question whose numeric label equals {start_at}.

[QUESTION BOUNDARY — GUARANTEED]
Every question start is explicitly marked by:
@@QUESTION_START@@

You MUST treat this marker as the ONLY valid question boundary.

[ANCHOR RULE]
Begin extraction from the question whose @@QIDX equals {start_at}.

[SEQUENCE RULE]
Continue extracting subsequent @@QUESTION_START@@ blocks
until exactly {questions_limit} questions are extracted,
ignoring section headers and numbering resets.

[INVALID FILTER]
Ignore any question marker not followed by real question text.

[OPTIONS]
- Exactly 4 options per question
- Remove option labels (A/B/1/2)
- Preserve wording exactly

[ANSWER RULE]
- Use answer ONLY if explicitly present
- Otherwise:
  "answer": ""
  "explanation": ""

[HARD STOP]
STOP after exactly {questions_limit} questions.

[OUTPUT — JSON ONLY]
[
  {{
    "question": "Exact question text",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "answer": "",
    "explanation": ""
  }}
]

[DOCUMENT TEXT]
{raw_text}
"""

    logger.info(f"📦 Prompt size sent to LLM: {len(extraction_prompt)} chars")

    return StreamingResponse(
        generate_questions_stream(extraction_prompt),
        media_type="application/json"
    )


@router.post("/generate-from-web")
async def generate_from_web(request: ExamRequest): # Reuse your existing Pydantic model
    # 1. Extract text from URL
    try:
        context_text = await extract_text_from_url(request.topic) # Here 'topic' is the URL
    except Exception as e:
        return {"error": f"Failed to read URL: {str(e)}"}
    
    # 2. Construct the Strict JSON Prompt
    web_prompt = f"""
    [CONTEXT FROM WEBSITE]:
    {context_text}
    
    [TASK]:
    Generate {request.total_questions} questions based ONLY on the website content.
    Difficulty: {request.difficulty}
    Types: {request.q_types}

    [STRICT RULE]: Output ONLY a raw JSON array. Start with '['.
    """
    
    return StreamingResponse(
        generate_questions_stream(web_prompt), 
        media_type="text/plain"
    )