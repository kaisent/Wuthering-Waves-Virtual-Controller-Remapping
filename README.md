# Wuthering Waves Virtual Controller Remapping

Keyboard-only combat controls for Wuthering Waves via a virtual gamepad.
Maps keyboard input to a virtual Xbox 360 (or DualShock 4) controller using
ViGEmBus + vgamepad, so the game runs in native controller mode while you
play entirely on keyboard — including camera panning on arrow keys via the
right stick, with a hold-to-ramp acceleration curve.

## Layout

| Key       | Virtual button | In-game action        |
|-----------|----------------|-----------------------|
| WASD      | Left stick     | Movement              |
| Arrows    | Right stick    | Camera (ramped)       |
| J         | X / Square     | Basic attack          |
| K         | A / Cross      | Jump                  |
| L         | Y / Triangle   | Resonance Liberation  |
| I         | RT / R2        | Resonance Skill       |
| Q         | LT / L2        | Echo skill            |
| Shift     | B / Circle     | Dodge / sprint        |
| 1 / 2 / 3 | D-pad L/U/R    | Resonator select      |
| F         | L3             | Interact              |
| F8        | —              | Toggle remap on/off   |

## Requirements

- Windows 10/11, [ViGEmBus driver](https://github.com/nefarius/ViGEmBus/releases)
- Python 3.11+ with `pip install vgamepad keyboard`
- Elevated (administrator) console — key suppression requires it

## Files

- `wuwa_kb_pad.py` — main script, virtual Xbox 360 pad
- `wuwa_kb_pad_ds4.py` — DualShock 4 variant (tests the HID/DirectInput path)
- `xinput_probe.py` — diagnostic: polls XInput slots 0–3 directly via
  `XInputGetState`, showing slot occupancy, packet counter, and live state
- `wuwa_pad.bat` — launcher (edit paths for your machine)

## Usage

1. Install ViGEmBus, reboot.
2. Run `wuwa_kb_pad.py` from an elevated console.
3. Verify in `joy.cpl` (one controller, axes respond) or with `xinput_probe.py`
   (slot 0 connected, values move on keypress).
4. Launch the game. Mapped keys are suppressed system-wide while enabled
   (F8 toggles this off for typing).

## Status / findings

- **Global client:** untested here, but virtual ViGEm pads are the basis of
  the DS4Windows ecosystem widely used with WuWa global, so expected to work.
- **CN client (independent launcher):** **does not accept virtual controllers.**
  Verified end-to-end delivery (hooks → feed loop → ViGEm device → XInput
  slot 0 confirmed live via `xinput_probe.py`) — game ignores the pad on both
  the XInput path (X360 pad) and the HID path (DS4 pad). Steam Input
  injection is blocked by the ACE anti-cheat (overlay does not load). No
  in-game input-mode selector exists to force controller mode. Conclusion:
  ACE on the CN client filters virtual input devices at a level below
  anything a user-mode feeder can address. Physical controllers work.

## Debugging notes (hard-won)

- Low-level keyboard hooks suppress the message queue but **cannot block
  Raw Input** — irrelevant here since the game runs in controller mode, but
  it matters for any hook-based remap design.
- Crashed feeder processes can leave **phantom pads** on the bus that occupy
  XInput slot 0 while being dead; games poll slot 0 and see nothing. Check
  `joy.cpl` for exactly one controller; reboot clears phantoms.
- The `keyboard` library's listener threads are non-daemon: if the main feed
  loop dies, the process stays alive with hooks working and the pad frozen —
  a convincing zombie. The scripts now heartbeat every second and print feed
  loop errors instead of dying silently.
- `XInputGetState`'s `dwPacketNumber` only increments on state **change**;
  a frozen packet counter with a connected slot means nobody is feeding it.

  ## Acknowledgments

- [ViGEmBus](https://github.com/nefarius/ViGEmBus) by Benjamin "Nefarius" Höglinger-Stelzer —
  the virtual gamepad bus driver this entire project runs on (BSD-3-Clause)
- [vgamepad](https://github.com/yannbouteiller/vgamepad) by Yann Bouteiller —
  Python bindings for ViGEm (MIT)