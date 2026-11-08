"""Protect the draft/ready interpreter matrix policy on focused workflows."""

from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("workflow", "field"),
    [
        ("linux-case-policy.yml", "python"),
        ("package-import-logging.yml", "python-version"),
        ("pandas-result-readers.yml", "python"),
        ("public-api-contracts.yml", "python-version"),
        ("raster-cache-reader-recovery.yml", "python"),
        ("tmf-pandas-compatibility.yml", "python"),
    ],
)
def test_focused_workflows_preserve_premerge_python312(workflow: str, field: str) -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / ".github/workflows" / workflow).read_text(encoding="utf-8")
    assert "types: [opened, synchronize, reopened, ready_for_review, converted_to_draft]" in source
    assert f'{field}: ' + '$' + '{{ fromJSON(' in source
    assert "github.event_name == 'pull_request' && github.event.pull_request.draft == true" in source
    assert '["3.11", "3.14"]' in source
    assert '["3.11", "3.12", "3.14"]' in source
