#!/bin/bash

echo "Press r to run..."
read -n 1 key
echo ""

if [ "$key" != "r" ]; then
    echo "Not running."
    exit 0
fi

SESSION="spider_teleop"

# 如果 session 已存在 → 先 kill 掉
tmux has-session -t $SESSION 2>/dev/null
if [ $? == 0 ]; then
    echo "Killing old session..."
    tmux kill-session -t $SESSION
fi

echo "Starting tmux session: $SESSION"

# 建立新的 session
tmux new-session -d -s $SESSION

# Pane 0
tmux send-keys -t $SESSION "python3 servo_publisher/teleop_gait_runner.py" C-m

# Pane 1
tmux split-window -v -t $SESSION
tmux send-keys -t $SESSION "ros2 run joy joy_node" C-m

# Pane 2
tmux split-window -h -t $SESSION
tmux send-keys -t $SESSION "python3 servo_publisher/teleop_joy_to_cmd.py" C-m

# Pane 3
tmux split-window -h -t $SESSION
tmux send-keys -t $SESSION "ros2 topic echo /teleop_cmd" C-m

# Pane 4
tmux split-window -v -t $SESSION
tmux send-keys -t $SESSION "python3 servo_publisher/keyboard_teleop_cmd.py" C-m



# 調整 layout
tmux select-layout -t $SESSION tiled

# attach session
tmux attach-session -t $SESSION
