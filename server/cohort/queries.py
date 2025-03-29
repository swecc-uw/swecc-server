COHORT_DASHBOARD_QUERY = """
WITH active_cohorts AS (
    SELECT COUNT(*) as total_count
    FROM cohort_cohort
    WHERE is_active = TRUE
),
user_cohort_stats AS (
    SELECT
        cs."cohort_id",
        c."name",
        c."level",
        cs."applications",
        cs."onlineAssessments",
        cs."interviews",
        cs."offers",
        cs."dailyChecks",
        cs."streak"
    FROM engagement_cohortstats cs JOIN cohort_cohort c ON cs.cohort_id = c.id
    WHERE cs.member_id = %s AND c.is_active = TRUE
),
aggregate_stats AS (
    SELECT
        SUM(engagement_cohortstats."applications") as applications_sum,
        MAX(engagement_cohortstats."applications") as applications_max,
        AVG(engagement_cohortstats."applications") as applications_avg,

        SUM(engagement_cohortstats."onlineAssessments") as online_assessments_sum,
        MAX(engagement_cohortstats."onlineAssessments") as online_assessments_max,
        AVG(engagement_cohortstats."onlineAssessments") as online_assessments_avg,

        SUM(engagement_cohortstats."interviews") as interviews_sum,
        MAX(engagement_cohortstats."interviews") as interviews_max,
        AVG(engagement_cohortstats."interviews") as interviews_avg,

        SUM(engagement_cohortstats."offers") as offers_sum,
        MAX(engagement_cohortstats."offers") as offers_max,
        AVG(engagement_cohortstats."offers") as offers_avg,

        SUM(engagement_cohortstats."dailyChecks") as daily_checks_sum,
        MAX(engagement_cohortstats."dailyChecks") as daily_checks_max,
        AVG(engagement_cohortstats."dailyChecks") as daily_checks_avg,

        SUM(engagement_cohortstats."streak") as streak_sum,
        MAX(engagement_cohortstats."streak") as streak_max,
        AVG(engagement_cohortstats."streak") as streak_avg
    FROM engagement_cohortstats
    JOIN cohort_cohort ON engagement_cohortstats.cohort_id = cohort_cohort.id
    WHERE cohort_cohort.is_active = TRUE
)
SELECT
    'user_cohorts' as type,
    cohort_id,
    name,
    level,
    applications,
    "onlineAssessments",
    interviews,
    offers,
    "dailyChecks",
    streak,
    NULL as applications_sum,
    NULL as applications_max,
    NULL as applications_avg,
    NULL as online_assessments_sum,
    NULL as online_assessments_max,
    NULL as online_assessments_avg,
    NULL as interviews_sum,
    NULL as interviews_max,
    NULL as interviews_avg,
    NULL as offers_sum,
    NULL as offers_max,
    NULL as offers_avg,
    NULL as daily_checks_sum,
    NULL as daily_checks_max,
    NULL as daily_checks_avg,
    NULL as streak_sum,
    NULL as streak_max,
    NULL as streak_avg
FROM user_cohort_stats

UNION ALL

SELECT
    'aggregate_stats' as type,
    NULL as cohort_id,
    NULL as name,
    NULL as level,
    NULL as applications,
    NULL as "onlineAssessments",
    NULL as interviews,
    NULL as offers,
    NULL as "dailyChecks",
    NULL as streak,
    applications_sum,
    applications_max,
    applications_avg,
    online_assessments_sum,
    online_assessments_max,
    online_assessments_avg,
    interviews_sum,
    interviews_max,
    interviews_avg,
    offers_sum,
    offers_max,
    offers_avg,
    daily_checks_sum,
    daily_checks_max,
    daily_checks_avg,
    streak_sum,
    streak_max,
    streak_avg
FROM aggregate_stats;
"""