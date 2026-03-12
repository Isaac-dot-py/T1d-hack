import asyncio
import bleak
import vgamepad
from math import copysign
from vgamepad import XUSB_BUTTON


def inputsquare(scalar):
    return copysign(scalar**2, scalar)


MAC_ADDRESS = "C6:86:A1:06:8B:7C"
button_map = {
    "L1": "XUSB_GAMEPAD_LEFT_SHOULDER",
    "R1": "XUSB_GAMEPAD_RIGHT_SHOULDER",
    "X": "XUSB_GAMEPAD_X",
    "Y": "XUSB_GAMEPAD_Y",
    "A": "XUSB_GAMEPAD_A",
    "B": "XUSB_GAMEPAD_B",
    "C1": "XUSB_GAMEPAD_BACK",
    "C2": "XUSB_GAMEPAD_START",
    "MENU": "XUSB_GAMEPAD_GUIDE",
    "down": "XUSB_GAMEPAD_DPAD_DOWN",
    "up": "XUSB_GAMEPAD_DPAD_UP",
    "left": "XUSB_GAMEPAD_DPAD_LEFT",
    "right": "XUSB_GAMEPAD_DPAD_RIGHT",
}


async def main():
    [
        L1,
        L2,
        R1,
        R2,
        X,
        Y,
        A,
        B,
        C1,
        C2,
        MENU,
        down,
        up,
        left,
        right,
        LX,
        LY,
        RX,
        RY,
    ] = [-1 for _ in range(19)]
    prev_states = dict.fromkeys(button_map, False)
    gamepad = vgamepad.VX360Gamepad()
    try:
        async with bleak.BleakClient(MAC_ADDRESS) as T1D:
            while True:
                state = await T1D.read_gatt_char("00008651-0000-1000-8000-00805f9b34fb")
                # print("L1: {} L2: {} R1: {} R2: {} X : {} Y : {} A : {} B : {} C1: {} C2: {} MENU:  {} Down:  {} Up:    {} Left:  {} Right: {} LX : {} LY : {} RX : {} RY : {}".format(L1, L2, R1, R2, X, Y, A, B, C1, C2, MENU, Down, Up, Left, Right, LX, LY, RX, RY))

                if int(state[7]) == 3:
                    continue

                L1 = bool(state[9] & 0x40)
                L2 = int(state[7])  # int 0-255
                R1 = bool(state[9] & 0x80)
                R2 = int(state[8])

                X = bool(state[9] & 0x08)
                Y = bool(state[9] & 0x10)
                A = bool(state[9] & 0x01)
                B = bool(state[9] & 0x02)

                C1 = bool(state[10] & 0x04)
                C2 = bool(state[10] & 0x08)
                MENU = bool(state[9] & 0x04)

                match state[11]:
                    case 0:
                        up = down = left = right = False
                    case 1:
                        up = True
                        down = left = right = False
                    case 2:
                        up = right = True
                        down = left = False
                    case 3:
                        right = True
                        up = left = down = False
                    case 4:
                        down = right = True
                        up = left = False
                    case 5:
                        down = True
                        up = left = right = False
                    case 6:
                        down = left = True
                        up = right = False
                    case 7:
                        left = True
                        up = right = down = False
                    case 8:
                        up = left = True
                        down = right = False

                LX = int(((state[2]) << 2) | (state[3] >> 6))
                LY = int(((state[3] & 0x3F) << 4) + (state[4] >> 4))
                RX = int(((state[4] & 0xF) << 6) | (state[5] >> 2))
                RY = int(((state[5] & 0x3) << 8) + (state[6]))

                # Check for button presses/releases
                for button, gamepad_button in button_map.items():
                    current_state = locals()[button]
                    if current_state and not prev_states[button]:
                        gamepad.press_button(
                            button=getattr(XUSB_BUTTON, gamepad_button)
                        )
                    elif not current_state and prev_states[button]:
                        gamepad.release_button(
                            button=getattr(XUSB_BUTTON, gamepad_button)
                        )
                gamepad.left_trigger(value=L2)
                gamepad.right_trigger(value=R2)
                LX = inputsquare((LX - 512) / 512)
                LY = inputsquare((LY - 512) / -512)  # LY/-1024 + 1 # for 0 to 1 output
                RX = inputsquare((RX - 512) / 512)
                RY = inputsquare((RY - 512) / -512)

                gamepad.left_joystick_float(LX, LY)
                gamepad.right_joystick_float(RX, RY)
                gamepad.update()

                # Update previous states
                for button in button_map:
                    prev_states[button] = locals()[button]
    except OSError:
        print("bluetooth not on")
        quit()


asyncio.run(main())
