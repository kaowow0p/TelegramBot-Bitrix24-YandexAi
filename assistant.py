import os
import requests
from typing import Optional, List


class YandexAssistantClient:
    """Minimal wrapper: if YANDEX_API_KEY present will call Yandex Generation API,
    otherwise will produce a concise, context-aware fallback answer locally.
    """

    def __init__(self, api_key: Optional[str] = None, folder_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("YANDEX_API_KEY")
        self.folder_id = folder_id or os.getenv("YANDEX_FOLDER_ID")
        self.model_id = os.getenv("YANDEX_MODEL_ID", "gpt-4o-mini")

    def _build_prompt(self, question: str, contexts: Optional[List[str]] = None) -> str:
        parts = [
            "Ты — ассистент разработчика. Отвечай коротко и точно по документации Bitrix24 API.",
        ]
        if contexts:
            parts.append("Контекст из документации:")
            parts.extend(contexts)
        parts.append(f"Вопрос: {question}")
        parts.append("Краткий ответ:")
        return "\n\n".join(parts)

    def generate(self, question: str, contexts: Optional[List[str]] = None) -> str:
        prompt = self._build_prompt(question, contexts)
        if not self.api_key:
            # Local fallback: echo context and produce a brief template answer
            ctx_text = "\n---\n".join(contexts) if contexts else ""
            answer = "На основе найденного контекста: \n"
            if ctx_text:
                answer += ctx_text[:2000] + ("..." if len(ctx_text) > 2000 else "") + "\n\n"
            answer += "Краткий ответ (локальный, без обращения к Yandex LLM): сформулируйте запрос точнее или добавьте детали."
            return answer

        url = f"https://api.generation.yandexcloud.net/v1/models/{self.model_id}:predict"
        headers = {"Authorization": f"Api-Key {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "folderId": self.folder_id,
            "texts": [prompt],
            "parameters": {"temperature": 0.2, "max_output_tokens": 1024},
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        # simple parse
        if "results" in data:
            texts = [res.get("text", "") for res in data["results"]]
            return "\n".join(t for t in texts if t).strip()
        return str(data)
