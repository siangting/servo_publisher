from inputs import get_gamepad

while True:
    events = get_gamepad()
    for e in events:
        print(e.ev_type, e.code, e.state)
