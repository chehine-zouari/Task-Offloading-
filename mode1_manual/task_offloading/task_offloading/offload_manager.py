import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import time

class OffloadManager(Node):
    def __init__(self):
        super().__init__('offload_manager')
        self.subscription = self.create_subscription(
            String, '/offload_trigger', self.trigger_callback, 10)
        self.get_logger().info('Offload manager ready — waiting for trigger')

    def trigger_callback(self, msg):
        if msg.data == 'OFFLOAD_LOGGER':
            self.get_logger().info('Trigger received — starting offload sequence')
            self.run_offload()

    def run_offload(self):
        # Step 1 — deactivate PT instance, gap begins
        t0 = time.time()
        result = subprocess.run(
            ['ros2', 'lifecycle', 'set', '/logger', 'deactivate'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            self.get_logger().error('Deactivation FAILED — ' + result.stderr)
            return
        self.get_logger().info(
            f'PT logger deactivated — GAP BEGINS at t0={t0:.3f}')

        # Step 2 — spawn DT instance (127.0.0.2 role)
        subprocess.Popen([
            'ros2', 'run', 'task_offloading', 'logger',
            '--ros-args', '-r', '__node:=logger_dt'
        ])
        time.sleep(2.0)

        # Step 3 — configure and activate DT instance
        subprocess.run(
            ['ros2', 'lifecycle', 'set', '/logger_dt', 'configure'],
            capture_output=True, text=True
        )
        subprocess.run(
            ['ros2', 'lifecycle', 'set', '/logger_dt', 'activate'],
            capture_output=True, text=True
        )
        t1 = time.time()
        self.get_logger().info(
            f'DT logger active — GAP CLOSED at t1={t1:.3f} — '
            f'gap duration={t1-t0:.3f}s'
        )

def main(args=None):
    rclpy.init(args=args)
    node = OffloadManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

