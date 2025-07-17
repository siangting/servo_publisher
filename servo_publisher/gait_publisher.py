#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class GaitPublisher(Node):
    def __init__(self):
        super().__init__('gait_publisher')
        self.pub = self.create_publisher(JointTrajectory, '/servo_trajectory', 10)

        # 12 顆舵機的 joint_names
        self.joint_names = [f'servo_{i+1}' for i in range(12)]

        # 原始 4 組步態點資料
        self.gait_sequence = [
            [90.0,  65.0, 120.0, 100.0, 120.0, 120.0,  90.0, 130.0, 120.0,  65.0, 120.0, 150.0],
            [90.0,  65.0, 120.0,  65.0, 120.0, 120.0,  90.0,  95.0, 120.0,  65.0, 120.0, 120.0],
            [120.0, 90.0, 180.0,  65.0,  90.0, 150.0, 120.0,  95.0, 150.0, 100.0,  90.0, 120.0],
            [120.0, 65.0, 180.0,  65.0,  90.0, 120.0, 120.0,  95.0, 150.0,  65.0,  90.0, 120.0],
        ]

        # 每段之間插值的步數，以及發送間隔
        self.steps_per_transition = 10
        self.interval = 0.1  # 秒

        # 預先計算全部插值後的步態序列
        self.full_sequence = []
        for i in range(len(self.gait_sequence)):
            start = self.gait_sequence[i]
            end = self.gait_sequence[(i + 1) % len(self.gait_sequence)]
            for step in range(self.steps_per_transition):
                alpha = step / float(self.steps_per_transition)
                interp = [
                    start[j] + alpha * (end[j] - start[j])
                    for j in range(len(start))
                ]
                self.full_sequence.append(interp)

        self.index = 0
        self.timer = self.create_timer(self.interval, self.publish_next)

    def publish_next(self):
        positions = self.full_sequence[self.index]
        msg = JointTrajectory()
        msg.joint_names = self.joint_names

        pt = JointTrajectoryPoint()
        pt.positions = positions
        pt.time_from_start.sec = 0
        pt.time_from_start.nanosec = 0
        msg.points = [pt]

        self.pub.publish(msg)
        self.get_logger().info(f'Published step #{self.index+1}/{len(self.full_sequence)}')

        self.index = (self.index + 1) % len(self.full_sequence)


def main():
    rclpy.init()
    node = GaitPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
