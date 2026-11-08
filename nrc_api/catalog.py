from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Resource:
    slug: str
    table: str
    entity: str
    title_field: str
    workflow: bool = False
    restricted_creation: bool = False


def _r(slug: str, table: str, title: str, *, workflow: bool = False, restricted: bool = False) -> Resource:
    return Resource(slug, table, table.removeprefix("perf_").removeprefix("plan_").removeprefix("ref_").removeprefix("evidence_").removeprefix("wf_").removeprefix("core_"), title, workflow, restricted)


RESOURCES = {
    r.slug: r
    for r in [
        _r("goals", "plan_goal", "goal"), _r("objectives", "plan_objective", "objective"),
        _r("strategies", "plan_strategy", "strategy"), _r("performance-goals", "plan_performance_goal", "performance_goal"),
        _r("external-factors", "plan_external_factor", "external_factor"), _r("definitions", "plan_definition", "title"),
        _r("fiscal-years", "ref_fiscal_year", "fiscal_year"), _r("signposts", "plan_signpost", "title"),
        _r("key-areas", "plan_key_area", "title"), _r("offices", "ref_office", "office"),
        _r("divisions", "ref_division", "name"), _r("organizations", "ref_organization", "name"),
        _r("business-lines", "ref_business_line", "business_line"), _r("product-lines", "ref_product_line", "product_line"),
        _r("products", "ref_product", "product"), _r("major-programs", "ref_major_program", "name"),
        _r("contributing-programs", "ref_contributing_program", "name"), _r("office-goals", "ref_office_goal", "name"),
        _r("performance-indicators", "perf_performance_indicator", "indicator_code", workflow=True, restricted=True),
        _r("pi-results", "perf_pi_result", "indicator_code", workflow=True),
        _r("planned-measures", "perf_planned_measure", "title"),
        _r("enterprise-risks", "perf_enterprise_risk", "risk_code", workflow=True, restricted=True),
        _r("risk-updates", "perf_risk_update", "entry_code", workflow=True),
        _r("accomplishments", "perf_accomplishment", "accomplishment_code", workflow=True),
        _r("priorities", "perf_priority", "update_code", workflow=True),
        _r("positive-change-management", "perf_positive_change_management", "pcm_code", workflow=True),
        _r("action-measures", "perf_action_measure", "title"),
        _r("priority-questions", "evidence_priority_question", "priority_question", workflow=True),
        _r("evaluations", "evidence_evaluation", "title", workflow=True),
        _r("research-activities", "evidence_research_activity", "activity_title", workflow=True),
        _r("submissions", "wf_submission", "name"), _r("approvals", "wf_approval", "name"),
        _r("rejections", "wf_rejection", "name"), _r("approval-queues", "wf_approval_queue", "name"),
        _r("tasks", "core_task", "subject"), _r("users", "core_app_user", "full_name"),
        _r("teams", "core_team", "name"), _r("business-units", "core_business_unit", "name"),
        _r("positions", "core_position", "name"), _r("security-roles", "core_security_role", "name"),
        _r("settings", "core_app_setting", "key"), _r("view-definitions", "core_view_definition", "name"),
        _r("form-definitions", "core_form_definition", "name"),
    ]
}

WORKFLOW_TYPES = {
    "performance_indicator": "performance-indicators", "pi_result": "pi-results",
    "enterprise_risk": "enterprise-risks", "risk_update": "risk-updates",
    "priority": "priorities", "positive_change_management": "positive-change-management",
    "accomplishment": "accomplishments", "priority_question": "priority-questions",
    "evaluation": "evaluations", "research_activity": "research-activities",
}

RELATIONSHIPS = {
    "contributing-business-lines": "business_line", "contributing-product-lines": "product_line",
    "contributing-offices": "office", "contributing-major-programs": "major_program",
    "other-contributing-programs": "contributing_program", "contributing-programs": "contributing_program",
    "related-performance-indicators": "performance_indicator", "performance-indicators": "performance_indicator",
    "applicable-fiscal-years": "fiscal_year", "goals": "goal", "objectives": "objective",
    "strategies": "strategy", "products": "product", "division-owners": "division_owner",
    "leading-offices": "office", "revision-history": "revision_history",
}

