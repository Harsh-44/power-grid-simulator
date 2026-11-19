# Power Grid Simulator — Final UI/UX Refinement

## Your Role

Act as an experienced senior UI/UX designer and frontend engineer improving an existing engineering simulation dashboard.

The application is the Arctic Station Power Grid Simulator, built using React, TypeScript, Tailwind CSS, and Recharts.

Your task is to significantly improve the interface's usability, information hierarchy, visual communication, and overall refinement.

**This is not a functionality expansion or backend refactoring task.**

The simulator already works. Your responsibility is to make the interface easier to understand and operate without sacrificing its technical depth.

Review the current frontend implementation and existing components before changing anything.

---

## 1. Core Design Philosophy

Design around four principles:

### Clarity over quantity

The user should immediately understand what matters most without having to read everything on the screen.

Show essential information by default and make secondary information easily accessible when needed.

### Progressive disclosure

Do not remove existing information to make the interface look cleaner.

Instead, organize information according to importance.

Primary information should be immediately visible. Detailed metrics, configuration settings, event history, and diagnostic explanations should be accessible through contextual panels, expandable sections, or drawers.

### Visual hierarchy

Differentiate information using typography, positioning, alignment, whitespace, and contrast.

Avoid giving every piece of information equal visual emphasis.

### Consistency

Use consistent sizing, spacing, colours, typography, controls, and component behaviour.

The interface should feel like one cohesive product rather than a collection of independent components.

---

## 2. Understand the User's Workflow

The intended workflow is:

1. Select or configure a simulation scenario.
2. Run the simulation.
3. Observe the frequency and component-state graphs.
4. Navigate the simulation timeline.
5. Inspect the system at a particular timestamp.
6. Investigate abnormal behaviour or specific events.
7. Open detailed metrics or diagnostics when necessary.

Design the interface around this workflow.

The most frequently used controls should be closest to the information they affect.

Avoid unnecessarily separating related information into distant sections.

The dashboard should support both quick interpretation and deeper investigation.

---

## 3. Establish a Clear Information Hierarchy

Use three levels of information.

### Primary — Always visible

These elements are essential:

- Bus frequency graph (FS101)
- Generator state graph (G101)
- Circuit breaker state graph (CB101)
- Simulation timeline and playback controls
- Current simulation status
- A small number of critical operational indicators

These should occupy the majority of the primary dashboard.

### Secondary — Accessible without leaving the dashboard

- Configuration controls
- Component-specific details
- Load availability
- Breaker switching information
- Fault information
- Comparison with the normal baseline

Use a compact side panel, drawer, or contextual disclosure.

### Tertiary — Available on demand

- Full operational metrics
- Complete event history
- Controller debug trace
- Detailed safety diagnostics
- Explanatory information and assumptions

These should not compete visually with the graphs.

Preserve all existing information and features.

Do not hide critical safety warnings inside secondary panels.

---

## 4. Dashboard Layout

The three required graphs are the foundation of the interface.

### Header

Use a compact header containing:

- Application identity
- Scenario selector
- Configure action
- Run Simulation action

Avoid unnecessary metadata or large headings.

### System Overview

Below the header, present a slim system-status strip.

Prioritize approximately three or four meaningful indicators:

- Actual frequency or frequency range
- Load availability
- Frequency safety status or violations
- Breaker operations

Avoid oversized statistic cards.

Consider using simple inline metrics separated by subtle dividers rather than four large containers.

The status strip should consume as little vertical space as possible while remaining readable.

### Main Visualization Area

Dedicate the largest portion of the screen to the bus frequency graph.

The frequency chart should be immediately identifiable as the primary visualization.

Below it, place the G101 generator and CB101 breaker graphs side by side.

Keep their proportions appropriate for discrete ON/OFF and OPEN/CLOSED states.

Both state graphs should remain visible without requiring scrolling at normal desktop resolutions.

### Playback Controls

Place playback controls directly beneath the graph area, visually integrated with the timeline.

The controls should feel like they belong to the graphs, rather than appearing as a separate unrelated dashboard section.

Organize the controls logically:

- Reset / return to beginning
- Step backward
- Play / Pause as a single stateful primary control
- Step forward
- Timeline scrubber
- Current timestamp / total duration

Use recognizable icons with accessible labels and tooltips.

Avoid presenting Play and Pause as two separate prominent buttons when one toggle is sufficient.

The playback timeline should be visually prominent enough to encourage interaction, but not compete with the frequency graph.

### Current State Inspector

Show the system state corresponding to the selected playback time.

Include:
- FS101 actual and reported frequency
- G101 state
- CB101 state
- L101 load connection and power supply state

Present these as compact status indicators closely associated with the visualization.

Avoid giving the state inspector a large independent card unless necessary.

Clearly distinguish values for the selected timestamp from whole-run statistics.

---

## 5. Typography

