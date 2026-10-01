-- One row per trial. Each child is aggregated BEFORE joining.
-- Only snapshot-selected baseline rows are registered by the ingestion module.
-- Outcome tables are deliberately absent from this query's interface.
WITH sponsor AS (
 SELECT nct_id,
   MAX(CASE WHEN lower(lead_or_collaborator)='lead' THEN agency_class END) AS sponsor_class,
   MAX(CASE WHEN lower(lead_or_collaborator)='lead' THEN name END) AS sponsor_group,
   COUNT(*) FILTER (WHERE lower(lead_or_collaborator)='lead') AS lead_count,
   COUNT(*) FILTER (WHERE lower(lead_or_collaborator)='collaborator') AS collaborator_count
 FROM sponsors GROUP BY nct_id
), condition_summary AS (
 SELECT nct_id, COUNT(DISTINCT lower(name)) AS condition_count,
   string_agg(DISTINCT lower(name), '; ' ORDER BY lower(name)) AS condition_terms
 FROM conditions GROUP BY nct_id
), intervention_summary AS (
 SELECT nct_id, COUNT(*) AS intervention_count,
   COUNT(DISTINCT lower(intervention_type)) AS intervention_type_count,
   MAX(CASE WHEN lower(intervention_type)='drug' THEN 1 ELSE 0 END) AS has_drug,
   MAX(CASE WHEN lower(intervention_type)='device' THEN 1 ELSE 0 END) AS has_device,
   MAX(CASE WHEN lower(intervention_type)='behavioral' THEN 1 ELSE 0 END) AS has_behavioral
 FROM interventions GROUP BY nct_id
), site_summary AS (
 SELECT nct_id, COUNT(*) AS facility_count,
   COUNT(DISTINCT NULLIF(country,'')) AS country_count,
   MAX(CASE WHEN country='United States' THEN 1 ELSE 0 END) AS has_us_site
 FROM facilities GROUP BY nct_id
)
SELECT s.nct_id, NULLIF(s.phase,'') AS phase,
 CASE WHEN lower(s.enrollment_type) IN ('anticipated','estimated')
      THEN CAST(NULLIF(s.enrollment,'') AS DOUBLE) END AS planned_enrollment,
 CASE WHEN lower(s.enrollment_type) IN ('anticipated','estimated') THEN 0 ELSE 1 END AS planned_enrollment_missing,
 CAST(NULLIF(s.number_of_arms,'') AS DOUBLE) AS number_of_arms,
 NULLIF(s.has_dmc,'') AS has_dmc,
 d.allocation, d.intervention_model, d.primary_purpose, d.masking,
 e.gender, e.minimum_age, e.maximum_age, e.healthy_volunteers,
 NULLIF(e.criteria,'') AS eligibility_text,
 p.sponsor_class, p.sponsor_group, p.lead_count, p.collaborator_count,
 c.condition_count, c.condition_terms,
 i.intervention_count, i.intervention_type_count, i.has_drug, i.has_device, i.has_behavioral,
 f.facility_count, f.country_count, f.has_us_site,
 CASE WHEN f.nct_id IS NULL THEN 1 ELSE 0 END AS facilities_unlisted
FROM studies s
LEFT JOIN designs d USING (nct_id)
LEFT JOIN eligibilities e USING (nct_id)
LEFT JOIN sponsor p USING (nct_id)
LEFT JOIN condition_summary c USING (nct_id)
LEFT JOIN intervention_summary i USING (nct_id)
LEFT JOIN site_summary f USING (nct_id)
ORDER BY s.nct_id;
