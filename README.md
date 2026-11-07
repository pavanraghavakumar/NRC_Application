# NRC SPA documentation — React + SQLite edition

A copy of `Proposal/Documentation` (repository commit `21fb8b6`) with the target stack changed to
**Python · React (latest) · SQLite**. Both the front end (Angular → React) and the database
(PostgreSQL → SQLite) changed; the Python API, its contract and the screens did not. The as-built
analysis of the legacy system is unchanged.

| Document | What changed |
|---|---|
| `01-Complete-Project-Summary.md` | Platform lines; the workspace access check (a React Router loader); accessibility NFR; ownership, identifier-generation and dashboard guidance; §12.5 staging; §14.1 architecture diagram, plus what choosing SQLite commits the rebuild to; increment 0 of the delivery plan |
| `02-Complete-Database-Schema.md` | Retargeted to SQLite throughout. Schemas become table-name prefixes (`plan.goal` → `plan_goal`); every column type is a `STRICT` SQLite type; new §1.2 *SQLite platform settings* (pragmas, single writer, backup, schema changes); enumerations as `CHECK` + `ref_enum_value`; hierarchy rules as triggers; FTS5 search; counter-based identifiers instead of sequences; audit archive instead of partitions; §13 row visibility enforced by the API, since SQLite has no row-level security; analytic views live, with optional snapshot tables. The form renderer and heat-map references name the React components |
| `03-Complete-APIs-and-UI-Screens.md` | New §11.6 *Client stack (React)* — TypeScript, Vite, React Router, TanStack Query, React Hook Form, CSS Modules, Vitest; the unsaved-changes guard becomes a navigation blocker; the character counter becomes a hook and component; dashboards are React Router routes. Database notes as in the Angular + SQLite edition, including the new `maintain_database` job (8 jobs, not 7) |
| `04-Legacy-Screen-Coverage.md` | Component names in React form (`shared/ViewSelector`, `shell/Header`, …); share-row wording; a note that the figures quoted were measured on the Angular + PostgreSQL reference build and are the bar this build must meet |

Read Document 3 §11.6 for the React stack, and Document 1 §14.1 with Document 2 §1.2 and §13 for
what SQLite changes — one writer at a time, one API host, row visibility enforced by the API,
scheduled backups.
