Refine the existing Power Grid Simulator event logging and safety diagnostics without changing the physics, sensor fault behaviour, or controller policy.

Requirements:

1. Separate operational events from per-step controller diagnostics.
2. Keep the operational event log limited to meaningful events:
    - FS101 fault activation and clearance
    - CB101 opening and closing
    - Entering and exiting under-frequency or over-frequency conditions
3. Avoid duplicate event entries for the same breaker transition.
4. Preserve every controller decision in a separate optional debug trace, including decisions where the breaker state does not change.
5. Ensure logging remains consistent before, during, and after fault injection.
6. Distinguish these safety metrics:
    - Number of violating recorded samples
    - Number of distinct violation episodes
    - Duration spent outside safe frequency limits
    - Duration CB101 remains CLOSED while actual frequency is below 49.50 Hz
7. Add diagnostics for premature breaker openings and missed protective openings. Define their criteria explicitly, using actual frequency only for retrospective analysis, never to make controller decisions.
8. Retain chronological event ordering and clickable event timestamps in the React frontend.
9. Use readable numerical precision in the UI while preserving full precision in calculations.
10. Extend backend tests to verify event counts, violation episodes, diagnostic metrics, and normal-operation regression behaviour.
11. Document any new assumptions and metric definitions in the README.

Maintain all existing engineering standards: strict separation of simulation and UI logic, configurable parameters, small reusable functions, type safety, structured logging, sanity checks, deterministic simulation, minimal comments, and clean project organization.

Keep the UI simple. Do not introduce new physics, generator failure scenarios, or unnecessary dependencies.

Expected reference behaviour for the existing 120-second scenario with a −0.50 Hz FS101 bias active from 5 s until 95 s:

- 14 actual breaker operations
- 8 over-frequency recorded samples
- 5 distinct over-frequency episodes
- Fault activation at 5 s
- Fault clearance at 95 s

Do not hard-code these results. Use them as regression references and investigate any differences.

Report the modified files, tests executed, results, and any additional design assumptions.
