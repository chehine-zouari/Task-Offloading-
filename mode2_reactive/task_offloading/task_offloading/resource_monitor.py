import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
import psutil
import time

CPU_UPPER = 20.0
CPU_LOWER = 10.0
RAM_UPPER = 30.0
RAM_LOWER = 28.0
CHECK_INTERVAL = 2.0
COOLDOWN = 30.0

CPU_WARNING = 70.0
CPU_CRITICAL = 90.0
RAM_WARNING = 60.0
RAM_CRITICAL = 80.0

class ResourceMonitor(Node):
    def __init__(self):
        super().__init__('resource_monitor')
        self.trigger_pub = self.create_publisher(
            String, '/offload_trigger', 10)
        self.cpu_pub = self.create_publisher(
            Float32, '/pt/cpu_usage', 10)
        self.ram_pub = self.create_publisher(
            Float32, '/pt/ram_usage', 10)
        self.reason_pub = self.create_publisher(
            String, '/offload_reason', 10)

        # non-blocking first call to initialize psutil cache
        psutil.cpu_percent(interval=None)

        self.timer = self.create_timer(CHECK_INTERVAL, self.check_resources)
        self.offloaded = False
        self.last_offload_time = 0.0
        # track last logged level: None, 'warning', 'critical'
        self.last_logged = {'cpu': None, 'ram': None}
        self.get_logger().info(
            f'Resource monitor started — '
            f'CPU upper: {CPU_UPPER}% lower: {CPU_LOWER}% | '
            f'RAM upper: {RAM_UPPER}% lower: {RAM_LOWER}% | '
            f'Cooldown: {COOLDOWN}s'
        )

    def check_resources(self):
        # Issue 4 fix — non-blocking, uses cached value from last interval
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        self.cpu_pub.publish(Float32(data=cpu))
        self.ram_pub.publish(Float32(data=ram))
        self.get_logger().info(
            f'CPU: {cpu}% | RAM: {ram}% | '
            f'Active: {"DT" if self.offloaded else "PT"}'
        )

        # Issue 3 fix — track level separately so CRITICAL overrides WARNING
        self._check_safety('cpu', cpu, CPU_WARNING, CPU_CRITICAL)
        self._check_safety('ram', ram, RAM_WARNING, RAM_CRITICAL)

        # Issue 2 fix — reset health when metrics drop below warning thresholds
        if cpu < CPU_WARNING and ram < RAM_WARNING:
            if self.last_logged['cpu'] or self.last_logged['ram']:
                self._publish_reason('System healthy — metrics back to normal')
                self.last_logged['cpu'] = None
                self.last_logged['ram'] = None

        # cooldown check
        now = time.time()
        if now - self.last_offload_time < COOLDOWN:
            remaining = round(COOLDOWN - (now - self.last_offload_time), 1)
            self.get_logger().info(f'Cooldown active — {remaining}s remaining')
            return

        # offload PT → DT — fires on CPU OR RAM crossing upper threshold
        if not self.offloaded:
            cpu_over = cpu > CPU_UPPER
            ram_over = ram > RAM_UPPER
            if cpu_over or ram_over:
                reasons = []
                if cpu_over:
                    reasons.append(f'CPU {cpu}%')
                if ram_over:
                    reasons.append(f'RAM {ram}%')
                reason_str = ' AND '.join(reasons) + ' — threshold crossed'
                self.get_logger().warn(
                    f'THRESHOLD CROSSED ({reason_str}) — offloading PT → DT')
                self._publish_trigger('OFFLOAD_LOGGER')
                self._publish_reason(reason_str)
                self.offloaded = True
                self.last_offload_time = now

        # Issue 5 fix — recovery uses CPU only
        # RAM baseline too high on this machine to reliably drop below RAM_LOWER
        elif self.offloaded:
            if cpu < CPU_LOWER:
                self.get_logger().warn(
                    f'CPU RECOVERED ({cpu}%) — offloading back DT → PT')
                self._publish_trigger('OFFLOAD_BACK_LOGGER')
                self._publish_reason(
                    f'CPU recovered to {cpu}% — offloading back DT → PT')
                self.offloaded = False
                self.last_offload_time = now

    def _check_safety(self, metric, val, warn_thresh, crit_thresh):
        if val > crit_thresh:
            # always log CRITICAL even if WARNING was already logged
            if self.last_logged[metric] != 'critical':
                self._publish_reason(
                    f'CRITICAL: {metric.upper()} at {val}% '
                    f'— immediate offload recommended')
                self.last_logged[metric] = 'critical'
        elif val > warn_thresh:
            # only log WARNING if nothing was logged yet
            if self.last_logged[metric] is None:
                self._publish_reason(
                    f'WARNING: {metric.upper()} at {val}% '
                    f'— consider offloading')
                self.last_logged[metric] = 'warning'
        else:
            # reset when metric drops back to normal
            self.last_logged[metric] = None

    def _publish_trigger(self, command):
        msg = String()
        msg.data = command
        self.trigger_pub.publish(msg)

    def _publish_reason(self, reason):
        msg = String()
        msg.data = reason
        self.reason_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ResourceMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
