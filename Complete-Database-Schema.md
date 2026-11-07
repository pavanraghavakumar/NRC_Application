# NRC Strategic Planning & Performance Management System
# Document 2 — Complete Database Schema (SQLite)

**Target DBMS:** SQLite 3.45 or later — one database file, `STRICT` tables, accessed only through the Python API tier
**Derived from:** `Core` managed solution v1.0.0.67 — 47 entities, 536 business attributes (excluding platform audit/system columns),
473 relationships (412 one-to-many, 61 many-to-many), 36 global option sets, 12 lifecycle state machines,
12 rollup/calculated columns (11 with formula definitions exported; Enterprise Risk Title's formula is
missing from the export)
**Document set:** 2 of 3 — (1) Project Summary · (2) Database Schema · (3) APIs & UI Screens
**Edition:** React + SQLite

> Every table, column, enumeration value, relationship, constraint and default in this document was
> extracted from the source solution. Columns that exist only to serve the Dataverse platform
> (`importsequencenumber`, `timezoneruleversionnumber`, `utcconversiontimezonecode`,
> `overriddencreatedon`, `versionnumber`, `traversedpath`, `processid`, `stageid`, `exchangerate`,
> `transactioncurrencyid`) have been dropped; everything that carries business meaning is retained.
> Where this document proposes something the old system did not have (the API-enforced row-visibility
> model, explicit audit tables, analytic views), it is marked **[NEW]**.
>
> **SQLite edition.** This edition targets SQLite instead of PostgreSQL. Table and column names,
> enumerations and business rules are unchanged; what changes is how they are stored and enforced —
> table-name prefixes instead of schemas (§1), SQLite storage classes (§1, §1.2), triggers and
> counters instead of sequences (§12), and row visibility enforced by the API's data-access layer,
> because SQLite has no row-level security (§13).

---

## Table of contents

1. Design conventions
2. Enumerations
3. Identity, security and organisation tables
4. Reference / master-data tables
5. Strategic Plan tables
6. Performance Management tables
7. Evidence Building tables
8. Signposts and Markers tables
9. Workflow, notification and audit tables
10. Junction (many-to-many) tables — all 61
11. Configuration tables
12. Constraints, indexes and integrity rules
13. Row-visibility model (enforced by the API)
14. Analytic views for the dashboards
15. Legacy-to-target migration mapping
16. Retired columns and tables

---

## 1. Design conventions

| Convention | Decision |
|---|---|
| Database layout | **One SQLite database file** (e.g. `nrc_spa.db`). SQLite has no schemas inside a file, so the logical areas become **table-name prefixes**: `core_` (identity/security/config), `ref_` (master data), `plan_` (strategic plan), `perf_` (performance management), `evidence_` (evidence building), `wf_` (workflow/audit), `analytics_` (views). Migration staging is a **separate file attached as `staging`** (`ATTACH DATABASE 'staging.db' AS staging`), so `staging.<table>` is literal SQLite syntax and the whole staging area is discarded by deleting one file. The operational areas are deliberately *not* split into attached files: foreign keys, triggers and views cannot reach across attached databases, and in WAL mode a transaction is atomic only within one file |
| Table form | Every table is declared `STRICT`, so a value of the wrong storage class is rejected instead of being silently coerced by type affinity. The 61 junction tables (§10) are also `WITHOUT ROWID` — two short keys, clustered on the pair. Business tables keep the implicit rowid: their rows are wide, which is where `WITHOUT ROWID` is slower |
| Primary keys | `id TEXT` holding a UUID in canonical lower-case 36-character form, `CHECK (length(id) = 36)`. SQLite has no UUID type and no built-in UUID generator, so **the API generates it** (`uuid.uuid4()`); SQL-only seed scripts use the expression in §1.2. Mirrors the Dataverse GUID primary keys and makes migration a straight copy of the original GUIDs |
| Natural/business keys | Kept as separate unique columns (e.g. `indicator_code`, `risk_code`) so the human-readable IDs described in Document 1 §8.1 stay stable |
| Naming | `snake_case` singular-noun tables carrying their area prefix (`perf_risk_update`); foreign keys named `<referenced_table>_id` without the prefix (`risk_update_id`); role-playing foreign keys keep the role prefix (`lead_office_id`, `reporting_office_id`) |
| Text | `TEXT` for all strings. SQLite does not enforce `VARCHAR(n)` widths (and `STRICT` tables do not accept them), so every documented limit is a `CHECK (length(col) <= n)` constraint — for a `TEXT` value `length()` counts characters, not bytes — and the limits stay visible and adjustable |
| Rich text | `TEXT` holding sanitised HTML; a companion `*_plain` column feeds the full-text index (§12.4) and export |
| Choices | SQLite has no enum types. Stable domains are `TEXT` columns with `CHECK (col IN (…))` listing the values of §2; user-maintained domains are small lookup tables. Every value, its label and its **legacy numeric code** are also rows of `ref_enum_value (enum_name, value, label, legacy_code, sort_order)`, so migration is loss-free. In the column tables, a type cell that names an enumeration from §2 (e.g. `ref_level`) means "`TEXT` constrained to that enumeration's values", and `TEXT enum …` lists the values inline |
| Multi-select choices | Child junction table (never a delimited string) |
| Booleans | `INTEGER` holding `0` / `1` with `CHECK (col IN (0, 1))` — shown as `INTEGER (0/1)`. SQLite has no boolean type; `TRUE` and `FALSE` are aliases for 1 and 0 |
| Money | `INTEGER` holding the amount × 10 000 — exact to four decimal places, as the Dataverse money type is. The API converts to and from `Decimal`; `REAL` is never used for money |
| Decimals | `REAL` (IEEE double) for result/target values. A double round-trips any decimal of up to 15 significant digits exactly, so the API rejects values with more than 15 significant digits or more than 10 decimal places (the Dataverse precision) and serialises them through `Decimal`. **Plan sequences are `TEXT`** and are held literally: `1.10` and `1.1` are different objectives, and any numeric type — including SQLite's numeric affinity — would collapse them into one |
| Timestamps | `TEXT` in ISO-8601 UTC with milliseconds, `YYYY-MM-DDTHH:MM:SS.sssZ` — shown as `TEXT (UTC timestamp)`. It is the one representation that sorts chronologically as text and that SQLite's date functions read directly. Default `(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))`; `CHECK (col IS NULL OR julianday(col) IS NOT NULL)` |
| Dates | `TEXT` `YYYY-MM-DD` — shown as `TEXT (date)`; `CHECK (date(col) IS col)` |
| JSON | `TEXT` with `CHECK (json_valid(col))` — shown as `TEXT (JSON)` — read with the JSON1 functions (`json_extract`, `->>`, `json_each`). SQLite keeps the text exactly as written; it does not normalise key order or spacing, so **never match JSON with `LIKE`** — traverse it with `json_each` / `json_tree` |
| Soft state | Every business table has `state` (`active`/`inactive`) and `status_reason` (entity-specific enumeration) — the two-level model the whole application depends on |
| Ownership | Every ownable table has `owner_user_id`, `owner_team_id` (exactly one non-null), `owning_business_unit_id` |
| Audit columns | `created_on`, `created_by_id`, `created_on_behalf_by_id`, `modified_on`, `modified_by_id`, `modified_on_behalf_by_id`, `row_version INTEGER` |
| Field history **[NEW]** | A generic `wf_field_audit` table replaces Dataverse attribute auditing |
| Cascade behaviour | Lookups use `ON DELETE SET NULL` (Dataverse `RemoveLink`); parent-owned children use `ON DELETE CASCADE`; business-unit references use `ON DELETE RESTRICT`. **None of this happens unless `PRAGMA foreign_keys = ON`** — SQLite ships with foreign-key enforcement off, per connection, so the API turns it on for every connection it opens (§1.2) |
| Case-insensitive uniqueness | A unique index on `col COLLATE NOCASE` for codes and names. `NOCASE` folds ASCII letters only (as does `lower()`, unless the ICU extension is loaded); the codes and names it guards are ASCII |
| Sorting | The default `BINARY` collation orders by code point, so every capital sorts before every lower-case letter. Name and title columns that users sort on declare `COLLATE NOCASE` |

### 1.1 Standard column block (applied to every business table)

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | generated by the API | PK |
| `state` | `core_record_state` | no | `'active'` | Active / Inactive |
| `status_reason` | *entity enumeration* | no | entity default | See §2.4 |
| `owner_user_id` | TEXT (uuid) → `core_app_user` | yes | | ownable tables only |
| `owner_team_id` | TEXT (uuid) → `core_team` | yes | | ownable tables only |
| `owning_business_unit_id` | TEXT (uuid) → `core_business_unit` | no | | ownable tables only |
| `created_on` | TEXT (UTC timestamp) | no | `strftime('%Y-%m-%dT%H:%M:%fZ','now')` | |
| `created_by_id` | TEXT (uuid) → `core_app_user` | yes | | |
| `created_on_behalf_by_id` | TEXT (uuid) → `core_app_user` | yes | | delegate |
| `modified_on` | TEXT (UTC timestamp) | no | `strftime('%Y-%m-%dT%H:%M:%fZ','now')` | set by the API in the same `UPDATE`; an `AFTER UPDATE … WHEN NEW.modified_on IS OLD.modified_on` trigger is the backstop |
| `modified_by_id` | TEXT (uuid) → `core_app_user` | yes | | |
| `modified_on_behalf_by_id` | TEXT (uuid) → `core_app_user` | yes | | delegate |
| `row_version` | INTEGER | no | 1 | optimistic concurrency: `UPDATE … SET row_version = row_version + 1 … WHERE id = ? AND row_version = ?`; zero rows changed is a 409 |
| `legacy_guid` | TEXT (uuid) | yes | | original Dataverse id (migration) |

Constraint on every ownable table: exactly one of `owner_user_id` / `owner_team_id` is non-null —
`CHECK ((owner_user_id IS NULL) <> (owner_team_id IS NULL))`.

### 1.2 SQLite platform settings **[NEW — SQLite edition]**

**Minimum version: SQLite 3.45.** The schema relies on `RETURNING` (3.35), `STRICT` tables (3.37) and
the `->>` JSON operator (3.38). The SQLite library bundled with Python varies by build, so the API
checks `sqlite3.sqlite_version` at start-up and refuses to run below the minimum.

Every connection the API opens runs:

```sql
PRAGMA foreign_keys = ON;      -- off by default, and per connection: without it no FK is enforced
PRAGMA journal_mode = WAL;     -- readers never block the writer (persistent once set)
PRAGMA synchronous = NORMAL;   -- safe with WAL; a power cut can lose only the last commits
PRAGMA busy_timeout = 5000;    -- wait up to 5 s for the write lock rather than fail at once
PRAGMA temp_store = MEMORY;
```

and `PRAGMA optimize` when a connection closes and on each `maintain_database` run.

