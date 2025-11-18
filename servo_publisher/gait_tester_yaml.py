import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import yaml
import time
import os

class GaitTester(Node):
    def __init__(self):
        super().__init__('gait_tester_yaml')

        # 可用 ros2 param 指定 gait 檔路徑與間隔時間
        self.declare_parameter('gait_file', 'gaits.yaml')
        self.declare_parameter('interval', 0.5)

        self.pub = self.create_publisher(JointTrajectory, '/servo_trajectory', 10)

        gait_path = self.get_parameter('gait_file').get_parameter_value().string_value
        interval = self.get_parameter('interval').get_parameter_value().double_value

        if not os.path.exists(gait_path):
            self.get_logger().error(f"Gait file not found: {gait_path}")
            return

        with open(gait_path, 'r') as f:
            data = yaml.safe_load(f)

        gaits = data.get('poses', [])
        if not gaits:
            self.get_logger().error("No poses found in gait file.")
            return

        self.get_logger().info(f"Loaded {len(gaits)} poses from {gait_path}")

        # 🟡 重播 gait 檔多次
        repeat_times = 5
        for round_idx in range(repeat_times):
            self.get_logger().info(f"=== Round {round_idx+1}/{repeat_times} ===")
            for idx, gait in enumerate(gaits):
                gait_floats = [float(x) for x in gait]

                msg = JointTrajectory()
                msg.joint_names = [f"servo_{i+1}" for i in range(len(gait_floats))]
                point = JointTrajectoryPoint()
                point.positions = gait_floats
                point.time_from_start.sec = 1
                msg.points.append(point)

                self.pub.publish(msg)
                self.get_logger().info(
                    f"Round {round_idx+1} | Sent pose {idx+1}/{len(gaits)}: {gait_floats}"
                )
                time.sleep(interval)

def main():
    rclpy.init()
    node = GaitTester()
    rclpy.spin_once(node, timeout_sec=1.0)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
