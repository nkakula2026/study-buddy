from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from study_buddy.flashcards import generate_flashcards, load_flashcards, save_flashcards
from study_buddy.materials import MATERIALS_DIR, ensure_materials_dir, list_pdfs, pdf_document_block
from study_buddy.quiz import generate_quiz, grade_answer
from study_buddy.summarize import summarize

console = Console()


def read_pasted_text():
    console.print("Paste your study material below. Type [bold]END[/bold] on its own line to finish:")
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
        console.print(f"\n[yellow]No PDFs found.[/yellow] Drop a PDF file into:\n  {MATERIALS_DIR}\nand try again.")
        return None
    table = Table(title="Available PDFs", show_header=True, header_style="bold cyan")
    table.add_column("#", justify="right")
    table.add_column("Filename")
    for i, name in enumerate(pdfs, 1):
        table.add_row(str(i), name)
    console.print(table)
    choice = Prompt.ask("Pick a number").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(pdfs):
        return pdfs[int(choice) - 1]
    console.print("[red]Invalid selection.[/red]")
    return None


def get_material():
    console.print("\n[bold]Where's your material coming from?[/bold]")
    console.print("  1. Paste text")
    console.print("  2. PDF from the materials/ folder")
    choice = Prompt.ask(">").strip()
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
        console.print("[yellow]No material provided.[/yellow]")
        return None
    return text


def run_summarize(content):
    with console.status("[bold green]Summarizing..."):
        result = summarize(content)
    console.print(Panel(Markdown(result), title="Summary", border_style="green"))


def run_quiz(content):
    num = IntPrompt.ask("How many questions?", default=5)
    with console.status("[bold green]Generating quiz..."):
        questions = generate_quiz(content, num)
    score = 0
    for i, q in enumerate(questions, 1):
        console.print(Panel(q["question"], title=f"Question {i}", border_style="cyan"))
        if q["type"] == "mcq" and q["options"]:
            for opt in q["options"]:
                console.print(f"  - {opt}")
        user_answer = Prompt.ask("Your answer")
        with console.status("[bold green]Grading..."):
            result = grade_answer(q["question"], q["answer"], user_answer)
        if result["correct"]:
            score += 1
            console.print(f"[bold green]Correct![/bold green] {result['feedback']}")
        else:
            console.print(f"[bold red]Not quite.[/bold red] Correct answer: {q['answer']}. {result['feedback']}")
    console.print(Panel(f"Score: {score}/{len(questions)}", border_style="magenta"))


def run_flashcards(content):
    num = IntPrompt.ask("How many flashcards?", default=10)
    with console.status("[bold green]Generating flashcards..."):
        cards = generate_flashcards(content, num)
    all_cards = save_flashcards(cards)
    console.print(f"[green]Saved {len(cards)} flashcards to flashcards.json ({len(all_cards)} total).[/green]")
    if Prompt.ask("Review them now?", choices=["y", "n"], default="n") == "y":
        review_flashcards(cards)


def review_flashcards(cards):
    for i, c in enumerate(cards, 1):
        console.print(Panel(c["front"], title=f"Card {i}", border_style="blue"))
        Prompt.ask("(press Enter to reveal answer)", default="", show_default=False)
        console.print(f"[bold]Answer:[/bold] {c['back']}\n")


def main():
    console.print(Panel("[bold cyan]AI Study Buddy[/bold cyan]", expand=False))
    while True:
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("  1. Summarize study material")
        console.print("  2. Generate & take a quiz")
        console.print("  3. Generate flashcards")
        console.print("  4. Review saved flashcards")
        console.print("  5. Quit")
        choice = Prompt.ask(">").strip()

        if choice == "5" or choice.lower() in ("q", "quit", "exit"):
            console.print("[cyan]Goodbye![/cyan]")
            break

        if choice == "4":
            cards = load_flashcards()
            if not cards:
                console.print("[yellow]No flashcards saved yet.[/yellow]")
            else:
                review_flashcards(cards)
            continue

        if choice not in ("1", "2", "3"):
            console.print("[red]Invalid choice.[/red]")
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
        console.print("\n[cyan]Goodbye![/cyan]")
    except Exception as e:
        message = str(e).lower()
        if "api_key" in message or "authentication" in message or "x-api-key" in message:
            console.print("\n[red]Couldn't authenticate with the Anthropic API.[/red]")
            console.print("Set your key first: export ANTHROPIC_API_KEY=your-key-here")
        else:
            raise
