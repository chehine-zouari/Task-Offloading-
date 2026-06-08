import rclpy
from rclpy.node import Node

class RamStress(Node):
    def __init__(self):
        super().__init__('ram_stress')
        self.get_logger().info('RAM stress started — allocating memory...')
        self.data = []
        for _ in range(500):
            self.data.append(' ' * 1024 * 1024)  # 1MB chunks = ~500MB total
        self.get_logger().info('Allocated ~500MB — RAM should be spiking')

def main(args=None):
    rclpy.init(args=args)
    node = RamStress()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

