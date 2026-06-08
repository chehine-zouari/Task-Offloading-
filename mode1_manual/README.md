# Mode 1: Manual Task Offloading

## Overview
A human-triggered proof-of-concept that offloads a running ROS2 node from the Physical Twin (PT) role to the Digital Twin (DT) role within the same ROS2 environment. The migration gap is measured automatically.

## Nodes
| Node | Role |
|---|---|
| `streamer.py` | Publishes data to `/data/stream` continuously, never changes |
| `logger.py` | Lifecycle node, the offloadable computation |
| `offload_manager.py` | Orchestrates deactivation, respawn, and gap measurement |

## How to Run
Source first in every terminal:
```bash
cd ~/workspaces/acc_ws && source install/setup.bash
```
Then in order:
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

# T5 — fire the trigger
ros2 topic pub --once /offload_trigger std_msgs/msg/String "data: 'OFFLOAD_LOGGER'"
```

## Verify
```bash
ros2 lifecycle get /logger      # inactive — PT preserved
ros2 lifecycle get /logger_dt   # active — DT running
```

## Key Design Decision
The streamer never changes. DDS automatically routes `/data/stream` to whichever logger instance is currently active, no IP updates, no restarts, no reconfiguration on the producer side.

## Next
- Mode 2: Reactive offloading (resource threshold-triggered)
- Mode 3: Proactive offloading (prediction-triggered)
