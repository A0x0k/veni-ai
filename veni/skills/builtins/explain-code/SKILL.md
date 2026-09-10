---
name: "Explain Code"
description: "Plain-English code explanations for any audience, from beginner to expert"
triggers: ["explain", "what does this do", "understand", "how does", "what is", "walk me through", "break down", "confused", "eli5", "in simple terms", "what does this mean"]
version: "2.0.0"
author: "veni-team"
---

# Explain Code Skill

## Explanation Structure — Always in This Order
1. **What it does** — one sentence in plain English, no jargon
2. **Why it exists** — what problem it solves or what would break without it
3. **How it works** — step by step, referencing actual line numbers or variable names
4. **Gotchas** — anything surprising, non-obvious, or that commonly causes bugs

Never start with "This code..." — start with what it *does*.

## Audience Calibration
- Uses technical terms correctly → use technical terms back
- Says "I'm new" or asks basic questions → use analogies, avoid jargon
- Asks "ELI5" or "simple terms" → explain as if to a smart 12-year-old
- Default: explain as if the reader knows programming but not this specific language/library

## Analogies That Work
- **Recursion** → "like Russian nesting dolls — each doll opens to reveal a smaller one until you reach the smallest"
- **Async/await** → "like ordering food and sitting down to do other things while waiting, instead of standing at the counter"
- **Decorators** → "like a gift wrapper — the gift is still there, but it's been enhanced before being handed over"
- **Generators** → "like a vending machine — it produces one item at a time on demand, not all at once"
- **Classes** → "like a blueprint for a house — the blueprint defines the structure, each house built from it is an instance"
- **APIs** → "like a waiter — you tell the waiter what you want, they go to the kitchen (server), and bring back the result"
- **Callbacks** → "like leaving your number at a restaurant — you go do other things, they call you when your table is ready"
- **Promises/Futures** → "like a ticket at a deli counter — you get a ticket now, the actual item comes later"
- **Regex** → "like a search pattern with wildcards — `*.txt` but much more powerful and precise"
- **Pointers/References** → "like a sticky note with an address on it — the note isn't the house, it tells you where the house is"

## What NOT to Do
- Don't restate the code in English word-for-word: "this line sets x to 5" for `x = 5`
- Don't explain every line — explain the *logic*, not the syntax
- Don't use jargon without defining it first
- Don't assume the reader knows what the library does — explain the relevant part
- Don't say "simply" or "just" — it's condescending when the reader is confused

## For Complex Code
Break it into named sections:
```
Section 1 — Setup (lines 1-10): loads config and connects to the database
Section 2 — Main loop (lines 11-30): processes each record one at a time
Section 3 — Cleanup (lines 31-40): closes connections and saves results
```
Then explain each section separately before explaining how they connect.

## Follow-Up Prompts to Offer
After explaining, always offer:
- "Want me to show what happens if [edge case]?"
- "Want a simpler version that does the same thing?"
- "Want me to add comments to the code itself?"
