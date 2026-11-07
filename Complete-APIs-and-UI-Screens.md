# NRC Strategic Planning & Performance Management System
# Document 3 — Complete API and UI Screen Specification

**Backend:** Python · **Frontend:** React (latest) · **Database:** SQLite
**Derived from:** `Core` managed solution v1.0.0.67 (334 saved views of which 190 are business views, 115 forms, 2 sitemaps,
52 client scripts, 30 custom ribbon command definitions (38 `<CommandDefinition>` in all, 8 of
them platform commands), 53 cloud flows) and
`Performance Review Dashboard DEV DATA REPOINT.pbix` (19 report pages)
**Document set:** 3 of 3 — (1) Project Summary · (2) Database Schema · (3) APIs & UI Screens
**Edition:** React + SQLite. The API contract and the screens are unchanged from the Angular +
PostgreSQL edition. The client is React — §11.6 sets out its stack and how the shared components of
§12 map onto it; the database-facing notes (§1 search, §2.4 row access, §7.1 jobs, §10 errors, §15.5.1
migration sizing, §20 job count) follow Document 2's SQLite design.

> Screen names, view names, field labels, button labels, dialog text and filter predicates in this
> document are reproduced from the source solution and the SPA User Training Guide. Items proposed for
> the rebuild that have no direct as-built equivalent are marked **[NEW]**.

---

## Table of contents

**Part A — API**
1. API conventions
2. Authentication and authorisation
3. Resource endpoints (full catalogue)
4. Workflow and command endpoints
5. Metadata endpoints
6. Analytics endpoints
7. Notification and task endpoints
8. Administration endpoints
9. Import / export endpoints
10. Error model

**Part B — UI**
11. Application shell and navigation
12. Shared UI components
13. List-view screens (all 190 business views)
14. Form screens (field-by-field)
15. Dialogs and command UX
16. Dashboard screens (all 19 pages)
17. Admin and utility screens
18. Accessibility, responsiveness and UX rules
19. Screen → API → table traceability matrix

---

# PART A — API

## 1. API conventions

| Aspect | Convention |
|---|---|
| Style | REST over HTTPS, JSON request/response, documented with OpenAPI 3.1 |
| Base path | `/api/v1` |
| Resource naming | plural kebab-case: `/performance-indicators`, `/pi-results`, `/enterprise-risks`, `/risk-updates`, `/accomplishments`, `/priorities`, `/positive-change-management`, `/goals`, `/objectives`, `/strategies` |
| Identifiers | UUID in the path; the human-readable code (e.g. `OR-NRR-12`) is a queryable field, never the path key |
| Collection response | `{ "items": [...], "page": {"number":1,"size":50,"total_items":812,"total_pages":17}, "applied_view": "...", "applied_filters": {...} }` |
| Paging | `?page=1&page_size=50` (default 50, max 200) |
| Sorting | `?sort=fiscal_year:desc,quarter:desc` |
| Field selection | `?fields=id,indicator_code,title,status_reason` |
| Expansion | `?expand=performance_indicator,fiscal_year,lead_office` — returns nested objects rather than bare ids |
| Filtering | `?filter[status_reason]=draft,revision&filter[fiscal_year_id]=…&filter[owner]=me` ; range filters `filter[created_on][gte]=…` |
| Named views | `?view=my-drafts` — applies a stored `core_view_definition` predicate (see §5) |
| Free-text search | `?q=…` — replaces Dataverse Quick Find; searches the table's configured search columns through its FTS5 index (Document 2 §12.4) |
| Concurrency | `If-Match: "<row_version>"` on PUT/PATCH; 409 on mismatch |
| Idempotency | `Idempotency-Key` header required on all bulk command endpoints |
| Partial update | `PATCH` with JSON Merge Patch semantics |
| Bulk | Command endpoints accept `{"ids": [...]}`; max 500 ids per call |
| Dates | ISO-8601 with timezone; server stores UTC |
| Rich text | HTML, sanitised server-side on write |
| Localisation | `en-US` only |
| Rate limiting | Per-user token bucket; `429` with `Retry-After` |
| Correlation | `X-Correlation-Id` echoed on every response and written to `wf_field_audit.correlation_id` |

---

## 2. Authentication and authorisation

### 2.1 Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/auth/login` | Initiate OIDC authorisation-code flow against ICAM / Entra ID |
| GET | `/api/v1/auth/callback` | OIDC redirect handler; issues the application session |
| POST | `/api/v1/auth/refresh` | Refresh the access token |
| POST | `/api/v1/auth/logout` | End the session |
| GET | `/api/v1/me` | Current user profile |
| GET | `/api/v1/me/permissions` | Resolved privilege map |
| GET | `/api/v1/me/teams` | Teams (offices) the user belongs to |
| GET | `/api/v1/me/roles` | Security roles |

### 2.2 `GET /api/v1/me` response fields

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `domain_name` | string | ICAM user principal name |
| `full_name` | string | used in every workflow message |
| `internal_email_address` | string | notification target |
| `title` | string | |
| `business_unit` | object | `id`, `name` |
| `manager` | object | `id`, `full_name` |
| `teams` | array of objects | `id`, `name`, `is_office`, and the linked `office` (`id`, `office`, `code`) |
| `roles` | array of objects | `id`, `name` |
| `is_edo_user` | boolean | true when the user holds the **EDO User** role |
| `is_submitter` | boolean | true when the user holds the **Quarterly Performance Submitter** role |
| `is_view_only` | boolean | true when the user holds only **SPA View Only User** |

### 2.3 `GET /api/v1/me/permissions` response

A three-level map: **entity → operation → depth**, exactly reproducing Document 1 §4.3.

| Level | Values |
|---|---|
| entity | every logical table name (`performance_indicator`, `enterprise_risk`, …) |
| operation | `create` · `read` · `write` · `delete` · `append` · `append_to` · `assign` · `share` |
| depth | `none` · `user` · `business_unit` · `parent_child_business_unit` · `organization` |

Example reading: for a Quarterly Performance Submitter, `performance_indicator` resolves to
create = user, read = organization, write = user, delete = none, append = user,
append_to = business_unit.

The React client uses this to enable/disable commands and to hide navigation items — replacing the
hard-coded EDO-role GUID checks in the legacy `nrc_*ButtonRules` scripts.

### 2.4 Authorisation layers

| Layer | Enforced by |
|---|---|
| Endpoint access | Role → privilege check in the API middleware |
| Row access | The API's data-access layer — the ownership / privilege-depth predicate of Document 2 §13.2, appended to every query (SQLite has no row-level security) |
| State guards | Service layer — edit/delete/submit/approve/return/discontinue/re-open guards (Document 2 §13.3) |
| Field guards | Service layer — the restricted-creation rule for CBJ/APPR and Agencywide Performance Indicators |

---

## 3. Resource endpoints (full catalogue)

### 3.1 Standard operation set

Every business resource `{res}` exposes:

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/{res}` | list, with `view` / `filter` / `sort` / `q` / `expand` / paging |
| POST | `/api/v1/{res}` | create — server generates the identifier and applies defaults |
| GET | `/api/v1/{res}/{id}` | single record |
| PATCH | `/api/v1/{res}/{id}` | partial update (blocked outside Draft / Revision for non-EDO users) |
| DELETE | `/api/v1/{res}/{id}` | delete (blocked outside Draft, and to non-owners) |
| POST | `/api/v1/{res}/{id}/deactivate` | state → inactive |
| POST | `/api/v1/{res}/{id}/activate` | state → active |
| POST | `/api/v1/{res}/{id}/assign` | change owner (user or team) |
| GET | `/api/v1/{res}/{id}/audit` | field-level history from `wf_field_audit` |
| GET | `/api/v1/{res}/{id}/timeline` | transitions + notes + tasks, merged chronologically |
| GET | `/api/v1/{res}/{id}/notes` · POST | notes and attachments |
| GET | `/api/v1/{res}/{id}/workflow` | current status, available transitions, submission/approval/rejection chain |

### 3.2 Related-collection operations (the sub-grid "Add Existing…" behaviour)

Exposed for every many-to-many relationship listed in Document 2 §10 (all 61), and additionally for
the 1:N child collections the legacy forms surface as related-record lists (`performance-indicators
→ actions`, `performance-indicators → pi-results`, `goals → objectives`, `goals → strategies`,
`objectives → strategies`, `fiscal-years → strategies`, `fiscal-years → pi-results`,
`priority-questions → approval-queue`), each marked **(1:N)** below. The two behave identically in the UI, but a POST to
a 1:N collection **re-parents** the child row instead of inserting a junction row, and DELETE nulls
the child's foreign key instead of removing a junction row. Slugs below are annotated with their
legacy relationship name wherever the mapping is not obvious:

| Method | Path |
|---|---|
| GET | `/api/v1/{res}/{id}/{relationship}` |
| POST | `/api/v1/{res}/{id}/{relationship}` — body `{"ids":[…]}` (**Add Existing…**) |
| DELETE | `/api/v1/{res}/{id}/{relationship}/{related_id}` (**Remove**) |

Relationship slugs per resource:

| Resource | Relationship slugs |
|---|---|
| `performance-indicators` | `contributing-business-lines`, `contributing-product-lines`, `contributing-offices`, `contributing-major-programs`, `other-contributing-programs`, `goals`, `objectives`, `strategies`, `actions` (1:N), `pi-results` (1:N `nrc_nrc_performanceindicatorfiscalyear_Perfor` — the form sub-grid), `pi-results-linked` (`nrc_manyupdates`), `related-enterprise-risks`, `related-accomplishments`, `related-priorities`, `related-risk-updates`, `updates-to-performance-indicators` (`nrc_manypis`) |
| `pi-results` | `contributing-business-lines`, `contributing-product-lines`, `contributing-offices`, `contributing-major-programs`, `other-contributing-programs`, `revision-history`, `performance-indicators` (`nrc_manyupdates`), `related-performance-indicators` (`nrc_manypis`) |
| `enterprise-risks` | `related-performance-indicators`, `applicable-fiscal-years`, `contributing-offices`, `contributing-major-programs`, `other-contributing-programs`, `contributing-business-lines`, `contributing-product-lines`, `impacted-strategies`, `risk-updates` (1:N — data model only; no Enterprise Risk form surfaces it) |
| `risk-updates` | `other-contributing-programs`, `other-contributing-business-lines`, `other-contributing-product-lines`, `contributing-offices`, `contributing-major-programs`, `related-performance-indicators` |
| `accomplishments` | `contributing-business-lines`, `contributing-product-lines`, `other-related-performance-indicators`, `contributing-major-programs`, `other-contributing-programs`, `contributing-offices` |
| `priorities` | `contributing-business-lines`, `contributing-product-lines`, `contributing-major-programs`, `other-contributing-programs`, `contributing-offices`, `related-performance-indicators` |
| `positive-change-management` | `contributing-business-lines`, `contributing-product-lines`, `contributing-major-programs`, `contributing-programs`, `division-owners`, `contributing-offices` |
| `goals` | `objectives` (1:N), `strategies` (1:N), `performance-indicators`, `applicable-fiscal-years`, `offices` |
| `objectives` | `strategies` (1:N), `performance-indicators`, `applicable-fiscal-years`, `external-factors` |
| `strategies` | `performance-indicators`, `applicable-fiscal-years`, `external-factors`, `enterprise-risks` |
| `fiscal-years` | `goals`, `strategies` (1:N), `objectives`, `pi-results` (1:N) |
| `external-factors` | `objectives`, `strategies` |
| `definitions` | `business-lines`, `product-lines`, `data-sources` (multi-select junction — Document 2 §10.11) |
| `offices` | `divisions`, `goals`, `performance-indicators`, `pi-results`, `enterprise-risks`, `risk-updates`, `accomplishments`, `priorities`, `positive-change-management`, `action-measures` |
| `divisions` | `offices` |
| `business-lines` | `product-lines`, `performance-indicators`, `pi-results`, `enterprise-risks`, `risk-updates`, `accomplishments`, `priorities`, `positive-change-management`, `definitions` |
| `product-lines` | `business-lines`, `performance-indicators`, `pi-results`, `enterprise-risks`, `risk-updates`, `accomplishments`, `priorities`, `positive-change-management`, `definitions` |
| `products` | `evaluations`, `research-activities` |
| `major-programs` | `performance-indicators`, `pi-results`, `enterprise-risks`, `risk-updates`, `accomplishments`, `priorities`, `positive-change-management` |
| `contributing-programs` | `performance-indicators`, `pi-results`, `enterprise-risks`, `risk-updates`, `accomplishments`, `priorities`, `positive-change-management` — the reverse ends of the seven junctions the QPR resources above reach as *(Other) Contributing Programs*, so the record can name what contributes through it |
| `action-measures` | `leading-offices` (`nrc_ActionMeasure_nrc_Office`) |
| `evaluations` / `research-activities` | `products` |
| `priority-questions` | `approval-queue` (1:N) |

### 3.3 Complete resource list

**Strategic Plan** — `/goals`, `/objectives`, `/strategies`, `/performance-goals`,
`/external-factors`, `/definitions`, `/fiscal-years`, `/signposts`, `/key-areas`

**Organisation** — `/offices`, `/divisions`, `/organizations`, `/business-lines`, `/product-lines`,
`/products`, `/major-programs`, `/contributing-programs`, `/office-goals`

**Performance Management** — `/performance-indicators`, `/pi-results`, `/planned-measures`,
`/enterprise-risks`, `/risk-updates`, `/accomplishments`, `/priorities`,
`/positive-change-management`, `/action-measures`

**Evidence Building** — `/priority-questions`, `/evaluations`, `/research-activities`

**Workflow** — `/submissions`, `/approvals`, `/rejections`, `/approval-queues`, `/tasks`

**Identity/Admin** — `/users`, `/teams`, `/business-units`, `/positions`, `/security-roles`,
`/settings`, `/view-definitions`, `/form-definitions`

### 3.4 Resource-specific sub-resources

| Path | Purpose |
|---|---|
| `GET/PUT /api/v1/pi-results/{id}/periods` | the five per-period measurement blocks |
| `PUT /api/v1/pi-results/{id}/periods/{period}` | update one quarter (`q1`…`q4`, `annual`) |
| `GET/PUT /api/v1/pi-results/{id}/quarters` | the multi-select Quarter(s) |
| `GET/PUT /api/v1/accomplishments/{id}/quarters` | multi-select Quarter(s) |
| `GET/PUT /api/v1/priorities/{id}/quarters` | multi-select Quarter(s) |
| `GET /api/v1/performance-indicators/{id}/revision-chain` | the full New→Revised lineage |
| `GET /api/v1/performance-indicators/{id}/prefill?previous_pi_id=…` | the 22-field auto-fill payload (§15.5.5) |
| `GET /api/v1/accomplishments/prefill?primary_related_pi_id=…` | Goal/Objective/Strategy auto-fill payload |
| `GET /api/v1/risk-updates/previous-quarter?enterprise_risk_id=…&fiscal_year_id=…&quarter=…` | the last-quarter likelihood/consequence carry-forward payload |
| `POST /api/v1/planned-measures/{id}/deliverable` | upload the deliverable file (≤ 32 MB) |
| `GET /api/v1/planned-measures/{id}/deliverable` | download |

### 3.5 Lookup endpoints (type-ahead pickers)

`GET /api/v1/lookups/{entity}?q=…&limit=25&filter[...]` returns `{id, display, secondary}` triples.

Cascading filters that must be honoured. The first two are as-built, declared on the form control as
`DependentAttributeName` + `FilterRelationshipName` (11 such controls across Accomplishment,
Enterprise Risk, Evaluations, Performance Indicator, PCM and Priorities Update); the last two
reproduce the named legacy lookup views. Rows marked **[NEW]** have no as-built equivalent — the
legacy solution filters lookups only declaratively and, for three sub-grid lookups, through the
(unwired) scripts of §15.5.3.

| Lookup | Filtered by |
|---|---|
| Objective | selected Goal |
| Strategy | selected Objective |
| Product **[NEW]** | selected Product Line |
| Product Line **[NEW]** | selected Business Line |
| Division **[NEW]** | selected Office |
| Previous PI **[NEW]** | same Business Line / Office, status ≠ Versioned-revised — the legacy lookup is unfiltered; `nrc_autofillPI` only copies 22 fields off the chosen PI (§3.4 `/performance-indicators/{id}/prefill`) |
| Performance Indicator (on a PI Result) | **"Performance Indicators Available for Results"** — status not in (Discontinued, Cancelled/closed, Versioned/revised) **and** Indicator Status ≠ Discontinued |
| Enterprise Risk (on a Risk Update) | **"Enterprise Risks Available for Update"** — status not in (Discontinued, Closed/cancelled) **and** Risk Status ≠ Discontinued |

In the legacy system Goal→Objective→Strategy integrity is additionally enforced post-hoc by the
`nrc_check*Objective` / `nrc_check*Strategy` sequence-comparison notifications (§15.5.5, §15.3) —
which is why those messages exist.

---

## 4. Workflow and command endpoints

### 4.1 Bulk commands

| Method | Path | Body | Applies to |
|---|---|---|---|
| POST | `/api/v1/workflow/submit` | `{"record_type":"risk_update","ids":[…]}` | all 7 QPR types |
| POST | `/api/v1/workflow/approve` | same | all 7 |
| POST | `/api/v1/workflow/return` | same | all 7 |
| POST | `/api/v1/workflow/propose-discontinue` | `{"record_type":"enterprise_risk"\|"performance_indicator","ids":[…]}` | Enterprise Risk, PI |
| POST | `/api/v1/workflow/discontinue` | same | Enterprise Risk, PI — **EDO only** |
| POST | `/api/v1/workflow/deny-discontinue` | same | Enterprise Risk, PI — **EDO only** |
| POST | `/api/v1/workflow/reopen-pi-results` | `{"fiscal_year_id": "…"}` | PI Result — **EDO only**; re-opens every finalized result for the given (current) fiscal year |
| POST | `/api/v1/performance-indicators/flag-carryover` | `{"ids":[…]}` | PI |
| POST | `/api/v1/performance-indicators/unflag-carryover` | `{"ids":[…]}` | PI |

### 4.2 Bulk response fields

| Field | Type | Notes |
|---|---|---|
| `requested` | integer | number of ids submitted |
| `succeeded` | integer | |
| `failed` | integer | |
| `results` | array | one entry per id |
| `results[].id` | uuid | |
| `results[].code` | string | the human-readable record identifier |
| `results[].status` | `ok` \| `error` | |
| `results[].new_status_reason` | string | present when `ok` |
| `results[].error` | object | `code` and `message`, present when `error` |
| `correlation_id` | uuid | ties every resulting audit row together |

The React client renders the success alert when `failed = 0` and an itemised error dialog otherwise —
matching the legacy alert-dialog behaviour (§15.2).

### 4.3 Per-record workflow endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/{res}/{id}/workflow` | current state, allowed transitions for the caller, submission / approval / rejection chain, approver comments |
| POST | `/api/v1/{res}/{id}/submit` | single-record submit |
| POST | `/api/v1/{res}/{id}/approve` | single-record approve |
| POST | `/api/v1/{res}/{id}/return` | single-record return; body `{"comments":"…"}` writes to the record's Comments field |
| GET | `/api/v1/{res}/{id}/approval-queue` | ordered approver chain |
| PUT | `/api/v1/{res}/{id}/approval-queue` | replace the chain |

