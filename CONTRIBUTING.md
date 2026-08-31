# Contributing to GERT

GERT welcomes technically specific feedback, reproduction reports, tests, and
small, reviewable improvements. The most useful contribution is one that makes
the evidence or decision boundary easier to verify.

## High-value contributions

- Reproduce a reported evaluation metric and document any mismatch.
- Propose a calibration diagnostic with a clear acceptance criterion.
- Identify an operational edge case or ambiguous provenance label.
- Add a focused test for model gating, API truth states, or data-quality checks.
- Improve documentation without overstating model authority.

## Before opening a pull request

1. Open an issue describing the problem, evidence, and intended change.
2. Keep live, simulated, fallback, and unavailable states explicitly separated.
3. Do not weaken a frozen validation threshold after seeing evaluation results.
4. Never add credentials, private data, generated training artifacts, or
   unpublished research material.
5. Run the relevant checks documented in the repository README.

## Research integrity

The current probabilistic candidate is not production-authorized. A contribution
must not relabel a rejected or provisional artifact as validated. GERT is
decision-support research software, not autonomous grid control.
