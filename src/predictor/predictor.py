
from pathlib import Path
import json
import joblib

from .preprocessing import (
    load_stopwords,
    preprocess_text,
)


class VietnameseNewsPredictor:

    def __init__(self, project_root=None):

        if project_root is None:
            self.project_root = Path(__file__).resolve().parents[2]
        else:
            self.project_root = Path(project_root)

        # Model artifacts
        self.vectorizer_path = (
            self.project_root
            / "models"
            / "p2_tfidf_vectorizer.joblib"
        )

        self.model_path = (
            self.project_root
            / "models"
            / "p2_linear_svm_balanced.joblib"
        )

        self.metadata_path = (
            self.project_root
            / "models"
            / "p2_model_metadata.json"
        )

        self.stopwords_path = (
            self.project_root
            / "data"
            / "stopwords_vi.txt"
        )

        # Load artifacts
        self.vectorizer = joblib.load(self.vectorizer_path)
        self.model = joblib.load(self.model_path)

        with open(
            self.metadata_path,
            "r",
            encoding="utf-8"
        ) as f:
            self.metadata = json.load(f)

        # Load stopwords for metadata / future extensions
        self.stopwords = load_stopwords(
            self.stopwords_path
        )

    # --------------------------------------------------------
    # Preprocessing
    # --------------------------------------------------------

    def preprocess(self, text):
        return preprocess_text(
            text,
            self.stopwords,
        )

    # --------------------------------------------------------
    # Predict one article
    # --------------------------------------------------------

    def predict_one(self, text):

        processed_text = self.preprocess(text)

        if not processed_text:
            return {
                "label": "UNKNOWN",
                "score": None,
                "status": "UNKNOWN"
            }

        X = self.vectorizer.transform([processed_text])

        # Zero-vector => unknown
        if X.nnz == 0:
            return {
                "label": "UNKNOWN",
                "score": None,
                "status": "UNKNOWN"
            }

        prediction = self.model.predict(X)[0]
        scores = self.model.decision_function(X)

        # LinearSVC score is NOT probability
        if scores.ndim == 1:
            score = float(scores[0])
        else:
            score = float(scores.max())

        return {
            "label": prediction,
            "score": score,
            "status": "OK"
        }

    # --------------------------------------------------------
    # Predict batch
    # --------------------------------------------------------

    def predict_batch(self, texts):

        return [
            self.predict_one(text)
            for text in texts
        ]
