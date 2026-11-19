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
| Scientific method | Preregistered validation gates; pass/fail decided by numbers fixed in advance; failures published | Met for process — the v1.4 candidate was rejected by its own gate and the record is public ([decision record](docs/DECISION_RECORD_ERCOT_v1_4.md)). No candidate has passed yet |
| Integrity & security | Every public claim traceable to a checked artifact; dependency audit green | Met as of v1.2 (see [CHANGELOG](CHANGELOG.md)); a drift-guard test fails CI if the README evidence tables diverge from the evidence files |
| Product | A stranger can reproduce the core calculation unaided in ~15 minutes; the hosted demo is honest about what is gated | Mostly met — reproduction path and labeled demo mode are in place; live inference stays gated (HTTP 503) until a candidate passes |
| Teaching impact | Real sessions with counted participants and published feedback, including the weak points | Public ledger: 4 organizer-forwarded reports, 2 hands-on core completions, 0 independent retests (Community evidence page, updated September 25, 2026). Those reports do not establish adoption or learning effectiveness. [docs/FEEDBACK.md](docs/FEEDBACK.md) is an organizer-reported, unverified survey summary |
| Independent validation | Replication by people other than the author; citable archive | Not established. The dataset archive [10.5281/zenodo.22975251](https://doi.org/10.5281/zenodo.22975251) is the author's own record (v1, published 2026-09-26) and includes a Python checker separate from the browser code. Author-submitted listings were found on MERLOT (material 824240305, added September 25, 2026, submitter Dresden Goehner) and, by search on November 17, 2026, on OER Commons (same title, author Dresden Goehner, date added September 25, 2026). A listing is not an independent replication |
| Sustainability | A stated model for who benefits, who hosts or pays, and why the project continues without depending on one person's spare time | Not yet — see "Later" below; this page deliberately does not invent one |
| Community | Contributors beyond the author; maintained release cadence | Early — contributions and reviews welcome; release cadence formalized from v1.2 |

## Now

- Keep the organizer-reported, unverified survey summary in
  `docs/FEEDBACK.md`, with its method and limitations. The repository holds
  `data/feedback/summary.json` and the analysis script, not the raw responses.
- Keep the changelog and releases current from v1.2 onward.

## Next

- **Publish the v1.5 record (pull request #23, under review).** The v1.5
  preregistration was committed on 2026-11-05, after its evaluation window
  closed on 2026-11-01, so it is a retrospective freeze. The scores used
  realized ERA5 weather and are an upper bound. The evidence-bundle and
  feature-availability gates are not passed. The candidate is not packaged,
  and the inference endpoints stay gated. No threshold changes after the fact.
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
