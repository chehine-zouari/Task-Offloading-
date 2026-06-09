# Mode 2: Reactive Task Offloading

## Overview
Resource threshold-triggered offloading with bidirectional migration. A monitor watches CPU and RAM continuously and fires the offload automatically when either crosses a threshold, no human intervention needed. Supports automatic recovery (DT→PT) when CPU drops below the lower threshold.

## New Nodes
| Node | Role |
|---|---|
| `resource_monitor.py` | Watches CPU/RAM, fires trigger automatically, publishes safety warnings |
| `cpu_stress.py` | Simulates PT CPU overload (3 intensity levels) |
| `ram_stress.py` | Simulates PT RAM overload (3 intensity levels) |

## Thresholds
| Metric | Offload trigger | Recovery trigger |
|---|---|---|
| CPU | > 20% | < 10% (used for recovery) |
| RAM | > 30% | — (RAM baseline too high for reliable recovery) |

## Safety Warnings
| Level | CPU | RAM |
|---|---|---|
| Warning | > 70% | > 60% |
| Critical | > 90% | > 80% |

Warnings appear once per spike on the dashboard health bar, not repeated every cycle.

## Stress Intensity Levels
| Intensity | CPU target | RAM allocation |
|---|---|---|
| 1x | ~35% | ~1GB |
| 2x | ~70% | ~5GB |
| 3x | ~95% | ~8GB |

## Key Design Decisions
- Offload fires on either CPU **or** RAM crossing upper threshold
- Recovery uses **CPU only**, RAM baseline on this machine sits too close to the upper threshold for reliable automatic recovery
- **30s cooldown** after any offload before the next one can fire, prevents flapping
- **Lock-protected offload manager**, concurrent triggers are ignored while an offload is in progress
- Stress controlled entirely from the dashboard, no terminal commands needed

## How to Run
Source first in every terminal:
```bash
cd ~/workspaces/acc_ws && source install/setup.bash
```

**Base setup — same as Mode 1:**
```bash
# T1
ros2 run task_offloading streamer

# T2
ros2 run task_offloading logger

# T3
ros2 lifecycle set /logger configure
ros2 lifecycle set /logger activate

# T4
ros2 run task_offloading offload_manager

# T5
ros2 run task_offloading dashboard_node
```

**Mode 2 extras:**
```bash
# T6: resource monitor (replaces manual trigger)
ros2 run task_offloading resource_monitor
```
Open dashboard at http://127.0.0.1:5000 and use the **Mode 2 Reactive Controls** section to start CPU/RAM stress at any intensity level.

## Verify
```bash
ros2 lifecycle get /logger        # inactive: PT preserved
ros2 lifecycle get /logger_dt     # active: DT running
```

## Next
- Mode 3: Proactive offloading (prediction-triggered)
