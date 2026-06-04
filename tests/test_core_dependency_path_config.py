from __future__ import annotations

import sys


def test_configure_core_path_rejects_missing_path(tmp_path) -> None:
    from coil_win_app.core_dependency import configure_core_path

    result = configure_core_path(tmp_path / "missing")

    assert result["status"] == "failed"
    assert "does not exist" in result["core_import_error"]


def test_configure_core_path_accepts_repo_root_and_reports_added_path(tmp_path) -> None:
    from coil_win_app.core_dependency import configure_core_path, get_core_dependency_status

    src = tmp_path / "src"
    package = src / "field_analysis"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")

    result = configure_core_path(tmp_path)
    status = get_core_dependency_status()

    assert result["status"] == "ok"
    assert result["added_sys_path"] == str(src)
    assert str(src) in sys.path
    assert status["configured_core_path"] == str(src)
    assert status["added_sys_path"] == str(src)


def test_configure_core_path_accepts_src_path(tmp_path) -> None:
    from coil_win_app.core_dependency import configure_core_path

    src = tmp_path / "src"
    (src / "field_analysis").mkdir(parents=True)
    (src / "field_analysis" / "__init__.py").write_text("", encoding="utf-8")

    result = configure_core_path(src)

    assert result["status"] == "ok"
    assert result["added_sys_path"] == str(src)


def test_core_dependency_resolver_still_does_not_import_streamlit(tmp_path) -> None:
    from coil_win_app.core_dependency import configure_core_path, get_core_dependency_status

    src = tmp_path / "src"
    (src / "field_analysis").mkdir(parents=True)
    (src / "field_analysis" / "__init__.py").write_text("", encoding="utf-8")
    configure_core_path(src)
    sys.modules.pop("streamlit", None)

    status = get_core_dependency_status()

    assert status["streamlit_imported"] is False
    assert "streamlit" not in sys.modules
