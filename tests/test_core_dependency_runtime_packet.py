from __future__ import annotations

import sys


def _write_package(root, marker: str) -> None:
    package = root / "src" / "field_analysis"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(f"MARKER = {marker!r}\n", encoding="utf-8")


def test_runtime_diagnostic_packet_reports_required_fields(tmp_path) -> None:
    from coil_win_app.core_dependency import build_runtime_diagnostic_packet, configure_core_path

    _write_package(tmp_path, "one")
    configure_core_path(tmp_path)

    packet = build_runtime_diagnostic_packet()

    assert packet["expected_core_repo"] == "ParkJaechang/Coil-Analyzing"
    assert packet["expected_core_sha"] == "b3c1103825c9c30f2db9ea14153959ffc2fe300e"
    assert packet["configured_core_path"] == str(tmp_path / "src")
    assert packet["configured_core_paths"]
    assert "module_status" in packet
    assert "finite_first_api" in packet
    assert "helper_api_status" in packet
    assert "field_analysis.finite_first_phase_sync" in packet["module_status"]
    assert "streamlit" in packet["forbidden_module_status"]
    assert packet["streamlit_imported"] is False


def test_configure_core_path_clears_stale_field_analysis_modules(tmp_path) -> None:
    from coil_win_app.core_dependency import configure_core_path

    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_package(first, "first")
    _write_package(second, "second")

    configure_core_path(first)
    sys.modules.pop("field_analysis", None)
    import field_analysis  # type: ignore[import-not-found]

    first_file = field_analysis.__file__
    assert "first" in str(first_file)

    configure_core_path(second)
    import field_analysis as reloaded_field_analysis  # type: ignore[import-not-found]

    assert "second" in str(reloaded_field_analysis.__file__)
    assert "first" not in str(reloaded_field_analysis.__file__)
