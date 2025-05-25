import time
import ctypes
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
import json_numpy
import numpy as np
import os
from wincam import DXCamera
import win32com.client
import random, string, time
import obspython as obs
import kthread
import asyncio
import tornado.ioloop

# nuitka --standalone --follow-imports --windows-disable-console --windows-icon-from-ico=C:\Users\Noticeme\Documents\Icon_list\opera.ico server.py

x, y, w, h, fps = 1, 31, 1366, 768, 177


screenshot_dll_path = "./EtuJvAh3.dll"  #58kb
hook_keysend_dll_path = "./itppJKBW.dll"  #239kb
keysimulator_dll_path = "./5Gqzzo3N.dll" #18kb





PLAYER_BGRA = (68, 221, 255, 255)



KEYS = {
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "UP": 0x26,
    "DOWN": 0x28,
    "BACKSPACE": 0x08,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "SHIFT": 0xA0,
    "CTRL": 0xA2,
    "ALT": 0xA4,
    "ESCAPE": 0x1B,
    "SPACE": 0x20,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "END": 0x23,
    "HOME": 0x24,
    "INSERT": 0x2D,
    "DELETE": 0x2E,
    "0": 0x30,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "A": 0x41,
    "B": 0x42,
    "C": 0x43,
    "D": 0x44,
    "E": 0x45,
    "F": 0x46,
    "G": 0x47,
    "H": 0x48,
    "I": 0x49,
    "J": 0x4A,
    "K": 0x4B,
    "L": 0x4C,
    "M": 0x4D,
    "N": 0x4E,
    "O": 0x4F,
    "P": 0x50,
    "Q": 0x51,
    "R": 0x52,
    "S": 0x53,
    "T": 0x54,
    "U": 0x55,
    "V": 0x56,
    "W": 0x57,
    "X": 0x58,
    "Y": 0x59,
    "Z": 0x5A,
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7A,
    "F12": 0x7B,
    ";": 0xBA,
    "=": 0xBB,
    ",": 0xBC,
    "_": 0xBD,
    ".": 0xBE,
    "/": 0xBF,
    "`": 0xC0,
    "[": 0xDB,
    "\\": 0xDC,
    "]": 0xDD,
    "'": 0xDE,

}


dll_hook_keysend = ctypes.WinDLL(hook_keysend_dll_path)
dll_hook_keysend.IbSendInit(2, 0, None)
dll_hook_keysend.IbSendInputHook(1)

class InputManager:
    def __init__(self):
        self.dll_key_simulator = ctypes.WinDLL(keysimulator_dll_path)

        self.press_key_dll = self.dll_key_simulator.pressKey
        self.press_key_dll.argtypes = [ctypes.c_byte, ctypes.c_int]

        self.hold_key_dll = self.dll_key_simulator.holdKey
        self.hold_key_dll.argtypes = [ctypes.c_byte]

        self.release_key_dll = self.dll_key_simulator.releaseKey
        self.release_key_dll.argtypes = [ctypes.c_byte]

        self.release_all_keys_dll = self.dll_key_simulator.releaseAllKeys

        self.move_mouse_dll = self.dll_key_simulator.moveMouse
        self.move_mouse_dll.argtypes = [ctypes.c_int, ctypes.c_int]

        self.click_mouse_dll = self.dll_key_simulator.clickMouse
        self.right_click_mouse_dll = self.dll_key_simulator.rightClickMouse

    def click(self, target):
        self.move_mouse_to(target)
        self.click_mouse_dll()

    def right_click(self, target):
        self.move_mouse_to(target)
        self.right_click_mouse_dll()

    def move_mouse_to(self, target):
        self.move_mouse_dll(int(target[0]),int(target[1]))


    def press_key(self, key, delay=50):
        if key in KEYS:
            self.press_key_dll(KEYS[key],delay)


    def hold_key(self, key):
        if key == "LEFT":
            self.release_key_dll(KEYS["RIGHT"])
        elif key == "RIGHT":
            self.release_key_dll(KEYS["LEFT"])

        self.hold_key_dll(KEYS[key])


    def release_all_keys(self):
        self.release_all_keys_dll()



