# Power Grid Simulator — Phase 4: Generator State Control and Complete Physics Verification

## Objective

Extend the existing Arctic Station Power Grid Simulator to support generator shutdown scenarios and allow all four frequency variation rates from the original project brief to be simulated, observed, and verified.

The existing application already includes:
- Python simulation engine
- Configurable physics and frequency variation rates
- Automatic circuit breaker control
- FS101 measurement fault injection
- Normal-operation and sensor-fault scenarios
- React + TypeScript + Tailwind CSS frontend
- Interactive playback
- Frequency, generator, and breaker graphs
- Operational metrics, safety diagnostics, and event logging

**Preserve all existing functionality. Do not rebuild the simulator or redesign the current UI.**

This phase should extend the simulator's capabilities while maintaining the existing architecture and engineering standards.

---

## 1. Original Physical Model

The original project brief specifies four operating combinations:

| G101 | CB101 | Frequency variation |
|---|---|---|
| ON | CLOSED | −0.05 Hz/s |
| ON | OPEN | +0.12 Hz/s |
| OFF | CLOSED | −0.15 Hz/s |
| OFF | OPEN | 0.00 Hz/s |

These values must remain configurable.

All four combinations must be supported by the physics engine.

Do not modify or reinterpret the specified variation rates.

Use the existing equation:

`next_frequency = current_frequency + variation_rate × time_step`

Continue to preserve deterministic discrete-time simulation.

Do not artificially clamp frequency to the safe range.

---

## 2. Add a Generator Shutdown Scenario

Introduce a new scenario:

**G101 Generator Failure**

Allow the user to configure:

- Generator shutdown time, in simulation seconds
- Initial generator state, where appropriate

For this initial implementation, a generator shutdown should represent a complete loss of G101 generation.

When the scheduled shutdown occurs:

1. G101 transitions from ON to OFF.
2. Record the transition as a structured event.
3. Apply the appropriate frequency variation rate according to the generator and breaker states.
4. Continue executing the existing controller and safety checks.
5. Keep G101 OFF for the remainder of the simulation.

Do not automatically restart the generator.

Do not introduce generator ramp-up, fuel consumption, cooling, inertia, or mechanical dynamics.

The shutdown is an instantaneous state transition in this simplified model.

Document this as an additional design assumption.

### Breaker Behaviour During Shutdown

Retain the existing automatic breaker control policy as far as applicable.

The controller must continue using FS101 reported frequency.

Do not allow the controller to read actual frequency directly.

If the breaker is CLOSED when G101 shuts down, the physics model must apply the specified −0.15 Hz/s variation rate until the breaker opens.

If both G101 and CB101 are OFF/OPEN, the frequency must remain unchanged according to the original brief.

Do not invent frequency recovery while G101 remains OFF.

Review the existing controller to ensure it does not incorrectly assume G101 is always ON.

Clearly define how the controller behaves when the generator is unavailable.

Any additional control rules required for the shutdown scenario must be documented as assumptions.

---

## 3. Introduce a Controlled Manual Testing Mode

A separate testing mode is required to demonstrate all four operating combinations.

Add:

**Manual State Testing**

This is a diagnostic mode intended for verifying the prescribed physics model, not a substitute for normal automatic control.

Allow the user to configure:

- Initial generator state: ON/OFF
- Initial breaker state: OPEN/CLOSED
- Simulation duration
- Initial frequency

Provide a simple option to hold the selected component states for a defined interval.

This should make it possible to reproduce each combination:

1. G101 ON, CB101 CLOSED
2. G101 ON, CB101 OPEN
3. G101 OFF, CB101 CLOSED
4. G101 OFF, CB101 OPEN

### Important Safety Separation

Manual testing mode may produce unsafe conditions because it deliberately exercises physical combinations without automatic corrective switching.

Therefore:

- Do not silently apply automatic breaker control in this mode.
- Do not disable or remove safety validation.
- Continue recording all frequency violations.
- Continue recording unsafe breaker/load combinations.
- Clearly label the mode as a diagnostic simulation.
- Distinguish unsafe simulated outcomes from application errors.

Never allow manual testing mode to change the behaviour of normal operation or the existing sensor-fault scenarios.

