# Glossary

Use these terms exactly in code, API and UI. Code identifiers in `snake_case` (Python) / `camelCase` (Dart).

| Term | Code name | Meaning |
|---|---|---|
| Operator | `operator` | A cab company using the platform. Top-level tenant. Every record belongs to one operator. |
| Client | `client` | A corporate company served by an operator. |
| Office | `office` | A client location (pickup destination for morning trips, origin for evening drops). |
| Employee | `employee` | A rider belonging to a client. |
| Driver | `driver` | A person who drives an operator's vehicle. |
| Vehicle / Cab | `vehicle` | A car. Types: `sedan_4` (4 passengers, "5-seater"), `suv_6` (6 passengers, "7-seater"), `vip`. |
| Seat capacity | `seat_capacity` | Passenger seats excluding the driver. |
| Supervisor | `supervisor` | Dispatcher who monitors and controls assignment. |
| Request | `ride_request` | One employee's need for one ride (one direction). |
| Direction | `direction` | `to_office` (pickup, morning) or `from_office` (drop, evening). |
| Trip | `trip` | One vehicle journey serving one or more requests, with ordered stops. |
| Stop | `trip_stop` | A pickup or drop point on a trip, with planned and actual times. |
| Pooling | `pooling` | Several requests served by one trip. |
| Zone | `zone` | A named polygon used for grouping and mode scope. |
| Priority | `priority` | Employee rank 1 (highest) to 10 (lowest). Set by client admin. |
| Urgency | `urgency` | Per request: `high`, `medium`, `low`. |
| VIP | `is_vip` | Employee flag: gets a VIP vehicle immediately, no waiting, no sharing. |
| Rider weight | `rider_weight` | Priority × urgency factor that scales a rider's minutes in the cost function. |
| Detour | `detour_minutes` | Extra minutes added to an existing rider's trip by adding another rider. |
| Dead km | `empty_km` | Kilometres driven with no passenger on board. |
| ETA | `eta` | Estimated time of arrival at a stop. |
| Mode | `dispatch_mode` | `manual`, `semi_auto`, `full_auto`. Who decides assignment. |
| Scope | `mode_scope` | Where a mode applies: operator default, client, zone, time window, or combination. |
| Suggestion | `assignment_suggestion` | System's ranked candidate vehicles for a request, with reasons. |
| Override | `override` | Supervisor action that changes or constrains a system decision on a specific trip/request. |
| Lock | `lock` | Override that pins a request to a vehicle; optimizer must not change it. |
| Failsafe | `failsafe` | Automatic action when the supervisor does not respond to a suggestion in time. |
| Emergency pause | `automation_paused` | Operator-wide switch that stops all automatic assignment. |
| Hold window | `hold_window` | Time a request waits for pooling partners before assignment. |
| Micro-batch | `batch_window` | Short window (30–60 s) in which requests are optimized together. |
| Ride offer | `ride_offer` | Phase 4: proactive proposal sent to an employee, accepted or rejected. |
| On duty | `on_duty` | Driver state in which GPS is shared and trips can be assigned. |
| Location ping | `location_ping` | One GPS sample from a vehicle. |
| Speed profile | `road_speed_profile` | Learned speed per road segment and time slot. |
| Scenario | `sim_scenario` | Simulator input: fleet, employees, demand, events, seed. |
| Sim run | `sim_run` | One execution of a scenario with results. |
