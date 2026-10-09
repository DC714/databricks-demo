# Talk track: digital natives program kit

Use your own words. Every claim below is something the kit does. Anything beyond it is outside what you built.

## 2-minute version

"This is a learning project on how I would run a program for digital natives, using synthetic data because I do not have real customer telemetry. I generated 40 fictional accounts, split between AI-native startups and data-heavy SaaS, with a year of weekly consumption, active users, and onboarding milestones. Each account follows a hidden pattern: fast ramp, steady grower, plateau, churn risk, or late bloomer.

On Databricks Free Edition I loaded it through bronze, silver and gold tables, and built an account health score from momentum, 13-week trend, workload breadth, and user growth, with rule-based statuses. The check I like is that the scoring has to find the hidden patterns without being told. It flagged all seven churn-risk accounts and all four late bloomers as expansion candidates. That only shows the logic works as designed, not that it predicts real churn, and the weights are my assumptions.

The playbook turns the statuses into plays, and lays out a first 90 days. The list at the end says what I would validate with real data first."

## 5-minute version

1. **Why (30s).** The role is about growing consumption-based customers, so I wanted to practice going from usage data to actions.
2. **The data (45s).** Synthetic and labeled. Two segments, five hidden patterns, fixed seed so anyone can reproduce it. Say plainly that segment differences are what I generated, not findings.
3. **The pipeline (30s).** CSVs into a volume, bronze, silver (typed, deduplicated), gold (monthly consumption, time to value, account health). Run from the CLI, dashboard created from a script.
4. **The health score (75s).** Four signals and weights, status rules, the plays each status triggers. Explain why momentum alone is noisy and why breadth catches shallow footprints.
5. **The check (45s).** Compare computed status with the hidden pattern. Be candid about the misses: two of the ten fast-ramp accounts were not flagged healthy (one at risk, one on watch). I have not yet investigated why, so say that, and offer it as the first thing to debug.
6. **Playbook and 90 days (45s).** Lifecycle, plays, cadence, targets.
7. **Unknowns (30s).** See below.

## What I built

Telemetry generator, three notebooks, a dashboard, local tests, a playbook, and this talk track.

## What I would do next

- Replace the synthetic data with real telemetry definitions and test the score against history.
- Fit the weights and thresholds on outcomes instead of assuming them.
- Add cohort retention and consumption forecasting.
- Run plays on a small group with a holdout to measure what works.

## What I do not know yet

- How Databricks defines and tracks activation and production workloads internally.
- Which commercial options and credits exist today. I would verify before proposing any.
- Whether my two-segment split matches how the field team segments digital natives.
- Whether a rule-based score holds up at thousands of accounts.

## Likely questions

- *"Is the data real?"* No, synthetic by design, and the names end in Demo.
- *"Why should I trust the score?"* You should not yet. It is a transparent starting point, and the validation plan is in the playbook.
- *"What would you change first?"* Fit the thresholds on real history and add a holdout for plays.
