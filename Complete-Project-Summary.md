# NRC Strategic Planning & Performance Management System
# Document 1 — Complete Project Summary

**Program:** U.S. Nuclear Regulatory Commission (NRC) — Office of the Executive Director for Operations (OEDO)
**Current system name:** Strategic Planning Application (SPA) / Enterprise Performance System (EPS)
**Current platform:** Microsoft Power Platform (Dataverse + model-driven apps + Power Automate + Power BI)
**Target platform for rebuild:** Python backend · React (latest) frontend · SQLite database
**Source solution analysed:** `Core` v1.0.0.67 (managed), publisher `NRC`, prefix `nrc`, option-value prefix `87567`
**Document set:** 1 of 3 — (1) Project Summary · (2) Database Schema · (3) APIs & UI Screens
**Edition:** React + SQLite. The as-built analysis is unchanged from the Angular + PostgreSQL
edition. The rebuild guidance that depends on the front-end framework (§1.2, §4.2, §6.7, §10, §14) is
rewritten for React, and the guidance that depends on the database (§4.5, §8.1, §9.6, §12.5, §14,
§16) for SQLite. Document 2 §1.2 and §13 set out what SQLite changes; Document 3 §11.6 the React client.

---

## 0. How this document was produced (traceability)

Every statement in this document set is derived from the artefacts in `Proposal/Documentation`.
Nothing has been invented. Where the source material is silent, the gap is explicitly flagged in
§17 "Open items and documented gaps" rather than filled with assumptions.

| # | Source artefact | What was extracted |
|---|---|---|
| 1 | `Core_1_0_0_67_managed/customizations.xml` (5.8 MB) | 47 entities, 536 business attributes (excluding platform audit/system columns), 473 relationships (412 one-to-many, 61 many-to-many), 36 global option sets, all state/status models, 334 saved views (with FetchXML filters), 115 forms (tabs/sections/fields, 80 sub-grid placements over 60 distinct relationships), 2 app modules + 2 sitemaps, 6 dashboards, 102 web resources, 4 security roles, 94 processes, 7 connection references |
| 2 | `Core_1_0_0_67_managed/solution.xml` | Solution manifest, version, publisher, component inventory |
| 3 | `Core_1_0_0_67_managed/Workflows/*.json` (53 cloud flows) | Complete submission / approval / rejection / discontinue / carry-over / notification logic, ID-generation algorithms |
| 4 | `Core_1_0_0_67_managed/Workflows/*.xaml` (41 files = 40 business rules + 1 business process flow) | Client-side field visibility, required-level, default-value and lock rules |
| 5 | `Core_1_0_0_67_managed/Formulas/*.xaml` (11) | Rollup and calculated column definitions |
| 6 | `Core_1_0_0_67_managed/WebResources/*` (102) | 52 JavaScript + 5 HTML resources (the remaining 45 are icons/images): command-bar visibility rules, referential-integrity validators, auto-fill logic, character counters, save-prevention rules |
| 7 | `Core_1_0_0_67_managed/environmentvariabledefinitions/*` (43) | Deep-link and webhook configuration surface |
| 8 | `Core_1_0_0_67_managed/CanvasApps/*.msapp` (2) | Modern command library apps (Submit / Approve / Return / Finalize buttons) |
| 9 | `Performance Review Dashboard DEV DATA REPOINT.pbix` (4.5 MB) | 19 report pages, 473 visual containers, 41 model tables, all slicers, page/visual filters, conditional-format colour rules, drill-through and navigation map |
| 10 | `SPA_USER_GUIDE.pdf` (39 pages) | End-to-end user procedures, field-by-field data entry rules, character limits, bulk submission/approval procedure, dashboard refresh schedule |
| 11 | `SPA/SPA System Architecture Document (9).docx` v2.0 | System context, functional capabilities, authentication, use-case view, 508 compliance |
| 12 | `SPA/Strategic Planning and Performance Management Overview (1).docx` | PMA system requirements, QPR module, SES module |
| 13 | `SPA/SPA+Product+Vision.doc` | Module and component catalogue (all 6 modules) |
| 14 | `SPA/SPA+Product+Roadmap.doc`, `SPA/MVP+Roadmap.doc` | Epics, program increments, MVP vs future increments |
| 15 | `SPA/SPA User Roles and Permissions 6.13.23 (1).docx` | Narrative role/permission definitions |
| 16 | `SPA/SPA Personas - Draft 02.28.23.docx` | 5 personas |
| 17 | `SPA/User Role Permissions Matrix 2.1.23.xlsx` | Per-module View/Edit/None matrix for 6 roles × 6 modules |
| 18 | `SPA/SPA - Data Migration Plan - Draft.docx` | Source systems, record volumes, ETL steps |
| 19 | `SPA/SPA+-Improvements.doc` | Known defects, deprecated tables/columns/flows, backlog |
| 20 | `SPA/SPA Datamodel.png` (3086×4875) + `SPA/ERD Draft Strategic Planning (1).pdf` | Entity-relationship diagrams (both drafts pre-dating the shipped solution — see §17.1) |
| 21 | `SPA/EPS diagram 2.6.23.pdf`, `SPA/Conceptual+Architecture+Diagram.doc` | Conceptual architecture |
| 22 | `SPA/SPA+Data+Planning+Activities.doc`, `SPA/Database+model+draft.doc`, `SPA/Requirements.doc`, `SPA/SPA+User+Roles+and+Permissions+At+The+Office+Level.doc`, `SPA/SPA+Data+model+(latest).doc` | Confluence page exports — see §17.1, these are attachment-reference pages |

---

## 1. Executive summary

### 1.1 What the system does

The NRC publishes a multi-year **Strategic Plan** made up of **Goals → Objectives → Strategies**.
Across the agency, offices measure how well the plan is being executed. The system:

1. **Stores the Strategic Plan** — Goals, Objectives, Strategies, Performance Goals, External Factors,
   Definitions (glossary) and the Fiscal Years they apply to.
2. **Stores the agency's accountable structure** — Offices, Divisions, Organizations, Business Lines,
   Product Lines, Products, Major Programs and Contributing Programs & Activities.
3. **Defines the measures** — Performance Indicators (PIs), Enterprise Risks, Priorities, and
   Planned Measures/Milestones/Deliverables ("Actions"), each tied to a Goal/Objective/Strategy and to
   an accountable part of the organisation.
4. **Collects quarterly results** — PI Results, Risk Updates, Accomplishments, Positive Change
   Management (PCM) items and Priority entries, entered by office staff each quarter.
5. **Routes everything through an approval workflow** — Draft → Pending approval → Finalized, with a
   Return-for-revision path, driven by bulk Submit / Approve / Return actions, Teams + task
   notifications, and a full audit trail of Submission / Approval / Rejection records.
6. **Visualises the results** — a Power BI "Quarterly Performance Review" (QPR) dashboard suite of 19
   pages including risk heat maps, PI profiles, historical trends and a natural-language Q&A visual.

### 1.2 Why it is being rebuilt

The as-is system is built on Microsoft Power Platform low-code (Dataverse, model-driven apps,
Power Automate cloud flows, Power BI). The System Architecture Document itself records this as a
constraint: *"SPA is the first custom model-driven application of its kind in a low-code/no-code
environment using the power platform and as such had to overcome multiple constraints."*

The client has decided to rebuild the complete software from scratch on:

- **Backend:** Python
- **Frontend:** React (latest version), written in TypeScript
- **Database:** SQLite (a single database file on the API host — Document 2 §1.2)

This document set specifies **100 % of the functionality that must be reproduced**, derived
exclusively from the as-built artefacts.

### 1.3 Scale of the rebuild (measured, not estimated)

| Dimension | Count |
|---|---|
| Business entities (tables) to build | 36 custom + 5 platform-derived = **41** |
| Business attributes (excluding platform audit/system columns) | **536** (522 `nrc_` · 11 `new_` · 2 `cr9de_` · 1 `tei_`) |
| Relationships | **473** total → 412 one-to-many (lookups), 61 many-to-many |
| Many-to-many junction tables required | **61** |
| Global enumerations (option sets) | **36** |
| Entity-local Yes/No (boolean) attributes | **38** |
| Record lifecycle state machines | **9 distinct** (see §7) |
| List views ("saved queries") to reproduce | **334** — of which **190** are business views: **154** public list views plus the **36** per-entity *"My &lt;entity&gt;"* filter views. The remaining **144** are system-generated, 4 per entity across 36 entities: advanced-find, sub-grid/associated, quick-find and lookup views |
| Forms (main + quick-create + quick-view + card) | **115** |
| Automation processes | **94** → 53 cloud flows, 40 business rules, 1 business process flow |
| Client-side scripts (validation / UX) | **52 JavaScript** + **5 HTML** web resources |
| Security roles | **4** |
| Application modules (separate navigations) | **2** live + **4** planned |
| Power BI report pages | **19** |
| Power BI model tables | **41** |
| Deep-link / webhook configuration variables | **43** |

---

## 2. Business context and stakeholders

### 2.1 Organisation

- **NRC** — U.S. Nuclear Regulatory Commission.
- **OEDO** — Office of the Executive Director for Operations (this expansion is external/common
  knowledge, not sourced: no supplied artefact contains the phrase "Executive Director", and the only
  artefact that expands the acronym — the cover of *SPA - Data Migration Plan - Draft.docx* — reads
  "Office of the Deputy Assistant for Operations", which matches neither the acronym nor any NRC
  office and is treated here as a typo). Owns the Strategic Plan and runs the
  Quarterly Performance Review. Acts as the final approver ("EDO User").
- **Offices** — ~50 NRC offices; each reports performance results for its own scope.
- **Divisions** — sub-units of Offices.
- **Business Lines / Product Lines / Products** — budget-and-programme dimensions sourced from FAIMIS.
- **Major Programs / Contributing Programs and Activities** — programme dimensions.

### 2.2 The Quarterly Performance Review (QPR) cycle

1. Each quarter, office submitters enter/refresh their quarterly data (PI Results, Risk Updates,
   Accomplishments, PCM items, Priorities).
2. Submitters bulk-select their own draft records and press **Submit for Approval**.
3. Records move to *Pending approval*, ownership transfers to the approver, a Task is created for the
   approver and a Microsoft Teams notification is sent.
4. OEDO reviewers open each record, add **Comments** where revisions are needed, then bulk
   **Approve** (→ *Finalized*) or **Return** (→ *Revision*, ownership returns to the submitter, with a
   Teams notification).
5. Finalized data flows into the Power BI QPR dashboards, which refresh 8 times a day
   (8am, 9am, 10am, 12pm, 2pm, 4pm, 5pm, 6pm — per the User Guide).
6. At the start of the next quarter, OEDO uses **Open PI child records for next quarter** to
   re-open the current fiscal year's finalized PI Results for editing.

### 2.3 Product vision (verbatim scope from `SPA+Product+Vision.doc`)

> "The vision for the “Performance Management Application” and “Strategic Planning Application” systems
> is to enable the NRC to have a holistic view of the Strategic Plan and visualize how well the Agency
> is doing at implementing the plan. The performance management modules and components are the
> measurements used to determine if the Agency is meeting its goals, objectives, and strategies."

**Performance Management Application**
- *Quarterly Performance Management Module* — components: Performance Indicators, Risks,
  Accomplishments (dual), Positive Change Management, Priorities. Dashboard: Quarterly Performance
  Review Dashboard.
- *Senior Executive Leader Performance Module* — components: Elements and Standards.
  Dashboard: SES Performance Plan Dashboard.

**Strategic Planning Application**
- *Strategic Planning Module* — components: Goals, Objectives, Strategies, Programs, External Factors,
  Definitions, Accomplishments (dual), Survey Results. Dashboard: Strategic Plan Dashboard.
- *Evidence Building Module* — components: Priority Questions, Evaluations, Other Evidence-Building
  activities.
- *Capacity Assessment Module* — components: Key Agency Functions, Type of Evidence Building,
  Activities, Attributes, Agency Environmental Scan, Findings, Mitigating Strategies.
  Dashboard: Capacity Assessment Dashboard.
- *Signposts and Markers Module* — components: Overall US Demand for Power, Nuclear Power Economics,
  Operating Reactors, State and Federal Energy Policy, Nuclear Waste and Reactor Decommissioning,
  New and Advanced Reactor Deployment, Nuclear Reactor Innovation, Nuclear Materials, Fuel Cycle,
  Human Capital and Budget Trends. Dashboard: Signposts and Markers Dashboard.

**Stated prioritisation order:** Strategic Planning → Quarterly Performance Review → Evidence Building
→ Capacity Assessment → SES Performance → Signposts and Markers.

---

## 3. Applications, modules and their build status

The Dataverse solution contains **two live application modules**. Note that the internal unique names
are historically swapped relative to their display names — this is a known naming artefact:

| Internal unique name | Display name (what users see) | Status |
|---|---|---|
| `nrc_EnterprisePerformanceSystem` | **Strategic Planning** | Live |
| `cr9de_StrategicPlanningModule` | **Performance Management** | Live |

### 3.1 Module build status (from Product Vision + MVP Roadmap + solution contents)

| # | Module | Status in the as-built solution | Evidence |
|---|---|---|---|
| 1 | **Strategic Planning** | **Fully built** | App module, sitemap, all entities, views, forms |
| 2 | **Quarterly Performance Review (Performance Management)** | **Fully built** | App module, sitemap, entities, workflow engine, dashboards |
| 3 | **Evidence Building** | **Partially built (data layer only)** | Entities `nrc_PriorityQuestion`, `nrc_Evaluations`, `nrc_OtherEvidenceBuildingActivity` exist with full attribute sets, lifecycles and views, but **no app module or sitemap** |
| 4 | **Capacity Assessment** | **Not built** | Entities listed as abandoned/unused in `SPA+-Improvements.doc` (Key Agency Function, Attribute, Findings/Mitigating Strategy, Cross-Cutting Items, Agency Environmental Scan) |
| 5 | **SES Performance** | **Not built** | "Elements and Standards" entity absent; `nrc_relatedecq` / `nrc_criticalelement` option sets exist as stubs |
| 6 | **Signposts and Markers** | **Skeleton only** | Entities `new_Signposts` and `new_KeyAreas` exist (Title, Number, Analysis rich-text, Associated Signpost) with views; no app module |

> **Rebuild guidance:** Modules 1 and 2 must be reproduced at 100 % fidelity. Module 3's data model is
> fully specified and should be built. Modules 4–6 are specified only at component-name level in the
> Product Vision and Roles Matrix — they are scoped in this document as *forward-looking requirements*
> and clearly marked as such.

### 3.2 Navigation — Strategic Planning app (as-built sitemap)

```
Strategic Planning  (area)
├── At a glance...
│   ├── Dashboards                (Power BI: Performance Review report)
│   └── My To-do List             (Tasks grid + activity timeline)
├── Other Modules
│   └── Performance Management    (deep link to the other app)
├── Strategic Planning
│   ├── Goals
│   ├── Objectives
│   ├── Strategies
│   └── Performance Goals
├── Organizational
│   ├── Product Lines
│   ├── Business Lines
│   ├── Offices
│   ├── Major Programs
│   ├── Contributing Programs and Activities
│   └── Products
└── Details
    ├── Definitions
    ├── External Factors
    └── Organizations
```

### 3.3 Navigation — Performance Management app (as-built sitemap)

```
Performance Management  (area)
├── At a glance...
│   ├── My To-do List             (dashboard)
│   ├── Performance Review        (Power BI dashboard)
│   ├── User Guides               (embedded PDF web resource)
│   └── FAQ                       (embedded PDF web resource)
├── Other Modules
│   └── Strategic Planning        (deep link to the other app)
├── Performance Management
│   ├── Performance Indicators
│   ├── Enterprise Risks
│   └── Priorities Updates
├── Quarterly Data
│   ├── PI Updates                (= PI Results)
│   ├── Risk Updates
│   ├── Accomplishments
│   └── Positive Change Management
└── Admin
    ├── Groups                    (Teams — office groups; gated in the source sitemap on
    │                              Create-privilege for Objective — an apparent copy-paste error,
    │                              so the item is EDO-only in practice)
    └── Users                     (ungated)
```

---

## 4. Personas, roles and permissions

### 4.1 Personas and narrative roles (five personas from `SPA Personas - Draft 02.28.23.docx`; the Dashboard Viewer row from `SPA User Roles and Permissions 6.13.23 (1).docx`, which lists it as a role)

| Persona | Description | Typical staff titles |
|---|---|---|
| **Submitter** | Office-level staff who enter Strategic Plan results data: PI results, Risk updates, Accomplishments. Submits entries for approval. Can view the whole plan, results and dashboards. | Technical Assistant, Branch Chief, Management Analyst |
| **Intermediate Approver (Office-Level Approver)** | Office staff designated to approve their office's updates. Approves or returns entries; approved entries route to OEDO for final approval. | Office Director, DERMA Director (Office Deputy Director) |
| **SES User** | NRC staff who create and view their annual SES Performance Plan, referencing Performance Indicators. Also views and updates entries for SES users listed as **deputies** — a second delegation axis distinct from Alternate Owner (roles document). | Senior Executive Service members |
| **SES Alternate** | Assigned alternate for an SES User; can create/update that SES User's plan only. | — |
| **EDO User (Final Approver)** | OEDO staff who maintain the overall Strategic Plan (Goals, Objectives, Strategies, PIs), provide final approval, and can unlock/update previously finalized results to prepare for the QPR. | OEDO staff |
| **Dashboard Viewer** | View Strategic Planning Module dashboards · View Performance Management Module dashboards. | Any NRC user |

### 4.2 Security roles actually implemented in the solution

Four Dataverse security roles exist. Privilege depth abbreviations: **User** = own records only,
**BU** = business unit, **P:C BU** = parent-and-child business units, **Org** = organisation-wide.

| Role | Purpose | Notes |
|---|---|---|
| **SPA View Only User** | Baseline read-only access for every NRC user | 299 privileges — Read:Org on every business table, no Create/Write/Delete |
| **Quarterly Performance Submitter** | Office submitter | 844 privileges — Create/Write on own performance records, Read:Org on everything |
| **EDO User** | OEDO administrator / final approver | 1 014 privileges — full Create/Read/Write/Delete:Org on virtually everything |
| **Deprecated - Quarterly Performance Approver** | Legacy approver role | 977 privileges — flagged deprecated; superseded by team-based approval |

**App access (`AppModuleRoleMaps`) — which workspace each role may open:**

| Role | Strategic Planning (`nrc_EnterprisePerformanceSystem`) | Performance Management (`cr9de_StrategicPlanningModule`) |
|---|---|---|
| SPA View Only User | — | — |
| Quarterly Performance Submitter | ✅ | ✅ |
| EDO User | ✅ | ✅ |
| Deprecated - Quarterly Performance Approver | ✅ | — |

SPA View Only User is mapped to **neither** app: as shipped it is a data-access role only, and a user
holding just that role cannot open either workspace. In the rebuild this becomes a workspace-level
route check — a React Router loader that redirects — fed by `GET /api/v1/me/permissions` (Document 3 §11.6).

### 4.3 Implemented privilege matrix (extracted from the role definitions)

Legend: `C`=Create, `R`=Read, `W`=Write, `D`=Delete, `Ap`=Append, `ApTo`=AppendTo, `As`=Assign, `S`=Share.

