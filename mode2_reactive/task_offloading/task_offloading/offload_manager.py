import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import time
import threading

class OffloadManager(Node):
    def __init__(self):
        super().__init__('offload_manager')
        self.subscription = self.create_subscription(
            String, '/offload_trigger', self.trigger_callback, 10)
        self._lock = threading.Lock()
        self._busy = False
        self.get_logger().info('Offload manager ready — waiting for trigger')

    def trigger_callback(self, msg):
        if self._busy:
            self.get_logger().warn(
                f'Offload in progress — ignoring trigger: {msg.data}')
            return
        if msg.data == 'OFFLOAD_LOGGER':
            self.get_logger().info('Trigger received — PT → DT offload')
            t = threading.Thread(target=self.offload_pt_to_dt, daemon=True)
            t.start()
        elif msg.data == 'OFFLOAD_BACK_LOGGER':
            self.get_logger().info('Trigger received — DT → PT reverse offload')
            t = threading.Thread(target=self.offload_dt_to_pt, daemon=True)
            t.start()

    def offload_pt_to_dt(self):
        with self._lock:
            self._busy = True
            try:
                t0 = time.time()
                result = subprocess.run(
                    ['ros2', 'lifecycle', 'set', '/logger', 'deactivate'],
                    capture_output=True, text=True)
                if result.returncode != 0:
                    self.get_logger().error(
                        'PT deactivation FAILED — ' + result.stderr)
                    return
                self.get_logger().info(
                    f'PT logger deactivated — GAP BEGINS at t0={t0:.3f}')

                subprocess.Popen([
                    'ros2', 'run', 'task_offloading', 'logger',
                    '--ros-args', '-r', '__node:=logger_dt'
                ])
                time.sleep(2.0)

                subprocess.run(
                    ['ros2', 'lifecycle', 'set', '/logger_dt', 'configure'],
                    capture_output=True, text=True)
                subprocess.run(
                    ['ros2', 'lifecycle', 'set', '/logger_dt', 'activate'],
                    capture_output=True, text=True)
                t1 = time.time()
                self.get_logger().info(
                    f'DT logger active — GAP CLOSED — duration={t1-t0:.3f}s')
            finally:
                self._busy = False

    def offload_dt_to_pt(self):
        with self._lock:
            self._busy = True
            try:
                t0 = time.time()
                result = subprocess.run(
                    ['ros2', 'lifecycle', 'set', '/logger_dt', 'deactivate'],
                    capture_output=True, text=True)
                if result.returncode != 0:
                    self.get_logger().error(
                        'DT deactivation FAILED — ' + result.stderr)
                    return
                self.get_logger().info(
                    f'DT logger deactivated — GAP BEGINS at t0={t0:.3f}')

                subprocess.run(
                    ['ros2', 'lifecycle', 'set', '/logger', 'activate'],
                    capture_output=True, text=True)
                t1 = time.time()
                self.get_logger().info(
                    f'PT logger reactivated — GAP CLOSED — duration={t1-t0:.3f}s')
            finally:
                self._busy = False

def main(args=None):
    rclpy.init(args=args)
    node = OffloadManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
