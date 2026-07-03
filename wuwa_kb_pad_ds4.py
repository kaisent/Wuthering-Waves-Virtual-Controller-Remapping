"""
wuwa_kb_pad_ds4.py — keyboard -> virtual DualShock 4 for Wuthering Waves.
Tests the game's PS/HID input path instead of XInput.
Same keys as the X360 version. F8 toggles. Requires ViGEmBus + vgamepad.
"""

import time
import keyboard
import vgamepad as vg


def _make_pad(retries=10, delay=1.0):
    for i in range(1, retries + 1):
        try:
            return vg.VDS4Gamepad()
        except Exception as e:
            print(f"[ds4] pad attach failed ({e}); retry {i}/{retries}")
            time.sleep(delay)
    raise SystemExit("[ds4] could not attach to ViGEmBus — reboot and retry")


pad = _make_pad()

B = vg.DS4_BUTTONS
BUTTONS = {
    'j':     B.DS4_BUTTON_SQUARE,      # basic attack
    'k':     B.DS4_BUTTON_CROSS,       # jump
    'l':     B.DS4_BUTTON_TRIANGLE,    # resonance liberation
    'shift': B.DS4_BUTTON_CIRCLE,      # dodge / sprint
    'f':     B.DS4_BUTTON_THUMB_LEFT,  # interact (L3)
}
TRIGGERS = {
    'i': 'rt',   # resonance skill (R2)
    'q': 'lt',   # echo skill (L2)
}
D = vg.DS4_DPAD_DIRECTIONS
DPAD = {  # resonator select
    '1': D.DS4_BUTTON_DPAD_WEST,
    '2': D.DS4_BUTTON_DPAD_NORTH,
    '3': D.DS4_BUTTON_DPAD_EAST,
    '4': D.DS4_BUTTON_DPAD_SOUTH,
}

MOVE = {'w': (0, 1), 's': (0, -1), 'a': (-1, 0), 'd': (1, 0)}
CAM  = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}

CAM_RAMP_S = 0.25
CAM_MIN    = 0.35
TICK_HZ    = 120
DEBUG      = True

down = set()
cam_press_t = {}
enabled = True
hooks = []
ALL_KEYS = list(BUTTONS) + list(TRIGGERS) + list(DPAD) + list(MOVE) + list(CAM)


def on_key(event):
    key = event.name
    if key == 'shift':
        key = 'shift'
    if event.event_type == 'down':
        if key in CAM and key not in down:
            cam_press_t[key] = time.monotonic()
        down.add(key)
    else:
        down.discard(key)
        cam_press_t.pop(key, None)
    if DEBUG:
        print(f"[debug] {event.event_type:>4} {key!r:>10}  held={sorted(down)}")


def hook_all():
    for k in ALL_KEYS:
        hooks.append(keyboard.hook_key(k, on_key, suppress=True))


def unhook_all():
    keyboard.unhook_all()
    keyboard.add_hotkey('f8', toggle)
    hooks.clear()
    down.clear()
    cam_press_t.clear()
    pad.reset()
    pad.update()


def toggle():
    global enabled
    try:
        enabled = not enabled
        if enabled:
            keyboard.unhook_all()
            keyboard.add_hotkey('f8', toggle)
            hook_all()
        else:
            unhook_all()
        print(f"[ds4] {'ENABLED' if enabled else 'disabled'}")
    except Exception as e:
        print(f"[ds4] toggle error: {e!r}")


keyboard.add_hotkey('f8', toggle)


def axis(keys_map, ramp=False):
    x = y = 0.0
    now = time.monotonic()
    for k, (dx, dy) in keys_map.items():
        if k in down:
            mag = 1.0
            if ramp:
                held = now - cam_press_t.get(k, now)
                mag = min(1.0, CAM_MIN + (1.0 - CAM_MIN) * held / CAM_RAMP_S)
            x += dx * mag
            y += dy * mag
    m = (x * x + y * y) ** 0.5
    if m > 1.0:
        x, y = x / m, y / m
    return x, y


def dpad_direction():
    for k, direction in DPAD.items():
        if k in down:
            return direction
    return D.DS4_BUTTON_DPAD_NONE


def main():
    hook_all()
    print("[ds4] running — F8 to toggle, Ctrl+C to quit")
    dt = 1.0 / TICK_HZ
    last_hb = 0.0
    while True:
        try:
            if enabled:
                lx, ly = axis(MOVE)
                rx, ry = axis(CAM, ramp=True)
                # DS4 Y axes are inverted relative to the float API convention
                pad.left_joystick_float(x_value_float=lx, y_value_float=-ly)
                pad.right_joystick_float(x_value_float=rx, y_value_float=-ry)

                for k, btn in BUTTONS.items():
                    (pad.press_button if k in down else pad.release_button)(button=btn)

                pad.directional_pad(direction=dpad_direction())

                lt = 1.0 if any(k in down for k, t in TRIGGERS.items() if t == 'lt') else 0.0
                rt = 1.0 if any(k in down for k, t in TRIGGERS.items() if t == 'rt') else 0.0
                pad.left_trigger_float(value_float=lt)
                pad.right_trigger_float(value_float=rt)

                pad.update()

                now = time.monotonic()
                if now - last_hb >= 1.0:
                    last_hb = now
                    print(f"[hb] lx={lx:+.2f} ly={ly:+.2f} rx={rx:+.2f} ry={ry:+.2f} held={sorted(down)}")
        except Exception:
            import traceback
            print("[ds4] FEED LOOP ERROR:")
            traceback.print_exc()
            time.sleep(2.0)
        time.sleep(dt)


if __name__ == '__main__':
    try:
        main()
    finally:
        unhook_all()
