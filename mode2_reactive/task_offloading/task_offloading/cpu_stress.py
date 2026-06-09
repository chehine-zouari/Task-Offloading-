import rclpy
from rclpy.node import Node
import multiprocessing
import math
import signal
import time
import sys

def burn(sleep_time, stop_event):
    while not stop_event.is_set():
        for _ in range(10000):
            math.sqrt(12345678.9 ** 2)
        if sleep_time > 0:
            time.sleep(sleep_time)

class CpuStress(Node):
    def __init__(self, intensity=1):
        super().__init__('cpu_stress')

        # tuned for 8-core machine using multiprocessing
        # each process gets a full core — bypasses Python GIL
        configs = {
            1: (2, 0.003),    # 2 cores → ~35%
            2: (5, 0.001),    # 5 cores → ~70%
            3: (8, 0.0),      # 8 cores → ~95%
        }
        num_procs, sleep_time = configs.get(intensity, (2, 0.003))
        self.get_logger().info(
            f'CPU stress started — intensity {intensity}x | '
            f'{num_procs} processes | sleep={sleep_time}s'
        )
        self.stop_event = multiprocessing.Event()
        self.processes = []
        for _ in range(num_procs):
            p = multiprocessing.Process(
                target=burn,
                args=(sleep_time, self.stop_event),
                daemon=True)
            p.start()
            self.processes.append(p)

    def cleanup(self):
        self.stop_event.set()
        for p in self.processes:
            p.terminate()
            p.join(timeout=2)
        self.get_logger().info('CPU stress stopped — all processes terminated')

def main(args=None):
    node = None

    def shutdown(sig, frame):
        if node:
            node.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    rclpy.init(args=args)

    tmp = rclpy.create_node('_tmp')
    tmp.declare_parameter('intensity', 1)
    intensity = tmp.get_parameter('intensity').value
    tmp.destroy_node()

    node = CpuStress(intensity=intensity)
    try:
        rclpy.spin(node)
    except Exception:
        pass
    node.cleanup()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
