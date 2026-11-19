# Codex Task: Power Grid Simulator — Phase 1

## 1. Project Overview

Build a working, extensible power grid simulator for a remote Arctic research station.

The simulator will eventually be used by a research team to train, test, and rehearse power system operating scenarios, including generator failures, abnormal frequency conditions, and faulty sensor readings.

**For this first phase, focus exclusively on implementing a reliable simulation engine, the necessary control logic, and a minimal frontend to verify the results.**

Do not attempt to build a sophisticated interface or advanced scenario-management system yet. I will iterate on those features in future prompts.

The priority is to establish a working simulation loop with a clean architecture that can accommodate future requirements without major refactoring.

## 2. Technology Stack

**Backend**
- Python 3.11+
- FastAPI for the API
- Pydantic for configuration and data validation
- Pytest for automated testing

**Frontend**
- React + Vite + TypeScript
- Tailwind CSS for styling
- Recharts for basic time-series graphs

Use Tailwind utility classes directly within React components to make UI styling easy to modify later.

Keep dependencies minimal. Do not introduce unnecessary frameworks, databases, state-management libraries, or infrastructure.

## 3. System Description

The simulator models a single-bus electrical distribution system supplying an Arctic research station.

The system contains four components:

| Component | Identifier | Description |
|---|---|---|
| Generator | G101 | Single diesel generator supplying the station |
| Circuit breaker | CB101 | Connects or disconnects the station load |
| Station load | L101 | Heating, life support, laboratories, and communications |
| Frequency sensor | FS101 | Measures and reports bus frequency |

### Operating Conditions

- Nominal frequency: 50.00 Hz
- Lower frequency limit: 49.50 Hz
- Upper frequency limit: 50.50 Hz
- Simulation time step: 1 second
- Default simulation duration: 120 seconds, configurable
- Initial operating condition: generator ON, breaker CLOSED, frequency 50.00 Hz

### Frequency Dynamics

Frequency changes according to the current generator and circuit breaker states.

| Generator | Breaker | Frequency change |
|---|---|---|
| ON | CLOSED | -0.05 Hz/second |
| ON | OPEN | +0.12 Hz/second |
| OFF | CLOSED | -0.15 Hz/second |
| OFF | OPEN | 0.00 Hz/second |

These rates must be configurable rather than hard-coded into simulation functions.

For each time step:

`next_frequency = current_frequency + frequency_rate × time_step`

Do not add unrequested physical behaviour, artificial frequency corrections, or external power system models.

### Operational Constraints

1. Under normal operation, bus frequency must remain within 49.50–50.50 Hz.
2. CB101 must never remain CLOSED when the bus frequency is below 49.50 Hz.
3. The station requires continuous power whenever possible, so CB101 should remain CLOSED whenever it is safe and feasible.
4. Control decisions should be deterministic and reproducible.
5. Do not silently clamp the frequency to maintain valid bounds.

## 4. Simulation Architecture

**This is the most important architectural requirement.**

All simulation logic must be completely independent of the frontend, visualization components, and API framework.

The Python simulation engine should be executable and testable without starting FastAPI or React.

Separate the following responsibilities:

### A. System Models

Represent the generator, breaker, station load, frequency sensor, and overall simulation state.

Use clearly defined typed models or dataclasses.

System state should capture at least:

- Simulation time
- Actual bus frequency
- FS101 reported frequency
- Generator state
- Circuit breaker state
- Whether the station load is connected and supplied with power

Keep actual frequency separate from reported sensor frequency, even though they are identical during normal operation. This distinction will support future sensor-fault scenarios.

### B. Physics Model

Implement the frequency dynamics separately from control logic.

The physics model must:

- Accept the current system state and configuration.
- Calculate frequency changes based on generator and breaker states.
- Return the updated physical state.
- Avoid making control decisions.
- Avoid mutating global state.

Keep physics calculations in small, reusable, testable functions.

### C. Control Logic

Implement a separate controller responsible for deciding the appropriate breaker state.

For the initial normal-operation scenario, assume G101 remains ON.

Use a simple, configurable hysteresis-based control policy:

- Open CB101 when frequency approaches the lower safety limit.
- Keep CB101 open while frequency recovers.
- Close CB101 once a configurable recovery frequency is reached.
- Prevent switching decisions that would knowingly violate the lower-frequency constraint.
- Prevent unnecessary rapid switching.

For the initial implementation, use:

- Breaker opening threshold: 49.55 Hz
- Breaker closing threshold: 50.00 Hz

Treat these as **additional design assumptions**, not requirements explicitly specified in the original brief.

Store both thresholds in configuration and validate their relationship to the safety limits.

The controller should use the FS101 reported frequency rather than directly accessing the actual frequency. During normal operation these values will be identical.

Do not implement PID control or complex generator regulation during this phase.

### D. Simulation Engine

Create a central simulation engine that orchestrates the system.

It must:

