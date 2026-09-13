# Grid Notes — a reusable public-data entry point

The winter brief is a source-linked reading exercise, a downloadable graphic,
and forwarding copy. It is not a new forecast or a retrospective outage model.

Public page: https://gert-d.vercel.app/briefs/winter-load

## Rebuild and inspect

Run `node scripts/build_winter_brief.mjs` after installing the existing app
dependencies. It uses the Sharp package included in the Next.js dependency
tree. No live API credentials are needed. The input bundle SHA-256 is pinned;
a changed dataset stops generation until reviewed.

The generator preserves all 72 points at hourly spacing, converts MW to GW,
uses a zero-based 0–80 GW scale, and makes no smoothed or forecast curve. It
generates PNG, SVG, and an exact-data manifest in `public/briefs/`.

Event annotation: 2021-02-15 01:25 CST, from ERCOT's February 15 news release.
This is an onset marker, not a point estimate of lost load or a blackout-duration
band. The title says what cannot be inferred, not that GERT has estimated the
counterfactual demand or proved what caused every hourly change.

## Source and rights

- Raw series: https://www.ercot.com/files/docs/2021/11/12/Native_Load_2021.zip
- Event context: https://www.ercot.com/news/release?id=9c552983-008a-3906-8066-8b76315ed3e7
- Data-use terms, checked September 13, 2026: https://www.ercot.com/help/terms

Section 5 permits public raw data in compilations, charts, and analyses. Keep
attribution and do not imply ERCOT endorsement. The forwarding pack includes
the existing repository MIT notice for original GERT material; it does not
relicense third-party material. Do not market through ERCOT mailing lists.

## Self-check and measurement limits

The two questions capture initial selections before revealing explanations.
The browser generates an optional receipt without a name, email, cookie,
tracking request, or automatic submission. A receipt is editable and is NOT
independent verification, proof of a unique person, or a certificate.

No new analytics service was added. Visits, copies, or downloads are not
silently counted as completed tests. For actual outside use, retain a voluntary
reply or GitHub review, the specific artifact, host confirmation when relevant,
and permission before identifying or quoting anyone. Count source publication,
referral traffic, completed exercises, independent reviews, and reuse separately.

The media/organizer contact list and private mail records belong outside the
public repository. Do not include them in released forwarding packs.
