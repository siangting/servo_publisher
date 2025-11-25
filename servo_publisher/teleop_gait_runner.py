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
        self.declare_parameter("repeat_one_shot", 3)  # 每組角度重複次數

        gait_path = self.get_parameter("gait_file").get_parameter_value().string_value
        command_map_path = self.get_parameter("command_map_file").get_parameter_value().string_value
        self.interval = self.get_parameter("interval").get_parameter_value().double_value
        self.repeat_one_shot = self.get_parameter("repeat_one_shot").get_parameter_value().integer_value

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
        self.one_shot_cmd = None  # 用來執行一次性 gait

        # ================= Worker Thread ======================
        self.action_thread = threading.Thread(target=self.action_loop, daemon=True)
        self.action_thread.start()

        self.get_logger().info("Teleop Ready with LT/RT interpolation + one-shot gaits!")

    # ------------------ Callback --------------------------
    def cmd_callback(self, msg: String):
        cmd = msg.data.strip()
        if cmd in self.command_map:
            if cmd == "crab_sway":
                self.one_shot_cmd = cmd
            else:
                self.current_cmd = cmd

    def lt_callback(self, msg: Float32):
        self.lt_value = float(msg.data)

    def rt_callback(self, msg: Float32):
        self.rt_value = float(msg.data)

    # ------------------ Action Loop -----------------------
    def action_loop(self):
        while True:
            if self.one_shot_cmd:
                # run one-shot gait once
                self.run_one_shot(self.one_shot_cmd)
                self.one_shot_cmd = None
                # 回到 Base pose
                self.publish_pose(self.base_pose)
                time.sleep(self.interval)
            else:
                # run normal gait
                self.run_gait(self.current_cmd)

            time.sleep(0.01)

    # ------------------ Run Normal Gait -------------------
    def run_gait(self, cmd):
        gait_name = self.command_map.get(cmd, None)
        if gait_name is None:
            return

        poses = self.gait_data.get(gait_name, None)
        if poses is None:
            return

        for pose in poses:
            # 內插 LT/RT
            pose_f = []
            for i, val in enumerate(pose):
                val_f = float(val)
                # LB 改變舵機 15~19 (示意)
                val_f = val_f + (self.lb_pose[i] - self.base_pose[i]) * self.lt_value
                # RB 改變舵機 15~19 (示意)
                val_f = val_f + (self.rb_pose[i] - self.base_pose[i]) * self.rt_value
                pose_f.append(val_f)

            self.publish_pose(pose_f)
            time.sleep(self.interval)

    # ------------------ Run One-Shot Gait -----------------
    def run_one_shot(self, cmd):
        gait_name = self.command_map.get(cmd, None)
        if gait_name is None:
            return

        poses = self.gait_data.get(gait_name, None)
        if poses is None:
            return

        for pose in poses:
            pose_f = [float(x) for x in pose]
            # ⭐ 每組 pose 發送 repeat_one_shot 次
            for _ in range(self.repeat_one_shot):
                self.publish_pose(pose_f)
                time.sleep(self.interval)

    # ------------------ Publish Pose ----------------------
    def publish_pose(self, pose):
        msg = JointTrajectory()
        msg.joint_names = [f"joint{i+1}" for i in range(len(pose))]
        point = JointTrajectoryPoint()
        point.positions = [float(x) for x in pose]
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 0
        msg.points.append(point)
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TeleopGaitRunner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
