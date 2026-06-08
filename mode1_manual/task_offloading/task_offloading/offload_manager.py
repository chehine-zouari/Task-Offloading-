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
            self.get_logger().info('Trigger received — PT → DT offload')
            self.offload_pt_to_dt()
        elif msg.data == 'OFFLOAD_BACK_LOGGER':
            self.get_logger().info('Trigger received — DT → PT reverse offload')
            self.offload_dt_to_pt()

    def offload_pt_to_dt(self):
        # Step 1 — deactivate PT instance
        t0 = time.time()
        result = subprocess.run(
            ['ros2', 'lifecycle', 'set', '/logger', 'deactivate'],
            capture_output=True, text=True)
        if result.returncode != 0:
            self.get_logger().error('PT deactivation FAILED — ' + result.stderr)
            return
        self.get_logger().info(
            f'PT logger deactivated — GAP BEGINS at t0={t0:.3f}')

        # Step 2 — spawn DT instance
        subprocess.Popen([
            'ros2', 'run', 'task_offloading', 'logger',
            '--ros-args', '-r', '__node:=logger_dt'
        ])
        time.sleep(2.0)

        # Step 3 — configure and activate DT instance
        subprocess.run(
            ['ros2', 'lifecycle', 'set', '/logger_dt', 'configure'],
            capture_output=True, text=True)
        subprocess.run(
            ['ros2', 'lifecycle', 'set', '/logger_dt', 'activate'],
            capture_output=True, text=True)
        t1 = time.time()
        self.get_logger().info(
            f'DT logger active — GAP CLOSED — duration={t1-t0:.3f}s')

    def offload_dt_to_pt(self):
        # Step 1 — deactivate DT instance
        t0 = time.time()
        result = subprocess.run(
            ['ros2', 'lifecycle', 'set', '/logger_dt', 'deactivate'],
            capture_output=True, text=True)
        if result.returncode != 0:
            self.get_logger().error('DT deactivation FAILED — ' + result.stderr)
            return
        self.get_logger().info(
            f'DT logger deactivated — GAP BEGINS at t0={t0:.3f}')

        # Step 2 — reactivate PT instance
        subprocess.run(
            ['ros2', 'lifecycle', 'set', '/logger', 'activate'],
            capture_output=True, text=True)
        t1 = time.time()
        self.get_logger().info(
            f'PT logger reactivated — GAP CLOSED — duration={t1-t0:.3f}s')

def main(args=None):
    rclpy.init(args=args)
    node = OffloadManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

