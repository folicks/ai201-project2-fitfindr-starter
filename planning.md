# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tool Inventory

**Tool 1: search_listings**
- **Inputs:** `description` (str), `size` (str | None), `max_price` (float | None)
- **Output:** list[dict]
- **Purpose:** Searches mock listings and returns ranked results matching the description, size, and price filter.

**Tool 2: suggest_outfit**
- **Inputs:** `new_item` (dict), `wardrobe` (dict)
- **Output:** str
- **Purpose:** Generates outfit styling suggestions using an LLM, returning general advice for empty wardrobes and specific combos for populated ones.

**Tool 3: create_fit_card**
- **Inputs:** `outfit` (str), `new_item` (dict)
- **Output:** str
- **Purpose:** Creates a 2–4 sentence social media caption for the thrift item and outfit combination.

---

## How the Planning Loop Works

The agent follows this conditional flow:
1. Parse the user query into description, size, and max_price using regex.
2. Call `search_listings()` with the parsed parameters.
3. **Early exit:** If `search_listings()` returns an empty list, set `session["error"]` and return immediately without calling downstream tools.
4. Select the top result and store it in `session["selected_item"]`.
5. Call `suggest_outfit()` with the selected item and wardrobe. The tool checks `wardrobe["items"]` — if empty, it calls the LLM with a general styling prompt; otherwise, it names specific wardrobe pieces in the prompt.
6. Call `create_fit_card()` with the outfit suggestion and selected item.
7. Convert the listing to a wardrobe entry, append it to the wardrobe, and persist to `data/session_wardrobe.json`.
8. Return the completed session dict with all fields populated.

---

## State Management Approach

The session dict is the single source of truth. Fields include:
- `query` (str): original user input
- `parsed` (dict): extracted {description, size, max_price}
- `search_results` (list): all matching listings
- `selected_item` (dict): top result
- `wardrobe` (dict): user's wardrobe with `items` list
- `outfit_suggestion` (str): output from `suggest_outfit()`
- `fit_card` (str): output from `create_fit_card()`
- `error` (str | None): set if the interaction ends early

Information flows sequentially: `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. Each tool receives only the fields it needs and writes its output into a new session field.

---

## Error Handling Strategy

**search_listings:** Returns an empty list (does not raise). When caught, `run_agent()` sets `session["error"] = "No listings found matching '<description>'. Try broadening your search."` and returns early.

**suggest_outfit:** If the LLM call fails or returns empty text, it returns a fallback generic string. Example: `"This piece has a versatile, easygoing vibe—try styling it with simple basics, layered outerwear, and one statement accessory for a polished thrifted look."`

**create_fit_card:** If `outfit` is blank, it returns a descriptive error string instead of crashing. If the LLM fails, it returns a safe fallback caption.

Concrete example from testing: Running `python agent.py` with a no-results query (`"designer ballgown size XXS under $5"`) prints the error message cleanly without exceptions.

---

## Spec Reflection

**How the spec helped:** The spec's emphasis on failure modes (e.g., "what if the wardrobe is empty?") forced explicit handling in each tool. Instead of raising exceptions, each tool returns a string, which simplified the loop logic and prevented crashes.

**How implementation diverged:** The spec suggested wardrobe might remain a temporary in-memory structure, but the implementation persists it to `data/session_wardrobe.json` after each interaction. This allows the wardrobe to accumulate across sessions, which is more realistic for a thrift-discovery app.

---

## AI Usage

**Instance 1:** I directed the AI to implement `search_listings()` using a keyword-matching and phrase-matching scoring algorithm. The AI initially returned only exact matches; I overrode it to use fuzzy token overlap so queries like "vintage tee" would match listings with those words in any field (title, description, tags, colors).

**Instance 2:** I asked the AI to implement `run_agent()` with early-exit logic. The AI included a try-except block that caught empty results; I overrode it to use an explicit `if not results:` check for clarity and to avoid exception handling overhead.

**Note on venv:** When testing `app.py` on Windows, I had to explicitly tell the AI to activate the virtual environment (`.venv\Scripts\Activate.ps1`) before running the command, as VS Code's Python terminal sometimes doesn't activate it automatically.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:**
<!-- Continue until the full interaction is complete -->

**Final output to user:**
<!-- What does the user actually see at the end? -->
