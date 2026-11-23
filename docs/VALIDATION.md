# Release validation

Prepared on 2026-11-23. These are local checks, not a claim that hosted CI has run.

| Check | Result |
|---|---|
| Full Python suite with vision dependencies, Python 3.12 | 11 tests passed, including actual checkpoint inference and masked-label gradients |
| Core checks without vision dependencies | Passed; optional vision checks skipped as designed |
| Text baseline reconstruction | 385 synthetic training examples, 47 synthetic test combinations; JSON model and report regenerated |
| Python package build | Wheel built successfully with Python 3.12 and the configured setuptools backend |
| Local HTTP API | Actual text and image inference passed |
| API boundaries | Invalid inputs and cross-origin requests rejected; private/static path boundaries checked |
| Browser behaviour | Action Board search, filters, actual text inference and review navigation; light/dark themes, listing filters, front/back view selection, stale-result invalidation and separate manual labels checked |
| Visual QA | Four desktop screenshots in the original dashboard design: Action Board, text review, image review and model overview, captured from the running demo and visually inspected |
| Publication audit | Token/path/address patterns, prohibited file types and selected tensor metadata checked |

## Interpretation

These checks verify the public application's behaviour and packaging. They do not establish accuracy on independent real-world descriptions or photos. The text evaluation is synthetic. Historical image metrics are documented separately with their scope and limitations.

The scanner is a pattern-based check, not a formal proof that no confidential information exists in any possible form. The publication folder was built from an explicit selection of code, fictional fixtures and a tensor-only model export rather than a copy of the private repository.

`RELEASE_MANIFEST.json` records the SHA-256 hashes of release files. The packaged ZIP excludes caches, build output, runtime data and Git metadata.
