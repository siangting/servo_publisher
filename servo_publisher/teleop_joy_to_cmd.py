#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String, Float32

class JoyToCommand(Node):
    def __init__(self):
        super().__init__('joy_to_command')

        # joy input
        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10
        )

        # publish /teleop_cmd (string)
        self.pub_cmd = self.create_publisher(String, '/teleop_cmd', 10)

        # publish LT / RT 0~1 interpolation value
        self.pub_lt = self.create_publisher(Float32, '/lt_value', 10)
        self.pub_rt = self.create_publisher(Float32, '/rt_value', 10)

        self.deadzone = 0.2

        self.get_logger().info("JoyToCommand ready!")

    def joy_callback(self, msg):
        lx = -msg.axes[0]    # 左搖桿左右
        ly = -msg.axes[1]    # 左搖桿上下

        # ============================================================
        # 1. Detect LT (Left Trigger)
        # axis index commonly = 2   (value: 1 → -1)
        # ============================================================
        lt_raw = msg.axes[2]
        lt_value = (1.0 - lt_raw) * 0.5     # map to 0~1

        msg_lt = Float32()
        msg_lt.data = float(lt_value)
        self.pub_lt.publish(msg_lt)

        # ============================================================
        # 2. Detect RT (Right Trigger)
        # axis index commonly = 5   (value: 1 → -1)
        # ============================================================
        rt_raw = msg.axes[5]
        rt_value = (1.0 - rt_raw) * 0.5     # map to 0~1

        msg_rt = Float32()
        msg_rt.data = float(rt_value)
        self.pub_rt.publish(msg_rt)

        # ============================================================
        # 3. RB pressed → enter RB mode
        # ============================================================
        if msg.buttons[5] == 1:   # RB
            self._send_cmd("rb_mode")
            return

        # ============================================================
        # 4. LB pressed → enter LB mode (if needed)
        # ============================================================
        if msg.buttons[4] == 1:   # LB
            self._send_cmd("lb_mode")
            return

        # ============================================================
        # 5. B → stop
        # ============================================================
        if msg.buttons[1] == 1:   # B
            self._send_cmd("stop")
            return

        # ============================================================
        # 6. normal movement
        # ============================================================
        cmd = None

        # forward/back
        if ly < -self.deadzone:
            cmd = "forward"
        elif ly > self.deadzone:
            cmd = "backward"

        # turn left/right
        if lx > self.deadzone:
            cmd = "turn_right"
        elif lx < -self.deadzone:
            cmd = "turn_left"

        if cmd:
            self._send_cmd(cmd)

    def _send_cmd(self, cmd):
        msg = String()
        msg.data = cmd
        self.pub_cmd.publish(msg)
        self.get_logger().info(f"CMD: {cmd}")


def main(args=None):
    rclpy.init(args=args)
    node = JoyToCommand()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
