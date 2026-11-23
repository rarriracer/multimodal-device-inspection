"""Rebuild the public baseline only from the bundled synthetic examples."""
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from device_inspection.text import features, matrix, FIELDS, TextModel

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = json.loads((ROOT / "examples/text_training.json").read_text())
    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] == "test"]
    df = Counter(token for r in train for token in features(r["text"]))
    vocabulary = {token: i for i, token in enumerate(sorted(t for t, count in df.items() if count >= 2))}
    idf = [float(np.log((1+len(train))/(1+df[token]))+1) for token in vocabulary]
    x = matrix([r["text"] for r in train], vocabulary, idf)
    payload = {"schema": "inspection-text/1", "version": "synthetic-text/1", "vocabulary": vocabulary,
               "idf": idf, "heads": {}, "training_data": "bundled synthetic examples only"}
    for field in FIELDS:
        model = LogisticRegression(max_iter=500, class_weight="balanced", C=4, random_state=42)
        model.fit(x, [r["labels"][field] for r in train])
        payload["heads"][field] = {"classes": model.classes_.tolist(), "coef": model.coef_.tolist(),
                                    "intercept": model.intercept_.tolist()}
    path = ROOT / "models/text_baseline.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"))+"\n")
    model = TextModel(path)
    predictions = [model.predict(r["text"])["fields"] for r in test]
    report = {"scope": "Synthetic smoke benchmark; not real-world accuracy", "train_samples": len(train),
              "test_samples": len(test), "fields": {}}
    for field in FIELDS:
        report["fields"][field] = classification_report([r["labels"][field] for r in test],
            [r[field]["value"] for r in predictions], output_dict=True, zero_division=0)
    (ROOT / "models/text_evaluation.json").write_text(json.dumps(report, indent=2)+"\n")
    print(f"Trained {len(FIELDS)} heads on {len(train)} synthetic examples; {len(test)} synthetic test cases.")


if __name__ == "__main__":
    main()
