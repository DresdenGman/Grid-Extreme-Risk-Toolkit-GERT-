# GERT 1.1.0 — Historical Lab

Try the [Historical Lab](https://gert-d.vercel.app/history) or start a
[10-minute independent review](https://gert-d.vercel.app/review).

This release adds a complete historical analysis workflow:

- Three source-linked ERCOT native-load cases, 72 hourly observations each.
- User-defined capacity and uniform load reduction, with immediate before/after comparison.
- Exceedance-hour counts, integrated gap energy, and the algebraic peak-clearing reduction.
- JSON reports, hourly CSV exports, and links preserving analysis inputs.
- Public source checksums, a reproducible archive extractor, and a Python report verifier.
- A structured GitHub review template and a 20-minute workshop guide.

The lab uses observed load and hypothetical planning assumptions. It does not
claim operational forecasting, avoided outages, or realized savings. The
probabilistic candidate's production gates remain unchanged.

Feedback request: independently reproduce one result or identify one missing
constraint that matters for interpreting the result. Use the **Historical Lab
independent review** issue template and include the case and assumptions.

Local verification: 35 frontend tests passed; production build and TypeScript
checks passed. A real browser-exported 72-row JSON report was independently
verified with the Python checker. These are maintainer checks, not third-party
validation or adoption.