Avoid modifying the controller solely to accommodate manual testing.

Instead, separate the operating mode from the physical model.

### Example Verification

For a one-second interval starting at 50.00 Hz:

| Generator | Breaker | Expected next frequency |
|---|---|---|
| ON | CLOSED | 49.95 Hz |
| ON | OPEN | 50.12 Hz |
| OFF | CLOSED | 49.85 Hz |
| OFF | OPEN | 50.00 Hz |

These are essential regression test cases.

Use the existing physics functions rather than implementing separate calculations for manual mode.

---

## 4. Clearly Define Generator and Load States

The simulator must distinguish:

- Generator running state
- Circuit breaker connection state
- Station load connection state
- Whether the station is actually receiving generator power

Do not automatically interpret CB101 CLOSED as meaning L101 is powered.

For example:

**G101 ON, CB101 CLOSED**
- Station load connected
- Generator power available to the station

**G101 ON, CB101 OPEN**
- Station load disconnected
- Generator running without supplying L101

**G101 OFF, CB101 CLOSED**
- Station load connected
- Generator power unavailable
- Frequency decreases at −0.15 Hz/s according to the supplied stored-energy assumption

**G101 OFF, CB101 OPEN**
- Station load disconnected
- Generator power unavailable
- Frequency remains unchanged according to the simplified model

Do not invent a detailed stored-energy capacity or assume an external power source exists.

Document that the original brief's stored-energy description is insufficient to calculate actual delivered power, energy consumption, or backup supply duration.

Metrics should distinguish load connection availability from confirmed generator-powered duration.

---

## 5. Simulation Scheduling and Time-Step Ordering

Keep all scenario scheduling logic in Python.

Do not implement generator failure timing in React.

Use the existing simulation orchestration architecture.

Clearly define the order of operations within a time step, including:

1. Scheduled scenario events
2. Component state updates
3. Sensor reading
4. Controller decision, when automatic control is enabled
5. Physics update
6. State recording
7. Safety checks and event recording

If the existing engine uses a different correct ordering, preserve consistency where possible.

Avoid introducing off-by-one errors.

A generator shutdown scheduled at t = 30 seconds should have a precisely defined effect on the interval beginning at that timestamp.

Use the same timestamp conventions throughout simulation history, metrics, events, and graphs.

Do not create a second simulation engine for manual testing.

---

## 6. Extend Operational Metrics

Reuse the existing backend metrics architecture.

Ensure the following remain accurate under generator failure and manual testing:

**Generator**
- ON duration
- OFF duration
- Number of state transitions

**Station Load**
- Connected duration
- Disconnected duration
- Generator-powered duration
- Time connected without generator power

**Breaker**
- OPEN/CLOSED duration
- Switching operations

**Safety**
- Frequency violation samples
- Frequency violation episodes
- Time outside frequency limits
- Time CB101 remains CLOSED below the lower safety limit

Do not count a connected but unpowered load as generator-powered.

Use elapsed intervals rather than incorrectly counting samples as seconds.

All calculations must continue to originate from Python.

---

## 7. Event Logging

Record meaningful events:

- Generator shutdown
- Generator state transitions
- Circuit breaker operations
- Frequency entering/exiting unsafe operating ranges
- Unsafe connected conditions
- Sensor fault activation/clearance, for existing scenarios

Preserve the distinction between operational events and optional controller debug traces.

Do not generate duplicate events for the same component transition.

Provide informative timestamps and reasons.

A generator shutdown should be clearly visible in the event log.

---

## 8. Frontend Integration

Keep the current dashboard layout and styling.

Do not perform another major UI redesign.

Extend the existing scenario selector with:

- Normal operation
- FS101 measurement fault
- G101 generator failure
- Manual state testing

Display only the relevant configuration fields for the selected scenario.

### Generator Failure

Show:
- Shutdown time

Reuse the existing graphs, playback controls, state inspector, and summary metrics.

The G101 graph should visibly transition from ON to OFF at the configured time.

The current-state inspector must accurately distinguish between generator running, breaker connection, and generator power availability.

### Manual State Testing

Provide compact controls for selecting generator and breaker states.

