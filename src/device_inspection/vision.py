"""Actual local view inference and an optional two-stage detector adapter."""
from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image, ImageOps


class ViewModel:
    def __init__(self, path):
        import torch
        from torchvision import models, transforms
        self.torch = torch
        # Only tensors and public labels. No executable pickle/checkpoint metadata.
        with np.load(path, allow_pickle=False) as weights:
            self.labels = weights["labels"].tolist()
            self.model = models.resnet18(weights=None)
            self.model.fc = torch.nn.Linear(self.model.fc.in_features, len(self.labels))
            self.model.load_state_dict({key: torch.from_numpy(weights[key].copy())
                                       for key in weights.files if key != "labels"})
        self.model.eval()
        self.transform = transforms.Compose([transforms.Resize((384, 384)), transforms.ToTensor(),
            transforms.Normalize([.485, .456, .406], [.229, .224, .225])])

    def predict(self, image):
        image = ImageOps.exif_transpose(image).convert("RGB")
        with self.torch.inference_mode():
            scores = self.model(self.transform(image).unsqueeze(0)).sigmoid()[0].tolist()
        return {"model": "device-views/1", "scope": "single_device_crop",
                "attributes": [{"label": label, "score": round(score, 4)}
                               for label, score in zip(self.labels, scores)],
                "score_calibrated": False, "requires_review": True,
                "condition_verdict": "unresolved"}


def crop_bounds(box, size, padding=0.1):
    width, height = size
    x1, y1, x2, y2 = box
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height) or not 0 <= padding <= .5:
        raise ValueError("Invalid device bounds or padding")
    dx, dy = (x2-x1)*padding, (y2-y1)*padding
    return (max(0, int(x1-dx)), max(0, int(y1-dy)),
            min(width, int(x2+dx)), min(height, int(y2+dy)))


def inspect_photos(photos, feature_predictor, condition_predictor):
    """Injectable predictors keep geometry and review semantics testable."""
    output = []
    for photo in photos:
        row = {"photo_id": photo["photo_id"], "status": "pending", "devices": []}
        try:
            with Image.open(photo["path"]) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
            detections = feature_predictor(image)
            row["objects"] = detections
            for detection in detections:
                if detection["label"] not in ("phone", "iphone"):
                    continue
                bounds = crop_bounds(detection["xyxy"], image.size)
                if min(bounds[2]-bounds[0], bounds[3]-bounds[1]) < 100:
                    row["devices"].append({"status": "crop_too_small"})
                    continue
                findings = condition_predictor(image.crop(bounds))
                translated = [{**f, "xyxy": [f["xyxy"][0]+bounds[0], f["xyxy"][1]+bounds[1],
                                               f["xyxy"][2]+bounds[0], f["xyxy"][3]+bounds[1]]}
                              for f in findings]
                row["devices"].append({"status": "processed", "crop": bounds, "findings": translated})
            row["status"] = "processed"
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            row.update(status="error", error=type(exc).__name__)
        output.append(row)
    observed = any(d.get("findings") for p in output for d in p["devices"])
    return {"photos": output, "coverage_complete": bool(output) and all(p["status"] == "processed" for p in output),
            "condition_verdict": "finding_requires_review" if observed else "unresolved"}


class LocalDetector:
    """Optional adapter: explicitly supplied trusted weights; no auto-download."""
    def __init__(self, path, threshold=0.25):
        if not Path(path).is_file():
            raise FileNotFoundError(path)
        from ultralytics import YOLO
        self.model, self.threshold = YOLO(str(path)), threshold

    def __call__(self, image):
        result = self.model.predict(image, conf=self.threshold, device="cpu", verbose=False)[0]
        return [{"label": result.names[int(box.cls.item())], "score": float(box.conf.item()),
                 "xyxy": box.xyxy[0].cpu().tolist()} for box in result.boxes]
