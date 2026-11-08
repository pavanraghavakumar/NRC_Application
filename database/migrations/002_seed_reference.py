"""Deterministic enumeration, role, and application-setting seeds."""

from __future__ import annotations

import sqlite3


ENUMS = {
 "ref_report_level":[("cbj_appr","CBJ/APPR",875670000),("business_product_line","Business Line/Product Line",875670002),("office_performance_report","Office Performance Report",875670003),("division","Division",875670004)],
 "ref_quarter":[("q1","Q1",875670000),("q2","Q2",875670001),("q3","Q3",875670002),("q4","Q4",875670003),("annual","Annual",875670004)],
 "ref_level":[("high","High",3),("medium","Medium",2),("low","Low",1)],
 "ref_operator":[("lt","<",875670000),("eq","=",875670001),("gt",">",875670002),("lte","<=",875670003),("gte",">=",875670004),("na","N/A",875670005)],
 "ref_units":[("percent","%",875670000),("integer","Integer",875670001),("decimal","Decimal",875670002),("yes_no","Yes/No",875670003),("dollar","Dollar",875670004),("text","Text",875670005)],
 "ref_measure_type":[("quantitative","Quantitative",875670000),("qualitative","Qualitative",875670001),("range","Range",875670002)],
 "ref_indicator_type":[("output","Output",875670000),("outcome","Outcome",875670001),("process","Process",875670003),("input","Input",875670004),("efficiency","Efficiency",875670005),("contextual","Contextual",875670006),("outcome_legacy","Outcome (legacy calculated code)",875670002)],
 "ref_indicator_status":[("active","Active",875670000),("discontinued","Discontinued",875670001),("under_development","Under Development",875670002),("pending_discontinue","Pending Discontinue",875670003)],
 "ref_risk_status":[("under_development","Under Development",875670001),("active","Active",875670002),("pending_discontinue","Pending Discontinue",875670003),("discontinued","Discontinued",875670004)],
 "ref_change_type":[("new","New",875670000),("no_change","No Change",875670001),("revised","Revised",875670002)],
 "ref_data_source":[("external_website","External Website",875670004),("faimis","FAIMIS",875670001),("hrms","HRMS",875670002),("ldap","LDAP",875670003),("sharepoint","SharePoint",875670006),("other","Other",875670007),("na","N/A",875670008)],
 "ref_success_likelihood":[("likely","Likely",875670000),("met","Met",875670001),("unlikely","Unlikely",875670002),("unmet","Unmet",875670003)],
 "ref_data_type":[("qualitative","Qualitative",875670000),("quantitative","Quantitative",875670001)],
 "ref_risk_outlook":[("increasing","Increasing",875670000),("decreasing","Decreasing",875670001),("stable","Stable",875670002)],
 "ref_principle_of_good_regulation":[("reliability","Reliability",875670000),("openness","Openness",875670001),("independence","Independence",875670002),("efficiency","Efficiency",875670003),("clarity","Clarity",875670004),("none","None",875670005)],
 "ref_agency_wide_support_level":[("agency","Agency",716580000),("office","Office",716580001),("na","N/A",716580002)],
 "ref_record_type":[("performance_indicator","Performance Indicator",875670000),("pi_result","PI Result",875670001),("enterprise_risk","Enterprise Risk",875670002),("risk_update","Risk Update",875670003),("priority","Priority",875670004),("positive_change_management","Positive Change Management",875670005),("accomplishment","Accomplishment",875670006)],
 "ref_workflow_action_type":[("submit","Submit",875670000),("approve","Approve",875670001),("reject","Reject",875670002)],
 "ref_approval_role":[("author","Author",875670000),("assignee_interim_approver","Assignee/Interim Approver",875670001),("final_approval","Final Approval",875670003)],
 "ref_answer_type":[("assessment","Assessment",875670000),("analysis","Analysis",875670001),("research","Research",875670002),("evaluation","Evaluation",875670003)],
 "ref_evidence_building_status":[("completed","Completed",875670000),("in_progress","In Progress",875670001),("delayed","Delayed",875670002),("starts_in_fy","Starts in FY",875670003)],
 "ref_evidence_building_activity_type":[("research","Research",875670000),("rulemaking","Rulemaking",875670002),("other","Other",875670003)],
 "ref_related_ecq":[("leading_change","Leading Change",875670000),("leading_people","Leading People",875670001)],
 "ref_critical_element":[("leading_change","Leading Change",875670000),("leading_people","Leading People",875670001),("business_acumen","Business Acumen",875670002),("building_coalitions","Building Coalitions",875670003),("results_driven","Results Driven",875670004)],
 "ref_number_type":[("percent","% (Percent)",875670000),("dollars","$ (Dollars)",875670001),("number","# (Number)",875670002)],
 "core_record_state":[("active","Active",0),("inactive","Inactive",1)],
 "perf_qpr_record_status":[("draft","Draft",1),("pending_approval","Pending approval",875670002),("revision","Revision",875670005),("finalized","Finalized",2),("cancelled_closed","Cancelled/closed",875670004)],
 "perf_pi_result_status":[("draft","Draft",1),("pending_approval","Pending approval",875670001),("revision","Revision",875670007),("finalized","Finalized",2),("cancelled_closed","Cancelled/closed",875670006)],
 "perf_performance_indicator_status":[("draft","Draft",1),("pending_approval","Pending approval",875670001),("revision","Revision",875670003),("finalized","Finalized",2),("cancelled_closed","Cancelled/closed",875670004),("discontinued","Discontinued",875670005),("versioned_revised","Versioned/revised",875670006)],
 "perf_enterprise_risk_status":[("draft","Draft",1),("pending_approval","Pending approval",875670001),("revision","Revision",875670004),("finalized","Finalized",2),("closed_cancelled","Closed/cancelled",875670003),("discontinued","Discontinued",875670005)],
 "evidence_eb_record_status":[("draft","Draft",1),("pending_intermediate_approval","Pending Intermediate Approval",875670001),("pending_final_approval","Pending Final Approval",875670002),("revision","Revision",875670004),("finalized","Finalized",2),("cancelled","Cancelled",875670003)],
 "wf_submission_status":[("pending","Pending",1),("complete","Complete",2)],
 "wf_rejection_status":[("pending_changes","Pending changes",1),("resubmitted","Resubmitted",2)],
 "ref_simple_status":[("active","Active",1),("inactive","Inactive",2)],
}


def upgrade(connection: sqlite3.Connection) -> None:
    for enum_name, values in ENUMS.items():
        connection.executemany(
            "INSERT INTO ref_enum_value(enum_name,value,label,legacy_code,sort_order) VALUES(?,?,?,?,?)",
            [(enum_name, value, label, legacy, order) for order, (value, label, legacy) in enumerate(values, 1)],
        )
    settings = [
        ("approver.qpr.default_team_id", "", "uuid", "Default QPR approver team"),
        ("links.user_guide", "", "url", "User guide document"),
        ("links.faq", "", "url", "FAQ document"),
        ("links.strategic_planning", "/sp", "url", "Strategic Planning workspace"),
        ("links.performance_management", "/pm", "url", "Performance Management workspace"),
        ("environment.name", "development", "string", "Visible environment name"),
        ("audit.retention_months", "84", "int", "Live audit retention before yearly archive"),
        ("dashboards.strategic_plan", "", "string", "Reporting plan, blank for earliest"),
    ]
    connection.executemany("INSERT INTO core_app_setting(key,value,value_type,description) VALUES(?,?,?,?)", settings)
