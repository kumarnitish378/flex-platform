"""`control-model.md` §5 says it twice: the system suggests, it never switches by itself (B35).

A prompt that quietly applied its own suggestion would be the platform taking back the
control the whole mode model exists to give a person. So this is enforced by looking, not
by trusting: the `mode_setting` table is touched by exactly the code a human reaches
through the admin endpoint, plus the places that only read it or wipe it.
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"

#: Modules allowed to name the `ModeSetting` model, and why.
ALLOWED = {
    "modules/modes/models.py": "defines it",
    "modules/modes/service.py": "the only writer: create / update / delete behind config.manage",
    "modules/modes/router.py": "the admin endpoints that call that service",
    "modules/zones/service.py": "counts settings scoped to a zone, to refuse deleting it",
    "modules/simctl/service.py": "wipes it between simulator runs (sim only)",
}


def test_only_the_admin_service_can_write_a_mode_setting() -> None:
    mentioning = {
        path.relative_to(APP).as_posix()
        for path in APP.rglob("*.py")
        if re.search(r"\bModeSetting\b", path.read_text(encoding="utf-8"))
    }

    assert mentioning, "found no mention of ModeSetting; this guard would pass vacuously"
    assert mentioning <= set(ALLOWED), (
        f"{sorted(mentioning - set(ALLOWED))} touch the mode_setting table. The system must "
        "never change a mode by itself (control-model.md section 5): if this needs to, it "
        "belongs behind a person and the admin service, and in ALLOWED above."
    )


def test_the_prompt_service_does_not_import_the_mode_writer() -> None:
    source = (APP / "modules" / "modes" / "prompts.py").read_text(encoding="utf-8")

    assert "ModeSetting" not in source
    # It may *read* settings through the service, and must not call any method that writes.
    assert not re.search(r"modes\.(create|update|delete)\(", source)
