# Codex Task: Power Grid Simulator — Phase 2

## Objective

Extend the existing Power Grid Simulator with improved operational metrics, configurable simulation parameters, and a simple interactive playback interface.

**Do not rebuild the project. Preserve the existing working simulation engine and architecture.**

Phase 1 already provides:
- A Python simulation engine
- Physics and breaker control logic
- FastAPI endpoints
- A React + TypeScript + Tailwind frontend
- Frequency, generator, and breaker graphs
- Basic event logging and safety validation

The Phase 1 normal scenario runs successfully for 120 seconds, with the frequency remaining within 49.50–50.50 Hz.

The purpose of Phase 2 is to make the existing simulation easier to configure, inspect, understand, and debug.

Do not introduce advanced physics or complex scenarios yet.

---

## 1. Preserve All Existing Engineering Principles

Continue to follow these requirements:

1. Maintain strict separation between simulation logic, controller logic, physical models, sensor logic, API handling, and frontend rendering.
2. Keep all numerical simulation calculations in Python, not React.
3. Keep physical and control parameters configurable rather than hard-coded.
4. Use small, reusable functions with clearly defined responsibilities.
5. Maintain proper type hints, validation, and error handling.
6. Avoid global mutable simulation state.
7. Maintain deterministic and reproducible simulation behaviour.
8. Keep logging of state changes, control decisions, and abnormal conditions.
9. Implement sanity checks and verify system invariants.
10. Comment sparingly, primarily when explaining non-obvious implementation decisions.
11. Maintain a clean, consistent, scalable project structure.
12. Avoid introducing unnecessary dependencies, design patterns, or abstractions.

Use the existing technology stack:
- Python, FastAPI, Pydantic, Pytest
- React, Vite, TypeScript
- Tailwind CSS
- Recharts

Review the existing codebase before making changes. Reuse existing interfaces, models, functions, and components wherever appropriate.

## 2. Important Physical Model Constraint

The existing simulation correctly uses these frequency variation rates:

| G101 | CB101 | Rate |
|---|---|---|
| ON | CLOSED | -0.05 Hz/s |
| ON | OPEN | +0.12 Hz/s |
| OFF | CLOSED | -0.15 Hz/s |
| OFF | OPEN | 0.00 Hz/s |

Retain the existing configurable values.

There is an inherent limitation in this model: maintaining safe frequency requires periodic disconnection of L101 because no generator governor, energy storage model, or adjustable generation mechanism is specified.

Do not attempt to solve this limitation by:
- Adding unrequested generator regulation
- Introducing energy storage
- Changing the frequency rates
- Artificially clamping frequency
- Adding fictional power generation sources
- Changing the definition of safe frequency

The existing controller should continue to prioritize frequency safety while keeping CB101 CLOSED whenever feasible.

Document the limitation clearly in the README.

## 3. Add Operational Metrics

Extend the backend simulation results to include a meaningful operational summary.

Metrics must be calculated from the simulation history and events, not generated or independently inferred in the frontend.

Organize the metrics into the following categories.

### A. Frequency and Safety

Calculate:
- Minimum actual frequency
- Maximum actual frequency
- Average actual frequency
- Total time within frequency safety limits
- Safety violation count
- Minimum margin to either frequency safety limit

Keep the existing safety validation.

Safety checks must refer to the actual system state, rather than relying exclusively on the sensor reading.

Continue treating FS101 reported frequency as the measurement used by the controller.

Avoid implying that zero safety violations means the station operated without power interruptions.

### B. Station Load L101

Calculate:
- Total connected duration in seconds
- Total disconnected duration in seconds
- Load connection availability percentage
- Number of disconnection episodes
- Longest continuous disconnection
- Average disconnection duration

For the normal scenario, the generator remains ON, so the connected duration corresponds to the time the station receives generator power.

Keep the distinction between breaker connection and actual electrical supply explicit in the data model.

Do not infer physical energy availability from an undefined stored-energy model when the generator is OFF.

### C. Generator G101

Calculate:
- Total time ON
- Total time OFF
- Percentage of simulation time ON
- Number of generator state transitions
- Total time G101 is ON while CB101 is OPEN

The final metric represents time operating without a connected station load.

Do not calculate fuel consumption, operating cost, or generator efficiency because the required physical parameters are not provided.

### D. Circuit Breaker CB101

Calculate:
- Total time CLOSED
- Total time OPEN
- Number of OPEN operations
- Number of CLOSE operations
- Total switching operations
- Number of continuous OPEN intervals
- Longest OPEN interval

Use the existing event system where appropriate.

Avoid counting both an event and its resulting state transition as separate switching operations.

### Duration Accounting

Be precise about how duration is calculated.

A 120-second simulation with a one-second time step contains 121 state samples, including the initial sample.

However, there are only 120 elapsed one-second intervals.

All duration metrics must use elapsed intervals rather than incorrectly counting all 121 samples as seconds.

For example:

