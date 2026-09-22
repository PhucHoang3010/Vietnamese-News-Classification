from pathlib import Path

from underthesea import word_tokenize


def load_stopwords(stopwords_path: Path) -> set[str]:
    with open(
        stopwords_path,
        "r",
        encoding="utf-8-sig",
    ) as f:
        return {
            line.strip().lower()
            for line in f
            if line.strip()
            and not line.lstrip().startswith("#")
        }


def preprocess_text(text: str, stopwords: set[str]) -> str:
    if text is None:
        return ""

    text = str(text).strip()

    if not text:
        return ""

    tokens = word_tokenize(text)

    cleaned = []

    for tok in tokens:
        tok_lower = (
            str(tok)
            .lower()
            .strip()
        )

        # Empty token
        if not tok_lower:
            continue

        # Whitespace-only token
        if tok_lower.isspace():
            continue

        # Punctuation-only token
        if all(
            not ch.isalnum()
            for ch in tok_lower
        ):
            continue

        # Stopword removal
        if tok_lower in stopwords:
            continue

        cleaned.append(tok_lower)

    return " ".join(cleaned)