| Table | SPA View Only User | Quarterly Performance Submitter | EDO User |
|---|---|---|---|
| Performance Indicator | R:Org | C:User R:Org W:User Ap/ApTo | C/R/W/D:Org, full |
| PI Result (Performance Indicator Results) | R:Org | C:User R:Org W:User Ap/ApTo | C/R/W/D:Org, full |
| Enterprise Risk | R:Org | C:User R:Org W:User Ap/ApTo | C/R/W/D:Org, full |
| Risk Update | R:Org | C:User R:Org W:User D:User | C/R/W/D:Org, full |
| Accomplishment | R:Org | C:User R:Org W:User Ap:BU | C:Org R:Org W:User Ap:Org |
| Priority (`nrc_PrioritiesUpdate`) | R:Org | C:User R:Org W:User D:User | C/R/W/D:Org, full |
| Positive Change Management | R:Org | C:User R:Org W:User D:User | C/R/W/D:Org, full |
| Goal / Objective / Strategy | R:Org | R:Org (+Append) | C/R/W/D:Org (Goal, Strategy), C/R/Ap:Org (Objective) |
| Fiscal Year | R:Org | R:Org (+Append) | C/R/Ap:Org |
| Office / Business Line / Product Line / Product / Organization | R:Org | R:Org (+Append) | C/R/Ap:Org |
| Major Programs / Office Goals / Planned Measure | R:Org | R:Org (+Append) | C/R/W/D:Org |
| Performance Goal (`nrc_PerformanceGoal`) | — | — | — *(no role in the solution grants any privilege on this table, so the Strategic Planning → Performance Goals sub-area is unreachable as shipped — see §13.1 and §17.3)* |
| Contributing Programs and Activities | R:Org | R:Org (+Append) | R:Org (+Append) |
| Definition / External Factor | R:Org | R:Org (+Append) | Definition R:Org; External Factor C/R/W/D:Org |
| Division | R:Org | C:User R:Org W:User | C:User R:Org W:User |
| Approval Queue | R:Org | C/R/W/D:Org | C/R/W/D:Org |
| Submission / Approval / Rejection | R:Org | *(created by automation only)* | *(created by automation only)* |
| Evaluations / Priority Question / Research Activity / Finding / Rulemaking | R:Org | R:Org (+Append) | R:Org (+Append) |
| Signposts (`new_Signposts`) | R:Org | R:Org | C/R/W/D/Ap:Org |
| Key Areas (`new_KeyAreas`) | R:Org | R:Org | R:Org |
| Team | — | R:Org | R:Org |

> **Note on the Finding / Rulemaking row.** `nrc_Finding` and `nrc_Rulemaking` privileges (Read Global
> in all four roles, plus Append/AppendTo/Assign/Share variants) are the only trace of those two tables
> in the export: neither appears as an `<Entity>`, a relationship or a form navigation link, and
> Document 2 defines no Finding or Rulemaking table. "Findings / Mitigating Strategy" is on the
> confirmed-removed list in §13.1 and "Rulemaking" survives only as option-set value 875670002 of
> `ref_evidence_building_activity_type`. Do **not** seed privileges for these two tables during the
> rebuild — they are orphaned role entries. Confirm with OEDO whether either table still exists
> outside the Core solution.

### 4.4 Intended permission matrix by module (from `User Role Permissions Matrix 2.1.23.xlsx`)

The workbook carries six role rows per module; the sixth, **SES Director?**, is spelled with a trailing
question mark in the source and its permissions are byte-identical to SES User / Alternate in all six
modules — treat it as a speculative role the authors had not yet confirmed, and confirm with OEDO
before implementing it (§17.3).

**QPR Module**

| Role | Goals | Objectives | Strategies | Perf. Indicators | PI Updates | Ent. Risks | Risk Updates | Accomplish. | PCM | Dashboards | Priorities | BL | PL | Products | Offices |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Submitter | View | View | View | View | Edit | View | Edit | Edit | Edit | View | Edit | View | View | View | View |
| EDO User | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit | View | Edit | Edit | Edit | Edit | Edit |
| Intermediate Approver | View | View | View | View | Edit | View | Edit | Edit | Edit | View | Edit | View | View | View | View |
| Final Approver | View | View | View | View | Edit | View | Edit | Edit | Edit | View | Edit | View | View | View | View |
| SES User / Alternate | View | View | View | View | View | View | View | View | View | View | View | View | View | View | View |
| SES Director? | View | View | View | View | View | View | View | View | View | View | View | View | View | View | View |

**Strategic Planning Module**

| Role | Goals | Objectives | Strategies | PIs | Programs | External Factors | Definitions | Accomplish. | BL | PL | Products | Offices | Survey Results | Dashboard |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Submitter | None ×13 (no module access) | | | | | | | | | | | | | View |
| EDO User | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit | View |
| Intermediate Approver | View ×13 | | | | | | | | | | | | | View |
| Final Approver | View ×13 | | | | | | | | | | | | | View |
| SES User / Alternate | View ×13 (no module access per note) | | | | | | | | | | | | | View |
| SES Director? | View ×13 (no module access per note) | | | | | | | | | | | | | View |

**SES Performance Module**

| Role | Goals | Objectives | Strategies | PIs | Elements & Standards | Dashboard | Accomplish. | PCM |
|---|---|---|---|---|---|---|---|---|
| Submitter | None (no module access) | | | | None | None | None | None |
| EDO User | Edit | Edit | Edit | Edit | Edit | Edit | Edit | Edit |
| Intermediate Approver | None (no module access) | | | | | | | |
| Final Approver | None (no module access) | | | | | | | |
| SES User / Alternate | View | View | View | View | **Edit** | View | View | View |
| SES Director? | View | View | View | View | **Edit** | View | View | View |

**Evidence Building Module**

| Role | Goals | Objectives | Strategies | PIs | Priority Questions | Evaluations | Other EB Activities | BL | PL | Products | Offices |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Submitter | View | View | View | View | Edit | Edit | Edit | View | View | View | View |
| EDO User | Edit ×11 | | | | | | | | | | |
| Intermediate Approver | View | View | View | View | Edit | Edit | Edit | View | View | View | View |
| Final Approver | View | View | View | View | Edit | Edit | Edit | View | View | View | View |
| SES User / Alternate | View ×11 | | | | | | | | | | |
| SES Director? | View ×11 | | | | | | | | | | |

**Capacity Assessment Module**

| Role | Goals | Objectives | Strategies | PIs | Key Agency Functions | Types of EB Activity | Attributes | Agency Env. Scan | Findings | Mitigating Strategies |
|---|---|---|---|---|---|---|---|---|---|---|
| Submitter | View | View | View | View | Edit | View | Edit | Edit | Edit | Edit |
| EDO User | Edit ×10 | | | | | | | | | |
| Intermediate Approver | View ×10 | | | | | | | | | |
| Final Approver | View ×10 | | | | | | | | | |
| SES User / Alternate | View ×10 | | | | | | | | | |
| SES Director? | View ×10 | | | | | | | | | |

**Signposts and Markers Module**

| Role | Goals/Objectives/Strategies/PIs | All 10 signpost topics |
|---|---|---|
| Submitter | View | View |
| EDO User | Edit | Edit |
| Intermediate Approver | View | View |
| Final Approver | View | View |
| SES User / Alternate | None (no module access) | None |
| SES Director? | None (no module access) | None |

### 4.5 Team-based (office) ownership

The system uses **Teams that represent Offices**. Key facts:

- The `Team` table is extended with a custom boolean `nrc_office` ("Office") — Yes marks a team as an
  Office group. There is a dedicated "Offices" view of Teams and an "SPA Teams" view.
- Records can be owned by a **user or a team**. Every submission/approval flow branches on
  `ownerid` logical name ("user" vs "team").
- Records carry both `nrc_Submitter` (user lookup) and `nrc_Submitterteam` (team lookup) — exactly one
  is populated.
- PI Results also carry `nrc_OfficeTeam` (Team lookup).
- "My Office's …" views filter by `nrc_office` records owned by `eq-useroruserteams`.
- The approver is resolved from the environment variable `nrc_ApproverForQPRFlows`, whose default
  value is a **team** reference (`teams(82c52953-f949-ef11-a316-001dd8308619)`).
- **Delegation during absence.** The Overview document requires *"functionality to control who updates
  what, without losing the flexibility of another person having that access in the event someone is out
  of the office"*. No such mechanism exists in the shipped solution beyond record re-assignment and the
  Approval Queue's *Alternate?* flag (§6.8) — see §17.3.

> **Rebuild guidance:** SQLite has no Dataverse ownership model — and no row-level security either.
> Doc 2 §1.1 and §13 specify an explicit `owner_user_id` / `owner_team_id` pair plus a visibility
> predicate that the API's data-access layer applies to every query, reproducing
> User / BU / Parent-Child-BU / Org privilege depths.

---

## 5. Functional scope — module by module

### 5.1 Strategic Planning module

| Capability | Detail |
|---|---|
| **Maintain Goals** | Title, sequence number, goal text, fiscal year, goal image, plus four rollup counters (Objective Count, Strategy Count, Indicators Count, Risk Count). Applicable Fiscal Years is many-to-many. Display name auto-composed as `"{sequence}: {goal text}"`. |
| **Maintain Objectives** | Title, decimal sequence, parent Goal, fiscal year. Display name auto-composed from a category derived from the first digit of the sequence: `1` → "Safety and Security Objective {n}:", `2` → "Organizational Health Objective {n}:", `3` → "Stakeholder Confidence Objective {n}:", followed by the title. Applicable Fiscal Years many-to-many. A view named "Filtered by Goals" exists but is hard-coded to a single goal ("Ensure the Safe and Secure Use of Radioactive Materials") — in the rebuild this becomes a parameterised filter. |
| **Maintain Strategies** | Title, sequence string, parent Goal and Objective, fiscal year. Display name auto-composed as `"{sequence} {title}"`. Applicable Fiscal Years many-to-many. |
| **Maintain Performance Goals** | Title, sequence, display name `"{sequence} {title}"`. Linked from Performance Indicator. |
| **Maintain Fiscal Years** | Year label, start date, end date. |
| **Maintain External Factors** | Title, description, affected Goal, fiscal year. Many-to-many to Objectives and Strategies. |
| **Maintain Definitions (glossary)** | Auto-numbered `NRC-{0001}`, title, description, data source (multi-select), fiscal year (integer), business line(s), business/product line owner, and links to Office, Office Goal, Performance Indicator, PI Entry, Product, Quarter, Goal, Objective, Strategy. Many-to-many to Business Lines and Product Lines. Supports the Overview document's User-Interface requirement that glossary terms be hover-explained on the dashboard (§10). |
| **Maintain the organisational structure** | Offices (Office name, Code, Prefix Code, calculated Display Name), Divisions (Name/Acronym), Organizations (Name), Business Lines (name, B&R code, Prefix code, Alternate Owner), Product Lines (name, B&R code, Prefix code), Products (Product, Product Code, calculated Internal Product Name), Major Programs (Name), Contributing Programs and Activities (Name), Office Goals (Name + Office). |
| **View performance data** | All Strategic Planning users can read PIs, PI Results and the accountable structure. |
| **Dashboards** | Embedded Power BI Strategic Planning dashboard. |

### 5.2 Performance Management (QPR) module

#### 5.2.1 Performance Indicators (the measure definition)

Created by office submitters (for non-Agencywide, non-CBJ/APPR indicators) or by EDO users (for
Agencywide / CBJ-APPR indicators). Field set and rules taken from the User Guide plus the form and
business rules:

| Field | Type | Rule |
|---|---|---|
| Indicator ID | text | **System generated** — see §8.1 |
| Implementation Year | lookup → Fiscal Year | |
| Indicator Title | text, **200 char** (User Guide) / stored 4000 | |
| Description | multiline, **1 000 char** (User Guide) / schema max 950 | Counter attached, but it tests for 959 — coherent when the column was 1 000 wide, unreachable since it was narrowed to 950 (Doc 3 §15.5.1). Enforce **950**; the guide's 1 000 is the pre-narrowing value. |
| Report Level | choice | CBJ/APPR · Business Line/Product Line · Office Performance Report · Division |
| Contact Person | lookup → User | required |
| Owner | lookup → User | required |
| Accountable Organization | lookup → Organization | required |
| Change Type | choice | New · Revised · (No Change — deprecated; "moving forward users should not be creating 'No Change' indicators") |
| PI being revised | lookup → Performance Indicator | **appears only when Change Type = Revised**, and becomes required (business rule `changetyperevised`). Selecting it **auto-fills ~20 fields** from the previous PI (web resource `nrc_autofillPI`) |
| Indicator Status | choice | Under Development (default) · Active · Discontinued · Pending Discontinue |
| Agencywide Support Level | choice | Agency · Office · N/A |
| Data Source | choice | External Website · FAIMIS · HRMS · LDAP · SharePoint · Other · N/A. Choosing **Other** reveals the "Other Data Source" text field (business rule `ShowOtherDataSource`) |
| Measure Type | choice | Quantitative · Qualitative · **Range** |
| Indicator Type | choice | Output · Outcome · Process · Input · Efficiency · Contextual |
| Units | choice | % · Integer · Decimal · Yes/No · Dollar · Text |
| Results Calculation | multiline, **1 000 char** (User Guide) | Field description reads "Limited to 670 characters or less"; character counter attached |
| Lead Business Line | lookup → Business Line | required |
| Strategic Plan Goal / Objective / Strategy | lookups | required; validated for hierarchy integrity (§8.3) |
| Primary Major Program / Primary Contributing Program | lookups | required |
| Lead Product Line / Product | lookups | Product Line required |
| Lead Office / Division | lookups | Office required |
| Performance Goal | lookup → Performance Goal | shown only when a condition on the form is met (business rule "show perf goal") |
| Annual Performance Plan and Report | Yes/No | hidden on the form |
| Quarterly Performance Review | Yes/No | hidden on the form |
| Review for carry-over? | Yes/No | set by the Flag / Unflag carry-over commands |
| Comments | rich text, 2 000 | "COMMENTS REGARDING SUBMISSION" — shown only in Pending-approval / Revision states |
| Entry count | integer | default 0 |
| Mitigation Strategy | multiline 4 000 | |
| Target | decimal | |

**Related grids** (populated after first save): Contributing Business Lines, Contributing Product
Lines, Contributing Offices, Contributing Major Programs, Other Contributing Programs, Actions
(Planned Measures/Milestones/Deliverables), Performance Indicator Results.

#### 5.2.2 PI Results (the quarterly reporting record)

| Field | Type | Rule |
|---|---|---|
| Indicator ID (`nrc_title`) | text | copied from the parent PI on creation |
| Reporting Person | lookup → User | required; **defaults to the record creator** (business rule) |
| Reporting Office | lookup → Office | required |
| Division | lookup → Division | |
| Performance Indicator | lookup → PI | required |
| Fiscal Year | lookup | required |
| Quarter(s) | **multi-select** | Q1 · Q2 · Q3 · Q4 · Annual |
| Reporting Business Line / Product Line | lookups | |
| Primary Major Program / Primary Contributing Program | lookups | |
| Data Type | calculated choice | derived from the PI's Measure Type (Quantitative/Qualitative) |
| Indicator Type | calculated choice | derived from the PI, but **not** a copy — see §8.5 |
| (INTERNAL) Measure Type | calculated choice | derived from the PI — drives the Range/Regular display rule |
| **Per quarter (Q1–Q4) and Annual, 11 fields each:** | | |
| · Results | decimal | quantitative indicators |
| · Operator | choice | `<` `=` `>` `<=` `>=` `N/A` |
| · Target | decimal | |
| · Minimum Target / Maximum Target | decimal | **Range** indicators only |
| · Lower Operator / Upper Operator | choice | **Range** indicators only |
| · Not Applicable | Yes/No | ticking it **clears and locks** that quarter's Results field |
| · Success Likelihood | choice | Likely · Unlikely · Met · Unmet |
| · Mitigation / Remarks | text, **800** (schema) / 100 (User Guide) | Character counter |
| · Raw Data | text, 850 (schema) / 100 (User Guide) | |
| Met or Unmet | Yes/No | |
| Mitigating Remarks / Mitigating Strategies | text | shown when *Met or Unmet* = No (rule deactivated in the shipped solution — see §8.2) |
| Comments | rich text 8 000 | approver comments |
| Public | Yes/No | |
| Planned Measure, Milestone or Deliverable | lookup | |
| Office Team | lookup → Team | |

**Related grids:** Contributing Business Lines, Contributing Product Lines, Contributing Major
Programs, Other Contributing Programs. (The Office ↔ PI Result M:N relationship exists in metadata but
is not placed on the form — see Doc 3 §14.2.) A read-only **quick-view** of the parent
Performance Indicator is embedded on the form as one card, "Performance Indicator Details", holding the
twelve fields the source splits over two quick views.

**Form tabs:** General · Quarterly Updates (5 sections: Quarter 1–4 + Annual) · Attachments.

#### 5.2.3 Enterprise Risks

| Field | Rule |
|---|---|
| Risk ID (`nrc_risktitle`) | system generated (§8.1); User Guide calls it "Risk ID – System Generated" |
| Risk Title (`nrc_riskid`) | text 100 (User Guide) |
| Description | **310 char** (User Guide) / schema 300. Counter attached and tests for 313 — reachable when the column was 550 wide, not for values written since it was narrowed to 300 (Doc 3 §15.5.1). Enforce **300**; 310 is unenforceable unless the column widens (§17 open question 5). Legacy rows may still hold up to 550 characters — see the migration hazard in Doc 3 §15.5.1.1. |
| Report Level | CBJ/APPR · BL/PL · Office Report · Division. The roles document restricts submitters to *"non Agency Wide and CBJ type risks"*, i.e. the same EDO-only creation rule as Performance Indicators (§5.2.1) — but the shipped solution implements the guard for PI only; see §17.3. |
| "Performance Indicators not applicable for this Risk" | checkbox; when **unchecked**, related PIs must be added to the sub-grid after first save. Backed by the required text field `Related PI Required` |
| Originating Fiscal Year, Originating Quarter | required |
| Lead Office, Division | |
| Strategic Plan Goal / Objective / Strategy | validated for hierarchy integrity |
| Primary Major Program, Primary Contributing Program | required |
| Lead Business Line, Lead Product Line, Product | |
| Risk Status | Under Development · Active · Pending Discontinue · Discontinued |
| Impact / Likelihood (+ descriptions) | legacy fields retained |
| Additional Factors, Initial Risk Control Efforts, Performance Monitoring/Progress Plans | long text 8 000 |
| Owner Office, Business Line/Product Line Owner | |
| Public? | Yes/No |
| Entry Count | default "0" |
| Comments | rich text; visible only in Pending approval / Revision |

**Related grids:** Related Performance Indicators (M:N), Applicable Fiscal Years (M:N), Contributing
Offices, Contributing Major Programs, Other Contributing Programs, Contributing Business Lines,
Contributing Product Lines.

#### 5.2.4 Risk Updates (the quarterly risk reporting record)

The richest form in the system. Sections and fields:

