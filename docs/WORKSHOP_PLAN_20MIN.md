# 20 分钟 GERT 工作坊方案（给维护者看的中文摘要）

- 基于仓库真实材料：`docs/WORKSHOP.md`（20 分钟流程）、Historical Lab 实测数字、"Same meter, two worlds" 5 分钟活动脚本。没有编造任何数字。
- 流程：hook（停电时用电量为何下降）→ same-meter 反例（3 分钟，非识别性）→ Historical Lab 实操（80,000 MW，0%/5%/10%，21→7 小时、66,683→4,458 MWh）→ 独立手算验证一行 → 冬季案例（呼应反例）→ debrief + 反馈表。
- 场地：纯浏览器、零安装，10–40 人。主持人只需这一份文档 + 投屏。
- 证据口径：出席 / 完成计算 / 提交反馈三个数字分开记；状态分 contacted → confirmed → held → feedback-received；绝不把报名数当出席数。
- 诚实声明：untested pilot teaching exercise，不是验证过的预测系统；v1.4 概率模型因未过校准门槛已被公开拒绝。

---

# GERT 20-Minute Workshop Plan

**Grid load, assumptions, and decisions — a hands-on exercise**

## Goal

Participants learn to separate **observations** (recorded load) from **assumptions** (capacity, load reduction), see why **power (MW) ≠ energy (MWh)**, and experience why correct arithmetic is not the same as a reliable operational decision.

## Honest framing (read aloud at the start)

> "This is an untested pilot teaching exercise built by a high school student, not a validated forecasting system. The numbers we compute today are counterfactual arithmetic on public historical data. Our probabilistic model v1.4 was publicly rejected for production after missing its predeclared 0.03 calibration tolerance at Q90/Q95/Q99. Nothing today is a prediction — it's practice in making assumptions visible."

## Audience & logistics

