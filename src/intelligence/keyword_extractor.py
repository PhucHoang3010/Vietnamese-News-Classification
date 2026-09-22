from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class VietnameseKeywordExtractor:
    """
    Corpus-aware Vietnamese keyword extractor for the News Intelligence layer.

    Final design (v1.0):
        Article
          -> candidate n-grams (1..5)
          -> structural candidate filtering
          -> TF-IDF relevance
          -> corpus association (PMI / NPMI)
          -> frequency + title signals
          -> phrase-quality scoring
          -> nested/redundancy reduction
          -> final ranked keywords

    This module is independent from the frozen P2 classifier.
    No database access is performed here.
    """

    VERSION = "v1.0"
    NGRAM_RANGE = (1, 5)

    PHRASE_WEIGHTS = {
        1: 0.55,
        2: 1.00,
        3: 1.06,
        4: 1.12,
        5: 1.15,
    }

    TITLE_BOOST_VALUE = 1.25

    NPMI_SCALE = 2.0
    ASSOCIATION_STRENGTH = 0.24
    MIN_ASSOCIATION = 0.76
    MAX_ASSOCIATION = 1.24
    MIN_RELIABLE_FREQ = 3

    MAX_CANDIDATES = 350

    TOKEN_RE = re.compile(
        r"\b[\wÀ-ỹ]+(?:[./:&+#-][\wÀ-ỹ]+)*\b",
        re.UNICODE,
    )

    FALLBACK_STOPWORDS = {
        "và", "là", "của", "cho", "với", "trong", "một", "những",
        "các", "được", "để", "khi", "theo", "từ", "tại", "trên",
        "vào", "ra", "này", "đó", "như", "có", "không", "đã", "sẽ",
        "bị", "do", "nên", "mà", "hay", "hoặc", "rất", "còn", "đang",
        "thì", "lại", "cùng", "sau", "trước", "qua", "đến", "về",
        "bởi", "hơn", "nhất", "nhiều", "ít", "từng", "mỗi", "mọi",
    }

    def __init__(
        self,
        stopwords_path: str | Path | None = None,
        *,
        min_df: int = 1,
        max_df: float = 0.90,
    ) -> None:
        self.stopwords_path = Path(stopwords_path) if stopwords_path else None
        self.min_df = min_df
        self.max_df = max_df
        self.stopwords = self._load_stopwords()

        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            token_pattern=self.TOKEN_RE.pattern,
            lowercase=False,
            ngram_range=self.NGRAM_RANGE,
            min_df=self.min_df,
            max_df=self.max_df,
            sublinear_tf=True,
            norm="l2",
        )

        self._fitted = False
        self.documents_count = 0
        self.total_tokens = 0

        self.unigram_counts: Counter[str] = Counter()
        self.bigram_counts: Counter[tuple[str, str]] = Counter()
        self.trigram_counts: Counter[tuple[str, str, str]] = Counter()
        self.fourgram_counts: Counter[tuple[str, str, str, str]] = Counter()
        self.fivegram_counts: Counter[tuple[str, str, str, str, str]] = Counter()

        self.total_bigrams = 0
        self.total_trigrams = 0
        self.total_fourgrams = 0
        self.total_fivegrams = 0

        self._vocabulary: dict[str, int] = {}
        self._feature_names: np.ndarray | None = None

    @property
    def fitted(self) -> bool:
        return self._fitted

    @property
    def stats(self) -> dict[str, int | str]:
        return {
            "version": self.VERSION,
            "documents": self.documents_count,
            "total_tokens": self.total_tokens,
            "unigrams": len(self.unigram_counts),
            "bigrams": len(self.bigram_counts),
            "trigrams": len(self.trigram_counts),
            "fourgrams": len(self.fourgram_counts),
            "fivegrams": len(self.fivegram_counts),
            "fitted": int(self._fitted),
        }

    def _candidate_stopword_paths(self) -> list[Path]:
        root = Path.cwd().resolve()
        return [
            root / "data" / "stopwords.txt",
            root / "data" / "stopwords" / "stopwords.txt",
            root / "data" / "processed" / "stopwords.txt",
            root / "data" / "raw" / "stopwords.txt",
            root / "src" / "intelligence" / "stopwords.txt",
            root / "src" / "intelligence" / "data" / "stopwords.txt",
        ]

    def _load_stopwords(self) -> set[str]:
        paths: list[Path] = []
        if self.stopwords_path is not None:
            paths.append(self.stopwords_path)
        paths.extend(self._candidate_stopword_paths())

        for path in paths:
            try:
                if not path.is_file():
                    continue
                words: set[str] = set()
                with path.open("r", encoding="utf-8") as handle:
                    for raw_line in handle:
                        line = raw_line.strip()
                        if not line:
                            continue
                        words.update(item.strip().lower() for item in line.split())
                if words:
                    return words
            except (OSError, UnicodeError):
                continue

        return set(self.FALLBACK_STOPWORDS)

    @staticmethod
    def _normalize_token(token: str) -> str:
        token = token.replace("_", " ")
        token = token.strip(" \t\r\n,.;:!?\"'`()[]{}<>“”‘’")
        return token.strip().lower()

    def _tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        text = text.replace("\u00a0", " ").replace("_", " ")
        return [
            raw
            for raw in self.TOKEN_RE.findall(text)
            if self._normalize_token(raw)
        ]

    def _is_stopword(self, token: str) -> bool:
        return self._normalize_token(token) in self.stopwords

    @staticmethod
    def _is_numeric(token: str) -> bool:
        compact = token.replace(",", "").replace(".", "")
        return compact.isdigit()

    @staticmethod
    def _has_letters(token: str) -> bool:
        return any(ch.isalpha() for ch in token)

    @staticmethod
    def _looks_like_entity_token(token: str) -> bool:
        if any(ch.isdigit() for ch in token) and any(ch.isalpha() for ch in token):
            return True
        letters = [ch for ch in token if ch.isalpha()]
        return bool(letters) and token[:1].isupper()

    def fit(self, documents: Iterable[str]) -> "VietnameseKeywordExtractor":
        documents_list = [
            str(doc).strip()
            for doc in documents
            if doc is not None and str(doc).strip()
        ]
        if not documents_list:
            raise ValueError("Cannot fit keyword extractor on an empty corpus.")

        self.documents_count = len(documents_list)
        print(
            f"[KeywordExtractor {self.VERSION}] fitting {self.documents_count} documents...",
            flush=True,
        )

        self.vectorizer.fit(documents_list)
        self._vocabulary = dict(self.vectorizer.vocabulary_)
        self._feature_names = self.vectorizer.get_feature_names_out()

        self.total_tokens = 0
        self.unigram_counts.clear()
        self.bigram_counts.clear()
        self.trigram_counts.clear()
        self.fourgram_counts.clear()
        self.fivegram_counts.clear()

        for document in documents_list:
            tokens = [
                self._normalize_token(token)
                for token in self._tokenize(document)
            ]
            tokens = [token for token in tokens if token]
            self.total_tokens += len(tokens)

            if not tokens:
                continue

            self.unigram_counts.update(tokens)
            if len(tokens) >= 2:
                self.bigram_counts.update(zip(tokens, tokens[1:]))
            if len(tokens) >= 3:
                self.trigram_counts.update(zip(tokens, tokens[1:], tokens[2:]))
            if len(tokens) >= 4:
                self.fourgram_counts.update(zip(tokens, tokens[1:], tokens[2:], tokens[3:]))
            if len(tokens) >= 5:
                self.fivegram_counts.update(
                    zip(tokens, tokens[1:], tokens[2:], tokens[3:], tokens[4:])
                )

        self.total_bigrams = max(self.total_tokens - self.documents_count, 0)
        self.total_trigrams = max(self.total_tokens - 2 * self.documents_count, 0)
        self.total_fourgrams = max(self.total_tokens - 3 * self.documents_count, 0)
        self.total_fivegrams = max(self.total_tokens - 4 * self.documents_count, 0)

        self._fitted = True
        return self

    def _get_tfidf_scores(self, text: str) -> dict[str, float]:
        if not self._fitted:
            raise RuntimeError("Extractor has not been fitted. Call fit() first.")

        matrix = self.vectorizer.transform([text])
        if matrix.nnz == 0:
            return {}

        scores: dict[str, float] = {}
        row = matrix.getrow(0)
        for index, value in zip(row.indices, row.data):
            feature = self._feature_names[index]
            scores[feature] = float(value)
        return scores

    def _numeric_quality(self, tokens: tuple[str, ...]) -> bool:
        numeric_only = [token for token in tokens if self._is_numeric(token)]

        # One numeric token is acceptable for values/products:
        # "1 triệu đồng", "90 ngày", "iPhone 18 Pro Max".
        if len(numeric_only) <= 1:
            return True

        # Multiple standalone numeric tokens inside a phrase are usually
        # malformed tokenization, e.g. "845.100 tệ 3 3".
        return False

    def _candidate_is_valid(self, tokens: tuple[str, ...]) -> bool:
        n = len(tokens)
        if n < 1 or n > self.NGRAM_RANGE[1]:
            return False

        if self._is_stopword(tokens[0]) or self._is_stopword(tokens[-1]):
            return False

        if not any(self._has_letters(token) for token in tokens):
            return False

        if all(self._is_numeric(token) for token in tokens):
            return False

        if not self._numeric_quality(tokens):
            return False

        if n == 1:
            normalized = self._normalize_token(tokens[0])
            if len(normalized) <= 2 and not self._looks_like_entity_token(tokens[0]):
                return False

        return True

    def _generate_candidates(self, tokens: list[str]) -> dict[str, dict[str, object]]:
        candidates: dict[str, dict[str, object]] = {}
        n_tokens = len(tokens)

        for size in range(self.NGRAM_RANGE[0], self.NGRAM_RANGE[1] + 1):
            if n_tokens < size:
                continue
            for start in range(0, n_tokens - size + 1):
                raw_tuple = tuple(tokens[start:start + size])
                if not self._candidate_is_valid(raw_tuple):
                    continue

                normalized_tuple = tuple(self._normalize_token(token) for token in raw_tuple)
                key = " ".join(normalized_tuple)
                if not key:
                    continue

                existing = candidates.get(key)
                if existing is None:
                    candidates[key] = {
                        "key": key,
                        "tokens": normalized_tuple,
                        "display": " ".join(raw_tuple),
                        "freq": 1,
                        "entity_like": (
                            all(self._looks_like_entity_token(token) for token in raw_tuple)
                            if size > 1
                            else self._looks_like_entity_token(raw_tuple[0])
                        ),
                    }
                else:
                    existing["freq"] = int(existing["freq"]) + 1

        return candidates

    def _ngram_frequency(self, tokens: tuple[str, ...]) -> int:
        n = len(tokens)
        if n == 1:
            return self.unigram_counts.get(tokens[0], 0)
        if n == 2:
            return self.bigram_counts.get(tokens, 0)
        if n == 3:
            return self.trigram_counts.get(tokens, 0)
        if n == 4:
            return self.fourgram_counts.get(tokens, 0)
        if n == 5:
            return self.fivegram_counts.get(tokens, 0)
        return 0

    def _total_ngram_count(self, n: int) -> int:
        return {
            2: max(self.total_bigrams, 1),
            3: max(self.total_trigrams, 1),
            4: max(self.total_fourgrams, 1),
            5: max(self.total_fivegrams, 1),
        }.get(n, 1)

    def _pmi_for_tokens(self, tokens: tuple[str, ...]) -> float:
        n = len(tokens)
        if n <= 1:
            return 0.0

        total = max(float(self.total_tokens), 1.0)
        unigram_product = 1.0
        for token in tokens:
            count = self.unigram_counts.get(token, 0)
            if count <= 0:
                return 0.0
            unigram_product *= count / total

        count_ngram = self._ngram_frequency(tokens)
        total_ngram = self._total_ngram_count(n)
        if count_ngram <= 0:
            return 0.0

        p_ngram = count_ngram / total_ngram
        if p_ngram <= 0:
            return 0.0

        pmi = math.log2(p_ngram / unigram_product)
        return pmi if math.isfinite(pmi) else 0.0

    def _association_boost(self, tokens: tuple[str, ...]) -> tuple[float, float]:
        if len(tokens) == 1:
            return 1.0, 0.0

        pmi = self._pmi_for_tokens(tokens)
        frequency = self._ngram_frequency(tokens)
        total_ngram = self._total_ngram_count(len(tokens))
        p_ngram = max(frequency / total_ngram, 1e-12)
        denominator = max(-math.log2(p_ngram), 1e-9)
        npmi = max(-1.0, min(1.0, pmi / denominator))

        reliability = min(1.0, math.sqrt(max(frequency, 0) / self.MIN_RELIABLE_FREQ))
        signal = math.tanh(npmi * self.NPMI_SCALE)
        boost = 1.0 + self.ASSOCIATION_STRENGTH * signal * reliability
        boost = max(self.MIN_ASSOCIATION, min(self.MAX_ASSOCIATION, boost))
        return float(boost), float(pmi)

    def _phrase_quality(self, tokens: tuple[str, ...], *, entity_like: bool = False) -> float:
        if not tokens:
            return 0.0

        n = len(tokens)
        score = 1.0

        internal_stopwords = sum(
            1 for token in tokens[1:-1] if self._is_stopword(token)
        )
        if internal_stopwords:
            score *= max(0.78, 1.0 - 0.07 * internal_stopwords)

        # Long phrases get only a modest quality advantage.
        if n == 2:
            score *= 1.02
        elif n == 3:
            score *= 1.04
        elif n == 4:
            score *= 1.05
        elif n == 5:
            score *= 1.06

        if entity_like:
            score *= 1.06

        return float(max(0.45, min(score, 1.20)))

    def _frequency_boost(self, frequency: int) -> float:
        if frequency <= 0:
            return 1.0
        return float(min(1.24, 1.0 + 0.08 * math.log1p(frequency)))

    def _title_boost(self, phrase: str, title: str | None) -> float:
        if not title:
            return 1.0

        phrase_tokens = [self._normalize_token(t) for t in self._tokenize(phrase)]
        title_tokens = [self._normalize_token(t) for t in self._tokenize(title)]
        if not phrase_tokens or len(phrase_tokens) > len(title_tokens):
            return 1.0

        size = len(phrase_tokens)
        for i in range(len(title_tokens) - size + 1):
            if title_tokens[i:i + size] == phrase_tokens:
                return self.TITLE_BOOST_VALUE
        return 1.0

    def _score_candidate(
        self,
        *,
        phrase: str,
        tokens: tuple[str, ...],
        tfidf: float,
        frequency: int,
        title: str | None,
        entity_like: bool,
    ) -> dict[str, object]:
        n = len(tokens)
        phrase_weight = self.PHRASE_WEIGHTS.get(n, 1.0)
        association_boost, pmi = self._association_boost(tokens)
        phrase_quality = self._phrase_quality(tokens, entity_like=entity_like)
        frequency_boost = self._frequency_boost(frequency)
        title_boost = self._title_boost(phrase, title)

        score = (
            float(tfidf)
            * phrase_weight
            * association_boost
            * phrase_quality
            * frequency_boost
            * title_boost
        )

        return {
            "phrase": phrase,
            "ngram": {
                1: "unigram",
                2: "bigram",
                3: "trigram",
                4: "fourgram",
                5: "fivegram",
            }.get(n, f"{n}-gram"),
            "freq": int(frequency),
            "tfidf": float(tfidf),
            "score": float(score),
            "pmi": float(pmi),
            "association_boost": float(association_boost),
            "phrase_quality": float(phrase_quality),
            "frequency_boost": float(frequency_boost),
            "title_boost": float(title_boost),
        }

    @staticmethod
    def _contains_consecutive(longer: tuple[str, ...], shorter: tuple[str, ...]) -> bool:
        if len(shorter) >= len(longer):
            return False
        k = len(shorter)
        return any(longer[i:i + k] == shorter for i in range(len(longer) - k + 1))

    @staticmethod
    def _token_set_overlap(left: tuple[str, ...], right: tuple[str, ...]) -> float:
        if not left or not right:
            return 0.0
        a, b = set(left), set(right)
        return len(a & b) / max(len(a | b), 1)

    def _reduce_nested_phrases(
        self,
        ranked: list[dict[str, object]],
        *,
        top_k: int,
    ) -> list[dict[str, object]]:
        if not ranked:
            return []

        ordered = sorted(
            ranked,
            key=lambda item: (
                float(item["score"]),
                len(str(item["phrase"]).split()),
                int(item["freq"]),
            ),
            reverse=True,
        )

        selected: list[dict[str, object]] = []

        for candidate in ordered:
            candidate_tokens = tuple(
                str(candidate["phrase"]).casefold().split()
            )
            candidate_score = float(candidate["score"])
            skip = False

            for existing in list(selected):
                existing_tokens = tuple(
                    str(existing["phrase"]).casefold().split()
                )
                existing_score = float(existing["score"])

                # Stronger longer phrase replaces a contained shorter phrase.
                if (
                    len(candidate_tokens) > len(existing_tokens)
                    and self._contains_consecutive(candidate_tokens, existing_tokens)
                    and candidate_score >= existing_score * 0.70
                ):
                    selected.remove(existing)
                    continue

                # Existing longer phrase suppresses candidate shorter phrase.
                if (
                    len(existing_tokens) > len(candidate_tokens)
                    and self._contains_consecutive(existing_tokens, candidate_tokens)
                    and existing_score >= candidate_score * 0.70
                ):
                    skip = True
                    break

                overlap = self._token_set_overlap(existing_tokens, candidate_tokens)
                if (
                    overlap >= 0.85
                    and abs(len(existing_tokens) - len(candidate_tokens)) <= 1
                    and candidate_score <= existing_score * 1.10
                ):
                    skip = True
                    break

            if not skip:
                selected.append(candidate)

        selected.sort(
            key=lambda item: (
                float(item["score"]),
                len(str(item["phrase"]).split()),
            ),
            reverse=True,
        )
        return selected[:top_k]

    def extract(
        self,
        text: str,
        top_k: int = 10,
        title: str | None = None,
    ) -> list[dict[str, object]]:
        if not self._fitted:
            raise RuntimeError("Extractor has not been fitted. Call fit(documents) first.")
        if not text or not str(text).strip():
            return []

        top_k = max(int(top_k), 1)
        text = str(text).strip()
        display_tokens = self._tokenize(text)
        if not display_tokens:
            return []

        candidates = self._generate_candidates(display_tokens)
        if not candidates:
            return []

        tfidf_scores = self._get_tfidf_scores(text)
        ranked: list[dict[str, object]] = []

        for key, candidate in candidates.items():
            tokens = tuple(str(token) for token in candidate["tokens"])
            if key not in self._vocabulary:
                continue

            tfidf = tfidf_scores.get(key, 0.0)
            if tfidf <= 0.0:
                continue

            ranked.append(
                self._score_candidate(
                    phrase=str(candidate["display"]),
                    tokens=tokens,
                    tfidf=tfidf,
                    frequency=int(candidate["freq"]),
                    title=title,
                    entity_like=bool(candidate["entity_like"]),
                )
            )

        if not ranked:
            return []

        ranked.sort(
            key=lambda item: (
                float(item["score"]),
                float(item["tfidf"]),
                int(item["freq"]),
            ),
            reverse=True,
        )

        ranked = ranked[: self.MAX_CANDIDATES]
        return self._reduce_nested_phrases(ranked, top_k=top_k)

    def extract_keywords(
        self,
        text: str,
        top_k: int = 10,
        title: str | None = None,
    ) -> list[dict[str, object]]:
        return self.extract(text=text, top_k=top_k, title=title)


__all__ = ["VietnameseKeywordExtractor"]