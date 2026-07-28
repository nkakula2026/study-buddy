from .client import get_client, MODEL


def summarize(content):
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are a study assistant. Summarize the given study material into "
            "clear, well-organized key points a student can review quickly. Use "
            "short bullet points grouped under headings where it helps."
        ),
        messages=[{"role": "user", "content": content}],
    )
    return next(b.text for b in response.content if b.type == "text")
