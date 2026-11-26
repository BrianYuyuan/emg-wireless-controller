import asyncio
from bleak import BleakScanner, BleakClient
from collections import deque
import matplotlib.pyplot as plt
from pynput.keyboard import Controller, Key

DEVICE_NAME = "EMG-Sensor-1"
CHAR_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"

HIGH_THRESHOLD = 1000
LOW_THRESHOLD = 500
BUFFER_SIZE = 500

kb = Controller()
values = deque([0] * BUFFER_SIZE, maxlen=BUFFER_SIZE)

peak_value = 0
was_below = True 
count = 0

def on_notify(sender, data):
    global was_below, peak_value, count
    value = int.from_bytes(data, byteorder='little')
    values.append(value)

    # if not was_below:
    #     if value > peak_value:
    #         peak_value = value
    #     elif value < peak_value * 0.7:
    #         was_below = True

    if value >= HIGH_THRESHOLD and was_below:
        was_below = False
        # peak_value = value
        kb.press(Key.space)
        kb.release(Key.space)
        count += 1
        print(f"JUMP! value={value} count={count} ")
    elif value <= LOW_THRESHOLD and not was_below:
        was_below = True

async def main():
    print("Scanning...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10)
    if not device:
        print("EMG-Sensor-1 not found!")
        return

    print(f"Found: {device.name}")

    async with BleakClient(device) as client:
        print("Connected! Grip to jump.")

        await client.start_notify(CHAR_UUID, on_notify)

        plt.ion()
        fig, ax = plt.subplots(figsize=(10, 4))
        line_plot, = ax.plot(values)
        ax.axhline(y=HIGH_THRESHOLD, color='r', linestyle='--', label=f'HIGH={HIGH_THRESHOLD}')
        ax.axhline(y=LOW_THRESHOLD, color='b', linestyle='--', label=f'LOW={LOW_THRESHOLD}')
        ax.set_ylim(0, 4095)
        ax.set_xlim(0, BUFFER_SIZE)
        ax.legend()
        ax.set_title('EMG Bluetooth Live')

        try:
            while True:
                line_plot.set_ydata(values)
                fig.canvas.draw_idle()
                fig.canvas.flush_events()
                await asyncio.sleep(0.05)
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            plt.ioff()
            plt.savefig('emg_ble_live.png', dpi=150)

asyncio.run(main())