import os
import re
from config import DOCS_PATH

# Matches "3 months ago", "a year ago", "just now", etc.
_TIME_AGO_RE = re.compile(
    r'^(?:\d+ (?:months?|years?|weeks?|days?) ago|a (?:month|year|week|day) ago|just now)$',
    re.IGNORECASE,
)


def _parse_header(lines):
    """Extract restaurant name, price range, and cuisine from the file header."""
    restaurant_name = lines[0].strip() if lines else "Unknown"
    price_range = ""
    cuisine = ""

    for line in lines[1:5]:
        line = line.strip()
        match = re.search(r'\$([\d,]+[–\-][\d,]+)', line)
        if match:
            price_range = "$" + match.group(1)
        if "restaurant" in line.lower() and not cuisine:
            cuisine = line.split("·")[0].strip().rstrip("·")

    return restaurant_name, price_range, cuisine


def _parse_ratings(block):
    """Extract food, service, atmosphere ratings (1-5) from a review block. Returns -1 if absent."""
    food = re.search(r'\bFood:\s*([1-5])\b', block)
    service = re.search(r'\bService:\s*([1-5])\b', block)
    atmosphere = re.search(r'\bAtmosphere:\s*([1-5])\b', block)
    return {
        "food_rating": int(food.group(1)) if food else -1,
        "service_rating": int(service.group(1)) if service else -1,
        "atmosphere_rating": int(atmosphere.group(1)) if atmosphere else -1,
    }


def _parse_months_ago(block):
    """Convert relative date string to months (int). Returns -1 if not found."""
    m = re.search(
        r'(\d+)\s+(month|year|week|day)s?\s+ago|a\s+(month|year|week|day)\s+ago',
        block, re.IGNORECASE,
    )
    if not m:
        return -1
    if m.group(3):
        unit, n = m.group(3).lower(), 1
    else:
        n, unit = int(m.group(1)), m.group(2).lower()

    if unit == "year":
        return n * 12
    if unit == "month":
        return n
    if unit == "week":
        return max(1, round(n * 7 / 30))
    return 1  # day → 1 month minimum


def load_documents():
    """Load all .txt review files from the documents folder."""
    documents = []
    for filename in sorted(os.listdir(DOCS_PATH)):
        if filename.endswith(".txt"):
            filepath = os.path.join(DOCS_PATH, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            documents.append({"filename": filename, "text": text})
    print(f"Loaded {len(documents)} document(s): {[d['filename'] for d in documents]}")
    return documents


def chunk_document(text, filename):
    """
    Split a restaurant review file into one chunk per individual review.

    Each chunk includes:
      - restaurant metadata header (name, cuisine, price range)
      - full review text and ratings
      - parsed numeric metadata: food_rating, service_rating, atmosphere_rating, months_ago
        (-1 means the field was not present in the review)

    Returns a list of dicts with 'text', 'restaurant', 'source', 'chunk_id',
    and the four numeric metadata fields.
    """
    lines = text.strip().split("\n")
    restaurant_name, price_range, cuisine = _parse_header(lines)

    review_starts = []
    for i, line in enumerate(lines):
        if _TIME_AGO_RE.match(line.strip()) and i > 0:
            review_starts.append(i - 1)

    if not review_starts:
        return []

    prefix = filename.replace(".txt", "").lower()
    metadata_header = (
        f"Restaurant: {restaurant_name}\n"
        f"Cuisine: {cuisine}\n"
        f"Price range: {price_range}\n"
        "---\n"
    )

    chunks = []

    for idx, start in enumerate(review_starts):
        end = review_starts[idx + 1] if idx + 1 < len(review_starts) else len(lines)
        block = "\n".join(lines[start:end]).strip()

        if len(block) < 50:
            continue

        ratings = _parse_ratings(block)
        months_ago = _parse_months_ago(block)

        base = {
            "restaurant": restaurant_name,
            "source": filename,
            "food_rating": ratings["food_rating"],
            "service_rating": ratings["service_rating"],
            "atmosphere_rating": ratings["atmosphere_rating"],
            "months_ago": months_ago,
        }

        if len(block) > 500:
            sub = _split_long_block(block, metadata_header, base, prefix, len(chunks))
            chunks.extend(sub)
        else:
            chunks.append({
                "text": metadata_header + block,
                "chunk_id": f"{prefix}_{len(chunks)}",
                **base,
            })

    return chunks


def _split_long_block(block, metadata_header, base, prefix, counter):
    """Split a long review block into sentence-grouped sub-chunks with ~50-char overlap."""
    sentences = re.split(r'(?<=[.!?])\s+', block)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) > 500 and len(current) >= 50:
            chunks.append({
                "text": metadata_header + current.strip(),
                "chunk_id": f"{prefix}_{counter + len(chunks)}",
                **base,
            })
            current = current[-50:] + " " + sentence
        else:
            current = (current + " " + sentence).strip()

    if len(current) >= 50:
        chunks.append({
            "text": metadata_header + current.strip(),
            "chunk_id": f"{prefix}_{counter + len(chunks)}",
            **base,
        })

    return chunks
