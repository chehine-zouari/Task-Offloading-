# Task Offloading over ROS2

Proof-of-concept implementation of dynamic task offloading between a Physical Twin (PT) and a Digital Twin (DT) using ROS2 lifecycle nodes and DDS pub/sub. Built on top of the Diagnostic Digital Twin battery monitoring system at McMaster University (MARC Center).

## What it demonstrates

A running ROS2 computation node migrates from the PT role to the DT role without stopping the data producer. The migration gap is measured automatically. Three modes are implemented with increasing autonomy.

## Dashboard

![Dashboard](dashboard.png)

Live web dashboard at `http://127.0.0.1:5000` showing node states, CPU/RAM gauges, gap timer, event log, and manual controls.

## Key insight

The streamer never needs to know about the new logger instance. DDS maintains a live registry of active subscribers per topic — when the PT logger deactivates and the DT logger activates on the same topic, routing happens transparently. No IP updates, no restarts, no reconfiguration on the producer side.

## Modes

| Mode | Trigger | Status |
|---|---|---|
| [Mode 1 — Manual](mode1_manual/) | Human button press | ✅ Done |
| [Mode 2 — Reactive](mode2_reactive/) | CPU/RAM threshold crossed | ✅ Done |
| Mode 3 — Proactive | Predicted overload | 🔄 Coming soon |

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
/pt/ram_usage ↗  live metrics published to dashboard
```

### Mode 3 — Proactive (coming soon)

```
resource_monitor → prediction model → /offload_trigger → offload_manager
                   (forecasts overload before threshold is crossed)
```

## Repository structure

```
Task-Offloading/
├── mode1_manual/       ← manual trigger implementation
├── mode2_reactive/     ← resource threshold implementation
└── mode3_proactive/    ← prediction-based (coming soon)
```

## Setup

```bash
cd ~/workspaces/acc_ws
colcon build --packages-select task_offloading
source install/setup.bash
```

