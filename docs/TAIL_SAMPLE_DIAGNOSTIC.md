# What 96 hours can and cannot tell us about P99

Run a dependency-free diagnostic on the published candidate evidence:

```bash
python scripts/diagnose_tail_sample.py
python -m unittest discover -s tests -p test_tail_sample_diagnostic.py
```

The JSON includes the input evidence SHA-256, inferred counts, coverage
resolution, and explicitly labeled IID sample-size illustrations. It never
changes candidate artifacts or promotion gates. Changing `--tolerance` explores
the arithmetic of a hypothetical tolerance; it does not amend the contract.

For v1.4, the published P99 coverage implies 4 exceedances in 96 observations.
One observation changes empirical coverage by approximately 1.04 percentage
points. Under an absolute coverage tolerance of 0.03, 0–3 exceedances would pass
that arithmetic gate. Three exceedances correspond to 3.125%, compared with a
nominal P99 exceedance rate of 1%. A uniform absolute tolerance therefore has
different relative tail-risk meanings at different quantiles.

Even if independent trials truly have 99% coverage, the probability of seeing
zero exceedances in 96 trials is about 38.1%. With zero failures, at least 299
independent trials are needed for the one-sided 95% binomial upper bound on the
failure rate to be at most 1%. These numbers are illustrations, not a required
grid deployment sample size. Hourly forecast errors are dependent, and hundreds
of ordinary hours do not establish performance during multiple extreme events.

The existing candidate remains rejected. An apparent improvement on this
already-inspected window is not a new untouched test.

## Next evaluation

Collect aligned, timestamped forecasts and observations before comparing:

- aggregate and event-specific coverage;
- pinball loss and sharpness;
- longest consecutive exceedance and exceedance-cluster duration;
- uncertainty estimates appropriate for temporal dependence and the number of
  independent events available.

Define event selection, time splits, baselines and scoring before the next
confirmatory evaluation. Preserve the old rejection. Do not infer cluster
lengths from the aggregate evidence: four scattered errors and four consecutive
errors have the same aggregate coverage.

These are load-forecast errors. They are not measured outages, prevented losses
or unserved energy. Publication of a diagnostic is not external validation.

Research entry point: Gibbs and Candès, [Adaptive Conformal Inference Under
Distribution Shift](https://arxiv.org/abs/2106.00170). Its long-run coverage
results do not by themselves guarantee coverage during each extreme event.
