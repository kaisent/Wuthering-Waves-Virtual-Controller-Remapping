"""
wuwa_kb_pad.py — keyboard -> virtual Xbox 360 pad for Wuthering Waves.
Requires: ViGEmBus driver (installed), `pip install vgamepad keyboard`.

F8 toggles the mapper on/off (off = keys pass through normally).
Mapped keys are SUPPRESSED while active so WuWa never sees keyboard
input and stays locked in controller mode.

Edit BUTTONS / TRIGGERS / sticks below to taste, then align the
virtual buttons with WuWa's in-game Controller settings screen.
"""

import time
import keyboard
import vgamepad as vg

def _make_pad(retries=10, delay=1.0):
    for i in range(1, retries + 1):
        try:
            return vg.VX360Gamepad()
        except Exception as e:
            print(f"[wuwa_kb_pad] pad attach failed ({e}); retry {i}/{retries}")
            time.sleep(delay)
    raise SystemExit("[wuwa_kb_pad] could not attach to ViGEmBus after retries — reboot and try again")


pad = _make_pad()

# ---- mapping ---------------------------------------------------------------
BUTTONS = {
    'j':     vg.XUSB_BUTTON.XUSB_GAMEPAD_X,               # basic attack
    'k':     vg.XUSB_BUTTON.XUSB_GAMEPAD_A,               # jump
    'l':     vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,               # resonance liberation (ultimate)
    'shift': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,               # dodge / sprint
    '1':     vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,       # resonator 1
    '2':     vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,         # resonator 2
    '3':     vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,      # resonator 3
    '4':     vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,       # (teams are 3 — spare)
    'f':     vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,      # interact
}
TRIGGERS = {
    'i': 'rt',   # resonance skill
    'q': 'lt',   # echo skill
}

MOVE = {'w': (0, 1), 's': (0, -1), 'a': (-1, 0), 'd': (1, 0)}    # left stick
CAM  = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}  # right stick

CAM_RAMP_S   = 0.25   # seconds to ramp camera from CAM_MIN to full tilt
CAM_MIN      = 0.35   # initial camera speed fraction (fine adjustments)
TICK_HZ      = 120

# ---- state -----------------------------------------------------------------
down = set()               # currently-held mapped keys
cam_press_t = {}           # key -> press timestamp, for the ramp
enabled = True
hooks = []

ALL_KEYS = list(BUTTONS) + list(TRIGGERS) + list(MOVE) + list(CAM)


DEBUG = True   # print every hooked key event and the held-key set


def on_key(event):
    key = event.name
    if key == 'shift':          # keyboard lib reports 'shift' for both sides
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
    keyboard.unhook_all()              # removes key hooks AND the F8 hotkey
    keyboard.add_hotkey('f8', toggle)  # so re-register the toggle immediately
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
        print(f"[wuwa_kb_pad] {'ENABLED' if enabled else 'disabled'}")
    except Exception as e:
        print(f"[wuwa_kb_pad] toggle error: {e!r}")  # never let the listener thread die


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
    # normalize diagonals
    m = (x * x + y * y) ** 0.5
    if m > 1.0:
        x, y = x / m, y / m
    return x, y


def main():
    hook_all()
    print("[wuwa_kb_pad] running — F8 to toggle, Ctrl+C in this window to quit")
    dt = 1.0 / TICK_HZ
    last_hb = 0.0
    while True:
        try:
            if enabled:
                lx, ly = axis(MOVE)
                rx, ry = axis(CAM, ramp=True)
                pad.left_joystick_float(x_value_float=lx, y_value_float=ly)
                pad.right_joystick_float(x_value_float=rx, y_value_float=ry)

                for k, btn in BUTTONS.items():
                    (pad.press_button if k in down else pad.release_button)(button=btn)

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
            print("[wuwa_kb_pad] FEED LOOP ERROR:")
            traceback.print_exc()
            time.sleep(2.0)   # keep looping; don't die silently
        time.sleep(dt)


if __name__ == '__main__':
    try:
        main()
    finally:
        unhook_all()