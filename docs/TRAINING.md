# Training and evaluation

## Public text baseline

```bash
python -m pip install '.[training]'
python scripts/train_text.py
```

This reads only `examples/text_training.json`, fits features on the training split, exports the three linear heads and evaluates the fixed synthetic holdout. `scripts/create_examples.py` rebuilds the original fixtures and SVG illustrations deterministically; it does not contact any data source.

The fixture split is deliberately small and templated. It does not support a real-world accuracy claim. Do not select future model changes against this holdout and continue describing it as an untouched test.

## Image-view training

Install `.[vision]`. Supply a local TorchVision ResNet18 base state dictionary and a permission-cleared image manifest:

```json
[
  {
    "photo_id": "photo-001",
    "listing_id": "example-device-001",
    "path": "images/device-001.jpg",
    "labels": {"display": true, "back": false, "camera": null}
  }
]
```

This is a schema example, not a sufficient dataset. Include enough independently reviewed groups to populate training, validation and test. Paths are relative to the manifest. A `true` or `false` value must represent a reviewed label; missing or null means unknown.

```bash
python scripts/train_views.py runtime/my-images/manifest.json \
  --base-weights runtime/resnet18-base.pth \
  --output runtime/view-training \
  --epochs 8
```

The script groups complete listings and exact file duplicates before splitting, excludes unlabelled targets from the loss, selects a checkpoint on validation loss and evaluates test loss once after selection. It saves tensor-only parameters and a local report. No default image dataset is distributed. Reproducing the included model's historical performance requires the original private data and training configuration, which are intentionally absent.

## Optional detector integration

`LocalDetector` in `src/device_inspection/vision.py` can wrap explicitly supplied local Ultralytics weights after installing `.[detection]`. The `inspect_photos` function accepts callable feature and condition predictors, processes all supplied photos, pads device crops and maps crop findings back to original coordinates.

Detector weights are not included. This optional path is separate from the bundled ResNet18 classifier. Upstream code and weights have their own terms. It is not necessary to install the detection extra to run the public demo.

## Tests

```bash
python -m unittest discover -s tests -v
```

Core checks cover negation, unknown inputs, passage offsets, fixture overlap, connected listing/duplicate groups, crop projection, incomplete image coverage and invalid boxes. With the vision extra, additional checks run the bundled model and verify that unknown labels have no gradient contribution.

CI is configured for Python 3.10/3.12 core checks and a separate CPU vision job. A configured workflow is not a claim that GitHub has executed it yet.
