import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class StreamerNode(Node):
    def __init__(self):
        super().__init__('streamer_node')
        self.publisher = self.create_publisher(String, '/data/stream', 10)
        self.timer = self.create_timer(1.0, self.publish_data)
        self.count = 0
        self.get_logger().info('StreamerNode started — publishing to /data/stream')

    def publish_data(self):
        msg = String()
        msg.data = f'data packet {self.count}'
        self.publisher.publish(msg)
        self.count += 1
        self.get_logger().info(f'Streamer sent: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(StreamerNode())

if __name__ == '__main__':
    main()

