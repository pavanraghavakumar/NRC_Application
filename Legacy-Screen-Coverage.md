# NRC Strategic Planning & Performance Management System
# Document 4 — Legacy screen coverage

**This is a record of the rebuild, not a description of the source.** Documents
1 to 3 and [`training-walkthrough/`](training-walkthrough/) are the
specification; this file traces one against the other, so that the question
"does the rebuild do what the recorded application does?" can be answered
screen by screen rather than taken on trust.

Its subject is the 11-minute training recording transcribed in
[`training-walkthrough/README.md`](training-walkthrough/README.md) — the only
source material that shows the legacy application **in use**, as opposed to
describing it. Every screen the presenter opened is listed below with the route
that serves it here.

Routes are given as they are typed. `{id}` is a record id; `?view=` slugs are
the ones `/metadata/entities/{e}/views` publishes, not names invented here.

> **React + SQLite edition.** The routes, screens and checks below do not depend
> on the front-end framework or the database. The component names (`shell/Header`,
> `shared/ViewSelector`, …) are those of the React client (Document 3 §11.6). The
> figures quoted under "How this is kept true" (263 elements, 362 routes) were
> measured on the reference build — Angular on PostgreSQL. For the React + SQLite
> build they are the bar to meet, and they count as met only once the same runs
> pass against it.

---

## The shell, present on every screen

| Recorded | Here |
|---|---|
| Power Apps header: waffle, app name, global Search, +, gear, ?, account | `shell/Header` — app switcher, workspace name, global search, notification bell, help, account menu |
| Left navigation, grouped **At a glance… / Performance Management / Quarterly Data / Admin** | `shell/LeftNav`, rendered from `GET /metadata/navigation` — the groups and their order come from the API, not from a list in the client |
| Platform Home · Recent · Pinned | not reproduced. These are Power Apps' own chrome, not part of the application; the workspace switcher and global search cover the same ground |

---

## The 33 recorded screens

| # | Time | Recorded screen | Route |
|---|---|---|---|
| 1 | 00:19 | My To-do List | `/pm/my-todo` — including the A–Z index bar of the My Tasks sub-grid, the only screen the recording shows one on |
| 2 | 00:44 | Performance Review dashboard | `/pm/dashboards/home` |
| 3 | 01:12 | Risk Dashboard | `/pm/dashboards/risks` |
| 4 | 01:26 | PSAT Risk Dashboard | `/pm/dashboards/risks/psat` |
| 5 | 01:37 | QPR Risk View | `/pm/dashboards/risks/{riskUpdateId}/qpr-view` |
| 6 | 01:50 | PSAT Risk Heatmap | `/pm/dashboards/risks/heatmap` |
| 7 | 02:04 | Performance Indicators dashboard | `/pm/dashboards/performance-indicators` |
| 8 | 02:14 | Agencywide Indicators matrix | `/pm/dashboards/performance-indicators/agencywide` |
| 9 | 02:41 | Strategic Planning Dashboard | `/sp/dashboards/home` |
| 10 | 03:10 | The same dashboard filtered to Goal 1 | the Goal slicer on the filter rail; the state is in the URL, so the filtered view is shareable (§16.1) |
| 11 | 03:21 | Smart Query — suggestions | the Smart Query panel on `/sp/dashboards/home`, seeded from `/analytics/query/suggestions` |
| 12 | 03:45 | Smart Query — a list answer | same panel |
| 13 | 04:01 | Smart Query — a chart answer | same panel; the answer's own `visual` block decides ring, bars or a single figure. The narrator's question here is *accomplishments by office*, and the parity run asks that exact question: the groupings a subject offers are derived from the organisational columns its fact declares, so office is answered wherever the fact carries one and refused by name where it does not |
| 14 | 04:12 | FAQ | `/pm/faq` |
| 15 | 04:22 | User Guides | `/pm/user-guide` |
| 16 | 04:49 | All Performance Indicators — list | `/pm/performance-indicators?view=all-performance-indicators` |
| 17 | 05:01 | Performance Indicator form — General | `/pm/performance-indicators/{id}` |
| 18 | 05:20 | …the same form's organisation section | `/pm/performance-indicators/{id}` |
| 19 | 05:25 | PI Results — Quarterly Updates tab | `/pm/pi-results/{id}/quarterly-updates` |
| 20 | 06:06 | All Enterprise Risks — list | `/pm/enterprise-risks?view=all-enterprise-risks` |
| 21 | 06:25 | Enterprise Risk form | `/pm/enterprise-risks/{id}` |
| 22 | 06:42 | Risk Update — inherent / residual | `/pm/risk-updates/{id}` |
| 23 | 07:01 | Risk Update — monitoring and mitigation | `/pm/risk-updates/{id}` |
| 24 | 07:11 | Priorities in Draft/Revision — list | `/pm/priorities?view=priorities-in-draft-revision` (the default) |
| 25 | 07:29 | Priority form | `/pm/priorities/{id}` |
| 26 | 07:52 | Finalized Accomplishments — list | `/pm/accomplishments?view=finalized-accomplishments` |
| 27 | 08:00 | Accomplishment form | `/pm/accomplishments/{id}` |
| 28 | 08:23 | All Positive Change Management — list | `/pm/positive-change-management?view=all-positive-change-managements` |
| 29 | 08:35 | Positive Change Management form | `/pm/positive-change-management/{id}` |
| 30 | 09:25 | The view selector, opened | `shared/ViewSelector` on every list screen — public and personal views grouped, the default marked |
| 31 | 09:38 | MY Priorities in Draft/Revision | `/pm/priorities?view=my-priorities-in-draft-revision` |
| 32 | 09:47 | Submit for Approval — confirmation dialog | `shared/CommandBar` + `shared/ConfirmDialog`; the wording is served by `/metadata/commands/{e}`, never composed here (§15.2) |
| 33 | 10:10 | The approver's views | `?view=priorities-pending-approval` and `?view=priorities-pending-my-approval`, and the equivalent pair on every record type |