**General** — Entry ID (system generated = parent Risk ID), Enterprise Risk, Fiscal Year, Quarter,
PSAT? (PSAT / Non-PSAT), Reporting Office, Contact Person, plus an embedded read-only quick-view of
the parent Enterprise Risk ("Risk Details").

**Program(s)** — Major Program, Primary Contributing Program, Other Contributing Programs (M:N grid).
**Business Line(s)** — Reporting Business Line, Other Contributing Business Lines (M:N grid).
**Product Line(s)** — Reporting Product Line, Other Contributing Product Lines (M:N grid).

**Inherent Risk**
- Inherent Likelihood (High / Medium / Low)
- Inherent Likelihood QPR Description (300 char)
- Inherent Likelihood Full Description (999 999 char)
- Inherent Consequence (High / Medium / Low)
- Inherent Consequence QPR Description (300)
- Inherent Consequence Full Description (999 999)

**Residual Risk**
- Residual Likelihood (H/M/L), QPR Description (300), Full Description (999 999)
- Residual Consequence (H/M/L), QPR Description (300), Full Description (999 999)

**Monitoring and Mitigation**
- Risk Outlook (Increasing / Decreasing / Stable) — hidden on the form
- MANAGE (Current Risk Response) QPR Description (600, required) + Full Description (999 999)
- "Check if this risk is accepted (have we done enough?)" — **when ticked, the ACT (Proposed Risk
  Response) QPR Description becomes optional; when unticked it is required** (business rule
  `Is risk accepted`)
- ACT (Proposed Risk Response) QPR Description (300) + Full Description (999 999)
- Risk Monitoring QPR Description (300) + Full Description (999 999)
- Informed Monitoring QPR Description (300) + Full Description (999 999)
- Budget String(s) (225 char)

**(For OEDO use only)** — PSAT Accepted?, Notes (PSAT comments).

**Carried forward automatically on creation** (flow *Last Quarter link for Risk Updates*): Last
Quarter's Inherent Likelihood, Inherent Consequence, Residual Likelihood, Residual Consequence — looked
up from the previous quarter's Risk Update for the same Enterprise Risk. Quarter→previous-quarter
mapping: Q1 → Q4 of prior FY; Q2 → Q1 same FY; Q3 → Q2; Q4 → Q3; Annual → Annual of prior FY.

**Risk Lead** and **Contact Person** are required on every Risk Update but have **no as-built source**:
`nrc_EnterpriseRisk` carries no `nrc_contactperson` / `nrc_risklead` column in v1.0.0.67 (both appear in
the 2022–23 canvas metadata cache and were deleted since), and no create-time flow or business rule
populates them — there are no `EntityMap` / `AttributeMap` field mappings in the solution and
`ON RISK UPDATE CREATION` writes only Entry ID. Confirm with OEDO how these two mandatory fields are to
be defaulted — §17.3.

#### 5.2.5 Priorities

Title (100), Description (650 per User Guide / 4 000 schema), Report Level, Fiscal Year,
Quarter (multi-select), Rank (1–11), Principles of Good Regulation (Openness · Reliability ·
Independence · Efficiency · Clarity · None), Lead Business Line, Lead Product Line, Product,
Strategic Plan Goal / Objective / Strategy, Primary Major Program, Primary Contributing Program,
Lead Office, Division, Priorities Owner, Office Goals (text), Update ID (system generated),
Related PI Required, Public.
Related grids: Contributing Business Lines, Contributing Product Lines, Contributing Major Programs,
Other Contributing Programs, Contributing Offices, Related Performance Indicators.

#### 5.2.6 Positive Change Management (PCM)

ID (system generated `PCM-…`), Title (100), Description (1 200 char — a counter exists but is
registered on no form; the User Guide's 650 is the width before this column was widened,
Doc 3 §15.5.1), Report Level,
Fiscal Year, Quarter, Contact Person, Lead Business Line, Lead Product Line, Product, Strategic Plan
Goal / Objective / Strategy, Primary Major Program, Primary Contributing Program, Lead Office,
Associated Offices (`nrc_partneroffices` — a single Office lookup, defined but placed on no form and
no view in the shipped solution), Division, Office Goals, Presented at QPR (Yes/No, hidden), Public,
Entry Count.
Related grids: Contributing Business Lines, Contributing Product Lines, Contributing Major Programs,
Contributing Programs, **Division Owner(s)** (M:N to Users), Contributing Offices.

#### 5.2.7 Accomplishments

Accomplishment ID (system generated `ACC-…`), Title (100), Description (850 char; this is one of
only two counters that actually fires — it warns at 755 saying "750 characters or less", Doc 3
§15.5.1),
Report Level, Fiscal Year, Quarter (multi-select), Owner, Contact Person, Lead Business Line,
Lead Product Line, **Primary Related PI** (selecting it auto-populates Strategic Plan Goal, Objective
and Strategy — web resource `nrc_accFillStratFromPI`), Strategic Plan Goal / Objective / Strategy,
Primary Major Program, Primary Contributing Program, Lead Office, Division, Related ECQ,
Related PI? / Related PI Required, Annual Performance Plan (hidden), Quarterly Performance Review
(hidden), Public, ProgramText.
Related grids: Contributing Business Lines, Contributing Product Lines, Other Related Performance
Indicators, Contributing Major Programs, Other Contributing Programs, Contributing Offices.
Form section header is **"NOTES FOR RESUBMISSION"** with field **"COMMENTS REGARDING RESUBMISSION"**
(business rule `Resubmission Comments`).

#### 5.2.8 Planned Measures, Milestones and Deliverables ("Actions")

Title (850), Deliverable Title (1 000), Description (8 000), Status Update (2 000), Type
(Quantitative / Qualitative / Range), Performance Goal (text), Regarding Performance Indicator
(required lookup), and a **file attachment** column (Deliverable Attachment, max 32 MB).
Status reason values: In progress · Met · Unmet · Cancelled/closed.

#### 5.2.9 Action/Measure (separate legacy table)

Title (850), Number, Timeframe (2 000), Objective satisfied? (Yes/No), Completed or carried forward?
(Completed / Carried forward), Completion/carry-over notes (2 000). Many-to-many to Office.

### 5.3 Evidence Building module (data layer built, no UI shipped)

| Entity | Key fields |
|---|---|
| **Priority Question** | Priority Question (4 000), Answer Type (Assessment · Analysis · Research · Evaluation), **Answer** (polymorphic lookup → Evaluations *or* Research Activity), Approval Stage (int), Approver Comments/Revisions (2 000), Publish?, Approval Queue grid |
| **Evaluations** | Title (100), Summary (750), Evaluation Objective, Key Questions, Evaluation Methods, Data Needs and Sources, Stakeholder Engagement, Challenges and Mitigating Strategies, Status Description (all rich text 2 000), Status (Completed · In Progress · Delayed · Starts in FY), Type of Activity, Contractor Support, Total Resources Dollars (money) and FTE (decimal), Office (required), Fiscal Year, Performance Indicator, Related Strategic Goal / Objective, Publish (Yes/No, required), Approval Order Stage, Approver Comments/Revisions. Many-to-many to Product |
| **Research Activity** (`nrc_OtherEvidenceBuildingActivity`) | Activity Title (100), Overview (2 000), Drivers, Impact and Benefits, Stakeholder Engagement, Strategic Focus Area (rich text 2 000), Type (Research · Rulemaking · Other), Lead Office, Point of Contact (required), Fiscal Year, Performance Indicator, Strategic Goal / Objective, Contractor Support, Total Resources Dollars / FTE, Publish?, Approval Stage, Approver Comments/Revisions |

Lifecycle for all three: Draft → Pending Intermediate Approval → Pending Final Approval → Finalized,
plus Revision and Cancelled. This is a **two-stage** approval, unlike the single-stage QPR lifecycle.

### 5.4 Signposts and Markers module (skeleton)

| Entity | Fields |
|---|---|
| **Signposts** (`new_Signposts`) | Title (100, required), Signpost Number (100), Analysis (rich text 2 000, required), Name (auto-set to Title) |
| **Key Areas** (`new_KeyAreas`) | Title (100, required), Key Area Number (100), Analysis (rich text 2 000, required), Associated Signpost (required lookup → Signposts), Name (auto-set to Title) |

Ten signpost topics are named in the Product Vision and the Roles Matrix: Overall U.S. Demand for
Power · Nuclear Power Economics · Operating Reactors · State and Federal Energy Policy · Nuclear Waste
and Reactor Decommissioning · New and Advanced Reactor Deployment · Nuclear Reactor Innovation ·
Nuclear Materials · Fuel Cycle · Human Capital and Budget Trends.

### 5.5 SES Performance module (requirements only)

From `Strategic Planning and Performance Management Overview (1).docx`:

> "Use of this module will be limited to the individual owner of the plan and whomever else they
> designate. The purpose of this module is to enable the SES to associate the performance indicators,
> accomplishments, and positive change management to their Elements and Standards in a way that can be
> used in their annual appraisals, **exportable into a Word File**. Ideally, this would be integrated or
> shared with the Talent Management System."

Supporting enumerations already exist: `nrc_criticalelement` (Leading Change · Leading People ·
Business Acumen · Building Coalitions · Results Driven) and `nrc_relatedecq` (Leading Change ·
Leading People).

### 5.6 Capacity Assessment module (requirements only)

Components named in the Product Vision: Key Agency Functions, Type of Evidence Building, Activities,
Attributes, Agency Environmental Scan, Findings, Mitigating Strategies.
Supporting enumerations already exist: `nrc_attributetypes` (Coverage · Quality · Effectiveness ·
Methods · Independence), `nrc_coveragetypes` (Distribution of Evidence-Building Activities ·
Workforce Gaps and Surpluses), `nrc_findingsprogresschoice` (New · Revised · No Change · Discontinued),
`nrc_staffchangetype` (Demand · Supply · Attrition), `nrc_staffpostition` (18 NRC job series),
`nrc_typeofevidencebuildingactivity`.

---

## 6. The approval workflow engine (complete specification)

This is the heart of the system and must be rebuilt exactly.

### 6.1 Record types covered

Seven record types participate, identified by the `Record Type` enumeration:

| Value | Record type |
|---|---|
| 875670000 | Performance Indicator |
| 875670001 | PI Result |
| 875670002 | Enterprise Risk |
| 875670003 | Risk Update |
| 875670004 | Priority |
| 875670005 | Positive Change Management |
| 875670006 | Accomplishment |

### 6.2 Actions and how they are triggered

Three bulk commands appear on list views, plus five record-specific commands. Each command is a
webhook that receives the selected record IDs.

| Command | Visible on view | Applies to | Effect |
|---|---|---|---|
| **Submit for Approval** | `MY {Type} in Draft/Revision` | all 7 types | Draft/Revision → Pending approval |
| **Approve** | `{Type} Pending MY Approval` | all 7 types | Pending approval → Finalized |
| **Return** | `{Type} Pending MY Approval` | all 7 types | Pending approval → Revision |
| **Propose for discontinuance** | `Finalized Enterprise Risks` / `Finalized Performance Indicators` | Ent. Risk, PI | status → Pending Discontinue |
| **Discontinue** | `… Pending Discontinuance` (EDO role only) | Ent. Risk, PI | status → Discontinued, record deactivated |
| **Deny discontinuance** | `… Pending Discontinuance` (EDO role only) | Ent. Risk, PI | status → Active, record re-finalized |
| **Open PI child records for next quarter** | `Finalized PI Results` (EDO role only, **no rows selected**) | PI Result | Re-opens records to Draft if their FY = current FY |
| **Flag / Unflag for carry-over** | Performance Indicator grid | PI | sets/clears `Review for carry-over?` |

**Command visibility logic** (JavaScript, one file per entity — `nrc_*ButtonRules`):
the current **view name** plus the user's **security roles** determine which buttons render.
The EDO role is identified by a hard-coded GUID in the scripts. This must be re-implemented as a
server-driven capability check in the rebuild (see Document 3, §4).

**Confirmation dialogs** — every command shows a confirm prompt and a success/failure alert. Examples
taken verbatim from the command definitions:

- `Submit {0} selected Accomplishments?` → *"Accomplishment(s) successfully submitted for approval."*
- `Approve {0} Enterprise Risks?` → *"Enterprise Risk(s) successfully approved."*
- `Return {0} Risk Update(s)? Please include revision notes on individual records.`
- `Deny discontinuance for {0} Enterprise Risk(s)?`
- `This will flag {0} Enterprise Risk(s) for review to discontinue. Do you want to proceed?`
- `This action will unlock all PI Result records for the current fiscal year to be editable for the next quarter. Do you want to proceed?`
- `Flag {0} selected record(s) for carry over review?`
- `Remove carry over flags for {0} records? This will not change anything within the record and will only remove them from the review list.`
- `Notification will be sent to EDO for review. Ok to proceed?`

### 6.3 Submit — exact algorithm (per record)

1. Load the record.
2. Capture the current owner as the **Submitter**; determine whether it is a user or a team.
3. Resolve the **Approver** from configuration (`nrc_ApproverForQPRFlows`); determine user vs team.
4. Update the record: `status = Pending approval`, `owner = Approver`,
   `Submitter = <user>` **or** `Submitter (team) = <team>` (exactly one).
5. If the record's previous status was **Revision**, this is a *resubmission*:
   create a `Submission` row with `Resubmission = true`, then find all **active** `Rejection` rows for
   this record and close them (`status = Resubmitted`, `state = Inactive`).
   Otherwise create a normal `Submission` row.
6. The `Submission` row carries: `Name` = `"{Type} {DocumentID} submitted at {timestamp} by {Submitter}"`,
   `From` / `From (team)`, `To` / `To (team)`, `Type` (record type enum), `Task Made? = false`,
   `Document GUID` = `"{prefix}-{record GUID}"`, and the typed foreign key to the record.

> **As-built exception.** For five of the seven types the interpolated value is the Document ID. The
> Performance Indicator flows interpolate `nrc_indicatorid` (display name "Title") and the Enterprise
> Risk flows `nrc_riskid` (display name "Risk Title") — i.e. the record *title*, not its identifier —
> while the *Check for new submissions* job resolves the Document ID from `nrc_performanceindicator` /
> `nrc_risktitle`. The rebuild should standardise on the identifier (§13.4, §17.3).

**Document GUID prefixes:** `PI-` Performance Indicator · `PIRES-` PI Result · `ER-` Enterprise Risk ·
`RU-` Risk Update · `PRI-` Priority · `PCM-` Positive Change Management · `ACC-` Accomplishment.

### 6.4 Approve — exact algorithm (per record)

1. Load the record; the current owner is the **Approver**, the stored `Submitter`/`Submitter (team)` is
   the **Submitter**.
2. Create an `Approval` row: `Name` = `"{Type} {DocumentID} approved by {Approver} at {timestamp}"`,
   `Approved by` = Approver, `To` = Submitter, `Document GUID`, typed FK.
3. Find the most recent **active** `Submission` for the record and close it:
   `Approved = true`, `Returned = false`, `status = Complete`, `state = Inactive`.
4. Update the record: `status = Finalized`, `state = Inactive`, `owner = Submitter`.
   - Performance Indicator additionally sets `Indicator Status = Active`.
   - Enterprise Risk additionally sets `Risk Status = Active`.

> **Known as-built defect (Positive Change Management).** The *Pos Change Mngmt Approval Childflow*
> binds **both** `nrc_To` and `nrc_Toteam` to `if(subSingle, null, Submitter)` (the other six approval
> child flows bind `nrc_To` to `if(subSingle, Submitter, null)`). For a single-user submitter the PCM
> `Approval` row therefore carries no recipient at all, *Check for new approvals* takes its team branch
> on the empty `To` lookup and builds `teams(null)` as the Task owner, so PCM approval notifications
> never fire; for a team submitter `nrc_To` receives a `teams(...)` reference into a user lookup. The
> rebuild must implement the documented behaviour (`To` = Submitter) and the migration must repair
> existing PCM Approval rows.

> **As-built exception.** The *Performance Indicator Approval Childflow* writes the **submitter's**
> name into the "approved by" slot — it interpolates `variables('Submitter Name')` where the other six
> approval child flows use `variables('Approver Name')` (which that flow populates but never reads).
> The rebuild must use the approver; migrated PI `Approval` rows will contain the wrong name.

### 6.5 Return — exact algorithm (per record)

1. Load the record; identify Approver (current owner) and Submitter.
2. Create a `Rejection` row: `Name` = `"{Type} {DocumentID} returned to {Submitter} at {timestamp}"`,
   `From` = Approver, `To` = Submitter, `Document GUID`, typed FK, `status = Pending changes`.
3. Close the most recent active `Submission`: `Returned = true`, `status = Complete`, `state = Inactive`.
4. Update the record: `status = Revision`, `state = Active`, `owner = Submitter`.

### 6.6 Notification engine

Four scheduled jobs plus one event-driven job:

| Job | Trigger | Behaviour |
|---|---|---|
| **Check for new submissions** | Recurrence — every 5 min | Find `Submission` rows with `Task Made? = false` and `state = Active`, ordered by From-user then Type. For each, resolve the record's human-readable Document ID. **Group** all other pending submissions of the **same type from the same submitter** into one Task. Create a Task owned by the Approver with `subject = "{Record Type}(s) waiting for your approval."`, `Action Type = Submit`, `Submitted Record(s) Type = {type}`. Link every grouped submission to that Task and set `Task Made? = true`. Finally set `description = "{Record Type}(s) sent from {Submitter}: {comma-separated Document IDs}."` and flip `Regarding Approval Submission? = true` (this flag is what fires the notifier). |
| **Check for new approvals** | Recurrence — every 5 min | Same grouping pattern over `Approval` rows; Task `Action Type = Approve`, owned by the Submitter, `subject = "Your {Record Type}(s) have been finalized."`, `description = "{Approver Name} has approved/finalized your submitted {Record Type}(s): {comma-separated Document IDs}."` |
| **Check for new rejections** | Recurrence — every 5 min | Same grouping pattern over `Rejection` rows; Task `Action Type = Reject`, owned by the Submitter, `subject = "Your {Record Type}(s) have been returned."`, `description = "{Returner Name} has returned your submitted {Record Type}(s): {comma-separated Document IDs}."` |
| **Notify user of new task…** | Task updated where `Regarding Approval Submission?` becomes true | Picks a **deep link** matching `Submitted Record(s) Type` × `Action Type` (21 combinations, see §6.7), then branches on the Task owner's type. **Owner = user:** resolve that user's `internalemailaddress` and post a 1:1 **Flow-bot chat** message (`location = "Chat with Flow bot"`, `isAlert = true`). **Owner = team:** collect every member's e-mail, then find the Microsoft Teams **group chat** topic'd **"SPA Notifications"** whose membership matches that set (Microsoft Graph `/beta/me/chats/{id}/members`), creating one if none matches, and post there (`location = "Group chat"`). Each of the three Action Type cases duplicates this user/team split, giving six post actions. The flow also appends the flow owner's literal address `Devan.Tighe@nrc.gov` to the `primEmails` membership set used to match an existing SPA Notifications chat, so chat matching depends on one hard-coded account. For `Action Type = Approve` only, the notifier additionally closes the Task itself immediately after posting (`statecode = 1` Inactive, `statuscode = 5` Completed); Submit and Reject Tasks are left to the *Check submission related tasks for completion* job. |
| **Check submission related tasks for completion** | Recurrence — every 4 min | For every open Task with `Regarding Approval Submission? = true`, look at all linked Submission / Approval / Rejection rows (chosen by `Action Type`). If none remain active, close the Task (`state = Completed`). (Approve Tasks are normally already closed by the notifier.) |

