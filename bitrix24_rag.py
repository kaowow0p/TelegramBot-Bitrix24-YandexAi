import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from utils import clean_text, split_into_sentences


class Bitrix24RAG:
    def __init__(self, base_url: str = "https://apidocs.bitrix24.ru/"):
        self.base_url = base_url.rstrip("/")

    def _get_index_links(self) -> List[str]:
        # Fetch a central index page and extract some links to work as knowledge base
        try:
            url = f"{self.base_url}/rest_help/"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            links = []
            for a in soup.select("a[href]"):
                href = a.get("href")
                if href and href.startswith("/") and "rest_help" in href:
                    full = self.base_url + href
                    links.append(full)
            # deduplicate while preserving order
            seen = set()
            out = []
            for u in links:
                if u not in seen:
                    seen.add(u)
                    out.append(u)
            return out[:30]
        except Exception:
            return []

    def _fetch_page_text(self, url: str) -> Optional[str]:
        try:
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            # get main content paragraphs
            texts = [p.get_text(separator=" ", strip=True) for p in soup.select("p, li, dd")]
            text = "\n".join(t for t in texts if t)
            return clean_text(text)
        except Exception:
            return None

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        # Very simple retrieval: look for query terms in index pages and return snippets
        query_lower = query.lower()
        candidates = []
        for link in self._get_index_links():
            text = self._fetch_page_text(link)
            if not text:
                continue
            score = 0
            if query_lower in text.lower():
                score += 10
            for token in query_lower.split():
                if token and token in text.lower():
                    score += 1
            if score > 0:
                # take first few sentences as snippet
                snip = " ".join(split_into_sentences(text, max_sentences=3))
                candidates.append((score, link, snip))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [f"Источник: {c[1]}\n{c[2]}" for c in candidates[:top_k]]
