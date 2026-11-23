"""Check the publication folder; print locations/rule names, never matched secrets."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {"__pycache__", ".venv", ".git", "runtime", "build", "dist"}
TEXT_SUFFIXES = {".py", ".js", ".mjs", ".css", ".html", ".md", ".json", ".toml", ".yml", ".yaml", ".svg", ".txt"}
RULES = {
    "private-home-path": re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "openai-token": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{25,}\b"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "email-address": re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    "marketplace-url": re.compile(r"https?://[^\s\"<>]*(?:ebay\.|ebayimg\.)",re.I),
}


def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and
                  not any(part in IGNORED or part.endswith('.egg-info') for part in p.relative_to(ROOT).parts))


def audit():
    findings = []
    for p in files():
        rel = p.relative_to(ROOT).as_posix()
        if p.is_symlink():
            findings.append((rel, "symlink"))
        if p.name.startswith('.env') or p.suffix.lower() in {'.pem','.key','.sqlite','.duckdb','.joblib','.pkl','.pt','.pth'}:
            findings.append((rel, "private-or-unreviewed-file-type"))
        if p.suffix.lower() in TEXT_SUFFIXES or p.name in {'NOTICE','.gitignore'}:
            text = p.read_text(encoding='utf-8')
            for name, pattern in RULES.items():
                if pattern.search(text):
                    findings.append((rel, name))
    # Tensor archive contains only numeric tensors and the three public labels.
    import numpy as np
    with np.load(ROOT/'models/device_views.npz',allow_pickle=False) as data:
        if data['labels'].tolist()!=['display','back','camera']:
            findings.append(('models/device_views.npz','unexpected-public-labels'))
        for key in data.files:
            if key!='labels' and (data[key].dtype.kind not in 'fiu' or '/' in key or '\\' in key):
                findings.append(('models/device_views.npz','unexpected-tensor-metadata'))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',action='store_true',help='Create a clean ZIP next to this folder')
    args=parser.parse_args()
    findings=audit()
    if findings:
        for rel,rule in findings:print(f'{rel}: {rule}')
        sys.exit(1)
    selected=files()
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in selected if p.name!='RELEASE_MANIFEST.json'}
    (ROOT/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Publication audit passed: {len(manifest)} files; text patterns, file types and tensor metadata checked.')
    if args.package:
        destination=ROOT.parent/(ROOT.name+'.zip')
        with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for p in files():archive.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
        print(f'Prepared {destination.name} ({destination.stat().st_size/1e6:.1f} MB)')


if __name__=='__main__':
    main()
