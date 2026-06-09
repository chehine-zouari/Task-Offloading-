from setuptools import find_packages, setup

package_name = 'task_offloading'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/templates',
            ['task_offloading/templates/dashboard.html']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='maccity',
    maintainer_email='zouarm1@mcmaster.ca',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'streamer = task_offloading.streamer:main',
        'logger = task_offloading.logger:main',
        'offload_manager = task_offloading.offload_manager:main',
        'resource_monitor = task_offloading.resource_monitor:main',
        'cpu_stress = task_offloading.cpu_stress:main',
        'ram_stress = task_offloading.ram_stress:main',
        'dashboard_node = task_offloading.dashboard_node:main',
    ],
},
)
