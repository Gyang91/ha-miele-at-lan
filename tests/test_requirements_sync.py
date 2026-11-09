"""The shipped requirement and the tested one must be the same version.

Dependabot (and the security audit) only read requirements_test.txt. Home
Assistant installs what manifest.json names. If the two drift, the version
that is audited and tested is not the one users run.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pins(lines: list[str]) -> dict[str, str]:
    pins = {}
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if "==" in line:
            name, version = line.split("==", 1)
            pins[name.strip().lower()] = version.strip()
    return pins


def test_manifest_requirements_match_tested_pins() -> None:
    manifest = json.loads(
        (ROOT / "custom_components" / "miele_lan" / "manifest.json").read_text()
    )
    shipped = _pins(manifest["requirements"])
    tested = _pins((ROOT / "requirements_test.txt").read_text().splitlines())
    assert shipped, "manifest.json pins no requirement"
    for name, version in shipped.items():
        assert tested.get(name) == version, (
            f"{name}: manifest.json ships {version}, "
            f"requirements_test.txt tests {tested.get(name)}"
        )