Improve the typographic system significantly.

Use a modern, highly legible sans-serif font suitable for technical dashboards. Prefer an existing font already in the project, or a sensible system font stack.

Establish a restrained type scale:

- Application title: approximately 16–18 px, semibold
- Section titles: approximately 13–15 px, semibold
- Primary metric values: approximately 18–22 px, semibold
- Body content: approximately 13–14 px
- Supporting labels: approximately 11–12 px, medium or regular

Adjust where necessary for readability.

Use:
- Tabular numerals for frequencies, times, counts, and percentages
- Consistent unit formatting
- Clear label/value relationships
- Consistent line heights
- Restrained use of bold weights
- Muted secondary text with sufficient contrast

Avoid:
- Excessively bold text everywhere
- Very small technical labels
- Inconsistent font sizes
- Unnecessarily large headers
- Excessive uppercase text

Typography should communicate which information is important before the user starts reading.

---

## 6. Alignment and Spacing

Use a consistent spacing system, preferably based on 4 px increments.

Align:
- Panel boundaries
- Headings
- Labels and values
- Buttons and inputs
- Chart axes where feasible
- Related status indicators

Use consistent internal padding.

Avoid arbitrary gaps or excessive whitespace that reduce the available graph area.

Also avoid making everything so compact that it becomes difficult to scan.

Pay particular attention to:
- The alignment of the three graphs
- The placement of chart titles and legends
- The relationship between playback controls and timeline
- The alignment of the current-state indicators
- Consistent margins between major layout regions

Use CSS Grid and Flexbox rather than absolute positioning for the dashboard structure.

---

## 7. Colour and Semantic Indicators

Use a restrained, consistent colour system.

Suggested direction:

- Light neutral background
- White or near-white surfaces
- Subtle cool-grey borders
- Deep neutral text
- Blue for primary interactions and primary graph data
- Muted violet for FS101 reported frequency
- Green for healthy/normal status
- Amber for caution and active fault states
- Red for actual safety violations or critical warnings

Do not colour everything.

Use semantic colours only when they convey useful meaning.

For example:

- G101 ON can use a subtle green status indicator.
- CB101 CLOSED can use a neutral or positive connected indicator.
- CB101 OPEN should clearly indicate disconnected status, but should not automatically imply a safety violation.
- Actual frequency outside limits should be visibly critical.
- A sensor measurement fault should be distinguishable from an actual frequency violation.

Do not rely on colour alone. Always accompany meaningful status with text, icons, or another visual cue.

Use a consistent icon library if one already exists.

Avoid adding icons merely for decoration.

---

## 8. Graph Refinement — Highest Priority

Spend the most design attention on the graphs.

### FS101 Bus Frequency

Keep it as the dominant visualization.

Retain:
- Actual frequency
- FS101 reported frequency
- Nominal frequency reference
- Upper and lower safety limits
- Fault interval shading
- Tooltips
- Selected playback time indicator

Improve the following:

**Visual distinction**
- Use a solid blue line for actual frequency.
- Use a muted dashed line for reported frequency.
- When actual and reported frequency overlap, avoid creating unnecessary visual clutter while maintaining a clear legend.

**Safety limits**
- Use subtle dashed reference lines.
- Clearly identify the upper and lower limits.
- Avoid visually overwhelming the chart with strong red lines during normal operation.

**Fault visualization**
- Use restrained translucent shading.
- Show fault start and end clearly.
- Avoid hiding the graph lines behind fault shading.

**Axis design**
- Ensure labels are readable.
- Use consistent numerical precision.
- Avoid excessive tick labels.
- Preserve sufficient vertical spacing to make frequency changes easy to interpret.

**Tooltips**
- Display simulation timestamp.
- Actual frequency.
- Reported frequency.
- Frequency status.
- Relevant component state where useful.

Keep tooltips concise and properly formatted.

**Playback cursor**
- Show a subtle synchronized vertical marker identifying the current playback timestamp.
- The marker should be visible without dominating the chart.

### G101 and CB101 Graphs

Both are mandatory functional requirements.

Retain accurate step-style state visualization.

Use consistent visual language across both graphs.

Make the ON/OFF and OPEN/CLOSED labels immediately understandable.

Avoid unnecessary chart gridlines.

Keep both graphs aligned and appropriately sized.

Ensure their playback markers correspond to the same timestamp as the frequency graph.

Do not interpolate discrete component states.

### Interaction

Where feasible, allow clicking or selecting a timestamp on a graph to update the playback position.

If this can be implemented cleanly with the existing charting library, do so without introducing a separate simulation system.

Do not compromise chart rendering or stability to introduce this interaction.

---

## 9. Configuration Experience

The configuration form should remain fully functional but should not dominate the dashboard.

Use a compact Configure action opening a simple side drawer.

Group related settings into meaningful sections:

