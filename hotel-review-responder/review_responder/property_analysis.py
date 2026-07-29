from .client import MODEL, get_client

SYSTEM_PROMPT = """You are a hospitality business analyst. Given a hotel's name and location, \
research its public guest reviews across major travel and review platforms (Google, TripAdvisor, \
Booking.com, Expedia, Yelp, and any other relevant sites you can find) using web search and web \
fetch. Read enough reviews across platforms and star ratings to form a representative picture, \
not just the first few results you see.

Produce a report in exactly this markdown structure:

## Overview
Which platforms you found reviews on, roughly how many reviews you looked at, and the overall \
sentiment/rating impression.

## What's Working Well
The recurring strengths guests mention. For each, give 1-2 short supporting quotes or paraphrases \
and which platform(s) they came from.

## Where the Property Is Falling Short
The recurring complaints or pain points. Group related issues together (e.g. "front desk & \
check-in" rather than listing every instance separately). For each, give 1-2 short supporting \
quotes or paraphrases and which platform(s) they came from.

## Recommendations
Concrete, actionable steps to address the weaknesses and reinforce the strengths, ordered by \
likely impact vs. effort — quick wins first, larger investments later.

## Sources
The review pages/URLs you actually read.

Be specific and grounded in what guests actually said — never invent statistics or quotes. If you \
can only find reviews on some platforms, say so plainly rather than guessing at the rest."""


def analyze_property(hotel_name, location, max_continuations=5):
    """Returns (report_text, truncated) or (None, False) if refused."""
    client = get_client()
    user_content = (
        f"Hotel name: {hotel_name}\n"
        f"Location: {location}\n\n"
        "Research this hotel's public reviews and produce the report."
    )
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 15},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 15},
    ]

    messages = [{"role": "user", "content": user_content}]
    response = None
    for _ in range(max_continuations + 1):
        with client.messages.stream(
            model=MODEL,
            max_tokens=32000,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        # Server-tool round trips (search/fetch) can hit the API's internal
        # iteration limit mid-turn; re-send to let it resume automatically.
        if response.stop_reason != "pause_turn":
            break
        messages = [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": response.content},
        ]

    if response.stop_reason == "refusal":
        return None, False

    # Claude may emit short preamble/transition text between tool calls (e.g.
    # "Let me also check TripAdvisor...") — the final synthesized report is
    # always the last text block, not the first.
    text_blocks = [b.text for b in response.content if b.type == "text"]
    report = text_blocks[-1] if text_blocks else None
    truncated = response.stop_reason == "max_tokens"
    return report, truncated