1. Initialize the system from configuration.
2. Record the initial state at t = 0.
3. Obtain the current sensor reading.
4. Execute the control logic.
5. Apply the resulting component states to the physics model.
6. Advance simulation time by one discrete step.
7. Record the updated state.
8. Perform sanity checks and record any violations.
9. Continue until the configured simulation duration is reached.

Implement a reusable `step()` function that advances the simulation by exactly one time step.

Implement a `run_simulation()` function that repeatedly invokes `step()` and returns the complete simulation history.

Clearly document the order in which sensor readings, controller decisions, physics updates, and state recordings occur.

The simulation must be deterministic: identical configurations and initial conditions should produce identical results.

**Avoid coupling simulation time to real-world wall-clock time.** A 120-second simulation should be able to execute immediately for testing. The frontend may later play back the results at a controlled rate.

### E. Sensor Model

For Phase 1, FS101 should report the actual bus frequency without measurement errors.

However, organize its implementation so that future changes can introduce:

- Sensor bias
- Sensor noise
- Frozen readings
- Incorrect measurements
- Sensor disconnection

Do not implement these failure scenarios yet.

## 5. Configuration Management

Avoid hard-coding parameters in the simulation logic.

Provide a centralized configuration mechanism, such as a JSON configuration file loaded into validated Python models.

Configuration should cover:

- Simulation duration
- Time-step duration
- Initial frequency
- Initial generator and breaker states
- Nominal frequency
- Upper and lower safety limits
- Frequency change rates for all four combinations
- Breaker opening and closing thresholds

Separate configuration values from calculations.

Validate configuration before running the simulation and provide meaningful errors for invalid combinations.

For now, one default configuration is sufficient. Do not build a full configuration editor.

## 6. Logging, Diagnostics, and Sanity Checks

Debugging and observability are essential.

### State Logging

Record the state at every simulation time step.

Each recorded sample should contain the time, actual frequency, sensor reading, generator state, breaker state, and load supply status.

### Event Logging

Log meaningful changes and decisions, including:

- Breaker opening
- Breaker closing
- Generator state changes, if applicable
- Frequency limit violations
- Invalid states or rejected configurations

Each event should include a timestamp, event type, and an informative reason.

Use Python's standard logging facilities where appropriate. Keep structured simulation events separately available in the simulation results so they can be inspected or displayed later.

Do not flood the application console with repetitive logs unless debug logging is enabled.

### Sanity Checks

Add checks for:

- Invalid or nonfinite frequency values
- Frequency outside configured limits
- Breaker CLOSED while frequency is below the lower limit
- Invalid component states
- Invalid configuration values
- Inconsistent simulation timestamps

Distinguish between an invalid configuration, a simulation invariant violation, and a legitimate abnormal operating condition.

Do not silently repair invalid simulation states by modifying frequency values.

Normal-operation tests should fail if required safety constraints are violated.

## 7. Backend API

Use FastAPI to expose the simulation to the frontend.

Implement only the endpoints needed for the first working version.

Suggested endpoints:

- `GET /api/config` — return the active default configuration.
- `POST /api/simulations/run` — execute a simulation using validated configuration or permitted overrides.
- `GET /api/health` — basic API health check.

The simulation endpoint should return:

- Configuration used
- Complete time-series samples
- Simulation events
- Any safety violations
- Basic summary statistics, including time the station load was powered

Keep API request and response models separate from internal simulation logic where appropriate.

Do not implement a database, authentication, WebSockets, or background job system for Phase 1.

## 8. Frontend — Minimal Verification Interface

**Do not spend time designing a polished UI.**

The initial frontend exists only to help verify the simulator.

Use a simple single-page layout with:

- A heading identifying the simulator
- A configurable simulation duration input
- A "Run Simulation" button
- Three time-series graphs
- A small text-based summary of the run
- Basic display of simulation errors or violations

### Required Graphs

**Graph 1: Bus Frequency**

Display FS101 reported frequency against simulation time.

Clearly show the following horizontal reference lines:

- Lower limit: 49.50 Hz
- Nominal frequency: 50.00 Hz
- Upper limit: 50.50 Hz

**Graph 2: Generator G101**

Display generator state over time.

- 1 = ON
- 0 = OFF

Use a step-style graph rather than interpolating between discrete states.

**Graph 3: Circuit Breaker CB101**

Display breaker state over time.

- 1 = CLOSED
- 0 = OPEN

Also use a step-style graph.

All graphs should use the same simulation timeline.

Keep the components small and straightforward. Use Tailwind CSS utility classes for basic layout and styling.

Avoid:

- Animations
- Complex dashboards
- Elaborate colour palettes
- Authentication
- Routing
- Custom UI component libraries
- Premature abstractions for frontend components

The UI can display the completed simulation immediately after the API responds.

I will handle advanced UI/UX design and real-time playback in later iterations.

## 9. Software Engineering Requirements

Treat this as a maintainable engineering project, not a quick demonstration script.

