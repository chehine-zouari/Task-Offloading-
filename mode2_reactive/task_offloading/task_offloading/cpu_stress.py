import rclpy
from rclpy.node import Node
import threading
import math

class CpuStress(Node):
    def __init__(self):
        super().__init__('cpu_stress')
        self.get_logger().info('CPU stress started — spiking load...')
        # spin up threads to eat CPU
        for _ in range(4):
            t = threading.Thread(target=self.burn, daemon=True)
            t.start()

    def burn(self):
        # pure CPU burn loop
        while True:
            math.sqrt(12345678.9 ** 2)

def main(args=None):
    rclpy.init(args=args)
    node = CpuStress()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
