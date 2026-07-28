import json

from .client import get_client, MODEL

QUIZ_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "type": {"type": "string", "enum": ["mcq", "short_answer"]},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "answer": {"type": "string"},
                },
                "required": ["question", "type", "options", "answer"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}

GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "correct": {"type": "boolean"},
        "feedback": {"type": "string"},
    },
    "required": ["correct", "feedback"],
    "additionalProperties": False,
}


def generate_quiz(content, num_questions=5):
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=(
            f"Generate a quiz of exactly {num_questions} questions from the study "
            "material to test understanding, mixing multiple-choice and "
            "short-answer questions. For multiple-choice, put 4 options in "
            "'options' and the correct option's text in 'answer'. For "
            "short-answer, leave 'options' as an empty list and put the expected "
            "answer in 'answer'."
        ),
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": QUIZ_SCHEMA}},
    )
    block = next(b.text for b in response.content if b.type == "text")
    return json.loads(block)["questions"]


def grade_answer(question, correct_answer, user_answer):
    client = get_client()
    prompt = (
        f"Question: {question}\n"
        f"Expected answer: {correct_answer}\n"
        f"Student's answer: {user_answer}\n\n"
        "Grade whether the student's answer is correct, allowing for reasonable "
        "paraphrasing or synonyms. Give brief, encouraging feedback."
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": GRADE_SCHEMA}},
    )
    block = next(b.text for b in response.content if b.type == "text")
    return json.loads(block)
