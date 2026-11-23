# Case study: making model output reviewable

## Problem

Unstructured device descriptions mix facts, seller claims, omissions and ambiguous wording. Images can show accessories or device surfaces that are not described in text, and several images may belong to the same device. A prediction alone is insufficient for a reliable review.

## Work in the larger project

The private application connects data ingestion, device-attribute normalisation, text annotation, image-region annotation, local model training and a dashboard for repeated review. Human annotations are kept separate from model drafts. Text and image predictions are stored with their sources and model versions.

The modelling work includes character-based text classification, weighted use of reviewed and weak labels, object/region detection, view classification and separate handling of visual attributes versus condition. The broader workflow supports batch processing and manual follow-up.

This public edition extracts a compact inspection layer. It is a curated adaptation, not the complete production repository. Its interface and examples were created specifically for public presentation.

## Decisions that matter

**Start with an explainable text baseline.** Character features offer a practical baseline for noisy device descriptions without requiring a hosted language model. Classifier outputs and rule-matched source passages remain distinguishable.

**Localise before assessing condition.** Full photos contain packaging, accessories and backgrounds. Cropping a detected device gives downstream models a consistent scope, while coordinate projection keeps findings attached to the source photo.

**Represent missing knowledge explicitly.** A reviewed negative and an unreviewed label have different meanings. Partial image labels are masked during training. A missing photo or missing detection does not establish a clean device.

**Split by the unit of use.** Images from one listing are related. Exact duplicates can connect different listings. Grouping these relationships before splitting prevents an obvious source of evaluation leakage.

**Review the evidence, not just the score.** The interface shows a description, visual source and suggestions together. Scores are labelled as uncalibrated, and review acknowledgement does not silently confirm model outputs.

## What this repository proves

The runnable public slice demonstrates training/inference separation, portable model parameters, image preprocessing, partial-label learning, geometry, explicit uncertainty and an interactive local interface.

It does not establish production readiness, commercial results, a general-purpose device inspector or reliable damage detection. The default image annotations are authored illustrations; real inference is available through the device-view model.

## Current limitations and next work

The synthetic text benchmark shares vocabulary and templates across splits. A useful next evaluation would use independently written, reviewed descriptions. The released vision checkpoint has only historical internal evaluation, with uneven performance across the broader class set. A public, permission-cleared image benchmark would make future comparisons reproducible.

Calibration, broader device coverage and a separately validated condition detector remain future work. Private operational details are outside the scope of this case study.