### 4.4 Transition guard matrix (server-enforced)

| Command | Allowed when | Caller must be |
|---|---|---|
| Submit | `status_reason ∈ {draft, revision}` | the record owner (user or a member of the owning team) |
| Approve | `status_reason = pending_approval` | the record owner (the approver), and **not** the record's creator |
| Return | `status_reason = pending_approval` | the record owner (the approver) |
| Propose discontinue | `status_reason = finalized` | any submitter |
| Discontinue / Deny | Indicator/Risk Status = `pending_discontinue` | EDO role |
| Re-open PI Results | `status_reason = finalized` and `fiscal_year = current FY` | EDO role |
| Flag carry-over | any | any submitter |
| Unflag carry-over | `review_for_carry_over = true` (legacy: the *Review for carry-over* view only) | any submitter |

### 4.5 Side effects each command must perform

Exactly as specified in Document 1 §6.3–6.5:

| Command | Side effects |
|---|---|
| **Submit** | update status + owner + submitter fields · create `wf_submission` (with `resubmission=true` when the prior status was `revision`) · close active `wf_rejection` rows · write `wf_workflow_transition` |
| **Approve** | create `wf_approval` · close the latest active `wf_submission` with `approved=true` · set status `finalized`, state inactive, owner back to submitter · PI also sets Indicator Status `active`; Enterprise Risk also sets Risk Status `active` · write transition |
| **Return** | create `wf_rejection` · close the latest active `wf_submission` with `returned=true` · set status `revision`, state active, owner back to submitter · write transition |
| **Propose discontinue** | PI → Indicator Status `pending_discontinue`; Risk → Risk Status `pending_discontinue` |
| **Discontinue** | PI → Indicator Status `discontinued`, state inactive, status `discontinued`; Risk → Risk Status `discontinued`, state inactive, status `discontinued` |
| **Deny discontinue** | PI → Indicator Status `active`, state inactive, status `finalized`; Risk → Risk Status `active`, state inactive, status `finalized` |
| **Re-open** | PI Result → status `draft`, state active — only when its fiscal year is the current one |
| **Flag / Unflag** | PI → `review_for_carry_over` true/false |
| **Create a Revised PI** | previous PI → Indicator Status `discontinued`, state inactive, status `versioned_revised` |

---

## 5. Metadata endpoints

Because the legacy application is metadata-driven (334 views, 115 forms), the rebuild should serve the
same metadata rather than hard-coding it.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/metadata/entities` | list of entities with labels, plural labels, primary field |
| GET | `/api/v1/metadata/entities/{entity}` | attributes with type, label, required level, max length, enum, lookup target |
| GET | `/api/v1/metadata/entities/{entity}/views` | the saved views the caller may use |
| GET | `/api/v1/metadata/entities/{entity}/views/{view}` | filter, columns, sort |
| GET | `/api/v1/metadata/entities/{entity}/forms` | form layouts (tabs → sections → controls) |
| GET | `/api/v1/metadata/option-sets` | all 36 global enumerations plus entity-local ones |
| GET | `/api/v1/metadata/option-sets/{name}` | one enumeration |
| GET | `/api/v1/metadata/business-rules/{entity}` | declarative visibility / requirement / lock rules (Document 1 §8.2) |
| GET | `/api/v1/metadata/commands/{entity}?view={view}` | which commands to render for the caller on that view |
| GET | `/api/v1/metadata/navigation` | the sitemap for the caller's apps |

`GET /api/v1/metadata/commands/...` replaces the legacy per-entity JavaScript. Each command it
returns carries:

| Field | Notes |
|---|---|
| `id` | e.g. `submit` |
| `label` | button caption, e.g. *Submit for Approval* |
| `icon` | icon token |
| `min_selection` / `max_selection` | selection rules — `min_selection = 0` for *Open PI child records for next quarter*, which requires **no** selection |
| `confirm` | confirmation dialog text with an `{n}` placeholder (§15.2) |
| `success` | success alert text (§15.2) |
| `endpoint` | the command endpoint to call |
| `requires_role` | e.g. `EDO User` for the discontinue and re-open commands |

Example for `entity=risk_update&view=my-drafts`: a single command `submit`, labelled
*Submit for Approval*, minimum selection 1, confirmation *"Submit {n} selected Risk Updates?"*,
success *"Risk Update(s) successfully submitted for approval."*, calling
`POST /api/v1/workflow/submit`.

---

## 6. Analytics endpoints

These serve the 19 dashboard pages described in Document 1 §9. All accept the **global filter object**.

### 6.1 Global filter parameters (the slicer bar)

| Parameter | Type | Slicer |
|---|---|---|
| `fiscal_year_ids` | uuid list | FY Filter |
| `quarters` | enum list | Qtr filter |
| `business_line_ids` | uuid list | BL filter |
| `product_line_ids` | uuid list | PL filter |
| `office_ids` | uuid list | Office filter |
| `division_ids` | uuid list | Division filter |
| `major_program_ids` | uuid list | Major program filter |
| `contributing_program_ids` | uuid list | Contributing program filter |
| `report_levels` | enum list | Report Level filter |
| `goal_ids` | uuid list | Goal slicer (Strategic Planning Home) |
| `view_toggle` | string | the View Toggle slicer |

Default exclusions applied server-side unless overridden (Document 1 §9.2):
Office excludes `null`, `Agencywide`, `N/A`; Fiscal Year excludes 2027–2030 and `null` (Historical Trends also excludes 2026); Business Line, Product
Line, Major Program and Contributing Program exclude `null`.

### 6.2 Endpoints

| Method | Path | Serves page |
|---|---|---|
| GET | `/api/v1/analytics/strategic-planning-home` | 1 — goal card, objectives table, 5 KPI counts. **[NEW]** `?plan=2022-2026` names the strategic plan to show; without it, the plan the dashboards report on |
| GET | `/api/v1/analytics/performance-management-home` | 2 — 3 KPI counts, risks-by-PSAT donut, PI-by-result donut, percentage pie |
| GET | `/api/v1/analytics/historical-trends` | 3 — risk trend and PI-result trend by reporting period |
| GET | `/api/v1/analytics/accomplishments` | 4 — totals, CBJ/APPR count, BL/PL count, trend, list + description |
| GET | `/api/v1/analytics/positive-change-management` | 5 — trend, counts, list + description |
| GET | `/api/v1/analytics/priorities` | 6 — Goal 1/2/3 counts, total, trend, rank+description table |
| GET | `/api/v1/analytics/risks/overview` | 7 — inherent donut, residual pie, trend |
| GET | `/api/v1/analytics/risks/list?psat=psat\|non_psat\|agencywide` | 8, 9, 10 — risk list + selected-risk detail cards |
| GET | `/api/v1/analytics/risks/heatmap?mitigation_type=inherent\|residual` | 11, 12 — nine-cell matrix with per-cell risk points |
| GET | `/api/v1/analytics/risks/{risk_update_id}/quadrant` | 14 — View Quadrant: single-risk drill-through (the risk's scatter point plus Consequence Text and Likelihood Text cards); the legacy page also carries a page filter `PSAT? = PSAT` |
| GET | `/api/v1/analytics/risks/{risk_update_id}/qpr-view` | 15 — the QPR meeting slide payload including colour tokens |
| GET | `/api/v1/analytics/performance-indicators/overview` | 16 — trend, pie, donut, indicator table |
| GET | `/api/v1/analytics/performance-indicators/agencywide-matrix` | 17 — Product Line × Office matrix with status colours |
| GET | `/api/v1/analytics/performance-indicators/{pi_id}/profile` | 18 — profile cards + target/result trend |
| GET | `/api/v1/analytics/tooltips/risk/{risk_update_id}` | 13 — heat-map tooltip |
| GET | `/api/v1/analytics/tooltips/goal/{goal_id}` | 19 — goal tooltip |
| GET | `/api/v1/analytics/glossary?terms=…` | glossary hover-over definitions |
| GET | `/api/v1/analytics/refresh-status` | last/next refresh (reports "live" in the rebuilt system) |
| GET | `/api/v1/analytics/slicer-options` | populates every slicer with the documented exclusions applied |

### 6.3 Heat-map response fields

| Field | Notes |
|---|---|
| `mitigation_type` | `inherent` or `residual` — set by the toggle |
| `cells` | exactly nine entries: LL · LM · LH · ML · MM · MH · HL · HM · HH |
| `cells[].risk_level` | the two-letter code |
| `cells[].likelihood`, `cells[].consequence` | `low` · `medium` · `high` |
| `cells[].count` | number of risks in the cell |
| `cells[].color` | the cell's hex colour (§16.3) |
| `cells[].points` | the risks plotted in the cell |
| `points[].risk_update_id`, `risk_code`, `risk_title` | identity |
| `points[].x`, `points[].y` | scatter coordinates |
| `points[].risk_index` | list ordering |
| `points[].risk_color` | `Green` · `Yellow` · `Red` |

### 6.4 QPR Risk View response fields

| Field | Notes |
|---|---|
| `risk_code`, `risk_title` | identity |
| `primary_column` | the `"RISK {risk code}: {risk title}"` composite shown as the slide heading — the `RISK ` prefix is part of the stored value |
| `risk_description` | |
| `associated_pis` | list of related Performance Indicator codes and titles |
| `inherent` | object: `likelihood`, `likelihood_description`, `likelihood_left_color`, `likelihood_right_color`, `consequence`, `consequence_description`, `consequence_left_color`, `consequence_right_color`. Left colour = the previous quarter's level, right colour = this quarter's (Document 2 §14.5) |
| `residual` | object with the same eight fields |
| `current_risk_response` | MANAGE (Current Risk Response) |
| `proposed_risk_response` | ACT (Proposed Risk Response) |
| `risk_monitoring`, `informed_monitoring` | |
| `budget_strings` | |
| `accepted` | the "risk accepted" flag |

Colour tokens map to the hex values in Document 1 §9.4.

### 6.5 Export endpoints

| Method | Path | Output |
|---|---|---|
| GET | `/api/v1/analytics/{page}/export?format=xlsx\|csv\|pdf` | the page's underlying data or a rendered PDF |
| GET | `/api/v1/{res}/export?view=…&format=xlsx\|csv` | any list view |
| GET | `/api/v1/{res}/{id}/export?format=pdf\|docx` | a single record (supports the SES Word-export requirement) |

### 6.6 Natural-language query **[NEW — replaces the Power BI Q&A visual]**

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/analytics/query` | body `{"question": "how many risks in FY24 Q3 for NRR?"}` → structured answer plus the visual spec used to render it |
| GET | `/api/v1/analytics/query/suggestions` | seeded example questions |

The SPA System Architecture Document records this as an existing capability:
*"Natural Language 'Smart' Query capability for end users to ask questions and get insights into the
available data."*

---

## 7. Notification and task endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/tasks?view=my-tasks` | open tasks owned by the user or their teams, newest first |
| GET | `/api/v1/tasks/{id}` | task detail with linked submissions / approvals / rejections |
| POST | `/api/v1/tasks/{id}/complete` | close the task |
| GET | `/api/v1/notifications` | the user's notification feed |
| POST | `/api/v1/notifications/{id}/read` | mark read |
| GET | `/api/v1/notifications/preferences` · PUT | per-channel opt-in (in-app / e-mail / Teams) **[NEW]** |

### 7.1 Background jobs the API tier must run

| Job | Cadence | Behaviour (Document 1 §6.6) |
|---|---|---|
| `create_submission_tasks` | every few minutes | group pending submissions by (submitter, record type) into one task per group |
| `create_approval_tasks` | same | same over approvals |
| `create_rejection_tasks` | same | same over rejections |
| `dispatch_notifications` | continuous | send queued in-app / e-mail / Teams messages with the correct deep link |
| `close_completed_tasks` | hourly (as-built: every 4 minutes) | close tasks whose linked workflow rows are all inactive |
| `recompute_rollups` | hourly | Goal objective/strategy/indicator/risk counts |
| `refresh_analytics` | on write + periodic | rebuild any `analytics_*_snapshot` summary table (Document 2 §14); the plain analytic views are live and need no refresh — SQLite has no materialised views |
| `maintain_database` | hourly; monthly archive | online backup with `VACUUM INTO`, WAL checkpoint and `PRAGMA optimize`; once a month, move audit history past the retention window into the yearly archive file (Document 2 §1.2, §9.7) **[NEW — SQLite edition]** |

---

## 8. Administration endpoints

| Method | Path | Purpose |
|---|---|---|
| GET/POST/PATCH/DELETE | `/api/v1/users` | user administration |
| POST | `/api/v1/users/{id}/roles` · DELETE `/{role_id}` | grant / revoke roles (the "OEDO Admin also retain the ability to add/revoke other OEDO Admin users' privileges" requirement) |
| GET/POST/PATCH | `/api/v1/teams` | team (office group) administration |
| POST | `/api/v1/teams/{id}/members` · DELETE `/{user_id}` | membership |
| GET/POST/PATCH | `/api/v1/business-units` | business-unit hierarchy |
| GET/PATCH | `/api/v1/security-roles/{id}/privileges` | privilege matrix editing |
| GET/PUT | `/api/v1/settings` | application settings (`core_app_setting`) |
| GET/POST/PUT/DELETE | `/api/v1/view-definitions` | saved views (public and personal) |
| GET/PUT | `/api/v1/form-definitions` | form layouts |
| GET | `/api/v1/admin/audit?table=…&record_id=…&from=…&to=…` | audit search |
| GET | `/api/v1/admin/jobs` · POST `/{job}/run` | background-job status and manual run |
| GET | `/api/v1/admin/health` · `/ready` | liveness / readiness |

---

## 9. Import / export endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/import/jobs` | start an import (multipart: file + entity + mapping profile) |
| GET | `/api/v1/import/jobs/{id}` | progress, row counts, error report |
| GET | `/api/v1/import/jobs/{id}/errors?format=xlsx` | downloadable error file |
| GET | `/api/v1/import/templates/{entity}?format=xlsx` | a template workbook with the correct columns |
| POST | `/api/v1/import/validate` | dry-run validation (used for the migration reconciliation checks in Document 2 §15.5) |
| POST | `/api/v1/records/{res}/{id}/duplicate` | **[NEW]** duplicate a record into a new fiscal year — the "duplicate records from year to year" request in `SPA+-Improvements.doc` |

---

## 10. Error model

All errors return RFC 9457 problem details plus a machine code.

| HTTP | Code | When |
|---|---|---|
| 400 | `VALIDATION_FAILED` | field-level validation; `errors[]` lists `{field, code, message}` |
| 400 | `CHARACTER_LIMIT_EXCEEDED` | a text field exceeds its documented limit |
| 400 | `HIERARCHY_MISMATCH` | *"This Objective does not fall under the Goal selected above."* / *"This Strategy does not fall under the Objective selected above."* |
| 400 | `RANGE_FIELDS_NOT_APPLICABLE` | min/max/lower/upper supplied for a non-Range indicator (or target/operator for a Range indicator) |
| 400 | `RESULT_NOT_APPLICABLE` | a result value supplied for a period marked Not Applicable |
| 400 | `ACT_RESPONSE_REQUIRED` | ACT (Proposed Risk Response) missing while the risk is not accepted |
| 400 | `PREVIOUS_PI_REQUIRED` | Change Type = Revised without a PI being revised |
| 400 | `RELATED_PI_REQUIRED` | the related-PI sub-grid is empty while "PIs not applicable" is unchecked |
| 401 | `UNAUTHENTICATED` | no/expired session |
| 403 | `FORBIDDEN` | privilege check failed |
| 403 | `INSUFFICIENT_PRIVILEGE_FOR_FIELD_VALUE` | *"You do not have the necessary priviledges to create this record with this field value."* (CBJ/APPR or Agencywide PI by a non-EDO user) |
| 403 | `RECORD_LOCKED` | edit/delete attempted outside Draft / Revision |
| 403 | `NOT_RECORD_OWNER` | submit attempted by a non-owner |
| 403 | `APPROVER_IS_CREATOR` | approve attempted by the record's creator |
| 404 | `NOT_FOUND` | missing, or not visible to the caller under the row-visibility predicate (Document 2 §13) |
| 409 | `CONCURRENCY_CONFLICT` | `If-Match` row-version mismatch |
| 409 | `INVALID_STATE` | transition not allowed from the current status |
| 409 | `DUPLICATE_CODE` | generated or supplied identifier already exists |
| 413 | `FILE_TOO_LARGE` | attachment over 32 MB |
| 422 | `BULK_PARTIAL_FAILURE` | some ids in a bulk command failed (body carries the per-id results) |
| 429 | `RATE_LIMITED` | |
| 500 | `INTERNAL_ERROR` | |

---

# PART B — UI

## 11. Application shell and navigation

### 11.1 Shell layout

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ Header:  NRC logo │ App switcher (Strategic Planning ▾ / Performance Mgmt)      │
│          Global search │ Notifications 🔔 │ Help (?) │ User avatar ▾            │
├──────────────┬─────────────────────────────────────────────────────────────────┤
│ Left nav     │  Command bar:  + New │ Submit │ Approve │ Return │ … │ ⋯         │
│ (collapsible │  View selector: [ MY Risk Updates in Draft/Revision  ▾ ]         │
│  groups)     │  Search this view  │ Filter │ Columns │ Export                   │
│              ├─────────────────────────────────────────────────────────────────┤
│              │  Grid / Form / Dashboard                                          │
│              │                                                                  │
├──────────────┴─────────────────────────────────────────────────────────────────┤
│ Footer: environment badge · build version · Section 508 statement              │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Strategic Planning workspace navigation (reproduces the as-built sitemap)

| Group | Items | Route |
|---|---|---|
| **At a glance…** | Dashboards | `/sp/dashboards` |
| | My To-do List | `/sp/my-todo` |
| **Other Modules** | Performance Management | `/pm` |
| **Strategic Planning** | Goals · Objectives · Strategies · Performance Goals | `/sp/goals`, `/sp/objectives`, `/sp/strategies`, `/sp/performance-goals` |
| **Organizational** | Product Lines · Business Lines · Offices · Major Programs · Contributing Programs and Activities · Products | `/sp/product-lines`, `/sp/business-lines`, `/sp/offices`, `/sp/major-programs`, `/sp/contributing-programs`, `/sp/products` |
| **Details** | Definitions · External Factors · Organizations | `/sp/definitions`, `/sp/external-factors`, `/sp/organizations` |

Create-privilege gating (as in the source sitemap): Goals, Objectives, Strategies, Product Lines,
Business Lines, Offices, Products, Definitions and External Factors show only when the user holds the
matching Create privilege.

### 11.3 Performance Management workspace navigation

| Group | Items | Route |
|---|---|---|
| **At a glance…** | My To-do List · Performance Review · User Guides · FAQ | `/pm/my-todo`, `/pm/dashboards`, `/pm/user-guide`, `/pm/faq` |
| **Other Modules** | Strategic Planning | `/sp` |
| **Performance Management** | Performance Indicators · Enterprise Risks · Priorities Updates | `/pm/performance-indicators`, `/pm/enterprise-risks`, `/pm/priorities` |
| **Quarterly Data** | PI Updates · Risk Updates · Accomplishments · Positive Change Management | `/pm/pi-results`, `/pm/risk-updates`, `/pm/accomplishments`, `/pm/positive-change-management` |
| **Admin** | Groups (Teams) · Users | `/pm/admin/teams`, `/pm/admin/users` |

