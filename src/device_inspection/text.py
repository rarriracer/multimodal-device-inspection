"""Character TF-IDF + linear heads; JSON weights, no pickle or network calls."""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
import re

import numpy as np

FIELDS = ("screen_damage", "cable_included", "account_lock")
TOPICS = {"screen_damage": r"display|bildschirm", "cable_included": r"kabel|lieferumfang",
          "account_lock": r"icloud|apple.id|aktivierung|kontostatus|konto"}


def features(text):
    counts = Counter()
    for word in re.sub(r"\s+", " ", text.lower()).split():
        padded = " " + word + " "
        for n in (3, 4, 5):
            counts.update(padded[i:i+n] for i in range(max(0, len(padded)-n+1)))
    return counts


def matrix(texts, vocabulary, idf):
    x = np.zeros((len(texts), len(vocabulary)), dtype=np.float64)
    for row, text in enumerate(texts):
        for token, count in features(text).items():
            col = vocabulary.get(token)
            if col is not None:
                x[row, col] = (1 + math.log(count)) * idf[col]
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(norm, 1e-12)


class TextModel:
    def __init__(self, path):
        self.data = json.loads(Path(path).read_text(encoding="utf-8"))
        if self.data.get("schema") != "inspection-text/1":
            raise ValueError("Unsupported text model schema")

    def predict(self, text):
        if not isinstance(text, str) or len(text) > 20000:
            raise ValueError("Text must contain at most 20,000 characters")
        x = matrix([text], self.data["vocabulary"], self.data["idf"])
        result = {}
        for field, head in self.data["heads"].items():
            logits = (x @ np.asarray(head["coef"]).T + head["intercept"])[0]
            scores = np.exp(logits - logits.max())
            scores /= scores.sum()
            index = int(scores.argmax())
            # Empty or out-of-vocabulary text must not produce a factual claim.
            known = bool(np.any(x)) and bool(re.search(TOPICS[field], text, re.I))
            result[field] = {"value": head["classes"][index] if known else "unknown",
                             "score": round(float(scores[index]), 4) if known else 0.0,
                             "model_value": head["classes"][index],
                             "decision_source": "model" if known else "missing_topic_guard",
                             "source": "synthetic_text_baseline", "requires_review": True,
                             "score_calibrated": False}
        return {"model": self.data["version"], "fields": result,
                "evidence": phrase_evidence(text), "training_data": "synthetic",
                "physical_verification": False}


# These passages are rule matches, not explanations of the linear classifier.
PATTERNS = {
    "screen_damage": r"(?:keine?\s+(?:kratzer|risse)|ohne\s+(?:kratzer|risse)|display[^.!;\n]*(?:kratzer|riss|gesprungen)|kratzer[^.!;\n]*display)",
    "cable_included": r"(?:ohne\s+(?:lade)?kabel|(?:lade)?kabel\s+(?:fehlt|dabei|enthalten|liegt bei|nicht enthalten))",
    "account_lock": r"(?:icloud[^.!;\n]*(?:entfernt|aktiv|abgemeldet)|aktivierungssperre[^.!;\n]*|apple-id[^.!;\n]*(?:entfernt|verknüpft))",
}


def phrase_evidence(text):
    return [{"field": field, "text": match.group(), "start": match.start(),
             "end": match.end(), "source": "phrase_rule"}
            for field, pattern in PATTERNS.items()
            for match in re.finditer(pattern, text, re.I)]
