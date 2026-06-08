# WinApp Core Contract

## Modeling Policy

- Target field shape: `fixed_rounded_triangle`.
- Target peak field: user input, not fixed to 50 mT.
- Field normalization: target peak based.
- HallBz convention: effective field = `-HallBz raw`.
- Voltage command limit / normalization: `±10V`.
- Finite production cycles: `1.0`, `1.5`.
- Continuous production: steady-state `1cycle` repeated output only.
- Continuous tail / zero-return tail: off.
- Final LUT export: `sample_index,time_s,voltage_v`.
- Fourier/harmonic resynthesis is not used for final LUT export.
- Heavy calculations must run only after button clicks.

## Adapter Return Shape

Each adapter function returns a result object with:

- `status`
- `metadata`
- `warnings`
- `command_profile`
- `export_frame`, if applicable
- `error_reason`, if failed

Placeholder functions must return `status="not_connected"` and must not fake modeling success.

