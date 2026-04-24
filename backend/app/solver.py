"""LLM-backed solver. Uses Google Gemini if GEMINI_API_KEY is set, else a mock."""
from __future__ import annotations

import base64
import logging
import os
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

DEFAULT_PROMPT = (
    "You are an expert technical interview assistant. Look at the screenshot and "
    "identify the question or problem being asked. Then answer it concisely and "
    "clearly. If it is a coding problem, provide a working solution with brief "
    "reasoning. Format the response as Markdown so the user can read it quickly."
)


@dataclass
class SolveResult:
    answer: str
    used_mock: bool


def _mock_answer(prompt: str) -> str:
    return (
        "**(Mock response — no `GEMINI_API_KEY` configured on the backend)**\n\n"
        "I can see your screenshot but the backend is running without an LLM key, "
        "so I'm returning a deterministic placeholder. Wire up `GEMINI_API_KEY` as "
        "a Fly secret on the backend and I'll return real answers.\n\n"
        f"Your prompt was: _{prompt!s}_"
    )


def _strip_data_url_prefix(image_b64: str) -> str:
    """Accept either raw base64 or a `data:image/png;base64,...` URL."""
    match = re.match(r"^data:image/[A-Za-z0-9.+-]+;base64,(.*)$", image_b64)
    return match.group(1) if match else image_b64


def solve_screenshot(image_base64: str, user_prompt: str | None = None) -> SolveResult:
    """Send the screenshot + prompt to Gemini and return the answer."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    prompt = (user_prompt or "").strip() or DEFAULT_PROMPT
    cleaned_b64 = _strip_data_url_prefix(image_base64)

    # Validate base64 quickly (raises on bad input -> 400 upstream).
    try:
        base64.b64decode(cleaned_b64, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"image_base64 is not valid base64: {exc}") from exc

    if not api_key:
        return SolveResult(answer=_mock_answer(prompt), used_mock=True)

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": cleaned_b64,
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }

    try:
        with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
            resp = client.post(
                GEMINI_ENDPOINT,
                params={"key": api_key},
                json=body,
            )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Gemini call failed")
        raise RuntimeError(f"Gemini API error: {exc}") from exc

    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        feedback = data.get("promptFeedback") or {}
        raise RuntimeError(
            f"Gemini returned no candidates (promptFeedback={feedback})"
        )
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text_chunks = [p.get("text", "") for p in parts if isinstance(p, dict)]
    answer = "".join(text_chunks).strip()
    if not answer:
        raise RuntimeError("Gemini returned an empty answer")
    return SolveResult(answer=answer, used_mock=False)
