"""Explicit baseline feature allowlist shared by training and serving."""
import re
import numpy as np
import pandas as pd

NUMERIC=['planned_enrollment','planned_enrollment_missing','number_of_arms','collaborator_count',
 'condition_count','intervention_count','intervention_type_count','has_drug','has_device','has_behavioral',
 'facility_count','country_count','has_us_site','facilities_unlisted','min_age_years','max_age_years','age_width']
CATEGORICAL=['phase','has_dmc','allocation','intervention_model','primary_purpose','masking','gender',
             'healthy_volunteers','sponsor_class','therapeutic_area']
COUNTS=['text_words','text_lines','inclusion_mentions','exclusion_mentions','numeric_mentions',
        'threshold_mentions','negation_mentions','conjunction_mentions','lab_mentions','prior_therapy_mentions']
LOG_FIELDS=['planned_enrollment','number_of_arms','collaborator_count','condition_count','intervention_count',
            'intervention_type_count','facility_count','country_count']
FORBIDDEN={'overall_status','outcome_status','label','why_stopped','completion_date','actual_enrollment',
           'results_first_posted_date','outcome_snapshot','outcome_last_update'}

def age_years(value):
    m=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(Years?|Months?|Weeks?|Days?|Hours?)\s*',str(value),re.I)
    if not m:return np.nan
    factors={'year':1,'month':1/12,'week':7/365.25,'day':1/365.25,'hour':1/(24*365.25)}
    return float(m[1])*factors[m[2].lower().rstrip('s')]

def area(text):
    text=str(text).lower()
    for name,pattern in [('cancer',r'cancer|carcinoma|tumou?r|lymphoma|leukemia|neoplasm'),
                         ('infection',r'infect|hiv|covid|hepatitis|tuberculo'),
                         ('cardiovascular',r'cardiac|heart|hypertension|vascular'),
                         ('metabolic',r'diabet|obes|metabolic'),
                         ('neurologic',r'alzheimer|parkinson|epilep|stroke|dementia')]:
        if re.search(pattern,text):return name
    return 'other'

def text_counts(text):
    t=str(text or '');lo=t.lower()
    return [len(re.findall(r'\b\w+\b',t)),len(t.splitlines()),lo.count('inclusion'),lo.count('exclusion'),
            len(re.findall(r'\b\d+(?:\.\d+)?\b',t)),len(re.findall(r'[<>≤≥]|at least|at most|greater than|less than',lo)),
            len(re.findall(r'\b(?:no|not|without|except|unless)\b',lo)),len(re.findall(r'\b(?:and|or)\b',lo)),
            len(re.findall(r'\b(?:creatinine|hemoglobin|platelet|bilirubin|neutrophil|ast|alt)\b',lo)),
            len(re.findall(r'\b(?:prior|previous|washout|treatment-naive)\b',lo))]

def build_features(raw):
    """Unknown extra columns never become predictors; future fields fail closed."""
    bad=FORBIDDEN.intersection(raw.columns)
    if bad:raise ValueError(f'Post-outcome fields in baseline input: {sorted(bad)}')
    x=raw.copy()
    for c in NUMERIC:
        if c not in x:x[c]=np.nan
    x['min_age_years']=x.minimum_age.map(age_years)
    x['max_age_years']=x.maximum_age.map(age_years)
    x['age_width']=x.max_age_years-x.min_age_years
    x.loc[x.age_width<0,'age_width']=np.nan
    x['therapeutic_area']=x.condition_terms.map(area)
    for c in NUMERIC:
        x[c]=pd.to_numeric(x[c],errors='coerce').astype(float)
        x.loc[~np.isfinite(x[c]),c]=np.nan
    for c in LOG_FIELDS:x[c]=np.log1p(x[c].clip(lower=0))
    for c in CATEGORICAL:x[c]=x[c].fillna('missing').astype(str).str.strip().str.lower().replace('','missing')
    x['eligibility_text']=x.eligibility_text.fillna('').astype(str)
    counts=pd.DataFrame([text_counts(t) for t in x.eligibility_text],columns=COUNTS,index=x.index)
    for c in COUNTS:x[c]=np.log1p(counts[c])
    return x
