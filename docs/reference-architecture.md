# Reference architecture: governed public-sector lakehouse

Status: learning project on Databricks Free Edition. Sections marked "verify" are things to confirm against current Databricks and cloud documentation before relying on them for a real agency.

## 1. Purpose

Show how an agency could keep mission data in one governed platform, with access decided by policy (who you are) rather than by copies of the data. The demo uses public federal contract awards.

## 2. Data flow

| Layer | Object | What happens |
|---|---|---|
| Raw | UC volume `bronze.raw_files` | Source CSVs land unchanged, one folder per load |
| Bronze | `bronze.awards_raw` | Delta table, all columns as loaded, plus load timestamp and source file |
| Silver | `silver.awards` | Typed, deduplicated, standardized agency and vendor fields, rows failing quality rules quarantined |
| Gold | `gold.spend_by_agency`, `gold.vendor_concentration`, `gold.spend_by_naics_sector` | Aggregates for the dashboard |
| Reference | `ref.nist_controls`, `ref.analyst_roles` | Control mapping (hand written) and synthetic analyst roles |

## 3. Governance controls and compliance intent

| Need | Platform feature | Related NIST 800-53 family |
|---|---|---|
| Least privilege | Unity Catalog grants on catalog, schema, table | AC (Access Control) |
| Protect identifiers | Column mask on contractor identifiers | AC, SC (System and Communications Protection) |
| Limit rows by role | Row filter by agency and region from the roles table | AC |
| Know where data came from | Lineage, table and column tags | AU (Audit and Accountability), CM (Configuration Management) |
| Prove who did what | Audit log query (system tables, verify availability on Free Edition) | AU |
| Data integrity | Quality expectations, quarantine of bad rows | SI (System and Information Integrity) |

The control mapping is a learning aid, not an assessment.

## 4. Roles in the demo

- Admin: sees all rows and unmasked identifiers.
- Restricted analyst: sees only their agency and region, with identifiers masked.
Free Edition has a single user, so the restricted role is shown by querying through the policy functions with a simulated identity from the synthetic roles table. Verify how far real multi-user testing is possible.

## 5. Cost notes

- Free Edition: no cost, serverless only, daily compute quotas, one 2X-Small SQL warehouse.
- A paid deployment would be billed on DBUs plus cloud infrastructure. Serverless SQL and jobs scale to zero when idle. Estimate with the Databricks pricing calculator before committing numbers.
- Storage cost is small for this dataset. Full USAspending history is large, so partitioning and file sizing would matter.

## 6. Extending to a real agency (things to verify)

- Network isolation and private connectivity (private link or equivalent, no public endpoints).
- Customer-managed keys for storage and workspace encryption.
- SSO and SCIM provisioning from the agency identity provider, group-based grants.
- Audit log export to the agency SIEM.
- Authorization level of the target cloud region and Databricks deployment (FedRAMP, DoD impact level): confirm which services are covered.
- Data classification and records retention requirements, and how tags map to them.
- Separation of dev, test, and prod workspaces and catalogs.

## 7. What this demo does not cover

Streaming ingest, ML workloads, cross-agency sharing (Delta Sharing), cross-domain solutions, and any classified environment.
