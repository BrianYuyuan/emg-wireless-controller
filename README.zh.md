[English](README.md) | [中文(决策解释)](README.zh.md)

## 技术踩坑与经验总结

**排针和杜邦线连接** — 焊接时给 MyoWare 选的的排针太短，导致之后杜邦线根本夹不牢。直接拆焊的话，又怕把板子搞坏，就先用胶带把线缠上去当作临时解法。今后做可穿戴设备的话，如果确定了要连线，其实直接把线焊到焊盘上比用排针+杜邦线靠谱得多。

**Windows 下 DFU 驱动缺失** — 第一次给 Arduino Nano ESP32 烧录固件时报错 "No DFU capable USB device available"。排查发现板子确实进了 DFU 模式（因为设备管理器里能看到 Arduino DFU，但带黄色感叹号），最后发现问题是 Windows 没有对应的驱动。用 Zadig 给 Arduino DFU 装上 WinUSB 之后就彻底解决了。

**切换到 3.3V 供电** — 从 Arduino Uno（5V 系统）迁移到 ESP32-C3 SuperMini（3.3V 系统）之后，我把 MyoWare 的供电也从 5V 换成了 3.3V。其实 MyoWare 支持 3.3–5V 输入，两种都能用，但 ESP32-C3 的 ADC 引脚最高只能承受 3.3V。用 3.3V 供电可以保证 ENV 输出不会超过 ADC 的安全范围。

**接反GND 和 3.3V** — 某次在 SuperMini 上测试时，信号完全是一条直线，MyoWare上面的的绿色指示灯也不随着肌肉收缩变化。当时排查了所有 GPIO 引脚、也确认代码没问题，最后发现是 3.3V 和 GND 的杜邦线插反了...... 改过来之后就正常了。感觉这个bug很难发现，因为接反了 MyoWare 照样能通电（红色电源灯也亮着），只是放大电路不工作了。

**pynput 替代 pyautogui/keyboard** — 一开始用 pyautogui 和 keyboard 库模拟按键，在文本编辑器里没问题，但在 Celeste 这类游戏里完全没反应——游戏收不到任何输入。换成 pynput 就好了，推断应该是 pynput 在更底层的系统层级注入输入。之前 ELEC 220 课程项目里也用 pynput 控制过同一个游戏，验证过确实可行。

**高低双阈值** — 只用一个阈值的话，EMG 信号在阈值附近徘徊时会疯狂误触发。尤其是持续握拳，肌肉疲劳会让信号慢慢往下掉，刚好掉进阈值区间。而加了 HIGH（1200）和 LOW（500）两个阈值之后，信号必须升到 HIGH 以上才算触发，然后必须降到 LOW 以下才算结束，允许再次触发。中间这段死区直接消灭了所有抖动误触。

**基于峰值的相对回落判定** — 即使加了上述功能后，快速连续握拳还是会漏检，因为信号来不及衰减到 LOW 阈值就开始下一次收缩了。这个的解决方法是把固定的 LOW 阈值换成相对判定，信号降到最近一次峰值的 60% 就允许重新触发。这样不管信号幅值大小（前臂的强信号还是面部的弱信号）都能适应，快速输入的响应也改善了。虽然还是比不上手指按键的速度。

## 迭代过程

1. **Arduino Uno + USB 串口** — 先验证了最基本的信号链：MyoWare ENV → analogRead → 串口绘图器。这也是第一次看到肌电信号。 [emg_serial_basic.ino](https://github.com/BrianYuyuan/emg-wireless-controller/blob/main/arduino/emg_serial_basic.ino)
2. **边沿检测 + 滞回** — 在 Python 端加入阈值触发逻辑。先用来玩了 Flappy Bird（握一下 = 扇翅膀），后来又控制了 Celeste（短握 = 跳，长握 = 走）。 [emg_serial_game.py](https://github.com/BrianYuyuan/emg-wireless-controller/blob/main/python/emg_serial_game.py)
3. **双阈值滞回** — 解决了持续握拳时肌肉疲劳导致信号在阈值附近反复抖动的问题。
4. **基于峰值的相对回落** — 解决了快速连续握拳时 ENV 包络衰减太慢、来不及重新触发的问题。
5. **Arduino Nano ESP32 + BLE** — 从 USB 串口迁移到蓝牙，验证了无线传输不影响信号质量，Python 端处理逻辑则完全复用。
6. **ESP32-C3 SuperMini + 扩展板 + LiPo 电池** — 从这里开始完全无线、电池供电，彻底去掉了和电脑之间的物理连接。 [emg_ble_server.ino](https://github.com/BrianYuyuan/emg-wireless-controller/blob/main/arduino/emg_ble_server.ino)
7. **面部肌电验证** — 用湿电极测试了咬合（颞肌）的信号。幅值比前臂弱很多（峰值约 500 vs 前臂约 4000），但调低阈值后完全可以检测到。 [emg_ble_receive.py](https://github.com/BrianYuyuan/emg-wireless-controller/blob/main/python/emg_ble_receive.py)

## 局限性
- **单通道只有一个bit信息。** 一路 EMG 只能区分"有没有在用力"，只能做最简单的二值控制，没法做比例控制，也没法识别多种手势。
- **肌肉速度上限。** 人的肌肉一次收缩-放松最快也要 100–200ms。加上 BLE 延迟（约 50ms）和 ENV 包络衰减时间的话，实际输入速率大概只能到每秒 3–4 次——玩 Flappy Bird 够用，玩音游就真不行。
- **电极接触太脆弱。** 湿式粘贴电极效果不错，但是一次性的。干电极贴在面部皮肤上则非常不稳定（没有买来测试过，不过试了直接裸金属纽扣贴在连上）。所以决定信号质量的主要因素是机械接触压力，而不是信号处理算法。
- **matplotlib 阻塞 asyncio。** 把实时绘图和 BLE 接收放在同一个进程里会引入明显的输入延迟。拆成两个进程倒是可以解决，但会增加复杂度。

## 后续计划
- **干电极可行性验证** — 用导电泡棉或橡胶电极配合头带，测试在颞肌上的干接触稳定性，和湿电极做信噪比对比。
- **BLE HID 键盘模拟** — 把阈值检测逻辑搬到 ESP32 上，让它直接作为蓝牙键盘被识别。这样就完全不需要电脑端装任何软件了，手机、平板、电脑直接把它当蓝牙键盘用，可以直接操纵移动端游戏。
- **多通道 EMG** — 增加第二个电极位点（比如对侧咬肌、不同的面部肌肉，等等），把指令空间从一个 bit 扩展出去。
- **耳机集成** — 把电极嵌入耳机耳罩的海绵里，做成一个可以检测咬合的可穿戴设备（切歌、磨牙检测），不需要额外贴电极。