#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String, Float32

class JoyToCommand(Node):
    def __init__(self):
        super().__init__('joy_to_command')

        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10
        )

        self.pub_cmd = self.create_publisher(String, '/teleop_cmd', 10)
        self.pub_lt = self.create_publisher(Float32, '/lt_value', 10)
        self.pub_rt = self.create_publisher(Float32, '/rt_value', 10)

        self.deadzone = 0.3
        self.get_logger().info("JoyToCommand ready!")

    def joy_callback(self, msg):

        # ---------------------------------------------------
        # LT / RT
        # ---------------------------------------------------
        lt_raw = msg.axes[2]
        lt_value = (1.0 - lt_raw) * 0.5
        self.pub_lt.publish(Float32(data=lt_value))

        rt_raw = msg.axes[5]
        rt_value = (1.0 - rt_raw) * 0.5
        self.pub_rt.publish(Float32(data=rt_value))

        # ---------------------------------------------------
        # RB / LB / B
        # ---------------------------------------------------
        if msg.buttons[5] == 1:
            self._send_cmd("rb_mode")
            return

        if msg.buttons[4] == 1:
            self._send_cmd("lb_mode")
            return

        if msg.buttons[1] == 1:
            self._send_cmd("stop")
            return
            
        if msg.buttons[0] == 1:   # X
            self._send_cmd("crab_sway")
            return
        # ============================================================
        # X → crab_sway
        # ============================================================
        if msg.buttons[0] == 1:   # X button
            self._send_cmd("crab_sway")
            return


        # ---------------------------------------------------
        # D-Pad
        # ---------------------------------------------------
        dx = msg.axes[6]
        dy = msg.axes[7]

        if dy > 0.5:
            self._send_cmd("forward")
            return
        elif dy < -0.5:
            self._send_cmd("backward")
            return
        elif dx < -0.5:
            self._send_cmd("turn_right")
            return
        elif dx > 0.5:
            self._send_cmd("turn_left")
            return

        # ---------------------------------------------------
        # 左搖桿六向動作（已修正方向）
        # ---------------------------------------------------
        lx = -msg.axes[0]     # 反轉左右
        ly = -msg.axes[1]     # 反轉上下

        dz = self.deadzone
        cmd = None

        if lx > dz:
            if ly < -dz:
                cmd = "joy_up_right"
            elif ly > dz:
                cmd = "joy_down_right"
            else:
                cmd = "joy_right"

        elif lx < -dz:
            if ly < -dz:
                cmd = "joy_up_left"
            elif ly > dz:
                cmd = "joy_down_left"
            else:
                cmd = "joy_left"

        elif ly < -dz:
            cmd = "joy_up"

        elif ly > dz:
            cmd = "joy_down"

        if cmd:
            self._send_cmd(cmd)

    # ---------------------------------------------------
    def _send_cmd(self, cmd):
        self.pub_cmd.publish(String(data=cmd))
        self.get_logger().info(f"[CMD] {cmd}")


def main(args=None):
    rclpy.init(args=args)
    node = JoyToCommand()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
