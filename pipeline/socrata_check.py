from .socrata import documents

fixture = [{
    "job_s1_no": "1", "job__": "123456789", "doc__": "01", "house__": "213", "street_name": "EAST 27 STREET",
    "applicant_s_first_name": "Ava", "applicant_s_last_name": "Lee", "owner_s_business_name": "Example LLC",
    "job_status_descrp": "PLAN EXAM - APPROVED", "latest_action_date": "08/05/2026", "bbl": "1009080050",
    "gis_longitude": "-73.9817", "gis_latitude": "40.7415", "job_description": "Interior work.",
}]
document = documents(fixture)[0]
assert document["meeting_date"] == "2026-08-05"
assert document["bbl"] == "1009080050" and document["longitude"] == -73.9817
assert "Applicant: Ava Lee" in document["text"] and "DOB Job 123456789" in document["text"]
print("Automated DOB connector check passed")