Follow these guidelines:

1. **Separation of concerns:** physics, control, sensors, simulation orchestration, API, and UI should remain independent.
2. **Single responsibility:** functions and modules should have clear responsibilities.
3. **Small reusable functions:** prefer focused functions over large monolithic implementations.
4. **Type safety:** use Python type hints and TypeScript types.
5. **Configuration over hard-coding:** store adjustable model parameters centrally.
6. **Explicit state management:** avoid hidden or mutable global simulation state.
7. **Testability:** ensure the simulation engine can be tested independently.
8. **Consistent naming:** use descriptive names and consistent conventions.
9. **Error handling:** detect and explain failures rather than silently ignoring them.
10. **Minimal comments:** add comments only where the reasoning or implementation is genuinely non-obvious.

Apply good engineering practices pragmatically.

Do not introduce excessive abstraction, elaborate design patterns, or unnecessary layers solely for architectural purity.

## 10. Project Structure

Use a sensible, scalable project layout.

A possible structure is:

```text
power-grid-simulator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── simulation/
│   │   │   ├── models.py
│   │   │   ├── physics.py
│   │   │   ├── sensors.py
│   │   │   ├── controller.py
│   │   │   └── engine.py
│   │   ├── config.py
│   │   └── main.py
│   ├── config/
│   │   └── default.json
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   └── (React + Vite application)
├── README.md
└── .gitignore
```

You may adjust this structure where appropriate, but preserve the separation of responsibilities.

Do not create unnecessary files or empty abstraction layers.

## 11. Testing Requirements

Use Pytest to verify the core behaviour.

At minimum, test:

- All four generator/breaker frequency-change combinations
- Correct initialization
- Correct single-step calculations
- Simulation duration and sample count
- Deterministic execution
- Breaker opening at the configured threshold
- Breaker reconnection after frequency recovery
- Frequency remaining within the safe range during normal operation
- Breaker never CLOSED below the lower limit during normal operation
- Invalid configuration handling

A 120-second simulation at one-second intervals should produce 121 recorded samples, including the initial state at t = 0.

The backend tests must run without the React frontend or API server.

## 12. Design Assumptions and Documentation

**Any design assumption not explicitly specified in the original project brief must be clearly documented.**

Create a dedicated `Design Assumptions` section in the README.

For every additional assumption, document:

- The assumption
- Why it was necessary
- Its implications for simulation behaviour
- Whether it is configurable

In particular, explain:

- The selected breaker control thresholds
- The initial operating state
- The initial ideal sensor behaviour
- How the generator is controlled during normal operation
- The interpretation of frequency when the generator is OFF
- The order of control decisions and physics updates
- How load disconnections are represented
- Any limitations imposed by the simplified physical model

If the original requirements conflict with the simplified frequency dynamics, do not conceal the conflict.

Document the limitation and implement the simplest defensible behaviour consistent with the stated requirements.

Also explain the difference between the current simplified model and a physically accurate power-grid simulation.

## 13. Implementation Order

Implement the project incrementally in this order:

**Step 1 — Simulation Models and Configuration**

Define the system state, component states, configuration models, and validation.

**Step 2 — Physics Engine**

Implement and test all four frequency dynamics.

**Step 3 — Controller**

Implement the initial hysteresis-based breaker controller.

**Step 4 — Simulation Loop**

Implement `step()` and `run_simulation()`, including state recording, events, and sanity checks.

**Step 5 — Backend Tests**

Verify a complete 120-second normal-operation simulation. Fix any failures before proceeding.

**Step 6 — FastAPI Integration**

Expose the working simulation through the API without moving physics or control logic into route handlers.

**Step 7 — Minimal React Frontend**

Implement only the necessary controls, graphs, and basic diagnostics.

**Step 8 — Documentation and Verification**

Provide clear setup instructions, document assumptions, run tests, and verify that the application works end to end.

## 14. Definition of Done

Phase 1 is complete when:

- The Python simulation runs independently.
- A 120-second normal scenario executes successfully.
- The frequency remains within the defined safety limits during normal operation.
- The breaker controller opens and reconnects the load appropriately.
- The frontend displays all three required graphs.
- System state and control events can be inspected.
- Core tests pass.
- Model parameters can be adjusted through configuration.
- The README documents setup, architecture, design assumptions, and known limitations.

## 15. Final Instructions

Start by implementing the simplest fully working version.

Prioritize **correct simulation behaviour, clean separation of responsibilities, configurability, testability, and maintainability** over advanced features.

Do not implement future features simply because the architecture allows them.

Keep the initial interface intentionally basic.

When implementation is complete, provide:

1. A concise summary of what was implemented.
2. Instructions to install dependencies and run the backend and frontend.
3. Commands to execute the automated tests.
4. A list of any additional design assumptions.
5. Any known limitations or unresolved issues.

The final result should be a reliable foundation that I can extend with subsequent Codex prompts without needing to restructure the core simulator.
