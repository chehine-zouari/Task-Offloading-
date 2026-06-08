import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
import psutil

CPU_UPPER = 20.0    # PT→DT offload threshold
CPU_LOWER = 10.0    # DT→PT reverse offload threshold
RAM_UPPER = 30.0    # trigger if RAM exceeds 30%
RAM_LOWER = 23.0    # recover when RAM drops below 23%
CHECK_INTERVAL = 2.0

class ResourceMonitor(Node):
    def __init__(self):
        super().__init__('resource_monitor')
        self.trigger_pub = self.create_publisher(
            String, '/offload_trigger', 10)
        self.cpu_pub = self.create_publisher(
            Float32, '/pt/cpu_usage', 10)
        self.ram_pub = self.create_publisher(
            Float32, '/pt/ram_usage', 10)
        self.timer = self.create_timer(CHECK_INTERVAL, self.check_resources)
        self.offloaded = False  # False = PT active, True = DT active
        self.get_logger().info(
            f'Resource monitor started — '
            f'upper threshold: {CPU_UPPER}% | '
            f'lower threshold: {CPU_LOWER}%'
        )

    def check_resources(self):
        cpu = psutil.cpu_percent(interval=1.0)
        ram = psutil.virtual_memory().percent

        self.cpu_pub.publish(Float32(data=cpu))
        self.ram_pub.publish(Float32(data=ram))
        self.get_logger().info(
            f'CPU: {cpu}% | RAM: {ram}% | '
            f'Active: {"DT" if self.offloaded else "PT"}'
        )

        if not self.offloaded and cpu > CPU_UPPER:
            self.get_logger().warn(
                f'THRESHOLD CROSSED ({cpu}%) — offloading PT → DT')
            self._publish_trigger('OFFLOAD_LOGGER')
            self.offloaded = True

        elif self.offloaded and cpu < CPU_LOWER:
            self.get_logger().warn(
                f'CPU RECOVERED ({cpu}%) — offloading back DT → PT')
            self._publish_trigger('OFFLOAD_BACK_LOGGER')
            self.offloaded = False

    def _publish_trigger(self, command):
        msg = String()
        msg.data = command
        self.trigger_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ResourceMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