`connected_seconds + disconnected_seconds = 120`

Likewise:

`generator_on_seconds + generator_off_seconds = 120`

Handle initial states, boundary transitions, and intervals that continue until the simulation ends.

Document the convention used to associate a component state with an elapsed interval.

Keep metric calculations isolated from the simulation physics and controller, preferably in a focused metrics module.

## 4. Expected Reference Results

For the existing default 120-second normal scenario, the current implementation reports approximately:

- 121 samples
- Actual frequency range: 49.51–50.11 Hz
- Load connected: 87 seconds
- Load disconnected: 33 seconds
- Load connection availability: 72.5%
- Generator ON: 120 seconds
- Generator state changes: 0
- Breaker OPEN operations: 7
- Breaker CLOSE operations: 7
- Total breaker operations: 14
- Longest continuous load disconnection: 5 seconds
- Safety violations: 0

Use these values as regression references, not hard-coded outputs.

If existing conventions or code produce different results, investigate and explain the difference rather than forcing the expected values.

## 5. Configurable Simulation Parameters

Improve the existing configuration interface.

The frontend should let the user modify:

- Simulation duration
- Initial bus frequency
- CB101 opening frequency threshold
- CB101 closing/recovery frequency threshold

Use the existing configuration mechanism and API where possible.

The default values should remain:

- Duration: 120 seconds
- Initial frequency: 50.00 Hz
- Lower safety limit: 49.50 Hz
- Upper safety limit: 50.50 Hz
- Breaker opening threshold: 49.55 Hz
- Breaker closing threshold: 50.00 Hz

Do not duplicate default constants throughout the frontend.

Obtain the defaults from the backend or a clearly defined API configuration response.

Validate:
- Positive simulation duration
- Initial frequency within configured limits for a normal scenario
- Opening threshold within the safe operating range
- Closing threshold greater than opening threshold
- Closing threshold within the safe operating range
- Appropriate numerical types and finite values

Preserve configuration values when returning a simulation result.

If a chosen configuration causes violations, report them instead of silently correcting the resulting frequency values.

The user should be able to adjust the parameters and rerun the simulation.

Keep advanced parameters in backend configuration for now. Do not expose every physics parameter through the UI.

## 6. Interactive Simulation Playback

Add a lightweight playback system to inspect the simulation history.

**Important: simulation playback and the actual Python simulation engine are separate concepts.**

The backend must continue executing the simulation independently of the frontend and return the complete recorded history.

React should only control which recorded state is currently displayed.

### Playback Controls

Implement:

- Run Simulation
- Play
- Pause
- Step Forward by one recorded time step
- Step Backward by one recorded time step
- Reset playback to t = 0
- Timeline slider for selecting a recorded timestamp

Optionally support a small playback speed selector, such as 1x, 5x, and 10x, if it can be implemented cleanly.

Keep the UI minimal.

When the user selects a timestamp, update the displayed component states immediately.

### Important Playback Requirements

- Do not recompute simulation physics in JavaScript.
- Do not create a second simulation engine in the frontend.
- Do not mutate backend simulation results during playback.
- Treat the simulation history as immutable data.
- Use the actual timestamps returned by the backend.
- Pause playback at the end of the simulation.
- Ensure playback cleanup is handled correctly when the component unmounts or a new simulation begins.
- Do not create persistent backend sessions or WebSocket infrastructure solely for playback.

The existing `step()` simulation function should remain independently testable.

## 7. Current State Inspector

Add a small panel displaying the system state at the selected simulation timestamp.

Show:

**FS101**
- Reported bus frequency
- Actual bus frequency, if already exposed in the result
- Frequency condition: normal, under-frequency, or over-frequency

**G101**
- ON/OFF state

**CB101**
- OPEN/CLOSED state

**L101**
- Connected/disconnected state
- Generator-supplied status when this can be determined from the model

The panel must update whenever the selected playback timestamp changes.

Use existing backend state data.

Do not introduce additional physical simulation calculations inside React.

Keep this inspector simple: text, numerical values, and basic state indicators are sufficient.

## 8. Improve the Run Summary

Replace the minimal existing summary with a compact, organized overview.

Display the most meaningful metrics prominently:

- Frequency range
- Load connection availability
- Load disconnected duration
- Generator ON duration
- Breaker switching operations
- Longest disconnection
- Safety violations

Additional metrics may appear in a small expandable details section.

Avoid overwhelming the user with a large number of cards.

Keep the interface visually restrained and consistent with the existing application.

Use Tailwind CSS utility classes directly for styling.

Do not introduce a UI component library.

## 9. Improve Graph Interaction

Retain the existing three graphs:

1. FS101 bus frequency
2. G101 ON/OFF
3. CB101 OPEN/CLOSED

Do not redesign the charts unnecessarily.

Add a playback-position indicator where practical, so the user can identify the currently selected simulation time.

