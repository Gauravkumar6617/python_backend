from fastapi import APIRouter ,File ,Form ,UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import pdfplumber
import os 
import io
import logging
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
logger = logging.getLogger("exam_processor")
logger.setLevel(logging.INFO)

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

@router.post("/api/extract-pyq")
async def extract_pyq(file: UploadFile = File(...), questions_limit: int = Form(20)):
    pdf_bytes = await file.read()
    raw_text = ""

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                # We stop looking for images here and just gather text context
                raw_text += f"\n--- PAGE {i+1} ---\n{text}"

    # We update the prompt to force TEXTUAL representation of visual logic
    extraction_prompt = f"""
[SYSTEM]: You are a high-precision JSON API. No preamble. No conversational text.
[TASK]: Convert the provided SSC CGL PDF text into a JSON array of exactly {questions_limit} questions.

[STRICT QUANTITY RULE]:
- You MUST generate exactly {questions_limit} question objects.
- DO NOT generate more than {questions_limit} questions, even if the context contains hundreds.
- If you reach {questions_limit} questions, close the JSON array with ']' and STOP immediately.

[CRITICAL RULE FOR VISUAL LOGIC]: 
Convert all non-textual elements (figures, patterns, dice, matrices) into TEXT or ASCII art.
- Dice: Describe positions, e.g., "Dice Pos 1: Top(6), Front(2), Right(3)".
- Figure Series: Use ASCII or specific descriptions, e.g., "Step 1: Arrow pointing UP inside a circle -> Step 2: Arrow pointing RIGHT inside a square".
- Matrices/Grids: Draw using pipes and dashes, e.g., "| 5 | 8 | ? |".
- Visual Options: If options are figures, describe the differences, e.g., "Option 1: Triangle rotated 90 deg clockwise".

[OUTPUT SCHEMA]:
[
  {{
    "question": "Question text + ASCII diagram if applicable",
    "options": ["Option 1 content", "Option 2 content", "Option 3 content", "Option 4 content"],
    "answer": "Option X",
    "explanation": "Brief logical derivation"
  }}
]

[CONTEXT]: 
{raw_text[:700000]}
"""
    logger.info(f"🚀 Starting textual extraction for {questions_limit} questions")
    logger.debug(f"Raw text length: {len(raw_text)} characters")

# Log a snippet of the prompt to confirm no-image instructions are present
    logger.info(f"Prompt instruction check: {'NO IMAGES' in extraction_prompt}")

    return StreamingResponse(
    generate_questions_stream(extraction_prompt),
    media_type="text/plain"
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