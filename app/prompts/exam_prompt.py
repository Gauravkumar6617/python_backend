def exam_prompt(topic, difficulty, total_questions, q_types):
    # Mapping and rules for all possible types
    type_constraints = {
        "MCQ": "- Standard 4-option multiple choice.",
        "Passage": "- Use 'passage_text' for a 300-word context. Link multiple questions to this same 'passage_text'.",
        "Figure Logic": """- MANDATORY: Use 'matrix' field (flat list of 9 symbols). 
          - Symbols ONLY: ↑, ↓, ←, →, ↗, ↘, ↙, ↖, ⚪, ⚫, ⬔, ⬓, ⬒, ⬑, ⬏, 🧩, ⬖, ⬗, ➕, ➖, ✖, ➗, ❓.
          - NO text descriptions of shapes allowed in the matrix.""",
        "Short Answer": "- Provide a 'question' and a 'model_answer'. Set 'options' and 'answer' to null."
    }

    selected_rules = "\n".join([type_constraints[t] for t in q_types if t in type_constraints])

    return f"""
    ROLE: Lead Examiner for UPSC/SSC (Group A Standards).
    TASK: Generate {total_questions} questions for Topic: {topic}.
    DIFFICULTY: {difficulty}.
    TYPES TO INCLUDE: {q_types}.

    STRICT RULES:
    1. DISTRIBUTION: Ensure a balanced mix of {q_types}. Interleave types; do not put all of one type together.
    2. CONTENT RULES:
    {selected_rules}
    3. VALIDATION: Every question must have a 'type' and 'explanation'.
    4. FORMAT: Return ONLY a valid JSON array. Do not include markdown preamble.

    JSON SCHEMA:
    {{
        "type": "Passage | Figure Logic | MCQ | Short Answer",
        "question": "Clear and concise question text",
        "options": ["A", "B", "C", "D"] or null,
        "answer": "Exact string matching one option" or null,
        "explanation": "Step-by-step logic",
        "passage_text": "Required for Passage type",
        "matrix": ["symbol1", ..., "symbol9"] for Figure Logic,
        "model_answer": "Required for Short Answer type"
    }}
    """