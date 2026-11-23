"""Training helpers: listing groups, duplicate protection, partial labels."""
from __future__ import annotations

import hashlib


def group_split(rows, seed="inspection-v1"):
    """Keep all connected listing/duplicate groups in one deterministic split."""
    parent = list(range(len(rows)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    listings, duplicates = {}, {}
    for i, row in enumerate(rows):
        for table, key in ((listings, row["listing_id"]), (duplicates, row["content_sha256"])):
            if key in table:
                parent[root(i)] = root(table[key])
            table[key] = i
    members = {}
    for i, row in enumerate(rows):
        members.setdefault(root(i), []).append(row["listing_id"])
    assignment = {}
    for i, row in enumerate(rows):
        identity = "|".join(sorted(set(members[root(i)])))
        bucket = int(hashlib.sha256((seed+identity).encode()).hexdigest()[:8], 16) % 100
        assignment[row["photo_id"]] = "train" if bucket < 70 else "validation" if bucket < 85 else "test"
    return assignment


def masked_binary_loss(logits, targets, known, sample_weights=None):
    """Unknown is excluded; a reviewed negative is an observed zero."""
    import torch
    raw = torch.nn.functional.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    weight = known.float()
    if sample_weights is not None:
        weight = weight * sample_weights[:, None]
    return (raw * weight).sum() / weight.sum().clamp_min(1)
