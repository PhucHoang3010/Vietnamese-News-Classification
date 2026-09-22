from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text))
    return " ".join(text.strip().split())


def is_valid_keyword(
    phrase: str,
    ngram: int,
    article_text: str = "",
) -> bool:
    """Final lightweight quality gate.

    The article_text argument is kept only for compatibility with the current
    persistence script. v1.0 deliberately does not infer phrase validity from
    local context; candidate ranking/reduction is handled by the extractor.
    """
    phrase = normalize_text(phrase)
    if not phrase:
        return False

    tokens = phrase.split()
    if len(tokens) != int(ngram):
        return False

    if not any(ch.isalpha() for token in tokens for ch in token):
        return False

    # Reject clearly malformed numeric tokenization such as:
    # "845.100 tệ 3 3" or "tệ 3 3 tỷ".
    numeric_only = [
        token
        for token in tokens
        if re.fullmatch(r"[\d.,]+", token)
    ]

    if len(numeric_only) >= 2:
        return False

    # Reject repeated standalone numeric groups anywhere in the phrase.
    if re.search(r"\b\d+[.,\d]*\s+\S+\s+\d+\s+\d+\b", phrase):
        return False

    return True
