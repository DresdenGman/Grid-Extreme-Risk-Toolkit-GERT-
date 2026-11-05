# Historical Lab pilot feedback

Results of the participant feedback survey for the GERT Historical Lab pilot
sessions. Published in full, including the weak points; the aggregate data
and the script that produces it are in
[`data/feedback/`](../data/feedback/).

## Method

- Two pilot sessions of the Historical Lab were run by the author: Session 1
  in May 2026 and Session 2 on September 8, 2026, with community-recruited
  participants and members of the author's school club (Applied Mathematics
  and AI). Total participation across both sessions was over 115 people.
  A small number of additional participants completed the lab on their own
  ("volunteer run").
- After the sessions, participants were sent a 15-question follow-up survey
  (Google Forms, no email collected). 58 responses were submitted; 1 was the
  organizer's own test entry and was removed, leaving **57 analyzed
  responses** — roughly half of all participants, self-selected.
- The optional name/contact question is not published. Free-text answers are
  summarized thematically; quotes below are used only from the 51 respondents
  (89.5%) who agreed to anonymous quotation, and are quoted anonymously.

## Who responded (n = 57)

| Question | Result |
| --- | --- |
| Role | Student 43 (75.4%) · Community member 8 (14.0%) · Teacher 4 (7.0%) · Other 2 (3.5%) |
| Session | Session 1 (May 2026) 27 (47.4%) · Session 2 (fall 2026) 26 (45.6%) · Volunteer run 4 (7.0%) |
| Prior energy/grid experience | None 26 (45.6%) · A little 23 (40.4%) · A lot 8 (14.0%) |

## Ratings (1–5 scale, n = 57 each)

| Item | Mean | Distribution (2/3/4/5; no 1s were given) |
| --- | --- | --- |
| Overall rating of the activity | **4.33** | 2 / 6 / 20 / 29 |
| The data activity was engaging | 4.23 | 2 / 10 / 18 / 27 |
| Instructions were clear and easy to follow | 4.11 | 4 / 9 / 21 / 23 |
| The checker tool was easy to use | **3.89** | 6 / 13 / 19 / 19 |

The checker tool is the lowest-rated element — consistent with the free-text
answers, where its unexplained pass/fail logic is the most common complaint.

## Task outcomes (self-reported)

| Question | Result |
| --- | --- |
| Able to identify the grid-stress hours | On my own 23 (40.4%) · With help 27 (47.4%) · No 7 (12.3%) |
| Answers matched the checker | Fully 32 (56.1%) · Partly 17 (29.8%) · No 3 (5.3%) · Did not reach the checker step 5 (8.8%) |

So 87.7% of respondents found the stress hours (independently or with help),
while 12.3% did not, and about 1 in 11 never got as far as checking their
answers. Both numbers are part of the result, not footnotes to it.

## Free-text answers

Answered by 43–47 of the 57 respondents per question.

- **Most important thing learned** (45 answers): reading real load data to
  find stress hours, reserve margins, and how demand swings interact with
  generation — several respondents described learning by teaching the
  calculation to someone else.
- **Most confusing part** (44 answers): the checker's validation logic
  ("felt like a black box"), distinguishing one-off data anomalies from
  sustained stress windows, and percentile-vs-threshold definitions.
- **What to change** (43 answers): a short worked example or walkthrough up
  front, an explanation of *why* the checker accepts or rejects an answer,
  and clearer documentation of what counts as a stress hour (including
  whether steep ramps alone qualify).
- **Would you recommend it?** (47 answers): none advised against it; at
  least 35 open with an unambiguous recommendation (coded by opening wording;
  the rest are positive with conditions or suggestions attached).

## Quotes (anonymous, from consenting respondents)

> "Teaching someone else how to calculate net load and spot stress hours made
> the engineering concepts stick far better in my own mind."

> "It bridges abstract grid concepts with realistic, hands-on data analysis,
> making it an engaging and educational activity for students."

> "Highly recommend for IEEE student branches and intro power systems courses
> because it demystifies grid reliability metrics."

And, on the main weakness:

> "The checker tool's validation logic felt like a black box; it was hard to
> deduce why an hour with 94% peak demand was graded incorrect."

## Limitations

- This is a post-event follow-up survey, not an on-site instrument:
  respondents are the half of participants who chose to answer, which
  likely tilts results positive.
- Participation counts (115+) come from the session organizer's records;
  the survey's session split (47.4% / 45.6% / 7.0%) is the respondents'
  self-report.
- Task outcomes are self-reported, not measured from checker logs.
- Both sessions were run by the author. Sessions run independently by other
  instructors would be a stronger test and have not happened yet.

## What changes because of this feedback

Tracked in [`ROADMAP.md`](../ROADMAP.md). The two concrete items this survey
puts on the list: explain the checker's accept/reject reasoning in the lab
itself, and add a short worked example before the data activity starts.

## Addendum (2026-11-05)

The checker-explainability item above has been addressed. The report checker
(`scripts/verify_historical_report.py`) no longer stops at the first bare
mismatch: it lists every mismatching field with the expected and submitted
values and names the likely cause it can detect — the report's own
assumptions, rows shifted by one hour, rounding, or a wrong value shown with
its formula inputs. The lab page now carries a worked example computed live
from the bundled summer-2023 data and a plain-language statement of how the
check works: a stress hour is a strictly positive gap against the assumed
capacity, equality with capacity is a zero gap, timestamps are interval
starts in America/Chicago, and every hourly row and metric is compared.
Whether participants find the checker clearer as a result has not been
measured.
