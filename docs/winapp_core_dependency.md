# Windows App Core Dependency

The Windows App does not modify or vendor-copy the Streamlit WebApp code.

```text
STREAMLIT_CORE_REPO=ParkJaechang/Coil-Analyzing
STREAMLIT_CORE_SHA=8f8a881b040429a4d6451f15831602d2e76added
SOURCE_OF_TRUTH_DOC=docs/pr61_user_feedback_resolution_log.md
```

Current status:
- Adapter state: placeholder, not connected.
- Modeling calls return `status="not_connected"` until Milestone 2.
- Required upstream changes must be written to `docs/upstream_core_requests.md`.
