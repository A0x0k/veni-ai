from pathlib import Path

import veni.logger as logger_module


def test_build_file_handler_returns_none_on_permission_error(monkeypatch):
    def boom(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(logger_module, "RotatingFileHandler", boom)
    assert (
        logger_module._build_file_handler(Path.cwd() / ".pytest_temp" / "veni.log")
        is None
    )
