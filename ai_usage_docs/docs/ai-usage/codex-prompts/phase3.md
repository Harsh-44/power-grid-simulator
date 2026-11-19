# Power Grid Simulator — Phase 3: Sensor Fault Injection

Extend the existing simulator to support its first abnormal operating scenario: faulty FS101 frequency measurements.

Preserve the existing architecture, configuration system, physics model, controller, metrics, playback functionality, and UI.

## Requirements

1. Implement a reusable, configurable fault-injection mechanism in Python. Keep it separate from physics, controller, API, and UI logic.
2. Initially support a temporary FS101 measurement bias with configurable:
    - Fault start time
    - Fault duration
    - Frequency offset in Hz
3. Maintain separate actual and reported frequency values. Inject faults only into the sensor output, never directly into the physical frequency.
4. Ensure the controller continues using the FS101 reported frequency. Do not allow it to access the actual frequency as a workaround for faulty measurements.
5. Preserve all four original frequency variation rates.
6. Add a simple scenario selector:
    - Normal operation
    - FS101 measurement fault
7. Retain the existing frontend controls. Display actual and reported frequency together on the frequency graph, with the injected fault interval clearly indicated.
8. Log fault activation, fault clearance, control decisions, breaker operations, and safety violations with timestamps.
9. Add a concise fault summary containing:
    - Fault duration
    - Maximum measurement error
    - Number of breaker operations
    - Load disconnection duration
    - Actual frequency safety violations
10. Allow comparison against an equivalent normal run using the same initial conditions and configuration. Show differences in breaker operations and load availability. Do not classify individual breaker trips as unnecessary without a defined, defensible comparison criterion.
11. Preserve deterministic simulation results. Define clearly whether fault start and end timestamps are inclusive or exclusive.
12. Extend Pytest coverage for fault activation, fault clearance, sensor readings, controller response, event timing, and baseline regression.
13. Update the README with every new design assumption, including fault timing conventions, bias interpretation, and limitations.

## Engineering Constraints

- Separate all simulation logic from rendering and frontend code.
- Avoid hard-coded simulation parameters.
- Use small reusable functions.
- Keep strict typing and configuration validation.
- Retain sanity checks and structured state-change logging.
- Comment sparingly, only where logic is non-obvious.
- Maintain clean project organization.
- Do not introduce databases, complex frameworks, or unnecessary dependencies.
- Keep the React + Tailwind UI simple.
- Do not rebuild working components.

## Scope

Do not implement generator failures, advanced sensor noise models, PID control, new physics, or sophisticated scenario management yet.

## Definition of Done

The user can run a normal simulation, inject a temporary FS101 measurement error, observe the controller's response, inspect the resulting events and metrics, and compare the abnormal run with its normal baseline.

All original normal-operation regression tests must continue passing.

Provide an implementation summary, test results, and any new design assumptions.