Ensure:
- All three graphs use the same timeline.
- Generator and breaker states remain discrete step-style graphs.
- The frequency graph retains the lower, nominal, and upper reference lines.
- Chart values originate from backend results.
- Selecting a playback timestamp updates the state inspector.

If displaying an exact vertical cursor across all graphs creates unnecessary complexity, prioritize a correct timeline slider and current state inspector instead.

Do not spend excessive time on cosmetic graph features.

## 10. Event Log Improvements

Preserve the existing structured event logging.

Improve the frontend presentation by displaying events in chronological order with:

- Simulation timestamp
- Component identifier
- Event type
- Previous state, when relevant
- New state, when relevant
- Reason for the transition

Allow the user to select an event and jump the playback timeline to that timestamp.

Use existing events rather than reconstructing events independently in React.

Do not log repetitive normal-state samples as separate operational events.

## 11. Testing and Validation

Extend the existing Pytest suite.

Add tests for:

- Correct duration accounting
- Load connection availability
- Generator ON/OFF duration
- Generator ON with breaker OPEN duration
- Breaker opening and closing counts
- Correct longest-disconnection calculation
- Initial OPEN and initial CLOSED conditions
- Events occurring at simulation boundaries
- Safety violation detection
- Validation of configurable control thresholds
- Deterministic simulation results
- Preservation of existing normal-operation behaviour

Verify that the default 120-second simulation continues to satisfy the initial functional requirements.

Pay particular attention to off-by-one errors introduced by the distinction between state samples and elapsed intervals.

Do not make backend tests depend on the frontend.

Add lightweight frontend tests only where useful and compatible with the existing testing setup. Avoid adding unnecessary infrastructure.

## 12. README and Design Assumptions

Update the existing README.

Add or revise sections covering:

### Architecture

Briefly explain:
- Simulation engine
- Physical models
- Sensor model
- Controller
- Metrics calculation
- API
- Frontend playback

### Design Assumptions

Clearly identify any assumptions not directly specified by the project brief.

Do not present implementation assumptions as original requirements.

### Known Limitations

Explicitly document:

**Continuous power limitation**

Under the supplied frequency variation rates, G101 cannot continuously supply L101 while maintaining safe frequency without periodically opening CB101.

No governor, energy storage model, or other frequency-regulation mechanism has been specified.

The simulator therefore models load disconnection as a necessary consequence of the simplified frequency dynamics rather than artificially hiding these interruptions.

**Simplified physical system**

The simulation is a discrete model with fixed frequency variation rates, not a complete electrical network or detailed generator dynamics model.

**Breaker switching**

Breaker switching delays, mechanical limits, and component wear are not specified and should not be invented.

**Sensor behaviour**

FS101 remains ideal during the normal scenario. Sensor faults will be considered in future iterations.

**Generator OFF behaviour**

Document how the model interprets bus frequency, load connectivity, and power availability when the generator is OFF, especially given the brief's simplified stored-energy assumption.

### How to Use the Simulator

Explain how to:
- Run a simulation
- Change configuration
- Inspect component states
- Use playback controls
- Interpret summary metrics and safety violations

## 13. Out of Scope

Do not implement the following during Phase 2:

- PID controllers or governor control
- Energy storage
- New generators
- Complex electrical network modelling
- Sensor fault injection
- Generator failure scenarios
- Automated scenario scheduling
- Databases or persistence
- User authentication
- WebSockets
- Advanced dashboards
- Complex UI animations
- Artificial changes to the specified frequency rates

These may be considered in subsequent iterations.

## 14. Implementation Order

Follow this order:

1. Review existing architecture and verify current behaviour.
2. Implement reusable backend metrics calculations.
3. Add and run backend tests for metrics.
4. Extend configuration handling and validation where necessary.
5. Update API response models while preserving the existing integration.
6. Implement frontend configuration controls.
7. Implement playback controls and timeline state.
8. Add the component state inspector.
9. Improve summary metrics and event navigation.
10. Update README and design assumptions.
11. Run regression tests and verify the complete application.

Before refactoring existing code, determine whether the change is genuinely necessary.

## 15. Definition of Done

Phase 2 is complete when:

- The original normal simulation still works.
- Core frequency and breaker safety behaviour is preserved.
- Operational metrics are calculated accurately.
- Users can configure and rerun the normal simulation.
- Playback can be paused, stepped, reset, and navigated.
- Component states are inspectable at any recorded timestamp.
- Event logs are synchronized with simulation timestamps.
- No simulation physics has been duplicated in React.
- Backend tests pass.
- The README explains all additional assumptions and limitations.

## Final Instructions

Keep the implementation small, maintainable, and technically defensible.

This is an iterative research simulator. Its architecture and correctness matter significantly more than UI complexity.

Avoid changing working code unless necessary to implement the requested improvements.

When finished, report:
- Files created or modified
- Features implemented
- Test results
- Any new design assumptions
- Any unresolved issues or known limitations

Do not add features beyond the scope of Phase 2.
