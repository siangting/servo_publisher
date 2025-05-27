#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class ServoTrajectoryPublisher(Node):
    def __init__(self):
        super().__init__('servo_trajectory_publisher')
        self.pub = self.create_publisher(JointTrajectory, '/servo_trajectory', 10)
        # 先記住兩個 servo 的目前角度（初始都 0°）
        self.positions = [0.0, 0.0]
        self.get_logger().info('輸入 q 離開')

    def publish_joint_trajectory(self):
        msg = JointTrajectory()
        msg.joint_names = ['servo_1', 'servo_2']
        pt = JointTrajectoryPoint()
        pt.positions = self.positions.copy()
        pt.time_from_start.sec = 0
        pt.time_from_start.nanosec = 0
        msg.points = [pt]
        self.pub.publish(msg)
        self.get_logger().info(f'Published → {self.positions}')

    def run_menu(self):
        try:
            while rclpy.ok():
                choice = input('\n選擇要控制哪顆舵機 (1 or 2, q = quit)：').strip()
                if choice.lower() == 'q':
                    break
                if choice not in ('1', '2'):
                    print('輸入錯誤，請輸入 1、2 或 q。')
                    continue
                idx = int(choice) - 1
                self.angle_menu(idx)
        except (KeyboardInterrupt, EOFError):
            pass

    def angle_menu(self, idx: int):
        prompt = f'Servo {idx+1} 角度 (0–240) 或 b 返回：'
        while rclpy.ok():
            inp = input(prompt).strip()
            if inp.lower() == 'b':
                return
            try:
                ang = float(inp)
                if not 0.0 <= ang <= 240.0:
                    raise ValueError
            except ValueError:
                print('角度範圍錯誤，請輸入 0 到 240 之間，或 b 返回。')
                continue

            # 更新並發佈
            self.positions[idx] = ang
            self.publish_joint_trajectory()

def main(args=None):
    rclpy.init(args=args)
    node = ServoTrajectoryPublisher()
    node.run_menu()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
