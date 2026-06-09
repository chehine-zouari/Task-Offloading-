import rclpy
from rclpy.node import Node
import signal
import sys

# intensity → MB to allocate
ALLOC_MAP = {
    1: 1024,    # ~1GB  → crosses offload threshold (30%)
    2: 5120,    # ~5GB  → crosses warning threshold (60%)
    3: 8192,    # ~8GB  → crosses critical threshold (80%)
}

class RamStress(Node):
    def __init__(self, intensity=1):
        super().__init__('ram_stress')
        mb = ALLOC_MAP.get(intensity, 1024)
        self.get_logger().info(
            f'RAM stress started — allocating ~{mb}MB (intensity {intensity}x)')
        self.data = [' ' * 1024 * 1024 for _ in range(mb)]
        self.get_logger().info(
            f'Allocated ~{mb}MB — RAM should be spiking')

    def release(self):
        self.data = []
        self.get_logger().info('RAM released — memory freed')

def main(args=None):
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    rclpy.init(args=args)

    node = rclpy.create_node('_tmp')
    node.declare_parameter('intensity', 1)
    intensity = node.get_parameter('intensity').value
    node.destroy_node()

    node = RamStress(intensity=intensity)
    try:
        rclpy.spin(node)
    except Exception:
        pass
    node.release()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
