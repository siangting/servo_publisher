#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String

class JoyToCommand(Node):
    def __init__(self):
        super().__init__('joy_to_command')

        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10
        )

        self.pub = self.create_publisher(String, '/teleop_cmd', 10)

        # deadzone 避免微動造成亂跳
        self.deadzone = 0.2

    def joy_callback(self, msg):
        lx = -msg.axes[0]   # 左搖桿 左右
        ly = -msg.axes[1]   # 左搖桿 上下

        cmd = None
        # ===== B 鍵 = 強制 Base pose =====
        if msg.buttons[1] == 1:   # B 按下
            msg_out = String()
            msg_out.data = "stop"
            self.pub.publish(msg_out)
            self.get_logger().info("CMD: stop (B pressed)")
            return

        # ↑↓ → forward/backward
        if ly < -self.deadzone:
            cmd = "forward"
        elif ly > self.deadzone:
            cmd = "backward"

        # ←→ → turn left/right
        if lx > self.deadzone:
            cmd = "turn_right"
        elif lx < -self.deadzone:
            cmd = "turn_left"

        if cmd is None:
            return

        msg_out = String()
        msg_out.data = cmd
        self.pub.publish(msg_out)
        self.get_logger().info(f"CMD: {cmd}")


def main(args=None):
    rclpy.init(args=args)
    node = JoyToCommand()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
