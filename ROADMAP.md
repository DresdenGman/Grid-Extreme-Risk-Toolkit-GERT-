# Roadmap

GERT is three things at once: a research tool for grid tail-risk, a teaching
lab used in community pilot sessions, and a candidate product. This roadmap
states the standard the project holds itself to in each role, where it stands
against that standard today, and what comes next. Status claims point to
evidence in this repository; anything not yet evidenced is listed as planned,
not done.

## Where the project stands

| Area | Standard | Status |
| --- | --- | --- |
| Scientific method | Preregistered validation gates; pass/fail decided by numbers fixed in advance; failures published | Met for process — the v1.4 candidate was rejected by its own gate and the record is public ([decision record](docs/DECISION_RECORD_ERCOT_v1_4.md)). The v1.5 scores are evidence only and do not package a model ([decision record](docs/DECISION_RECORD_ERCOT_v1_5.md)). No candidate has passed yet |
| Integrity & security | Every public claim traceable to a checked artifact; dependency audit green | Met as of v1.2 (see [CHANGELOG](CHANGELOG.md)); a drift-guard test fails CI if the README evidence tables diverge from the evidence files |
| Product | A stranger can reproduce the core calculation unaided in ~15 minutes; the hosted demo is honest about what is gated | Mostly met — reproduction path and labeled demo mode are in place; live inference stays gated (HTTP 503) until a candidate passes |
| Teaching impact | Real sessions with counted participants and published feedback, including the weak points | Two pilot sessions run (115+ participants); feedback report published ([docs/FEEDBACK.md](docs/FEEDBACK.md)); third-party adoption beyond author-run sessions has not happened yet |
| Independent validation | Replication by people other than the author; citable archive | Started — one independent reproduction on record, Zenodo DOI [10.5281/zenodo.22975251](https://doi.org/10.5281/zenodo.22975251), listings on OER Commons and MERLOT; scale is the gap |
| Sustainability | A stated model for who benefits, who hosts or pays, and why the project continues without depending on one person's spare time | Not yet — see "Later" below; this page deliberately does not invent one |
| Community | Contributors beyond the author; maintained release cadence | Early — contributions and reviews welcome; release cadence formalized from v1.2 |

## Now

- Publish the Historical Lab pilot feedback report (57 responses) with method
  and limitations — done alongside this roadmap in `docs/FEEDBACK.md`, with
  aggregate data and the analysis script under `data/feedback/`.
- Keep the changelog and releases current from v1.2 onward.

## Next

- **Forecast-weather evaluation of the frozen v1.5 multipliers.** A draft
  preregistration is in
  [docs/PREREGISTRATION_ERCOT_FORECAST_WEATHER_DRAFT.md](docs/PREREGISTRATION_ERCOT_FORECAST_WEATHER_DRAFT.md).
  It is not approved and the evaluation has not been run. The realized-ERA5
  v1.5 result stays evidence only. v1.4 stays rejected. No threshold changes
  after the fact.
- Follow through on the tail-sample diagnostic: the q99 band is the known
  weak point (small effective tail sample), so candidate design starts there.

## Later

- Adoption of the Historical Lab by groups other than the author (classes,
  clubs, other instructors), with their sessions counted separately from
  author-run pilots.
- A one-page sustainability note, written only when there is real partner
  progress to describe (for example the TeachEngineering review or a
  university club hosting the lab on its own).

## Not planned

- No live or "real-time" inference claims until a candidate passes the gate.
- No additional grid-operator feeds described as real data unless an official
  source is integrated and verified end to end.
