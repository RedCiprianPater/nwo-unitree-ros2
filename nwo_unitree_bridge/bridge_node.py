#!/usr/bin/env python3
"""NWO-Unitree G1 ROS2 Bridge Node

This node bridges Unitree G1 robot ROS2 topics with NWO Robotics API.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState, Image
from std_msgs.msg import Float64, String
from nav_msgs.msg import Path
import requests
import websocket
import threading
import json
import yaml
import os
from typing import Optional, Dict, Any


class NWOUnitreeBridge(Node):
    """ROS2 node that bridges G1 to NWO API."""
    
    def __init__(self):
        super().__init__('nwo_unitree_bridge')
        
        # Load configuration
        self.config = self._load_config()
        
        # API settings
        self.api_base = self.config.get('nwo_api', {}).get('base_url', 'https://nwo.capital/webapp')
        self.api_key = self.config.get('nwo_api', {}).get('api_key', '')
        self.agent_id = self.config.get('unitree_g1', {}).get('robot_id', 'g1_001')
        
        # ROS namespace
        self.namespace = self.config.get('unitree_g1', {}).get('ros_namespace', '/unitree_g1')
        
        # Publishers
        self.action_pub = self.create_publisher(String, '/nwo/actions', 10)
        self.waypoint_pub = self.create_publisher(Path, '/nwo/waypoints', 10)
        self.gripper_pub = self.create_publisher(Float64, '/nwo/gripper_cmd', 10)
        self.status_pub = self.create_publisher(String, '/nwo/status', 10)
        
        # Subscribers
        self.joint_sub = self.create_subscription(
            JointState,
            f'{self.namespace}/joint_states',
            self._joint_callback,
            10
        )
        
        # State
        self.current_joints = {}
        self.websocket = None
        self.ws_thread = None
        
        # Start WebSocket connection
        if self.config.get('streaming', {}).get('enabled', True):
            self._start_websocket()
        
        # Timer for periodic API calls
        self.timer = self.create_timer(0.033, self._timer_callback)  # 30 Hz
        
        self.get_logger().info(f'NWO Unitree Bridge initialized for {self.agent_id}')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = os.path.expanduser('~/.nwo/config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _joint_callback(self, msg: JointState):
        """Handle joint state updates."""
        self.current_joints = {
            name: {
                'position': pos,
                'velocity': vel,
                'effort': eff
            }
            for name, pos, vel, eff in zip(msg.name, msg.position, msg.velocity, msg.effort)
        }
    
    def _start_websocket(self):
        """Start WebSocket connection for streaming."""
        ws_url = self.config.get('streaming', {}).get('websocket_url', 'wss://nwo-ros2-bridge.onrender.com')
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self._handle_ws_message(data)
            except json.JSONDecodeError:
                self.get_logger().warn(f'Invalid WebSocket message: {message}')
        
        def on_open(ws):
            self.get_logger().info('WebSocket connected')
            # Authenticate
            ws.send(json.dumps({
                'type': 'auth',
                'api_key': self.api_key,
                'agent_id': self.agent_id
            }))
        
        def run_ws():
            self.websocket = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_open=on_open
            )
            self.websocket.run_forever()
        
        self.ws_thread = threading.Thread(target=run_ws, daemon=True)
        self.ws_thread.start()
    
    def _handle_ws_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        msg_type = data.get('type')
        
        if msg_type == 'action':
            # Publish action to ROS topic
            action_msg = String()
            action_msg.data = json.dumps(data)
            self.action_pub.publish(action_msg)
            
        elif msg_type == 'waypoints':
            # Convert to Path message and publish
            path = self._waypoints_to_path(data.get('waypoints', []))
            self.waypoint_pub.publish(path)
    
    def _waypoints_to_path(self, waypoints: list) -> Path:
        """Convert waypoint list to ROS Path message."""
        from geometry_msgs.msg import PoseStamped
        
        path = Path()
        path.header.stamp = self.get_clock().now().to_msg()
        path.header.frame_id = 'map'
        
        for wp in waypoints:
            pose = PoseStamped()
            pose.header = path.header
            pose.pose.position.x = wp.get('x', 0.0)
            pose.pose.position.y = wp.get('y', 0.0)
            pose.pose.position.z = wp.get('z', 0.0)
            pose.pose.orientation.w = 1.0
            path.poses.append(pose)
        
        return path
    
    def _timer_callback(self):
        """Periodic callback for telemetry streaming."""
        if self.websocket and self.websocket.sock and self.websocket.sock.connected:
            telemetry = {
                'type': 'telemetry',
                'agent_id': self.agent_id,
                'timestamp': self.get_clock().now().to_msg().sec,
                'joint_states': self.current_joints
            }
            try:
                self.websocket.send(json.dumps(telemetry))
            except Exception as e:
                self.get_logger().warn(f'WebSocket send failed: {e}')
    
    def send_command(self, instruction: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """Send a natural language command to NWO API."""
        payload = {
            'agent_id': self.agent_id,
            'instruction': instruction,
            'proprioception': {
                'joint_angles': [
                    self.current_joints.get(f'joint_{i}', {}).get('position', 0.0)
                    for i in range(23)
                ]
            }
        }
        
        if image_url:
            payload['image_url'] = image_url
        
        try:
            response = requests.post(
                f'{self.api_base}/api-robot-v2.php',
                headers={'X-API-Key': self.api_key},
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.get_logger().error(f'API request failed: {e}')
            return {'error': str(e)}


def main(args=None):
    rclpy.init(args=args)
    node = NWOUnitreeBridge()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
