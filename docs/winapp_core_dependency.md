# Windows App Core Dependency

The Windows App does not modify or vendor-copy the Streamlit WebApp code.

```text
STREAMLIT_CORE_REPO=ParkJaechang/Coil-Analyzing
STREAMLIT_CORE_SHA=27e89a4d23b78747c7ac7b18b093bd542c39fc1a
SOURCE_OF_TRUTH_DOC=docs/pr61_user_feedback_resolution_log.md
```

Current status:
- Core path can be configured with `COIL_ANALYZING_CORE_SRC` or the Project/Data page.
- Finite first bridge is guarded / feature-detected and calls PR61 core via
  `field_analysis.finite_first_phase_sync.apply_finite_first_phase_sync_modeling`
  when the configured core path exposes that API.
- Finite first diagnostics distinguish missing source, schema unavailable, core import unavailable,
  API unavailable, failed, and ok.
- Finite second modeling: `status="not_connected"`.
- Continuous extraction / first / second modeling: `status="not_connected"`.
- Final export accepts only an ok finite first `ModelingResult` or explicit demo export.
- Final export requires `time_s` and `limited_voltage_v`, rejects non-finite values, and writes only
  `sample_index,time_s,voltage_v`.
- PR61 body text may be stale; this document's `STREAMLIT_CORE_SHA` is the current WinApp dependency pin.
- Required upstream changes must be written to `docs/upstream_core_requests.md`.
