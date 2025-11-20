#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import sys
import tty
import termios
import threading
import os


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__("keyboard_teleop_cmd")

        self.pub = self.create_publisher(String, "/teleop_cmd", 10)

        # 啟動鍵盤 thread
        self.key_thread = threading.Thread(target=self.keyboard_loop, daemon=True)
        self.key_thread.start()

        self.get_logger().info("Keyboard Teleop Ready! (W/A/S/D, Z=stop, Q=quit)")

    # ---------------------------
    # Non-blocking keyboard input
    # ---------------------------
    def get_key(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return key

    # ---------------------------
    # Keyboard event loop
    # ---------------------------
    def keyboard_loop(self):
        while True:
            key = self.get_key().lower()
            cmd = None

            if key == 'w':
                cmd = "forward"
            elif key == 's':
                cmd = "backward"
            elif key == 'a':
                cmd = "turn_left"
            elif key == 'd':
                cmd = "turn_right"
            elif key == 'z':
                cmd = "stop"
            elif key == 'q':
                print("Exiting keyboard cmd...")
                os._exit(0)
            else:
                continue

            msg = String()
            msg.data = cmd
            self.pub.publish(msg)
            self.get_logger().info(f"[Keyboard] CMD: {cmd}")


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardTeleop()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