**Teams / Flow-bot message bodies** (HTML, with the deep link anchored on the text "SPA"):
Submit — *"There are record(s) awaiting your review/approval. Please go to SPA for details."*;
Approve — *"Your record(s) have been finalized. Please go to SPA for details."*;
Reject — *"There are record(s) awaiting your revision. Please go to SPA for details."*

### 6.7 Deep links used in notifications (43 configuration variables)

| Record type | "Pending My Approval" link | "Finalized" link | "My … in Draft/Revision" link |
|---|---|---|---|
| Performance Indicator | `nrc_PerfIndsPendingMyApprovalLink` | `nrc_FinalizedPI` | `nrc_MyPerfIndsinDraftRevisionLink` |
| PI Result | `nrc_PIUpdatesPendingMyApprovalLink` | `nrc_FinalizedPIResults` | `nrc_MyPIUpdatesinDraftRevisionLink` |
| Enterprise Risk | `nrc_EntRisksPendingMyApprovalLink` | `nrc_FinalizedEntRisks` | `nrc_MyEntRisksinDraftRevisionLink` |
| Risk Update | `nrc_RiskUpdatesPendingMyApprovalLink` | `nrc_FinalizedRiskUpdates` | `nrc_MyRiskUpdatesinDraftRevisionLink` |
| Priority | `nrc_PrioritiesPendingMyApprovalLink` | `nrc_FinalizedPriorities` | `nrc_MyPrioritiesinDraftRevisionLink` |
| Positive Change Mgmt | `nrc_PCMPendingMyApprovalLink` | `nrc_FinalizedPCM` | `nrc_MyPCMinDraftRevisionLink` |
| Accomplishment | `nrc_AccomplishmentsPendingMyRevisionLink` | `nrc_FinalizedAccomplishments` | `nrc_MyAccomplishmentsinDraftRevision` |

Plus: `nrc_SUBMITURL`, `nrc_APPROVEURL`, `nrc_REJECTURL`, `nrc_PIDiscontinueURL`,
`nrc_PIProposeDiscontinueURL`, `nrc_PIDenyDiscontinueURL`, `nrc_EntRiskDiscontinueURL`,
`nrc_EntRiskDiscontinueProposeURL`, `nrc_EntRiskDenyDiscontinueURL`, `nrc_Flagforcarryoverflow`,
`nrc_UnflagPIflow`, `nrc_OpenPIchildrecordsbuttonflow`, `nrc_ApproverForQPRFlows`,
`nrc_SPAHomeLink`, `nrc_QPRHomeLink`, `nrc_SPModule`, `nrc_PMModule`, `nrc_SpaAppID`,
`nrc_QPRAppID`, `nrc_EnvironmentLink`, `nrc_UserGuideDocumentLink`, `nrc_FAQDocumentLink`.

Plus one **undefined** token: `nrc_SUBMITURL2`, referenced by `submitAccomplishmentCommand` as the
target of a second, single-record webhook but with no environment-variable definition in the export, so
its target is unknown (see §17.3).

Eight of the 43 have **no consumer anywhere in the export**: `nrc_EnvironmentLink`,
`nrc_FAQDocumentLink`, `nrc_PMModule`, `nrc_QPRAppID`, `nrc_QPRHomeLink`, `nrc_SPAHomeLink`,
`nrc_SpaAppID`, `nrc_UserGuideDocumentLink`; of those, `nrc_FAQDocumentLink` and
`nrc_UserGuideDocumentLink` also have no value at all. Only `nrc_ApproverForQPRFlows` (7 consumers) is
referenced more than once.

**Twelve of the 43 are not links at all — they are signed webhook endpoints.** Their default values
are HTTP-triggered Azure Logic Apps URLs on `prod-10.usgovtexas.logic.azure.us`, each carrying its own
`sig=` SAS signature in the query string: `nrc_SUBMITURL`, `nrc_APPROVEURL`, `nrc_REJECTURL`,
`nrc_PIDiscontinueURL`, `nrc_PIProposeDiscontinueURL`, `nrc_PIDenyDiscontinueURL`,
`nrc_EntRiskDiscontinueURL`, `nrc_EntRiskDiscontinueProposeURL`, `nrc_EntRiskDenyDiscontinueURL`,
`nrc_Flagforcarryoverflow`, `nrc_UnflagPIflow` and `nrc_OpenPIchildrecordsbuttonflow`. This is how the
ribbon buttons reach the flows: the command POSTs to the URL, and **the signature in the query string
is the only authorisation** — there is no Dataverse action, no bearer token and no per-user check on
the receiving side. The remaining 31 are 23 ordinary URLs and 8 non-URL settings.

> **Security finding — raise with OEDO before the rebuild.** Those twelve signatures are live
> credentials and they are stored in the solution export, so anyone holding a copy of the export can
> invoke Submit, Approve, Reject, Discontinue, Propose/Deny discontinuance, Flag/Unflag carry-over and
> Open-next-quarter against that environment, as any record, with no user identity attached. Treat them
> as compromised by distribution: rotate them, and do not carry this pattern forward. In the rebuild
> each of these becomes an authenticated endpoint under `/workflow/*` (Document 3 §4.1) that checks the
> caller's role and the record's state server-side — which is also what closes the gap in §8.2, where
> the only guard on these commands today is client-side view-name matching.

> **Rebuild guidance:** in the Python/React system these become internal route constants plus a
> single notification service; they must not remain 43 environment variables.

### 6.8 The Approval Queue (multi-step approval — designed but not wired into the QPR flow)

The `Approval Queue` entity supports an ordered, optionally parallel, optionally alternate approver
chain per record:

- **Regarding** — polymorphic lookup to any of 10 record types (Accomplishment, Enterprise Risk,
  Evaluations, Research Activity, Performance Indicator, PI Result, Positive Change Management,
  Priority, Priority Question, Risk Update).
- **Location** — a *second, independent* polymorphic lookup (`tei_location_lu`), accepting a
  **narrower set of exactly 5** record types: Accomplishment, PI Result, Positive Change Management,
  Priority, Risk Update. It is not a duplicate of **Regarding** and must not share its type domain.
  (Source relationships `nrc_regarding_accomplishment`, `nrc_regarding_pi`,
  `nrc_regarding_poschangemngmt`, `nrc_regarding_priority`, `nrc_regarding_risk`; Document 2 §9.4.)
- **Order** (integer ≥ 1) — the step number.
- **Role** — Author · Assignee/Interim Approver · Final Approval.
- **User** — the Active Directory user to notify.
- **Parallel?** — this step runs alongside another.
- **Alternate?** — this person is an alternate for another approver.
- **Valid** — validation flag held as free text, not a boolean (Document 2 §9.4). The only code that
  writes it is the `nrc_queueValidation` script, which sets the sentinel string `"Needs attention"` and
  clears it to `""`. **That script is never invoked**: it appears in the solution as a `<Library>`
  declaration with no `<Handler>` on any form, so the flag is never maintained in the as-built system.
  The companion `nrc_queueRowValidation` *is* wired — an `onsave` handler on the Approval Queue form —
  but it writes nothing, `nrc_valid` included (it is an unfinished debug stub; Document 3 §15.5.5). An
  HTML web resource `nrc_invalidwarningtext` displays the warning banner, which therefore never fires
  either.
  > **Rebuild guidance.** Do not treat `Valid` as migrated state — every legacy row carries whatever
  > value it was seeded with, which is almost certainly empty. Implement chain validation server-side
  > as part of saving an Approval Queue row, and derive the banner from that, rather than porting a
  > stored flag nothing keeps current.
- Status reasons — **seven** values, two of which share the label *Approved*: Pending (1, active) ·
  Rejected (875670002, active) · Contingent (875670003, active) · Approved (875670004, active) ·
  Complete (875670006, active) · Approved (2, inactive) · Closed (875670005, inactive). See
  Document 2 §2.4 `wf_approval_queue_status`.

On **Priority** creation, a queue row is auto-created with `Order = 1`, `Role = Author`,
`User = record creator`, `status = Complete`.

> **Rebuild guidance:** the Roles/Personas documents describe a two-tier chain (Intermediate Approver
> at office level → EDO Final Approver) and the Evidence Building lifecycle has both stages. The QPR
> lifecycle as shipped is single-stage. The rebuild should implement the **configurable chain** in the
> Approval Queue and make the single-stage case a chain of length 1. This is flagged in §17.

---

### 6.9 Complete cloud-flow inventory (all 53 Power Automate flows)

Every flow exported with the solution, with its trigger and top-level action count (a proxy for
complexity). Sections 6.2–6.6 describe the behaviour; this table guarantees none is overlooked.
The **Rebuild as** column states where the logic belongs in the Python service tier.


#### 1 · Submit / Approve / Return child flows (21)

*Rebuild as:* Domain service method on the record aggregate — one implementation parameterised by record type, not 21 copies (7 record types × Submit / Approve / Reject)

| Flow (display name) | Trigger | Actions |
|---|---|---|
| Accomplishment Approval Childflow | `manual` | 16 |
| Accomplishment Rejection Childflow | `manual` | 15 |
| Accomplishment Submission Childflow | `manual` | 14 |
| Enterprise Risk Approval Childflow | `manual` | 16 |
| Enterprise Risk Rejection Childflow | `manual` | 15 |
| Enterprise Risk Submission Childflow | `manual` | 14 |
| PI Result Rejection Childflow | `manual` | 15 |
| PI Result Submission Childflow | `manual` | 14 |
| PI Results Approval Childflow | `manual` | 16 |
| Performance Indicator Approval Childflow | `manual` | 15 |
| Performance Indicator Rejection Childflow | `manual` | 15 |
| Performance Indicator Submission Childflow | `manual` | 14 |
| Pos Change Mngmt Approval Childflow | `manual` | 16 |
| Pos Change Mngmt Rejection Childflow | `manual` | 15 |
| Pos Change Mngmt Submission Childflow | `manual` | 14 |
| Priorities Approval Childflow | `manual` | 16 |
| Priority Rejection Childflow | `manual` | 15 |
| Priority Submission Childflow | `manual` | 14 |
| Risk Update Approval Childflow | `manual` | 16 |
| Risk Update Rejection Childflow | `manual` | 15 |
| Risk Update Submission Childflow | `manual` | 14 |

#### 2 · Bulk command flows (3)

*Rebuild as:* Single bulk endpoint that loops the per-record service method inside one transaction (§4.2 of Document 3)

| Flow (display name) | Trigger | Actions |
|---|---|---|
| Bulk Approval | `manual` | 5 |
| Bulk Rejection | `manual` | 5 |
| Bulk Submission | `manual` | 5 |

#### 3 · Notification engine (5)

*Rebuild as:* Scheduled jobs + one notification service (Document 3 §7)

| Flow (display name) | Trigger | Actions |
|---|---|---|
| Check for new approvals | `Recurrence` | 13 |
| Check for new rejections | `Recurrence` | 10 |
| Check for new submissions | `Recurrence` | 10 |
| Check submission related tasks for completion | `Recurrence` | 2 |
| Notify user of new task for submission, approval, or rejection | `When a new task is set to approvals yes` | 14 |

#### 4 · Record-creation flows — document ID generation (11)

*Rebuild as:* Database trigger or service-layer hook that assigns the document identifier (§8.1)

| Flow (display name) | Trigger | Actions |
|---|---|---|
| ON ACCOMPLISHMENT CREATION | `When a row is added, modified or deleted in accomplishments` | 7 |
| ON ENT RISK CREATION | `When a row is added, modified or deleted` | 9 |
| ON GOAL CREATION | `When a row is added, modified or deleted` | 1 |
| ON OBJECTIVE CREATION | `When a row is added, modified or deleted` | 5 |
| ON PERF GOAL CREATION | `When a row is added, modified or deleted` | 1 |
| ON PERF IND CREATION | `When a row is added, modified or deleted` | 6 |
| ON PI RESULT CREATION | `When a row is added, modified or deleted` | 5 |
| ON POS CHANGE MNGMT CREATION | `When a row is added, modified or deleted in positive change mgmt table` | 7 |
| ON PRIORITY CREATION | `When a row is added, modified or deleted in Priorities Updates` | 11 |
| ON RISK UPDATE CREATION | `When a row is added in Risk Updates` | 3 |
| ON STRATEGY CREATION | `When a row is added, modified or deleted` | 1 |

#### 5 · Discontinuance, carry-over and quarter flows (11)

*Rebuild as:* Command endpoints under `/workflow/*` (Document 3 §4.1)

| Flow (display name) | Trigger | Actions |
|---|---|---|
| Deny Ent Risk Discontinuance | `manual` | 3 |
| Deny PI Discontinuance | `manual` | 3 |
| Discontinue PI | `manual` | 3 |
| Discontinue Risk | `manual` | 3 |
| Ent Risk Discontinue Proposed | `manual` | 3 |
| Flag for carry over | `manual` | 3 |
| Last Quarter link for Risk Updates | `When a Risk Update is added` | 7 |
| Move Risk Leads and Contacts from Ent Risks to Risk Updates — do not rebuild (reads deleted Enterprise Risk columns) | `manual` | 2 |
| Open PI child records for next quarter | `manual` | 7 |
| PI Discontinue Proposed | `manual` | 3 |
| Unflag PI from carry over | `manual` | 3 |

#### 6 · One-off data-migration flows — do not rebuild (2)

*Rebuild as:* **Not rebuilt** — one-off backfills already applied to production data

| Flow (display name) | Trigger | Actions |
|---|---|---|
| TEMP - back fill rejections | `manual` | 2 |
| TEMP Back fill old risk data into new columns | `manual` | 4 |

**Total: 53 flows.** Flow definition files are under `Core_1_0_0_67_managed/Workflows/`; each
file name is the display name with spaces removed plus the flow GUID.

## 7. Record lifecycles (state machines)

Every business record has a two-level state: **State** (Active / Inactive) and **Status Reason**.

### 7.1 QPR performance records — Accomplishment, Positive Change Management, Priority, Risk Update

| Status Reason | State | Meaning |
|---|---|---|
| Draft | Active | editable by owner |
| Pending approval | Active | locked for the submitter, visible to the approver |
| Revision | Active | returned; editable by the submitter again |
| Finalized | Inactive | approved and locked |
| Cancelled/closed | Inactive | withdrawn |

Transitions: `Draft → Pending approval` (Submit) · `Revision → Pending approval` (Resubmit) ·
`Pending approval → Finalized` (Approve) · `Pending approval → Revision` (Return).

### 7.2 PI Result (`nrc_PerformanceIndicatorFiscalYear`)

Same five states but with **different numeric codes**: Draft, Pending approval, **Revision**,
Finalized, Cancelled/closed. Plus the **re-open** transition `Finalized → Draft` performed by the
"Open PI child records for next quarter" command, gated on the related Fiscal Year record's `Fiscal Year`
value equalling `formatDateTime(utcNow(),'yyyy')` — i.e. the current **calendar** year. The flow also
initialises a `Current qtr` variable (month ≥ 10 → Q1, ≥ 7 → Q4, ≥ 4 → Q3, else Q2 — an October-start
federal fiscal quarter) that no action ever reads; it is dead code and does not affect the gate.

### 7.3 Performance Indicator

| Status Reason | State |
|---|---|
| Draft | Active |
| Pending approval | Active |
| Revision | Active |
| Finalized | Inactive |
| Cancelled/closed | Inactive |
| Discontinued | Inactive |
| **Versioned/revised** | Inactive |

Plus an independent **Indicator Status** field: Active · Discontinued · Under Development ·
Pending Discontinue.

Discontinuance sub-flow:
`Propose` → Indicator Status = *Pending Discontinue* (record stays finalized) →
EDO `Discontinue` → Indicator Status = *Discontinued*, state Inactive, status *Discontinued*
**or** EDO `Deny` → Indicator Status = *Active*, state Inactive, status *Finalized*.

Revision sub-flow: creating a new PI with `Change Type = Revised` and a `PI being revised` pointer
sets the **previous** PI to Indicator Status = *Discontinued*, state Inactive,
status = *Versioned/revised*.

### 7.4 Enterprise Risk

| Status Reason | State |
|---|---|
| Draft | Active |
| Pending approval | Active |
| Revision | Active |
| Finalized | Inactive |
| Closed/cancelled | Inactive |
| Discontinued | Inactive |

Plus **Risk Status**: Under Development · Active · Pending Discontinue · Discontinued, driven by the
same Propose / Discontinue / Deny commands.

### 7.5 Evidence Building records — Priority Question, Evaluations, Research Activity

| Status Reason | State |
|---|---|
| Draft | Active |
| **Pending Intermediate Approval** | Active |
| **Pending Final Approval** | Active |
| Revision | Active |
| Finalized | Inactive |
| Cancelled | Inactive |

### 7.6 Workflow audit records

- **Submission** — Pending (Active) → Complete (Inactive). Carries `Approved?`, `Returned?`, `Resubmission?`.
- **Approval** — Active → Inactive.
- **Rejection** — Pending changes (Active) → Resubmitted (Inactive).
- **Approval Queue** — Pending · Rejected · Contingent · Approved · Complete (all Active) →
  Approved · Closed (Inactive). *Approved* is two distinct values, one Active and one Inactive
  (Document 2 §2.4).
- **Task** — Open → Completed.

### 7.7 Reference data

All reference tables (Goal, Objective, Strategy, Fiscal Year, Office, Division, Organization,
Business Line, Product Line, Product, Major Programs, Contributing Programs, Definition,
External Factor, Office Goal, Performance Goal, Signposts, Key Areas) plus Action/Measure use the simple
Active / Inactive pair.

### 7.8 Planned Measure / Milestone / Deliverable

In progress (Active) · Met (Active) · Unmet (Active) · Cancelled/closed (Inactive).

---

## 8. Business rules catalogue

### 8.1 Identifier generation (server-side, on create)

