@echo off
start "XInput Probe" cmd /k py C:\tools\xinput_probe.py
title WuWa Pad
py -V:Astral\CPython3.11.15 C:\tools\wuwa_kb_pad.py
pause