Create-privilege gating (as in the source sitemap): **Admin → Groups (Teams)** (`subarea_38256cab`,
entity `team`) is gated on the Create privilege for **Objective**
(`<Privilege Entity="nrc_objective" Privilege="Create" />`) — an unrelated entity and almost
certainly a configuration error; because only EDO User holds Create on Objective, the item is
EDO-only in practice. **Users** (`subarea_f2451f44`, entity `systemuser`) carries no privilege at
all. Confirm the intended gate with OEDO (Team Create, or a team-administration permission) before
reproducing it; do not ship the Admin group ungated.

### 11.4 Evidence Building workspace **[NEW — the data model exists, the UI never shipped]**

| Group | Items | Route |
|---|---|---|
| **Evidence Building** | Priority Questions · Evaluations · Research Activities | `/eb/priority-questions`, `/eb/evaluations`, `/eb/research-activities` |

### 11.5 Route map

| Pattern | Screen |
|---|---|
| `/{workspace}/{entity}` | list view |
| `/{workspace}/{entity}?view={slug}` | list view with a named view (the deep-link targets in Document 1 §6.7) |
| `/{workspace}/{entity}/new` | create form |
| `/{workspace}/{entity}/{id}` | edit form |
| `/{workspace}/{entity}/{id}/{tab}` | a specific form tab |
| `/{workspace}/dashboards/{page}` | dashboard page |
| `/{workspace}/my-todo` | task list |

### 11.6 Client stack (React) **[React edition]**

| Concern | Choice |
|---|---|
| Language and build | TypeScript in strict mode, built with Vite into static files served from the same origin as `/api/v1`, so no cross-origin configuration is needed |
| Routing | React Router in data-router mode. The §11.5 patterns are its route table and each workspace (`/sp`, `/pm`, `/eb`) is a lazily loaded route module. Route **loaders** perform the permission checks — a workspace, or a create screen, that the user's `GET /me/permissions` does not allow redirects instead of rendering — and the list state (`?view=`, filters, page, sort) lives in the URL, so every list is linkable: the Document 1 §6.7 deep links |
| Server state | TanStack Query. Every API read is a query keyed by resource, view, filters and page; a command (§4) invalidates the queries of the resources it changed, which is how the grid refreshes after Submit / Approve / Return (§15.4). The record's `row_version` travels with the cached record and is sent back as `If-Match` |
| Forms | The form renderer of §12 builds its fields from `GET /metadata/entities/{e}/forms`; field state, dirty tracking and client validation use React Hook Form, and a `VALIDATION_FAILED` response's `errors[]` (§10) is mapped back onto the fields it names |
| Application state | React context for the signed-in user, their permissions and the theme. Nothing else needs a global store: server data lives in the query cache |
| Styling and theming | CSS custom properties carry the light and dark palettes (the §16.3 colours are tokens, not literals); component styles are CSS Modules |
| Dialogs and overlays | The native `<dialog>` element or an accessible primitive that traps focus, closes on `Esc` and returns focus to the control that opened it (§18.1) |
| Testing | Vitest and React Testing Library for components and hooks; the browser suites of Document 4 run unchanged against the built application |

The shared components of §12 are React components of the same names (`ViewSelector`, `DataGrid`,
`CommandBar`, `FormRenderer`, `SubGrid`, …), each driven by the metadata endpoints of §5 rather than
by lists of fields or views written into the client.

---

## 12. Shared UI components

