import json
import os

from .client import get_client, MODEL

FLASHCARD_SCHEMA = {
    "type": "object",
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "front": {"type": "string"},
                    "back": {"type": "string"},
                },
                "required": ["front", "back"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["cards"],
    "additionalProperties": False,
}

FLASHCARDS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "flashcards.json")


def generate_flashcards(content, num_cards=10):
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=(
            f"Create exactly {num_cards} flashcards from the study material. "
            "Each card's 'front' is a short question or term, and 'back' is the "
            "concise answer or definition."
        ),
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": FLASHCARD_SCHEMA}},
    )
    block = next(b.text for b in response.content if b.type == "text")
    return json.loads(block)["cards"]


def load_flashcards():
    if os.path.exists(FLASHCARDS_FILE):
        with open(FLASHCARDS_FILE) as f:
            return json.load(f)
    return []


def save_flashcards(new_cards):
    existing = load_flashcards()
    existing.extend(new_cards)
    with open(FLASHCARDS_FILE, "w") as f:
        json.dump(existing, f, indent=2)
    return existing
