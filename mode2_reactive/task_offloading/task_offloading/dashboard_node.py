import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from flask import Flask, render_template, jsonify, request, Response
import threading
import time
import os
import subprocess
import csv
import io
from ament_index_python.packages import get_package_share_directory

template_dir = os.path.join(
    get_package_share_directory('task_offloading'), 'templates')
app = Flask(__name__, template_folder=template_dir)

state = {
    'streamer_count': 0,
    'pt_status': 'INACTIVE',
    'dt_status': 'INACTIVE',
    'pt_last_change': None,
    'dt_last_change': None,
    'cpu': 0.0,
    'ram': 0.0,
    'last_trigger': None,
    'gap_duration': None,
    'gap_start': None,
    'gap_history': [],
    'events': [],
    'offload_reason': None,
    'cpu_stress_active': False,
    'ram_stress_active': False,
    'stress_intensity': 1,
    'total_offloads': 0,
    'pt_to_dt_count': 0,
    'dt_to_pt_count': 0,
    'avg_gap': 0.0,
    'min_gap': None,
    'max_gap': None,
    'health_status': 'healthy',
    'health_message': 'System healthy',
    'cooldown_remaining': 0.0,
}

ros_node = None
stress_procs = {'cpu': [], 'ram': []}

def add_event(msg):
    ts = time.strftime('%H:%M:%S')
    state['events'].insert(0, f'[{ts}] {msg}')
    state['events'] = state['events'][:20]

def update_stats(gap, direction):
    state['total_offloads'] += 1
    if direction == 'PT → DT':
        state['pt_to_dt_count'] += 1
    else:
        state['dt_to_pt_count'] += 1
    gaps = [g['duration'] for g in state['gap_history']]
    if gaps:
        state['avg_gap'] = round(sum(gaps) / len(gaps), 3)
        state['min_gap'] = min(gaps)
        state['max_gap'] = max(gaps)