## The grid command bar

The recording shows the command bar twice, once unselected and once with a row
selected (04:49, 09:38).

| Recorded | Here |
|---|---|
| Show Chart | a chart of the current view, grouped by a column the reader picks. It reads the **view**, not the page, and prints how many records it counted of how many there are |
| + New · Delete ⌄ · Refresh · Export to Excel ⌄ · Import from Excel ⌄ | `shared/CommandBar`; import is the §17 screen at `/admin/import` |
| Submit for Approval · Edit · Activate · Deactivate · Assign (on selection) | `shared/CommandBar`, gated on the selected rows' status and the caller's roles — never on a view name (§15.5.2) |
| Edit columns · Edit filters · Filter by keyword | `shared/ColumnChooser`, `shared/FilterPanel`, `shared/QuickSearch` |
| Share | not reproduced. Sharing a record is a Dataverse access-grant; row visibility here is the API's privilege-depth predicate over the §4.3 matrix (Document 2 §13), so there is nothing for a per-record share to write |

## The approval workflow

Stated in the narration rather than shown (08:51 – 10:43), and reproduced in
full:

| Recorded behaviour | Here |
|---|---|
| Every record type in the two groups has an approval process, **optional** | the §4.5 workflow endpoints; a record can be finalised without one |
| Submitting creates a task for the EDO admins, on **their** To-do List | `POST /{res}/{id}/submit`; the task appears on `/pm/my-todo` |
| Rejection returns the record and puts a task on the submitter's list | `POST /{res}/{id}/return`; the comments show in `shared/ApproverCommentsBanner` above the form |
| Approval finalises and **locks** the record from edits | the API's §4.4 guard matrix; the form renders read-only and the command bar drops its write commands |
| Which view you are looking at is how you find your work | the view selector, and the `MY … in Draft/Revision` / `… Pending MY Approval` pairs above |

---

## Where the rebuild goes past the recording

These are not additions for their own sake — each one answers a question the
recorded screen raises but cannot settle.

| | |
|---|---|
| **The heat map plots risks, on named axes** | the source's grid is nine coloured squares with no axis labels, so which corner is "likely and severe" has to be known in advance. Here consequence runs up the side and likelihood along the bottom, both labelled, and each risk is its own marker; a **Risk IDs** toggle prints the identifiers when the cell is sparse enough to read |
| **The quadrant shows movement** | Document 1 §9.3 page 14 records that the shipped page carries two hard-coded filters — a deleted PSAT column and a single risk id — so it answers "where is this one risk". Here both the inherent and the residual placement are drawn, joined by an arrow, which is the question a quarterly review actually asks |
| **The home page carries the heat map** | the source shows it there and the rebuild had left it to its own page. The ring says how many risks there are; the grid says how bad they are |
| **Charts state their coverage** | `Show Chart` prints what it counted of how many. A figure that silently charts one page of a view is wrong on every page but the one it was read on |
| **Every chart has a data table** | §18.1 requires it, and because each is drawn inside one shared frame, none can ship without one |
| **A dark theme** | not in the source at all; the palette was selected against the dark surface rather than inverted |