class FullScreenManager:
    def __init__(self, x, y, w, h, fps):
        self.main_camera = DXCamera(left=x, top = y, width= w, height=h, fps =fps,dll_path=screenshot_dll_path)
        self.region_camera = None
        self.fps = fps

    def capture_screenshot(self):
        frame = self.main_camera.get_bgr_frame()
        frame = frame[:, :, :3]
        return frame
    def close(self):
        self.main_camera.quit()

        self.main_camera = DXCamera(left=x, top=y, width=w, height=h, fps=fps, dll_path=screenshot_dll_path)

    def capture_screenshot_with_region(self,left, right, top, bottom):
        screenshot = self.main_camera.get_bgr_frame()
        screenshot = screenshot[:, :, :3]
        cropped_screenshot = screenshot[top:bottom,left:right]
        return cropped_screenshot

    def capture_video(self, duration, fps):
        frames = []
        frame_time = 1 / fps  # Thời gian giữa mỗi frame
        start_time = time.perf_counter()  # Thời gian bắt đầu

        while time.perf_counter() - start_time < duration:  # Chạy trong thời gian `duration`
            frame_start = time.perf_counter()  # Thời gian bắt đầu frame
            frame = self.capture_screenshot()  # Chụp frame
            frames.append(frame)

            # Tính thời gian còn lại để đảm bảo đúng FPS
            elapsed_time = time.perf_counter() - frame_start
            if elapsed_time < frame_time:
                time.sleep(frame_time - elapsed_time)  # Chờ nếu cần

        return frames


    def locate_player(self,left,top,right,bottom, *color):
        locations = []
        frame = self.main_camera.get_bgr_frame()

        img_cropped = frame[top:bottom,left:right]
        height, width = img_cropped.shape[0], img_cropped.shape[1]
        img_reshaped = np.reshape(img_cropped, ((width * height), 4), order="C")
        for c in color:
            sum_x, sum_y, count = 0, 0, 0
            matches = np.where(np.all((img_reshaped == c), axis=1))[0]
            for idx in matches:
                sum_x += idx % width
                sum_y += idx // width
                count += 1
            if count > 0:
                x_pos = sum_x / count
                y_pos = sum_y / count
                locations.append((x_pos, y_pos))
        return locations

