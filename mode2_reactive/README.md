# Mode 2: Reactive Task Offloading

## Overview
Resource threshold-triggered offloading. A monitor watches CPU and RAM continuously and fires the offload automatically when either crosses a threshold, no human intervention needed. Supports bidirectional migration (PT→DT and DT→PT recovery).

## New Nodes
| Node | Role |
|---|---|
| `resource_monitor.py` | Watches CPU/RAM, fires trigger automatically |
| `cpu_stress.py` | Simulates PT CPU overload |
| `ram_stress.py` | Simulates PT RAM overload |

## Thresholds
| Metric | Offload trigger | Recovery trigger |
|---|---|---|
| CPU | > 20% | < 10% |
| RAM | > 30% | < 27% |

## How to Run
Source first in every terminal:
```bash
cd ~/workspaces/acc_ws && source install/setup.bash
```

**Base setup: same as Mode 1:**
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
# T6 — resource monitor (replaces manual trigger)
ros2 run task_offloading resource_monitor

# T7 — simulate load (pick one or both)
ros2 run task_offloading cpu_stress
ros2 run task_offloading ram_stress
```

Open dashboard at `http://127.0.0.1:5000`

## Key Design Decision
Offload fires on either CPU **or** RAM threshold crossed. Recovery requires **both** to drop below lower thresholds, prevents flapping.

## Next
- Mode 3: Proactive offloading (prediction-triggered)