def kill_procs(kind):
    import subprocess as sp
    node_name = 'cpu_stress' if kind == 'cpu' else 'ram_stress'
    try:
        sp.run(['pkill', '-9', '-f', node_name],
               stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    except Exception:
        pass
    for p in stress_procs[kind]:
        try:
            p.kill()
        except Exception:
            pass
    stress_procs[kind] = []

def start_stress(kind, intensity):
    kill_procs(kind)
    p = subprocess.Popen(
        ['ros2', 'run', 'task_offloading',
         'cpu_stress' if kind == 'cpu' else 'ram_stress',
         '--ros-args', '-p', f'intensity:={intensity}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    stress_procs[kind].append(p)

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
        msg.data = 'OFFLOAD_LOGGER' if direction == 'PT_TO_DT' \
            else 'OFFLOAD_BACK_LOGGER'
        ros_node.trigger_pub.publish(msg)
        add_event(f'Manual trigger fired — {direction}')
    return jsonify({'ok': True})

@app.route('/stress', methods=['POST'])
def stress():
    data = request.json
    kind = data.get('kind')
    action = data.get('action')
    intensity = data.get('intensity', 1)
    state['stress_intensity'] = intensity

    if action == 'start':
        if kind in ('cpu', 'ram'):
            start_stress(kind, intensity)
            state[f'{kind}_stress_active'] = True
            add_event(
                f'🔥 {kind.upper()} stress started — intensity {intensity}x')
        elif kind == 'both':
            start_stress('cpu', intensity)
            start_stress('ram', intensity)
            state['cpu_stress_active'] = True
            state['ram_stress_active'] = True
            add_event(
                f'⚡ CPU + RAM stress started — intensity {intensity}x')

    elif action == 'stop':
        if kind in ('cpu', 'ram'):
            kill_procs(kind)
            state[f'{kind}_stress_active'] = False
            add_event(f'⏹ {kind.upper()} stress stopped')
        elif kind in ('both', 'all'):
            kill_procs('cpu')
            kill_procs('ram')
            state['cpu_stress_active'] = False
            state['ram_stress_active'] = False
            add_event('⏹ All stress stopped')

    return jsonify({'ok': True})

@app.route('/export')
def export():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['=== SUMMARY ==='])
    writer.writerow(['Total offloads', state['total_offloads']])
    writer.writerow(['PT to DT', state['pt_to_dt_count']])
    writer.writerow(['DT to PT', state['dt_to_pt_count']])
    writer.writerow(['Avg gap (s)', state['avg_gap']])
    writer.writerow(['Min gap (s)', state['min_gap']])
    writer.writerow(['Max gap (s)', state['max_gap']])
    writer.writerow([])

    writer.writerow(['=== GAP HISTORY ==='])
    writer.writerow(['Time', 'Direction', 'Duration (s)'])
    for g in state['gap_history']:
        writer.writerow([g['time'], g['direction'], g['duration']])
    writer.writerow([])

    writer.writerow(['=== EVENT LOG ==='])
    writer.writerow(['Event'])
    for e in state['events']:
        writer.writerow([e])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition':
                f'attachment; filename=offloading_report_'
                f'{time.strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )

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
        self.create_subscription(
            String, '/offload_reason', self.on_reason, 10)

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
            add_event('⚡ PT → DT offload triggered — GAP BEGINS')
        elif msg.data == 'OFFLOAD_BACK_LOGGER':
            state['gap_start'] = time.time()
            state['gap_duration'] = None
            add_event('🔄 DT → PT recovery triggered — GAP BEGINS')

    def on_reason(self, msg):
        state['offload_reason'] = msg.data
        r = msg.data
        if 'CRITICAL' in r:
            state['health_status'] = 'critical'
            state['health_message'] = r
        elif 'WARNING' in r:
            if state['health_status'] != 'critical':
                state['health_status'] = 'warning'
                state['health_message'] = r
        elif 'healthy' in r or 'recovered' in r:
            state['health_status'] = 'healthy'
            state['health_message'] = 'System healthy'
        add_event(f'Trigger reason: {msg.data}')

    def on_pt_status(self, msg):
        state['pt_status'] = msg.data
        state['pt_last_change'] = time.strftime('%H:%M:%S')
        if msg.data == 'ACTIVE' and state.get('gap_start'):
            gap = round(time.time() - state['gap_start'], 3)
            state['gap_duration'] = gap
            state['gap_history'].insert(0, {
                'time': time.strftime('%H:%M:%S'),
                'duration': gap,
                'direction': 'DT → PT'
            })
            state['gap_history'] = state['gap_history'][:10]
            state['gap_start'] = None
            state['health_status'] = 'healthy'
            state['health_message'] = 'System healthy'
            update_stats(gap, 'DT → PT')
            add_event(f'✅ PT logger ACTIVE — GAP CLOSED ({gap}s)')
        elif msg.data == 'INACTIVE':
            add_event('🔴 PT logger INACTIVE — decommissioned')

    def on_dt_status(self, msg):
        state['dt_status'] = msg.data
        state['dt_last_change'] = time.strftime('%H:%M:%S')
        if msg.data == 'ACTIVE' and state.get('gap_start'):
            gap = round(time.time() - state['gap_start'], 3)
            state['gap_duration'] = gap
            state['gap_history'].insert(0, {
                'time': time.strftime('%H:%M:%S'),
                'duration': gap,
                'direction': 'PT → DT'
            })
            state['gap_history'] = state['gap_history'][:10]
            state['gap_start'] = None
            update_stats(gap, 'PT → DT')
            add_event(f'✅ DT logger ACTIVE — GAP CLOSED ({gap}s)')
        elif msg.data == 'INACTIVE':
            add_event('🔵 DT logger INACTIVE — standing by')

def main(args=None):
    rclpy.init(args=args)
    node = DashboardNode()
    flask_thread = threading.Thread(
        target=lambda: app.run(
            host='0.0.0.0', port=5000, debug=False),
        daemon=True)
    flask_thread.start()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