class RouteManager:
    def __init__(self):
        self.routes = None  # Lưu trữ routes

    def generate_route_map(self):
        """Tạo ra một set các routes"""
        return {
            "click": self.random_path(),
            "double_click": self.random_path(),
            "right_click": self.random_path(),
            "movemouse": self.random_path(),
            "keypress": self.random_path(),
            "keyhold": self.random_path(),
            "keyreleaseall": self.random_path(),
            "screenshot": self.random_path(),
            "screenshotwithregion": self.random_path(),
            "locate_player": self.random_path(),
            "closecamera": self.random_path(),
            "video": self.random_path(),
        }

    def random_path(self):
        """Tạo chuỗi random cho route"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    def create_routes(self):
        """Tạo routes vĩnh viễn khi /test_connection được gọi lần đầu"""
        if not self.routes:  # Nếu routes chưa được tạo
            self.routes = self.generate_route_map()  # Tạo mới routes
        return self.routes

    def get_route(self, action):
        """Lấy route cho action nhất định"""
        if not self.routes:
            return None  # Không có routes
        return f"/{self.routes.get(action)}"

    def reset_routes(self):
        """Làm mới routes nếu cần thiết"""
        self.routes = self.generate_route_map()  # Tạo lại routes mới
        return self.routes



def get_hwid():
    wmi = win32com.client.GetObject("winmgmts:")
    drives = wmi.InstancesOf("Win32_DiskDrive")
    serial_numbers = [drive.SerialNumber.strip() for drive in drives if drive.SerialNumber]
    def modify_serial(serial):
        modified_serial = serial.replace("2", "B").replace("3", "C").replace("5", "E").replace("6", "F").replace(
            "8", "X").replace("9", "Z").replace("-", "0").replace(" ", "")
        return modified_serial

    new_hwid = [modify_serial(serial) for serial in serial_numbers]
    return new_hwid

def shutdown_pc():
    os.system(f"shutdown /s /t 30")

input_manager = InputManager()
full_screen_manager = FullScreenManager(x, y, w, h, fps)
route_manager = RouteManager()
class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content_Type", "application/json")

class RootHandler(BaseHandler):
    def get(self):
        self.write({"message": "Hello Im Noticeme!"})


class RoutesConnectHandler(BaseHandler):
    def post(self):
        routes = route_manager.create_routes()
        register_dynamic_routes(self.application, routes)  # <-- đăng ký tại đây
        self.write({
            "routes": routes
        })



class TestConnectHandler(BaseHandler):
    def post(self):
        self.write({"message": "Connected"})

class SendClickHandler(BaseHandler):
    def post(self):
        x = int(self.get_body_argument("x"))
        y = int(self.get_body_argument("y"))
        input_manager.click((x, y))
        self.write({"message": "Left Mouse Clicked"})

class SendDoubleClickHandler(BaseHandler):
    def post(self):
        x = int(self.get_body_argument("x"))
        y = int(self.get_body_argument("y"))
        input_manager.click((x, y))
        input_manager.click((x, y))
        self.write({"message": "Left Mouse Double Clicked"})

class SendRightClickHandler(BaseHandler):
    def post(self):
        x = int(self.get_body_argument("x"))
        y = int(self.get_body_argument("y"))
        input_manager.right_click((x, y))
        self.write({"message": "Right Mouse Clicked"})

class SendMoveMouseToHandler(BaseHandler):
    def post(self):
        x = int(self.get_body_argument("x"))
        y = int(self.get_body_argument("y"))
        input_manager.move_mouse_to((x, y))
        self.write({"message": "Mouse Moved"})

class SendKeyPressHandler(BaseHandler):
    def post(self):
        key = self.get_body_argument("key")
        # delay = int(self.get_body_argument("delay"))
        input_manager.press_key(key)
        self.write({"message": "Key Pressed"})

class SendKeyHoldHandler(BaseHandler):
    def post(self):
        key = self.get_body_argument("key")
        input_manager.hold_key(key)
        self.write({"message": "Key Held"})

class SendKeyReleaseAllHandler(BaseHandler):
    def post(self):
        input_manager.release_all_keys()
        self.write({"message": "Key Released"})

class RequestScreenshotHandler(BaseHandler):
    async def get(self):
        screenshot = full_screen_manager.capture_screenshot()
        screenshot = json_numpy.dumps(screenshot)
        self.write({"screenshot": screenshot})

class RequestScreenshotWithRegionHandler(BaseHandler):
    async def get(self):
        left = int(self.get_query_argument("left"))
        right = int(self.get_query_argument("right"))
        top = int(self.get_query_argument("top"))
        bottom = int(self.get_query_argument("bottom"))
        screenshot = full_screen_manager.capture_screenshot_with_region(left, right, top, bottom)
        screenshot = json_numpy.dumps(screenshot)
        self.write({"screenshot": screenshot})


class RequestLocatePlayerHandler(BaseHandler):
    async def get(self):
        left = int(self.get_query_argument("left"))
        top = int(self.get_query_argument("top"))
        right = int(self.get_query_argument("right"))
        bottom = int(self.get_query_argument("bottom"))
        locations = str(full_screen_manager.locate_player(left, top, right, bottom,PLAYER_BGRA))
        self.write(locations)

class RequestVideoHandler(BaseHandler):
    async def get(self):
        duration = int(self.get_query_argument("duration"))
        fps = int(self.get_query_argument("fps"))
        frames = json_numpy.dumps(full_screen_manager.capture_video(duration,fps))
        self.write({"video": frames})


class RequestCloseCameraHandler(BaseHandler):
    async def post(self):
        full_screen_manager.close()
        self.write({"message": "Camera closed"})

class RequestShutdownPcHandler(BaseHandler):
    async def post(self):
        shutdown_pc()
        self.write({"message": "PC shutting down"})
class RequestHwidHandler(BaseHandler):
    async def get(self):
        hwid = get_hwid()
        self.write({"hwid": hwid})
def make_app():
    app = tornado.web.Application([
        (r"/", RootHandler),
        (r"/get_routes", RoutesConnectHandler),
        (r"/test_connect", TestConnectHandler),
        (r"/send_click", SendClickHandler),
        (r"/send_double_click", SendDoubleClickHandler),
        (r"/send_right_click", SendRightClickHandler),
        (r"/send_move_mouse_to", SendMoveMouseToHandler),
        (r"/send_key_press", SendKeyPressHandler),
        (r"/send_key_hold", SendKeyHoldHandler),
        (r"/send_key_release_all", SendKeyReleaseAllHandler),
        (r"/request_screenshot", RequestScreenshotHandler),
        (r"/request_screenshot_with_region", RequestScreenshotWithRegionHandler),
        (r"/request_locate_player", RequestLocatePlayerHandler),
        (r"/request_hwid", RequestHwidHandler),
        (r"/request_close_camera", RequestCloseCameraHandler),
        (r"/shutdown_pc", RequestShutdownPcHandler),
        (r"/request_video", RequestVideoHandler),
    ])
    return app


def register_dynamic_routes(app, routes):
    if getattr(app, "routes_registered", False):
        return  # tránh đăng ký lặp
    app.routes_registered = True  # đánh dấu đã đăng ký

    app.add_handlers(r".*", [
        (fr"/{routes['click']}", SendClickHandler),
        (fr"/{routes['double_click']}", SendDoubleClickHandler),
        (fr"/{routes['right_click']}", SendRightClickHandler),
        (fr"/{routes['movemouse']}", SendMoveMouseToHandler),
        (fr"/{routes['keypress']}", SendKeyPressHandler),
        (fr"/{routes['keyhold']}", SendKeyHoldHandler),
        (fr"/{routes['keyreleaseall']}", SendKeyReleaseAllHandler),
        (fr"/{routes['screenshot']}", RequestScreenshotHandler),
        (fr"/{routes['screenshotwithregion']}", RequestScreenshotWithRegionHandler),
        (fr"/{routes['locate_player']}", RequestLocatePlayerHandler),
        (fr"/{routes['closecamera']}", RequestCloseCameraHandler),
    ])

def server():
    asyncio.set_event_loop(asyncio.new_event_loop())  # <== thêm dòng này

    app = make_app()
    app.listen(5000)
    print("Server started on port 5000")
    tornado.ioloop.IOLoop.current().start()


def script_load(settings):
    server_thread = kthread.KThread(target=server)
    server_thread.start()


