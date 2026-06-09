# Task Offloading over ROS2

Proof-of-concept implementation of dynamic task offloading between a Physical Twin (PT) and a Digital Twin (DT) using ROS2 lifecycle nodes and DDS pub/sub. Built on top of the Diagnostic Digital Twin battery monitoring system at McMaster University (MARC Center).

## What it demonstrates

A running ROS2 computation node migrates from the PT role to the DT role without stopping the data producer. The migration gap is measured automatically. Three modes are implemented with increasing autonomy.

## Dashboard

<img width="627" height="332" alt="Screenshot from 2026-06-09 17-15-26" src="https://github.com/user-attachments/assets/bfe9fbef-f32e-4a47-a55c-e3be4ada98ea" />


Live web dashboard at http://127.0.0.1:5000 showing:
- Node states (PT/DT active/inactive) with timestamps
- CPU and RAM gauges with threshold lines
- Migration gap timer and full gap history
- Summary stats (total offloads, avg/min/max gap)
- System health indicator (healthy / warning / critical)
- Manual controls (Mode 1) and reactive stress controls (Mode 2)
- CSV export of full session report

## Key insight

The streamer never needs to know about the new logger instance. DDS maintains a live registry of active subscribers per topic — when the PT logger deactivates and the DT logger activates on the same topic, routing happens transparently. No IP updates, no restarts, no reconfiguration on the producer side.

## Modes

| Mode | Trigger | Status |
|---|---|---|
| [Mode 1 — Manual](mode1_manual/) | Human button press or dashboard button | ✅ Done |
| [Mode 2 — Reactive](mode2_reactive/) | CPU/RAM threshold crossed automatically | ✅ Done |
| Mode 3 — Proactive | Predicted overload before threshold is hit | 🔄 Coming soon |

## Architecture

### Mode 1 — Manual

```
streamer_node → /data/stream → logger (PT, 127.0.0.1) [active]
                                        ↓ human fires trigger
                               logger (PT, 127.0.0.1) [inactive — preserved]
                               logger_dt (DT, 127.0.0.2) [active — took over]

offload_manager → deactivate PT → spawn DT → activate DT → measure gap
```

### Mode 2 — Reactive

```
cpu_stress  ↘
              resource_monitor → /offload_trigger → offload_manager
ram_stress  ↗                                              ↓
                                         deactivate PT ←──┤
streamer_node → /data/stream → logger (PT) [inactive]     │
                             → logger_dt (DT) [active] ←──┘

/pt/cpu_usage ↗
/pt/ram_usage ↗  live metrics + safety warnings published to dashboard

recovery: CPU < 10% → offload_manager → deactivate DT → reactivate PT
```

### Mode 3 — Proactive (coming soon)

```
resource_monitor → prediction model → /offload_trigger → offload_manager
                   (forecasts overload before threshold is crossed)
```

## Node inventory

| Node | Role | Used in |
|---|---|---|
| `streamer.py` | Publishes data to `/data/stream` at 1Hz | Modes 1, 2, 3 |
| `logger.py` | Lifecycle node — offloadable computation | Modes 1, 2, 3 |
| `offload_manager.py` | Orchestrates hot-swap, measures gap, lock-protected | Modes 1, 2, 3 |
| `dashboard_node.py` | Flask ROS2 node — live web dashboard | Modes 1, 2, 3 |
| `resource_monitor.py` | CPU/RAM monitor, auto-triggers offload | Modes 2, 3 |
| `cpu_stress.py` | Simulates CPU overload (3 intensity levels) | Mode 2 |
| `ram_stress.py` | Simulates RAM overload (3 intensity levels) | Mode 2 |

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
└── mode3_proactive/    ← prediction-based (coming soon)
```
