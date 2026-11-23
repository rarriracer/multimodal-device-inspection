# Vision model card

**Model:** `device-views/1` · **Parameters:** `device_views.npz` · approximately 42 MB

## Task

Recognise three visible device views: `display`, `back` and `camera`. These are independent sigmoid heads, not exclusive categories. Input should be a single-device crop. The model is not a damage detector, device-identity classifier or battery-health reader.

## Implementation and provenance

The architecture is TorchVision ResNet18 with a task-specific output layer. Parameters come from an internally fine-tuned candidate with a wider set of view labels. This public export retains the shared encoder and only the three selected output rows. It contains NumPy tensor arrays and the three public label names, with no source images, optimiser state, training paths or listing identifiers. Loading uses `allow_pickle=False`.

Preprocessing applies EXIF orientation, converts to RGB, resizes to 384×384 and uses ImageNet mean/std normalisation, matching the original training transform. Inference runs on CPU without implicit weight downloads. The training implementation supports partial labels through a masked binary loss.

## Historical internal evaluation

The following figures were recorded for the original candidate on 100 internal held-out photo examples. They are historical measurements, not a newly executed public benchmark. Counts refer to photo examples, not independent devices or listings.

| View | True positives | False positives | False negatives | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Display | 55 | 4 | 2 | 0.932 | 0.965 |
| Back | 30 | 1 | 5 | 0.968 | 0.857 |
| Camera | 27 | 1 | 3 | 0.964 | 0.900 |

The source evaluation data is not included; these figures cannot be independently reproduced from this repository. They do not establish performance on other device families, backgrounds or seller photo styles. Broader view classes had weaker performance and are not included in this checkpoint. Damage detection in the wider project remains experimental and is not represented by these numbers.

## Limits

- Scores are not calibrated probabilities.
- An unrelated image can still receive high scores; the model has no validated out-of-distribution rejection.
- Use a device crop. Full scenes, multiple devices and accessories can confuse the classifier.
- Recognising a visible display does not mean its condition is known.
- Tensor-only packaging removes checkpoint metadata, not all possible information learned during training. The model is not claimed to provide a formal privacy guarantee.

The supplied tests verify that the exported model loads and performs inference. They do not reevaluate real-photo accuracy.

See [third-party notices](../THIRD_PARTY_NOTICES.md) for the TorchVision notice and [training notes](../docs/TRAINING.md) for retraining on your own data.
