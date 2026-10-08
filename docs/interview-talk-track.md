# Interview talk track

Use your own words. Every claim below is something this repo actually does. If asked about anything beyond it, say it is outside what you built.

## 2-minute version

"This is a learning project I built on Databricks Free Edition to understand how governance works end to end. I took a public sample of federal contract awards from USAspending, about three thousand rows (the largest awards by value, so totals are skewed and not real agency spending), and loaded it into bronze Delta tables from a Unity Catalog volume. Silver types and cleans the data and removes duplicate award IDs, with a quarantine table for rows that fail quality rules. Gold gives award value by agency, vendor concentration, and award value by NAICS sector.

The part I cared most about is governance. I used Unity Catalog grants, a row filter so an analyst only sees their agency and region, and a column mask on the contractor identifier so it shows only to people with enough clearance. The roles table is synthetic. I wrote down which NIST 800-53 family each control relates to, as a learning aid and not an assessment.

I also wrote a reference architecture for how this would extend to a real agency, and I phrased the hard parts, like network isolation, customer-managed keys, and FedRAMP coverage, as things to verify, because I have not done them."

## 5-minute version

1. **Why this project (30s).** I wanted hands-on time with the platform behind the governance conversations I would have with agencies, not just slides.
2. **Architecture (60s).** Raw CSV in a volume, bronze as loaded text with load metadata so it can be replayed, silver typed and deduplicated, gold for the dashboard. Walk the mermaid diagram in the README.
3. **Quality (45s).** Rules for missing award ID, non-positive amount, bad date, missing agency. Failing rows are quarantined with a reason instead of silently dropped. In this sample 82 duplicate award IDs were removed and nothing failed the rules.
4. **Governance demo (90s).** Same query, three identities. Admin sees 2,918 rows and full identifiers. A Defense analyst for the West sees 432 rows of one agency with identifiers visible at SECRET. A GSA analyst with a lower clearance sees 3 rows and masked identifiers. Explain that the enforced filter wraps the same functions the simulation calls.
5. **Bug story (30s).** My first policy function let everyone see everything because a function parameter was shadowed by a column of the same name in the subquery. I caught it because the simulated analysts returned the admin's row count, then renamed the parameters. Test the policy with identities that should be denied, not only the ones that should pass.
6. **Next and unknowns (45s).** See below.

## What I built

Ingest, silver and gold transforms with quality checks, row filter and column mask, tags and comments, a dashboard dataset set, local tests, and a reference architecture.

## What I would do next

- Move transforms to Lakeflow Declarative Pipelines with expectations.
- Use groups instead of an email table for roles, synced from an identity provider (SCIM).
- Get the real small business flag from the bulk download.
- Turn on system tables and show real lineage and audit output.
- Add a second workspace or user to test the restricted role with a real login.

## What I do not know yet

- Which Databricks services are covered at which FedRAMP or DoD impact level. I would check the current compliance documentation.
- How private connectivity and customer-managed keys are configured in practice. I have only described them.
- Whether row filters and masks perform well at agency scale. Mine ran on 3,000 rows.
- Whether Genie and other AI/BI features are available on Free Edition.

## Likely questions

- *"Is this production?"* No. It is a Free Edition learning project with public and synthetic data.
- *"Why simulate the restricted user?"* Free Edition has a single user. The enforced policy runs as the caller, and the simulation calls the same functions with another identity.
- *"Why not Lakeflow Declarative Pipelines?"* Plain SQL kept it a simple job. It is the first thing I would change.
