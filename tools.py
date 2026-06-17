"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings, get_example_wardrobe, get_empty_wardrobe

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _tokenize(text: str) -> list[str]:
    """Return normalized lowercase word tokens from a string."""
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token]


def _size_matches(listing_size: str, requested_size: str) -> bool:
    """Return True when requested size plausibly matches a listing size."""
    if not requested_size:
        return True

    listing_tokens = set(_tokenize(str(listing_size)))
    requested_tokens = set(_tokenize(str(requested_size)))

    if requested_tokens & listing_tokens:
        return True

    requested_text = str(requested_size).lower().replace("/", " ")
    listing_text = str(listing_size).lower()
    return requested_text in listing_text or any(token in listing_text for token in requested_text.split())


def _score_listing(listing: dict, description: str) -> int:
    """Score a listing for keyword relevance to the user description."""
    query_tokens = _tokenize(description)
    if not query_tokens:
        return 0

    haystack = " ".join(
        [
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            " ".join(listing.get("style_tags", []) or []),
            " ".join(listing.get("colors", []) or []),
            listing.get("brand", "") or "",
            listing.get("size", ""),
        ]
    )
    haystack_tokens = _tokenize(haystack)

    score = 0
    for token in query_tokens:
        if token in haystack_tokens:
            score += 2

    for left, right in zip(query_tokens, query_tokens[1:]):
        phrase = f"{left} {right}"
        if phrase in haystack.lower():
            score += 2

    return score


def _call_llm(prompt: str, temperature: float = 0.7) -> str:
    """Call the Groq chat model and return the text response."""
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=220,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    filtered = []
    for item in listings:
        if max_price is not None and float(item.get("price", 0)) > max_price:
            continue
        if size is not None and not _size_matches(item.get("size", ""), size):
            continue

        score = _score_listing(item, description)
        if score > 0:
            filtered.append({**item, "_score": score})

    filtered.sort(key=lambda item: item["_score"], reverse=True)
    return [
        {key: value for key, value in item.items() if key != "_score"}
        for item in filtered
    ]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []

    if not wardrobe_items:
        prompt = (
            "You are helping a thrift shopper style a new secondhand find. "
            f"The item is: {new_item.get('title', 'Unknown item')} "
            f"({new_item.get('category', 'unknown category')}, "
            f"${new_item.get('price', 'n/a')}, {new_item.get('platform', 'unknown platform')}). "
            "Give 2 concise outfit ideas that explain what it pairs well with, "
            "the overall vibe, and why it works. Keep the advice practical and stylish."
        )
    else:
        wardrobe_lines = "\n".join(
            f"- {item.get('name', 'Unnamed item')} ({item.get('category', 'unknown category')}, "
            f"colors: {', '.join(item.get('colors', []) or [])})"
            for item in wardrobe_items
        )
        prompt = (
            "You are styling a thrifted item using the user's existing wardrobe. "
            f"New item: {new_item.get('title', 'Unknown item')} "
            f"({new_item.get('category', 'unknown category')}, "
            f"size {new_item.get('size', 'unknown')}, "
            f"${new_item.get('price', 'n/a')}, platform {new_item.get('platform', 'unknown')}). "
            "Existing wardrobe pieces:\n"
            f"{wardrobe_lines}\n\n"
            "Suggest 1–2 complete outfits using the new item and specific wardrobe pieces. "
            "Mention colors, vibe, and how the layers work together."
        )

    response = _call_llm(prompt, temperature=0.75)
    if response:
        return response

    if not wardrobe_items:
        return (
            "This piece has a versatile, easygoing vibe—try styling it with simple basics, "
            "layered outerwear, and one statement accessory for a polished thrifted look."
        )

    return (
        "Try pairing this thrifted find with your existing wardrobe staples for a balanced, "
        "easy outfit. Focus on one standout silhouette, one neutral base, and one accent color."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not isinstance(outfit, str) or not outfit.strip():
        return (
            "Outfit suggestion is missing, so I can’t create a fit card yet. "
            "Try running the styling step again with a valid thrifted item."
        )

    prompt = (
        "Write a short, casual Instagram/TikTok style caption for a thrifted outfit. "
        "Use 2–4 sentences, sound natural and authentic, and mention the item name, price, "
        "and platform once each. Capture the outfit vibe in specific terms, and make it feel "
        "different every time.\n\n"
        f"Item: {new_item.get('title', 'Unknown item')}\n"
        f"Price: ${new_item.get('price', 'n/a')}\n"
        f"Platform: {new_item.get('platform', 'unknown platform')}\n"
        f"Outfit idea: {outfit}"
    )

    response = _call_llm(prompt, temperature=0.9)
    if response:
        return response

    return (
        f"Found {new_item.get('title', 'this thrifted piece')} for ${new_item.get('price', 'n/a')} "
        f"on {new_item.get('platform', 'the platform')}—it has a fun, wearable vibe that pairs "
        "well with your current closet staples."
    )


# ── Tool 4: add_to_wardrobe ───────────────────────────────────────────────────

def _listing_to_wardrobe_item(listing: dict) -> dict:
    """Convert a listing dict to a wardrobe item dict matching wardrobe_schema.json."""
    notes_parts = []
    if listing.get("size"):
        notes_parts.append(f"Size: {listing['size']}")
    if listing.get("condition"):
        notes_parts.append(f"Condition: {listing['condition']}")
    if listing.get("brand"):
        notes_parts.append(f"Brand: {listing['brand']}")
    if listing.get("price") is not None:
        notes_parts.append(f"Paid: ${listing['price']} on {listing.get('platform', 'unknown')}")

    return {
        "id": listing.get("id", ""),
        "name": listing.get("title", ""),
        "category": listing.get("category", ""),
        "colors": list(listing.get("colors") or []),
        "style_tags": list(listing.get("style_tags") or []),
        "notes": ". ".join(notes_parts) if notes_parts else None,
    }


def add_to_wardrobe(listing: dict, wardrobe: dict | None = None) -> dict:
    """
    Convert a listing to wardrobe schema format and append it to a wardrobe.

    Args:
        listing:  A listing dict returned by search_listings(). Uses load_listings()
                  fields: id, title, category, colors, style_tags, size, condition,
                  brand, price, platform.
        wardrobe: An existing wardrobe dict (matching wardrobe_schema.json) to append
                  the item to. Pass get_example_wardrobe() to start from the sample
                  closet, or get_empty_wardrobe() / None to start fresh.

    Returns:
        The wardrobe dict with the converted item appended to 'items'. Skips the
        append if an item with the same id already exists (idempotent).

    Mapping from listing → wardrobe schema:
        id         → id
        title      → name
        category   → category
        colors     → colors
        style_tags → style_tags
        size + condition + brand + price/platform → notes (single string)
    """
    if wardrobe is None:
        wardrobe = get_empty_wardrobe()

    wardrobe_item = _listing_to_wardrobe_item(listing)

    existing_ids = {item.get("id") for item in wardrobe.get("items", [])}
    if wardrobe_item["id"] not in existing_ids:
        wardrobe["items"].append(wardrobe_item)

    return wardrobe
