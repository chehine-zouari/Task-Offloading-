import rclpy
from rclpy.lifecycle import LifecycleNode, TransitionCallbackReturn
from std_msgs.msg import String

class LoggerNode(LifecycleNode):
    def __init__(self):
        super().__init__('logger')
        self._sub = None

    def on_configure(self, state):
        self._sub = self.create_subscription(
            String, '/data/stream', self.on_data, 10)
        self.get_logger().info('Logger CONFIGURED — subscription created')
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state):
        self.get_logger().info('Logger ACTIVATED — receiving data')
        return super().on_activate(state)

    def on_deactivate(self, state):
        # destroy subscription so data flow stops immediately
        self.destroy_subscription(self._sub)
        self._sub = None
        self.get_logger().info('Logger DEACTIVATED — subscription destroyed, GAP BEGINS')
        return super().on_deactivate(state)

    def on_cleanup(self, state):
        self._sub = None
        return TransitionCallbackReturn.SUCCESS

    def on_data(self, msg):
        self.get_logger().info(f'Logger received: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(LoggerNode())

if __name__ == '__main__':
    main()
