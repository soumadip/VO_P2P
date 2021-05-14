import numpy as np
import cv2
import base64

from modules .params import *

class VideoStream :
    def __init__ (self, device = 0) :
        self .INTERVAL = VIDEO_FRAME_INTERVAL
        self .webcam = cv2 .VideoCapture (device)
        self .captured = True
        self .stream = self .video_stream ()
        self .shape = self .get_next_frame () .shape
        self .cx, self .cy = tuple (int (v / RESIZE) for v in self .shape [ : 2]) 

    def set_remote_frame_shape (self, shape):
        self .remote_frame_shape = shape

        self .rx, self .ry, _ = self .remote_frame_shape
        self .remote_frame = np .zeros (self .remote_frame_shape, dtype = "B")
        self .corner_frame = np .zeros (self .remote_frame_shape, dtype = "B")

    def video_stream (self) :
        while True:
            _, frame = self .webcam .read()
            yield frame

    def get_next_frame (self) :
        self .latest_frame = next (self .stream)
        return self .latest_frame

    def get_remote_frame_shape (self) :
        return self .remote_frame_shape

    def get_frame_shape (self) :
        return self .shape

    def store_frame (self, frame) :
        self .remote_frame = frame

    def get_data_to_send (self) :
        frame = self .get_next_frame ()
        encoded, buf = cv2 .imencode ('.jpg', frame)
        image = base64 .b64encode (buf)
        return image

    def process_received_data (self, data) :
        buf = base64 .b64decode (data)
        frame = cv2 .imdecode (np .frombuffer (buf, dtype = "B"), 1)
        self .store_frame (frame)

    def get_output (self) :
        corner = cv2 .resize (self .latest_frame, dsize = (self .cy, self .cx), interpolation = cv2 .INTER_CUBIC)
        self .corner_frame [self .rx - self .cx : , self .ry - self .cy : ] = cv2 .flip (corner, 1)
        f = self .remote_frame .copy ()
        f [f .shape [0] - self .cx : , f .shape [1] - self .cy : ] = np .zeros ((self .cx, self .cy, 3), dtype = "B")
        return f + self .corner_frame


    def render (self, title) :
        cv2 .imshow (f"[{title}]Remote, press 'q' to quit", self .get_output ())

        key = cv2 .waitKey (1)
        if key == ord ('q') :
            print ("[V] 'q' Pressed.")
            raise Exception

    def rendering (self, title = "") :
        try :
            while (self .captured) :
                self .render (title)
        except Exception as e :
            print ("[V] Rendering ended")
            self .stop ()

    def release (self) :
        if self .captured :
            self .webcam .release ()
            print ("[V] Release video source")
    
    def stop (self) :
        self .release ()
        cv2 .destroyAllWindows ()
        print ("[V] Destroying Windows")
        self .captured =  False

    def __exit__ (self) :
        self .stop ()

