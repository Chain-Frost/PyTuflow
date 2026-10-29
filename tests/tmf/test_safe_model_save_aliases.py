"""Regressions for save destinations reached through directory aliases."""

import os
import subprocess
from pathlib import Path

import pytest

from pytuflow._tmf.cf.tcf import TCF


def _alias(tmp_path: Path) -> tuple[Path, Path]:
    real = tmp_path / "real"
    alias = tmp_path / "alias"
    real.mkdir()
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(real)],
            check=True, capture_output=True, text=True,
        )
    else:
        alias.symlink_to(real, target_is_directory=True)
    return real, alias


def test_save_preserves_lexical_child_directory_alias(tmp_path: Path) -> None:
    real, _ = _alias(tmp_path)
    source = real / "grid_003.tgc"
    original = b"Cell Size == 5\n"
    source.write_bytes(original)
    root = tmp_path / "model_010.tcf"
    root.write_bytes(b"Geometry Control File == alias/grid_003.tgc\n")
    model = TCF(root)
    reference = model.find_input("Geometry Control File")[0]
    child = reference.cf[0]

    child.find_input("Cell Size")[0].rhs = "10"
    model.write("auto")

    assert source.read_bytes() == original
    assert (real / "grid_011.tgc").read_bytes() == b"Cell Size == 10\n"
    assert reference.cf[0] is child
    assert model.fpath.read_bytes() == b"Geometry Control File == alias/grid_011.tgc\n"
    assert TCF(model.fpath).find_input("Cell Size")[0].rhs == "10"


@pytest.mark.parametrize("extension", ["csv", "tmf"])
def test_save_preserves_lexical_material_directory_alias(tmp_path: Path, extension: str) -> None:
    real, _ = _alias(tmp_path)
    header = "! Material ID,Manning's n" if extension == "tmf" else "Material ID,Manning's n"
    original = f"{header}\n1,0.03\n".encode("ascii")
    filename = f"materials_003.{extension}"
    (real / filename).write_bytes(original)
    root = tmp_path / "model_010.tcf"
    root.write_text(f"Read Materials File == alias/{filename}\n", encoding="utf-8")
    model = TCF(root)
    reference = model.find_input("Read Materials File")[0]
    database = reference.cf[0]

    database.df.loc[1, "Manning's n"] = 0.06
    model.write("auto")

    assert (real / filename).read_bytes() == original
    assert (real / f"materials_011.{extension}").exists()
    assert reference.cf[0] is database
    assert f"alias/materials_011.{extension}".encode() in model.fpath.read_bytes()
    assert TCF(model.fpath).mat_file().value(1) == pytest.approx(0.06)
