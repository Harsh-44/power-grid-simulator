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

**Requirements:** Python 3.11+ and Node.js 20.19+ or 22.12+

### Backend

Open a terminal in the project directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Frontend

Open another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173 in your browser.

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

From the `backend` directory:

```bash
python -m pytest
```

## AI Usage

I used ChatGPT and Codex throughout development, mainly for planning, implementation, debugging, and reviewing simulation behaviour.

I've documented the process and prompts in [AI_USAGE.md](AI_USAGE.md).