| Record | Pattern | Algorithm |
|---|---|---|
| **Performance Indicator** (new) | `{BusinessLine.PrefixCode}-{Office.Code}-{n}` | `n` starts at 0 and increments until no existing PI has that exact Indicator ID |
| **Performance Indicator** (revised, previous also revised) | `{previous ID with trailing counter stripped}-{counter+1}` | parse the integer after the last `-` of the previous ID, strip it, increment, re-append |
| **Performance Indicator** (revised, previous not revised) | `{previous ID}-1` | |
| **Performance Indicator** (revised, previous was CBJ/APPR but the new one is not) | `{BusinessLine.BRCode}-{Office.Code}-{n}` | regenerated from scratch with a uniqueness loop |
| **Performance Indicator** (revised, previous was Agencywide office but the new one is not) | `{BusinessLine.BRCode}-{Office.Code}-{n}` | same |
| **PI Result** | = parent Performance Indicator's Indicator ID | copied verbatim into `nrc_title` |
| **Enterprise Risk** | `{BusinessLine.PrefixCode}-{Office.Code}-{n}` | uniqueness loop on Risk ID |
| **Risk Update** | = parent Enterprise Risk's Risk ID | copied into `Entry ID` |
| **Accomplishment** | `ACC-{Office.Code}-{totalAccomplishmentCount+1}` | global count |
| **Positive Change Management** | `PCM-{Office.Code}-{countOfIdsStartingWithThatPrefix+1}` | prefix-scoped count |
| **Priority** | `{BusinessLine.PrefixCode}-{Office.Code}-{countOfIdsContainingThatPrefix+1}`; for multi-office priorities each related Office's Prefix Code is appended as `"{prefix} - "` | |
| **Definition** | `NRC-{0001}` | platform auto-number, 4-digit sequence |
| **Goal** display name | `"{Sequence}: {Goal Text}"` | recomputed whenever Goal Text changes |
| **Objective** display name | `"{Category} {Title}"` where Category = `Safety and Security Objective {last digit}:` (sequence starts with 1) · `Organizational Health Objective {last digit}:` (2) · `Stakeholder Confidence Objective {last digit}:` (3) | recomputed when Title changes |
| **Strategy** display name | `"{Sequence} {Title}"` | recomputed when Title changes |
| **Performance Goal** display name | `"{Sequence} {Title}"` | on create |
| **Signposts / Key Areas** | `Name` = `Title` | on create |

> **Note on concurrency:** the as-built uniqueness loops (up to 60 iterations, 1-hour timeout) are
> race-prone. The rebuild must generate these identifiers inside the same database transaction as the
> insert, from a counter row drawn under SQLite's write lock (`BEGIN IMMEDIATE` — Doc 2 §12.5). Flagged
> in §17.

### 8.2 Field visibility / requirement rules (from the 40 business rules + 52 scripts)

