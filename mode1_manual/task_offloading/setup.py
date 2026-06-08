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
    ],
},
)