| Component | Behaviour |
|---|---|
| **View selector** | Dropdown listing the entity's public + personal views (grouped). Remembers the last-used view per entity per user. Default view is the one flagged default in metadata. **The bulk commands appear only on the views that allow them** (§15.1) |
| **Data grid** | Server-side paging, sorting, column chooser, column resize, multi-select via checkbox (the legacy radio-button selection becomes a checkbox), row click opens the form, sticky header, virtual scroll |
| **Command bar** | Renders commands from `GET /metadata/commands`; disables when the selection count is below the command's minimum; shows an overflow menu beyond 5 commands |
| **Filter panel** | Per-column filters plus the saved-view predicate shown as removable chips |
| **Quick search** | Debounced `?q=` against the entity's searchable columns |
| **Form renderer** | Renders tabs → sections → controls from `GET /metadata/entities/{e}/forms`; supports 1-, 2- and 3-column sections |
| **Lookup control** | Type-ahead with "press Enter or click 🔍 to browse", inline create where permitted, cascading filters (§3.5) |
| **Multi-select choice** | Chip-based multi-select for Quarter(s) |
| **Sub-grid** | Related-record grid with **⋯ → Add Existing…** opening a right-hand search-and-select panel that supports multi-select, plus **Remove**. Reproduces the User Guide procedure verbatim |
| **Quick-view panel** | Read-only card of a related record (Performance Indicator details on a PI Result — two quick views in the source, drawn as one card; Enterprise Risk details on a Risk Update; the selected Answer on a Priority Question — the control carries two quick-view forms, Evaluation and Research Activity, and resolves by the answer's type; Associated Signpost on a Key Area) |
| **Character counter** | Live "n of m characters" under every limited text field (14 fields in the source) |
| **Rich-text editor** | For Comments and the Evidence Building narrative fields; sanitised on save |
| **Status badge** | Colour-coded Draft / Pending approval / Revision / Finalized / Discontinued / Cancelled |
| **Approver comments banner** | When status is Pending approval or Revision, a prominent banner at the top of the form showing the approver's comments (the legacy "COMMENTS REGARDING SUBMISSION" behaviour) |
| **Timeline panel** | Submissions, approvals, rejections, notes and tasks in one chronological feed |
| **Audit panel** | Field-level change history |
| **Confirmation dialog** | Title, body, Cancel / Confirm; used by every bulk command |
| **Alert dialog** | Success / failure message after a command; 300×200 equivalent |
| **Notification bell** | Unread count, dropdown feed, deep links |
| **Glossary tooltip** | Any word matching a Definition title is underlined; hover shows the definition (the Product-Vision requirement) |
| **Unsaved-changes guard** | Navigation blocker (React Router `useBlocker`, plus a `beforeunload` handler for closing the tab) prompting before navigating away |
| **Save / Save & Close / Save & New** | Standard form actions; **after the first save the related sub-grids become enabled** (the "additional entry tables will appear on the form after saving" behaviour) |

---

## 13. List-view screens

Every list screen has: the view selector, the command bar, quick search, filter panel, column chooser
and export. The tables below give **the exact view names, their filter predicates and their default
columns**, as extracted from the solution. The lifecycle column is shown as "Status" throughout;
its shipped label is "Stage" on nine tables and "Approval Status" on Approval Queue
(Document 2 §2.4).

### 13.1 Performance Indicators — `/pm/performance-indicators`

| View | Filter | Default columns |
|---|---|---|
| **All Performance Indicators** | status ≠ Cancelled/closed | Implementation Year · Indicator Title · Indicator ID · Business Line · Product Line · Office · Change Type · Indicator Status |
| **MY Performance Indicators in Draft/Revision** | owner = me AND status ∈ {Draft, Revision} AND status ≠ Cancelled/closed | Implementation Year · Indicator Title · Indicator ID · Business Line · Office · Product Line · Status |
| **Performance Indicators in Draft/Revision** | status ∈ {Draft, Revision} | as above |
| **Performance Indicators Pending Approval** | status = Pending approval | + Submitter |
| **Performance Indicators Pending MY Approval** | status = Pending approval AND owner = me-or-my-teams | + Submitter |
| **Finalized Performance Indicators** | status = Finalized | Implementation Year · Indicator Title · Indicator ID · Business Line · Office · Product Line · Units |
| **Discontinued Performance Indicators** | status = Discontinued | |
| **Cancelled/closed Performance Indicators** | status = Cancelled/closed | |
| **My Performance Indicators** | owner = me | |
| **My Office's Performance Indicators** | status ≠ Cancelled/closed AND the PI's Office record is owned by me or my teams | Indicator ID · Indicator Title · Business Line · Product Line · Office |
| **Performance Indicators Pending Discontinuance** | Indicator Status = Pending Discontinue AND status ≠ Cancelled/closed | + Units |
| **Review for carry-over** | `review_for_carry_over = true` AND status ≠ Cancelled/closed | as All, ordered by Implementation Year desc |
| **Performance Indicators Available for Results** *(lookup)* | status ∉ {Discontinued, Cancelled/closed, Versioned/revised} AND Indicator Status ≠ Discontinued | Indicator ID · Indicator Title |
| **Performance Requirements View**, **Subgrid View** | internal sub-grid views | |

Commands: **+ New** · **Submit for Approval** (on *MY … in Draft/Revision*) · **Approve** / **Return**
(on *… Pending MY Approval*) · **Propose for discontinuance** (on *Finalized*) · **Discontinue** /
**Deny** (on *… Pending Discontinuance*, EDO only) · **Flag for carry-over** (any PI view) · **Unflag** (on *Review for carry-over* only).

### 13.2 PI Results (PI Updates) — `/pm/pi-results`

| View | Filter | Default columns |
|---|---|---|
| **All PI Results** | status ≠ Cancelled/closed | Indicator ID · Indicator Title (from PI) · Fiscal Year · Quarter(s) · Reporting Office · Reporting Business Line · Product Line · Status |
| **MY PI Results in Draft/Revision** | owner = me AND status ∈ {Draft, Revision} | Fiscal Year · Indicator ID · Indicator Title · Reporting Office · Business Line · Product Line · Q1–Q4 Results · Annual Results · Status |
| **PI Results in Draft/Revision** | status ∈ {Draft, Revision} | as above |
| **PI Results Pending Approval** | status = Pending approval | + Submitter |
| **PI Results Pending MY Approval** | status = Pending approval AND owner = me-or-my-teams | + Submitter |
| **Finalized PI Results** | status = Finalized | Fiscal Year · Indicator ID · Performance Indicator · Business Line · Office · Product Line · Q1–Q4 Results · Annual Results |
| **Cancelled/closed PI Results** | status = Cancelled/closed | |
| **My PI Results** | (owner = me OR submitter = me) AND status ≠ Cancelled/closed | Indicator ID · Title (from PI) · Fiscal Year · Quarter(s) · Q1–Q4 **Raw Data** · Annual Raw Data · Status, ordered Fiscal Year asc — the only list view that shows the raw-data columns rather than the results columns |
| **My Performance Indicators** | state = Active AND owner = me | |
| **My Offices' PI Results** | the related Office is owned by me or my teams | |
| **My Previously Submitted Entries** | `submitter = me` AND status ∈ {Finalized, Pending approval, Revision, Cancelled/closed} | Indicator ID · Indicator Title · Fiscal Year · Quarter(s) · Modified On |
| **All Results View** *(note the trailing space in the source name)* | status ≠ Cancelled/closed | Fiscal Year · Quarter(s) · Indicator ID · Reporting Business Line · Product Line · Reporting Office · Q1–Q4 Results, ordered Fiscal Year asc |
| **Finalized Results View** | status ≠ Cancelled/closed AND **status ≠ Finalized** | as All Results View **+ Annual Results**, ordered Fiscal Year desc |

> **As-built defect — do not reproduce blindly.** Despite its name, *Finalized Results View*
> **excludes** Finalized rows (`statuscode ne 2`); it is wired into the app module as a grid view
> picker option (`AppModuleComponent` type 26). Confirm with OEDO whether the name or the filter is
> the mistake before rebuilding it.

Commands: **+ New** · **Submit for Approval** · **Approve** / **Return** ·
**Open PI child records for next quarter** (on *Finalized PI Results*, EDO only, **enabled when no
rows are selected**).

### 13.3 Enterprise Risks — `/pm/enterprise-risks`

| View | Filter | Default columns |
|---|---|---|
| **All Enterprise Risks** | status ≠ Closed/cancelled | Risk ID · Risk Title · Originating Fiscal Year · Originating Quarter · Office · Business Line · Product Line · Status |
| **MY Enterprise Risks in Draft/Revision** | owner = me AND status ∈ {Draft, Revision} | Originating Fiscal Year · Risk ID · Risk Title · Business Line · Product Line · Status |
| **Enterprise Risks in Draft/Revision** | status ∈ {Draft, Revision} | |
| **Enterprise Risks Pending Approval** | status ∈ {Pending approval (875670001), 875670002 — see note} AND status ≠ Closed/cancelled | Originating Fiscal Year · Risk Title · Risk ID · Business Line · Product Line · Submitter |
| **Enterprise Risks Pending MY Approval** | as above AND owner = me-or-my-teams | as above |
| **Finalized Enterprise Risks** | status = Finalized | |
| **Discontinued Enterprise Risks** | status = Discontinued | |
| **Cancelled/closed Enterprise Risks** | status = Closed/cancelled | |
| **Enterprise Risks Pending Discontinuance** | Risk Status = Pending Discontinue | |
| **My Enterprise Risks** | owner = me | |
| **My Office's Enterprise Risks** | the risk's Office is owned by me or my teams | |
| **Enterprise Risks Available for Update** *(lookup)* | status ∉ {Discontinued, Closed/cancelled} AND Risk Status ≠ Discontinued | Risk ID · Risk Title |

> **Migration note.** The shipped FetchXML for both *Pending Approval* views ORs in
> `statuscode = 875670002` and prefixes `statuscode ≠ 875670003`. 875670002 is **not a member of the
> Enterprise Risk status option set today**: the 2022–23 metadata cache shows this table once carried
> a two-stage model — 875670001 *Pending intermediate approval* and 875670002 *Pending final
> approval* — later collapsed to a single 875670001 *Pending approval* with 875670002 removed. The
> two views were never rewritten. Do not implement the view as a single-value equality test, and
> profile the migrated data for rows still holding 875670002 before deciding how they map
> (Document 1 §17.3).

Commands: **+ New** · **Submit for Approval** · **Approve** / **Return** ·
**Propose for discontinuance** (on *Finalized*) · **Discontinue** / **Deny discontinuance**
(on *… Pending Discontinuance*, EDO only).

### 13.4 Risk Updates — `/pm/risk-updates`

| View | Filter | Default columns |
|---|---|---|
| **All Risk Updates** | status ≠ Cancelled/closed | Entry ID · Enterprise Risk · Fiscal Year · Quarter(s) · Reporting Office · Business Line (from risk) · Product Line (from risk) · Office (from risk) · Status, ordered Fiscal Year desc, Quarter desc |
| **MY Risk Updates in Draft/Revision** | owner = me AND status ∈ {Draft, Revision} AND status ≠ Cancelled/closed | Fiscal Year · Quarter(s) · Entry ID · Enterprise Risk · Business Line (from risk) · Product Line (the update's own) · Office (from risk) · Status, ordered Fiscal Year desc, Quarter desc |
| **Risk Updates in Draft/Revision** | status ∈ {Draft, Revision} | |
| **Risk Updates Pending Approval** | status = Pending approval AND status ≠ Cancelled/closed | + Submitter |
| **Risk Updates Pending MY Approval** | status = Pending approval AND owner = me-or-my-teams | + Submitter |
| **Finalized Risk Updates** | status = Finalized | |
| **Cancelled/closed Risk Updates** | status = Cancelled/closed | |
| **My Risk Updates** | owner = me | |
| **My Offices' Risk Updates** | the parent risk's Office is owned by me or my teams | |
| **Risk Outlooks** | status ≠ Cancelled/closed | Entry ID · Risk Outlook · MANAGE (Current Risk Response) QPR Description · ACT (Proposed Risk Response) QPR Description · Inherent Likelihood · Inherent Consequence · Residual Likelihood · Residual Consequence |

Commands: **+ New** · **Submit for Approval** · **Approve** / **Return**.

### 13.5 Accomplishments — `/pm/accomplishments`

| View | Filter | Default columns |
|---|---|---|
| **All Accomplishments** | status ≠ Cancelled/closed | Fiscal Year · Quarter(s) · Accomplishment ID · Title · Business Line · Product Line · Office · Status |
| **MY Accomplishments in Draft/Revision** | owner = me AND status ∈ {Draft, Revision} | same |
| **Accomplishments in Draft/Revision** | status ∈ {Draft, Revision} | |
| **Accomplishments Pending Approval** | status = Pending approval | |
| **Accomplishments Pending MY Approval** | status = Pending approval AND owner = me-or-my-teams | |
| **Finalized Accomplishments** | status = Finalized | |
| **Cancelled/closed Accomplishments** | status = Cancelled/closed | |
| **My Accomplishments** | owner = me | |
| **My Office's Accomplishments** | the Office is owned by me or my teams | |

### 13.6 Priorities — `/pm/priorities`

| View | Filter | Default columns |
|---|---|---|
| **All Priorities** | status ≠ Cancelled/closed | Update Id · Title · Fiscal Year · Quarter · Office · Rank · Business Line · Product Line · Status |
| **MY Priorities in Draft/Revision** | owner = me AND status ∈ {Draft, Revision} | Fiscal Year · Update Id · Business Line · Title · Rank · Office · Status |
| **Priorities in Draft/Revision** · **Priorities Pending Approval** · **Priorities Pending MY Approval** · **Finalized Priorities Updates** · **Cancelled/closed Priorities** · **My Priorities Updates** · **My Offices' Priorities** | as per the pattern | |

### 13.7 Positive Change Management — `/pm/positive-change-management`

| View | Filter | Default columns |
|---|---|---|
| **All Positive Change Managements** | status ≠ Cancelled/closed | Title · ID · Fiscal Year · Quarter · Office · Business Line · Product Line · Status |
| **MY Positive Change Managements in Draft/Revision** | owner = me AND status ∈ {Draft, Revision} | Fiscal Year · Quarter · ID · Business Line · Product Line · Title · Office · Status |
| **Positive Change Managements in Draft/Revision** · **… Pending Approval** · **… Pending MY Approval** · **Finalized …** · **Cancelled/closed …** · **My …** · **My Office's …** | as per the pattern | |

### 13.8 Strategic Plan list screens

| Entity | Views | Default columns |
|---|---|---|
| **Goals** `/sp/goals` | Active Goals · Inactive Goals · My Goals | Goal (display name) |
| **Objectives** `/sp/objectives` | Active Objectives · Inactive Objectives · My Objectives · **Filtered by Goals** *(hard-coded to one goal in the source; parameterise it)* | Sequence · Objective · Strategic Goal |
| **Strategies** `/sp/strategies` | Active Strategies · Inactive Strategies · My Strategies | Sequence · Strategy · Strategic Goal · Strategic Objective |
| **Performance Goals** `/sp/performance-goals` | Active · Inactive · My | Performance Goal (Inactive adds Created On) (+ Sequence, Title available) |
| **External Factors** `/sp/external-factors` | Active · Inactive · My | External Factor · Created On (+ Affected Goal, Fiscal Year available) |
| **Definitions** `/sp/definitions` | Active · Inactive · My | *Active* (11 columns): Identification Number · Title · Fiscal Year · Quarter · Data Source · Strategic Goal · Strategic Objective · Strategy · Performance Indicator · Office · Description; *Inactive*: Title · Created On |
| **Fiscal Years** `/sp/fiscal-years` | Active · Inactive · My | Fiscal Year · Start · End |

### 13.9 Organisational list screens

| Entity | Views | Default columns |
|---|---|---|
| **Offices** `/sp/offices` | Active Offices · Inactive Offices · My Offices | Office (+ Code, Prefix Code, Display Name available) |
| **Divisions** | Active · Inactive · My | Name · Acronym |
| **Organizations** | Active · Inactive · My | Name |
| **Business Lines** | Active · Inactive · My | Business Line · Owner · Alternate Owner (+ B&R Code, Prefix Code available) |
| **Product Lines** | Active · Inactive · My | Product Line · Owner (+ B&R Code, Prefix Code available) |
| **Products** | Active · Inactive · My | Product · Created On (+ Product Code available) |
| **Major Programs** | Active · Inactive · My | Name |
| **Contributing Programs and Activities** | Active · Inactive · My | Name |
| **Office Goals** | Active · Inactive · My | Name · Created On (+ Office available) |

### 13.10 Workflow list screens (audit)

| Entity | Views |
|---|---|
| **Submissions** `/admin/submissions` | Active Submissions · Inactive Submissions · My Submissions · Submitted Performance Indicators · Submitted PI Results · Submitted Enterprise Risks · Submitted Risk Updates · Submitted Priorities · Submitted PCM · Submitted Accomplishments |
| **Approvals** | Active Approvals · Inactive Approvals · My Approvals |
| **Rejections** | Active Rejections · Inactive Rejections · My Rejections · Rejected Performance Indicators · Rejected PI Results · Rejected Enterprise Risks · Rejected Risk Updates · Rejected Priorities · Rejected PCM · Rejected Accomplishments |
| **Approval Queues** | Active Approval Queues · Inactive · My · **Approval Queue Setup** (columns: Order · User · Role · Alternate? · Parallel? · Status · Valid, ordered by Order) |

### 13.11 Evidence Building list screens **[NEW UI]**

| Entity | Views |
|---|---|
| **Priority Questions** | Active Priority Questions · Inactive · My |
| **Evaluations** | Active Evaluations · Inactive · My |
| **Research Activities** | Active Research Activities · Inactive Other Evidence Building Activities · My |

### 13.12 Signposts **[NEW UI]**

| Entity | Views |
|---|---|
| **Signposts** | Signposts · Active Signposts · Inactive Signposts · Display View |
| **Key Areas** | Key Areas · Active Key Areas · Inactive Key Areas · Display View |


### 13.13 Measures and Actions list screens

| Entity | Route | Views | Filter | Default columns |
|---|---|---|---|---|
| **Planned Measures, Milestones and Deliverables** ("Actions") | `/pm/planned-measures` | **Actions** | state = Active | Title · Description · Deliverable Attachment · Deliverable Title · Status · Status Update |
| | | **Inactive Planned Measures, Milestones, and Deliverables** | state = Inactive | Title · Created On |
| | | **My Planned Measures, Milestones, and Deliverables** | state = Active AND owner = me | — |
| **Action/Measure** | `/pm/action-measures` | **Active Action/Measures** | state = Active | Number · Title · Timeframe · Objective satisfied? · Completed or carried forward? · Completion/carry-over notes |
| | | **Inactive Action/Measures** | state = Inactive | Title · Created On |
| | | **My Action/Measures** | state = Active AND owner = me | — |

`Action/Measure` (`nrc_ActionMeasure`) is a separate legacy table from `Planned Measure, Milestone or
Deliverable` (`nrc_PlannedMeasureMilestoneorDeliverable`) — see Document 2 sections 6.2 and 6.9. It has
its own many-to-many relationship to Office and no relationship to Performance Indicator.

### 13.14 Task list screens

| Route | Views | Filter | Default columns |
|---|---|---|---|
| `/{ws}/my-todo` | **My Tasks** | state = Open AND owner = me-or-my-teams, newest first | Subject · Created On |
| `/admin/tasks` | **All Tasks** | any state | Subject · Owner · Created On |

### 13.15 Retired process views (no screen required)

The solution also contains six saved views over `nrc_pisubmissionapprovals`, the instance table of the
**PI Submission/Approvals** business process flow: *PI Submission/Approvals*, *Active PI
Submission/Approvals*, *Inactive PI Submission/Approvals*, *All PI Submission/Approvals*, *Active PI
Submission/Approvals on my Performance Indicator Entries*, *Inactive PI Submission/Approvals on my
Performance Indicator Entries*.

That business process flow is **deactivated** in the shipped solution and the table is not carried
forward (Document 2 section 16.3). Its purpose — recording how a PI Result moved through Draft →
Review → Finalize with a duration — is served in the rebuild by `wf_workflow_transition`
(Document 2 section 9.8), surfaced through `GET /api/v1/{res}/{id}/workflow` and the record timeline
panel. **No list screen is required.**

---

### 13.16 Complete public-view catalogue (authoritative — all 190 business views)

Sections 13.1–13.15 describe the screens; this table is the exhaustive, **verbatim** list of every
view name the rebuild must reproduce, taken directly from the solution's saved queries. Names are
reproduced exactly as they appear in the source, **including the source's own typographic errors**
(a stray `)`, inconsistent `MY`/`My` casing, `My Offices'` vs `My Office's`, and trailing spaces).
Correct them in the rebuild only with OEDO's agreement — several are referenced by name in the User
Guide. **Bold** marks the entity's default view. The *"My …"* column is the per-entity owner-filtered
view (Dataverse query type 8192); it exists for 36 entities.

| Entity (legacy) | Public list views (154) | "My …" view (36) |
|---|---|---|
| `SystemUser` | SPA Users | — |
| `Task` | All Tasks · **My Tasks** | — |
| `Team` | Offices · **SPA Teams** | — |
| `new_KeyAreas` | **Active Key Areas** · Display View · Inactive Key Areas | Key Areas |
| `new_Signposts` | **Active Signposts** · Display View · Inactive Signposts | Signposts |
| `nrc_Accomplishment` | Accomplishments Pending Approval · Accomplishments Pending MY Approval · **Accomplishments in Draft/Revision** · All Accomplishments  · Cancelled/closed Accomplishments  · Finalized Accomplishments · MY Accomplishments in Draft/Revision · **My Office's Accomplishments** | My Accomplishments |
| `nrc_ActionMeasure` | **Active Action/Measures** · Inactive Action/Measures | My Action/Measures |
| `nrc_Approval` | **Active Approvals** · Inactive Approvals | My Approvals |
| `nrc_ApprovalQueue` | **Active Approval Queues** · Approval Queue Setup · Inactive Approval Queues | My Approval Queues |
| `nrc_BusinessLine` | **Active Business Lines** · Inactive Business Lines | My Business Lines |
| `nrc_ContributingProgramsandActivities` | **Active Contributing Programs and Activities** · Inactive Contributing Programs and Activities | My Contributing Programs and Activities |
| `nrc_Definition` | **Active Definitions** · Inactive Definitions | My Definitions |
| `nrc_Division` | **Active Divisions** · Inactive Divisions | My Divisions |
| `nrc_EnterpriseRisk` | All Enterprise Risks · Cancelled/closed Enterprise Risks · Discontinued Enterprise Risks · Enterprise Risks Available for Update · Enterprise Risks Pending Approval · Enterprise Risks Pending Discontinuance · Enterprise Risks Pending MY Approval · **Enterprise Risks in Draft/Revision** · Finalized Enterprise Risks · MY Enterprise Risks in Draft/Revision · My Office's Enterprise Risks | My Enterprise Risks |
| `nrc_Evaluations` | **Active Evaluations** · Inactive Evaluations | My Evaluations |
| `nrc_ExternalFactor` | **Active External Factors** · Inactive External Factors | My External Factors |
| `nrc_FiscalYear` | **Active Fiscal Years** · Inactive Fiscal Years | My Fiscal Years |
| `nrc_Goal` | **Active Goals** · Inactive Goals | My Goals |
| `nrc_MajorPrograms` | **Active Major Programs** · Inactive Major Programs | My Major Programs |
| `nrc_Objective` | **Active Objectives** · Filtered by Goals · Inactive Objectives | My Objectives |
| `nrc_Office` | Active Offices · Inactive Offices | My Offices |
| `nrc_OfficeGoals` | **Active Office Goals** · Inactive Office Goals | My Office Goals |
| `nrc_Organization` | **Active Organizations** · Inactive Organizations | My Organizations |
| `nrc_OtherEvidenceBuildingActivity` | **Active Research Activities** · Inactive Other Evidence Building Activities | My Other Evidence Building Activities |
| `nrc_PerformanceGoal` | **Active Performance Goals** · Inactive Performance Goals | My Performance Goals |
| `nrc_PerformanceIndicator` | **All Performance Indicators** · Cancelled/closed Performance Indicators · Discontinued Performance Indicators · Finalized Performance Indicators · **MY Performance Indicators in Draft/Revision** · My Office's Performance Indicators · Performance Indicators Available for Results · Performance Indicators Pending Approval · Performance Indicators Pending Discontinuance · Performance Indicators Pending MY Approval · Performance Indicators in Draft/Revision · Performance Requirements View · Review for carry-over · Subgrid View | My Performance Indicators |
| `nrc_PerformanceIndicatorFiscalYear` | All PI Results · All Results View  · Cancelled/closed PI Results · Finalized PI Results · Finalized Results View · **MY PI Results in Draft/Revision** · My Offices' PI Results · My PI Results · My Previously Submitted Entries · PI Results Pending Approval · PI Results Pending MY Approval · PI Results in Draft/Revision | My Performance Indicators |
| `nrc_PlannedMeasureMilestoneorDeliverable` | **Actions** · Inactive Planned Measures, Milestones, and Deliverables | My Planned Measures, Milestones, and Deliverables |
| `nrc_PositiveChangeManagement` | All Positive Change Managements · Cancelled/closed Positive Change Managements) · Finalized Positive Change Managements · **MY Positive Change Managements in Draft/Revision** · My Office's Positive Change Managements · Positive Change Managements Pending Approval · Positive Change Managements Pending MY Approval · Positive Change Managements in Draft/Revision | My Positive Change Managements |
| `nrc_Priorities` | **Active Priorities** · Inactive Priorities | My Priorities *(no screen — archive-only table, Document 2 §6.10/§16.2)* |
| `nrc_PrioritiesUpdate` | All Priorities · Cancelled/closed Priorities  · Finalized Priorities Updates · MY Priorities in Draft/Revision · My Offices' Priorities · Priorities Pending Approval · Priorities Pending MY Approval · **Priorities in Draft/Revision** | My Priorities Updates |
| `nrc_PriorityQuestion` | **Active Priority Questions** · Inactive Priority Questions | My Priority Questions |
| `nrc_Product` | **Active Products** · Inactive Products | My Products |
| `nrc_ProductLine` | **Active Product Lines** · Inactive Product Lines | My Product Lines |
| `nrc_Rejection` | **Active Rejections** · Inactive Rejections · Rejected Accomplishments · Rejected Enterprise Risks · Rejected PCM · Rejected PI Results · Rejected Performance Indicators · Rejected Priorities · Rejected Risk Updates | My Rejections |
| `nrc_RiskUpdate` | All Risk Updates · Cancelled/closed Risk Updates · Finalized Risk Updates · MY Risk Updates in Draft/Revision · My Offices' Risk Updates · Risk Outlooks · Risk Updates Pending Approval · Risk Updates Pending MY Approval · Risk Updates in Draft/Revision | My Risk Updates |
| `nrc_Strategy` | **Active Strategies** · Inactive Strategies | My Strategies |
| `nrc_Submission` | **Active Submissions** · Inactive Submissions · Submitted Accomplishments · Submitted Enterprise Risks · Submitted PCM · Submitted PI Results · Submitted Performance Indicators · Submitted Priorities · Submitted Risk Updates | My Submissions |
| `nrc_pisubmissionapprovals` | Active PI Submission/Approvals · **Active PI Submission/Approvals on my Performance Indicator Entries** · All PI Submission/Approvals · Inactive PI Submission/Approvals · Inactive PI Submission/Approvals on my Performance Indicator Entries | PI Submission/Approvals |

**Totals: 154 public list views + 36 "My …" views = 190 business views catalogued.** The remaining
144 saved queries (advanced-find, sub-grid, quick-find and lookup, 4 per entity across 36 entities)
are platform-generated and need no screen.

Two of the 39 entities above need **no screen at all**: `nrc_pisubmissionapprovals` (§13.15 — the
deactivated PI Submission/Approvals process table, 6 views) and `nrc_Priorities`, the
*(DEPRECATED) Priority* table that Document 2 §6.10 and §16.2 retire to archive only (3 views).
Their 9 views are catalogued above for completeness of the 190; the live Priorities screens are
those of `nrc_PrioritiesUpdate` (§13.6, `/pm/priorities`). That leaves **37 entities** with list
screens and **181 of the 190 views** needing one.

## 14. Form screens

Each form reproduces the as-built tab/section/field layout. `*` marks required fields.

### 14.1 Performance Indicator form — `/pm/performance-indicators/{id}`

**Header:** Stage (`statuscode`, read-only badge) · Status (`statecode`, hidden) · **Current Record
Holder** (`ownerid`, read-only — the workflow holder label, not "Owner")
**Command bar:** Save · Save & Close · New · Submit for Approval · Deactivate · Assign · Share · Delete

**Tab: General**

| Section | Fields |
|---|---|
| *(banner)* | **COMMENTS REGARDING SUBMISSION** — rich text, visible only when status ∈ {Pending approval, Revision} |
| Identification | Indicator ID (read-only, system generated) · Implementation Year · Indicator Title* (≤ 200) · Description* (≤ 950, counter — the User Guide's 1 000 is the pre-narrowing width; see §15.5.1) · Report Level* · Contact Person* · Owner* · Accountable Organization* |
| Revision | Change Type* · **PI being revised** (shown and required only when Change Type = Revised; selecting it auto-fills 22 fields — §15.5.5) |
| Measurement | Agency Wide Support Level* · Data Source · Measure Type* · Indicator Type* · Units* · Results Calculation* (counter) |
| Business Line(s) | Lead Business Line* · **Contributing Business Lines** (sub-grid) |
| Strategic Plan | Strategic Plan Goal* · Strategic Plan Objective* · **Performance Goal** (conditional) · Strategic Plan Strategy* |
| Program(s) | Primary Major Program* · **Contributing Major Programs** (sub-grid) · Primary Contributing Program* · **Contributing Programs** (sub-grid) |
| Product Line(s) | Lead Product Line* · Product · **Contributing Product Lines** (sub-grid) |
| Office(s) | Lead Office* · Division · **Contributing Offices** (sub-grid) |
| Hidden/system | Indicator Status · Annual Performance Plan and Report · Quarterly Performance Review · **Other Data Source** (its own `visible="false"` section `null_section_32`, below Quarterly Performance Review — surfaced when Data Source = Other) · Modified On |
| *(hidden sections)* | **Actions** (Planned Measures/Milestones/Deliverables sub-grid, control `planned_subgrid` in the `visible="false"` section `null_section_27`) — revealed by `cr9de_outcomebased` **only when Indicator Type = Outcome** (`nrc_indicatortype` = 875670001), hidden for every other type · **Performance Indicator Results** (sub-grid `Subgrid_new_2` in the `visible="false"` section labelled *General*, alongside a hidden `modifiedon`) — **no script ever unhides it, so it is permanently invisible on the as-built form**; mark it **[NEW]** if the rebuild should show it |

**Validation:** hierarchy integrity on Goal→Objective→Strategy; character limits; restricted-creation
rule for CBJ/APPR and Agencywide.

### 14.2 PI Result form — `/pm/pi-results/{id}`

**Header:** Status (`statecode`, hidden) · Stage (`statuscode`) · **Current Editor** (`ownerid`)

**Tab: General**

| Section | Fields |
|---|---|
| *(banner)* | **COMMENTS REGARDING SUBMISSION** (conditional) |
| Reporting | Reporting Person* (defaults to creator) · Reporting Office* · Division |
| Indicator | Performance Indicator* (filtered to *Available for Results*) · Fiscal Year* · **Quarter(s)*** (multi-select) |
| Business Line(s) | Reporting Business Line · **Contributing Business Lines** (sub-grid) |
| Product Line(s) | Reporting Product Line · **Contributing Product Lines** (sub-grid) |
| **Performance Indicator Details** | read-only quick-view of the parent PI, in one card: Indicator ID · Indicator Title · Description · Report Level · Change Type · Indicator Status · Agency Wide Support Level · Data Source · Measure Type · Indicator Type · Units · Results Calculation. As built this was two quick views side by side, atop the middle and right columns of a three-column tab, the second titled *Performance Indicator Details cont...*; stacked in one column they read as one card cut in two, with Program(s) between the halves, so they are one card holding the fields of both |
| Program(s) | Primary Major Program · **Contributing Major Programs** (sub-grid) |
| Contributing Programs | Primary Contributing Program · **Contributing Programs** (sub-grid) |
| Hidden/system | Data Type · Indicator Type · Performance Goal Met · Title |

**Tab: Quarterly Updates** — five sections, **Quarter 1 · Quarter 2 · Quarter 3 · Quarter 4 · Annual**,
each rendered in three columns:

| Non-Range indicator | Range indicator |
|---|---|
| Results · Operator · Target | Minimum Target · Maximum Target · Lower Operator · Upper Operator |
| *(both)* Not Applicable checkbox — ticking it **clears and locks Results** | |
| *(both)* Success Likelihood · Mitigation / Remarks (counter) · Raw Data | |

The **Quarter 1** section also carries a hidden **(INTERNAL) Measure Type**
(`nrc_internalmeasuretype`) cell — the driver of the Range-vs-Regular display rule for all five
quarterly sections.

**Tab: Attachments** — notes/files, plus Office Team.

**Sub-grid enablement:** the Contributing sub-grids activate only after the first save
(User Guide: *"Additional entry tables listed below will appear on the form after saving"*).

**Quick-create form** (used from sub-grids): Performance Indicator · Fiscal Year · Reporting Person ·
Quarter(s) · Public.

### 14.3 Enterprise Risk form — `/pm/enterprise-risks/{id}`

**Header:** Risk Status · Stage (`statuscode`) · Status (`statecode`, hidden) · Current Record Holder

**Tab: General**

| Section | Fields |
|---|---|
| *(banner)* | **COMMENTS REGARDING SUBMISSION** (conditional) |
| General | Risk ID (read-only, system generated) · Risk Title* (≤ 100) · Description* (≤ 300, counter — User Guide says 310, unreachable against a 300-wide column; open question, Document 1 §17.3 item 5) · Report Level* |
| *"Related Performance Indicators can be added after initial 'save'"* | **Performance Indicators not applicable for this Risk** (checkbox) · **Related Performance Indicators** (sub-grid; mandatory unless the checkbox is ticked) |
| History | Originating Fiscal Year* · **Applicable Fiscal Years** (sub-grid) |
| Office(s) | Lead Office* · Division · **Contributing Offices** (sub-grid) |
| Strategic Plan Impact | Goal* · Objective* · Strategy* |
| Program(s) | Primary Major Program* · **Contributing Major Programs** (sub-grid) · Primary Contributing Program* · **Contributing Programs** (sub-grid) |
| Business Line(s) | Lead Business Line* · **Contributing Business Lines** (sub-grid) |
| Product Line(s) | Lead Product Line* · Product · **Contributing Product Lines** (sub-grid) |
| Also on the record | Originating Quarter* · Owner Office · Business Line/Product Line Owner · Public? · Additional Factors · Initial Risk Control Efforts · Performance Monitoring/Progress Plans |

### 14.4 Risk Update form — `/pm/risk-updates/{id}`

**Header:** Status (`statecode`, hidden) · Status Reason (`statuscode`) · Current Record Holder

**Tab: General**

| Section | Fields |
|---|---|
| *(banner)* | **COMMENTS REGARDING SUBMISSION** (conditional) |
| General | Entry ID (read-only) · Enterprise Risk* (filtered to *Available for Update*) · Fiscal Year* · Quarter* · PSAT? · Reporting Office · Contact Person* · **Risk Details** (read-only quick-view of the parent risk) |
| Program(s) | Major Program · Primary Contributing Program · **Other Contributing Programs** (sub-grid) |
| Business Line(s) | Reporting Business Line · **Other Contributing Business Lines** (sub-grid) |
| Product Line(s) | Reporting Product Line · **Other Contributing Product Lines** (sub-grid) |
| *(hidden)* | Risk Lead |
| **Inherent Risk** | Inherent Likelihood* (H/M/L) · Inherent Likelihood QPR Description* (≤ 300) · Inherent Likelihood Full Description (≤ 999 999) · Inherent Consequence* · Inherent Consequence QPR Description* (≤ 300) · Inherent Consequence Full Description |
| **Residual Risk** | Residual Likelihood* · Residual Likelihood QPR Description* (≤ 300) · Residual Likelihood Full Description · Residual Consequence* · Residual Consequence QPR Description* (≤ 300) · Residual Consequence Full Description |
| **Monitoring and Mitigation** | Risk Outlook (hidden) · MANAGE (Current Risk Response) QPR Description* (≤ 600, counter) · MANAGE Full Description · **"Check if this risk is accepted (have we done enough?)"** · ACT (Proposed Risk Response) QPR Description (≤ 300, **required unless the risk is accepted**, counter) · ACT Full Description · Risk Monitoring QPR Description* (≤ 300) · Risk Monitoring Full Description · Informed Monitoring QPR Description* (≤ 300) · Informed Monitoring Full Description · Budget String(s) (≤ 225) |
| **(For OEDO use only)** | PSAT Accepted? · Notes |
| *(auto-populated, read-only)* | Last Quarter's Inherent Likelihood / Consequence · Last Quarter's Residual Likelihood / Consequence |

### 14.5 Priority form — `/pm/priorities/{id}`

**Header:** Status (`statecode`) · Status Reason (`statuscode`) · Owner

| Section | Fields |
|---|---|
| *(banner)* | **COMMENTS REGARDING SUBMISSION** (conditional) |
| Main Info | Title* (≤ 100) · Description* (≤ 650) · Report Level* |
| *(hidden)* | Update Id · Owner |
| Period & rank | Fiscal Year* · Quarter* (multi-select) · Rank* (1–10 per the User Guide; the enumeration holds 1–11) · Principles of Good Regulation* |
| Business Line(s) | Lead Business Line* · **Contributing Business Lines** (sub-grid) |
| Product Line(s) | Lead Product Line* · Product · **Contributing Product Lines** (sub-grid) |
| Strategic Plan | Strategic Plan Goal* · Strategic Plan Objective* · Strategic Plan Strategy* |
| Program(s) | Primary Major Program* · **Contributing Major Programs** (sub-grid) · Primary Contributing Program* · **Other Contributing Programs** (sub-grid) |
| Office(s) | Lead Office* · Division · **Contributing Offices** (sub-grid) |
| *"Please 'Save' to Enter Related Performance Indicators"* | **Related Performance Indicators** (sub-grid) |

### 14.6 Positive Change Management form — `/pm/positive-change-management/{id}`

**Header:** Status (`statecode`, hidden) · Stage (`statuscode`) · Current Record Holder

| Section | Fields |
|---|---|
| *(banner)* | **COMMENTS REGARDING SUBMISSION** (conditional) |
| General Info | ID (read-only) · Title* (≤ 100) · Description* (≤ 1 200, counter) · Report Level* |
| Period | Fiscal Year* · Quarter* · Contact Person* |
| Business Line(s) | Lead Business Line* · **Contributing Business Lines** (sub-grid) |
| Product Line(s) | Lead Product Line* · Product · **Contributing Product Lines** (sub-grid) |
| Strategic Plan | Strategic Plan Goal* · Strategic Plan Objective* · Strategic Plan Strategy* |
| Program(s) | Primary Major Program* · **Contributing Major Programs** (sub-grid) · Primary Contributing Program* · **Contributing Programs** (sub-grid) |
| *"Please 'Save' to Enter Contributing Offices and Division Owners(s)"* *(sic — source typo)* | **Division Owner(s)** (sub-grid of Users) |
| Office(s) | Lead Office* · Division · **Contributing Offices** (sub-grid) |
| *(hidden)* | Presented at QPR |

### 14.7 Accomplishment form — `/pm/accomplishments/{id}`

**Header:** Stage (`statuscode`) · Status (`statecode`, hidden) · Current Record Holder

| Section | Fields |
|---|---|
| **NOTES FOR RESUBMISSION** | **COMMENTS REGARDING RESUBMISSION** (conditional) · hidden red banner *"One or more of your approval steps are invalid. Please revise in order to submit."* (web resource `nrc_invalidwarningtext`, control `WebResource_invalidwarningtext` — §15.5.6) |
| Details | Accomplishment ID (read-only) · Title* (≤ 100) · Description* (≤ 850, counter) · Report Level |
| Period | Fiscal Year* · Quarter* (multi-select) |
| People | Owner* · Contact Person* |
| Business Line(s) | Lead Business Line* · **Contributing Business Lines** (sub-grid) |
| Product Line(s) | Lead Product Line* · **Contributing Product Lines** (sub-grid) |
| Related PIs | **Primary Related PI** (selecting it auto-fills the three Strategic Plan fields) · **Other Related Performance Indicators** (sub-grid) |
| Strategic Plan | Strategic Plan Goal* · Strategic Plan Objective* · Strategic Plan Strategy* (auto-filled, editable) |
| Program(s) | Primary Major Program* · **Contributing Major Programs** (sub-grid) · Primary Contributing Program* · **Other Contributing Programs** (sub-grid) |
| Office(s) | Lead Office* · Division · **Contributing Offices** (sub-grid) |
| *(hidden)* | Annual Performance Plan · Quarterly Performance Review |

### 14.8 Strategic Plan forms

| Form | Sections and fields |
|---|---|
| **Goal** | Goal (display name, read-only) · Goal Text* · Sequence · rollup counters (Objective Count, Strategy Count, Indicators Count, Risk Count) · **Objectives** sub-grid · **Strategies** sub-grid · **Applicable Fiscal Years** sub-grid. *Section split:* **General** (Sequence · Goal Text · Risk Count · Indicators Count · Applicable Fiscal Years grid) and **Objectives and Strategies** (Objective Count · Strategy Count · Objectives grid · Strategies grid). *Columns that exist but are not form-placed:* Number · Fiscal Year · Goal Image |
| **Objective** | Objective (display name, read-only) · Title* · Sequence* · Strategic Goal* · **Strategies** sub-grid · **Applicable Fiscal Years** sub-grid — validated against the Goal sequence. *Not form-placed:* Fiscal Year (`nrc_fiscalyear`) |
| **Strategy** | Strategy (display name, read-only) · Title · Sequence · Strategic Goal · Strategic Objective · **Applicable Fiscal Years** sub-grid — validated against the Objective sequence |
| **Performance Goal** | Performance Goal (read-only) · Title* · Sequence |
| **External Factor** | External Factor* · Description* · Affected Goal · Fiscal Year* · **Objectives** sub-grid · **Strategies** sub-grid |
| **Definition** | Title* · Identification Number (auto `NRC-0001`) · Description · Data Source (multi-select) · Fiscal Year · Quarter · Business/Product Line Owner · Office · Office Goal · Performance Indicator · Performance Indicator Entry · Product · Strategic Goal · Strategic Objective · Strategy · **Related Business Lines** sub-grid · **Related Product Lines** sub-grid (the `nrc_businesslines` picklist exists but is not form-placed) |
| **Fiscal Year** | **General:** Fiscal Year* · Owner (hidden) · Start · End · **Goals** (sub-grid). **Section "RELATED TO THIS FISCAL YEAR"** (two columns): **Strategies** · **Objectives** · **Performance Indicators** sub-grids. Note the third grid is labelled *Performance Indicators* but is bound to **PI Results** (`nrc_performanceindicatorfiscalyear`) — relabel it *PI Results* in the rebuild. |

### 14.9 Organisational forms

| Form | Fields |
|---|---|
| **Office** | Office* · Team (owner) · **Office instructions panel** (`nrc_officeInstructions`, control `WebResource_new_1`, General section — §15.5.6): *"Follow link to Office's Team to add/remove members to this office."* |
| **Division** | Name* · Acronym |
| **Organization** | Name* |
| **Business Line** | Business Line* · Owner · Alternate Owner |
| **Product Line** | Product Line* · Owner · B&R Code |
| **Product** | Product* · Owner |
| **Major Program** | Name* |
| **Contributing Programs and Activities** | Name* |
| **Office Goal** | Name* · Owner · **Notes** |

**[NEW] Proposed additions to the organisational forms.** These columns and relationships exist in
the tables but appear on no as-built form: **Office** — Code, Prefix Code, Display Name (computed),
and **Divisions** / **Goals** sub-grids on the existing `nrc_Office_nrc_Division` and
`nrc_Office_nrc_Goal` relationships; **Business Line** — B&R Code, Prefix Code, and a **Product
Lines** sub-grid on `cr9de_nrc_ProductLine_nrc_BusinessLine`; **Product Line** — Prefix Code;
**Product** — Product Code, (INTERNAL) Product Name (computed); **Office Goal** — the **Office**
lookup, which metadata marks `req=required` but which has no form cell at all, so the rebuild must
supply it.

### 14.10 Planned Measure / Milestone / Deliverable ("Action") form

Title* · Deliverable Title · Description · Status Update · Regarding Performance Indicator*
(read-only on the form — set from the parent PI's Actions sub-grid) ·
**Deliverable Attachment** (file upload ≤ 32 MB) · Status (In progress / Met / Unmet / Cancelled-closed).
The entity also defines **Type** (`nrc_type`, option set `nrc_pitype`) and **Performance Goal**
(`nrc_performancegoal`, ≤ 1 000), neither of which is placed on the form.

**Scope note (guidance text, not enforced).** The solution's `nrc_measures_text` web resource reads
*"Planned Measures Milestone, or Deliverables only apply to Performance Indicators under Strategic
Goals 2 and 3"*. It is placed on no form (§15.5.6), so in the legacy system the rule is documentation
only — see Document 1 §8.

### 14.10a Action/Measure form — `/pm/action-measures/{id}`

| Section | Fields |
|---|---|
| General | Number · Title* · Owner · Timeframe · Objective satisfied? · Completed or carried forward? · Completion/carry-over notes |
| *(New Section)* | **Leading Offices/Officials** — sub-grid on the M:N `nrc_ActionMeasure_nrc_Office` (Document 2 §6.9); endpoint `/action-measures/{id}/leading-offices` (§3.2) |

This is the legacy `nrc_ActionMeasure` table, distinct from §14.10's
`nrc_PlannedMeasureMilestoneorDeliverable` — see §13.13.

### 14.11 Evidence Building forms **[NEW UI]**

| Form | Sections and fields |
|---|---|
| **Priority Question** | Approver Comments/Revisions · Priority Question* · Answer Type · **Answer** (a single picker that searches both Evaluations and Research Activities) · read-only quick-view of the selected answer · **Approval Queue** sub-grid |
| **Evaluation** | Title* · Summary* (≤ 750) · Office* · Fiscal Year · Type of Activity · Status* · Status Description · Evaluation Objective · Key Questions · Evaluation Methods · Data Needs and Sources · Stakeholder Engagement · Challenges and Mitigating Strategies · Contractor Support · Total Resources Dollars · Total Resources FTE · Performance Indicator · Related Strategic Goal · Related Strategic Objective · Publish* · Approval Order Stage · Approver Comments/Revisions · **Products** sub-grid |
| **Research Activity** | *(banner)* Approver Comments/Revisions. **General** (two columns): Activity Title* · Fiscal Year · Lead Office · Type* · Overview · Strategic Goal · Strategic Objective · Total Resources, FTE · Point of Contact* · Total Resources, Dollars · Contractor Support · Performance Indicator · Approval Stage (hidden). **Details** (four columns): Strategic Focus Area · Impact and Benefits · Drivers · Stakeholder Engagement. **Publications and Products**: Products sub-grid (relationship `nrc_publicationsandprodicts` — *sic*, misspelt in the source). **Approval Queue** — an empty placeholder section (`null_section_5`) in the source, so the sub-grid is **[NEW]** (only Priority Question carries a real one, relationship `nrc_regarding_entry_priquestion`). Second tab **Status**. The quick-view form labels the same grid *Products and Publications*. |

### 14.12 Signposts forms **[NEW UI]**

| Form | Fields |
|---|---|
| **Signpost** | Title* · Signpost Number (read-only) · Analysis* (rich text ≤ 2 000) · **Key Areas** sub-grid **[NEW]** — the source form ends with an empty placeholder section (`_section_37`) and binds no grid |
| **Key Area** | Title* · Key Area Number (read-only) · Analysis* (rich text ≤ 2 000) · Associated Signpost* · read-only quick-view of the associated Signpost (section *Associated Signpost*) |

### 14.13 Workflow forms

| Form | Fields |
|---|---|
| **Task** | **Header:** Priority · Due · Activity Status · Owner. **Tab TASK** — *TASK*: Subject · Action Type (hidden) · Submitted Record(s) Type; *Description* (labelled section): Description; *`rej_section`*: **seven** **Records needing revision** sub-grids, all on `nrc_rejection_Task_task` but each bound to a different view — `RU_rejgrid` (Rejected Risk Updates) · `PRI_rejgrid` (Rejected Priorities) · `PIRES_rejgrid` (Rejected PI Results) · `ACC_rejgrid` (Rejected Accomplishments) · `PI_rejgrid` (Rejected Performance Indicators) · `PCM_rejgrid` (Rejected PCM) · `ER_rejgrid` (Rejected Enterprise Risks); *`sub_section`* ("Submissions"): **seven** **Submitted Records** sub-grids, all on `nrc_submission_Task_task` — `ACC_subgrid` · `PIRES_subgrid` · `PCM_subgrid` · `PRI_subgrid` · `RU_subgrid` · `PI_subgrid` · `ER_subgrid` (Submitted Accomplishments / PI Results / PCM / Priorities / Risk Updates / Performance Indicators / Enterprise Risks); plus a Notes control. `nrc_taskFormAprrovals::determineSectionGrid` (§15.5.4) shows exactly one section and exactly one grid within it, chosen from Action Type and Submitted Record(s) Type — the rebuild must keep the per-record-type filtering rather than substituting one generic grid per section |
| **Approval Queue** | Regarding (record, polymorphic) · User · Role · Order* · Parallel? · Alternate? · Approval Status (`statuscode`) · Name (hidden) · Owner (hidden). *`Valid` is not on the form* — it is a column of the Approval Queue Setup view (§13.10) which **nothing in the shipped solution ever writes**: its only writer, `nrc_queueValidation`, is declared as a library but bound to no event (§15.5.5) |
| **Approval Queue** *(quick-create)* | Regarding · Order · Role · User · Parallel? · Alternate? — one visible section; the second and third column sections are `visible="false"`. Used from the Regarding record's Approval Queue sub-grid |
| **Submission / Approval / Rejection** | Name · Owner · typed record link · From / To (user or team) · Task · flags · Status — read-only audit records |

### 14.14 Admin forms

| Form | Fields |
|---|---|
| **Team — "Office" form** | **Office** (`nrc_office`, visible — this is what makes the team an office group) · Office Name · Administrator · **MEMBERS** sub-grid. *Hidden on the form:* Description · Business Unit · Team Type · Azure AD Object Id · Membership Type · Default Queue (header) |
| **Team — "SPA Team" form** | Team Name · Description (visible here) · Administrator · **MEMBERS** sub-grid. *Hidden on the form:* Office · Business Unit · Team Type · Azure AD Object Id · Membership Type · Default Queue (header) |
| **User** | User Name · Full Name · Title · Primary Email · Mobile Phone · Main Phone · **Security Roles** sub-grid · **Teams** sub-grid · Business Unit · Manager · Position · Home/Other Phone · Email 2 · Preferred Phone · Mobile Alert Email · Pager · Fax · Mailing Address · Other Address · **Direct Reports** sub-grid · Access Mode · License Type |

---

## 15. Dialogs and command UX

### 15.1 Command visibility matrix (replaces `nrc_*ButtonRules`)

| Entity | View | Visible commands |
|---|---|---|
| Performance Indicator | MY Performance Indicators in Draft/Revision | Submit for Approval |
| | Performance Indicators Pending MY Approval | Approve · Return |
| | Finalized Performance Indicators | Propose for discontinuance |
| | Performance Indicators Pending Discontinuance | Discontinue · Deny *(EDO role only)* |
| | any grid *(ungated in the source)* | Flag for carry-over |
| | Review for carry-over | Unflag from carry-over |
| PI Result | MY PI Results in Draft/Revision | Submit for Approval |
| | PI Results Pending MY Approval | Approve · Return |
| | Finalized PI Results | Open PI child records for next quarter *(EDO role only, no selection)* |
| Enterprise Risk | MY Enterprise Risks in Draft/Revision | Submit for Approval |
| | Enterprise Risks Pending MY Approval | Approve · Return |
| | Finalized Enterprise Risks | Propose for discontinuance |
| | Enterprise Risks Pending Discontinuance | Discontinue · Deny discontinuance *(EDO role only)* |
| Risk Update / Accomplishment / Priority / PCM | MY … in Draft/Revision | Submit for Approval |
| | … Pending MY Approval | Approve · Return |

All other views show no workflow commands. This exactly reproduces the legacy behaviour, including the
User Guide note *"Submission is only available on the 'MY' view, not the default."*

### 15.2 Dialog text (verbatim from the ribbon command definitions)

Every string below was extracted directly from the `CommandDefinition` JavaScript parameters in
`customizations.xml`. `{n}` is the selected-record count (`{0}` in the source). The source contains
three spelling errors — *succesfully* (three times — `flagPI`, `returnPerfIndCommand`, `unflagPI`),
*distcontinuance*, and a doubled full stop — reproduced
here so the mapping is unambiguous; the rebuild should correct them.

| Command | Confirmation | Success | Error |
|---|---|---|---|
| **Approve — Accomplishments**<br>`approveAccomplishmentCommand` | Approve {n} Accomplishments? | Accomplishment(s) successfully approved. | Error on approval. Please try again later. |
| **Return — Accomplishments**<br>`returnAccomplishmentCommand` | Return {n} Accomplishments for revision? Please include revision notes on individual records. | Accomplishment(s) successfully returned. | Error on return. Please try again later. |
| **Submit — Accomplishments**<br>`submitAccomplishmentCommand` | Submit {n} selected Accomplishments? | Accomplishment(s) successfully submitted for approval. | Error on submission. Please try again later. |
| **Submit (second webhook, Accomplishments)**<br>`submitAccomplishmentCommand` → `{%nrc_SUBMITURL2%}` (`RunWebHookSingle`, first selected record only; the token is undefined in the export — Document 1 §17.3) | Notification will be sent to EDO for review. Ok to proceed? | *(none)* | *(none)* |
| **Approve — Enterprise Risks**<br>`approveEntRiskCommand` | Approve {n} Enterprise Risks? | Enterprise Risk(s) successfully approved. | Error on approval. Please try again later. |
| **Deny discontinuance — Enterprise Risks**<br>`denyEntRiskCommand` | Deny discontinuance for {n} Enterprise Risk(s)? | Enterprise Risk(s) discontinuance successfully denied. | Error on return. Please try again later. |
| **Discontinue — Enterprise Risks**<br>`discontinueEntRiskCommand` | Discontinue {n} Enterprise Risk(s)? | Enterprise Risk(s) successfully discontinued. | Error on distcontinuance. Please try again later. |
| **Propose for discontinuance — Enterprise Risks**<br>`proposeEntRiskCommand` | This will flag {n} Enterprise Risk(s) for review to discontinue. Do you want to proceed? | Enterprise Risk(s) successfully flagged for discontinuance review. | Error on submission. Please try again later. |
| **Return — Enterprise Risks**<br>`returnEntRiskCommand` | Return {n} Enterprise Risk(s) for revision? Please include revision notes on individual records. | Enterprise Risk(s) successfully returned. | Error on return. Please try again later. |
| **Submit — Enterprise Risks**<br>`submitEntRiskCommand` | Submit {n} selected Enterprise Risks? | Enterprise Risk(s) successfully submitted for approval. | Error on submission. Please try again later. |
| **Approve — PI Results**<br>`approvePIResultCommand` | Approve {n} PI Result(s)? | PI Result(s) successfully approved. | Error on approval. Please try again later. |
| **Open PI child records for next quarter**<br>`openPIResCommand` | This action will unlock all PI Result records for the current fiscal year to be editable for the next quarter. Do you want to proceed? | PI Result(s) successfully submitted for reactivation. This may take a minute, please wait to refresh the records. | Error on reactivation. Please try again later. |
| **Return — PI Results**<br>`returnPIResultCommand` | Return {n} PI Result(s)? Please include revision notes on individual records. | PI Result(s) successfully returned. | Error on return. Please try again later.. |
| **Submit — PI Results**<br>`submitPIResultCommand` | Submit {n} selected PI Results? | PI Result(s) successfully submitted for approval. | Error on submission. Please try again later. |
| **Approve — Performance Indicators**<br>`approvePerfIndCommand` | Approve {n} Performance Indicator(s)? | Performance Indicator(s) successfully approved. | Error on approval. Please try again later. |
| **Deny discontinuance — Performance Indicators**<br>`denyPerfIndCommand` | Deny {n} Performance Indicator(s) for discontinuance? | Performance Indicator(s) successfully denied from discontinuance. | Error on return. Please try again later. |
| **Discontinue — Performance Indicators**<br>`discontinuePerfIndCommand` | Discontinue {n} Performance Indicator(s)? | Performance Indicator(s) successfully discontinued. | Error on discontinuance. Please try again later. |
| **Flag for carry-over — Performance Indicators**<br>`flagPI` | Flag {n} selected record(s) for carry over review? | Performance Indicator(s) succesfully flagged. | Error occurred. Please try again later. |
| **Propose for discontinuance — Performance Indicators**<br>`proposePerfIndCommand` | This will flag {n} Performance Indicator(s) for review to discontinue. Do you want to proceed? | Performance Indicator(s) successfully flagged for discontinuance. | Error on submission. Please try again later. |
| **Return — Performance Indicators**<br>`returnPerfIndCommand` | Return {n} Performance Indicator(s)? | Performance Indicator(s) succesfully returned. | Error on return. Please try again later. |
| **Submit — Performance Indicators**<br>`submitPerfIndCommand` | Submit {n} selected Performance Indicators? | Performance Indicator(s) successfully submitted for approval. | Error on submission. Please try again later. |
| **Unflag from carry-over — Performance Indicators**<br>`unflagPI` | Remove carry over flags for {n} records? This will not change anything within the record and will only remove them from the review list. | Performance Indicator(s) succesfully unflagged. Refresh to update list. | Error occurred. Please try again later. |
| **Approve — Positive Change Management**<br>`approvePCMCommand` | Approve {n} Positive Change Management Item(s)? | Positive Change Management Item(s) successfully approved. | Error on approval. Please try again later. |
| **Return — Positive Change Management**<br>`returnPCMCommand` | Return {n} Positive Change Management Item(s)? | Positive Change Management(s) successfully returned. | Error on return. Please try again later. |
| **Submit — Positive Change Management**<br>`submitPCMCommand` | Submit {n} selected Change Managements for approval? | Change Management(s) successfully submitted for approval. | Error on submission. Please try again later. |
| **Approve — Priorities**<br>`approvePriorityCommand` | Approve {n} Priority(s)? | Priority(s) successfully approved. | Error on approval. Please try again later. |
| **Return — Priorities**<br>`returnPriorityCommand` | Return {n} Priority(s)? Please include revision notes on individual records. | Priority(s) successfully returned. | Error on return. Please try again later. |
| **Submit — Priorities**<br>`submitPriorityCommand` | Submit {n} selected Priorities? | Priority(s) successfully submitted for approval. | Error on submission. Please try again later. |
| **Approve — Risk Updates**<br>`approveRiskUpdateCommand` | Approve {n} Risk Update(s)? | Risk Update(s) successfully approved. | Error on approval. Please try again later. |
| **Return — Risk Updates**<br>`returnRiskUpdateCommand` | Return {n} Risk Update(s)? Please include revision notes on individual records. | Risk Update(s) successfully returned. | Error on return. Please try again later. |
| **Submit — Risk Updates**<br>`submitRiskUpdateCommand` | Submit {n} selected Risk Updates? | Risk Update(s) successfully submitted for approval. | Error on submission. Please try again later. |

### 15.3 In-form validation messages

The source contains exactly **12 distinct** client-side notification strings. All of them are listed
here verbatim; the last row is the only **proposed** message in this table and is marked as such.

| Trigger | Message | Source |
|---|---|---|
| Objective does not belong to the selected Goal (sequence-number mismatch) | *This Objective does not fall under the Goal selected above.* | verbatim |
| Strategy does not belong to the selected Objective | *This Strategy does not fall under the Objective selected above.* | verbatim |
| Non-EDO user saving a restricted Performance Indicator — see §15.5 for the exact rule | *You do not have the necessary **priviledges** to create this record with this field value.* | verbatim — **note the misspelling of "privileges" in the source**; correct it in the rebuild |
| Approval Queue: step role = Final Approval but the chosen user's `nrc_finalapprovercapabilities` flag is not set (§15.5.5) | *Cannot be final approver, user has insufficient roles.* | verbatim |
| Character limit exceeded | *Exceeds character limit. Please condense response to **{n}** characters or less.* — where {n} is 300, 310, 600, 670, 750, 760, 950 or 1000 depending on the field (§15.5.1) | verbatim (8 variants) |
| Required sub-grid empty (Related PIs) | *At least one Related Performance Indicator is required, or tick "Performance Indicators not applicable for this Risk".* | **proposed** — no such message exists in the source; only the field label *"Performance Indicators not applicable for this Risk"* does. Confirm the wording with OEDO |

### 15.4 Add Existing… panel (sub-grid)

Reproduces the User Guide procedure exactly:

1. Click the **⋯** in the top-right corner of the sub-grid.
2. Choose **Add Existing…** — a panel opens on the right of the screen.
3. Type in the panel's search bar to find records; **multiple records can be selected at once**.
4. Click **Add** at the bottom of the panel.
5. The grid refreshes (show a spinner while it does).

### 15.5 Client-side scripts to reimplement (52 JScript + 5 HTML web resources)

The legacy forms carry 52 JScript and 5 content-bearing HTML web resources (the remaining 45
web resources are icon images). Each is catalogued below with its **wiring status**; only the *live*
ones describe behaviour the React rebuild must reproduce — the orphaned, never-invoked and
disabled ones are technical debt (Document 1 §13.5).
Every fact below is read directly from the script source — function name, the fields and
controls it touches, and the literal limits and messages it emits.

#### 15.5.1 Character counters (14 scripts)

Each script reads one field on change and, if `value.length >= threshold`, calls
`setNotification` with a message naming a *different*, rounded number; otherwise it calls
`clearNotification`. In React this is one reusable hook (`useCharacterLimit`) behind one `<CharacterCounter>`
component, parameterised by field, limit and message — but **do not port the legacy thresholds**. They were written
against column widths that have since changed; §15.5.1.1 sets out the evidence.

| Script | Field (entity) | Column max **when written** | Column max **now** | JS threshold | Message says | Guide says | Wired? | Can trip today? | **Enforce** |
|---|---|---|---|---|---|---|---|---|---|
| `nrc_AnnRemarksCharCounter` | `nrc_statusupdatesummary` (PI Result) | 4000 | 800 | 959 | 950 | — | yes | no — threshold > column | **800** |
| `nrc_CRCECharCount` | `nrc_currentriskcontrolefforts` (Risk Update) | 700 | 600 | 767 | 760 | 700 | yes | no — threshold > column | **600** |
| `nrc_ERDescrCharCounter` | `nrc_description` (Enterprise Risk) | 550 | 300 | 313 | 310 | 310 | yes | no — threshold > column | **300** |
| `nrc_GFCPcharCount` | `nrc_goforwardcontrolplans` (Risk Update) | 700 | 300 | 600 | 600 | 350 | yes | no — threshold > column | **300** |
| `nrc_ImpactDescrCharCounter` | `nrc_impactdescription` (Risk Update) | 350 | **column deleted** | 313 | 300 | — | **no** | n/a | — *do not port* |
| `nrc_LikeDescrCharCounter` | `nrc_likelihooddescription` (Risk Update) | 350 | **column deleted** | 313 | 300 | — | **no** | n/a | — *do not port* |
| `nrc_PCMDescrCharCounter` | `nrc_positivechangemgmtitem` (Pos. Change Mgmt) | 650 | 1200 | 1000 | 1000 | 650 | **no** | n/a | **1200** |
| `nrc_PIDescrCharCounter` | `nrc_description` (Performance Indicator) | 1000 | 950 | 959 | 950 | 1000 | yes | no — threshold > column | **950** |
| `nrc_PIResCalcCharCounter` | `nrc_resultscalculation` (Performance Indicator) | 100 | 4000 | 672 | 670 | 1000 | yes | yes | **670** |
| `nrc_accDescrCharCount` | `nrc_description` (Accomplishment) | 4000 | 850 | 755 | 750 | 650 | yes | yes | **850** |
| `nrc_q1RemarksCharCount` | `nrc_q1mitigationremarks` (PI Result) | 100 | 800 | 959 | 950 | 100 | yes | no — threshold > column | **800** |
| `nrc_q2RemarksCharCounter` | `nrc_q2mitigationremarks` (PI Result) | 100 | 800 | 959 | 950 | 100 | yes | no — threshold > column | **800** |
| `nrc_q3RemarksCharCounter` | `nrc_q3mitigationremarks` (PI Result) | 100 | 800 | 959 | 950 | 100 | yes | no — threshold > column | **800** |
| `nrc_q4RemarksCharCounter` | `nrc_q4mitigationremarks` (PI Result) | 100 | 800 | 959 | 950 | 100 | yes | no — threshold > column | **800** |

> **Where "column max when written" comes from.** `CanvasApps/cr9de_strategicplanningmodule…
> _DocumentUri.msapp` embeds a frozen Dataverse metadata cache
> (`References\DataSources.json` → `TableDefinition` → `EntityMetadata`) listing every column's
> `MaxLength` with its own `ModifiedOn` stamp. Those stamps run from 2022-12-13 to 2023-04-24;
> the `.msapp` itself records `LastSavedDateTimeUTC 08/05/2024`, so the cache preserves the
> 2022–23 schema, not the shipped one. The export gives no date for any later resize, so the
> cache establishes *that* the columns changed, never exactly when.

##### 15.5.1.1 Why the legacy thresholds must not be copied

**The counters were coherent when written; the columns moved underneath them.** All 14 scripts
carry `<IntroducedVersion>1.0.0.48</IntroducedVersion>` — one authoring session — and share a
single template, including the same declared-but-unused `var formContext` and the deprecated
global `Xrm.Page`. Compare the two "column max" columns above: **five fields were later narrowed**
(Enterprise Risk `Description` 550→300, Accomplishment `Description` 4000→850, PI Result
`Annual Mitigation / Remarks` 4000→800, Risk Update `MANAGE…` 700→600, Risk Update `ACT…`
700→300) and **four were widened** (PI Result `Q1–Q4 Mitigation / Remarks` 100→800, PCM
`Description` 650→1200, PI `Results Calculation` 100→4000). Not one counter was updated. So
`nrc_GFCPcharCount` warning at 600 was a sane soft limit under a 700-character column, and
`nrc_ERDescrCharCounter` tripping at 313 was reachable under a 550-character one.

**What that means for the nine counters whose threshold now exceeds their column.** They cannot
trip on any value written under the *current* ceiling. They are **not** provably dead, and the
spec must not claim users have never seen these warnings: Dataverse does not truncate stored
values when a column is narrowed, so a row written while Enterprise Risk `Description` was 550
characters wide still holds up to 550, loads into the control at that length, and satisfies
`descr.length >= 313` on the next edit. Whether such rows exist is a question only the live
environment can answer — see the migration hazard below.

**The scripts' own two numbers follow a rounding convention, with two exceptions.** In 12 of 14,
the message states the threshold truncated down to the nearest ten (959→950, 767→760, 755→750,
672→670, 313→310, plus the exact pairs 600→600 and 1000→1000): the message number is the
human-chosen limit, the threshold a trip point a few characters above it. The only breakers are
`nrc_ImpactDescrCharCounter` and `nrc_LikeDescrCharCounter` (313→300, the only delta ≥ 10).
`313` occurs nowhere in the solution or in any of the 25 narrative documents outside these three
scripts. **`nrc_ERDescrCharCounter` is therefore internally consistent** — 313 → "310" obeys the
convention — which is why it is listed here as a column-history problem, not a message mismatch.

**The rule applied in the "Enforce" column.** Take the **lesser of** (a) the column's current
`MaxLength` and (b) any limit stated in the field's own `Description` metadata. **11 of these 14
fields** carry a description reading exactly `Max characters {MaxLength}`, so (a) and (b) agree;
solution-wide that phrasing appears on **25** attributes and agrees with its own `MaxLength` in
all 25, which is what makes it trustworthy. The one field where they diverge is
`nrc_resultscalculation`, whose description reads *"Instruction of how to calculate results for
this indicator. Limited to 670 characters or less."* on a 4 000-character column — there 670
wins, and the shipped counter independently agrees. The JS threshold is discarded everywhere, and
the message must state the same number the validator applies.

**The User Guide is a lagging document — now demonstrated, not assumed.** Its stated limits match
the 2022–23 metadata cache rather than the shipped schema in four places: PI `Description`
1,000 = cache 1000 (now 950); `Mitigation / Remarks` 100 = cache 100 (now 800); PCM
`Description` 650 = cache 650 (now 1200); `MANAGE (Current Risk Response)` 700 = cache 700
(now 600). Treat every number in the guide as describing the 2023 system.

**Three conflicts the rule does not settle — OEDO must decide** (Document 1 §17, open question 5):

| Field | Enforced here | The conflict | The decision |
|---|---|---|---|
| Enterprise Risk `Description` | 300 | User Guide p3: *"Description – Text, character limit 310"* — the guide's only "310", matching the counter's message. But 310 matches **no** width this column has ever carried: the cache shows 550, the shipped schema says 300 twice. | Unlike the four fields above, 310 cannot be explained as a stale cache value, so it may be a deliberate soft limit under the then-550 column. Confirm whether 310 is a live requirement; if so the column must widen, since 310 > 300 is unenforceable today. |
| Accomplishment `Description` | 850 | one of only two counters that can still trip: it warns at 755 saying *"750 characters or less"*, while the column allows 850 and its metadata says 850. Guide says 650. | Enforcing 850 is a visible behaviour change for users accustomed to the 750 warning. If 750 is intended, narrow the column to 750. |
| PCM `Description` | 1200 | guide says 650 (= the cache value), the unwired counter says 1000, the column and its metadata say 1200. | The column was widened 650→1200 and nothing enforces a shorter limit. Confirm 1200 is intended. |

*(PI Result `Mitigation / Remarks` is no longer on this list: the guide's 100 is simply the
pre-widening cache value, so the schema's 800 supersedes it under the staleness finding above.)*

**The two orphaned counters — the fields they were written for no longer exist.** This is the
cleanest case in the table, and it is not the Enterprise Risk story it first appears to be:

- Both are declared as `<Library>` on the **Risk Update** form (`customizations.xml` lines 78202–
  78203), **not** Enterprise Risk, and neither has a `<Handler>` element anywhere —
  `functionName="characterCounterImp"` and `characterCounterLike` both have zero occurrences, so
  neither was ever bound to an event.
- The metadata cache shows `nrc_riskupdate.nrc_impactdescription` and
  `nrc_riskupdate.nrc_likelihooddescription` at `MaxLength` **350**. Both are **absent from the
  shipped Risk Update table**.
- `Workflows/TEMPBackfilloldriskdataintonewcolumns…json` migrated them off that table, reading
  `nrc_riskupdates` rows and writing
  `"item/nrc_inherentconsequencedescription": "@items('Apply_to_each')?['nrc_impactdescription']"`
  and
  `"item/nrc_residuallikelihooddescription1": "@items('Apply_to_each')?['nrc_likelihooddescription']"`.
  Both destinations are 300-character columns carrying `Max characters 300`, and the User Guide
  documents them at *"character limit 300"* — **which is where the orphans' "300" message came
  from**. The author retargeted the message to the new destination and left the old 313 threshold.
- `SPA+-Improvements.doc` lists *"Impact Description"* and *"Likelihood Description"* under its
  deprecated-columns section beneath a **"Risk Updates:"** heading. That heading is **correct**,
  not mis-filed: those were Risk Update columns and they are gone.

Drop both scripts. The same-named `nrc_EnterpriseRisk.nrc_impactdescription` (4 000) and
`nrc_likelihooddescription` (8 000) columns are a separate matter: both carry an **empty**
`Description`, neither appears as `datafieldname` on any form in the solution, and Document 2
§16.1 already marks the first as a duplicate of `nrc_impactdescription1`. Confirm with OEDO
before dropping the Enterprise Risk columns themselves.

> **Migration hazard — size the SQLite length checks before loading, not after.** Five columns were
> narrowed after data had been written, and Dataverse does not truncate existing rows on a
> narrowing. Legacy rows may therefore exceed the current `MaxLength`: Enterprise Risk
> `Description` up to 550 against today's 300, Accomplishment `Description` up to 4 000 against
> 850, `Annual Mitigation / Remarks` up to 4 000 against 800, `MANAGE…` up to 700 against 600,
> and `ACT…` up to 700 against 300. SQLite stores a `TEXT` value of any length, so the limit is the
> `CHECK (length(col) <= 300)` of Document 2 §1 — and a naïve one will reject those rows at load.
> Run `max(length(col))` per column against the live environment during migration planning
> (Document 2 §15), and decide per field whether to widen the target check or truncate with an
> audit trail. This is the one place where the *old* widths matter operationally.

#### 15.5.2 Ribbon button visibility rules (7 scripts)

Each exports `visibilityOfButton(selectedCtrl, cmdProperties)` and decides button visibility
**from the name of the currently selected list view** — the view name is the authorisation
surface. `nrc_PIButtonRules`, `nrc_PIRButtonRules` and `nrc_ERButtonRules` additionally check membership of
the **EDO User** role by hard-coded GUID `9C144FD5-1AD3-ED11-B596-001DD8098656`, gating
`discontinuePerfIndCommand` / `denyPerfIndCommand`, `openPIResCommand`, and
`discontinueEntRiskCommand` / `denyEntRiskCommand` respectively (matching §15.1). The other four
scripts contain no role check.
In the rebuild this must become a server-evaluated permission on the record and the user's
role, never a client-side string comparison on a view name.

| Script | Entity | View names it tests | Buttons it governs |
|---|---|---|---|
| `nrc_AccButtonRules` | Accomplishment | Accomplishments Pending MY Approval · MY Accomplishments in Draft/Revision | `approveAccomplishmentCommand` · `returnAccomplishmentCommand` · `submitAccomplishmentCommand` |
| `nrc_ERButtonRules` | Enterprise Risk | Enterprise Risks Pending Discontinuance · Enterprise Risks Pending MY Approval · Finalized Enterprise Risks · MY Enterprise Risks in Draft/Revision | `approveEntRiskCommand` · `denyEntRiskCommand` · `discontinueEntRiskCommand` · `proposeEntRiskCommand` · `returnEntRiskCommand` · `submitEntRiskCommand` |
| `nrc_PCMButtonRules` | Positive Change Management | MY Positive Change Managements in Draft/Revision · Positive Change Managements Pending MY Approval | `approvePCMCommand` · `returnPCMCommand` · `submitPCMCommand` |
| `nrc_PIButtonRules` | Performance Indicator | Finalized Performance Indicators · MY Performance Indicators in Draft/Revision · Performance Indicators Pending Discontinuance · Performance Indicators Pending MY Approval · Review for carry-over | `approvePerfIndCommand` · `denyPerfIndCommand` · `discontinuePerfIndCommand` · `proposePerfIndCommand` · `returnPerfIndCommand` · `submitPerfIndCommand` · `unflagPI` |
| `nrc_PIRButtonRules` | PI Result | Finalized PI Results · MY PI Results in Draft/Revision · PI Results Pending MY Approval | `approvePIResultCommand` · `openPIResCommand` · `returnPIResultCommand` · `submitPIResultCommand` |
| `nrc_PriButtonRules` | Priority | MY Priorities in Draft/Revision · Priorities Pending MY Approval | `approvePriorityCommand` · `returnPriorityCommand` · `submitPriorityCommand` |
| `nrc_RUButtonRules` | Risk Update | MY Risk Updates in Draft/Revision · Risk Updates Pending MY Approval | `approveRiskUpdateCommand` · `returnRiskUpdateCommand` · `submitRiskUpdateCommand` |

#### 15.5.3 Lookup and sub-grid filtering (3 scripts — all dev leftovers, none wired to a form)

All three are **unfinished development code**: each hard-codes the same literal FetchXML
`<filter type='and'><condition attribute='nrc_businessline' operator='eq' value='Acquisitions' /></filter>`,
so the filter is pinned to one business line and the driving field's value is never used —
`cr9de_lookupFilter` reads `nrc_filterbybusinessline`, logs the name and discards it, and attaches
`addPreSearch` to `Subgrid_new_1` while calling `addCustomFilter` on `Subgrid_performance_indicators`;
`nrc_setSubgridLookupFiltering` additionally hard-codes a DOM button id. None of the three is declared
as a `<Library>` or bound as a `<Handler>` on any form, so none of them runs today. Do **not** port
them as-built. The cascading business-line filter that was evidently intended is a **[NEW]** design
item (§3.5) — confirm the intended filter field with OEDO.

| Script | Driving field | Controls filtered | Mechanism | Wiring |
|---|---|---|---|---|
| `cr9de_lookupFilter` | `nrc_filterbybusinessline` | `Subgrid_new_1` · `Subgrid_performance_indicators` | `addPreSearch` + `addCustomFilter` with FetchXML **hard-coded to `nrc_businessline eq 'Acquisitions'`** | orphan — attached to nothing |
| `nrc_newLookupFilter` | `nrc_addfilter` | `Subgrid_performance_indicators` | as above, same hard-coded filter | orphan — attached to nothing |
| `nrc_setSubgridLookupFiltering` | — | `lookup_Subgrid_performance_indicators` | as above, same hard-coded filter, plus a hard-coded DOM button id | orphan — attached to nothing |

#### 15.5.4 Conditional visibility of fields, sections and sub-grids (8 scripts)

| Script | Entry function | Driving field(s) | Controls shown/hidden | Wiring |
|---|---|---|---|---|
| `cr9de_outcomebased` | `outcomeBased` | `nrc_indicatortype` | `planned_subgrid`, in the `visible="false"` section `null_section_27` — shown **only when Indicator Type = Outcome** (`875670001`), hidden for every other type (§14.1) | registered but `enabled="false"` |
| `cr9de_showCrossCutting` | `showCrossCutting` | `nrc_keyagencyfunction` | `nrc_crosscuttingitem` | orphan — both the driving field and the target control have zero occurrences in `customizations.xml`, and the script is declared on no form (no `<Library>`, no `<Handler>`); **do not port** |
| `nrc_hideQsections` | `hideQsection` | `nrc_datatype` | Section `null_section_3` on tab `General` — hidden when *Data type* = **Qualitative** (`875670000`), shown otherwise. The same section `nrc_quarterlyFields` toggles | orphan — attached to nothing |
| `nrc_hideSubgrid` | `hideSubgrid` | `nrc_keyagencyfunction` · `nrc_attribute` | Fields `nrc_crosscuttingitem` · `nrc_attribute` · `nrc_coveragetype` **and four whole tabs** `budget_tab` · `staffing_tab` · `survey_tab` · `crosscut_tab`. Key Agency Function name = "Cross-Cutting Items" → show `crosscut_tab` + Cross-Cutting Item, hide `survey_tab`, `budget_tab`, `staffing_tab` and Attribute; any other Key Agency Function → the inverse. Attribute name = "Coverage" → show Coverage Type + `budget_tab` + `staffing_tab`, hide `survey_tab`; otherwise the reverse | orphan — the two driving choice fields and all four tabs have zero occurrences in `customizations.xml` (they belong to the abandoned Attribute/Coverage/Budget entities of Document 2 §16.4), and the script is declared on no form; confirm with OEDO before rebuilding |
| `nrc_hideWarning` | `hideSection` | `nrc_approvalqueueflag` | `WebResource_warning` — a control id that exists on no form (§15.5.6) | registered but `enabled="false"` (on the Enterprise Risk and Performance Indicator forms) |
| `nrc_quarterlyFields` | `quarterlyFields` | `nrc_quarters` · `nrc_performanceindicator` | 12 controls — `nrc_q{1–4}rawdata` · `nrc_q{1–4}atfaultoffice` · `nrc_q{1–4}atfaultbusinessline`, each quarter's triple shown only when that quarter is selected in `nrc_quarters`; **plus** section `null_section_3` on tab `General`, hidden when the PI name contains "Qualit" and shown otherwise | orphan — attached to nothing |
| `nrc_showSpecificQuarterFields` | `showSpecificQuarterFields` | `nrc_quarters` (first selected value only — `quarterSelectedArray[0]`) | 16 controls — `nrc_q{1–4}update` · `nrc_q{1–4}atfaultbusinessline` · `nrc_q{1–4}atfaultoffice` · `nrc_q{1–4}rawdata`. **Hide-only:** 875670000 hides Q2–Q4, 875670001 hides all but Q2, 875670002 all but Q3, 875670003 all but Q4; every show-branch is commented out in the source, and the fall-through hides all 16 and calls `formContext.data.refresh(true)` | orphan — attached to nothing |
| `nrc_taskFormAprrovals` | `determineSectionGrid` | `nrc_actiontype` · `nrc_submittedrecordstype` | 14 sub-grids — {`ACC`, `ER`, `RU`, `PI`, `PIRES`, `PRI`, `PCM`} × {`_subgrid`, `_rejgrid`} — **plus** sections `sub_section` and `rej_section` on tab `TASK_TAB`. Action Type `submit` (875670000) shows `sub_section` and exactly one `*_subgrid`; `reject` (875670002) shows `rej_section` and exactly one `*_rejgrid`; anything else hides both sections. Prefix per Submitted Record Type (`ref_record_type`, Document 2 §4): Performance Indicator → `PI_`, PI Result → `PIRES_`, Enterprise Risk → `ER_`, Risk Update → `RU_`, Priority → `PRI_`, Positive Change Management → `PCM_`, Accomplishment → `ACC_` | live |

#### 15.5.5 Remaining scripts (20)

| Script | Entry function | Fields read | Behaviour (read from the source) | Wiring |
|---|---|---|---|---|
| `cr9de_checkUser` | `checkUser` | `nrc_role` · `nrc_user` | Approval Queue row check. When `nrc_role` = `875670003` (Final Approval) it retrieves the selected `nrc_user`'s **systemuser** record and reads the custom column `nrc_finalapprovercapabilities`; the notification *"Cannot be final approver, user has insufficient roles."* fires only when that per-user flag is falsy **and** the role is Final Approval, otherwise the notification is cleared. That column is **not** in the shipped solution — add it to the rebuild's user table and confirm the eligibility list with OEDO (Document 1 §6.8, §17) | live |
| `cr9de_defaultQuarterChoices` | `defaultQuarterChoices` | `nrc_quarter` | Defaults the Quarter multi-select to the single value `875670004` | live |
| `nrc_accFillStratFromPI` | `fillStrategicFields` | `nrc_primaryrelatedpi` · `nrc_strategicgoal` · `nrc_strategicobjective` | On change of `nrc_primaryrelatedpi`, retrieves that Performance Indicator and copies its **Goal, Objective and Strategy** onto the Accomplishment | live |
| `nrc_accRevIcon` | `displayIconTooltip` | — | **List-view cell renderer**, not a form script: when `statuscode` = `Revision` it draws icon `nrc_revisionIcon` with tooltip *"Revisions requested."* and sets that grid row's background to `#ffcd8f`. Reproduce as a row-status style rule in the React data grid (Document 3 §12) | live |
| `nrc_autofillPI` | `fillPIFields` | `nrc_previouspi` | **Revised-PI autofill.** On change of `nrc_previouspi`, retrieves the previous Performance Indicator and copies **22** fields onto the new record: Strategic Goal, Objective, Strategy, Description, Title, Report Level, Contact Person, Owner, Accountable Organization, Agency Wide Support Level, Data Source, Measure Type, Indicator Type, Units, Results Calculation, Lead Business Line, Major Program, Contributing Program, Lead Product Line, Product, Lead Office, Division (Document 1 §8.4) | live |
| `nrc_checkImpactedObjective` | `checkObjective` | `nrc_impactedobjective` · `nrc_impactedstrategicgoal` | Compares the sequence numbers of `nrc_impactedstrategicgoal` and `nrc_impactedobjective`; on mismatch sets the notification *"This Objective does not fall under the Goal selected above."* | live |
| `nrc_checkImpactedStrategy` | `checkStrategy` | `nrc_impactedobjective` · `nrc_strategy` | Same test for `nrc_impactedobjective` vs the impacted Strategy; message *"This Strategy does not fall under the Objective selected above."* | library only — never invoked |
| `nrc_checkObjective` | `checkObjective` | `nrc_strategicgoal` · `nrc_strategicobjective` | Compares the sequence numbers of `nrc_strategicgoal` and `nrc_strategicobjective`; on mismatch sets *"This Objective does not fall under the Goal selected above."* | live |
| `nrc_checkRelatedObjective` | `checkObjective` | `nrc_relatedgoal` · `nrc_relatedobjective` | Same Goal→Objective sequence test on the related-record lookups | live |
| `nrc_checkRelatedStrategy` | `checkStrategy` | `nrc_relatedobjective` · `nrc_relatedstrategy` | Same Objective→Strategy sequence test on the related-record lookups | live |
| `nrc_checkStrategy` | `checkStrategy` | `nrc_strategicobjective` · `nrc_strategy` | Compares the sequence numbers of `nrc_strategy` and `nrc_strategicobjective`; on mismatch sets *"This Strategy does not fall under the Objective selected above."* | live |
| `nrc_disableSubgrid` | `disableSubgrid` | — | Disables `Subgrid_fiscal_year`, `Subgrid_strategies` and `Subgrid_pi` — inside a 5-second `setTimeout`, a timing hack that must become a declarative read-only binding | registered but `enabled="false"` |
| `nrc_displayUserRole` | `displayUserRole` | — | **No-op.** The body only writes the user's roles to the browser console; the DOM-update line is commented out. Debug leftover — do not port | library only — never invoked |
| `nrc_getsubgridcount` | `getsubgridcount` | `nrc_relatedpirequired` | Counts rows in `Subgrid_related_pi` and maintains the `nrc_relatedpirequired` flag from that count (also via `setTimeout`) | live on 1 of 3 registrations — **Priority only**; the Accomplishment and Enterprise Risk registrations are `enabled="false"` |
| `nrc_objectiveSubgridFilter` | `objectiveSubgridFilter` | `nrc_affectedgoal` | Filters sub-grid `Subgrid_new_1` to the Objectives belonging to the Goal in `nrc_affectedgoal` | registered but `enabled="false"` |
| `nrc_preventSave` | `hideSaveSecurityRole` | `cr9de_agencywidesupportlevel` · `nrc_reportlevel` | **Authorisation rule, not a validation rule.** Cancels the save (`preventDefault`) when the user lacks the *EDO User* role **and** either `nrc_reportlevel` = `875670001` or `cr9de_agencywidesupportlevel` = `716580000`, showing *"You do not have the necessary priviledges to create this record with this field value."* (source spelling). **Must be enforced server-side in the rebuild** — see Document 1 §5 and Document 2 §13 | registered but `enabled="false"` |
| `nrc_queueRowValidation` | `showValidStatus` | `nrc_title` | **Unfinished debug stub — do not port.** Builds a FetchXML query for the record's Approval Queue rows, calls `Xrm.WebApi.retrieveMultipleRecords` and then only `console.log`s the result; because that call returns a Promise, even the log loop never iterates. It writes nothing at all — in particular it never touches `nrc_valid` | **wired** — `onsave` handler on the Approval Queue form, enabled |
| `nrc_queueValidation` | `checkQueue` | `nrc_regarding_entry` | Validates the whole Approval Queue chain — order, parallel and alternate combinations — drives the `nrc_invalidwarningtext` banner, and is the **only** code in the solution that writes `nrc_valid` (Document 1 §6.8). Because it is never invoked, **the `Valid` flag is never maintained in the as-built system** | `<Library>` declaration only — no `<Handler>`, so never invoked |
| `nrc_refreshSave` | `refreshSave` | — | Calls `formContext.data.refresh(true)` and nothing else. Declared as a `<Library>` on three forms but **registered as no handler** (`functionName="refreshSave"` has zero occurrences), so the trigger is unknown — the "and Save" in its display name *Refresh and Save* is the only hint. Treat any refresh-after-save behaviour in the rebuild as **[NEW]** | library only — never invoked |
| `nrc_setLookupFieldToCurrentUser` | `setLookupFieldToCurrentUser` | `nrc_reportingperson` | Defaults the `nrc_reportingperson` lookup to the signed-in user | orphan — attached to nothing |

#### 15.5.6 Content-bearing HTML web resources (5)

| Web resource | Role |
|---|---|
| `nrc_invalidwarningtext` | Red (`#cc0000`) warning banner: *"One or more of your approval steps are invalid. Please revise in order to submit."* Placed on exactly one form — the **Accomplishment** "Information" form, tab `general_tab` ("General"), section `null_section_4` ("NOTES FOR RESUBMISSION"), control `WebResource_invalidwarningtext` — and **not** on any Approval Queue form. Its driving script `nrc_hideWarning` is registered `enabled="false"` on both forms that load it (Enterprise Risk and Performance Indicator) and addresses a control `WebResource_warning` and an attribute `nrc_approvalqueueflag` that exist nowhere in the solution, so the Approval-Queue warning UX was never wired up and must be designed fresh (Document 1 §6.8) |
| `nrc_measures_text` | *"Planned Measures Milestone, or Deliverables only apply to Performance Indicators under Strategic Goals 2 and 3"* — **defined but not placed on any form** (no `<Url>` control anywhere in the solution). Its body carries a live business constraint (Document 1 §8); §14.10 records it as guidance text. Confirm with OEDO whether the rebuild should enforce it as validation or keep it as helper text |
| `nrc_officeInstructions` | Static panel on the Office main form (control `WebResource_new_1`, General section): *"Follow link to Office's Team to add/remove members to this office."* |
| `nrc_faqpdf` | Embeds the FAQ PDF; hosted by the **Frequently Asked Questions** Dataverse dashboard (Document 1 §9.7), which the sitemap's FAQ item reaches via `DefaultDashboard` |
| `nrc_userguidepdf` | Embeds the User Guide PDF; hosted by the **User Guides** Dataverse dashboard (Document 1 §9.7), which the sitemap's User Guides item reaches via `DefaultDashboard` |

The other 45 web resources are icons (28 PNG, 14 SVG, 3 JPG) used by the sitemap, ribbon
buttons and dashboards; reproduce them as ordinary static assets of the React app (imported through Vite, or served from `public/`).

---

## 16. Dashboard screens

All 19 pages of the **supplied** Power BI report, rebuilt as React Router routes under
`/{workspace}/dashboards/{page}`. Two further Power BI reports are embedded in the solution but were
not exported for this rebuild — see §16.4.

### 16.1 Shared dashboard chrome

- **Slicer rail** (left or top): Lead Business Line · Reporting BL · Lead Product Line · Fiscal Year ·
  Quarter · Lead Office (Reporting Office on the Agencywide Indicator page) · Division · Major
  Program · Contributing Program · Report Level · View Toggle. Ten filter slicers — see Document 1
  §9.2 on the duplicated BL slicer (two independent slicers bound to the same column).
- **Clear Filters** button.
- **Last Refreshed** / **Next Refresh** indicators — in the rebuilt system these report live data;
  keep the labels so the QPR audience is not surprised.
- **Report Level guidance** shown as help text: *"For QPR presented data, set the Report Level filter
  to BL/PL and CBJ/APPR. For Office Level dashboards, set the Report Level filter to Office Report."*
- Every dashboard route except the two home pages and Historical Trends provides a return control
  (**Back**, or an explicit navigation button) — see Document 1 §9.3.1.
- Filter state is encoded in the URL so a dashboard view is shareable.

### 16.2 Page inventory

| Route | Page | Contents |
|---|---|---|
| `/sp/dashboards/home` | **Strategic Planning Home** | Goal slicer + Goal card · Objectives table (Objective Number, Objective Title) · KPI cards: Strategies · Enterprise Risk(s) · Performance Indicator(s) · Accomplishment(s) · Change Management(s) · **Smart Query** natural-language box · link to the app home dashboard (My To-do's) — the same target as the PM home link · **[NEW]** Goal tooltip on hover (the as-built Goal Tooltip page is orphaned — no visual binds it — so wiring it is a rebuild addition) |
| `/pm/dashboards/home` | **Performance Management Home** | KPI cards: Priorities · Positive Change Management Items · Accomplishments · donut *Count of Risks by PSAT* (Inherent) · donut *Performance Indicators by Result* · pie *Percentage Distribution* · six navigation tiles (Accomplishments, PCM, Priorities, Heatmap, Risk, PI) · link to the app home dashboard (My To-do's) |
| `/pm/dashboards/historical-trends` | **Historical Trends** | Risk count by reporting period (series = PSAT?) · PI result counts by reporting period (series = Result). Both exclude Annual periods; the PI-result trend additionally excludes `No data` results, FY24 Q3 and FY24 Q4, and Indicator IDs beginning `AW` |
| `/pm/dashboards/accomplishments` | **Accomplishments Dashboard** | Total · CBJ/APPR · BL/PL cards · historical trend · selectable accomplishment list → description card · Back |
| `/pm/dashboards/positive-change-management` | **PCM Dashboard** | Trend · PCM count · Accomplishments count · ID+Title list → description card · Back |
| `/pm/dashboards/priorities` | **Priorities Dashboard** | Goal 1 / Goal 2 / Goal 3 counts · Total · trend by fiscal year · Rank + Description table · Back |
| `/pm/dashboards/risks` | **Risk Dashboard** | Inherent donut · Residual pie · historical trend · navigation to PSAT / Non-PSAT / Agencywide / Heatmap · Back to Performance Management home |
| `/pm/dashboards/risks/psat` | **PSAT Risks Dashboard** | Risk list → Inherent/Residual Likelihood and Consequence cards, Risk Description, Current Risk Response, Proposed Risk Response · **Profile** button → QPR Risk View · Back |
| `/pm/dashboards/risks/non-psat` | **Non-PSAT Risks Dashboard** | identical, filtered to Non-PSAT · Back |
| `/pm/dashboards/risks/agencywide` | **Agencywide Risks Dashboard** | identical, filtered to Agencywide risks · Back |
| `/pm/dashboards/risks/heatmap` | **Heatmap** | Mitigation Type toggle (Inherent/Residual) · 3×3 grid of scatter cells LL LM LH ML MM MH HL HM HH · cells are **not** clickable · hover tooltip shows Risk ID + Title · the axis labels carry the risk-scale definitions (Document 1 §9.4.1) as help/ARIA text · buttons: Back, and **See grid & list** → Heatmap and List |
| `/pm/dashboards/risks/heatmap-list` | **Heatmap and List** | the same 3×3 grid beside a Risk Index / Risk ID / Risk Title table · heading "PSAT RISK HEATMAP" · Back to Heatmap |
| `/pm/dashboards/risks/{id}/quadrant` | **View Quadrant** | drill-through on one Risk Update (as-built key `Risk Update[ID]` — the same key as QPR Risk View — with page filter `PSAT? = PSAT`): that risk's single scatter point plus Consequence Text and Likelihood Text cards · Back to Heatmap |
| `/pm/dashboards/risks/{id}/qpr-view` | **QPR Risk View** | the meeting slide: Risk ID and Title · Risk Description · Associated Performance Indicators · Inherent and Residual likelihood/consequence descriptions with colour bars · Current Risk Response · Proposed Risk Response · Risk Monitoring · Informed Monitoring · Budget Strings · Accepted? · Back |
| `/pm/dashboards/performance-indicators` | **Performance Indicator Dashboard** | clustered column trend by reporting period · percentage pie · by-result donut · indicator table with drill-through to PI Profile · button → Agencywide Indicator Dashboard · Back to Performance Management home |
| `/pm/dashboards/performance-indicators/agencywide` | **Agencywide Indicator Dashboard** | Product Line + Indicator (rows) × Office (columns) matrix of max results, cells coloured by status · Back |
| `/pm/dashboards/performance-indicators/{id}/profile` **[NEW]** (the as-built drill-through key is `Performance Indicator[Title]`; routing by id is a deliberate rebuild correction) | **PI Profile** | Back · Indicator headline · Description · Owner · Contact Person · Results Calculation · Operator · Units · Last Quarter Remarks · Contributing Offices list · trend of Target / Min Target / Max Target / Result Value by reporting period |
| *(tooltip)* | **Heatmap Tooltip** | Risk ID + Risk Title |
| *(tooltip)* | **Goal Tooltip** | Goal Title |

### 16.3 Colour rules (must match exactly — Document 1 §9.4)

| Element | Rule |
|---|---|
| Inherent likelihood / consequence tile | Low `#ABE6AC` · Medium `#e8d166` · High `#de6a73` |
| Residual likelihood / consequence tile | Low `#8ADE9E` · Medium `#E8D166` · High `#de6a73` |
| Indicator bar (left / right) | Green `#B7EFB6` · Yellow `#f0e199` · Red `#efb5b9` |
| Overall risk marker | Green `#7AD479` · Yellow `#e8d166` · Red `#ED6161` |
| Agencywide indicator matrix cell | No data `#e6e6e6` · Out of Standard `#de6a73` · In Standard `#B8E6BB` |
| Page background | `#D5D9E2` **[NEW — normalised]** (as-built: 13 of the 19 pages set it; the other 6 inherit a transparent theme background over white — Document 1 §9.4) |

Because colour alone must not convey meaning (Section 508), every coloured element also carries a text
label and an ARIA description.

### 16.4 Other embedded Power BI reports (content not supplied)

The solution embeds **three** Power BI reports as Dataverse dashboards (Document 1 §9.7), not one.
Only the first was exported for this rebuild.

| Dashboard | PowerBIReportId | In app | Status |
|---|---|---|---|
| **Performance Review** | `b1a3a1a0-9ecd-429f-b9fc-735c3fb507d9` | both | supplied — the 19 pages of §16.2 |
| **Performance Management** | `b897caa1-79dd-4798-88f6-b81da61ff25a` | `cr9de_StrategicPlanningModule` | **.pbix not supplied — page inventory unknown** |
| **Strategic Planning Dashboard** | `49d4caf6-5048-4fe7-9de6-f9319e634535` | `nrc_EnterprisePerformanceSystem` | **.pbix not supplied — page inventory unknown** |

All three live in PowerBIGroupId `85361f4a-cc4b-4b07-8408-081c1e2ff89a`. Neither of the two
unsupplied reports has a sitemap SubArea of its own; both are reached from the app's Dashboards
picker. OEDO must export them before dashboard UI build starts — see Document 1 §17.

---

## 17. Admin and utility screens

| Route | Screen | Contents |
|---|---|---|
| `/{ws}/my-todo` | **My To-do List** | Open tasks owned by me or my teams, newest first (Subject, Created On), 8 per page with a view picker, quick find and jump bar · activity timeline · click-through to the underlying records |
| `/{ws}/user-guide` | **User Guides** | Embedded PDF viewer |
| `/{ws}/faq` | **FAQ** | Embedded PDF viewer |
| `/admin/users` | **Users** | SPA Users list; role and team assignment |
| `/admin/teams` | **Groups (Teams)** | Offices and SPA Teams lists; membership management |
| `/admin/business-units` | **Business Units** | Hierarchy management |
| `/admin/roles` | **Security Roles** | Privilege matrix editor |
| `/admin/settings` | **Settings** | Application settings (default approver team, links, environment) |
| `/admin/views` | **Saved Views** | Public and personal view management |
| `/admin/audit` | **Audit Search** | Field-level history search |
| `/admin/jobs` | **Background Jobs** | Job status and manual run |
| `/admin/import` | **Data Import** | Template download, upload, validation, error report |
| `/admin/approval-queues` | **Approval Queue Setup** | Ordered approver chains per record type |

---

## 18. Accessibility, responsiveness and UX rules

### 18.1 Accessibility (Section 508 / WCAG 2.1 AA)

| Requirement | Implementation |
|---|---|
| Keyboard operability | Every command, grid cell, sub-grid and dialog reachable and operable by keyboard; visible focus ring |
| Screen readers | Semantic landmarks; `aria-live` regions for command results and validation summaries; grids expose row/column headers |
| Colour contrast | ≥ 4.5:1 for text; the dashboard palette in §16.3 is paired with text labels so colour is never the only signal |
| Form labelling | Every control has a programmatic label; required fields marked both visually and with `aria-required` |
| Error identification | Validation summary at the top of the form plus inline messages; focus moves to the first error |
| Character counters | Announced politely, not on every keystroke |
| Charts | Each chart has an accessible data table alternative and a text summary |
| Zoom | Usable at 200 % without horizontal scrolling |
| Motion | No auto-playing animation; respect `prefers-reduced-motion` |

### 18.2 Responsiveness

| Breakpoint | Behaviour |
|---|---|
| ≥ 1280 px | Full shell: left nav expanded, grids at full column set, dashboards at the designed 1280×720 canvas |
| 960–1279 px | Left nav collapses to icons; grids drop low-priority columns |
| 600–959 px | Single-column forms; slicer rail becomes a filter drawer; dashboards stack |
| < 600 px | Read-optimised: list cards instead of grids; commands in an overflow menu |

### 18.3 Usability improvements requested by users (to be designed in)

From `SPA+-Improvements.doc`:

1. More hover-over help text on fields.
2. Display character limits on the QPR view.
3. Implement sensible **default views** to avoid user confusion.
4. Minimise manual data entry.
5. Provide a **duplicate record year-to-year** action.
6. Make the distinction clearer between **Performance Indicators vs Indicator Results** and
   **Enterprise Risks vs Risk Updates** — e.g. explicit "definition" vs "quarterly reporting" labelling
   in the navigation and on the forms.
7. Remove deprecated components from the UI.

Plus, from the Product Vision: **glossary hover-over definitions** for any Strategic-Plan term
appearing on a dashboard.

---

## 19. Screen → API → table traceability matrix

| Screen | Primary API | Primary tables |
|---|---|---|
| Strategic Planning Home dashboard | `/analytics/strategic-planning-home` | `analytics_dim_goal`, `dim_objective`, `dim_strategy`, `fact_*`; for another plan `dim_plan_goal`, `dim_plan_objective` |
| Performance Management Home dashboard | `/analytics/performance-management-home` | `analytics_fact_risk_update`, `fact_pi_result`, `fact_accomplishment`, `fact_positive_change_management`, `fact_priority` |
| Historical Trends | `/analytics/historical-trends` | `analytics_fact_risk_update`, `fact_pi_result`, `dim_reporting_period` |
| Accomplishments dashboard | `/analytics/accomplishments` | `analytics_fact_accomplishment` |
| PCM dashboard | `/analytics/positive-change-management` | `analytics_fact_positive_change_management` |
| Priorities dashboard | `/analytics/priorities` | `analytics_fact_priority` |
| Risk dashboards (4) | `/analytics/risks/*` | `analytics_fact_risk_update`, `dim_enterprise_risk` |
| Heatmap / Heatmap+List / View Quadrant | `/analytics/risks/heatmap*`, `/analytics/risks/{id}/quadrant` | `analytics_fact_risk_update` |
| QPR Risk View | `/analytics/risks/{id}/qpr-view` | `perf_risk_update`, `perf_enterprise_risk`, `perf_risk_update_performance_indicator` |
| PI dashboards (2) + PI Profile | `/analytics/performance-indicators/*` | `analytics_fact_pi_result`, `dim_performance_indicator`, `fact_agency_wide_indicator` |
| Performance Indicators list | `/performance-indicators` | `perf_performance_indicator` |
| Performance Indicator form | `/performance-indicators/{id}` + relationship endpoints | `perf_performance_indicator` + 14 junctions + `perf_planned_measure` |
| PI Results list | `/pi-results` | `perf_pi_result` |
| PI Result form | `/pi-results/{id}`, `/periods`, `/quarters` | `perf_pi_result`, `pi_result_period`, `pi_result_quarter` + 8 junctions |
| Enterprise Risks list | `/enterprise-risks` | `perf_enterprise_risk` |
| Enterprise Risk form | `/enterprise-risks/{id}` + relationships | `perf_enterprise_risk` + 8 junctions |
| Risk Updates list | `/risk-updates` | `perf_risk_update` |
| Risk Update form | `/risk-updates/{id}` + relationships | `perf_risk_update` + 6 junctions |
| Accomplishments list / form | `/accomplishments` | `perf_accomplishment`, `accomplishment_quarter` + 6 junctions |
| Priorities list / form | `/priorities` | `perf_priority`, `priority_quarter` + 6 junctions |
| PCM list / form | `/positive-change-management` | `perf_positive_change_management` + 6 junctions |
| Goals / Objectives / Strategies | `/goals`, `/objectives`, `/strategies` | `plan_goal`, `plan_objective`, `plan_strategy` + fiscal-year junctions |
| Performance Goals | `/performance-goals` | `plan_performance_goal` |
| External Factors | `/external-factors` | `plan_external_factor` + 2 junctions |
| Definitions | `/definitions` | `plan_definition` + 3 junctions |
| Fiscal Years | `/fiscal-years` | `ref_fiscal_year` |
| Offices / Divisions / Organizations | `/offices`, `/divisions`, `/organizations` | `ref_office`, `ref_division`, `ref_organization`, `ref_office_division` |
| Business Lines / Product Lines / Products | `/business-lines`, `/product-lines`, `/products` | `ref_business_line`, `ref_product_line`, `ref_product`, `ref_business_line_product_line` |
| Major Programs / Contributing Programs | `/major-programs`, `/contributing-programs` | `ref_major_program`, `ref_contributing_program` |
| Office Goals | `/office-goals` | `ref_office_goal` |
| Actions (Planned Measures) | `/planned-measures` | `perf_planned_measure`, `core_file_attachment` |
| Priority Questions / Evaluations / Research Activities | `/priority-questions`, `/evaluations`, `/research-activities` | `evidence.*` |
| Signposts / Key Areas | `/signposts`, `/key-areas` | `plan_signpost`, `plan_key_area` |
| Bulk Submit / Approve / Return | `/workflow/*` | `wf_submission`, `wf_approval`, `wf_rejection`, `wf_workflow_transition`, `core_task` |
| Discontinue / Propose / Deny | `/workflow/*-discontinue` | `perf_performance_indicator`, `perf_enterprise_risk` |
| Open PI child records | `/workflow/reopen-pi-results` | `perf_pi_result` |
| Flag / Unflag carry-over | `/performance-indicators/*-carryover` | `perf_performance_indicator` |
| My To-do List | `/tasks?view=my-tasks` | `core_task`, `wf_submission`, `wf_approval`, `wf_rejection` |
| Notifications | `/notifications` | `wf_notification` |
| Submissions / Approvals / Rejections lists | `/submissions`, `/approvals`, `/rejections` | `wf.*` |
| Approval Queue Setup | `/approval-queues` | `wf_approval_queue` |
| Users / Teams / Roles / Business Units | `/users`, `/teams`, `/security-roles`, `/business-units` | `core.*` |
| Settings | `/settings` | `core_app_setting` |
| Saved Views / Forms | `/view-definitions`, `/form-definitions` | `core_view_definition`, `core_form_definition` |
| Audit Search | `/admin/audit` | `wf_field_audit` |
| Data Import | `/import/*` | `staging.*` |
| User Guide / FAQ | static | `core_app_setting` links |

---

## 20. Build checklist (screens and endpoints)

| Category | Count to build |
|---|---|
| List-view screens | 37 entities — the 39 entities with public views catalogued in §13.16, less `nrc_pisubmissionapprovals` (§13.15) and the archive-only `nrc_Priorities` |
| Named views to reproduce | 190 business views — 154 public list views + 36 per-entity "My …" filter views (334 saved queries in total; the other 144 are the system-generated advanced-find, sub-grid, quick-find and lookup views, 4 per entity across 36 entities) |
| Form screens (main) | 37 — the solution ships 41 main forms over 39 entities (Team carries three); `nrc_pisubmissionapprovals` (§13.15) and the deprecated `nrc_Priorities` need no screen |
| Quick-create forms | 2 (PI Result, Approval Queue — §14.13) |
| Quick-view panels | 4 — the source places 5, and its two on a PI Result are built as one card (Performance Indicator on PI Result ×2 in the source, Enterprise Risk on Risk Update, Answer on Priority Question — polymorphic over Evaluation / Research Activity, Associated Signpost on Key Area) |
| Sub-grids across all forms | 80 placements over 60 distinct relationships |
| Dashboard pages | 19 — 17 full pages + 2 tooltip pages (§16.2) |
| Dialogs | 30 confirmation + success pairs |
| Bulk command endpoints | 9 |
| Resource endpoint groups | 43 — the §3.3 resource list: 30 business resources (Strategic Plan 9 · Organisation 9 · Performance Management 9 · Evidence Building 3), 5 workflow resources and 8 identity/admin resources (including `/positions`, §3.3), each with the §3.1 standard operation set |
| Relationship endpoint groups | 127 slugs over 23 resources — all 61 many-to-many junctions of Document 2 §10 (several reachable from both ends, now including every junction the nine Organisation resources are named by), 8 one-to-many child collections surfaced on the legacy forms (plus `enterprise-risks → risk-updates`, data model only), and 1 multi-select junction (Document 2 §10.11). Was 85 over 18: every addition is the reverse end of a junction already counted here, so the 61 is unchanged. The `*_quarter` junctions are excluded on purpose — they are the §10.11 multi-select served by `/{res}/{id}/quarters`, not sub-grids |
| Analytics endpoints | 24 — 19 (§6.2) + 3 export (§6.5) + 2 natural-language (§6.6) |
| Metadata endpoints | 10 |
| Admin endpoints | 12 rows / 16 method+path pairs (§8) |
| Background jobs | 8 (§7.1) |

**How the 115 source forms reduce to the screens above.** Document 1 §1.3 counts 115 forms: 41 main
+ 2 quickCreate + 37 quick-view + 35 card. The 41 main forms become 37 screens (39 entities carry a
main form — Team carries three, collapsed to the two of §14.14 — less `nrc_pisubmissionapprovals`
and the archive-only `nrc_Priorities`); both quickCreate forms are reproduced; of the 37 quick-view
forms only the 5 actually placed on a form are reproduced (§12); and the 35 card forms are not
reproduced at all — a card form is a model-driven mobile artefact with no React equivalent.

---

*End of Document 3 — Complete API and UI Screen Specification.*
*See Document 1 for the project summary and Document 2 for the database schema.*