| Rule | Entity | Behaviour |
|---|---|---|
| **Range or Regular Display Rules** | PI Result | If the parent PI's Measure Type = **Range**: for Q1–Q4 and Annual show *Minimum Target, Maximum Target, Lower Operator, Upper Operator* and hide *Target, Operator*. Otherwise show *Target, Operator* and hide the four range fields. |
| **Check for Q1/Q2/Q3/Q4/Annual Not Applicable** | PI Result | When the quarter's *Not Applicable* box is ticked: clear that quarter's Results value and **lock** the field. When unticked: unlock it. |
| **Show Mitigating Remarks** | PI Result | Shows *Mitigating Remarks* when *Met or Unmet* = No (the rule's own branch label is *If "Unmet"*); hides it otherwise. **Rule is deactivated in the shipped solution (StateCode 0 / StatusCode 1)** — confirm with OEDO whether the rebuild should restore it. |
| **Show/hide comments** | PI, PI Result, Enterprise Risk, Risk Update, Priority, PCM, Accomplishment | The "COMMENTS REGARDING SUBMISSION" field is shown only while the record is *Pending approval* or *Revision*; hidden in Draft and Finalized. Each entity uses its own status codes. |
| **Hide Approver Comments field on Draft Stage** | Priority | Same intent, Priority-specific codes. |
| **Resubmission Comments** | Accomplishment | Same intent; labelled "NOTES FOR RESUBMISSION". |
| **Approver Comments/Revisions hidden in Draft** (3 rules) | Priority Question, Evaluations, Research Activity | *Approver Comments/Revisions* is hidden while `statuscode = 1` (Draft) and visible in every other status. |
| **Default Approval Stage to 1** (2 rules) | Priority Question, Research Activity | *Approval Stage* defaults to the integer 1 on create. |
| **Change type revised** | Performance Indicator | When *Change Type = Revised*: show **PI being revised** and make it required; otherwise hide it and clear the requirement. |
| **Show 'Other Data Source'** | Performance Indicator | Visible only when *Data Source = Other*. |
| **Is risk accepted** | Risk Update | When "risk accepted" is ticked → *ACT (Proposed Risk Response) QPR Description* is **not required**; when unticked → **required**. |
| **Ind statuses** | Performance Indicator | Conditional visibility on the Indicator Status field (rule currently deactivated). |
| **show perf goal / hide perf goal** | Performance Indicator | Performance Goal lookup shown only for a specific Report Level. |
| **Default reporting person / contact person to created by** (2 rules) | PI Result, Accomplishment | PI Result *Reporting Person* and Accomplishment *Contact Person* default to the creating user (`createdby`). |
| **Default Approval order** | Evaluations | Approval Order Stage defaults to 1. |
| **Default entry count to 0** | Enterprise Risk | Entry Count defaults to "0". |
| **Default entry sequence count to zero** | Performance Indicator | Entry count defaults to 0. |
| **Add 'Yes' to Related PI Required Field** | Accomplishment | Sets the hidden "Related PI Required" text to "Yes" — makes the related-PI sub-grid mandatory. |
| **Add 'Yes' to PI Required Field when Title has data** | Priority | Same mechanism. |
| **Business Unit** (7 rules) | Accomplishment, Enterprise Risk, PI, **PI Result**, PCM, Priority, Risk Update | Sets the owning business unit to **EDO** while `status = Pending approval`, and to the **root / agency-wide** business unit for every other status. A status-driven ownership transfer, not a report-level rule — it is what makes a submitted record visible to its approver. Full detail, including the per-entity status codes, in Doc 2 §13.4. |
| **Set Primary Name column to Title** | Signposts, Key Areas | Copies Title into Name. |
| **Prevent Save** (script) | Performance Indicator | Blocks save with the message *"You do not have the necessary priviledges to create this record with this field value."* when a non-EDO user sets Report Level to the restricted value **or** Agency Wide Support Level = *Agency*. **Registered with `enabled="false"`, so it does not run in the shipped system** — the restriction is unenforced today and must be implemented server-side (Doc 2 §13.3). |
| **quarterlyFields** (script) | PI Result | Shows/hides per-quarter Raw Data, At-Fault Office and At-Fault Business Line controls based on which quarters are selected; hides a whole section for Qualitative indicators. |
| **showSpecificQuarterFields / hideQsections** (scripts) | PI Result | Companion quarter-section visibility logic. |
| **Character counters** (14 scripts) | Ent. Risk Description, PCM Description, PI Description, PI Results Calculation, Accomplishment Description, Q1–Q4 + Annual Remarks, Likelihood Description, Impact Description, Current-Risk-Control-Efforts, Go-Forward-Control-Plans | Live "characters remaining" feedback against the documented limits. |
| **disableSubgrid / hideSubgrid / getsubgridcount** (scripts) | several | Read-only or hidden sub-grids depending on record state; count-based validation. |
| **setLookupFieldToCurrentUser** (script) | several | Defaults a user lookup to the signed-in user. |
| **lookupFilter / newLookupFilter / setSubgridLookupFiltering / objectiveSubgridFilter** (scripts) | several | Cascading filters — e.g. Objectives filtered by the selected Goal. |
| **checkUser** (script) | Approval Queue | Validates the chosen final approver: when *Role* = `875670003` (Final Approval) it retrieves the selected user and, if `nrc_finalapprovercapabilities` is false, sets the notification *"Cannot be final approver, user has insufficient roles."* on the User lookup. |
| **displayUserRole** (script) | — | **No-op debug leftover.** Loaded as a library on one form with no handler registration, and its only DOM line is commented out — it writes the user's roles to the console and nothing else. Do not port (Doc 3 §15.5.5). |
| **refreshSave** (script) | several | Forces a form refresh after save so server-computed values (IDs) appear. |
| **accRevIcon** (+ `revisionIcon` image) | **7 entities** — Accomplishment, Enterprise Risk, PI, PI Result, PCM, Priority, Risk Update | Grid cell renderer registered as the `statuscode` image provider on all seven *"MY … in Draft/Revision"* views: when status = *Revision* it draws the `nrc_revisionIcon` glyph with tooltip *"Revisions requested."* and sets the row background to `#ffcd8f`. Detail in Doc 3 §15.5.5. |
| **outcomebased / showCrossCutting / defaultQuarterChoices** (scripts) | several | Outcome-based indicator UX; cross-cutting section visibility; default quarter selection. |
| **taskFormAprrovals** (script) | Task | Task form behaviour for approval tasks. |

> **What is actually switched on.** A sweep of every form-script registration and every process
> state in the solution found that a substantial part of this layer is inert, and the rebuild should
> not infer behaviour from a script's existence. Verified totals: **8 handler registrations carry
> `enabled="false"`** (`nrc_preventSave` and `nrc_hideWarning` and `cr9de_outcomebased` on Performance
> Indicator; `nrc_hideWarning` and `nrc_getsubgridcount` on Enterprise Risk; `nrc_getsubgridcount` on
> Accomplishment; `nrc_objectiveSubgridFilter` on External Factor; `nrc_disableSubgrid` on Risk
> Update); **7 scripts are declared as a `<Library>` on a form but bound to no `<Handler>` at all**
> (`nrc_queueValidation`, `nrc_refreshSave`, `nrc_displayUserRole`, `nrc_checkImpactedStrategy`,
> `nrc_ImpactDescrCharCounter`, `nrc_LikeDescrCharCounter`, `nrc_PCMDescrCharCounter`); and of the 94
> processes, **2 business rules** (*Show Mitigating Remarks*, *Ind statuses*) and **1 business process
> flow** (*Approval Process (PI Results)*) are not activated. Every one of these is marked as such in
> its own row here and in Document 3 §15.5. The consequences worth carrying into design are recorded
> where they bite: the restricted-creation rule is enforced nowhere (§8.2 *Prevent Save*), and the
> Approval Queue `Valid` flag is never written (§6.8).

### 8.3 Referential-integrity validation (Strategic Plan hierarchy)

Six scripts enforce that the Goal → Objective → Strategy chain stays consistent, by comparing
**sequence-number prefixes**:

| Script | Check | Message shown |
|---|---|---|
| `checkObjective` | Objective.Sequence starts with Goal.Sequence | *"This Objective does not fall under the Goal selected above."* |
| `checkStrategy` | Strategy.Sequence starts with Objective.Sequence | *"This Strategy does not fall under the Objective selected above."* |
| `checkRelatedObjective` | same check on the "Related Objective" field | same |
| `checkRelatedStrategy` | same check on the "Related Strategy" field | same |
| `checkImpactedObjective` | same check on Enterprise Risk's "Impacted Objective" | same |
| `checkImpactedStrategy` | same check on Enterprise Risk's "Impacted Strategy" | same |

### 8.4 Auto-fill rules

| Rule | Trigger | Effect |
|---|---|---|
| **Autofill Prev PI** (`nrc_autofillPI`) | Performance Indicator — "PI being revised" selected | Copies from the previous PI: Strategic Goal, Objective, Strategy, Description, Title, Report Level, Contact Person, Owner, Accountable Organization, Agency Wide Support Level, Data Source, Measure Type, Indicator Type, Units, Results Calculation, Lead Business Line, Major Program, Contributing Program, Lead Product Line, Product, Lead Office, Division |
| **Acc Fill Strategic From PI** (`nrc_accFillStratFromPI`) | Accomplishment — "Primary Related PI" selected | Copies Strategic Goal, Strategic Objective and Strategy from the PI (the User Guide notes these remain editable afterwards) |
| **Last Quarter link for Risk Updates** | Risk Update created | Copies the previous quarter's Inherent Likelihood/Consequence and Residual Likelihood/Consequence |
| **Move Risk Leads and Contacts** | on-demand data-fix job | Copied Risk Lead and Contact Person from every Enterprise Risk down to all its Risk Updates. **Dead code in v1.0.0.67** — the flow still reads `_nrc_contactperson_value` / `_nrc_risklead_value` from `nrc_enterpriserisks`, columns that no longer exist; do not rebuild. |

### 8.5 Rollups and calculated columns

| Table.Column | Kind | Definition |
|---|---|---|
| Goal.Objective Count | Rollup | COUNT of related Objectives |
| Goal.Strategy Count | Rollup | COUNT of related Strategies |
| Goal.Indicators Count | Rollup | COUNT of related Performance Indicators |
| Goal.Risk Count | Rollup | COUNT of related Enterprise Risks |
| Office.Display Name | Calculated | verbatim copy of `Office` (`nrc_office`) — unconditional, no composition |
| Product.(INTERNAL) Product Name | Calculated | verbatim copy of `Product` (`nrc_product`) — unconditional, no composition |
| Business Line.Test | Calculated | verbatim copy of `Business Line` (`nrc_businessline`) — unused duplicate (`nrc_test`), not carried forward |
| PI Result.Data Type | Calculated | Quantitative if PI Measure Type = Quantitative; Qualitative if Qualitative **or** Range |
| PI Result.Indicator Type | Calculated | **not a copy** — two branches only: if the parent PI's Indicator Type is *Outcome* (875670001) **or** 875670002, the column is set to legacy option value **875670002, which is not a member of the global `nrc_indicatortype` option set**; every other parent value (Output, Process, Input, Efficiency, Contextual) falls through to **Output (875670000)**. The column is evaluated on read and never stored (`ValidForCreateApi 0` / `ValidForUpdateApi 0`), so no stored row carries the orphan code — the risk is that a faithful rebuild would *emit* it. See §17.3 item 19. |
| PI Result.(INTERNAL) Measure Type | Calculated | copied from the parent PI's Measure Type — drives the Range display rule |
| PI Submission/Approvals.Duration | Calculated | minutes between two stage timestamps |
| Enterprise Risk.Enterprise Risk Title | Calculated | formula body **not present in the export** (no `Formulas/*.xaml` file) — recover the expression from the live environment |

### 8.6 Editing / locking rules (stated in the User Guide)

> *"Records can be edited at any time prior to submission for approval. Once submitted, edits are
> restricted."*

> *"Submitters can edit any of their own performance related data in the Draft stage; once records are
> submitted, they are no longer open for edits and will be view-only."* (System Architecture Document)

> *"Submitters have the ability to delete any performance related data they own in the Draft stage.
> Records that have been submitted, or are not in their ownership, will not be able to be deleted."*

> *"Read/write users of the system will have the ability to view and update information, but cannot
> delete a risk, performance indicator, or priority. EXCEPT: Office level performance indicators and
> Non-PSAT risks, which can be removed when they are no longer needed."*

> *"Submission is only available on the “MY” view, not the default"* (User Guide, Screenshot 2 note — no terminal period in the source)

### 8.7 Quarterly set-up rule

> *"Enable a function for the set up of each quarter where the previous data is not available for edit,
> and the new quarter is ready to input the information."*
> (`Strategic Planning and Performance Management Overview`)

Implemented by the **Open PI child records for next quarter** command (§6.2).

### 8.8 Guidance text present in the solution but not enforced

**Planned Measures scope.** Source web resource `nrc_measures_text` carries the sentence
*"Planned Measures Milestone, or Deliverables only apply to Performance Indicators under Strategic
Goals 2 and 3"*. The resource is not placed on any form, so the rule is documentation only in the
legacy system; confirm with OEDO whether the rebuild should enforce it as validation or keep it as
guidance — flagged in §17.

---

## 9. Reporting and analytics — complete dashboard specification

Source: `Performance Review Dashboard DEV DATA REPOINT.pbix`. 19 pages, 473 visual containers.

### 9.1 Semantic model (41 tables)

**Fact tables:** PI Result · Risk Update · Accomplishment · Positive Change Management · Priorities ·
Agency Wide Indicators.
**Dimension tables:** Performance Indicator · Enterprise Risk · Goal · Objective · Strategy ·
Fiscal Year · Reporting Period · Date · Office · Division · Business Line · Product Line · Product ·
Major Program · Contributing Program · Primary Contributing Program · Accountable Organization ·
Report Level · Stage · User.
**Role-playing dimensions:** Lead BL · Lead PL · Lead Office · Reporting Office · PI Reporting Periods.
**Bridge tables:** Performance Indicators' Contributing Offices · Positive Change Managements'
Contributing Offices · Priorities' Contributing Offices · Risks' Contributing Offices ·
Risks' Related Indicators.
**Utility tables:** Refresh Times and History (Last Refresh in EST, Last Refresh in EDT, Next Refresh) ·
View (Toggle) · Images · Terms (four static label constants — Inherent / Residual / Likelihood /
Consequence; no relationships, bound by no visual) · QPR?.

The 41 names above are exactly the 41 business tables in the decompressed model and the 41 nodes of the
`All tables` model diagram (the remaining 61 model tables are Power BI's auto-generated
`LocalDateTable_*` / `DateTableTemplate_*`). One dangling reference survives: the table
"SELECT AN INDICATOR TO VIEW FULL PROFILE" on the Performance Indicator Dashboard carries a
visual-level filter on `(Deprecated)[Fiscal Year]`, an entity that no longer exists in the model — drop
it in the rebuild rather than reproduce it. `(Deprecated)` is therefore **not** a table in the shipped
model, which is why the total is 41.

Report-level filter: `Reporting Period.Reporting Period ≠ null`.

**Model-wide record filter.** Before any page filter is applied, the semantic model drops every closed
record: the Power Query for Enterprise Risk filters `Stage <> "Closed/cancelled"` and those for
Performance Indicator, PI Result, Positive Change Management, Priorities, Risk Update and
Accomplishment filter `Stage <> "Closed"`. Each query first normalises the status label —
"Cancelled/closed" → `Closed`, "Pending approval" / "Pending intermediate approval" / "Pending final
approval" → `Pending` — so the `Stage` dimension has exactly five values: Closed · Draft · Revision ·
Finalized · Pending. Every analytic view in Document 2 §14 must therefore carry
`WHERE status_reason NOT IN ('closed','cancelled_closed','closed_cancelled')`; serving the dashboards
straight from the operational tables without it will change every count on pages 1–18.

### 9.2 Global slicer bar (present on almost every page)

Lead Business Line · **Reporting BL** · Lead Product Line · Fiscal Year · Quarter · Lead Office
(**Reporting Office** on the Agencywide Indicator page) · Division · Major Program · Contributing
Program (bound to `Primary Contributing Program[Program]`) · Report Level — **ten** filter slicers —
plus a **View Toggle**, **Clear Filters**, **Last Refreshed** and **Next Refresh** cards.

Note: "Lead Business Line" (sync group `Business Line`) and "Reporting BL" (sync group `BL`) are two
independent slicers bound to the *same* column `Lead BL[BL]`; they filter independently and both appear
on pages 2–12 and 16–18. Strategic Planning Home carries only the first, plus a Strategic Goal slicer
and no Division slicer; PI Profile has no View Toggle. Confirm with OEDO whether the duplicate BL
slicer is intentional before reproducing it.

Standard slicer exclusions, applied consistently:
- Office slicer excludes `null`, `Agencywide`, `N/A`
- Fiscal Year slicer excludes 2027–2030 and `null` (Historical Trends also excludes 2026)
- Business Line / Product Line / Major Program / Contributing Program slicers exclude `null`

### 9.3 Page-by-page specification

| # | Page | Key visuals |
|---|---|---|
| 1 | **Strategic Planning Home** | Goal slicer + Goal card; Objectives table (Objective Number, Objective Title); KPI cards: STRATEGIES (count of Strategy Title), ENTERPRISE RISK(S), PERFORMANCE INDICATOR(S) (distinct count of Indicator ID), ACCOMPLISHMENT(S), CHANGE MANAGEMENT(S); a **natural-language Q&A visual ("SMART QUERY")**; link button "Go to SPA Application" (external `WebUrl`); the Goal Tooltip page exists but is **orphaned** — no visual on this page binds it |
| 2 | **Performance Management Home** | KPI cards: PRIORITIES, POSITIVE CHANGE MANAGEMENT ITEMS, ACCOMPLISHMENTS; donut *COUNT OF RISKS BY PSAT* (filtered to Mitigation Type = **Inherent**); donut *PERFORMANCE INDICATORS BY RESULT* (distinct PIs by Result; excludes IDs starting with `AW`); pie *PERCENTAGE DISTRIBUTION* of PI Results; six navigation arrows → Accomplishments, PCM, Priorities, Heatmap, Risk, PI dashboards; link button "Performance Management Application" (external `WebUrl`) |
| 3 | **Historical Trends** | Line chart: risk count by Reporting Period, series = PSAT?; line chart: PI Result counts by Reporting Period, series = Result. Both exclude null and Annual Reporting Periods; the PI trend also excludes `No data` results, FY24 Q3/Q4 and Indicator IDs starting with `AW`, and carries a Count-of-`Result` measure filter; the risk trend additionally excludes null `Enterprise Risk[DEPRECATED PSAT?]` |
| 4 | **Accomplishments Dashboard** | Cards: TOTAL ACCOMPLISHMENTS, CBJ/APPR ACCOMPLISHMENTS (Report Level = CBJ/APPR), BL/PL ACCOMPLISHMENTS (Report Level = BL/PL); HISTORICAL TREND line chart (excludes Annual); selectable Accomplishment table driving a DESCRIPTION card |
| 5 | **Positive Change Management Dashboard** | HISTORICAL TREND line chart; cards: POSITIVE CHANGE MANAGEMENT ITEMS, ACCOMPLISHMENTS; ID + Title table driving a DESCRIPTION card |
| 6 | **Priorities Dashboard** | Cards: GOAL 1 PRIORITIES, GOAL 2 PRIORITIES, GOAL 3 PRIORITIES (filtered by Goal = 1/2/3), TOTAL COUNT; HISTORICAL TREND by Fiscal Year; table PRIORITIES BY RANK AND DESCRIPTION |
| 7 | **Risk Dashboard** | Donut COUNT OF RISKS BY PSAT? (**Inherent**); pie PERCENTAGE DISTRIBUTION (**Residual**); HISTORICAL TREND line (distinct Enterprise Risks by Reporting Period, series = Enterprise Risk `DEPRECATED PSAT?` (legacy `nrc_risktype`) — a column deleted from the model, so the legend is blank as shipped; the rebuild should use Risk Update `psat`. Excludes Annual); navigation buttons → PSAT / Non-PSAT / Agencywide / Heatmap |
| 8 | **PSAT Risks Dashboard** | Page filter `PSAT? = PSAT`. Selectable table (Risk ID, Risk Title) driving cards: Inherent Likelihood, Inherent Consequence, Residual Likelihood, Residual Consequence, RISK DESCRIPTION, CURRENT RISK RESPONSE, PROPOSED RISK RESPONSE. Drill-through button → QPR Risk View |
| 9 | **Non-PSAT Risks Dashboard** | Identical, page filter `PSAT? = Non-PSAT` |
| 10 | **Agencywide Risks Dashboard** | Identical, page filter `Enterprise Risk.Agencywide = true` |
| 11 | **Heatmap** | Page filter `PSAT? = PSAT`; Mitigation Type slicer (Inherent / Residual). **Nine scatter charts**, one per risk-level cell — LL, LM, LH, ML, MM, MH, HL, HM, HH — each plotting the in-cell placement coordinates X/Y by Risk ID — the cell a marker lands in is fixed by that visual's own `Risk Level` filter, not by X/Y; the nine cells have **no click action** — each has only a canvas tooltip bound to the Heatmap Tooltip page (Risk ID + Risk Title); the eight axis-label shapes (LOW/MEDIUM/HIGH consequence, the three likelihood labels and the two rotated axis titles) are inert (`visualLink.type = PageNavigation` with no `navigationSection`) and exist only to host the risk-scale hover definitions (§9.4.1); the page's only real navigation is the top-left **Back** button and a bottom-right button → **Heatmap and List**. **View Quadrant is a hidden drill-through page keyed on Risk Update ID**, reached by right-clicking a plotted risk point, not by clicking a cell |
| 12 | **Heatmap and List** | Same nine-cell heatmap (categorised by Risk Index) plus a side table of Risk Index / Risk ID / Risk Title; title textbox "PSAT RISK HEATMAP" |
| 13 | **Heatmap Tooltip** | Tooltip page (600×100): Risk ID + Risk Title table |
| 14 | **View Quadrant** | **Drill-through target**, keyed on `Risk Update[ID]`: scatter of X/Y by Risk ID plus Consequence Text and Likelihood Text cards, with a bottom-left button back to Heatmap. Nothing in the report navigates *to* this page — it is reached by drill-through from a risk record. Page filters as shipped: `Risk Update.DEPRECATED PSAT? = PSAT` (always blank — admits nothing) **and** `Risk Update.ID = AW-MULTI-0`, a hard-coded single risk. Both are as-built defects; the rebuild's cell-zoom endpoint must take the risk level and the selected risk as parameters |
| 15 | **QPR Risk View** | The QPR meeting slide for one risk: Risk ID and Title, Risk Description, Associated Performance Indicators, Inherent Likelihood/Consequence descriptions, Residual Likelihood/Consequence descriptions, Current Risk Response, Proposed Risk Response, Risk Monitoring, Informed Monitoring, Budget Strings, Accepted?, with **colour-coded left/right indicator bars** driven by the Likelihood/Consequence colour columns — the **right** bar is this quarter's level, the **left** bar last quarter's (Document 2 §14.5), so the pair shows quarter-over-quarter movement |
| 16 | **Performance Indicator Dashboard** | Page filter excludes Indicator IDs starting with `AW`. Clustered column HISTORICAL TREND (Result counts by Reporting Period, excludes `No data`); pie PERCENTAGE DISTRIBUTION; donut PERFORMANCE INDICATORS BY RESULT (In Standard / Out of Standard / No data); table "SELECT AN INDICATOR TO VIEW FULL PROFILE" (Indicator ID, Title, sum of Reported Results — i.e. the count of periods reported, not a sum of measured values) with drill-through to PI Profile; button → Agencywide Indicator Dashboard — this page is itself a drill-through target keyed on `PI Result[Indicator ID]` |
| 17 | **Agencywide Indicator Dashboard** | Matrix: rows = Product Line + Performance Indicator, columns = Office, values = Results — the legacy display string `"{result value} {operator} {target}"`, aggregated with a text MAX; the cell colour comes from the separate `Status` column — with conditional background: `No data` → grey `#e6e6e6`, `Out of Standard` → red `#de6a73`, `In Standard` → green `#B8E6BB` |
| 18 | **PI Profile** | Drill-through target keyed on `Performance Indicator[Title]`. Cards: Indicator Headline, INDICATOR DESCRIPTION, OWNER, CONTACT PERSON, RESULTS CALCULATION, OPERATOR, UNITS, LAST QUARTER REMARKS; multi-row card CONTRIBUTING OFFICES; line chart HISTORICAL TREND plotting Target, Maximum Target, Minimum Target and Result Value by Reporting Period |
| 19 | **Goal Tooltip** | Tooltip page (320×240): Goal Title card. **Unreferenced** — no visual in the report binds this page as a canvas tooltip; the only wired tooltip page is Heatmap Tooltip (19 bindings on Heatmap, Heatmap and List and View Quadrant) |

Both home-page link buttons carry a byte-identical URL — app
`d419405f-d648-ee11-be6d-001dd8097981`, `pagetype=dashboard`,
`id=eb13ebda-7fbf-ed11-83ff-001dd8098656`, which is the **My To-do's** dashboard. Only the captions
differ; there is one destination, not two apps. If the rebuild should route the two home pages to two
different workspaces, that is a **[NEW]** decision.

#### 9.3.1 Page navigation map (as-built)

| Page | Return control | Other navigation / Clear Filters |
|---|---|---|
| Strategic Planning Home | — | external app link; Clear Filters |
| Performance Management Home | — | six navigation arrows → Accomplishments, PCM, Priorities, Heatmap, Risk Dashboard, PI Dashboard; external app link; Clear Filters |
| Historical Trends | — | Clear Filters only |
| Accomplishments · PCM · Priorities · PSAT Risks · Non-PSAT Risks · Agencywide Risks · Agencywide Indicator · PI Profile | top-left `Back` (returns to caller) | Clear Filters |
| Risk Dashboard | top-left `PageNavigation` → Performance Management Home | buttons → PSAT / Non-PSAT / Agencywide / Heatmap; Clear Filters |
| Heatmap | top-left `Back` | bottom-right `PageNavigation` → Heatmap and List; Clear Filters |
| Heatmap and List | top-left `PageNavigation` → Heatmap | **no Clear Filters** |
| View Quadrant | bottom-left `PageNavigation` → Heatmap | **no Clear Filters** |
| QPR Risk View | bottom-left `Back` | **no Clear Filters** |
| Performance Indicator Dashboard | top-left `PageNavigation` → Performance Management Home | button → Agencywide Indicator; drill-through button; Clear Filters |
| Heatmap Tooltip · Goal Tooltip | — | none |

`Back` returns to whichever page invoked the current one; the explicit `PageNavigation` buttons always
land on their fixed target. Clear Filters (`ClearAllSlicers`) is present on 14 of the 19 pages — not on
Heatmap and List, View Quadrant, QPR Risk View or the two tooltip pages. The `Back` buttons on
Accomplishments, PCM, Priorities, PSAT / Non-PSAT / Agencywide Risks, Agencywide Indicator and
PI Profile retain a stale `navigationSection` pointing at Performance Management Home even though
`type = "Back"` makes them return to the caller; drop the stale target in the rebuild.

### 9.4 Risk colour model (exact hex values from the report)

| Semantic | Level value | Hex |
|---|---|---|
| Low likelihood / consequence (inherent) | 1 ≤ level < 2 | `#ABE6AC` |
| Medium (inherent) | 2 ≤ level < 3 | `#e8d166` |
| High (inherent) | 3 ≤ level < 4 | `#de6a73` |
| Low (residual) | 1 ≤ level < 2 | `#8ADE9E` |
| Medium (residual) | 2 ≤ level < 3 | `#E8D166` |
| High (residual) | 3 ≤ level < 4 | `#de6a73` |
| Indicator-bar Green / Yellow / Red | — | `#B7EFB6` / `#f0e199` / `#efb5b9` |
| Overall Risk Color Green / Yellow / Red | — | `#7AD479` / `#e8d166` / `#ED6161` |
| Agency Wide Indicator status: No data / Out of Standard / In Standard | — | `#e6e6e6` / `#de6a73` / `#B8E6BB` |

Page background: `#D5D9E2` is set explicitly on 13 of the 19 pages. Priorities, PSAT Risks, Non-PSAT
Risks, Agencywide Risks and the two tooltip pages set no page background and inherit the theme default
— base theme `CY22SU11` sets `visualStyles.page['*'].background = transparency 100` over a `#FFFFFF`
outspace. The custom theme (`Custom48037914116998315.json`) overrides only `foregroundNeutralSecondary`
= `#D9B300`. Normalising all pages to `#D5D9E2` in the rebuild is a reasonable **[NEW]** decision, but
it is not the as-built state.

#### 9.4.1 Risk-scale definitions (verbatim from the Heatmap axis tooltips)

| Axis | Level | Definition |
|---|---|---|
| Consequence | High | *"Event/situation would threaten an agency level goal, objective, or CBJ major activity."* |
| Consequence | Medium | *"Event/situation would affect a business line or office's goals and objectives, but would not have agencywide implications."* |
| Consequence | Low | *"Event/situation would have minimal impact to the business line or office's ability to achieve objectives or performance goals."* |
| Likelihood | High | *"Event or situation is almost certain to happen."* |
| Likelihood | Medium | *"Event or situation is likely to occur."* |
| Likelihood | Low | *"Event or situation is unlikely to occur."* |
| Consequence axis | — | *"Inherent - potential consequence if not mitigated. Residual - anticipated consequence after mitigation."* |
| Likelihood axis | — | *"Inherent - likelihood of occurrence without mitigation. Residual - likelihood of occurrence after mitigation."* |

These eight strings are hard-coded as the hover tooltips on the Heatmap page's axis-label shapes and
are the only place in the supplied artefacts where the Low/Medium/High scale and the
Inherent-vs-Residual distinction are defined.

### 9.5 Derived analytic columns that the rebuild must compute

| Column | Where | Meaning |
|---|---|---|
| `Result` | PI Result | **In Standard · Out of Standard · No data** — the pass/fail verdict, derived from Results vs Target/Operator (or vs Min/Max/Lower/Upper for Range indicators) |
| `Result Value`, `Temp Target` | PI Result | flattened per-quarter numeric values for trending (`Result Value` coalesces null to 0) |
| `Reported Results` (identical to `Count Towards Reported Results`) | PI Result | 0/1 applicability flag — `IF(not_applicable, 0, 1)`; SUM gives the number of periods in which the indicator reported, and that sum is what the page-16 indicator table displays (Document 2 §14.5 item 5) |
| `Risk Level` | Risk Update | two-letter code `LL, LM, LH, ML, MM, MH, HL, HM, HH` = Likelihood × Consequence |
| `Risk Index` | Risk Update | ordered index used to sort the heat-map list |
| `X`, `Y` (plus `n`, `i`, `A`, `B`) | Risk Update | in-cell marker placement only — a hand-authored lookup that spreads up to 12 markers inside one cell of width `A` = 10 and height `B` = 5, keyed on `n` (PSAT Risk Updates sharing Risk Level + Reporting Period + Mitigation Type) and `i` (0-based rank by `Index` within that group); **not** derived from the likelihood or consequence levels, and blank for `n` > 12. Full rule: Document 2 §14.5 item 3 |
| `Mitigation Type` | Risk Update | **Inherent** or **Residual** — the report un-pivots each Risk Update into two rows |
| `Inherent/Residual Likelihood Level`, `… Consequence Level` | Risk Update | numeric 1/2/3 from High/Medium/Low |
| `… Left Side Color`, `… Right Side Color`, `Risk Color` | Risk Update | Green / Yellow / Red tokens; eight colour columns (inherent + residual × likelihood + consequence × left + right). Right = this quarter's level, left = last quarter's — see Document 2 §14.5 |
| `Consequence Text`, `Likelihood Text` | Risk Update | active (inherent or residual) text depending on the Mitigation Type slicer |
| `Primary Column` | Risk Update | `"RISK {Risk ID}: {Risk Title}"` composite — the literal `RISK ` prefix is part of the stored value (Document 2 §14.5) |
| `Associated PIs` | Risk Update | concatenated list of related Performance Indicators |
| `Reporting Period` | Reporting Period | `"FY{yy} {Qn}"` label (e.g. `FY24 Q3`); `Annual` rows exist and are excluded from trend charts |
| `Indicator Headline` | Performance Indicator | display composite used on the PI Profile page |
| `Agencywide` | Enterprise Risk | true when the risk's **contributing-offices** junction contains the Agencywide office — not derived from the lead office. The legacy DAX pins office GUID `4d4622ce-2958-ee11-be6e-001dd8098e36`, which matches no office in the shipped extract, so the flag is false for all 22 risks today; see Document 2 §14.5 |
| `Goal` (1/2/3) | Priorities | numeric goal number |
| `Count` | Positive Change Management | measure used by the KPI cards |
| `Toggle` | View | two-value **stage** filter on the `View` dimension — `All` admits Draft, Pending, Revision and Finalized records; `Finalized` restricts every visual to Finalized records. Implemented as a 5-row (Stage, Toggle) bridge joined many-to-many on `Stage` to PI Result, Risk Update, Priorities, Positive Change Management, Accomplishment, Performance Indicator and Enterprise Risk. It **filters which record rows the page shows** — the report contains no bookmarks or visual groups, so it is a data filter, not a page-variant switch. Implement it as a global filter parameter (Doc 3 §6.1) |
| `Owner`, `Contact Person` | Performance Indicator | user full name resolved by lookup from the owner / contact-person pointer — the OWNER and CONTACT PERSON cards on page 18 |
| `GOAL`, `Column` | Goal | `"GOAL {goal_number}"` and `"{GOAL}: {goal_title}"` — the page-1 Goal slicer values and Goal card |
| `Accepted?` | Risk Update | a yes/no badge image resolved through a lookup from `risk_accepted` to a two-row image table (`Accepted` / `Not accepted`) — the page-15 **Accepted?** element. **Rebuild:** render the badge in the UI; no analytic column is needed |
| `Outlook Text` | Risk Update | `"OUTLOOK: {risk_outlook}"` |
| `Risk Description` | Risk Update | the parent Enterprise Risk's description, denormalised onto the update |
| `Associated PIs` | Enterprise Risk | the same concatenated indicator list as on Risk Update, also computed on the risk itself |
| `Reporting Period` | PI Result · Risk Update · Accomplishment · Positive Change Management · Priorities · Date | the per-fact `"FY{yy} {Qn}"` key each fact table carries to join the Reporting Period dimension |

### 9.6 Dashboard access and refresh

- Dashboards are embedded inside both model-driven apps and are also available directly in Power BI.
- **For QPR-presented data set the Report Level filter to BL/PL and CBJ/APPR.**
- **For Office-level dashboards set the Report Level filter to Office Report.**
- Refresh schedule: 8 a.m., 9 a.m., 10 a.m., 12 p.m., 2 p.m., 4 p.m., 5 p.m., 6 p.m.
  *"Anything entered in the Performance Management application between these times will not show up
  until the next scheduled refresh."*

> **Rebuild guidance:** the rebuilt system should serve dashboards from the operational SQLite
> database through live views (with job-refreshed snapshot tables only for a page that proves too slow
> — Doc 2 §14) so that data is live rather than refreshed eight times a day. The 19 pages above map to
> the analytics endpoints in Document 3, §6.

#### 9.6.1 Drill-through targets and embed parameters (as-built)

| Target page | Drill-through key |
|---|---|
| QPR Risk View | `Risk Update[ID]` |
| View Quadrant | `Risk Update[ID]` |
| PI Profile | `Performance Indicator[Title]` |
| Performance Indicator Dashboard | `PI Result[Indicator ID]` |

The nine `Layout.pods` entries and the parameter each binds:

| Pod | Bound page | Parameter |
|---|---|---|
| 1 | QPR Risk View | `Risk Update[ID]` |
| 2 | PSAT Risks Dashboard | `Risk Update[PSAT?]` (single-select) |
| 3 | Non-PSAT Risks Dashboard | `Risk Update[PSAT?]` (single-select) |
| 4 | View Quadrant | `Risk Update[ID]` |
| 5 | PI Profile | `Performance Indicator[Title]` |
| 6 | Performance Indicator Dashboard | `PI Result[Indicator ID]` |
| 7 | Heatmap | — |
| 8 | Heatmap and List | — |
| 9 | Strategic Planning Home | — |

The three "VIEW RISK MITIGATION" / Profile drill-through buttons on the PSAT, Non-PSAT and Agencywide
Risks pages point at section `ReportSectiond4899664a0b897d57c1a`, which does not exist in the file; the
click therefore resolves by drill-through-filter matching on `Risk Update[ID]`, which now matches two
pages (QPR Risk View and View Quadrant). Fix this in the rebuild by routing explicitly to QPR Risk View
rather than copying the dangling target.

### 9.7 In-app dashboards (Dataverse)

| Dashboard | Content |
|---|---|
| **My To-do's** | Tasks grid (8 rows/page, view picker, quick find, jump bar) + activity timeline |
| **Performance Review** | Embedded Power BI report (the 19-page report above) |
| **Performance Management** | Embedded Power BI report |
| **Strategic Planning Dashboard** | Embedded Power BI report |
| **User Guides** | Embedded PDF (web resource `nrc_userguidepdf`) |
| **Frequently Asked Questions** | Embedded PDF (web resource `nrc_faqpdf`) |

---

## 10. Non-functional requirements

| Area | Requirement | Source |
|---|---|---|
| **Authentication (internal)** | ICAM-issued credentials, single sign-on — the same mechanism as SharePoint, Teams and Outlook. All pages accessible by internal NRC users only. | System Architecture Document §2.3.1 |
| **Authentication (external)** | *"This feature is not yet available."* A future external-facing portal for publicly available data is planned. | SAD §2.3.2, EPS diagram |
| **Accessibility** | Section 508 compliance was closely followed; Power BI dashboards were customised for screen readers and colour-contrast levels. The rebuilt React UI must meet Section 508 / WCAG 2.1 AA. | SAD §6 |
| **Security and privacy reviews** | *"Ensure 508 compliance, security and privacy reviews. Ensure NRC Power platform governance."* — a Governance-epic gate, not a stated classification. FISMA and CISO appear in the SAD only as glossary acronyms (§1.2); no security-classification or review requirement is documented — see §17.3. | `SPA+Product+Roadmap.doc`, Governance epic PI 0 |
| **Audit** | Auditing is enabled on every custom table and on all attributes. Field-level security profile present. | `customizations.xml` (`IsAuditEnabled=1`, `FieldSecurityProfiles`) |
| **Data provenance** | *"Data provided in the applications is entered and verified by NRC users. Dashboards will only report on entered data from the model-driven applications."* | SAD §3 |
| **Change tracking** | Change tracking enabled on tables (needed for downstream analytics sync). | `customizations.xml` |
| **Search** | Quick Find configured on every table; Advanced Find views defined for all. | 334 saved queries |
| **Duplicate detection** | Duplicate-check flag present per table. | `customizations.xml` |
| **File storage** | Planned Measure/Milestone/Deliverable supports a file attachment up to 32 MB. Notes/attachments enabled on records. | `nrc_Deliverable` (file, max 32768 KB) |
| **Localisation** | Single language: en-US (LCID 1033). | `customizations.xml` |
| **Human-centred design** | *"Human Centered design (HCD) based user interface"* — stated in the PI 0 column of every one of the six module tables. | `SPA+Product+Roadmap.doc` |
| **Governance gates** | *"Ensure 508 compliance, security and privacy reviews. Ensure NRC Power platform governance."* — a delivery gate, not a system feature; the same obligation is recorded once under **Security and privacy reviews** above. | `SPA+Product+Roadmap.doc`, Governance epic PI 0 |
| **Usability improvements requested** | More hover-over help text; display character limits on the QPR view; default view implementation to avoid user confusion; minimise manual data entry; ability to **duplicate records year to year**; clarify Performance Indicators vs Indicator Results and Enterprise Risks vs Risk Updates. | `SPA+-Improvements.doc` |
| **Glossary hover** | *"Words that are defined in the glossary in the Strategic Plan should be highlighted or have some other indicator where a hover and display the definition from the strategic plan appendix. For any word in the dashboard view."* | Overview doc |
| **Export** | SES module plans require export of a performance plan into a Word file. | Overview doc |

---

## 11. Integrations

| System | Direction | Purpose | Status |
|---|---|---|---|
| **ICAM / Entra ID (Azure AD)** | in | Authentication, user identity, group membership | Live |
| **Microsoft Teams (via Graph)** | out | "SPA Notifications" group chat messages on submit / approve / return | Live |
| **Microsoft Power BI** | out | Embedded dashboards; scheduled data refresh 8×/day | Live |
| **FAIMIS** | in | Business Line Owner, Product Line Owner, Associated Business Line, Associated Product Line — *"Manual, no active connection"*, refreshed ad-hoc when changes are identified | Manual |
| **SharePoint (legacy EPMS lists)** | in | One-time migration source for PIs, Accomplishments, Risks, PCM, Priorities | Migration only |
| **gid.nrc.gov (EA)** | in | Migration source for Priority Questions, Evaluations, Research Activities | Migration only |
| **HRMS / LDAP / External websites** | in | Named as Performance Indicator *Data Source* values; no automated feed exists | Reference only |
| **Talent Management System** | ↔ | *"Ideally, this would be integrated or shared"* for the SES module | Aspiration |

Seven connection references exist in the solution: six to **Microsoft Dataverse** and one to
**Microsoft Teams**.

---

## 12. Data migration

From `SPA - Data Migration Plan - Draft.docx` (May 15, 2023).

### 12.1 Static/reference data to load before go-live

| Table | Source | Approx. records |
|---|---|---|
| Goals | Excel extract from Strategic Plan Appendix A | 3 |
| Objectives | Data file from Strategic Plan Appendix A | 10 |
| Strategies | Data file from Strategic Plan Appendix A | 30 |
| Performance Indicators | SharePoint `OEDO-EPMS/Lists/Performance Indicators` | 3 552 |
| Planned Measures, Milestones, Deliverables | OEDO-supplied file | 20 |
| Definitions | Strategic Plan Appendix A | 25 |
| External Factors | Strategic Plan Appendix A | 8 |
| Product Lines | OEDO file | 25 |
| Business Lines | OEDO file | 15 |
| Products | OEDO file | 170 |
| Programs | OEDO file | 14 |
| Offices | OEDO file | 50 |
| Sign-Post and Markers | TBD | — |

### 12.2 Historical results data

| Table | Modules | Source | Approx. records |
|---|---|---|---|
| Performance Indicator Results | QPR, SES | SharePoint EDO-EPMS Performance Indicators list | 3 552 |
| Accomplishments | QPR, SES, Strategic Planning | SharePoint EDO-EPMS Accomplishments list | 2 594 |
| Risks | QPR | SharePoint EDO-EPMS Risks list | 861 |
| Positive Change Management | QPR, SES | SharePoint Change Management / End of FY22 PCM | 669 |
| Priorities | QPR | SharePoint EDO-EPMS Priorities list | 352 |
| Elements & Standards | SES | OEDO extract of prior-year data | — |
| External Factors | Strategic Planning | *"Manually entered by OEDO team"* — contradicts §12.1, which sources them from Strategic Plan Appendix A (8 records); see §17.3 | — |
| Priority Questions / Evaluations / Other Evidence Building | Evidence Building | `gid.nrc.gov/EA/...` | — |
| Capacity Assessment tables | Capacity Assessment | TBD | — |
| Survey Results | Strategic Planning | TBD (see §17.3 question 12) | — |

### 12.3 Assumptions and constraints recorded in the plan

- Existing SharePoint data is accurate and ready to extract.
- The development team has access to the legacy SharePoint lists.
- For migrated records the **Date Created** value is set to the date/time of the ETL run.
- Adequate table space must be allocated for the ETL.
- Every new field in the target system must map to a valid value.

### 12.4 ETL procedure (generic, as documented)

1. Run the routine to pull data from SharePoint.
2. Convert data to Excel.
3. Clean data per OEDO direction.
4. Format the workbook into loadable form.
5. Run the import routine into the target tables.
6. Review results; resolve issues; reload as needed.

**Performance Indicator specific steps:** export the All Items view; add a "primary BL" column
(first Business Line listed — all others become contributing); find-and-replace every drop-down choice
with its numeric code; remove single quotes from short-description values; replace values in the
Objective/Strategy column with their preceding sequence numbers; run the push flow in two passes
(create, then update); clean non-numeric characters (including `%` and unit symbols) from quarterly
Results and Target columns.

### 12.5 Migration-support columns present in the current schema

The current tables still carry legacy migration columns (`BLText`, `FYText`, `IndTitle`, `MergeID`,
`MigratedFlag`, `OfficeText`, `OrgText`, `PLText`, `ProductText`, `ProgramText`, `ReptPersonText`,
`ContactText`, `OwnerText`, `PIText`, `StrategyText`, `BLPLText`). `SPA+-Improvements.doc` lists these
as **removal candidates**. In the current export the surviving examples are `nrc_pltext` on Enterprise
Risk and `nrc_programtext` on Accomplishment. The rebuild should stage these in the separate migration
database (`staging.db`, attached only while migrating — Document 2 §1), not in the production tables.

---

## 13. Known technical debt to retire during the rebuild

Recorded in `SPA+-Improvements.doc`:

### 13.1 Abandoned / unused tables
Accomplished Item · (DEPRECATED) Priority · Approval Processes (Accomplishment / Enterprise Risk /
Evaluation / Performance Indicators / Priority Question / Research / Risk Update) · Approval Queue ·
Associated Performance Indicator · Attachment · Attribute · Budget · Budget Data · Cross-Cutting Data ·
Cross-Cutting Items · Data Entry · Definition · Division Owner(s) · Evaluations · External Factor ·
Fiscal Year Resources · Feedback · Findings / Mitigating Strategy · Indicators · Key Agency Function ·
Key Areas · Key Deliverables · Markers · Measure · Performance Goal · Performance Requirements ·
Positive Change Management Approval Flow · Principle · Priorities Approval Flow · Priority Question ·
Report · Report Strategy · Research · Research Activity · Signposts · Staffing Data ·
Supporting Dataset · Survey Data · Program.

> **Caution:** several of these (Approval Queue, Definition, Evaluations, External Factor,
> Performance Goal, Priority Question, Research Activity, Signposts, Key Areas) are still present and
> referenced in the shipped solution. The "abandoned" list appears to be an intent list, not a completed clean-up.
> The rebuild should confirm each with OEDO before dropping it. Flagged in §17.

**Corroborating evidence from the solution export.** 15 names on this list — Accomplished Item,
Attribute, Budget, Budget Data, Cross-Cutting Data, Data Entry, Division Owner(s), Fiscal Year
Resources, Findings / Mitigating Strategy, Indicators (`nrc_IndicatorIDs`), Key Deliverables,
Markers, Performance Requirements, Program and Research — genuinely **are** gone: the forms still
carry 34 of the 47 orphaned navigation links pointing at them (the other 13 name entities that
survive — Performance Indicator, PI Result and the deprecated Priorities table), but every one of
those links is hidden and has no relationship definition behind it. That removal is therefore already complete and confirmed, and
those tables must not be rebuilt. The full inventory is in Document 2 §16.4.

### 13.2 Deprecated columns flagged for removal

**Performance Indicators:** Indicator Status (the old `nrc_indicatorstatus`), Operator,
Performance Goal, *OLD* Accountable Organization.
**Performance Indicator Results:** Approval Queue Flag, Business Line/Product Line Owner,
Q# At-Fault Business Lines, Q# At-Fault Offices, Q# Raw Data (the decimal variants), Q# Updates,
duplicate Q4 Success Likelihood, Return to, Send next to.
**Enterprise Risks:** Contact Person, Risk Lead.
**Risk Updates:** Impact Description, Likelihood Description, Performance Monitoring and Progress,
duplicate Residual Likelihood Description.
**Positive Change Managements:** Positive Change Management Item.

Observable duplicates in the current schema that confirm this: Enterprise Risk has both
`nrc_impactdescription` (nvarchar) and `nrc_impactdescription1` (ntext); PI Result has both
`nrc_q4successlikelihood1` and the pattern-consistent name; `nrc_indicatorstatus` and `nrc_indstatus`
option sets both exist.

### 13.3 Disabled / deprecated flows
33 entries (32 distinct flow names — "When a Positive Change Mgmt Entry is submitted for next
approval" is listed twice) named in the improvements document, including
"Deprecated – Approval Submission Parentflow",
"Deprecated – Approval Steps Validation", "Deprecated – Submitted Flow", "Deprecated - Rejected Entry",
"(DEPRECATED) Add Alternate User to Performance Requirement Record", "(DEPRECATED) Append PI Revision
History…", and the per-entity "When a X is submitted / returned / finalized" flows that were replaced
by the current child-flow architecture.

### 13.4 Naming inconsistencies observed in the schema (must be corrected, not copied)

| Table | Issue |
|---|---|
| `nrc_EnterpriseRisk` | `nrc_risktitle` is labelled **"Risk ID"** while `nrc_riskid` is labelled **"Risk Title"** — the two are swapped |
| `nrc_Division` | `nrc_acronym` is labelled **"Name"** while `nrc_name` is labelled **"Acronym"** — swapped |
| `nrc_PerformanceIndicator` | `nrc_performanceindicator` is labelled **"Indicator ID"** while `nrc_indicatorid` is labelled **"Title"** — swapped |
| `nrc_PerformanceIndicatorFiscalYear` | `nrc_statusupdatesummary` is labelled **"Annual Mitigation / Remarks"**; `nrc_q2rawdata1` display name contains a stray backtick |
| App modules | `nrc_EnterprisePerformanceSystem` displays as "Strategic Planning"; `cr9de_StrategicPlanningModule` displays as "Performance Management" |
| `nrc_EnterpriseRisk.nrc_strategicobjective` | Points at the **Strategy** table, not Objective |
| `nrc_Definition.nrc_officegoal` | Points at the **Office** table, not Office Goal |
| Business rules | Several named "New business rule", "SHOWHIDESOMMENTS", "SHOWHISECOMMENTS", "showhidecomments" (four near-duplicates) |
| `cr9de_` prefixed columns | `cr9de_businessline` on PI Result and `cr9de_agencywidesupportlevel` on PI belong to a different publisher prefix |

### 13.5 Hard-coded values and configuration debt

| Item | Issue and rebuild action |
|---|---|
| **Hard-coded flow-owner address** | `Devan.Tighe@nrc.gov` is appended to the notifier's chat-membership set (§6.6), so Teams chat matching depends on one named account. Like the hard-coded EDO role GUID (§6.2), it must become configuration or a service account in the rebuild |
| **Hard-coded cross-app link** | The Strategic Planning app's Other Modules → Performance Management sub-area (`subarea_f78b065f`) hard-codes an absolute URL to a *different* host and appid (`https://nrc-spa.crm9.dynamics.com/…appid=d419405f-d648-ee11-be6d-001dd8097981…`) instead of using the `nrc_PMModule` environment variable that exists for exactly that purpose (value: `nrc-eps-dev`, appid `fda39968-…`, same dashboard id). The reciprocal link in the Performance Management app does use `{%nrc_SPModule%}`. In the rebuild both become internal routes |

---

## 14. Proposed target architecture (rebuild)

This section is **design guidance for the rebuild**, not a description of the as-built system.

### 14.1 Logical tiers

```
┌──────────────────────────────────────────────────────────────────────────┐
│  React (latest) SPA — TypeScript, Vite, React Router, TanStack Query      │
│  · Strategic Planning workspace   · Performance Management workspace      │
│  · Shared record framework (list views, forms, sub-grids, bulk commands)  │
│  · Dashboard/analytics workspace  · Admin workspace                       │
│  · 508 / WCAG 2.1 AA, responsive                                          │
└───────────────▲──────────────────────────────────────────────────────────┘
                │ HTTPS / REST+JSON (OpenAPI), JWT bearer
┌───────────────┴──────────────────────────────────────────────────────────┐
│  Python API tier                                                          │
│  · Auth & session (OIDC against ICAM / Entra ID)                          │
│  · Authorisation (role + privilege-depth + ownership evaluation)          │
│  · Record services (CRUD, validation, ID generation, auto-fill)           │
│  · Workflow engine (submit / approve / return / discontinue / re-open)    │
│  · Notification service (in-app task, e-mail, Teams)                      │
│  · Analytics/query service (dashboard aggregates)                         │
│  · Import/export service (bulk load, Word/Excel export)                   │
│  · Scheduler (task grouping, task closure, carry-over jobs, DB upkeep)    │
│  · Data-access layer (the only path to the database; applies the          │
│    row-visibility predicate reproducing privilege depths)                 │
└───────────────▲──────────────────────────────────────────────────────────┘
                │ SQL (Python sqlite3, in-process — no database server)
┌───────────────┴──────────────────────────────────────────────────────────┐
│  SQLite — one database file on the API host's local disk (WAL mode)       │
│  · Operational tables, prefixed by area (see Document 2)                  │
│  · Audit tables (row history; yearly archive files attached on demand)    │
│  · Analytics views for the 19 dashboard pages                             │
│  · Triggers for the plan hierarchy; FTS5 indexes for quick search         │
│  · staging.db attached during migration only                              │
└──────────────────────────────────────────────────────────────────────────┘
```

**What choosing SQLite commits the rebuild to** (Document 2 §1.2 has the detail):

- **No database server.** The database is a file opened in-process by the Python API, so there is no
  database host to provision, patch or authenticate against — and no network hop on any query.
- **One writer at a time.** Readers run concurrently under WAL; writes are serialised. Every write
  transaction is short and opens with `BEGIN IMMEDIATE`, and nothing slow (Teams, e-mail) happens
  inside one. This comfortably fits an internal agency application whose writes cluster around the
  quarterly cycle, but it means **one API host**: the file must sit on that host's local disk, not on
  shared or network storage, and the API tier scales by worker processes on that host rather than by
  adding hosts.
- **Row visibility is the API's job.** SQLite has no row-level security or database roles, so the
  privilege-depth model is enforced by the data-access layer (Document 2 §13), which every query
  passes through and which the test suite checks entity by entity.
- **Backups are scheduled, not implied.** The database is backed up online with `VACUUM INTO` by a
  scheduled job, optionally with continuous WAL replication; restoring is copying one file back.

### 14.2 Cross-cutting capabilities the rebuild must provide generically

Because the as-built system repeats the same behaviour across seven record types, the rebuild should
implement these once and configure them per entity:

1. **Record framework** — metadata-driven list views, forms with tabs/sections, sub-grids, quick-view
   panels, lookups with cascading filters, multi-select choices.
2. **Workflow engine** — state machine definitions, transition guards, ownership transfer,
   audit-record creation, comment capture.
3. **Bulk command framework** — selection-based commands with confirm/success/error dialogs and
   view+role-scoped visibility.
4. **Validation framework** — required-level rules, character limits with live counters, conditional
   visibility, referential-integrity checks, save-prevention rules.
5. **Identifier framework** — pluggable generators per entity, transaction-safe.
6. **Notification framework** — task creation with grouping, e-mail, Teams, deep links.
7. **Audit framework** — full field-level history on every table.
8. **Analytics framework** — the derived columns in §9.5 as database views.

---

## 15. Functional requirements traceability index

Bare `§n` references point within this document; `Doc 2 §n` / `Doc 3 §n` point at the other two.
Within one `·`-separated group, a bare `§n` following a `Doc N §m` continues to refer to Document N
(so "Doc 3 §13.8, §14.8" means Doc 3 §13.8 and Doc 3 §14.8).

| ID | Requirement | Source | Where specified |
|---|---|---|---|
| FR-01 | Maintain Strategic Plan hierarchy (Goals, Objectives, Strategies, Performance Goals) | Product Vision, MVP Roadmap | §5.1 · Doc 2 §5 · Doc 3 §13.8, §14.8 |
| FR-02 | Maintain organisational structure (Offices, Divisions, Organizations, BL, PL, Products, Programs) | MVP Roadmap | §5.1 · Doc 2 §4 · Doc 3 §13.9, §14.9 |
| FR-03 | Maintain glossary Definitions and External Factors | Product Vision | §5.1 · Doc 2 §5.5, §5.6 · Doc 3 §13.8, §14.8 |
| FR-04 | Create/maintain Performance Indicators with revision chaining | User Guide, forms | §5.2.1, §8.1 · Doc 2 §6.1 · Doc 3 §13.1, §14.1 |
| FR-05 | Capture quarterly PI Results incl. Range indicators and Not-Applicable handling | User Guide, business rules | §5.2.2, §8.2 · Doc 2 §6.3 · Doc 3 §13.2, §14.2 |
| FR-06 | Create/maintain Enterprise Risks | User Guide | §5.2.3 · Doc 2 §6.4 · Doc 3 §13.3, §14.3 |
| FR-07 | Capture quarterly Risk Updates incl. inherent/residual scoring and last-quarter carry-forward | User Guide, flows | §5.2.4, §8.4 · Doc 2 §6.5 · Doc 3 §13.4, §14.4 |
| FR-08 | Capture Priorities with rank and Principles of Good Regulation | User Guide | §5.2.5 · Doc 2 §6.7 · Doc 3 §13.6, §14.5 |
| FR-09 | Capture Positive Change Management items | User Guide | §5.2.6 · Doc 2 §6.8 · Doc 3 §13.7, §14.6 |
| FR-10 | Capture Accomplishments with PI-driven auto-fill | User Guide | §5.2.7, §8.4 · Doc 2 §6.6 · Doc 3 §13.5, §14.7 |
| FR-11 | Capture Planned Measures/Milestones/Deliverables with file attachments | forms | §5.2.8 · Doc 2 §6.2 · Doc 3 §13.13, §14.10 |
| FR-12 | Bulk submit / approve / return with confirm dialogs and role+view-scoped visibility | User Guide, ribbon | §6 · Doc 3 §4, §15 |
| FR-13 | Maintain a complete Submission / Approval / Rejection audit trail | flows, entities | §6.3–6.5 · Doc 2 §9 |
| FR-14 | Notify approvers and submitters via Task + Teams + deep link | flows | §6.6–6.7 · Doc 2 §9.5, §9.6 · Doc 3 §7 |
| FR-15 | Propose / discontinue / deny discontinuance for PIs and Risks | flows, ribbon | §6.2, §7.3, §7.4 · Doc 3 §4.1, §15.1 |
| FR-16 | Re-open finalized PI Results for the next quarter | flows | §6.2, §7.2 · Doc 3 §4.1, §15.1 |
| FR-17 | Flag / unflag Performance Indicators for carry-over review | flows | §6.2 · Doc 3 §4.1, §15.1 |
| FR-18 | Enforce Goal→Objective→Strategy referential integrity | scripts | §8.3 · Doc 2 §12.3 · Doc 3 §15.3 |
| FR-19 | Enforce field-level character limits with live counters | scripts, User Guide | §8.2 · Doc 2 §12.2 · Doc 3 §12 |
| FR-20 | Restrict CBJ/APPR and Agencywide record creation to EDO users | script | §8.2 · Doc 2 §13.3 · Doc 3 §10 |
| FR-21 | Provide 190 business list views — 154 public + 36 "My …" (334 saved queries in total) incl. My / My Office's / Pending / Finalized | saved queries | Doc 2 §11.2 · Doc 3 §13 |
| FR-22 | Provide 19 dashboard pages with the global slicer bar | pbix | §9 · Doc 2 §14 · Doc 3 §16 |
| FR-23 | Provide a natural-language query capability | SAD, pbix | §9.3 (page 1) · Doc 3 §6.6 |
| FR-24 | Provide embedded User Guide and FAQ | dashboards | §9.7 · Doc 3 §17 |
| FR-25 | Provide a My To-do list of open approval tasks | dashboard | §9.7 · Doc 2 §9.5 · Doc 3 §13.14, §17 |
| FR-26 | Support team (office) ownership alongside user ownership | flows, entities | §4.5 · Doc 2 §3.2, §3.3, §13 |
| FR-27 | Support a configurable multi-step approval chain | Approval Queue | §6.8 · Doc 2 §9.4 · Doc 3 §4.3 |
| FR-28 | Evidence Building: Priority Questions, Evaluations, Research Activities with 2-stage approval | entities | §5.3, §7.5 · Doc 2 §7 · Doc 3 §13.11, §14.11 |
| FR-29 | Signposts and Key Areas | entities | §5.4 · Doc 2 §8 · Doc 3 §13.12, §14.12 |
| FR-30 | SES Performance plans with Word export *(future)* | Overview doc | §5.5 · Doc 3 §6.5 (export) |
| FR-31 | Capacity Assessment *(future)* | Product Vision | §5.6 · Doc 2 §2.1 (enumerations already present) |
| FR-32 | Migrate ~11 700 historical records from SharePoint / gid.nrc.gov | Migration plan | §12 · Doc 2 §15 · Doc 3 §9 |
| FR-33 | Glossary hover-over definitions on dashboards | Overview doc | §10 · Doc 2 §14.1 · Doc 3 §12, §16.1 |
| FR-34 | Duplicate records year-to-year | Improvements doc | §10 · Doc 3 §9 |
| FR-35 | Section 508 / WCAG 2.1 AA accessibility | SAD | §10 · Doc 3 §18.1 |
| FR-36 | ICAM SSO authentication | SAD | §10 · Doc 3 §2 |
| FR-37 | Full field-level audit | solution config | §10 · Doc 2 §9.7 |
| FR-38 | Reproduce every user-facing command dialog (confirm / success / error) | ribbon command definitions | §6.2 · Doc 3 §15.2 |

---
## 16. Recommended delivery plan

Based on the original MVP roadmap and the measured scope, a suggested increment plan for the rebuild:

| Increment | Contents | Rationale |
|---|---|---|
| **0 — Foundation** | SQLite schema and connection settings (Document 2 §1.2), backup job, auth (ICAM OIDC), role/privilege engine and data-access layer, record framework, list-view + form engine, audit | Everything else depends on it |
| **1 — Strategic Plan + structure** | Goals, Objectives, Strategies, Performance Goals, Fiscal Years, Offices, Divisions, Organizations, Business Lines, Product Lines, Products, Major Programs, Contributing Programs, Office Goals, Definitions, External Factors | Mirrors the original "Mini MVP"; reference data must exist before measures |
| **2 — Measures** | Performance Indicators (incl. revision chaining, auto-fill, discontinuance), Planned Measures/Milestones/Deliverables, Enterprise Risks | The measure definitions |
| **3 — Quarterly capture + workflow** | PI Results, Risk Updates, Accomplishments, PCM, Priorities; the full submit/approve/return engine; Submission/Approval/Rejection audit; Tasks; notifications; carry-over and re-open commands | The core QPR cycle |
| **4 — Analytics** | The 19 dashboard pages, derived analytic columns, natural-language query, glossary hover | Replaces Power BI |
| **5 — Migration + cutover** | ETL from SharePoint/gid.nrc.gov, reconciliation, parallel run | Per §12 |
| **6 — Evidence Building** | Priority Questions, Evaluations, Research Activities with 2-stage approval | Data model already fully specified |
| **7+ — Future modules** | Capacity Assessment, SES Performance (incl. Word export), Signposts and Markers, external public portal | Requirements-level only today |

---

## 17. Open items and documented gaps

These are the points where the supplied documentation is silent or contradictory. **No assumption has
been made about them anywhere in this document set** — each must be confirmed with OEDO before build.

### 17.1 Source artefacts referenced but not supplied

The Confluence page exports `Requirements.doc`, `Conceptual+Architecture+Diagram.doc`,
`Database+model+draft.doc`, `SPA+Data+model+(latest).doc`, `SPA+Data+Planning+Activities.doc` and
`SPA+User+Roles+and+Permissions+At+The+Office+Level.doc` contain **only attachment placeholders**, not
prose. The attachments they point at are:

| Referenced attachment | Supplied in this repository? |
|---|---|
| `EPS diagram 2.6.23.pdf` | ✅ yes |
| `ERD Draft Strategic Planning (1).pdf` | ✅ yes |
| `SPA - Data Migration Plan - Draft.docx` | ✅ yes |
| `User Role Permissions Matrix 2.1.23.xlsx` | ✅ yes |
| `SPA User Roles and Permissions 6.13.23.docx` | ✅ yes |
| `SPA Personas - Draft 02.28.23.docx` | ✅ yes |
| `SPA Datamodel.png` | ✅ yes (large ERD; **pre-dates the shipped solution** — it carries full entity boxes for Program and Division Owner(s), which no longer exist (§13.1), and renders Planned Measure/Milestone/Deliverable as "Milestone" with Program and Deliverable as lookups rather than the current `nrc_Deliverable` file column. Useful for history, not as an as-built model) |
| **`User Journey (Value Stream) - Submitter.vsdx.pdf`** | ❌ **missing** |
| **`User Journey (Value Stream) - Final Approver.pdf`** | ❌ **missing** |
| **`User Journey (Value Stream) - Reviewer.pdf`** | ❌ **missing** |
| **`Requirements Matrix (4).xlsx`** | ❌ **missing** |
| **`SPA User Roles and Permissions 11.25.22.docx`** | ❌ **missing** (superseded by the 6.13.23 version, which *is* supplied) |

The three **User Journey value-stream maps** and the **Requirements Matrix** are the only materially
missing inputs. Everything they would cover (screens, roles, transitions) has been reconstructed from
the solution export, the user guide and the dashboards — but the value-stream maps should still be
requested to validate the end-to-end journeys.

### 17.2 Power BI semantic-model internals

The `.pbix` stores its tabular model in an XPress9-compressed backup (`DataModel`). Both layers
have now been decoded.

The **report layer** gives 19 pages, every visual, every field binding, every filter, every colour
rule, the complete navigation and drill-through map, and all 41 model table names with the columns
the report consumes.

The **tabular model** was decompressed and read as well, yielding **442 calculated-column
definitions, 76 of them on business tables** (the remaining 366 belong to Power BI's auto-generated
date tables and carry no business logic). The derived columns listed in §9.5 are therefore
specified from the as-built logic, not inferred from how the report uses them (§9.5 covers the
report-bearing subset of the 76; the full recovered set is in `DAX_columns.txt`) — see Document 2
§14.5 for each rule. Reproduce with:

```
pip install pbixray            # pulls the xpress9 decompressor
python -c "from pbixray import PBIXRay; m=PBIXRay('<file>.pbix'); print(m.dax_columns)"
```

> **An earlier revision of this document stated that the DAX "could not be read from the compressed
> backup" and that it should be obtained from the Power BI workspace if byte-level parity was
> required. That was wrong** — the compression is reversible with a public library, and reading the
> model changed three substantive conclusions: `result` has no Qualitative branch and returns
> **blank** for an unlisted operator; `risk_index` is a **text** value (`R0`, `Y3`, `G16`) ranked over
> PSAT rows only; and `x`/`y` are a **hand-authored 12 × 12 placement lookup**, not a computed
> formula. None of those was recoverable from report usage alone. The workspace
> (`DatasetId 396552cb-341f-4331-b3af-fbfeeef72c17`) is still the place to confirm anything the
> export cannot show, such as row-level-security roles or refresh history.

> **As-built defect — the deleted PSAT column.** `Enterprise Risk[DEPRECATED PSAT?]` (legacy
> `nrc_risktype`) was removed from the model but is still bound by the page-7 trend legend and by
> orphaned filters on pages 3, 7, 10 and 14; `Risk Update[DEPRECATED PSAT?]` is therefore an errored,
> always-blank calculated column. Use `Risk Update.PSAT?` throughout the rebuild.

### 17.3 Business questions to confirm with OEDO

| # | Question |
|---|---|
| 1 | **Approval chain depth.** The personas describe Intermediate (office) → Final (EDO) approval, and the Approval Queue entity supports N ordered steps, but the shipped QPR flow is single-stage to one configured approver team. Which behaviour is required in the rebuild? |
| 2 | **Report Level value 875670001.** The `nrc_reportlevel` option set has no value 875670001, yet the Prevent-Save script tests for it. Was a value removed? What is the intended restricted level? |
| 3 | **Deprecated tables.** §13.1 lists tables as abandoned that are still live in the solution (Approval Queue, Definition, Evaluations, External Factor, Performance Goal, Priority Question, Research Activity, Signposts, Key Areas — External Factor is also an Increment 1 build item in §16). Confirm which are genuinely retired. |
| 4 | **Enterprise Risk `nrc_approvalorderstage`.** The creation flow writes this column but it does not exist on the Enterprise Risk table in the shipped schema (it exists on Evaluations). Confirm it is dead code. |
| 5 | **Character limits.** The User Guide and the schema disagree in several places (e.g. PI Description 1 000 vs 950; Enterprise Risk Description 310 vs 300; PI Results Calculation 1 000 vs "670 or less"; PI Result Mitigation/Remarks 100 vs 800; Risk Update Budget Strings 300 vs 225). Which is authoritative? **Largely answered — see Doc 3 §15.5.1.** The schema is authoritative: the guide's numbers match a 2022–23 Dataverse metadata cache embedded in the canvas app, not the shipped columns, in four demonstrable cases (PI Description 1 000, Mitigation / Remarks 100, PCM Description 650, MANAGE 700 — each the width before a later resize). That leaves **three** decisions that genuinely need OEDO: Enterprise Risk Description (300 vs the guide's 310, which matches no width the column has ever had), Accomplishment Description (850 vs the 750 users are warned at today) and PCM Description (1 200 vs 650). A migration hazard also follows from the resizes — Doc 3 §15.5.1.1. |
| 6 | **Swapped labels.** Confirm the corrected naming for Enterprise Risk ID/Title, Division Name/Acronym and Performance Indicator ID/Title (§13.4). |
| 7 | **Delete rules.** Confirm the exact delete matrix: the SAD says submitters may delete their own Draft records; the Overview doc says read/write users cannot delete risks, PIs or priorities *except* office-level PIs and Non-PSAT risks. |
| 8 | **PSAT.** "PSAT" is used throughout (PSAT?, PSAT Accepted?, PSAT comments, PSAT/Non-PSAT dashboards) but is never expanded in the documentation. Confirm the definition and any rules attached to it. |
| 9 | **`Result` derivation — mostly answered.** The as-built rule is recovered in Doc 2 §14.5. What remains is a genuine design decision, not a missing fact: the shipped logic has **no Qualitative branch** (Qualitative indicators fall through to the operator comparison) and returns **blank**, not `No data`, when `operator` is null or unrecognised. Confirm the intended behaviour for both cases. |
| 10 | **Risk heat-map coordinates — answered.** X/Y are a hand-authored 12 × 12 marker-placement lookup and `risk_index` is a text colour-prefixed rank; both are specified in Doc 2 §14.5. The one point worth confirming is that the `risk_index` rank is computed over **PSAT rows only**, even on the Non-PSAT and Agencywide pages. The Low/Medium/High and Inherent/Residual definitions are recovered verbatim in §9.4.1. |
| 11 | **Fiscal-year boundary.** The re-open flow gates on the **calendar** year (`formatDateTime(utcNow(),'yyyy')`), while the dead `Current qtr` variable implies an October-start federal fiscal year (month ≥ 10 → Q1). Confirm whether the calendar-year gate is intended or a defect that should become a true October-start FFY gate in the rebuild, and confirm how "Annual" periods are treated. |
| 12 | **Survey Results.** Named as a Strategic Planning component in the Product Vision and Roles Matrix but marked "TBD" everywhere and absent from the schema. In or out of scope? |
| 13 | **External public portal.** The EPS diagram shows an external-facing website for publicly available data (the `Public?` flags on records suggest the intent). In or out of scope for this rebuild? |
| 14 | **Word export for SES.** Confirm the required output format and template. |
| 15 | **Duplicate-records-year-to-year.** Confirm which record types need the "duplicate from last year" action and what should and should not be copied. |
| 16 | **Teams notifications.** Confirm whether the rebuilt system should keep posting to the "SPA Notifications" Teams group chat, or switch to e-mail plus in-app notifications only. |
| 17 | **Data retention.** No retention or archival policy appears in any document. |
| 18 | **Environment strategy.** The environment variables point at a `nrc-eps-dev` environment. Confirm the dev/test/prod topology for the rebuild. |
| 19 | **PI Result Indicator Type calculated column.** The shipped formula writes option value 875670002, which does not exist in `nrc_indicatortype` (and does not exist in the 2022–23 metadata cache either), for Outcome PIs, and collapses every other parent Indicator Type to Output (§8.5). Confirm the intended mapping before rebuilding — do not reimplement it as a copy of the parent value. The column is evaluated on read and never stored, so no migrated row carries the orphan code, but profile the data anyway. |
| 20 | **`SPA Datamodel.png` vintage.** The ERD still shows Program, Division Owner(s) and a "Milestone" entity with Program/Deliverable lookups, none of which exist in the shipped solution. Confirm no later as-built ERD exists. |
| 21 | **SES Director.** The permissions matrix carries a sixth role "SES Director?" whose access is identical to SES User / Alternate in every module (§4.4). Distinct role or alias? |
| 22 | **Security classification.** No artefact states the system's FISMA categorisation or any required CISO review; both terms appear only as acronyms in SAD §1.2. Confirm the applicable classification and review gates. |
| 23 | **Enterprise Risk restricted creation.** The roles document restricts submitters to non-Agency-Wide, non-CBJ Enterprise Risks as well as Performance Indicators, but `nrc_preventSave` is registered on the Performance Indicator form only. Is the Enterprise Risk guard required, or was it never implemented? |
| 24 | **External Factors load method.** The migration plan sources External Factors from Strategic Plan Appendix A in its reference-data table (§12.1) and as "manually entered by OEDO team" in its historical-data table (§12.2). Which applies? |
| 25 | **Out-of-office delegation.** The Overview document requires that another person be able to update an absent user's records (§4.5). Confirm the intended mechanism (temporary delegate, team ownership, or approval-queue alternate) and whether the SES "deputies" relationship is the same feature. |
| 26 | **Risk Update Risk Lead / Contact Person defaulting.** Both are required on every Risk Update, but `nrc_EnterpriseRisk` no longer carries the columns the legacy back-fill flow read, and nothing populates them at creation (§5.2.4, §8.4). Confirm how they are to be defaulted. |
| 27 | **Accomplishment second submit webhook.** `submitAccomplishmentCommand` posts to `{%nrc_SUBMITURL%}` (all selected records) *and* to `{%nrc_SUBMITURL2%}` (first record only). `nrc_SUBMITURL2` is not defined in the solution (§6.7). What is its endpoint, and is the second call still required? |

---

*End of Document 1 — Complete Project Summary.*
*See Document 2 for the complete SQLite database schema and Document 3 for the complete API and UI screen specification.*
