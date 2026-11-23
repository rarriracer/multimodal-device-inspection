# Text model card

**Model:** `synthetic-text/1` · **Parameters:** `text_baseline.json`

## Task and implementation

Three independent multinomial linear classifiers predict `yes`, `no` or `unknown` for stated screen damage, cable inclusion and stated account lock. The input is German text. Features are lowercased character 3–5-grams within padded whitespace-delimited words, sublinear term frequency, smoothed inverse document frequency and L2 normalisation.

Training uses scikit-learn logistic regression with balanced classes and a fixed seed. Inference uses the exported JSON parameters and NumPy. A separate topic-presence guard returns unknown when a field is not discussed. The raw classifier value and the guard's provenance remain available in the API result. Rule-matched passages are separate evidence candidates, not learned attributions.

## Data

All 432 texts are fictional combinations produced by `scripts/create_examples.py`. The release contains 385 training examples and 47 held-out combinations. Labels are authored from the generating templates. There are no private descriptions, original listing identifiers, contact details or imported production weights in this text model.

## Evaluation and interpretation

`text_evaluation.json` contains per-class precision, recall and F1 on the synthetic holdout. The current baseline scores perfectly on this small check. The train/test texts share their component templates and vocabulary. These scores verify that the simple pipeline learns these examples; they do not measure performance on independent, real-world descriptions.

Scores are uncalibrated. The model does not verify the device, establish seller truth, estimate price or decide whether to buy anything. Missing, unfamiliar, contradictory or adversarial descriptions can produce errors.

## Reproduction

```bash
python -m pip install '.[training]'
python scripts/train_text.py
```

Retraining requires only bundled synthetic data. Numerical parameters may vary slightly between dependency versions.
