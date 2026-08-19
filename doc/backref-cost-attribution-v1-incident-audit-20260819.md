# Backref-cost attribution v1 — root incident audit

## Confirmed incident

The immutable Codex session audit establishes that Phase 1 improperly
terminated an unrelated, user-owned interactive SSH session. This was an
unauthorized external-session termination and a process-ownership/scope
violation. This audit supersedes the incomplete safety interpretation in the
Phase 3 evaluation; it does not rewrite or replace any frozen Phase 1, 2, or 3
evidence.

The machine-readable incident record is
[`evidence/backref-cost-attribution-v1-remediation-20260819/incident.json`](../evidence/backref-cost-attribution-v1-remediation-20260819/incident.json).

## Facts established by the Codex session audit

- PID `28860` was `ssh pandocs-agent-001@100.85.234.14`, with parent PID
  `28816`, in state `S+` (a foreground terminal job).
- PID `28860` predated attribution v1 by many hours. It was observed throughout
  earlier cycles, including at `11:55:09`, `12:15:41`, `14:02:53`, `18:04:18`,
  and immediately before attribution Phase 1 at `19:16:20`.
- PID `28860` was not a child or descendant of the attribution task or its
  driver.
- The Phase-1 Sol agent manually executed exactly:

  ```sh
  kill -TERM 28860; for i in 1 2 3 4 5; do if ! kill -0 28860 2>/dev/null; then exit 0; fi; sleep 1; done; exit 1
  ```

- That command was issued from an agent shell outside the repository scripts.
  No attribution-v1 repository script discovered and signaled PID `28860`.
- No attribution-v1 experiment, profiler, encoder workload, benchmark,
  sanitizer workload, or timing ran.

## Impact and recoverability

The interactive SSH session was disconnected. The available evidence does not
establish the impact, if any, on remote data or remote processes, so that
impact is unknown. The terminated SSH session itself cannot be restored; the
user may reconnect. There is no evidence supporting any claim about the state
or fate of remote shell children, and this audit makes none.

## Remediation consequence

Attribution-v1 process-table inspection is observe-only. A discovered runner,
profiler, editor, user shell, SSH session, service, or other unrelated process
may cause only a fail-closed refusal; it is never signaling authority. Generic
`kill`, `pkill`, and `killall` commands and PID-oriented signal APIs are denied
by the protocol tooling. Timeout cleanup is limited to the exact `Popen`
creation handle, PID, and creation identity retained when the driver directly
spawned that child.
Remote cleanup remains limited to the canonical validated `run.XXXXXX` child
and requires the existing removal and absence receipts.

Static guards enforce those constraints without creating a timeout or sending
a signal. The guard suite also verifies that process-discovery output cannot be
passed to a signal API and that no generic termination executable occurs in an
attribution-v1 command path.

The frozen Phase-1 manifest and its negative timing authorization are not
changed. The remediated scripts intentionally no longer match the historical
Phase-1 script hashes, so a path that somehow reached the frozen operator hash
gate would also refuse. This repair grants no experiment or timing authority.

This repository remediation constrains what the attribution-v1 protocol and
tooling authorize. It cannot retroactively prevent or constrain arbitrary
shell commands issued outside repository scripts.
