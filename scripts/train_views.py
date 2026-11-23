"""Fine-tune ResNet18 on an explicitly supplied, permission-cleared dataset.

Manifest: [{"photo_id": "p1", "listing_id": "l1", "path": "images/p1.jpg",
            "labels": {"display": true, "back": false, "camera": null}}]
Missing/null labels are unknown. True/false labels must be explicitly reviewed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("runtime/view-training"))
    parser.add_argument("--base-weights", type=Path, required=True, help="Local torchvision ResNet18 state dict")
    parser.add_argument("--epochs", type=int, default=8)
    args = parser.parse_args()
    import numpy as np
    import torch
    from PIL import Image, ImageOps
    from torch.utils.data import Dataset, DataLoader
    from torchvision import models, transforms
    from device_inspection.learning import group_split, masked_binary_loss
    torch.manual_seed(42)
    if args.epochs < 1:
        parser.error("--epochs must be positive")
    labels = ["display", "back", "camera"]
    rows = json.loads(args.manifest.read_text())
    for row in rows:
        row["path"] = str((args.manifest.parent / row["path"]).resolve())
        row["content_sha256"] = hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest()
        if any(value is not None and not isinstance(value, bool) for value in row["labels"].values()):
            raise ValueError("View labels must be true, false or null")
    splits = group_split(rows)
    transform = transforms.Compose([transforms.Resize((384, 384)), transforms.ToTensor(),
        transforms.Normalize([.485, .456, .406], [.229, .224, .225])])
    class Photos(Dataset):
        def __init__(self, split):
            self.rows = [r for r in rows if splits[r["photo_id"]] == split and
                         any(r["labels"].get(label) is not None for label in labels)]
        def __len__(self):
            return len(self.rows)
        def __getitem__(self, index):
            row = self.rows[index]
            with Image.open(row["path"]) as image:
                x = transform(ImageOps.exif_transpose(image).convert("RGB"))
            return x, torch.tensor([float(row["labels"].get(k) or False) for k in labels]), torch.tensor([
                row["labels"].get(k) is not None for k in labels])
    datasets = {part: Photos(part) for part in ("train", "validation", "test")}
    if any(not dataset for dataset in datasets.values()):
        raise ValueError("Need independently labelled train, validation and test groups")
    model = models.resnet18(weights=None)
    model.load_state_dict(torch.load(args.base_weights, map_location="cpu", weights_only=True))
    model.fc = torch.nn.Linear(model.fc.in_features, len(labels))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    args.output.mkdir(parents=True, exist_ok=True)
    best, history = float("inf"), []
    checkpoint = args.output / "device_views.npz"
    def loss_on(split):
        model.eval()
        total, count = 0., 0.
        with torch.inference_mode():
            for x, y, known in DataLoader(datasets[split], batch_size=4):
                n = int(known.sum())
                total += float(masked_binary_loss(model(x), y, known))*n
                count += n
        return total/max(count, 1)
    for epoch in range(args.epochs):
        model.train()
        # Frozen BN also handles small final batches.
        for module in model.modules():
            if isinstance(module, torch.nn.BatchNorm2d):
                module.eval()
        for x, y, known in DataLoader(datasets["train"], batch_size=4, shuffle=True):
            optimizer.zero_grad()
            loss = masked_binary_loss(model(x), y, known)
            loss.backward()
            optimizer.step()
        validation = loss_on("validation")
        history.append({"epoch": epoch+1, "validation_loss": validation})
        if validation < best:
            best = validation
            np.savez_compressed(checkpoint, labels=np.array(labels),
                                **{k: v.detach().cpu().numpy() for k, v in model.state_dict().items()})
    with np.load(checkpoint, allow_pickle=False) as state:
        model.load_state_dict({k: torch.from_numpy(state[k].copy()) for k in state.files if k != "labels"})
    # Test is evaluated once after selection on validation loss.
    report = {"history": history, "samples": {k: len(v) for k,v in datasets.items()},
              "test_loss": loss_on("test"), "split_by_photo": splits, "score_calibrated": False}
    (args.output / "report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(f"Saved {checkpoint}")


if __name__ == "__main__":
    main()