## What is deliberately not reproduced

| | Why |
|---|---|
| The Power BI report itself | there is no report to embed. §6 serves the same figures as JSON and the client draws them |
| LAST REFRESHED / NEXT REFRESH timestamps | the source's dashboards were a four-hourly extract, so a reader had to know how stale the numbers were. These read the operational tables directly, so the rail says **live** rather than printing two timestamps that would imply a staleness that does not exist |
| The platform chrome — Save As, Set As Default, Share, Open in Power BI | Dataverse dashboard commands, not application behaviour |
| The Timeline panel's full feature set | the To-do List shows a task's activity on demand, read from `GET /tasks/{id}/timeline`; notes and attachments are §13.10 sub-resources rather than a Dataverse timeline control |

---

## Where the recording and the solution export disagree

The transcription lists what was legible on a video frame; Documents 1 to 3 were
extracted from the solution itself. Four places disagree, and each is settled
here rather than left for the next reader to re-litigate.

| The recording shows | The documents say | Here |
|---|---|---|
| The lifecycle column headed **Stage** on the Enterprise Risk, Priorities and Positive Change Management grids | Document 3 §13 prints it as "Status" **and says so**: "its shipped label is 'Stage' on nine tables and 'Approval Status' on Approval Queue". Document 2 §2.4 names the nine and adds "the rebuild renames it" | **Stage** on the nine, **Approval Status** on Approval Queue, **Status** on Planned Measure, **Status Reason** elsewhere. `scripts/generate_view_columns.py` applies the shipped label after transcribing §13, so 52 views now carry the heading the source shipped |
| **Risk Outlook** in the Risk Update's left column | Document 1 p.579 — "hidden on the form" — and Document 3 §14, "Risk Outlook (hidden)" | The field is on the record and in the form definition, carrying `visible: false`. Not rendering it is the source's own layout, not an omission |
| The Priorities grid column headed **Priorities Title** | Document 3 §13.6, extracted from the solution, gives the column as **Title** | **Title**. The frame shows the attribute's display name; the view names the column |
| Quarterly blocks labelled **Q1 … Q4** | The field names are `Qn Results`, `Qn Target` …; the blocks are **Quarter 1** … **Quarter 4** | Blocks headed **Quarter 1** to **Quarter 4** and **Annual**, fields named as the source names them |

---

## How this is kept true

Nothing above is a claim a reader has to take on faith:

* `npm run e2e:coverage` parses the routes **out of this file** and opens each
  one in a browser. A route renamed here without being renamed in the client,
  or the other way round, fails the run — the table cannot quietly stop being
  true.
* `npm run e2e:parity` goes further than the routes. For each of the 33 screens
  it takes the transcription's own "On screen:" list — every command, column,
  field, sub-grid, axis, toggle and tile — and asserts the rebuild serves it:
  **263 elements across the 33 screens**, all passing. A check that fails is
  either a gap or one of the four disagreements above; there is no third
  answer, and the table cannot drift without the run saying so.
* `npm run e2e:smoke` opens every screen in this table in a browser and asserts
  it rendered.
* `npm run e2e:narrow` opens each kind of screen at 400px in both themes and
  fails on any box that runs past the edge. It measures elements rather than
  `document.scrollWidth`, because the shell's main region is `overflow-x:
  hidden` and clips such a page instead of scrolling it — which is how the left
  navigation came to be taking two thirds of a phone screen while every
  document-level check reported no overflow.
* `npm run e2e:integration` visits every route the client can reach — 362 of
  them — and asserts the rows on screen are the rows the API returned.
* `npm run e2e:interactions` drives the view selector, the command bar and its
  dialogs, sub-grids and the unsaved-changes guard.
* `npm run verify` re-reads the live metadata and fails if the route map, the
  saved views or the form layouts drift from what the API publishes.
