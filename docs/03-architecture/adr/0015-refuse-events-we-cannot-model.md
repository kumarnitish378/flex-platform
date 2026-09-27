# ADR-0015: A scenario feature the simulator cannot model faithfully is refused, not approximated

- Status: accepted
- Date: 2026-09-27

## Context
`simulator-spec.md` §7 lists eight event types. When M07 built the injector, two of them
could not be modelled honestly:

- **`vip_burst`** — the seeded world did not say which employees were VIP, so a burst
  would have used ordinary riders.
- **`optimizer_down`** — there is no optimizer in Phase 1 to take down.

The tempting move with `vip_burst` was to burst whoever was to hand. It would have run,
produced metrics, and passed S07's assertions. It would also have been worthless: S07
exists to check that a VIP is never pooled and never put in an ordinary cab, and a run
made of ordinary riders tests neither while *looking* exactly like one that does.

The same question recurs across the simulator — supervisor policies (`approve_all`,
`mixed`), assertion types, scenario fields.

## Decision
When the simulator cannot model something faithfully, it **raises with the reason**. It
never silently substitutes a near-neighbour.

This is enforced at three points already:

| Feature | Behaviour |
|---|---|
| Phase 2 supervisor policies (`approve_all`, `mixed`) | `UnsupportedPolicyError`, rather than behaving like `manual_nearest` |
| Events not implementable this phase | `UnsupportedEventError` carrying *why*, listed in `NOT_YET` |
| An assertion whose metric was never measured | **Fails**, rather than passing vacuously |
| An offline run | Reports `assert not checked`, never a pass |

Validation happens when events are **armed**, not when they fire, so a scenario naming
something unsupported fails at the start of the run rather than ninety simulated minutes
in with the results half-collected.

The refusal message must say what is missing, not just that something is. `vip_burst`'s
read: *"the seeded world does not say which employees are VIP, so a burst would use
ordinary riders and S07 would report a VIP result it never tested"* — which is what made
it obvious later what to build.

## Consequences
- A green suite means what it says. The expensive failure mode for a simulator is not a
  missing feature; it is a feature that runs and measures the wrong thing, because that
  produces confident wrong answers.
- Coverage gaps are visible in the task notes and in `NOT_YET`, rather than hidden inside
  a scenario that appears to pass.
- `vip_burst` was subsequently implemented properly — the reset now seeds and reports VIP
  employees and honours the scenario's fleet composition — and S07 reports 5 VIP requests
  and 0 pooled. The refusal is what named the missing pieces.

## Alternatives considered
- **Approximate and document the approximation in a comment.** Rejected: nobody reads the
  comment when the run is green, and the metrics carry no trace of it.
- **Skip unsupported events silently.** Rejected: a scenario that quietly does less than
  it says is the same problem with less evidence.
