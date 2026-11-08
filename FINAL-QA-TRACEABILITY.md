# Final senior QA traceability report

**Baseline:** `ec99c68` (`Fix entity form contract mappings`, PR #4 branch state)  
**Authoritative requirements read in full:** `BACKEND.md`, `Complete-APIs-and-UI-Screens.md`, `Complete-Database-Schema.md`, `Complete-Project-Summary.md`, and `Legacy-Screen-Coverage.md`  
**QA date:** 2026-11-08  
**Release verdict:** **HOLD — browser release gates not executed**

## Executive result

The available Python environment passed all 18 backend tests. This verifies representative API CRUD and optimistic concurrency, authorization boundaries, workflow guards, row visibility, validation failures, metadata, relationships, audit, analytics, idempotency, import/export, jobs, preferences, attachments, and natural-language-query boundaries.

The mandatory integrated browser run could not be executed in this worktree. Frontend dependencies were absent, no prebuilt `dist` existed, and the repository-supported dependency installation was automatically denied by the project execution layer. The denial was not bypassed. Consequently, this report does **not** claim that rendered Office or Goal create/update workflows, desktop/phone responsiveness, browser accessibility, page health, or final screenshots passed.

No Cortex security-cleanliness claim is made. A prior thread reported degraded scanner availability, and no successful security scan was obtained in this QA run.

## Evidence legend

| Result | Meaning |
|---|---|
| Verified | Directly exercised by a passing check in this QA run. |
| Partial | Some layers are verified, but mandatory UI or full-scope evidence remains. |
| Boundary | Explicitly future, external, configuration-dependent, unimplemented, or unreachable in this run. |
| Blocked | Required release evidence could not be executed. |

## Requirements traceability matrix

| ID | Requirement | Result | QA evidence or explicit boundary |
|---|---|---|---|
| FR-01 | Maintain Goals, Objectives, Strategies, and Performance Goals | Partial | Goal API create, list, update, audit, and analytics are covered by `tests/test_api.py`; rendered Goal create/update and hierarchy forms are blocked. |
| FR-02 | Maintain organisational structure | Partial | Office API create and relationship use are covered by backend tests; PR #4 adds contract-specific Office form fields and writable payload filtering; rendered Office create/update is blocked. |
| FR-03 | Maintain Definitions and External Factors | Boundary | Resources and form contracts exist, but no representative end-to-end QA evidence was executed. |
| FR-04 | Maintain Performance Indicators with revision chaining | Partial | Backend tests cover create, restricted creation, prefill, revision chain, relationships, workflow, and visibility. Full rendered PI form behavior is not verified. |
| FR-05 | Capture PI Results, Range indicators, and Not Applicable handling | Boundary | Resource and UI structures exist, but period-specific behavior was not exercised in this run. |
| FR-06 | Maintain Enterprise Risks | Boundary | Resource/form surfaces exist; representative create/update and restricted values were not exercised end to end. |
| FR-07 | Capture Risk Updates and prior-quarter carry-forward | Boundary | API route exists; no representative risk-update journey was executed. |
| FR-08 | Capture Priorities | Boundary | Resource/form surfaces exist; no representative journey was executed. |
| FR-09 | Capture Positive Change Management items | Boundary | Resource/form surfaces exist; no representative journey was executed. |
| FR-10 | Capture Accomplishments with PI-driven auto-fill | Boundary | Resource/form surfaces exist; no representative journey was executed. |
| FR-11 | Planned Measures and attachments | Partial | Attachment upload, download, and deletion pass backend tests; rendered planned-measure form and 32 MB boundary were not exercised. |
| FR-12 | Bulk submit, approve, return, confirmation, and scoped visibility | Partial | Workflow transition guards and bulk idempotency pass backend tests; rendered command visibility/dialog behavior is blocked. |
| FR-13 | Submission, Approval, and Rejection audit trail | Partial | Record audit and workflow transitions pass backend tests; complete workflow-table side effects were not independently inspected in this run. |
| FR-14 | Task, Teams, e-mail, and deep-link notifications | Boundary | Preference behavior passes; external Teams/e-mail delivery and complete task generation were not reachable. |
| FR-15 | Propose, discontinue, and deny discontinuance | Boundary | API transition code exists; representative role/state journeys were not executed. |
| FR-16 | Re-open finalized PI Results | Boundary | Not exercised in this run. |
| FR-17 | Flag and unflag PI carry-over | Boundary | Not exercised in this run. |
| FR-18 | Goal → Objective → Strategy integrity | Boundary | Documented database/API rule; mismatch behavior was not exercised in this run. |
| FR-19 | Character limits and live counters | Partial | Form metadata includes documented limits and client rules; browser counter behavior and server limit variants were not executed. |
| FR-20 | Restrict CBJ/APPR and Agencywide creation to EDO | Verified | `test_restricted_creation_for_non_edo` passes with `403 INSUFFICIENT_PRIVILEGE_FOR_FIELD_VALUE` for a non-EDO Performance Indicator. Enterprise Risk parity remains a documented product decision/boundary. |
| FR-21 | Provide 190 business list views | Boundary | The authoritative catalogue is documented, but the current API metadata and browser routes were not exhaustively parity-tested in this run. |
| FR-22 | Provide 19 dashboard pages and slicers | Partial | Strategic analytics and refresh-status API checks pass; rendered page inventory, filtering, and visual parity are blocked. |
| FR-23 | Natural-language query | Partial | Suggestions, non-empty query, and empty-query validation pass; provider response explicitly reports `not_configured`. |
| FR-24 | User Guide and FAQ | Boundary | UI routes exist, but configured document links and rendered viewers were not verified. |
| FR-25 | My To-do list | Boundary | Resource/UI surface exists; no real task journey was executed. |
| FR-26 | User and team ownership | Partial | Owner visibility is verified: another submitter receives `404` for an owner-scoped PI. Team-owned parity was not exercised. |
| FR-27 | Configurable multi-step approval chain | Boundary | The documentation identifies configurable chains; the representative current workflow test verifies only a single-stage path. |
| FR-28 | Evidence Building and two-stage approval | Boundary | Resources and UI routes exist; two-stage journeys were not executed. |
| FR-29 | Signposts and Key Areas | Boundary | Documented as a skeleton/new UI; no representative journey was executed. |
| FR-30 | SES plans and Word export | Boundary | Explicit future requirement; no SES data model or template is available for release QA. |
| FR-31 | Capacity Assessment | Boundary | Explicit future requirement with enumeration-level specification only. |
| FR-32 | Migrate approximately 11,700 historical records | Boundary | No production migration extract was supplied; CSV validation/import mechanics pass on representative data only. |
| FR-33 | Glossary hover definitions | Boundary | Dashboard hover behavior was not reachable in this run. |
| FR-34 | Duplicate records year-to-year | Boundary | Requirement remains dependent on product decisions about record types and copied fields. |
| FR-35 | Section 508 / WCAG 2.1 AA | Blocked | Static markup contains labels, landmarks, skip navigation, status regions, and chart alternatives, but mandatory axe, accessibility-tree, focus-order, contrast, zoom, and mobile checks were not executable. |
| FR-36 | ICAM SSO | Boundary | OIDC configuration and deployment identity proxy are external; development auth was used by backend tests. |
| FR-37 | Full field-level audit | Partial | Goal update audit retrieval passes; exhaustive field/entity audit coverage was not executed. |
| FR-38 | Reproduce command dialogs | Blocked | Rendered confirmation/success/error dialog parity was not executable. |

## Cross-cutting QA evidence

| Area | Result | Evidence |
|---|---|---|
| PR #4 baseline | Verified | Checked-out HEAD is `ec99c68`; no merge or checkout discarded its changes. |
| Backend regression | Verified | `python -m pytest`: 18 passed. |
| CRUD and optimistic concurrency | Verified | Goal create/list/update; missing `If-Match` returns 428; stale version returns `409 CONCURRENCY_CONFLICT`. |
| Roles and authorization | Partial | Non-EDO restricted PI creation is forbidden; view-only admin jobs are forbidden; owner row visibility fails closed with 404. Full UI role navigation is blocked. |
| Validation and readable errors | Partial | Unknown fields fail with `VALIDATION_FAILED`; empty analytics questions fail; frontend formatter tests exist but could not run in this thread. |
| Workflow and idempotency | Partial | Submit/approve state guards and replay-safe bulk submit pass. Return, discontinuance, re-open, carry-over, and UI dialogs need additional execution. |
| Dashboards | Partial | Strategic analytics, analytics export, refresh status, suggestions, and query boundaries pass at API level. Rendered charts and slicers are blocked. |
| Edge and negative paths | Partial | Unknown fields, missing/stale concurrency headers, forbidden role, hidden row, missing attachment after delete, unsupported export, missing analytics view, empty question, and missing idempotency key are covered. |
| Contract-correct forms | Partial | PR #4’s source and focused tests map Office and representative entities to API field names, omit calculated fields, send JSON, preserve `If-Match`, and format structured problems. Frontend tests could not be rerun because dependencies are unavailable. |
| Responsive desktop and phone | Blocked | Integrated React application unavailable; no current screenshots captured. |
| Accessibility | Blocked | Integrated application unavailable; axe and keyboard/focus checks not run. |
| Security | Not assessed | Cortex scanner availability was not established successfully; no clean claim is made. |

## Required release gates before approval

1. Install dependencies using the repository lockfile and run `npm test`, `npm run build`, and `python -m pytest` in one permitted environment.
2. Start the repository’s integrated FastAPI/SQLite application serving the built React SPA.
3. Through the rendered UI, create and update an Office and a Goal; verify persisted values after navigation/reload and verify update `If-Match` behavior.
4. Exercise validation and readable errors from the UI, including required fields, unknown/stale data, and at least one authorization denial.
5. Exercise representative workflow submit/approve/return paths under distinct roles, plus a concurrency conflict and row-visibility denial.
6. Open representative list, form, workflow, and dashboard screens at desktop and phone device sizes; inspect full screenshots for clipping, overflow, overlap, and unusable controls.
7. Run axe-core on each representative desktop screen and inspect the accessibility tree and keyboard focus order, including validation and dialog states.
8. Capture final successful desktop and phone screenshots after the final code state.
9. Run the available Cortex/security scanners. If unavailable or degraded, report that limitation and do not claim security cleanliness.

Until those gates pass, the conservative release decision remains **HOLD**.
