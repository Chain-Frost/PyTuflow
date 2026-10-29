"""POSIX permission contracts for staged control-file saves.

Run only with an actual POSIX filesystem: the tests check observable creation
modes and ownership, not simulated permissions on Windows.
"""

import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from pytuflow._tmf.cf import cf_build_state as saves
from pytuflow._tmf.cf.tcf import TCF
from tests.tmf.test_safe_model_saves import _edit_all, _model, _state


pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX permissions only")


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


@pytest.mark.parametrize("mask", [0o022, 0o027, 0o077])
def test_new_files_use_normal_creation_mode_not_mkstemp_mode(
    tmp_path: Path, mask: int,
) -> None:
    """A staged save must respect umask like a direct Python file creation."""
    previous = os.umask(mask)
    try:
        ordinary = tmp_path / "ordinary.txt"
        ordinary.write_bytes(b"")
        target = tmp_path / "new.tcf"
        model = TCF(target)
        model.append_input("Hardware == CPU")
        model.write()
    finally:
        os.umask(previous)

    assert _mode(target) == _mode(ordinary) == (0o666 & ~mask)
    assert target.read_bytes() == b"Hardware == CPU\n"
    assert not list(tmp_path.glob(".pytuflow-permissions-*"))


def test_existing_destination_keeps_owner_group_and_mode(tmp_path: Path) -> None:
    """Do not change shared-file access rights during an ordinary replacement."""
    target = tmp_path / "model_001.tcf"
    target.write_bytes(b"Hardware == GPU\n")
    target.chmod(0o640)
    original = target.stat()
    model = TCF(target)
    model.find_input("Hardware")[0].rhs = "CPU"

    model.write(None)

    saved = target.stat()
    assert target.read_bytes() == b"Hardware == CPU\n"
    assert (saved.st_uid, saved.st_gid) == (original.st_uid, original.st_gid)
    assert _mode(target) == 0o640


def test_foreign_owned_file_is_rejected_before_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not turn a group-accessible file into an inaccessible one."""
    target = tmp_path / "model_001.tcf"
    target.write_bytes(b"Hardware == GPU\n")
    target.chmod(0o660)
    model = TCF(target)
    model.find_input("Hardware")[0].rhs = "CPU"
    before_state = _state(model)
    original = target.read_bytes()
    original_mode = _mode(target)

    # Reproduce the owner mismatch without requiring privileged chown.
    monkeypatch.setattr(saves.os, "geteuid", lambda: target.stat().st_uid + 1)
    with pytest.raises(PermissionError, match="POSIX ownership"):
        model.write(None)

    assert target.read_bytes() == original
    assert _mode(target) == original_mode
    assert _state(model) == before_state
    assert sorted(p.name for p in tmp_path.iterdir()) == ["model_001.tcf"]


def test_unavailable_group_change_fails_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A different group must be preserved or rejected, never silently lost."""
    source = tmp_path / "source.tcf"
    staged = tmp_path / ".stage"
    source.write_bytes(b"Hardware == GPU\n")
    staged.write_bytes(b"Hardware == CPU\n")
    source_group = staged.stat().st_gid + 1

    class GroupOwnedSource:
        def stat(self):
            info = source.stat()
            return SimpleNamespace(st_uid=info.st_uid, st_gid=source_group, st_mode=info.st_mode)

        def __str__(self) -> str:
            return str(source)

    def refuse_chgrp(path, uid, gid):
        assert path == staged
        assert uid == -1
        assert gid == source_group
        raise PermissionError("unsupported group")

    monkeypatch.setattr(saves.os, "chown", refuse_chgrp)
    with pytest.raises(PermissionError, match="POSIX group ownership"):
        saves._preserve_file_metadata(GroupOwnedSource(), staged, backup=False)

    assert staged.read_bytes() == b"Hardware == CPU\n"
    assert source.read_bytes() == b"Hardware == GPU\n"


def test_mid_commit_rollback_restores_original_permissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _model(tmp_path)
    for path in tmp_path.iterdir():
        if path.is_file():
            path.chmod(0o640)
    _edit_all(model)
    before_files = {
        path.name: (path.read_bytes(), path.stat().st_uid,
                    path.stat().st_gid, _mode(path))
        for path in tmp_path.iterdir() if path.is_file()
    }
    before_state = _state(model)
    actual_replace = saves.os.replace
    count = 0

    def fail_second(source, destination):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("injected second replacement failure")
        return actual_replace(source, destination)

    monkeypatch.setattr(saves.os, "replace", fail_second)
    with pytest.raises(saves.ModelSaveError):
        model.write(None)

    assert count >= 3  # successful first replacement, failure, rollback
    assert _state(model) == before_state
    assert {
        path.name: (path.read_bytes(), path.stat().st_uid,
                    path.stat().st_gid, _mode(path))
        for path in tmp_path.iterdir() if path.is_file()
    } == before_files
