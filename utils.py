import re
from typing import List

def clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def split_into_sentences(text: str, max_sentences: int = 3) -> List[str]:
    # naive splitter for short snippets
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts[:max_sentences]
