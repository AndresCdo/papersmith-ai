#!/usr/bin/env python3
# This skill's entry point into the shared implementation engine.
#
# The engine under `_core/` serves no domain of its own and refuses to start
# without one, so the only thing this file does is name which domain is asking
# before handing over. Every argument, subcommand and exit code is the engine's.
#
# `setdefault` rather than `=`: an explicit IMPLEMENTATION_DOMAIN_PROFILE in
# the environment is a deliberate override (a test fixture profile) and must
# win over the default -- the same `??=` semantics
# `proposal-deliberation/cli.mjs` uses, including for the empty string, which
# stays empty and is refused.
#
# One inherited value is never deliberate: another skill's own profile, left
# exported by a shell or by an earlier process that ran the other skill. Under
# it this skill would read the other skill's documents and holder, silently.
# It is refused here, before the engine loads, naming both profiles.
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_OWN = _HERE.parents[1] / "impl_profile.py"
_INHERITED = os.environ.get("IMPLEMENTATION_DOMAIN_PROFILE")
if _INHERITED:
    _NAMED = Path(_INHERITED).resolve()
    if (_NAMED != _OWN and _NAMED.name == _OWN.name
            and _NAMED.parent.parent == _OWN.parent.parent):
        sys.stderr.write(
            "IMPLEMENTATION_DOMAIN_PROFILE_SIBLING: the environment carries "
            f"IMPLEMENTATION_DOMAIN_PROFILE={_INHERITED}, which is another "
            f"skill's own profile; this launcher serves {_OWN}. Unset the "
            "variable (it is usually left exported by a shell or an earlier "
            "process) and run this command again.\n")
        raise SystemExit(2)
os.environ.setdefault("IMPLEMENTATION_DOMAIN_PROFILE", str(_OWN))
sys.path.insert(0, str(_HERE.parents[2] / "_core" / "implementation" / "engine"))
import implementation_engine as _engine  # noqa: E402  (path set above)

if __name__ == "__main__":
    raise SystemExit(_engine.main())
