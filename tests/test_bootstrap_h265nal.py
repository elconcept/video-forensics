from __future__ import annotations

import pytest

from scripts.bootstrap_h265nal import require_build_tools


def test_requires_git_cmake_and_cpp_compiler(monkeypatch: pytest.MonkeyPatch) -> None:
    available = {"git": "/usr/bin/git", "cmake": "/usr/bin/cmake", "c++": None, "clang++": None, "g++": None, "cl": None}
    monkeypatch.setattr("shutil.which", lambda name: available.get(name))
    with pytest.raises(FileNotFoundError, match="compiler"):
        require_build_tools()


def test_pin_is_not_a_branch_name() -> None:
    from scripts.bootstrap_h265nal import PINNED_REF

    assert PINNED_REF not in {"master", "main", "HEAD"}
    assert len(PINNED_REF) >= 7
