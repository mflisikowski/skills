# Triage roles

The local tracker uses the five canonical triage roles unchanged. Record the role in an issue's `Status:` line.

| Role / status | Meaning |
| --- | --- |
| `needs-triage` | A maintainer needs to evaluate the incoming issue. |
| `needs-info` | The issue is waiting for information from the reporter. |
| `ready-for-agent` | The issue is sufficiently specified for an agent to implement. |
| `ready-for-human` | The issue requires human implementation. |
| `wontfix` | The issue will not be actioned. |

When a workflow asks to apply a triage label, use the exact string above. Triage applies to incoming reports and requests; implementation tickets produced from an agreed spec are already prepared for implementation.

`claimed` and `resolved` describe work progress and completion. They are not additional triage roles. See the [issue tracker conventions](issue-tracker.md) for their use.
