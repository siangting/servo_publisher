ros2 topic pub -1 /servo_trajectory trajectory_msgs/msg/JointTrajectory \
"{ \
  joint_names: ['servo_1','servo_2','servo_3','servo_4','servo_5','servo_6','servo_7','servo_8','servo_9','servo_10','servo_11','servo_12'], \
  points: [{ \
    positions: [120.0, 65.0, 120.0, 65.0, 120.0, 120.0, 120.0, 95.0, 120.0, 65.0, 120.0, 120.0], \
    time_from_start: {sec: 0, nanosec: 0} \
  }] \
}"

