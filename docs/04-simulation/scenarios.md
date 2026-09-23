# Standard scenarios

Each scenario lives in `simulator/scenarios/<name>.yaml`. Assertions must pass for the phase listed before that phase goes live. Values are initial targets; calibrate after Phase 0 baseline.

| ID | Name | Phase | Setup | Key assertions |
|---|---|---|---|---|
| S01 | `smoke_tiny` | 0+ | 3 cabs, 10 employees, 1 hour | All requests end in terminal state; 0 invalid transitions; 0 API 5xx |
| S02 | `normal_weekday` | 1+ | 35 cabs, 300 employees, 2 shifts, manual_nearest supervisor | p90 wait ≤ 30 min; gave up ≤ 2%; ETA error p90 ≤ 8 min |
| S03 | `evening_surge` | 1+ | 150 drop requests within 20 min | No request expires; supervisor queue visible; alerts raised for > 20 min waits |
| S04 | `rain_day` | 1+ | S02 + rain 0.7 factor all day, +15% demand | System stable; metrics recorded; no crashes |
| S05 | `breakdown_with_riders` | 1+ | Breakdown mid-trip with 3 riders | Trip `aborted`; alert raised; riders re-queued or handled; 0 lost requests |
| S06 | `gps_loss` | 1+ | One cab loses GPS 10 min, one cab offline 15 min | Vehicle shown stale within 60 s; not auto-assigned while stale; batch upload accepted after reconnect in order |
| S07 | `vip_burst` | 1+ (manual) / 2+ | 5 VIP requests in 5 min, 2 VIP cars | VIP never pooled; VIP never on non-VIP car without override; alert when no VIP car |
| S08 | `supervisor_absent_semi_auto` | 2+ | Semi-auto scope, supervisor absent 30 min | Failsafe assigns within timeout + 30 s; every failsafe logged |
| S09 | `override_respected` | 2+ | Supervisor locks 10 requests, optimizer runs | Locked requests never moved by system (0 violations) |
| S10 | `pooling_efficiency` | 3+ | S02 in full_auto with pooling | Vehicles used ≤ 80% of S02 manual run; riders/trip ≥ 1.8 (evening); no detour violations |
| S11 | `night_safety` | 3+ | Night window, flagged riders, policy on | 0 night-rule violations without logged override |
| S12 | `optimizer_down` | 3+ | Optimizer disabled for 20 min | Scopes fall back to manual; alert raised; recovery after restart |
| S13 | `offers_week` | 4 | 5 simulated days, offer model on | Offer acceptance ≥ 40% (with sim behaviour model); no double bookings |
| S14 | `load_multi_operator` | 5 | 5 operators × 200 cabs | API p95 ≤ 300 ms; ingestor lag ≤ 5 s |

## Adding a scenario
1. Copy the closest YAML, change name and seed.
2. Add assertions (what must be true).
3. Add a row here.
4. Run it three times with different seeds before adding it to CI.