Keep these controls in the existing configuration panel.

Clearly indicate that automatic breaker control is disabled in this diagnostic mode.

Avoid creating additional dashboard panels.

### Graph Requirements

Retain all three mandatory graphs:

1. FS101 bus frequency
2. G101 generator ON/OFF
3. CB101 breaker OPEN/CLOSED

Ensure they remain synchronized with playback.

Do not hide the generator or breaker graph merely because their states remain constant during a particular run.

Preserve the existing viewport-focused layout.

---

## 9. Testing Requirements

Extend the backend Pytest suite.

At minimum, verify:

1. Each of the four frequency rates independently.
2. Generator shutdown at the configured timestamp.
3. Correct application of −0.15 Hz/s when G101 is OFF and CB101 is CLOSED.
4. Correct application of 0 Hz/s when G101 is OFF and CB101 is OPEN.
5. Generator remaining OFF after shutdown.
6. Correct generator state history.
7. Correct breaker controller response during generator failure.
8. Manual mode preserving configured states.
9. Safety violations still being detected during manual testing.
10. Correct distinction between load connection and generator-powered duration.
11. Correct event timestamps and duration accounting.
12. Deterministic simulation results.
13. All existing normal-operation and FS101 fault tests continuing to pass.

Do not change existing expected results simply to make new tests pass.

Investigate regressions rather than hiding them.

---

## 10. README and Design Assumptions

Update the existing README.

Clearly document:

- Generator failure scenario
- Manual testing mode
- All four physical operating combinations
- Instantaneous generator shutdown assumption
- Generator remaining OFF without automatic restart
- Control behaviour when G101 becomes unavailable
- Difference between breaker connection and generator power supply
- Interpretation of frequency when G101 is OFF
- Limitations of the simplified stored-energy assumption
- Unsafe conditions permitted in manual diagnostic simulations
- Time-step ordering and scheduling conventions

Separate assumptions from requirements explicitly stated in the original project brief.

Do not claim the simulator models real generator failure dynamics or stored-energy behaviour beyond what is specified.

---

## 11. Engineering Standards

Preserve all previous engineering requirements:

- Strict separation of physics, control, sensors, scenarios, simulation engine, API, and UI
- Centralized and validated configuration
- Small, reusable functions
- Strong Python and TypeScript typing
- Clear responsibilities between modules
- Deterministic execution
- No unnecessary global mutable state
- Structured event logging
- Sanity checks
- Minimal comments
- Clean project organization
- No unnecessary dependencies
- No redundant physics implementations

Prefer extending existing classes and functions over creating parallel systems.

Avoid unnecessary abstraction.

---

## 12. Implementation Order

1. Inspect the current simulation architecture.
2. Verify the existing four-state physics implementation.
3. Extend scenario configuration and validation.
4. Implement scheduled G101 shutdown.
5. Ensure controller behaviour is well-defined when G101 is OFF.
6. Implement manual state testing using the existing physics engine.
7. Extend metrics and event handling.
8. Add backend tests.
9. Integrate the new scenarios into the existing React UI.
10. Verify graph and playback synchronization.
11. Update documentation and assumptions.
12. Run all existing regression tests and frontend build checks.

---

## 13. Definition of Done

The implementation is complete when:

- All four specified frequency variation rates can be demonstrated.
- Generator failure can be scheduled at a chosen simulation time.
- Generator failure is visible on the G101 graph.
- The existing controller responds consistently to generator failure.
- Manual diagnostic testing can hold each generator/breaker combination.
- Unsafe simulation outcomes are recorded rather than hidden.
- Load connection and generator power availability are correctly distinguished.
- Existing normal-operation and sensor-fault scenarios remain unchanged.
- All three required graphs and playback controls continue working.
- All tests pass.
- The README clearly documents all new assumptions and limitations.

## Final Instructions

This is a focused functionality extension, not a full rebuild.

The goal is to make the existing simulator capable of demonstrating every physical operating combination specified in the original project brief.

**Do not sacrifice existing simulation correctness, modularity, or UI simplicity to achieve this.**

After implementation, provide:
- Summary of changes
- Files modified
- Test results
- New design assumptions
- Known limitations