**Simulation**
- Duration
- Initial frequency

**Controller**
- Breaker opening threshold
- Breaker recovery threshold

**Fault Settings**
- Fault start time
- Fault duration
- Sensor frequency offset

Only display fault settings when applicable.

Use clear field labels and units.

Preserve configuration validation.

Keep the Run Simulation action easy to locate.

If the configuration is changed after a simulation has run, distinguish between pending input values and the configuration used for the currently displayed results.

Do not silently imply that existing graphs represent newly edited parameters before rerunning.

---

## 10. Detailed Information and Diagnostics

Preserve all existing information.

Use a single organized detail panel with compact sections or tabs for:

- Operational metrics
- Component diagnostics
- Fault analysis and baseline comparison
- Event log
- Controller debug trace, if present

Do not introduce multiple overlapping drawers.

The detail panel should be easy to open and close.

Use clear section headings and sensible groupings.

The event log should support chronological scanning and retain navigation to corresponding playback timestamps.

Use semantic differentiation for event types:
- Breaker transition
- Sensor fault
- Safety violation
- Fault recovery

Avoid oversized event rows.

Present operational metrics with readable precision and clear units.

Make detailed data accessible without requiring users to navigate to another page.

---

## 11. Visual Feedback and Interaction States

The user must always understand what the application is doing.

Implement clear visual feedback for:

- Running a simulation
- Simulation completion
- API or validation errors
- Playback running
- Playback paused
- Reaching the end of the timeline
- Active sensor fault
- Unsafe actual frequency
- Current breaker state
- Disabled controls
- Selected timestamp or event

Distinguish:

**Simulation execution** — Python computing results.

**Playback** — React navigating already computed results.

Avoid calling playback "live simulation" if the entire run was already calculated.

Use subtle transitions for panels, controls, and status changes.

Avoid excessive animation.

---

## 12. Responsive Layout and Viewport Usage

Desktop is the main target.

Aim to keep the entire primary dashboard visible without vertical page scrolling at:

- 1920 × 1080
- 1440 × 900
- 1366 × 768

Prioritize keeping:
- All three graphs
- Essential operational indicators
- Playback controls
- Current state information

visible together.

Use viewport-aware layout sizing.

Do not achieve this by making charts or text unreadably small.

Use internal scrolling for detailed panels.

On narrow screens, allow sensible stacking and vertical scrolling.

Do not clip information or break responsiveness to enforce the desktop requirement.

---

## 13. Engineering Constraints

Do not modify:

- Backend physics
- Controller policies
- Sensor fault behaviour
- Simulation stepping
- Safety calculations
- Metrics calculations
- API contracts

Preserve the existing separation between simulation logic and UI.

Maintain:
- React and TypeScript
- Tailwind CSS
- Existing chart library
- Small reusable components
- Clean project organization
- Type safety
- Clear naming
- Minimal necessary comments
- Sensible error handling

Avoid unnecessary frontend abstractions and dependencies.

Do not duplicate simulation logic in the frontend.

All simulation values must continue originating from backend results.

---

## 14. Implementation Process

First, inspect the current frontend and identify the main usability issues.

Then:

1. Reorganize the overall dashboard layout.
2. Establish a consistent typography and spacing system.
3. Refine the header and configuration access.
4. Improve the operational status hierarchy.
5. Make the frequency graph the primary focus.
6. Align and simplify the generator and breaker graphs.
7. Integrate playback with the visualizations.
8. Refine the current state inspector.
9. Organize detailed metrics and events into a secondary panel.
10. Improve interactive states and visual feedback.
11. Verify all existing features still work.
12. Test the responsive layout at the target desktop resolutions.

Do not make superficial CSS changes without reconsidering the information hierarchy and user workflow.

However, avoid rebuilding components unnecessarily.

## 15. Acceptance Criteria

The redesign is complete when:

- The three graphs are clearly the main focus.
- The dashboard is easier to understand within a few seconds.
- Important system conditions are immediately identifiable.
- Playback controls are positioned naturally and intuitively.
- Typography and spacing feel consistent.
- The design uses colour purposefully.
- Current-time information and whole-run metrics are clearly distinguished.
- Detailed information remains accessible without overwhelming the main dashboard.
- The primary desktop dashboard fits within the viewport where practical.
- All existing configurations, metrics, events, fault scenarios, and playback features work.
- No simulation or backend functionality has been changed.
- Frontend build and existing regression tests pass.

## Final Instructions

The objective is not to make the simulator look more complicated or visually impressive.

It is to make the simulator **simpler to understand, faster to operate, and easier to investigate**, while preserving every important technical detail.

Be deliberate about every layout decision.

If an element does not need to be visible constantly, make it accessible contextually rather than permanently occupying space.

Do not sacrifice technical correctness or functional requirements for visual appearance.

After implementation, summarize the layout changes, interaction improvements, and verification results.
