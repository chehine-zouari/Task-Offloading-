# Mode 2 — Reactive Task Offloading

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
Same as Mode 1 plus two extra terminals:
```bash
# T6 — resource monitor
ros2 run task_offloading resource_monitor

# T7 — simulate load (CPU or RAM or both)
ros2 run task_offloading cpu_stress
ros2 run task_offloading ram_stress
```

## Key Design Decision
Offload fires on either CPU **or** RAM threshold crossed. Recovery requires **both** to drop below lower thresholds, prevents flapping.

## Next
- Mode 3 — Proactive offloading (prediction-triggered)
