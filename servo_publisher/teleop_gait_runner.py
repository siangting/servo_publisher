#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import String

import yaml
import time
import threading
import os


class TeleopGaitRunner(Node):
    def __init__(self):
        super().__init__("teleop_gait_runner")

        # =============== ROS Parameters ====================
        self.declare_parameter("gait_file", "three_joints_six_leg_gait.yaml")
        self.declare_parameter("command_map_file", "command_map.yaml")
        self.declare_parameter("interval", 0.3)

        gait_path = self.get_parameter("gait_file").get_parameter_value().string_value
        command_map_path = self.get_parameter("command_map_file").get_parameter_value().string_value
        self.interval = self.get_parameter("interval").get_parameter_value().double_value

        # =============== Load GAIT YAML ==========================
        if not os.path.exists(gait_path):
            self.get_logger().error(f"Gait file not found: {gait_path}")
            raise SystemExit

        with open(gait_path, "r") as f:
            self.gait_data = yaml.safe_load(f)

        # =============== Load COMMAND MAP YAML ====================
        if not os.path.exists(command_map_path):
            self.get_logger().error(f"Command map file not found: {command_map_path}")
            raise SystemExit

        with open(command_map_path, "r") as f:
            self.command_map = yaml.safe_load(f).get("command_map", {})

        if not self.command_map:
            self.get_logger().error("command_map.yaml did not contain 'command_map'")
            raise SystemExit

        # =============== ROS Publisher ======================
        self.pub = self.create_publisher(JointTrajectory, "/servo_trajectory", 10)

        # =============== ROS Subscriber ======================
        self.sub_cmd = self.create_subscription(
            String,
            "/teleop_cmd",
            self.cmd_callback,
            10
        )

        # =============== Current Command ====================
        self.current_cmd = "stop"

        # =============== Worker Thread ======================
        self.action_thread = threading.Thread(target=self.action_loop, daemon=True)
        self.action_thread.start()

        self.get_logger().info("Teleop Ready! Listening to /teleop_cmd")

    # ------------------------------------------------------
    # RECEIVE COMMAND FROM JOYSTICK NODE
    # ------------------------------------------------------
    def cmd_callback(self, msg: String):
        cmd = msg.data.strip()

        if cmd in self.command_map:
            self.current_cmd = cmd
            self.get_logger().info(f"[CMD] {cmd}")
        else:
            self.get_logger().warn(f"Unknown command: {cmd}")

    # ------------------------------------------------------
    # ACTION LOOP (continuous)
    # ------------------------------------------------------
    def action_loop(self):
        while True:
            self.run_gait(self.current_cmd)

    # ------------------------------------------------------
    # EXECUTE GAIT
    # ------------------------------------------------------
    def run_gait(self, cmd):
        if cmd not in self.command_map:
            return

        yaml_key = self.command_map[cmd]
        poses = self.gait_data.get(yaml_key, None)
        if poses is None:
            return

        for pose in poses:
            if cmd != self.current_cmd:
                return  # user switched command mid-way

            pose_f = [float(x) for x in pose]

            msg = JointTrajectory()
            msg.joint_names = [f"servo_{i+1}" for i in range(len(pose_f))]
            pt = JointTrajectoryPoint()
            pt.positions = pose_f
            pt.time_from_start.sec = 1
            msg.points.append(pt)

            self.pub.publish(msg)
            time.sleep(self.interval)


# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------
def main():
    rclpy.init()
    node = TeleopGaitRunner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
