CANONICAL_FIELDS = [
    "case_id","age","sex","date_onset","date_reported","classification",
    "outcome","region","district","hospitalized","latitude","longitude",
]

ALIASES = {
    "case_id": ["case_id","caseid","id","patient_id","patient_no","record_id"],
    "age": ["age","patient_age","age_years"],
    "sex": ["sex","gender"],
    "date_onset": ["date_onset","onset_date","symptom_date","symptom_onset_date"],
    "date_reported": ["date_reported","report_date","notification_date","date_notification"],
    "classification": ["classification","case_classification","case_status","status"],
    "outcome": ["outcome","patient_outcome"],
    "region": ["region","reporting_region"],
    "district": ["district","reporting_district"],
    "hospitalized": ["hospitalized","hospitalised","admitted"],
    "latitude": ["latitude","lat"],
    "longitude": ["longitude","lon","lng"],
}
