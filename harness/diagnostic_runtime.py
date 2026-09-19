"""Isolated, output-free emulator runs and retained evidence for diagnostics."""
from __future__ import annotations

from datetime import datetime, timezone
import os
import re
from pathlib import Path
import subprocess
import tempfile
import time

from verification import sha256_file, write_json

ROOT = Path(__file__).resolve().parents[1]


def execution_failure(invocation, stderr):
    """Keep the emulator's cause ahead of secondary incomplete-capture errors."""
    if invocation.get('error'):
        return invocation['error']
    if invocation.get('returncode') != 0:
        fatal = re.search(r'^Fatal error:[ \t]*(.+)$', stderr, re.MULTILINE)
        detail = ': ' + fatal.group(1).strip()[:1000] if fatal else ''
        return f"emulator exit code {invocation.get('returncode')}{detail}"
    return None


def new_run(kind, output=None):
    if output:
        path = Path(output).resolve()
        path.mkdir(parents=True, exist_ok=False)
        return path
    parent = ROOT / "results" / "diagnostics"
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(tempfile.mkdtemp(prefix=f"{kind}-{stamp}-", dir=parent))


def diagnostic_env(overrides=None):
    # Diagnostic settings must be explicit, never inherited from a driving or
    # instrumentation session. In particular, no actuator or external UDP output.
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(("MIDV_", "MIDZ_", "SNAP_"))}
    env.update(overrides or {})
    env["MIDV_FFB"] = "0"
    for k in ("MIDV_FFB_TEST", "MIDV_TELEM_UDP", "MIDV_TELEM_FORZA", "MIDZ_TELEM_UDP"):
        env.pop(k, None)
    return env


def execute(command, directory, env, timeout):
    """Write invocation BEFORE launch and retain output even on timeout/error.

    Only call with physical outputs disabled: subprocess.run terminates on timeout.
    Returns status instead of treating a missing executable as a passing test.
    """
    # Missing is not an explicit disable. Windows environment names are case
    # insensitive, so also reject conflicting aliases supplied by a caller.
    if (env.get("MIDV_FFB") != "0" or any(
            (key.upper() == "MIDV_FFB" and value != "0") or
            (key.upper() == "MIDV_FFB_TEST" and bool(value))
            for key, value in env.items())):
        raise ValueError("timeout-capable diagnostics require physical force disabled: literal MIDV_FFB=0 and no force test")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    command = [str(c) for c in command]
    report = {"command": command, "cwd": str(directory), "timeout_seconds": timeout,
              "environment": {k: v for k, v in env.items()
                              if k.startswith(("MIDV_", "MIDZ_", "SNAP_"))},
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "returncode": None, "error": None}
    try:
        report["executable_sha256"] = sha256_file(command[0])
    except OSError as exc:
        report["error"] = str(exc)
    write_json(directory / "invocation.json", report)
    started = time.perf_counter()
    if report["error"] is None:
        with open(directory / "stdout.log", "wb") as out, open(directory / "stderr.log", "wb") as err:
            try:
                process = subprocess.run(command, cwd=directory, env=env, timeout=timeout,
                                         stdout=out, stderr=err)
                report["returncode"] = process.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                report["error"] = str(exc)
    report["elapsed_seconds"] = time.perf_counter() - started
    write_json(directory / "invocation.json", report)
    return report
