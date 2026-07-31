#!/usr/bin/env python3
"""Pre-flight content linter for Aviation Synergy Gamma decks.

Checks a source outline against the measured character budgets *before* you
spend generation credits. Gamma auto-fits type to content volume, so an
over-budget title is a guaranteed font shrink on export -- this catches it
while it is still free to fix.

Expected outline format (the same shape you feed Gamma with
cardSplit: "inputTextBreaks"):

    # Slide title                 <- title
    ## Subhead                    <- subhead
    - Body line                   <- body
    Plain paragraph text          <- also treated as body
    ---                           <- card break

Usage:
    python lint_content.py outline.md
    python lint_content.py outline.md --column half
    python lint_content.py outline.md --profile training_4x3
    python lint_content.py outline.md --json
"""

import argparse
import json
import re
import sys

import avs_tokens as T

CARD_BREAK = re.compile(r"^\s*---+\s*$")
TITLE = re.compile(r"^\s*#\s+(.*\S)\s*$")
SUBHEAD = re.compile(r"^\s*##\s+(.*\S)\s*$")
BULLET = re.compile(r"^\s*[-*+]\s+(.*\S)\s*$")


class Finding:
    def __init__(self, line_no, card_no, role, actual, limit, text):
        self.line_no = line_no
        self.card_no = card_no
        self.role = role
        self.actual = actual
        self.limit = limit
        self.text = text

    @property
    def over(self):
        return self.actual - self.limit

    def as_dict(self):
        return {
            "line": self.line_no,
            "card": self.card_no,
            "role": self.role,
            "chars": self.actual,
            "limit": self.limit,
            "over_by": self.over,
            "text": self.text,
        }

    def __str__(self):
        return (
            f"  line {self.line_no:>4}  card {self.card_no:>2}  {self.role:<8}"
            f"  {self.actual:>3}/{self.limit:<3} (+{self.over})  {self.text[:56]}"
        )


def strip_markup(text):
    """Length should reflect what renders, not the markdown around it."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)
    return text.strip()


def lint(lines, profile, column):
    ramp = profile["type_ramp"]
    body_limit = profile["columns"][column]["budget"]
    max_lines = profile["max_body_lines_per_block"]
    max_subheads = profile["max_subheads_per_card"]

    findings = []
    card_no = 1
    card_titles = 0
    subheads_in_card = 0
    body_run = 0
    cards_seen = 0

    def close_card(at_line):
        if subheads_in_card > max_subheads:
            findings.append(Finding(at_line, card_no, "density", subheads_in_card,
                                    max_subheads, "too many subheads on one card"))

    for idx, raw in enumerate(lines, start=1):
        if CARD_BREAK.match(raw):
            close_card(idx)
            card_no += 1
            card_titles = 0
            subheads_in_card = 0
            body_run = 0
            continue

        m = SUBHEAD.match(raw)
        if m:
            cards_seen = max(cards_seen, card_no)
            body_run = 0
            subheads_in_card += 1
            text = strip_markup(m.group(1))
            limit = ramp["subhead"]["max_chars"]
            if len(text) > limit:
                findings.append(Finding(idx, card_no, "subhead", len(text), limit, text))
            continue

        m = TITLE.match(raw)
        if m:
            cards_seen = max(cards_seen, card_no)
            body_run = 0
            card_titles += 1
            text = strip_markup(m.group(1))
            limit = ramp["title"]["max_chars"]
            if len(text) > limit:
                findings.append(Finding(idx, card_no, "title", len(text), limit, text))
            if card_titles > 1:
                findings.append(Finding(
                    idx, card_no, "struct", card_titles, 1,
                    "second title on the same card -- missing '---' break?"))
            continue

        m = BULLET.match(raw)
        text = strip_markup(m.group(1)) if m else strip_markup(raw)
        if not text:
            continue

        cards_seen = max(cards_seen, card_no)
        body_run += 1
        if len(text) > body_limit:
            findings.append(Finding(idx, card_no, "body", len(text), body_limit, text))
        if body_run == max_lines + 1:
            findings.append(Finding(
                idx, card_no, "density", body_run, max_lines,
                "body block longer than fits without shrinking"))

    close_card(len(lines))
    return findings, max(cards_seen, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outline", help="Markdown outline to check")
    ap.add_argument("--profile", default=T.DEFAULT_PROFILE,
                    help=f"Token profile (default: {T.DEFAULT_PROFILE}). "
                         f"Available: {', '.join(T.profile_names())}")
    ap.add_argument("--column", default=None,
                    help="Body column profile the deck uses "
                         "(default: the profile's own default)")
    ap.add_argument("--json", action="store_true", help="Emit findings as JSON")
    args = ap.parse_args()

    try:
        profile = T.get_profile(args.profile)
    except KeyError as exc:
        sys.exit(str(exc).strip('"'))

    column = args.column or profile["default_column"]
    if column not in profile["columns"]:
        sys.exit(f"unknown column '{column}' for profile '{args.profile}'. "
                 f"Available: {', '.join(sorted(profile['columns']))}")

    with open(args.outline, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    findings, n_cards = lint(lines, profile, column)
    col = profile["columns"][column]

    if args.json:
        json.dump({
            "outline": args.outline,
            "profile": args.profile,
            "cards": n_cards,
            "column": column,
            "body_limit": col["budget"],
            "findings": [f.as_dict() for f in findings],
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1 if findings else 0

    print(f"Aviation Synergy deck linter -- {args.outline}")
    print(f"  profile '{args.profile}' | {n_cards} cards | column '{column}' "
          f"({col['width_in']}in @ {col['body_pt']}pt, {col['budget']} chars/line)")
    print()

    if not findings:
        print("  PASS -- every line is inside budget. Gamma will hold the type ramp.")
        return 0

    by_role = {}
    for f in findings:
        by_role.setdefault(f.role, []).append(f)

    for role in ("title", "subhead", "body", "density", "struct"):
        group = by_role.get(role)
        if not group:
            continue
        print(f"{role.upper()} ({len(group)})")
        for f in sorted(group, key=lambda x: -x.over):
            print(f)
        print()

    print(f"  FAIL -- {len(findings)} over budget. Each one is a font shrink on export.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
