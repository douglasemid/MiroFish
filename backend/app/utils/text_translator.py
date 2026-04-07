"""
Batch translator for content coming from external services (Zep Cloud).

Zep Cloud generates entity summaries and edge facts using its own internal
LLM, which produces text in English regardless of MiroFish's UI locale.
This module provides a thin batch-translation layer that converts those
fields to the active locale before they reach the frontend, with an
in-memory cache to avoid retranslating identical strings.
"""

import json
import re
from typing import List, Optional, Dict

from .llm_client import LLMClient
from .locale import get_locale
from .logger import get_logger

logger = get_logger('mirofish.translator')

# Process-wide cache: source string → translated string (per locale)
_translation_cache: Dict[str, Dict[str, str]] = {}

# Singleton LLM client used only for translation tasks
_translator_client: Optional[LLMClient] = None


def _get_client() -> LLMClient:
    global _translator_client
    if _translator_client is None:
        # Create a fresh client without the language enforcement injection,
        # so we have full control over the translator's system prompt.
        _translator_client = LLMClient()
    return _translator_client


def _looks_like_pt(text: str) -> bool:
    """Cheap heuristic: if the string already contains common PT markers,
    skip translation. Avoids round-trips for already-localized data."""
    if not text:
        return True
    # Common PT-BR words that rarely appear in EN/ZH
    pt_markers = re.compile(
        r'\b(é|são|não|também|porém|além|através|você|nós|está|foram|sobre|'
        r'quando|onde|porque|qual|como|para|com|dos|das|uma|umas|uns)\b',
        re.IGNORECASE
    )
    return bool(pt_markers.search(text))


def translate_strings(
    texts: List[str],
    target_locale: Optional[str] = None,
) -> List[str]:
    """
    Translate a batch of strings to the target locale (defaults to current
    request locale). Returns the list in the same order. Strings already in
    the target locale (heuristically) and cache hits are passed through.

    Translation happens in a single LLM call to minimize latency/cost.
    """
    if not texts:
        return texts

    locale = target_locale or get_locale()

    # Only PT-BR is currently supported as a translation target. For en/zh
    # we trust the upstream content (Zep is in EN, internal prompts in ZH).
    if locale != 'pt':
        return texts

    cache = _translation_cache.setdefault(locale, {})

    # Build the work list: only items that aren't cached and don't look
    # like they're already in the target language.
    work_indices: List[int] = []
    work_texts: List[str] = []
    result: List[str] = list(texts)

    for i, txt in enumerate(texts):
        if not txt or not isinstance(txt, str):
            continue
        if txt in cache:
            result[i] = cache[txt]
            continue
        if _looks_like_pt(txt):
            cache[txt] = txt
            continue
        work_indices.append(i)
        work_texts.append(txt)

    if not work_texts:
        return result

    # Single batched LLM call. We ask for a JSON object mapping the index
    # back to the translated string, so we can re-assemble safely.
    payload = {str(idx): text for idx, text in enumerate(work_texts)}

    system_prompt = (
        "You are a professional translator. Translate every value in the "
        "JSON object below to natural Brazilian Portuguese (pt-BR). Use "
        "Brazilian vocabulary and grammar (NOT European Portuguese). "
        "Preserve the meaning, technical terms, names of products, "
        "company names, brand names, acronyms (such as ISP, LLM, MBTI, "
        "GraphRAG, ReACT) and any UUIDs or IDs exactly as they are. Do "
        "NOT add explanations or change the structure. Return ONLY a "
        "valid JSON object using the same keys, with each value replaced "
        "by its Brazilian Portuguese translation."
    )
    user_prompt = (
        "Translate every value in the following JSON object to natural "
        "Brazilian Portuguese (pt-BR):\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    try:
        client = _get_client()
        response = client.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        for str_idx, original in payload.items():
            translated = response.get(str_idx, original)
            if isinstance(translated, str) and translated.strip():
                cache[original] = translated
                result[work_indices[int(str_idx)]] = translated
            else:
                cache[original] = original
    except Exception as e:
        logger.warning(f"Batch translation failed, returning original strings: {e}")
        # On any failure, return originals so the request still completes.
        return result

    return result


def translate_string(text: str, target_locale: Optional[str] = None) -> str:
    """Convenience helper for a single string."""
    if not text:
        return text
    return translate_strings([text], target_locale=target_locale)[0]