- **Who:** university energy/data club or high-school STEM club, 10–40 people.
- **Prerequisites:** percentages, maxima, and (we'll teach it) the difference between power and energy.
- **Setup:** browser only, no install, no accounts. Facilitator shares one screen; participants can follow on phones/laptops but it's optional.
- **Facilitator prep:** open the three links below once beforehand; no other preparation needed.

## Materials (exact links)

| # | What | Link | Used for |
|---|---|---|---|
| 1 | Historical Lab (summer case) | https://gert-d.vercel.app/history | Main exercise, minutes 5–13 |
| 2 | Same meter, two worlds | https://gert-d.vercel.app/briefs/same-meter | Counterexample, minutes 2–5 |
| 3 | Facilitator guide (repo) | https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-/blob/main/docs/WORKSHOP.md | Reference if you want more depth |
| 4 | Reproduction docs | https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-/blob/main/docs/HISTORICAL_LAB.md | For the curious / follow-up |
| 5 | 10-minute review guide | https://gert-d.vercel.app/review | Optional take-home |

**Screenshare plan:** keep link 1 open the whole time; switch to link 2 only for minutes 2–5. A calculator or spreadsheet is enough for the hand-check — no code needed.

## Minute-by-minute flow (20 minutes total)

### 0:00–0:02 — Hook
Ask the room: **"Why can electricity use *fall* during a blackout?"** Take 2–3 answers. Don't resolve it yet — say: "Keep your answer in mind. In 15 minutes you'll be able to check it against real data."

### 0:02–0:05 — Same meter, two worlds (counterexample)
Show link 2. Present only the two readings: **60 GW → 45 GW**. Ask: *"Does this fall tell you how much electricity people wanted but didn't receive?"*

Reveal the two worlds:
- **World A** (demand falls to 45 GW, delivery ceiling stays 90 GW): unserved energy = **0 MWh**.
- **World B** (delivery ceiling falls to 45 GW, assumed second-hour demand 65 GW): unserved energy = **20,000 MWh**.

Same readings, different unserved energy. Name the idea: **non-identifiability** — different hidden inputs produce the same observation, so the reading alone can't recover both. Ask: *"What one extra observation would let you tell the worlds apart?"* (Answer: a demand estimate independent of the delivered-load reading — which brings its own uncertainty.)

### 0:05–0:10 — Guided Historical Lab: assumptions move the answer
Open link 1 (summer case: August 9–11, 2023, 72 hourly ERCOT observations).
1. Set **capacity 80,000 MW, reduction 0%**. Read the results aloud: **21 hours above capacity, gap energy 66,683 MWh.**
2. **Before touching anything**, ask the room to predict: at 5% reduction, do exceedance hours and gap energy go up, down, or stay? Then set **5%**: **7 hours, 4,458 MWh.**
3. Ask for a prediction at **10%**, then try it. Point out the **piecewise-linear** response: hours drop in steps, energy falls smoothly-ish — and every change came from *your* assumptions, not from new data.
4. Key question: *"Can you distinguish the actual observations from the two assumptions we just typed in?"*

### 0:10–0:13 — Hand-check one row (independent verification)
Pick one visible row together, e.g. **Aug 10, 15:00**: recorded 84,661 MW → at 5% reduction, adjusted = 84,661 × 0.95 = **80,428 MW** → gap = max(0, 80,428 − 80,000) = **428 MW** → × 1 hour = **428 MWh**. Check it matches the table. Formula on screen: **gap energy = Σ max(0, adjusted load − capacity) × 1 hour**. One person with a calculator can do this — that's the point: the arithmetic is checkable by hand.

### 0:13–0:16 — Winter case: the counterexample was real
Switch to the **winter case (Feb 14–16, 2021)**. Ask: *"Why can't measured load during outages tell us the demand that would have existed without them?"* Connect it back: this is the same non-identifiability from minute 3, now in real data — the meter can't show electricity that was never delivered. The lab states this limit openly; discuss what constraint you'd need to add.

### 0:16–0:20 — Debrief + feedback
Each participant names: **(a)** one constraint missing from the lab that would matter for a real operational decision, and **(b)** one change that would make the tool clearer or more useful. Collect the 3-question feedback form (below). Close by returning to the hook question — let 1–2 people revise their original answer out loud.

## One-page handout (copy-paste ready)

> **GERT Historical Lab — 20-minute exercise**
> Link: https://gert-d.vercel.app/history
> - **Observed:** 72 hourly ERCOT load readings (summer Aug 9–11, 2023). These are facts.
> - **Assumed:** capacity (try 80,000 MW), load reduction (try 0% / 5% / 10%). These are your choices.
> - **Computed:** hours above capacity (21 → 7 at 5%), gap energy = Σ max(0, adjusted load − capacity) × 1h (66,683 → 4,458 MWh at 5%).
> - **Check by hand:** one row: adjusted = recorded × (1 − reduction); gap = max(0, adjusted − capacity).
> - **Remember:** capacity is *not* historical capacity. Gap energy is *not* expected unserved energy. Same meter, two worlds: https://gert-d.vercel.app/briefs/same-meter
> - This is a teaching exercise, not a forecast. The v1.4 probability model was publicly rejected for missing its calibration gate.

## Recording evidence (honest metrics only)

**Three separate counts — never substitute one for another:**
1. **Attended** (bodies in room / on call)
2. **Completed a calculation** (did the hand-check or the 0%/5%/10% comparison themselves)
3. **Submitted substantive feedback** (answered the form below)

**Session status pipeline** (log each transition with date in `outreach-log.md`):
`contacted` → `confirmed` (date + host name, with host's permission to be named) → `held` (date + the three counts) → `feedback-received` (aggregate answers, no names)

**Do not publish** attendance names, contact details, or student work without permission. A class/club can keep anonymous aggregate counts plus a host confirmation. Hosting this exercise is **not** institutional endorsement, formal validation, or operational deployment.

**Feedback loop:** turn the best critique into a GitHub issue on the repo (issue template: *Historical Lab independent review*). If it leads to a product change, record the change and any retest. Distinguish "second session requested" from "second session held."

## 3-question feedback form

1. In one sentence: besides the recorded load, what *two* inputs does the "gap energy" number depend on? *(checks understanding: assumed capacity + assumed reduction)*
2. What confused you most during the 20 minutes? *(open)*
3. Name one constraint missing from the lab that would matter for a real operational decision. *(open)*

---
*Source materials: [WORKSHOP.md](https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-/blob/main/docs/WORKSHOP.md) · [HISTORICAL_LAB.md](https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-/blob/main/docs/HISTORICAL_LAB.md) · Numbers verified on the live Historical Lab, 2026-09-25.*
