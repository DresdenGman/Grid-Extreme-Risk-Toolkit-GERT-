# PR #23 evidence snapshot

`ercot_v1_5_validation.json` in this directory is a byte-for-byte copy of
[`evidence/ercot_v1_5_validation.json`](https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-/blob/98d4fbf82a78ebfaeca160bb0ac20915c8fc566e/evidence/ercot_v1_5_validation.json)
from commit `98d4fbf82a78ebfaeca160bb0ac20915c8fc566e` on `feat/ercot-v1-5`.

That commit is the head of [pull request #23](https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-/pull/23), which is open and unmerged. The candidate is `provisional_candidate`. It is not in `models/production/` and it is not a production model.

The homepage reads `evidence/ercot_v1_5_validation.json` when that file is on the branch being built. Until PR #23 lands on main, it reads this snapshot. `lib/homepage/evidence.ts` pins the git blob SHA-1 (`25f2dfadd717487be2db600c1478d1fa2f64cf86`). Do not edit the JSON in place. Replace it only by copying a newer commit and updating the pin.
