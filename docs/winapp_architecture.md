# WinApp Architecture

The Windows App is a separate PySide6 desktop shell around the Coil-Analyzing modeling core.

## Boundaries

- UI code calls only `src/coil_win_app/core_adapter.py`.
- Streamlit modules are not imported.
- User data, upload caches, and generated exports are not committed.
- The final LUT export is a time-voltage table only: `sample_index,time_s,voltage_v`.

## Layers

- `ui/`: PySide6 widgets and navigation.
- `project_state.py`: selected project/data folder state.
- `core_adapter.py`: stable boundary to the pinned Streamlit core dependency.
- `docs/upstream_core_requests.md`: requests for Streamlit/core changes.

## Milestones

- Milestone 1: desktop skeleton, TargetConfig, placeholder adapter, dummy LUT preview.
- Milestone 2: connect finite first modeling through pinned core dependency.
- Milestone 3: connect actual-drive finite second correction.
- Milestone 4: connect continuous steady-state one-cycle modeling.
- Milestone 5: PyInstaller packaging, config paths, runtime logs.