| Concern | Rule |
|---|---|
| **Write concurrency** | SQLite allows **one writer at a time** per database file; under WAL any number of readers run alongside it. Every write transaction opens with `BEGIN IMMEDIATE`, so it takes the write lock up front and waits for it (`busy_timeout`) instead of failing with `SQLITE_BUSY` halfway through. Write transactions stay short — a bulk command of up to 500 ids (Document 3 §1) is one transaction, and no network call (Teams, e-mail) is made while one is open: notifications go to the `wf_notification` outbox and are dispatched afterwards |
| **Deployment** | The database file lives on the API host's **local disk**, never on a network share, where SQLite's file locking is unreliable. All reads and writes go through the API; several worker processes on that one host are fine, several API hosts sharing one file are not |
| **Backup** | Online, without stopping the API: `VACUUM INTO '<backup-dir>/nrc_spa-<timestamp>.db'` (or Python's `Connection.backup`) on a schedule — the `maintain_database` job of Document 3 §7.1 — optionally with continuous WAL replication (for example Litestream) for a recovery point measured in seconds. Copying the `.db` file while the API is running is **not** a backup: the `-wal` file holds committed transactions the main file does not yet contain |
| **Schema changes** | `ALTER TABLE` can add, rename and drop columns, but cannot change a column's type or its constraints. Those changes use SQLite's 12-step table rebuild (create the new table, copy, drop, rename, re-create indexes and triggers) inside one transaction, with foreign-key enforcement switched off for its duration and `PRAGMA foreign_key_check` run before the commit; Alembic does this with `render_as_batch=True` |
| **Identifiers in SQL-only scripts** | Seed and fix scripts that must mint a UUID without the API use `lower(hex(randomblob(4)) \|\| '-' \|\| hex(randomblob(2)) \|\| '-4' \|\| substr(hex(randomblob(2)), 2) \|\| '-' \|\| substr('89ab', 1 + (abs(random()) % 4), 1) \|\| substr(hex(randomblob(2)), 2) \|\| '-' \|\| hex(randomblob(6)))` — a version-4 UUID in canonical form |
| **Size** | SQLite's limits (a database file of terabytes, a single value of up to 1 GB by default) are far beyond this system's ~11 700 migrated records and their quarterly growth. File attachments are **not** stored in the database: `core_file_attachment.storage_key` points into the object store (§9.9) |

---

## 2. Enumerations

All 36 global option sets, the entity-local choice sets, and all 12 status models. **Legacy code** is
the Dataverse integer value — retained so migration is deterministic and so the Power BI filters that
reference numeric values still resolve.

SQLite has no enum types, so each enumeration below is two things: a `CHECK (col IN (…))` on every
column that uses it, generated from the **Value** column, and one row per value in `ref_enum_value`
(`enum_name`, `value`, `label`, `legacy_code`, `sort_order`, plus `state` for the status models). The
headings (`ref_report_level`, `perf_qpr_record_status`, …) are the `enum_name` keys, not tables.
Adding a value therefore means rebuilding the `CHECK` (§1.2, schema changes) as well as inserting the
row — which is the reason user-maintained domains are lookup tables instead.

### 2.1 Global enumerations

#### `ref_report_level`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `cbj_appr` | CBJ/APPR |
| 875670002 | `business_product_line` | Business Line/Product Line |
| 875670003 | `office_performance_report` | Office Performance Report |
| 875670004 | `division` | Division |

*(There is no 875670001; the Prevent-Save script references it — see Document 1 §17.3 item 2.)*

#### `ref_quarter`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `q1` | Q1 |
| 875670001 | `q2` | Q2 |
| 875670002 | `q3` | Q3 |
| 875670003 | `q4` | Q4 |
| 875670004 | `annual` | Annual |

#### `ref_level` (`nrc_levels` — risk likelihood / consequence)
| Legacy code | Value | Label |
|---|---|---|
| 3 | `high` | High |
| 2 | `medium` | Medium |
| 1 | `low` | Low |

#### `ref_operator` (`nrc_operator`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `lt` | `<` |
| 875670001 | `eq` | `=` |
| 875670002 | `gt` | `>` |
| 875670003 | `lte` | `<=` |
| 875670004 | `gte` | `>=` |
| 875670005 | `na` | N/A |

#### `ref_units`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `percent` | % |
| 875670001 | `integer` | Integer |
| 875670002 | `decimal` | Decimal |
| 875670003 | `yes_no` | Yes/No |
| 875670004 | `dollar` | Dollar |
| 875670005 | `text` | Text |

#### `ref_measure_type` (`nrc_pitype`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `quantitative` | Quantitative |
| 875670001 | `qualitative` | Qualitative |
| 875670002 | `range` | Range |

#### `ref_indicator_type`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `output` | Output |
| 875670001 | `outcome` | Outcome |
| 875670003 | `process` | Process |
| 875670004 | `input` | Input |
| 875670005 | `efficiency` | Efficiency |
| 875670006 | `contextual` | Contextual |
| 875670002 | `outcome_legacy` | **Not a member of the source option set** — an orphan code with no label. Emitted (never stored) by the PI Result `indicator_type` calculated column (§6.3). Given its own value name, following the `_legacy` convention used by `ref_indicator_status_legacy` and `perf_priority_legacy`, so that this table stays a one-to-one code↔value map; a loader must fold it into `outcome`, and the rebuild must never emit it. See Document 1 §17.3 item 19 |

#### `ref_indicator_status` (`nrc_indstatus` — current)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `active` | Active |
| 875670001 | `discontinued` | Discontinued |
| 875670002 | `under_development` | Under Development |
| 875670003 | `pending_discontinue` | Pending Discontinue |

#### `ref_indicator_status_legacy` (`nrc_indicatorstatus` — deprecated, retained for migration)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 |  | Active |
| 875670001 |  | Discontinued |
| 875670002 |  | Under Development |
| 875670003 |  | New |

#### `ref_risk_status`
| Legacy code | Value | Label |
|---|---|---|
| 875670001 | `under_development` | Under Development |
| 875670002 | `active` | Active |
| 875670003 | `pending_discontinue` | Pending Discontinue |
| 875670004 | `discontinued` | Discontinued |

#### `ref_change_type`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `new` | New |
| 875670001 | `no_change` | No Change *(deprecated for new records)* |
| 875670002 | `revised` | Revised |

#### `ref_data_source`
| Legacy code | Value | Label |
|---|---|---|
| 875670004 | `external_website` | External Website |
| 875670001 | `faimis` | FAIMIS |
| 875670002 | `hrms` | HRMS |
| 875670003 | `ldap` | LDAP |
| 875670006 | `sharepoint` | SharePoint |
| 875670007 | `other` | Other |
| 875670008 | `na` | N/A |

#### `ref_success_likelihood` (`nrc_successlikelihood`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `likely` | Likely |
| 875670001 | `met` | Met |
| 875670002 | `unlikely` | Unlikely |
| 875670003 | `unmet` | Unmet |

#### `ref_data_type`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `qualitative` | Qualitative |
| 875670001 | `quantitative` | Quantitative |

#### `ref_risk_outlook` (`nrc_outlook`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `increasing` | Increasing |
| 875670001 | `decreasing` | Decreasing |
| 875670002 | `stable` | Stable |

#### `ref_principle_of_good_regulation`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `reliability` | Reliability |
| 875670001 | `openness` | Openness |
| 875670002 | `independence` | Independence |
| 875670003 | `efficiency` | Efficiency |
| 875670004 | `clarity` | Clarity |
| 875670005 | `none` | None |

#### `ref_rank`
1…11 — values 1 through 11

#### `ref_agency_wide_support_level` (`cr9de_agencywidesupportlevel`)
| Legacy code | Value | Label |
|---|---|---|
| 716580000 | `agency` | Agency |
| 716580001 | `office` | Office |
| 716580002 | `na` | N/A |

#### `ref_record_type` (`nrc_recordtype`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `performance_indicator` | Performance Indicator |
| 875670001 | `pi_result` | PI Result |
| 875670002 | `enterprise_risk` | Enterprise Risk |
| 875670003 | `risk_update` | Risk Update |
| 875670004 | `priority` | Priority |
| 875670005 | `positive_change_management` | Positive Change Management |
| 875670006 | `accomplishment` | Accomplishment |

#### `ref_workflow_action_type` (`nrc_performancemanagementactiontype`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `submit` | Submit |
| 875670001 | `approve` | Approve |
| 875670002 | `reject` | Reject |

#### `ref_approval_role` (`nrc_role`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `author` | Author |
| 875670001 | `assignee_interim_approver` | Assignee/Interim Approver |
| 875670003 | `final_approval` | Final Approval |

#### `ref_answer_type`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `assessment` | Assessment |
| 875670001 | `analysis` | Analysis |
| 875670002 | `research` | Research |
| 875670003 | `evaluation` | Evaluation |

#### `ref_evidence_building_status` (`nrc_evidencebuildingchoice`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `completed` | Completed |
| 875670001 | `in_progress` | In Progress |
| 875670002 | `delayed` | Delayed |
| 875670003 | `starts_in_fy` | Starts in FY |

#### `ref_evidence_building_activity_type`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `research` | Research |
| 875670002 | `rulemaking` | Rulemaking |
| 875670003 | `other` | Other |

#### `ref_related_ecq`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `leading_change` | Leading Change |
| 875670001 | `leading_people` | Leading People |

#### `ref_critical_element`
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `leading_change` | Leading Change |
| 875670001 | `leading_people` | Leading People |
| 875670002 | `business_acumen` | Business Acumen |
| 875670003 | `building_coalitions` | Building Coalitions |
| 875670004 | `results_driven` | Results Driven |

#### `ref_business_line_choice` (`nrc_businesslines` — the fixed 15-value list used by Definitions)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 |  | Acquisition |
| 875670001 |  | Administrative Services |
| 875670002 |  | Decommissioning and Low-Level Waste |
| 875670003 |  | Financial Management |
| 875670004 |  | Fuel Facilities |
| 875670005 |  | High Level Waste Repository |
| 875670006 |  | Human Resources Management |
| 875670007 |  | Information Technology/Management |
| 875670008 |  | International Activities |
| 875670009 |  | New Reactors |
| 875670010 |  | Nuclear Materials Users |
| 875670011 |  | Operating Reactors |
| 875670012 |  | Outreach |
| 875670013 |  | Spent Fuel Storage and Transportation |
| 875670014 |  | Training |

#### `ref_number_type` (`nrc_numbertype`)
| Legacy code | Value | Label |
|---|---|---|
| 875670000 | `percent` | % (Percent) |
| 875670001 | `dollars` | $ (Dollars) |
| 875670002 | `number` | # (Number) |

#### `ref_update_frequency` (`new_updatefrequency`)
| Legacy code | Value | Label |
|---|---|---|
| 100000000 |  | Weekly |
| 100000001 |  | Biweekly (Pay Period) |
| 100000002 |  | Biweekly |
| 100000003 |  | Monthly |
| 100000004 |  | Quarterly |
| 100000005 |  | Annually |

#### Capacity-Assessment enumerations *(module not yet built — retained for the future build)*
- `ref_attribute_type`: 875670000 Coverage · 875670001 Quality · 875670002 Effectiveness · 875670003 Methods · 875670004 Independence
- `ref_coverage_type`: 875670000 Distribution of Evidence-Building Activities · 875670001 Workforce Gaps and Surpluses
- `ref_findings_progress`: 875670000 New · 875670001 Revised · 875670002 No Change · 875670003 Discontinued
- `ref_staff_change_type`: 875670000 Demand · 875670001 Supply · 875670002 Attrition
- `ref_staff_position`: 875670000 Project Manager · 875670001 Nuclear Engineer · 875670002 Reactor Engineer · 875670003 Risk Analyst · 875670004 Materials Engineer · 875670005 Mechanical Engineer · 875670006 Project Engineer (RIDP) · 875670007 Resident Inspector · 875670008 Health Physicist (Materials Inspector/License Reviewer) · 875670009 Reactor Inspector · 875670010 Reliability and Risk Engineer/Analyst · 875670011 Human Factors Analyst · 875670012 Reactor Systems Engineer (Neutronics) · 875670013 Reactor Systems Engineer (Severe Accident/Source Term) · 875670014 Cost Analyst · 875670015 Regulation Specialist · 875670016 Accountant · 875670017 Budget Analyst

#### Test/utility enumerations present in the solution (not to be carried forward)
`nrc_demotemp` (This · Next · Last · Q1) and `nrc_product` (Product A · Product B).

### 2.2 Boolean (Yes/No) fields

The following are two-value option sets in the source; in SQLite they become `INTEGER` columns
holding `1` (true) or `0` (false), with `CHECK (col IN (0, 1))`.
Legacy mapping is always `1 → true`, `0 → false` except where noted.

| Table | Column | True label | False label |
|---|---|---|---|
| Accomplishment | `annual_performance_plan` | Yes | No |
| Accomplishment | `public` | Yes | No |
| Accomplishment | `quarterly_performance_review` | Yes | No |
| Accomplishment | `related_pi` | Yes | No |
| Action/Measure | `objective_satisfied` | Yes | No |
| Action/Measure | `completed_or_carried_forward` | **Carried forward** | **Completed** |
| Approval | `task_made` | Yes | No |
| Approval Queue | `alternate` | Yes | No |
| Approval Queue | `parallel` | Yes | No |
| Enterprise Risk | `no_associated_performance_indicators` | Yes | No |
| Enterprise Risk | `public` | Yes | No |
| Evaluations | `publish` | Yes | No |
| Performance Indicator | `annual_performance_plan_and_report` | Yes | No |
| Performance Indicator | `quarterly_performance_review` | Yes | No |
| Performance Indicator | `review_for_carry_over` | Yes | No |
| PI Result | `q1_not_applicable` … `q4_not_applicable`, `annual_not_applicable` | Yes | No |
| PI Result | `met_or_unmet` | Yes | No |
| PI Result | `public` | Yes | No |
| Positive Change Management | `presented_at_qpr` | Yes | No |
| Positive Change Management | `public` | Yes | No |
| Priority | `public` | Yes | No |
| Rejection | `task_made` | Yes | No |
| Research Activity | `publish` | Yes | No |
| Risk Update | `psat` | **PSAT** | **Non-PSAT** |
| Risk Update | `psat_accepted` | Yes | No |
| Risk Update | `qpr` | Yes | No |
| Risk Update | `qpr_discussion` | Yes | No |
| Risk Update | `risk_accepted` | Yes | No |
| Submission | `approved` | Yes | No |
| Submission | `resubmission` | Yes | No |
| Submission | `returned` | Yes | No |
| Submission | `task_made` | Yes | No |
| Task | `regarding_approval_submission` | Yes | No |
| Team | `is_office` | Yes | No |

Two booleans default to their **Yes/true** side: `core_team.is_office` and
`perf_action_measure.completed_or_carried_forward` (= Carried forward). All others default false.

### 2.3 Record state

#### `core_record_state`
| Legacy code | Value | Label |
|---|---|---|
| 0 | `active` | Active |
| 1 | `inactive` | Inactive |

Legacy display labels: `statecode` ships as **"Record Status"** on Performance Indicator and
Enterprise Risk, **"State"** on Planned Measure, and "Status" elsewhere.

#### `core_task_state` *(exception — `core_task` only)*
| Legacy code | Value | Label |
|---|---|---|
| 0 | `open` | Open |
| 1 | `completed` | Completed |
| 2 | `cancelled` | Cancelled |

`core_task` carries `core_task_state` in place of `core_record_state`; it is the one exception to
§1.1, whose standard column block gives every other business table `core_record_state`.

### 2.4 Status-reason enumerations (one per lifecycle)

Legacy display labels: `statuscode` ships as **"Stage"** on nine tables (Accomplishment, Enterprise
Risk, Performance Indicator, PI Result, Positive Change Management, Priority, Rejection, Risk Update,
Submission), **"Approval Status"** on Approval Queue, **"Status"** on Planned Measure, and
"Status Reason" elsewhere. Document 3 §13 prints this column as "Status"; the rebuild renames it.

#### `perf_qpr_record_status` — used by Accomplishment, Positive Change Management, Priority, Risk Update
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `draft` | Draft | active |
| 875670002 | `pending_approval` | Pending approval | active |
| 875670005 | `revision` | Revision | active |
| 2 | `finalized` | Finalized | inactive |
| 875670004 | `cancelled_closed` | Cancelled/closed | inactive |

#### `perf_pi_result_status`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `draft` | Draft | active |
| 875670001 | `pending_approval` | Pending approval | active |
| 875670007 | `revision` | Revision | active |
| 2 | `finalized` | Finalized | inactive |
| 875670006 | `cancelled_closed` | Cancelled/closed | inactive |

#### `perf_performance_indicator_status`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `draft` | Draft | active |
| 875670001 | `pending_approval` | Pending approval | active |
| 875670003 | `revision` | Revision | active |
| 2 | `finalized` | Finalized | inactive |
| 875670004 | `cancelled_closed` | Cancelled/closed | inactive |
| 875670005 | `discontinued` | Discontinued | inactive |
| 875670006 | `versioned_revised` | Versioned/revised | inactive |

#### `perf_enterprise_risk_status`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `draft` | Draft | active |
| 875670001 | `pending_approval` | Pending approval | active |
| 875670004 | `revision` | Revision | active |
| 2 | `finalized` | Finalized | inactive |
| 875670003 | `closed_cancelled` | Closed/cancelled | inactive |
| 875670005 | `discontinued` | Discontinued | inactive |

#### `evidence_eb_record_status` — used by Priority Question, Evaluations, Research Activity
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `draft` | Draft | active |
| 875670001 | `pending_intermediate_approval` | Pending Intermediate Approval | active |
| 875670002 | `pending_final_approval` | Pending Final Approval | active |
| 875670004 | `revision` | Revision | active |
| 2 | `finalized` | Finalized | inactive |
| 875670003 | `cancelled` | Cancelled | inactive |

#### `wf_submission_status`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `pending` | Pending | active |
| 2 | `complete` | Complete | inactive |

#### `wf_approval_status`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `active` | Active | active |
| 2 | `inactive` | Inactive | inactive |

#### `wf_rejection_status`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `pending_changes` | Pending changes | active |
| 2 | `resubmitted` | Resubmitted | inactive |

#### `wf_approval_queue_status`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `pending` | Pending | active |
| 875670002 | `rejected` | Rejected | active |
| 875670003 | `contingent` | Contingent | active |
| 875670004 | `approved_active` | Approved | active |
| 875670006 | `complete` | Complete | active |
| 2 | `approved` | Approved | inactive |
| 875670005 | `closed` | Closed | inactive |

#### `perf_action_status` — Planned Measure / Milestone / Deliverable
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `in_progress` | In progress | active |
| 875670002 | `met` | Met | active |
| 875670001 | `unmet` | Unmet | active |
| 2 | `cancelled_closed` | Cancelled/closed | inactive |

#### `ref_simple_status` — all reference tables and `perf_action_measure`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `active` | Active | active |
| 2 | `inactive` | Inactive | inactive |

#### `core_task_status`
| Legacy | Value | Label | State |
|---|---|---|---|
| 1 | `not_started` | Not Started | open |
| 2 | `in_progress` | In Progress | open |
| 3 | `waiting_on_someone_else` | Waiting on Someone Else | open |
| 4 | `deferred` | Deferred | open |
| 5 | `completed` | Completed | completed |
| 6 | `cancelled` | Cancelled | cancelled |

*(Status 5 = Completed is the value the "Check submission related tasks for completion" job writes.)*

---

## 3. Identity, security and organisation tables

### 3.1 `core_app_user`

Replaces Dataverse `SystemUser`. Populated from ICAM / Entra ID.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | TEXT (uuid) | no | PK |
| `domain_name` | TEXT | no | unique; ICAM user principal name |
| `azure_object_id` | TEXT (uuid) | yes | unique; Entra ID object id |
| `full_name` | TEXT | no | used in every workflow message |
| `first_name`, `last_name` | TEXT | yes | |
| `title` | TEXT | yes | |
| `internal_email_address` | TEXT | yes | primary e-mail (used by the notifier) |
| `personal_email_address` | TEXT | yes | |
| `mobile_phone`, `main_phone`, `home_phone`, `other_phone`, `pager`, `fax` | TEXT | yes | |
| `preferred_phone_code`, `preferred_address_code` | TEXT | yes | |
| `mobile_alert_email` | TEXT | yes | |
| `address_composite`, `address2_composite` | TEXT | yes | |
| `business_unit_id` | TEXT (uuid) → `core_business_unit` | no | |
| `manager_id` | TEXT (uuid) → `core_app_user` | yes | self-reference |
| `position_id` | TEXT (uuid) → `core_position` | yes | |
| `default_queue_id` | TEXT (uuid) | yes | |
| `evaluation_id` | TEXT (uuid) → `evidence_evaluation` | yes | source `SystemUser.nrc_Evaluations` (relationship `nrc_Evaluations_nrc_Evaluations_SystemUse`) — the only one-to-many in the solution whose *referencing* table is the user table; see §7.2 |
| `access_mode`, `cal_type` | TEXT | yes | licence metadata |
| `is_disabled` | INTEGER (0/1) | no | default false |
| `state`, `created_on`, `modified_on`, … | | | standard block |

Views required: **SPA Users**.

### 3.2 `core_team`

Represents both generic teams and **Offices** (`is_office = true`).

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | TEXT (uuid) | no | PK |
| `name` | TEXT | no | unique; when `is_office` this is the Office name |
| `description` | TEXT | yes | |
| `business_unit_id` | TEXT (uuid) → `core_business_unit` | no | |
| `administrator_id` | TEXT (uuid) → `core_app_user` | yes | |
| `team_type` | TEXT | yes | owner / access / AAD security group / AAD office group |
| `azure_ad_object_id` | TEXT (uuid) | yes | |
| `membership_type` | TEXT | yes | |
| `is_office` | INTEGER (0/1) | no | `nrc_office` — **default true** in the source (`AppDefaultValue=1`; every new Team is flagged as an Office unless unticked); confirm with OEDO whether this default should be preserved or flipped in the rebuild |
| `office_id` | TEXT (uuid) → `ref_office` | yes | **[NEW]** explicit link to the Office record |
| standard block | | | |

Views required: **Offices** (filtered `is_office = true`), **SPA Teams**.

### 3.3 `core_team_membership`

| Column | Type | Null |
|---|---|---|
| `team_id` | TEXT (uuid) → `core_team` | no |
| `user_id` | TEXT (uuid) → `core_app_user` | no |
| `added_on` | TEXT (UTC timestamp) | no |

PK `(team_id, user_id)`.

### 3.4 `core_business_unit`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | TEXT (uuid) | no | PK |
| `name` | TEXT | no | unique |
| `parent_business_unit_id` | TEXT (uuid) → self | yes | hierarchy; drives Parent-Child depth |
| `is_root` | INTEGER (0/1) | no | |
| standard block | | | |

Two business units are referenced by the "Business Unit" rules: the **EDO** business unit and the
agency-wide ("all") business unit.

### 3.5 `core_security_role`, `core_privilege`, `core_role_privilege`, `core_user_role`, `core_team_role`

| `core_security_role` | Type | Notes |
|---|---|---|
| `id` | TEXT (uuid) | PK |
| `name` | TEXT | unique — `SPA View Only User`, `Quarterly Performance Submitter`, `EDO User`, `Deprecated - Quarterly Performance Approver` |
| `description` | TEXT | |
| `business_unit_id` | TEXT (uuid) | |
| `is_deprecated` | INTEGER (0/1) | |

| `core_privilege` | Type | Notes |
|---|---|---|
| `id` | TEXT (uuid) | PK |
| `entity_name` | TEXT | logical table name |
| `operation` | `core_privilege_operation` enum | `create` · `read` · `write` · `delete` · `append` · `append_to` · `assign` · `share` |

| `core_role_privilege` | Type | Notes |
|---|---|---|
| `role_id` | TEXT (uuid) → `core_security_role` | |
| `privilege_id` | TEXT (uuid) → `core_privilege` | |
| `depth` | `core_privilege_depth` enum | `user` · `business_unit` · `parent_child_business_unit` · `organization` |

PK `(role_id, privilege_id)`.

`core_user_role (user_id, role_id)` and `core_team_role (team_id, role_id)` assign roles.

The privilege matrix for the three live roles is in Document 1 §4.3. **Deprecated - Quarterly
Performance Approver** (977 privileges in the source) is seeded **name-only** with no privilege rows:
its shape is Read:Org + Append/AppendTo:User + Assign:Org + Share:Org across the business tables,
Read-only (no Create/Write) on Performance Indicator and Enterprise Risk, and **no privileges at all**
on `new_Signposts`. It is retired technical debt (Document 1 §13) and must not be granted access in
the rebuild.

### 3.6 `core_position`

| Column | Definition |
|---|---|
| `id` | TEXT (uuid) PK |
| `name` | TEXT |
| `parent_position_id` | TEXT (uuid) → self |

---

## 4. Reference / master-data tables

All reference tables use `ref_simple_status` and the standard column block.

### 4.1 `ref_fiscal_year`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_fiscalyearid` |
| `fiscal_year` | TEXT | no | unique, ≤ 100 | `nrc_fiscalyear` — the year label, e.g. `2024` |
| `start_date` | TEXT (date) | yes | | `nrc_start` |
| `end_date` | TEXT (date) | yes | | `nrc_end` |

### 4.2 `ref_office`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_officeid` |
| `office` | TEXT | no | ≤ 100, unique | `nrc_office` — Office name |
| `code` | TEXT | yes | ≤ 100 | `nrc_code` — used in every generated identifier |
| `prefix_code` | TEXT | yes | ≤ 100 | `nrc_prefixcode` |
| `display_name` | TEXT | yes | ≤ 4000, **computed** | `nrc_displayname` (calculated column) |

One row is named exactly `Agencywide` — the PI identifier algorithm and the risk dashboards depend on it.

### 4.3 `ref_division`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_divisionid` |
| `name` | TEXT | no | ≤ 100 | `nrc_name` — **labelled "Acronym" in the source (swapped, see Doc 1 §13.4)** |
| `acronym` | TEXT | yes | ≤ 100 | `nrc_acronym` — **labelled "Name" in the source** |

Many-to-many to Office (§10).

### 4.4 `ref_organization` (`nrc_Organization`)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_OrganizationId` |
| `name` | TEXT NOT NULL ≤ 100 | `nrc_Name` |

Used as *Accountable Organization* on Performance Indicator.

### 4.5 `ref_business_line`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_businesslineid` |
| `business_line` | TEXT | no | ≤ 850 | `nrc_businessline` |
| `br_code` | TEXT | yes | ≤ 100 | `nrc_brcode` — B&R Code, used in revised-PI identifiers |
| `prefix_code` | TEXT | yes | ≤ 100 | `nrc_prefixcode` — used in new-record identifiers |
| `alternate_owner_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_alternateowner` |

*(`nrc_test`, a calculated utility column, is not carried forward.)*

### 4.6 `ref_product_line` (`nrc_ProductLine`)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_ProductLineId` |
| `product_line` | TEXT NOT NULL ≤ 100 | `nrc_ProductLine` |
| `br_code` | TEXT ≤ 100 | `nrc_BRCode` |
| `prefix_code` | TEXT ≤ 100 | `nrc_PrefixCode` |

Many-to-many to Business Line (§10).

### 4.7 `ref_product` (`nrc_Product`)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_ProductId` |
| `product` | TEXT NOT NULL ≤ 850 | `nrc_Product` |
| `product_code` | TEXT ≤ 100 | `nrc_ProductCode` |
| `internal_product_name` | TEXT ≤ 4000 **computed** | `nrc_INTERNALProductName` |

### 4.8 `ref_major_program` (`nrc_MajorPrograms`)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_MajorProgramsId` |
| `name` | TEXT NOT NULL ≤ 100 | `nrc_Name` |

### 4.9 `ref_contributing_program`

(`nrc_ContributingProgramsandActivities`)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_ContributingProgramsandActivitiesId` |
| `name` | TEXT NOT NULL ≤ 400 | `nrc_Name` |

### 4.10 `ref_office_goal` (`nrc_OfficeGoals`)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_OfficeGoalsId` |
| `name` | TEXT NOT NULL ≤ 100 | `nrc_Name` |
| `office_id` | TEXT (uuid) → `ref_office` NOT NULL | `nrc_Office` |

---

## 5. Strategic Plan tables

### 5.1 `plan_goal`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_goalid` |
| `goal` | TEXT | no | ≤ 4000 | `nrc_goal` — **display name, auto-composed as `"{sequence}: {goal_text}"`** |
| `goal_text` | TEXT | yes | ≤ 800 | `nrc_goaltext` — the raw goal statement |
| `number` | INTEGER | yes | | `nrc_number` |
| `sequence` | INTEGER | yes | | `nrc_sequence` — drives the hierarchy-integrity checks |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | yes | | `nrc_fiscalyear` |
| `goal_image` | TEXT (object-store key) | yes | JPEG, ≤ 10 MB | `nrc_goalimage` |
| `objective_count` | INTEGER | yes | **rollup** | `nrc_objectivecount` |
| `strategy_count` | INTEGER | yes | **rollup** | `nrc_strategycount` |
| `indicators_count` | INTEGER | yes | **rollup** | `nrc_indicatorscount` |
| `risk_count` | INTEGER | yes | **rollup** | `nrc_riskcount` |
| `theme` | TEXT | yes | ≤ 100 | **[NEW]** — the name a strategic plan gives the goal (NRC's draft FY 2026–2030 plan, since taken out, called its first "Core Mission Delivery"). Its objectives are named `"{theme} Objective {n}:"`; null on every goal today, so every objective keeps the first-digit rule of §5.2 |

Many-to-many: Applicable Fiscal Years, Offices, Performance Indicators (§10). A strategic plan
is the span of its goals' Applicable Fiscal Years — FY 2022–2026, the one plan today — and has no
record of its own.

### 5.2 `plan_objective`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_objectiveid` |
| `objective` | TEXT | no | ≤ 4000 | `nrc_objective` — **display name, auto-composed** (see Doc 1 §8.1) |
| `title` | TEXT | yes | ≤ 1000 | `nrc_title` |
| `sequence` | TEXT | yes | | `nrc_sequence` (`numeric(10,2)` in earlier editions) — held literally, so `1.10` stays `1.10` (§1, Decimals) |
| `goal_id` | TEXT (uuid) → `plan_goal` | yes | | `nrc_strategicgoal` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | yes | | `nrc_fiscalyear` |

**Integrity rule:** `objective.sequence` must start with the goal's sequence followed by a dot —
`substr(objective.sequence, 1, length(CAST(goal.sequence AS TEXT)) + 1) = CAST(goal.sequence AS TEXT) || '.'`
(§12.3).

Many-to-many: Applicable Fiscal Years, External Factors, Performance Indicators (§10).

### 5.3 `plan_strategy`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_strategyid` |
| `strategy` | TEXT | no | ≤ 850 | `nrc_strategy` — display name `"{sequence} {title}"` |
| `title` | TEXT | yes | ≤ 1000 | `nrc_title` |
| `sequence` | TEXT | yes | ≤ 100 | `nrc_sequence` |
| `goal_id` | TEXT (uuid) → `plan_goal` | yes | | `nrc_strategicgoal` |
| `objective_id` | TEXT (uuid) → `plan_objective` | yes | | `nrc_strategicobjective` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | yes | | `nrc_fiscalyear` |

**Integrity rule:** `strategy.sequence` must start with `objective.sequence` followed by a dot (§12.3).

Many-to-many: Applicable Fiscal Years, External Factors, Enterprise Risks, Performance Indicators (§10).

### 5.4 `plan_performance_goal` (`nrc_PerformanceGoal`)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_PerformanceGoalId` |
| `performance_goal` | TEXT NOT NULL ≤ 1000 (display name `"{sequence} {title}"`) | `nrc_PerformanceGoal` |
| `title` | TEXT NOT NULL ≤ 1000 | `nrc_Title` |
| `sequence` | TEXT ≤ 100 | `nrc_Sequence` |

### 5.5 `plan_external_factor`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_ExternalFactorId` |
| `external_factor` | TEXT | no | ≤ 100 | `nrc_ExternalFactor` |
| `description` | TEXT | no | ≤ 4000 | `nrc_Description` |
| `affected_goal_id` | TEXT (uuid) → `plan_goal` | yes | | `nrc_AffectedGoal` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | no | | `nrc_FiscalYear` |

Many-to-many: Objectives, Strategies (§10).

### 5.6 `plan_definition` (glossary)

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_definitionid` |
| `title` | TEXT | no | ≤ 100 | `nrc_title` — the glossary term |
| `identification_number` | TEXT | yes | unique, auto `NRC-0001` | `nrc_identificationnumber` |
| `description` | TEXT | yes | ≤ 4000 | `nrc_description` — the definition text |
| `business_lines` | `ref_business_line_choice` | yes | | `nrc_businesslines` (choice, not FK) |
| `data_source` | `ref_data_source[]` | yes | multi-select | `nrc_datasource` → junction table |
| `fiscal_year` | INTEGER | yes | 0–9999 | `nrc_fiscalyear` (integer, **not** a FK) |
| `quarter` | `ref_quarter` | yes | | `nrc_quarter` |
| `business_product_line_owner_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_businessproductlineowner` |
| `office_id` | TEXT (uuid) → `ref_office` | yes | | `nrc_office` |
| `office_goal_id` | TEXT (uuid) → `ref_office` | yes | **points at Office in the source — see Doc 1 §13.4** | `nrc_officegoal` |
| `performance_indicator_id` | TEXT (uuid) → `perf_performance_indicator` | yes | | |
| `pi_result_id` | TEXT (uuid) → `perf_pi_result` | yes | | `nrc_performanceindicatorentry` |
| `product_id` | TEXT (uuid) → `ref_product` | yes | | |
| `goal_id` | TEXT (uuid) → `plan_goal` | yes | | |
| `objective_id` | TEXT (uuid) → `plan_objective` | yes | | |
| `strategy_id` | TEXT (uuid) → `plan_strategy` | yes | | |

Many-to-many: Business Lines, Product Lines (§10).

---

## 6. Performance Management tables

### 6.1 `perf_performance_indicator`

| Column | Type | Null | Constraint | Source | Notes |
|---|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_performanceindicatorid` | |
| `indicator_code` | TEXT | no | ≤ 850, unique | `nrc_performanceindicator` | **"Indicator ID"** — system generated (Doc 1 §8.1) |
| `indicator_title` | TEXT | no | ≤ 200 *(guide)* / 4000 *(schema)* | `nrc_indicatorid` | |
| `description` | TEXT | no | ≤ 950 *(schema)* / 1000 *(guide)* | `nrc_description` | counter tests 959; unreachable since the column was narrowed 1000→950 — Doc 3 §15.5.1 |
| `report_level` | `ref_report_level` | no | | `nrc_reportlevel` | |
| `implementation_year_id` | TEXT (uuid) → `ref_fiscal_year` | yes | | `nrc_fiscalyear` | |
| `contact_person_id` | TEXT (uuid) → `core_app_user` | no | | `nrc_contactperson` | |
| `owner_person_id` | TEXT (uuid) → `core_app_user` | no | | `nrc_owner` | distinct from record owner |
| `accountable_organization_id` | TEXT (uuid) → `ref_organization` | no | | `nrc_newaccountableorganization` | |
| `change_type` | `ref_change_type` | no | | `nrc_changetype` | |
| `previous_pi_id` | TEXT (uuid) → self | yes | required when `change_type='revised'` | `nrc_previouspi` | drives revision chaining + auto-fill |
| `indicator_status` | `ref_indicator_status` | yes | default `under_development` | `nrc_indstatus` | |
| `agency_wide_support_level` | `ref_agency_wide_support_level` | no | | `cr9de_agencywidesupportlevel` | EDO-only when `agency` |
| `data_source` | `ref_data_source` | yes | | `nrc_datasource` | |
| `other_data_source` | TEXT | yes | ≤ 4000 | `nrc_otherdatasource` | visible only when `data_source='other'` |
| `measure_type` | `ref_measure_type` | no | | `nrc_type` | drives the Range display rule |
| `indicator_type` | `ref_indicator_type` | no | | `nrc_indicatortype` | |
| `units` | `ref_units` | no | | `nrc_units` | |
| `results_calculation` | TEXT | no | ≤ 4000 *(schema)* / "670 or less" *(field description)* / 1000 *(guide)* | `nrc_resultscalculation` | |
| `business_line_id` | TEXT (uuid) → `ref_business_line` | no | | `nrc_businessline` | Lead Business Line |
| `product_line_id` | TEXT (uuid) → `ref_product_line` | no | | `nrc_productline` | Lead Product Line |
| `product_id` | TEXT (uuid) → `ref_product` | yes | | `nrc_product` | |
| `office_id` | TEXT (uuid) → `ref_office` | no | | `nrc_office` | Lead Office |
| `division_id` | TEXT (uuid) → `ref_division` | yes | | `nrc_division` | |
| `goal_id` | TEXT (uuid) → `plan_goal` | no | | `nrc_relatedgoal` | |
| `objective_id` | TEXT (uuid) → `plan_objective` | no | | `nrc_relatedobjective` | integrity-checked |
| `strategy_id` | TEXT (uuid) → `plan_strategy` | no | | `nrc_relatedstrategy` | integrity-checked |
| `performance_goal_id` | TEXT (uuid) → `plan_performance_goal` | yes | | `nrc_performancegoallu` | |
| `major_program_id` | TEXT (uuid) → `ref_major_program` | no | | `nrc_majorprogram` | |
| `contributing_program_id` | TEXT (uuid) → `ref_contributing_program` | no | | `nrc_contributingprogramsandactivities` | |
| `annual_performance_plan_and_report` | INTEGER (0/1) | no | | `nrc_annualperformanceplanandreport` | hidden on the form |
| `quarterly_performance_review` | INTEGER (0/1) | no | | `nrc_quarterlyperformancereview` | hidden on the form |
| `review_for_carry_over` | INTEGER (0/1) | yes | default false | `nrc_reviewforcarryover` | Flag/Unflag commands |
| `target` | REAL | yes | | `nrc_target` | |
| `mitigation_strategy` | TEXT | yes | ≤ 4000 | `nrc_mitigationstrategy` | |
| `comments` | TEXT (HTML) | yes | ≤ 2000 | `nrc_comments` | "COMMENTS REGARDING SUBMISSION" |
| `entry_count` | INTEGER | yes | ≥ 0, default 0 | `nrc_entrycount` | |
| `submitter_user_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_submitter` | workflow |
| `submitter_team_id` | TEXT (uuid) → `core_team` | yes | | `nrc_submitterteam` | workflow |
| `status_reason` | `perf_performance_indicator_status` | no | default `draft` | `statuscode` | |
| *(temp)* `temp_notes` | TEXT | yes | ≤ 2000 | `nrc_temp` | utility column — do not carry forward |

Many-to-many: Contributing Business Lines, Contributing Product Lines, Contributing Offices,
Contributing Major Programs, Other Contributing Programs, Goals, Objectives, Strategies,
Enterprise Risks, Accomplishments, Priorities, Risk Updates, PI Results (two separate
relationships — `nrc_manypis` and `nrc_manyupdates`) (§10). **14 junction tables in total.**

### 6.2 `perf_planned_measure` (Planned Measure, Milestone or Deliverable — "Action")

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_plannedmeasuremilestoneordeliverableid` |
| `title` | TEXT | no | ≤ 850 | `nrc_name` |
| `deliverable_title` | TEXT | yes | ≤ 1000 | `nrc_milestone` |
| `description` | TEXT | yes | ≤ 8000 | `nrc_description` |
| `status_update` | TEXT | yes | ≤ 2000 | `nrc_statusupdate` |
| `performance_goal` | TEXT | yes | ≤ 1000 | `nrc_performancegoal` (free text) |
| `type` | `ref_measure_type` | yes | | `nrc_type` |
| `performance_indicator_id` | TEXT (uuid) → `perf_performance_indicator` | no | | `nrc_regardingperformanceindicator` |
| `deliverable_file_id` | TEXT (uuid) → `core_file_attachment` | yes | ≤ 32 MB | `nrc_deliverable` |
| `status_reason` | `perf_action_status` | no | default `in_progress` | |

### 6.3 `perf_pi_result` (Performance Indicator Results)

The largest table. Per-quarter blocks repeat for Q1, Q2, Q3, Q4 and Annual.

**Header**

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_performanceindicatorfiscalyearid` |
| `indicator_code` | TEXT | no | ≤ 1000 | `nrc_title` — copied from the parent PI |
| `performance_indicator_id` | TEXT (uuid) → `perf_performance_indicator` | no | | `nrc_performanceindicator` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | no | | `nrc_fiscalyear` |
| `reporting_person_id` | TEXT (uuid) → `core_app_user` | no | defaults to creator | `nrc_reportingperson` |
| `reporting_office_id` | TEXT (uuid) → `ref_office` | no | | `nrc_reportingoffice` |
| `division_id` | TEXT (uuid) → `ref_division` | yes | | `nrc_division` |
| `reporting_business_line_id` | TEXT (uuid) → `ref_business_line` | yes | | `cr9de_businessline` |
| `product_line_id` | TEXT (uuid) → `ref_product_line` | yes | | `nrc_productline` |
| `major_program_id` | TEXT (uuid) → `ref_major_program` | yes | | `nrc_majorprogram` |
| `contributing_program_id` | TEXT (uuid) → `ref_contributing_program` | yes | | `nrc_contributingprogram` |
| `objective_id` | TEXT (uuid) → `plan_objective` | yes | | `nrc_strategicobjective` |
| `planned_measure_id` | TEXT (uuid) → `perf_planned_measure` | yes | | `nrc_plannedmeasuremilestoneordeliverable` |
| `office_team_id` | TEXT (uuid) → `core_team` | yes | | `nrc_officeteam` |
| `data_type` | `ref_data_type` | yes | **computed** from the PI | `nrc_datatype` |
| `indicator_type` | `ref_indicator_type` | yes | **computed** from the PI — a two-branch rule, **not** a copy: an *Outcome* (875670001) parent yields legacy code **875670002**, every other parent value yields *Output* (875670000). See Document 1 §8.5 | `nrc_indicatortype` — 875670002 is not a member of the source option set; map it to `outcome` (§2.1) |
| `internal_measure_type` | `ref_measure_type` | yes | **computed** from the PI | `nrc_internalmeasuretype` |
| `met_or_unmet` | INTEGER (0/1) | yes | | `nrc_metorunmet` |
| `mitigating_remarks` | TEXT | yes | ≤ 4000 | `nrc_mitigatingremarks` |
| `mitigating_strategies` | TEXT | yes | ≤ 100 | `nrc_mitigatingstrategies` |
| `public` | INTEGER (0/1) | yes | | `nrc_public` |
| `comments` | TEXT (HTML) | yes | ≤ 8000 | `nrc_comments` |
| `submitter_user_id` / `submitter_team_id` | TEXT (uuid) | yes | | workflow |
| `status_reason` | `perf_pi_result_status` | no | default `draft` | |

**Quarters (multi-select)** — child table `perf_pi_result_quarter (pi_result_id, quarter)` reproducing
`nrc_quarters` (multi-select `ref_quarter`). Required: at least one row.

**Per-period measurement block** — one row per period in `perf_pi_result_period`:

| Column | Type | Null | Applies to | Source (Q1 example) |
|---|---|---|---|---|
| `pi_result_id` | TEXT (uuid) → `perf_pi_result` | no | | |
| `period` | `ref_quarter` | no | Q1–Q4 + Annual | |
| `results` | REAL | yes | quantitative | `nrc_q1results` |
| `operator` | `ref_operator` | yes | quantitative | `nrc_q1operator` |
| `target` | REAL | yes | quantitative | `nrc_q1target` |
| `minimum_target` | REAL | yes | **range** | `nrc_q1minimumtarget` |
| `maximum_target` | REAL | yes | **range** | `nrc_q1maximumtarget` |
| `lower_operator` | `ref_operator` | yes | **range** | `nrc_q1loweroperator` |
| `upper_operator` | `ref_operator` | yes | **range** | `nrc_q1upperoperator` |
| `not_applicable` | INTEGER (0/1) | no | all | `nrc_q1notapplicable` — clears + locks `results` |
| `success_likelihood` | `ref_success_likelihood` | yes | all | `nrc_q1successlikelihood` |
| `mitigation_remarks` | TEXT ≤ 800 | yes | all | `nrc_q1mitigationremarks` |
| `raw_data` | TEXT ≤ 850 (Q1–Q4) / ≤ 100 (Annual in the source — widened to 850 on migration) | yes | all | `nrc_q1rawdata1` |

PK `(pi_result_id, period)`.

> The source system stores these as **55 flat columns** (11 fields × 5 periods). Normalising them into
> `perf_pi_result_period` removes 44 columns, makes the Range/Regular rule a single predicate, and
> makes the dashboard un-pivot (which Power BI performs today) a straight query. The exact legacy
> column for every field is listed in §15.3 so migration is mechanical.
> The Annual period's "Mitigation / Remarks" is stored in `nrc_statusupdatesummary`
> (display name *"Annual Mitigation / Remarks"*) — mapped to `period='annual'`, `mitigation_remarks`.

Many-to-many: Contributing Business Lines, Contributing Product Lines, Contributing Offices,
Contributing Major Programs, Other Contributing Programs, Performance Indicators (two separate
relationships), Users (revision history) (§10).

### 6.4 `perf_enterprise_risk`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_enterpriseriskid` |
| `risk_code` | TEXT | no | ≤ 850, unique | `nrc_risktitle` — **labelled "Risk ID"**, system generated |
| `risk_title` | TEXT | yes | ≤ 850 / 100 *(guide)* | `nrc_riskid` — **labelled "Risk Title"** |
| `enterprise_risk_title` | TEXT | yes | ≤ 4000, **computed / read-only** | `nrc_enterpriserisktitle` — calculated column (`SourceType=1`, not writable via create or update); its formula body is **absent from the export** and must be recovered from the live environment |
| `description` | TEXT | no | ≤ 300 *(schema)* / 310 *(guide)* | `nrc_description` |
| `report_level` | `ref_report_level` | no | | `nrc_reportlevel` |
| `risk_status` | `ref_risk_status` | no | default `under_development` | `nrc_riskstatus` |
| `originating_fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | no | | `nrc_originatingfiscalyear` |
| `originating_quarter` | `ref_quarter` | no | | `nrc_originatingquarter` |
| `office_id` | TEXT (uuid) → `ref_office` | no | | `nrc_office` — Lead Office |
| `owner_office_id` | TEXT (uuid) → `ref_office` | yes | | `nrc_owneroffice` |
| `division_id` | TEXT (uuid) → `ref_division` | yes | | `nrc_division` |
| `impacted_goal_id` | TEXT (uuid) → `plan_goal` | no | | `nrc_impactedstrategicgoal` |
| `impacted_objective_id` | TEXT (uuid) → `plan_objective` | no | | `nrc_impactedobjective` |
| `strategy_id` | TEXT (uuid) → `plan_strategy` | no | | `nrc_strategy` — Impacted Strategy |
| `goal_id` | TEXT (uuid) → `plan_goal` | yes | | `nrc_strategicgoal` |
| `objective_strategy_id` | TEXT (uuid) → `plan_strategy` | yes | **points at Strategy in the source** | `nrc_strategicobjective` |
| `strategic_plan_strategy_id` | TEXT (uuid) → `plan_strategy` | yes | | `nrc_strategicplanstrategy` |
| `business_line_id` | TEXT (uuid) → `ref_business_line` | no | | `nrc_businessline` |
| `product_line_id` | TEXT (uuid) → `ref_product_line` | no | | `nrc_productline` |
| `product_id` | TEXT (uuid) → `ref_product` | yes | | `nrc_product` |
| `major_program_id` | TEXT (uuid) → `ref_major_program` | no | | `nrc_majorprogram` |
| `contributing_program_id` | TEXT (uuid) → `ref_contributing_program` | no | | `nrc_contributingprogramsandactivites` |
| `business_product_line_owner_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_businesslineproductlineowner` |
| `no_associated_performance_indicators` | INTEGER (0/1) | yes | | `nrc_noassociatedperformanceindicators` |
| `related_pi_required` | TEXT | no | ≤ 850 | `nrc_relatedpirequired` — "Yes" makes the PI sub-grid mandatory |
| `impact` | `ref_level` | yes | legacy | `nrc_impact` |
| `impact_description` | TEXT | yes | ≤ 8000 | `nrc_impactdescription1` |
| `impact_description_legacy` | TEXT | yes | ≤ 4000 | `nrc_impactdescription` — duplicate, retire |
| `likelihood` | `ref_level` | yes | legacy | `nrc_likelihood` |
| `likelihood_description` | TEXT | yes | ≤ 8000 | `nrc_likelihooddescription` |
| `additional_factors` | TEXT | yes | ≤ 8000 | `nrc_additionalfactors` |
| `initial_risk_control_efforts` | TEXT | yes | ≤ 8000 | `nrc_initialriskcontrolefforts` |
| `performance_monitoring_progress_plans` | TEXT | yes | ≤ 8000 | `nrc_performancemonitoringprogressplans` |
| `public` | INTEGER (0/1) | yes | | `nrc_public` |
| `entry_count` | TEXT | yes | ≤ 4000, default `'0'` | `nrc_entrycount` — **should become integer** |
| `comments` | TEXT (HTML) | yes | ≤ 2000 | `nrc_comments` |
| `pl_text` | TEXT | yes | ≤ 4000 | `nrc_pltext` — migration column, move to `staging` |
| `submitter_user_id` / `submitter_team_id` | TEXT (uuid) | yes | | workflow |
| `status_reason` | `perf_enterprise_risk_status` | no | default `draft` | |

Many-to-many: Related Performance Indicators, Applicable Fiscal Years, Contributing Offices,
Contributing Major Programs, Other Contributing Programs, Contributing Business Lines,
Contributing Product Lines, Strategies (§10).

### 6.5 `perf_risk_update`

**Header**

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_riskupdateid` |
| `entry_code` | TEXT | no | ≤ 850 | `nrc_entryid` — copied from the parent risk |
| `enterprise_risk_id` | TEXT (uuid) → `perf_enterprise_risk` | no | | `nrc_enterpriserisk` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | no | | `nrc_fiscalyear` |
| `quarter` | `ref_quarter` | no | | `nrc_quarters` |
| `psat` | INTEGER (0/1) | yes | true = PSAT, false = Non-PSAT | `nrc_psat` |
| `reporting_office_id` | TEXT (uuid) → `ref_office` | yes | | `nrc_owneroffice` |
| `contact_person_id` | TEXT (uuid) → `core_app_user` | no | | `nrc_contactperson` |
| `risk_lead_id` | TEXT (uuid) → `core_app_user` | no | | `nrc_risklead` |
| `owner_person_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_owner` |
| `business_line_id` | TEXT (uuid) → `ref_business_line` | yes | | `nrc_businessline` |
| `product_line_id` | TEXT (uuid) → `ref_product_line` | yes | | `nrc_productline` |
| `major_program_id` | TEXT (uuid) → `ref_major_program` | yes | | `nrc_majorprogram` |
| `contributing_program_id` | TEXT (uuid) → `ref_contributing_program` | yes | | `nrc_contributingprogram` |
| `contributing_bl_id` / `contributing_pl_id` | TEXT (uuid) | yes | **polymorphic in the source** (`nrc_contributingblpl` → Business Line *or* Product Line) — split into two nullable FKs | `nrc_contributingblpl` |
| `qpr` | INTEGER (0/1) | yes | | `nrc_qpr` |
| `qpr_discussion` | INTEGER (0/1) | yes | | `nrc_qprdiscussion` |
| `psat_accepted` | INTEGER (0/1) | yes | | `nrc_psataccepted` |
| `psat_comments` | TEXT | yes | ≤ 2000 | `nrc_psatcomments` |
| `budget_strings` | TEXT | yes | ≤ 225 *(schema)* / 300 *(guide)* | `nrc_budgetstrings` |
| `additional_factors` | TEXT | yes | ≤ 8000 (guide: 700) | `nrc_additionalfactors` |
| `risk_outlook` | `ref_risk_outlook` | no | | `nrc_riskoutlook` |
| `risk_accepted` | INTEGER (0/1) | no | | `nrc_riskaccepted` — controls the ACT requirement |
| `comments` | TEXT (HTML) | yes | ≤ 2000 | `nrc_comments` |
| `submitter_user_id` / `submitter_team_id` | TEXT (uuid) | yes | | workflow |
| `status_reason` | `perf_qpr_record_status` | no | default `draft` | |

**Risk scoring block**

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `inherent_likelihood` | `ref_level` | no | | `nrc_inherentlikelihood` |
| `inherent_likelihood_qpr_description` | TEXT | no | ≤ 300 | `nrc_inherentlikelihooddescription` |
| `inherent_likelihood_full_description` | TEXT | yes | ≤ 999999 | `nrc_inherentlikelihoodfulldescription` |
| `inherent_consequence` | `ref_level` | no | | `nrc_impactlevel` |
| `inherent_consequence_qpr_description` | TEXT | no | ≤ 300 | `nrc_inherentconsequencedescription` |
| `inherent_consequence_full_description` | TEXT | yes | ≤ 999999 | `nrc_inherentconsequencefulldescription` |
| `residual_likelihood` | `ref_level` | no | | `nrc_likelihoodlevel` |
| `residual_likelihood_qpr_description` | TEXT | no | ≤ 300 | `nrc_residuallikelihooddescription1` |
| `residual_likelihood_full_description` | TEXT | yes | ≤ 999999 | `nrc_residuallikelihoodfulldescription` |
| `residual_consequence` | `ref_level` | no | | `nrc_residualimpact` |
| `residual_consequence_qpr_description` | TEXT | no | ≤ 300 | `nrc_residualimpactdescription` |
| `residual_consequence_full_description` | TEXT | yes | ≤ 999999 | `nrc_residualconsequencefulldescription` |
| `last_quarter_inherent_likelihood` | `ref_level` | yes | auto-populated | `nrc_lastquartersinherentlikelihood` |
| `last_quarter_inherent_consequence` | `ref_level` | yes | auto-populated | `nrc_lastquartersinherentconsequence` |
| `last_quarter_residual_likelihood` | `ref_level` | yes | auto-populated | `nrc_lastquartersresiduallieklihood` |
| `last_quarter_residual_consequence` | `ref_level` | yes | auto-populated | `nrc_lastquartersresidualconsequence` |

**Response and monitoring block**

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `manage_current_response_qpr_description` | TEXT | no | ≤ 600 | `nrc_currentriskcontrolefforts` |
| `manage_current_response_full_description` | TEXT | yes | ≤ 999999 | `nrc_managecurrentriskresponsedescription` |
| `act_proposed_response_qpr_description` | TEXT | conditional | ≤ 300 — **required unless `risk_accepted`** | `nrc_goforwardcontrolplans` |
| `act_proposed_response_full_description` | TEXT | yes | ≤ 999999 | `nrc_actproposedriskresponsedescription` |
| `risk_monitoring_qpr_description` | TEXT | no | ≤ 300 | `nrc_riskmonitoring` |
| `risk_monitoring_full_description` | TEXT | yes | ≤ 999999 | `nrc_riskmonitoringfullcontext` |
| `informed_monitoring_qpr_description` | TEXT | no | ≤ 300 | `nrc_informedmonitoring` |
| `informed_monitoring_full_description` | TEXT | yes | ≤ 999999 | `nrc_informedmonitoringfullcontext` |

Many-to-many: Contributing Business Lines, Contributing Product Lines, Contributing Offices,
Contributing Major Programs, Other Contributing Programs, Performance Indicators (§10).

Unique constraint recommended: `(enterprise_risk_id, fiscal_year_id, quarter)`.

### 6.6 `perf_accomplishment`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_accomplishmentid` |
| `accomplishment_code` | TEXT | no | ≤ 4000, unique | `nrc_accomplishment` — `ACC-…`, system generated |
| `title` | TEXT | no | ≤ 100 | `nrc_title` |
| `description` | TEXT | no | ≤ 850 | `nrc_description` |
| `report_level` | `ref_report_level` | yes | | `nrc_reportlevel` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | no | | `nrc_fiscalyear` |
| `owner_person_id` | TEXT (uuid) → `core_app_user` | no | | `nrc_owner` |
| `contact_person_id` | TEXT (uuid) → `core_app_user` | no | | `nrc_contactperson` |
| `business_line_id` | TEXT (uuid) → `ref_business_line` | no | | `nrc_businessline` |
| `product_line_id` | TEXT (uuid) → `ref_product_line` | no | | `nrc_productline` |
| `product_id` | TEXT (uuid) → `ref_product` | yes | | `nrc_product` |
| `primary_related_pi_id` | TEXT (uuid) → `perf_performance_indicator` | yes | triggers strategic auto-fill | `nrc_primaryrelatedpi` |
| `goal_id` | TEXT (uuid) → `plan_goal` | no | | `nrc_strategicgoal` |
| `objective_id` | TEXT (uuid) → `plan_objective` | no | | `nrc_strategicobjective` |
| `strategy_id` | TEXT (uuid) → `plan_strategy` | no | | `nrc_strategy` |
| `major_program_id` | TEXT (uuid) → `ref_major_program` | no | | `nrc_majorprogram` |
| `contributing_program_id` | TEXT (uuid) → `ref_contributing_program` | no | | `nrc_contributingprogramsandactivities` |
| `office_id` | TEXT (uuid) → `ref_office` | no | | `nrc_office` |
| `division_id` | TEXT (uuid) → `ref_division` | yes | | `nrc_division` |
| `related_ecq` | `ref_related_ecq` | yes | | `nrc_relatedecq` |
| `related_pi` | INTEGER (0/1) | yes | | `nrc_relatedpi` |
| `related_pi_required` | TEXT | no | ≤ 100 | `nrc_relatedpirequired` |
| `annual_performance_plan` | INTEGER (0/1) | no | | `nrc_annualperformanceplan` |
| `quarterly_performance_review` | INTEGER (0/1) | no | | `nrc_quarterlyperformancereview` |
| `public` | INTEGER (0/1) | yes | | `nrc_public` |
| `program_text` | TEXT | yes | ≤ 1000 | `nrc_programtext` — migration column, move to `staging` |
| `comments` | TEXT (HTML) | yes | ≤ 2000 | `nrc_comments` — "COMMENTS REGARDING RESUBMISSION" |
| `submitter_user_id` / `submitter_team_id` | TEXT (uuid) | yes | | workflow |
| `status_reason` | `perf_qpr_record_status` | no | default `draft` | |

**Quarters (multi-select)** — `perf_accomplishment_quarter (accomplishment_id, quarter)`.

Many-to-many: Contributing Business Lines, Contributing Product Lines, Other Related Performance
Indicators, Contributing Major Programs, Other Contributing Programs, Contributing Offices (§10).

### 6.7 `perf_priority`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_prioritiesupdateid` |
| `update_code` | TEXT | no | ≤ 100, unique | `nrc_updateid` — system generated |
| `title` | TEXT | no | ≤ 4000 (guide: 100) | `nrc_prioritiestitle` |
| `description` | TEXT | no | ≤ 4000 (guide: 650) | `nrc_prioritiesdescription` |
| `report_level` | `ref_report_level` | no | | `nrc_reportlevel` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | no | | `nrc_fiscalyear` |
| `rank` | `ref_rank` | no | 1–11 | `nrc_rank` |
| `principle_of_good_regulation` | `ref_principle_of_good_regulation` | no | | `nrc_principlesofgoodrecognition` |
| `business_line_id` | TEXT (uuid) → `ref_business_line` | no | | `nrc_businessline` |
| `product_line_id` | TEXT (uuid) → `ref_product_line` | no | | `nrc_productline` |
| `product_id` | TEXT (uuid) → `ref_product` | yes | | `nrc_product` |
| `goal_id` | TEXT (uuid) → `plan_goal` | no | | `nrc_strategicgoal` |
| `objective_id` | TEXT (uuid) → `plan_objective` | no | | `nrc_strategicobjective` |
| `strategy_id` | TEXT (uuid) → `plan_strategy` | no | | `nrc_strategy` |
| `major_program_id` | TEXT (uuid) → `ref_major_program` | no | | `nrc_majorprogram` |
| `contributing_program_id` | TEXT (uuid) → `ref_contributing_program` | no | | `nrc_contributingprogramsandactivities` |
| `office_id` | TEXT (uuid) → `ref_office` | no | | `nrc_office` |
| `division_id` | TEXT (uuid) → `ref_division` | yes | | `nrc_division` |
| `priorities_owner_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_prioritiesowner` |
| `office_goals` | TEXT | yes | ≤ 100 | `nrc_officegoals` |
| `related_pi_required` | TEXT | no | ≤ 100 | `nrc_relatedpirequired` |
| `public` | INTEGER (0/1) | yes | | `nrc_public` |
| `comments` | TEXT (HTML) | yes | ≤ 2000 | `nrc_comments` |
| `submitter_user_id` / `submitter_team_id` | TEXT (uuid) | yes | | workflow |
| `status_reason` | `perf_qpr_record_status` | no | default `draft` | |

**Quarters (multi-select)** — `perf_priority_quarter (priority_id, quarter)`.

Many-to-many: Contributing Business Lines, Contributing Product Lines, Contributing Offices,
Contributing Major Programs, Other Contributing Programs, Related Performance Indicators (§10).

### 6.8 `perf_positive_change_management`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_positivechangemanagementid` |
| `pcm_code` | TEXT | no | ≤ 100, unique | `nrc_pcmid` — `PCM-…`, system generated |
| `title` | TEXT | no | ≤ 850 (guide: 100) | `nrc_title` |
| `description` | TEXT | no | ≤ 1200 | `nrc_positivechangemgmtitem` |
| `report_level` | `ref_report_level` | no | | `nrc_reportlevel` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | no | | `nrc_fiscalyear` |
| `quarter` | `ref_quarter` | no | | `nrc_quarter` |
| `contact_person_id` | TEXT (uuid) → `core_app_user` | no | | `nrc_contactperson` |
| `business_line_id` | TEXT (uuid) → `ref_business_line` | no | | `nrc_businessline` |
| `product_line_id` | TEXT (uuid) → `ref_product_line` | no | | `nrc_productline` |
| `product_id` | TEXT (uuid) → `ref_product` | yes | | `nrc_product` |
| `goal_id` | TEXT (uuid) → `plan_goal` | no | | `nrc_strategicgoal` |
| `objective_id` | TEXT (uuid) → `plan_objective` | no | | `nrc_strategicobjective` |
| `strategy_id` | TEXT (uuid) → `plan_strategy` | no | | `nrc_strategy` |
| `major_program_id` | TEXT (uuid) → `ref_major_program` | no | | `nrc_majorprogram` |
| `contributing_program_id` | TEXT (uuid) → `ref_contributing_program` | no | | `nrc_contributingprogramsandactivities` |
| `office_id` | TEXT (uuid) → `ref_office` | no | | `nrc_owneroffice` — Lead Office |
| `partner_office_id` | TEXT (uuid) → `ref_office` | yes | | `nrc_partneroffices` — Associated Offices |
| `division_id` | TEXT (uuid) → `ref_division` | yes | | `nrc_division` |
| `division_owner_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_divisionowners` (single lookup) |
| `office_goals` | TEXT | yes | ≤ 100 | `nrc_officegoals` |
| `presented_at_qpr` | INTEGER (0/1) | no | | `nrc_presentedatqpr` |
| `public` | INTEGER (0/1) | yes | | `nrc_public` |
| `entry_count` | INTEGER | yes | | `nrc_entrycount` |
| `comments` | TEXT (HTML) | yes | ≤ 2000 | `nrc_comments` |
| `submitter_user_id` / `submitter_team_id` | TEXT (uuid) | yes | | workflow |
| `status_reason` | `perf_qpr_record_status` | no | default `draft` | |

Many-to-many: Contributing Business Lines, Contributing Product Lines, Contributing Major Programs,
Contributing Programs, **Division Owner(s) (Users)**, Contributing Offices (§10).

### 6.9 `perf_action_measure` (legacy "Action/Measure" table)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_ActionMeasureId` |
| `title` | TEXT NOT NULL ≤ 850 | `nrc_Name` |
| `number` | INTEGER | `nrc_Number` |
| `timeframe` | TEXT ≤ 2000 | `nrc_Timeframe` |
| `objective_satisfied` | INTEGER (0/1) | `nrc_Objectivesatisfied` |
| `completed_or_carried_forward` | INTEGER (0/1; 1 = Carried forward) — **default true**, i.e. Carried forward | `nrc_Completedorcarriedforward` |
| `completion_carryover_notes` | TEXT ≤ 2000 | `nrc_Completioncarryovernotes` |
| `status_reason` | `ref_simple_status` — default `active` | `statuscode` |

Many-to-many: Offices (§10).

### 6.10 `perf_priority_legacy` — `(DEPRECATED) Priority`

Retained only for migration reconciliation; **not** part of the target application.

| Column | Definition | Legacy column |
|---|---|---|
| `id` | TEXT (uuid) PK | `nrc_prioritiesid` |
| `indicator_id` | TEXT ≤ 100 | `nrc_indicatorid` |
| `priorities_title` | TEXT ≤ 100 | `nrc_prioritiestitle` |
| `priority_description` | TEXT ≤ 2000 | `nrc_prioritydescription` |
| `principle_of_good_regulation` | TEXT enum | `nrc_principlesofgoodregulation` |
| `quarters` | TEXT enum | `nrc_quarters` |
| `rank` | TEXT enum | `nrc_rank` |

Status values: Draft · Pending intermediate approval · Pending final approval · Approved · Inactive.

---

## 7. Evidence Building tables

### 7.1 `evidence_priority_question`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_priorityquestionid` |
| `priority_question` | TEXT | no | ≤ 4000 | `nrc_priorityquestion` |
| `answer_type` | `ref_answer_type` | yes | | `nrc_answertype` |
| `answer_evaluation_id` | TEXT (uuid) → `evidence_evaluation` | yes | **polymorphic in the source** — split into two nullable FKs | `nrc_answer` |
| `answer_research_activity_id` | TEXT (uuid) → `evidence_research_activity` | yes | | `nrc_answer` |
| `approval_stage` | INTEGER | yes | | `nrc_approvalstage` |
| `approver_comments_revisions` | TEXT | yes | ≤ 2000 | `nrc_approvercommentsrevisions` |
| `publish` | TEXT | yes | ≤ 100 | `nrc_publish` — **string in the source, should become boolean** |
| `status_reason` | `evidence_eb_record_status` | no | default `draft` | |

Constraint: at most one of `answer_evaluation_id` / `answer_research_activity_id` is non-null.

### 7.2 `evidence_evaluation`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_evaluationsid` |
| `title` | TEXT | no | ≤ 100 | `nrc_title` |
| `summary` | TEXT | no | ≤ 750 | `nrc_summary` |
| `evaluation_objective` | TEXT (HTML) | yes | ≤ 2000 | `nrc_evaluationobjective` |
| `key_questions` | TEXT (HTML) | yes | ≤ 2000 | `nrc_keyquestions` |
| `evaluation_methods` | TEXT (HTML) | yes | ≤ 2000 | `nrc_evaluationmethods` |
| `data_needs_and_sources` | TEXT (HTML) | yes | ≤ 2000 | `nrc_dataneedsandsources` |
| `stakeholder_engagement` | TEXT (HTML) | yes | ≤ 2000 | `nrc_stakeholderengagement` |
| `challenges_and_mitigating_strategies` | TEXT (HTML) | yes | ≤ 2000 | `nrc_challengesandmitigatingstrategies` |
| `status` | `ref_evidence_building_status` | no | | `nrc_status` |
| `status_description` | TEXT (HTML) | yes | ≤ 2000 | `nrc_statusdescription` |
| `type_of_activity` | TEXT | yes | ≤ 100 | `nrc_typeofactivity` |
| `contractor_support` | TEXT | yes | ≤ 2000 | `nrc_contractorsupport` |
| `total_resources_dollars` | INTEGER (money × 10 000) | yes | | `nrc_totalresourcesdollars` |
| `total_resources_fte` | REAL | yes | | `nrc_totalresourcesfte` |
| `office_id` | TEXT (uuid) → `ref_office` | no | | `nrc_office` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | yes | | `nrc_fiscalyear` |
| `performance_indicator_id` | TEXT (uuid) → `perf_performance_indicator` | yes | | |
| `goal_id` | TEXT (uuid) → `plan_goal` | yes | | `nrc_relatedstrategicgoal` |
| `objective_id` | TEXT (uuid) → `plan_objective` | yes | | `nrc_relatedstategicobjective` |
| `publish` | INTEGER (0/1) | no | | `nrc_publish` |
| `approval_order_stage` | INTEGER | yes | ≥ 1, default 1 | `nrc_approvalorderstage` |
| `approver_comments_revisions` | TEXT | yes | ≤ 2000 | `nrc_approvercommentsrevisions` |
| `status_reason` | `evidence_eb_record_status` | no | default `draft` | |

> The source also carries `nrc_totalresourcesdollars_base` (*"Total Resources, Dollars (Base)"*), the
> Dataverse base-currency shadow of the money column. With a single currency there is nothing to
> convert, so it is **not carried forward**; the same applies to `nrc_OtherEvidenceBuildingActivity`.

Many-to-many: Products (§10).
*(The source also carries a `SystemUser.nrc_Evaluations` lookup — a user-level pointer to an
Evaluation. Modelled as `core_app_user.evaluation_id`.)*

### 7.3 `evidence_research_activity` (`nrc_OtherEvidenceBuildingActivity`)

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_otherevidencebuildingactivityid` |
| `activity_title` | TEXT | no | ≤ 100 | `nrc_name` |
| `overview` | TEXT | yes | ≤ 2000 | `nrc_overview` |
| `drivers` | TEXT (HTML) | yes | ≤ 2000 | `nrc_drivers` |
| `impact_and_benefits` | TEXT (HTML) | yes | ≤ 2000 | `nrc_impactandbenefits` |
| `stakeholder_engagement` | TEXT (HTML) | yes | ≤ 2000 | `nrc_stakeholderengagement` |
| `strategic_focus_area` | TEXT (HTML) | yes | ≤ 2000 | `nrc_strategicfocusarea` |
| `type` | `ref_evidence_building_activity_type` | no | | `nrc_type` |
| `contractor_support` | TEXT | yes | ≤ 2000 | `nrc_contractorsupport` |
| `total_resources_dollars` | INTEGER (money × 10 000) | yes | ≥ 0 | `nrc_totalresourcesdollars` |
| `total_resources_fte` | INTEGER | yes | | `nrc_totalresourcesfte` |
| `lead_office_id` | TEXT (uuid) → `ref_office` | yes | | `nrc_leadoffice` |
| `point_of_contact_id` | TEXT (uuid) → `core_app_user` | no | | `nrc_pointofcontact` |
| `fiscal_year_id` | TEXT (uuid) → `ref_fiscal_year` | yes | | `nrc_fiscalyear` |
| `performance_indicator_id` | TEXT (uuid) → `perf_performance_indicator` | yes | | |
| `goal_id` | TEXT (uuid) → `plan_goal` | yes | | `nrc_strategicgoal` |
| `objective_id` | TEXT (uuid) → `plan_objective` | yes | | `nrc_strategicobjective` |
| `publish` | INTEGER (0/1) | yes | | `nrc_publish` |
| `approval_stage` | INTEGER | yes | | `nrc_approvalstage` |
| `approver_comments_revisions` | TEXT | yes | ≤ 2000 | `nrc_approvercommentsrevisions` |
| `status_reason` | `evidence_eb_record_status` | no | default `draft` | |

Many-to-many: Products (§10).

---

## 8. Signposts and Markers tables

### 8.1 `plan_signpost` (`new_Signposts` — note the `new_` publisher prefix, not `nrc_`)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `new_SignpostsId` |
| `title` | TEXT NOT NULL ≤ 100 | `new_Title` |
| `signpost_number` | TEXT ≤ 100 | `new_SignpostNumber` |
| `analysis` | TEXT (HTML) NOT NULL ≤ 2000 | `new_Analysis` |
| `name` | TEXT ≤ 100 (= title) | `new_Name` (Dataverse primary-name column) |

### 8.2 `plan_key_area` (`new_KeyAreas` — `new_` publisher prefix)

| Column | Definition | Source |
|---|---|---|
| `id` | TEXT (uuid) PK | `new_KeyAreasId` |
| `title` | TEXT NOT NULL ≤ 100 | `new_Title` |
| `key_area_number` | TEXT ≤ 100 | `new_KeyAreaNumber` |
| `analysis` | TEXT (HTML) NOT NULL ≤ 2000 | `new_Analysis` |
| `signpost_id` | TEXT (uuid) → `plan_signpost` NOT NULL | `new_AssociatedSignpost` |
| `name` | TEXT ≤ 100 (= title) | `new_Name` (Dataverse primary-name column) |

---

## 9. Workflow, notification and audit tables

### 9.1 `wf_submission`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_submissionid` |
| `name` | TEXT | no | ≤ 850 | `nrc_name` — `"{Type} {DocumentID} submitted at {ts} by {Submitter}."` (Performance Indicator and Enterprise Risk interpolate the record title — `nrc_indicatorid` / `nrc_riskid` — not the Document ID) |
| `record_type` | `ref_record_type` | no | | `nrc_type` |
| `document_guid` | TEXT | yes | ≤ 1000 | `nrc_documentguid` — `"{prefix}-{record uuid}"` |
| `from_user_id` | TEXT (uuid) → `core_app_user` | no | source `RequiredLevel=required` — every submission carries a submitting user | `nrc_from` |
| `from_team_id` | TEXT (uuid) → `core_team` | yes | | `nrc_fromteam` |
| `to_user_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_to` |
| `to_team_id` | TEXT (uuid) → `core_team` | yes | | `nrc_toteam` |
| `task_id` | TEXT (uuid) → `core_task` | yes | | `nrc_task` |
| `task_made` | INTEGER (0/1) | no | default false | `nrc_taskmade` |
| `approved` | INTEGER (0/1) | yes | | `nrc_approved` |
| `returned` | INTEGER (0/1) | yes | | `nrc_returned` |
| `resubmission` | INTEGER (0/1) | yes | | `nrc_resubmission` |
| `performance_indicator_id` | TEXT (uuid) | yes | typed FK | `nrc_performanceindicator` |
| `pi_result_id` | TEXT (uuid) | yes | typed FK | `nrc_piresult` |
| `enterprise_risk_id` | TEXT (uuid) | yes | typed FK | `nrc_enterpriserisk` |
| `risk_update_id` | TEXT (uuid) | yes | typed FK | `nrc_riskupdate` |
| `priority_id` | TEXT (uuid) | yes | typed FK | `nrc_priority` |
| `positive_change_management_id` | TEXT (uuid) | yes | typed FK | `nrc_positivechangemanagement` |
| `accomplishment_id` | TEXT (uuid) | yes | typed FK | `nrc_accomplishment` |
| `status_reason` | `wf_submission_status` | no | default `pending` | |

Constraint: exactly one of the seven typed FKs is non-null, and it must match `record_type`.

### 9.2 `wf_approval`

Identical shape to `wf_submission`, minus `approved` / `returned` / `resubmission`, plus:

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (uuid) | PK — source `nrc_ApprovalId` |
| `from_user_id` / `from_team_id` | TEXT (uuid) | **"Approved by"** — source `nrc_From` / `nrc_Fromteam` |
| `submission_id` | TEXT (uuid) → `wf_submission` | `nrc_Submission` |
| `name` | TEXT | `"{Type} {DocumentID} approved by {Approver} at {ts}."` — source `nrc_Name` (Performance Indicator and Enterprise Risk interpolate the record title — `nrc_indicatorid` / `nrc_riskid` — not the Document ID) |
| `status_reason` | `wf_approval_status` | default `active` |

### 9.3 `wf_rejection`

Identical shape, plus:

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (uuid) | PK — source `nrc_RejectionId` |
| `returned_by` | TEXT ≤ 100 | `nrc_Returnedby` |
| `submission_id` | TEXT (uuid) → `wf_submission` | `nrc_Submission` |
| `name` | TEXT | `"{Type} {DocumentID} returned to {Submitter} at {ts}."` — source `nrc_Name` (Performance Indicator and Enterprise Risk interpolate the record title — `nrc_indicatorid` / `nrc_riskid` — not the Document ID) |
| `status_reason` | `wf_rejection_status` | default `pending_changes` |

### 9.4 `wf_approval_queue`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `nrc_approvalqueueid` |
| `name` | TEXT | yes | ≤ 100 | `nrc_name` |
| `regarding_record_type` | `ref_record_type` + evidence types | no | | polymorphic `nrc_regarding_entry` |
| `regarding_record_id` | TEXT (uuid) | no | | |
| `order_no` | INTEGER | no | ≥ 1 | `nrc_order` |
| `approval_role` | `ref_approval_role` | yes | | `nrc_role` |
| `user_id` | TEXT (uuid) → `core_app_user` | yes | | `nrc_user` |
| `parallel` | INTEGER (0/1) | yes | default false | `nrc_parallel` |
| `alternate` | INTEGER (0/1) | yes | default false | `nrc_alternate` |
| `valid` | TEXT | yes | ≤ 100 | `nrc_valid` |
| `location_record_type` / `location_record_id` | | yes | second polymorphic pointer — see the enumeration below | `tei_location_lu` |
| `status_reason` | `wf_approval_queue_status` | no | default `pending` | |

`location_record_type` is a **narrower** polymorphic set than `regarding_record_type`. Where
`regarding_record_type` accepts all 10 approvable types (Document 1 §6.8), `location_record_type`
accepts exactly **5**:

| Value | Target table | Legacy target entity | Legacy relationship |
|---|---|---|---|
| `accomplishment` | `perf_accomplishment` | `nrc_Accomplishment` | `nrc_regarding_accomplishment` |
| `pi_result` | `perf_pi_result` | `nrc_PerformanceIndicatorFiscalYear` | `nrc_regarding_pi` |
| `positive_change_management` | `perf_positive_change_management` | `nrc_PositiveChangeManagement` | `nrc_regarding_poschangemngmt` |
| `priority` | `perf_priority` | `nrc_PrioritiesUpdate` | `nrc_regarding_priority` |
| `risk_update` | `perf_risk_update` | `nrc_RiskUpdate` | `nrc_regarding_risk` |

A `CHECK` constraint must restrict `location_record_type` to these five values; do **not** reuse the
`regarding_record_type` domain.

Unique constraint: `(regarding_record_type, regarding_record_id, order_no)` when not parallel.

### 9.5 `core_task`

| Column | Type | Null | Constraint | Source |
|---|---|---|---|---|
| `id` | TEXT (uuid) | no | PK | `activityid` |
| `subject` | TEXT | no | | `subject` — e.g. `"Risk Update(s) waiting for your approval."` |
| `description` | TEXT | yes | | `"{Type}(s) sent from {Submitter}: {doc ids}."` |
| `owner_user_id` / `owner_team_id` | TEXT (uuid) | yes | | task recipient |
| `action_type` | `ref_workflow_action_type` | yes | | `nrc_actiontype` |
| `submitted_record_type` | `ref_record_type` | yes | | `nrc_submittedrecordstype` |
| `regarding_approval_submission` | INTEGER (0/1) | no | default false | `nrc_regardingapprovalsubmission` — flipping to true fires the notifier |
| `due_date` | TEXT (UTC timestamp) | yes | | |
| `state` | `core_task_state` | no | default `open` | `statecode` — three-valued, **not** `core_record_state` (§2.3) |
| `status_reason` | `core_task_status` | no | default `not_started` | |

### 9.6 `wf_notification` **[NEW]**

Replaces the Power Automate + Teams plumbing with an auditable outbox.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (uuid) | PK |
| `task_id` | TEXT (uuid) → `core_task` | |
| `channel` | TEXT enum `in_app` · `email` · `teams` | |
| `recipient_user_id` | TEXT (uuid) → `core_app_user` | |
| `subject`, `body` | TEXT | |
| `deep_link` | TEXT | the route derived from record type × action type |
| `queued_on`, `sent_on` | TEXT (UTC timestamp) | |
| `delivery_status` | TEXT enum `queued` · `sent` · `failed` | |
| `error_detail` | TEXT | |

### 9.7 `wf_field_audit` **[NEW]**

Replaces Dataverse attribute auditing (which is enabled on every table and column today).

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | PK — `INTEGER PRIMARY KEY AUTOINCREMENT`: an alias of the rowid, assigned by SQLite, monotonic and never reused, so audit order survives deletions |
| `table_name`, `record_id` | TEXT / TEXT (uuid) | |
| `column_name` | TEXT | |
| `old_value`, `new_value` | TEXT (JSON) | |
| `operation` | TEXT enum `insert` · `update` · `delete` · `state_change` · `assign` | |
| `changed_by_id` | TEXT (uuid) → `core_app_user` | |
| `changed_on` | TEXT (UTC timestamp) | |
| `correlation_id` | TEXT (uuid) | groups a bulk command's changes |

Index on `(table_name, record_id, changed_on DESC)`, and on `(changed_on)` for Audit Search's date
range. SQLite has no table partitioning, so the monthly partitions of earlier editions become an
**archive**: once a month the `maintain_database` job (Document 3 §7.1) moves rows older than the
retention window (setting `audit.retention_months`) into a year file attached as `audit_<yyyy>` (`audit_2026.db`) inside one
transaction, and Audit Search attaches the year files a query's date range reaches. The live table
stays small enough that the record-level audit panel never scans history.

### 9.8 `wf_workflow_transition` **[NEW]**

A denormalised, queryable history of every lifecycle transition — what the dashboards and the
"My To-do" screens need without joining three audit tables.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (uuid) | PK |
| `record_type`, `record_id` | TEXT enum / TEXT (uuid) | |
| `from_state`, `from_status`, `to_state`, `to_status` | TEXT | |
| `action` | TEXT enum `submit` · `approve` · `return` · `propose_discontinue` · `discontinue` · `deny_discontinue` · `reopen` · `flag_carryover` · `unflag_carryover` | |
| `actor_user_id`, `actor_team_id` | TEXT (uuid) | |
| `from_owner_user_id` / `from_owner_team_id`, `to_owner_user_id` / `to_owner_team_id` | TEXT (uuid) | ownership transfer |
| `comment` | TEXT | the approver's comment at the time of the transition |
| `submission_id`, `approval_id`, `rejection_id` | TEXT (uuid) | |
| `occurred_on` | TEXT (UTC timestamp) | |

### 9.9 `core_note` / `core_file_attachment`

| `core_note` | Type |
|---|---|
| `id` | TEXT (uuid) PK |
| `regarding_table`, `regarding_id` | TEXT / TEXT (uuid) |
| `subject`, `body` | TEXT |
| `file_attachment_id` | TEXT (uuid) → `core_file_attachment` |

| `core_file_attachment` | Type |
|---|---|
| `id` | TEXT (uuid) PK |
| `file_name`, `mime_type` | TEXT |
| `size_bytes` | INTEGER (≤ 32 MB for deliverables) |
| `storage_key` | TEXT (object-store key — the file itself is never a `BLOB` in the database) |
| `uploaded_by_id`, `uploaded_on` | TEXT (uuid) / TEXT (UTC timestamp) |

---

## 10. Junction (many-to-many) tables — all 61

Every junction table has the shape
`(<left>_id TEXT NOT NULL, <right>_id TEXT NOT NULL, PRIMARY KEY (<left>_id, <right>_id)) STRICT, WITHOUT ROWID`
plus `created_on TEXT` (UTC timestamp) and `created_by_id TEXT` (uuid). Foreign keys use `ON DELETE CASCADE`.
Because the primary key leads with `<left>_id`, each junction also carries an index on
`(<right>_id, <left>_id)` so it can be walked from either end.

### 10.1 Contributing Business Lines (8)

| Target table | Legacy relationship | Used on the form as |
|---|---|---|
| `perf_accomplishment_business_line` | `nrc_Accomplishment_nrc_BusinessLine` | Contributing Business Lines |
| `plan_definition_business_line` | `nrc_Definition_nrc_BusinessLine` | Business Lines |
| `perf_enterprise_risk_business_line` | `nrc_EnterpriseRisk_nrc_BusinessLine` | Contributing Business Lines |
| `perf_performance_indicator_business_line` | `nrc_PerformanceIndicator_nrc_BusinessLine` | Contributing Business Lines |
| `perf_pi_result_business_line` | `nrc_buslin_piu` | Contributing Business Lines |
| `perf_pcm_business_line` | `nrc_PositiveChangeManagement_nrc_BusinessLine` | Contributing Business Lines |
| `perf_priority_business_line` | `nrc_PrioritiesUpdate_nrc_BusinessLine` | Contributing Business Lines |
| `perf_risk_update_business_line` | `nrc_RiskUpdate_nrc_BusinessLine` | Other Contributing Business Lines |

### 10.2 Contributing Product Lines (9)

| Target table | Legacy relationship | Used on the form as |
|---|---|---|
| `ref_business_line_product_line` | `cr9de_nrc_ProductLine_nrc_BusinessLine` | BL ↔ PL master relationship |
| `perf_accomplishment_product_line` | `nrc_Accomplishment_nrc_ProductLine` | Contributing Product Lines |
| `plan_definition_product_line` | `nrc_Definition_nrc_ProductLine` | Product Lines |
| `perf_enterprise_risk_product_line` | `nrc_EnterpriseRisk_nrc_ProductLine` | Contributing Product Lines |
| `perf_performance_indicator_product_line` | `nrc_PerformanceIndicator_nrc_ProductLine` | Contributing Product Lines |
| `perf_pi_result_product_line` | `nrc_prodline_pi` | Contributing Product Lines |
| `perf_pcm_product_line` | `nrc_PositiveChangeManagement_nrc_ProductLine` | Contributing Product Lines |
| `perf_priority_product_line` | `nrc_PrioritiesUpdate_nrc_ProductLine` | Contributing Product Lines |
| `perf_risk_update_product_line` | `nrc_RiskUpdate_nrc_ProductLine` | Other Contributing Product Lines |

### 10.3 Contributing Offices (10)

| Target table | Legacy relationship | Used on the form as |
|---|---|---|
| `ref_office_division` | `nrc_Office_nrc_Division` | Divisions of an Office |
| `plan_goal_office` | `nrc_Office_nrc_Goal` | Office ↔ Goal |
| `perf_accomplishment_office` | `nrc_Accomplishment_nrc_Office` | Contributing Offices |
| `perf_action_measure_office` | `nrc_ActionMeasure_nrc_Office` | Leading Offices/Officials |
| `perf_enterprise_risk_office` | `nrc_EnterpriseRisk_nrc_Office` | Contributing Offices |
| `perf_performance_indicator_office` | `nrc_PerformanceIndicator_nrc_Office` | Contributing Offices |
| `perf_pi_result_office` | `nrc_PerformanceIndicatorFiscalYear_nrc_Office` | Contributing Offices |
| `perf_pcm_office` | `nrc_Office_nrc_PositiveChangeManagement` | Contributing Offices |
| `perf_priority_office` | `nrc_Office_nrc_PrioritiesUpdate` | Contributing Offices |
| `perf_risk_update_office` | `nrc_RiskUpdate_nrc_Office` | Contributing Offices |

### 10.4 Contributing Major Programs (7)

| Column 1 | Column 2 |
|---|---|
| `perf_accomplishment_major_program` | `nrc_Accomplishment_nrc_MajorPrograms` |
| `perf_enterprise_risk_major_program` | `nrc_EnterpriseRisk_nrc_MajorPrograms` |
| `perf_performance_indicator_major_program` | `nrc_PerformanceIndicator_nrc_MajorPrograms` |
| `perf_pi_result_major_program` | `nrc_majprog` |
| `perf_pcm_major_program` | `nrc_PositiveChangeManagement_nrc_MajorPrograms` |
| `perf_priority_major_program` | `nrc_PrioritiesUpdate_nrc_MajorPrograms` |
| `perf_risk_update_major_program` | `nrc_RiskUpdate_nrc_MajorPrograms` |

### 10.5 Other Contributing Programs & Activities (7)

| Column 1 | Column 2 |
|---|---|
| `perf_accomplishment_contributing_program` | `nrc_Accomplishment_nrc_ContributingProgramsandActivities` |
| `perf_enterprise_risk_contributing_program` | `nrc_EnterpriseRisk_nrc_ContributingProgramsandActivities` |
| `perf_performance_indicator_contributing_program` | `nrc_PerformanceIndicator_nrc_ContributingProgramsandActivities` |
| `perf_pi_result_contributing_program` | `nrc_Performanccon` |
| `perf_pcm_contributing_program` | `nrc_PositiveChangeManagement_nrc_ContributingProgramsandActivities` |
| `perf_priority_contributing_program` | `nrc_PrioritiesUpdate_nrc_ContributingProgramsandActivities` |
| `perf_risk_update_contributing_program` | `nrc_RiskUpdate_nrc_ContributingProgramsandActivities` |

### 10.6 Applicable Fiscal Years (4)

| Target table | Legacy relationship | Used on the form as |
|---|---|---|
| `perf_enterprise_risk_fiscal_year` | `nrc_EnterpriseRisk_nrc_FiscalYear` | Applicable Fiscal Years |
| `plan_goal_fiscal_year` | `nrc_Goal_nrc_FiscalYear` | Applicable Fiscal Years |
| `plan_objective_fiscal_year` | `nrc_Objective_nrc_FiscalYear` | Applicable Fiscal Years |
| `plan_strategy_fiscal_year` | `nrc_Strategy_nrc_FiscalYear` | Applicable Fiscal Years |

### 10.7 Strategic-Plan cross links (6)

| Target table | Legacy relationship | Used on the form as |
|---|---|---|
| `plan_performance_indicator_goal` | `nrc_PerformanceIndicator_nrc_Goal` | additional Goals on a PI |
| `plan_performance_indicator_objective` | `nrc_PerformanceIndicator_nrc_Objective` | additional Objectives on a PI |
| `plan_performance_indicator_strategy` | `nrc_PerformanceIndicator_nrc_Strategy` | additional Strategies on a PI |
| `plan_external_factor_objective` | `nrc_ExternalFactor_nrc_Objective` | Objectives affected |
| `plan_external_factor_strategy` | `nrc_ExternalFactor_nrc_Strategy` | Strategies affected |
| `perf_enterprise_risk_strategy` | `nrc_EnterpriseRisk_nrc_Strategy` | Strategies impacted |

### 10.8 Related Performance Indicators (6)

| Target table | Legacy relationship | Used on the form as |
|---|---|---|
| `perf_accomplishment_performance_indicator` | `nrc_Accomplishment_nrc_PerformanceIndicator` | Other Related Performance Indicators |
| `perf_enterprise_risk_performance_indicator` | `nrc_EnterpriseRisk_nrc_PerformanceIndicator` | Related Performance Indicators |
| `perf_priority_performance_indicator` | `nrc_PerformanceIndicator_nrc_PrioritiesUpdate` | Related Performance Indicators |
| `perf_risk_update_performance_indicator` | `nrc_RiskUpdate_nrc_PerformanceIndicator` | Related Performance Indicators |
| `perf_pi_result_performance_indicator_a` | `nrc_manypis` | secondary PI links on a result |
| `perf_pi_result_performance_indicator_b` | `nrc_manyupdates` | reverse secondary link |

### 10.9 Products (2)

| Column 1 | Column 2 |
|---|---|
| `evidence_evaluation_product` | `nrc_Evaluations_nrc_Product` |
| `evidence_research_activity_product` | `nrc_Publications_prods_EvBuildAct` |

### 10.10 Users (2)

| Target table | Legacy relationship | Used on the form as |
|---|---|---|
| `perf_pcm_division_owner` | `nrc_SystemUser_nrc_PositiveChangeManagement` | Division Owner(s) |
| `perf_pi_result_revision_history` | `nrc_revisionhistory` | users who touched a PI Result |

> **Total:** sections 10.1–10.10 list exactly **61** junction tables — the full set of many-to-many
> relationships in the source solution (8 + 9 + 10 + 7 + 7 + 4 + 6 + 6 + 2 + 2). Section 10.11 below
> adds four further junctions that are **[NEW]** in this design; they replace legacy multi-select
> columns and have no many-to-many relationship in the source.

### 10.11 Multi-select choice junctions **[NEW — replaces delimited multi-select columns]**

| Table | Replaces |
|---|---|
| `perf_pi_result_quarter` | `nrc_PerformanceIndicatorFiscalYear.nrc_quarters` |
| `perf_accomplishment_quarter` | `nrc_Accomplishment.nrc_quarters` |
| `perf_priority_quarter` | `nrc_PrioritiesUpdate.nrc_quarter` |
| `plan_definition_data_source` | `nrc_Definition.nrc_datasource` |

---

## 11. Configuration tables

### 11.1 `core_app_setting` **[NEW]**

Replaces the 43 Dataverse environment variables.

| Column | Type | Notes |
|---|---|---|
| `key` | TEXT PK | e.g. `approver.qpr.default_team_id`, `links.user_guide`, `links.faq` |
| `value` | TEXT | |
| `value_type` | TEXT enum `string` · `uuid` · `url` · `json` · `bool` · `int` | |
| `description` | TEXT | |
| `is_secret` | INTEGER (0/1) | |
| `modified_on`, `modified_by_id` | | |

Seed keys derived from the source environment variables: the default approver team, both app home
links, the two module links, the user-guide and FAQ document links, the environment name.
The 21 "pending my approval / finalized / my drafts" deep links become **client-side routes**, not
settings.

### 11.2 `core_view_definition` **[NEW]**

Persists the 334 saved views (190 of them business views: 154 public list views + 36 "My …" filter views) so the list-view picker is data-driven rather than hard-coded.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (uuid) PK | |
| `entity_name` | TEXT | |
| `name` | TEXT | e.g. `MY Risk Updates in Draft/Revision` |
| `view_type` | TEXT enum `public` · `personal` · `lookup` · `associated` · `advanced_find` · `quick_find` | |
| `is_default` | INTEGER (0/1) | |
| `filter_definition` | TEXT (JSON) | the translated FetchXML predicate |
| `column_definition` | TEXT (JSON) | ordered column list with widths |
| `sort_definition` | TEXT (JSON) | |
| `owner_user_id` | TEXT (uuid) | null for public views |

### 11.3 `core_form_definition` **[NEW]**

Persists the form layouts (41 target screens; see Document 3 §20 for how the 115 source forms reduce
to them) as tabs → sections → fields/sub-grids/quick-views, so the React form renderer is
metadata-driven.

| Column | Type |
|---|---|
| `id` | TEXT (uuid) PK |
| `entity_name` | TEXT |
| `name` | TEXT |
| `form_type` | TEXT enum `main` · `quick_create` · `quick_view` · `card` |
| `is_default` | INTEGER (0/1) |
| `layout` | TEXT (JSON) (tabs → sections → cells) |

---

## 12. Constraints, indexes and integrity rules

### 12.1 Unique constraints

| Table | Constraint |
|---|---|
| `perf_performance_indicator` | unique `indicator_code` |
| `perf_enterprise_risk` | unique `risk_code` |
| `perf_accomplishment` | unique `accomplishment_code` |
| `perf_positive_change_management` | unique `pcm_code` |
| `perf_priority` | unique `update_code` |
| `plan_definition` | unique `identification_number` |
| `ref_fiscal_year` | unique `fiscal_year` |
| `ref_office` | unique (`office` `COLLATE NOCASE`); unique (`code` `COLLATE NOCASE`) |
| `ref_business_line` / `ref_product_line` | unique (`name` `COLLATE NOCASE`); unique `prefix_code` |
| `core_app_user` | unique (`domain_name` `COLLATE NOCASE`); unique `azure_object_id` |
| `core_team` | unique (`name` `COLLATE NOCASE`) |
| `perf_risk_update` | unique `(enterprise_risk_id, fiscal_year_id, quarter)` |
| `perf_pi_result_period` | PK `(pi_result_id, period)` |
| all junction tables | PK on the pair |

A SQLite unique index admits any number of `NULL`s, so the nullable codes above need no
`WHERE … IS NOT NULL` clause to stay optional.

### 12.2 Check constraints

SQLite `CHECK` constraints may not contain subqueries, so a rule that reads another row (the parent
PI's `measure_type`, a status→state map) is either generated inline from the enumerations of §2 or
enforced by a trigger, as marked. Booleans compare against `1` / `0` (§1).

| Rule | Where |
|---|---|
| Exactly one of `owner_user_id` / `owner_team_id` | every ownable table |
| Exactly one of `submitter_user_id` / `submitter_team_id`, or both null | every workflow-enabled table |
| Exactly one typed FK on `wf_submission` / `wf_approval` / `wf_rejection`, matching `record_type` | workflow tables |
| At most one of `answer_evaluation_id` / `answer_research_activity_id` | `evidence_priority_question` |
| At most one of `contributing_bl_id` / `contributing_pl_id` | `perf_risk_update` |
| `previous_pi_id IS NOT NULL` when `change_type = 'revised'` | `perf_performance_indicator` |
| `other_data_source` may only be non-empty when `data_source = 'other'` | `perf_performance_indicator` |
| `act_proposed_response_qpr_description IS NOT NULL` when `risk_accepted = 0` | `perf_risk_update` |
| `results IS NULL` when `not_applicable = 1` | `perf_pi_result_period` |
| Range fields null unless the parent PI's `measure_type = 'range'`; target/operator null when it is | `perf_pi_result_period` (trigger) |
| `rank BETWEEN 1 AND 11` | `perf_priority` |
| `order_no >= 1` | `wf_approval_queue` |
| `length(col) <= n` for every documented character limit | all text columns |
| `state`/`status_reason` pair must be a legal combination | all tables — a `CHECK` generated from §2.4, e.g. `(state = 'active' AND status_reason IN ('draft','pending_approval','revision')) OR (state = 'inactive' AND status_reason IN ('finalized','cancelled_closed'))` |

### 12.3 Referential-integrity triggers (the Strategic Plan hierarchy)

| Trigger | Rule |
|---|---|
| `plan_objective` before insert/update | `objective.sequence` must start with the parent goal's sequence (`CAST(goal.sequence AS TEXT)`) followed by `.` |
| `plan_strategy` before insert/update | `strategy.sequence` must start with the parent objective's `sequence` followed by `.` |
| `perf_performance_indicator` | `objective_id`'s goal must equal `goal_id`; `strategy_id`'s objective must equal `objective_id` |
| `perf_enterprise_risk` | `impacted_objective_id`'s goal must equal `impacted_goal_id`; `strategy_id`'s objective must equal `impacted_objective_id` |
| `perf_accomplishment`, `perf_priority`, `perf_positive_change_management` | same goal→objective→strategy consistency |

In the source these are client-side warnings; the rebuild should enforce them server-side and surface
the same messages (Document 1 §8.3).

Each is a pair of SQLite triggers (`BEFORE INSERT`, and `BEFORE UPDATE OF` the columns involved) that
aborts the statement with the Document 3 §10 code as the message prefix, so the API can map it to
`HIERARCHY_MISMATCH` without parsing prose:

```sql
CREATE TRIGGER plan_strategy_sequence_ins
BEFORE INSERT ON plan_strategy
WHEN NEW.objective_id IS NOT NULL AND NEW.sequence IS NOT NULL
 AND NOT EXISTS (SELECT 1 FROM plan_objective o
                 WHERE o.id = NEW.objective_id
                   AND substr(NEW.sequence, 1, length(o.sequence) + 1) = o.sequence || '.')
BEGIN
  SELECT RAISE(ABORT, 'HIERARCHY_MISMATCH: This Strategy does not fall under the Objective selected above.');
END;
```

The prefix test includes the dot: a bare `starts with` would accept strategy `1.11.1` under objective
`1.1`. The API runs the same checks before writing so that it can report every failing field at once;
the triggers are the guarantee that no other path — an import, a fix script — writes an inconsistent
hierarchy.

### 12.4 Indexes

| Purpose | Index |
|---|---|
| List views by state | `(state, status_reason)` on every business table |
| "My …" views | `(owner_user_id, status_reason)` and `(owner_team_id, status_reason)` |
| Row visibility (§13.2) | `(owning_business_unit_id)` on every ownable table |
| "My Office's …" views | `(office_id, status_reason)` on each performance table |
| Quarterly filtering | `(fiscal_year_id, quarter)` on Risk Update, PCM; `(fiscal_year_id)` on PI Result, Accomplishment, Priority |
| Parent navigation | `(performance_indicator_id)` on PI Result; `(enterprise_risk_id)` on Risk Update |
| Revision chain | `(previous_pi_id)` on Performance Indicator |
| Carry-over review | partial index on `performance_indicator (review_for_carry_over) WHERE review_for_carry_over` |
| Workflow scanning | partial index `wf_submission (task_made, state) WHERE task_made = 0 AND state = 'active'`; same on approval and rejection. SQLite uses a partial index only when the query repeats its `WHERE` terms literally, so the job's query is written to match |
| Task closure job | `core_task (regarding_approval_submission, status_reason) WHERE regarding_approval_submission` |
| Identifier generation | unique indexes listed in §12.1 |
| Full-text search | An **FTS5** virtual table per searchable table (replaces Quick Find): `CREATE VIRTUAL TABLE perf_risk_update_fts USING fts5(title, description_plain, content='perf_risk_update', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2')`, an external-content index kept in step by `AFTER INSERT / UPDATE / DELETE` triggers on the base table. `?q=` becomes a `MATCH` with each term quoted and suffixed `*` for prefix search, ranked by `bm25()` |
| Audit | `wf_field_audit (table_name, record_id, changed_on DESC)` and `(changed_on)`; history beyond the retention window is archived to yearly attached files (§9.7) |
| Reporting | covering indexes on the analytic views' driving columns; `ANALYZE` is run by `PRAGMA optimize` (§1.2) so the planner has statistics for them |

### 12.5 Counter-based identifier generation **[NEW — replaces the loop-and-retry algorithm]**

SQLite has no sequences. Every generated identifier draws from one counter table,
`core_id_counter (scope_key TEXT PRIMARY KEY, next_value INTEGER NOT NULL) STRICT`.

| Table | Mechanism |
|---|---|
| `perf_performance_indicator` | `core_id_counter` row scoped by `"{bl_prefix}-{office_code}"` |
| `perf_enterprise_risk` | same, scoped by `"{bl_prefix}-{office_code}"` |
| `perf_accomplishment` | scope `"ACC-{office_code}"` |
| `perf_positive_change_management` | scope `"PCM-{office_code}"` |
| `perf_priority` | scope `"{bl_prefix}-{office_code}"` |
| `plan_definition` | the single scope `"NRC"`, formatted `NRC-0000` (`printf('NRC-%04d', n)`) |

The draw happens inside the record's own insert transaction, which the API opens with
`BEGIN IMMEDIATE` (§1.2):

```sql
INSERT INTO core_id_counter (scope_key, next_value) VALUES (:scope, 1)
ON CONFLICT (scope_key) DO UPDATE SET next_value = next_value + 1
RETURNING next_value;
```

Because SQLite admits one writer at a time and the transaction holds the write lock from its first
statement, two creates in the same scope cannot draw the same number; and because the counter and the
record commit or roll back together, a failed save leaves no gap. This removes the race condition and
the 60-iteration / 1-hour timeout in the legacy flows (Document 1 §8.1 note). On migration, each
scope's counter is seeded with the highest number already issued in it.

---

## 13. Row-visibility model (enforced by the API)

The legacy system relies on Dataverse's ownership + privilege-depth engine. **SQLite has no
row-level security, no database roles and no session variables**, so the same model is enforced in
the API's data-access layer instead of by the database. The predicates are the same ones a
PostgreSQL edition would install as policies; what differs is who guarantees they are applied.

This is a weaker guarantee and is stated as one: the database will serve any row to any code that
holds a connection. It is made safe by construction and by test:

- **One gateway.** Business tables are read and written only through the repository layer, which
  composes every `SELECT`, `UPDATE` and `DELETE` from the entity's base query plus the §13.2
  predicate. No route handler builds SQL against a business table; raw connections are confined to
  the migration, maintenance and fix scripts.
- **Fail closed.** The predicate is built from the request context below, and a request without one
  — no signed-in user, a background job that forgot to declare its identity — resolves every depth
  to *(none)*, so the predicate is `0` and the query returns nothing rather than everything.
- **Tested both ways.** The suite asserts, per entity and per depth, that a user sees exactly the rows
  the §4.3 matrix of Document 1 allows and that a forged id outside them is `404 NOT_FOUND`; and a
  static check fails the build if any module outside the repository layer names a business table in
  SQL.

### 13.1 Request context

The API resolves, once per request, and holds in a context variable for the request's lifetime:

| Value | Meaning |
|---|---|
| `current_user_id` | the signed-in user |
| `current_business_unit_id` | their business unit |
| `current_team_ids` | JSON array of the team ids they belong to |
| `current_business_unit_subtree` | JSON array of the business-unit ids in their parent-child subtree |
| `privilege_depths` | map `{entity: {operation: depth}}` resolved from their roles |

The values reach SQL as **bound parameters** (`:current_user_id`, and the two arrays as JSON text
expanded with `json_each`), never by string formatting. Pooled connections carry no per-request
state, so nothing set for one request can leak into the next — the reason a per-connection `TEMP`
table or a registered SQL function is *not* used to emulate PostgreSQL's session settings.

### 13.2 Predicate template (applied per table, per operation)

A record is visible/editable when the resolved depth for `(entity, operation)` is:

| Depth | Predicate appended to the statement's `WHERE` |
|---|---|
| `organization` | `1` (always true) |
| `parent_child_business_unit` | `owning_business_unit_id IN (SELECT value FROM json_each(:current_business_unit_subtree))` |
| `business_unit` | `owning_business_unit_id = :current_business_unit_id` |
| `user` | `owner_user_id = :current_user_id OR owner_team_id IN (SELECT value FROM json_each(:current_team_ids))` |
| *(none)* | `0` (always false) |

The `(owning_business_unit_id)`, `(owner_user_id, status_reason)` and `(owner_team_id, status_reason)`
indexes of §12.4 serve these predicates.

### 13.3 Additional application-level guards (state rules beyond row visibility)

| Guard | Rule | Source |
|---|---|---|
| **Edit lock** | Update is refused unless `status_reason IN ('draft','revision')`, except for EDO users | User Guide; SAD |
| **Delete lock** | Delete is refused unless `status_reason = 'draft'` **and** the caller owns the record | SAD |
| **Restricted creation** | A non-EDO user may not create/save a Performance Indicator whose `report_level` is the restricted value or whose `agency_wide_support_level = 'agency'`. Message: *"You do not have the necessary priviledges to create this record with this field value."* (misspelling of "privileges" is verbatim from the source.) The roles document states the identical restriction for **Enterprise Risk** (*"Enter and modify new Enterprise Risk entries for non Agency Wide and CBJ type risks"*); the shipped solution registers `nrc_preventSave` on the Performance Indicator form only **and that handler carries `enabled="false"`** — so as shipped this restriction is enforced nowhere, on either entity. Treat it as a requirement to implement server-side, not as behaviour to preserve, and decide whether it extends to Enterprise Risk — Document 1 §17.3. | `nrc_preventSave`; Roles document |
| **Approve/Return guard** | Only the current owner (approver) of a record in `pending_approval` may approve or return it | flows |
| **Submit guard** | Only the owner of a record in `draft` or `revision` may submit it | flows + view filters |
| **Discontinue guard** | Only EDO-role users may discontinue or deny discontinuance | `nrc_ERButtonRules`, `nrc_PIButtonRules` |
| **Re-open guard** | Only EDO-role users may re-open PI Results, and only for the current fiscal year | `nrc_PIRButtonRules` + flow |
| **Approver cannot be the creator** | *"Approve/Disapprove plan results entries (cannot be creator of the entry)"* | Roles document |

### 13.4 Business-unit assignment rule

Seven business rules implement this — one each on **Accomplishment, Enterprise Risk, Performance
Indicator, PI Result, Positive Change Management, Priority and Risk Update**. All seven have the
same two-branch shape, and the branch condition is the record's **status**, not its report level:

| Branch | Condition | `owning_business_unit_id` is set to |
|---|---|---|
| Then | `status_reason = pending_approval` | the **EDO** business unit (source GUID `d5cffd5e-24a1-ef11-8a6b-001dd8308619`) |
| Else | any other status (unconditional) | the **root / agency-wide** business unit (`3188eccf-3436-ed11-9daf-001dd803db14`, org `orgaae2a570`) |

The legacy `statuscode` compared against differs per entity because each lifecycle numbers its own
options: **875670001** on Performance Indicator, Enterprise Risk and PI Result; **875670002** on
Accomplishment, Positive Change Management, Priority and Risk Update. In every case that value is
`pending_approval` in the corresponding enumeration (§2.4).

This is therefore a **status-driven ownership transfer**, not a report-level classification: a record
moves into the EDO business unit for the duration of its approval and returns to the agency-wide
business unit once it leaves `pending_approval`. Because `owning_business_unit_id` is the operand of
the `business_unit` and `parent_child_business_unit` row-visibility predicates in §13.2, this
rule *is* the mechanism that makes a submitted record visible to its approver. Implement it as part
of the submit / approve / return transition (Document 1 §6.3–§6.5), not as a field-derivation rule.

> **Earlier revisions of this section described the condition as `report_level` being CBJ/APPR or
> Business Line/Product Line. That was wrong** — none of the seven rules reads `nrc_reportlevel` at
> all. Verified: each `Workflows/BusinessUnit-*.xaml` (plus
> `Workflows/Newbusinessrule-44E3C561-…xaml` for PI Result) contains exactly one
> `GetEntityProperty Attribute="statuscode"` and one
> `OptionSetValue, "8756700…", "Status"` comparison, and zero references to `nrc_reportlevel`.

---

## 14. Analytic views for the dashboards

These views replace the Power BI semantic model (Document 1 §9). They are ordinary SQLite views in
the main database file, named with the `analytics_` prefix, and are the data source for the dashboard
endpoints in Document 3 §6. Within a row of the tables below, the names after the first are written
without the `analytics_` prefix they all carry.

SQLite has no materialised views and no stored functions. The views are therefore **live** — a
dashboard reads the operational rows as they stand, which is what lets the rail say *live* rather than
print a refresh time (Document 4). Where a page proves too slow over plain views, the
`refresh_analytics` job (Document 3 §7.1) rebuilds a summary table `analytics_<view>_snapshot` with
`DELETE` + `INSERT … SELECT` in one transaction, so a reader sees either the old snapshot or the new
one and never a half-built one; the endpoint reads the snapshot and reports its `refreshed_on`.
Logic that PostgreSQL would hold in a function is a view (one row where a scalar is wanted) or lives
in the Python analytics service.

> **Model-wide record filter.** Before any page filter is applied, the legacy semantic model drops
> every closed record: the Power Query for Enterprise Risk filters `Stage <> "Closed/cancelled"`, and
> those for Performance Indicator, PI Result, Positive Change Management, Priorities, Risk Update and
> Accomplishment filter `Stage <> "Closed"`. Each query first normalises the status label —
> "Cancelled/closed" → `Closed`, and "Pending approval" / "Pending intermediate approval" /
> "Pending final approval" → `Pending` — so the `Stage` dimension has exactly five values:
> Closed · Draft · Revision · Finalized · Pending. Every view in this section must therefore carry
> `WHERE status_reason NOT IN ('closed','cancelled_closed','closed_cancelled')`; serving the
> dashboards straight from the operational tables without that filter will change every count on
> Document 1 §9.3 pages 1–18.

### 14.1 Dimension views

| View | Contents |
|---|---|
| `analytics_dim_reporting_period` | One row per (fiscal year, quarter) including `Annual`; columns `fiscal_year`, `quarter`, `reporting_period_label` (`"FY24 Q3"`), `sort_order`, `is_annual` |
| `analytics_dim_date` | Standard calendar with federal fiscal-year attributes (FY starts 1 October) |
| `analytics_dim_office`, `dim_division`, `dim_business_line`, `dim_product_line`, `dim_product`, `dim_major_program`, `dim_contributing_program`, `dim_organization`, `dim_report_level` | Straight projections of the `ref_` tables |
| `analytics_dim_lead_office`, `dim_lead_business_line`, `dim_lead_product_line`, `dim_reporting_office`, `dim_primary_contributing_program` | Role-playing aliases (`dim_primary_contributing_program` backs the global Contributing Program slicer) |
| `analytics_dim_goal`, `dim_objective`, `dim_strategy` | Plan hierarchy with sequence, title and display name. `dim_goal` and `dim_objective` hold the strategic plan the dashboards report on — the one-row view `analytics_reporting_plan`, which the `dashboards.strategic_plan` setting names and, left empty, is the earliest plan **[NEW]** |
| `analytics_dim_plan_goal`, `dim_plan_objective`, `strategic_plan` | **[NEW]** Every plan's goals and objectives, and one row per plan keyed by the fiscal years it spans (`2022-2026`) — what the Strategic Planning home's plan switch reads |
| `analytics_dim_performance_indicator` | PI attributes plus `indicator_headline` |
| `analytics_dim_enterprise_risk` | Risk attributes plus `is_agencywide` — true when the risk's contributing-offices junction contains the Agencywide office (§14.5), **not** the lead office. Recompute on migration; the legacy flag is stale |
| `analytics_dim_user` | User display attributes |
| `analytics_dim_term` | Glossary terms from `plan_definition` — powers the hover-over definitions |

### 14.2 Fact views

| View | Grain | Key derived columns |
|---|---|---|
| `analytics_fact_pi_result` | one row per PI Result × period | `result_value`, `target`, `minimum_target`, `maximum_target`, `operator`, `reported_results`, **`result`** (`In Standard` · `Out of Standard` · `No data`), `success_likelihood`, `remarks` |
| `analytics_fact_risk_update` | **two rows per Risk Update** — one `mitigation_type = 'Inherent'`, one `'Residual'` | `likelihood_level` (1/2/3), `consequence_level`, `likelihood_text`, `consequence_text`, `risk_level` (`LL…HH`), `risk_index`, `x`, `y`, `risk_color`, `likelihood_left_side_color`, `likelihood_right_side_color`, `consequence_left_side_color`, `consequence_right_side_color`, `inherent_likelihood_left_side_color`, `inherent_likelihood_right_side_color`, `inherent_consequence_left_side_color`, `inherent_consequence_right_side_color`, `outlook_text`, `risk_owner`, `primary_column` (`"RISK {risk_code}: {risk_title}"`), `associated_pis` |
| `analytics_fact_accomplishment` | one row per (Accomplishment, quarter) — **including Annual**; see the as-built notes below | count measures, `report_level` |
| `analytics_fact_positive_change_management` | one row per PCM | `count` measure |
| `analytics_fact_priority` | one row per (Priority, quarter) — including Annual; the legacy model collapses Annual to Q4, see the as-built notes below | `goal_number` (1/2/3), `rank`, `description` |
| `analytics_fact_agency_wide_indicator` | PI Results whose indicator code **contains** `AW-` — the legacy calculated table tests `CONTAINSSTRING(indicator_id, "AW-")`, whereas the reciprocal exclusion on the PI dashboards (Document 1 §9.3 pages 2 and 16) tests `NOT StartsWith(indicator_id, 'AW')`. The two predicates are asymmetric: `NMSS-AW-01` would appear in the Agencywide matrix *and* in the ordinary PI dashboards, while `AWX-01` would appear in neither. **Rebuild:** carry an explicit `is_agencywide_indicator` flag on the indicator and use it for both halves | `indicator_code`, `performance_indicator` (= `"{indicator_code}: {title}"`), `result_value`, `operator`, `target`, `results` (the legacy **display string** `"{result_value} {operator} {target}"`, e.g. `95 >= 90` — the matrix aggregates it with a text MAX, so the rebuild should select the single value for that PI × office × period instead), `status` (In Standard · Out of Standard · No data — this is what colours the cell), `office` (reporting office), `product_line` (lead PL), `reporting_period` |

> **As-built divergence — Accomplishment quarters.** The legacy model does **not** expand the
> multi-select `nrc_quarters`: it applies four literal replacements (875670000 → Q1, 875670001 → Q2,
> 875670002 → Q3, 875670003 → Q4) and leaves 875670004 (**Annual**) unmapped, with no
> `Text.Split` / `ExpandListColumn` step (PI Result and Priorities both have one). A multi-quarter
> accomplishment therefore keeps a comma-joined string — the shipped extract contains
> `Quarter Value = "Q1,Q2,Q3,Q4,875670004"` and `Reporting Period = "FY18 Q1,Q2,Q3,Q4,875670004"`, a
> key that matches no row of the 55-row reporting-period dimension, so those accomplishments vanish
> from every period-filtered visual. Expanding the multi-select correctly (as specified above) is the
> right rebuild behaviour but will **not** reconcile to today's figures: a Q1–Q4 accomplishment will
> count in four periods instead of none.

> **As-built divergence — Priority quarters.** `Priorities[Quarter]` is a three-test IF whose bare
> `else` returns `Q4`, so option value 875670004 (**Annual**) — and any value added later — is
> relabelled `Q4` and `Reporting Period` becomes `"FY{yy} Q4"`. The single Priority in the shipped
> extract is exactly this case (`Quarters Values = 875670004` → `FY24 Q4`). Annual priorities are
> therefore counted as Q4 priorities on Document 1 §9.3 page 6's GOAL 1/2/3 cards, TOTAL COUNT and
> historical trend. Keep Annual as its own period in the rebuild and expect page-6 figures not to
> reconcile. Confirm with OEDO alongside Document 1 §17.3 item 11.

> **Label prefixes are part of the stored value.** On `fact_risk_update`, `consequence_text`,
> `likelihood_text`, `outlook_text`, `risk_owner` and `primary_column` each embed an upper-case label
> prefix in the value itself (`"INHERENT CONSEQUENCE: …"`, `"RESIDUAL LIKELIHOOD: …"`,
> `"OUTLOOK: …"`, `"RISK OWNER: …"`, `"RISK {risk_code}: …"`). The rebuild should store the bare value
> and apply the label in the UI.

### 14.3 Bridge views

`analytics_bridge_pi_contributing_office`, `bridge_pcm_contributing_office`,
`bridge_priority_contributing_office`, `bridge_risk_contributing_office`,
`bridge_risk_related_indicator` — direct projections of the junction tables.

### 14.4 Utility views

| View | Purpose |
|---|---|
| `analytics_refresh_status` | Last refresh (ET), next refresh — retained so the dashboard header behaves as users expect; in a live system it reports "live" |
| `analytics_view_toggle` | The (stage, toggle) bridge behind the View Toggle slicer — rows (Draft, All), (Pending, All), (Revision, All), (Finalized, All), (Finalized, Finalized): `all` shows records in any of the four stages, `finalized` restricts every visual to Finalized records |
| `analytics_dim_stage` | The five-value stage dimension (Closed · Draft · Revision · Finalized · Pending) that `analytics_view_toggle` joins to |
| `analytics_qpr_flag` | The `QPR?` helper dimension |

### 14.5 Derived-column definitions (recovered from the Power BI model)

These five were previously listed here as "to be confirmed with OEDO". **They no longer need
confirming.** The `.pbix` tabular model was decoded (Document 1 §17.2) and all 76 business-table
calculated-column definitions were read out, so the rules below are the as-built logic, not
inference. Each is stated as a specification, not as DAX; the recovered expressions are preserved
verbatim in the project scratch artefact `DAX_columns.txt` for byte-level comparison.

**1. `result` — In Standard / Out of Standard / No data.** Precedence matters:

| Order | Condition | Result |
|---|---|---|
| 1 | `not_applicable = true` | `No data` |
| 2 | `measure_type <> 'Range'` | compare `result_value` against `target` using the record's `operator`: one of `<`, `<=`, `=`, `N/A`, `>=`, `>` → `In Standard` when the comparison holds, else `Out of Standard`. `N/A` is treated **exactly as `=`**. |
| 3 | `measure_type = 'Range'` | `In Standard` only when **both** `lower_range_result` and `upper_range_result` are `In Standard`; otherwise `Out of Standard`. |

> **Two as-built behaviours the rebuild must decide about rather than copy blindly.**
> (a) There is **no Qualitative branch** — a Qualitative indicator falls through to the operator
> comparison in row 2, so its result depends on `result_value` vs `target` like any quantitative one.
> (b) The operator comparison has **no fallback**: if `operator` is null or any value outside the six
> listed, the expression returns **blank** — not `No data`, not `Out of Standard`. Blank renders as an
> empty cell on every dashboard that groups by result. Earlier revisions of this document implied
> `No data` covered these cases; it does not. Confirm the intended handling with OEDO and record the
> decision, because a `CASE … ELSE NULL` and a `CASE … ELSE 'No data'` produce visibly different
> dashboards.

**2. `risk_index` — the heat-map cell ordering.** A **text** value, not a number: a one-letter colour
prefix followed by a zero-based rank. Colour prefix is `R` for Red, `Y` for Yellow, `G` for anything
else. The rank is the row's `index` position within the set of Risk Updates sharing the **same
risk colour, the same reporting period and the same mitigation type**, restricted to
`psat = 'PSAT'`, minus one. So values look like `R0`, `Y3`, `G16`.

> Note the PSAT restriction: the rank denominator is PSAT rows only, even on the Non-PSAT and
> Agencywide dashboard pages. Whether that is intended or a defect is a question for OEDO.

**3. `x`, `y` — heat-map marker coordinates.** These are **not** a formula over the data; they are a
hand-authored placement lookup that spreads up to 12 markers inside one heat-map cell without
overlap. Given `n` (the number of markers in the cell, 1–12) and `i` (the marker's zero-based
position, 0–11), `x` is a fraction of the cell width `A` and `y` a fraction of the cell height `B`.
`n = 1` → centre (`A/2`, `B/2`); for `n = 2` and `3` the markers sit on one row at `B/2` spread across
`A/3`/`2A/3` and `A/4`/`A/2`/`3A/4`; from `n = 4` upward they arrange in two, three or four rows.
The complete 12 × 12 table is in the recovered expressions — reproduce it as a static lookup in the
React heat-map component, not as arithmetic.

**4. `indicator_headline`** = the Indicator ID, then a colon and a space, then the Title
(`"{indicator_id}: {title}"`).

**5. `reported_results`** = `0` when `not_applicable = true`, otherwise `1`. Summing it therefore
counts indicators that actually reported in the period.

**Supporting definitions recovered alongside them** (needed by the four risk dashboards):

| Column | Definition |
|---|---|
| `Risk Update.color` | `residual_likelihood_level + residual_consequence_level` when `mitigation_type = 'Residual'`, otherwise `inherent_consequence_level + inherent_likelihood_level` — a numeric sum of the two 1–3 levels |
| `Risk Update.risk_color` | `Yellow` when `color = 4`; `Green` when `color < 4`; `Red` otherwise |
| `Risk Update.risk_value` | `3` when `risk_level` ∈ {HH, HM, MH}; `2` when ∈ {LL, LM, ML}; `1` otherwise |
| `Risk Update.primary_column` | `"RISK {enterprise_risk.id}: {enterprise_risk.risk_title}"` |
| `Enterprise Risk.agencywide` | true when the risk's contributing-offices set contains one specific office — source GUID `4d4622ce-2958-ee11-be6e-001dd8098e36`. **Seed this office's identity explicitly**; the flag is not derived from any attribute of the office. |
| `Enterprise Risk.risk_owner` | resolved by lookup from the column the source labels `DEPRECATED Risk Lead Pointer` to the user's full name — see §16.1 |
| `Risk Update.*_right_side_color` / `*_left_side_color` | **right** = the current quarter's level → 3 Red / 2 Yellow / 1 Green. **left** = `last_quarter_*_level` under the same mapping, falling back to the right-side colour when the last-quarter level is null. Eight columns in all: likelihood and consequence × left and right × inherent and residual (the four unprefixed ones are the residual pair) |

---

## 15. Legacy-to-target migration mapping

### 15.1 Table mapping

| Dataverse entity | Target table |
|---|---|
| `nrc_FiscalYear` | `ref_fiscal_year` |
| `nrc_Office` | `ref_office` |
| `nrc_Division` | `ref_division` |
| `nrc_Organization` | `ref_organization` |
| `nrc_BusinessLine` | `ref_business_line` |
| `nrc_ProductLine` | `ref_product_line` |
| `nrc_Product` | `ref_product` |
| `nrc_MajorPrograms` | `ref_major_program` |
| `nrc_ContributingProgramsandActivities` | `ref_contributing_program` |
| `nrc_OfficeGoals` | `ref_office_goal` |
| `nrc_Goal` | `plan_goal` |
| `nrc_Objective` | `plan_objective` |
| `nrc_Strategy` | `plan_strategy` |
| `nrc_PerformanceGoal` | `plan_performance_goal` |
| `nrc_ExternalFactor` | `plan_external_factor` |
| `nrc_Definition` | `plan_definition` |
| `new_Signposts` | `plan_signpost` |
| `new_KeyAreas` | `plan_key_area` |
| `nrc_PerformanceIndicator` | `perf_performance_indicator` |
| `nrc_PerformanceIndicatorFiscalYear` | `perf_pi_result` + `perf_pi_result_period` + `perf_pi_result_quarter` |
| `nrc_PlannedMeasureMilestoneorDeliverable` | `perf_planned_measure` |
| `nrc_EnterpriseRisk` | `perf_enterprise_risk` |
| `nrc_RiskUpdate` | `perf_risk_update` |
| `nrc_Accomplishment` | `perf_accomplishment` + `perf_accomplishment_quarter` |
| `nrc_PrioritiesUpdate` | `perf_priority` + `perf_priority_quarter` |
| `nrc_Priorities` | `perf_priority_legacy` (archive only) |
| `nrc_PositiveChangeManagement` | `perf_positive_change_management` |
| `nrc_ActionMeasure` | `perf_action_measure` |
| `nrc_PriorityQuestion` | `evidence_priority_question` |
| `nrc_Evaluations` | `evidence_evaluation` |
| `nrc_OtherEvidenceBuildingActivity` | `evidence_research_activity` |
| `nrc_Submission` | `wf_submission` |
| `nrc_Approval` | `wf_approval` |
| `nrc_Rejection` | `wf_rejection` |
| `nrc_ApprovalQueue` | `wf_approval_queue` |
| `Task` | `core_task` |
| `SystemUser` | `core_app_user` |
| `Team` | `core_team` |
| `BusinessUnit` | `core_business_unit` |
| `Role` | `core_security_role` |
| `Annotation` | `core_note` |
| `nrc_pisubmissionapprovals` (BPF) | `wf_workflow_transition` (reconstructed) |

### 15.2 Original external sources (for a green-field load rather than a Dataverse copy)

See Document 1 §12 — SharePoint EPMS lists (PIs 3 552, Accomplishments 2 594, Risks 861, PCM 669,
Priorities 352) and `gid.nrc.gov/EA/*` for Evidence Building.

### 15.3 PI Result un-pivot map (all 55 legacy columns, explicit)

The 55 flat quarterly columns on `nrc_PerformanceIndicatorFiscalYear` become 5 rows in
`perf_pi_result_period` (one per period), 11 columns wide. Every legacy column name is spelled out
below — this is the single most error-prone step of the migration, so nothing is abbreviated.

| `perf_pi_result_period` column | Q1 | Q2 | Q3 | Q4 | Annual |
|---|---|---|---|---|---|
| `results` | `nrc_q1results` | `nrc_q2results` | `nrc_q3results` | `nrc_q4results` | `nrc_annualresults` |
| `operator` | `nrc_q1operator` | `nrc_q2operator` | `nrc_q3operator` | `nrc_q4operator` | `nrc_annualoperator` |
| `target` | `nrc_q1target` | `nrc_q2target` | `nrc_q3target` | `nrc_q4target` | `nrc_annualtarget` |
| `minimum_target` | `nrc_q1minimumtarget` | `nrc_q2minimumtarget` | `nrc_q3minimumtarget` | `nrc_q4minimumtarget` | `nrc_annualminimumtarget` |
| `maximum_target` | `nrc_q1maximumtarget` | `nrc_q2maximumtarget` | `nrc_q3maximumtarget` | `nrc_q4maximumtarget` | `nrc_annualmaximumtarget` |
| `lower_operator` | `nrc_q1loweroperator` | `nrc_q2loweroperator` | `nrc_q3loweroperator` | `nrc_q4loweroperator` | `nrc_annualloweroperator` |
| `upper_operator` | `nrc_q1upperoperator` | `nrc_q2upperoperator` | `nrc_q3upperoperator` | `nrc_q4upperoperator` | `nrc_annualupperoperator` |
| `not_applicable` | `nrc_q1notapplicable` | `nrc_q2notapplicable` | `nrc_q3notapplicable` | `nrc_q4notapplicable` | `nrc_annualnotapplicable` |
| `success_likelihood` | `nrc_q1successlikelihood` | `nrc_q2successlikelihood` | `nrc_q3successlikelihood` | **`nrc_q4successlikelihood1`** | `nrc_annualsuccesslikelihood` |
| `mitigation_remarks` | `nrc_q1mitigationremarks` | `nrc_q2mitigationremarks` | `nrc_q3mitigationremarks` | `nrc_q4mitigationremarks` | **`nrc_statusupdatesummary`** |
| `raw_data` | `nrc_q1rawdata1` | `nrc_q2rawdata1` | `nrc_q3rawdata1` | `nrc_q4rawdata1` | `nrc_annualrawdata` |

Four irregularities in the legacy Annual/quarterly column families, all confirmed against the
solution export:

1. **`nrc_q4successlikelihood1`** carries a trailing `1`. The improvements document lists a duplicate
   "Q4 Success Likelihood" column; this is the surviving one. Confirm which of the pair holds data
   before migrating.
2. **The annual "Mitigation / Remarks" is `nrc_statusupdatesummary`**, whose display name is
   *"Annual Mitigation / Remarks"* — it does not follow the `nrc_annual*` naming of its siblings.
3. **`raw_data` for Q1–Q4 uses the `...rawdata1` suffix**, but Annual is plain `nrc_annualrawdata`.
   The improvements document flags decimal-typed `Q# Raw Data` columns as deprecated; the `...1`
   columns are the surviving `nvarchar` versions.
4. **`nrc_annualrawdata` is MaxLength 100** while the four quarterly `nrc_q#rawdata1` columns are
   MaxLength 850 — an 8.5× difference the un-pivot erases. The normalised `raw_data` column is 850;
   existing Annual values fit, but any front-end limit must not be set to 100.

The multi-select `nrc_quarters` column is **not** part of this map — it becomes
`perf_pi_result_quarter` (section 10.11) and records which periods the user selected for reporting,
independently of which period rows carry values.

### 15.4 Migration staging columns

The following legacy text columns exist only to support the original SharePoint migration and must be
loaded into the attached `staging` database (`staging.db`, §1), not into the operational tables:

`BLText`, `FYText`, `IndTitle`, `MergeID`, `MigratedFlag`, `OfficeText`, `OrgText`, `PLText`,
`ProductText`, `ProgramText`, `ReptPersonText`, `ContactText`, `OwnerText`, `PIText`, `StrategyText`,
`BLPLText`. In the current export the surviving examples are `nrc_pltext` (Enterprise Risk) and
`nrc_programtext` (Accomplishment).

### 15.5 Migration validation checks

| Check | Expectation |
|---|---|
| Row counts per table | match the source export exactly |
| Identifier uniqueness | no duplicate `indicator_code`, `risk_code`, `accomplishment_code`, `pcm_code`, `update_code` |
| Orphan lookups | zero rows with a non-null FK pointing at a missing parent |
| State/status legality | every `(state, status_reason)` pair appears in the status→state map (`core_task` is checked against `core_task_state`) |
| Ownership | exactly one of user/team owner on every row |
| PI revision chains | every `change_type='revised'` row has a resolvable `previous_pi_id`; no cycles |
| Plan hierarchy | every objective sequence prefixes its goal; every strategy prefixes its objective (report, do not auto-fix) |
| Quarterly uniqueness | no duplicate `(enterprise_risk_id, fiscal_year_id, quarter)` risk updates |
| PI Result periods | at most one row per `(pi_result_id, period)`; range fields populated only for range indicators |
| Workflow integrity | every Approval/Rejection resolves to a Submission; every closed Submission has `approved` XOR `returned` |
| Character limits | report every value exceeding its target limit before enforcing the constraint |

---

## 16. Retired columns and tables

### 16.1 Columns to drop (confirmed deprecated in `SPA+-Improvements.doc`)

| Table | Columns |
|---|---|
| Performance Indicator | old `Indicator Status` (`nrc_indicatorstatus`), `Operator`, free-text `Performance Goal`, `*OLD* Accountable Organization`, `nrc_temp` |
| PI Result | `Approval Queue Flag`, `Business Line/Product Line Owner`, `Q# At-Fault Business Lines`, `Q# At-Fault Offices`, decimal `Q# Raw Data`, `Q# Updates`, duplicate `Q4 Success Likelihood`, `Return to`, `Send next to` |
| Enterprise Risk | legacy `Contact Person`, legacy `Risk Lead`, `nrc_impactdescription` (duplicate of `nrc_impactdescription1`) |
| Risk Update | `Impact Description`, `Likelihood Description`, `Performance Monitoring and Progress`, duplicate `Residual Likelihood Description` |
| Positive Change Management | legacy `Positive Change Management Item` label |
| Business Line | `nrc_test` |

### 16.2 Tables to retire

`nrc_Priorities` ((DEPRECATED) Priority) — archive only.
The full "abandoned/unused" list in Document 1 §13.1 must be confirmed with OEDO before dropping,
because several of those tables are still live in the shipped solution.

### 16.3 Platform artefacts not carried forward

`nrc_pisubmissionapprovals` (Business Process Flow instance table — the BPF itself is deactivated),
`ProcessSession`, `SyncError`, `QueueItem`, `Feedback`, `Connection`, `aaduser`, and all Dataverse
system columns listed in the preamble.

### 16.4 Orphaned form-navigation relationships (referenced but **not** defined in the export)

The exported forms carry **47** `NavBarByRelationshipItem` entries whose `RelationshipName` has **no
matching `EntityRelationship` definition anywhere in `customizations.xml`**, grouped under 18 distinct
navigation labels. Of these, **15 name entities that are absent from the export altogether**
(Accomplished Item, Attribute, Budget, Budget Data, Cross-Cutting Data, Data Entry, Division Owners,
Indicator IDs, Key Deliverables, Markers, Mitigating Strategy, Performance Requirement, Program,
Research, Fiscal Year Resources) and **3 name entities that are still present** — Performance
Indicator, PI Result and the deprecated Priorities table — meaning the relationship itself was
deleted while the entity survived. **Every one of the 47 is `Show="false"`**, which is why the
shipped application still works. They are listed here so the rebuild team recognises them as
dead references and does **not** attempt to build the tables behind them; they also corroborate the
"abandoned/unused" list in Document 1 §13.1.

| Navigation label | Orphaned relationships | Referenced from the form(s) of |
|---|---|---|
| (DEPRECATED) Priorities | 4 | `nrc_BusinessLine`, `nrc_FiscalYear`, `nrc_ProductLine`, `nrc_Strategy` |
| Accomplished Items | 1 | `nrc_FiscalYear` |
| Associated Performance Indicators | 3 | `nrc_PerformanceIndicator`, `nrc_PerformanceIndicatorFiscalYear`, `nrc_PrioritiesUpdate` |
| Attributes | 1 | `nrc_FiscalYear` |
| Budget Data | 2 | `nrc_BusinessLine`, `nrc_FiscalYear` |
| Budgets | 2 | `nrc_BusinessLine`, `nrc_FiscalYear` |
| Cross-Cutting Data | 1 | `nrc_FiscalYear` |
| Data Entries | 3 | `nrc_FiscalYear`, `nrc_Goal`, `nrc_Objective` |
| Division Owner(s)S | 1 | `nrc_PositiveChangeManagement` |
| Findings / Mitigating Strategies | 1 | `nrc_FiscalYear` |
| Fiscal Year Resources | 3 | `nrc_BusinessLine`, `nrc_FiscalYear`, `nrc_Product` |
| Key Deliverables | 2 | `nrc_Accomplishment`, `nrc_FiscalYear` |
| Markers | 2 | `nrc_FiscalYear`, `nrc_Office` |
| Performance Indicator Results | 8 | `nrc_BusinessLine`, `nrc_Office` |
| Performance Indicators | 1 | `nrc_Office` |
| Performance Requirements | 5 | `nrc_BusinessLine`, `nrc_FiscalYear`, `nrc_Office`, `nrc_PerformanceIndicator` |
| Programs | 4 | `nrc_BusinessLine`, `nrc_Goal`, `nrc_Objective`, `nrc_Strategy` |
| Research | 3 | `nrc_Goal`, `nrc_Objective`, `nrc_Office` |

Two of these deserve specific mention:

- **`nrc_IndicatorIDs`** ("Associated Performance Indicators") is referenced from three different
  forms — Performance Indicator, PI Result and Priority — and is the only orphan that appears on the
  core transactional forms. It was evidently an earlier mechanism for cross-linking indicators,
  superseded by the `nrc_manypis` / `nrc_manyupdates` junctions.
- **`nrc_nrc_performanceindicatorfiscalyear_Q#At…`** — 8 relationships (Q1–Q4 × At-Fault Business
  Line / At-Fault Office). These are the relationship halves of the per-quarter at-fault columns that
  §16.1 already marks for deletion on PI Result, confirming that removal is safe.

No API endpoint, screen, or table is specified for anything in this section.

---

*End of Document 2 — Complete Database Schema.*
*See Document 3 for the complete API and UI screen specification.*
