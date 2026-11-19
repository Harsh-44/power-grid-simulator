# Arctic Station Power Grid Simulator

The simulator models a single 50 Hz bus at an Arctic research station. Diesel generator G101 supplies station load L101 through breaker CB101. The controller uses the reading from frequency sensor FS101. The Python engine returns a complete history and operational summary. The browser uses that history for playback, inspection, and event navigation.

## Setup

Install Python 3.11 or newer and Node.js 20.19+ or 22.12+. Run the commands from the project root in two terminals.

### Backend

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
```

On macOS or Linux:

```sh
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -e '.[test]'
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
```

### Frontend

```sh
cd frontend
npm ci
npm run dev
```

Open [the local simulator](http://127.0.0.1:5173). Vite forwards `/api` requests to port 8000. Run `npm run build` from `frontend` to type-check and build the UI.

If an older simulator backend is already running on port 8000, stop it and start it using the command above. Uvicorn then reloads Python source changes under `app`.

## How to Use the Simulator

Choose **G101 generator failure** and enter a shutdown time in **Configure**. Choose **Manual state testing** to select the initial G101 and CB101 states. In manual testing, the simulation duration is also the hold interval. The run can start outside frequency limits, and the usual safety metrics and events remain active. The **Run details** load metrics distinguish time connected from time supplied by G101.

### Phase 4 physics checks

| G101 | CB101 | Default rate | After one second from 50.00 Hz |
| --- | --- | ---: | ---: |
| ON | CLOSED | −0.05 Hz/s | 49.95 Hz |
| ON | OPEN | +0.12 Hz/s | 50.12 Hz |
| OFF | CLOSED | −0.15 Hz/s | 49.85 Hz |
| OFF | OPEN | 0.00 Hz/s | 50.00 Hz |

The rates are the original configurable inputs. In the run API, `generator_shutdown_seconds` schedules a failure, and `manual_state_testing: true` holds `initial_generator_state` and `initial_breaker_state`. These scenarios and FS101 bias are mutually exclusive. A shutdown requires an initially running G101 and a timestamp on the time-step grid from zero to strictly before the last sample.

### Phase 4 timing assumptions

- Shutdown is instantaneous and G101 stays off. At the start of the scheduled interval the engine applies the shutdown before selecting component states for that interval. If CB101 was closed, its state is held for this interval, which uses the OFF/CLOSED rate. On the next step the existing generator-off interlock opens CB101. A breaker that was already open stays open and the OFF/OPEN rate applies immediately.
- The engine uses the FS101 reading captured at the start timestamp for automatic decisions. It advances the original physics, then records the resulting states and the next FS101 reading and checks safety. The scheduled event marks the transition at the start timestamp. The sample at that timestamp still holds the pre-decision component state. The step chart shows the switch at the interval boundary.
- Manual testing holds the states for every interval. Controller traces omit held intervals because they contain no automatic decision. The log marks entry into and exit from an elapsed connected-without-power period, and the regular frequency event and closed-below-limit diagnostics still apply.

1. The dashboard opens with a run using the server defaults. Use **Configure** to edit the **Simulation** and **Controller** settings. Choose **FS101 measurement fault** in the header to reveal **Fault settings**. **Pending settings** means the plots still show the last completed run. Select **Run Simulation** to apply your edits. The previous result stays visible while the new run computes or if a submission fails.
2. The **Run overview** shows execution and frequency safety status. Each graph has its own card. The **Selected state** strip describes the current sample, including actual and reported frequency, fault activity, component states, load connection, and power supply.
3. Use **Reset**, **Step backward**, the **Play / Pause** toggle, **Step forward**, or the timeline slider beneath the plots. Clicking a point in any chart also seeks to the nearest recorded sample. The frequency tooltip shows both readings and the recorded safety status. The vertical playback marker follows the selection on all three charts. Coincident actual and reported readings share one plotted line.
4. Open **Run details** for frequency ranges, load availability, breaker counts, protection diagnostics, and chronological events. Fault runs also show the fault summary and equivalent normal baseline. Selecting an event timestamp closes the centered dialog and focuses the timeline. A breaker event describes the decision made at that sample. Step forward to see the resulting recorded state.
5. Select **Include controller debug trace** in **Configure** before running to capture every controller decision, then open the trace in **Run details**. The configuration drawer and run details dialog scroll internally and close with Escape.

The desktop layout places simulation controls, run status, playback and the selected state on the left, with all three graph cards on the right. The control column can scroll independently on shorter desktop viewports. On phones, the graphs stack below the controls.

The default 120-second normal run records 121 samples and an actual frequency range of 49.51–50.11 Hz. It reports zero safety violations, 87 seconds connected and supplied, and 33 seconds disconnected. Load connection availability is 72.5%. G101 runs for all 120 seconds. CB101 opens seven times and closes seven times, and the longest disconnection is five seconds.

For an example fault, set the simulation duration to 30 s and enter a 5 s fault start, 20 s fault duration, and +0.5 Hz offset. At 11 s, FS101 reports 49.95 Hz while the actual frequency is 49.45 Hz. CB101 is still closed, and the event log reports the actual low-frequency condition. Over the run, the fault produces three breaker operations and 70% load connection availability, compared with four operations and 73.33% availability in the normal baseline.

For the 120 s regression case, use a 5 s start, 90 s duration, and −0.50 Hz offset. The run has 14 breaker operations and 8 over-frequency samples in 5 episodes. It spends about 7.367 s above the upper limit and 0 s closed below the lower limit. The fault activates at 5 s and clears at 95 s.

## Running the engine and tests

From `backend`, with the virtual environment active, run:

```sh
python -m pytest
python -m pytest tests/test_config.py tests/test_simulation.py tests/test_metrics.py tests/test_sensor_faults.py tests/test_diagnostics.py
python -c "from app.config import load_config; from app.simulation.engine import run_simulation; result = run_simulation(load_config()); print(len(result.samples), result.summary)"
```

The first command runs the full suite, including in-process API tests. The second runs the configuration, engine, and metrics tests. Both work without either server. To run without activating the environment, replace `python` with the virtual environment's Python executable shown above.

## Configuration and API

Edit [`backend/app/default.json`](backend/app/default.json) to change the initial states, limits, rates, thresholds, duration, time step, or optional FS101 bias. Restart FastAPI to load changes. The Python engine can also accept a validated `SimulationConfig` constructed in code or loaded with `load_config(path)`.

| Endpoint | Result |
| --- | --- |
| `GET /api/health` | Basic readiness response |
| `GET /api/config` | Active default configuration |
| `POST /api/simulations/run` | Configuration, samples, operational events, protection findings, summary, and optional controller trace |

The POST accepts this optional set of per-run overrides. Omitted values use the active configuration.

```json
{
  "duration_seconds": 30,
  "initial_frequency_hz": 50.00,
  "breaker_open_threshold_hz": 49.60,
  "breaker_close_threshold_hz": 50.10
}
```

The duration must be a positive multiple of the configured time step. An explicitly supplied initial frequency must be within the configured limits for a normal run. Both thresholds must be within the limits, and the opening threshold must be lower than the recovery threshold. For advanced diagnostics, Python and the backend configuration still allow an out-of-band initial state. A POST that omits the initial frequency uses that state if it is configured.

Supply `fs101_bias` to run the sensor fault scenario. Omit it to use the backend configuration or send `null` to explicitly select ideal FS101.

```json
{
  "fs101_bias": {
    "start_seconds": 5,
    "duration_seconds": 20,
    "offset_hz": 0.5
  }
}
```

The start must be nonnegative, the duration must be positive, and the offset must be finite. Start and end must be on the time-step grid, and the end can be as late as the final sample. Fault runs include `fault_analysis` with the effective window, summary, and baseline comparison.

The response includes the effective configuration and summary groups `frequency`, `load`, `generator`, and `breaker`. Each sample includes its actual frequency condition. `events` carries the operational timeline and `violations` is the subset of episode-entry events. In the frequency summary, `safety_violation_count` is an alias for `violating_sample_count`. Set `include_controller_trace` to `true` to populate `controller_trace`. It is `null` by default. The live API exposes [OpenAPI documentation](http://127.0.0.1:8000/docs).

Rejected API inputs return HTTP 422. A malformed simulation state raises `SimulationInvariantError` with a structured `invalid_state` event and returns HTTP 500 through the API. A completed run retains its samples even when their actual frequency is outside limits. The engine logger records operational events at DEBUG level and reports the sample and episode totals in one warning. Its `controller` child logger records each decision at DEBUG level.

## Architecture

| Module | Responsibility |
| --- | --- |
| `app/config.py` | Load and validate settings with Pydantic |
| `app/simulation/models.py` | Typed component states, physical state, samples, events, and results |
| `app/simulation/physics.py` | Select a configured rate and advance the physical state |
| `app/simulation/sensors.py` | Produce an FS101 reading from the physical state |
| `app/simulation/faults.py` | Apply a scheduled bias to an FS101 reading and emit fault transitions |
| `app/simulation/controller.py` | Select the breaker position from the previous position, generator status, and FS101 reading |
| `app/simulation/engine.py` | Run discrete steps, collect events, and run the ideal-sensor baseline when requested by the fault scenario |
| `app/simulation/diagnostics.py` | Check sample invariants, detect frequency transitions, and assess recorded breaker decisions |
| `app/simulation/metrics.py` | Calculate operational metrics, measurement error, and baseline deltas |
| `app/api/` and `app/main.py` | Adapt simulation inputs and outputs to HTTP |
| `frontend/src/` | Submit configuration, select a recorded sample during playback, and render the inspector, summary, events, and charts |

### Step order

1. Record the configured physical state and its FS101 reading at `t = 0`. Apply any active offset to that reading and record any fault transition and operating-limit events.
2. Use the FS101 reading at the current sample time to decide the breaker position. When a switch occurs, timestamp it at the start of the interval.
3. Hold the resulting generator and breaker states for one time step. Apply `next_frequency = current_frequency + frequency_rate × time_step` to the actual frequency and advance the clock.
4. Read FS101 once at the new time and apply any active offset. Validate and append the sample, recording a fault transition and a frequency condition change if either occurs. Its reported frequency becomes the input for the next decision.
5. Repeat through the configured duration. The step-state charts draw each interval with the breaker and generator state that applied during it.

### Metric accounting

- Each adjacent sample pair contributes its elapsed time once. Its ending sample carries the generator and breaker states used during that interval. The initial sample contributes zero time. A positive-duration open streak counts as an episode even when the run starts open or ends before reconnection.
- Breaker operations are counted from recorded switch events. Starting in a state contributes no operation. A decision at `t = 0` counts when it changes the initial state. The final sample is recorded after the last interval and has no further control decision.
- A violating sample is a recorded actual frequency strictly outside the configured limits. An episode is a consecutive run of recorded samples on the same side of the safe band. An out-of-band initial sample starts an episode at 0 s. If consecutive samples jump from one side to the other, the exit and new entry are recorded in that order at the second sample. An episode still active at the last sample has no exit event.
- Average actual frequency and elapsed safety durations use the linear segments between actual readings. Out-of-band time includes the exact fraction of each interval outside the limits. CB101 closed-below-limit time counts only the portion below the configured lower bound (49.50 Hz by default) during intervals that ran with CB101 closed. Each interval uses its ending sample's breaker state. The signed minimum margin measures the largest excursion beyond either bound when negative.
- Connection availability is connected time divided by elapsed time. Power-supply duration additionally requires G101 to be on. For the default on-generator scenario the two durations are equal.

### Breaker protection criteria

The post-run check evaluates the existing policy at each recorded decision that began with CB101 closed. It substitutes the actual frequency for the reported reading while keeping the same generator state, breaker state, thresholds, and one-step projection. The observed decision is the breaker state applied to the following interval.

| Finding | Observed decision | Policy with ideal FS101 |
| --- | --- | --- |
| Premature opening | Opens CB101 | Keeps CB101 closed |
| Missed protective opening | Keeps CB101 closed | Opens CB101 |

Each finding is tied to one decision, so consecutive missed decisions count separately. The check measures a difference from the ideal-reading policy at the observed state. The full normal baseline is a separate run with its own trajectory.

## Design Assumptions

| Assumption or brief baseline | Reason and effect | Configurability |
| --- | --- | --- |
| Open CB101 at or below 49.55 Hz. Reclose at or above 50.00 Hz. | The separate thresholds supply a margin above 49.50 Hz and make the controller wait for recovery before reconnecting. The gap provides hysteresis. | Both thresholds are configurable and must be ordered within the safety band. |
| Before leaving or putting CB101 closed, project the next frequency from FS101 with the closed-breaker rate. | A larger step or steeper decline can cross the lower limit before the opening threshold reacts. The controller opens or stays open if the projected value is below the lower limit. Equality at the limit is allowed by the projection. | The projection uses the configured rate, step, and lower limit. |
| Start at 50.00 Hz with G101 on and CB101 closed. | This is the baseline in the brief. The initial sample preserves the configured starting state. An explicitly unsafe start is recorded at zero, then the first control decision applies. | The initial frequency and both component states are configurable. |
| FS101 is ideal and sampled once per recorded timestamp. | This is the Phase 1 baseline. The recorded measurement is also the reading used for the next decision. Actual and reported frequencies remain distinct in the sample. | The Python engine accepts a sensor callable. The API and UI use the ideal sensor. |
| G101 holds its initial state unless a shutdown is scheduled. Automatic control opens CB101 when G101 is unavailable after the scheduled hold, or immediately when starting off. | The generator-off interlock isolates L101 during automatic operation. | Initial states, shutdown time, and manual testing are configurable. |
| Bus frequency with G101 off is a synthetic state variable. | This lets the model apply all four supplied rates. With G101 off and CB101 open, the default rate holds the last simulated frequency even though the load is unpowered. | Both off-state rates are configurable. |
| CB101 closed means L101 is connected. L101 is powered only when CB101 is closed and G101 is on. | Connectivity and supply are derived from component states. Power time counts the intervals in which both conditions hold. The initial sample contributes zero elapsed time. | Initial states and step size are configurable. The supply rule is fixed. |
| Switching occurs before physics for the next interval. | The controller acts on the current reading. The end sample records the component positions that applied during the interval. Events and step charts place the switch at the interval start. | Fixed execution order. |
| The duration is positive and lies on the time-step grid. Configuration numbers use up to 16 digits with up to eight decimal places. | Whole intervals give a consistent final timestamp and sample count. Decimal arithmetic avoids binary floating-point drift at thresholds. The API serializes numbers as JSON numbers. | Duration and time step are configurable within these validation rules. |
| Playback advances one recorded sample per wall-clock second. | A fixed inspection cadence keeps each step visible for custom time steps. The timeline, event jumps, and cursor use actual recorded timestamps. Playback pauses on manual navigation, at the end, and when a new run starts. | Fixed playback cadence. Simulation time step is configurable separately. |
| Safety events use recorded timestamps and duration metrics use linear segments. | Timeline links seek to existing samples. Duration metrics include partial intervals between samples. | Fixed metric convention. Frequency limits are configurable. |
| Fault start is inclusive and end is exclusive. Both boundaries lie on the sample grid. | The start sample already carries the bias and the end sample has a restored reading. Fault transitions are logged at those samples before any control decision made at the same timestamp. A fault can start at zero or clear at the final sample. | Start and positive duration are configurable. |
| FS101 reports the ideal reading plus the configured offset while the bias is active. | Positive offsets read high, negative offsets read low, and a zero offset can serve as a comparison check. The applied bias changes only the reading. Any subsequent effect on actual frequency comes through CB101 decisions. Safety checks use the actual frequency. | One finite signed offset per run. |
| Fault comparisons run the same effective configuration with the bias removed. | Deltas represent fault run minus normal run across the full simulation. Availability deltas use percentage points. | The baseline shares the selected initial conditions, rates, thresholds, time step, and duration. |
| Fault summary measures the full run, including effects after clearance. | The frequency count is the number of out-of-range recorded samples. Maximum measurement error is the largest absolute gap between actual and reported samples. | Metric convention is fixed. |
| Operational ties are ordered fault boundary, frequency exit and entry, then breaker operation. | This follows sample capture and the subsequent decision. One breaker transition produces one operational entry. | Fixed event order. |
| A selected debug trace records one decision per simulated step. | It includes hold decisions before, during, and after bias. The final sample has no following step. | The UI and API can opt in. |

The chart connects sampled values for display. The sensor offset changes at the scheduled sample boundaries. The UI rounds displayed metrics and preserves sample timestamps for seeking. Calculations retain decimal precision in Python.

## Known Limitations

- At the supplied rates, frequency falls whenever G101 supplies L101. Recovery requires opening CB101 and interrupting station power because the model has no governor, energy storage, or adjustable generation. A safe run can include disconnections.
- The model uses fixed rates for a single bus. A detailed electrical model would also represent power balance, load demand, generator inertia, voltage, and the loss of a measurable waveform on a de-energized bus.
- Breaker changes take effect at interval boundaries. Mechanical delays, operating limits, and wear are outside the model.
- FS101 is ideal outside the one scheduled additive bias window. The scenario models a temporary fixed offset.
- With G101 off, bus frequency is a synthetic variable that follows the configured off-state rate. The default OFF/OPEN rate holds the last value. CB101 closed means the load is connected, and confirmed generator power requires G101 ON as well. The brief’s stored-energy description supplies the OFF/CLOSED frequency rate. It leaves delivered power, energy consumption, and backup supply duration unspecified.
- Custom rates, thresholds, initial conditions, and time steps can cause operating-limit violations. For example, opening can raise frequency past the upper limit within a single interval. The result preserves the calculated values and reports the excursions.
- The engine retains the complete history in memory and returns it in a single response. Use shorter runs or coarser steps when checking large configurations.
