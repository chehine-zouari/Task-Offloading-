import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from flask import Flask, render_template, jsonify, request
import threading
import time

import os
from ament_index_python.packages import get_package_share_directory
template_dir = os.path.join(
    get_package_share_directory('task_offloading'), 'templates')
app = Flask(__name__, template_folder=template_dir)

# shared state
state = {
    'streamer_count': 0,
    'pt_status': 'INACTIVE',
    'dt_status': 'INACTIVE',
    'cpu': 0.0,
    'ram': 0.0,
    'last_trigger': None,
    'gap_duration': None,
    'gap_start': None,
    'events': []
}

ros_node = None

def add_event(msg):
    ts = time.strftime('%H:%M:%S')
    state['events'].insert(0, f'[{ts}] {msg}')
    state['events'] = state['events'][:20]  # keep last 20

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/state')
def get_state():
    return jsonify(state)

@app.route('/trigger', methods=['POST'])
def trigger():
    direction = request.json.get('direction', 'PT_TO_DT')
    if ros_node:
        msg = String()
        msg.data = 'OFFLOAD_LOGGER' if direction == 'PT_TO_DT' else 'OFFLOAD_BACK_LOGGER'
        ros_node.trigger_pub.publish(msg)
        add_event(f'Manual trigger fired — {direction}')
    return jsonify({'ok': True})

class DashboardNode(Node):
    def __init__(self):
        super().__init__('dashboard_node')
        global ros_node
        ros_node = self

        self.trigger_pub = self.create_publisher(
            String, '/offload_trigger', 10)

        self.create_subscription(
            String, '/data/stream', self.on_stream, 10)
        self.create_subscription(
            Float32, '/pt/cpu_usage', self.on_cpu, 10)
        self.create_subscription(
            Float32, '/pt/ram_usage', self.on_ram, 10)
        self.create_subscription(
            String, '/offload_trigger', self.on_trigger, 10)
        self.create_subscription(
            String, '/logger/status', self.on_pt_status, 10)
        self.create_subscription(
            String, '/logger_dt/status', self.on_dt_status, 10)

        self.get_logger().info(
            'Dashboard node started — open http://127.0.0.1:5000')

    def on_stream(self, msg):
        state['streamer_count'] += 1

    def on_cpu(self, msg):
        state['cpu'] = round(msg.data, 1)

    def on_ram(self, msg):
        state['ram'] = round(msg.data, 1)

    def on_trigger(self, msg):
        state['last_trigger'] = msg.data
        if msg.data == 'OFFLOAD_LOGGER':
            state['gap_start'] = time.time()
            state['gap_duration'] = None
            add_event('Offload triggered — PT → DT — GAP BEGINS')
        elif msg.data == 'OFFLOAD_BACK_LOGGER':
            state['gap_start'] = time.time()
            state['gap_duration'] = None
            add_event('Reverse offload triggered — DT → PT — GAP BEGINS')

    def on_pt_status(self, msg):
        state['pt_status'] = msg.data
        if msg.data == 'ACTIVE' and state.get('gap_start'):
            gap = round(time.time() - state['gap_start'], 3)
            state['gap_duration'] = gap
            state['gap_start'] = None
            add_event(f'PT logger ACTIVE — GAP CLOSED ({gap}s)')
        add_event(f'PT logger → {msg.data}')

    def on_dt_status(self, msg):
        state['dt_status'] = msg.data
        if msg.data == 'ACTIVE' and state.get('gap_start'):
            gap = round(time.time() - state['gap_start'], 3)
            state['gap_duration'] = gap
            state['gap_start'] = None
            add_event(f'DT logger ACTIVE — GAP CLOSED ({gap}s)')
        add_event(f'DT logger → {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    node = DashboardNode()

    # run flask in background thread
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=5000, debug=False),
        daemon=True)
    flask_thread.start()

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
