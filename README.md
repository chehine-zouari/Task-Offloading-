# Task Offloading over ROS2

Proof-of-concept implementation of dynamic task offloading between a Physical Twin (PT) and a Digital Twin (DT) using ROS2 lifecycle nodes and DDS pub/sub. Built on top of the Diagnostic Digital Twin battery monitoring system at McMaster University (MARC Center).

## What it demonstrates

A running ROS2 computation node migrates from the PT role to the DT role without stopping the data producer. The migration gap is measured automatically. Three modes are implemented with increasing autonomy.

## Architecture

The core mechanism is the same across all modes:
- `streamer_node` publishes continuously to `/data/stream`, never changes
- `logger` (PT role) is a lifecycle node, deactivated on offload trigger
- `logger_dt` (DT role) spawns and activates, DDS routes data automatically
- `offload_manager` orchestrates the transition and measures the gap

**Key insight:** The streamer never needs to know about the new logger instance. DDS maintains a live registry of active subscribers per topic, when the PT logger deactivates and the DT logger activates on the same topic, routing happens transparently.

## Dashboard

![Task Offloading Dashboard](assets/dashboard.png)

Live web dashboard at `http://127.0.0.1:5000` showing node states, CPU/RAM gauges, gap timer, event log, and manual controls.

## Modes

| Mode | Trigger | Status |
|---|---|---|
| [Mode 1 — Manual](mode1_manual/) | Human button press | ✅ Done |
| [Mode 2 — Reactive](mode2_reactive/) | CPU/RAM threshold crossed | ✅ Done |
| Mode 3 — Proactive | Predicted overload | 🔄 Coming soon |

## Setup

```bash
cd ~/workspaces/acc_ws
colcon build --packages-select task_offloading
source install/setup.bash
```

## Repository structure

```
Task-Offloading/
├── mode1_manual/       ← manual trigger implementation
├── mode2_reactive/     ← resource threshold implementation  
├── mode3_proactive/    ← prediction-based (coming soon)
└── assets/             ← screenshots and diagrams
```
