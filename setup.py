from setuptools import setup

package_name = 'nwo_unitree_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/nwo_bridge.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='NWO Robotics',
    maintainer_email='ciprian.pater@publicae.org',
    description='NWO Robotics ROS2 bridge for Unitree G1 humanoid robot',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'api_bridge_node = nwo_unitree_bridge.bridge_node:main',
        ],
    },
)
