import argparse
import os
import re

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from review_responder.client import HOTEL_NAME
from review_responder.generator import generate_reply
from review_responder.property_analysis import analyze_property
from review_responder.reviews import (
    STATUS_APPROVED,
    STATUS_EDITED,
    STATUS_PENDING,
    STATUS_SKIPPED,
    load_drafts,
    load_reviews,
    save_drafts,
)

console = Console()

REVIEWS_PATH = "reviews.csv"
DRAFTS_PATH = "drafts.csv"


def cmd_generate(args):
    if not os.path.exists(args.reviews):
        console.print(f"[red]No reviews file found at {args.reviews}[/red]")
        return

    reviews = load_reviews(args.reviews)
    drafts = load_drafts(args.drafts)

    new_count = 0
    for review in reviews:
        if review["id"] in drafts:
            continue
        console.print(f"Generating draft reply for review [bold]{review['id']}[/bold]...")
        reply = generate_reply(review)
        if reply is None:
            console.print(f"  [yellow]Skipped (declined by safety classifier)[/yellow]")
            continue
        drafts[review["id"]] = {
            **review,
            "draft_reply": reply,
            "status": STATUS_PENDING,
            "final_reply": "",
        }
        new_count += 1

    save_drafts(args.drafts, drafts)
    console.print(f"\n[green]Generated {new_count} new draft(s).[/green] Saved to {args.drafts}")
    console.print(f"Run [bold]python main.py review[/bold] to approve or edit them.")


def cmd_review(args):
    drafts = load_drafts(args.drafts)
    pending = [d for d in drafts.values() if d["status"] == STATUS_PENDING]

    if not pending:
        console.print("[green]No pending drafts to review.[/green]")
        return

    console.print(f"[bold]{len(pending)}[/bold] draft(s) awaiting review for {HOTEL_NAME}.\n")

    for draft in pending:
        console.print(Panel(
            f"[bold]Guest:[/bold] {draft.get('guest_name') or 'unknown'}   "
            f"[bold]Rating:[/bold] {draft.get('rating') or '?'}/5   "
            f"[bold]Date:[/bold] {draft.get('date') or 'unknown'}\n\n"
            f"[italic]{draft['review_text']}[/italic]",
            title=f"Review {draft['id']}",
            border_style="cyan",
        ))
        console.print(Panel(draft["draft_reply"], title="Draft reply", border_style="magenta"))

        choice = Prompt.ask(
            r"\[a]pprove / \[e]dit / \[r]egenerate / \[s]kip / \[q]uit",
            choices=["a", "e", "r", "s", "q"],
            default="a",
        )

        if choice == "q":
            break
        elif choice == "s":
            draft["status"] = STATUS_SKIPPED
        elif choice == "r":
            console.print("Regenerating...")
            new_reply = generate_reply(draft)
            if new_reply:
                draft["draft_reply"] = new_reply
            console.print(Panel(draft["draft_reply"], title="New draft", border_style="magenta"))
            approve = Prompt.ask(r"Approve this version? \[y/n]", choices=["y", "n"], default="y")
            if approve == "y":
                draft["status"] = STATUS_APPROVED
                draft["final_reply"] = draft["draft_reply"]
        elif choice == "e":
            console.print("Enter your edited reply (single line):")
            edited = Prompt.ask(">")
            draft["status"] = STATUS_EDITED
            draft["final_reply"] = edited
        elif choice == "a":
            draft["status"] = STATUS_APPROVED
            draft["final_reply"] = draft["draft_reply"]

        drafts[draft["id"]] = draft
        save_drafts(args.drafts, drafts)
        console.print()

    console.print("[green]Progress saved.[/green]")


def cmd_list(args):
    drafts = load_drafts(args.drafts)
    if not drafts:
        console.print("No drafts yet. Run [bold]python main.py generate[/bold] first.")
        return

    table = Table(title=f"Draft status ({DRAFTS_PATH})", show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Guest")
    table.add_column("Rating")
    table.add_column("Status")

    counts = {}
    for draft in sorted(drafts.values(), key=lambda r: r["id"]):
        status = draft["status"]
        counts[status] = counts.get(status, 0) + 1
        table.add_row(draft["id"], draft.get("guest_name") or "-", draft.get("rating") or "-", status)

    console.print(table)
    console.print(", ".join(f"{status}: {count}" for status, count in counts.items()))


def cmd_analyze(args):
    hotel_name = args.hotel_name or Prompt.ask("Hotel name")
    location = args.location or Prompt.ask("Location (city, state/country)")

    console.print(
        f"\nResearching public reviews for [bold]{hotel_name}[/bold] ({location}) across the web — "
        "this can take a minute or two.\n"
    )
    with console.status("Searching and reading reviews...", spinner="dots"):
        report, truncated = analyze_property(hotel_name, location)

    if report is None:
        console.print(
            "[red]The request was declined by the safety classifier. Try rephrasing the hotel "
            "name/location.[/red]"
        )
        return

    console.print(Markdown(report))
    if truncated:
        console.print(
            "\n[yellow]Note: the report hit the output length limit and may be cut off "
            "mid-sentence at the end.[/yellow]"
        )

    slug = re.sub(r"[^a-z0-9]+", "-", hotel_name.lower()).strip("-") or "hotel"
    out_path = f"property_analysis_{slug}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    console.print(f"\n[green]Saved report to {out_path}[/green]")


def main():
    parser = argparse.ArgumentParser(description="Draft replies to hotel reviews with Claude.")
    parser.add_argument("--reviews", default=REVIEWS_PATH, help="Path to the input reviews CSV")
    parser.add_argument("--drafts", default=DRAFTS_PATH, help="Path to the drafts CSV")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("generate", help="Generate draft replies for new reviews")
    subparsers.add_parser("review", help="Interactively approve or edit pending drafts")
    subparsers.add_parser("list", help="Show draft status summary")

    analyze_parser = subparsers.add_parser(
        "analyze", help="Research a property's public reviews across the web and report on it"
    )
    analyze_parser.add_argument("--hotel-name", help="Hotel name")
    analyze_parser.add_argument("--location", help="City, state/country")

    args = parser.parse_args()
    {
        "generate": cmd_generate,
        "review": cmd_review,
        "list": cmd_list,
        "analyze": cmd_analyze,
    }[args.command](args)


if __name__ == "__main__":
    main()
