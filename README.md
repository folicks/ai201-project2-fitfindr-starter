# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.


Tool inventory: list every tool by name, the input parameters and types that match the function signatures in `tools.py`, the output type, and a short sentence describing the tool's purpose.

data parsing 
How the planning loop works: describe the conditional tool flow, including when the agent returns early on no search results and when it proceeds to outfit suggestion and caption creation.
State management approach: describe the session state object, what fields are stored, when they are written, and how the selected item and wardrobe are passed between tools.
Error handling strategy: explain how each tool handles failure, and include one concrete example from your testing of a terminal command or app run where the agent produced a clean error message instead of crashing.
Spec reflection: describe one way the spec helped you implement the tools and one way your implementation diverged from it, such as treating the wardrobe as a persistent JSON file instead of a temporary in-memory array.
AI usage section: include at least two specific examples of what you asked the AI to do, what code or behavior you revised or overrode, and one note about explicitly telling the AI to use the project virtual environment on Windows when testing localhost.