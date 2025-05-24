import ctypes as ct
import os
from typing import Tuple

import numpy as np

from .camera import Camera
from .throttle import FpsThrottle





class DXCamera(Camera):
    _instance = None

    """ Camera that captures frames from the screen using the ScreenCapture.dll native library
    which is based on Direct3D11CaptureFramePool.  Only one DXCamera can be activate at a time.
    See https://learn.microsoft.com/en-us/uwp/api/windows.graphics.capture.direct3d11captureframepool"""

    def __init__(self, left: int, top: int, width: int, height: int,dll_path, fps: int = 120, capture_cursor: bool = False):
        super().__init__()
        if os.name != "nt":
            raise Exception("This class only works on Windows")

        self._width = width
        self._height = height
        self._left = left
        self._top = top
        self._capture_cursor = capture_cursor

        self.lib = ct.cdll.LoadLibrary(dll_path)

        self._started = False
        self._buffer = None
        self._size = 0

    def __enter__(self):
        if self._instance is None:
            DXCamera._instance = self
        else:
            raise Exception("You can only use 1 instance of DXCamera at a time.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        DXCamera._instance = None
        self.stop()



    def get_bgr_frame(self) -> Tuple[np.ndarray, float]:
        if not self._started:
            hr = self.lib.StartCapture(self._left, self._top, self._width, self._height, self._capture_cursor)
            if hr <= 0:
                raise Exception(f"Failed to start capture, error code {f'{-hr:02x}'}")
            self._size = hr
            self._buffer = ct.create_string_buffer(self._size)  # type: ignore
            self._started = True
            timestamp = self.lib.ReadNextFrame(self._buffer, len(self._buffer))
            image = np.resize(np.frombuffer(self._buffer, dtype=np.uint8), (self._height, self._width, 4))
            # self._throttle.reset()

        timestamp = self.lib.ReadNextFrame(self._buffer, len(self._buffer))
        image = np.resize(np.frombuffer(self._buffer, dtype=np.uint8), (self._height, self._width, 4))
        # strip out the alpha channel
        # image = image[:, :, :3]

        # self._throttle.step()
        return image
    #
    # def get_rgb_frame(self) -> Tuple[np.ndarray, float]:
    #     frame, timestamp = self.get_bgr_frame()
    #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     return frame, timestamp

    def stop(self):
        self._started = False
        self.lib.StopCapture()
        self._buffer = None

    def quit(self):
        DXCamera._instance = None
        self.stop()

