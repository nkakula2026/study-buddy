from study_buddy.flashcards import generate_flashcards, load_flashcards, save_flashcards
from study_buddy.materials import MATERIALS_DIR, ensure_materials_dir, list_pdfs, pdf_document_block
from study_buddy.quiz import generate_quiz, grade_answer
from study_buddy.summarize import summarize


def read_pasted_text():
    print("Paste your study material below. Type END on its own line to finish:")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def choose_pdf():
    ensure_materials_dir()
    pdfs = list_pdfs()
    if not pdfs:
        print(f"\nNo PDFs found. Drop a PDF file into:\n  {MATERIALS_DIR}\nand try again.")
        return None
    print("\nAvailable PDFs:")
    for i, name in enumerate(pdfs, 1):
        print(f"  {i}. {name}")
    choice = input("Pick a number: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(pdfs):
        return pdfs[int(choice) - 1]
    print("Invalid selection.")
    return None


def get_material():
    print("\nWhere's your material coming from?")
    print("  1. Paste text")
    print("  2. PDF from the materials/ folder")
    choice = input("> ").strip()
    if choice == "2":
        filename = choose_pdf()
        if not filename:
            return None
        return [
            pdf_document_block(filename),
            {"type": "text", "text": "This is the study material."},
        ]
    text = read_pasted_text()
    if not text.strip():
        print("No material provided.")
        return None
    return text


def run_summarize(content):
    print("\nSummarizing...\n")
    print(summarize(content))


def run_quiz(content):
    num = input("How many questions? [5]: ").strip()
    num = int(num) if num.isdigit() else 5
    print("\nGenerating quiz...\n")
    questions = generate_quiz(content, num)
    score = 0
    for i, q in enumerate(questions, 1):
        print(f"\nQ{i}. {q['question']}")
        if q["type"] == "mcq" and q["options"]:
            for opt in q["options"]:
                print(f"  - {opt}")
        user_answer = input("Your answer: ")
        result = grade_answer(q["question"], q["answer"], user_answer)
        if result["correct"]:
            score += 1
            print("Correct! " + result["feedback"])
        else:
            print(f"Not quite. Correct answer: {q['answer']}. {result['feedback']}")
    print(f"\nScore: {score}/{len(questions)}")


def run_flashcards(content):
    num = input("How many flashcards? [10]: ").strip()
    num = int(num) if num.isdigit() else 10
    print("\nGenerating flashcards...\n")
    cards = generate_flashcards(content, num)
    all_cards = save_flashcards(cards)
    print(f"Saved {len(cards)} flashcards to flashcards.json ({len(all_cards)} total).")
    if input("Review them now? [y/N]: ").strip().lower() == "y":
        review_flashcards(cards)


def review_flashcards(cards):
    for i, c in enumerate(cards, 1):
        input(f"\nCard {i}: {c['front']}\n(press Enter to reveal answer)")
        print(f"Answer: {c['back']}")


def main():
    print("=== AI Study Buddy ===")
    while True:
        print("\nWhat would you like to do?")
        print("1. Summarize study material")
        print("2. Generate & take a quiz")
        print("3. Generate flashcards")
        print("4. Review saved flashcards")
        print("5. Quit")
        choice = input("> ").strip()

        if choice == "5" or choice.lower() in ("q", "quit", "exit"):
            print("Goodbye!")
            break

        if choice == "4":
            cards = load_flashcards()
            if not cards:
                print("No flashcards saved yet.")
            else:
                review_flashcards(cards)
            continue

        if choice not in ("1", "2", "3"):
            print("Invalid choice.")
            continue

        content = get_material()
        if content is None:
            continue

        if choice == "1":
            run_summarize(content)
        elif choice == "2":
            run_quiz(content)
        elif choice == "3":
            run_flashcards(content)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        message = str(e).lower()
        if "api_key" in message or "authentication" in message or "x-api-key" in message:
            print("\nCouldn't authenticate with the Anthropic API.")
            print("Set your key first: export ANTHROPIC_API_KEY=your-key-here")
        else:
            raise
