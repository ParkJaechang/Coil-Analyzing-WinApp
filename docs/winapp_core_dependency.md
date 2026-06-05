# Windows App Core Dependency

The Windows App does not modify or vendor-copy the Streamlit WebApp code.

```text
STREAMLIT_CORE_REPO=ParkJaechang/Coil-Analyzing
STREAMLIT_CORE_SHA=b3c1103825c9c30f2db9ea14153959ffc2fe300e
SOURCE_OF_TRUTH_DOC=docs/pr61_user_feedback_resolution_log.md
```

Current status:
- Core path can be configured with `COIL_ANALYZING_CORE_SRC` or the Project/Data page.
- Finite first bridge: guarded / feature-detected.
- Finite first bridge calls `field_analysis.finite_first_phase_sync.apply_finite_first_phase_sync_modeling`
  when the configured core path exposes that API.
- Finite second modeling: `status="not_connected"`.
- Continuous extraction / first / second modeling: `status="not_connected"`.
- Final export supports demo output and any ok finite first `ModelingResult` with `time_s` and `limited_voltage_v`.
- PR61 body text may be stale; this document's `STREAMLIT_CORE_SHA` is the current WinApp dependency pin.
- Required upstream changes must be written to `docs/upstream_core_requests.md`.
