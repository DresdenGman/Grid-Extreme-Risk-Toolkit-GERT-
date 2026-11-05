# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions use
[semantic versioning](https://semver.org/).

## [Unreleased]

### Added

- Zenodo software archive for the 1.2.0 release: version DOI
  10.5281/zenodo.23982227, concept DOI 10.5281/zenodo.23982226. The README
  badge row now labels the software and dataset DOIs separately, and
  CITATION.cff records the concept DOI and the 1.2.0 release date.

## [1.2.0] - 2026-11-05

### Fixed

- Frontend dependency vulnerabilities that had kept CI red since mid-October:
  `next` 16.4.1 (critical unauthenticated RCE advisories), `vite` 8.3.6,
  `vitest` 4.1.12, `undici` 7.30.2. The full lockfile now has no high or
  critical findings and CI is green again.
- Bulletin timestamps render the actual minutes instead of a hard-coded `:00`.

### Changed

- Model naming corrected to match the implementation: the estimator is a
  gradient-boosting regressor with empirical residual quantiles, so version
  strings and demo/presentation identifiers no longer say "conformal" or
  "quantile regression forest".
- Demo-mode backtest entries are labeled as illustrative simulated values,
  not measured model performance.
- Data-source descriptions corrected in `DEPLOYMENT.md`,
  `docs/REAL_DATA_SETUP.md`, and `docs/PROJECT_INTRO.md`: ERCOT is the only
  real feed (official API, with any fallback returned as a clearly labeled
  `estimated_fallback`); the CAISO/PJM/NYISO adapters return labeled
  estimates, not live data.
- `DEPLOYMENT.md` status section rewritten to describe the actual deployment
  state instead of local-dev boilerplate.
- README first screen restructured: audience routing table, evidence tables
  tied to machine-readable artifacts, and a drift-guard test that fails CI if
  the printed numbers diverge from the evidence files.
- The social-preview/banner image was re-encoded without embedded provenance
  metadata (pixels unchanged).

### Added

- `ROADMAP.md`, this changelog, `CODE_OF_CONDUCT.md`, a pull-request
  template, and repository topics.
- Historical Lab pilot feedback report (`docs/FEEDBACK.md`) with aggregate
  data and a reproducible analysis script (`data/feedback/`).
- Regression tests for the bulletin timestamp format and README evidence
  drift (backend suite: 135 tests).

### Removed

- Leftover pre-Next.js template files at the repository root
  (`index.html`, `index.tsx`, `metadata.json`) and stale merged branches.

## [1.1.0] - 2026-09-13

### Added

- Historical Lab: three source-linked ERCOT native-load cases of 72 hourly
  observations each, with user-defined capacity and uniform load reduction,
  before/after exceedance-hour counts, integrated gap energy, and the
  algebraic peak-clearing reduction.
- JSON reports and hourly CSV exports, public source checksums, a
  reproducible archive extractor, and a Python report verifier.
- A structured GitHub review template and a 20-minute workshop guide.
