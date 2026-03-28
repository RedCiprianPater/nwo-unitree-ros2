from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='nwo_unitree_bridge',
            executable='api_bridge_node',
            name='nwo_unitree_bridge',
            output='screen',
            parameters=[
                {'use_sim_time': False}
            ]
        )
    ])
