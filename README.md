# NWO-Unitree-ROS2 Integration

Official ROS2 bridge integration for Unitree G1 humanoid robots with NWO Robotics API.

## Overview

This package provides a seamless bridge between Unitree's G1 humanoid robot and the NWO Robotics cloud API, enabling natural language control, VLA inference, and multi-agent coordination for the world's most deployed humanoid platform.

**Unitree G1 Stats:**
- 5,500+ units shipped in 2025
- 10,000-20,000 units projected for 2026
- Full ROS2 support with Jetson Orin
- Python/C++ SDK included
- Price: ~$16,000 (EDU version)

## What's Included

- **nwo_unitree_bridge**: ROS2 node that bridges G1's ROS2 topics to NWO API
- **WebSocket streaming**: Real-time telemetry and command streaming
- **VLA inference**: Cloud-based Vision-Language-Action processing
- **Multi-agent support**: Coordinate multiple G1 units via NWO swarm API
- **Safety layer**: Hardware-level safety integration with G1's built-in protections

## Installation

### Prerequisites

- Unitree G1 robot with ROS2 Humble
- Jetson Orin or compatible compute
- Python 3.8+
- ROS2 Humble installed

### Quick Install

```bash
# Clone the repository
cd ~/ros2_ws/src
git clone https://github.com/nwo-robotics/nwo-unitree-ros2.git

# Install dependencies
cd nwo-unitree-ros2
pip install -r requirements.txt

# Build the package
cd ~/ros2_ws
colcon build --packages-select nwo_unitree_bridge

# Source the workspace
source install/setup.bash
```

### Configuration

Create a config file at `~/.nwo/config.yaml`:

```yaml
nwo_api:
  base_url: "https://nwo.capital/webapp"
  api_key: "your_api_key_here"
  
unitree_g1:
  robot_id: "g1_001"
  ros_namespace: "/unitree_g1"
  
streaming:
  enabled: true
  websocket_url: "wss://nwo-ros2-bridge.onrender.com"
  telemetry_rate: 30  # Hz
```

## Usage

### Start the Bridge

```bash
# Launch the NWO-Unitree bridge
ros2 launch nwo_unitree_bridge nwo_bridge.launch.py

# Or run individual components
ros2 run nwo_unitree_bridge api_bridge_node
ros2 run nwo_unitree_bridge websocket_node
```

### Send Natural Language Commands

```python
import rclpy
from nwo_unitree_bridge import NWOCommandClient

node = rclpy.create_node('g1_controller')
client = NWOCommandClient(node)

# Simple command
client.send_command("Walk forward 2 meters")

# Complex task with context
client.send_command(
    instruction="Pick up the red box and place it on the table",
    image_topic="/unitree_g1/camera/color/image_raw",
    use_vla=True
)

# Multi-step task
client.send_command("Navigate to the kitchen, open the fridge, get a bottle")
```

### Subscribe to Action Output

```python
from nwo_unitree_bridge import NWOActionSubscriber

subscriber = NWOActionSubscriber(node)
subscriber.subscribe("/nwo/actions", callback=on_action_received)

def on_action_received(action_msg):
    # action_msg contains joint targets, gripper commands, etc.
    print(f"Received action: {action_msg.action_type}")
    print(f"Joint targets: {action_msg.joint_positions}")
```

## ROS2 Topics

### Input Topics (from G1)

| Topic | Type | Description |
|-------|------|-------------|
| `/joint_states` | sensor_msgs/JointState | Joint positions, velocities, efforts |
| `/camera/color/image_raw` | sensor_msgs/Image | RGB camera feed |
| `/camera/depth/image_rect_raw` | sensor_msgs/Image | Depth camera feed |
| `/imu/data` | sensor_msgs/Imu | IMU data |
| `/odom` | nav_msgs/Odometry | Odometry data |

### Output Topics (from NWO)

| Topic | Type | Description |
|-------|------|-------------|
| `/nwo/actions` | nwo_msgs/Action | Generated actions from VLA |
| `/nwo/waypoints` | nav_msgs/Path | Navigation waypoints |
| `/nwo/gripper_cmd` | std_msgs/Float64 | Gripper position commands |
| `/nwo/status` | nwo_msgs/Status | API connection status |

## API Integration

### Direct API Calls

```python
import requests

# Send proprioceptive state and get actions
response = requests.post(
    "https://nwo.capital/webapp/api-robot-v2.php",
    headers={"X-API-Key": "your_key"},
    json={
        "agent_id": "g1_001",
        "instruction": "Wave hello",
        "proprioception": {
            "joint_angles": [0.1, -0.5, 1.2, ...],  # 23 joints
            "end_effector_pose": {"x": 0.5, "y": 0.2, "z": 1.0, ...},
            "gripper_state": {"position": 0.0, "force": 0.0}
        },
        "image_url": "http://g1.local/camera/latest.jpg"
    }
)

actions = response.json()
```

### WebSocket Streaming

```python
import asyncio
import websockets
import json

async def stream_telemetry():
    uri = "wss://nwo-ros2-bridge.onrender.com"
    async with websockets.connect(uri) as websocket:
        # Authenticate
        await websocket.send(json.dumps({
            "type": "auth",
            "api_key": "your_key",
            "agent_id": "g1_001"
        }))
        
        # Stream telemetry
        while True:
            telemetry = {
                "type": "telemetry",
                "joint_states": get_joint_states(),
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(telemetry))
            
            # Receive actions
            response = await websocket.recv()
            action = json.loads(response)
            execute_action(action)
            
            await asyncio.sleep(0.033)  # 30 Hz
```

