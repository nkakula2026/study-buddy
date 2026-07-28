import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-5"

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client
