# Digital natives program playbook

Status: a learning exercise using synthetic data. Everything marked "assumption" or "verify" needs real data or real program details before use.

## 1. Who the program serves

Digital natives are cloud-native, usually venture-backed companies that build their product on data and increasingly on AI. Two segments behave differently and need different plays.

| | AI-native startups | Data-heavy SaaS |
|---|---|---|
| Typical workload mix (assumption) | Mostly ML and AI, then jobs, then SQL | Mostly SQL and jobs, small ML share |
| What they want | Fast path from prototype to production, model and serving help, predictable cost as usage spikes | Reliable pipelines, analytics for their own customers, governance as they sell to larger buyers |
| Early signal of success | First production ML or AI workload, weekly users growing | Pipelines in production, a second workload type |
| Main risk | Volatile, experiment-driven spend that disappears if a model or vendor choice changes | Shallow footprint (SQL only) that is easy to replace |
| Lead plays | Technical enablement, architecture reviews, cost guardrails | Migration help, governance and security reviews, partner integrations |

## 2. Lifecycle and metrics

| Stage | Entry | Metric that matters | Owner action |
|---|---|---|---|
| Identify | Fits the profile (funding stage, cloud-native, data or AI product) | Qualified accounts in the pipeline | Source through partners, VC networks, community |
| Onboard | Workspace created | Days to first job | Welcome plan, named technical contact |
| Activate | First job run | Days to first production workload, workload breadth | Enablement sessions, reference architecture |
| Expand | Production workload live | 13-week trend, new workload types, active users | Expansion plays, commitment discussion |
| Retain | Steady consumption | Momentum, share of peak | Early-warning plays |

## 3. Account health (as built in this kit)

Score 0 to 100 from four signals. The weights are assumptions.

| Signal | Weight | How it is measured |
|---|---|---|
| Momentum | 35% | Last 4 weeks of consumption versus the 4 weeks before |
| Trend | 30% | Last 13 weeks versus the 13 weeks before |
| Breadth | 20% | Workload types holding at least 10% of recent consumption (of 3) |
| Users | 15% | Average weekly active users, last 4 weeks versus before |

Status rules (assumptions):
- **At risk:** momentum below 0.85, or recent weekly consumption under 60% of the account's own peak, or score below 40.
- **Expansion candidate:** score of 70 or more and at least 2 workload types.
- **Watch:** score below 55.
- **Healthy:** everything else.

## 4. Plays by status

- **At risk:** a technical check-in within a week to find the cause (project ended, team change, cost concern, competing platform). Offer a cost review and an architecture review. Escalate to the account team if there is no reply in two weeks.
- **Watch (narrow footprint):** show the next workload type with a worked example, for instance moving from SQL only to scheduled jobs. Pair with a solutions architect for one session.
- **Healthy:** keep a regular cadence, share relevant releases and community events, and watch for a trend change.
- **Expansion candidate:** discuss a commitment or reserved capacity (verify what commercial options exist), propose a co-build of the next workload, and invite them to share the story through a customer case study or event.

## 5. Program levers (things to verify against what exists)

- Startup credits and onboarding offers: confirm current terms before promising anything.
- Partner and investor channels: VC portfolio programs, cloud marketplaces, system integrators.
- Technical enablement: office hours, reference architectures, a short "first production workload" guide.
- Community: meetups, builder events, a shared channel for program members.
- Co-marketing: case studies and joint sessions, with the company's approval.

## 6. First 90 days

- **Days 1 to 30:** learn the current program and its data. Agree definitions for activation, production workload, and health with sales, solutions, and finance. Review the existing account list.
- **Days 31 to 60:** publish a weekly program health view (this dashboard, on real data). Run the first at-risk and expansion plays on a small set. Collect what worked.
- **Days 61 to 90:** tune thresholds against real outcomes, formalize the plays, set program targets (activation rate, time to production, expansion rate, at-risk recovery), and report to leadership.

## 7. Reporting cadence

Weekly: health view and at-risk list with owners. Monthly: cohort activation and expansion, play results. Quarterly: program targets versus actuals, segment strategy changes.

## 8. What I would validate with real data

- Whether the activation milestone (first production workload) is defined and tracked the way I assumed.
- Whether momentum and trend predict churn or expansion at all, using history, and the right thresholds.
- Whether the two segments really differ in workload mix and time to value. The synthetic data shows similar time to production for both because I generated it that way, so it proves nothing.
- Which levers (credits, enablement, partners) move activation, using a holdout where possible.
- How consumption is priced and committed in practice. The price per unit in this kit is illustrative only.