## Multi-Agent Swarm

Coordinate multiple G1 robots:

```python
from nwo_unitree_bridge import NWOSwarmClient

# Create a swarm
swarm = NWOSwarmClient("warehouse_team_a")
swarm.create_swarm(strategy="divide_and_conquer")

# Add G1 units
swarm.add_agent("g1_001", role="picker")
swarm.add_agent("g1_002", role="picker")
swarm.add_agent("g1_003", role="transporter")

# Assign coordinated task
swarm.assign_task(
    task="Sort packages by destination",
    agents=["g1_001", "g1_002", "g1_003"]
)
```

## Safety Integration

The bridge integrates with G1's hardware safety systems:

```python
# Configure safety limits
safety_config = {
    "max_joint_velocity": 2.0,  # rad/s
    "max_joint_torque": 50.0,   # Nm
    "collision_threshold": 5.0,  # N
    "human_proximity_stop": 0.5  # meters
}

# Enable safety monitoring
bridge.enable_safety_monitoring(safety_config)
```

## Examples

### Example 1: Hello World

```python
#!/usr/bin/env python3
"""Basic G1 control via NWO API."""

import rclpy
from nwo_unitree_bridge import NWOCommandClient

def main():
    rclpy.init()
    node = rclpy.create_node('g1_hello')
    
    client = NWOCommandClient(node)
    
    # Simple greeting
    client.send_command("Wave hello")
    
    # Wait for completion
    rclpy.spin_once(node, timeout_sec=5.0)
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Example 2: Pick and Place

```python
#!/usr/bin/env python3
"""Pick and place with VLA inference."""

import rclpy
from nwo_unitree_bridge import NWOCommandClient, NWOActionSubscriber

class PickPlaceController:
    def __init__(self):
        self.node = rclpy.create_node('g1_pick_place')
        self.client = NWOCommandClient(self.node)
        self.subscriber = NWOActionSubscriber(self.node)
        
        self.subscriber.subscribe("/nwo/actions", self.on_action)
        
    def on_action(self, msg):
        # Convert NWO actions to G1 joint commands
        if msg.action_type == "gripper":
            self.set_gripper(msg.gripper_position)
        elif msg.action_type == "arm":
            self.set_arm_joints(msg.joint_positions)
            
    def pick_object(self, object_name):
        self.client.send_command(
            instruction=f"Pick up the {object_name}",
            image_topic="/camera/color/image_raw",
            use_vla=True
        )
        
    def place_object(self, location):
        self.client.send_command(
            instruction=f"Place it on the {location}",
            use_vla=True
        )

def main():
    rclpy.init()
    controller = PickPlaceController()
    
    controller.pick_object("red box")
    rclpy.spin(controller.node)
    
if __name__ == '__main__':
    main()
```

### Example 3: Navigation

```python
#!/usr/bin/env python3
"""Navigate G1 using NWO API."""

import rclpy
from nwo_unitree_bridge import NWONavigationClient

def main():
    rclpy.init()
    node = rclpy.create_node('g1_navigate')
    
    nav = NWONavigationClient(node)
    
    # Navigate to location
    nav.navigate_to("kitchen")
    
    # Or use coordinates
    nav.navigate_to_coordinates(x=5.0, y=3.0, theta=1.57)
    
    rclpy.spin(node)
    
if __name__ == '__main__':
    main()
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Unitree G1 Robot                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   ROS2 Humble │  │  Jetson Orin │  │   Sensors    │      │
│  │   (unitree_ros2)│  │  (Compute)   │  │  (Cam/IMU)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
                    ┌───────▼───────┐
                    │  nwo_unitree  │
                    │    _bridge    │
                    │  (ROS2 Node)  │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │  WebSocket   │ │  REST API   │ │   Swarm     │
    │   Stream     │ │   Client    │ │   Coord     │
    └───────┬──────┘ └──────┬──────┘ └──────┬──────┘
            │               │               │
            └───────────────┼───────────────┘
                            │
              ┌─────────────▼─────────────┐
              │    NWO Robotics Cloud     │
              │  (VLA Inference + API)    │
              └───────────────────────────┘
```

## Troubleshooting

### Connection Issues

```bash
# Check ROS2 topics
ros2 topic list | grep unitree

# Test API connectivity
curl -H "X-API-Key: your_key" \
  https://nwo.capital/webapp/api-robot-v2.php?action=health

# View bridge logs
ros2 run nwo_unitree_bridge api_bridge_node --ros-args --log-level debug
```

### Performance Tuning

```yaml
# config.yaml optimizations
streaming:
  telemetry_rate: 30  # Reduce if bandwidth limited
  compression: true   # Enable image compression
  
inference:
  cache_actions: true  # Cache common actions
  batch_size: 4        # Batch multiple requests
```

## Support

- **Documentation**: https://nwo.capital/webapp/nwo-robotics.html
- **API Reference**: https://nwo.capital/webapp/api-robot-v2.php
- **Issues**: https://github.com/nwo-robotics/nwo-unitree-ros2/issues
- **Discord**: https://discord.gg/nwo-robotics

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- Unitree Robotics for the G1 platform
- NWO Robotics for the cloud VLA API
- ROS2 community for the robotics framework
