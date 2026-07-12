# CrisisRelay Complete Synthetic Dataset

Files:
- wildfire_scenario.json: 30 chronological wildfire field reports with ground truth.
- extraction_test_cases.json: 60 Gemini extraction benchmark cases.
- state_engine_test_cases.json: 10 deterministic Unconfirmed State Engine fixtures.
- scenario_metadata.json: scenario, resources, operations, and state machine.
- wildfire_scenario.csv: spreadsheet-friendly scenario stream.

Critical rules:
1. Never infer completion from intention, assignment, dispatch, expectation, or elapsed time.
2. ARRIVED, COMPLETED, and VERIFIED require explicit evidence.
3. Do not connect events solely because a relationship is temporally plausible.
4. Assumption language such as should, probably, likely, must have, and I think must not advance state.
5. An unlinked outcome such as evacuees arriving must not confirm that Bus 7 arrived.
6. Gemini interprets language; the deterministic engine detects overdue or missing lifecycle transitions.

The data is synthetic and intended for hackathon prototyping/evaluation. It is not authentic responder communication and is not validated for operational emergency use.
