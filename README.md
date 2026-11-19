# Arctic Station Power Grid Simulator

A power grid simulator built for a remote Arctic research station. It models a single generator (G101), circuit breaker (CB101), station load (L101), and frequency sensor (FS101).

Built using Python, FastAPI, React, TypeScript, and Tailwind CSS.

## Features

- Frequency simulation with configurable parameters
- Automatic breaker control to keep frequency within 49.50–50.50 Hz
- Graphs showing frequency, generator, and breaker states over time
- Playback controls, event logs, and operational metrics
- Sensor faults and generator failure scenarios
- Manual testing of all four generator/breaker states

## Setup

**Requirements:** Python 3.11+ and either Node.js 20.x (20.19 or newer) or Node.js 22.12 or newer.

### Backend

From the project root in Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
```

From the project root on macOS or Linux:

```sh
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -e '.[test]'
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
```

### Frontend

In a second terminal, start from the project root:

```bash
cd frontend
npm ci
npm run dev
```

Vite forwards `/api` requests to the backend on port 8000. Open [the local simulator](http://127.0.0.1:5173/).

## How to Use

Choose a scenario, adjust the settings under **Configure**, and click **Run Simulation**.

You can use the playback controls to go through the simulation, inspect the graphs, and check the event logs and metrics under **Run details**.

## Frequency Model

The simulator uses the frequency variation rates given in the task brief:

| Generator | Breaker | Frequency change |
|---|---|---|
| ON | CLOSED | −0.05 Hz/s |
| ON | OPEN | +0.12 Hz/s |
| OFF | CLOSED | −0.15 Hz/s |
| OFF | OPEN | 0.00 Hz/s |

During normal operation, G101 stays ON while CB101 opens at 49.55 Hz and reconnects at 50.00 Hz, subject to safety checks.

**Limitations:** With the given frequency rates, the load has to be disconnected periodically to keep frequency within safe limits. The simulator follows the simplified model in the brief rather than modelling detailed generator regulation or electrical behaviour.

## Tests

Run the tests from `backend` with the Python interpreter you used to install the test dependencies. The backend and frontend servers can be stopped.

- Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m pytest
```

- macOS or Linux

```sh
./.venv/bin/python -m pytest
```

From `frontend`, run `npm run build` to type-check and build the UI.

## AI Usage

I used ChatGPT and Codex throughout development, mainly for planning, implementation, debugging, and reviewing simulation behaviour.

I've documented the process and prompts in [AI_USAGE.md](ai_usage_docs/AI_USAGE.md).
