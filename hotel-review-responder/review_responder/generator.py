from .client import HOTEL_NAME, MODEL, get_client

SYSTEM_PROMPT = """You are the guest relations manager for {hotel_name}, writing public replies \
to guest reviews. Write a single reply to the review given by the user.

Guidelines:
- Thank the guest by name if one is given.
- Reference specific, concrete points from their review rather than replying generically.
- For positive reviews (4-5 stars): be warm and appreciative, and invite them back.
- For mixed or negative reviews (1-3 stars): acknowledge the specific issue without being \
defensive, apologize where appropriate, and briefly note what will be done about it or invite \
them to reach out directly to resolve it. Do not over-promise specific compensation.
- Keep the tone professional, sincere, and human — avoid corporate boilerplate and avoid \
sounding like a form letter.
- Length: 2-4 sentences. No subject line, no greeting salutation beyond addressing the guest, \
no sign-off with a title/signature block.
- Do not include internal or system XML tags in your response.
- Output only the reply text, nothing else.""".format(hotel_name=HOTEL_NAME)


def generate_reply(review):
    client = get_client()
    user_content = (
        f"Guest name: {review.get('guest_name') or 'not given'}\n"
        f"Rating: {review.get('rating') or 'not given'}/5\n"
        f"Review: {review['review_text']}"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        thinking={"type": "disabled"},
        output_config={"effort": "medium"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    if response.stop_reason == "refusal":
        return None
    return next(b.text for b in response.content if b.type == "text").strip()
