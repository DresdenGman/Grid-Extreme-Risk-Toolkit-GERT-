# PR #23 evidence snapshot

`ercot_v1_5_validation.json` in this directory is a byte-for-byte copy of
[`evidence/ercot_v1_5_validation.json`](https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-/blob/41095ba0e5c88c1750296b23a0b5bf6fedeb4010/evidence/ercot_v1_5_validation.json)
from commit `41095ba0e5c88c1750296b23a0b5bf6fedeb4010` on `feat/ercot-v1-5`.

That commit is the current head of unmerged [pull request #23](https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-/pull/23). The file's validation status is `evidence_only_not_packaged`. `all_gates_passed` is false. The evidence-bundle and feature-availability gates are not passed, and `packaging_authorized` is false. It is not in `models/production/`.

The homepage reads `evidence/ercot_v1_5_validation.json` when that file is on the branch being built. Until PR #23 lands on main, it reads this snapshot. `lib/homepage/evidence.ts` pins the git blob SHA-1 (`53e3561aed744fee2c44d369d2b39b4cfbd4afc5`). Do not edit the JSON in place. Replace it only by copying a newer commit and updating the pin.
