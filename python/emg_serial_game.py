import serial, time
import matplotlib.pyplot as plt
import keyboard
from collections import deque
from pynput.keyboard import Controller, Key

kb = Controller()

HIGH_THRESHOLD = 300
LOW_THRESHOLD = 150
REFRACTORY = 0.3
TIME_THRESHOLD = 0.5

ser = serial.Serial('COM5', 115200, timeout=1)
time.sleep(2)

was_below = True
last_flap_time = 0
grip_start_time = 0

is_jumping = False
jump_start_time = 0
JUMP_DURATION = 0.75

BUFFER_SIZE = 1000
values = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

plt.ion()
fig, ax = plt.subplots(figsize=(10, 4))
line_plot, = ax.plot(values)
ax.axhline(y=HIGH_THRESHOLD, color='r', linestyle='--', label=f'threshold={HIGH_THRESHOLD}')
ax.axhline(y=LOW_THRESHOLD, color='b', linestyle='--', label=f'threshold={LOW_THRESHOLD}')
ax.set_ylim(0, 1023)
ax.set_xlim(0, BUFFER_SIZE)
ax.legend()
ax.set_title('EMG live')

sample_count = 0
PLOT_EVERY = 5

print('Started')

try:
    while not keyboard.is_pressed('esc'):
        line = ser.readline().decode().strip()
        if line.isdigit():
            value = int(line)
            now = time.time()

            values.append(value)

            if value >= HIGH_THRESHOLD and was_below and not is_jumping:
                was_below = False
                grip_start_time = now
                kb.press(Key.right)
                print(f'GRIP START value={value}')

            elif value < LOW_THRESHOLD and not was_below and not is_jumping:
                was_below = True
                duration = now - grip_start_time
                if duration < TIME_THRESHOLD:
                    kb.press(Key.up)
                    is_jumping = True
                    jump_start_time = now
                    print(f'JUMP START (short grip {duration:.2f}s)')
                else:
                    kb.release(Key.right)
                    print(f'WALK END (held {duration:.2f}s)')

            if is_jumping and now - jump_start_time >= JUMP_DURATION:
                kb.release(Key.up)
                kb.release(Key.right)
                is_jumping = False
                print('JUMP END')      

            sample_count += 1
            if sample_count >= PLOT_EVERY:
                sample_count = 0
                line_plot.set_ydata(values)
                fig.canvas.draw_idle()
                fig.canvas.flush_events()

except KeyboardInterrupt:
    print("STOP")
finally:
    kb.release(Key.right)
    kb.release(Key.up)
    ser.close()
    plt.ioff()
    plt.savefig('emg_live.png', dpi=150)
    plt.show()