#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import String, Float32

import yaml
import time
import threading
import os


class TeleopGaitRunner(Node):
    def __init__(self):
        super().__init__("teleop_gait_runner")

        # ================= ROS Parameters ====================
        self.declare_parameter("gait_file", "three_joints_six_leg_gait.yaml")
        self.declare_parameter("command_map_file", "command_map.yaml")
        self.declare_parameter("interval", 0.3)

        gait_path = self.get_parameter("gait_file").get_parameter_value().string_value
        command_map_path = self.get_parameter("command_map_file").get_parameter_value().string_value
        self.interval = self.get_parameter("interval").get_parameter_value().double_value

        # ================= Load YAMLs ==========================
        with open(gait_path, "r") as f:
            self.gait_data = yaml.safe_load(f)

        with open(command_map_path, "r") as f:
            self.command_map = yaml.safe_load(f).get("command_map", {})

        # ================= Load Base / LB / RB Pose =============
        self.base_pose = self.gait_data.get("Base pose", [[]])[0]
        self.lb_pose   = self.gait_data.get("LB Mode", [[]])[0]
        self.rb_pose   = self.gait_data.get("RB Mode", [[]])[0]

        if not self.base_pose or not self.lb_pose or not self.rb_pose:
            raise RuntimeError("Missing Base pose / LB Mode / RB Mode in YAML!")

        # ================= ROS Pub/Sub =========================
        self.pub = self.create_publisher(JointTrajectory, "/servo_trajectory", 10)

        self.sub_cmd = self.create_subscription(String, "/teleop_cmd", self.cmd_callback, 10)
        self.sub_lt  = self.create_subscription(Float32, "/lt_value", self.lt_callback, 10)
        self.sub_rt  = self.create_subscription(Float32, "/rt_value", self.rt_callback, 10)

        # ================= States ==============================
        self.current_cmd = "stop"
        self.lt_value = 0.0
        self.rt_value = 0.0
        self.one_shot_cmd = None  # ⭐ 用來執行像 crab_sway 這類一次性 gait

        # ================= Worker Thread ======================
        self.action_thread = threading.Thread(target=self.action_loop, daemon=True)
        self.action_thread.start()

        self.get_logger().info("Teleop Ready with LT/RT interpolation + one-shot gait support!")

    # ------------------------------------------------------
    def cmd_callback(self, msg: String):
        cmd = msg.data.strip()

        # ⭐ one-shot gait（例如 crab_sway）
        if cmd == "crab_sway":
            self.one_shot_cmd = cmd
            return

        # ⭐ normal command
        if cmd in self.command_map:
            self.current_cmd = cmd

    # ------------------------------------------------------
    def lt_callback(self, msg: Float32):
        self.lt_value = max(0.0, min(1.0, float(msg.data)))

    # ------------------------------------------------------
    def rt_callback(self, msg: Float32):
        self.rt_value = max(0.0, min(1.0, float(msg.data)))

    # ------------------------------------------------------
    def action_loop(self):
        while True:

            # ================================
            #  ⭐ First: one-shot motion
            # ================================
            if self.one_shot_cmd:
                self.run_one_shot(self.one_shot_cmd)
                self.one_shot_cmd = None

                time.sleep(self.interval)
                continue

            # ================================
            #  ⭐ Second: LT/RT interpolation
            # ================================
            if self.lt_value > 0.01 or self.rt_value > 0.01:
                self.run_combined_interpolation()
                continue

            # ================================
            #  ⭐ Third: normal gait
            # ================================
            self.run_gait(self.current_cmd)

    # ------------------------------------------------------
    # ⭐ One-shot gait (e.g., crab_sway)
    # ------------------------------------------------------
    def run_one_shot(self, cmd):
        yaml_key = self.command_map.get(cmd, None)
        if yaml_key is None:
            return

        poses = self.gait_data.get(yaml_key, None)
        if poses is None:
            return

        for pose in poses:
            pose_f = [float(x) for x in pose]

            # ⭐ 每組 pose 重複發送 3 次
            for _ in range(3):
                self.publish_pose(pose_f)
                time.sleep(self.interval)

    # ------------------------------------------------------
    # ⭐ Combined LT/RT interpolation
    # ------------------------------------------------------
    def run_combined_interpolation(self):
        pose = []

        for b, L, R in zip(self.base_pose, self.lb_pose, self.rb_pose):
            angle = b

            # LT interpolation
            angle += (L - b) * self.lt_value

            # RT interpolation
            angle += (R - b) * self.rt_value

            pose.append(angle)

        self.publish_pose(pose)
        time.sleep(self.interval)

    # ------------------------------------------------------
    # ⭐ Normal gait (forward/back/turn/joystick directions)
    # ------------------------------------------------------
    def run_gait(self, cmd):
        yaml_key = self.command_map.get(cmd, None)
        if yaml_key is None:
            return

        poses = self.gait_data.get(yaml_key, None)
        if poses is None:
            return

        for pose in poses:
            if cmd != self.current_cmd:
                return
            self.publish_pose([float(x) for x in pose])
            time.sleep(self.interval)

    # ------------------------------------------------------
    def publish_pose(self, pose):
        msg = JointTrajectory()
        msg.joint_names = [f"servo_{i+1}" for i in range(len(pose))]

        pt = JointTrajectoryPoint()
        pt.positions = pose
        pt.time_from_start.sec = 1

        msg.points.append(pt)
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = TeleopGaitRunner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
