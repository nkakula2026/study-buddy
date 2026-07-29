import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-5"
HOTEL_NAME = os.environ.get("HOTEL_NAME", "our hotel")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client
