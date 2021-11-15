import io
import picamera  # Camera

#### THIS IS IMPORTANT FOR LIFE STREAMING ####
import logging
import socketserver
from threading import Condition
from http import server

#### THIS IS IMPORTANT FOR IMAGE PROCESSING ####
import numpy as np
import cv2
import serial
import time

# set-up
frame_rate = 5

PAGE = """\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<img src="stream.mjpg" width="640" height="480" style="width:100%;height:100%;" />
</body>
</html>
"""


def detect_color(frame):
    # setting values for base colors
    b = frame[:, :, 0]
    g = frame[:, :, 1]
    r = frame[:, :, 2]

    # computing the mean
    b_mean = np.mean(b)
    g_mean = np.mean(g)
    r_mean = np.mean(r)

    max_color = np.amax([b_mean, g_mean, r_mean])

    # displaying the most prominent color
    if (b_mean == max_color):
        color = 'B'
    elif (g_mean == max_color):
        color = 'G'
    elif (r_mean == max_color):
        color = 'R'

    return color



class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    frame_i = 0

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame

                        ### The image is encoded in bytes,
                        ### needs to be converted to e.g. numpy array
                        frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8),
                                             cv2.IMREAD_COLOR)

                        ###############
                        ## HERE CAN GO ALL IMAGE PROCESSING
                        ###############
                        color = detect_color(frame)
                        if color == 'R':
                            ser.write(b'r')
                        elif color == 'G':
                            ser.write(b'g')
                        elif color == 'B':
                            ser.write(b'b')

                        ### and now we convert it back to JPEG to stream it
                        _, frame = cv2.imencode('.JPEG', frame)

                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


ser = serial.Serial()
ser.baudrate = 19200
ser.port = '/dev/ttyUSB0'
ser.open()
time.sleep(2.00)

# Open the camera and stream a low-res image (width 640, height 480 px)
with picamera.PiCamera(resolution='640x480', framerate=frame_rate) as camera:
    camera.vflip = True  # Flips image vertically, depends on your camera mounting
    camera.awb_gains = (1.2, 1.5)
    camera.awb_mode = 'off'
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)  # port 8000
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()




Last login: Tue Nov  9 17:12:56 on ttys003

The default interactive shell is now zsh.
To update your account to use zsh, please run `chsh -s /bin/zsh`.
For more details, please visit https://support.apple.com/kb/HT208050.
(base) C02CT16JML7H:~ hey2$ ssh pi@192.168.1.219
^C
(base) C02CT16JML7H:~ hey2$ arp -a
? (192.168.1.68) at 12:cc:e8:85:d8:df on en0 ifscope [ethernet]
? (192.168.1.219) at e4:5f:1:4a:24:29 on en0 ifscope [ethernet]
? (192.168.1.255) at ff:ff:ff:ff:ff:ff on en0 ifscope [ethernet]
? (224.0.0.251) at 1:0:5e:0:0:fb on en0 ifscope permanent [ethernet]
? (239.255.255.250) at 1:0:5e:7f:ff:fa on en0 ifscope permanent [ethernet]
broadcasthost (255.255.255.255) at ff:ff:ff:ff:ff:ff on en0 ifscope [ethernet]
(base) C02CT16JML7H:~ hey2$ ssh pi@192.168.1.219
ssh: connect to host 192.168.1.219 port 22: Connection refused
(base) C02CT16JML7H:~ hey2$ ssh pi@192.168.1.219
pi@192.168.1.219's password:
Linux raspberrypi 5.10.63-v7l+ #1459 SMP Wed Oct 6 16:41:57 BST 2021 armv7l

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Tue Nov  9 16:54:19 2021 from 192.168.1.171
pi@raspberrypi:~ $ ls
final
pi@raspberrypi:~ $ cd final/
pi@raspberrypi:~/final $ ls
camera_detect_color.py  camera_detect.py  __pycache__  send_command.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 17:51:17] "GET / HTTP/1.1" 301 -
192.168.1.171 - - [09/Nov/2021 17:51:17] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 17:51:18] "GET /stream.mjpg HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 17:51:18] code 404, message Not Found
192.168.1.171 - - [09/Nov/2021 17:51:18] "GET /favicon.ico HTTP/1.1" 404 -
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 157, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ ls
camera_detect_color.py  camera_detect.py  __pycache__  send_command.py
pi@raspberrypi:~/final $ rm camera_detect.py
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 17:53:27] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 17:53:27] "GET /stream.mjpg HTTP/1.1" 200 -
OpenCV Error: Assertion failed (!buf.empty() && buf.isContinuous()) in imdecode_, file /build/opencv-L65chJ/opencv-3.2.0+dfsg/modules/imgcodecs/src/loadsave.cpp, line 637
WARNING:root:Removed streaming client ('192.168.1.171', 52229): /build/opencv-L65chJ/opencv-3.2.0+dfsg/modules/imgcodecs/src/loadsave.cpp:637: error: (-215) !buf.empty() && buf.isContinuous() in function imdecode_

192.168.1.171 - - [09/Nov/2021 17:53:32] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 17:53:32] "GET /stream.mjpg HTTP/1.1" 200 -
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
G
G
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
G
G
G
G
G
G
G
G
R
G
G
R
R
G
R
G
G
R
R
R
R
R
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 157, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 17:57:56] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 17:57:56] "GET /stream.mjpg HTTP/1.1" 200 -
OpenCV Error: Assertion failed (!buf.empty() && buf.isContinuous()) in imdecode_, file /build/opencv-L65chJ/opencv-3.2.0+dfsg/modules/imgcodecs/src/loadsave.cpp, line 637
WARNING:root:Removed streaming client ('192.168.1.171', 52538): /build/opencv-L65chJ/opencv-3.2.0+dfsg/modules/imgcodecs/src/loadsave.cpp:637: error: (-215) !buf.empty() && buf.isContinuous() in function imdecode_

192.168.1.171 - - [09/Nov/2021 17:58:06] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 17:58:06] "GET /stream.mjpg HTTP/1.1" 200 -
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
B
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
Corrupt JPEG data: 32764 extraneous bytes before marker 0xd9
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^CTraceback (most recent call last):
R
  File "camera_detect_color.py", line 157, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:03:49] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:03:49] "GET /stream.mjpg HTTP/1.1" 200 -
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
(480, 640, 3)
R
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 159, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:07:56] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:07:56] "GET /stream.mjpg HTTP/1.1" 200 -
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^CR
Traceback (most recent call last):
  File "camera_detect_color.py", line 162, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:09:37] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:09:37] "GET /stream.mjpg HTTP/1.1" 200 -
R
R
R
192.168.1.171 - - [09/Nov/2021 18:09:37] "GET /index.html HTTP/1.1" 200 -
R
192.168.1.171 - - [09/Nov/2021 18:09:37] "GET /stream.mjpg HTTP/1.1" 200 -
R
WARNING:root:Removed streaming client ('192.168.1.171', 53262): [Errno 32] Broken pipe
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^XR
R
R
R
R
R
R
R
R
R
R
R
R
R
^CR
Traceback (most recent call last):
  File "camera_detect_color.py", line 162, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
^[[A^[[A^[[Api@raspberrypnanoal $ python3 camera_dete^C_color.py
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:10:24] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:10:24] "GET /stream.mjpg HTTP/1.1" 200 -
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^XR
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 162, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
^C
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:10:54] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:10:54] "GET /stream.mjpg HTTP/1.1" 200 -
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^XR
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 162, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
^C
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:12:08] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:12:08] "GET /stream.mjpg HTTP/1.1" 200 -
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 163, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
R
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:16:30] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:16:30] "GET /stream.mjpg HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:16:31] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:16:31] "GET /stream.mjpg HTTP/1.1" 200 -
OpenCV Error: Assertion failed (!buf.empty() && buf.isContinuous()) in imdecode_, file /build/opencv-L65chJ/opencv-3.2.0+dfsg/modules/imgcodecs/src/loadsave.cpp, line 637
WARNING:root:Removed streaming client ('192.168.1.171', 53705): /build/opencv-L65chJ/opencv-3.2.0+dfsg/modules/imgcodecs/src/loadsave.cpp:637: error: (-215) !buf.empty() && buf.isContinuous() in function imdecode_

OpenCV Error: Assertion failed (!buf.empty() && buf.isContinuous()) in imdecode_, file /build/opencv-L65chJ/opencv-3.2.0+dfsg/modules/imgcodecs/src/loadsave.cpp, line 637
WARNING:root:Removed streaming client ('192.168.1.171', 53707): /build/opencv-L65chJ/opencv-3.2.0+dfsg/modules/imgcodecs/src/loadsave.cpp:637: error: (-215) !buf.empty() && buf.isContinuous() in function imdecode_

192.168.1.171 - - [09/Nov/2021 18:16:32] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:16:32] "GET /stream.mjpg HTTP/1.1" 200 -
WARNING:root:Removed streaming client ('192.168.1.171', 53711): name 'crop_start' is not defined
192.168.1.171 - - [09/Nov/2021 18:16:33] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:16:34] "GET /stream.mjpg HTTP/1.1" 200 -
WARNING:root:Removed streaming client ('192.168.1.171', 53714): name 'crop_start' is not defined
192.168.1.171 - - [09/Nov/2021 18:16:35] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:16:35] "GET /stream.mjpg HTTP/1.1" 200 -
WARNING:root:Removed streaming client ('192.168.1.171', 53717): name 'crop_start' is not defined
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 165, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:18:13] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:18:13] "GET /stream.mjpg HTTP/1.1" 200 -
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
192.168.1.171 - - [09/Nov/2021 18:18:20] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:18:20] "GET /stream.mjpg HTTP/1.1" 200 -
R
WARNING:root:Removed streaming client ('192.168.1.171', 53802): [Errno 32] Broken pipe
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
R
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
R
G
R
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
G
^CG
Traceback (most recent call last):
  File "camera_detect_color.py", line 165, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 265, in open
    self.fd = os.open(self.portstr, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
FileNotFoundError: [Errno 2] No such file or directory: '/dev/ttyUSB0'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "camera_detect_color.py", line 157, in <module>
    ser.open()
  File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 268, in open
    raise SerialException(msg.errno, "could not open port {}: {}".format(self._port, msg))
serial.serialutil.SerialException: [Errno 2] could not open port /dev/ttyUSB0: [Errno 2] No such file or directory: '/dev/ttyUSB0'
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:28:25] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:28:25] "GET /stream.mjpg HTTP/1.1" 200 -
[142.404672, 166.737024]
[142.934464, 167.596736]
[143.886272, 167.798272]
[144.393536, 167.84]
[144.549824, 168.015168]
[144.876224, 168.205056]
[144.870592, 168.624448]
[144.532928, 169.0544]
[144.53312, 169.133056]
[144.539456, 169.41216]
[145.03424, 169.86912]
[145.040832, 169.879808]
[145.520576, 170.255168]
[145.74816, 170.595904]
[145.598656, 170.542464]
[145.519296, 170.553152]
[145.5696, 170.56448]
[145.515776, 170.53344]
[145.301248, 170.521856]
[145.334848, 170.506176]
[145.31968, 170.441024]
[145.147776, 170.378496]
[145.020352, 170.462784]
[145.061312, 170.493504]
[145.076544, 170.50688]
[144.903552, 170.420864]
[145.076992, 170.594176]
[145.254912, 170.604736]
[145.350912, 170.680768]
[145.382912, 170.728448]
[145.048192, 170.575488]
[144.857984, 170.620032]
[144.752896, 170.43776]
[144.81504, 170.49664]
[144.7488, 170.507968]
[145.069184, 170.764544]
[144.95776, 170.63168]
[144.916096, 170.658048]
[145.358336, 170.468992]
[145.612288, 170.453376]
[145.750016, 170.455872]
[145.832512, 170.391936]
[145.33632, 170.586304]
[145.182016, 170.650816]
[144.993024, 170.572224]
[144.912, 170.54912]
[145.39712, 170.531136]
[145.481088, 170.584768]
[145.510272, 170.578048]
[145.69088, 170.580544]
[145.2528, 170.6592]
[145.093824, 170.741184]
[144.899776, 170.758016]
[144.85408, 170.786368]
[145.038528, 170.653312]
[145.155712, 170.672064]
[145.175552, 170.46336]
[145.107968, 170.492992]
[144.826368, 170.559552]
[144.65088, 170.668096]
[144.574592, 170.754368]
[144.913664, 170.774848]
[145.10592, 170.715456]
[145.21664, 170.697728]
[145.301056, 170.742592]
[145.039552, 170.633664]
[145.06944, 170.785088]
[144.858432, 170.60416]
[144.929344, 170.631296]
[145.137984, 170.446144]
[145.370688, 170.647296]
[145.38496, 170.430208]
[145.432384, 170.44896]
[144.975744, 170.504]
[144.741632, 170.723776]
[144.767424, 170.745344]
[144.567808, 170.608256]
[144.633472, 170.615232]
[144.708352, 170.758464]
[144.671872, 170.607552]
[144.544256, 170.504704]
[144.629184, 170.460352]
[144.807296, 170.6656]
[144.738688, 170.510272]
[144.728896, 170.498944]
[143.878528, 170.48096]
[143.66464, 170.352256]
[143.585664, 170.286272]
[143.908736, 170.186176]
[144.327104, 170.168896]
[144.421696, 170.108032]
[144.79648, 169.848768]
[145.124352, 169.8992]
[145.10752, 169.978816]
[145.011904, 169.877504]
[144.831232, 169.86848]
[144.885056, 169.775808]
[144.824704, 169.853952]
[144.692928, 169.789888]
[144.435328, 169.727808]
[144.107584, 169.997248]
[143.747904, 170.06688]
[143.684032, 170.074944]
[143.365056, 170.002944]
[143.195008, 169.845952]
[143.139904, 169.96128]
[143.036608, 169.870464]
[142.865728, 169.770816]
[143.095552, 170.019136]
[143.220096, 170.126592]
[143.119232, 170.233664]
[143.424256, 170.134592]
[143.771136, 170.010752]
[143.866496, 170.12864]
[143.872, 170.0832]
[143.334272, 170.095552]
[142.767872, 170.073856]
[143.101568, 170.324672]
[143.279744, 170.164608]
[143.667328, 170.256]
[143.73216, 170.098624]
[143.995904, 170.291648]
[144.087424, 170.086272]
[144.268864, 170.252928]
[144.222016, 170.170048]
[144.295232, 170.10656]
[144.158912, 170.045056]
[144.144448, 170.109504]
[144.184192, 170.308032]
[144.075904, 170.104832]
[144.045184, 170.157312]
[143.849664, 170.227712]
[143.829888, 170.321984]
[143.732928, 170.285504]
[143.7808, 170.318784]
[143.700544, 170.38784]
[143.588096, 170.410048]
[143.41824, 170.406848]
[143.494976, 170.371328]
[143.781056, 170.481152]
[143.94336, 170.382848]
[143.9664, 170.423936]
[143.808896, 170.334336]
[143.768576, 170.282432]
[143.901888, 170.428736]
[143.706816, 170.23296]
[143.87168, 170.257728]
[143.949568, 170.339456]
[143.930176, 170.206272]
[143.9584, 170.188608]
[144.389824, 170.301312]
[144.531392, 170.434688]
[144.343936, 170.315264]
[144.598144, 170.2768]
[144.595968, 170.271296]
[144.442752, 170.34176]
[144.520768, 170.298112]
[144.582912, 170.30688]
[144.437824, 170.256832]
[144.33536, 170.231232]
[144.29376, 170.137984]
[144.091136, 170.152256]
[144.239424, 170.2768]
[144.267136, 170.379712]
[144.132864, 170.332992]
[144.251712, 170.403008]
[144.011648, 170.302912]
[143.896832, 170.224256]
[143.888896, 170.356096]
[143.94432, 170.428928]
[143.814976, 170.424128]
[144.017152, 170.6064]
[144.143744, 170.467264]
[144.231744, 170.597376]
[143.98368, 170.303232]
[144.165056, 170.301824]
[144.256448, 170.399616]
[144.192256, 170.491072]
[144.1968, 170.452224]
[144.201024, 170.533184]
[144.119296, 170.431424]
[144.208384, 170.288]
[144.160064, 170.322176]
[144.287104, 170.337856]
[144.302912, 170.42688]
[144.358912, 170.3984]
[144.405248, 170.401152]
[144.625536, 170.527488]
[144.583936, 170.373184]
[144.611968, 170.48608]
[144.053824, 170.419072]
[144.033664, 170.514304]
[143.867264, 170.50112]
[143.786688, 170.431296]
[144.413888, 170.452096]
[144.373504, 170.467008]
[144.45088, 170.342144]
[144.295936, 170.31264]
[144.22048, 170.29568]
[144.146432, 170.24672]
[144.083584, 170.211968]
[144.169536, 170.357824]
[144.130176, 170.34272]
[144.258752, 170.434688]
[144.066624, 170.32736]
[144.271808, 170.334528]
[144.166464, 170.397184]
[144.076224, 170.248128]
[144.144384, 170.297472]
[144.006912, 170.191296]
[144.336128, 170.438976]
[144.202496, 170.378816]
[144.140032, 170.311424]
[143.982336, 170.297984]
[143.955328, 170.368448]
[144.100608, 170.39648]
[144.012224, 170.358848]
[144.019776, 170.279168]
[144.149248, 170.3328]
[144.093312, 170.162752]
[144.241856, 170.308736]
[144.367488, 170.368192]
[144.348992, 170.484096]
[144.3024, 170.444736]
[144.458176, 170.378304]
[144.116416, 170.314496]
[144.203392, 170.25376]
[144.125632, 170.328448]
[144.11712, 170.350976]
[144.127808, 170.3728]
[144.125056, 170.421056]
[144.299712, 170.448512]
[144.294208, 170.340352]
[144.222656, 170.493056]
[144.25216, 170.323648]
[144.204544, 170.442176]
[144.114944, 170.333504]
[144.111104, 170.329536]
[144.05632, 170.32736]
[144.036608, 170.195904]
[143.770816, 170.41632]
[143.497152, 170.473536]
[143.245696, 170.384128]
[143.443776, 170.537792]
[144.288576, 170.506752]
[144.347904, 170.375424]
[144.462656, 170.336576]
[144.387456, 170.33792]
[144.3824, 170.47584]
[144.36512, 170.489728]
[144.342336, 170.467008]
[144.176384, 170.337664]
[143.989056, 170.311168]
[143.981376, 170.276224]
[143.98528, 170.259136]
[144.149632, 170.349568]
[144.360064, 170.380032]
[144.427776, 170.575872]
[144.300992, 170.467968]
[144.548992, 170.289344]
[144.563392, 170.372736]
[144.78144, 170.342016]
[144.636864, 170.275456]
[144.414592, 170.361984]
[144.270528, 170.465344]
[144.106176, 170.423616]
[144.203904, 170.437184]
[143.83328, 170.239488]
[143.760896, 170.31936]
[143.672448, 170.22368]
[143.485952, 170.158336]
[143.816384, 170.231168]
[143.901376, 170.296256]
[143.957952, 170.358784]
[144.032448, 170.310144]
[144.29248, 170.284608]
[144.502272, 170.433216]
[144.523264, 170.262912]
[144.62016, 170.233472]
[144.19968, 170.24992]
[144.129024, 170.39552]
[144.193408, 170.361024]
[144.265664, 170.420416]
[144.644416, 170.462848]
[145.420288, 170.574016]
[146.170688, 170.458816]
[146.850304, 170.482624]
[147.240896, 170.248064]
[147.68512, 170.308352]
[148.423424, 170.31872]
[148.854848, 170.36416]
[149.270016, 170.34144]
[149.479552, 170.403904]
[149.405184, 170.770304]
[148.878464, 170.763264]
[147.77728, 170.80896]
[147.37216, 170.801216]
[147.273216, 170.952064]
[146.774656, 170.66336]
[146.429376, 170.705792]
[146.191296, 170.8336]
[146.089984, 170.914368]
[145.913728, 170.777664]
[145.556992, 170.881984]
[145.443392, 170.606592]
[145.060672, 170.486656]
[145.323328, 170.49952]
[145.427328, 170.54176]
[145.483776, 170.499712]
[145.890624, 170.832064]
[146.049024, 170.835456]
[146.232832, 170.921856]
[146.300608, 170.988864]
[146.124608, 170.943872]
[146.121792, 171.112448]
[145.937088, 171.093504]
[145.969408, 171.008576]
[145.830272, 171.006272]
[146.058176, 171.098176]
[146.20384, 171.205888]
[145.99104, 171.05344]
[146.097728, 171.035136]
[146.283968, 171.0688]
[146.426816, 171.131776]
[146.414336, 171.13856]
[146.41984, 171.116992]
[146.418176, 171.043968]
[146.44032, 171.06784]
[146.530688, 171.104576]
[146.510336, 171.119168]
[146.69632, 171.04256]
[146.742976, 170.887552]
[146.796736, 170.913088]
[146.767744, 170.796608]
[146.34688, 171.09664]
[146.279808, 171.152512]
[146.16544, 171.114368]
[145.915584, 170.960576]
[145.806464, 170.922816]
[145.794112, 170.916288]
[145.683776, 170.874176]
[145.993024, 171.056896]
[145.971776, 171.121152]
[145.89856, 170.98048]
[145.836736, 170.914432]
[145.869632, 170.966464]
[145.803904, 170.927488]
[145.886784, 170.994816]
[145.965888, 170.967232]
[146.028544, 170.929216]
[145.957312, 170.945408]
[145.789056, 170.799808]
[145.631552, 170.83936]
[145.385664, 170.636928]
[145.292864, 170.46208]
[144.96128, 170.396672]
[144.691136, 170.01856]
[144.461504, 169.903552]
[144.293376, 169.437504]
[143.978944, 169.241728]
[143.985408, 168.479872]
[143.960704, 167.95776]
[143.83328, 167.396544]
[143.481344, 165.67328]
[143.417664, 164.893952]
[143.419968, 164.275584]
[143.265408, 163.396096]
[143.085184, 162.404608]
[142.884416, 162.28]
[142.844928, 162.387136]
[142.595584, 162.284992]
[142.37024, 161.94144]
[142.17152, 161.829952]
[142.293888, 161.964352]
[142.175104, 161.768448]
[142.152256, 161.992832]
[142.506176, 162.080064]
[142.950656, 162.289344]
[142.896192, 162.140416]
[143.428864, 162.576832]
[143.057664, 162.8064]
[143.027584, 163.112]
[143.063552, 163.270784]
[143.19648, 163.74432]
[143.192768, 163.99776]
[143.291008, 164.20864]
[143.18752, 164.117568]
[143.131328, 164.32736]
[143.011392, 164.355648]
[143.02208, 164.37312]
[142.9248, 164.1696]
[142.828288, 163.939072]
[142.574464, 163.671168]
[142.655488, 163.663232]
[142.425472, 163.266176]
[142.360192, 162.680576]
[142.377472, 162.372096]
[142.352448, 161.968896]
[142.489984, 161.581312]
[142.30816, 160.717184]
[142.294144, 160.549568]
[142.083648, 160.35104]
[141.943616, 159.866688]
[141.704576, 159.39296]
[141.566912, 158.739584]
[141.683712, 158.528064]
[141.524096, 158.071936]
[141.542784, 157.666304]
[141.11424, 157.483968]
[140.880832, 157.581248]
[140.676224, 157.373504]
[140.597888, 157.22528]
[140.386688, 157.264576]
[140.095616, 157.182784]
[140.38176, 157.44576]
[140.2368, 157.725184]
[140.446016, 158.007552]
[141.052352, 158.795776]
[141.785536, 159.325184]
[143.129088, 160.181632]
[143.505408, 160.804352]
[144.104256, 161.301312]
[144.530368, 161.570048]
[145.03552, 162.115584]
[145.261312, 162.633792]
[145.030656, 162.844608]
[144.854208, 162.905088]
[145.044032, 163.076992]
[145.223808, 162.946048]
[144.858048, 145.048832]
[144.578496, 145.477888]
[145.252032, 145.366912]
[145.61984, 145.14688]
[145.713152, 145.156608]
[145.616128, 145.606848]
[145.925696, 145.81792]
[146.219776, 146.178624]
[146.386432, 146.543232]
[146.83456, 147.82656]
[146.922752, 148.261632]
[147.672064, 149.301568]
[147.830912, 150.14592]
[148.35168, 152.139328]
[148.601408, 152.835904]
[148.726592, 153.607232]
[148.897792, 154.50912]
[148.956096, 154.77632]
[149.321344, 155.392832]
[149.523968, 155.772288]
[150.078464, 156.432128]
[150.559104, 156.718592]
[150.92544, 156.946112]
[151.039488, 157.174016]
[151.5696, 157.767104]
[151.83904, 158.176064]
[152.061376, 158.607296]
[152.379456, 159.024512]
[152.245504, 159.024192]
[152.106816, 159.015744]
[152.13664, 159.067328]
[152.100288, 159.089408]
[152.069376, 159.059008]
[152.076864, 159.06272]
[152.0448, 159.037184]
[151.936, 158.870464]
[151.771264, 158.968704]
[151.6768, 158.644416]
[151.644672, 158.636928]
[151.42176, 158.461248]
[151.36192, 158.39936]
[150.778432, 158.219072]
[150.711936, 158.17088]
[150.398528, 158.181184]
[150.12256, 158.133312]
[149.848064, 158.07648]
[149.990016, 158.1168]
[150.193152, 158.0496]
[150.010304, 158.043328]
[150.093056, 158.055424]
[150.249216, 158.167488]
[150.544832, 158.192128]
[150.631296, 158.069376]
[151.249984, 158.307968]
[151.74784, 158.20832]
[151.831936, 158.280064]
[151.870528, 158.23456]
[151.700928, 158.19136]
[151.432448, 158.20416]
[151.345344, 158.332864]
[151.27488, 158.19584]
[151.386048, 158.2768]
[151.332416, 158.184512]
[151.519744, 158.434496]
[151.464768, 158.390528]
[151.283904, 158.403712]
[151.206144, 158.43104]
[151.263616, 158.383488]
[151.357824, 158.311488]
[151.652096, 158.13312]
[151.86432, 158.181568]
[151.761664, 158.183424]
[151.741568, 158.208576]
[151.725184, 158.122048]
[151.728512, 158.053632]
[151.676096, 158.176256]
[151.571968, 158.221312]
[151.80544, 158.444928]
[151.595776, 158.405824]
[151.581952, 158.4112]
[151.550528, 158.33152]
[151.589952, 158.306304]
[151.650944, 158.440832]
[151.49344, 158.328192]
[152.05792, 158.429376]
[152.180352, 158.332352]
[152.27968, 158.40032]
[152.218688, 158.222208]
[152.205504, 158.385472]
[152.36736, 158.514112]
[152.370304, 158.477696]
[152.272, 158.503872]
[151.943744, 158.511232]
[151.839168, 158.612416]
[151.865152, 158.52288]
[151.663872, 158.48608]
[151.984512, 158.736192]
[151.945984, 158.492544]
[151.974784, 158.490816]
[152.006528, 158.484288]
[152.273664, 158.396288]
[152.544128, 158.572096]
[152.488128, 158.5536]
[152.741632, 158.663552]
[151.97824, 158.55232]
[151.55264, 158.373312]
[151.456512, 158.521344]
[151.386304, 158.45952]
[151.860416, 158.422528]
[152.363712, 158.460544]
[152.406528, 158.394368]
[152.6896, 158.42816]
[152.466816, 158.497984]
[152.726016, 158.727616]
[152.538432, 158.656576]
[152.710848, 158.775616]
[152.28, 158.627904]
[152.382144, 158.781504]
[152.252544, 158.83104]
[152.4064, 158.663872]
[152.786944, 158.70176]
[153.1568, 158.664704]
[153.362432, 158.644352]
[152.929984, 158.581504]
[152.939328, 158.726784]
[152.726016, 158.675264]
[152.672448, 158.676864]
[152.720576, 158.629952]
[152.856768, 158.6528]
[152.761664, 158.799808]
[152.56384, 158.652992]
[152.736704, 158.724544]
[152.914496, 158.719744]
[152.907584, 158.712768]
[152.75936, 158.528384]
[152.804224, 158.680512]
[152.884352, 158.734528]
[152.886464, 158.693312]
[152.92128, 158.758336]
[152.545408, 158.765248]
[152.526336, 158.76]
[152.2848, 158.942016]
[152.296128, 158.905216]
[152.489024, 158.914496]
[152.402816, 158.71136]
[152.489408, 158.744384]
[152.410816, 158.758592]
[152.401984, 158.684864]
[152.156928, 158.738112]
[152.223488, 158.82112]
[152.35872, 158.786176]
[152.454272, 158.613952]
[152.30336, 158.717952]
[152.467584, 158.790464]
[152.293696, 158.78272]
[152.236352, 158.664576]
[152.350016, 158.877376]
[152.08896, 158.681536]
[152.263808, 158.919936]
[152.191872, 158.671616]
[152.178432, 158.570112]
[152.07648, 158.554304]
[152.356736, 158.577216]
[152.851072, 158.83168]
[152.885632, 158.814592]
[152.97024, 158.712576]
[152.61728, 158.899264]
[152.298176, 158.832832]
[152.288192, 158.884608]
[152.003392, 158.89088]
[152.034432, 158.86112]
[152.019328, 158.880128]
[152.022656, 158.86112]
[152.327744, 158.637056]
[152.658624, 158.71104]
[152.833024, 158.696704]
[152.791808, 158.614784]
[152.659072, 158.73664]
[152.256384, 158.710464]
[152.300096, 158.70816]
[152.249344, 158.6832]
[152.249856, 158.626368]
[152.35712, 158.689792]
[152.24864, 158.636288]
[152.313472, 158.703168]
[152.343616, 158.565376]
[152.492032, 158.664384]
[152.47712, 158.700352]
[152.37056, 158.649984]
[152.078848, 158.637504]
[151.640064, 158.620928]
[151.611008, 158.6704]
[151.816192, 158.673344]
[152.017024, 158.674752]
[152.204224, 158.631616]
[152.122624, 158.691008]
[152.017984, 158.53024]
[151.929344, 158.661056]
[151.714624, 158.574784]
[151.677184, 158.617792]
[152.096832, 158.572224]
[152.467584, 158.626432]
[152.630912, 158.577344]
[152.059392, 158.627904]
[151.853568, 158.55328]
[151.61824, 158.524352]
[151.499456, 158.5392]
[152.054016, 158.597376]
[152.541632, 158.638848]
[152.466688, 158.721088]
[152.655104, 158.671808]
[152.420928, 158.720384]
[152.119808, 158.695424]
[152.261952, 158.705024]
[152.069376, 158.540928]
[152.089216, 158.876288]
[152.057984, 158.835584]
[152.018176, 158.904448]
[152.252992, 158.759808]
[152.456576, 158.723648]
[152.378624, 158.5856]
[152.43424, 158.608448]
[152.240512, 158.5424]
[152.249024, 158.534144]
[152.338304, 158.651136]
[152.158464, 158.588224]
[152.200768, 158.67136]
[152.213056, 158.598592]
[152.276864, 158.788224]
[152.297024, 158.675904]
[152.44928, 158.674304]
[152.632, 158.72736]
[152.561088, 158.696]
[152.706688, 158.707968]
[152.510208, 158.521152]
[152.572288, 158.393536]
[152.523456, 158.324096]
[152.49824, 158.502144]
[152.58176, 158.690368]
[152.590592, 158.686592]
[152.47328, 158.65088]
[152.549696, 158.68064]
[152.424768, 158.51392]
[152.386688, 158.611456]
[151.84512, 158.663168]
[151.779776, 158.704704]
[151.666176, 158.618432]
[152.153536, 158.690176]
[152.399616, 158.480768]
[152.469568, 158.579264]
[152.469504, 158.579968]
[152.485184, 158.65792]
[152.413696, 158.58848]
[152.43232, 158.712832]
[152.66048, 158.698944]
[152.57536, 158.642816]
[152.734784, 158.72096]
[152.78592, 158.680384]
[152.611008, 158.856192]
[152.60032, 158.834368]
[152.625728, 158.717376]
[152.553344, 158.761472]
[153.328384, 158.48608]
[153.16352, 158.376192]
[153.259584, 158.359296]
[152.755712, 158.423808]
[152.45056, 158.471744]
[152.472192, 158.490304]
[152.730368, 158.608768]
[152.831616, 158.786624]
[152.96512, 158.748864]
[153.119104, 158.782144]
[153.248768, 158.830464]
[152.612096, 158.686528]
[152.421568, 158.512512]
[152.159488, 158.138432]
[152.040896, 157.923456]
[152.06528, 157.714496]
[151.823104, 157.534016]
[151.994944, 156.621824]
[151.770624, 156.26144]
[151.488, 155.80416]
[151.511744, 155.511296]
[151.191296, 155.430272]
[151.476352, 155.770496]
[151.67488, 155.976896]
[151.434176, 156.230976]
[151.656576, 156.942016]
[151.512832, 156.900096]
[151.450944, 157.38528]
[152.001152, 157.770368]
[152.45184, 158.115584]
[152.625216, 158.01472]
[152.718592, 158.296256]
[152.924608, 158.375296]
[152.972096, 158.587584]
[153.049856, 158.619264]
[153.2048, 158.896832]
[153.243712, 158.825408]
[153.270144, 158.89632]
[153.479104, 159.021184]
[153.506752, 159.02784]
[153.775552, 158.776768]
[153.819904, 158.920576]
[153.648896, 158.656768]
[153.833088, 158.880192]
[153.813312, 170.173632]
[153.252864, 171.876224]
[152.478144, 171.6752]
[151.884608, 171.441216]
[151.2432, 171.37088]
[150.138944, 171.36608]
[150.462016, 171.349056]
[151.064064, 171.729984]
[150.861952, 171.387776]
[150.7408, 171.29696]
[150.772352, 171.552384]
[150.868736, 171.683904]
[150.575552, 171.351104]
[150.674496, 171.60192]
[150.694464, 171.414912]
[150.862528, 171.454592]
[151.066496, 171.20192]
[151.45376, 170.830016]
[151.999424, 170.713344]
[152.22496, 170.28736]
[152.266368, 170.243456]
[151.369472, 170.352768]
[150.571712, 170.299904]
[150.057024, 170.243008]
[149.846848, 170.157632]
[149.66368, 170.01504]
[149.550464, 170.058432]
[149.380608, 170.001856]
[149.498048, 170.012288]
[149.132352, 170.046976]
[149.183232, 170.214976]
[149.186752, 170.274048]
[149.146944, 170.232704]
[149.695488, 170.214784]
[149.627712, 170.143168]
[149.494528, 169.911104]
[149.139264, 169.920128]
[149.134144, 169.973632]
[149.193344, 170.17792]
[149.038336, 169.970176]
[148.932736, 170.064768]
[148.771968, 170.194496]
[148.66112, 170.127616]
[148.654848, 170.220288]
[148.39456, 170.257856]
[148.432128, 170.266368]
[148.376, 170.23776]
[148.470272, 170.193792]
[148.229952, 170.199424]
[148.22176, 170.35104]
[148.31104, 170.218304]
[148.387456, 170.285376]
[148.51616, 170.391744]
[148.601664, 170.454976]
[148.421888, 170.332992]
[149.030528, 170.347776]
[149.188288, 170.249536]
[149.297152, 170.207488]
[149.166976, 170.044864]
[148.741504, 170.14944]
[148.518336, 170.394112]
[148.42336, 170.259648]
[148.318016, 170.29376]
[148.410112, 170.320448]
[148.618624, 170.376192]
[148.563008, 170.37152]
[148.676352, 170.269312]
[148.75232, 170.41632]
[148.673984, 170.508416]
[148.736576, 170.356736]
[148.630976, 170.24576]
[148.304192, 170.34944]
[148.226624, 170.44256]
[148.144448, 170.401728]
[148.073472, 170.407232]
[148.506432, 170.460608]
[148.447296, 170.427392]
[148.515136, 170.481408]
[148.680128, 170.37504]
[148.711552, 170.284416]
[148.856512, 170.371456]
[148.94496, 170.198656]
[148.729344, 170.182208]
[148.871552, 170.35232]
[148.631488, 170.165888]
[148.765056, 170.37408]
[148.928, 170.23648]
[148.95552, 170.286592]
[149.019968, 170.27232]
[148.997248, 170.174976]
[148.766656, 170.282368]
[148.737856, 170.175936]
[148.626816, 170.176832]
[148.698752, 170.232576]
[148.620736, 170.227072]
[148.68928, 170.381952]
[148.605184, 170.225984]
[148.661568, 170.315136]
[148.675328, 170.309312]
[148.900032, 170.50304]
[148.75712, 170.38368]
[148.838464, 170.408256]
[148.772672, 170.4704]
[149.01664, 170.339648]
[149.040768, 170.446656]
[149.002304, 170.364544]
[148.72, 170.554048]
[148.432256, 170.651584]
[148.45088, 170.548416]
[148.26688, 170.630016]
[148.193536, 170.487168]
[148.19616, 170.654848]
[148.37792, 170.544]
[148.3344, 170.48864]
[148.19936, 170.312064]
[148.17824, 170.274944]
[147.908224, 170.062464]
[147.807808, 169.639488]
[147.86016, 169.6016]
[147.542144, 169.305408]
[147.560576, 169.395264]
[147.73376, 169.200768]
[148.05216, 169.365696]
[148.33568, 169.44256]
[148.393664, 169.398592]
[148.125888, 169.4752]
[147.929344, 169.462336]
[147.862336, 169.541248]
[148.032576, 169.439168]
[148.148416, 169.439744]
[148.272128, 169.421952]
[148.312448, 169.51136]
[148.246912, 169.615424]
[148.3952, 169.644288]
[148.222848, 169.604928]
[148.333504, 169.550144]
[148.479744, 169.66784]
[148.51072, 169.528256]
[148.404928, 169.442816]
[147.88896, 169.314368]
[147.746176, 169.20992]
[147.512896, 169.266176]
[147.953088, 169.828608]
[147.892672, 170.028096]
[147.71872, 170.043648]
[147.8944, 170.122816]
[148.160704, 170.201536]
[148.204608, 170.33664]
[148.30624, 170.37952]
[148.24352, 170.316608]
[147.958848, 170.13664]
[148.076544, 170.20128]
[147.855552, 170.089984]
[147.932544, 169.986496]
[148.09728, 170.208832]
[147.957248, 170.06016]
[148.139776, 170.116352]
[148.293952, 170.18016]
[148.318272, 170.054912]
[148.162112, 169.947904]
[148.165248, 169.96]
[148.186176, 170.033024]
[147.631808, 169.572224]
[146.760192, 168.953536]
[146.999744, 168.626752]
[146.926912, 168.249152]
[146.902272, 168.144512]
[146.662976, 168.123456]
[146.546816, 168.183552]
[146.509824, 168.508672]
[146.659072, 168.567104]
[146.867136, 169.017024]
[147.31168, 169.249408]
[147.648512, 169.483264]
[147.626304, 169.318592]
[147.827776, 169.556544]
[147.830656, 169.605888]
[147.833344, 169.679744]
[148.047616, 169.734464]
[149.140608, 170.151552]
[149.273856, 170.27392]
[149.375616, 170.3888]
[149.228608, 170.417984]
[148.805504, 170.2656]
[148.990528, 170.403136]
[149.286208, 170.6048]
[149.244672, 170.497728]
[149.417536, 170.544]
[149.371776, 170.453504]
[149.476864, 170.617408]
[149.297152, 170.4528]
[149.304832, 170.477248]
[148.923008, 170.432576]
[148.535936, 170.418112]
[148.388928, 170.274752]
[148.016192, 170.18176]
[148.340032, 170.242432]
[148.464576, 170.17376]
[148.394432, 170.235392]
[148.527552, 170.2448]
[148.572992, 170.26848]
[148.518848, 170.079616]
[148.733888, 170.26464]
[148.56064, 170.255744]
[148.607232, 170.2432]
[148.610432, 170.248512]
[148.99328, 170.238272]
[149.121792, 170.080512]
[149.483392, 170.305664]
[149.206912, 170.347008]
[149.278656, 170.555776]
[148.96544, 170.483456]
[149.051776, 170.571008]
[148.960384, 170.55488]
[148.92384, 170.534592]
[148.797184, 170.518016]
[148.774144, 170.472704]
[149.141248, 170.52352]
[149.158976, 170.408384]
[149.292224, 170.392256]
[149.363712, 170.33216]
[149.351744, 170.436736]
[149.461184, 170.719552]
[149.232896, 170.5776]
[149.420544, 170.6528]
[149.23008, 170.641536]
[149.37344, 170.780416]
[149.43488, 170.912384]
[149.222528, 170.683584]
[149.092864, 170.699456]
[149.144064, 170.580672]
[149.07264, 170.607168]
[149.60576, 170.723712]
[149.6672, 170.550208]
[149.595968, 170.552704]
[149.214912, 170.70912]
[149.077312, 170.830144]
[149.165888, 170.69824]
[148.9632, 170.60576]
[148.993408, 170.621632]
[149.125376, 170.722496]
[149.159872, 170.643072]
[149.074304, 170.441984]
[149.14112, 170.525696]
[149.272192, 170.623424]
[149.088192, 170.469248]
[149.316096, 170.529344]
[149.434048, 170.53376]
[149.46368, 170.677568]
[149.602048, 170.59232]
[149.599616, 170.605824]
[149.155648, 170.533952]
[149.1712, 170.681984]
[148.939008, 170.476224]
[148.851264, 170.470912]
[149.188352, 170.553856]
[149.35328, 170.491264]
[149.25568, 170.429248]
[149.360064, 170.443648]
[149.620864, 170.32288]
[149.761792, 170.264768]
[149.968896, 170.402112]
[149.978368, 170.28256]
[149.671744, 170.21376]
[149.272448, 170.239104]
[149.222784, 170.179008]
[149.197504, 170.11552]
[149.354624, 170.315392]
[149.409664, 170.416064]
[149.390144, 170.306368]
[149.543488, 170.393344]
[149.398656, 170.237632]
[149.527616, 170.269632]
[149.692928, 170.255488]
[149.77664, 170.1248]
[149.584128, 170.198208]
[149.510784, 170.1728]
[150.001728, 170.23424]
[150.167744, 170.036032]
[150.445568, 170.227776]
[150.400192, 169.972288]
[150.274688, 170.103936]
[150.32992, 170.067712]
[150.437056, 170.25184]
[150.140608, 170.25472]
[149.621056, 170.156992]
[149.521984, 169.980416]
[149.4992, 170.12032]
[149.70208, 170.129792]
[149.887808, 170.204096]
[149.852288, 170.110528]
[149.996352, 170.222592]
[149.925312, 170.014144]
[149.966976, 170.100672]
[149.987136, 170.030976]
[150.243264, 170.115008]
[150.295296, 170.213824]
[150.22976, 170.202944]
[150.356864, 170.165248]
[150.64512, 170.164992]
[151.128896, 170.297216]
[151.341696, 170.336384]
[151.345408, 170.245504]
[151.516992, 170.242496]
[151.451648, 170.22432]
[151.16992, 170.30784]
[151.085184, 170.187776]
[151.075456, 170.174784]
[150.905024, 170.336448]
[150.863872, 170.306816]
[150.82208, 170.516352]
[150.873088, 170.444288]
[151.055872, 170.394944]
[151.192384, 170.42368]
[151.07232, 170.225664]
[151.199296, 170.324992]
[151.538944, 170.287296]
[151.821504, 170.354432]
[151.815872, 170.188864]
[151.913664, 170.208704]
[151.774976, 170.289984]
[151.784704, 170.333056]
[151.798272, 170.271616]
[151.669632, 170.27232]
[151.805056, 170.163328]
[152.027456, 169.99584]
[152.137344, 170.092416]
[151.440064, 170.06528]
[151.343424, 170.340544]
[151.029952, 170.25344]
[150.958528, 170.102528]
[151.276608, 170.180608]
[151.29248, 170.233472]
[151.331776, 170.239936]
[151.34336, 170.16576]
[151.21952, 170.02336]
[150.837376, 169.96768]
[150.93952, 170.063232]
[150.995712, 169.989632]
[151.181952, 170.038976]
[151.162816, 170.101056]
[151.266944, 170.004992]
[150.819456, 170.021888]
[150.692608, 169.98432]
[150.828992, 170.094848]
[150.639488, 169.931776]
[150.677248, 170.08608]
[150.650048, 170.082496]
[150.6048, 170.069824]
[150.619904, 170.100032]
[150.740992, 170.097088]
[150.965184, 170.20256]
[150.901248, 170.101504]
[150.985088, 170.10432]
[151.161856, 170.073216]
[151.20224, 170.164736]
[151.308416, 170.03104]
[151.306048, 170.101056]
[151.385344, 170.011904]
[151.578048, 169.97952]
[151.630016, 169.98592]
[151.456384, 169.937472]
[151.456064, 169.94432]
[151.634688, 170.167552]
[151.573312, 170.054656]
[151.32224, 170.06784]
[151.217664, 169.97248]
[151.103872, 170.033216]
[151.060672, 169.970944]
[150.926592, 169.932288]
[151.137024, 169.946112]
[151.30144, 170.07456]
[151.220032, 169.94656]
[151.33824, 170.016704]
[151.17088, 170.032448]
[151.216896, 170.06496]
[151.105408, 170.044352]
[151.096704, 169.943296]
[151.3712, 170.138432]
[151.6064, 170.247616]
[151.576192, 170.14816]
[151.35584, 170.16768]
[150.699776, 170.178688]
[150.50528, 170.290688]
[150.102976, 170.08608]
[149.9296, 170.065344]
[149.843392, 170.166208]
[150.000064, 170.203584]
[150.028352, 170.284096]
[150.242496, 170.356032]
[150.261504, 170.346944]
[150.322816, 170.5008]
[150.317184, 170.437504]
[151.035136, 170.388544]
[151.379776, 170.338304]
[151.597376, 170.352384]
[152.142912, 170.440064]
[152.445056, 170.515712]
[153.161984, 170.762688]
[153.64448, 170.731008]
[154.099968, 170.719488]
[153.797056, 170.745024]
[153.928384, 170.665408]
[154.987648, 170.730176]
[155.964736, 170.9744]
[156.532992, 170.92672]
[156.660352, 170.692224]
[157.016, 170.780032]
[156.924928, 170.611712]
[157.252736, 170.903424]
[157.14368, 170.68448]
[157.446592, 170.71424]
[156.931328, 170.367744]
[156.850944, 170.309824]
[156.64576, 170.164032]
[156.670336, 170.30176]
[156.375872, 170.156928]
[156.478848, 170.190976]
[156.201536, 170.099264]
[156.020736, 170.085248]
[155.967808, 170.201344]
[155.42816, 169.963392]
[154.00288, 169.938688]
[153.664192, 169.825472]
[153.169344, 169.934336]
[152.47744, 169.642752]
[150.914624, 169.621056]
[150.58016, 169.491584]
[150.456128, 169.5344]
[150.227648, 169.470912]
[150.158272, 169.543744]
[150.142656, 169.618624]
[150.24992, 169.740288]
[150.196928, 169.648704]
[150.147456, 169.675904]
[150.010048, 169.641024]
[150.055616, 169.744832]
[149.912448, 169.827456]
[149.489408, 169.824512]
[149.15488, 169.84352]
[149.05376, 169.912512]
[148.855616, 169.800448]
[149.232704, 169.831808]
[149.579584, 169.897664]
[149.643968, 169.852224]
[149.669184, 169.78976]
[149.30048, 169.893248]
[149.128128, 170.010048]
[148.985792, 169.939968]
[148.5824, 169.88448]
[149.34656, 169.816384]
[149.539392, 169.857728]
[149.627904, 169.687296]
[149.834112, 169.682688]
[149.517504, 169.745088]
[149.508608, 169.87168]
[149.214528, 169.7808]
[149.124928, 169.838912]
[148.92096, 169.901568]
[149.058496, 169.992832]
[148.998912, 169.909056]
[149.200704, 169.910208]
[149.343168, 169.88832]
[149.464256, 169.774016]
[149.589824, 169.890432]
[149.522368, 169.892288]
[149.7376, 170.090624]
[149.744576, 169.955392]
[149.469696, 170.094272]
[148.460096, 170.888832]
[146.849408, 171.981056]
[146.183744, 171.742592]
[145.206336, 171.653632]
[144.043136, 171.858624]
[141.976896, 172.91872]
[139.0464, 177.079744]
[147.32288, 161.820672]
[161.922304, 142.015424]
[167.632064, 129.639744]
[173.12672, 86.477888]
[174.505088, 90.490816]
[174.187456, 112.968704]
[137.55392, 133.996288]
[142.564992, 232.01152]
[168.924224, 215.318208]
[211.645696, 179.120896]
[231.710592, 159.915072]
[238.097984, 167.597376]
[217.11584, 188.801664]
[198.470784, 196.370368]
[187.961216, 175.598976]
[182.92096, 165.248]
[174.822336, 162.250688]
[174.871552, 161.47904]
[179.129024, 161.781632]
[181.056192, 161.59456]
[180.925248, 161.4608]
[180.237888, 160.746944]
[179.523072, 159.799488]
[178.531264, 159.434624]
[178.309696, 159.585216]
[177.73632, 159.396992]
[177.366208, 160.023808]
[177.458624, 160.511232]
[177.6544, 161.139904]
[177.470848, 161.4256]
[177.421376, 161.677952]
[177.38528, 161.755136]
[177.20416, 161.845184]
[176.625472, 161.25248]
[175.78816, 160.61376]
[175.422848, 160.302656]
[175.297088, 160.262976]
[174.837824, 159.739008]
[174.676736, 159.71904]
[174.632896, 159.692608]
[174.847232, 159.830208]
[174.569536, 159.593344]
[174.648064, 159.568704]
[174.872512, 159.698368]
[174.79264, 159.641728]
[174.871872, 159.660864]
[174.747264, 159.585536]
[174.829056, 159.53952]
[174.82912, 159.692032]
[174.736256, 159.544576]
[174.702976, 159.55136]
[174.514944, 159.494976]
[174.402112, 159.542912]
[174.337024, 159.454528]
[174.237056, 159.433088]
[174.334976, 159.532736]
[174.400832, 159.572288]
[174.301184, 159.463424]
[174.3184, 159.461824]
[174.128, 159.499968]
[174.157568, 159.406912]
[174.005312, 159.42976]
[174.08288, 159.459968]
[174.197312, 159.377536]
[174.247616, 159.376256]
[174.284736, 159.39104]
[174.259392, 159.346112]
[174.375168, 159.459904]
[174.409344, 159.513536]
[174.336256, 159.508352]
[174.332224, 159.398528]
[174.300352, 159.392128]
[174.231168, 159.431808]
[174.026304, 159.132544]
[174.022016, 159.269568]
[174.02144, 159.299712]
[173.976704, 159.123456]
[173.802048, 159.245952]
[173.778752, 159.298304]
[173.610304, 159.32896]
[173.576448, 159.240384]
[173.528384, 159.18464]
[173.579776, 159.302272]
[173.683008, 159.232512]
[173.787776, 159.263808]
[173.767616, 159.263104]
[173.92224, 159.381056]
[174.001024, 159.41728]
[174.0304, 159.398912]
[174.195968, 159.379008]
[174.428352, 159.44512]
[174.686016, 159.606528]
[174.517568, 159.376768]
[174.677824, 159.534272]
[174.56736, 159.4832]
[174.529664, 159.45024]
[174.43936, 159.333376]
[174.3824, 159.375616]
[174.452928, 159.412544]
[174.47712, 159.430656]
[174.437824, 159.503936]
[174.51552, 159.547712]
[174.512896, 159.517888]
[174.42688, 159.507648]
[174.469952, 159.489728]
[174.4608, 159.514944]
[174.697792, 159.617088]
[174.492096, 159.452352]
[174.510528, 159.436288]
[174.795392, 159.598656]
[174.821504, 159.5408]
[175.066688, 159.652288]
[175.139904, 159.609024]
[175.051392, 159.585216]
[175.008128, 159.669888]
[174.630592, 159.429376]
[174.599232, 159.429632]
[174.642368, 159.280128]
[174.833472, 159.363072]
[175.03904, 159.405952]
[174.524992, 146.550272]
[172.011584, 136.859008]
[169.20736, 120.430144]
[168.209664, 99.38208]
[170.392704, 111.372288]
[135.882624, 109.276224]
[123.060352, 100.228224]
[111.786304, 83.011136]
[114.83456, 80.91264]
[119.294208, 82.829888]
[122.317056, 83.874496]
[135.057152, 84.32384]
[136.387072, 85.1536]
[130.437376, 85.66112]
[126.698944, 85.495744]
[122.769536, 95.510016]
[117.883648, 113.816704]
[113.892096, 123.735808]
[108.50144, 135.0784]
[116.702016, 133.633536]
[113.726016, 123.25472]
[109.848576, 119.504192]
[117.08864, 122.032768]
[152.484928, 126.2]
[158.673728, 124.62368]
[161.253376, 119.774848]
[165.18656, 115.871616]
[165.93024, 115.572736]
[166.110784, 116.005824]
[167.446016, 117.102016]
[168.066496, 118.092032]
[168.888384, 119.359232]
[169.389888, 120.022912]
[168.512448, 118.463296]
[168.20256, 117.923392]
[167.966336, 117.356352]
[168.304576, 116.955328]
[169.16128, 116.866176]
[170.65056, 116.63552]
[170.32416, 115.690816]
[169.592192, 114.84736]
[170.135872, 115.536128]
[169.346304, 115.98784]
[167.726208, 115.847936]
[164.908736, 115.437504]
[163.578752, 114.300416]
[163.495936, 113.698112]
[163.821824, 113.800256]
[164.970112, 115.448768]
[164.66624, 116.432128]
[162.859584, 119.537664]
[161.746112, 120.037952]
[161.693568, 119.292992]
[165.63552, 120.232832]
[172.022592, 118.933248]
[173.338176, 118.307712]
[173.405248, 118.023104]
[173.015616, 117.795648]
[172.206848, 118.053696]
[172.447616, 118.145088]
[172.99072, 118.303296]
[172.885376, 118.06688]
[172.42176, 117.780672]
[169.344896, 116.162112]
[152.875968, 110.801856]
[150.827072, 102.453824]
[186.94304, 110.53856]
[141.824448, 167.490624]
[97.593024, 80.590656]
[97.0784, 81.225536]
[101.07488, 82.672]
[109.928384, 85.710016]
[112.956992, 87.495744]
[115.652096, 89.284992]
[119.5232, 90.55776]
[123.094144, 92.952512]
[122.42592, 94.828352]
[120.996928, 94.746112]
[120.475264, 94.323392]
[120.23456, 93.687872]
[120.573184, 92.921856]
[119.56736, 92.521152]
[120.214976, 92.022656]
[122.859136, 90.896704]
[126.622336, 90.7184]
[129.121728, 91.3296]
[132.485824, 92.558016]
[136.838144, 93.189056]
[152.47552, 94.409344]
[156.966016, 94.567936]
[162.992704, 95.904256]
[160.5792, 97.250496]
[162.022976, 97.73056]
[144.102976, 106.743104]
[127.684736, 116.1008]
[124.909824, 120.42464]
[143.712192, 119.65248]
[196.346752, 114.513216]
[212.211008, 117.446144]
[208.348736, 110.089728]
[206.00096, 103.007232]
[201.963904, 150.941696]
[191.769728, 164.12768]
[186.440384, 168.475264]
[173.51616, 162.302528]
[170.243072, 159.909952]
[167.270464, 158.610624]
[164.393152, 159.095552]
[161.094208, 159.825216]
[161.262656, 159.677312]
[162.479552, 159.492928]
[166.580992, 158.289856]
[167.200832, 158.073728]
[168.45824, 158.379456]
[169.911616, 159.44672]
[170.162368, 160.223104]
[169.132224, 159.606976]
[168.985152, 159.648576]
[169.989376, 161.516672]
[169.614016, 160.853568]
[169.282432, 160.610688]
[171.599872, 161.441536]
[171.03616, 160.994752]
[170.596544, 160.860032]
[170.132352, 160.517056]
[169.929664, 160.299776]
[169.56864, 159.703488]
[169.732352, 159.925376]
[169.782912, 159.976192]
[169.861568, 159.913344]
[169.633664, 160.104512]
[169.51424, 159.985024]
[169.411008, 159.992704]
[169.541504, 159.998592]
[169.561024, 160.044224]
[169.509056, 160.097024]
[169.51136, 159.959616]
[169.533824, 159.958592]
[169.602048, 159.914048]
[169.369024, 159.770368]
[169.380608, 159.797632]
[169.270592, 159.818496]
[169.236672, 159.823744]
[169.04928, 159.659712]
[169.09824, 159.678976]
[169.335808, 159.89536]
[169.374592, 159.759872]
[169.29024, 159.715136]
[169.168448, 159.662208]
[169.060352, 159.556096]
[168.505856, 159.171776]
[168.131968, 158.73664]
[167.936064, 158.6368]
[167.810176, 158.523776]
[167.817088, 158.59232]
[167.706688, 158.522048]
[167.754752, 158.571264]
[167.904704, 158.739328]
[167.834496, 158.928448]
[168.047488, 158.88032]
[168.140864, 158.849408]
[168.438208, 159.140992]
[168.265216, 159.149696]
[168.306816, 159.34912]
[168.450432, 159.675328]
[168.467456, 159.539584]
[168.473408, 159.579712]
[168.554048, 159.623424]
[168.699904, 159.851328]
[168.713792, 159.9552]
[168.613248, 159.944064]
[168.736448, 160.159232]
[168.297152, 159.824192]
[168.23968, 159.861184]
[168.227008, 160.017152]
[167.85152, 159.644992]
[167.91232, 159.687872]
[167.563008, 159.50176]
[167.603904, 159.334656]
[167.563328, 159.172928]
[167.676992, 159.260032]
[167.502016, 159.11136]
[167.222656, 159.104256]
[167.205312, 158.990656]
[167.069312, 158.842944]
[167.405248, 158.79136]
[167.356672, 158.773632]
[167.39808, 158.606528]
[167.293312, 158.487296]
[167.193024, 158.55072]
[166.99648, 158.710656]
[166.907648, 158.480768]
[167.014016, 158.612416]
[167.235648, 158.597696]
[167.13984, 158.539136]
[167.031872, 158.382976]
[167.03168, 158.616512]
[166.897984, 158.684032]
[166.915456, 158.861312]
[166.836672, 158.8128]
[166.6528, 158.776896]
[166.69536, 158.876352]
[166.440768, 158.788544]
[166.56032, 158.895808]
[167.22368, 158.876672]
[167.227008, 158.829632]
[167.235904, 158.791488]
[167.176384, 158.735488]
[166.991424, 158.661888]
[167.171072, 158.7024]
[167.035712, 158.665088]
[167.041472, 158.820928]
[166.799296, 158.87904]
[166.814592, 158.90848]
[166.593408, 158.848768]
[166.776, 158.86816]
[166.783488, 158.904064]
[166.78656, 158.888576]
[166.873536, 158.88896]
[166.710656, 158.979648]
[166.702912, 159.073408]
[166.55424, 158.93216]
[166.53536, 159.056192]
[166.8032, 158.951936]
[167.1696, 158.97856]
[166.972096, 158.728192]
[167.121792, 158.803008]
[167.062592, 158.758976]
[167.104384, 159.053632]
[167.063488, 158.87168]
[167.178752, 158.947904]
[167.257472, 158.862528]
[167.244288, 158.910272]
[167.383552, 158.897344]
[167.309184, 158.75648]
[167.032512, 158.806592]
[167.012224, 158.955072]
[166.87584, 158.835136]
[166.871488, 158.914816]
[166.988032, 158.782656]
[167.280192, 158.858816]
[167.132416, 158.597504]
[167.219072, 158.716992]
[167.377984, 158.810304]
[167.272896, 158.826688]
[167.25248, 158.687616]
[167.296512, 158.77632]
[167.195456, 158.770368]
[166.991936, 158.758144]
[167.23328, 158.883648]
[167.006144, 158.787904]
[166.95424, 158.769472]
[166.948032, 158.795584]
[166.963264, 158.746816]
[166.748096, 158.750976]
[166.649792, 158.828992]
[166.60736, 158.73024]
[166.56576, 158.660288]
[166.831744, 158.850368]
[166.870784, 158.703744]
[166.979648, 159.012736]
[167.014848, 158.837632]
[166.953728, 158.846144]
[166.862336, 158.974336]
[167.28128, 159.04512]
[167.140032, 158.91008]
[166.982144, 158.83264]
[167.02208, 158.830208]
[167.275456, 158.942976]
[167.508032, 159.064896]
[167.530304, 158.963712]
[167.637248, 158.974976]
[167.336512, 159.00544]
[167.3024, 158.8672]
[167.267008, 158.846336]
[167.136064, 159.072704]
[166.800384, 158.960448]
[166.823296, 159.036352]
[166.811968, 158.96608]
[167.008, 158.83552]
[167.113088, 159.017728]
[167.143616, 158.862912]
[167.122496, 158.809984]
[167.028544, 158.899328]
[167.222272, 159.042304]
[167.18144, 158.90272]
[166.955968, 159.032256]
[166.925632, 158.987136]
[166.872448, 159.02528]
[166.75712, 158.881856]
[166.92832, 159.066176]
[166.761088, 158.896384]
[166.870272, 158.892928]
[167.279552, 159.00096]
[167.77376, 158.933184]
[167.787968, 158.961408]
[167.491712, 159.014592]
[167.020416, 158.903488]
[167.079808, 158.82144]
[166.987392, 158.81088]
[167.016576, 158.846592]
[167.083648, 158.97536]
[167.068032, 158.87296]
[167.02176, 158.838528]
[167.146496, 158.825472]
[167.306688, 158.704384]
[167.401536, 158.852928]
[167.321984, 158.696896]
[167.382592, 158.89152]
[167.363392, 158.969088]
[167.248384, 158.894848]
[167.306432, 158.763712]
[167.298112, 159.065856]
[167.297856, 158.840128]
[167.224128, 158.93824]
[167.07872, 158.80288]
[166.963712, 158.821952]
[166.996096, 158.759424]
[166.931776, 158.726912]
[167.295872, 158.806976]
[167.286912, 158.874048]
[167.266112, 158.802048]
[167.38176, 158.956352]
[167.356224, 158.96512]
[167.38592, 159.10944]
[167.306944, 159.013248]
[167.351168, 159.07168]
[167.1808, 158.963328]
[167.219712, 159.143936]
[167.146112, 159.006272]
[167.109952, 159.092544]
[167.312768, 159.038784]
[167.299584, 159.05536]
[167.250176, 158.883968]
[167.258432, 158.91136]
[167.016, 158.970688]
[166.854976, 159.007488]
[166.967168, 159.17056]
[166.997248, 158.998144]
[167.3184, 158.959424]
[167.384704, 158.980224]
[167.178112, 158.873856]
[167.082432, 158.996416]
[166.973056, 158.94464]
[166.948736, 159.00672]
[166.85312, 158.900288]
[166.858624, 158.853376]
[167.054592, 159.018176]
[166.929856, 158.9248]
[167.080064, 158.86176]
[166.815424, 158.906944]
[166.725568, 159.023744]
[166.74912, 158.925184]
[166.697408, 158.899904]
[166.729472, 158.994752]
[166.75904, 158.931136]
[167.095808, 159.112896]
[166.9424, 159.044096]
[167.20928, 159.169536]
[167.248, 158.971392]
[167.505984, 159.042304]
[167.839616, 159.309184]
[167.990528, 159.310976]
[167.997696, 159.161344]
[168.299136, 159.200192]
[168.315968, 159.095616]
[168.246784, 158.8784]
[168.45248, 158.788608]
[168.289216, 158.703488]
[168.300608, 158.690816]
[168.223232, 158.671808]
[168.289664, 158.493184]
[168.310464, 158.61024]
[168.237248, 158.593984]
[168.18624, 158.460672]
[167.9472, 158.412224]
[167.95072, 158.261376]
[167.80928, 158.230528]
[167.19488, 157.685952]
[167.127424, 157.69888]
[167.222144, 157.803264]
[167.365952, 157.949568]
[167.076416, 157.921664]
[166.78976, 157.560704]
[165.81248, 156.260288]
[165.088512, 154.817024]
[164.302848, 153.3392]
[161.537024, 150.150912]
[161.680192, 148.923392]
[163.578816, 147.257024]
[163.801536, 144.03936]
[152.124864, 140.75488]
[133.563648, 133.065856]
[123.943936, 127.38688]
[89.770816, 129.383424]
[86.900992, 139.808064]
[84.989184, 146.855488]
[95.186816, 111.379904]
[110.346816, 96.813952]
[128.926912, 82.799872]
[111.876288, 81.481344]
[126.609216, 83.544192]
^C[130.07904, 82.448]
Traceback (most recent call last):
  File "camera_detect_color.py", line 170, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:30:22] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:30:22] "GET /stream.mjpg HTTP/1.1" 200 -
[170.87776, 165.901376]
1.0299960381280984
[170.533824, 165.877376]
1.02807162804408
[168.02592, 163.254976]
1.029223881053402
[167.86432, 162.834944]
1.0308863434128732
[167.032256, 162.005632]
1.0310274645266653
[166.163008, 161.56352]
1.0284686047939533
[164.990336, 160.6624]
1.0269380763638538
[164.919104, 160.616192]
1.0267900262509024
[164.220736, 160.0384]
1.0261333280012797
[163.94144, 159.705216]
1.0265252701577385
[163.298624, 159.100608]
1.0263859205365198
[162.777216, 158.476032]
1.0271409117562964
[162.641024, 158.388288]
1.0268500660856945
[162.621568, 158.412672]
1.0265691875963054
[162.331328, 158.385024]
1.0249158910377791
[162.242752, 158.339776]
1.0246493717409326
[162.002496, 158.439552]
1.022487718218239
[162.450048, 158.33504]
1.0259892440738325
[162.85344, 158.417152]
1.0280038363522659
[163.102976, 158.573824]
1.0285617883566962
[162.163136, 158.416064]
1.0236533587906842
[161.841792, 158.562048]
1.0206842938860123
[161.826496, 158.680384]
1.0198267228796218
[162.269568, 158.513344]
1.023696579134688
[162.68544, 158.520384]
1.0262745767761956
[162.907968, 158.55648]
1.027444403407543
[162.862912, 158.591872]
1.0269310144721666
[162.990528, 158.799744]
1.0263903699995889
[163.065088, 158.940416]
1.0259510582884093
[162.631232, 158.922432]
1.0233371711804664
[162.595392, 158.935872]
1.0230251355716602
[162.715648, 159.0432]
1.0230908834832295
[162.620288, 159.023296]
1.0226192771152223
[162.639296, 159.039488]
1.022634680514062
[162.471424, 158.9792]
1.0219665465670982
[162.644992, 159.017792]
1.0228100261887678
[162.495424, 158.90816]
1.0225744480333798
[162.647424, 159.153856]
1.0219508850605543
[162.560704, 159.0848]
1.0218493784447036
[162.407616, 159.10976]
1.0207269246085218
[162.472384, 159.022272]
1.021695778563647
[162.336704, 158.962496]
1.0212264407322844
[162.338176, 158.984704]
1.0210930480456788
[162.094848, 158.817088]
1.020638585188012
[162.13344, 158.803008]
1.0209720964479463
[161.974272, 158.790336]
1.0200511950550946
[162.046528, 158.704064]
1.0210609855586308
[161.984256, 158.688896]
1.0207661662729066
[161.991232, 158.653504]
1.021037846097619
[162.053696, 158.711424]
1.0210587991447926
[162.057088, 158.56672]
1.0220119833468209
[162.056064, 158.412288]
1.0230018519775437
[161.809664, 158.571904]
1.0204182450883608
[161.767232, 158.5408]
1.0203507992895204
[161.91552, 158.667392]
1.0204713013748912
[161.644096, 158.463104]
1.0200740230356715
[161.45632, 158.0272]
1.0216995555195563
[161.133056, 157.674432]
1.0219352240951787
[160.84096, 157.347648]
1.0222012343012588
[160.195456, 156.666688]
1.0225240479967255
[160.345472, 156.652224]
1.0235760968194108
[160.444352, 156.731456]
1.0236895393864012
[160.505472, 156.659072]
1.024552679592025
[160.37888, 156.588352]
1.0242069601703199
[159.932224, 156.6064]
1.021236833232869
[159.850624, 156.669376]
1.0203054871425543
[159.90688, 156.58688]
1.0212022871903443
[159.664, 156.462016]
1.0204649286891458
[159.729408, 156.402816]
1.0212693868632134
[159.578176, 156.257536]
1.0212510710523428
[159.529984, 156.074304]
1.0221412488246624
[159.35392, 156.095616]
1.020873770087175
[159.470656, 156.260416]
1.0205441664765567
[159.366464, 156.190912]
1.0203312213197142
[159.317184, 156.052224]
1.0209222266515088
[159.42432, 156.134912]
1.0210677289138255
[159.380928, 156.160704]
1.0206212185109003
[159.563904, 156.083072]
1.0223011499927424
[159.330688, 155.995136]
1.0213824102823308
[159.5088, 156.070528]
1.0220302451978633
[159.577216, 156.185344]
1.0217169672462993
[159.47136, 155.894464]
1.0229443426547848
[159.60384, 156.017216]
1.022988642484173
[159.390208, 156.009536]
1.0216696497321804
[159.463424, 156.08352]
1.0216544578184807
[159.299072, 156.010688]
1.02107794050623
[159.35584, 156.070528]
1.021050175469388
[159.63904, 156.07744]
1.022819441426
[159.586944, 156.177792]
1.0218286605050735
[159.793856, 156.108672]
1.0236065296872168
[159.904768, 156.169728]
1.0239165429038846
[159.716608, 156.071232]
1.0233571296470576
[159.659968, 156.139392]
1.0225476476813744
[159.698304, 156.259904]
1.0220043652401067
[159.569024, 156.145536]
1.0219249815761624
[159.616448, 156.147776]
1.022214033967413
[159.613696, 156.230592]
1.021654555338304
[159.655744, 156.201984]
1.0221108587199506
[160.064832, 156.25792]
1.0243630018881602
[160.181888, 156.3888]
1.0242542176933385
[160.148992, 156.307648]
1.0245755345253482
[160.34784, 156.412992]
1.0251567849299883
[160.158272, 156.43104]
1.0238266778767182
[160.274496, 156.633984]
1.0232421592494256
[159.969344, 156.445888]
1.0225218830935334
[160.31648, 156.692544]
1.0231276862796996
[160.486528, 156.485824]
1.025565919632439
[160.831616, 156.6368]
1.0267805266706165
[160.96928, 156.61856]
1.0277790831431473
[161.301504, 156.626944]
1.0298451842359893
[161.570624, 156.599488]
1.0317442672609505
[161.8528, 156.63744]
1.033295743342077
[162.188096, 156.583808]
1.0357909803802958
[162.540288, 156.705856]
1.0372317419969295
[161.982272, 156.537152]
1.0347848413646876
[161.880448, 156.592128]
1.0337713017093682
[161.915264, 156.532608]
1.0343868032914905
[161.882624, 156.503168]
1.0343728249641566
[162.458368, 156.46656]
1.0382944956417526
[162.532096, 156.561152]
1.038138094436096
[162.86432, 156.656512]
1.039626874878971
[163.078848, 156.651968]
1.0410264874552995
[162.973952, 156.832512]
1.0391592273928507
[163.20064, 156.960768]
1.0397543416709072
[163.303936, 157.109248]
1.0394291747867064
[163.574528, 157.149248]
1.040886482638466
[163.895808, 157.245952]
1.0422895210682435
[164.109248, 157.48768]
1.0420449904398872
[164.372288, 157.457344]
1.0439163002774896
[164.424128, 157.617472]
1.0431846540464753
[164.639936, 157.764608]
1.0435796601478577
[164.66176, 157.906944]
1.0427771941428996
[164.753792, 157.729984]
1.0445305820864093
[164.656704, 157.67936]
1.0442502049729272
[164.427008, 157.520384]
1.0438459063177499
[164.360128, 157.353728]
1.0445264315568044
[164.413632, 157.439296]
1.0442985720667857
[164.41472, 157.394688]
1.0446014544023239
[164.274048, 157.330176]
1.0441356653665728
[164.557888, 157.420992]
1.0453363678460366
[164.585728, 157.340032]
1.0460511918543398
[164.59648, 157.282176]
1.0465043413438024
[164.5968, 157.185792]
1.0471480781163733
[164.352, 157.2768]
1.0449856558627846
[164.191488, 157.406528]
1.0431046925830165
[163.953024, 157.230336]
1.0427569397294933
[163.968512, 157.326848]
1.0422157062474169
[163.592576, 156.69344]
1.0440295139349802
[163.323264, 156.158528]
1.0458811701913584
[162.085952, 151.327808]
1.071091652897001
[162.555072, 154.250624]
1.053837370537963
[162.524992, 153.362112]
1.0597466993673117
[153.760256, 131.894528]
1.1657819193226877
[154.395392, 119.706048]
1.289787730691769
[156.265472, 114.60352]
1.3635311725154688
[158.218624, 115.419264]
1.3708164349410512
[154.747008, 114.028096]
1.3570954302350184
[159.934464, 118.269568]
1.3522875470383047
[161.380864, 118.703232]
1.3595321819038593
[163.486912, 119.646144]
1.3664202333173394
[164.423488, 119.95456]
1.3707147773290151
[165.701376, 120.409664]
1.3761468182487413
[166.228288, 121.614208]
1.3668492418254288
[168.271232, 123.535232]
1.362131509171408
[168.946432, 125.152704]
1.3499223476625801
[169.749696, 125.537792]
1.352180035156266
[170.293888, 127.242112]
1.3383453427745682
[165.578816, 125.89088]
1.3152566413071383
[162.210112, 125.12928]
1.2963401691434653
[160.169152, 124.262016]
1.2889630890907162
[160.02784, 124.342336]
1.2869939969601343
[160.464384, 124.245312]
1.2915125843943311
[160.080128, 124.55552]
1.2852110287845935
[159.97024, 125.600448]
1.2736438647097819
[158.951104, 125.846848]
1.2630519280069692
[159.248064, 126.54688]
1.2584116178921203
[159.815232, 126.98848]
1.2585018105579342
[161.176576, 127.450304]
1.2646229231434396
[161.324608, 127.813056]
1.2621919313156866
[161.813376, 128.209216]
1.2621040908634837
[161.265344, 128.370688]
1.2562474075078571
[162.029568, 128.195008]
1.2639304020325035
[162.27392, 128.216896]
1.2656204062216576
[162.760896, 128.12928]
1.2702865106242696
[164.113984, 128.285824]
1.2792838591425346
[163.806528, 128.392384]
1.2758274509491154
[163.901056, 128.643968]
1.2740671680774027
[163.7232, 128.594688]
1.2731723413023095
[164.03904, 128.775488]
1.273837455774192
[163.06464, 128.801024]
1.2660197484144224
[162.165632, 128.919232]
1.2578854953153924
[161.008512, 129.145344]
1.2467233197350112
[160.818304, 128.881152]
1.2478031232992084
[160.792448, 128.905344]
1.247368363564508
[160.084864, 128.991744]
1.241047365015857
[159.294464, 129.144192]
1.233462082445024
[158.993536, 129.24512]
1.230170516302666
[158.901888, 129.21344]
1.229762848199073
[160.232704, 129.647104]
1.2359142553620017
[160.626432, 129.735744]
1.238104681466967
[162.853312, 131.755584]
1.2360258825918147
[162.855936, 131.662592]
1.2369188053050029
[163.399552, 131.781696]
1.2399260061124118
[164.968896, 131.84128]
1.251268919719226
[164.969152, 131.686336]
1.2527431243891545
[164.545792, 131.812736]
1.248329994455164
[163.97568, 131.704256]
1.2450294696626967
[163.725312, 131.9056]
1.2412309409153213
[162.835776, 131.869952]
1.2348209241783905
[161.144384, 131.86272]
1.2220617320801512
[159.74912, 131.87008]
1.2114129300596466
[158.43648, 131.779904]
1.2022810397555002
[158.612928, 132.014912]
1.2014773603757734
[160.007296, 132.144192]
1.2108537921969358
[161.292864, 132.312832]
1.219026617161365
[162.18816, 132.153792]
1.227268302675719
[163.40608, 132.08096]
1.2371660533054878
[162.58336, 132.093696]
1.230818463887936
[161.715392, 132.194368]
1.2233152928269986
[161.139456, 132.189504]
1.2190034089242063
[158.732352, 131.161856]
1.2102020880216882
[157.24512, 130.219264]
1.2075411515150323
[156.400128, 128.60192]
1.2161570216058981
[155.837376, 126.670912]
1.2302538407554846
[162.51488, 123.672128]
1.3140784639850298
[164.802432, 120.131008]
1.3718558991863286
[159.098688, 115.292352]
1.3799587330823124
[158.31936, 112.8112]
1.4034010807437558
[158.635968, 117.40416]
1.3511954601949367
[166.654976, 131.66336]
1.265765783282456
[172.387072, 141.732224]
1.2162870738555545
[176.50528, 152.917568]
1.1542511583757336
[174.363456, 157.457856]
1.1073658719194044
[171.296192, 159.508864]
1.0738976361840304
[171.01024, 163.040896]
1.0488794173456948
[171.144064, 164.595648]
1.0397848672159302
[168.966528, 162.81248]
1.037798380075041
[168.370176, 162.600128]
1.0354861221265457
[167.555584, 161.937792]
1.034691049758169
[166.77792, 161.27328]
1.0341323745632258
[166.732416, 160.8448]
1.0366043291421296
[166.820032, 160.15904]
1.0415898596794786
[163.649024, 155.619072]
1.0516000506673115
[163.80672, 155.710464]
1.051995580720895
[163.364224, 155.668992]
1.0494333001141294
[163.012928, 155.505536]
1.048277329496488
[163.614016, 155.979136]
1.0489480849541313
[162.277248, 156.511104]
1.036841756607889
[156.04416, 153.092544]
1.0192799461220006
[149.89728, 141.800512]
1.0570997092027425
[140.52032, 122.224192]
1.1496931802175465
[144.826432, 111.451392]
1.2994582606918001
[153.507584, 113.068224]
1.3576545077775344
[158.469568, 117.144448]
1.3527706238369914
[174.555072, 123.226112]
1.4165428833784839
[175.133376, 124.696256]
1.4044798265635177
[173.73824, 125.28384]
1.3867569831831463
[174.358272, 125.684608]
1.3872682962101452
[174.195904, 126.36192]
1.3785474611338606
[166.932736, 125.760128]
1.3273899975674326
[159.195584, 124.93792]
1.274197489441156
[155.18112, 123.68896]
1.2546076868946106
[155.108928, 122.22784]
1.269014718741655
[154.293056, 120.108736]
1.2846114374228368
[153.251968, 117.740928]
1.3016031944304023
[150.631424, 112.977856]
1.333282727546184
[151.774208, 112.429696]
1.3499476864190754
[153.217664, 111.509184]
1.374036276689102
[152.85344, 108.917888]
1.403382335140395
[153.727168, 108.110528]
1.4219444751948673
[153.851712, 106.587712]
1.4434282255725688
[153.358656, 104.952]
1.4612266178824604
[153.009984, 103.6752]
1.4758590675494236
[152.775552, 102.128896]
1.495909169526321
[152.418816, 101.467968]
1.5021372656245564
[152.863424, 100.944448]
1.514332160199638
[153.406912, 100.800832]
1.5218814066931512
[154.055296, 100.2192]
1.537183453869119
[154.113984, 99.88384]
1.5429321099389048
[152.507136, 98.3888]
1.5500456962581106
[148.927168, 95.758464]
1.555237644580431
[148.08576, 94.774016]
1.5625143499247724
[147.577728, 94.19136]
1.5667862530066452
[147.094592, 93.36992]
1.5753959305095262
[146.678208, 92.45472]
1.5864869635644347
[146.62304, 92.359424]
1.5875265744403082
[147.299776, 92.182976]
1.5979064941448626
[148.387456, 92.634304]
1.6018629124692294
[148.050176, 92.973888]
1.5923844768113815
[148.418496, 93.743936]
1.5832330317344474
[148.797568, 93.827712]
1.5858594953269243
[149.40928, 94.246336]
1.5853059794282083
[149.291264, 94.623488]
1.5777400215895658
[149.247744, 95.3024]
1.5660439191457929
[148.818624, 95.22368]
1.562832102266999
[144.808832, 93.062528]
1.5560380220919852
[145.07776, 91.989632]
1.5771099073426016
[149.603776, 90.21472]
1.658307823822986
[147.352064, 95.549632]
1.5421520828044635
[156.430592, 115.857152]
1.350202290489585
[161.435264, 124.804864]
1.293501381484619
[175.34816, 153.53152]
1.142098769034528
[178.228416, 157.800768]
1.129452145632143
[176.987072, 158.431616]
1.117119653693364
[176.25696, 159.314112]
1.1063486955882478
[176.127296, 160.035456]
1.100551717739349
[176.13184, 160.256]
1.0990654952076677
[176.106624, 160.140672]
1.099699544160774
[176.115072, 160.188608]
1.0994231999319204
[176.517952, 160.257344]
1.101465602724578
[176.54016, 160.22784]
1.1018070267938456
[176.487488, 160.235648]
1.101424621816988
[176.249856, 160.116288]
1.1007615664934725
[176.09728, 159.954432]
1.1009215424552914
[176.179008, 160.212096]
1.0996610892600769
[176.246976, 160.026112]
1.1013638574184692
[176.204864, 159.925248]
1.1017951586981436
[176.317376, 160.25088]
1.1002583948368958
[176.422976, 160.048064]
1.1023124653354133
[176.608, 160.245632]
1.1021080437312638
[176.856064, 160.971392]
1.0986800934168477
[176.912384, 161.373056]
1.0962944396368128
[173.643072, 161.438784]
1.0755970015235001
[167.339328, 160.061632]
1.045468085693391
[164.457024, 159.544384]
1.0307916823947874
[160.974848, 153.39744]
1.0493972259250222
[165.829312, 129.16736]
1.2838329435547804
[183.327488, 132.407808]
1.384567049097286
[185.446016, 137.432064]
1.3493649924372815
[185.0912, 165.477568]
1.1185274369031095
[183.460416, 170.991936]
1.0729185264034908
[179.799104, 170.255872]
1.0560522928689355
[177.303296, 169.21984]
1.0477689613700143
[174.981824, 167.821824]
1.0426642961525672
[174.873152, 167.602752]
1.0433787626589806
[174.816896, 167.45792]
1.0439452251646264
[174.854528, 167.459264]
1.0441615699445568
[174.974144, 167.449984]
1.0449337755684707
[175.021312, 167.488192]
1.0449770214248895
[172.576448, 164.6288]
1.0482761703905998
[169.94944, 161.252864]
1.0539312963768508
[169.478464, 159.753472]
1.060874996194136
[167.55488, 155.570688]
1.077033740443444
[167.572352, 152.734016]
1.0971514819593298
[162.97504, 146.40448]
1.1131834217094996
[152.351424, 145.283904]
1.0486462698579466
[143.840384, 143.899072]
0.9995921585929338
[101.919872, 149.296768]
0.6826662985765373
[100.33024, 154.0256]
0.6513867824569423
[97.583936, 148.577152]
0.6567896522878564
[124.587584, 125.740032]
0.9908346770581385
[137.875904, 96.698496]
1.4258329726245171
[122.3088, 85.786176]
1.4257402031767916
[108.030592, 88.3248]
1.223105990616452
[110.133376, 96.13088]
1.1456607491786197
[114.937472, 103.833664]
1.1069384202795733
[128.149824, 127.952768]
1.0015400682851971
[138.317824, 125.084672]
1.1057935539855754
[144.179136, 114.347008]
1.2608911988322422
[133.699008, 110.159168]
1.2136893408635765
[127.780608, 110.860544]
1.1526247607083724
[135.66496, 127.436992]
1.0645649891045765
[167.809536, 129.381312]
1.2970152598236135
[199.695744, 126.279936]
1.5813734970534035
[223.599232, 115.827264]
1.930454232260895
[191.421184, 130.415424]
1.4677802527406576
[170.42848, 146.721664]
1.161576793458395
[160.240064, 150.673792]
1.063489953183099
[168.280512, 145.65888]
1.1553055467679003
[201.042496, 111.889408]
1.7967964939094145
[214.172544, 108.649792]
1.971219088942204
[194.822976, 110.644864]
1.760795476236475
[165.942976, 108.115648]
1.534865480341939
[123.516032, 94.03392]
1.3135263530436676
[137.091776, 97.42144]
1.4072033425085895
[128.388416, 107.502976]
1.1942777844587298
[120.10528, 119.385856]
1.0060260404716619
[107.58208, 130.506112]
0.8243451463790447
[106.470656, 142.078912]
0.7493769096430017
[109.1216, 146.129408]
0.7467463359599732
[89.345216, 144.657344]
0.6176334607664302
[85.745088, 147.274688]
0.5822119820073901
[86.96992, 152.998912]
0.5684348918768782
[88.257408, 151.203904]
0.583697944730316
[87.513344, 148.776704]
0.588219402951688
[87.175424, 148.870016]
0.5855808062786801
[86.71136, 148.835712]
0.582597810933978
[87.301952, 149.712448]
0.5831308830111441
[90.71424, 153.290688]
0.5917791953546455
[91.3248, 154.149184]
0.5924442649012012
[91.46048, 154.76608]
0.5909594660535435
[89.376256, 152.540352]
0.5859187738074709
[88.71328, 150.143168]
0.5908579203550574
[89.046912, 150.4672]
0.591802811509751
[89.548352, 151.378624]
0.5915521599667862
[89.823232, 152.24896]
0.5899759972087822
[89.224128, 151.649984]
0.5883556703837173
[89.081152, 151.536768]
0.5878517350983756
[89.006656, 151.69888]
0.5867324531334708
[88.316544, 152.45152]
0.5793090419826579
[89.581056, 154.544256]
0.5796466223888646
[90.093504, 154.286208]
0.5839375091777484
[90.438208, 154.419648]
0.5856651609515391
[90.343232, 149.600064]
0.6038983512734326
[90.104256, 132.38656]
0.6806148297833254
[90.034368, 94.346752]
0.9542921837945201
[104.944896, 81.549312]
1.2868887968055451
[120.121216, 77.554496]
1.5488620543675509
[129.027328, 76.247872]
1.6922089051875442
[129.648448, 75.617472]
1.7145303138406953
[100.32736, 78.610304]
1.2762622060334483
[95.200512, 77.905408]
1.2220013275586723
[94.882944, 77.933376]
1.2174879219912147
[95.254912, 77.802816]
1.2243118809478566
[96.892608, 77.809728]
1.2452505681551795
[96.915968, 78.529536]
1.2341339696697051
[95.774144, 79.209536]
1.209123911545196
[96.007296, 79.172672]
1.2126317525319847
[96.921216, 78.810944]
1.2297938722825092
[97.314048, 78.694144]
1.2366110494829197
[97.917824, 79.023808]
1.2390927048213114
[98.695872, 80.99712]
1.2185108803868583
[99.84896, 81.702144]
1.2221094222447821
[102.236992, 82.5424]
1.2385997014867511
[104.506176, 82.894656]
1.2607106542549618
[105.524288, 82.585984]
1.2777505684257513
[105.176768, 83.026496]
1.266785581316114
[108.86016, 83.575104]
1.302542919958556
[117.560768, 83.056384]
1.4154332555580555
[111.939328, 96.223296]
1.1633287639616918
[95.52032, 162.654144]
0.5872602913824316
[95.562432, 162.673792]
0.5874482350543596
[95.921536, 164.228608]
0.5840732450219636
[96.742592, 165.682176]
0.5839046440336467
[97.869056, 166.437888]
0.5880214966438412
[97.888384, 166.590656]
0.5875982864249001
[97.907072, 166.505664]
0.588010459512056
[97.222208, 166.74656]
0.5830537553518346
[96.84064, 166.886336]
0.58027902296327
[96.546048, 166.86752]
0.578579030838356
[96.51296, 166.876096]
0.5783510179912168
[96.147328, 166.75104]
0.5765920740284439
[96.110272, 166.594112]
0.5769127782859457
[96.10944, 166.623744]
0.5768051881009228
[96.163136, 166.564032]
0.5773343431071601
[96.31904, 166.342144]
0.5790417129648155
[96.413888, 166.41504]
0.5793580195636163
[96.721472, 166.161536]
0.5820930302425706
[96.955712, 166.133824]
0.5836000741185612
[97.340096, 166.38944]
0.5850136643286977
[97.251776, 166.30176]
0.5847910208526957
[97.394752, 166.40992]
0.5852701088973542
[97.017344, 166.11264]
0.5840455247716249
[96.655488, 166.123008]
0.5818308322469095
[96.458368, 166.025792]
0.5809842364733305
[96.406912, 166.305408]
0.5796979975539942
[96.627008, 166.063872]
0.5818665242250886
[96.865216, 166.271552]
0.5825723933821223
[96.83296, 166.25248]
0.5824452062309086
[96.794048, 166.266944]
0.5821605044957102
[96.471616, 166.268096]
0.5802172414363846
[96.848, 167.408768]
0.5785121123404958
[97.309888, 168.602816]
0.5771545832306858
[97.680832, 168.431104]
0.5799453288627734
[97.784384, 168.132096]
0.5815926068036409
[97.675072, 167.447488]
0.5833176308981118
[97.89952, 167.885568]
0.5831324345878258
[98.261568, 168.40864]
0.5834710618172559
[98.13216, 168.463872]
0.5825116022502439
[98.110528, 168.558912]
0.5820548248436725
[97.569728, 168.189824]
0.5801167138387635
[97.183104, 167.698368]
0.5795113283392239
[96.784384, 167.140928]
0.5790585535100057
[96.621184, 167.12544]
0.5781357045342708
[97.42464, 167.292992]
0.5823593614728344
[97.91776, 167.3856]
0.5849831765695496
[98.132288, 167.428096]
0.5861160124522947
[97.8336, 167.25408]
0.5849399907015722
[97.717504, 167.218752]
0.58436929370218
[97.751552, 167.32352]
0.584206882570962
[97.455488, 166.945792]
0.583755282672833
[97.075456, 166.507648]
0.5830089918752561
[96.947456, 166.087616]
0.5837127314778243
[97.388352, 167.12192]
0.582738350540731
[97.625536, 167.651264]
0.5823131521394315
[97.831872, 168.148928]
0.5818168046840001
[97.707136, 167.710528]
0.5825939323260613
[97.569984, 167.227136]
0.5834578426314734
[97.755456, 167.09376]
0.5850335524199108
[97.324224, 167.12896]
0.582330100061653
[97.259072, 166.954944]
0.5825468217341321
[97.242368, 166.991488]
0.5823193095925943
[97.43776, 167.502272]
0.5817100797295454
[98.02592, 168.294784]
0.5824655860992103
[98.376576, 168.803072]
0.5827890146454208
[98.493184, 168.79392]
0.5835114440140972
[98.313024, 168.425792]
0.5837171541992808
[98.22528, 168.220416]
0.583908198158302
[98.269312, 168.22464]
0.5841552818897399
[98.196224, 168.035776]
0.5843768888834721
[98.071616, 167.752704]
0.5846201799525091
[98.273536, 167.974848]
0.585049114019737
[98.374336, 167.976832]
0.5856422866696284
[98.337792, 167.897216]
0.5857023382686702
[98.547968, 168.207168]
0.5858725830280906
[98.65312, 168.523072]
0.5853983008332532
[98.961024, 169.030656]
0.5854619886229395
[98.999552, 169.16544]
0.5852232701904124
[99.075072, 169.259776]
0.5853432773064761
[99.05056, 169.29504]
0.5850765621957974
[99.095744, 169.27904]
0.5853987829798656
[98.762304, 169.438592]
0.5828796311055277
[98.557952, 169.342848]
0.5820024474845256
[98.535296, 169.376896]
0.5817516929817866
[98.414784, 169.23168]
0.5815387757185888
[98.404544, 169.409344]
0.5808684555203756
[98.48896, 169.496832]
0.5810666714997953
[98.278144, 169.360832]
0.5802885049596356
[98.524928, 169.534656]
0.581149189933178
[98.620096, 169.583168]
0.5815441306061696
[98.494464, 169.439168]
0.581296905329469
[98.241472, 168.753984]
0.5821579418237616
[98.454016, 168.063168]
0.5858155428796867
[98.144448, 167.29088]
0.5866694466548326
[98.955008, 155.689792]
0.6355908549225886
[98.214336, 154.816064]
0.6343937021935915
[97.929536, 154.721152]
0.6329421332126587
[97.980736, 154.735488]
0.6332143793671946
[98.043584, 155.09152]
0.6321659881855565
[98.261568, 155.573696]
0.6316078522682909
[98.474752, 155.755008]
0.6322413209339631
[98.351168, 155.76928]
0.6313900147705632
[98.294784, 155.650112]
0.6315111678172131
[98.225536, 155.289024]
0.632533668316442
[98.224, 155.09088]
0.6333318890188773
[98.411392, 154.987328]
0.6349641178406534
[98.445568, 154.95936]
0.6352992681435958
[98.354048, 155.179456]
0.6338084340236378
[98.226688, 155.166592]
0.6330401843200887
[98.184576, 155.051776]
0.6332373516314964
[98.095232, 155.13248]
0.6323320042327694
[98.27904, 155.33344]
0.6326972479332202
[98.556736, 155.458624]
0.6339740663084732
[98.507712, 155.382016]
0.6339711282932512
[98.035136, 155.27104]
0.631380687602788
[97.744512, 154.992896]
0.6306386584324484
[97.526336, 154.882304]
0.6296803022764951
[97.3904, 154.728]
0.6294297089085362
[97.367488, 154.709184]
0.6293581640247032
[97.457152, 154.70304]
0.6299627466919848
[97.38592, 154.845056]
0.6289249557958118
[97.309504, 154.829056]
0.6284963979887599
[97.138752, 154.74304]
0.627742301043071
[97.66752, 154.437568]
0.6324077830596244
[97.659712, 154.446976]
0.6323187059356863
[97.604288, 154.382784]
0.6322226188122116
[97.772288, 154.465984]
0.6329697028958816
[97.753088, 154.628416]
0.6321806206693601
[97.799296, 154.694912]
0.6322075802984394
[97.246528, 154.498112]
0.6294350574329348
[97.13568, 154.57216]
0.6284163978817401
[97.101568, 154.456192]
0.628667369968567
[97.22336, 154.482816]
0.6293474090995337
[97.517568, 154.520832]
0.6310965760267198
[97.63648, 154.418432]
0.6322851406754344
[97.308928, 154.544384]
0.6296503663310081
[97.318208, 154.713344]
0.6290227170062331
[97.161536, 154.539776]
0.6287153929872398
[97.125632, 154.543744]
0.6284669277845372
[97.168192, 154.66112]
0.6282651515778497
[97.21632, 154.60896]
0.6287883962223146
[97.196288, 154.6064]
0.6286692400832048
[97.148992, 154.628992]
0.6282715210353308
[97.01792, 154.451264]
0.6281458467054047
[96.795392, 154.266432]
0.627455958792124
[96.78912, 154.234496]
0.6275452153064383
[96.6864, 154.162496]
0.6271719938940272
[96.345984, 154.34432]
0.6242275971023747
[96.207552, 154.298496]
0.623515811845632
[96.09856, 154.48672]
0.6220506202733802
[96.102912, 154.531008]
0.6219005055606703
[96.69632, 154.387712]
0.6263213486835014
[96.860608, 154.458112]
0.6270995206778133
[96.880128, 154.34368]
0.6276909297484679
[97.4496, 154.276608]
0.6316550594630652
[97.763008, 154.227584]
0.6338879561259287
[97.89184, 154.26688]
0.6345616116693357
[97.930176, 154.352896]
0.6344563564262508
[97.468288, 154.27776]
0.6317714750330832
[97.343232, 154.3152]
0.6308078011757753
[97.306496, 154.475904]
0.6299137501729719
[97.243008, 154.544064]
0.6292251250750078
[97.152256, 154.628864]
0.6282931497188002
[97.364352, 154.577792]
0.6298728345142878
[97.273792, 154.763392]
0.6285323082089077
[97.30656, 154.783744]
0.6286613664029215
[97.383616, 154.888256]
0.6287346666231428
[97.54592, 155.146112]
0.6287358332253921
[97.437376, 155.116672]
0.6281554055001902
[97.666048, 155.135552]
0.6295529731315231
[97.659264, 155.086528]
0.6297082361660711
[97.878528, 155.187392]
0.6307118557672521
[97.900672, 155.299328]
0.6303998430695077
[97.875392, 155.20256]
0.6306300102266355
[98.120704, 155.261312]
0.6319713696609752
[98.233792, 155.310848]
0.6324979437366796
[98.2384, 155.395392]
0.6321834819915381
[98.312768, 155.279552]
0.6331340265587577
[98.056512, 155.458944]
0.630755037162738
[97.936768, 155.469184]
0.6299432818789349
[97.659968, 155.321728]
0.6287592164825774
[97.72, 155.550144]
0.6282218549408737
[98.08096, 155.955648]
0.6289029044975659
[98.570304, 156.791744]
0.6286702442700044
[98.71008, 156.855616]
0.6293053606700317
[98.712128, 156.928512]
0.6290260880062382
[98.676736, 156.894336]
0.628937529013157
[98.853056, 157.130112]
0.6291159265513665
[98.750976, 157.146432]
0.6284010062665628
[98.95904, 157.840256]
0.626956915224466
[99.223808, 158.479936]
0.6260969716696504
[99.479296, 158.757376]
0.6266121203716545
[99.53248, 158.972096]
0.6261003188886685
[99.81344, 159.256768]
0.6267453575348207
[100.324352, 159.94848]
0.6272291677920291
[100.481408, 160.208128]
0.6271929474140039
[100.31232, 159.852928]
0.6275288244954763
[100.562688, 159.770048]
0.6294214044424646
[100.92704, 160.128064]
0.6302895162711766
[101.337728, 160.876416]
0.6299104027777446
[101.798272, 161.811008]
0.6291183353854394
[101.609792, 161.901952]
0.6276007839609
[101.651648, 161.966336]
0.6276097274930019
[101.822848, 161.891136]
0.6289587590515148
[102.115968, 161.835712]
0.6309853785547654
[102.37472, 161.978816]
0.6320253631190884
[101.532224, 162.433856]
0.6250681138789195
[101.071424, 162.666752]
0.6213403953624155
[101.07328, 162.889088]
0.6205036889886695
[101.288512, 162.671488]
0.6226568235485741
[101.549312, 162.645184]
0.6243610139725994
[101.518592, 162.587584]
0.6243932624031119
[101.328192, 162.245376]
0.6245367017424275
[101.320448, 162.26176]
0.6244259152618583
[101.420288, 162.285312]
0.6249505069195664
[101.412864, 162.161792]
0.6253807555358046
[101.496, 162.269184]
0.6254792037408655
[101.695424, 162.118016]
0.6272925521121601
[102.268544, 162.552768]
0.6291405877505575
[102.6672, 163.245824]
0.6289116467689856
[103.74144, 164.538752]
0.6304985223177091
[103.731264, 164.752512]
0.6296187095465956
[103.7984, 164.868416]
0.6295832914413395
[103.718976, 164.95744]
0.6287620370442218
[103.808128, 164.884288]
0.6295816857941007
[103.714432, 165.09472]
0.6282116835717096
[103.900544, 165.101632]
0.6293126405921899
[103.720512, 165.017152]
0.6285438255533582
[103.511936, 165.028928]
0.6272350990488165
[103.274176, 164.288064]
0.6286164282756415
[103.105152, 164.069312]
0.6284243576275861
[102.613632, 163.282496]
0.6284423285641101
[102.535296, 162.964288]
0.6291887459416875
[102.444992, 162.873408]
0.6289853774042721
[102.879936, 163.564864]
0.6289855503441131
[102.773568, 163.913024]
0.6270006219884028
[103.1856, 164.517824]
0.6272001263522669
[103.448384, 164.509568]
0.6288289809380571
[103.564288, 164.747776]
0.6286232841164424
[104.162944, 164.895616]
0.6316901960571226
[104.492608, 164.98496]
0.6333462638048947
[103.962176, 165.05728]
0.6298551387736427
[103.877568, 164.860928]
0.6300920979894035
[104.383616, 164.875328]
0.633106343236509
[105.451456, 165.020672]
0.6390196738503161
[106.019456, 164.999296]
0.6425448991006605
[104.781696, 164.97952]
0.6351194136096407
[103.748992, 165.191168]
0.6280541100114989
[102.6496, 165.005952]
0.6220963471669192
[102.5808, 164.978752]
0.6217818886155716
[103.618112, 164.742656]
0.6289695365843804
[104.10912, 164.5872]
0.6325468809239115
[104.3776, 164.624192]
0.634035610027474
[104.41952, 164.586432]
0.6344357717165896
[104.1072, 164.751872]
0.6319029868140134
[104.194304, 164.93376]
0.6317342428863563
[103.984832, 164.937728]
0.6304490383182676
[103.719872, 164.977856]
0.6286896588109376
[103.671936, 164.556992]
0.6300062655496279
[103.805184, 164.639872]
0.6304984493671132
[103.998208, 164.74944]
0.6312507526580972
[104.190848, 164.678656]
0.6326918772035643
[104.51584, 164.929088]
0.6337016791119344
[104.61024, 165.013184]
0.6339507999554751
[104.764672, 165.224896]
0.634073160499977
[104.926464, 165.0112]
0.6358748012256138
[103.939648, 164.722304]
0.63099923614473
[103.619968, 164.62112]
0.629445164751643
[103.397312, 164.385792]
0.6289917805061888
[103.148032, 164.274944]
0.6278987500370111
[103.063872, 164.38304]
0.626973877597105
[103.032, 164.750976]
0.6253802101906819
[103.047744, 164.722496]
0.6255839153870033
[103.130688, 164.806336]
0.6257689510189706
[103.23488, 164.590016]
0.6272244362622822
[103.263296, 164.621312]
0.6272778095706102
[102.979776, 164.424896]
0.6263028197384416
[102.908736, 164.458816]
0.6257416811270246
[102.994304, 164.339456]
0.6267168366432951
[102.71808, 164.287552]
0.6252334930403004
[102.45792, 164.061568]
0.6245089648295937
[102.42784, 163.900352]
0.6249397194705232
[102.541632, 163.877568]
0.6257209772602923
[102.509952, 163.942272]
0.6252807817620095
[102.364032, 163.610752]
0.6256558982138288
[101.719296, 163.58528]
0.6218120358995626
[101.50016, 163.557952]
0.6205761246020004
[101.442368, 163.582272]
0.6201305725842957
[101.653312, 163.490816]
0.621767720579485
[101.757248, 163.417088]
0.6226842568630276
[101.816064, 163.477696]
0.6228131818055473
[101.293632, 163.335232]
0.6201578848585467
[101.032448, 163.228096]
0.6189648135085764
[100.97344, 163.025664]
0.6193714383521848
[101.159296, 162.798592]
0.6213769711226986
[101.122752, 162.636672]
0.6217709127742113
[101.158528, 162.710656]
0.6217080705519373
[101.391296, 162.61728]
0.6234964451502325
[101.391744, 162.359616]
0.6244886905867036
[101.590528, 162.329024]
0.625830954296873
[101.278016, 162.503424]
0.6232361971646825
[101.006144, 162.436928]
0.6218176201904041
[100.948864, 162.517824]
0.6211556462877573
[101.093568, 162.876096]
0.6206777451247358
[101.096, 162.963008]
0.6203616467364177
[101.151488, 175.56992]
0.5761322212825523
[101.23136, 175.374272]
0.5772303932928087
[101.304448, 175.635456]
0.5767881400894361
[101.487168, 175.59328]
0.5779672661732841
[101.5984, 175.757248]
0.578060940052953
[101.100736, 176.018304]
0.5743762648684536
[101.157568, 176.124032]
0.5743541460599766
[100.95552, 176.128704]
0.5731917495969312
[101.603328, 176.111488]
0.576926179852617
[102.172352, 176.257856]
0.5796754500406496
[102.036096, 176.012288]
0.579710071151396
[102.069696, 175.901376]
0.5802666148558155
[101.653568, 175.806016]
0.5782143882948807
[101.469248, 175.804608]
0.5771705824684641
[101.416576, 175.882752]
0.576614675667572
[101.428416, 175.777792]
0.5770263401647462
[101.130432, 175.720384]
0.5755190701153943
[101.124736, 175.812416]
0.5751854067007417
[101.227072, 175.855232]
0.5756272977991351
[101.262528, 175.568448]
0.5767695115696415
[101.365824, 175.733184]
0.5768166358381125
[101.65856, 175.857408]
0.5780737994273178
[101.96, 176.028736]
0.579223610399611
[101.815872, 175.924416]
0.5787478186086461
[102.33792, 176.257024]
0.5806175418007739
[102.069568, 176.194304]
0.5793011787713638
[101.978304, 176.049408]
0.5792595678594954
[102.024064, 176.048768]
0.5795216016507426
[101.96032, 175.877184]
0.5797245423260814
[101.911168, 175.866432]
0.5794805002924037
[101.670976, 175.613504]
0.5789473684210525
[101.563904, 175.553856]
0.5785341678852101
[101.517056, 175.747968]
0.5776286187274723
[101.646144, 175.935488]
0.5777466795101623
[102.051328, 176.331136]
0.5787482024728747
[102.079232, 176.233984]
0.5792255822804302
[102.163776, 176.287552]
0.5795291547301082
[102.43328, 176.165952]
0.581459009740997
[102.761728, 176.249536]
0.5830468001912924
[102.985536, 176.284992]
0.5841991132177605
[102.648704, 176.334784]
0.582123967101125
[102.654016, 176.50848]
0.5815812135484936
[102.727424, 176.770944]
0.5811329717173429
[102.722368, 176.78784]
0.581048832317879
[102.977344, 177.00064]
0.5817908003044509
[102.829888, 176.998784]
0.5809638104632402
[102.986432, 177.191936]
0.5812139893318847
[102.897408, 176.943296]
0.58152758723337
[102.965504, 177.030784]
0.5816248545789641
[102.97728, 176.969472]
0.5818929041049521
[102.719552, 176.719872]
0.5812563739294695
[103.236032, 176.77568]
0.5839945404254703
[103.611456, 176.691648]
0.5863970208710715
[103.892096, 176.73504]
0.587840962380748
[104.602624, 177.000384]
0.590973994723085
[105.146816, 177.222976]
0.5933023943802863
[104.908544, 177.02304]
0.5926264965283615
[103.55168, 176.793024]
0.5857226583781948
[103.015424, 176.428224]
0.5838942413204816
[99.603968, 169.238656]
0.5885414736453591
[97.13376, 160.4224]
0.6054875129657703
[95.983424, 136.992832]
0.7006455929022622
[96.51712, 129.607168]
0.7446896764228349
[96.390208, 125.885376]
0.7656982174005661
[100.349056, 119.838592]
0.8373684497227738
[112.047552, 107.641856]
1.0409292088014535
[113.152832, 105.724288]
1.0702633627572882
[112.589696, 107.990912]
1.042584916775219
[112.075904, 112.008576]
1.0006010968302999
[111.132928, 112.109312]
0.9912907859072403
[112.017728, 111.446464]
1.0051259051162
[113.098624, 110.231168]
1.0260131145485096
[113.328, 110.315904]
1.0273042769970864
[112.271552, 110.41248]
1.0168375169183774
[111.832, 110.703552]
1.010193421797342
[111.515968, 111.193984]
1.0028956962275946
[111.172416, 111.52608]
0.9968288672927444
[112.955904, 111.371392]
1.014227280197773
[113.224896, 111.030336]
1.019765408977957
[113.330624, 110.405824]
1.0264913561081705
[113.072, 110.476864]
1.0234903119625118
[112.3296, 110.625088]
1.015408005822332
[111.593728, 110.92544]
1.0060246594469222
[111.638016, 110.493568]
1.0103575983716988
[111.937728, 110.54976]
1.0125551425891834
[111.81056, 110.430144]
1.01250035497554
[111.888192, 110.330816]
1.014115512387763
[112.019008, 110.401344]
1.0146525752440116
[111.847296, 111.046016]
1.0072157473889023
[112.11712, 111.188864]
1.008348461946693
[112.05792, 111.173888]
1.0079517952992703
[111.797312, 111.017792]
1.0070215772261082
[111.629952, 110.44832]
1.0106985058713434
[111.71616, 110.473984]
1.0112440590537588
[112.03136, 110.30752]
1.0156275836860444
[112.756608, 109.427456]
1.0304233701640655
[113.94304, 106.648448]
1.0683984824608042
[114.407744, 101.379648]
1.128508001921648
[114.556032, 100.119872]
1.144188758051948
[115.109056, 99.034112]
1.162317242769845
[117.108096, 97.129152]
1.2056946198809602
[124.246336, 95.127168]
1.3061077987731118
[128.015488, 95.112256]
1.3459410320369227
[133.38176, 94.785152]
1.4072009928306073
[137.087296, 93.948032]
1.4591821997931793
[143.943552, 92.615936]
1.5541985344725124
[151.453632, 91.850496]
1.6489146884955308
[154.499072, 91.509824]
1.688333178304441
[158.425792, 91.21888]
1.7367653713792583
[159.408256, 91.05024]
1.750772496590893
[160.17088, 90.910464]
1.7618530689712464
[160.705664, 90.916352]
1.7676211205658583
[160.705152, 90.738176]
1.7710864278338592
[161.40416, 90.51424]
1.7831907995913128
[161.24384, 89.800768]
1.7955730623595558
[160.139904, 88.047296]
1.8187941171981021
[159.831232, 86.796352]
1.8414510324120534
[159.563776, 84.70784]
1.883695487926501
[159.928, 84.17568]
1.8999311915270538
[159.932288, 84.379904]
1.895383621199664
[160.46048, 85.09664]
1.8856265065224667
[160.346304, 85.748352]
1.8699636816343714
[140.252544, 93.538112]
1.499416024133564
[138.982784, 92.029056]
1.5102054724977296
[138.186176, 91.935552]
1.5030765900007865
[138.64288, 91.5472]
1.5144415121380008
[139.090944, 91.566592]
1.519014096320195
[138.742976, 91.541952]
1.5156217774338043
[138.963584, 91.566016]
1.5176327426979022
[139.003136, 91.749888]
1.515022405258958
[140.050304, 91.667776]
1.5278030089875858
[140.242112, 91.744192]
1.528621146938653
[140.040256, 91.672704]
1.5276112723804898
[140.14848, 91.673728]
1.5287747434030392
[139.505024, 91.710464]
1.5211462020299014
[139.245056, 91.841216]
1.5161499603837998
[139.123648, 91.749312]
1.5163454086718382
[139.09056, 91.732608]
1.5162608262483936
[138.88352, 91.718592]
1.5142351945394017
[138.515712, 91.827584]
1.5084324988883515
[138.562816, 91.66912]
1.5115539016846675
[138.338944, 91.730624]
1.5080998903921115
[138.555456, 91.689024]
1.5111454998146778
[138.400064, 91.844096]
1.5069021311941488
[138.312448, 91.600192]
1.509958057729835
[138.24736, 91.567552]
1.5097854750993014
[137.580224, 91.63776]
1.5013486143703205
[137.426944, 91.556928]
1.500999946175564
[137.443584, 91.605056]
1.5003929914086835
[137.166656, 91.583104]
1.4977288387168006
[136.742336, 91.726592]
1.4907600186432306
[136.735296, 91.60576]
1.4926495451814383
[136.676672, 91.62528]
1.4916917252531179
[136.266816, 91.839936]
1.4837424973815314
[136.006592, 91.71296]
1.4829593549265012
[136.024192, 91.711552]
1.4831740280657337
[136.142656, 91.597824]
1.4863088450660136
[136.153984, 91.564288]
1.4869769314429662
[136.026752, 91.64544]
1.4842719070365094
[137.674176, 91.578624]
1.5033440118078207
[138.64192, 91.541184]
1.514530552718217
[139.1184, 91.768832]
1.5159656821174319
[138.407744, 91.435648]
1.5137175382625385
[138.366208, 91.719872]
1.5085739325933645
[137.981824, 91.5072]
1.5078794236956217
[137.87712, 91.484864]
1.5071030766357152
[137.779136, 91.521344]
1.5054317384150302
[137.524032, 91.639104]
1.500713407237155
[137.516416, 91.50144]
1.5028879982653824
[137.486912, 91.444224]
1.5035056998241898
[137.1792, 91.58432]
1.4978459194761724
[136.94144, 91.797568]
1.491776339869919
[136.721984, 91.684736]
1.4912186037161081
[136.703872, 91.714368]
1.4905393231298285
[137.69184, 91.626176]
1.5027565921773274
[138.802176, 91.554816]
1.5160554306613427
[138.84256, 91.554624]
1.516499701861044
[138.437824, 91.519168]
1.5126648004492351
[138.05216, 91.51648]
1.5084950819786773
[137.851264, 91.651456]
1.5040815499974163
[137.802304, 91.46336]
1.5066394236992824
[137.704064, 91.53952]
1.5043127165185046
[137.899968, 91.747456]
1.5030386019640698
[137.749376, 91.567488]
1.5043480935067262
[137.84064, 91.602752]
1.5047652716809208
[137.95616, 91.503936]
1.5076527418448975
[137.907136, 91.569728]
1.5060341339006709
[138.014208, 91.485248]
1.5085952218219925
[138.00736, 91.432896]
1.50938410613178
[138.111488, 91.487488]
1.5096215998410625
[138.337728, 91.616384]
1.5099671255307348
[138.125248, 91.486784]
1.5097836207686566
[138.270912, 91.508928]
1.5110100732466236
[137.579392, 91.566464]
1.5025085166551808
[137.391872, 91.637312]
1.499300546921324
[137.173568, 91.802816]
1.4942196108668386
[136.897664, 91.590784]
1.4946663629388737
[136.571328, 91.674304]
1.489744912598409
[136.571776, 91.587584]
1.4911603738777517
[136.336832, 91.505088]
1.4899371715811036
[138.055232, 91.592384]
1.507278509095254
[138.500288, 91.456192]
1.5143894029613654
[138.532736, 91.465536]
1.5145894514847646
[138.69536, 91.48064]
1.5161170713278789
[139.030464, 91.362816]
1.5217401355054556
[139.147648, 91.50112]
1.5207207081181082
[138.25696, 91.521408]
1.5106515843812194
[137.684288, 91.739776]
1.500813431242736
[137.606848, 91.565056]
1.5028314731768417
[137.481024, 91.624576]
1.5004819667596605
[137.425344, 91.522816]
1.5015419105985548
[137.530752, 91.703808]
1.499727819372561
[137.407744, 91.488448]
1.501913596785465
[137.484736, 91.568192]
1.5014464411397355
[137.36, 91.559424]
1.5002278738669217
[137.249088, 91.740672]
1.4960549667654495
[137.310976, 91.546816]
1.4998989806483276
[137.259008, 91.606912]
1.4983477229316495
[137.477952, 91.526272]
1.5020599986854046
[137.513408, 91.630208]
1.5007431610326587
[137.554816, 91.499328]
1.5033423633450071
[137.745216, 91.468608]
1.5059288537549407
[137.5424, 91.494656]
1.5032834267391526
[137.423552, 91.67136]
1.4990892684476371
[137.560512, 91.697344]
1.500158085276712
[136.783232, 91.70848]
1.491500371612309
[136.373376, 91.7184]
1.4868704207661714
[136.424256, 91.802816]
1.486057421157974
[136.171712, 91.696448]
1.4850271190439133
[137.370304, 91.60768]
1.499550081390556
[138.129408, 91.694144]
1.5064147171710336
[138.243584, 91.532672]
1.5103195501601876
[138.515136, 91.537536]
1.513205861254557
[138.053632, 91.465664]
1.5093492570064324
[138.1552, 91.666944]
1.5071430765707647
[137.972928, 91.52896]
1.507423748723901
[137.954304, 91.468672]
1.5082136974722888
[137.476352, 91.601152]
1.500814662243549
[136.980544, 91.71264]
1.493584134095366
[136.949248, 91.707392]
1.4933283458764155
[136.840704, 91.613696]
1.4936708153331133
[137.406464, 91.52608]
1.5012820826588444
[137.909248, 91.340416]
1.5098381859789207
[138.166656, 91.48736]
1.5102267242163288
[137.39392, 91.480768]
1.5018885718143513
[136.896896, 91.541824]
1.4954573769471755
[136.830016, 91.460416]
1.4960572232691354
[136.57344, 91.436864]
1.493636527166986
[137.114112, 91.604992]
1.4967973797759844
[137.412352, 91.58752]
1.500339260196149
[137.284928, 91.498496]
1.5004063891935449
[137.741248, 91.557248]
1.5044275686398962
[138.184768, 91.54304]
1.5095059984898904
[138.446336, 91.6736]
1.5102094387042726
[137.929152, 91.550848]
1.5065851929629313
[137.643584, 91.664256]
1.5016058604130273
[137.867968, 91.60608]
1.5050089251717789
[137.539648, 91.484096]
1.5034268688625398
[136.864, 91.603456]
1.4940921006299153
[136.55648, 91.578176]
1.491146536921635
[136.40448, 91.462144]
1.4913763665981854
[136.22272, 91.492928]
1.4888879717566805
[135.52992, 91.567552]
1.480108586936997
[135.360384, 91.820544]
1.4741840780207098
[135.1312, 91.653184]
1.4743754019500295
[135.112832, 91.679808]
1.4737468909184452
[136.277952, 91.606976]
1.487637273388437
[136.601216, 91.743936]
1.4889399992605505
[136.855232, 91.529216]
1.4952081748411348
[136.995584, 91.552896]
1.496354457209087
[137.3536, 91.646272]
1.4987363588559282
[137.561856, 91.70688]
1.5000167490159955
[137.428224, 91.860416]
1.4960548839665608
[137.277184, 91.662016]
1.4976452623516376
[137.018432, 91.767744]
1.4931001463869484
[137.010304, 91.601408]
1.495722685834698
[137.071232, 91.620672]
1.4960732005982231
[135.966144, 91.679808]
1.4830544147736437
[135.386752, 91.797952]
1.4748341226610373
[135.102144, 91.619008]
1.4746082385000285
[134.630592, 91.656192]
1.4688652131653037
[135.176576, 91.53568]
1.47676377124199
[135.389248, 91.579072]
1.4783863282650431
[135.320256, 91.449408]
1.479728069972853
[135.189568, 91.240512]
1.4816835749453052
[135.6416, 91.220544]
1.486963287568204
[135.88704, 91.304192]
1.488289168584943
[136.183424, 91.16928]
1.4937424535984052
[135.983936, 91.070208]
1.4931769563982988
[134.90816, 91.199168]
1.4792696354422883
[133.691648, 91.155392]
1.4666345573940374
[133.425024, 91.266816]
1.4619226335232294
[132.619136, 91.203584]
1.4541000494015672
[132.215296, 91.260096]
1.448774456691345
[132.022272, 91.098048]
1.4492327212104477
[131.861248, 91.083008]
1.447704142577285
[132.355712, 90.931776]
1.4555496199700313
[132.59648, 90.792576]
1.460433064483158
[132.6592, 90.80064]
1.4609941075305195
[132.24256, 90.872192]
1.455258832096842
[131.988288, 90.824832]
1.4532180802712633
[132.105856, 90.804096]
1.4548446801342527
[131.749056, 90.910144]
1.449222828202758
[131.655168, 90.921984]
1.4480014866371593
[131.669888, 91.10976]
1.4451787382603136
[131.54688, 90.934912]
1.4466047979460297
[131.695232, 90.988736]
1.4473795086020318
[131.453184, 90.990208]
1.444695939149848
[131.533504, 90.850944]
1.447794576575891
[131.462784, 90.8736]
1.4466553982674837
[131.69728, 90.887232]
1.449018493598749
[131.972416, 90.974016]
1.4506605490517204
[131.966272, 90.828032]
1.4529244892149598
[131.963776, 90.866432]
1.4522830169011147
[131.195584, 90.995776]
1.4417766380716395
[131.11808, 90.959168]
1.441504829947433
[130.744448, 90.86272]
1.4389228937896643
[130.61888, 90.9152]
1.4367111330118616
[130.48128, 91.06848]
1.4327820119540813
[130.381504, 90.879168]
1.4346687680943557
[130.639936, 90.950784]
1.43638053741241
[131.722816, 90.841472]
1.4500295195568826
[132.608064, 90.994752]
1.4573155163937368
[132.932224, 90.783296]
1.4642806535686916
[133.216832, 90.861376]
1.4661546838119643
[133.630848, 90.847168]
1.4709412625828908
[133.497792, 90.745536]
1.4711224142199126
[133.549632, 90.675456]
1.472831104372941
[133.02144, 90.801408]
1.4649711158663974
[132.895616, 90.84448]
1.4628914822342534
[132.477888, 90.807616]
1.4588852106854122
[132.525312, 90.87456]
1.4583323649655087
[133.598144, 90.819328]
1.4710320692969672
[134.128256, 90.911744]
1.475367758867325
[134.57984, 90.712064]
1.483593626532409
[134.804992, 90.772992]
1.4850782047594069
[133.695232, 90.867968]
1.4713131034249605
[132.935552, 91.006016]
1.4607336728156521
[132.720448, 90.926144]
1.4596511208041552
[132.644928, 90.90592]
1.459145102981192
[131.852928, 90.894656]
1.4506125420618787
[131.3744, 90.991936]
1.4438026684034948
[131.308736, 90.964224]
1.4435206526908866
[131.257152, 91.002944]
1.4423396236499777
[131.283584, 91.036288]
1.4421016814745347
[131.246272, 90.981056]
1.442567032855719
[131.495104, 90.974656]
1.4454036957281817
[131.44992, 91.053248]
1.4436598681246384
[132.064576, 91.093696]
1.4497663592440029
[132.346624, 91.018368]
1.4540650080651853
[132.543744, 91.129984]
1.454447133448416
[133.011968, 91.169728]
1.4589488300327054
[133.388288, 91.192128]
1.4627171327770747
[133.414976, 91.357056]
1.4603686003191696
[133.782336, 91.305984]
1.4652088520288002
[133.503104, 91.228544]
1.4633918085988527
[133.271488, 91.44768]
1.4573523133665063
[133.471232, 91.345984]
1.4611614671532793
[133.308992, 91.31808]
1.4598313061334622
[135.523072, 92.137472]
1.470878992642646
[137.199488, 93.066112]
1.4742153191056266
[137.16384, 92.96608]
1.4754181310000376
[137.340992, 92.911936]
1.4781845897603512
[137.254144, 92.996864]
1.475900778761744
[138.641664, 93.648384]
1.4804490806803459
[139.756864, 94.23072]
1.4831348418010601
[140.907392, 94.685248]
1.488166266407202
[143.108032, 95.21024]
1.503073955070379
[144.41536, 95.8656]
1.506435676613926
[145.49376, 96.141952]
1.513322300757946
[147.110912, 96.8016]
1.519715707178394
[147.6064, 96.758144]
1.5255191335625455
[148.198272, 97.025024]
1.5274231934227607
[148.69792, 97.234688]
1.5292682381003784
[149.9376, 97.662464]
1.5352633331061563
[149.625856, 98.158464]
1.5243296390619967
[149.61088, 98.038016]
1.5260496499643568
[148.992128, 98.044736]
1.5196341392565942
[149.384704, 98.147392]
1.5220445592685743
[149.45792, 98.157504]
1.5226336643604956
[149.669504, 98.287616]
1.5227707222037006
[149.920768, 98.09568]
1.5283116239165682
[150.27552, 98.221504]
1.5299655765808677
[150.171328, 97.980608]
1.5326637695491743
[167.217152, 98.041728]
1.7055712441135267
[167.02208, 98.025088]
1.703870747864057
[166.750016, 98.0224]
1.7011419430660746
[166.66272, 97.862656]
1.7030267398424175
[166.297024, 97.538368]
1.7049395782385859
[165.96608, 97.555136]
1.7012541502684184
[165.685056, 97.48608]
1.6995765549296884
[165.734656, 97.486144]
1.700084229405976
[166.412544, 97.393856]
1.7086554617983294
[167.88288, 97.732544]
1.717778675647694
[168.199104, 97.903488]
1.7180093113740749
[168.157632, 97.579136]
1.7232949469853884
[167.12032, 97.710656]
1.710359205857752
[165.389376, 97.784704]
1.6913624445802893
[164.29664, 98.024896]
1.6760705362033743
[163.64288, 97.832384]
1.6726862140045569
[163.478848, 97.965888]
1.6687323652902528
[163.845888, 97.541248]
1.679760012912691
[163.771072, 97.47296]
1.6801692695081796
[163.363648, 97.446016]
1.6764528167062265
[163.30272, 97.453632]
1.6756966020517325
[163.026304, 97.366528]
1.6743567563588178
[163.579968, 97.254912]
1.6819712715384494
[163.750016, 97.193792]
1.6847785504654451
[163.68832, 97.225856]
1.6835883656298178
[162.6624, 97.266368]
1.672339610748085
[162.109952, 97.445888]
1.6635894579769235
[161.976576, 97.31296]
1.6644913072215664
[161.88992, 97.361344]
1.6627740882459467
[162.681024, 97.446208]
1.6694443769428156
[163.309184, 97.527744]
1.6744895073139392
[163.454272, 97.664192]
1.6736356350544528
[162.87296, 97.5392]
1.6698205439454088
[162.51968, 97.606144]
1.6650558391078332
[162.280128, 97.509504]
1.6642493433255487
[162.259584, 97.435904]
1.6652956183379795
[162.821376, 97.4064]
1.6715675356034099
[163.095104, 97.39584]
1.674559241955303
[163.291456, 97.520256]
1.6744362935224453
[163.079296, 97.428288]
1.673839285772937
[163.202048, 97.320128]
1.6769608852137967
[163.074624, 97.342592]
1.6752648624766433
[163.250496, 97.392192]
1.6762174939034127
[163.484544, 97.61952]
1.6747116150540384
[163.294976, 97.4096]
1.6763745667778125
[163.461248, 97.475776]
1.6769422589669871
[163.260032, 97.51296]
1.6742393216245306
[163.337152, 97.65632]
1.672571237580937
[163.375104, 97.573632]
1.6743776023424033
[163.209792, 97.572864]
1.6726965398904352
[163.268928, 97.520192]
1.6742063838430508
[163.258112, 97.611968]
1.672521467859351
[163.271232, 97.439744]
1.6756122840388414
[163.291648, 97.391552]
1.6766510508016137
[162.800768, 97.538944]
1.669084791403934
[162.6896, 97.670272]
1.6657023336640244
[162.605888, 97.527168]
1.6672881140155735
[162.224768, 97.405888]
1.6654513534130504
[162.909376, 97.38016]
1.6729216300322365
[163.454976, 97.16288]
1.6822780057569309
[163.404864, 97.12096]
1.6824881467399004
[162.343488, 96.962496]
1.6742915528907176
[161.689984, 96.829568]
1.6698410138522979
[161.51936, 97.051328]
1.6642673864287567
[161.142016, 97.11872]
1.6592271397316605
[161.484672, 97.192768]
1.6614885584902777
[161.5808, 97.19168]
1.662496213667672
[161.487808, 97.250304]
1.6605378220720008
[160.943808, 97.060288]
1.6581839114262673
[160.460032, 96.995456]
1.6543046305179492
[159.953472, 97.212544]
1.6453995072899235
[159.937152, 97.092288]
1.6472693691181735
[159.91776, 97.0848]
1.6471966775437554
[159.563392, 96.899904]
1.646682663380141
[159.479616, 97.041536]
1.6434160316670998
[159.931136, 97.066176]
1.6476505265850796
[160.387072, 97.222592]
1.6496893232387795
[161.082368, 97.402816]
1.6537752666206282
[159.893824, 97.36096]
1.6422786299559904
[159.10144, 97.279232]
1.6355129119440417
[158.852224, 97.438848]
1.630276088649981
[159.363136, 97.33984]
1.6371830485852452
[159.327744, 97.22528]
1.63874811160225
[159.339712, 97.119872]
1.6406499382536253
[159.507328, 97.197376]
1.6410661950380223
[159.671872, 97.387648]
1.6395495248021599
[159.721344, 97.372992]
1.6403043669439674
[159.484288, 97.1728]
1.6412441341609998
[159.315264, 97.184064]
1.6393146925816973
[159.182656, 97.288]
1.6362003124743032
[159.286976, 97.11776]
1.64014260625451
[159.408512, 97.095872]
1.6417640494541312
[159.771456, 97.091968]
1.6455682101324798
[159.825856, 97.252864]
1.6434051340637124
[160.471552, 97.110208]
1.6524684202097477
[160.62848, 97.012224]
1.6557550520643665
[160.751872, 96.99936]
1.6572467282258356
[160.327232, 97.036288]
1.652239953778941
[160.252672, 97.205568]
1.6485956030831483
[160.080832, 97.133568]
1.6480485098622135
[159.896384, 97.031424]
1.6478824839260322
[159.677824, 97.083264]
1.6447512930756014
[159.715264, 97.107456]
1.6447270948999013
[159.635392, 97.314496]
1.6404071187914284
[159.634816, 97.231936]
1.6417940706230512
[159.57472, 97.359744]
1.639021565216934
[159.608128, 97.17344]
1.6425077469728353
[159.735936, 97.251456]
1.6425043137657498
[160.2384, 97.321152]
1.6464909909821044
[160.104704, 97.12736]
1.6483996270463854
[160.157248, 97.187264]
1.6479242383034882
[160.17472, 97.182272]
1.648188673753172
[160.184128, 97.105344]
1.6495912727521977
[160.181376, 97.230912]
1.6474326189596986
[159.845824, 97.050112]
1.6470441991864986
[159.74112, 97.128256]
1.6446410815818624
[159.689984, 97.071808]
1.6450706676855138
[159.476928, 96.989056]
1.6442775564286343
[159.77408, 97.180096]
1.6441029241214167
[159.969856, 97.386432]
1.6426298069940584
[160.082816, 97.25344]
1.6460375694679799
[160.018176, 97.1104]
1.6477964872969324
[159.791488, 97.169152]
1.644467248206509
[159.861824, 97.29792]
1.6430137869339858
[159.662784, 97.092096]
1.6444467735046115
[159.586944, 97.086784]
1.643755590874243
[160.633152, 97.150784]
1.6534416438677426
[161.117312, 97.034944]
1.6604050598514284
[161.42272, 97.250688]
1.6598619847296094
[160.535872, 97.176128]
1.6520093494566896
[159.945344, 97.223296]
1.6451339399149767
[160.006208, 97.173824]
1.6465978327661572
[160.129024, 97.243008]
1.6466893331806436
[160.321664, 97.23104]
1.6488732816187095
[160.414912, 97.35296]
1.6477661490724063
[160.333696, 97.19776]
1.6495616359883192
[160.138304, 97.12448]
1.648794454292059
[159.966656, 97.153088]
1.646542166523827
[159.837312, 97.042752]
1.6470814018135018
[159.846272, 97.228096]
1.6440337574850794
[160.236288, 97.04512]
1.6511524536215731
[160.51264, 97.066624]
1.6536336939049203
[160.632064, 97.130048]
1.6537834306434196
[160.102912, 97.1312]
1.648316009685868
[159.813888, 97.186688]
1.6444010109697327
[159.746048, 97.05024]
1.6460139408207544
[159.699584, 97.087104]
1.6449103683224497
[160.079552, 97.078848]
1.6489642728352114
[160.12608, 97.242752]
1.6466633934835575
[160.332928, 97.115136]
1.650957148430498
[160.453952, 97.186176]
1.6509956313128318
[159.639168, 97.135616]
1.6434668824254948
[159.411008, 97.206016]
1.6399294463420866
[159.234304, 97.179328]
1.6385614850104748
[159.010944, 97.092736]
1.6377223523704183
[160.00928, 97.141888]
1.6471707858920757
[160.45952, 97.186496]
1.6510474870912106
[160.697408, 97.162496]
1.6539036625819081
[160.810368, 97.119616]
1.6557969916190776
[161.229248, 97.124224]
1.6600312605843832
[161.464448, 97.167936]
1.6617050299390943
[161.616512, 97.13056]
1.663910019668372
[160.917888, 97.059968]
1.6579223269473982
[160.656256, 97.115648]
1.654277753467701
[160.65056, 97.232]
1.6522395919039001
[160.231296, 96.965568]
1.6524556015595142
[160.08608, 97.087424]
1.6488858536405293
[159.814848, 97.144704]
1.6451215703946147
[159.572928, 97.055104]
1.6441477204537331
[159.538432, 96.93216]
1.6458771990637577
[159.341696, 97.14528]
1.6402412551592833
[159.523776, 97.233984]
1.6406175026213057
[159.411008, 97.266176]
1.638915135308702
[159.361472, 97.31392]
1.637602020348168
[160.502464, 97.454848]
1.6469418124791493
[160.807296, 97.266624]
1.653262849957659
[160.666752, 97.21568]
1.652683517720598
[160.68928, 97.071232]
1.655374890060116
[160.620224, 96.979136]
1.65623484210047
[160.738112, 97.123968]
1.6549788410621773
[159.81088, 97.116416]
1.6455599020458085
[159.451456, 97.310784]
1.6385795021443874
[159.259968, 97.170816]
1.6389691324605113
[159.127552, 97.162752]
1.63774233154697
[160.704384, 97.227904]
1.6528627830956844
[160.863104, 97.158336]
1.6556798996639874
[161.261952, 97.155264]
1.6598375153403937
[160.651392, 97.0512]
1.6553261783470992
[160.41312, 97.100416]
1.6520332930396509
[160.075648, 96.94592]
1.6511849905596852
[160.230592, 97.024704]
1.6514411834742624
[159.824, 97.049024]
1.6468377878792475
[159.838336, 97.164864]
1.6450219700816955
[159.775296, 97.113664]
1.645240117806697
[159.727232, 97.235008]
1.6426926400828805
[160.638336, 97.06016]
1.6550388542528676
[161.120192, 97.280256]
1.6562476151378551
[161.276736, 97.040512]
1.661952649219328
[161.523968, 96.962624]
1.6658374261818656
[160.829184, 96.981248]
1.6583534169409742
[160.083456, 97.100032]
1.6486447295918503
[160.210176, 97.262592]
1.647192129117842
[160.023232, 97.165504]
1.6469140323709945
[160.146816, 97.219904]
1.6472636714391324
[160.246528, 97.377792]
1.6456167747159436
[159.359616, 97.227648]
1.639036007535634
[158.654912, 97.199744]
1.6322564800170667
[158.579968, 97.38848]
1.6283236785295345
[159.68416, 97.085888]
1.6447721011729326
[160.191296, 97.139008]
1.6490933899592632
[160.397568, 97.114368]
1.6516358115001069
[160.6368, 97.071808]
1.6548244367715907
[160.662592, 97.13984]
1.653930992680243
[160.5888, 97.205568]
1.6520535119963498
[160.64096, 97.384384]
1.649555641282282
[160.177216, 97.193216]
1.6480287677691412
[159.931072, 97.150912]
1.6462127704987473
[160.074112, 97.173824]
1.64729662177337
[160.168448, 97.122816]
1.6491330729125482
[160.303744, 97.21376]
1.648982037110796
[160.432448, 97.442432]
1.6464331267922376
[160.6656, 97.150592]
1.653778908521731
[160.601024, 97.141312]
1.6532721320461474
[160.766912, 97.106752]
1.6555688321240525
[160.716032, 96.986176]
1.6571024720059075
[160.233536, 97.12928]
1.6496934395066039
[159.886144, 97.291136]
1.6433783237971444
[159.616, 97.112512]
1.6436193103521
[159.708736, 97.05056]
1.6456240541012848
[159.962816, 97.262656]
1.6446478286589252
[160.050688, 97.167808]
1.647157544194061
[159.85024, 97.146048]
1.6454631278464362
[160.960192, 97.045184]
1.6586108178227577
[161.706176, 97.000384]
1.6670673798569704
[161.906112, 97.176128]
1.6661099318548687
[160.38688, 97.2544]
1.6491478020531718
[159.946368, 97.128448]
1.6467509910175853
[159.75808, 97.06976]
1.645806891868281
[159.00768, 97.072256]
1.6380342494564049
[158.640128, 97.158208]
1.6328021200226337
[158.531968, 97.094464]
1.6327601128731706
[158.21728, 97.106624]
1.629315009447759
[158.89568, 97.11456]
1.6361674294771043
[159.303872, 97.325696]
1.6368120501290844
[159.388032, 97.193344]
1.639906864404213
[159.77632, 97.185024]
1.6440426047535883
[159.799168, 97.06272]
1.646349576850927
[160.067392, 97.135232]
1.6478819137426883
[160.099712, 97.049472]
1.6496711285559598
[160.187328, 97.059648]
1.6504008751402026
[160.53024, 97.149504]
1.652404113149152
[160.500096, 97.219648]
1.6509018423930109
[160.617536, 97.089728]
1.6543205888886618
[160.732928, 97.014848]
1.6567868868897262
[160.48416, 97.1168]
1.6524860786187354
[160.39872, 97.0656]
1.6524774997527445
[160.323712, 97.00224]
1.652783605821886
[160.25536, 97.067072]
1.6509755233989134
[160.393472, 97.340032]
1.6477647346571656
[160.328064, 97.241856]
1.6487556963125016
[160.325824, 97.245952]
1.648663216336244
[160.644672, 97.187008]
1.6529438996619796
[160.854464, 97.079488]
1.6569356443247827
[160.904384, 97.195712]
1.6554679284617
[160.755328, 97.076736]
1.6559614035642896
[160.6768, 97.209216]
1.652896778840393
[160.564992, 96.9456]
1.6562380551567064
[160.546112, 97.052864]
1.6542130276547016
[160.113088, 97.1584]
1.6479592912192873
[159.923712, 97.294528]
1.643707156891701
[159.906624, 97.153216]
1.645922086614199
[159.833472, 97.259904]
1.6433644845053517
[159.84672, 97.19776]
1.6445514793756564
[159.9344, 97.14112]
1.6464129711496018
[160.027264, 97.360704]
1.6436535216507884
[160.32704, 97.000896]
1.6528408149961833
[160.647104, 97.013696]
1.6559219019961884
[160.787392, 97.11456]
1.6556466095300233
[160.039424, 97.11872]
1.6478741070722513
[159.648192, 97.214016]
1.6422343049792325
[159.420032, 97.283136]
1.6387221727720618
[160.049344, 97.14752]
1.6474876970611292
[160.294976, 97.238016]
1.6484805284385893
[160.346752, 97.195776]
1.6497296343413115
[160.43584, 97.076224]
1.652679032921594
[159.500992, 96.977984]
1.6447134227908882
[159.198784, 97.103616]
1.6394732818188766
[159.000896, 96.991168]
1.6393337587191446
[158.712192, 96.965056]
1.6367978171435282
[159.112256, 97.075712]
1.6390531959219625
[159.286528, 97.266624]
1.6376278054021902
[159.238656, 97.150656]
1.6390898688321776
[159.243392, 97.1184]
1.6396830260795072
[159.724288, 97.077184]
1.6453329342556948
[160.024768, 97.1136]
1.6478100698563332
[160.05472, 96.910272]
1.651576419061129
[160.26624, 96.968384]
1.6527679784784286
[160.53024, 97.003968]
1.6548832311684403
[160.681152, 97.101952]
1.6547674757351942
[160.881536, 97.15392]
1.6559448759247184
[160.823488, 97.056064]
1.6570163817893953
[160.181504, 97.154432]
1.6487307959352795
[159.873024, 97.193152]
1.6449000851418007
[159.777792, 97.107968]
1.6453623249536022
[159.621952, 97.02816]
1.6451095434562502
[160.569536, 97.08928]
1.6538338321182318
[160.716352, 97.00768]
1.6567384355547934
[161.0224, 96.978944]
1.6603851656706017
[160.202624, 97.099584]
1.6498796122545694
[159.802304, 97.244416]
1.643305709193626
[159.675712, 97.254976]
1.6418256275133933
[159.473728, 97.229504]
1.6401783557386036
[159.416448, 97.1712]
1.6405730092867024
[159.5728, 97.369664]
1.6388348633923602
[159.323968, 97.111872]
1.6406229714117755
[159.42624, 96.930368]
1.644750177777103
[159.03872, 97.150464]
1.6370351046393357
[159.008448, 97.237312]
1.6352616575826364
[159.168384, 97.293824]
1.6359556799823183
[159.011776, 97.227328]
1.6354638070481582
[159.783232, 97.200128]
1.643858246771033
[160.17248, 97.355968]
1.6452250775216986
[160.335808, 97.176]
1.6499527455338765
[160.360832, 97.24704]
1.649004761481686
[160.136832, 97.147072]
1.6483958672475483
[159.891072, 97.241536]
1.6442672398757667
[159.72256, 97.098304]
1.6449572589856976
[159.798592, 97.020992]
1.6470517225797898
[160.19328, 97.086336]
1.6500085037713235
[160.57792, 97.278848]
1.6506971793087024
[160.682048, 97.294272]
1.6515057330404816
[160.818944, 97.251008]
1.6536480938069043
[159.912832, 97.138816]
1.6462299890498975
[159.538112, 97.347456]
1.6388524010324421
[159.403264, 97.172992]
1.6404070793662504
[159.1616, 97.234368]
1.6368862499317112
[159.884224, 97.157312]
1.645622143189799
[160.266176, 96.95936]
1.6529211413936724
[160.508672, 97.076608]
1.6534227483514876
[160.307968, 97.132736]
1.6504010347242766
[160.196288, 97.30208]
1.6463809201201043
[160.268096, 97.258688]
1.6478537732279506
[160.091264, 97.295104]
1.6454195269681813
[159.794752, 97.283264]
1.6425718610757138
[159.593216, 97.384704]
1.6387914060918645
[159.366784, 97.211776]
1.6393773528013724
[159.265408, 97.154176]
1.6393058389996535
[159.603968, 97.13056]
1.6431900320558226
[159.84448, 97.130816]
1.6456618669815357
[160.110336, 97.320192]
1.6451913288457136
[159.42592, 97.231552]
1.6396521162184061
[159.13248, 97.201024]
1.6371481847763247
[158.91136, 97.399232]
1.631546334985475
[160.881216, 97.278976]
1.6538128032926662
[161.118528, 97.13664]
1.658679237824162
[161.30528, 97.108864]
1.661076789035448
[160.82656, 97.102464]
1.6562562202335052
[160.559936, 97.123456]
1.653153034422498
[160.420032, 97.200512]
1.6504031583701944
[160.784896, 97.084288]
1.6561371496075659
[161.056768, 97.090368]
1.658833634248868
[161.230144, 97.194624]
1.658838085530327
[162.136512, 97.165312]
1.668666612216508
[162.200256, 97.035328]
1.671558795575978
[162.501376, 97.053248]
1.674352784154117
[161.009152, 97.047552]
1.6590748419908625
[160.18688, 97.000384]
1.6514045965013913
[159.90016, 97.078272]
1.647126145797074
[160.048384, 97.242816]
1.645863320124337
[159.874048, 97.081728]
1.6467985407099468
[159.956864, 97.19008]
1.6458147168929176
[160.424384, 97.187136]
1.6506750852293868
[160.606528, 97.142976]
1.6533004712558939
[160.705024, 97.086208]
1.6552817059246974
[159.873216, 97.176064]
1.645191309662429
[159.501696, 97.15168]
1.6417801112651886
[159.379456, 97.292992]
1.6381391169468815
[158.990848, 97.054272]
1.638164345820862
[159.520576, 97.142848]
1.64212373102341
[159.731776, 97.276032]
1.642046583479063
[159.906176, 97.105088]
1.6467332381182744
[160.163904, 97.177216]
1.648163124986005
[159.680704, 97.001408]
1.6461689298365647
[159.758656, 97.23328]
1.6430450150401181
[159.703616, 96.98112]
1.6467495529026681
[159.689152, 97.083584]
1.644862554723979
[159.30016, 97.15552]
1.639640856227212
[159.279808, 97.239424]
1.638016778050845
[159.00992, 97.161664]
1.636549987451841
[158.980032, 97.233344]
1.6350361456251057
[160.064448, 97.082624]
1.648744558037492
[160.538816, 97.165952]
1.6522126598419988
[160.71808, 96.906048]
1.658493802161863
[160.915392, 97.003008]
1.6588701249346824
[160.60896, 96.943168]
1.6567331490549184
[160.543936, 97.088256]
1.6535875976595975
[160.47328, 96.9776]
1.6547458382141855
[160.459136, 96.990848]
1.6543739879457493
[159.907392, 97.132288]
1.6462846216491882
[159.550848, 97.280512]
1.6401111046783965
[159.497984, 97.097024]
1.6426660409282987
[159.416256, 97.22816]
1.639609923709345
[159.595392, 97.224896]
1.6415074591594319
[159.630528, 97.187904]
1.6424937819422465
[159.653248, 97.230016]
1.6420160622003803
[160.399744, 97.120704]
1.6515504665205063
[160.51488, 97.070144]
1.6535968052133518
[160.843328, 97.076864]
1.6568657182827828
[160.824832, 97.119872]
1.6559415564303872
[160.219584, 97.251456]
1.647477483524771
[159.709888, 97.290496]
1.6415774876921174
[159.528576, 97.21376]
1.6410081864954096
[159.28576, 97.196736]
1.6387974180532154
[159.80768, 97.133696]
1.6452342140877663
[160.091008, 97.164608]
1.6476267572653613
[160.109312, 97.21344]
1.6469874124400903
[160.128256, 97.17888]
1.6477680747092371
[160.014976, 97.106688]
1.6478265225151123
[159.967232, 97.057472]
1.648170189308042
[159.735552, 97.166848]
1.6439305718757082
[159.708736, 97.29824]
1.6414349940965014
[159.58304, 97.257856]
1.6408241612893462
[159.682752, 97.18528]
1.6430754945604928
[160.098304, 97.150976]
1.6479330480426673
[160.398208, 97.243392]
1.6494509776047304
[160.494016, 97.23616]
1.6505589690090599
[160.67552, 97.157248]
1.6537677147874754
[160.62976, 97.275712]
1.65128331314604
[160.536704, 97.249152]
1.6507774175758365
[160.673664, 97.301056]
1.6513044216087438
[160.491968, 97.242624]
1.6504281908312142
[160.47424, 97.31744]
1.6489772028528493
[160.633664, 97.344768]
1.6501520040604545
[160.571584, 97.097152]
1.6537208423991674
[160.802112, 97.109888]
1.6558778442829631
[160.91456, 97.256192]
1.6545430855446202
[160.973056, 97.248512]
1.655275260149996
[160.982528, 97.463552]
1.6517203066844925
[161.105408, 97.336576]
1.6551374069291283
[161.168576, 97.414464]
1.6544624831072314
[161.85856, 97.199232]
1.6652246799645498
[162.40192, 97.340288]
1.668393666556647
[162.551296, 97.206464]
1.6722272296624225
[162.900672, 97.217216]
1.6756360519519506
[162.326208, 97.344448]
1.667544593811863
[162.032896, 97.544576]
1.6611164110242274
[161.762624, 97.71456]
1.6554608033848792
[160.940032, 97.305984]
1.6539582190546473
[160.25632, 97.138176]
1.6497769116027048
[160.123456, 97.148224]
1.6482386337808914
[158.938944, 97.11072]
1.6366776397085718
[158.64832, 96.945152]
1.6364750245582165
[158.333696, 96.96608]
1.6328771463175575
[155.0416, 88.284416]
1.7561604530520993
[155.56128, 86.232448]
1.8039761552403104
[157.439808, 90.240896]
1.744661400525101
[158.543616, 94.267904]
1.6818408946485113
[159.48288, 96.301056]
1.6560865126961846
[159.08832, 96.972032]
1.6405587953442082
[154.749248, 98.835904]
1.56571895168784
[147.95296, 107.661056]
1.3742477131192172
[140.374272, 124.18144]
1.130396555234019
[142.656192, 121.394624]
1.175144230439727
[143.519296, 119.335936]
1.2026494349531058
[147.481664, 118.946048]
1.239903859605323
[168.531776, 132.183168]
1.2749866609340155
[170.830592, 142.734464]
1.196841934404854
[169.146944, 151.174144]
1.1188880553542275
[164.990784, 157.5488]
1.0472360563837997
[159.92288, 163.471936]
0.97828950897113
[156.921536, 165.244864]
0.9496303376787553
[153.96832, 166.480576]
0.924842547397241
[150.820352, 167.072896]
0.9027218394538395
[144.793216, 167.236416]
0.8657995636548442
[143.697664, 165.258752]
0.8695313395565277
[142.632384, 162.700544]
0.8766558518698008
[140.927232, 157.296064]
0.895936162776457
[139.834752, 155.171776]
0.9011609946386128
[138.908352, 153.343808]
0.9058621525819941
[137.992896, 150.978176]
0.9139923375415531
[137.192064, 147.957312]
0.9272408517397234
[137.005952, 146.819456]
0.9331593763703906
[136.696512, 144.953088]
0.9430396681166254
[136.340608, 141.13952]
0.9659988074211957
[136.280896, 130.845312]
1.0415420615145923
[137.88896, 125.137856]
1.1018964556976267
[139.071616, 121.544832]
1.1442001581770256
[140.0608, 118.757312]
1.17938674799241
[141.83072, 114.710208]
1.2364263170022325
[142.3248, 113.882752]
1.2497485132779371
[142.590656, 113.357824]
1.2578810263683255
[142.617408, 112.100672]
1.2722261647102349
[141.57696, 109.832768]
1.2890229626189518
[139.921728, 107.585664]
1.300561085908249
[139.09664, 105.943936]
1.3129268672819558
[137.676096, 102.191424]
1.3472372789325258
[136.896448, 99.897728]
1.370365980695777
[136.301824, 97.05952]
1.4043117460296528
[136.166592, 96.491968]
1.4111702229972136
[136.344832, 95.664832]
1.4252346358586612
[136.583744, 95.23168]
1.4342259214580695
[136.758592, 95.07776]
1.438386768893167
[136.845504, 95.09184]
1.4390877703071052
[136.384192, 95.519232]
1.4278191851458772
[136.34592, 96.308416]
1.4157217578991228
[136.224704, 96.802752]
1.4072399925159154
[135.892864, 97.620544]
1.3920519025175686
[136.207424, 98.095488]
1.3885187461425341
[136.100352, 98.220608]
1.3856598403463354
[135.890304, 98.014656]
1.386428413318106
[135.482688, 97.22496]
1.3934969785536553
[134.91616, 96.803776]
1.3937076173557525
[134.423808, 96.820416]
1.3883828799083038
[134.278784, 97.820864]
1.372700858581662
[134.272064, 98.54144]
1.3625949042352132
[133.883136, 99.673984]
1.3432104409511714
[133.772224, 100.104512]
1.3363256193686854
[133.006208, 100.758976]
1.320043268403204
[132.699904, 101.764608]
1.3039887501949599
[132.720256, 102.451392]
1.2954460979895717
[132.7744, 103.8432]
1.2786046654956706
[133.94368, 104.039104]
1.2874359240925413
[133.82752, 103.5152]
1.2928296520704206
[131.948352, 99.135168]
1.330994385362821
[128.48768, 97.552448]
1.3171138462870764
[146.828288, 90.840896]
1.6163236434832169
[148.290368, 83.987136]
1.7656319177260669
[148.316096, 81.86304]
1.8117589574000672
[152.128576, 89.780416]
1.6944516719548282
[152.634304, 90.4992]
1.6865818040380465
[151.446208, 90.370368]
1.675839230841685
[150.838272, 90.43968]
1.6678328804347826
[150.856256, 90.647936]
1.6641995687579694
[150.649472, 90.519232]
1.6642813761389403
[150.587456, 90.601216]
1.6620908929081042
[150.544064, 90.505728]
1.66336504138169
[150.509248, 90.494592]
1.6631850000495059
[150.038144, 90.568448]
1.656627084964512
[149.986176, 90.697984]
1.6536880907959322
[149.564352, 90.522304]
1.6522375745098137
[149.703744, 90.55072]
1.65325846111439
[150.23104, 90.518464]
1.6596728817669733
[150.731712, 90.408896]
1.667222128229505
[150.596608, 90.51744]
1.6637303043479799
[149.675264, 90.488]
1.6540896472460436
[149.338176, 90.414976]
1.65169734712975
[148.951936, 90.406208]
1.6475852631713077
[149.186496, 90.398016]
1.6503293169620006
[149.325248, 90.502784]
1.649951983797537
[149.291264, 90.400448]
1.651443851251711
[149.137472, 90.429888]
1.649205537001218
[149.555392, 90.373504]
1.6548588400423205
[149.950784, 90.215552]
1.6621389624706835
[149.868032, 90.439808]
1.6571025007041147
[149.609792, 90.427648]
1.6544695710763149
[149.03712, 90.31008]
1.6502822276317326
[149.014144, 90.455616]
1.647373049783885
[148.851136, 90.38208]
1.6469098299131864
[148.79712, 90.448832]
1.64509719705391
[148.99584, 90.64096]
1.643802536954595
[149.58208, 90.461248]
1.6535487107142275
[150.231488, 90.430144]
1.6612987810790174
[150.368512, 90.478848]
1.6619189492775153
[149.183296, 90.496064]
1.6485059062900238
[149.159168, 90.468096]
1.6487488362748344
[149.048256, 90.438016]
1.6480708289752841
[149.511808, 90.445376]
1.6530619320992155
[149.66656, 90.435648]
1.6549509326233833
[149.944192, 90.438144]
1.657975112801961
[149.683136, 90.342656]
1.6568378950470526
[149.583744, 90.473664]
1.6533401808508605
[149.590912, 90.330304]
1.6560434912296986
[149.595712, 90.309504]
1.6564780601607554
[149.062976, 90.372672]
1.6494253484062085
[148.860864, 90.377216]
1.6471061024937965
[148.804736, 90.575552]
1.6428797033442313
[148.742656, 90.393856]
1.6454951982577224
[148.846656, 90.58944]
1.6430905853927344
[149.006016, 90.426752]
1.6478090023624867
[149.016704, 90.384256]
1.6487020040304365
[149.434624, 90.451968]
1.652088144726713
[149.7424, 90.398528]
1.6564694504760078
[149.74976, 90.624064]
1.6524282115619975
[149.677504, 90.402048]
1.655687092398615
[149.455808, 90.319232]
1.6547506515555845
[149.49952, 90.322432]
1.6551759810896143
[149.361472, 90.396224]
1.6522976888946157
[149.648768, 90.412288]
1.6551817381283391
[149.55968, 90.568192]
1.6513488532486107
[149.637504, 90.40416]
1.6552059551241889
[148.691584, 90.721024]
1.6389980783285691
[148.380864, 90.561856]
1.6384476925914593
[148.112576, 90.598016]
1.6348324448959235
[148.606976, 90.54464]
1.6412564675280612
[148.698944, 90.554816]
1.6420876389390489
[148.817472, 90.633088]
1.6419772875883916
[149.659392, 90.472192]
1.6542032274403164
[150.398336, 90.444672]
1.6628766811161635
[150.710528, 90.52]
1.6649417587273532
[150.323584, 90.355264]
1.6636948125125284
[150.185408, 90.357376]
1.662126708947369
[150.253696, 90.518272]
1.6599266941375106
[149.423232, 90.34464]
1.6539247043322107
[149.132352, 90.47232]
1.6483754589248956
[148.787136, 90.32288]
1.6472806890125737
[149.077632, 90.38592]
1.649345738805336
[150.091456, 90.403904]
1.6602320182986787
[150.305792, 90.380224]
1.6630384983334408
[150.647488, 90.462592]
1.6653014762168212
[149.803136, 90.378368]
1.6575109654558047
[146.911744, 84.22976]
1.744178589610133
[146.099456, 83.00832]
1.7600579797302247
[147.180416, 84.638336]
1.7389332417877403
[148.213696, 87.574016]
1.692439181960092
[148.465408, 89.28128]
1.6628951556250091
[149.132736, 90.35456]
1.6505280530390496
[150.541184, 89.867136]
1.6751527944542484
[146.208512, 88.577216]
1.650633408934415
[136.952576, 92.133248]
1.48646204245399
[134.110336, 98.876544]
1.3563412572348807
[133.205376, 101.779584]
1.3087632191540497
[134.022528, 99.893312]
1.341656666664531
[133.014848, 94.328704]
1.4101205927731182
[134.16992, 93.00832]
1.4425582571537685
[136.267008, 92.566848]
1.4720929894901469
[138.667072, 95.51232]
1.4518239322424582
[139.5216, 97.960256]
1.4242674090194294
[139.985984, 102.094848]
1.3711366121040702
[140.228928, 103.303744]
1.3574428435042973
[139.277504, 101.006272]
1.378899559821394
[137.639104, 98.3488]
1.399499577015683
[134.686848, 99.012608]
1.3602999731104952
[129.03552, 95.374656]
1.3529330055984683
[129.692864, 95.305408]
1.3608132709531024
[131.878848, 90.821184]
1.4520714462387982
[133.645184, 87.42816]
1.5286285791671699
[132.669568, 85.570112]
1.5504194735657235
[132.399424, 85.522048]
1.5481320559582485
[133.308096, 88.959232]
1.4985302031384444
[134.195648, 90.631616]
1.4806714689937783
[134.078016, 91.18912]
1.470329091891664
[134.784768, 91.317632]
1.4759993776448344
[134.784384, 90.665664]
1.486608910733836
[133.91808, 89.20992]
1.501156822021587
[132.968192, 87.655232]
1.5169452976862807
[132.934272, 87.1776]
1.5248673053628454
[133.524352, 87.83168]
1.5202299671371422
[135.140992, 88.648896]
1.5244520586020611
[135.479168, 88.714496]
1.5271367601524783
[136.198784, 88.620096]
1.536883733459282
[137.177344, 88.790592]
1.5449535914796018
[137.42624, 88.721664]
1.5489592260127132
[137.995136, 88.35584]
1.5618111490989164
[137.980032, 87.61056]
1.574924666615531
[137.977664, 87.178432]
1.5827041257177006
[138.22208, 87.310272]
1.5831136111911324
[139.73728, 86.614528]
1.6133238063711435
[140.722368, 85.840832]
1.639340681134125
[144.975168, 84.875008]
1.7081019656575467
[145.356864, 84.460928]
1.720995345919003
[144.50368, 84.036544]
1.719533825665177
[144.299264, 84.33152]
1.7110952583328274
[144.6688, 83.869888]
1.724919437116692
[146.92192, 83.553856]
1.7584098093569733
[148.464, 83.20096]
1.784402487663604
[150.382144, 83.621312]
1.798371018144274
[150.509184, 87.249088]
1.7250516589926992
[152.965952, 89.411136]
1.7108154402601483
[155.53216, 85.75392]
1.813703210302223
[156.895616, 91.618752]
1.7124836627331486
[158.373504, 94.725248]
1.671924933888798
[159.056384, 94.980288]
1.6746252022314356
[158.71648, 95.002752]
1.6706513933406897
[158.379008, 93.8576]
1.6874393549376927
[158.623744, 93.649792]
1.693797077520471
[160.081536, 95.795584]
1.6710742741544327
[160.605056, 96.250368]
1.6686175786881148
[160.741312, 96.273088]
1.6696390999736084
[160.401152, 96.270144]
1.6661567681876532
[158.474432, 96.514816]
1.6419699955704212
[158.207872, 96.485888]
1.6396996004223956
[158.021312, 96.63136]
1.6353005069989701
[158.620416, 96.452672]
1.644541438934942
[159.003968, 96.335104]
1.6505298836860132
[159.090176, 96.414976]
1.6500566882887573
[158.719232, 96.360192]
1.647145244376433
[158.4416, 96.497728]
1.6419205227298201
[158.354112, 96.568704]
1.6398077787188694
[158.531648, 96.41856]
1.6442026099539342
[158.61856, 96.306112]
1.647024853417403
[158.601856, 96.343424]
1.646213611839247
[158.1792, 96.43264]
1.6403076800552179
[157.669376, 96.40992]
1.6354061490767755
[157.454464, 96.596224]
1.630027111618773
[158.071808, 96.404096]
1.639679376278784
[158.415104, 96.430016]
1.642798690399471
[158.44416, 96.586368]
1.6404401913114697
[157.912, 96.556544]
1.6354355019168871
[157.1312, 96.428416]
1.6295113672716557
[156.967296, 96.56832]
1.6254533163671068
[157.850752, 96.392576]
1.6375820478124787
[158.211264, 96.357888]
1.641912948527888
[158.301952, 96.432448]
1.6415838784887014
[158.563328, 96.367872]
1.6453961751900053
[158.738944, 96.364224]
1.6472808829965777
[158.823936, 96.321344]
1.64889659346946
[158.85408, 96.316672]
1.6492895435589803
[158.65344, 96.294912]
1.6475786384227653
[158.958592, 96.458176]
1.6479535337678375
[158.992704, 96.449536]
1.648454835490344
[158.926208, 96.410944]
1.6484249754882598
[158.942592, 96.334144]
1.6499092159888813
[159.201088, 96.46432]
1.6503624137919595
[159.542144, 96.526528]
1.6528321002077275
[159.789504, 96.475776]
1.6562655479443875
[159.909696, 96.407552]
1.6586843321153928
[159.794944, 96.4512]
1.6567439700076307
[159.624704, 96.465792]
1.654728590213617
[159.60576, 96.390592]
1.6558230081209586
[159.56064, 96.485312]
1.6537298443933106
[160.503936, 96.4192]
1.6646470412531944
[161.069248, 96.448704]
1.6699990909157263
[161.284608, 96.333184]
1.6742372804785524
[161.501632, 96.442432]
1.6745910347843573
[160.867264, 96.486464]
1.66725214430078
[160.589376, 96.628352]
1.6619281264364312
[160.456128, 96.597056]
1.6610871453473697
[160.395264, 96.5856]
1.660654010535732
[160.19456, 96.530816]
1.6595173089596589
[159.914496, 96.448512]
1.6580296853102308
[159.870528, 96.657088]
1.6539969422625271
[160.49792, 96.63712]
1.6608309519157856
[160.656896, 96.52448]
1.6644160735183446
[160.837376, 96.556032]
1.6657413593798056
[160.488128, 96.502784]
1.6630414310119797
[159.896448, 96.434688]
1.6580802127964576
[158.589184, 94.648512]
1.6755591889284007
[157.70368, 89.394944]
1.764123035862073
[156.471616, 86.568832]
1.8074821201237878
[156.087744, 83.958656]
1.8591024610970426
[155.364032, 82.688448]
1.8789085508050656
[155.085504, 81.912]
1.8933184881336065
[154.770432, 80.556288]
1.9212706523915304
[154.499648, 79.900288]
1.9336557084750432
[153.589312, 79.736448]
1.926212113185679
[148.034688, 79.855424]
1.853783758007471
[143.56736, 79.722688]
1.8008344124071682
[142.069696, 79.72256]
1.7820513540960048
[143.733504, 79.793344]
1.801321974925628
[146.797504, 81.261824]
1.8064756213200432
[146.433408, 84.91968]
1.7243754097990005
[143.566656, 85.73504]
1.6745388583244376
[135.809536, 85.044672]
1.596919981065951
[133.640512, 82.595072]
1.618020406834926
[134.60736, 83.508736]
1.6118955506643042
[134.039936, 84.5792]
1.5847860466876018
[133.019776, 85.071936]
1.5636152443974005
[132.447872, 86.274816]
1.5351857951224142
[131.383424, 87.311232]
1.5047711616301553
[131.207872, 87.648576]
1.4969766536766096
[132.610752, 88.397184]
1.500169417161524
[133.697728, 89.279296]
1.4975222026840356
[133.459008, 92.314304]
1.445702369158305
[133.934976, 93.930048]
1.4259012834742724
[134.928448, 97.954496]
1.3774604894092866
[135.27264, 100.255552]
1.3492782923383635
[136.454976, 102.493824]
1.3313482771410694
[138.324352, 102.164288]
1.3539403514464858
[139.701824, 102.48]
1.3632106167056985
[141.515456, 103.728192]
1.3642911658963457
[142.416256, 104.432832]
1.3637115193811846
[143.5792, 105.209216]
1.3647017386765812
[143.1152, 105.610496]
1.3551228847556969
[142.724672, 106.106304]
1.3451102019348447
[142.071424, 106.191232]
1.3378828112663765
[141.681792, 106.17152]
1.3344613696780454
[142.66656, 106.593472]
1.3384174220350005
[142.441728, 106.199296]
1.341268100308311
[142.384768, 106.228608]
1.3403617978313338
[142.013056, 106.80384]
1.329662454084048
[141.9936, 107.635136]
1.31921234344889
[142.130368, 107.980096]
1.316264508599807
[141.677696, 108.045248]
1.3112811402867066
[142.179776, 108.202816]
1.3140117905988695
[142.423104, 108.363776]
1.31430547418355
[142.368704, 108.796288]
1.308580528041545
[143.094592, 110.200064]
1.2984982658449273
[146.947968, 113.743168]
1.2919278633069198
[155.859776, 117.250624]
1.329287390402289
[172.046592, 121.787584]
1.4126776010270472
[173.675328, 123.204864]
1.4096466840789663
[173.712, 124.154688]
1.3991577990192363
[171.92128, 124.595264]
1.3798380009050746
[167.830656, 125.124736]
1.341306774065841
[168.128, 124.972992]
1.3453146740697381
[167.583488, 125.130752]
1.3392670092800207
[166.749184, 125.538496]
1.3282713216510098
[165.777216, 125.886784]
1.3168754553297668
[165.297344, 126.306496]
1.3087002587737055
[165.322112, 126.268672]
1.309288435376908
[166.276992, 125.895872]
1.3207501513631839
[168.395392, 124.745664]
1.3499097812329572
[171.252096, 123.66272]
1.3848320334535744
[173.92672, 123.4336]
1.4090711119176624
[175.886976, 122.49568]
1.4358626851167324
[177.829376, 121.290368]
1.4661459020389813
[178.002304, 120.214656]
1.4807038502859418
[178.387648, 119.66848]
1.4906819907798612
[178.26048, 119.100032]
1.4967290688889152
[177.101184, 118.242944]
1.4977738037374984
[176.902016, 118.3648]
1.494549190299819
[176.06592, 118.632832]
1.4841247320134785
[176.418624, 118.66496]
1.4866951794362886
[177.054016, 118.667456]
1.4920183002827665
[177.772288, 118.655552]
1.4982214064454398
[178.22976, 118.624256]
1.5024731535513276
[177.81632, 118.471808]
1.5009167413060835
[176.332032, 118.43136]
1.4888964544526044
[175.543424, 118.603968]
1.4800805315383714
[175.208896, 118.452608]
1.4791476435875521
[174.45664, 118.365312]
1.473883159282341
[174.766272, 118.205696]
1.4784928130705308
[175.05536, 117.958016]
1.4840480192545795
[175.256128, 117.1152]
1.496442203915461
[175.75744, 116.667712]
1.5064788448066935
[175.431808, 116.53152]
1.505445119054484
[174.80288, 117.030464]
1.493652797958658
[172.90464, 117.312704]
1.4738782254989196
[168.057472, 119.79616]
1.402861928128581
[166.576128, 121.535744]
1.3705937242627158
[166.202112, 122.798656]
1.3534522071642219
[165.946304, 123.287104]
1.3460151030881542
[165.557952, 124.094656]
1.334126362379376
[165.164416, 123.98528]
1.332129233405772
[164.65792, 123.707136]
1.3310300870598117
[162.948096, 122.361152]
1.3316979559002515
[158.18304, 117.067456]
1.3512127571987214
[151.63072, 111.514816]
1.3597360910320653
[147.94208, 109.315072]
1.3533548237520256
[139.19424, 105.68544]
1.317061650119449
[135.908288, 104.863232]
1.2960528243111942
[131.187392, 96.124608]
1.3647638698302935
[128.588928, 90.907776]
1.414498667308724
[126.935744, 91.035712]
1.3943510871865317
[126.453504, 91.947968]
1.3752724149379787
[126.73664, 92.526016]
1.3697405927431263
[129.865984, 95.194368]
1.3642191941439226
[131.263296, 96.027584]
1.366933234517282
[131.63904, 96.291072]
1.3670949680568516
[131.861824, 96.288064]
1.3694513995005653
[132.08512, 96.619904]
1.3670591103050567
[132.2912, 97.001536]
1.3638052081979404
[132.467264, 97.740096]
1.3553011447829968
[132.685248, 98.062784]
1.353064257282355
[133.036544, 98.526016]
1.3502681768843672
[133.456832, 99.012416]
1.347879764897364
[133.819584, 99.544512]
1.344319051963407
[133.827328, 99.452416]
1.3456417991896747
[133.95488, 99.212544]
1.350180880353194
[134.128832, 99.187712]
1.3522726686144346
[134.297088, 99.138112]
1.3546464148923876
[134.021824, 98.85696]
1.3557146001657345
[133.913024, 98.918016]
1.3537779002765282
[136.23552, 100.86912]
1.3506167199634538
[139.537152, 103.199168]
1.3521150868193046
[146.79328, 106.715264]
1.3755602947297212
[157.461952, 112.421248]
1.400642270044894
[163.3872, 113.378944]
1.4410718095945576
[171.88608, 125.03456]
1.3747085605771716
[164.099776, 140.805504]
1.165435805691232
[166.427136, 132.9648]
1.2516631168549872
[167.513664, 115.630464]
1.448698363780673
[168.410624, 100.368128]
1.6779293123809185
[168.406656, 99.831808]
1.686903797234645
[166.344448, 99.546048]
1.6710301548083557
[165.063936, 99.333696]
1.6617114095905583
[164.364736, 98.927168]
1.6614721650578332
[163.394112, 98.515904]
1.658555678482126
[162.631808, 98.515072]
1.6508317427814498
[161.894976, 98.338112]
1.6463095813757338
[161.517312, 98.2352]
1.6441897812596706
[162.225792, 97.996928]
1.6554171167488028
[162.430976, 97.67648]
1.6629487057682668
[162.62176, 97.764416]
1.6634044026816464
[162.19968, 97.775616]
1.6588970403418375
[161.877184, 97.896384]
1.653556315215892
[161.821312, 98.041728]
1.6505350864480888
[161.915904, 97.839808]
1.6549082353064308
[161.868992, 97.905216]
1.653323475635864
[161.833536, 97.912128]
1.6528446404514874
[161.162944, 97.78944]
1.648060813110291
[160.893312, 97.92928]
1.6429540991213252
[160.68, 97.758336]
1.6436449982127357
[160.452736, 97.74336]
1.6415717241559937
[161.470144, 97.861632]
1.649984173572744
[161.970752, 97.944832]
1.6536937038189008
[162.099648, 97.763328]
1.6580823435143288
[162.6592, 97.843008]
1.662450933642596
[161.954176, 97.7168]
1.657383131662109
[161.87744, 97.96832]
1.652344757978906
[161.832384, 97.876928]
1.653427291874138
[161.912, 97.958592]
1.6528616499510325
[161.710848, 97.870592]
1.652292529302367
[161.705408, 98.055616]
1.6491192916477115
[161.637824, 97.84928]
1.6519061152008476
[161.46304, 97.847488]
1.650150078456792
[162.56416, 97.888128]
1.6607137486580599
[163.184768, 97.96096]
1.665814299900695
[163.093504, 97.72736]
1.6688622715276458
[163.321408, 97.69568]
1.6717362323492706
[162.98752, 97.730176]
1.6677297296589335
[162.810688, 97.802496]
1.6646884758442155
[162.760064, 97.768192]
1.6647547701403744
[162.68992, 97.73568]
1.6645908638482896
[162.913216, 97.860672]
1.6647465490529232
[163.031424, 97.754304]
1.6677672217890271
[162.9568, 97.69056]
1.6680915740476867
[162.651648, 97.896]
1.6614738906594753
[162.390208, 97.96224]
1.657681653665739
[162.218432, 98.080768]
1.6539270165584348
[162.160192, 97.801152]
1.6580601422772607
[162.27552, 97.649088]
1.661823201052323
[162.272, 97.611136]
1.6624332699088757
[162.364608, 97.702464]
1.661827157194316
[162.364736, 97.729088]
1.6613757410690253
[162.39136, 97.85824]
1.659455146546678
[162.564544, 97.702976]
1.6638648141076071
[162.713984, 97.738176]
1.6647945629760885
[162.741312, 97.80416]
1.663950817633933
[162.31104, 97.730496]
1.6608023763636683
[162.10656, 97.49888]
1.6626504837799163
[161.912448, 97.533824]
1.6600645946169406
[161.392064, 97.567872]
1.654151727322699
[160.827456, 97.516032]
1.6492411832343632
[160.849344, 97.736896]
1.6457382071965945
[161.195776, 97.56256]
1.652229871786882
[161.64256, 97.592768]
1.6562964993471647
[161.768, 97.725248]
1.6553347605728257
[161.88864, 97.815424]
1.6550420514457926
[161.97536, 97.763008]
1.6568164514741608
[162.054912, 97.713216]
1.6584748576896702
[161.910272, 97.72832]
1.6567385175556073
[161.868864, 97.63264]
1.65793800106194
[162.001408, 97.765504]
1.657040585603691
[161.241088, 97.690944]
1.6505223657169286
[160.82112, 97.653824]
1.6468491802225789
[160.67264, 97.69984]
1.6445537679488524
[162.067648, 97.698944]
1.6588474896924168
[162.387264, 97.720768]
1.6617477259286375
[162.562112, 97.672128]
1.6643654165085868
[161.884224, 97.715136]
1.656695478579695
[161.298368, 97.7232]
1.6505637146552712
[161.198656, 97.847808]
1.6474426897738987
[161.469248, 97.73696]
1.6520797045457523
[161.716608, 97.836416]
1.6529285782504544
[161.687744, 97.726336]
1.654495099458144
[161.940608, 97.690944]
1.6576829066161956
[161.399424, 97.73024]
1.6514788462608914
[161.101248, 97.70464]
1.648859747090824
[161.142848, 97.72832]
1.6488858910088702
[161.15936, 97.701696]
1.6495042215029716
[161.009664, 97.646656]
1.6489009516106727
[160.954752, 97.734848]
1.6468512029608928
[161.03872, 97.585792]
1.6502271150292045
[161.335616, 97.594944]
1.6531144892096048
[161.651648, 97.724288]
1.6541604068785847
[161.69568, 97.557376]
1.6574418729753453
[161.81728, 97.61408]
1.6577247872438075
[161.505216, 97.595392]
1.654844687749192
[161.437376, 97.755008]
1.6514486500783674
[161.54944, 97.621824]
1.6548496369008634
[161.31072, 97.588352]
1.6529710431015374
[160.820736, 97.632064]
1.6472122928795196
[160.401152, 97.739392]
1.6411105974549136
[160.176, 97.641984]
1.6404418820494266
[160.098432, 97.599616]
1.6403592407576686
[160.457536, 97.722944]
1.641963795114482
[160.844416, 97.855104]
1.6436998115090655
[160.886848, 97.741632]
1.646042169625324
[160.856512, 97.7152]
1.6461769714435421
[161.443136, 97.65088]
1.653268623897706
[161.527552, 97.500928]
1.6566770728582192
[161.86432, 97.69568]
1.6568216731794077
[161.441344, 97.730624]
1.6519012914518991
[161.232128, 97.74624]
1.6494969832087658
[161.239488, 97.676864]
1.6507439059468576
[161.248192, 97.653376]
1.6512300813849998
[161.015424, 97.611968]
1.6495459245325326
[160.999232, 97.640768]
1.6488935441392678
[161.609088, 97.638784]
1.655173091873
[161.872896, 97.775936]
1.655549439076707
[161.862336, 97.615744]
1.6581580938419114
[162.102656, 97.635008]
1.660292341042262
[161.727616, 97.675584]
1.6557629796203728
[161.82176, 97.847616]
1.6538140285400516
[161.730688, 97.705152]
1.6552933462505641
[161.732032, 97.75968]
1.654383811403638
[160.953408, 97.805056]
1.6456552920945111
[160.580544, 97.948992]
1.6394302863269894
[160.488768, 97.85376]
1.640087902600779
[160.369088, 97.8736]
1.6385326380147456
[161.191104, 97.72736]
1.6493958703069436
[161.621888, 97.611072]
1.6557741318525836
[161.761344, 97.727232]
1.6552330470180512
[161.935744, 97.497152]
1.6609279417720837
[161.920192, 97.43616]
1.6618080187068125
[162.051584, 97.712576]
1.6584516613296532
[161.800256, 97.73216]
1.6555477337244977
[161.717056, 97.565888]
1.657516364736003
[161.703872, 97.506496]
1.6583907599345995
[161.031616, 97.8208]
1.6461899309758252
[160.853568, 97.684544]
1.646663447597196
[160.913792, 97.709184]
1.646864556764695
[161.35296, 97.668416]
1.6520484984623893
[161.56832, 97.85184]
1.651152599685402
[161.407168, 97.694592]
1.6521607255394446
[161.635264, 97.690752]
1.6545605463247943
[161.037888, 97.720384]
1.6479457141715694
[160.962304, 97.898112]
1.6441819020983774
[160.803648, 97.789952]
1.6443780236235315
[160.876416, 97.796416]
1.645013412352453
[161.673984, 97.711616]
1.6546035222669941
[162.449024, 97.679168]
1.6630877118036058
[162.753856, 97.828864]
1.6636588563473458
[161.704128, 97.740352]
1.6544254720916085
[161.987648, 98.099264]
1.6512626231324223
[165.034368, 98.060608]
1.6829833239459417
[163.87584, 97.497216]
1.6808258401962988
[163.281856, 97.900288]
1.6678383622323971
[161.531712, 98.000192]
1.648279546227828
[157.612672, 99.001728]
1.5920194039441413
[150.91296, 101.064256]
1.4932377278867022
[135.228672, 104.380992]
1.2955296688500526
[121.649152, 114.144832]
1.065743843751069
[99.366272, 153.293312]
0.6482100928186613
[109.007808, 182.27424]
0.598042861130569
[114.924032, 180.911168]
0.6352511747644015
[130.914752, 177.040192]
0.7394634547165425
[177.008256, 170.271168]
1.0395668161505769
[184.158464, 169.806976]
1.0845164806421146
[180.968512, 169.406464]
1.0682503354771633
[177.874688, 168.765696]
1.0539741915323835
[174.71488, 169.365568]
1.0315844127184104
[176.652224, 168.980544]
1.0453997828294361
[181.007232, 168.006976]
1.0773792631086936
[180.545472, 167.702656]
1.076580874187228
[180.238528, 167.80288]
1.0741086684567036
[180.286784, 167.903168]
1.073754510695117
[178.6832, 166.26752]
1.0746729126650834
[178.381568, 165.670528]
1.0767248113074162
[177.794112, 164.996736]
1.0775613888507467
[176.541632, 163.593984]
1.0791450130586708
[175.434048, 162.761408]
1.0778602259326733
[175.268352, 162.745664]
1.0769463695204806
[174.472896, 161.651776]
1.0793132022255048
[174.261312, 161.452544]
1.0793345690483516
[174.186368, 161.263616]
1.080134331106652
[174.155776, 160.90784]
1.0823324457030807
[173.837888, 160.579776]
1.0825640210134555
[174.292416, 160.790592]
1.0839714801224192
[174.009536, 160.61248]
1.0834122977243112
[174.09344, 160.545408]
1.0843875397544849
[173.977344, 160.487104]
1.0840580935400268
[173.847936, 160.590912]
1.0825515207236633
[173.901696, 160.801024]
1.081471321973671
[173.950144, 160.773888]
1.0819551990930267
[174.108672, 160.915776]
1.081986342967392
[174.102208, 160.792192]
1.0827777508002379
[174.130368, 160.868032]
1.0824423338503948
[174.16032, 160.85248]
1.0827331975235943
[174.233856, 160.961024]
1.0824599127798789
[174.126464, 160.82016]
1.082740273358763
[174.317376, 160.994624]
1.0827527756454776
[174.166976, 161.079296]
1.0812499205360322
[174.047488, 160.933312]
1.0814882626662154
[174.070016, 160.971648]
1.0813706523026962
[173.930176, 161.040896]
1.0800373092807432
[173.908608, 161.076992]
1.079661383296753
[173.852032, 161.177856]
1.0786347226259172
[173.89248, 160.94528]
1.0804447325202704
[173.996864, 160.891904]
1.0814519542263605
[174.151872, 161.065792]
1.0812467988236758
[174.36384, 160.885568]
1.083775519256022
[174.373952, 160.796608]
1.084438000085176
[174.429696, 160.867776]
1.0843047646782908
[174.315328, 160.865344]
1.0836102025803644
[174.34624, 160.881856]
1.0836911279790307
[174.417152, 161.034816]
1.083102128672597
[174.07392, 160.984064]
1.0813115017397001
[173.454784, 160.543168]
1.0804245746539647
[172.936768, 160.425088]
1.077990794058346
[172.750848, 160.519616]
1.0761977402188652
[173.131008, 161.09664]
1.0747027870972357
[173.139456, 161.421504]
1.0725922613135856
[172.593984, 161.050816]
1.0716740733558283
[172.624896, 160.93344]
1.0726477728929427
[172.488384, 160.781248]
1.0728140634907872
[172.061504, 160.155968]
1.0743371361596716
[171.87584, 159.046976]
1.0806608482766753
[171.927552, 160.136768]
1.073629461536279
[172.169344, 160.151808]
1.0750384035626999
[173.712768, 160.60576]
1.081609825201786
[173.804608, 160.498752]
1.082903174225305
[172.125376, 159.544192]
1.0788570479582233
[170.9344, 159.144256]
1.0740846342578647
[170.804032, 158.998912]
1.0742465457876844
[170.681152, 159.16128]
1.0723786086666305
[170.654144, 158.970496]
1.073495700736821
[170.499776, 158.919488]
1.0728688982436188
[170.395648, 158.818688]
1.0728941924013375
[170.309312, 158.849344]
1.0721436281159586
[170.520512, 158.871552]
1.0733231333952096
[170.7984, 158.877568]
1.0750315614096007
[171.102656, 159.032832]
1.0758951711304492
[171.255424, 159.13504]
1.0761641433589988
[171.418816, 159.170944]
1.0769479133075945
[171.391936, 159.127104]
1.077075694157043
[171.5472, 159.150464]
1.077893181637221
[171.535744, 159.011008]
1.0787664713124767
[171.779072, 159.197632]
1.0790303212550298
[171.882624, 158.991168]
1.0810828435451207
[172.106944, 159.156928]
1.0813663354949903
[172.177472, 159.096256]
1.0822220228740014
[172.17312, 159.156928]
1.0817821263803233
[172.437504, 159.233152]
1.0829246412204414
[172.389824, 159.290432]
1.0822358997682924
[172.516864, 159.33664]
1.082719354443523
[172.392512, 159.411648]
1.0814298337847934
[172.297664, 159.614336]
1.0794623360147297
[172.101248, 159.408832]
1.079621786577045
[172.04608, 159.13248]
1.0811499952743777
[172.177472, 159.27904]
1.0809800963139908
[172.233664, 159.224128]
1.0817058078031994
[172.26784, 159.296192]
1.0814309986769803
[172.29696, 159.191872]
1.0823225949626374
[172.62624, 159.582784]
1.0817347314858223
[172.683456, 159.432128]
1.0831157945781167
[173.107392, 159.634624]
1.0843975301999647
[173.146624, 159.583424]
1.0849912833052133
[173.21344, 159.609408]
1.0852332714622936
[173.1328, 159.557504]
1.0850808997363108
[173.476416, 159.455168]
1.0879322268187634
[173.6768, 159.554432]
1.088511286229893
[173.914944, 159.706112]
1.0889686175567281
[174.160768, 159.636032]
1.0909865762636846
[174.601856, 159.788224]
1.0927079081872766
[175.100928, 159.970304]
1.0945839547820075
[175.450432, 160.033216]
1.0963376003141747
[175.483968, 160.021248]
1.0966291676465365
[175.573312, 159.883136]
1.0981352780070561
[175.81824, 160.04352]
1.098565190268247
[175.770688, 159.914368]
1.0991550677922826
[175.694976, 159.914944]
1.0986776570424839
[175.568384, 159.9312]
1.0977744430104945
[175.658688, 159.969984]
1.0980727984569905
[175.686848, 159.870208]
1.0989342554680357
[175.627264, 159.888192]
1.0984379884663402
[175.523392, 159.78144]
1.0985217807525078
[175.567104, 159.742912]
1.099060370202842
[175.936064, 160.04992]
1.0992574316813155
[175.628416, 159.67744]
1.0998949882964055
[175.963968, 159.929408]
1.1002602348156005
[175.949184, 159.923392]
1.1002091801554583
[176.103936, 159.98752]
1.1007354573656747
[176.265152, 159.997632]
1.1016735047678705
[176.382528, 160.154368]
1.1013282385154803
[176.290752, 160.01312]
1.1017268583976114
[176.041536, 160.098944]
1.099579619963015
[175.894784, 160.409536]
1.0965357072038409
[175.554688, 160.491264]
1.093858217728287
[175.809344, 160.965888]
1.09221491698912
[175.813376, 160.68576]
1.0941440983942823
[176.004352, 160.82752]
1.094367133187156
[176.072704, 160.799296]
1.094984296448661
[175.939584, 160.403072]
1.0968591923227005
[175.964736, 160.5984]
1.09568175025405
[176.020672, 160.646592]
1.0957012521000133
[175.994432, 160.792]
1.0945471914025573
[175.966208, 160.795136]
1.0943503166662951
[175.9184, 160.890624]
1.0934036777680718
[175.809664, 160.67104]
1.0942212361356471
[175.869952, 160.833344]
1.093491857011939
[175.999296, 160.856576]
1.094138022681771
[176.094912, 160.805632]
1.0950792569255285
[176.201984, 160.797952]
1.0957974390121585
[176.346432, 160.756928]
1.0969756277004747
[176.263616, 160.406464]
1.0988560660498072
[176.522624, 160.235456]
1.101645218895873
[176.690688, 160.400704]
1.1015580579995459
[176.775616, 160.423104]
1.1019336466647598
[176.788352, 160.42304]
1.102013476368482
[176.944768, 160.477632]
1.102613278840007
[176.742272, 160.476032]
1.1013624265086515
[176.538048, 160.336]
1.1010505937531183
[176.553216, 160.306496]
1.1013478580431324
[176.490432, 160.262528]
1.1012582554544503
[176.61952, 160.494848]
1.1004684711125432
[176.28736, 160.032256]
1.1015739226971843
[176.522752, 160.062848]
1.102834006802128
[176.760448, 160.04032]
1.1044744724329467
[176.800832, 160.242944]
1.103329903873958
[176.648704, 159.998016]
1.1040680904443214
[176.701056, 160.051072]
1.104029193881313
[176.409216, 159.922752]
1.1030901719350101
[176.423424, 159.73312]
1.104488687130133
[176.399552, 159.785856]
1.1039747598185412
[176.643072, 159.800256]
1.1053991803367325
[176.666816, 159.805952]
1.1055083605396627
[177.152, 160.013376]
1.1071074458175296
[177.161536, 159.950592]
1.1076016273825358
[177.315392, 159.866816]
1.109144451841713
[177.576768, 160.093952]
1.1092034757190576
[177.257344, 160.072256]
1.10735831698405
[177.241088, 160.109952]
1.1069960722991161
[177.128384, 160.144064]
1.1060565067213484
[177.36768, 160.0464]
1.1082266142818582
[177.376448, 160.11424]
1.1078118223588358
[177.500992, 160.11264]
1.108600745075467
[177.426624, 160.069888]
1.1084322367989663
[177.563072, 160.153088]
1.1087083878145392
[177.45728, 160.057216]
1.1087115247587462
[177.585408, 160.145792]
1.1088983718036125
[177.669056, 160.139584]
1.1094637038647484
[177.655616, 160.168832]
1.109177196222546
[177.661568, 160.096064]
1.1097185249975914
[177.598016, 160.106112]
1.1092519441106659
[177.457344, 160.089856]
1.1084858743329746
[177.416128, 160.047424]
1.1085222340098393
[177.357568, 160.163392]
1.1073539701257076
[177.344128, 160.180416]
1.1071523749819703
[177.420992, 160.172416]
1.1076875558897732
[177.281024, 159.949312]
1.1083575276647644
[177.076544, 159.862528]
1.107680118758037
[177.097472, 159.807872]
1.1081899144492706
[177.1328, 159.985792]
1.1071783174345882
[176.921344, 159.760448]
1.1074164238698179
[176.560064, 159.520512]
1.1068173101149525
[176.27392, 159.627136]
1.104285426758518
[176.05152, 159.634624]
1.1028404464434984
[175.5488, 159.252096]
1.1023327441793922
[175.068416, 158.835776]
1.102197630841052
[175.317568, 158.885568]
1.1034203433756802
[175.32352, 158.989248]
1.1027382178699279
[175.36512, 158.894464]
1.1036578341709877
[175.500288, 158.946624]
1.1041460559741112
[175.647488, 159.074112]
1.1041865064756733
[175.67104, 159.057088]
1.1044527610111912
[175.750144, 158.943424]
1.1057402664233533
[175.863104, 159.0128]
1.1059682239417203
[175.626432, 158.859264]
1.105547310102104
[175.755136, 159.045056]
1.1050650703659723
[175.770496, 159.077184]
1.1049384429636373
[175.70624, 158.966912]
1.1053007055958914
[175.7024, 159.04832]
1.104710819957105
[175.677056, 158.91584]
1.1054722801704349
[175.6624, 159.0192]
1.1046615754575546
[175.592512, 158.928064]
1.1048552884907727
[175.758464, 159.174016]
1.1041906739351228
[175.70048, 158.996352]
1.1050598192340917
[175.707008, 158.986432]
1.1051698298380581
[175.838272, 158.975424]
1.1060720429341329
[175.829312, 159.015744]
1.1057352409079693
[175.668224, 158.749696]
1.1065736088086746
[175.569472, 158.614208]
1.106896249798757
[175.655872, 158.877888]
1.1056030150652554
[175.572544, 158.861632]
1.1051916173189005
[175.560448, 158.820032]
1.1054049403541237
[175.771904, 158.890304]
1.106246885901861
[175.719744, 158.771328]
1.1067473341282374
[175.972352, 158.840448]
1.107856054397429
[175.818688, 158.707776]
1.1078139485742653
[175.975232, 158.694464]
1.1088933259826883
[175.996224, 158.709824]
1.1089182733893022
[176.105152, 158.778176]
1.1091269369412582
[176.014336, 158.59648]
1.1098249847663704
[176.040576, 158.621696]
1.1098139815627743
[175.971712, 158.8528]
1.1077658813694187
[175.77152, 158.627392]
1.1080779793694144
[175.759936, 158.70656]
1.1074522439400112
[175.932352, 158.632576]
1.1090556330624046
[176.126144, 158.784576]
1.1092144365457766
[176.214336, 158.773888]
1.1098445608386185
[176.29792, 158.75136]
1.1105285649206407
[176.38432, 158.908928]
1.1099711150275962
[176.317888, 158.77568]
1.110484225291934
[176.509632, 158.843648]
1.1112161815875696
[176.16416, 158.709632]
1.1099777485464777
[175.980672, 158.731648]
1.1086678316349363
[175.971584, 158.878848]
1.1075834588125917
[175.833344, 158.590912]
1.1087226990661356
[176.123968, 158.694784]
1.1098283356307412
[176.540224, 158.927616]
1.1108215704940796
[176.69728, 158.934592]
1.1117609941075635
[176.776192, 159.02496]
1.1116254454646617
[176.693312, 158.959872]
1.11155922420471
[176.85344, 159.048704]
1.1119451812697576
[176.741888, 158.961152]
1.1118558577129587
[177.002432, 159.0144]
1.1131220317153667
[176.99456, 159.01056]
1.1130994067312259
[176.79104, 158.951104]
1.1122353701928362
[176.929856, 159.111552]
1.1119862371778009
[176.730176, 158.983872]
1.111623297236087
[176.923328, 159.02304]
1.1125641164953204
[176.646208, 158.872064]
1.1118770887246736
[176.832832, 159.036544]
1.1119006207780773
[176.844928, 159.04416]
1.1119234305742507
[176.82272, 158.9936]
1.1121373438930877
[176.742848, 158.984256]
1.1117003183007004
[176.528064, 158.818368]
1.111509117131842
[176.581888, 158.826368]
1.1117920168016433
[176.652736, 158.93344]
1.1114887842357153
[176.781376, 159.015808]
1.1117220245172104
[176.602432, 158.839936]
1.1118263860292665
[176.770752, 158.975104]
1.1119398418509605
[176.762816, 159.045632]
1.1113968599904709
[176.96352, 159.154496]
1.1118977122707234
[177.034112, 159.171776]
1.1122204981868142
[176.93152, 159.052864]
1.1124070045038612
[176.851904, 158.997376]
1.1122944821429002
[176.975808, 159.167808]
1.1118819202435708
[176.689344, 159.029312]
1.1110489115365096
[176.83808, 159.176384]
1.110956761023042
[176.638272, 159.054976]
1.110548543919808
[176.59008, 159.0256]
1.1104506444245454
[176.657216, 158.948352]
1.1114126933508566
[176.784832, 158.900928]
1.112547511365069
[176.713792, 158.957632]
1.1117037274435493
[176.92128, 159.044672]
1.112399917426973
[176.891456, 159.169792]
1.1113381111913496
[176.98784, 159.148672]
1.1120912149364337
[176.90176, 158.987648]
1.1126761243741399
[176.891968, 159.013696]
1.1124322775316158
[177.01088, 158.9104]
1.1139036840886436
[176.893824, 158.866816]
1.1134724573318067
[176.744704, 158.928128]
1.1121046112114277
[176.664896, 158.853184]
1.1121268806296007
[176.653632, 158.85664]
1.1120317790934013
[176.78144, 159.163008]
1.110694263832963
[176.685632, 159.060544]
1.1108074168286513
[176.630912, 159.037632]
1.1106233774909324
[176.828032, 159.059648]
1.1117089357572323
[176.938304, 159.147776]
1.1117862181121525
[176.909056, 159.055104]
1.1122501042154547
[176.889088, 159.009792]
1.1124414778179195
[176.757184, 158.991744]
1.1117381289936663
[176.662784, 158.851008]
1.1121288194784384
[176.552896, 158.90912]
1.1110306066763191
[176.545152, 158.76288]
1.1120052243950223
[176.160448, 158.502208]
1.1114069022937523
[175.784192, 158.539904]
1.1087693859080423
[175.232896, 158.33408]
1.1067288608996877
[174.47552, 158.105408]
1.1035392287150607
[174.022464, 157.875648]
1.1022755327028015
[173.667968, 157.535808]
1.1024031311027396
[173.372736, 157.44608]
1.1011562561608395
[173.004736, 157.3776]
1.0992970791268897
[172.483584, 157.220672]
1.0970795494373666
[172.234176, 157.058304]
1.0966257218720508
[172.048384, 157.1136]
1.095057232473828
[171.861952, 156.830848]
1.0958427770536572
[172.028096, 156.919936]
1.0962794172946897
[171.829056, 156.854656]
1.095466723027973
[171.642496, 156.646528]
1.0957312504238843
[171.586816, 156.6032]
1.0956788622454714
[171.268096, 156.448192]
1.0947272308522429
[170.92224, 156.431744]
1.0926314290787424
[170.256896, 156.352256]
1.0889314958141698
[169.962496, 156.172224]
1.0883016944165436
[169.75648, 156.19776]
1.0868048299796362
[169.438656, 156.063552]
1.0857029320978162
[169.411648, 156.1408]
1.0849928269869247
[169.320896, 156.170048]
1.0842085160913826
[169.170368, 156.1488]
1.0833920465607165
[169.230464, 156.21568]
1.0833129171156188
[169.035136, 156.165952]
1.0824071049750972
[169.026368, 156.150336]
1.0824592013686092
[169.022208, 156.245248]
1.081775031007663
[168.9168, 156.37184]
1.0802251863251082
[168.78848, 156.357056]
1.0795066389584618
[169.1216, 156.511168]
1.0805720905488354
[168.782656, 156.445248]
1.0788608676691798
[168.653888, 156.515328]
1.077555087767506
[168.6032, 156.594944]
1.0766835486080573
[168.827904, 156.627392]
1.07789513599256
[169.111104, 156.5936]
1.0799362426050618
[169.264384, 156.675328]
1.0803512343692045
[169.204608, 156.532416]
1.0809557044082165
[169.190656, 156.451072]
1.0814285503905015
[169.615872, 156.661696]
1.0826888533110224
[169.651584, 156.66496]
1.0828942476990389
[170.050432, 156.863296]
1.084067696754249
[170.158464, 157.00416]
1.0837831558093747
[169.94752, 156.950144]
1.0828121317301882
[169.54464, 157.024384]
1.079734469775089
[169.531136, 156.934848]
1.080264441967663
[169.52576, 156.774656]
1.0813339625506817
[169.578752, 156.92928]
1.0806061940767204
[169.75584, 157.070912]
1.0807592433155289
[169.615168, 156.982848]
1.080469428099559
[169.654016, 157.017536]
1.080478144810526
[169.524864, 156.895232]
1.0804972327011189
[169.704064, 157.021568]
1.0807691335753313
[170.079616, 157.0704]
1.082824109443918
[170.026368, 157.017728]
1.0828482246284954
[170.00192, 156.946624]
1.0831830317038231
[170.035584, 157.094848]
1.0823753048858737
[169.9008, 157.014528]
1.0820705712021756
[169.884992, 156.921472]
1.0826115115718518
[170.074368, 156.944768]
1.0836574558509653
[170.238336, 156.988992]
1.0843966435557468
[170.18784, 157.059968]
1.0835850927971664
[169.97952, 157.013184]
1.08258119267233
[169.896064, 156.820544]
1.08337887158458
[169.82592, 156.95136]
1.082028980188512
[169.833408, 156.801024]
1.083114151091258
[169.966528, 156.83648]
1.0837180737542695
[170.027904, 156.897088]
1.0836906291084256
[169.993792, 156.682048]
1.0849602374357528
[169.907392, 156.726464]
1.084101482695354
[169.775424, 156.59584]
1.0841630531181414
[169.589504, 156.47296]
1.0838262662123859
[169.418944, 156.458048]
1.0828394330983857
[169.224128, 156.553024]
1.0809380980082506
[169.243712, 156.64512]
1.0804276060435205
[169.236608, 156.556032]
1.0809970451984885
[169.295808, 156.762432]
1.0799514006008788
[169.006656, 156.6176]
1.0791038555053838
[169.018304, 156.640384]
1.079021256740535
[168.91104, 156.471808]
1.0794982314002532
[169.150016, 156.712256]
1.0793668620276897
[169.273728, 156.704704]
1.0802083388639054
[169.291136, 156.803072]
1.0796417049788414
[169.179328, 156.709632]
1.079571981893238
[168.929088, 156.669248]
1.078253008529153
[169.044352, 156.802816]
1.0780696183415481
[169.195968, 156.696768]
1.0797668015718103
[169.35168, 156.711232]
1.0806607659111505
[169.340928, 156.74016]
1.0803927213038444
[169.403008, 156.780544]
1.0805103980248978
[169.403584, 156.789568]
1.0804518831252854
[169.511808, 156.940416]
1.080102960858725
[169.586368, 156.821824]
1.0813952017290656
[169.641536, 156.81792]
1.081773919715298
[169.733952, 156.836224]
1.0822369199605315
[169.777088, 156.931712]
1.081853284057718
[169.917504, 156.92896]
1.0827670303811356
[169.98624, 157.058496]
1.0823116503038461
[170.494784, 157.182528]
1.0846929755449666
[170.695232, 157.264832]
1.0853998941098286
[171.180928, 157.416896]
1.087436814914709
[171.388928, 157.766784]
1.0863435487155522
[171.583808, 157.80192]
1.0873366306316172
[171.765888, 158.042752]
1.0868317959940357
[171.719936, 157.96896]
1.0870485948631932
[171.822784, 157.99552]
1.0875168106032373
[172.020032, 158.019456]
1.0886003303289438
[172.262784, 158.165312]
1.089131250220023
[172.157824, 158.134784]
1.0886777699712165
[172.233216, 158.101312]
1.0893851152860767
[172.423168, 158.309504]
1.0891523480485417
[172.551552, 158.264192]
1.0902753795375266
[172.825792, 158.376128]
1.0912363762296298
[172.885504, 158.443968]
1.091146013207647
[172.78528, 158.596736]
1.08946302652786
[172.81536, 158.567744]
1.0898519184330453
[172.791168, 158.4944]
1.0902036160268123
[172.808576, 158.498816]
1.0902830718937357
[172.643392, 158.463488]
1.089483730157448
[172.752896, 158.504]
1.0898961288043205
[172.702912, 158.331328]
1.090769048561255
[172.84288, 158.253632]
1.0921890247675325
[172.864192, 158.304128]
1.0919752642205263
[172.71296, 158.346624]
1.0907271379527486
[172.649408, 158.453248]
1.0895921047954789
[172.511552, 158.239808]
1.0901906048824326
[172.472704, 158.25888]
1.089813753263008
[172.685696, 158.239424]
1.091293760017731
[172.686656, 158.186816]
1.0916627590506658
[172.658688, 158.218176]
1.0912696149398158
[172.402368, 158.012736]
1.0910662796193846
[172.361984, 157.978368]
1.0910480098135968
[172.286848, 157.997568]
1.0904398730998188
[172.511232, 158.030784]
1.0916305521840606
[172.54272, 158.073856]
1.0915323024700554
[172.538624, 157.971136]
1.0922161375100827
[172.601664, 157.901568]
1.0930965802695511
[172.58272, 157.896704]
1.0930102758826428
[172.649024, 157.996416]
1.0927401289912804
[172.282496, 157.910336]
1.0910146882342142
[172.239616, 157.968512]
1.0903414472879254
[172.131328, 157.929216]
1.0899270721384446
[172.097408, 157.843712]
1.0903025899441594
[172.12032, 157.914624]
1.08995807760021
[172.026432, 157.81696]
1.090037674024389
[172.174848, 157.81056]
1.0910223498351441
[172.274496, 157.81504]
1.0916228009700468
[172.251136, 157.714112]
1.0921732609444614
[172.31392, 157.790784]
1.092040457825471
[172.202176, 157.678016]
1.0921127774717814
[172.28608, 157.791104]
1.0918618073677968
[172.248768, 157.789952]
1.0916333126205655
[172.190144, 157.7776]
1.0913472127855919
[172.26112, 157.842048]
1.0913512728876908
[172.23104, 157.888704]
1.0908382654151119
[172.173056, 157.724736]
1.0916046548335956
[172.20352, 157.849088]
1.090937693602639
[172.319232, 157.965824]
1.0908640086605061
[172.228032, 157.985408]
1.0901515157653041
[172.24448, 157.972992]
1.0903413160649638
[172.141888, 157.860096]
1.0904711979904027
[172.156608, 157.832896]
1.0907523866254092
[172.209728, 157.748736]
1.0916710483182572
[172.180608, 157.893184]
1.0904879085850852
[172.377024, 157.904704]
1.091652241088397
[172.696704, 158.05568]
1.0926320648520826
[172.647296, 158.003328]
1.0926813895970595
[172.64928, 157.955648]
1.093023783486362
[172.420352, 158.14144]
1.0902920322465763
[172.215616, 158.059072]
1.0895648938138776
[172.243264, 158.125056]
1.0892850782610948
[172.105536, 158.089792]
1.0886568564781212
[172.101696, 157.925632]
1.0897641745704711
[172.238336, 158.014976]
1.0900127339828853
[172.095424, 157.952256]
1.0895407787021416
[172.081152, 157.851968]
1.0901425821944772
[172.006144, 157.814784]
1.0899241480443302
[172.001408, 157.768128]
1.0902164472662057
[172.114048, 157.893504]
1.090064148554205
[171.817344, 157.71136]
1.0894417751517709
[171.875776, 157.803264]
1.0891775723979955
[171.943232, 157.865984]
1.089172142366021
[172.003072, 157.918336]
1.089189997544047
[171.841408, 157.841408]
1.0886966238922553
[171.933056, 157.885632]
1.0889721491566757
[172.331712, 157.997952]
1.0907211759301791
[172.248256, 157.96096]
1.0904482727884155
[172.230336, 157.785792]
1.0915452767762512
[172.519936, 157.93856]
1.0923230907005863
[172.510592, 157.948032]
1.0921984263786204
[172.55264, 157.889472]
1.0928698273181887
[172.475136, 157.906176]
1.0922633957015082
[172.606016, 157.964672]
1.09268745862366
[172.607936, 157.97056]
1.0926588853011598
[172.524672, 157.856832]
1.0929186264171322
[172.603904, 157.939968]
1.0928449979171833
[172.332736, 157.871744]
1.091599621525686
[172.2816, 157.975872]
1.090556411044846
[172.218496, 157.969088]
1.0902037745511324
[172.16672, 157.873664]
1.0905347708912363
[172.325056, 157.9792]
1.0908085115002482
[172.12576, 157.801472]
1.090774108875233
[172.205696, 157.78496]
1.091394870588426
[172.125184, 157.742976]
1.0911749503191825
[172.172416, 157.80864]
1.091020212834988
[172.31232, 157.95616]
1.0908869904155685
[172.290368, 157.85504]
1.091446734928451
[172.328256, 157.923776]
1.0912115981826576
[172.13152, 157.71008]
1.0914427283278278
[172.323712, 157.743296]
1.0924312878564426
[172.306624, 157.774592]
1.0921062879376673
[172.222016, 157.669888]
1.0922949092219816
[172.137664, 157.782784]
1.0909787470856136
[172.224256, 157.887296]
1.0908050258837798
[172.12128, 157.810752]
1.0906815778940082
[172.146624, 157.908544]
1.0901666220163488
[172.305344, 158.124416]
1.0896820893238903
[172.016, 157.945088]
1.089087366870187
[172.206528, 157.968704]
1.090130662843192
[172.033664, 158.004672]
1.0887884631664562
[171.96256, 157.976768]
1.088530688259175
[171.987584, 157.933632]
1.088986442102465
[172.066432, 157.971584]
1.0892239454913613
[172.226368, 157.944576]
1.0904228075549742
[172.051776, 157.902912]
1.0896048326201864
[172.16864, 157.939136]
1.0900948578064908
[172.216064, 157.904896]
1.090631565977536
[172.28864, 157.707904]
1.09245405988022
[172.434048, 157.726976]
1.0932438595665461
[172.35104, 157.61792]
1.0934736354851022
[172.498944, 157.670848]
1.0940446264359533
[172.521792, 157.79424]
1.0933339011614112
[172.732096, 157.985344]
1.0933425318237115
[172.66816, 157.977152]
1.0929945110037178
[172.616576, 157.968064]
1.0927308446345205
[172.557696, 157.967936]
1.0923589961952784
[172.29408, 157.973504]
1.0906517589177487
[172.204736, 157.934912]
1.0903525624530692
[172.055104, 157.865216]
1.0898860962506143
[172.2512, 157.936384]
1.090636594541762
[172.263488, 157.943936]
1.0906622461276385
[172.41824, 158.140096]
1.090287943166545
[172.3744, 158.00448]
1.0909462820294715
[172.4896, 157.998784]
1.091714731171602
[172.572992, 157.980736]
1.0923673124297888
[172.462912, 157.930112]
1.092020450159625
[172.499072, 157.939136]
1.092187005505716
[172.529024, 158.067648]
1.0914885252167477
[172.374848, 157.878208]
1.0918216654701325
[172.51552, 157.919744]
1.0924252764746123
[172.472256, 157.740672]
1.0933911578619369
[172.551616, 157.937664]
1.0925298730516868
[172.349632, 157.729664]
1.092690034513736
[172.470976, 157.693888]
1.0937074238413096
[172.36672, 157.907968]
1.091564423145512
[172.157504, 157.797504]
1.0910027068615735
[172.26432, 157.976704]
1.0904412843048048
[172.132416, 157.788032]
1.0909092015293025
[172.29152, 157.83232]
1.0916111478308117
[172.367552, 157.9376]
1.0913648934769173
[172.361728, 157.793536]
1.0923243902716016
[172.350976, 157.7872]
1.0923001105286105
[172.130688, 157.807104]
1.090766408082617
[172.196928, 157.989248]
1.0899281449836384
[171.977344, 157.790592]
1.089908731694219
[171.973312, 157.809024]
1.0897558811338952
[172.223936, 157.831168]
1.0911909110372928
[172.386944, 157.892096]
1.091802239423055
[172.348032, 157.81888]
1.0920621917985984
[172.231936, 157.815808]
1.0913478071854499
[171.975168, 157.76384]
1.0900797546510024
[172.017216, 157.969152]
1.0889291600425886
[171.93152, 157.791872]
1.0896094825467308
[172.059584, 158.021056]
1.0888396037550845
[172.044032, 157.893888]
1.0896180604533596
[172.017728, 157.787456]
1.090186332682872
[172.016448, 157.89472]
1.0894376202066793
[171.9376, 157.761856]
1.0898553323307758
[172.03904, 157.799104]
1.0902409179712453
[171.890432, 157.790336]
1.0893596931056666
[171.9584, 157.815232]
1.0896185230079691
[172.191872, 158.086464]
1.0892259061471574
[171.982208, 157.792512]
1.089926295108351
[172.002496, 157.92224]
1.0891594242837488
[171.999744, 157.732992]
1.0904487502525788
[172.034432, 157.789696]
1.0902767187028488
[172.078208, 157.756928]
1.0907806724025457
[171.980608, 157.72544]
1.0903796369184324
[172.038592, 157.74592]
1.0906056524314542
[171.910592, 157.817664]
1.0892987999112698
[171.90144, 157.628736]
1.0905463328716916
[171.850688, 157.638272]
1.0901584102621982
[172.047424, 157.870208]
1.0898029855005957
[171.982144, 157.925696]
1.0890067187039658
[171.95744, 157.826944]
1.0895315821359375
[171.9968, 157.952256]
1.0889163874936993
[171.992512, 157.91936]
1.0891160653133345
[171.98016, 157.877696]
1.0893252457902605
[172.093568, 157.944192]
1.0895846553192663
[172.4992, 157.989888]
1.09183696617343
[172.683072, 158.052736]
1.0925661672822924
[172.832, 158.066368]
1.0934141284248398
[172.834688, 157.990528]
1.09395601235031
[172.77984, 158.215104]
1.092056546004609
[172.75648, 158.342976]
1.0910271131950937
[172.780928, 158.33312]
1.0912494366308199
[172.8704, 158.475392]
1.0908343422807245
[172.790528, 158.373568]
1.0910313518983168
[173.229824, 158.589632]
1.0923149377129522
[173.201984, 158.471296]
1.0929549285695248
[173.221248, 158.618048]
1.0920651854195054
[173.287168, 158.703936]
1.0918895420463928
[173.182976, 158.590144]
1.0920160082583694
[172.876352, 158.31744]
1.0919602540313942
[172.231616, 157.77888]
1.091601207969026
[172.080704, 157.665536]
1.091428782508309
[172.191104, 157.669184]
1.0921037303015406
[172.0112, 157.50208]
1.0921201802541274
[171.914368, 157.619264]
1.090693888787604
[171.880896, 157.56896]
1.0908296659443586
[171.8976, 157.670272]
1.090234689263427
[172.14368, 157.776704]
1.0910589183052017
[172.13024, 157.836608]
1.0905596754841562
[172.554624, 157.96576]
1.0923545963378394
[172.765696, 158.121856]
1.092611106209125
[172.859904, 158.00736]
1.0939990643473823
[173.001216, 158.089216]
1.0943264846098042
[173.108352, 158.167872]
1.094459638427708
[173.218176, 158.146176]
1.0953042329648237
[173.428672, 158.228928]
1.0960617264625594
[173.200768, 157.830464]
1.097384900294027
[173.194944, 157.065792]
1.1026904190570026
[173.176448, 157.427392]
1.100040125164495
[173.347008, 158.001792]
1.0971205187343698
[173.301312, 157.6464]
1.099303961270286
[173.309632, 157.472896]
1.1005680113992442
[172.83424, 157.13472]
1.0999112099477442
[172.69088, 157.088768]
1.0993203536996357
[172.844096, 157.005504]
1.1008792150369455
[173.4048, 156.261504]
1.1097090170077974
[173.602944, 155.292992]
1.117905848578151
[173.738176, 153.70784]
1.1303143418058572
[173.82112, 149.623424]
1.161723982469483
[173.873472, 148.077312]
1.1742073762116914
[175.352192, 146.174976]
1.1996047257774136
[175.653056, 142.238592]
1.2349184108909064
[175.983744, 140.296256]
1.2543723476127546
[176.263808, 138.772096]
1.270167512638852
[176.467264, 137.605312]
1.28241607417016
[176.691328, 136.695424]
1.2925913891601815
[176.931264, 137.16512]
1.289914403895101
[177.002368, 138.776192]
1.2754519737794792
[176.91904, 142.93344]
1.2377722106177533
[176.483648, 145.438848]
1.2134560361754239
[175.841216, 150.1264]
1.1712877681740188
[175.62304, 156.34368]
1.1233139708621416
[175.335872, 158.548864]
1.1058790809122416
[175.151424, 159.563776]
1.0976891396703974
[175.104704, 159.992128]
1.0944582473457694
[174.785728, 160.102656]
1.0917103586339005
[174.259584, 159.775104]
1.0906554252657534
[173.734144, 159.30112]
1.0906021501920387
[172.238656, 158.798656]
1.0846354770156241
[171.607296, 158.746048]
1.0810177523285491
[170.730688, 158.325504]
1.0783524049290252
[170.976448, 158.321088]
1.0799347715447736
[170.819712, 158.015744]
1.081029697901495
[170.98208, 158.18624]
1.0808909801509916
[170.975296, 158.136704]
1.081186667454508
[171.319936, 158.040064]
1.0840285157059921
[171.474368, 157.992]
1.0853357638361436
[171.82496, 158.118656]
1.0866836611614004
[171.68128, 158.102592]
1.0858852965547838
[171.51968, 158.080448]
1.085015143681779
[171.821632, 158.172672]
1.0862915181707242
[171.933376, 158.312064]
1.0860408970474924
[172.314432, 158.4032]
1.0878216601684816
[172.808896, 158.650304]
1.089244026913431
[173.10752, 158.703808]
1.0907584523743752
[173.243136, 158.770304]
1.091155786915921
[173.320512, 158.618368]
1.0926887862066517
[173.449216, 158.732928]
1.0927109969268634
[173.445312, 158.970112]
1.0910561099686462
[173.220608, 158.767168]
1.0910354463209926
[173.312384, 158.586496]
1.092857137091925
[173.637248, 158.570304]
1.095017437817361
[173.696448, 158.371264]
1.0967674539744787
[173.683648, 157.923648]
1.0997950604585833
[173.755264, 157.974272]
1.0998959628058929
[173.886592, 158.064]
1.10010243951817
[173.87264, 158.36704]
1.0979092619272293
[173.910208, 158.502336]
1.097209116211385
[173.900544, 158.720512]
1.0956400140644706
[174.003712, 159.000256]
1.0943612065630888
[173.6976, 158.881152]
1.093254912955314
[173.623232, 158.998272]
1.0919818801552763
[173.615424, 159.11328]
1.0911435173732826
[173.710272, 158.940928]
1.092923479092811
[173.742272, 158.966656]
1.092947894683021
[173.597312, 158.764736]
1.0934248774236617
[173.554432, 158.828288]
1.0927173879756231
[173.56704, 158.775872]
1.0931575296276754
[173.553728, 158.729216]
1.0933949802914669
[173.655872, 158.866944]
1.0930900263304617
[173.519232, 158.839616]
1.0924178512242184
[173.640896, 158.831744]
1.0932379864820978
[173.465344, 158.821376]
1.0922040116312808
[173.235136, 158.894272]
1.0902541282293676
[173.3568, 158.990848]
1.0903571003030312
[173.238592, 158.874752]
1.0904098342825423
[173.32992, 158.978624]
1.0902718594419334
[173.633664, 158.74592]
1.0937834748760786
[173.564928, 158.653184]
1.0939895665756068
[173.736768, 158.661312]
1.0950165847613815
[173.446464, 158.760384]
1.0925046893310613
[173.470208, 158.614784]
1.093657246981467
[173.400576, 158.637248]
1.0930634399305768
[173.487424, 158.808704]
1.0924301982843458
[173.380096, 158.863168]
1.0913800736996508
[173.411584, 158.782208]
1.0921348568222455
[173.373248, 158.824896]
1.0915999466481627
[173.258816, 158.780608]
1.091183729438799
[173.039744, 158.758272]
1.0899573409315013
[173.178368, 158.758208]
1.0908309572252164
[173.11136, 158.613184]
1.0914058695146047
[173.307008, 158.82432]
1.0911868409069845
[173.194048, 158.725952]
1.0911514205314075
[173.368256, 158.7312]
1.0922128478837179
[173.293568, 158.6384]
1.0923809619865053
[173.357504, 158.83328]
1.0914432038424189
[173.254976, 158.844032]
1.0907238617564177
[173.108864, 158.913664]
1.089326491144273
[173.173248, 158.767168]
1.0907371478717818
[173.205696, 158.857408]
1.0903218060815898
[172.895872, 158.874176]
1.0882566088021757
[172.554944, 158.823104]
1.0864599649179505
[172.694016, 158.853824]
1.0871253310213043
[172.859968, 158.807296]
1.0884888311428713
[172.819264, 158.825088]
1.0881106138596945
[172.947776, 158.725888]
1.0896003051499703
[172.9536, 158.84064]
1.0888498056920444
[173.052288, 158.762624]
1.0900064740678512
[173.14048, 158.8224]
1.0901515151515153
[173.112384, 158.705024]
1.0907807430217205
[173.220352, 158.880192]
1.090257695559683
[173.289216, 158.87552]
1.0907232026683533
[173.25824, 158.815936]
1.0909373729346656
[173.217472, 158.87168]
1.090297981364583
[173.157632, 158.747008]
1.0907772951538086
[172.861504, 158.575232]
1.090091446311111
[172.686656, 158.237824]
1.0913108613020361
[172.19328, 158.067072]
1.0893684422774657
[172.425536, 158.142144]
1.090319959238696
[172.293568, 158.088384]
1.0898559631047908
[172.363328, 158.268416]
1.0890570105914246
[172.437952, 158.128832]
1.0904902655576436
[172.376064, 158.121792]
1.0901474225639942
[172.53696, 158.082944]
1.0914331150108136
[172.51712, 158.167552]
1.0907238420178622
[172.581952, 158.111616]
1.091519752729616
[172.640384, 158.14368]
1.0916679313393998
[172.5104, 158.176896]
1.0906169254958702
[172.472576, 158.18976]
1.0902891312307446
[172.554048, 158.298176]
1.0900570831593157
[172.533568, 158.26368]
1.090165273548549
[172.663872, 158.219264]
1.091294875445761
[172.679296, 158.298752]
1.0908443295876393
[172.79776, 158.276416]
1.0917467325011958
[172.900928, 158.357568]
1.091838743065314
[173.011136, 158.365824]
1.0924777305487325
[172.772288, 158.29024]
1.09149046713177
[172.8848, 158.201856]
1.092811452224682
[173.089088, 158.25184]
1.0937571910696269
[172.940032, 158.050688]
1.0942061321492
[173.044864, 158.175552]
1.094005121600587
[172.752064, 157.997056]
1.0933878666701233
[172.86016, 158.070336]
1.0935648292668905
[172.751744, 158.150208]
1.092327011040036
[172.709888, 158.129152]
1.092207766977717
[172.743424, 158.30368]
1.0912154663745024
[172.652288, 158.185088]
1.0914574198043243
[172.7712, 158.347712]
1.0910874417939174
[173.027072, 158.493952]
1.0916951077098513
[172.82752, 158.248]
1.092130832617158
[172.894272, 158.179904]
1.0930229923517971
[172.829952, 158.137152]
1.0929117529573316
[172.94016, 158.199936]
1.093174652106054
[172.745216, 158.05984]
1.0929102294422162
[172.965888, 158.294656]
1.0926830530526566
[173.004224, 158.411904]
1.0921163096429924
[173.284928, 158.5936]
1.0926350621967091
[173.299776, 158.50848]
1.09331548696953
[173.234752, 158.507008]
1.092915412295209
[173.317632, 158.507712]
1.093433434961196
[173.020288, 158.65824]
1.0905219167942364
[172.7312, 158.544768]
1.0894790296706605
[172.753792, 158.502976]
1.0899088229106817
[172.889344, 158.497408]
1.0908023429632363
[172.935104, 158.480768]
1.0912056155608736
[172.741632, 158.381696]
1.0906666386499613
[172.878976, 158.394944]
1.0914425147307731
[172.61952, 158.387264]
1.0898573259021636
[172.913856, 158.644352]
1.0899464986941358
[172.980864, 158.85184]
1.0889446669298888
[173.046912, 158.683904]
1.090513326417782
[173.114304, 158.677056]
1.0909851012108518
[173.118208, 158.707648]
1.090799404953692
[173.05888, 158.546048]
1.0915370151641999
[173.102144, 158.630848]
1.0912262411911209
[172.86272, 158.57504]
1.0901004344693843
[172.919936, 158.54752]
1.0906505254702188
[172.937408, 158.594432]
1.0904380804491294
[173.048192, 158.693824]
1.090453223938948
[172.916416, 158.421056]
1.0914989482206203
[172.78208, 158.313728]
1.0913903815087975
[172.714688, 158.329472]
1.0908562115333775
[172.58336, 158.188288]
1.090999606747119
[172.38016, 158.349504]
1.0886056201350653
[172.095168, 157.906944]
1.0898518053772226
[171.84032, 153.926528]
1.1163788479656995
[171.960128, 149.509824]
1.150159390194988
[171.818688, 147.378368]
1.1658338352613595
[171.956544, 142.504448]
1.2066749242802584
[172.156352, 143.64768]
1.1984624603752736
[172.263232, 149.558144]
1.1518144541831168
[172.545664, 156.73472]
1.1008770998538167
[172.5536, 156.151744]
1.105037930284019
[172.62752, 155.37024]
1.111071978777918
[172.910336, 154.888064]
1.11635675167326
[172.770304, 154.359872]
1.1192695469454652
[172.876864, 153.665728]
1.1250190022852722
[172.735744, 153.41184]
1.1259609688535122
[172.69344, 153.21248]
1.1271499554083324
[172.7392, 153.245568]
1.1272051926487037
[172.897216, 153.590976]
1.1256990514859413
[172.949184, 153.667456]
1.1254769780271499
[173.10368, 153.99296]
1.1241012576159324
[173.165312, 154.54016]
1.120519818278951
[173.182656, 155.1056]
1.1165467655584325
[173.277504, 155.707648]
1.1128387476509825
[173.261504, 156.279168]
1.1086666650285726
[173.34016, 157.256512]
1.1022765149464844
[173.180032, 157.490496]
1.0996221130702388
[173.630528, 158.219456]
1.0974031411155907
[173.690176, 158.599616]
1.0951487801836797
[173.611328, 158.570432]
1.0948530934190805
[173.83936, 158.70528]
1.095359650290148
[173.775296, 158.869312]
1.0938254456593857
[173.50656, 158.731008]
1.0930854795554503
[173.329664, 158.746304]
1.091865823849354
[173.500032, 158.845952]
1.0922534053621964
[173.58688, 158.888768]
1.0925056703819367
[173.581952, 158.794368]
1.0931241087845132
[173.619392, 158.867584]
1.0928559976086751
[173.25984, 158.82912]
1.0908568907263354
[173.243456, 158.751872]
1.0912844920657063
[173.253376, 158.78048]
1.0911503479520908
[172.973312, 158.923904]
1.0884033656761918
[173.005888, 159.021312]
1.0879415206937797
[172.908864, 158.867072]
1.0883870510309397
[173.094336, 158.831616]
1.0897977390093418
[173.323328, 158.81216]
1.0913731542975047
[173.29728, 158.781312]
1.091421136512589
[173.52288, 158.709888]
1.0933337688449505
[173.813824, 158.78976]
1.0946160759988555
[173.678656, 158.662272]
1.0946436970220619
[173.711488, 158.766848]
1.09412947468731
[173.32256, 158.729344]
1.0919377326979944
[173.39776, 158.849856]
1.091582733320199
[173.273344, 158.872576]
1.0906435104319074
[172.998016, 158.839232]
1.0891390862428747
[173.09856, 158.996224]
1.088696043498492
[173.113792, 158.839424]
1.089866656781631
[173.122112, 158.74912]
1.0905390341691341
[173.077184, 158.735232]
1.0903514098243796
[173.283456, 158.833984]
1.0909721687771807
[173.073664, 158.700928]
1.0905649146550676
[173.264256, 158.841088]
1.0908025006728737
[173.372736, 158.741248]
1.0921719350474048
[173.18144, 158.704]
1.0912229055348321
[173.030272, 158.681792]
1.0904229768214364
[172.955584, 158.809152]
1.0890781911611742
[172.861184, 158.741632]
1.088946748386712
[173.610944, 158.823744]
1.093104466798113
[173.564672, 158.720064]
1.093526978416541
[173.690752, 158.76992]
1.09397770056192
[173.537408, 158.706624]
1.0934477945923669
[173.63936, 158.839424]
1.0931754574985113
[173.705088, 158.84]
1.093585293376983
[173.592576, 158.907264]
1.0924143530656976
[173.585024, 158.812864]
1.093016142571423
[173.5744, 158.865664]
1.0925859976892174
[173.541312, 158.723456]
1.0933564349808513
[173.896192, 158.918144]
1.0942500813500566
[173.789312, 158.748032]
1.0947493950665166
[173.919104, 158.888576]
1.0945979149564535
[173.760832, 158.775296]
1.0943820378706772
[173.831296, 158.854336]
1.0942810903191211
[173.788928, 158.905216]
1.0936640871499146
[173.78368, 158.830336]
1.094146649667731
[173.894144, 158.98272]
1.0937927342040696
[173.911744, 158.750912]
1.0955007552964484
[173.927232, 158.808]
1.095204473326281
[173.685504, 158.74016]
1.0941497350134963
[173.71744, 158.980736]
1.0926949036139826
[173.576704, 158.805568]
1.0930139678729653
[173.580032, 158.819328]
1.0929402245046647
[173.714624, 158.833344]
1.0936911584509608
[173.759872, 158.858624]
1.0938019455588386
[173.63008, 158.836544]
1.0931368539471622
[173.716608, 158.820992]
1.0937887102480761
[173.532608, 158.785728]
1.0928728304851176
[173.63264, 158.877312]
1.0928724675301658
[173.628864, 158.82272]
1.0932243447285124
[173.881408, 158.873024]
1.0944677933492346
[173.831936, 158.744896]
1.095039528074024
[173.86944, 158.75584]
1.0952002773567258
[173.819776, 158.884672]
1.0939996527795959
[173.727296, 158.922752]
1.0931555980102836
[173.71936, 158.910592]
1.093189307355925
[174.1344, 158.883328]
1.0959891273173734
[174.0688, 158.893312]
1.0955074056232146
[174.074368, 158.833152]
1.095957398112958
[174.08768, 158.812992]
1.0961803427266201
[173.597568, 158.933184]
1.092267603472916
[173.6384, 159.02368]
1.0919027908296424
[173.645824, 158.925824]
1.092621825890297
[173.72352, 158.846592]
1.0936559469906664
[173.905856, 158.967744]
1.093969453325072
[173.909632, 159.063936]
1.0933316273526639
[173.867008, 158.9392]
1.0939214995419633
[173.829376, 159.066816]
1.0928072892337268
[173.76992, 158.947264]
1.0932551817941327
[173.788288, 158.903424]
1.0936723931134422
[173.915712, 158.934144]
1.094262740673269
[174.151488, 159.085312]
1.0947050095988748
[174.11168, 159.05344]
1.0946740919278453
[174.059776, 159.116672]
1.0939128741958606
[174.006336, 158.976]
1.0945446859903383
[173.95296, 159.075648]
1.093523503987235
[173.969216, 159.017536]
1.0940253532792759
[173.743424, 158.990144]
1.0927936765690331
[173.58336, 158.842432]
1.0928022053955961
[173.513984, 158.832192]
1.0924358709347788
[173.344384, 158.851648]
1.0912344075901559
[173.394944, 158.908224]
1.091164067128458
[173.464128, 158.844352]
1.0920383747733127
[173.78944, 159.045376]
1.0927035061993882
[173.743808, 159.020864]
1.0925849830623484
[173.852032, 158.93824]
1.0938338816385536
[173.834112, 158.982272]
1.093418214579296
[173.678272, 158.942336]
1.0927124664884753
[173.710976, 159.016192]
1.092410614385735
[173.5296, 158.809152]
1.092692693176776
[173.776768, 158.987904]
1.0930187997195058
[173.820928, 158.835264]
1.0943472099495488
[173.860864, 158.952064]
1.0937943152471425
[173.922176, 159.164352]
1.0927206614707292
[173.824832, 159.215424]
1.0917587481976618
[173.769984, 159.046272]
1.0925750211862872
[173.78016, 159.080128]
1.0924064632384505
[174.032192, 159.151104]
1.0935028889274938
[174.017664, 159.100032]
1.0937625958491322
[174.095168, 159.0832]
1.0943655143974977
[174.182208, 159.148224]
1.0944652954468408
[174.158592, 159.087488]
1.0947346908890785
[174.143488, 159.044736]
1.0949339939172837
[174.03744, 159.105792]
1.0938472937553398
[173.81344, 159.082048]
1.0926024789421873
[173.884864, 159.216]
1.0921318460456235
[173.755328, 159.038592]
1.0925356280820193
[173.748096, 158.98176]
1.0928806927285244
[173.975616, 159.173504]
1.0929935675726532
[174.025664, 159.050176]
1.094155746171573
[174.125248, 159.07584]
1.0946052398654629
[174.118976, 158.9856]
1.095187086126039
[174.146624, 159.023488]
1.0951000144079346
[174.138752, 158.980992]
1.0953432219117114
[174.133056, 158.962112]
1.0954374838703704
[174.097728, 159.08384]
1.0943772038693558
[174.096512, 159.078336]
1.0944074245282525
[173.973568, 159.022912]
1.094015735292283
[173.955072, 159.093248]
1.093415806056081
[173.785408, 159.16256]
1.0918736667718838
[173.571904, 159.139712]
1.0906888156238461
[173.578112, 159.166016]
1.090547570154674
[173.926272, 159.101952]
1.093174972485567
[173.863104, 158.970112]
1.0936842266299718
[174.035584, 159.138432]
1.0936112780098273
[173.978112, 158.936512]
1.0946390468163791
[173.971392, 159.074176]
1.0936494934287764
[173.8944, 159.047488]
1.0933489248192338
[174.003968, 159.032512]
1.0941408508972053
[173.838144, 159.089536]
1.0927063361351435
[173.913984, 159.1104]
1.0930397007360926
[173.823744, 158.99392]
1.0932728999951697
[173.6496, 158.93216]
1.0926020259209965
[173.684544, 159.100096]
1.0916683796344158
[173.38016, 158.878144]
1.0912776020344246
[173.502592, 158.983104]
1.091327239402748
[173.70016, 158.9952]
1.0924868172120918
[173.966656, 159.022592]
1.0939744712499717
[173.94464, 158.980608]
1.0941248884895447
[174.002304, 158.933696]
1.0948106561367579
[173.922944, 159.179648]
1.0926204837442537
[173.860224, 159.043008]
1.0931648375262117
[173.815872, 159.088128]
1.0925760091915846
[173.71456, 158.888576]
1.0933105725612395
[173.939712, 159.077824]
1.093425265862324
[173.768192, 158.923712]
1.0934063256715272
[173.818112, 158.953024]
1.09351874928784
[173.615616, 158.872576]
1.092797891059562
[173.471744, 158.944768]
1.0913963773881503
[173.467392, 158.88128]
1.0918051012680663
[173.405312, 158.788864]
1.092049578489333
[173.571584, 159.013568]
1.091552036616146
[173.506944, 159.073088]
1.0907372590893565
[173.524288, 158.939456]
1.0917634448176292
[173.470272, 158.948864]
1.0913589920340672
[173.521472, 158.851328]
1.0923514092371955
[173.596992, 159.019584]
1.091670520280068
[173.474496, 158.821056]
1.092263836855486
[173.5088, 158.974528]
1.091425162149247
[173.561728, 158.849792]
1.092615393541088
[173.72224, 158.904064]
1.0932523412365338
[173.854784, 159.0064]
1.0933823041085138
[173.788032, 158.861696]
1.0939580551878283
[173.839936, 159.026432]
1.0931512064610742
[173.793024, 158.822144]
1.0942619185395206
[173.85024, 158.944256]
1.0937812059090706
[173.858048, 158.841152]
1.0945403367510202
[174.072512, 159.244352]
1.0931157671450726
[173.88896, 158.969408]
1.093851717683946
[174.037888, 159.07584]
1.0940560678478894
[173.836992, 159.071808]
1.0928208724452293
[173.724608, 159.0224]
1.092453692058477
[173.893376, 159.127168]
1.0927950153678345
[173.70144, 159.054272]
1.092089120372699
[173.696256, 159.015424]
1.0923233207867937
[173.867136, 159.119424]
1.0926832917645553
[173.950208, 159.13152]
1.093122267668907
[174.015488, 159.101632]
1.0937379196713708
[174.011904, 159.155136]
1.093347713265125
[174.032, 159.245504]
1.0928534597749147
[173.9984, 159.146624]
1.093321338692048
[173.994752, 159.088384]
1.0936986574708059
[174.01824, 159.191808]
1.09313564677901
[174.132288, 159.117184]
1.094365068703076
[174.291904, 159.297024]
1.0941315764944861
[174.1712, 159.2256]
1.0938643032276218
[174.174272, 159.390656]
1.0927508322696156
[173.9808, 159.222016]
1.0926931109828428
[174.05952, 159.205888]
1.0932982579136772
[173.868416, 159.145216]
1.0925142481191517
[174.04352, 159.298496]
1.0925622298405127
[173.928768, 159.25472]
1.092141997424001
[173.921024, 159.151424]
1.0928021856719297
[174.21984, 159.102144]
1.0950188075403937
[174.345792, 158.746112]
1.0982681075048941
[174.30144, 157.89888]
1.1038801541847543
[174.370752, 157.172352]
1.109423825381197
[174.21728, 155.904384]
1.1174623543620172
[174.156992, 153.959488]
1.1311871341115398
[174.172928, 149.790016]
1.1627806221744446
[174.262528, 148.017536]
1.1773100181859533
[174.37632, 146.24448]
1.1923617219603775
[174.3952, 143.970944]
1.2113221956785947
[174.175744, 138.461696]
1.2579344976389717
[174.297088, 136.109312]
1.2805669607675338
[174.26912, 134.23968]
1.2981937978398042
[173.969856, 132.77824]
1.3102286639738558
[173.481408, 131.49536]
1.319296802563984
[173.46368, 130.932608]
1.3248317791088375
[172.7104, 130.24992]
1.3259923691315894
[172.49408, 130.182272]
1.3250197384786768
[172.703744, 129.853184]
1.3299923704604732
[173.444992, 130.267648]
1.3314510138388314
[173.80096, 131.564096]
1.3210364019070977
[173.701824, 133.161472]
1.3044450575013167
[173.58624, 136.21824]
1.2743244957503488
[173.784576, 145.938688]
1.190805388081877
[173.809024, 151.370432]
1.1482362949192084
[173.457024, 158.548544]
1.0940310117259733
[173.308864, 158.85568]
1.0909831112113837
[173.186688, 159.013888]
1.0891293218363418
[172.966976, 158.653696]
1.0902171229594297
[172.77696, 158.541824]
1.0897878909227132
[172.470912, 158.535744]
1.087899218487914
[172.329024, 158.414528]
1.0878359843359822
[171.907776, 158.384512]
1.0853824899242674
[171.68, 158.4352]
1.0835975843751893
[171.604352, 158.174912]
1.084902465442813
[171.331456, 158.171136]
1.083203044074995
[171.176704, 158.247936]
1.0816994415649124
[171.036544, 158.228992]
1.0809431434664007
[170.830592, 158.135296]
1.080281229561805
[170.482432, 158.075008]
1.0784907377641884
[170.600064, 158.051712]
1.0793939644260226
[170.416256, 157.994752]
1.078619725293154
[170.206976, 157.818624]
1.0784974021823939
[170.06848, 157.704832]
1.0783973949510943
[169.571008, 157.884736]
1.0740177441852263
[169.438208, 157.761408]
1.074015566595349
[169.352832, 157.790528]
1.0732762869010744
[169.526912, 157.72096]
1.0748534120005357
[169.694592, 157.836864]
1.0751264799584463
[169.856064, 157.721088]
1.0769394641761538
[169.81408, 157.714624]
1.0767174006641262
[169.634368, 157.611392]
1.0762824047642445
[169.608768, 157.6576]
1.0758045790371031
[169.720512, 157.586496]
1.07699908499774
[169.72256, 157.413952]
1.0781926115418283
[169.63456, 157.446976]
1.0774075457632162
[169.785408, 157.426816]
1.0785037283609928
[169.765376, 157.441472]
1.0782760974186014
[169.733056, 157.428224]
1.0781615372857156
[169.71904, 157.327424]
1.0787632294799412
[169.582784, 157.279168]
1.0782278807578636
[169.648448, 157.552512]
1.0767739964691898
[169.394624, 157.455488]
1.0758254675759538
[169.320896, 157.475904]
1.0752178060206594
[169.347072, 157.569728]
1.0747436969618935
[169.325184, 157.4512]
1.0754137408924163
[169.454656, 157.5552]
1.0755256316516368
[169.560448, 157.480576]
1.0767070600503772
[169.617664, 157.395584]
1.0776519879998665
[169.613184, 157.346304]
1.0779610304669118
[169.582272, 157.251456]
1.0784146380177237
[169.645184, 157.32288]
1.0783249327751945
[169.661888, 157.411328]
1.0778251486449566
[169.923328, 157.431552]
1.0793473470934212
[169.845376, 157.432768]
1.0788438655922
[169.780736, 157.472128]
1.0781637243131685
[169.966656, 157.44384]
1.0795383039438062
[169.844352, 157.371328]
1.0792585546459899
[170.014016, 157.459264]
1.0797333334417212
[169.977344, 157.406336]
1.0798634179503421
[170.10688, 157.549696]
1.0797030036795499
[170.122752, 157.45792]
1.0804331214333327
[170.304064, 157.4256]
1.0818066693091848
[170.534784, 157.673088]
1.081571916698936
[170.587328, 157.649088]
1.0820698689991788
[170.653312, 157.615424]
1.0827196201305782
[170.75936, 157.560448]
1.0837704650344735
[171.065664, 157.693696]
1.0847970993082692
[171.31904, 157.727168]
1.0861733090902894
[171.862656, 157.989952]
1.0878075081635572
[172.11808, 158.07072]
1.0888675650999755
[172.281536, 158.123584]
1.0895372571367974
[172.411136, 158.093952]
1.0905612379150342
[172.798144, 158.3536]
1.0912170231684029
[172.97472, 158.00416]
1.094747885118974
[173.043712, 150.652224]
1.1486303182620126
[173.323456, 146.053952]
1.18670842949871
[173.249152, 138.299136]
1.2527131912089458
[173.358592, 136.022016]
1.2744892120993117
[172.680064, 133.491968]
1.2935614523264798
[172.644736, 133.941888]
1.28895253440059
[173.092736, 135.248704]
1.2798106812173224
[173.648704, 141.164928]
1.2301122273090381
[173.73952, 144.711488]
1.2005924505454604
[173.528704, 147.315456]
1.1779395639246435
[173.800768, 150.043328]
1.1583371971061587
[173.566272, 155.998592]
1.1126143497500285
[173.540608, 157.795392]
1.0997824828750387
[173.371328, 158.422848]
1.0943581067296557
[173.136192, 158.470656]
1.092544174235008
[172.871424, 158.471808]
1.0908654743183088
[172.645376, 158.357952]
1.0902223337669836
[172.401984, 158.231104]
1.0895581187375145
[172.307456, 158.244352]
1.0888695477738126
[171.956736, 158.100864]
1.0876394451582505
[171.866944, 157.891968]
1.088509733440019
[171.756416, 157.83584]
1.088196546487794
[171.687232, 157.885888]
1.0874134108806481
[171.35808, 157.932544]
1.0850080398882196
[171.436288, 158.039936]
1.0847656126613465
[171.279168, 157.537216]
1.0872298771612163
[171.247424, 153.357632]
1.1166540704019217
[171.587392, 147.921152]
1.1599922639866946
[171.589696, 145.156544]
1.1821010012473154
[171.795008, 141.4528]
1.2145041172744548
[171.851328, 140.396928]
1.2240390900860736
[171.647168, 137.874368]
1.2449534347094884
[171.838912, 136.229184]
1.2613957373480267
[171.981184, 135.9184]
1.265326725447033
[172.067648, 134.603904]
1.2783258351852855
[172.136064, 133.22048]
1.292114125395735
[171.639616, 132.342528]
1.2969346935854211
[171.578304, 131.241088]
1.3073520390199753
[171.561536, 130.440896]
1.3152434647489692
[172.07872, 130.12896]
1.322370669833986
[172.107328, 129.971648]
1.3241913190175139
[172.137472, 129.263168]
1.3316822932886807
[172.509248, 129.02528]
1.3370189779863295
[172.451712, 128.892416]
1.3379508069737787
[172.381248, 128.925184]
1.3370641999626698
[172.0272, 128.743104]
1.3362051609381735
[171.79488, 128.564992]
1.3362492956091812
[170.971904, 127.673088]
1.3391381588577225
[170.592256, 128.227136]
1.330391220778728
[170.657856, 128.861696]
1.3243489826488084
[168.379456, 127.592]
1.3196709511568123
[169.953344, 132.581952]
1.2818739009062108
[174.191872, 134.393984]
1.2961284933706556
[175.508096, 135.70752]
1.293282022985904
[175.469184, 136.648512]
1.28409143599017
[174.928256, 137.12608]
1.2756745908582816
[175.23968, 138.75808]
1.2629151397886162
[175.476096, 140.32544]
1.2504938235005714
[175.565312, 141.41184]
1.241517768243451
[175.421632, 144.495552]
1.2140279030872867
[175.760704, 145.922368]
1.2044808921960477
[175.543488, 145.898944]
1.20318545965624
[175.743168, 146.373952]
1.2006450983847181
[175.797952, 147.089728]
1.1951749071151998
[175.886464, 148.009024]
1.188349596846203
[176.244672, 148.712896]
1.1851337492613956
[176.235968, 148.935232]
1.183306096437947
[176.325888, 149.35328]
1.1805960203887051
[176.348864, 150.869824]
1.1688809552796986
[176.421248, 151.704192]
1.162929288071354
[176.468928, 152.545024]
1.1568317561115595
[176.393792, 153.190528]
1.151466701648812
[176.520256, 154.398144]
1.1432796497864637
[176.341056, 154.937408]
1.1381438367679417
[176.537536, 155.471168]
1.135500159103455
[176.467584, 155.647168]
1.1337667512202985
[176.408704, 156.668352]
1.126000891360624
[176.696448, 157.059328]
1.1250299504655974
[176.78368, 157.607552]
1.1216701088029082
[176.7616, 157.805056]
1.1201263411991056
[176.806144, 158.4272]
1.1160087661714655
[176.4928, 158.52352]
1.11335403099805
[176.625088, 158.836544]
1.1119927666016203
[176.544832, 158.918784]
1.1109123009650013
[176.496896, 159.161536]
1.1089167674280298
[176.403968, 159.224448]
1.107894988588687
[176.257088, 159.274432]
1.1066251236105493
[176.232384, 159.184256]
1.1070968224395257
[176.30784, 159.080064]
1.1082962601775166
[176.385472, 158.992064]
1.1093979634102995
[176.352384, 158.878912]
1.1099798065082418
[176.5104, 158.825728]
1.1113463934508143
[176.407296, 158.942848]
1.109878791148879
[176.544128, 159.038272]
1.1100732281598231
[176.604224, 159.09888]
1.110028078136062
[176.147712, 158.997888]
1.1078619610343505
[176.067072, 158.930752]
1.1078225565811202
[175.924736, 158.88992]
1.1072114329216103
[175.821632, 158.572992]
1.1087741347530353
[176.540928, 158.089408]
1.1167157258252243
[176.57376, 157.36]
1.1221006609049313
[176.027648, 155.141888]
1.1346236033945907
[175.904384, 154.463488]
1.138808829695727
[175.778304, 153.793984]
1.1429465537481622
[175.795456, 154.371456]
1.1387821334016568
[176.049664, 154.595776]
1.1387740891445832
[176.129472, 154.690368]
1.1385936582683673
[176.197376, 154.570368]
1.1399169082653668
[176.207808, 154.452928]
1.1408511983664045
[175.879808, 154.742976]
1.1365931594853131
[175.691648, 155.521344]
1.1296947639547148
[175.584512, 156.332416]
1.1231484582186717
[175.622016, 158.016832]
1.1114133461427704
[175.370432, 157.829184]
1.111140712734091
[175.66144, 157.946304]
1.1121592310257542
[175.6032, 157.78368]
1.1129363949427469
[175.622016, 157.920704]
1.1120898751819142
[175.643968, 158.177728]
1.1104216138443965
[175.716992, 158.227072]
1.110536836578762
[175.564096, 158.055488]
1.1107750716001712
[175.742208, 158.044608]
1.1119785117882668
[175.633792, 158.114688]
1.1107999783043558
[175.329472, 158.663872]
1.1050371441836488
[175.402816, 159.099712]
1.102470983731259
[175.672512, 159.674304]
1.1001927523667177
[175.159744, 159.639808]
1.0972184581930844
[175.209728, 159.798912]
1.0964388042892308
[175.18336, 159.451264]
1.0986639779788763
[175.196032, 158.996288]
1.1018875610479661
[175.263936, 157.74336]
1.1110701331580612
[175.236096, 157.155648]
1.1150480318721985
[175.208704, 156.768128]
1.1176296243073083
[175.23296, 156.230208]
1.1216330199086721
[175.249536, 155.594944]
1.1263189631663095
[175.001728, 156.518208]
1.1180918197070084
[175.038144, 157.358464]
1.1123529014619766
[174.868032, 158.896448]
1.1005156767255113
[175.04032, 159.30528]
1.0987728718093963
[175.065216, 159.298752]
1.0989741840538712
[175.09408, 158.60736]
1.1039467525340563
[174.98208, 158.014336]
1.1073810416796614
[174.914368, 157.516288]
1.110452577450276
[174.792384, 157.100992]
1.112611586819261
[174.744512, 157.33344]
1.1106635181942248
[174.922688, 157.716928]
1.1090926650562203
[175.040768, 157.993792]
1.107896492540669
[175.044736, 158.21056]
1.1064036180644328
[175.080768, 158.340608]
1.1057224688691356
[174.979712, 158.115008]
1.1066609945085037
[174.883712, 157.751936]
1.10859946593619
[174.90208, 157.949504]
1.1073290866427794
[174.860288, 157.820032]
1.1079727065319567
[175.090304, 158.093824]
1.10750881704272
[175.136448, 158.148736]
1.10741604662588
[175.14432, 157.968832]
1.108727068387769
[175.136512, 157.959744]
1.108741427182865
[175.027712, 157.826816]
1.1089858899516798
[174.958208, 157.953856]
1.107653921408541
[175.01472, 157.977792]
1.1078438164270583
[174.94976, 158.06976]
1.1067882939785574
[174.946048, 158.265472]
1.1053961788961777
[174.963136, 158.236544]
1.1057062520273444
[174.95328, 158.339712]
1.1049235709106255
[175.12384, 158.63552]
1.1039383865605885
[174.84096, 158.524608]
1.1029263040347654
[174.8016, 158.686016]
1.101556421959702
[174.796288, 158.697984]
1.101439877144249
[174.7728, 158.737536]
1.1010174682313325
[174.778944, 158.574016]
1.1021915721677882
[174.710272, 158.680576]
1.1010186401138347
[174.214144, 157.965184]
1.1028641855663588
[173.972992, 157.843008]
1.1021900444269284
[174.910144, 158.238848]
1.1053552664893012
[175.019584, 158.247744]
1.1059847020631144
[174.953408, 158.147648]
1.1062662658125653
[175.285952, 157.728128]
1.1113170125242342
[175.22624, 157.014336]
1.1159887973541474
[175.105856, 157.01344]
1.1152284543284956
[175.027264, 157.157504]
1.113706056314053
[174.963392, 156.983616]
1.1145328185076333
[175.118912, 156.100224]
1.1218363914711615
[174.787328, 155.73568]
1.1223332251157858
[174.903232, 156.161152]
1.1200175572475286
[174.851584, 156.962048]
1.1139736403031641
[174.9824, 157.113408]
1.1137330812657313
[174.84704, 157.052288]
1.1133046339318533
[174.919616, 157.025344]
1.1139578589300845
[174.898688, 157.085056]
1.1134011882072345
[174.936256, 157.323712]
1.1119509816803712
[174.875584, 157.708096]
1.1088560982944085
[175.031424, 158.046656]
1.1074667976524601
[174.891072, 157.886912]
1.1076983505763924
[174.9504, 158.076544]
1.1067448438143992
[174.741952, 158.716416]
1.1009696186688085
[174.672128, 159.045248]
1.098254303077323
[174.221056, 159.628864]
1.0914132421565064
[173.83616, 159.85664]
1.0874503555185446
[173.84544, 159.572736]
1.0894432492528048
[174.172416, 159.737792]
1.0903644893251059
[174.335808, 159.805376]
1.09092580214573
[173.587072, 159.414848]
1.0889015306779957
[173.403776, 159.391168]
1.0879133277949253
[172.93184, 159.075264]
1.0871070438707553
[173.215936, 159.27424]
1.0875326480917442
[173.171072, 159.271936]
1.087266698384328
[173.228224, 159.334976]
1.0871952182049471
[173.165568, 159.388544]
1.086436726594353
[172.896, 159.37184]
1.0848591570505806
[172.583424, 159.409216]
1.0826439545377353
[172.39808, 159.521088]
1.0807228195434575
[172.068608, 159.745984]
1.0771388656631269
[172.015552, 159.69216]
1.077169674453649
[171.704192, 159.750912]
1.0748244867609895
[171.619584, 159.753472]
1.0742776469984954
[171.390528, 159.809536]
1.072467465270658
[171.207552, 159.76416]
1.0716267778705812
[170.959552, 159.54912]
1.0715167341568541
[170.917888, 159.470016]
1.0717869872164558
[170.6208, 159.28]
1.0712004018081367
[170.575232, 159.242816]
1.0711643783038853
[170.614656, 159.283136]
1.071140738966867
[170.588224, 159.148928]
1.0718779331017547
[170.335744, 159.031616]
1.0710810107092164
[169.993984, 158.937088]
1.069567752493364
[169.662016, 158.61344]
1.0696572497261265
[169.61344, 158.628352]
1.0692504704329273
[169.57952, 158.53536]
1.0696637015237485
[169.800576, 158.678976]
1.0700886801790301
[169.755328, 158.736]
1.0694192117730068
[169.56576, 158.701184]
1.0684593254200296
[169.602112, 158.6496]
1.069035862681028
[169.654784, 158.803456]
1.0683318126275538
[169.707712, 158.889472]
1.068086575301855
[169.694848, 159.028288]
1.0670733498684208
[170.073024, 159.37856]
1.0671010203630904
[170.8096, 159.350144]
1.0719136846214585
[171.09024, 159.517696]
1.072547085935845
[171.167936, 159.392576]
1.0738764646102463
[171.343744, 159.419712]
1.0747964718440841
[171.151744, 159.321984]
1.0742506445312658
[171.314624, 159.191232]
1.0761561541278857
[171.24768, 158.936256]
1.077461394334091
[171.291328, 158.87424]
1.0781567106158936
[171.221824, 158.62944]
1.0793823895488757
[171.238528, 158.44896]
1.080717273246855
[171.26592, 158.260736]
1.082175682539477
[171.219264, 158.11584]
1.082872304254906
[171.309184, 158.1024]
1.083533102596798
[171.477824, 158.092736]
1.0846660532208134
[171.510784, 158.115968]
1.0847151376893192
[171.984704, 158.395776]
1.08579097462801
[171.610688, 158.112768]
1.085368943765503
[171.476352, 157.790976]
1.086731043478684
[171.361344, 157.47904]
1.0881533440894737
[171.237888, 157.695168]
1.0858791056933337
[171.432832, 157.755904]
1.0866967742773037
[171.854208, 157.969344]
1.087895940113545
[172.49792, 158.081344]
1.0911972003476893
[172.564352, 158.061376]
1.0917553444555614
[172.700992, 158.18112]
1.0917926994068572
[172.588736, 158.043776]
1.092031210390721
[172.606848, 157.930048]
1.0929322835385955
[172.543488, 157.62336]
1.0946568325913113
[172.733888, 156.705856]
1.1022810021853937
[172.817984, 155.940288]
1.1082317867721265
[172.84992, 155.218304]
1.113592376321803
[172.940416, 154.12384]
1.1220873811605006
[173.17824, 153.65344]
1.1270703734325767
[173.197504, 153.020608]
1.1318573770142124
[173.433088, 153.775424]
1.127833586724495
[173.382016, 154.303104]
1.1236456785729987
[173.548224, 155.147712]
1.1185999571814504
[173.501248, 155.901632]
1.1128892351813224
[173.470848, 157.14624]
1.1038816328026684
[173.394688, 157.865472]
1.0983699336103083
[173.346688, 158.1184]
1.0963093985266736
[173.304576, 158.482624]
1.0935241455870899
[173.007168, 158.212096]
1.0935141646818205
[172.27648, 157.54688]
1.0934934414442228
[172.432, 157.744896]
1.0931066828304858
[172.312832, 157.582848]
1.0934745385487636
[172.376768, 157.611136]
1.0936839386780386
[172.425984, 157.43072]
1.0952499232678348
[172.012992, 157.3648]
1.0930842983945583
[172.076416, 157.378624]
1.0933912854645367
[171.792448, 157.363776]
1.0916899197945023
[171.50048, 157.689472]
1.087583576917551
[171.170944, 157.573952]
1.086289591822892
[170.85184, 157.7024]
1.0833813562761252
[170.652032, 157.978944]
1.080220108320258
[170.531328, 157.935296]
1.0797543824529257
[170.342848, 157.954176]
1.0784320637398026
[170.322368, 157.894336]
1.078711069154501
[170.212544, 157.685504]
1.079443193459305
[170.442624, 157.679936]
1.0809404691792872
[170.597376, 157.8112]
1.08102198069592
[171.182016, 157.921664]
1.0839679095579946
[171.249472, 157.835648]
1.0849860229293702
[171.422464, 157.602624]
1.0876878801205747
[171.607744, 157.602304]
1.0888657059226747
[171.931968, 157.7376]
1.0899872192806284
[171.889216, 157.759296]
1.089566322608336
[171.997056, 157.715328]
1.0905538363398641
[172.0864, 157.83968]
1.0902606999710087
[172.4528, 157.993856]
1.0915158624902477
[172.536896, 158.192064]
1.090679845987723
[172.3424, 157.765568]
1.0923955219430388
[172.5344, 157.879168]
1.0928256221872161
[172.558528, 157.7456]
1.0939039060360478
[172.663168, 157.656896]
1.095183099380569
[172.644288, 157.535168]
1.0959095051080912
[172.670784, 157.534784]
1.0960803678760875
[172.560128, 157.47264]
1.0958102182067944
[172.561728, 157.447424]
1.0959958798690792
[172.432512, 157.119936]
1.0974578808382407
[172.343872, 156.978368]
1.0978829388772855
[172.232192, 157.007616]
1.096967117824399
[172.227968, 157.460224]
1.093787139538173
[172.046848, 157.341888]
1.0934586471976235
[172.129856, 157.362944]
1.093839830551213
[171.94784, 157.23424]
1.0935775820839024
[171.873472, 157.215296]
1.0932363222469141
[171.38784, 157.0832]
1.0910640985159457
[171.200256, 157.119808]
1.0896159954574283
[170.856704, 157.073408]
1.0877506649629707
[170.5392, 157.08352]
1.0856593995347188
[170.348736, 157.179904]
1.0837819063688956
[169.96352, 157.017536]
1.0824492877024894
[169.85408, 156.977472]
1.0820283817540393
[169.892864, 157.08128]
1.081560221561729
[169.55904, 156.965632]
1.0802303525908143
[169.841856, 157.097088]
1.081126697905438
[169.779968, 157.108672]
1.0806530654144921
[169.651008, 156.89248]
1.0813202009427092
[169.689536, 156.883904]
1.0816248937813275
[169.720256, 156.72288]
1.0829322176825744
[170.018432, 156.835968]
1.0840525561075376
[170.315904, 156.88768]
1.0855913224033908
[170.2416, 156.728512]
1.0862197173160173
[170.346816, 156.80384]
1.0863689052513
[170.544064, 156.795904]
1.0876818823022314
[170.44768, 156.903296]
1.086323132434388
[170.299648, 156.657152]
1.0870850505440057
[170.238592, 156.767552]
1.0859300271525578
[170.621952, 156.878272]
1.0876072882801768
[170.683456, 156.77344]
1.0887268659793394
[170.612288, 156.8768]
1.0875558909921672
[170.488704, 156.880064]
1.0867455026025488
[170.279936, 156.906496]
1.085231907798132
[170.136448, 156.960384]
1.0839451565052236
[169.907456, 156.865408]
1.0831416445874416
[170.032384, 156.998336]
1.083020293922096
[169.839168, 156.765824]
1.0833940948761893
[170.090496, 156.844352]
1.0844540707465196
[169.92608, 156.815936]
1.0836021155400941
[170.147904, 157.035712]
1.0834981535919679
[170.105088, 157.038016]
1.0832096095763206
[170.286464, 156.966336]
1.084859775283281
[170.220352, 157.017216]
1.0840871869744526
[170.263552, 157.075328]
1.0839611425162836
[170.302528, 157.024]
1.0845636845323008
[170.337344, 156.976128]
1.085116228628088
[170.499968, 157.140224]
1.0850179773194164
[170.30752, 157.025408]
1.084585750606679
[170.389376, 157.030464]
1.085072104225585
[170.041536, 156.87552]
1.0839265170244536
[170.13696, 156.982912]
1.083792865302435
[170.110592, 157.027712]
1.0833157398357813
[169.924032, 156.833984]
1.083464359357217
[170.393856, 156.932672]
1.0857768100704996
[170.276544, 156.927104]
1.0850677777116182
[170.441792, 156.864576]
1.0865537417447264
[170.501504, 156.7984]
1.08739313666466
[170.299328, 157.142336]
1.0837265903950926
[169.989056, 156.93056]
1.0832119378150438
[170.204288, 157.094848]
1.0834492038847765
[170.146752, 157.044864]
1.0834276758009738
[170.183168, 157.098496]
1.083289607050089
[170.194688, 157.090496]
1.083418108247618
[170.299584, 157.04896]
1.0843725676375062
[170.130944, 156.900608]
1.0843230384422728
[170.011264, 156.830784]
1.0840426838649229
[170.076096, 156.778112]
1.0848204116656286
[170.013568, 156.689088]
1.0850377021787248
[170.091264, 156.800896]
1.0847595156599106
[170.171456, 156.812288]
1.0851920992314072
[170.123904, 156.81376]
1.0848786739122893
[170.139392, 156.824064]
1.0849061531781246
[170.102592, 156.906624]
1.0841007706596248
[170.175872, 156.98432]
1.0840310166008937
[170.211328, 156.953856]
1.0844673226760355
[170.112896, 156.923392]
1.0840505920239094
[170.196736, 157.004992]
1.0840211755814746
[170.190208, 157.054912]
1.083635053706566
[169.980928, 156.792768]
1.084112042718705
[170.073024, 156.90816]
1.0839017167749592
[170.02784, 156.951488]
1.0833146099258388
[169.968768, 156.957184]
1.0828989388596575
[170.10112, 156.936832]
1.0838827178568253
[169.9424, 156.946432]
1.0828051191377195
[169.911488, 157.039104]
1.0819692909098615
[169.95968, 157.044928]
1.0822360337546209
[169.825984, 156.95296]
1.082018357602176
[170.198592, 156.87008]
1.0849652910229917
[170.480064, 157.060864]
1.085439489241572
[170.287872, 156.8192]
1.085886626127413
[170.362048, 156.854592]
1.086114507887662
[170.294592, 156.89856]
1.0853802099904548
[170.389376, 157.021184]
1.0851362323188187
[170.360256, 156.978112]
1.0852484708186576
[170.244544, 156.929344]
1.0848483760946583
[170.275392, 157.020544]
1.0844147374753714
[170.168064, 157.034624]
1.083634039840793
[170.12224, 156.94496]
1.0839611542798189
[170.112, 156.877888]
1.0843593202886566
[170.19872, 157.102592]
1.0833603560150047
[170.07872, 157.000832]
1.0832982082540812
[169.946432, 156.962944]
1.0827168990918008
[169.962304, 156.928]
1.0830591353996737
[170.063616, 156.901376]
1.083888620581632
[170.185792, 156.890112]
1.0847451750177857
[170.229376, 156.888064]
1.085037138325577
[170.163712, 156.854464]
1.0848509354505842
[170.180672, 157.00224]
1.0839378597400902
[170.145856, 157.041088]
1.0834480209408637
[170.119744, 157.039232]
1.0832945489697758
[170.0784, 156.97504]
1.0834741625165376
[170.173632, 156.855872]
1.0849044401729506
[170.167872, 156.796928]
1.085275548255639
[170.40064, 156.952384]
1.0856836682391522
[170.354432, 156.835776]
1.0861962515491363
[170.512576, 156.968704]
1.0862839002607807
[170.468864, 156.804544]
1.0871423726087939
[170.565376, 156.880832]
1.087228910157743
[170.367104, 157.017792]
1.085017830336068
[169.990272, 156.860096]
1.0837062856317519
[170.09248, 156.918592]
1.0839536464869632
[170.1136, 156.881088]
1.0843474007523455
[170.01248, 156.734208]
1.0847184042937201
[170.208704, 156.881984]
1.084947421368664
[170.220352, 156.882176]
1.0850203403603988
[170.31104, 157.047424]
1.0844561194458051
[170.185792, 156.861632]
1.084942122749303
[170.308352, 156.883904]
1.0855693137264102
[170.176448, 156.868672]
1.0848338666371828
[170.180608, 156.824896]
1.085163212861305
[170.115456, 156.829056]
1.0847189949291027
[170.123904, 156.80352]
1.0849495215413534
[170.357888, 156.976704]
1.0852431198963126
[170.277248, 156.940928]
1.0849766862599408
[170.396416, 156.97888]
1.0854735108315208
[170.238336, 156.961216]
1.0845885393752301
[170.312768, 156.986624]
1.084887130256397
[170.29344, 157.00416]
1.084642852775366
[170.141248, 156.850944]
1.0847320625625307
[169.942656, 156.75136]
1.084154268262808
[170.106112, 156.939136]
1.0838986140461484
[170.221568, 156.866496]
1.085136548214859
[170.19328, 156.792704]
1.0854668339669682
[170.333056, 156.82048]
1.0861658885370074
[170.382208, 156.871616]
1.086125153450322
[170.360704, 156.964288]
1.0853469038766321
[170.5152, 156.982912]
1.0862022995216192
[170.48768, 156.96768]
1.086132380882485
[170.4816, 156.890816]
1.086625746149475
[170.545856, 156.98112]
1.0864099835699985
[170.437312, 156.913344]
1.0861874946722185
[170.432576, 156.91648]
1.0861356053870186
[170.421504, 156.886272]
1.0862741642557483
[170.507136, 156.872576]
1.0869148728710873
[170.516224, 156.7792]
1.087620194515599
[170.52576, 156.6976]
1.088247426891031
[170.305408, 156.880064]
1.085577119601379
[170.072896, 156.798144]
1.0846614102779175
[170.228288, 156.83168]
1.0854202926347534
[170.330304, 156.899136]
1.085603836594741
[170.174784, 156.725504]
1.0858142399082666
[170.297792, 156.918592]
1.0852620446658099
[170.170688, 156.762944]
1.085528784149397
[170.179392, 156.823936]
1.0851621017852786
[170.189696, 156.802624]
1.0853753059642675
[170.460352, 156.877568]
1.086582066341059
[170.24384, 156.811392]
1.0856598989950934
[170.301568, 156.765696]
1.0863446043705889
[169.969024, 156.688704]
1.0847560778854868
[169.959808, 156.725568]
1.08444212497606
[170.028224, 156.813888]
1.0842676383357066
[169.884608, 156.683648]
1.0842523145746517
[170.135232, 156.789376]
1.0851196448412423
[170.330624, 156.87648]
1.0857626586216111
[170.388992, 156.821376]
1.0865163687889081
[170.399104, 156.746496]
1.0870999247090027
[170.075072, 156.742912]
1.0850574984851629
[170.287808, 156.9568]
1.0849342494240455
[170.060352, 156.749056]
1.0849210600668626
[169.804736, 156.430336]
1.0854974830457436
[169.977728, 156.495168]
1.0861532031455439
[169.869248, 156.611392]
1.0846544803075373
[169.973184, 156.535232]
1.0858461818998038
[169.856704, 156.434048]
1.0858039293338495
[169.888384, 156.535616]
1.0853017884441072
[169.810112, 156.553088]
1.084680693107759
[169.788672, 156.7408]
1.0832448985841592
[169.830464, 156.507136]
1.0851292045878342
[169.879616, 156.25152]
1.0872189659338993
[169.833536, 156.278656]
1.0867353248801934
[169.253376, 156.313088]
1.0827844178985193
[169.304384, 156.30944]
1.0831360153295924
[169.21344, 156.285568]
1.0827195509184826
[169.417792, 156.148032]
1.0849819227949027
[169.639424, 156.164544]
1.0862864236327547
[169.856512, 156.323904]
1.0865677459027636
[169.526208, 156.273152]
1.0848069923104897
[169.390336, 156.380928]
1.0831905026167896
[169.331968, 156.372032]
1.082878861611263
[169.432896, 156.33088]
1.0838095199105895
[169.483264, 156.311808]
1.0842639859939434
[169.575488, 156.474624]
1.0837251668359977
[169.255488, 156.25216]
1.0832201487646635
[169.513984, 156.325824]
1.0843632847251135
[169.174784, 156.106048]
1.0837170383046273
[169.07584, 156.211904]
1.08234926833745
[169.550592, 156.251712]
1.08511189944594
[169.517312, 156.235008]
1.0850149026778941
[169.727808, 156.219072]
1.0864730268017466
[169.70144, 156.28768]
1.0858273665588996
[169.789824, 156.381824]
1.0857388643836257
[169.65632, 156.32896]
1.0852520224019913
[169.738496, 156.411264]
1.0852063442182784
[169.672768, 156.337728]
1.0852963655708237
[169.57536, 156.383296]
1.0843572449067704
[169.633408, 156.533696]
1.0836862115617587
[169.588608, 156.441344]
1.0840395746024785
[169.697984, 156.519168]
1.0841993742261649
[169.784896, 156.410752]
1.0855065513654714
[169.583232, 156.289472]
1.0850585764343745
[169.809216, 156.45696]
1.0853413999607302
[169.752, 156.530944]
1.0844628906090288
[169.74112, 156.41952]
1.0851658411942446
[169.792576, 156.44064]
1.0853482573326214
[169.51232, 156.461952]
1.083409211205546
[169.571392, 156.510592]
1.0834499431195046
[169.462656, 156.339072]
1.083943084937846
[169.472768, 156.35968]
1.0838648940698778
[169.63296, 156.596864]
1.0832462136661944
[169.679168, 156.568192]
1.0837397164297586
[169.446016, 156.407808]
1.0833603396577234
[169.581376, 156.490496]
1.0836528756353356
[169.563392, 156.452544]
1.0838007977677884
[169.490176, 156.415808]
1.0835872548125058
[169.642688, 156.50752]
1.0839267531681545
[169.582592, 156.382592]
1.084408372000894
[169.665472, 156.420288]
1.0846768930638973
[169.71904, 156.430016]
1.084951880334782
[169.809152, 156.32128]
1.0862830191769157
[169.811776, 156.546624]
1.0847361103104975
[169.71456, 156.475584]
1.0846072956660127
[169.578048, 156.441216]
1.083972960169269
[169.66368, 156.373376]
1.0849908362917227
[169.648064, 156.478336]
1.0841632671758472
[169.505664, 156.237824]
1.0849207935717282
[169.670016, 156.326464]
1.085356961697797
[169.42304, 156.407872]
1.083212998384122
[169.477888, 156.521792]
1.0827750298182122
[169.373952, 156.467264]
1.0824881043487793
[169.19712, 156.40928]
1.0817588317010347
[169.58272, 156.633408]
1.0826727335205526
[169.483968, 156.647616]
1.0819441261078624
[169.6624, 156.62752]
1.0832221566171767
[169.481536, 156.619712]
1.082121361581868
[169.789696, 156.753984]
1.0831603233765337
[169.73568, 156.777216]
1.0826552756237233
[169.899712, 156.649216]
1.0845870559607524
[169.892416, 156.648064]
1.0845484563409606
[169.859584, 156.530688]
1.0851519671337546
[169.862592, 156.492672]
1.0854347991450999
[170.003712, 156.456512]
1.0865876391262002
[170.09376, 156.57056]
1.086371282059667
[170.039488, 156.478848]
1.0866611696936828
[169.979584, 156.3824]
1.0869483010875904
[169.86016, 156.333312]
1.0865256919779196
[170.033024, 156.346496]
1.0875397169118521
[170.362496, 156.558656]
1.08817040432437
[170.402112, 156.575488]
1.0883064404052822
[170.74752, 156.736]
1.089395671702736
[170.795904, 157.125632]
1.087002176704053
[171.037504, 156.745344]
1.0911807626005148
[171.085696, 156.706112]
1.091761475136337
[171.16864, 156.56864]
1.0932498359824805
[171.001408, 156.448704]
1.093019012800515
[170.724224, 156.426304]
1.0914035532029192
[170.457152, 156.0928]
1.0920244367453207
[170.097792, 155.966848]
1.0906022284940964
[169.801088, 155.80032]
1.089863538149344
[169.781056, 155.858496]
1.0893282070423675
[169.694208, 155.737152]
1.0896193093347437
[169.897984, 155.730624]
1.0909735004978853
[169.811712, 155.718336]
1.0905055651249702
[169.728512, 155.622528]
1.0906423008370614
[169.82944, 155.559232]
1.0917348833401286
[169.656832, 155.50048]
1.0910373524248929
[169.796992, 155.540288]
1.0916592362230935
[169.882944, 155.71136]
1.0910118824984896
[169.800768, 155.608448]
1.0912053309599232
[169.867072, 155.824192]
1.0901200244952978
[170.225344, 156.198336]
1.0898025443753767
[170.151104, 156.090944]
1.090076718352091
[170.59744, 156.448768]
1.0904364552106924
[170.832704, 156.25952]
1.0932626952905014
[171.296832, 156.511936]
1.0944649742240746
[171.742784, 156.80512]
1.0952626036700843
[171.706816, 156.905216]
1.0943346587024871
[171.254464, 156.801984]
1.092170262335456
[170.749696, 157.258304]
1.0857912851457434
[170.519936, 156.672832]
1.0883822920875013
[170.229824, 156.570944]
1.087237642253725
[169.92416, 156.549184]
1.0854362549727503
[169.371584, 156.223936]
1.0841589857267455
[168.618048, 155.920384]
1.0814368440754993
[168.369664, 155.850816]
1.0803258418614887
[168.097024, 155.66464]
1.0798664616447256
[168.19008, 155.765376]
1.0797655057822348
[167.975232, 155.699072]
1.0788454281859818
[168.270016, 155.758016]
1.080329734040783
[167.814144, 155.65536]
1.0781134938109422
[167.77344, 155.605376]
1.0781982236911916
[168.025088, 155.78016]
1.0786038992385167
[168.144832, 155.902592]
1.0785249292070782
[168.502016, 155.867776]
1.081057421387728
[168.416576, 155.628928]
1.0821675517806046
[168.628096, 155.58784]
1.083812822390233
[168.662656, 155.613376]
1.083857058663132
[168.851904, 155.789312]
1.0838478059393446
[168.537152, 155.58144]
1.083272863395531
[168.535104, 155.724352]
1.0822655662744385
[168.782784, 155.87392]
1.0828160605699786
[168.759232, 155.68672]
1.0839667763570329
[168.942016, 155.88256]
1.0837775309822983
[169.059456, 155.776704]
1.0852678973102423
[169.101568, 155.877312]
1.084837593299017
[169.117952, 155.960832]
1.0843616940950918
[169.158336, 155.90464]
1.0850115557817908
[169.74368, 156.172288]
1.0869001291701637
[169.798208, 155.997696]
1.0884661270894667
[170.02048, 156.353792]
1.0874087403009707
[169.81632, 156.392384]
1.085834972628846
[170.00416, 156.66144]
1.085169139259795
[170.134912, 156.839808]
1.0847686832159347
[170.2032, 156.732864]
1.085944553402661
[170.036352, 156.419968]
1.0870501648485185
[170.089024, 156.3216]
1.0880711558735325
[169.950144, 156.185088]
1.0881329720798953
[169.832512, 156.367936]
1.0861082926873193
[169.760128, 156.125952]
1.0873280567730341
[169.59648, 156.054464]
1.0867774983995333
[169.475264, 156.094976]
1.0857188895048102
[169.480768, 156.045824]
1.086096145706533
[169.182464, 155.976384]
1.0846671762822762
[169.160384, 156.039424]
1.0840874675364092
[168.912832, 155.956608]
1.0830758258091893
[169.28896, 156.16448]
1.0840426709069821
[169.336448, 156.264064]
1.0836557277814047
[169.378752, 156.410688]
1.082910344336571
[168.986176, 156.351296]
1.0808108427831644
[168.861376, 156.256768]
1.080665997136201
[168.853056, 156.282368]
1.080435740518086
[168.613568, 156.348032]
1.0784502103614582
[168.364224, 156.212032]
1.0777929321090964
[168.255552, 156.316672]
1.0763762421963536
[168.435072, 156.407872]
1.0768963853686342
[168.24544, 155.981696]
1.078622968684736
[168.2288, 156.023872]
1.078224747556579
[168.291968, 155.818112]
1.0800539541898697
[168.224, 155.736384]
1.0801843196770256
[168.34464, 155.61888]
1.0817751676403276
[168.68128, 155.704832]
1.0833400468907732
[169.005632, 155.756672]
1.0850619099000778
[169.187904, 156.03648]
1.0842842904428502
[169.263552, 156.065984]
1.084564026456912
[169.45248, 156.265344]
1.0843893832275442
[169.460608, 156.118016]
1.0854647806951376
[170.013952, 156.27616]
1.0879071510331453
[170.148416, 156.279808]
1.088742161751312
[170.209472, 156.420864]
1.0881506958048768
[170.3088, 156.317952]
1.089502503205774
[170.443904, 156.398016]
1.0898086072907727
[170.467968, 156.351616]
1.0902859360276775
[170.498112, 156.388736]
1.0902198992132017
[170.369984, 156.033664]
1.0918796600200327
[170.237376, 155.995072]
1.0912997046470803
[170.581056, 156.179264]
1.0922132146813037
[170.491136, 156.158208]
1.0917846598239653
[170.430208, 156.222272]
1.0909469297693992
[169.998208, 156.040768]
1.0894473936452298
[169.90304, 156.195072]
1.08776184692946
[169.70272, 156.097152]
1.0871608983615537
[169.7072, 156.024704]
1.0876944204938213
[169.654016, 155.954624]
1.0878421661931614
[169.709568, 156.103296]
1.0871619776689403
[169.57792, 155.903488]
1.0877108791818693
[169.59584, 155.936448]
1.087595890346303
[169.566656, 156.249728]
1.0852284875657512
[169.420416, 156.008896]
1.0859663797633694
[169.582976, 156.135616]
1.0861261533050859
[169.58464, 156.013568]
1.0869864856882192
[169.796096, 155.995648]
1.0884668782554756
[169.797568, 155.952448]
1.0887778305345999
[169.901184, 155.983232]
1.0892272318091218
[169.875328, 155.847488]
1.0900100487984765
[169.906816, 155.929216]
1.089640673881154
[169.954944, 155.8688]
1.0903717998727136
[169.976704, 155.9712]
1.0897954494163025
[170.083712, 156.050496]
1.0899274040115834
[170.23808, 156.20928]
1.0898077246114954
[170.135808, 156.217472]
1.089095898312834
[170.328704, 156.277056]
1.0899149776663313
[170.242304, 156.127296]
1.0904070483613575
[170.6496, 156.137536]
1.0929441079433966
[170.54944, 156.248576]
1.0915263637346684
[170.294144, 156.220544]
1.0900880232500023
[170.06176, 156.202496]
1.0887262646558478
[169.938432, 156.308992]
1.0871954954453293
[169.99136, 156.062848]
1.0892493772765186
[170.078592, 156.245504]
1.0885343107216703
[170.147072, 156.181632]
1.0894179412851825
[170.107392, 156.309632]
1.0882719754595802
[170.021952, 156.233088]
1.0882582823940599
[170.055872, 156.29472]
1.0880461732808375
[170.157376, 156.298176]
1.0886715402232203
[170.224704, 156.305792]
1.0890492400946985
[170.23168, 156.40032]
1.088435624684144
[170.27072, 156.332032]
1.0891607933555165
[169.96832, 156.23808]
1.087880240207765
[169.757888, 156.272704]
1.086292638796344
[169.661056, 156.364032]
1.0850388918085714
[169.945088, 156.37376]
1.0867877577414522
[170.12864, 156.397952]
1.0877932723824926
[170.058624, 156.4016]
1.0873202320180868
[170.155648, 156.411328]
1.0878729192811407
[169.942336, 156.22624]
1.0877963650664577
[170.07776, 156.473472]
1.0869430953765762
[170.101056, 156.298176]
1.0883112033245992
[170.166144, 156.302464]
1.0886977699852514
[170.410368, 156.456768]
1.0891850201072797
[169.95456, 156.236544]
1.0878028638421493
[169.936128, 156.081024]
1.0887686641522802
[169.919232, 156.18816]
1.0879136549146875
[170.192256, 156.301056]
1.0888746394650077
[170.186432, 156.321984]
1.0886916071894277
[170.217472, 156.38784]
1.0884316325361356
[169.965312, 156.333632]
1.0871960807511976
[169.916928, 156.528512]
1.0855334010969198
[169.723776, 156.239616]
1.086304359580607
[169.814848, 156.28192]
1.086593049279149
[169.79904, 156.309824]
1.0862979411965814
[169.852608, 156.387648]
1.0860998945389855
[169.853376, 156.433856]
1.0857839878344493
[169.917184, 156.343104]
1.0868223775319183
[170.13344, 156.26688]
1.0887363976294915
[170.245312, 156.408704]
1.088464437375557
[170.006784, 156.219328]
1.088257043328211
[169.987456, 156.251968]
1.0879060160061471
[170.133888, 156.30592]
1.08846733380284
[169.982016, 156.297216]
1.0875562620386021
[170.093376, 156.292288]
1.0883030645760332
[170.134592, 156.371712]
1.088013872995136
[169.956416, 156.26656]
1.0876057935875723
[169.728768, 156.173376]
1.0867970735293575
[169.75808, 156.32256]
1.085947415395449
[170.046912, 156.417344]
1.0871359124982967
[169.971648, 156.366912]
1.0870052099001608
[169.959936, 156.396544]
1.0867243716075976
[170.001216, 156.32256]
1.087502763516667
[170.03008, 156.219648]
1.0884039375123928
[170.08576, 156.280256]
1.0883381199477942
[170.120576, 156.284352]
1.0885323695106723
[170.06816, 156.197376]
1.08880292585709
[170.204608, 156.340032]
1.0886821872980044
[169.941568, 156.181184]
1.0881052611305597
[170.015168, 156.329792]
1.0875417015843019
[169.993024, 156.364224]
1.0871606026708514
[170.161408, 156.30336]
1.0886612290356394
[170.33632, 156.340544]
1.0895210905751997
[170.3136, 156.298048]
1.0896719580272687
[170.302272, 156.340672]
1.089302417735546
[170.248704, 156.260864]
1.0895159519916644
[170.288064, 156.238592]
1.089923186199732
[170.045312, 156.283584]
1.0880561326261882
[169.874368, 156.317888]
1.0867237919693489
[169.788032, 156.33344]
1.0860634295516045
[169.939456, 156.410752]
1.0864947187262421
[169.87616, 156.345984]
1.0865399651071306
[169.901248, 156.245312]
1.0874006126980629
[169.702464, 156.250048]
1.086095435951482
[170.102592, 156.298368]
1.088319693779528
[169.983168, 156.220992]
1.0880942812090197
[170.010048, 156.189568]
1.0884852949974226
[169.90272, 156.19232]
1.0877789637800372
[169.89344, 156.369664]
1.086485931184197
[169.86368, 156.420544]
1.0859422659980007
[169.7312, 156.38528]
1.0853400013095862
[169.85184, 156.441664]
1.0857199780232458
[169.672256, 156.301504]
1.0855446151049193
[170.033792, 156.337472]
1.087607403553257
[170.270208, 156.433536]
1.0884508037969556
[170.396416, 156.300096]
1.0901875325783548
[170.448064, 156.343744]
1.0902135233501893
[170.189696, 156.199616]
1.0895653930416833
[170.22752, 156.235584]
1.0895566531117522
[170.24544, 156.235584]
1.0896713516941186
[170.125888, 156.113216]
1.0897596780018932
[170.238528, 156.198336]
1.0898869498840242
[170.244416, 156.208896]
1.0898509646979389
[170.200192, 156.213568]
1.0895352700733394
[170.074496, 156.193344]
1.0888715974990586
[169.863808, 156.177152]
1.0876354564334736
[169.960384, 156.206272]
1.0880509586708529
[169.59488, 156.01856]
1.0870173394755085
[169.709568, 156.157632]
1.0867836930314105
[169.806144, 156.026496]
1.0883160767771134
[170.00032, 156.034816]
1.0895024864194411
[170.211136, 156.214976]
1.0895955071554728
[170.063936, 156.039232]
1.0898793452149265
[170.00032, 156.125056]
1.0888727559527664
[169.937856, 156.251392]
1.0875925892551408
[169.847808, 156.04]
1.0884889002819789
[169.852224, 156.055104]
1.088411847138303
[169.876544, 156.237952]
1.0872937197743093
[169.881984, 156.42016]
1.086061950070886
[169.721024, 156.309248]
1.0858028310647365
[169.869312, 156.4208]
1.0859764941746877
[169.831296, 156.187712]
1.0873537605826507
[169.850368, 156.312704]
1.086606294009219
[169.80128, 156.211584]
1.086995443308481
[169.796736, 156.020032]
1.0883008663913107
[169.760256, 156.166784]
1.0870445792109031
[169.591104, 156.053568]
1.0867492885519925
[169.641792, 156.226624]
1.0858699218898824
[169.665408, 156.103104]
1.0868804248761128
[169.698176, 156.177792]
1.0865704645126497
[169.840448, 156.341184]
1.0863449006501065
[169.620224, 156.220416]
1.085775011634843
[169.683584, 156.26848]
1.08584651236129
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 171, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:34:56] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:34:56] "GET /stream.mjpg HTTP/1.1" 200 -
[202.41979591836736, 175.03367346938776]
1.1564620218850017
[202.28510204081633, 175.02224489795918]
1.1557679548605484
[202.1369387755102, 174.94979591836736]
1.1553996831744149
[201.87510204081633, 174.7273469387755]
1.1553721016067016
[201.8795918367347, 174.60897959183674]
1.1561810412536935
[201.9295918367347, 174.51489795918368]
1.1570908512576552
[201.49244897959184, 174.5865306122449]
1.1541122231651693
[201.434693877551, 174.6122448979592]
1.1536115007012622
[201.3338775510204, 174.39551020408163]
1.1544670921597402
[201.17408163265307, 174.55530612244897]
1.152494794352062
[201.29979591836735, 174.5234693877551]
1.153425362356972
[201.08122448979591, 174.42714285714285]
1.1528092543170472
[201.5987755102041, 174.47918367346938]
1.1554316753767482
[201.51857142857142, 174.53102040816327]
1.1546289648527481
[201.69918367346938, 174.34408163265306]
1.1569029575575391
[201.44775510204082, 174.34591836734694]
1.155448644788978
[201.6826530612245, 174.58938775510205]
1.1551827728734945
[201.75714285714287, 174.38714285714286]
1.1569496440596048
[201.71571428571428, 174.27081632653062]
1.1574841877584383
[201.8704081632653, 174.3161224489796]
1.1580707815615308
[201.88673469387754, 174.71510204081633]
1.155519656490333
[201.98142857142858, 174.66183673469388]
1.1564142021375416
[202.0069387755102, 174.73591836734693]
1.156069917753438
[202.07836734693876, 174.72938775510204]
1.1565219219457727
[202.24795918367346, 174.74428571428572]
1.1573938361243892
[202.04448979591837, 174.6695918367347]
1.156723890353916
[201.99571428571429, 174.84142857142857]
1.155308075072106
[201.90081632653062, 174.6538775510204]
1.15600534701871
[202.14265306122448, 174.7869387755102]
1.1565089158112032
[201.97469387755103, 174.7430612244898]
1.1558381343570328
[202.06020408163266, 174.83857142857144]
1.1556958080281636
[202.08204081632653, 174.66918367346938]
1.1569415770219855
[202.09714285714287, 174.85877551020408]
1.1557735221893353
[202.07877551020408, 174.73265306122448]
1.1565026454408485
[201.91204081632654, 174.6342857142857]
1.1561993109799138
[201.98979591836735, 174.7642857142857]
1.1557841757702796
[202.14489795918368, 174.7608163265306]
1.1566946310292319
[202.07265306122449, 174.6491836734694]
1.157020312439748
[202.05448979591836, 174.57673469387754]
1.1573964317194005
[202.0434693877551, 174.55959183673468]
1.1574469627353736
[202.02102040816325, 174.7887755102041]
1.1558008791952967
[202.01877551020408, 174.62938775510204]
1.1568429466952754
[202.02530612244897, 174.6865306122449]
1.156501908958788
[201.96816326530612, 174.59591836734694]
1.1567748270057976
[201.89530612244897, 174.72489795918366]
1.155503929208832
[201.96673469387756, 174.70897959183674]
1.1560180545139789
[201.8504081632653, 174.63571428571427]
1.155836931688705
[201.85102040816327, 174.64061224489797]
1.15580802090357
[201.93591836734694, 174.6269387755102]
1.1563846894604475
[201.90938775510205, 174.4504081632653]
1.157402782148485
[202.02428571428572, 174.52693877551022]
1.1575535967782296
[201.77877551020407, 174.5326530612245]
1.156109025853299
[201.7226530612245, 174.68714285714285]
1.1547653122141393
[201.87918367346938, 174.41040816326532]
1.1574950474543388
[201.73142857142858, 174.53367346938776]
1.1558309898680448
[201.84, 174.46102040816328]
1.1569346523812698
[201.8248979591837, 174.66714285714286]
1.1554829068467254
[201.59938775510204, 174.45632653061224]
1.1555865686517648
[201.69326530612244, 174.49448979591835]
1.1558718303484234
[201.90142857142857, 174.4222448979592]
1.1575440316660601
[201.9208163265306, 174.50551020408165]
1.1571028106240724
[202.09591836734694, 174.73673469387754]
1.1565737377512526
[202.1169387755102, 174.52102040816325]
1.1581237509545075
[202.16510204081632, 174.81020408163266]
1.1564834164166384
[202.15489795918367, 174.50857142857143]
1.1584238888914877
[202.25326530612244, 174.61265306122448]
1.1582967314241903
[201.99530612244897, 174.50183673469388]
1.157554040130564
[201.83612244897958, 174.4938775510204]
1.156694580243737
[201.83591836734695, 174.7112244897959]
1.155254443191973
[201.8665306122449, 174.63122448979593]
1.155958971266564
[201.8369387755102, 174.74448979591835]
1.1550403621380723
[201.84020408163266, 174.67102040816326]
1.1555448843773952
[201.97183673469388, 174.68897959183673]
1.1561796125125003
[201.8473469387755, 174.49897959183673]
1.1567250846446677
[202.08938775510205, 174.75469387755103]
1.1564175088578976
[202.03244897959183, 174.46571428571428]
1.158006602080755
[201.9426530612245, 174.57897959183674]
1.1567409405952747
[202.0183673469388, 174.45265306122448]
1.1580125827954022
[202.07061224489797, 174.40020408163267]
1.1586604116031507
[202.04795918367347, 174.41714285714286]
1.15841800796589
[202.035306122449, 174.35061224489795]
1.158787477262565
[201.93428571428572, 174.50102040816327]
1.1572097701317459
[202.01714285714286, 174.6530612244898]
1.1566767936433746
[201.83, 174.40897959183673]
1.1572225264566982
[201.80326530612246, 174.51897959183674]
1.1563399337888516
[202.08857142857144, 174.56]
1.1577026319235302
[202.06163265306122, 174.68836734693878]
1.1566976995769727
[202.2051020408163, 174.65591836734694]
1.1577340403405412
[202.12938775510204, 174.62551020408162]
1.1575020598014412
[202.2118367346939, 174.64408163265307]
1.1578510696974371
[201.92591836734695, 174.45367346938775]
1.1574758751226863
[201.81367346938777, 174.46285714285713]
1.1567715717514284
[201.6281632653061, 174.73551020408163]
1.1539049105119807
[201.72142857142856, 174.4973469387755]
1.1560143011355064
[201.7638775510204, 174.51142857142858]
1.1561642650150976
[201.75040816326532, 174.4365306122449]
1.156583471679659
[201.61448979591836, 174.38061224489795]
1.1561749164681994
[201.6891836734694, 174.28714285714287]
1.1572235356384666
[201.91061224489795, 174.43857142857144]
1.157488338681882
[202.04530612244898, 174.63244897959183]
1.156974590364135
[202.1818367346939, 174.4965306122449]
1.1586582038354076
[202.17551020408163, 174.624693877551]
1.1577715941243087
[202.2316326530612, 174.4965306122449]
1.1589435729381206
[202.15448979591838, 174.4604081632653]
1.1587413552691916
[202.2034693877551, 174.55326530612246]
1.158405539037847
[202.1334693877551, 174.32183673469387]
1.1595418748104902
[202.20061224489797, 174.70285714285714]
1.1573972833172128
[202.02489795918368, 174.26408163265307]
1.1593031453552782
[202.0748979591837, 174.28836734693877]
1.1594284864516116
[201.85061224489795, 174.30163265306123]
1.158053479892937
[201.95326530612246, 174.53163265306122]
1.1571155453955486
[202.47469387755103, 174.69122448979593]
1.1590433032277359
[201.78061224489795, 170.57102040816326]
1.182971244248012
[201.0591836734694, 166.3265306122449]
1.2088220858895704
[201.38632653061225, 167.7261224489796]
1.2006855198829969
[200.86551020408163, 167.17714285714285]
1.2015129985546311
[189.21367346938774, 168.03163265306122]
1.1260598405305122
[191.22285714285715, 168.40673469387755]
1.1354822447597108
[183.3769387755102, 160.74428571428572]
1.1407991143240563
[182.25673469387755, 148.06938775510204]
1.230887339085371
[179.96979591836734, 140.7077551020408]
1.279032529428487
[188.32530612244898, 145.16734693877552]
1.297297981218017
[186.43142857142857, 148.9142857142857]
1.2519378357636224
[186.57183673469387, 150.16714285714286]
1.2424278253211727
[188.6734693877551, 150.34918367346938]
1.254901854322794
[189.20448979591836, 150.3673469387755]
1.2582817589576547
[189.2526530612245, 150.29285714285714]
1.259225865147637
[189.00897959183675, 149.99693877551022]
1.2600855799778228
[188.86, 150.02163265306123]
1.2588851131673529
[189.0361224489796, 150.23591836734693]
1.2582618358065412
[189.96816326530612, 150.53224489795917]
1.261976551230464
[191.33959183673468, 151.37673469387755]
1.2639960309863483
[192.47387755102042, 151.57530612244898]
1.269823446013903
[193.86204081632653, 151.37714285714284]
1.2806559640201256
[202.04816326530613, 150.75326530612244]
1.3402572929682373
[208.095306122449, 149.79673469387754]
1.3891845276047543
[212.58632653061224, 149.49673469387756]
1.4220131761802182
[215.2969387755102, 148.93591836734694]
1.4455676047498855
[217.22061224489795, 148.23183673469387]
1.4654113247863247
[218.38061224489795, 148.16816326530613]
1.4738700098068382
[218.9161224489796, 148.2016326530612]
1.4771505450379243
[219.0177551020408, 148.15489795918367]
1.4783024936669977
[218.88122448979593, 148.03061224489795]
1.478621355207831
[218.27244897959184, 147.87081632653062]
1.4761022790162952
[217.96510204081633, 147.8712244897959]
1.474019727589781
[217.76897959183674, 147.56938775510204]
1.4757056521318233
[218.36061224489796, 147.45755102040818]
1.4808371001270513
[218.5661224489796, 147.48877551020408]
1.481916991261874
[218.8526530612245, 147.80673469387756]
1.4806676672378298
[218.78285714285715, 147.85979591836735]
1.4796642710344743
[217.8595918367347, 148.08285714285714]
1.4712006240301212
[215.32020408163265, 148.45938775510203]
1.4503643544376186
[201.90102040816328, 149.095306122449]
1.3541742235825052
[189.56244897959184, 148.3330612244898]
1.2779514385717745
[185.4430612244898, 141.3669387755102]
1.3117852224201603
[194.85142857142858, 149.9395918367347]
1.2995328731026372
[202.46510204081633, 157.61489795918368]
1.2845556141098233
[204.26877551020408, 164.26183673469387]
1.2435558957016113
[205.33591836734695, 168.99755102040817]
1.2150230410294558
[204.27836734693878, 170.78428571428572]
1.1961192242750431
[203.8869387755102, 171.28142857142856]
1.1903622037486938
[203.87897959183672, 172.77]
1.180060077512512
[204.7657142857143, 175.8718367346939]
1.1642893944105865
[205.33857142857144, 177.86408163265307]
1.1544690166992913
[205.25489795918367, 178.17061224489797]
1.1520132044955762
[205.16122448979593, 178.20673469387756]
1.1512540468362245
[204.4334693877551, 177.58612244897958]
1.15117930707952
[204.20979591836735, 177.13897959183674]
1.1528224696162703
[203.54795918367347, 176.5108163265306]
1.1531755584152212
[203.5265306122449, 176.24979591836734]
1.154761794484637
[203.05775510204083, 175.30469387755102]
1.158313280783429
[202.55897959183673, 172.67163265306124]
1.1730877647912576
[195.77877551020407, 164.24775510204083]
1.191972306644765
[189.78591836734694, 164.45795918367347]
1.1540087163272297
[189.99448979591835, 164.26]
1.1566692426392204
[184.32061224489797, 158.09775510204082]
1.1658648291744065
[191.76734693877552, 151.17877551020408]
1.2684806203224728
[198.0612244897959, 143.68857142857144]
1.3784062470706202
[197.7322448979592, 147.05510204081634]
1.3446132922547427
[201.9726530612245, 156.88877551020408]
1.2873620334176687
[208.36857142857144, 161.31163265306122]
1.2917144783768775
[207.72897959183675, 157.5661224489796]
1.3183606752720594
[207.60816326530613, 153.22816326530614]
1.3548955938722833
[208.1095918367347, 150.9461224489796]
1.378701144887485
[210.28326530612244, 150.15163265306123]
1.4004727194142519
[211.184693877551, 149.36612244897958]
1.413872773926279
[211.77326530612245, 149.0687755102041]
1.4206413421006876
[211.92673469387756, 148.63816326530613]
1.4257895148745001
[212.13816326530613, 147.8069387755102]
1.4352381899167974
[211.69755102040816, 147.71714285714285]
1.4331278477619942
[211.75020408163266, 147.84204081632652]
1.4322732756692886
[211.7961224489796, 147.96428571428572]
1.4314002965414985
[211.24102040816325, 148.95061224489797]
1.4181950461596637
[209.8495918367347, 149.55163265306123]
1.4031915808204933
[205.58244897959185, 150.21591836734694]
1.368579649973236
[199.95489795918368, 150.71714285714285]
1.3266898122445887
[195.01938775510203, 151.53775510204082]
1.286935969348246
[194.94489795918366, 152.0565306122449]
1.2820554117225467
[195.29, 152.11897959183673]
1.283797725464627
[195.44102040816327, 152.08]
1.285119808049469
[196.01265306122448, 151.83612244897958]
1.2909487538256204
[195.96673469387756, 151.77816326530612]
1.291139189445391
[196.05408163265307, 151.89857142857142]
1.2906907536312497
[196.13102040816327, 151.56571428571428]
1.294032897429821
[196.3165306122449, 152.0626530612245]
1.291023973738
[196.9108163265306, 151.9204081632653]
1.2961445977351191
[197.27510204081634, 152.23489795918368]
1.2958599157317303
[197.32326530612244, 152.05714285714285]
1.2976915230579267
[198.1642857142857, 151.35489795918366]
1.3092690648684873
[198.61102040816326, 151.0530612244898]
1.314842736705577
[195.99367346938774, 151.27285714285713]
1.2956301425859744
[188.95408163265307, 149.99448979591835]
1.2597401537199326
[185.14510204081634, 142.18408163265306]
1.3021507043183456
[186.23816326530613, 145.3461224489796]
1.2813424956051425
[194.05163265306123, 161.2622448979592]
1.2033296000303726
[200.08265306122448, 166.04183673469387]
1.205013489346796
[201.20285714285714, 168.57877551020408]
1.1935242531802488
[200.61204081632653, 169.56102040816327]
1.1831259350375338
[202.0308163265306, 171.87204081632652]
1.17547226045005
[203.50204081632654, 175.37448979591838]
1.1603856470410259
[203.935306122449, 175.91061224489795]
1.159312127448774
[203.77020408163264, 175.95367346938775]
1.1580900816889417
[203.59163265306123, 176.04510204081632]
1.156474280129976
[203.51530612244898, 176.2038775510204]
1.1549990213099621
[203.2418367346939, 175.9318367346939]
1.1552305739931745
[202.8165306122449, 175.5422448979592]
1.1553716356432604
[202.70285714285714, 175.22795918367348]
1.1567951717704168
[202.49408163265306, 175.01530612244898]
1.157007841879719
[202.4, 174.77775510204083]
1.1580421082867922
[201.85877551020408, 174.40510204081633]
1.1574132473656804
[201.95183673469387, 174.20489795918368]
1.1592776041349384
[201.94061224489795, 174.33632653061224]
1.1583392644758899
[201.9222448979592, 174.2608163265306]
1.1587357912957121
[201.9726530612245, 174.17285714285714]
1.1596103800235984
[201.99510204081633, 174.40020408163267]
1.1582274407561308
[201.69857142857143, 174.17979591836735]
1.1579906289653783
[201.8030612244898, 174.21795918367346]
1.1583367304385312
[201.56224489795918, 173.87081632653062]
1.159264384653396
[201.7173469387755, 174.01734693877552]
1.1591795328872911
[201.6534693877551, 173.8169387755102]
1.16014854943566
[201.60387755102042, 173.93571428571428]
1.1590712027080143
[201.77102040816325, 173.89673469387756]
1.160292174337573
[201.48265306122448, 174.0122448979592]
1.1578647995684093
[201.68285714285713, 174.05959183673468]
1.1587000464302633
[201.66857142857143, 174.0381632653061]
1.1587606283866898
[201.87755102040816, 174.01979591836735]
1.160083828135903
[202.1757142857143, 174.19]
1.1606620029032337
[202.09551020408162, 173.84775510204082]
1.1624855902537288
[202.14816326530612, 173.93020408163267]
1.1622372567931307
[202.05755102040817, 173.86428571428573]
1.1621567373097712
[201.97591836734694, 174.0973469387755]
1.1601320865525622
[201.92530612244897, 173.82673469387754]
1.1616470071652396
[201.92265306122448, 173.9530612244898]
1.1607881553785326
[201.8773469387755, 173.88204081632654]
1.161001711223419
[201.6457142857143, 173.86673469387756]
1.1597716759375876
[201.7869387755102, 173.80632653061224]
1.1609873058330231
[201.65204081632652, 173.79020408163265]
1.1603187986453287
[201.66285714285715, 173.89061224489797]
1.1597110076238404
[201.69448979591837, 173.85]
1.1601638757314834
[201.65857142857143, 173.89408163265307]
1.1596632245056515
[201.54632653061225, 173.94204081632654]
1.1586981823642875
[201.74224489795918, 173.83408163265307]
1.1605448310434416
[201.61163265306124, 173.90775510204082]
1.159302140003849
[201.64510204081634, 173.80591836734695]
1.1601739683836887
[201.59591836734694, 173.7538775510204]
1.1602383855183382
[201.94571428571427, 173.8638775510204]
1.1615162225198459
[201.90775510204082, 173.81571428571428]
1.1616196839955995
[202.18979591836734, 173.90795918367348]
1.1626253155258057
[201.6795918367347, 173.63877551020408]
1.1614893692041888
[201.6608163265306, 173.83061224489796]
1.1600995573922537
[201.4538775510204, 173.60795918367347]
1.1603954017908047
[201.37020408163266, 173.74877551020407]
1.1589733711234496
[201.5183673469388, 173.75306122448978]
1.1597975076052105
[201.5734693877551, 173.64877551020408]
1.1608113492047636
[201.5491836734694, 173.83836734693878]
1.159405640707765
[201.43428571428572, 173.82857142857142]
1.1588099934253782
[201.46693877551022, 173.75183673469388]
1.159509692453699
[201.34551020408162, 173.68551020408162]
1.1592533537627825
[201.58102040816325, 173.7642857142857]
1.1600831527579585
[201.46285714285713, 173.75775510204082]
1.1594467080018744
[201.56979591836733, 173.83163265306123]
1.1595691350415307
[201.38591836734693, 173.6218367346939]
1.1599112309535031
[201.53428571428572, 173.76244897959182]
1.1598264578899649
[201.51795918367347, 173.78061224489795]
1.1596112856345968
[201.59510204081633, 173.8481632653061]
1.159604440187074
[201.52673469387756, 173.78285714285715]
1.1596468029537212
[201.42938775510203, 173.91591836734693]
1.1581998338394814
[201.6469387755102, 173.90489795918367]
1.1595242062868045
[201.62510204081633, 173.7730612244898]
1.1602782423240257
[201.67142857142858, 173.77326530612245]
1.1605434714952279
[201.70673469387756, 173.81897959183672]
1.160441369334506
[201.73714285714286, 173.89612244897958]
1.1601014445640196
[201.54102040816326, 173.9242857142857]
1.1587859601116601
[201.83714285714285, 174.0230612244898]
1.1598298606916981
[201.64265306122448, 173.94918367346938]
1.159204365337754
[201.94591836734693, 173.88857142857142]
1.1613524494926377
[201.79938775510203, 174.02102040816325]
1.159626505360014
[201.79897959183674, 173.84918367346938]
1.1607703604226511
[201.8365306122449, 173.82163265306122]
1.161170376388651
[201.96020408163264, 173.91469387755103]
1.1612601533475242
[202.12938775510204, 173.9238775510204]
1.162171581045895
[202.0104081632653, 173.84061224489795]
1.1620438144723233
[202.03938775510204, 173.94897959183675]
1.1614864785592771
[201.83142857142857, 173.87591836734694]
1.160778504962488
[201.66061224489795, 174.04265306122448]
1.1586850044969037
[201.85020408163265, 173.77612244897958]
1.1615531595308533
[201.66204081632654, 173.9230612244898]
1.159489945706699
[201.6777551020408, 173.79877551020408]
1.160409528260456
[201.64244897959185, 174.05102040816325]
1.1585249457700653
[201.72918367346938, 173.9387755102041]
1.1597712073213655
[201.58428571428573, 173.9038775510204]
1.1591707358862333
[201.66632653061225, 173.9551020408163]
1.1593010159787889
[201.8181632653061, 173.89836734693878]
1.1605523751851303
[201.7473469387755, 173.9069387755102]
1.1600879663531045
[201.89714285714285, 173.92020408163265]
1.1608607747629982
[201.76857142857142, 173.90244897959184]
1.160239965638723
[201.77448979591836, 174.20265306122448]
1.1582744938161396
[201.71367346938774, 173.9618367346939]
1.1595283037682436
[201.71571428571428, 174.12428571428572]
1.158458244111349
[201.85061224489795, 173.9634693877551]
1.160304591275907
[201.6661224489796, 174.19530612244898]
1.157701243150721
[201.77816326530612, 174.2226530612245]
1.1581626138731695
[201.5408163265306, 173.96836734693878]
1.1584911636527868
[201.26, 173.9108163265306]
1.1572598200109603
[201.4583673469388, 174.06571428571428]
1.1573696070684072
[201.10530612244898, 173.88816326530613]
1.1565209635092693
[201.09081632653061, 173.98530612244897]
1.1557919505283112
[201.2904081632653, 173.76122448979592]
1.158431110014916
[201.36408163265307, 173.70755102040818]
1.1592131743829355
[201.23897959183674, 173.9265306122449]
1.157034403454426
[201.13857142857142, 173.6518367346939]
1.158286461063305
[201.38102040816327, 173.75020408163266]
1.159026094228637
[201.03367346938776, 173.76551020408164]
1.1569250608666852
[201.07367346938776, 173.6830612244898]
1.1577045686078442
[201.18816326530612, 173.91163265306122]
1.1568413233556334
[201.15795918367348, 173.86081632653062]
1.1570057212079097
[201.01857142857142, 173.8904081632653]
1.1560072435958373
[201.22714285714287, 173.92755102040817]
1.1569595597510105
[201.22183673469388, 173.88326530612244]
1.1572237062631745
[201.1830612244898, 174.02693877551022]
1.1560455101954656
[201.2826530612245, 173.7683673469388]
1.1583388630184446
[201.38714285714286, 173.78551020408165]
1.1588258573493715
[201.0969387755102, 173.86163265306124]
1.156649317660537
[200.89020408163265, 173.89755102040817]
1.1552215824940322
[200.80938775510205, 173.86204081632653]
1.154992698879243
[200.70734693877552, 173.64795918367346]
1.1558289995592772
[200.7465306122449, 173.6204081632653]
1.156238098596516
[200.93, 173.7704081632653]
1.1562958395725067
[200.80428571428573, 173.70979591836735]
1.155975600873143
[200.8677551020408, 173.67265306122448]
1.1565882800859228
[200.7726530612245, 173.61816326530612]
1.1564035080501547
[200.77326530612245, 173.7704081632653]
1.1553938753339794
[200.87, 173.58244897959185]
1.157202247006069
[200.72897959183675, 173.60061224489795]
1.1562688460376447
[200.89142857142858, 173.81224489795918]
1.1557956039827166
[200.96755102040817, 173.86979591836734]
1.155850847807766
[200.88857142857142, 173.68102040816328]
1.1566524134673344
[200.85857142857142, 173.66918367346938]
1.1565585049689828
[200.80897959183673, 173.77836734693878]
1.15554647369274
[200.99469387755101, 173.8357142857143]
1.156233600807706
[200.80510204081634, 173.5930612244898]
1.1567576527793126
[200.87428571428572, 173.74897959183673]
1.1561177866262613
[200.91591836734693, 173.64612244897958]
1.1570423544953026
[200.94816326530614, 173.7004081632653]
1.1568663850025613
[201.0257142857143, 173.6626530612245]
1.1575644546605135
[200.90510204081633, 173.54714285714286]
1.157639928455598
[200.9822448979592, 173.42122448979592]
1.1589253016131538
[201.02489795918368, 173.41408163265305]
1.1592189980570278
[200.9373469387755, 173.4361224489796]
1.1585668781189804
[201.1169387755102, 173.31204081632654]
1.1604325806113545
[200.8230612244898, 173.58142857142857]
1.1569386361044456
[200.7334693877551, 173.42489795918368]
1.157466267819276
[200.43591836734694, 173.01979591836735]
1.1584565644841867
[200.2426530612245, 172.75530612244899]
1.15911144818494
[200.32102040816326, 172.7430612244898]
1.1596472760653136
[200.39326530612246, 172.6269387755102]
1.1608458490173454
[200.40836734693877, 172.59938775510204]
1.1611186456309703
[200.39591836734695, 172.58836734693878]
1.1611206563215768
[200.80061224489796, 172.66857142857143]
1.1629250800164526
[200.9842857142857, 172.5448979591837]
1.1648231161365865
[200.90795918367348, 170.5365306122449]
1.178093388333818
[201.03632653061226, 172.48816326530613]
1.1655079555887893
[200.83938775510205, 171.3726530612245]
1.1719453726572715
[201.1177551020408, 166.56795918367348]
1.20742161990632
[201.01877551020408, 161.48244897959182]
1.244833582723339
[201.6404081632653, 151.39469387755102]
1.3318855700871084
[202.7426530612245, 146.95795918367347]
1.379596274930773
[203.1226530612245, 144.91387755102042]
1.4016784071609034
[203.74938775510205, 144.08632653061224]
1.4140785781766319
[200.87163265306123, 141.14469387755102]
1.4231610635489127
[189.9430612244898, 140.00367346938776]
1.356700553046713
[191.96632653061224, 141.1530612244898]
1.3599869876382564
[189.5930612244898, 143.37]
1.3224039982178264
[189.39673469387756, 144.08897959183673]
1.3144428895976976
[193.59918367346938, 143.0734693877551]
1.3531452372122215
[194.65775510204082, 145.11591836734695]
1.3413949158167713
[192.90142857142857, 145.86265306122448]
1.3224867676749306
[191.33408163265307, 145.98510204081632]
1.3106411473354145
[191.39530612244897, 146.30346938775511]
1.3082075696727655
[191.38163265306122, 146.1895918367347]
1.3091330938716705
[191.68857142857144, 146.50775510204082]
1.3083851520014265
[192.00183673469388, 146.62081632653062]
1.3095128068793305
[193.6969387755102, 148.15142857142857]
1.3074253866011334
[193.62551020408162, 147.9934693877551]
1.308338205767491
[193.3012244897959, 147.83877551020407]
1.307513700804793
[193.46489795918367, 147.84673469387755]
1.3085503603428261
[192.88387755102042, 147.6791836734694]
1.306100648399454
[192.25285714285715, 147.8073469387755]
1.3006989241373217
[192.22775510204082, 147.97040816326532]
1.2990959306535366
[192.13448979591837, 147.73734693877552]
1.3005140120428835
[195.72591836734694, 147.0865306122449]
1.3306855328808254
[193.18102040816328, 145.4034693877551]
1.3285860455846294
[191.69979591836736, 144.66183673469388]
1.3251580392273044
[192.7691836734694, 139.58816326530612]
1.3809851721244126
[200.1834693877551, 144.0838775510204]
1.3893537069535744
[198.96673469387756, 150.7104081632653]
1.320192394929592
[195.42020408163265, 159.0673469387755]
1.2285375210089424
[197.04714285714286, 165.03979591836736]
1.1939371456482357
[201.38714285714286, 168.02204081632652]
1.1985757456504735
[204.03673469387755, 169.29204081632653]
1.2052352473867765
[203.8248979591837, 170.2208163265306]
1.1974146426850119
[203.68244897959184, 170.5573469387755]
1.1942167994246953
[203.55775510204083, 170.49204081632652]
1.1939428616573162
[203.3730612244898, 170.5191836734694]
1.1926696858573576
[202.84285714285716, 170.53591836734694]
1.1894436027600865
[202.34918367346938, 170.58551020408163]
1.1862038190194875
[202.09755102040816, 170.63387755102042]
1.1843928879831025
[201.9208163265306, 170.89]
1.1815835702880837
[202.02469387755102, 170.99571428571429]
1.1814605688888251
[202.4530612244898, 169.69836734693877]
1.1930171420599818
[197.285306122449, 160.07795918367347]
1.2324326667363605
[201.76877551020408, 148.6457142857143]
1.3573803757461929
[191.63979591836735, 142.99510204081633]
1.3401843362695454
[191.18285714285713, 146.33530612244897]
1.3064711600280596
[198.594693877551, 149.28571428571428]
1.3302993848257005
[220.3012244897959, 148.38571428571427]
1.4846525189453852
[221.43551020408162, 151.5795918367347]
1.4608530575975442
[217.90571428571428, 153.57469387755103]
1.4188907611266737
[220.07591836734693, 150.28428571428572]
1.4643974073626447
[221.1895918367347, 145.88571428571427]
1.5161840411840415
[200.71897959183673, 139.99]
1.433809412042551
[194.99081632653062, 135.1495918367347]
1.4427776930476133
[200.6930612244898, 135.3634693877551]
1.4826235034623336
[197.97979591836736, 132.62673469387755]
1.4927593322367054
[202.61061224489796, 132.5365306122449]
1.528715225220925
[204.1177551020408, 134.70408163265307]
1.5153049011438526
[205.3038775510204, 139.16877551020409]
1.475215089005128
[205.40020408163267, 137.97020408163266]
1.4887287110201257
[205.52061224489796, 137.76183673469387]
1.4918544722998728
[205.39163265306124, 136.82816326530613]
1.5010917909846702
[204.98816326530613, 137.16020408163266]
1.4945163186204127
[204.80775510204083, 137.5873469387755]
1.488565334377568
[204.77469387755102, 138.07265306122449]
1.4830937867670968
[204.86061224489796, 139.06714285714287]
1.4731057821137639
[204.9822448979592, 139.61877551020407]
1.4681567299877802
[205.3842857142857, 140.4604081632653]
1.4622219058024921
[205.5926530612245, 140.8242857142857]
1.4599232796986839
[205.74938775510205, 141.89836734693878]
1.4499771322389408
[206.0081632653061, 142.4534693877551]
1.44614353129271
[206.00040816326532, 143.12673469387755]
1.4392867174945567
[206.14469387755102, 143.70122448979592]
1.4345367940284264
[206.1873469387755, 144.48857142857142]
1.4270149182055216
[206.3522448979592, 145.92795918367347]
1.4140692849560939
[206.82244897959183, 147.35367346938776]
1.4035785067995505
[207.3465306122449, 149.20183673469387]
1.3897049470037164
[205.96081632653062, 150.19]
1.3713350844032932
[200.96163265306123, 139.88061224489795]
1.4366653779097336
[197.08265306122448, 137.29734693877552]
1.4354440013258871
[194.8026530612245, 134.40428571428572]
1.4493782845238474
[205.45448979591836, 129.97591836734694]
1.580711968622131
[205.67408163265307, 130.00755102040816]
1.5820164291870018
[218.08530612244897, 130.54816326530613]
1.6705352313478798
[222.35122448979592, 132.7661224489796]
1.67475874408581
[221.8265306122449, 133.654693877551]
1.6596987668496952
[221.58448979591836, 134.07795918367347]
1.6526541062007787
[221.5142857142857, 134.5708163265306]
1.6460796758250342
[222.12020408163266, 135.62775510204082]
1.6377193880007703
[222.50469387755103, 135.66836734693877]
1.6400631792711822
[222.11836734693878, 135.7473469387755]
1.6362630456941318
[218.79387755102042, 137.96795918367346]
1.5858310787923255
[216.2995918367347, 137.5073469387755]
1.5730038914432773
[213.5687755102041, 138.5234693877551]
1.541751563501359
[210.74020408163264, 138.33408163265307]
1.523414921286386
[206.93285714285713, 136.60836734693876]
1.5147890364381422
[205.36591836734695, 134.86204081632653]
1.522785189399901
[204.36408163265307, 132.38632653061225]
1.5436947832025318
[204.03102040816327, 129.66040816326532]
1.5735799639875592
[207.66918367346938, 128.9904081632653]
1.609958342101058
[213.72387755102042, 129.4257142857143]
1.651324690232834
[217.7957142857143, 128.65591836734694]
1.6928542196080671
[217.875306122449, 127.11836734693877]
1.7139561392242488
[208.46510204081633, 127.87755102040816]
1.6301931056495373
[209.22673469387755, 128.44775510204082]
1.6288858807042965
[200.26673469387754, 133.60510204081632]
1.498945262080606
[205.30795918367346, 135.74326530612245]
1.5124725246639061
[210.09163265306123, 149.03938775510204]
1.40963832324834
[210.59163265306123, 150.08877551020407]
1.4031138033952695
[209.77204081632652, 150.46204081632652]
1.3941858004731005
[209.30142857142857, 147.29285714285714]
1.4209883128849232
[210.3995918367347, 142.15204081632652]
1.4801025059400326
[209.96204081632652, 138.79795918367347]
1.5127170604755111
[209.42734693877551, 141.22040816326532]
1.4829821671146564
[208.4473469387755, 144.7969387755102]
1.4395839352788211
[208.05959183673468, 146.21489795918367]
1.422971220722085
[209.10367346938776, 148.6173469387755]
1.406993717601016
[208.8242857142857, 149.99]
1.3922547217433543
[208.78183673469388, 150.71163265306123]
1.3853067149455576
[209.065306122449, 147.9891836734694]
1.4127066649934428
[202.8877551020408, 143.6077551020408]
1.4127910777372605
[195.61428571428573, 136.61714285714285]
1.4318428977748037
[195.9530612244898, 132.94979591836736]
1.4738876421051985
[197.42469387755102, 136.00938775510204]
1.4515519636999847
[197.56489795918367, 137.88510204081632]
1.432822654768759
[197.72204081632654, 139.9034693877551]
1.4132747506662757
[198.12244897959184, 142.5369387755102]
1.3899726673071497
[199.58959183673468, 146.82938775510203]
1.3593300012231329
[200.02632653061224, 146.3761224489796]
1.366522921799167
[201.4661224489796, 145.61102040816326]
1.3835911724555499
[205.06061224489795, 144.64367346938775]
1.4176949971358186
[212.94571428571427, 144.36]
1.4751019277203814
[221.87489795918367, 144.55877551020407]
1.5348421233930696
[228.27897959183673, 145.13387755102042]
1.5728855553493184
[232.32163265306122, 145.24428571428572]
1.5995233926797499
[233.45530612244897, 145.4373469387755]
1.6051950275243003
[234.45489795918368, 145.0973469387755]
1.6158455196159651
[234.70265306122448, 145.1377551020408]
1.6171026821808978
[234.99081632653062, 145.44897959183675]
1.615623684579767
[235.30367346938775, 145.57734693877552]
1.6163481366942882
[234.155306122449, 146.6065306122449]
1.5971683194779307
[232.77857142857144, 147.08265306122448]
1.5826378337877498
[232.93224489795918, 147.39938775510205]
1.5802795957671576
[234.09285714285716, 147.4]
1.5881469276991664
[236.33836734693878, 147.29448979591837]
1.6045295901726793
[236.9530612244898, 147.46857142857144]
1.6068038018477822
[237.38326530612244, 147.62061224489796]
1.6080631403445953
[237.05816326530612, 147.4030612244898]
1.6082309369699908
[236.31591836734694, 147.21816326530612]
1.6052089845834796
[235.10857142857142, 146.84489795918367]
1.6010673485838174
[233.88448979591837, 146.6642857142857]
1.5946928637524265
[233.42448979591836, 146.63918367346938]
1.591828895581547
[232.5169387755102, 146.21061224489796]
1.5902877035084977
[225.1330612244898, 144.73591836734693]
1.5554747139759113
[215.7642857142857, 142.17163265306124]
1.5176324677990527
[206.74714285714285, 139.66204081632654]
1.4803388354394864
[212.0165306122449, 136.27877551020407]
1.5557560582599295
[210.13040816326532, 141.715306122449]
1.4827643810168416
[209.42265306122448, 143.53306122448978]
1.4590551561753533
[209.8365306122449, 143.59551020408162]
1.461302866043791
[210.04979591836735, 144.92836734693878]
1.4493352803425759
[210.02632653061224, 148.56918367346938]
1.4136600965124473
[208.13836734693876, 151.59836734693877]
1.3729591616947034
[207.36897959183673, 153.78244897959183]
1.348456738514785
[207.36142857142858, 155.96897959183673]
1.3295042970344706
[207.7869387755102, 158.86489795918368]
1.3079474537471192
[207.77367346938775, 160.7834693877551]
1.2922576820898686
[207.74632653061224, 162.76714285714286]
1.276340684513622
[207.77102040816325, 172.22387755102042]
1.2064007811379822
[207.8404081632653, 180.01795918367347]
1.1545537406698652
[206.8542857142857, 179.5965306122449]
1.1517721695910221
[206.18, 179.1930612244898]
1.1506025880193065
[205.50448979591837, 178.68081632653062]
1.1501206118309242
[205.55510204081634, 178.55346938775511]
1.1512243517062286
[204.93142857142857, 177.67836734693878]
1.1533842393501672
[204.7773469387755, 177.2261224489796]
1.1554580335510498
[204.55102040816325, 176.65224489795918]
1.1579304895124285
[204.25061224489795, 175.80489795918368]
1.1618027405147635
[204.22224489795917, 177.00448979591837]
1.1537687271855204
[204.30857142857144, 176.80816326530612]
1.1555381134863105
[204.3734693877551, 177.5748979591837]
1.1509141874023838
[204.21163265306123, 175.90163265306123]
1.1609422242023024
[203.99244897959184, 174.67612244897958]
1.1678324783009488
[203.91795918367347, 174.7083673469388]
1.1671905718100484
[203.8104081632653, 174.54734693877552]
1.167651137285714
[203.8473469387755, 175.90673469387755]
1.158837649357324
[203.94061224489795, 175.36408163265307]
1.1629554373175806
[203.75448979591837, 175.91979591836736]
1.1582237731248122
[203.77081632653062, 175.77591836734695]
1.1592646946135037
[203.8526530612245, 175.63204081632654]
1.160680318430113
[203.73673469387754, 174.67326530612246]
1.1663876228386758
[203.9334693877551, 174.45857142857142]
1.1689507011196156
[204.09061224489795, 174.85142857142858]
1.1672230184926677
[203.99836734693878, 174.31551020408162]
1.170282363905
[204.2391836734694, 174.1908163265306]
1.172502592160837
[204.23183673469387, 173.68326530612245]
1.1758866714920897
[204.5434693877551, 174.24959183673468]
1.1738533630506558
[204.18408163265306, 174.33673469387756]
1.1712051507170032
[204.11204081632653, 174.72775510204082]
1.1681718264915915
[204.15102040816328, 174.71591836734694]
1.1684740710284216
[204.1165306122449, 174.3434693877551]
1.1707724489425635
[204.2161224489796, 174.15979591836734]
1.1725790178618511
[204.27, 173.60326530612244]
1.1766483749012528
[204.20795918367347, 173.3691836734694]
1.177879221997648
[204.15428571428572, 173.39857142857142]
1.177370055775711
[204.2587755102041, 171.09204081632652]
1.1938531712850586
[204.36632653061224, 154.36755102040817]
1.3238943364696767
[204.39204081632653, 153.5969387755102]
1.3307038697890714
[204.5087755102041, 154.05795918367346]
1.3274794537968748
[204.66326530612244, 153.785306122449]
1.3308375843343754
[204.59061224489795, 154.43775510204082]
1.324744795142353
[204.3795918367347, 154.3957142857143]
1.3237387629719024
[204.48897959183674, 154.9630612244898]
1.3195982189303836
[204.39795918367346, 155.50632653061226]
1.3144028525645652
[204.3808163265306, 155.58102040816325]
1.3136616265296512
[204.32, 155.8065306122449]
1.3113699355034762
[204.3934693877551, 156.06204081632654]
1.3096936853998409
[204.35285714285715, 156.1765306122449]
1.3084735353112973
[204.314693877551, 156.5865306122449]
1.3048037598041897
[204.43448979591838, 156.98408163265307]
1.3022625457930221
[204.5638775510204, 157.48285714285714]
1.2989596535288583
[204.69551020408164, 157.18142857142857]
1.3022881396644201
[204.6518367346939, 156.965306122449]
1.3038029981927632
[204.73510204081632, 156.74816326530612]
1.3061403577296742
[204.48204081632653, 156.3495918367347]
1.3078514527230316
[204.564693877551, 156.33551020408163]
1.3084979452877379
[204.45755102040818, 156.23]
1.308695839598081
[204.35510204081632, 156.33265306122448]
1.3071811808936988
[204.66387755102042, 156.54387755102042]
1.3073898561399622
[204.5065306122449, 156.85530612244898]
1.3037909629438804
[204.65102040816328, 156.48448979591836]
1.3078038639807819
[204.2004081632653, 156.7022448979592]
1.3031109305181672
[204.15591836734694, 156.7730612244898]
1.3022385145302973
[203.86142857142858, 156.4030612244898]
1.3034363072908173
[203.75448979591837, 156.65979591836734]
1.3006176128436377
[203.69571428571427, 156.1218367346939]
1.3047227636186807
[203.57387755102042, 156.07632653061225]
1.30432258418827
[203.47183673469388, 156.26979591836735]
1.3020547927315658
[203.31224489795918, 156.63755102040815]
1.2979789557069226
[203.31, 156.75591836734694]
1.2969845229291868
[203.24142857142857, 156.73061224489797]
1.2967564259485924
[203.0604081632653, 156.81]
1.2949455274744295
[203.03510204081633, 156.9087755102041]
1.2939690682093976
[203.1, 156.7638775510204]
1.2955790783747296
[203.25204081632654, 156.71591836734694]
1.2969457278736516
[203.30714285714285, 156.50428571428571]
1.2990516005951456
[203.0477551020408, 156.35795918367347]
1.2986083737734189
[202.89244897959185, 156.24510204081633]
1.2985523791113125
[202.7134693877551, 156.11326530612246]
1.2985025262923964
[202.72102040816327, 156.55408163265307]
1.2948945073424454
[202.55673469387756, 156.83081632653062]
1.2915620758623292
[202.78142857142856, 157.21775510204083]
1.2898125179297657
[202.40326530612245, 156.74897959183673]
1.2912573072766806
[202.57265306122449, 156.3665306122449]
1.29549880187315
[202.52897959183673, 155.52857142857144]
1.3021979031348003
[202.65571428571428, 155.12571428571428]
1.306396655247357
[202.76122448979592, 155.11836734693878]
1.3071387222397641
[202.74755102040817, 155.3369387755102]
1.3052114495021356
[202.7369387755102, 155.22387755102042]
1.3060937658181664
[202.86755102040817, 155.45326530612246]
1.305006688800755
[202.70530612244897, 155.45489795918368]
1.3039493048052522
[202.73632653061225, 154.7908163265306]
1.3097438939978248
[202.8718367346939, 154.78857142857143]
1.3106383427558856
[203.03142857142856, 154.7826530612245]
1.3117195277116693
[203.0087755102041, 154.6326530612245]
1.3128454533456513
[203.04673469387754, 155.06163265306122]
1.3094582535976478
[202.95122448979592, 155.00938775510204]
1.3092834403709586
[203.0191836734694, 155.35897959183674]
1.3067746982301687
[203.00530612244899, 155.37775510204082]
1.3065274755007874
[203.12551020408162, 155.66387755102042]
1.3048981780471527
[203.15714285714284, 155.8508163265306]
1.303535956022832
[203.20469387755102, 155.6173469387755]
1.305797186977476
[203.12244897959184, 155.96714285714285]
1.3023412832896517
[203.03755102040816, 155.68510204081633]
1.3041553004036142
[203.0730612244898, 155.97591836734694]
1.301951373969294
[202.95204081632653, 155.35734693877552]
1.3063562478078845
[204.11122448979592, 157.4391836734694]
1.2964448857479143
[203.8169387755102, 157.23326530612246]
1.2962711063634818
[203.73020408163265, 157.43938775510205]
1.2940230966760127
[203.78489795918367, 157.52693877551022]
1.2936511021114625
[203.61448979591836, 157.19510204081632]
1.295297926922997
[203.76816326530613, 156.99163265306123]
1.2979555650307633
[203.6504081632653, 157.03489795918367]
1.2968480943401375
[203.55877551020407, 157.06632653061226]
1.2960051973363649
[203.58469387755102, 157.18857142857144]
1.2951621865846819
[203.86632653061224, 157.24224489795918]
1.2965111676121726
[203.85897959183674, 157.1430612244898]
1.2972827308016484
[203.58163265306123, 156.84448979591838]
1.297983964358301
[203.62551020408162, 156.8565306122449]
1.2981640573668645
[203.58897959183673, 156.89061224489797]
1.2976492135427777
[203.57122448979592, 156.86714285714285]
1.2977301733300897
[203.57163265306122, 156.60142857142858]
1.2999347101115921
[203.6434693877551, 156.51265306122448]
1.3011310293749478
[203.53326530612244, 156.69285714285715]
1.298931355374807
[203.6661224489796, 156.40448979591838]
1.3021756774036968
[203.48857142857142, 156.87836734693877]
1.2971104612438598
[203.684693877551, 156.75020408163266]
1.2994221925955243
[203.5069387755102, 156.7757142857143]
1.2980769355936792
[203.63795918367347, 156.68326530612245]
1.299679061358675
[203.73061224489797, 156.6034693877551]
1.3009329425547693
[203.6722448979592, 156.7034693877551]
1.2997302848093437
[203.73, 156.97632653061225]
1.2978390086117235
[203.72306122448978, 157.31918367346938]
1.2949664272815957
[203.9865306122449, 157.20448979591836]
1.2975871800930026
[204.03836734693877, 157.71775510204083]
1.2936930735219332
[204.155306122449, 157.8295918367347]
1.2935172913178126
[204.10142857142858, 157.8108163265306]
1.293329781332078
[204.2057142857143, 157.7965306122449]
1.294107756953866
[204.02632653061224, 157.8565306122449]
1.292479479558421
[204.08285714285714, 157.86877551020407]
1.2927373160607427
[204.10408163265305, 157.82020408163265]
1.2932696597393831
[203.99571428571429, 158.065306122449]
1.2905786809895161
[203.95122448979592, 158.124693877551]
1.2898126123661127
[203.99510204081633, 157.90020408163267]
1.2919242456162572
[204.0530612244898, 157.76489795918368]
1.2933996336579359
[204.06897959183672, 157.62489795918367]
1.2946494001517423
[204.07469387755103, 157.5665306122449]
1.2951652427999316
[204.10918367346937, 157.41224489795917]
1.2966537883109475
[203.92061224489797, 157.61102040816326]
1.2938220418648858
[203.9869387755102, 157.5926530612245]
1.2943937094342945
[203.97367346938776, 157.49489795918367]
1.295112896433315
[203.9516326530612, 157.47020408163266]
1.2951760229340437
[203.96102040816328, 157.58938775510205]
1.2942560619952654
[203.92734693877551, 157.65163265306123]
1.2935314624210188
[204.08510204081634, 157.72122448979593]
1.2939609282200317
[204.01265306122448, 157.59285714285716]
1.294555202310267
[204.02775510204083, 157.40244897959184]
1.2962171581491355
[204.12571428571428, 157.40224489795918]
1.2968411881167579
[203.90163265306123, 157.2916326530612]
1.2963285409008873
[204.10510204081632, 157.35489795918366]
1.2971004060754385
[204.22897959183675, 157.42061224489797]
1.2973458601095984
[204.1122448979592, 157.1491836734694]
1.2988438127815634
[204.2226530612245, 157.17612244897958]
1.2993236496689662
[204.11122448979592, 157.21224489795918]
1.2983163278552328
[204.01795918367347, 157.17204081632653]
1.2980550365321766
[204.0830612244898, 157.33081632653062]
1.2971588528526268
[203.9765306122449, 157.2704081632653]
1.2969797242497971
[204.02448979591836, 157.0442857142857]
1.2991525853230013
[204.21244897959184, 156.9934693877551]
1.3007703427154125
[204.07102040816326, 157.06897959183672]
1.2992445799193908
[204.1177551020408, 156.9030612244898]
1.3009163333658504
[203.98122448979592, 157.13795918367347]
1.2981027980092885
[203.86591836734695, 156.814693877551]
1.3000434673968497
[203.77591836734695, 157.1595918367347]
1.2966177627837034
[203.96591836734694, 156.83448979591836]
1.3005169885320416
[203.91224489795917, 156.59102040816327]
1.3021962840937524
[203.8930612244898, 156.4361224489796]
1.30336304705448
[203.94979591836736, 156.8808163265306]
1.3000301801965877
[204.0865306122449, 156.52510204081634]
1.303858154068005
[203.91408163265305, 156.83816326530612]
1.3001560167962034
[203.90367346938777, 156.80877551020407]
1.3003333060025015
[203.7838775510204, 156.63448979591837]
1.3010153626863006
[204.0334693877551, 156.75204081632654]
1.3016319808354544
[203.97204081632654, 156.64142857142858]
1.3021589669894715
[203.9626530612245, 156.8481632653061]
1.3003827957884657
[203.97673469387755, 156.83530612244897]
1.30057918549681
[203.99755102040817, 156.92163265306124]
1.2999963585099021
[204.10061224489795, 156.7726530612245]
1.301889125810676
[204.10367346938776, 156.85673469387754]
1.3012107759843248
[204.2865306122449, 156.87408163265306]
1.3022325197773335
[204.2930612244898, 156.97387755102042]
1.3014462304920096
[204.38591836734693, 156.83142857142857]
1.3032204082376242
[204.41795918367347, 156.94163265306122]
1.3025094471622103
[204.51877551020408, 156.77857142857144]
1.304507201759924
[204.39714285714285, 177.88632653061225]
1.1490323446640425
[204.44448979591837, 177.63897959183674]
1.1508988076022109
[204.52551020408163, 177.7391836734694]
1.150705803734433
[204.4426530612245, 177.3634693877551]
1.1526762177518552
[204.46938775510205, 177.2461224489796]
1.1535901882082564
[205.1008163265306, 176.5134693877551]
1.1619556118744478
[205.10979591836735, 175.97387755102042]
1.165569565056038
[205.3026530612245, 175.46816326530612]
1.1700279369244262
[205.26265306122448, 174.6869387755102]
1.175031484895428
[205.30102040816325, 174.42979591836735]
1.1769836645583394
[205.28918367346938, 174.55714285714285]
1.1760571942992764
[205.68020408163267, 174.91061224489795]
1.175916094751605
[206.0365306122449, 174.9012244897959]
1.178016513110607
[206.22857142857143, 174.97551020408164]
1.1786139168163474
[206.25285714285715, 175.38857142857142]
1.1759766070439515
[206.15020408163267, 175.4565306122449]
1.174936056026436
[206.0804081632653, 175.46367346938774]
1.174490446304369
[205.99020408163264, 175.37755102040816]
1.1745528597195554
[205.71102040816328, 175.51734693877552]
1.1720267198427972
[205.51061224489797, 175.38530612244898]
1.1717664198243403
[205.27836734693878, 175.56142857142856]
1.1692680392118115
[205.0761224489796, 175.15020408163267]
1.1708585983342576
[204.87489795918367, 175.30346938775511]
1.168687069769391
[204.79387755102042, 175.19183673469388]
1.1689692931363869
[204.6895918367347, 175.03163265306122]
1.1694434242206948
[204.8004081632653, 174.38816326530613]
1.1743939745021075
[204.84591836734694, 174.52938775510205]
1.1737044460087418
[205.08530612244897, 174.45612244897958]
1.1755695543584435
[204.96448979591835, 174.07244897959183]
1.1774665720934867
[205.11897959183673, 173.86102040816326]
1.1797870454820236
[204.72816326530614, 173.6065306122449]
1.179265333759663
[204.85795918367347, 174.1973469387755]
1.1760107876710324
[204.78122448979593, 174.18673469387755]
1.1756419043602047
[204.59979591836733, 175.53918367346938]
1.1655505718823171
[204.50020408163266, 176.08612244897958]
1.161364684720603
[204.6342857142857, 176.75306122448978]
1.157741112355529
[204.53755102040816, 176.65795918367348]
1.1578167888136188
[204.49244897959184, 176.71]
1.157220581628611
[204.53244897959183, 176.79938775510203]
1.1568617492211282
[204.67816326530613, 176.6204081632653]
1.1588590774634868
[204.60204081632654, 176.46693877551022]
1.1594355420683529
[204.81285714285715, 176.0838775510204]
1.1631550826310746
[204.74571428571429, 175.67734693877551]
1.1654645169309692
[204.8187755102041, 175.3530612244898]
1.168036497794537
[204.84857142857143, 175.3665306122449]
1.1681166908725282
[204.93591836734694, 175.06857142857143]
1.1706037051371125
[204.91102040816327, 175.38020408163266]
1.1683816966753282
[204.83755102040817, 175.3991836734694]
1.167836398838335
[204.87836734693877, 175.22224489795917]
1.169248616043299
[204.76204081632653, 174.7908163265306]
1.1714691030094282
[204.9222448979592, 174.67612244897958]
1.1731554492103755
[204.80612244897958, 174.37244897959184]
1.1745325803903208
[204.44142857142856, 173.5234693877551]
1.1781773917543352
[204.4018367346939, 173.84775510204082]
1.175751948103783
[204.26265306122448, 173.66020408163266]
1.1762202753441802
[204.11408163265307, 173.78244897959183]
1.1745379515086891
[204.03510204081633, 173.50020408163266]
1.1759934411651576
[203.94836734693877, 173.61061224489796]
1.1747459715149549
[203.8130612244898, 173.7677551020408]
1.1729049564161407
[203.6730612244898, 173.98448979591836]
1.1706391843514083
[203.58836734693878, 173.67448979591836]
1.1722410561630074
[203.70877551020408, 173.9108163265306]
1.1713404595130275
[203.3248979591837, 174.20204081632653]
1.167178622055085
[203.04183673469387, 173.19897959183675]
1.1723038854685244
[203.30102040816325, 154.46020408163264]
1.3162032357585007
[203.21285714285713, 154.1934693877551]
1.317908326142085
[203.4204081632653, 154.25102040816327]
1.31876215551116
[203.34795918367348, 154.61122448979592]
1.3152211933816882
[203.42, 155.68755102040816]
1.3065913020453053
[203.32836734693876, 155.70367346938775]
1.3058675034209408
[203.40816326530611, 155.77020408163264]
1.3058220245940515
[203.42816326530613, 155.714693877551]
1.3064159726973192
[203.45897959183674, 155.91857142857143]
1.3049053600715184
[203.5122448979592, 156.1987755102041]
1.3029055076341762
[203.46755102040817, 155.70734693877552]
1.3067305751501377
[203.40571428571428, 155.95755102040818]
1.3042376784891754
[203.49673469387756, 156.28285714285715]
1.302105287900275
[203.44938775510204, 156.4861224489796]
1.3001113745497417
[203.5687755102041, 156.56204081632654]
1.300243497394265
[203.4538775510204, 156.88734693877552]
1.2968150811449264
[203.53285714285715, 156.80591836734695]
1.2979921884456151
[203.57673469387754, 156.5304081632653]
1.300557106332603
[203.41224489795917, 156.58448979591836]
1.299057430037119
[203.37326530612245, 156.90775510204082]
1.2961326556094313
[203.34857142857143, 157.14326530612246]
1.2940330025116817
[203.66653061224488, 157.10938775510203]
1.29633584295876
[203.6838775510204, 157.42367346938775]
1.293857988840721
[203.8291836734694, 157.53632653061226]
1.2938551263848441
[204.08020408163264, 157.55244897959184]
1.2953159751142151
[203.9938775510204, 157.52938775510205]
1.2949575978048797
[204.14122448979592, 157.53836734693877]
1.2958190942795924
[203.9708163265306, 157.70816326530613]
1.2933434268928659
[203.82142857142858, 157.52285714285713]
1.2939165291204906
[203.74591836734695, 157.61510204081634]
1.2926801793053084
[203.73857142857142, 157.5461224489796]
1.2931995295190524
[203.7948979591837, 157.7630612244898]
1.2917782932038357
[204.03489795918367, 157.6742857142857]
1.2940277296001574
[204.1404081632653, 157.84285714285716]
1.293314197794241
[204.21816326530612, 157.7691836734694]
1.2944109775453418
[203.93714285714285, 157.8257142857143]
1.292166766234001
[203.80285714285714, 157.84183673469389]
1.2911840191356627
[203.7804081632653, 157.9695918367347]
1.2899976874908756
[203.8712244897959, 157.9612244897959]
1.2906409477913723
[203.96693877551022, 157.9557142857143]
1.291291927600477
[204.1308163265306, 158.05448979591836]
1.2915217820772222
[204.03183673469388, 158.00469387755103]
1.2913023767054195
[204.23408163265307, 158.04551020408164]
1.2922485515022153
[203.88122448979593, 158.10714285714286]
1.2895130530188132
[204.13551020408164, 158.44653061224489]
1.2883558220889557
[203.89122448979592, 158.30612244897958]
1.2879553951269822
[203.95673469387756, 158.45938775510203]
1.2871230766654949
[204.14, 158.39510204081634]
1.2888024779162413
[204.1173469387755, 158.31836734693877]
1.289284056924822
[204.14979591836735, 158.51020408163265]
1.2879284150894812
[204.20734693877552, 158.52673469387756]
1.2881571511146641
[204.41591836734693, 158.73510204081632]
1.2877801805600912
[204.45734693877552, 158.52489795918368]
1.2897491155705922
[204.41632653061225, 158.78489795918367]
1.2873788953352374
[204.50979591836736, 158.98469387755102]
1.28634896184333
[204.28183673469388, 159.02816326530612]
1.2845638944712656
[204.285306122449, 159.3365306122449]
1.2820996248474221
[204.13979591836735, 159.1708163265306]
1.2825202548410963
[204.02877551020407, 159.36836734693878]
1.2802338312598842
[204.0569387755102, 159.43673469387755]
1.2798615022272284
[204.38755102040815, 159.58408163265307]
1.2807514943181382
[204.3691836734694, 159.51469387755103]
1.2811934669187919
[204.45877551020408, 159.69408163265305]
1.2803152967216656
[204.49897959183673, 159.57]
1.2815628225345412
[204.58612244897958, 159.74244897959184]
1.2807248402402847
[204.74551020408163, 159.62163265306123]
1.2826927453442196
[204.62510204081633, 159.7942857142857]
1.2805533134438156
[204.7838775510204, 159.78367346938776]
1.2816320535417782
[204.47530612244898, 159.95714285714286]
1.2783130685515254
[204.4391836734694, 160.0612244897959]
1.2772561519826597
[204.35163265306122, 160.15857142857143]
1.2759331631788393
[204.34673469387755, 160.52530612244897]
1.2729876654961898
[204.3930612244898, 160.40510204081633]
1.2742304242447375
[204.60877551020408, 160.27510204081634]
1.2766098595781743
[204.44979591836736, 160.39285714285714]
1.274681426344753
[204.66530612244898, 160.2438775510204]
1.2772113933481493
[204.55448979591836, 160.30530612244897]
1.2760306863434059
[204.7461224489796, 160.2587755102041]
1.2775969477936195
[204.59102040816327, 159.98632653061225]
1.2788031630254117
[204.7095918367347, 160.06632653061226]
1.2789047907436328
[204.68551020408162, 160.1422448979592]
1.2781481259645442
[204.84, 160.07632653061225]
1.2796395596998371
[204.90816326530611, 160.2042857142857]
1.2790429566331762
[204.73448979591836, 159.934693877551]
1.2801130563495304
[204.7561224489796, 159.61204081632653]
1.2828363161185476
[204.75326530612244, 159.40755102040816]
1.2844640294355245
[204.70326530612246, 159.08122448979591]
1.2867845716089075
[204.63591836734693, 158.6238775510204]
1.2900700797805618
[204.3461224489796, 158.76816326530613]
1.2870724095202348
[204.48469387755102, 158.8522448979592]
1.2872634819161948
[204.07632653061225, 158.69857142857143]
1.28593675855781
[204.01673469387754, 158.85836734693876]
1.2842681068748185
[203.9365306122449, 158.63489795918366]
1.2855716695119457
[203.96632653061224, 158.74224489795918]
1.2848900219454717
[203.98591836734693, 158.72938775510204]
1.285117527713706
[203.96979591836734, 158.58877551020407]
1.286155311195043
[203.89877551020408, 158.41816326530613]
1.2870921572845826
[204.07897959183674, 158.51857142857142]
1.287413693882517
[203.97571428571428, 158.49020408163264]
1.2869925650461884
[204.04551020408164, 158.3134693877551]
1.2888701826394546
[203.9891836734694, 158.44979591836736]
1.2874057835868955
[204.1061224489796, 158.42122448979592]
1.288376119464512
[203.86959183673468, 158.35714285714286]
1.287403827566209
[203.90571428571428, 158.72632653061225]
1.284637014807929
[204.79755102040815, 160.8134693877551]
1.273509935455706
[204.77326530612245, 160.98510204081632]
1.2720013386965712
[204.28306122448978, 155.01448979591837]
1.3178320394011882
[203.79877551020408, 153.60142857142858]
1.326802604673904
[203.50775510204082, 155.65]
1.30747031867678
[203.44918367346938, 156.54326530612244]
1.2996354923070104
[203.3995918367347, 155.5912244897959]
1.3072690474910054
[203.38673469387754, 154.30285714285714]
1.3181008988419276
[203.41673469387754, 154.75040816326532]
1.3144827022315062
[203.64020408163265, 155.50183673469388]
1.3095678376395579
[203.57142857142858, 156.30346938775511]
1.3024114523421861
[203.53795918367348, 155.59163265306123]
1.3081549162577601
[203.73530612244897, 157.5930612244898]
1.2927936327871061
[204.04326530612244, 150.24551020408163]
1.3580656422209634
[205.00163265306122, 161.12510204081633]
1.2723134387907482
[205.3726530612245, 160.99244897959184]
1.275666370459763
[205.41326530612244, 160.78326530612244]
1.2775786392634019
[205.55081632653062, 160.59897959183672]
1.279901135417792
[205.41734693877552, 160.8038775510204]
1.2774402587002294
[205.61204081632653, 160.2369387755102]
1.2831750430803364
[205.40918367346939, 160.03857142857143]
1.283497983266789
[205.41122448979593, 160.9073469387755]
1.276580767738057
[205.54142857142858, 160.62714285714284]
1.2796182819128596
[205.47142857142856, 160.43020408163267]
1.2807527718837612
[205.51469387755103, 160.73795918367347]
1.2785697598829886
[205.49142857142857, 160.7438775510204]
1.2783779494569254
[205.62, 160.91469387755103]
1.2778199121856935
[205.57836734693876, 160.9318367346939]
1.2774250982162556
[205.53367346938776, 161.14408163265307]
1.2754652320271123
[205.67326530612246, 161.07122448979592]
1.2769088082468272
[205.48204081632653, 161.00428571428571]
1.276251994813169
[205.7234693877551, 161.23755102040818]
1.2759029648231028
[205.52489795918368, 161.065306122449]
1.276034565773802
[205.55530612244897, 161.23551020408163]
1.2748761477063593
[205.61163265306124, 161.0634693877551]
1.2765876299240635
[205.57877551020408, 161.18163265306123]
1.2754479038731814
[205.55346938775511, 161.214693877551]
1.2750293688730456
[205.42734693877551, 161.2]
1.2743631944092775
[205.85367346938776, 161.43795918367346]
1.2751255932019125
[205.88816326530613, 161.2369387755102]
1.2769292497667903
[205.77428571428572, 161.49632653061224]
1.274173166256388
[205.714693877551, 161.33326530612246]
1.2750916154037844
[205.83102040816325, 161.57979591836735]
1.2738660748906523
[205.77102040816325, 161.41489795918366]
1.2747957159455985
[205.9726530612245, 161.62897959183672]
1.2743547201830345
[205.88551020408164, 161.4673469387755]
1.2750906861815747
[205.80081632653062, 161.7091836734694]
1.272660041015933
[205.83183673469387, 161.5704081632653]
1.273945143015934
[205.67122448979592, 161.5630612244898]
1.2730089596657148
[205.8330612244898, 161.52836734693878]
1.2742842920116388
[205.61551020408163, 161.35632653061225]
1.2742946906706667
[205.47020408163266, 161.3542857142857]
1.2734102671773104
[205.61469387755102, 161.19673469387754]
1.2755512341365096
[205.59102040816327, 161.2734693877551]
1.274797529864345
[205.7077551020408, 161.30816326530612]
1.2752470236965625
[205.39632653061224, 161.00244897959183]
1.2757341756748535
[205.37591836734694, 160.88489795918366]
1.2765394451096996
[205.2, 160.55326530612246]
1.27808051495403
[205.2369387755102, 160.77408163265306]
1.276554881802707
[205.19918367346938, 160.76551020408164]
1.2763880972540815
[204.96693877551022, 160.3404081632653]
1.278323668521564
[204.74, 160.24816326530612]
1.2776433490912056
[204.67244897959185, 159.74775510204083]
1.2812226929189385
[204.5065306122449, 159.41816326530613]
1.2828308043663883
[204.30795918367346, 159.1030612244898]
1.284123370168226
[204.30061224489796, 159.11938775510205]
1.2839454395044152
[204.51061224489797, 158.81714285714287]
1.2877111914099644
[204.4234693877551, 158.1830612244898]
1.292322122263407
[204.43081632653062, 158.42897959183674]
1.290362513557868
[204.33489795918368, 158.67102040816326]
1.287789650772745
[204.44653061224489, 158.5965306122449]
1.2890983795358006
[204.24163265306123, 158.61285714285714]
1.2876738767091738
[204.3181632653061, 158.4634693877551]
1.2893707556367204
[204.46367346938774, 158.32387755102042]
1.2914266415910551
[204.59408163265306, 158.2691836734694]
1.2926968907273708
[204.48265306122448, 158.05979591836734]
1.29370439758655
[204.66836734693877, 158.16857142857143]
1.2939888468257839
[204.63734693877552, 158.13877551020408]
1.2940364959735702
[204.53, 158.30020408163264]
1.2920387638573572
[204.5230612244898, 158.6226530612245]
1.2893685566181323
[204.3161224489796, 158.12775510204082]
1.292095257515881
[204.15897959183673, 158.00755102040816]
1.2920836901362245
[204.1865306122449, 157.95061224489797]
1.2927238945782586
[204.14673469387756, 157.72530612244898]
1.2943182024030413
[204.44714285714286, 157.8412244897959]
1.2952708870448475
[204.62285714285716, 157.54510204081632]
1.2988208106263062
[204.82591836734693, 157.67367346938775]
1.2990495741009913
[204.46408163265306, 157.5469387755102]
1.2977978704111506
[204.6130612244898, 157.74244897959184]
1.2971337933961067
[204.69755102040816, 157.45877551020408]
1.3000072581355924
[204.5416326530612, 157.77183673469386]
1.296439446268313
[204.80530612244897, 157.82755102040815]
1.2976524364619095
[204.82387755102042, 157.62326530612245]
1.2994520647267964
[204.81897959183672, 157.56224489795918]
1.2999242281961778
[205.05224489795918, 157.59061224489795]
1.3011704312646821
[205.2008163265306, 157.54408163265308]
1.3024977783995666
[205.0234693877551, 175.07122448979592]
1.171086053606171
[205.2704081632653, 178.1961224489796]
1.1519353246423054
[205.23285714285714, 178.06489795918367]
1.152573356652814
[205.30061224489796, 178.18857142857144]
1.1521536459884278
[205.63163265306122, 177.99857142857144]
1.1552431629238022
[205.47244897959183, 177.9142857142857]
1.1548957305742273
[205.52551020408163, 176.29408163265308]
1.165810606350011
[205.84285714285716, 175.96]
1.1698275582112818
[206.23530612244897, 175.5116326530612]
1.1750520635297155
[206.24755102040817, 175.8895918367347]
1.1725966776468078
[206.1138775510204, 176.57979591836735]
1.167256290443934
[205.93, 176.48122448979592]
1.166866337171787
[206.17673469387756, 175.80408163265307]
1.1727642087667163
[205.66510204081632, 175.82]
1.1697480493733154
[205.62591836734694, 176.09857142857143]
1.1676751077492544
[205.39714285714285, 175.68938775510205]
1.1690924846493929
[205.09938775510204, 175.29122448979592]
1.1700493755581092
[205.0130612244898, 174.84938775510204]
1.1725123196406937
[205.1795918367347, 175.10510204081632]
1.1717510766128798
[205.0157142857143, 175.33877551020407]
1.1692548535779135
[205.11061224489796, 174.99979591836734]
1.1720620082355782
[204.9926530612245, 174.55979591836734]
1.1743405861742016
[205.22244897959183, 174.1177551020408]
1.178641712094911
[205.27367346938775, 175.86326530612246]
1.1672345166119318
[205.09755102040816, 176.44448979591837]
1.1623913631852765
[205.16020408163266, 176.6377551020408]
1.1614742497328212
[204.95857142857142, 176.59285714285716]
1.1606277555312865
[205.12571428571428, 176.435306122449]
1.162611490827996
[204.9073469387755, 176.16469387755103]
1.1631578520563433
[204.77836734693878, 174.85122448979592]
1.171157753938917
[204.90632653061223, 173.3673469387755]
1.1819199529134785
[204.57591836734693, 173.12918367346938]
1.181637399464597
[204.66040816326532, 173.5730612244898]
1.179102371758996
[204.81, 173.30551020408163]
1.1817858518105928
[205.23285714285714, 174.3895918367347]
1.1768641406936615
[205.34142857142857, 174.73897959183674]
1.1751323548476387
[205.6042857142857, 175.29]
1.1729379069786394
[205.81591836734694, 175.34836734693877]
1.1737544037699879
[206.65510204081633, 175.14]
1.1799423435012923
[206.8973469387755, 173.81102040816327]
1.1903580477976314
[207.0477551020408, 156.79632653061225]
1.32048855788479
[207.1212244897959, 157.11673469387756]
1.3182632957166904
[207.0122448979592, 156.95142857142858]
1.3189573792490072
[207.08183673469387, 157.1738775510204]
1.317533421973844
[207.04285714285714, 157.20102040816326]
1.3170579720493065
[207.05346938775511, 157.51795918367347]
1.3144753173593424
[207.09918367346938, 157.92326530612246]
1.311391220742701
[206.91020408163266, 158.15081632653062]
1.3083094282259635
[207.15775510204082, 158.72326530612244]
1.3051505379662203
[206.99204081632652, 159.27]
1.2996298161381712
[207.34897959183672, 159.89183673469387]
1.296807790981148
[207.57408163265305, 160.1065306122449]
1.2964747961178906
[207.62061224489796, 160.34408163265306]
1.2948442507566635
[207.7361224489796, 160.9557142857143]
1.2906414871374177
[207.90571428571428, 161.18326530612245]
1.2898715874185551
[208.00857142857143, 161.37142857142857]
1.289004957507082
[208.12244897959184, 161.16897959183675]
1.291330686008347
[208.07408163265305, 161.32795918367347]
1.289758344960892
[208.17326530612246, 161.09204081632652]
1.29226288431889
[207.98755102040818, 161.19]
1.2903253987245373
[208.01510204081632, 161.13591836734693]
1.290929447316627
[208.01142857142858, 160.81673469387755]
1.2934687983025424
[207.83816326530612, 160.30142857142857]
1.296545920504356
[207.9861224489796, 160.2165306122449]
1.2981564489893143
[207.6834693877551, 160.24469387755101]
1.2960396026994432
[207.85020408163265, 160.78142857142856]
1.2927500764759867
[207.77326530612245, 160.94489795918366]
1.2909590048565234
[207.84102040816327, 161.26448979591837]
1.2888207482700496
[207.77428571428572, 161.315306122449]
1.288001062692534
[207.71551020408162, 161.53204081632654]
1.285909031758405
[207.92142857142858, 161.38857142857142]
1.2883280812944802
[207.8195918367347, 161.0130612244898]
1.2907002093885145
[207.92102040816326, 161.03591836734694]
1.291146860378468
[207.71632653061224, 160.4338775510204]
1.294716114210699
[207.86632653061224, 160.39408163265307]
1.2959725472083425
[207.92102040816326, 160.0608163265306]
1.299012620203035
[207.8634693877551, 160.05142857142857]
1.2987292349907937
[207.91755102040815, 159.2069387755102]
1.3059578471864368
[207.59673469387755, 159.25755102040816]
1.303528362477927
[207.63387755102042, 159.0891836734694]
1.30514138520686
[207.47040816326532, 158.92265306122448]
1.3054803967017714
[207.31183673469388, 158.6708163265306]
1.3065530356134574
[207.39061224489797, 158.48]
1.3086232473807293
[207.4265306122449, 158.4222448979592]
1.3093270502879801
[207.34244897959184, 158.26510204081632]
1.3100958221738521
[207.44183673469388, 158.0130612244898]
1.3128144922145417
[207.2430612244898, 157.9504081632653]
1.3120767691228323
[207.25306122448978, 158.00306122448978]
1.3117028215676525
[206.96591836734694, 157.74775510204083]
1.3120054750285912
[207.0161224489796, 157.61326530612246]
1.3134435229604884
[206.90510204081633, 157.56795918367348]
1.313116594977483
[206.9551020408163, 157.53061224489795]
1.3137453037958284
[206.99142857142857, 157.5073469387755]
1.314169990126797
[207.17204081632653, 157.59775510204082]
1.3145621311812947
[207.12551020408162, 157.84]
1.3122498112270757
[207.31897959183672, 157.89897959183673]
1.3129849231942405
[207.27163265306123, 157.87163265306123]
1.3129124540604546
[207.19836734693877, 158.09285714285716]
1.3106118207460093
[207.20183673469387, 157.78836734693877]
1.3131629423549755
[207.5761224489796, 157.96102040816328]
1.3140971229016716
[207.37408163265306, 177.56489795918367]
1.167877683123618
[207.5373469387755, 178.20857142857142]
1.1645755603958672
[207.62918367346938, 178.18510204081633]
1.1652443514941466
[207.75510204081633, 178.20122448979592]
1.1658455357735924
[207.8834693877551, 178.02204081632652]
1.167740064289219
[207.8795918367347, 177.67530612244897]
1.1699970939882314
[207.91918367346938, 177.51714285714286]
1.1712625627418565
[208.1369387755102, 176.97591836734694]
1.176074918529213
[208.06408163265306, 176.6238775510204]
1.178006532964665
[208.15285714285713, 175.96877551020407]
1.1828965482048648
[208.2669387755102, 176.33714285714285]
1.1810724354552735
[208.2683673469388, 176.5961224489796]
1.1793484729944148
[208.29673469387754, 176.60244897959183]
1.179466852795163
[209.04204081632653, 170.86122448979592]
1.2234609779986145
[209.24693877551022, 157.09857142857143]
1.3319467953955855
[209.16204081632654, 157.22755102040816]
1.3303141813178612
[209.14857142857142, 157.28326530612244]
1.3297573077561866
[209.55673469387756, 157.45755102040818]
1.3308776450277495
[209.54102040816326, 157.45734693877552]
1.3307795697182652
[209.70020408163265, 157.5538775510204]
1.3309745678187184
[209.50428571428571, 157.66673469387754]
1.3287792515082835
[209.23326530612246, 157.55448979591836]
1.3280057304437598
[208.95204081632653, 157.43489795918367]
1.3272282290963158
[208.82183673469387, 157.50102040816327]
1.3258443417924082
[208.4134693877551, 157.30632653061224]
1.3248893034648372
[208.17836734693878, 157.18897959183673]
1.324382713645086
[207.7995918367347, 156.7991836734694]
1.3252593984766683
[207.50795918367348, 156.27551020408163]
1.327834149526608
[207.58979591836734, 156.42489795918368]
1.3270892206209668
[207.61142857142858, 156.87775510204082]
1.3233962229787655
[207.55020408163264, 157.7773469387755]
1.3154626320480036
[207.31673469387755, 157.87408163265306]
1.3131777714867054
[207.69918367346938, 157.8426530612245]
1.3158622187686264
[207.98326530612246, 157.8461224489796]
1.3176330344975602
[208.32816326530613, 157.80775510204083]
1.3201389445696003
[208.3938775510204, 157.75183673469388]
1.3210234623226353
[208.2791836734694, 157.57183673469387]
1.321804632030483
[208.27326530612245, 157.3781632653061]
1.3233936715541534
[208.2965306122449, 157.2977551020408]
1.3242180759485132
[208.18367346938774, 157.15163265306123]
1.3247312163086995
[208.0381632653061, 157.23510204081632]
1.32310254240368
[208.09755102040816, 157.31142857142856]
1.3228380983516383
[208.2112244897959, 157.18714285714285]
1.324607221081851
[207.9069387755102, 156.97040816326532]
1.3244976630198073
[208.16734693877552, 156.97510204081632]
1.3261169716242536
[207.86102040816326, 156.86]
1.3251371950029531
[207.90551020408162, 157.314693877551]
1.321589897800068
[207.74795918367346, 157.14469387755102]
1.3220170153855344
[207.45877551020408, 157.04816326530613]
1.320988231869594
[207.59673469387755, 156.98244897959182]
1.322420028756627
[207.7395918367347, 156.88285714285715]
1.324170120433028
[207.58612244897958, 156.8726530612245]
1.3232779480561379
[207.5087755102041, 156.81326530612245]
1.3232858527951483
[207.4004081632653, 156.87326530612245]
1.3220889343926399
[207.36591836734695, 157.15061224489796]
1.3195361787340365
[207.34632653061223, 156.88163265306122]
1.3216736913310438
[207.26714285714286, 157.03775510204082]
1.319855487761295
[207.4895918367347, 157.0408163265306]
1.3212462638076674
[207.75244897959183, 157.29530612244898]
1.3207797111114283
[207.73551020408163, 157.48979591836735]
1.3190410781391733
[207.77244897959184, 157.7934693877551]
1.3167366798243119
[207.76714285714286, 157.4934693877551]
1.3192111626267626
[207.53326530612244, 157.8665306122449]
1.314612188544702
[207.6791836734694, 157.94530612244898]
1.3148803770873927
[207.64979591836735, 158.36816326530612]
1.311183962969263
[207.82408163265305, 158.61204081632653]
1.3102667399211785
[207.7316326530612, 158.5612244897959]
1.3101036102709311
[207.84081632653061, 159.14816326530612]
1.305957995758028
[207.97795918367348, 159.04183673469387]
1.3076933934723889
[207.85020408163265, 159.08795918367346]
1.3065112227736935
[207.8461224489796, 158.97673469387755]
1.307399619505357
[207.79, 159.00326530612244]
1.3068285082067368
[208.06979591836733, 159.0087755102041]
1.308542847718583
[208.20367346938775, 159.24591836734695]
1.3074349132710927
[208.13836734693876, 159.25040816326532]
1.306987967864754
[208.05285714285714, 159.27204081632652]
1.3062735686471485
[208.25408163265305, 159.33]
1.3070613295214526
[208.04408163265308, 159.32836734693876]
1.3057566903929636
[208.14877551020408, 159.28755102040816]
1.3067485448598286
[207.88367346938776, 159.2773469387755]
1.3051678563511986
[207.92142857142858, 159.2287755102041]
1.305803099378253
[208.03755102040816, 159.17877551020408]
1.3069427777264941
[208.16163265306122, 159.2930612244898]
1.3067840560845367
[207.90836734693877, 159.2004081632653]
1.3059537330690876
[208.01530612244898, 159.33428571428573]
1.3055275905617505
[207.90816326530611, 159.21408163265306]
1.3058402946103884
[207.93244897959184, 159.4065306122449]
1.3044161251171438
[208.06244897959184, 159.43938775510205]
1.3049626689433511
[208.04857142857142, 159.52693877551022]
1.3041594919673216
[207.8704081632653, 159.81142857142856]
1.300723046038954
[207.8434693877551, 159.79897959183674]
1.300655798420209
[207.81285714285715, 159.3677551020408]
1.3039830862259287
[207.86857142857144, 159.52591836734695]
1.3030394907359435
[207.91714285714286, 159.50224489795917]
1.3035374078286917
[207.86489795918368, 160.02836734693878]
1.298925318087737
[207.94857142857143, 160.07714285714286]
1.2990522426687132
[207.94673469387754, 160.69510204081632]
1.2940452574656531
[207.98591836734693, 161.3542857142857]
1.2890015127062264
[208.00020408163266, 160.92530612244897]
1.2925263844044772
[207.85387755102042, 160.845306122449]
1.2922595166860793
[208.0912244897959, 161.4295918367347]
1.2890525344340427
[208.06632653061226, 161.81408163265306]
1.2858357222763843
[208.13918367346938, 161.8761224489796]
1.2857929911131338
[208.20142857142858, 162.00448979591837]
1.2851583856330513
[208.0608163265306, 162.0238775510204]
1.2841367548496883
[208.16326530612244, 162.2383673469388]
1.2830705135301042
[208.06142857142856, 161.93836734693878]
1.2848186132794286
[208.08877551020407, 161.9318367346939]
1.2850393085526033
[208.0212244897959, 161.90408163265306]
1.2848423732872827
[207.93938775510205, 161.98102040816326]
1.2837268664633172
[208.10673469387754, 162.06795918367348]
1.2840708042607472
[207.9673469387755, 162.09857142857143]
1.2829684130215553
[207.9938775510204, 161.92714285714285]
1.2844905053040987
[208.0404081632653, 161.72163265306122]
1.2864105113851467
[207.9061224489796, 161.53285714285715]
1.2870825547591884
[207.86897959183673, 161.02510204081634]
1.2909104043861839
[207.5638775510204, 153.03102040816327]
1.356351653392936
[207.77020408163264, 143.77857142857144]
1.4450707224118717
[207.73489795918368, 121.81816326530613]
1.705286735499046
[207.61551020408163, 122.59897959183674]
1.6934521877366893
[208.4073469387755, 106.65142857142857]
1.9540980344130794
[208.64612244897958, 97.42734693877551]
2.1415560312865263
[208.73061224489797, 93.35061224489796]
2.2359854662475023
[209.07204081632653, 83.96632653061225]
2.4899510250707886
[209.53163265306122, 78.06204081632653]
2.6841680087005626
[209.97387755102042, 76.82448979591837]
2.7331633195197114
[210.80714285714285, 78.4795918367347]
2.6861396437394354
[211.15285714285713, 87.57632653061225]
2.4110723240834813
[211.32020408163265, 86.23816326530613]
2.450425612979717
[211.62081632653062, 85.13326530612245]
2.4857594216031047
[212.32122448979592, 86.28183673469388]
2.460787026853146
[213.52061224489796, 90.30224489795918]
2.3645105665554
[212.38673469387754, 92.38408163265306]
2.2989537909614253
[211.18979591836734, 94.29040816326531]
2.239780270679165
[211.47469387755103, 96.42020408163265]
2.1932612142005974
[213.00163265306122, 99.79816326530612]
2.1343241767567602
[211.72020408163266, 99.69918367346939]
2.123590146686154
[207.43326530612245, 97.17326530612245]
2.134674230125444
[197.39591836734695, 94.30714285714286]
2.0931173651010053
[183.34836734693877, 92.65]
1.9789354273819617
[149.79, 91.47142857142858]
1.6375605185069497
[147.04448979591837, 88.73387755102041]
1.6571403600769095
[147.79326530612244, 85.2673469387755]
1.7332926449821688
[152.45714285714286, 80.2469387755102]
1.8998499529513493
[179.15163265306123, 74.79836734693878]
2.39512758108875
[210.57979591836735, 72.77326530612245]
2.8936422604174554
[216.20755102040818, 77.71755102040817]
2.781965568673585
[215.91877551020409, 85.60020408163265]
2.522409587999266
[216.25632653061226, 107.9369387755102]
2.0035432631676473
[216.3369387755102, 112.9730612244898]
1.914942698999942
[215.535306122449, 114.38408163265306]
1.8843120742503774
[214.9295918367347, 118.8038775510204]
1.8091126002552655
[214.3726530612245, 126.50448979591837]
1.6945853337463217
[213.75285714285715, 141.4595918367347]
1.5110524098610407
[212.78020408163266, 148.35979591836735]
1.434217422344741
[212.2042857142857, 150.73734693877552]
1.4077751136251324
[211.90979591836734, 150.01]
1.4126377969359867
[110.81, 74.67693877551021]
1.4838583613223764
[90.79387755102042, 43.51510204081632]
2.0864912017408925
[88.04102040816326, 36.99857142857143]
2.3795789136921996
[86.05571428571429, 33.73489795918368]
2.550940405684176
[85.14632653061224, 31.147755102040815]
2.733626428346787
[84.8730612244898, 28.64469387755102]
2.9629592687323223
[89.49897959183673, 28.074897959183673]
3.187864822232076
[94.67081632653061, 28.66734693877551]
3.302391969815619
[98.55938775510204, 30.004285714285714]
3.2848436617898122
[101.01183673469387, 31.73204081632653]
3.183275772251056
[102.44775510204082, 32.84530612244898]
3.1190988057809643
[100.45612244897958, 34.34979591836735]
2.9245042004824313
[98.67693877551021, 34.61918367346939]
2.850354292181992
[97.69183673469388, 34.608163265306125]
2.8227974997051537
[99.16571428571429, 35.08428571428571]
2.826499450303351
[134.55877551020407, 37.82163265306122]
3.557719909780603
[204.12591836734694, 42.99142857142857]
4.748060837945865
[213.0804081632653, 50.07367346938776]
4.255338052909794
[212.88795918367347, 56.05816326530612]
3.7976263720261394
[201.3261224489796, 75.20081632653061]
2.6771800132434516
[199.3338775510204, 72.6426530612245]
2.744033555368887
[193.11836734693878, 73.04]
2.6440083152647693
[179.4004081632653, 71.52857142857142]
2.5080943821507033
[148.05510204081634, 75.85857142857142]
1.9517254181384802
[137.97530612244898, 78.10979591836735]
1.7664276868249298
[127.28244897959183, 78.71244897959184]
1.617056140796648
[125.47285714285714, 79.68836734693878]
1.5745442066416884
[131.73632653061225, 79.29183673469387]
1.6614109592566855
[135.9073469387755, 79.68959183673469]
1.7054591924277618
[131.59673469387755, 79.71755102040817]
1.650787474143404
[130.0161224489796, 79.99897959183673]
1.6252222604880164
[129.42244897959185, 78.9730612244898]
1.638817680014885
[130.3830612244898, 78.03530612244899]
1.6708214230607286
[130.53163265306122, 77.75448979591837]
1.678766499473749
[141.4708163265306, 68.05489795918368]
2.07877493859999
[112.3534693877551, 47.625510204081635]
2.359102693205922
[97.68102040816326, 55.49857142857143]
1.7600636898173514
[206.76938775510203, 153.34020408163266]
1.3484355847408789
[216.64285714285714, 157.27612244897958]
1.3774681990467825
[216.1495918367347, 155.57591836734693]
1.3893512190386739
[216.23469387755102, 167.63918367346938]
1.2898815726682185
[216.09163265306123, 169.95142857142858]
1.2714905339100486
[215.63551020408164, 171.87367346938777]
1.2546162879476026
[214.18571428571428, 171.33]
1.250135494576048
[213.25204081632654, 169.65571428571428]
1.2569693966051296
[212.57897959183674, 168.66571428571427]
1.2603567980137018
[212.1230612244898, 167.5804081632653]
1.2657986906072503
[211.81571428571428, 167.2365306122449]
1.2665636718859636
[211.98938775510203, 167.58081632653062]
1.2649979419007094
[212.33020408163264, 168.314693877551]
1.2615072349898515
[212.58897959183673, 168.42489795918368]
1.2622182478231683
[212.5791836734694, 168.38795918367347]
1.2624369622628018
[212.68326530612245, 168.1269387755102]
1.2650159864630952
[212.64816326530612, 168.19102040816327]
1.2643253055320967
[212.75510204081633, 168.33551020408163]
1.2638753509754572
[212.6157142857143, 168.06142857142856]
1.265107146196544
[211.61469387755102, 166.14102040816326]
1.2737052737347545
[211.28142857142856, 165.27469387755102]
1.2783652694462897
[211.22918367346938, 165.16530612244898]
1.2788956024267586
[210.57591836734693, 164.2661224489796]
1.2819193344796398
[210.52612244897958, 164.1530612244898]
1.2824989121651023
[210.40795918367348, 163.904693877551]
1.2837213761606112
[210.07387755102042, 163.59224489795918]
1.2841310276171967
[209.80244897959184, 163.10632653061225]
1.2862925273485055
[209.80285714285714, 163.27469387755102]
1.2849686143046775
[209.8165306122449, 163.13061224489795]
1.2861873545675182
[209.52551020408163, 163.02959183673468]
1.2851992564264658
[209.4961224489796, 162.71857142857144]
1.2874751825174553
[209.39714285714285, 162.55326530612246]
1.2881755556420438
[209.39979591836735, 162.66]
1.2873465874730563
[209.37775510204082, 162.49816326530612]
1.288493056750406
[209.54367346938776, 162.68367346938774]
1.2880436555228
[209.50795918367348, 162.49979591836734]
1.289281368014277
[209.73142857142858, 162.75857142857143]
1.2886045062362308
[209.48897959183674, 162.59142857142857]
1.2884380279604066
[209.19591836734693, 162.65102040816328]
1.286164192775317
[209.24795918367346, 162.62857142857143]
1.2866617307499246
[209.17938775510203, 162.63816326530613]
1.286164228342119
[209.34632653061223, 162.6330612244898]
1.2872310522498374
[209.45897959183674, 162.53408163265306]
1.2887080511842415
[209.2104081632653, 162.53408163265306]
1.287178701609835
[209.24673469387756, 162.76408163265307]
1.2855829897786204
[209.4822448979592, 162.80163265306123]
1.286733071924265
[209.5934693877551, 163.28061224489795]
1.2836396587819894
[209.66326530612244, 163.34591836734694]
1.2835537453382393
[209.66163265306122, 163.8208163265306]
1.279822902573992
[209.46326530612245, 163.4787755102041]
1.2812872169638199
[209.45857142857142, 163.3108163265306]
1.2825762318753646
[209.27183673469386, 162.95897959183674]
1.2841994792729858
[209.6377551020408, 162.87897959183672]
1.2870767954672746
[209.66, 162.3161224489796]
1.2916769870836575
[209.51673469387754, 161.94367346938776]
1.2937630115787297
[209.44122448979593, 160.3691836734694]
1.3059942046985973
[209.18428571428572, 160.26510204081632]
1.305239150947601
[209.04285714285714, 160.2361224489796]
1.30459258466778
[208.9361224489796, 159.32591836734693]
1.3113756041076117
[208.7791836734694, 158.47530612244898]
1.3174240755979494
[208.65795918367348, 158.45551020408163]
1.3168236239619182
[208.68367346938774, 157.82755102040815]
1.3222258859126792
[208.41102040816327, 157.7969387755102]
1.3207545217633099
[208.33938775510205, 157.41938775510204]
1.3234671454777633
[208.52612244897958, 157.3665306122449]
1.3250983016381876
[208.54020408163265, 156.90448979591838]
1.3290901003079996
[208.30244897959184, 156.38020408163266]
1.3320256883080615
[208.38489795918366, 155.69918367346938]
1.338381441974713
[208.63571428571427, 155.56938775510204]
1.341110338585053
[208.64020408163265, 155.20448979591836]
1.344292322702636
[208.59897959183672, 154.90836734693877]
1.3465959467809145
[208.58346938775512, 154.1812244897959]
1.3528461074166633
[208.61877551020407, 154.40816326530611]
1.351086439333862
[208.58142857142857, 154.72142857142856]
1.3481095055629935
[208.44795918367348, 155.16530612244898]
1.3433928266101984
[208.23673469387754, 155.53244897959183]
1.3388636008759902
[208.2316326530612, 156.97530612244898]
1.3265247751173652
[208.51061224489797, 157.55897959183673]
1.3233813317720997
[208.63734693877552, 157.77959183673468]
1.3223341783940399
[208.79183673469387, 157.0142857142857]
1.3297633128403759
[208.82551020408164, 158.15816326530611]
1.3203587212490726
[208.54877551020408, 159.17061224489797]
1.310221607926804
[208.36836734693878, 158.90918367346939]
1.311241820832076
[208.52183673469386, 158.48265306122448]
1.3157391847430673
[208.41122448979593, 157.32183673469387]
1.3247444144785745
[208.49693877551022, 155.654693877551]
1.3394837867178528
[208.5265306122449, 155.24428571428572]
1.3432154984178983
[208.36163265306124, 154.87448979591838]
1.3453579923176766
[208.19040816326532, 154.68020408163267]
1.3459408681242273
[208.13897959183674, 154.5361224489796]
1.3468629618331096
[208.0104081632653, 154.7565306122449]
1.3441139274726464
[207.98265306122448, 156.69448979591837]
1.3273131258929698
[208.10755102040815, 157.80877551020407]
1.3187324364414177
[208.09591836734694, 158.8677551020408]
1.3098688165744325
[208.49285714285713, 160.1030612244898]
1.3022415408442265
[208.4765306122449, 160.5777551020408]
1.2982902300494006
[208.73816326530613, 160.93632653061223]
1.297023287191791
[208.50938775510204, 160.40632653061223]
1.2998825686299207
[208.47142857142856, 160.63755102040815]
1.2977751917105818
[208.5495918367347, 160.86061224489796]
1.296461507427523
[208.6026530612245, 160.94244897959183]
1.296131967568582
[208.47306122448978, 160.95142857142858]
1.295254494320761
[208.40755102040816, 160.80102040816325]
1.296058635022369
[208.2426530612245, 160.33326530612246]
1.2988112770212046
[208.27244897959184, 159.83408163265307]
1.303054059886081
[207.9938775510204, 159.8065306122449]
1.3015355302074447
[207.9991836734694, 159.58959183673468]
1.303338026493979
[207.90285714285713, 159.48285714285714]
1.3036062989304715
[207.78, 159.2261224489796]
1.3049366322826734
[208.08326530612246, 159.14816326530612]
1.307481412520229
[207.8561224489796, 159.19510204081632]
1.3056690801686033
[207.95489795918368, 159.32326530612244]
1.3052387393618932
[207.98204081632653, 159.66469387755103]
1.302617602961308
[208.06714285714287, 159.4257142857143]
1.3051040341224753
[208.18714285714285, 159.48510204081632]
1.3053704715557848
[208.14081632653063, 159.57673469387754]
1.304330588828099
[208.0695918367347, 159.5904081632653]
1.303772540163403
[207.9373469387755, 159.7869387755102]
1.3013413269711196
[208.01408163265307, 160.05020408163264]
1.299680202385476
[207.97530612244898, 159.86408163265307]
1.3009508077014402
[208.0404081632653, 160.12591836734694]
1.2992300702126005
[208.0865306122449, 160.01795918367347]
1.3003948536388772
[207.97326530612244, 160.13448979591837]
1.2987412366391005
[208.04102040816326, 160.29897959183674]
1.2978312209964797
[208.09448979591838, 160.05448979591836]
1.3001477813040714
[208.0395918367347, 160.2969387755102]
1.2978388322691943
[208.14448979591836, 160.37448979591838]
1.297865327963249
[208.24551020408163, 160.15061224489796]
1.3003104220771773
[208.0569387755102, 160.45469387755102]
1.2966709402361656
[207.57816326530613, 160.07163265306122]
1.2967829453905204
[207.35734693877552, 160.1330612244898]
1.294906531812829
[207.04448979591837, 159.84448979591838]
1.2952870008860653
[206.84571428571428, 159.81489795918367]
1.294283054503105
[206.44918367346938, 159.56163265306122]
1.2938522891800495
[206.24632653061224, 159.10857142857142]
1.2962615695610236
[206.14448979591836, 159.21163265306123]
1.2947828394243575
[206.3534693877551, 159.12285714285716]
1.296818528104327
[206.24061224489796, 159.00918367346938]
1.2970358534034103
[206.2287755102041, 159.02510204081634]
1.2968315873633094
[205.94204081632654, 158.79408163265308]
1.2969125719228214
[205.79877551020408, 158.7995918367347]
1.2959653934236195
[205.79673469387754, 158.81061224489795]
1.295862611350704
[205.49857142857144, 158.71897959183673]
1.2947321861382524
[205.84979591836733, 158.7234693877551]
1.2969083697098662
[205.845306122449, 158.62081632653062]
1.2977193718301379
[205.90204081632652, 158.78714285714287]
1.2967173356193695
[206.0169387755102, 158.61448979591836]
1.298853207172827
[206.10530612244898, 158.78408163265306]
1.2980224717945819
[206.15755102040816, 158.55530612244897]
1.300224861987255
[206.15510204081633, 158.83285714285714]
1.297937377373982
[206.19326530612244, 158.94591836734693]
1.2972542322828327
[206.46367346938774, 158.61183673469387]
1.3016914608632548
[206.08489795918368, 154.08979591836734]
1.3374337783428694
[204.80755102040817, 152.11632653061224]
1.3463877000684226
[203.54183673469387, 149.76244897959182]
1.359097945590023
[202.0830612244898, 148.02469387755102]
1.3651983053020662
[199.94591836734693, 145.15]
1.3775123552693553
[198.59510204081633, 142.6777551020408]
1.3919135600275203
[197.8530612244898, 141.27979591836734]
1.4004342230138198
[197.57816326530613, 140.13734693877552]
1.4098894233499788
[197.5538775510204, 139.8469387755102]
1.4126435607442538
[199.49959183673468, 142.5326530612245]
1.3996764078406665
[200.6342857142857, 143.84102040816327]
1.3948335818597912
[203.11142857142858, 145.01877551020408]
1.4005871160947492
[206.33489795918368, 146.53061224489795]
1.4081350974930362
[207.65163265306123, 149.3138775510204]
1.3907055128355827
[207.79061224489797, 155.74244897959184]
1.3341938155353292
[207.3187755102041, 160.07591836734693]
1.2951278220028253
[207.19020408163266, 161.3222448979592]
1.2843250737843763
[207.01530612244898, 161.52244897959184]
1.2816503676749298
[207.05979591836734, 161.35020408163265]
1.283294292045696
[206.92877551020408, 161.17938775510203]
1.2838414290580025
[206.87020408163266, 161.14020408163265]
1.2837901333228638
[206.86612244897958, 160.78408163265306]
1.2866082285534408
[206.92591836734695, 160.78510204081633]
1.2869719628303466
[206.97224489795917, 160.7908163265306]
1.287214342376646
[207.13, 160.86122448979592]
1.2876316256882596
[207.23510204081632, 160.89469387755102]
1.2880170069407801
[207.2391836734694, 160.97244897959183]
1.2874202075396348
[207.2191836734694, 160.89204081632653]
1.2879393077624621
[207.23367346938775, 160.9038775510204]
1.2879346142772528
[207.4508163265306, 161.05673469387756]
1.2880604882548676
[207.58469387755102, 161.09081632653061]
1.2886190449043193
[207.55979591836734, 161.11265306122448]
1.2882898516945933
[207.56551020408162, 161.16183673469388]
1.2879321457832347
[207.72142857142856, 161.4334693877551]
1.2867308703655007
[207.78979591836736, 161.46448979591835]
1.2869070851491957
[207.73510204081632, 161.63836734693876]
1.2851843621690142
[207.67204081632653, 161.67714285714285]
1.2844860884251557
[207.51938775510203, 161.7191836734694]
1.2832082319566291
[207.46938775510205, 161.75571428571428]
1.2826093264850122
[207.58265306122448, 161.9251020408163]
1.2819670974108714
[207.48591836734693, 161.95326530612246]
1.2811468665059584
[207.53510204081633, 161.96142857142857]
1.2813859686924702
[207.69755102040816, 161.815306122449]
1.2835470018098234
[207.4742857142857, 161.94367346938776]
1.2811509166704471
[207.5734693877551, 161.88020408163266]
1.2822659235287368
[207.66367346938776, 162.02102040816325]
1.281708218762242
[207.58142857142857, 162.00591836734694]
1.281320032399925
[207.71775510204083, 162.03673469387755]
1.2819176805461097
[207.70755102040818, 162.02326530612245]
1.2819612703642964
[207.6465306122449, 162.10816326530613]
1.2809134742487378
[207.67183673469387, 162.30877551020407]
1.2794861897139869
[207.55367346938775, 162.39081632653063]
1.2781121381399116
[207.4834693877551, 162.4065306122449]
1.277556195588797
[207.33836734693878, 162.30979591836734]
1.2774236217462702
[207.53326530612244, 162.4326530612245]
1.2776573022414313
[207.41142857142856, 162.70204081632653]
1.2747930359741106
[207.57551020408164, 162.72285714285715]
1.2756383082792577
[207.61448979591836, 162.8291836734694]
1.2750447131901088
[207.60244897959183, 162.9461224489796]
1.274055779048039
[207.4708163265306, 162.59163265306123]
1.276023943798097
[207.46224489795918, 162.49877551020407]
1.276700358181663
[207.5291836734694, 162.5904081632653]
1.2763925376525211
[207.42244897959185, 162.24448979591835]
1.2784560464303056
[207.42122448979592, 162.38489795918366]
1.2773430725185564
[207.5630612244898, 162.13734693877552]
1.2801681114399104
[207.5416326530612, 162.09163265306123]
1.2803969536001933
[207.61530612244897, 162.2838775510204]
1.2793341473935194
[207.62224489795918, 162.3534693877551]
1.2788285072127834
[207.54673469387754, 162.64979591836735]
1.2760343996868193
[207.61938775510205, 162.69938775510204]
1.2760920039085482
[207.59979591836733, 162.6169387755102]
1.2766185213027235
[207.7930612244898, 162.70795918367347]
1.277092173406968
[207.71367346938774, 162.56571428571428]
1.2777212857092641
[207.6104081632653, 162.50591836734694]
1.2775559822624984
[207.64979591836735, 162.57795918367347]
1.2772321473403025
[207.5491836734694, 162.74755102040817]
1.275282991185798
[207.78775510204082, 162.93551020408162]
1.2752760576364257
[207.75408163265305, 162.8738775510204]
1.2755518856458359
[207.58428571428573, 162.80591836734695]
1.275041397732871
[207.51061224489797, 162.65632653061223]
1.2757610888614535
[207.4291836734694, 162.6895918367347]
1.2749997177547325
[207.54061224489797, 162.5612244897959]
1.276691984181784
[207.2804081632653, 162.69673469387754]
1.274029307061843
[207.24367346938774, 162.4408163265306]
1.2758103422282527
[207.19285714285715, 162.41734693877552]
1.2756818224654298
[207.2765306122449, 162.4804081632653]
1.2757016858547467
[207.1430612244898, 162.38979591836735]
1.2755916100086715
[207.09285714285716, 162.29142857142858]
1.2760554205837822
[207.22551020408164, 162.2661224489796]
1.277071930212903
[207.13734693877552, 162.33591836734695]
1.2759797648111877
[207.30448979591836, 162.25061224489795]
1.2776807860855215
[207.36448979591836, 162.19918367346938]
1.278455816481625
[207.5573469387755, 162.18204081632652]
1.2797800909031425
[207.41755102040815, 162.14795918367346]
1.279186935590447
[207.33877551020407, 162.1973469387755]
1.278311756779031
[207.41530612244898, 162.15163265306123]
1.2791441117724276
[207.14938775510205, 162.10489795918366]
1.2778724786419478
[207.31673469387755, 162.12551020408162]
1.2787422191172122
[207.11142857142858, 162.30673469387756]
1.2760495056601069
[207.12897959183672, 162.41734693877552]
1.2752885298016572
[207.08285714285714, 162.22632653061225]
1.2765058641932598
[207.0969387755102, 162.33102040816325]
1.2757693400484273
[207.14265306122448, 162.2726530612245]
1.27650993037669
[207.06979591836733, 162.3826530612245]
1.2751965312470543
[207.06897959183672, 162.53244897959183]
1.2740162403990913
[207.07591836734693, 162.43102040816328]
1.2748545065283599
[207.26020408163265, 162.4551020408163]
1.2757999070386796
[207.35163265306122, 162.32979591836735]
1.2773479537751313
[207.3104081632653, 162.26591836734693]
1.2775967390388414
[207.5765306122449, 162.3108163265306]
1.2788829192667635
[207.38061224489795, 162.62775510204082]
1.2751858507471676
[207.54979591836735, 162.6369387755102]
1.2761540980850048
[207.43081632653062, 162.58897959183673]
1.275798746306575
[207.4857142857143, 162.37836734693877]
1.2777916028826601
[207.36959183673468, 162.42857142857142]
1.2766817439376807
[207.42408163265307, 162.41204081632654]
1.2771471905043734
[207.55714285714285, 162.3577551020408]
1.2783937713766398
[207.18408163265306, 162.4234693877551]
1.2755797078686981
[207.10836734693876, 162.3534693877551]
1.275663329696354
[207.16673469387754, 162.50489795918367]
1.2748337883693301
[207.28979591836736, 162.23673469387754]
1.2776995068934287
[207.5838775510204, 162.46755102040817]
1.2776943841847226
[207.56551020408162, 162.29102040816326]
1.2789710094991864
[207.4557142857143, 162.21081632653062]
1.2789265166393444
[207.56571428571428, 162.35755102040815]
1.2784481718354048
[207.4930612244898, 162.46367346938774]
1.27716588449286
[207.66795918367347, 162.45204081632653]
1.2783339509933858
[207.3673469387755, 162.48489795918368]
1.2762253572074516
[207.4134693877551, 162.35489795918366]
1.277531334101785
[207.11102040816326, 162.2881632653061]
1.2761930151959477
[207.12408163265306, 162.28510204081633]
1.2762975715451643
[207.30326530612246, 162.16632653061225]
1.2783373080045053
[207.43795918367346, 162.24061224489796]
1.2785822015424306
[207.4487755102041, 162.3795918367347]
1.2775544830706582
[207.53020408163266, 162.43816326530612]
1.2775951162577408
[207.50673469387755, 162.4108163265306]
1.277665733030247
[207.6077551020408, 162.34020408163266]
1.278843748389311
[207.50408163265305, 162.30673469387756]
1.2784687094101241
[207.48102040816326, 162.44653061224489]
1.2772265411036348
[207.41448979591837, 162.55877551020407]
1.2759353602715753
[207.40918367346939, 162.6442857142857]
1.2752319133905594
[207.4026530612245, 162.45591836734692]
1.2766703432265458
[207.4204081632653, 162.48326530612246]
1.2765647451291686
[207.54387755102042, 162.5404081632653]
1.2768755775643859
[207.3487755102041, 162.4830612244898]
1.276125486235928
[207.5338775510204, 162.69938775510204]
1.275566432145424
[207.46897959183673, 162.59632653061223]
1.2759758108851018
[207.33755102040817, 162.77530612244897]
1.2737653883718512
[207.15448979591838, 162.45632653061224]
1.2751395665522665
[207.4134693877551, 162.70673469387756]
1.2747688027664648
[207.22163265306122, 162.52448979591836]
1.2750178936926304
[207.3222448979592, 162.45591836734692]
1.2761753894934138
[207.46142857142857, 162.48061224489797]
1.2768380528917107
[207.34714285714287, 162.63]
1.2749624476243182
[207.4612244897959, 162.435306122449]
1.2771929295556284
[207.54244897959182, 162.44551020408164]
1.277612712834319
[207.58102040816325, 162.56]
1.2769501747549412
[207.63489795918366, 162.53938775510204]
1.2774435835332847
[207.57326530612244, 162.6642857142857]
1.276083833612486
[207.71285714285713, 162.78061224489795]
1.276029462466698
[207.57469387755103, 162.70612244897958]
1.2757644933898604
[207.37428571428572, 162.5157142857143]
1.276026054623289
[207.07755102040815, 162.27591836734695]
1.2760830633639857
[206.96755102040817, 161.92897959183674]
1.2781378079581374
[206.8004081632653, 161.63795918367347]
1.2794049690287945
[206.6273469387755, 161.3434693877551]
1.2806675579920135
[206.61938775510205, 161.31632653061226]
1.2808337023214624
[206.65775510204082, 161.26510204081632]
1.2814784630200748
[206.7361224489796, 161.35755102040815]
1.2812299216342968
[206.7661224489796, 161.2808163265306]
1.2820255201980066
[206.5095918367347, 161.31510204081633]
1.2801627945812732
[206.66510204081632, 161.21204081632652]
1.2819458211330241
[206.55979591836734, 161.11163265306124]
1.282091134680352
[206.53673469387755, 161.32714285714286]
1.2802354956274675
[206.51857142857142, 161.2016326530612]
1.2811196017663264
[206.50489795918367, 161.32938775510203]
1.2800203411957283
[206.54938775510203, 161.41510204081632]
1.2796162511663425
[206.33183673469387, 161.2622448979592]
1.2794801217436422
[206.58428571428573, 161.34183673469389]
1.2804136229959207
[206.7304081632653, 161.36489795918368]
1.281136175077907
[206.77428571428572, 161.3481632653061]
1.2815409951353773
[206.77061224489796, 161.37102040816328]
1.2813367091681231
[206.70061224489797, 161.36265306122448]
1.2809693465220313
[206.80061224489796, 161.26530612244898]
1.2823626929891168
[206.73326530612246, 160.98408163265307]
1.2841845181802738
[206.7630612244898, 161.11163265306124]
1.2833527773238735
[206.72285714285715, 161.18816326530612]
1.2824940303004981
[206.68795918367346, 161.3622448979592]
1.2808941727005405
[206.84918367346938, 161.4765306122449]
1.2809860534480908
[206.5165306122449, 161.08775510204083]
1.282012592958585
[206.51734693877552, 161.16448979591837]
1.2814072578909113
[206.51897959183674, 161.05163265306123]
1.282315343159058
[206.35510204081632, 161.03244897959183]
1.2814504365326294
[206.45061224489797, 161.07857142857142]
1.2816764540058407
[206.3108163265306, 161.0361224489796]
1.2811461999272566
[206.46857142857144, 161.09795918367348]
1.2816336871975473
[206.42061224489797, 161.05408163265307]
1.2816850721965622
[206.43367346938774, 161.11183673469387]
1.281306685177491
[206.3461224489796, 161.0065306122449]
1.2816009491312308
[206.42, 161.22489795918366]
1.2803233409535673
[206.3734693877551, 161.3522448979592]
1.2790244692180626
[206.3622448979592, 161.0134693877551]
1.2816458503915251
[206.33102040816325, 161.2534693877551]
1.2795446894355698
[206.36265306122448, 160.99877551020407]
1.2817653575765566
[206.2095918367347, 161.01979591836735]
1.2806474549332887
[206.39408163265307, 161.12897959183672]
1.2809246490325916
[206.6281632653061, 161.03367346938776]
1.283136370261005
[206.55, 160.99469387755101]
1.282961537583949
[206.46061224489796, 161.07163265306122]
1.2817937512907809
[206.58591836734695, 160.84755102040816]
1.2843584938457382
[206.37775510204082, 160.69795918367348]
1.2842587183459906
[206.4695918367347, 160.934693877551]
1.2829402216642574
[206.5395918367347, 160.83897959183673]
1.2841389093668278
[206.44061224489795, 160.90081632653062]
1.283030235383948
[206.45551020408163, 161.09102040816327]
1.2816078120368
[206.2418367346939, 160.88938775510204]
1.2818858944794118
[206.38979591836735, 161.16653061224488]
1.2805996079603301
[206.29530612244898, 160.8338775510204]
1.2826607756006325
[206.4991836734694, 160.82551020408164]
1.2839952033196074
[206.5238775510204, 160.79061224489797]
1.2844274592130211
[206.42612244897958, 160.64836734693878]
1.2849562423698861
[206.35755102040815, 160.90897959183673]
1.2824489443899074
[206.60734693877552, 160.89510204081634]
1.2841120973736215
[206.39326530612246, 161.0191836734694]
1.2817930174373948
[206.41714285714286, 160.8530612244898]
1.2832652439798016
[206.45530612244897, 161.07673469387754]
1.2817202094071023
[206.5169387755102, 160.8738775510204]
1.2837195318426655
[206.41795918367347, 160.8134693877551]
1.28358625660862
[206.55367346938775, 161.08795918367346]
1.2822415437883474
[206.4326530612245, 160.76530612244898]
1.2840622024754047
[206.4877551020408, 161.07163265306122]
1.2819622654896858
[206.4834693877551, 161.14979591836735]
1.2813138745292123
[206.47469387755103, 161.00204081632654]
1.2824352587747652
[206.41285714285715, 161.2383673469388]
1.280172086453318
[206.2757142857143, 160.93020408163267]
1.2817712837863542
[206.33081632653062, 160.99571428571429]
1.2815919805191924
[206.4442857142857, 161.0408163265306]
1.2819376504878977
[206.1973469387755, 160.9769387755102]
1.280912337551202
[206.38877551020408, 161.0265306122449]
1.2817066524720226
[206.3826530612245, 161.05163265306123]
1.281468865986697
[206.2691836734694, 161.09857142857143]
1.2803911409290547
[206.33612244897958, 160.9795918367347]
1.2817532961460445
[206.34408163265306, 161.0008163265306]
1.2816337602547332
[206.27795918367346, 161.08673469387756]
1.2805397016438094
[206.25551020408165, 161.09285714285716]
1.2803516795358236
[206.3261224489796, 161.09938775510204]
1.2807380917091362
[206.3734693877551, 161.0273469387755]
1.281605101934771
[206.2038775510204, 161.13285714285715]
1.2797134067337006
[206.37857142857143, 160.9634693877551]
1.282145397421902
[206.31142857142856, 160.93591836734694]
1.281947688647782
[206.57938775510203, 161.09591836734694]
1.2823378136995325
[206.46775510204083, 160.85510204081632]
1.2835636077595505
[206.39020408163265, 160.88714285714286]
1.2828259636936525
[206.62714285714284, 161.02591836734695]
1.2831918299373783
[206.4551020408163, 160.75408163265305]
1.284291508769257
[206.47326530612244, 160.93102040816328]
1.2829923328793422
[206.52714285714285, 160.91489795918366]
1.2834556991082877
[206.4516326530612, 160.8942857142857]
1.2831508076034206
[206.55081632653062, 160.96102040816328]
1.283235008095508
[206.55673469387756, 160.90285714285713]
1.2837356549267909
[206.64938775510205, 160.874693877551]
1.2845363231111553
[206.4108163265306, 160.9265306122449]
1.2826400689882567
[206.34020408163266, 160.84673469387755]
1.2828373822716264
[206.37632653061223, 160.96489795918367]
1.2821200718118286
[206.35122448979592, 160.82183673469387]
1.2831045129164356
[206.19204081632654, 160.86020408163265]
1.281808897318625
[206.39183673469387, 160.9918367346939]
1.2820018761250411
[206.23897959183674, 160.83265306122448]
1.2823203228098672
[206.5495918367347, 160.9426530612245]
1.2833738471936385
[206.66469387755103, 160.83959183673468]
1.2849118274767357
[206.91448979591837, 161.0734693877551]
1.284596964244989
[206.66551020408164, 161.00204081632654]
1.2836204383262984
[206.53204081632654, 160.98367346938775]
1.2829378058365661
[206.6104081632653, 161.2095918367347]
1.2816260236705417
[206.46836734693878, 160.97857142857143]
1.2825829271230167
[206.6757142857143, 161.0183673469388]
1.2835536572073156
[206.7430612244898, 161.05061224489796]
1.283714841829416
[206.69530612244898, 161.06244897959184]
1.2833239990572805
[206.6873469387755, 161.10448979591837]
1.282939707022442
[206.60020408163265, 161.10204081632654]
1.2824182923739549
[206.40836734693877, 160.87795918367348]
1.2830120943496273
[206.4665306122449, 160.91061224489795]
1.2831132001288585
[206.5981632653061, 160.93510204081633]
1.283735870207537
[206.56408163265306, 161.08591836734695]
1.2823224011523828
[206.6395918367347, 161.28857142857143]
1.2811793793353021
[206.5108163265306, 161.07551020408164]
1.282074575240412
[206.5769387755102, 161.05816326530612]
1.2826232125547241
[206.45285714285714, 160.97285714285715]
1.2825321039039412
[206.6869387755102, 161.04816326530613]
1.2833858802538471
[206.41632653061225, 161.10938775510203]
1.2812184901625971
[206.62551020408162, 161.32265306122449]
1.2808214239178424
[206.5869387755102, 161.185306122449]
1.2816735206531207
[206.47714285714287, 161.0791836734694]
1.2818362878949128
[206.5969387755102, 161.03938775510204]
1.2828969462408106
[206.7242857142857, 160.98285714285714]
1.2841385063183302
[206.81795918367348, 160.9838775510204]
1.2847122477723083
[206.70857142857142, 160.99448979591835]
1.2839481133211557
[206.55346938775511, 161.0530612244898]
1.2825181205332252
[206.59163265306123, 161.0483673469388]
1.2827924682279501
[206.55081632653062, 161.07755102040815]
1.2823066592337322
[206.5191836734694, 160.89122448979592]
1.283595076912149
[206.54142857142858, 161.00571428571428]
1.2828204855195913
[206.58408163265307, 160.88571428571427]
1.2840424182459347
[206.5, 160.87326530612245]
1.2836191247007722
[206.64163265306124, 160.96102040816328]
1.2837992212590448
[206.5661224489796, 160.91326530612244]
1.2837109610323727
[206.6165306122449, 160.97897959183675]
1.2835000640215415
[206.8542857142857, 161.08]
1.2841711305828514
[206.59918367346938, 161.18775510204082]
1.2817300144336683
[206.74673469387756, 161.07367346938776]
1.2835538560754933
[206.71795918367346, 161.0748979591837]
1.2833654517419326
[206.7791836734694, 161.23795918367347]
1.2824472892138126
[206.6573469387755, 161.0661224489796]
1.283059055477279
[206.77959183673468, 161.20795918367347]
1.282688478185738
[206.72244897959183, 161.09448979591838]
1.2832372431948291
[206.84897959183672, 161.16775510204081]
1.2834389823254257
[206.75775510204082, 161.31775510204082]
1.2816800913901705
[206.57244897959183, 161.0457142857143]
1.2826944814756616
[206.5122448979592, 161.22040816326532]
1.2809311628142483
[206.49428571428572, 161.11428571428573]
1.281663415499202
[206.44571428571427, 161.02408163265306]
1.2820797497648975
[206.4726530612245, 160.93673469387755]
1.2829429741690865
[206.3787755102041, 160.9434693877551]
1.282305994118863
[206.4018367346939, 160.93244897959184]
1.2825371020164373
[206.4373469387755, 160.89244897959185]
1.2830766654870218
[206.39755102040817, 161.12244897959184]
1.2809981000633313
[206.44061224489795, 161.01510204081632]
1.2821195628753292
[206.49244897959184, 161.18428571428572]
1.2810954124003073
[206.70408163265307, 161.26367346938775]
1.2817770870876952
[206.595306122449, 161.02714285714285]
1.2829843618707963
[206.50061224489795, 161.03918367346938]
1.28230041617454
[206.80428571428573, 161.1365306122449]
1.28341031626115
[206.42632653061224, 161.2404081632653]
1.2802394193990974
[206.5061224489796, 161.12448979591838]
1.2816557105039834
[206.50040816326532, 161.35204081632654]
1.2798128063241108
[206.5095918367347, 160.98326530612246]
1.2828016094967407
[206.6973469387755, 161.13816326530613]
1.2827336662542093
[206.58224489795919, 160.97551020408164]
1.2833147392175257
[206.6469387755102, 161.0722448979592]
1.2829456676811266
[206.65571428571428, 160.99469387755101]
1.2836181696950337
[206.8026530612245, 160.96816326530612]
1.2847425780734942
[206.63551020408164, 160.98326530612246]
1.283583792459097
[206.6995918367347, 161.11183673469387]
1.282957205541087
[206.72183673469388, 160.99816326530612]
1.284001211827743
[206.67836734693878, 161.28714285714287]
1.2814311400506386
[206.85673469387754, 161.12020408163266]
1.2838658930016755
[206.76551020408164, 161.28102040816327]
1.2820201018124024
[206.8057142857143, 161.08489795918368]
1.283830557089936
[206.79326530612244, 161.2022448979592]
1.28281876866555
[206.815306122449, 161.1969387755102]
1.282997727459756
[206.81632653061226, 161.19591836734693]
1.28301217937356
[206.56795918367348, 161.10510204081632]
1.282193776404046
[206.75510204081633, 161.125306122449]
1.2831944715356536
[206.72122448979593, 160.9269387755102]
1.2845656921254671
[206.6526530612245, 161.19816326530614]
1.2819789560573815
[206.4691836734694, 161.45734693877552]
1.278784691982845
[206.4795918367347, 161.22857142857143]
1.2806637806637806
[206.57285714285715, 161.37244897959184]
1.2800999083119922
[206.78775510204082, 161.1891836734694]
1.2828885312859653
[206.82551020408164, 161.09632653061223]
1.2838623614721578
[206.80530612244897, 161.28836734693877]
1.2822084414655965
[206.57673469387754, 161.08612244897958]
1.282399324990308
[206.62551020408162, 161.2561224489796]
1.2813498617359884
[206.74591836734695, 161.15836734693877]
1.282874242094226
[206.565306122449, 161.07142857142858]
1.2824453595185301
[206.5769387755102, 161.11265306122448]
1.2821894174693331
[206.51, 161.1008163265306]
1.281868116555231
[206.25163265306122, 160.94448979591837]
1.2815078845792947
[206.31326530612245, 160.91469387755103]
1.2821281906245163
[206.4230612244898, 160.96163265306123]
1.2824364279990668
[206.5369387755102, 161.01265306122448]
1.282737318147135
[206.54408163265308, 160.96571428571428]
1.2831557487207317
[206.5226530612245, 160.94489795918366]
1.2831885675158188
[206.61408163265307, 161.25673469387755]
1.281274124921851
[206.75755102040816, 161.30448979591836]
1.2817842285853096
[206.5761224489796, 161.2634693877551]
1.280985230153216
[206.69571428571427, 161.20367346938775]
1.2822022590258488
[206.71020408163264, 161.10020408163265]
1.2831157183195652
[206.76591836734693, 160.9912244897959]
1.2843303665936918
[206.72571428571428, 161.18102040816328]
1.2825685912784077
[206.88408163265305, 161.30163265306123]
1.2825913676747074
[206.89591836734695, 161.16061224489795]
1.2837871207199816
[206.8938775510204, 161.3638775510204]
1.2821573247432916
[206.8634693877551, 161.24142857142857]
1.2829424250363568
[206.96755102040817, 161.1634693877551]
1.284208833469883
[206.87204081632652, 161.15244897959184]
1.2837039841853384
[206.98183673469387, 161.24755102040817]
1.2836277848864655
[206.82857142857142, 161.20265306122448]
1.2830345375892684
[206.90448979591838, 161.11122448979592]
1.2842338604969314
[206.81775510204082, 161.06836734693877]
1.284037073875335
[206.82387755102042, 161.05081632653062]
1.2842150214978414
[206.77673469387756, 161.24061224489796]
1.2824109994063886
[206.6212244897959, 161.16775510204081]
1.2820258268099407
[206.5465306122449, 161.17163265306124]
1.2815315400871932
[206.58204081632653, 161.1495918367347]
1.2819271737630014
[206.4691836734694, 161.0865306122449]
1.281728415707618
[206.4426530612245, 161.1608163265306]
1.2809729918651418
[206.22897959183675, 161.11816326530612]
1.2799859147615074
[206.32979591836735, 161.03142857142856]
1.281301406494359
[206.5065306122449, 160.99857142857144]
1.2826606396558213
[206.3391836734694, 160.9861224489796]
1.2817203156058579
[206.44795918367348, 160.93632653061223]
1.28279278913704
[206.37367346938777, 160.95877551020408]
1.2821523574295866
[206.42673469387756, 161.05224489795918]
1.2817377045856586
[206.52510204081634, 161.19591836734693]
1.281205530093941
[206.33448979591836, 161.09836734693877]
1.2807981433577151
[206.51816326530613, 161.04102040816326]
1.2823947758271756
[206.58897959183673, 161.10122448979592]
1.2823551170768537
[206.48795918367347, 161.11612244897958]
1.2816095375499228
[206.4361224489796, 160.9926530612245]
1.2822704547298394
[206.35795918367347, 161.00020408163266]
1.2817248298582458
[206.36163265306124, 161.09979591836733]
1.280955270468679
[206.24, 161.034693877551]
1.280717807038666
[206.07795918367347, 161.07285714285715]
1.2794083549464876
[206.34183673469389, 161.0695918367347]
1.2810725747902099
[206.42755102040817, 161.13326530612244]
1.281098292324898
[206.51551020408164, 161.1212244897959]
1.2817399498919562
[206.43081632653062, 161.1057142857143]
1.281337643681801
[206.7334693877551, 161.05714285714285]
1.2836032337362833
[206.61857142857144, 160.88061224489795]
1.2842975206611573
[206.62489795918367, 161.04387755102042]
1.2830347921405625
[206.60632653061225, 160.7983673469388]
1.2848782605164029
[206.58775510204083, 160.97061224489795]
1.2833880186014435
[206.57326530612244, 161.23448979591836]
1.2811977484940806
[206.46428571428572, 161.01897959183674]
1.2822357105829836
[206.48734693877552, 161.18775510204082]
1.281036185459978
[206.57244897959183, 161.20673469387756]
1.2814132695625973
[206.5038775510204, 161.1273469387755]
1.281619051479119
[206.52632653061224, 161.27591836734695]
1.280577587908667
[206.58510204081634, 161.12142857142857]
1.2821702480699688
[206.66469387755103, 161.10285714285715]
1.2828120962143592
[206.6608163265306, 161.16938775510204]
1.2822584934091399
[206.46326530612245, 161.06714285714287]
1.281845953455841
[206.5665306122449, 161.1838775510204]
1.28155826594294
[206.38510204081632, 161.0973469387755]
1.2811204278817345
[206.45632653061224, 161.1130612244898]
1.2814375505095927
[206.5026530612245, 161.1026530612245]
1.2818078978671223
[206.6587755102041, 161.22387755102042]
1.2818124625789717
[206.80959183673468, 161.17469387755102]
1.2831393493686656
[206.8957142857143, 161.22775510204082]
1.2832512252916397
[206.7995918367347, 161.14897959183673]
1.2832820434887227
[206.64714285714285, 161.33367346938775]
1.280868019758771
[206.64755102040817, 161.00938775510204]
1.2834503248638056
[206.44857142857143, 160.9795918367347]
1.2824518255578092
[206.46897959183673, 161.06448979591838]
1.2819025463244536
[206.52469387755102, 161.0142857142857]
1.2826482629250795
[206.7287755102041, 160.97795918367348]
1.2842054686153004
[206.73448979591836, 161.05244897959184]
1.283646980258681
[206.5869387755102, 161.28673469387755]
1.2808675131752931
[206.5104081632653, 161.2669387755102]
1.2805501842552847
[206.40938775510205, 161.40714285714284]
1.2788119788341057
[206.30020408163264, 161.30448979591836]
1.278948926608569
[206.54142857142858, 161.38489795918366]
1.2798064204475044
[206.49081632653062, 160.9842857142857]
1.2826768489255513
[206.66142857142856, 161.10938775510203]
1.282739829447859
[206.4918367346939, 160.92244897959185]
1.2831760767006544
[206.66816326530613, 161.03836734693877]
1.28334735796261
[206.57408163265305, 160.99244897959184]
1.283129009726657
[206.54551020408164, 160.94387755102042]
1.2833387224599777
[206.5434693877551, 160.99081632653062]
1.2829518732846974
[206.70897959183674, 161.0969387755102]
1.2831341250989707
[206.4626530612245, 160.92]
1.2830142496968961
[206.4469387755102, 161.00632653061226]
1.2822287373673995
[206.67367346938775, 161.08714285714285]
1.2829929800957018
[206.58530612244897, 160.91061224489795]
1.2838513460382366
[206.5434693877551, 160.9408163265306]
1.2833504520612216
[206.5273469387755, 161.03448979591838]
1.282503811453751
[206.4891836734694, 161.0073469387755]
1.282482989748218
[206.54102040816326, 161.03183673469388]
1.282609852786114
[206.4018367346939, 160.91408163265305]
1.2826834956923394
[206.5122448979592, 161.07510204081632]
1.2820866929864128
[206.48734693877552, 160.9883673469388]
1.2826227779165182
[206.54326530612244, 161.18142857142857]
1.2814333955018364
[206.53326530612244, 161.02795918367346]
1.282592578041334
[206.4930612244898, 161.14367346938775]
1.281422079928673
[206.56571428571428, 160.9618367346939]
1.2833210559481076
[206.79448979591837, 161.05510204081634]
1.2839983780427537
[206.43061224489796, 161.00040816326532]
1.2821744652694502
[206.5495918367347, 161.03979591836736]
1.2825996869831895
[206.4, 160.99755102040817]
1.2820070783178348
[206.64612244897958, 161.21408163265306]
1.2818118638038658
[206.5234693877551, 160.94244897959183]
1.28321316530944
[206.42530612244897, 161.0734693877551]
1.281559942224362
[206.5116326530612, 161.0457142857143]
1.2823168475423379
[206.4391836734694, 160.9742857142857]
1.2824357800840291
[206.92102040816326, 161.03673469387755]
1.2849305520352816
[206.8938775510204, 161.09061224489795]
1.2843323063201848
[206.625306122449, 161.05142857142857]
1.282977170431045
[206.3269387755102, 161.0138775510204]
1.281423327688829
[206.42734693877551, 161.14081632653063]
1.2810369938829012
[206.30163265306123, 160.98244897959182]
1.2815163016883577
[206.49142857142857, 161.14551020408163]
1.2813973427489163
[206.51244897959182, 161.16387755102042]
1.2813817346521412
[206.8365306122449, 161.1730612244898]
1.2833194892548003
[206.54, 160.91571428571427]
1.2835290879875
[206.4734693877551, 160.85204081632654]
1.283623560757446
[206.50938775510204, 160.904693877551]
1.283426746470531
[206.51, 160.97163265306122]
1.282896847080421
[206.43897959183673, 160.97204081632654]
1.2824523969810957
[206.46244897959184, 160.99204081632652]
1.2824388580497705
[206.56979591836733, 161.0116326530612]
1.2829495143588308
[206.47857142857143, 161.0226530612245]
1.282295177126808
[206.38142857142856, 161.0557142857143]
1.2814287868439491
[206.57122448979592, 161.02489795918368]
1.2828526961225415
[206.5387755102041, 160.8426530612245]
1.2841045057344673
[206.6042857142857, 160.9808163265306]
1.2834093554055117
[206.37448979591838, 160.7995918367347]
1.2834267017633816
[206.4504081632653, 160.94326530612244]
1.2827527002797285
[206.58020408163264, 160.8822448979592]
1.2840460065227068
[206.38897959183674, 160.97469387755103]
1.2821206527581974
[206.33122448979591, 160.7730612244898]
1.2833693836412843
[206.1834693877551, 160.78755102040816]
1.2823347832543641
[206.16122448979593, 160.64122448979592]
1.2833643738994998
[206.13714285714286, 160.7581632653061]
1.28228102803679
[206.25142857142856, 160.68775510204082]
1.2835541105198318
[206.25204081632654, 160.8073469387755]
1.282603343333892
[206.5761224489796, 160.98979591836735]
1.2831628319705901
[206.49530612244897, 160.94061224489795]
1.2830528183168084
[206.52183673469386, 160.8691836734694]
1.2837874353480263
[206.43632653061223, 160.86020408163265]
1.2833275185070063
[206.58204081632653, 161.04367346938776]
1.282770296813895
[206.60244897959183, 161.00836734693877]
1.283178336529601
[206.39755102040817, 160.83204081632653]
1.2833111485299027
[206.45530612244897, 160.83857142857144]
1.2836181289643944
[206.44938775510204, 160.96571428571428]
1.2825674627123027
[206.4, 160.95265306122448]
1.282364695917674
[206.35795918367347, 160.96142857142857]
1.282033596589879
[206.33816326530612, 160.67408163265307]
1.2842031593935244
[206.1465306122449, 160.84408163265306]
1.2816544352751302
[206.1826530612245, 160.81244897959184]
1.2821311681373029
[206.27061224489796, 160.73510204081632]
1.2832953699965213
[206.38469387755103, 160.56061224489795]
1.285400516303208
[206.6177551020408, 160.7616326530612]
1.28524295064819
[206.41775510204081, 160.8057142857143]
1.2836468904039353
[206.46142857142857, 160.7587755102041]
1.2842933638687957
[206.41530612244898, 160.76061224489797]
1.2839917890335102
[206.5477551020408, 160.9822448979592]
1.2830468057701887
[206.5612244897959, 160.92265306122448]
1.2836056363749349
[206.63448979591837, 161.11489795918368]
1.2825287568891766
[206.5665306122449, 161.00755102040816]
1.2829617574026824
[206.31755102040816, 161.16836734693877]
1.2801367564658583
[206.37755102040816, 161.12714285714284]
1.280836657070155
[206.46510204081633, 160.95326530612246]
1.2827642958851029
[206.57163265306122, 160.84632653061223]
1.2842794554822896
[206.4626530612245, 160.83408163265307]
1.2836996422983757
[206.60387755102042, 160.8426530612245]
1.2845092618086633
[206.41285714285715, 160.87795918367348]
1.2830400024356148
[206.61102040816326, 160.9073469387755]
1.2840372073674038
[206.58244897959185, 160.92244897959185]
1.283739156901537
[206.59367346938777, 161.00367346938776]
1.2831612410922302
[206.5061224489796, 160.9487755102041]
1.2830549458631153
[206.44918367346938, 161.04897959183674]
1.2819030843703272
[206.50591836734694, 161.1265306122449]
1.281638210558314
[206.6204081632653, 161.08]
1.2827191964444082
[206.55244897959184, 160.92448979591836]
1.2835364539079046
[206.6104081632653, 160.94551020408164]
1.2837289334836355
[206.6077551020408, 160.9918367346939]
1.2833430519990872
[206.53306122448978, 160.90714285714284]
1.2835543379690404
[206.71510204081633, 161.0608163265306]
1.283459917536537
[206.69653061224489, 161.035306122449]
1.28354791001593
[206.63, 160.92755102040817]
1.2839939382026389
[206.71510204081633, 161.09244897959184]
1.2832078930465838
[206.36489795918368, 161.19244897959183]
1.2802392374180693
[206.47755102040816, 160.9926530612245]
1.2825277867921465
[206.39020408163265, 161.11265306122448]
1.2810303856345922
[206.53755102040816, 160.94571428571427]
1.2832746242236577
[206.3677551020408, 160.9430612244898]
1.2822407721833426
[206.42244897959185, 161.1026530612245]
1.2813100532934383
[206.42755102040817, 160.8542857142857]
1.2833201807695138
[206.47938775510204, 160.94755102040816]
1.282898599239453
[206.38734693877552, 160.8561224489796]
1.2830555890357083
[206.46571428571428, 161.0395918367347]
1.2820804618968082
[206.4565306122449, 160.86551020408163]
1.2834107842652185
[206.36285714285714, 161.02612244897958]
1.2815489437637195
[206.44102040816327, 160.99632653061224]
1.2822716198366804
[206.52755102040817, 161.0422448979592]
1.2824433188401572
[206.5969387755102, 160.74448979591835]
1.2852505179978875
[206.55530612244897, 160.75204081632654]
1.2849311590293073
[206.6642857142857, 160.99571428571429]
1.2836632740889287
[206.82102040816326, 160.82265306122449]
1.2860192048282364
[206.69857142857143, 160.8922448979592]
1.2847018920002231
[206.74755102040817, 161.05469387755102]
1.2837101859173206
[206.65795918367348, 160.95326530612246]
1.283962514153557
[206.93979591836734, 161.19918367346938]
1.2837521332462312
[207.19918367346938, 161.0395918367347]
1.2866350523511774
[207.02530612244897, 161.16795918367347]
1.2845314116468685
[207.08938775510205, 161.0291836734694]
1.2860363757108295
[207.1469387755102, 161.08612244897958]
1.285939071760321
[207.2161224489796, 161.2983673469388]
1.2846758826967895
[207.13816326530613, 161.1777551020408]
1.2851535445084716
[207.2008163265306, 161.39469387755102]
1.2838143023693973
[207.05081632653062, 161.12673469387755]
1.2850183845648184
[207.21224489795918, 161.05020408163264]
1.2866313711277761
[207.06244897959184, 161.1138775510204]
1.2851931325035657
[207.04122448979592, 161.22489795918366]
1.2841764957557071
[207.11265306122448, 161.11163265306124]
1.2855226506655923
[207.07102040816326, 161.0008163265306]
1.2861488850354417
[207.03551020408165, 160.96857142857144]
1.2861859204357295
[207.1365306122449, 160.96]
1.286882024181442
[207.09938775510204, 160.99755102040817]
1.2863511677196255
[207.0987755102041, 160.94979591836736]
1.2867290345322537
[207.0491836734694, 160.90408163265306]
1.2867863982851997
[207.16183673469388, 161.11959183673468]
1.2857644087418905
[207.05, 161.0234693877551]
1.2858374048655603
[206.97387755102042, 161.09489795918367]
1.284794740075884
[206.89877551020408, 161.02530612244897]
1.2848836030336213
[207.02326530612245, 161.1104081632653]
1.2849775980725602
[207.09673469387755, 160.9516326530612]
1.2867016710559518
[206.99, 160.70448979591836]
1.2880162854370807
[207.1104081632653, 160.9618367346939]
1.2867050498723869
[206.82448979591837, 160.47591836734694]
1.2888194808299802
[206.85591836734693, 160.5365306122449]
1.2885286456512537
[206.80285714285714, 160.36102040816326]
1.2896080145691673
[206.79510204081632, 160.62367346938777]
1.287450956475778
[206.8030612244898, 160.58816326530612]
1.2877852079473162
[206.86163265306124, 160.92734693877551]
1.2854349281714148
[206.87448979591838, 160.6595918367347]
1.2876572598674851
[207.12938775510204, 160.3669387755102]
1.291596568074747
[206.84489795918367, 160.1218367346939]
1.2917969352419139
[207.03857142857143, 160.14326530612246]
1.2928334577967178
[206.66122448979593, 160.28938775510204]
1.2893007290385503
[206.82326530612244, 160.54795918367347]
1.2882335369302833
[206.87285714285716, 160.61877551020407]
1.2879743136238426
[206.7573469387755, 160.5491836734694]
1.2878131312039922
[206.96408163265306, 160.50020408163266]
1.2894941960783315
[207.08142857142857, 160.44653061224489]
1.2906569421054508
[207.04897959183674, 160.52714285714285]
1.289806670116186
[207.0891836734694, 160.54]
1.2899538038711187
[206.89122448979592, 160.45897959183674]
1.2893714332228086
[207.2042857142857, 160.47836734693877]
1.291166461497767
[207.00306122448978, 160.21795918367346]
1.2920090998486755
[206.93510204081633, 160.2916326530612]
1.2909912926566247
[206.8922448979592, 160.47367346938776]
1.2892597298050033
[206.82714285714286, 160.64448979591836]
1.28748358017069
[206.90408163265306, 160.5777551020408]
1.2884977841493281
[206.76122448979592, 160.58714285714285]
1.287532867271505
[206.54530612244898, 160.4565306122449]
1.2872352738423656
[206.50285714285715, 160.52448979591836]
1.286425874365918
[206.32755102040815, 160.41163265306122]
1.2862380839091265
[206.40408163265306, 160.40448979591838]
1.2867724706163752
[206.2377551020408, 160.29816326530613]
1.2865883856741454
[206.53673469387755, 160.26734693877552]
1.2887012772026334
[206.46755102040817, 160.24857142857144]
1.2884205405377869
[206.5273469387755, 160.20632653061224]
1.2891335280652119
[206.31918367346938, 159.98632653061225]
1.2896051065588512
[206.40571428571428, 160.04122448979592]
1.28970341825193
[206.4708163265306, 160.2273469387755]
1.2886115901639763
[206.4234693877551, 160.07183673469387]
1.289567694096528
[206.49102040816325, 160.22530612244898]
1.288754101367462
[206.41, 160.0457142857143]
1.2896940159954298
[206.4195918367347, 160.1942857142857]
1.2885577716854024
[206.48877551020408, 160.22204081632654]
1.2887663548544877
[206.4804081632653, 160.29877551020408]
1.2880972266074575
[206.77469387755102, 160.42142857142858]
1.288946842818342
[206.6361224489796, 160.34428571428572]
1.2887027531319724
[206.80959183673468, 160.52510204081634]
1.2883317886578867
[206.63122448979593, 160.38530612244898]
1.2883426137057699
[206.53918367346938, 160.52836734693878]
1.2866210943707577
[206.6457142857143, 160.51673469387754]
1.287378008777774
[206.3165306122449, 160.37020408163266]
1.2865016403372806
[206.40244897959184, 160.31408163265306]
1.287487954130858
[206.26714285714286, 160.18326530612245]
1.2876947068281483
[206.3942857142857, 160.48020408163265]
1.2861043322782515
[206.2991836734694, 160.24408163265306]
1.2874059470501633
[206.43020408163267, 160.57163265306122]
1.2855957224253656
[206.4038775510204, 160.48857142857142]
1.2860970455013645
[206.47979591836736, 160.63142857142856]
1.2854258830584404
[206.64102040816326, 160.95938775510203]
1.2838084394466345
^CTraceback (most recent call last):
  File "camera_detect_color.py", line 171, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:37:06] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:37:06] "GET /stream.mjpg HTTP/1.1" 200 -
[156.72, 241.45666666666668]
0.6490605629719618
[156.50555555555556, 241.48222222222222]
0.6481038401722694
[154.4011111111111, 240.9477777777778]
0.6408073672026672
[153.92777777777778, 240.63222222222223]
0.6396806560495731
[153.17333333333335, 240.44222222222223]
0.6370484015563915
[152.24, 240.48]
0.6330671989354625
[151.5811111111111, 240.25444444444443]
0.6309190719098734
[150.88555555555556, 240.13222222222223]
0.6283436440109385
[149.84777777777776, 239.94444444444446]
0.6245103033109515
[149.87555555555556, 239.8022222222222]
0.6249965249140496
[150.46, 239.94666666666666]
0.6270560124472105
[150.49444444444444, 239.84444444444443]
0.6274668766793292
[149.37555555555556, 239.58444444444444]
0.623477688219417
[149.3322222222222, 239.54]
0.623412466486692
[148.7188888888889, 239.57777777777778]
0.6207541044430016
[148.78444444444443, 239.5]
0.6212294131292043
[148.68555555555557, 239.47222222222223]
0.6208885280129915
[148.97, 239.36666666666667]
0.622350647542125
[149.20888888888888, 239.31666666666666]
0.6234788866448453
[149.46, 239.36222222222221]
0.6244093099254501
[148.76333333333332, 239.15444444444444]
0.6220387569167297
[148.70111111111112, 239.30333333333334]
0.621391725053744
[148.4, 239.43444444444444]
0.6197938661011365
[148.42888888888888, 239.18555555555557]
0.6205595841443416
[148.3177777777778, 239.35444444444445]
0.6196575046769319
[148.4311111111111, 239.2188888888889]
0.6204824033776597
[148.52777777777777, 239.36]
0.6205204619726677
[148.38777777777779, 239.30555555555554]
0.6200766105629716
[148.44, 239.29555555555555]
0.6203207562939368
[148.31, 239.18555555555557]
0.6200625270013518
[147.88222222222223, 239.20444444444445]
0.6182252280708274
[147.88, 239.22444444444446]
0.6181642530027589
[147.55333333333334, 239.1677777777778]
0.6169448690133844
[147.57, 239.22]
0.6168798595435164
[148.70111111111112, 239.14777777777778]
0.621795914195314
[148.54333333333332, 239.32222222222222]
0.6206834114861414
[148.29222222222222, 239.3011111111111]
0.6196888160430142
[148.4611111111111, 239.20222222222222]
0.6206510530374114
[148.44333333333333, 239.27444444444444]
0.6203894180090738
[148.28666666666666, 239.22]
0.6198757071593791
[147.57111111111112, 239.29444444444445]
0.6166925916467393
[147.82111111111112, 239.24555555555557]
0.6178635618448735
[148.29555555555555, 239.04555555555555]
0.6203652488368093
[148.01444444444445, 239.24777777777777]
0.6186659112124576
[148.4411111111111, 239.15]
0.6207029525867075
[148.57777777777778, 239.15222222222224]
0.6212686480484303
[148.23222222222222, 239.14555555555555]
0.6198410080332294
[148.76, 239.32111111111112]
0.6215916318846366
[148.0077777777778, 239.17111111111112]
0.6188363514731434
[148.29888888888888, 239.2111111111111]
0.6199498351061359
[148.28666666666666, 239.1611111111111]
0.6200283397988339
[149.01222222222222, 239.11555555555555]
0.6231807958959871
[148.47444444444446, 239.33]
0.6203753998430804
[148.52555555555554, 239.21]
0.6209002782306573
[147.8711111111111, 239.14444444444445]
0.6183338753891185
[147.79333333333332, 239.25555555555556]
0.6177216365578414
[147.84222222222223, 239.13333333333333]
0.618241799089304
[147.59333333333333, 239.10333333333332]
0.6172784430720331
[147.66444444444446, 239.09666666666666]
0.6175930702133494
[147.49444444444444, 239.25]
0.6164867061418785
[147.05666666666667, 239.15333333333334]
0.6149053605775932
[147.45666666666668, 239.04111111111112]
0.6168673914761292
[147.67777777777778, 239.03222222222223]
0.6178153572972496
[148.33666666666667, 239.1688888888889]
0.6202172337539257
[148.17888888888888, 239.11777777777777]
0.6196899714691969
[148.72666666666666, 239.09333333333333]
0.6220443899174659
[148.2811111111111, 238.97444444444446]
0.6204894061196687
[148.30777777777777, 239.21]
0.6199898740762416
[148.29444444444445, 239.0988888888889]
0.6202222232549062
[148.14666666666668, 238.9988888888889]
0.6198634117313423
[148.38777777777779, 239.07111111111112]
0.6206846870294287
[148.31555555555556, 239.01]
0.6205412139891869
[148.02333333333334, 238.9622222222222]
0.619442403727228
[148.17777777777778, 239.02777777777777]
0.6199186519465427
[148.22, 239.03333333333333]
0.6200808813275693
[148.2111111111111, 238.95111111111112]
0.620257049326687
[148.5511111111111, 239.19222222222223]
0.6210532672467053
[148.20222222222222, 239.02333333333334]
0.6200324468554906
[148.19, 238.96333333333334]
0.6201369805688459
[148.2277777777778, 238.92666666666668]
0.6203902638652492
[148.4011111111111, 238.99444444444444]
0.620939584834608
[148.3177777777778, 238.95888888888888]
0.6206832416547711
[148.36333333333334, 238.96444444444444]
0.6208594491044693
[148.31333333333333, 238.94555555555556]
0.6206992759856964
[148.5011111111111, 239.09777777777776]
0.6210894659553506
[148.04555555555555, 238.99777777777777]
0.6194432305274805
[148.03444444444443, 238.9188888888889]
0.6196012593767294
[147.7711111111111, 239.01555555555555]
0.6182489284751341
[148.35111111111112, 239.00555555555556]
0.6207015178633691
[147.84333333333333, 238.90777777777777]
0.6188301390122641
[147.91333333333333, 238.85333333333332]
0.6192642625879201
[148.43666666666667, 238.83555555555554]
0.621501544530872
[148.61777777777777, 238.8188888888889]
0.6223032795656401
[148.26222222222222, 238.9622222222222]
0.6204420968446895
[148.23111111111112, 239.02]
0.620161957623258
[148.18, 239.07111111111112]
0.6198155825323939
[148.68555555555557, 238.99555555555557]
0.6221268642838547
[148.49, 238.92333333333335]
0.6214964353976868
[148.30333333333334, 238.95444444444445]
0.6206343375538806
[148.85, 238.91333333333333]
0.6230292714233893
[148.83333333333334, 238.89777777777778]
0.6230000744158357
[148.36, 238.93666666666667]
0.6209176769297304
[148.39, 238.9622222222222]
0.6209768164191457
[148.82, 238.94333333333333]
0.6228254955847272
[148.19555555555556, 238.90222222222224]
0.6203188659237624
[148.4111111111111, 238.9011111111111]
0.6212240303984446
[148.5911111111111, 238.84444444444443]
0.6221250465202829
[148.39333333333335, 238.88333333333333]
0.621195841763762
[148.59777777777776, 238.9411111111111]
0.621901258794589
[148.76222222222222, 238.8311111111111]
0.6228762305301747
[148.18, 238.75666666666666]
0.6206318846245131
[148.39888888888888, 238.75444444444443]
0.6215544562288544
[148.17, 238.72222222222223]
0.6206795438678147
[147.87, 238.74444444444444]
0.6193651975613161
[148.36333333333334, 238.78555555555556]
0.621324572954813
[147.93666666666667, 238.79]
0.6195262224827952
[148.02, 238.78222222222223]
0.6198953951531847
[148.29777777777778, 238.7111111111111]
0.6212437162539565
[148.0822222222222, 238.79]
0.6201357771356515
[148.07, 238.72222222222223]
0.6202606469629974
[148.69, 238.7277777777778]
0.6228433129319774
[148.70444444444445, 238.7277777777778]
0.6229038188545764
[148.53444444444443, 238.7288888888889]
0.6221888148341214
[148.94333333333333, 238.7488888888889]
0.6238493256513119
[148.78444444444443, 238.73888888888888]
0.6232099225094827
[148.1811111111111, 238.73555555555555]
0.6206914205396953
[148.19444444444446, 238.81444444444443]
0.6205422154811034
[148.7722222222222, 238.83444444444444]
0.6229094072602592
[148.12777777777777, 238.73444444444445]
0.6204709090993712
[148.15333333333334, 238.65555555555557]
0.6207830904604498
[148.33777777777777, 238.79777777777778]
0.621185754566858
[148.17222222222222, 238.7277777777778]
0.6206744083218915
[148.2422222222222, 238.76888888888888]
0.6208607114271355
[147.47222222222223, 238.64444444444445]
0.6179579104199646
[147.02, 238.61666666666667]
0.6161346650834673
[146.89777777777778, 238.14555555555555]
0.6168403077482959
[146.77666666666667, 238.11222222222221]
0.6164180288472756
[146.88666666666666, 237.97222222222223]
0.617242908836232
[147.42, 237.10333333333332]
0.6217542281143242
[147.27444444444444, 236.92333333333335]
0.6216122421223931
[148.02333333333334, 236.38555555555556]
0.6261944939294092
[149.73222222222222, 235.88]
0.6347813389105571
[154.10777777777778, 236.88777777777779]
0.6505518318566222
[155.8177777777778, 236.98777777777778]
0.657492885240214
[153.29777777777778, 236.92]
0.6470444782111168
[143.33555555555554, 236.86]
0.6051488455440156
[132.48111111111112, 236.9711111111111]
0.5590601761114811
[132.24777777777777, 237.0888888888889]
0.5577982941231605
[144.2577777777778, 237.18666666666667]
0.6082035714954935
[154.66, 237.2722222222222]
0.6518251422416821
[165.51222222222222, 237.23222222222222]
0.6976801914673386
[175.95111111111112, 236.59222222222223]
0.7436893295074037
[186.2277777777778, 235.97555555555556]
0.7891824953620432
[193.99555555555557, 235.43333333333334]
0.8239935815753457
[193.2188888888889, 235.33777777777777]
0.8210279314838247
[183.87444444444444, 235.32111111111112]
0.78137674761201
[170.90444444444444, 235.54888888888888]
0.7255582705170901
[159.55444444444444, 235.79111111111112]
0.6766770964884172
[156.02, 235.79444444444445]
0.6616780152204133
[154.91555555555556, 235.84666666666666]
0.6568486116214867
[155.20222222222222, 235.96333333333334]
0.6577387258849068
[157.92555555555555, 236.1677777777778]
0.6687006883053949
[160.51777777777778, 236.3311111111111]
0.67920713876012
[162.42, 236.52]
0.6867072552004058
[163.84222222222223, 236.60555555555555]
0.6924698865904342
[166.47, 236.70666666666668]
0.7032755027319326
[166.92777777777778, 236.67]
0.705318704431393
[166.65777777777777, 236.48444444444445]
0.7047304027514142
[166.58555555555554, 236.29888888888888]
0.7049781585468498
[166.22333333333333, 235.9611111111111]
0.704452240246745
[166.06, 236.02]
0.703584441996441
[166.82666666666665, 236.29888888888888]
0.7059985235271713
[167.81, 236.20555555555555]
0.7104405296704848
[169.40444444444444, 236.28555555555556]
0.7169479490447057
[171.6211111111111, 236.37222222222223]
0.726062942158084
[173.01777777777778, 236.29888888888888]
0.7321988630218791
[173.6211111111111, 236.42888888888888]
0.7343481244066808
[174.67777777777778, 236.45]
0.7387514391109232
[175.12, 236.3022222222222]
0.7410848630755342
[176.05333333333334, 236.32111111111112]
0.7449750574782898
[177.70444444444445, 236.39333333333335]
0.7517320473410606
[177.9622222222222, 236.36888888888888]
0.7529003628979185
[177.97666666666666, 236.32777777777778]
0.7530924563341874
[178.70111111111112, 236.39888888888888]
0.7559304189246989
[179.8388888888889, 236.2877777777778]
0.7611011055257478
[179.86111111111111, 236.4111111111111]
0.7607980448371482
[180.95333333333335, 236.26222222222222]
0.7659004119716324
[181.37666666666667, 236.13666666666666]
0.7681003938397256
[180.77666666666667, 236.1211111111111]
0.7656099271089696
[179.77666666666667, 235.98777777777778]
0.761804989900607
[179.48444444444445, 236.13777777777779]
0.7600835670324293
[180.10444444444445, 236.04666666666665]
0.7630035492040181
[180.43666666666667, 235.9922222222222]
0.7645873451573263
[180.11111111111111, 235.9922222222222]
0.7632078269999483
[180.14666666666668, 235.99666666666667]
0.7633441150298733
[180.28333333333333, 236.07111111111112]
0.7636823179456284
[179.90777777777777, 236.06666666666666]
0.7621058081521227
[180.57111111111112, 236.0]
0.7651318267419963
[180.65555555555557, 235.87333333333333]
0.7659007188415629
[181.6911111111111, 235.89]
0.7702365980376917
[181.99444444444444, 235.76111111111112]
0.7719442938944788
[181.12444444444444, 235.63666666666666]
0.7686598482597974
[179.20666666666668, 235.4411111111111]
0.7611528242495176
[176.0822222222222, 235.35555555555555]
0.7481540930979133
[173.42666666666668, 235.2588888888889]
0.7371737046185527
[170.2811111111111, 235.20222222222222]
0.7239774756474334
[168.17666666666668, 235.18777777777777]
0.71507400705819
[167.89333333333335, 235.13]
0.7140447128538823
[168.79, 235.20777777777778]
0.7176208269756763
[170.66444444444446, 235.4488888888889]
0.7248471005738448
[173.5211111111111, 235.34444444444443]
0.7373070204428498
[172.0388888888889, 235.59]
0.730246992185105
[165.61888888888888, 235.97]
0.7018641729410047
[158.22222222222223, 236.01555555555555]
0.6703889574133532
[161.7877777777778, 236.0511111111111]
0.6853929939843537
[174.89222222222222, 236.1]
0.7407548590521906
[166.27666666666667, 235.9177777777778]
0.7048077013648822
[137.95666666666668, 235.84555555555556]
0.5849449498494778
[122.92888888888889, 235.1911111111111]
0.5226765939755849
[121.35333333333334, 235.14]
0.5160897054237192
[124.02, 234.64444444444445]
0.5285443697319822
[126.52777777777777, 234.2422222222222]
0.5401578612831921
[125.85333333333334, 234.1911111111111]
0.5373958590325091
[127.80222222222223, 234.9611111111111]
0.543929255432341
[127.96888888888888, 234.90666666666667]
0.5447648238543913
[129.76666666666668, 234.76111111111112]
0.5527604893863739
[131.31333333333333, 234.73444444444445]
0.5594122909576306
[133.43777777777777, 234.66444444444446]
0.5686322787147605
[134.98222222222222, 234.8322222222222]
0.5748028143024098
[133.54888888888888, 234.99333333333334]
0.5683092664567316
[129.96, 234.84555555555556]
0.553384966952276
[128.25555555555556, 234.88777777777779]
0.5460290729852081
[127.28666666666666, 234.99666666666667]
0.5416530730932353
[126.45666666666666, 235.20444444444445]
0.5376457360972015
[125.21444444444444, 235.21333333333334]
0.532344160383954
[125.51222222222222, 235.17666666666668]
0.5336933463731757
[125.8, 235.34666666666666]
0.5345306214945329
[125.71888888888888, 235.3388888888889]
0.5342036306980477
[126.04444444444445, 235.38555555555556]
0.5354807951021257
[128.01888888888888, 235.54444444444445]
0.543502051983584
[129.73777777777778, 235.60888888888888]
0.550648909680827
[134.9411111111111, 235.76888888888888]
0.5723448574875584
[135.81, 235.98777777777778]
0.5754959060968318
[137.4622222222222, 236.08777777777777]
0.5822504812240268
[137.18444444444444, 235.89555555555555]
0.5815473891458555
[136.58333333333334, 235.93666666666667]
0.5788982919144968
[137.2488888888889, 235.65444444444444]
0.5824158725817935
[137.22333333333333, 235.60666666666665]
0.5824255114456297
[137.89888888888888, 235.36444444444444]
0.5858951602243329
[140.74777777777777, 235.32666666666665]
0.5980953190364222
[143.84, 235.39555555555555]
0.6110565667245677
[146.85, 235.5]
0.6235668789808917
[148.01777777777778, 235.54111111111112]
0.6284158934274271
[149.52, 235.59666666666666]
0.6346439536495989
[150.40555555555557, 235.67]
0.6382040800931623
[151.12555555555556, 235.64333333333335]
0.6413317678789507
[149.0077777777778, 235.7]
0.6321925234525999
[148.3411111111111, 235.8088888888889]
0.6290734493092334
[148.17222222222222, 235.74666666666667]
0.6285230850442094
[147.66444444444446, 235.69]
0.6265197693769123
[147.61, 235.56444444444443]
0.6266225802799895
[146.62555555555556, 235.39888888888888]
0.6228812559296514
[145.94333333333333, 235.2588888888889]
0.6203520471537266
[145.89444444444445, 235.24555555555557]
0.6201793870234884
[145.96444444444444, 235.2288888888889]
0.6205209110747923
[145.77777777777777, 235.2577777777778]
0.6196512572497307
[145.0911111111111, 235.23222222222222]
0.6167994747507192
[146.31444444444443, 235.38333333333333]
0.6216006986239939
[146.64555555555555, 235.4411111111111]
0.6228545000637102
[147.48444444444445, 235.5288888888889]
0.6261840963127902
[148.57111111111112, 235.44333333333333]
0.6310270459039449
[151.74, 236.51666666666668]
0.6415615530970333
[151.92444444444445, 236.21555555555557]
0.6431602020753172
[151.26888888888888, 236.26]
0.640264492037962
[151.09555555555556, 236.33777777777777]
0.6393203700917708
[151.14666666666668, 236.24444444444444]
0.6397892954566833
[150.88111111111112, 236.36444444444444]
0.6383409800308376
[149.78333333333333, 236.34333333333333]
0.6337531557197862
[149.39111111111112, 236.40333333333334]
0.6319331838712559
[149.0588888888889, 236.45777777777778]
0.6303826851869256
[149.79888888888888, 236.47444444444446]
0.6334675581575645
[150.48333333333332, 236.55555555555554]
0.6361437294504462
[150.2422222222222, 236.57555555555555]
0.6350707784217398
[149.93666666666667, 236.66333333333333]
0.6335441344244286
[148.23444444444445, 236.57333333333332]
0.6265898288526931
[147.35333333333332, 236.59666666666666]
0.6228039279223432
[147.4622222222222, 236.41444444444446]
0.6237445540552606
[147.35777777777778, 236.28444444444443]
0.6236457000978106
[147.4411111111111, 236.3011111111111]
0.6239543708357039
[147.93777777777777, 236.42]
0.6257413830377201
[148.1511111111111, 236.38888888888889]
0.6267262044653349
[149.45888888888888, 236.28444444444443]
0.6325379956361448
[150.09666666666666, 236.17666666666668]
0.6355270771879807
[150.80666666666667, 236.20222222222222]
0.6384642161612931
[146.0288888888889, 236.04]
0.6186616204409799
[135.75222222222223, 235.84666666666666]
0.5755952549208054
[128.4388888888889, 235.88222222222223]
0.5445043194814738
[128.23888888888888, 235.9922222222222]
0.5434030311733438
[127.97, 236.0011111111111]
0.5422432097777318
[125.01, 235.85777777777778]
0.5300228009346499
[122.45, 235.86111111111111]
0.5191614650806736
[119.93333333333334, 235.87666666666667]
0.508457809872391
[120.25555555555556, 235.85111111111112]
0.5098791139419407
[132.00666666666666, 235.59]
0.560323726247577
[145.68777777777777, 235.18444444444444]
0.6194617935804522
[149.06444444444443, 235.5222222222222]
0.6329103174977591
[159.3322222222222, 235.84666666666666]
0.6755754680536318
[159.0888888888889, 235.5288888888889]
0.6754538249613165
[160.3788888888889, 235.75444444444443]
0.6802793867442113
[160.30444444444444, 235.93444444444444]
0.6794448552093095
[160.67555555555555, 236.7588888888889]
0.6786463490752429
[160.44555555555556, 237.20333333333335]
0.676405147014048
[160.75666666666666, 237.91555555555556]
0.6756879191496515
[155.39888888888888, 238.31444444444443]
0.6520749896262175
[152.88888888888889, 238.87777777777777]
0.640029768826457
[151.85, 238.86666666666667]
0.6357102986324309
[150.46333333333334, 239.04444444444445]
0.6294366459049922
[150.45444444444445, 239.01222222222222]
0.6294843127501616
[150.41444444444446, 239.09333333333333]
0.6291034649416314
[150.15222222222224, 238.98]
0.6283045536121108
[150.61666666666667, 239.0011111111111]
0.6301923282550989
[150.6911111111111, 238.88]
0.6308234725013023
[150.23666666666668, 238.86333333333334]
0.6289649590421301
[149.14666666666668, 238.62]
0.625038415332607
[148.66444444444446, 238.35777777777778]
0.6237029302355935
[148.1688888888889, 238.0222222222222]
0.6225002334049109
[147.82, 238.29444444444445]
0.6203249947543887
[148.27444444444444, 238.2277777777778]
0.6224061938854037
[148.14777777777778, 238.3]
0.6216860166923113
[148.3788888888889, 238.26555555555555]
0.6227458624597205
[148.28666666666666, 238.20111111111112]
0.6225271829126648
[147.42, 238.09777777777776]
0.6191573956544464
[147.14666666666668, 237.9177777777778]
0.61847697150276
[147.02333333333334, 238.04555555555555]
0.6176268781419056
[147.60777777777778, 237.99777777777777]
0.6202065378761706
[147.16444444444446, 237.9322222222222]
0.6185141426830237
[146.74555555555557, 237.84333333333333]
0.616984102513793
[146.94222222222223, 237.9]
0.6176638176638176
[146.40333333333334, 238.0088888888889]
0.6151170824619062
[146.65222222222224, 237.77777777777777]
0.6167616822429908
[146.34555555555556, 237.86555555555555]
0.6152448395218588
[147.03222222222223, 237.85333333333332]
0.6181633873348656
[147.1822222222222, 237.99444444444444]
0.6184271341534583
[146.79, 237.94666666666666]
0.616902947439202
[147.15444444444444, 237.87666666666667]
0.6186165566656857
[147.92555555555555, 237.9311111111111]
0.6217159028290168
[147.47222222222223, 237.86666666666667]
0.6199785127055306
[147.45888888888888, 237.76777777777778]
0.6201802879560355
[147.3111111111111, 237.76888888888888]
0.6195558712475232
[147.33555555555554, 237.83777777777777]
0.619479196838181
[146.82111111111112, 237.81222222222223]
0.6173825286991137
[147.10222222222222, 237.97333333333333]
0.6181458239952189
[147.83, 237.82333333333332]
0.6215958624749465
[147.43, 237.7811111111111]
0.620024018354883
[147.60777777777778, 237.68333333333334]
0.6210270434518383
[147.4, 237.87555555555556]
0.6196517319980569
[147.41666666666666, 237.7877777777778]
0.619950562826797
[148.28444444444443, 237.85666666666665]
0.6234193328381705
[148.44, 237.97333333333333]
0.6237673688928731
[148.75666666666666, 238.04]
0.6249229821318546
[148.93666666666667, 237.76111111111112]
0.6264130663364255
[148.39777777777778, 237.70555555555555]
0.6242924252693576
[149.10222222222222, 237.74444444444444]
0.6271533392531663
[148.79333333333332, 237.50333333333333]
0.6264894527796101
[148.77444444444444, 237.52555555555554]
0.6263513165834788
[149.26, 237.55777777777777]
0.6283103057969524
[148.94555555555556, 237.42444444444445]
0.6273387557211183
[149.28222222222223, 237.74444444444444]
0.6279104547366454
[149.60777777777778, 240.50666666666666]
0.6220525187566989
[149.23444444444445, 239.51111111111112]
0.6230794210428651
[149.86777777777777, 238.20666666666668]
0.6291502243616653
[149.68333333333334, 237.92777777777778]
0.6291124757746281
[149.79777777777778, 238.51666666666668]
0.6280390375701674
[149.92111111111112, 237.61222222222221]
0.6309486511636607
[150.1588888888889, 238.50555555555556]
0.6295823530781952
[150.0377777777778, 236.64888888888888]
0.6340100664838674
[149.43333333333334, 238.33666666666667]
0.6269842379826855
[149.5211111111111, 238.62777777777777]
0.62658719996275
[149.5311111111111, 238.1611111111111]
0.6278569595745177
[149.0011111111111, 238.02333333333334]
0.6259937167691308
[148.54111111111112, 238.39555555555555]
0.6230867465836426
[148.80555555555554, 238.61111111111111]
0.6236321303841675
[148.50333333333333, 237.72333333333333]
0.624689765413576
[149.19444444444446, 188.21333333333334]
0.7926879663738547
[148.7511111111111, 189.62666666666667]
0.7844419444053813
[148.67888888888888, 189.9011111111111]
0.7829279566558033
[149.2288888888889, 189.93555555555557]
0.7856816932058827
[148.66444444444446, 189.94]
0.7826916102160917
[148.66444444444446, 189.73444444444445]
0.7835395669971481
[148.13888888888889, 189.20222222222222]
0.7829659036187031
[148.05555555555554, 189.05444444444444]
0.7831371327483558
[148.02777777777777, 188.66555555555556]
0.7846041496121885
[148.22666666666666, 188.66444444444446]
0.7856629642280827
[147.98222222222222, 188.56555555555556]
0.784778650513526
[148.23666666666668, 188.54333333333332]
0.7862206742923821
[148.46555555555557, 188.33666666666667]
0.7882987321758317
[148.26888888888888, 188.24]
0.7876587807527033
[148.03555555555556, 187.82222222222222]
0.788168480832939
[148.6911111111111, 187.92888888888888]
0.7912094409232806
[149.12, 187.85444444444445]
0.7938060791747747
[149.07777777777778, 187.75444444444443]
0.794003988661313
[149.0811111111111, 187.69555555555556]
0.7942708641653742
[149.31333333333333, 187.95555555555555]
0.7944076613856704
[148.5611111111111, 187.95777777777778]
0.790396188269233
[148.56333333333333, 187.95444444444445]
0.7904220289786532
[149.04, 187.95222222222222]
0.7929674799151084
[148.72666666666666, 188.0077777777778]
0.7910665634400467
[148.6688888888889, 188.0522222222222]
0.7905723587419571
[148.38111111111112, 187.78666666666666]
0.7901578623497113
[148.40555555555557, 187.8788888888889]
0.7899001129569285
[148.34666666666666, 187.80444444444444]
0.7898996592199924
[148.79222222222222, 188.06555555555556]
0.7911721090163595
[148.36777777777777, 188.0211111111111]
0.789101696617992
[148.21777777777777, 188.32]
0.7870527706976305
[148.88333333333333, 188.27666666666667]
0.7907689039179929
[148.1988888888889, 188.03444444444443]
0.7881475616169615
[148.8011111111111, 187.92111111111112]
0.7918275399251459
[148.89888888888888, 186.15222222222224]
0.7998770420862256
[148.38777777777779, 186.35222222222222]
0.7962758694705964
[148.8188888888889, 187.0677777777778]
0.7955345953041381
[148.80777777777777, 186.32555555555555]
0.7986439505524977
[149.03555555555556, 185.93]
0.8015680931294334
[149.48666666666668, 185.90333333333334]
0.804109662727941
[149.64, 186.44555555555556]
0.8025935483102007
[149.5822222222222, 187.83666666666667]
0.7963419755934529
[150.09444444444443, 187.47555555555556]
0.8006080792755202
[149.60777777777778, 186.83555555555554]
0.8007457538417623
[149.64444444444445, 186.38333333333333]
0.8028853319025903
[149.45666666666668, 184.43666666666667]
0.8103413999385517
[149.0077777777778, 184.24555555555557]
0.8087455750477925
[149.5088888888889, 183.4111111111111]
0.8151572060338039
[149.56222222222223, 182.38777777777779]
0.8200232715398814
[149.57777777777778, 181.42]
0.8244833964159287
[150.01777777777778, 181.18555555555557]
0.8279786836085781
[149.31, 181.8711111111111]
0.8209660076733218
[149.6288888888889, 181.77777777777777]
0.8231418092909536
[149.62777777777777, 181.33555555555554]
0.8251430742270315
[149.3111111111111, 181.37777777777777]
0.8232050967900024
[149.52666666666667, 181.95666666666668]
0.8217707512777768
[149.4322222222222, 182.78555555555556]
0.8175275216252195
[149.31666666666666, 182.1822222222222]
0.8196006440438145
[149.13222222222223, 182.69222222222223]
0.8163030719546536
[148.92666666666668, 183.01222222222222]
0.8137525726879201
[149.14555555555555, 182.29555555555555]
0.8181524508429534
[149.37, 182.77333333333334]
0.8172417566384593
[149.64666666666668, 182.99]
0.8177860356667942
[149.88111111111112, 183.51]
0.8167462869114006
[149.55555555555554, 183.89666666666668]
0.8132586537125317
[149.86333333333334, 184.1]
0.8140322288611263
[149.54555555555555, 184.2411111111111]
0.8116839648528197
[149.28555555555556, 184.16]
0.8106296457186988
[149.75666666666666, 184.19666666666666]
0.8130259324272969
[149.19444444444446, 184.2711111111111]
0.8096464147029739
[148.9711111111111, 183.83777777777777]
0.8103400340880245
[149.32444444444445, 183.34]
0.814467352702326
[149.21666666666667, 183.2422222222222]
0.8143137801816661
[148.95111111111112, 182.89666666666668]
0.8144003596444865
[148.78666666666666, 182.85222222222222]
0.8136989797468508
[149.26111111111112, 182.94222222222223]
0.8158920849327049
[149.04111111111112, 182.85]
0.8151004162488987
[149.17555555555555, 183.2577777777778]
0.8140203235272717
[149.28222222222223, 183.16222222222223]
0.815027358868277
[149.29222222222222, 183.2711111111111]
0.8145976816374042
[149.04, 183.57666666666665]
0.811867884444283
[149.1977777777778, 183.2711111111111]
0.8140823552235911
[149.51888888888888, 183.50222222222223]
0.8148069657043208
[149.42, 183.48888888888888]
0.8143272374954583
[149.47, 183.58]
0.814195446127029
[149.49777777777777, 183.33444444444444]
0.8154374821970776
[149.57, 183.72333333333333]
0.8141045412486165
[149.62333333333333, 183.95111111111112]
0.813386407016357
[149.62, 184.09]
0.8127546308870661
[149.70111111111112, 184.65666666666667]
0.8106997370495395
[149.7122222222222, 184.53222222222223]
0.8113066673089312
[149.88444444444445, 184.77]
0.8111946985140686
[149.90555555555557, 184.83444444444444]
0.8110260834019634
[149.68555555555557, 184.75333333333333]
0.8101913662661328
[149.64888888888888, 184.6211111111111]
0.8105730053743703
[149.58777777777777, 224.70111111111112]
0.6657189056079433
[149.14777777777778, 234.89555555555555]
0.6349535963974533
[149.30555555555554, 235.6211111111111]
0.633667988625807
[149.6588888888889, 235.15222222222224]
0.6364340828872078
[149.52333333333334, 234.87555555555556]
0.636606619107991
[149.87333333333333, 234.4922222222222]
0.639139890922703
[149.81666666666666, 234.82666666666665]
0.6379883034294799
[149.77, 235.5911111111111]
0.6357200799879265
[150.00444444444443, 235.67777777777778]
0.6364810711423318
[149.9611111111111, 235.54666666666665]
0.6366513830710593
[150.45888888888888, 235.87777777777777]
0.6378680107400254
[149.96777777777777, 236.45666666666668]
0.6342294336289007
[150.2577777777778, 236.69444444444446]
0.6348175096819623
[150.44333333333333, 237.29]
0.6340062089988341
[150.59333333333333, 237.39888888888888]
0.634347254269654
[150.80666666666667, 237.85111111111112]
0.6340381003989424
[150.81, 238.4388888888889]
0.6324891073883362
[151.25222222222223, 239.06444444444443]
0.6326838881194286
[151.39888888888888, 238.97444444444446]
0.6335358964463889
[151.92666666666668, 239.11111111111111]
0.6353810408921934
[152.27333333333334, 240.09666666666666]
0.634216773799442
[152.11111111111111, 240.07888888888888]
0.6335880335630418
[151.84777777777776, 240.1977777777778]
0.632178112481381
[152.23111111111112, 241.13222222222223]
0.6313179951985771
[152.95555555555555, 240.67555555555555]
0.6355259270202394
[153.08, 241.25]
0.6345284974093265
[153.5388888888889, 241.08777777777777]
0.6368588665262537
[153.03, 241.55]
0.6335334299316911
[151.84555555555556, 241.39555555555555]
0.6290321095850058
[151.06222222222223, 241.68666666666667]
0.6250333305749409
[150.35111111111112, 241.28333333333333]
0.6231309433354056
[148.36333333333334, 240.15222222222224]
0.6177887173413159
[148.14, 239.65444444444444]
0.6181400071399097
[148.02666666666667, 239.5]
0.6180654140570634
[147.88555555555556, 239.87555555555556]
0.6165094864003557
[147.83666666666667, 239.40333333333334]
0.6175213377702901
[147.48777777777778, 239.07333333333332]
0.6169143823838339
[147.70888888888888, 236.85]
0.6236389651209157
[147.6822222222222, 235.6211111111111]
0.6267783965783107
[147.98777777777778, 239.62444444444444]
0.6175821424265749
[148.23, 238.4711111111111]
0.6215847249142686
[149.07, 237.0011111111111]
0.628984392947056
[149.25555555555556, 236.32666666666665]
0.6315645951460784
[150.38111111111112, 239.23222222222222]
0.6285988973986225
[150.3488888888889, 238.65]
0.6299974392997649
[150.46, 237.8011111111111]
0.6327136122156237
[150.48777777777778, 238.2111111111111]
0.631741219273287
[150.2577777777778, 238.95222222222222]
0.6288193362689892
[149.6, 238.41555555555556]
0.6274758358421803
[150.11, 238.11333333333334]
0.6304140885292718
[149.49333333333334, 238.20444444444445]
0.6275841480707516
[149.18333333333334, 238.51888888888888]
0.6254571033274794
[149.13666666666666, 238.57555555555555]
0.6251129388313974
[148.36222222222221, 238.1]
0.6231088711559102
[148.02333333333334, 238.1211111111111]
0.6216304494911553
[147.34777777777776, 238.24]
0.6184846280128348
[146.91, 237.92]
0.6174764626765299
[147.35444444444445, 237.57666666666665]
0.6202395484030887
[146.26333333333332, 237.34222222222223]
0.6162550091756862
[146.53333333333333, 237.15666666666667]
0.6178756658748787
[146.54, 237.5888888888889]
0.6167796847963335
[147.15, 237.50666666666666]
0.6195615561668445
[147.24333333333334, 237.51333333333332]
0.6199371263367671
[146.91222222222223, 237.3488888888889]
0.6189716029848231
[147.34444444444443, 237.5388888888889]
0.6202960918679982
[146.82222222222222, 237.70555555555555]
0.617664243812373
[147.40222222222224, 237.74666666666667]
0.6199970089544427
[147.57777777777778, 237.51]
0.621353954687288
[147.3388888888889, 237.61888888888888]
0.620063874458166
[147.22666666666666, 237.7577777777778]
0.6192296548307801
[147.59777777777776, 237.88888888888889]
0.6204483886034563
[146.99555555555557, 238.03222222222223]
0.6175447768509399
[146.77777777777777, 238.49]
0.6154462567729371
[146.40444444444444, 238.89777777777778]
0.612833010864712
[147.57666666666665, 238.52333333333334]
0.618709560210741
[148.12, 238.35444444444445]
0.6214274726248025
[148.08777777777777, 238.38666666666666]
0.6212083076980442
[148.44666666666666, 238.10111111111112]
0.6234606213046744
[148.05777777777777, 238.13444444444445]
0.6217402867661125
[148.01555555555555, 238.31444444444443]
0.6210935132388115
[148.36777777777777, 238.05666666666667]
0.623245632459125
[147.99444444444444, 236.98333333333332]
0.6244930492064609
[148.12444444444444, 237.61444444444444]
0.6233814816719896
[147.71333333333334, 237.88666666666666]
0.62093994339041
[147.51, 237.44]
0.6212516846361186
[147.31666666666666, 237.4911111111111]
0.6203039178074501
[147.32222222222222, 237.66666666666666]
0.61986909770921
[147.0822222222222, 237.67222222222222]
0.618844814286716
[147.28, 237.54888888888888]
0.6199986903280729
[147.44222222222223, 237.73111111111112]
0.6202058347900055
[147.29222222222222, 238.08555555555554]
0.6186524918680026
[146.6977777777778, 238.65777777777777]
0.614678386532087
[147.41333333333333, 238.42333333333335]
0.6182840046416038
[147.01888888888888, 238.80666666666667]
0.6156398016061342
[146.40555555555557, 238.57444444444445]
0.6136682237549892
[146.32333333333332, 237.43333333333334]
0.616271234030605
[146.14222222222222, 238.03444444444443]
0.61395409627925
[146.68666666666667, 185.32111111111112]
0.7915270191679307
[146.67333333333335, 187.4388888888889]
0.782512818992857
[146.99666666666667, 187.47222222222223]
0.7840983849459179
[146.43666666666667, 187.96]
0.7790842023125487
[146.60777777777778, 187.6611111111111]
0.7812368631398207
[146.77555555555554, 187.28333333333333]
0.7837085817685622
[146.71444444444444, 187.27444444444444]
0.7834194616338469
[147.07, 187.13]
0.7859242238016352
[147.05444444444444, 186.5522222222222]
0.7882749542874501
[146.7888888888889, 186.44]
0.7873250852225322
[146.79222222222222, 185.39888888888888]
0.7917643039931919
[146.63555555555556, 184.92222222222222]
0.7929580003605119
[146.76777777777778, 182.76111111111112]
0.803058029607563
[146.6511111111111, 183.2577777777778]
0.8002449494337059
[146.90777777777777, 182.11333333333334]
0.8066832619492135
[146.94333333333333, 182.69]
0.804331563486416
[147.27666666666667, 182.56444444444443]
0.806710567957738
[146.78666666666666, 181.82222222222222]
0.807308726472745
[146.68666666666667, 182.17777777777778]
0.8051841912661625
[146.7122222222222, 182.0377777777778]
0.8059438211848577
[146.61444444444444, 181.71333333333334]
0.8068447249024715
[146.9611111111111, 181.45888888888888]
0.8098865368954095
[147.02777777777777, 181.64222222222222]
0.8094361320789342
[146.71, 182.2288888888889]
0.8050863992780752
[147.18777777777777, 182.83333333333334]
0.8050379823761774
[146.7188888888889, 183.14777777777778]
0.8010956543895944
[146.95888888888888, 182.87555555555556]
0.803600505504654
[147.40777777777777, 183.77777777777777]
0.8020979443772672
[147.0822222222222, 183.38777777777779]
0.8020284885094728
[147.29222222222222, 183.40555555555557]
0.8030957501590282
[147.10222222222222, 183.4322222222222]
0.8019431942770264
[146.57888888888888, 183.55333333333334]
0.7985629365972953
[147.03555555555556, 183.48]
0.8013710243926072
[146.5, 183.5522222222222]
0.7981379807139355
[147.03444444444443, 183.93666666666667]
0.7993753888717734
[146.87, 183.69555555555556]
0.7995294146111319
[146.98555555555555, 226.95444444444445]
0.6476434330922994
[147.3711111111111, 234.70111111111112]
0.6279097291590723
[147.3311111111111, 234.72666666666666]
0.6276709553428574
[147.84, 234.7788888888889]
0.6296988655993109
[147.21, 234.13222222222223]
0.6287472890437028
[147.67222222222222, 234.03444444444443]
0.6309849927123737
[146.96, 233.15]
0.6303238258631783
[146.95222222222222, 234.14888888888888]
0.6276016210008827
[146.77, 235.01]
0.6245266158886856
[147.05777777777777, 235.68777777777777]
0.6239516497814905
[147.0688888888889, 235.41222222222223]
0.624729198427345
[147.0077777777778, 236.39666666666668]
0.621869080688297
[147.09, 236.26444444444445]
0.6225651106575495
[147.3311111111111, 237.1677777777778]
0.6212104885898871
[148.14777777777778, 237.44555555555556]
0.6239231449548668
[147.99444444444444, 237.80777777777777]
0.6223280240343508
[148.1977777777778, 238.35111111111112]
0.6217624792556267
[148.31666666666666, 237.96777777777777]
0.6232636538093392
[148.94222222222223, 238.3011111111111]
0.6250169020520256
[148.79222222222222, 238.46666666666667]
0.623953965147703
[148.9088888888889, 238.69]
0.6238589337169085
[149.1288888888889, 238.46777777777777]
0.6253628489290424
[149.39, 239.09555555555556]
0.6248129525154982
[149.86333333333334, 240.22555555555556]
0.6238442574802385
[151.55, 239.04333333333332]
0.6339854698590215
[151.0222222222222, 238.38444444444445]
0.6335238130750515
[151.2211111111111, 239.04888888888888]
0.632594913174432
[151.54777777777778, 239.51666666666668]
0.632723308514833
[151.4988888888889, 239.23555555555555]
0.6332624284758862
[150.93555555555557, 238.20666666666668]
0.6336327931861222
[150.65777777777777, 238.21]
0.6324578219964643
[149.93444444444444, 238.49444444444444]
0.6286705956346526
[148.84222222222223, 237.74444444444444]
0.6260597279992522
[148.78, 237.22333333333333]
0.6271727064510236
[148.43444444444444, 237.55333333333334]
0.6248468180244904
[148.18333333333334, 237.56222222222223]
0.6237664050587916
[147.55444444444444, 237.58333333333334]
0.6210639541681281
[147.55666666666667, 237.2888888888889]
0.6218439782730849
[147.28222222222223, 237.42222222222222]
0.6203388244103333
[147.38111111111112, 237.31666666666666]
0.6210314394737458
[147.10222222222222, 237.3322222222222]
0.6198156358409918
[147.16444444444446, 237.39333333333335]
0.6199181854774543
[147.58333333333334, 238.4788888888889]
0.6188528218197744
[148.13444444444445, 238.49444444444444]
0.6211232500174707
[148.46333333333334, 238.28333333333333]
0.6230537875078688
[148.09666666666666, 237.01222222222222]
0.6248482262986906
[147.54111111111112, 236.95222222222222]
0.6226618586963149
[147.53555555555556, 237.14888888888888]
0.6221220611523938
[147.1688888888889, 236.87444444444444]
0.6212949194838334
[146.9988888888889, 236.7511111111111]
0.6209005237567817
[147.28555555555556, 236.34444444444443]
0.6231817968125618
[147.1511111111111, 236.42111111111112]
0.6224110462028677
[147.52666666666667, 236.87]
0.6228170163662206
[146.88333333333333, 236.62666666666667]
0.6207387164027722
[147.26222222222222, 236.6588888888889]
0.6222551914851662
[147.5211111111111, 237.05555555555554]
0.622306069838294
[147.13, 236.82888888888888]
0.6212502228519419
[146.77, 237.05444444444444]
0.6191404693717806
[146.5088888888889, 236.43333333333334]
0.6196625781286714
[146.20111111111112, 235.9477777777778]
0.6196333463619539
[146.37555555555556, 236.69]
0.6184272912060313
[146.70333333333335, 237.75]
0.6170487206449352
[146.50666666666666, 238.04]
0.6154707892230997
[146.69333333333333, 237.8177777777778]
0.616830813508008
[146.27777777777777, 234.89444444444445]
0.6227383458290958
[146.7588888888889, 184.80666666666667]
0.7941211836994817
[146.25, 185.9922222222222]
0.7863232034792376
[146.12222222222223, 186.18777777777777]
0.7848110330669755
[146.3188888888889, 186.43444444444444]
0.7848275533252678
[146.57777777777778, 186.19666666666666]
0.7872202032498494
[146.53, 185.87777777777777]
0.7883137067368045
[146.66333333333333, 185.5077777777778]
0.7906047664967626
[146.80777777777777, 185.04111111111112]
0.7933792490557653
[147.31, 184.39888888888888]
0.798865984972192
[147.49666666666667, 183.59777777777776]
0.8033684745639623
[147.50444444444443, 182.88111111111112]
0.8065592096869246
[147.4477777777778, 184.39555555555555]
0.7996276121381571
[147.59777777777776, 184.42777777777778]
0.8003012320390396
[147.63555555555556, 184.10222222222222]
0.8019216377374888
[147.79111111111112, 184.37777777777777]
0.801566831384838
[148.0911111111111, 184.38]
0.8031842450976847
[148.38666666666666, 184.96444444444444]
0.8022442751760098
[148.12, 184.96]
0.8008217993079585
[148.38, 185.65222222222224]
0.7992363259858636
[147.41, 184.5377777777778]
0.7988066279713879
[147.64333333333335, 185.37]
0.7964791138443833
[147.50666666666666, 185.5211111111111]
0.7950937000281489
[147.60111111111112, 184.85333333333332]
0.7984768705520293
[147.88333333333333, 184.73333333333332]
0.8005232767953807
[148.0688888888889, 236.76333333333332]
0.6253877524203729
[148.24555555555557, 238.75444444444443]
0.6209122343272261
[147.73, 238.83777777777777]
0.6185369893093405
[147.33777777777777, 239.4477777777778]
0.6153232205584145
[148.37555555555556, 239.31222222222223]
0.6200082644244386
[148.3711111111111, 238.65222222222224]
0.6217042930903639
[148.70333333333335, 238.50444444444443]
0.623482441510524
[148.61555555555555, 238.33]
0.6235704928274054
[148.77, 239.05666666666667]
0.6223210675293166
[149.9688888888889, 239.96777777777777]
0.6249542762685731
[151.01111111111112, 239.85666666666665]
0.6295889674852111
[151.24555555555557, 240.18777777777777]
0.6296971351118802
[151.3388888888889, 239.85666666666665]
0.6309555243640879
[152.14333333333335, 239.62777777777777]
0.6349152620963069
[151.20333333333335, 239.38333333333333]
0.6316368446703335
[150.70222222222222, 239.17]
0.6301050391864458
[150.42222222222222, 238.41555555555556]
0.630924529532935
[149.37, 238.63111111111112]
0.6259452059897191
[149.69333333333333, 238.35555555555555]
0.6280253589408913
[149.00333333333333, 238.01666666666668]
0.6260205867936418
[148.94, 237.6677777777778]
0.6266730870823418
[148.17111111111112, 237.89]
0.6228555681664262
[148.1811111111111, 238.15777777777777]
0.6221972361926268
[147.77555555555554, 237.82]
0.6213756435773087
[147.38666666666666, 237.8088888888889]
0.6197693759694992
[147.28444444444443, 237.90333333333334]
0.6190936561535263
[146.91555555555556, 237.81555555555556]
0.6177710083444686
[146.93555555555557, 237.89111111111112]
0.617658872873677
[146.7422222222222, 237.68444444444444]
0.6173825239813758
[145.70111111111112, 237.61]
0.6131943567657553
[145.45666666666668, 237.57222222222222]
0.6122629375862312
[144.94333333333333, 237.51]
0.6102620240551275
[144.7488888888889, 237.49]
0.6094946687813756
[144.19666666666666, 237.4322222222222]
0.6073171758958112
[144.55666666666667, 237.38555555555556]
0.6089530861654974
[144.17666666666668, 237.50666666666666]
0.6070426093302644
[144.54666666666665, 237.38666666666666]
0.6089081105369579
[143.69333333333333, 237.34666666666666]
0.6054154260996573
[143.35555555555555, 237.36666666666667]
0.6039413939989702
[143.47444444444446, 237.38444444444445]
0.6043969931569044
[143.13222222222223, 237.22222222222223]
0.603367681498829
[143.05666666666667, 237.36]
0.6026991349286597
[143.00666666666666, 237.26888888888888]
0.6027198396568356
[142.79333333333332, 237.50444444444443]
0.6012238367469147
[143.33777777777777, 237.30555555555554]
0.6040220063209646
[143.4188888888889, 237.27666666666667]
0.60443738907698
[144.07666666666665, 237.44666666666666]
0.6067748547042142
[143.39777777777778, 237.3311111111111]
0.6042097772451053
[143.29666666666665, 237.41]
0.6035831121969026
[143.10555555555555, 237.20666666666668]
0.6032948296375406
[142.77333333333334, 237.24555555555557]
0.6017956079261525
[143.2811111111111, 237.26777777777778]
0.6038793486965032
[142.92444444444445, 237.43666666666667]
0.6019476538772912
[142.55555555555554, 237.3411111111111]
0.6006357469558582
[142.76333333333332, 237.1911111111111]
0.6018915829710688
[142.60444444444445, 237.38333333333333]
0.6007348639097569
[142.85, 237.36888888888888]
0.6018059092270821
[142.75666666666666, 237.17666666666668]
0.601900130704257
[143.05333333333334, 237.2877777777778]
0.6028685281350821
[142.76222222222222, 237.29555555555555]
0.6016219810269425
[143.56444444444443, 237.17333333333335]
0.605314444194588
[143.45, 237.23]
0.604687434135649
[143.03222222222223, 237.24]
0.6029009535585156
[142.89555555555555, 237.20444444444445]
0.6024151692866913
[142.40555555555557, 237.36333333333334]
0.5999475721701845
[142.39666666666668, 237.18555555555557]
0.6003597745787406
[143.38555555555556, 237.29222222222222]
0.6042572917593403
[143.42888888888888, 237.32]
0.6043691593160664
[143.26777777777778, 237.24]
0.6038938533880365
[143.64888888888888, 237.33666666666667]
0.6052536715308305
[143.07333333333332, 237.2811111111111]
0.60296975458083
[143.07111111111112, 237.36555555555555]
0.602745881879333
[143.34222222222223, 237.21666666666667]
0.6042670788543058
[143.25222222222223, 237.2]
0.6039301105489976
[142.96555555555557, 237.28]
0.6025183561849106
[142.64333333333335, 237.38333333333333]
0.6008986870743523
[142.33, 237.23777777777778]
0.59994660771659
[142.64222222222222, 237.37666666666667]
0.6009108823763452
[142.39555555555555, 237.29111111111112]
0.6000880306421553
[142.83666666666667, 237.4]
0.6016708789665824
[142.64444444444445, 237.27333333333334]
0.6011819467468368
[142.76222222222222, 237.2277777777778]
0.6017938689960423
[142.90222222222224, 237.36888888888888]
0.602025913720791
[143.10222222222222, 237.3488888888889]
0.602919284316571
[143.48333333333332, 237.29222222222222]
0.6046693481548769
[143.22666666666666, 237.28555555555556]
0.6036046582411253
[143.59666666666666, 237.29333333333332]
0.6051441254143957
[143.04, 237.40666666666667]
0.602510460251046
[143.1677777777778, 237.31333333333333]
0.603285857422442
[142.8711111111111, 237.26888888888888]
0.6021485234754755
[143.07111111111112, 237.20888888888888]
0.6031439706212997
[142.89555555555555, 237.21]
0.6024010604761837
[142.98222222222222, 237.36]
0.6023854997565816
[142.5, 237.29666666666665]
0.6005141243731476
[142.58333333333334, 237.34222222222223]
0.6007499719111644
[142.94, 237.37777777777777]
0.6021625163826999
[142.0611111111111, 237.23222222222222]
0.59882721571456
[142.31222222222223, 237.26888888888888]
0.599793014957245
[142.23333333333332, 237.36111111111111]
0.5992276184903451
[142.01444444444445, 237.31222222222223]
0.5984286991820433
[142.10666666666665, 237.2422222222222]
0.5989939958223662
[142.29, 237.34444444444443]
0.5995084499789336
[142.61666666666667, 237.19555555555556]
0.6012619685585265
[142.46777777777777, 237.0988888888889]
0.6008791455979455
[142.54, 237.30555555555554]
0.600660189628936
[142.88111111111112, 237.39777777777778]
0.6018637261417781
[143.0077777777778, 237.32555555555555]
0.6025806089150862
[143.32555555555555, 237.46333333333334]
0.6035692060060734
[143.10333333333332, 237.23444444444445]
0.6032148226555072
[142.9911111111111, 237.32444444444445]
0.6025132027416757
[143.17111111111112, 237.29111111111112]
0.6033564023562245
[143.0588888888889, 237.14444444444445]
0.6032563369723095
[143.21666666666667, 237.23444444444445]
0.6036925497983711
[143.63111111111112, 237.2488888888889]
0.6054026713624698
[143.28444444444443, 237.37777777777777]
0.6036135555139487
[143.0222222222222, 237.39111111111112]
0.6024750528897459
[142.43444444444444, 237.18555555555557]
0.6005190497828704
[142.79444444444445, 237.34666666666666]
0.6016281856824524
[142.7488888888889, 237.2588888888889]
0.6016587600043085
[142.76777777777778, 237.31]
0.6016087723980353
[142.5688888888889, 237.25555555555556]
0.6009085374420456
[142.9788888888889, 237.25222222222223]
0.6026450987462943
[143.14222222222222, 237.35666666666665]
0.6030680504257541
[143.1511111111111, 237.18]
0.6035547310528337
[143.30555555555554, 237.30333333333334]
0.6038918777186254
[143.2488888888889, 237.35444444444445]
0.6035230948557947
[143.43777777777777, 237.24666666666667]
0.604593437678553
[143.07777777777778, 237.28444444444443]
0.6029800146097511
[143.03222222222223, 237.38777777777779]
0.6025256378452509
[142.81333333333333, 237.19222222222223]
0.6020995629423861
[142.77555555555554, 237.22222222222223]
0.6018641686182669
[143.23333333333332, 237.28555555555556]
0.6036327537847038
[142.63555555555556, 237.3711111111111]
0.6008968609865472
[142.69222222222223, 237.2588888888889]
0.6014199210426492
[142.88, 237.2577777777778]
0.6022141880373901
[143.18333333333334, 237.29333333333332]
0.6034022588076643
[143.3, 237.35222222222222]
0.6037440840382554
[143.32777777777778, 237.30666666666667]
0.6039770386185714
[143.70111111111112, 237.29222222222222]
0.6055871101267541
[143.07888888888888, 237.28555555555556]
0.6029818736918012
[142.7888888888889, 237.38666666666666]
0.6015034074739759
[143.22222222222223, 237.3088888888889]
0.6035265804530429
[143.39666666666668, 237.33555555555554]
0.6041937809571072
[143.5611111111111, 237.32444444444445]
0.6049149780890669
[143.01666666666668, 237.36555555555555]
0.6025165122712741
[142.98222222222222, 237.32666666666665]
0.6024701068382071
[143.15, 237.21333333333334]
0.6034652352312967
[142.5222222222222, 237.21333333333334]
0.6008187660427556
[142.64555555555555, 237.35333333333332]
0.6009839994756996
[142.5588888888889, 237.20222222222222]
0.6010014895869442
[142.8488888888889, 237.2711111111111]
0.602049226388941
[142.56555555555556, 237.09666666666666]
0.6012971736797462
[142.5377777777778, 237.34444444444443]
0.6005524085951033
[142.8088888888889, 237.17]
0.602137238642699
[142.9622222222222, 237.21444444444444]
0.6026708135629739
[142.80777777777777, 237.22222222222223]
0.602
[142.60444444444445, 237.17777777777778]
0.601255504544177
[142.31333333333333, 237.20777777777778]
0.5999522219151517
[142.46555555555557, 237.1211111111111]
0.6008134614753831
[142.45444444444445, 237.20222222222222]
0.6005611714336572
[142.5222222222222, 237.36666666666667]
0.6004306511257782
[142.18333333333334, 237.2111111111111]
0.5993957562415102
[142.35888888888888, 237.14777777777778]
0.6002961116603337
[142.16333333333333, 237.22]
0.5992889863136891
[142.4322222222222, 237.3488888888889]
0.6000964356268783
[142.30777777777777, 237.25333333333333]
0.5998136075830804
[142.23444444444445, 237.07555555555555]
0.599954069963631
[142.44222222222223, 237.06]
0.600869915726914
[142.13555555555556, 237.18666666666667]
0.5992560945902898
[142.09, 237.19444444444446]
0.5990443845883593
[141.99444444444444, 237.1677777777778]
0.5987088371570055
[142.60777777777778, 237.13]
0.6013907045830463
[142.09333333333333, 237.3177777777778]
0.598747108892905
[142.42555555555555, 237.24666666666667]
0.6003268983992281
[142.2788888888889, 237.2188888888889]
0.5997789196101116
[142.10111111111112, 237.2422222222222]
0.5989705785929056
[142.23, 237.25]
0.5994942044257112
[142.43333333333334, 237.19333333333333]
0.600494673824447
[142.4777777777778, 237.14222222222222]
0.6008115148902675
[142.46444444444444, 237.14]
0.6007609194756028
[142.54888888888888, 237.23444444444445]
0.6008777065350263
[142.42666666666668, 237.2211111111111]
0.6003962547833949
[142.44333333333333, 237.19666666666666]
0.6005283941595582
[142.82777777777778, 237.2]
0.6021407157579165
[142.7211111111111, 237.2811111111111]
0.6014853455582455
[142.76111111111112, 237.19666666666666]
0.6018681169399983
[142.91666666666666, 237.1511111111111]
0.6026396671601791
[142.61888888888888, 237.1988888888889]
0.6012628876845029
[143.00666666666666, 237.30444444444444]
0.6026295335574555
[142.72333333333333, 237.3711111111111]
0.6012666523118979
[142.90444444444444, 237.2411111111111]
0.6023595310912011
[142.98, 237.18666666666667]
0.6028163471808421
[142.41222222222223, 237.3411111111111]
0.6000318341627382
[142.79444444444445, 237.15222222222224]
0.6021214690986099
[142.80666666666667, 237.15555555555557]
0.6021645427286357
[142.78666666666666, 237.29444444444445]
0.6017278112050195
[143.15333333333334, 237.26444444444445]
0.6033492867779974
[142.73222222222222, 237.16444444444446]
0.6018280799070499
[143.46777777777777, 237.16444444444446]
0.604929537873393
[142.6511111111111, 237.1988888888889]
0.601398732428014
[142.49555555555557, 237.35666666666665]
0.6003435991779835
[143.11444444444444, 237.20777777777778]
0.6033294767362883
[143.19444444444446, 237.14333333333335]
0.603830782133637
[143.28666666666666, 237.13]
0.6042536442738863
[143.38111111111112, 237.3022222222222]
0.6042130990953871
[143.02, 237.3322222222222]
0.6026151807826816
[143.43, 237.2811111111111]
0.6044728943166334
[144.14888888888888, 237.4188888888889]
0.6071500442256302
[143.6988888888889, 237.17777777777778]
0.6058699522158718
[143.98555555555555, 237.22333333333333]
0.606962028280898
[143.97222222222223, 237.2711111111111]
0.6067836136814896
[144.09666666666666, 237.37555555555556]
0.6070408822400509
[144.0822222222222, 237.3]
0.6071732921290443
[144.2577777777778, 237.20888888888888]
0.6081465937195534
[144.54666666666665, 237.25444444444443]
0.6092474558490883
[144.33444444444444, 237.24]
0.6083900035594522
[144.54555555555555, 237.23333333333332]
0.6092969884314552
[144.87777777777777, 237.36111111111111]
0.6103686366296079
[144.85666666666665, 237.29222222222222]
0.6104568675285512
[144.95888888888888, 237.50444444444443]
0.6103417947734311
[145.37333333333333, 237.35555555555555]
0.6124707424398464
[144.3011111111111, 237.35333333333332]
0.6079590671198121
[144.03, 237.37444444444444]
0.6067628734722919
[143.96777777777777, 237.30333333333334]
0.6066824926371779
[143.45222222222222, 237.36444444444444]
0.6043542981257138
[142.94444444444446, 237.20111111111112]
0.6026297422253034
[142.88333333333333, 237.38333333333333]
0.6019097100329986
[143.02777777777777, 237.19555555555556]
0.6029951844703854
[142.72, 237.26]
0.6015341819101407
[143.26333333333332, 237.31444444444443]
0.6036856865949068
[143.44666666666666, 237.35444444444445]
0.6043563540696286
[143.4088888888889, 237.09]
0.6048710991137918
[143.48888888888888, 237.07555555555555]
0.6052453976228862
[143.29222222222222, 237.24555555555557]
0.6039827464277518
[143.41444444444446, 237.27666666666667]
0.604418658012915
[143.42222222222222, 237.13]
0.6048252950795859
[143.1977777777778, 237.21]
0.6036751308029922
[143.68333333333334, 237.18]
0.6057986901649942
[143.29222222222222, 237.24333333333334]
0.603988403842281
[143.6988888888889, 237.39555555555555]
0.6053141498483544
[143.70777777777778, 237.13555555555556]
0.6060153123857897
[143.31666666666666, 237.19333333333333]
0.6042187807414486
[143.79777777777778, 237.2111111111111]
0.6062016956297719
[143.86222222222221, 237.17111111111112]
0.6065756556447759
[143.16333333333333, 237.20222222222222]
0.6035497137932003
[143.7811111111111, 237.19444444444446]
0.6061740250614825
[143.04888888888888, 237.20888888888888]
0.6030502885408079
[143.41444444444446, 237.30333333333334]
0.604350737218656
[143.39111111111112, 237.16555555555556]
0.6046034415715229
[143.31444444444443, 237.1911111111111]
0.6042150727027432
[143.54666666666665, 237.1211111111111]
0.6053727818414406
[143.09444444444443, 237.17666666666668]
0.6033242917843707
[142.61888888888888, 237.11111111111111]
0.6014854732895969
[142.85, 237.17777777777778]
0.6022908273212779
[142.54666666666665, 237.22333333333333]
0.6008964829204546
[142.99555555555557, 237.20777777777778]
0.6028282752579783
[143.19666666666666, 237.30777777777777]
0.6034217167578906
[142.88555555555556, 237.29]
0.6021558243312215
[143.22444444444446, 237.14]
0.603965777365457
[143.23222222222222, 237.17222222222222]
0.6039165163617625
[143.3711111111111, 237.41222222222223]
0.6038910287310866
[143.4922222222222, 237.27444444444444]
0.6047521154593601
[143.4922222222222, 237.22]
0.6048909123270475
[143.32777777777778, 237.2511111111111]
0.6041184680085798
[142.96666666666667, 237.35444444444445]
0.6023340620450428
[143.25222222222223, 237.2411111111111]
0.6038254565210265
[143.35222222222222, 237.22444444444446]
0.6042894211763824
[143.16333333333333, 237.27666666666667]
0.603360352893247
[143.40555555555557, 237.20444444444445]
0.6045652133180941
[143.18333333333334, 237.07555555555555]
0.6039565445615088
[142.92, 237.16666666666666]
0.6026141953619114
[143.2422222222222, 237.17888888888888]
0.6039417036367298
[142.43666666666667, 237.12555555555556]
0.6006803709239831
[142.79666666666665, 237.31]
0.6017305072127878
[142.48888888888888, 237.13555555555556]
0.6008752612195556
[142.21444444444444, 237.13555555555556]
0.5997179297354537
[142.36555555555555, 237.12666666666667]
0.600377669693647
[142.26333333333332, 237.22333333333333]
0.5997021091236107
[142.36333333333334, 237.1988888888889]
0.6001854983394151
[142.50222222222223, 237.0388888888889]
0.6011765533081773
[142.15555555555557, 237.0988888888889]
0.5995623017118971
[142.28333333333333, 237.17444444444445]
0.5999100521416492
[142.30666666666667, 237.25666666666666]
0.5998004973516726
[142.63888888888889, 237.20444444444445]
0.6013331209833055
[142.74666666666667, 237.07111111111112]
0.6021259443954932
[142.37444444444444, 237.11666666666667]
0.6004404770272486
[142.39333333333335, 237.10777777777778]
0.6005426505527257
[142.2411111111111, 237.14333333333335]
0.599810709884786
[142.11222222222221, 237.13333333333333]
0.5992924749320588
[142.12555555555556, 237.18555555555557]
0.5992167407608671
[142.56444444444443, 237.13555555555556]
0.6011938787941261
[142.45111111111112, 237.09777777777776]
0.6008116670103286
[142.40333333333334, 237.07333333333332]
0.6006720845870477
[142.92666666666668, 237.12666666666667]
0.6027439624392027
[142.45555555555555, 237.04222222222222]
0.6009712287543709
[142.66, 237.03]
0.6018647428595536
[142.21777777777777, 237.21444444444444]
0.5995325373665646
[142.46, 237.12333333333333]
0.6007844019286729
[142.14, 237.22222222222223]
0.5991850117096018
[142.56555555555556, 237.05333333333334]
0.6014070907625101
[142.5511111111111, 236.96444444444444]
0.6015717313427237
[142.55, 236.92333333333335]
0.6016714267625252
[142.64111111111112, 236.99777777777777]
0.6018668717006255
[142.53222222222223, 237.11222222222221]
0.6011171456553625
[142.60555555555555, 237.1]
0.6014574253713857
[142.8711111111111, 237.07222222222222]
0.6026480444309048
[142.48555555555555, 237.16]
0.6007992728771949
[142.88666666666666, 237.09333333333333]
0.6026599932516027
[142.96777777777777, 237.1688888888889]
0.6028099994378127
[142.97666666666666, 237.1677777777778]
0.6028503028798178
[143.2577777777778, 237.21]
0.6039280712355204
[143.36222222222221, 237.0377777777778]
0.6048074849766094
[143.45444444444445, 237.11222222222221]
0.6050065369890488
[143.12555555555556, 237.0888888888889]
0.6036788827443996
[143.3411111111111, 237.2211111111111]
0.6042510737755212
[143.05555555555554, 237.10555555555555]
0.6033412216781087
[143.23444444444445, 237.13444444444445]
0.6040220971694444
[143.08333333333334, 237.07444444444445]
0.6035375667277508
[142.58555555555554, 237.21555555555557]
0.6010801240315886
[142.79777777777778, 237.08666666666667]
0.6023020180149781
[142.69444444444446, 237.02333333333334]
0.6020269921854857
[143.2288888888889, 237.16333333333333]
0.6039250961597025
[143.44222222222223, 237.20222222222222]
0.6047254569471899
[142.88666666666666, 237.10333333333332]
0.6026345756421251
[142.81333333333333, 237.1]
0.6023337550963026
[142.31444444444443, 237.07111111111112]
0.6003027689769594
[142.13222222222223, 237.27777777777777]
0.5990119409974245
[142.0588888888889, 237.05666666666667]
0.5992613111726686
[142.10444444444445, 237.07222222222222]
0.5994141494621893
[142.17555555555555, 237.0811111111111]
0.5996916198394361
[141.89222222222222, 237.23555555555555]
0.5981068979729477
[141.8177777777778, 237.14444444444445]
0.5980227709319216
[141.69333333333333, 237.15444444444444]
0.5974728142466934
[142.29, 237.1288888888889]
0.6000534168009896
[142.58333333333334, 237.2488888888889]
0.6009863059890224
[142.52555555555554, 237.12555555555556]
0.6010552309371968
[142.95111111111112, 237.11222222222221]
0.602883772803314
[142.85777777777778, 237.04444444444445]
0.6026624167994751
[142.0211111111111, 237.0677777777778]
0.5990738701074704
[142.38777777777779, 237.08666666666667]
0.6005726925924885
[141.85666666666665, 236.9911111111111]
0.5985737861710706
[142.15333333333334, 237.05444444444444]
0.5996653370768085
[142.22222222222223, 236.99444444444444]
0.6001078318760402
[142.14666666666668, 237.23777777777778]
0.599173824667235
[142.2511111111111, 237.09444444444443]
0.5999765681748951
[142.09, 237.09222222222223]
0.5993026623489219
[142.06, 237.1911111111111]
0.5989263228901215
[142.03333333333333, 237.24]
0.5986904962625751
[141.88888888888889, 237.10888888888888]
0.5984123562545104
[142.04333333333332, 236.97555555555556]
0.5994007820778514
[142.00444444444443, 237.08]
0.598972686200626
[142.02333333333334, 237.26222222222222]
0.5985922748389031
[142.0077777777778, 237.00666666666666]
0.5991720814229323
[141.64888888888888, 237.01888888888888]
0.5976270058176328
[142.20444444444445, 237.0311111111111]
0.5999399984999625
[142.4711111111111, 237.15777777777777]
0.6007439960270237
[142.53555555555556, 237.04777777777778]
0.6012946288371308
[142.49333333333334, 237.08555555555554]
0.601020728569621
[143.03444444444443, 237.04444444444445]
0.6034077060091871
[142.84, 237.15333333333334]
0.6023107412925534
[142.61666666666667, 237.04555555555555]
0.6016424409747775
[142.87, 237.07444444444445]
0.6026377087365901
[142.53333333333333, 237.02666666666667]
0.601338808572875
[142.70888888888888, 237.15333333333334]
0.6017578875364273
[142.76666666666668, 237.0588888888889]
0.6022413558750053
[142.50444444444443, 237.09666666666666]
0.601039426019392
[142.59555555555556, 237.08]
0.6014659842903474
[142.0688888888889, 237.23888888888888]
0.5988431726108236
[142.35333333333332, 237.07]
0.6004696221931638
[141.98444444444445, 236.9]
0.5993433703860044
[141.8788888888889, 236.92333333333335]
0.5988388179955072
[142.45555555555555, 236.92111111111112]
0.6012784377359552
[142.47, 236.98555555555555]
0.6011758803865215
[142.59666666666666, 236.9911111111111]
0.6016962661515669
[142.44555555555556, 236.98555555555555]
0.6010727329841951
[142.63111111111112, 237.04333333333332]
0.6017090171042333
[142.95555555555555, 237.19333333333333]
0.6026963470961335
[142.8788888888889, 236.9711111111111]
0.6029380046325384
[142.49333333333334, 237.00666666666666]
0.6012207814126186
[142.41444444444446, 236.95222222222222]
0.6010259921128029
[141.79, 237.13222222222223]
0.597936453642834
[142.36555555555555, 237.15222222222224]
0.6003129729147242
[141.81555555555556, 237.04555555555555]
0.5982628749279323
[142.57111111111112, 237.02444444444444]
0.601503829890963
[142.99333333333334, 237.10111111111112]
0.6030901022067472
[143.14555555555555, 237.0511111111111]
0.6038594583446607
[143.29666666666665, 236.98888888888888]
0.6046556331754888
[142.89, 237.04555555555555]
0.602795524535837
[142.9777777777778, 237.1822222222222]
0.6028182738072931
[142.35444444444445, 237.04666666666665]
0.600533415829982
[142.63888888888889, 237.10222222222222]
0.6015923745969858
[142.4, 237.10222222222222]
0.6005848391692284
[142.4111111111111, 237.2411111111111]
0.6002800713760497
[142.49666666666667, 236.98]
0.6013025009142825
[142.4011111111111, 237.02]
0.6007978698468952
[142.4088888888889, 237.1288888888889]
0.6005547850208045
[142.26444444444445, 237.2]
0.5997657860221098
[142.41, 237.13777777777779]
0.6005369592923008
[142.29555555555555, 237.05444444444444]
0.600265293017544
[142.30666666666667, 237.00222222222223]
0.6004444402771657
[142.65777777777777, 237.1977777777778]
0.601429655514854
[142.37777777777777, 237.0888888888889]
0.6005248851813665
[142.37333333333333, 237.00333333333333]
0.6007229152895177
[142.85333333333332, 237.03666666666666]
0.6026634416616276
[142.51777777777778, 237.04]
0.6012393595080062
[141.96444444444444, 236.9988888888889]
0.5990089029953257
[142.31333333333333, 237.0077777777778]
0.6004584940953649
[142.40444444444444, 237.02777777777777]
0.600792218446033
[142.61333333333334, 237.04666666666665]
0.6016255589616673
[142.70666666666668, 237.18777777777777]
0.6016611311244257
[142.45777777777778, 236.95222222222222]
0.6012088700488144
[142.81666666666666, 237.08]
0.6023986277487205
[142.57555555555555, 237.08666666666667]
0.6013647142629511
[142.77666666666667, 237.20222222222222]
0.6019195997789041
[142.7488888888889, 236.99777777777777]
0.6023216345207175
[142.60111111111112, 237.08333333333334]
0.6014809607498536
[142.44555555555556, 237.06]
0.6008839768647413
[142.36666666666667, 237.04222222222222]
0.6005962369573166
[142.85555555555555, 237.00555555555556]
0.6027519279904362
[142.88777777777779, 237.01444444444445]
0.602865273096342
[142.59444444444443, 237.01666666666668]
0.6016220143918617
[143.05555555555554, 237.00666666666666]
0.6035929603480445
[142.7277777777778, 237.1611111111111]
0.6018177984960997
[143.0388888888889, 236.98]
0.603590551476449
[142.76777777777778, 237.06222222222223]
0.602237574757682
[142.78444444444443, 237.01222222222222]
0.6024349424080333
[142.82333333333332, 237.23222222222222]
0.6020401950269075
[142.6588888888889, 237.02666666666667]
0.6018685192477171
[142.71444444444444, 236.92222222222222]
0.6023683346621019
[142.93333333333334, 237.00555555555556]
0.6030800965753265
[142.47555555555556, 236.99444444444444]
0.6011767739515694
[142.85222222222222, 236.9988888888889]
0.6027548183535788
[142.89333333333335, 237.00666666666666]
0.6029084976512616
[142.61, 237.04]
0.6016284171447858
[142.6822222222222, 236.98888888888888]
0.602062919030428
[142.44444444444446, 237.1288888888889]
0.6007047269183192
[142.18444444444444, 237.06222222222223]
0.5997768987045126
[142.20111111111112, 237.07333333333332]
0.5998190902018129
[142.08333333333334, 237.0011111111111]
0.5995049249651901
[142.4322222222222, 237.01555555555555]
0.6009403977235437
[142.13666666666666, 236.82333333333332]
0.6001801624276887
[142.29333333333332, 236.85888888888888]
0.600751502300948
[142.32444444444445, 237.07]
0.6003477641390494
[142.65444444444444, 236.95111111111112]
0.6020416776081329
[142.17222222222222, 236.98555555555555]
0.5999193574854539
[142.38444444444445, 237.01444444444445]
0.6007416331869132
[142.51333333333332, 236.9177777777778]
0.6015307701687411
[142.55666666666667, 237.05777777777777]
0.6013583186471184
[142.51888888888888, 237.00666666666666]
0.6013286077278651
[142.31444444444443, 236.97444444444446]
0.6005476446124054
[142.43777777777777, 236.97666666666666]
0.601062458094796
[142.25333333333333, 236.98333333333332]
0.6002672480483859
[142.45888888888888, 237.0011111111111]
0.6010895401334264
[142.24, 237.12444444444444]
0.5998538039098084
[142.36777777777777, 236.89555555555555]
0.6009727681209722
[142.42888888888888, 236.9711111111111]
0.601039038982717
[142.29, 236.9488888888889]
0.6005092518780422
[142.40444444444444, 237.14222222222222]
0.6005022771145304
[142.7422222222222, 236.96333333333334]
0.6023810528586232
[142.7711111111111, 236.95777777777778]
0.6025170916525213
[142.7511111111111, 236.98]
0.6023761967723483
[143.06222222222223, 237.02444444444444]
0.6035758149651701
[142.55444444444444, 236.99]
0.6015209268089136
[142.45888888888888, 237.03]
0.6010162801708175
[142.6988888888889, 237.03222222222223]
0.6020231660955613
[142.38, 236.97333333333333]
0.6008270972823946
[142.07111111111112, 237.05]
0.5993297241557103
[142.03222222222223, 236.98]
0.5993426543261973
[141.43, 237.02333333333334]
0.5966923087741011
[141.84555555555556, 237.0077777777778]
0.5984848129691008
[141.75, 236.99444444444444]
0.5981152863405144
[142.16222222222223, 237.06444444444443]
0.5996775372847515
[142.48777777777778, 236.9322222222222]
0.6013862379771056
[142.54777777777778, 236.95333333333335]
0.6015858725112305
[142.27333333333334, 236.9911111111111]
0.600331939313242
[141.80555555555554, 237.11444444444444]
0.5980468878131985
[142.23444444444445, 236.91]
0.6003733250789095
[141.99555555555557, 236.93777777777777]
0.5992947046575754
[142.07222222222222, 236.94444444444446]
0.599601406799531
[142.49444444444444, 237.06666666666666]
0.6010733033370829
[142.1, 236.93666666666667]
0.599738326697711
[141.95, 237.02]
0.5988946080499535
[142.32222222222222, 236.9188888888889]
0.6007212970214841
[142.70111111111112, 236.92333333333335]
0.6023092327100656
[142.87444444444444, 236.92]
0.6030493181008123
[142.92777777777778, 236.8711111111111]
0.6033989417592315
[143.01555555555555, 237.0311111111111]
0.6033619590489763
[142.82333333333332, 236.92333333333335]
0.602825105167635
[142.66222222222223, 237.13444444444445]
0.6016090262907586
[142.19333333333333, 236.95666666666668]
0.600081590164165
[142.29222222222222, 236.93333333333334]
0.6005580566497842
[142.11, 236.98111111111112]
0.5996680466797636
[142.10444444444445, 237.17111111111112]
0.5991642227365147
[141.59777777777776, 236.9688888888889]
0.5975374170073895
[141.98111111111112, 236.94]
0.5992281215122441
[142.11111111111111, 236.88888888888889]
0.599906191369606
[142.30555555555554, 236.96666666666667]
0.6005298447976742
[142.46666666666667, 236.84666666666666]
0.6015143412052805
[142.87222222222223, 236.92777777777778]
0.6030201420967478
[142.79444444444445, 236.8177777777778]
0.6029718114255687
[142.45888888888888, 236.9188888888889]
0.6012981470451678
[142.09666666666666, 237.06444444444443]
0.5994010067585935
[142.36666666666667, 237.0288888888889]
0.6006300216569944
[142.23888888888888, 236.93777777777777]
0.6003216972107069
[141.86777777777777, 236.98111111111112]
0.598645930524233
[142.7511111111111, 236.9188888888889]
0.6025315743315809
[142.60111111111112, 237.01555555555555]
0.6016529622997084
[142.8, 236.79888888888888]
0.6030433701359336
[142.91333333333333, 236.9311111111111]
0.6031851733743516
[142.6988888888889, 236.97444444444446]
0.6021699480018942
[142.38222222222223, 236.87222222222223]
0.6010929474400168
[142.5811111111111, 237.01]
0.6015826805244974
[142.2811111111111, 236.92222222222222]
0.6005393237349341
[142.42777777777778, 236.86777777777777]
0.6012965508183187
[142.07, 236.70888888888888]
0.6001886987298041
[142.05777777777777, 236.8788888888889]
0.5997063665914601
[142.23888888888888, 236.90666666666667]
0.6004005327930362
[142.4411111111111, 236.88111111111112]
0.6013189926498524
[141.85777777777778, 236.9622222222222]
0.5986514493637055
[142.46333333333334, 236.96666666666667]
0.6011956674637783
[142.5, 236.91333333333333]
0.6014857753890311
[142.33555555555554, 236.85555555555555]
0.6009382183234038
[142.38555555555556, 236.99555555555557]
0.6007942014852599
[142.65, 236.83444444444444]
0.6023194824326417
[143.04444444444445, 237.11777777777777]
0.6032632634508871
[143.11, 236.82333333333332]
0.6042901178093376
[142.57444444444445, 236.97444444444446]
0.6016448093324643
[142.45888888888888, 237.00222222222223]
0.6010867221123102
[142.70555555555555, 236.93333333333334]
0.60230256987432
[142.64666666666668, 236.9111111111111]
0.6021104962011069
[142.40444444444444, 237.06555555555556]
0.6006964787049057
[142.77666666666667, 236.94444444444446]
0.6025744431418523
[142.8, 236.9488888888889]
0.6026616147879993
[142.74333333333334, 237.05]
0.6021655065738593
[142.93555555555557, 236.9711111111111]
0.6031771336402938
[142.57111111111112, 236.93666666666667]
0.6017266686362507
[142.61666666666667, 237.08666666666667]
0.6015381154570761
[142.33, 236.9488888888889]
0.6006780646552937
[142.28444444444443, 237.0011111111111]
0.6003534910759912
[142.61, 236.92333333333335]
0.6019246732416956
[142.42777777777778, 237.15]
0.6005809731299927
[142.48777777777778, 236.91444444444446]
0.6014313652842329
[142.42888888888888, 236.9322222222222]
0.6011376905725501
[142.82888888888888, 236.97]
0.6027298345313283
[142.95444444444445, 237.09222222222223]
0.6029486885084566
[142.93, 236.93333333333334]
0.6032498593134497
[142.9988888888889, 237.03444444444443]
0.6032831609095726
[142.6911111111111, 237.0011111111111]
0.6020693761398211
[142.65777777777777, 236.98888888888888]
0.6019597730789066
[142.68777777777777, 236.91]
0.6022868506089982
[142.43777777777777, 236.84666666666666]
0.6013923682457474
[142.93555555555557, 236.92]
0.6033072579586172
[142.1977777777778, 236.87555555555556]
0.600305833348969
[142.3788888888889, 236.95444444444445]
0.6008703032462874
[142.55333333333334, 236.90555555555557]
0.6017306474685177
[142.3, 236.86222222222221]
0.6007711937553947
[142.45, 236.9711111111111]
0.601128126260116
[142.22, 236.98222222222222]
0.6001294049248889
[142.49666666666667, 236.92444444444445]
0.6014434981616268
[142.7722222222222, 236.92]
0.6026178550659388
[142.46, 236.88444444444445]
0.6013902699863037
[142.1977777777778, 237.10888888888888]
0.5997150863644458
[142.17222222222222, 236.88555555555556]
0.6001726103087754
[142.35555555555555, 236.90555555555557]
0.6008958093942733
[142.13222222222223, 236.99666666666667]
0.5997224527302306
[142.45888888888888, 237.04777777777778]
0.6009712059922284
[142.19222222222223, 236.85888888888888]
0.6003246189714457
[141.90333333333334, 236.95666666666668]
0.5988577377016895
[142.06222222222223, 237.03]
0.5993427929891669
[142.13555555555556, 237.07666666666665]
0.5995341403859042
[142.05333333333334, 236.9477777777778]
0.5995132542097884
[142.1511111111111, 236.9177777777778]
0.6000018759438343
[142.56666666666666, 236.98555555555555]
0.6015837814775397
[142.86333333333334, 237.07]
0.6026208855331057
[142.45222222222222, 236.98555555555555]
0.6011008640939204
[143.21777777777777, 236.92666666666668]
0.6044814616805949
[142.76333333333332, 236.87444444444444]
0.6026962244414528
[142.95111111111112, 237.08666666666667]
0.6029487576038767
[142.8411111111111, 236.88]
0.6030104319111411
[142.71, 236.98222222222222]
0.60219707057257
[142.62666666666667, 236.91222222222223]
0.6020232528690889
[142.56, 236.85333333333332]
0.6018914658860617
[142.42222222222222, 236.86111111111111]
0.6012900199366717
[142.29333333333332, 236.98111111111112]
0.6004416667057383
[142.3022222222222, 236.97555555555556]
0.6004932529374806
[142.40222222222224, 236.93666666666667]
0.6010138668092271
[142.49444444444444, 236.85777777777778]
0.6016034000713039
[142.29333333333332, 236.97222222222223]
0.6004641894267964
[142.32111111111112, 237.07444444444445]
0.6003224491134993
[142.95555555555555, 236.95666666666668]
0.6032983058318211
[142.4711111111111, 236.89]
0.6014230702482634
[142.57888888888888, 236.9011111111111]
0.6018498107508524
[142.40444444444444, 236.98888888888888]
0.6008908059449576
[142.30777777777777, 237.13]
0.6001255757507602
[142.42222222222222, 236.86444444444444]
0.6012815581345167
[142.18, 237.07555555555555]
0.5997244197817855
[142.26222222222222, 236.91333333333333]
0.6004821266098245
[142.35111111111112, 236.9711111111111]
0.6007108226975628
[142.85222222222222, 236.89111111111112]
0.6030290522602978
[142.82444444444445, 237.11333333333334]
0.6023467446415685
[142.83444444444444, 236.95777777777778]
0.6027843685232249
[142.84, 236.94]
0.6028530429644636
[143.4388888888889, 236.92333333333335]
0.6054232264539396
[142.81666666666666, 237.0522222222222]
0.6024692168157978
[142.76888888888888, 236.95222222222222]
0.6025218398458199
[142.75444444444443, 236.95555555555555]
0.6024524055143955
[143.0288888888889, 237.05555555555554]
0.6033559878134521
[142.9, 237.03666666666666]
0.6028603169692452
[142.47555555555556, 236.92333333333335]
0.6013572135383691
[142.48333333333332, 236.91222222222223]
0.6014182467955782
[142.6511111111111, 236.9088888888889]
0.6021349041825736
[142.7711111111111, 237.0388888888889]
0.6023109194459418
[142.46, 236.86555555555555]
0.6014382279680457
[142.63888888888889, 236.83444444444444]
0.602272567334894
[142.70444444444445, 236.85888888888888]
0.602487181772551
[142.1511111111111, 236.89888888888888]
0.6000497164753833
[142.60444444444445, 237.10333333333332]
0.6014442835519441
[142.47444444444446, 236.93]
0.6013356031082786
[142.88666666666666, 236.94555555555556]
0.6030358591518914
[142.71666666666667, 237.12333333333333]
0.6018668203607125
[142.58, 236.9411111111111]
0.6017528968754544
[142.95222222222222, 236.91555555555556]
0.6033889243237159
[142.5377777777778, 236.93666666666667]
0.6015859840651276
[142.4622222222222, 237.12777777777777]
0.6007825129442635
[142.53333333333333, 236.92666666666668]
0.6015926165620867
[142.65, 237.01444444444445]
0.6018620524768767
[142.61111111111111, 237.01555555555555]
0.6016951536232972
[142.64111111111112, 237.08555555555554]
0.6016440384858724
[142.54111111111112, 236.82333333333332]
0.6018879521068213
[142.57444444444445, 236.95]
0.6017068767438044
[142.95666666666668, 236.87777777777777]
0.6035039166940289
[142.99333333333334, 236.9622222222222]
0.6034435868821098
[142.61444444444444, 236.97333333333333]
0.6018164256643973
[143.05666666666667, 236.8177777777778]
0.6040790856542302
[142.88555555555556, 236.94444444444446]
0.603033997655334
[142.58666666666667, 236.91]
0.6018600593755716
[143.20777777777778, 236.88777777777779]
0.6045384828259044
[142.86666666666667, 236.91333333333333]
0.6030334580859387
[142.86, 236.88]
0.6030901722391084
[142.70111111111112, 236.86111111111111]
0.602467456315234
[142.37666666666667, 237.1]
0.6004920567974132
[142.80777777777777, 237.0288888888889]
0.60249102312892
[142.2422222222222, 236.95333333333335]
0.6002963546502358
[142.54, 236.85444444444445]
0.6018042022995839
[142.3322222222222, 236.97222222222223]
0.6006282967999061
[142.4611111111111, 237.0811111111111]
0.6008960833844956
[142.50333333333333, 236.8188888888889]
0.6017397260916687
[143.25333333333333, 236.95555555555555]
0.6045578167495076
[142.89777777777778, 236.76888888888888]
0.6035327464193869
[142.76666666666668, 236.91555555555556]
0.6026057104265937
[142.76222222222222, 236.83333333333334]
0.6027961529439362
[142.3411111111111, 236.9922222222222]
0.6006151162954246
[144.9788888888889, 237.62222222222223]
0.6101234452445525
[144.69666666666666, 237.6688888888889]
0.6088161868519228
[145.23111111111112, 237.61888888888888]
0.6111934610510763
[144.87555555555556, 237.76]
0.6093352774039181
[144.9411111111111, 237.70222222222222]
0.6097591758128751
[144.82111111111112, 237.51888888888888]
0.6097246066979469
[145.06444444444443, 237.64444444444445]
0.6104264073312137
[144.72333333333333, 237.76777777777778]
0.6086751311971064
[144.9311111111111, 237.59333333333333]
0.6099965393716621
[144.79333333333332, 237.69]
0.6091688053066319
[144.73888888888888, 237.66555555555556]
0.6090023796277682
[145.18777777777777, 237.59666666666666]
0.6110682435686995
[144.62555555555556, 237.55666666666667]
0.6088044489969645
[144.84333333333333, 237.67444444444445]
0.6094190465950156
[144.74444444444444, 237.64111111111112]
0.6090884012773696
[144.86888888888888, 237.56555555555556]
0.6098059482996505
[144.63777777777779, 237.6288888888889]
0.6086708499714775
[144.99777777777777, 237.5522222222222]
0.6103827462499474
[144.97222222222223, 237.6288888888889]
0.6100782733113258
[145.09777777777776, 237.68666666666667]
0.6104582129601062
[144.6811111111111, 237.55777777777777]
0.6090354627178417
[144.5611111111111, 237.6588888888889]
0.6082714254323422
[144.57666666666665, 237.5677777777778]
0.6085701858183161
[144.6988888888889, 237.61111111111111]
0.6089735796118775
[144.84555555555556, 237.58444444444444]
0.6096592556564684
[145.13, 237.81444444444443]
0.6102657066900898
[145.35333333333332, 237.57111111111112]
0.611830843630445
[145.00555555555556, 237.51888888888888]
0.6105011531246638
[145.27666666666667, 237.57777777777778]
0.6114909737162099
[144.8711111111111, 237.76777777777778]
0.6092966526629624
[144.9322222222222, 237.65222222222224]
0.6098500610135258
[144.97666666666666, 237.63777777777779]
0.6100741558113655
[144.9911111111111, 237.6]
0.610231949120838
[145.1, 237.8088888888889]
0.610153811650812
[144.89222222222222, 237.59]
0.609841416819825
[145.00666666666666, 237.56666666666666]
0.6103830503718254
[145.17333333333335, 237.63555555555556]
0.6109074586668662
[145.2722222222222, 237.71555555555557]
0.6111178626182552
[145.5377777777778, 237.61777777777777]
0.6124869070776598
[145.50333333333333, 237.59666666666666]
0.6123963579735967
[145.40444444444444, 237.59777777777776]
0.6119772912204566
[145.14, 237.7277777777778]
0.6105302516884391
[144.90444444444444, 237.70111111111112]
0.6096077707298148
[145.35222222222222, 237.6888888888889]
0.6115229992520568
[145.6688888888889, 237.70777777777778]
0.6128065738979233
[146.47333333333333, 237.8711111111111]
0.6157676426075746
[146.29555555555555, 237.7877777777778]
0.6152358078398572
[146.57666666666665, 237.80444444444444]
0.6163747990879527
[146.9622222222222, 237.89666666666668]
0.6177565422896028
[147.35, 237.88444444444445]
0.6194183917494955
[147.67333333333335, 237.94]
0.6206326524894231
[148.14333333333335, 237.9322222222222]
0.6226282928378297
[148.43666666666667, 237.95888888888888]
0.6237912244411967
[148.20777777777778, 237.9777777777778]
0.6227799047530115
[149.08333333333334, 238.02666666666667]
0.6263303831503473
[148.5888888888889, 238.03666666666666]
0.6242268931490481
[148.69, 238.00333333333333]
0.6247391493116343
[148.87333333333333, 237.96555555555557]
0.6256087482315368
[149.02, 237.95444444444445]
0.6262543250575507
[148.63333333333333, 237.93666666666667]
0.624676034238803
[148.86777777777777, 238.13666666666666]
0.625135893021281
[148.74444444444444, 237.95666666666668]
0.6250904693198107
[148.77777777777777, 238.0077777777778]
0.6250962853688254
[149.35444444444445, 238.08666666666667]
0.6273112498716621
[149.43666666666667, 237.8022222222222]
0.628407359991029
[149.5088888888889, 238.60777777777778]
0.6265884971617764
[149.26, 238.74444444444444]
0.6251873225671336
[148.72555555555556, 237.90555555555557]
0.6251453658080938
[148.08, 237.93555555555557]
0.6223533916746832
[147.68666666666667, 238.22555555555556]
0.6199446836098376
[147.01, 239.11444444444444]
0.6148102024600028
[147.2111111111111, 235.53555555555556]
0.6250058967270806
[146.82444444444445, 237.53222222222223]
0.6181243246530296
[147.26555555555555, 240.41444444444446]
0.6125487006234603
[147.38777777777779, 242.06444444444443]
0.6088782601511077
[147.05777777777777, 242.00333333333333]
0.6076683975886467
[146.17333333333335, 241.9188888888889]
0.6042245564399455
[146.16333333333333, 238.6822222222222]
0.6123762883238523
[146.14111111111112, 236.7877777777778]
0.6171818177552332
[145.88555555555556, 238.17]
0.6125269998553787
[145.67888888888888, 234.92333333333335]
0.6201124716810684
[145.32333333333332, 234.75333333333333]
0.6190469428904097
[145.67555555555555, 237.56666666666666]
0.6131986343014826
[145.11555555555555, 234.00666666666666]
0.6201342791753321
[145.92888888888888, 184.4322222222222]
0.791233154004181
[145.7788888888889, 185.74777777777777]
0.7848217116400377
[145.82111111111112, 187.86666666666667]
0.7761947007333807
[146.39777777777778, 188.09777777777776]
0.7783067907943859
[145.8188888888889, 188.8488888888889]
0.7721458661834271
[146.46, 187.74555555555557]
0.7800983600736221
[146.42, 187.29]
0.7817822628010037
[145.96444444444444, 187.38888888888889]
0.7789386302994367
[146.36666666666667, 187.39111111111112]
0.7810758247752769
[146.04333333333332, 187.67]
0.7781922168345144
[146.20111111111112, 187.05444444444444]
0.7815965642801561
[146.11888888888888, 186.4177777777778]
0.783824861720389
[145.38888888888889, 186.03222222222223]
0.7815253032628755
[145.76333333333332, 185.81]
0.7844751807401825
[145.65555555555557, 184.8488888888889]
0.7879709552547427
[146.4911111111111, 184.12444444444444]
0.7956092497827556
[146.51666666666668, 183.94222222222223]
0.7965363519945877
[146.38333333333333, 186.88111111111112]
0.7832965700118315
[146.49777777777777, 187.89444444444445]
0.7796812631205463
[146.42777777777778, 186.81]
0.783832652308644
[146.71444444444444, 186.9]
0.7849890018429344
[147.12222222222223, 187.46777777777777]
0.7847867189028042
[146.81333333333333, 187.36888888888888]
0.7835523506807723
[146.29666666666665, 184.67]
0.7922059168607065
[146.29777777777778, 183.84222222222223]
0.7957789892298952
[145.53555555555556, 184.58555555555554]
0.7884449848609799
[145.9622222222222, 184.57555555555555]
0.7907993113329079
[146.61111111111111, 184.07555555555555]
0.7964724629982858
[147.13777777777779, 184.25]
0.7985768129051711
[147.12555555555556, 184.39888888888888]
0.7978657379232221
[147.26111111111112, 184.72222222222223]
0.797203007518797
[146.47666666666666, 184.77666666666667]
0.7927227463785109
[146.36111111111111, 184.98444444444445]
0.7912076691133189
[146.85333333333332, 184.57]
0.7956511531307001
[145.7722222222222, 184.84222222222223]
0.7886305437670564
[146.01555555555555, 184.95777777777778]
0.7894534488351695
[145.3411111111111, 185.01333333333332]
0.7855710098971846
[145.41333333333333, 185.49555555555557]
0.7839181531752781
[145.25, 185.20888888888888]
0.7842496160491458
[145.4088888888889, 184.65]
0.787483828263682
[146.19333333333333, 184.46]
0.7925476164660811
[145.98222222222222, 184.27444444444444]
0.7922000397957153
[146.19222222222223, 183.98555555555555]
0.7945853237271042
[146.02555555555554, 183.42222222222222]
0.7961170341652531
[146.07888888888888, 182.31]
0.8012664631061867
[146.17111111111112, 182.3488888888889]
0.8016013259076008
[146.80444444444444, 182.58444444444444]
0.8040358798972773
[146.65444444444444, 182.71777777777777]
0.802628218381718
[146.27444444444444, 182.48777777777778]
0.8015574863461176
[146.69555555555556, 182.19666666666666]
0.8051495026741555
[146.62333333333333, 182.16666666666666]
0.8048856358645929
[146.35666666666665, 181.9777777777778]
0.8042557088777628
[146.35777777777778, 182.48888888888888]
0.8020092547491476
[146.86111111111111, 182.4088888888889]
0.8051203645046537
[146.58333333333334, 181.86333333333334]
0.8060081746366319
[146.29444444444445, 180.79]
0.8091954446841333
[146.23, 181.36888888888888]
0.8062573514997059
[146.24444444444444, 182.04888888888888]
0.8033251141329557
[146.26, 182.35222222222222]
0.8020741300413728
[146.73666666666668, 182.3188888888889]
0.8048352398422789
[147.1911111111111, 182.49666666666667]
0.8065413675744457
[147.08666666666667, 184.15777777777777]
0.7986991830676594
[146.36111111111111, 186.38111111111112]
0.7852786703468997
[145.8388888888889, 187.13777777777779]
0.7793129245238208
[146.15777777777777, 187.13777777777779]
0.7810169572032488
[146.06333333333333, 187.28]
0.7799195500498363
[146.48333333333332, 188.10333333333332]
0.7787386365650085
[146.28, 187.85666666666665]
0.7786787799208617
[145.95333333333335, 187.89555555555555]
0.7767790616536375
[146.28222222222223, 187.81333333333333]
0.7788702730843864
[146.45222222222222, 187.70222222222222]
0.7802370184452916
[146.69666666666666, 187.60222222222222]
0.781955911443835
[146.48666666666668, 187.84222222222223]
0.7798388718664601
[146.34555555555556, 187.81555555555556]
0.7791982678041104
[146.2411111111111, 187.83555555555554]
0.7785592598727019
[146.52777777777777, 187.60888888888888]
0.7810279067563726
[146.78222222222223, 187.8711111111111]
0.7812921388185754
[146.73777777777778, 187.8011111111111]
0.7813466965643322
[146.6822222222222, 187.65666666666667]
0.7816520714543699
[147.56444444444443, 187.52777777777777]
0.7868937935120722
[146.87, 187.45444444444445]
0.7834970274259228
[147.6822222222222, 187.49444444444444]
0.7876618566476044
[147.4688888888889, 187.84333333333333]
0.7850632027871927
[147.47333333333333, 187.80666666666667]
0.7852401405700897
[148.00666666666666, 187.9177777777778]
0.7876139682840012
[147.54888888888888, 187.90222222222224]
0.7852429159373668
[147.73111111111112, 187.67222222222222]
0.7871762233208017
[147.1988888888889, 187.81555555555556]
0.7837417324325283
[147.49666666666667, 188.82555555555555]
0.7811266130408432
[146.5911111111111, 187.8411111111111]
0.7803995102243622
[147.11666666666667, 186.61111111111111]
0.7883596308425127
[147.38777777777779, 185.7888888888889]
0.7933078165181509
[146.84444444444443, 186.63777777777779]
0.7867884315429768
[147.13555555555556, 187.5688888888889]
0.7844347558230458
[147.06666666666666, 187.35555555555555]
0.7849602656861582
[147.1511111111111, 187.58444444444444]
0.7844526317036475
[147.01111111111112, 186.09555555555556]
0.7899764756457256
[147.45777777777778, 185.1611111111111]
0.7963755288187465
[146.91444444444446, 185.3311111111111]
0.7927133418865934
[147.18, 185.80333333333334]
0.7921278771460863
[147.20333333333335, 185.64666666666668]
0.7929220382806048
[147.25222222222223, 184.73]
0.7971213242149203
[147.2288888888889, 184.2588888888889]
0.7990327618748982
[147.73666666666668, 183.56666666666666]
0.8048120573815145
[147.12, 183.75444444444443]
0.8006336959347923
[147.53222222222223, 183.91666666666666]
0.802168856668177
[147.34444444444443, 183.96333333333334]
0.8009446326864652
[146.89555555555555, 184.58444444444444]
0.795817632399504
[147.89555555555555, 184.98666666666668]
0.7994930565566286
[147.08333333333334, 225.96333333333334]
0.6509168154125301
[147.10555555555555, 238.2122222222222]
0.6175399153882393
[147.22333333333333, 235.89]
0.6241185863467436
[147.17666666666668, 236.6511111111111]
0.6219141164207976
[146.66444444444446, 236.09444444444443]
0.6212109090053416
[147.4788888888889, 237.66]
0.6205456908562185
[147.0, 239.22444444444446]
0.6144856991574625
[147.37333333333333, 239.8188888888889]
0.6145192900197834
[148.4911111111111, 240.35333333333332]
0.6178034190404867
[148.76666666666668, 240.93777777777777]
0.6174484883141799
[149.26888888888888, 240.24333333333334]
0.6213237504567128
[150.01222222222222, 241.05777777777777]
0.6223081603303957
[151.08, 240.89]
0.6271742289011583
[151.65444444444444, 240.80333333333334]
0.6297854865427296
[152.34444444444443, 240.63777777777779]
0.6330861506921421
[152.00222222222223, 240.64444444444445]
0.6316465047557485
[150.14333333333335, 240.24444444444444]
0.6249606881879568
[149.27333333333334, 239.89111111111112]
0.6222545414123074
[147.76888888888888, 239.41222222222223]
0.6172153097168528
[146.8177777777778, 238.07888888888888]
0.6166770118214785
[146.31222222222223, 238.60111111111112]
0.6132084697379634
[146.15777777777777, 238.52777777777777]
0.6127495050657971
[146.60444444444445, 238.84666666666666]
0.6138015091039347
[145.8188888888889, 238.13666666666666]
0.6123327874283209
[145.2888888888889, 238.16222222222223]
0.6100417082660745
[144.7888888888889, 238.38666666666666]
0.6073699125603594
[144.28333333333333, 238.30333333333334]
0.6054608272369948
[144.1888888888889, 237.89777777777778]
0.606095988940161
[143.88333333333333, 237.93444444444444]
0.6047183864836719
[143.52333333333334, 238.00666666666666]
0.6030223243046414
[143.85444444444445, 238.09222222222223]
0.6041963198200511
[144.26666666666668, 237.86666666666667]
0.6065022421524664
[144.2211111111111, 237.79777777777778]
0.6064863703053014
[144.27, 237.86777777777777]
0.6065134224896185
[144.5588888888889, 238.0222222222222]
0.6073335822985716
[144.56, 237.87222222222223]
0.6077212322208468
[144.54111111111112, 237.75333333333333]
0.6079456766583481
[144.52444444444444, 237.77444444444444]
0.6078216049757706
[144.91666666666666, 237.37444444444444]
0.6104981814947785
[144.86666666666667, 236.66666666666666]
0.6121126760563381
[143.93777777777777, 236.70333333333335]
0.6080935817455511
[139.26888888888888, 236.79666666666665]
0.5881370327097322
[146.93666666666667, 236.16222222222223]
0.6221853151788319
[146.82888888888888, 236.0911111111111]
0.6219162093730293
[146.70555555555555, 236.34222222222223]
0.6207335878293246
[146.63666666666666, 236.16333333333333]
0.6209120806221683
[150.43555555555557, 236.71666666666667]
0.6355089300382549
[151.44333333333333, 236.7811111111111]
0.6395921221193508
[152.3111111111111, 236.83777777777777]
0.6431031085506254
[152.42333333333335, 236.66222222222223]
0.6440543484384684
[152.29111111111112, 236.7488888888889]
0.6432600880445292
[150.9311111111111, 236.65333333333334]
0.6377730200762484
[150.25, 236.9388888888889]
0.6341297568524467
[149.34444444444443, 236.98333333333332]
0.630189652343109
[132.6911111111111, 236.9488888888889]
0.5599988745814849
[121.84, 237.33333333333334]
0.513370786516854
[132.11444444444444, 237.48333333333332]
0.5563103843544577
[147.04444444444445, 237.3111111111111]
0.6196273059275214
[146.89888888888888, 238.19222222222223]
0.6167241210413624
[147.05555555555554, 238.40222222222224]
0.6168380235083565
[147.45666666666668, 238.46555555555557]
0.6183562499126359
[147.09777777777776, 238.42333333333335]
0.6169604951044126
[147.10555555555555, 238.45333333333335]
0.6169154924327145
[146.9088888888889, 238.39222222222222]
0.6162486658308204
[146.7877777777778, 238.36666666666667]
0.6158066470889852
[146.8111111111111, 238.31]
0.6160509886748818
[146.60444444444445, 238.37555555555556]
0.6150145894899738
[146.65666666666667, 238.42555555555555]
0.6151046448227493
[147.01666666666668, 238.43555555555557]
0.6165886892335223
[146.63666666666666, 238.40666666666667]
0.6150694891082463
[147.03666666666666, 238.3411111111111]
0.6169169304498221
[146.9688888888889, 238.29777777777778]
0.6167446891844005
[146.99444444444444, 238.3188888888889]
0.61679728841375
[147.03444444444443, 238.39111111111112]
0.6167782169357544
[147.20888888888888, 238.29666666666665]
0.6177547128462654
[146.5677777777778, 238.38444444444445]
0.614837843632601
[146.5822222222222, 238.47666666666666]
0.6146606469768764
[146.96555555555557, 238.26777777777778]
0.6168083528802795
[147.0377777777778, 237.9411111111111]
0.6179586919265739
[148.4111111111111, 238.36888888888888]
0.6226110789998694
[148.14444444444445, 238.75666666666666]
0.6204829649899247
[148.52444444444444, 238.8]
0.6219616601526149
[148.6988888888889, 238.26111111111112]
0.6241005432881759
[148.4188888888889, 237.79222222222222]
0.6241536729077205
[147.9388888888889, 238.36888888888888]
0.620630022560737
[147.72555555555556, 238.30555555555554]
0.6198997552162258
[148.15444444444444, 238.45333333333335]
0.6213142100946842
[147.86888888888888, 238.00666666666666]
0.621280449660607
[147.71666666666667, 238.0288888888889]
0.6205829357781035
[147.34777777777776, 238.3488888888889]
0.6182020753890188
[147.01, 238.60111111111112]
0.6161329229164435
[147.07, 237.9788888888889]
0.617995994042422
[146.92333333333335, 238.33666666666667]
0.6164529167424232
[146.88222222222223, 238.13222222222223]
0.6168095222542098
[146.01888888888888, 237.53222222222223]
0.6147329719008883
[146.19555555555556, 238.36888888888888]
0.6133164283183861
[145.5088888888889, 238.4411111111111]
0.6102508422764531
[144.60555555555555, 237.16666666666666]
0.609721246193488
[144.07111111111112, 237.92222222222222]
0.6055386914491198
[145.43333333333334, 239.10555555555555]
0.6082390390111294
[145.60444444444445, 238.58]
0.6102961037993312
[145.0222222222222, 238.45]
0.6081871345029239
[143.78222222222223, 237.1811111111111]
0.6062127862908326
[143.9711111111111, 239.03333333333333]
0.6023055826709431
[143.0511111111111, 239.79222222222222]
0.596562764986354
[139.44666666666666, 235.29111111111112]
0.5926559061588008
[136.12444444444444, 237.83555555555554]
0.5723469063592024
[88.57222222222222, 239.64888888888888]
0.3695916247844068
[58.42666666666667, 241.76]
0.24167218177807193
[40.24111111111111, 243.57555555555555]
0.165209973633552
[35.60111111111111, 243.94222222222223]
0.14594075099750395
[34.87777777777778, 243.95555555555555]
0.1429677536891966
[33.10777777777778, 243.99555555555557]
0.1356900854296071
[89.94, 242.62222222222223]
0.3706997618611467
[117.83222222222223, 233.67222222222222]
0.5042628563277145
[113.72, 227.9488888888889]
0.49888376536650514
[115.56333333333333, 232.94]
0.4961077244497868
[148.07111111111112, 237.5377777777778]
0.6233581558956705
[170.43444444444444, 239.40777777777777]
0.7119001981741984
[99.24555555555555, 237.94]
0.4171032846749414
[79.48444444444445, 236.01111111111112]
0.3367826373522904
[136.86222222222221, 234.79777777777778]
0.5828940270114235
[128.67333333333335, 235.75333333333333]
0.5457964539207647
[75.33555555555556, 236.95777777777778]
0.31792818223593516
[71.87666666666667, 239.99777777777777]
0.2994888841563348
[93.71111111111111, 239.68777777777777]
0.3909715880381422
[115.36444444444444, 237.8111111111111]
0.48510956407980194
[186.72555555555556, 237.73555555555555]
0.7854338620876604
[230.95555555555555, 238.90555555555557]
0.9667232518661488
[237.98, 239.06444444444443]
0.9954637986967717
[235.14111111111112, 239.81444444444443]
0.9805127112165425
[223.0011111111111, 240.19555555555556]
0.9284148101546887
[190.39111111111112, 237.28666666666666]
0.8023675067194861
[172.9011111111111, 234.4177777777778]
0.7375767859851357
[184.48555555555555, 236.0588888888889]
0.7815234428320617
[182.36444444444444, 236.72333333333333]
0.770369535932711
[135.65555555555557, 237.08]
0.5721931649888458
[93.0988888888889, 236.36333333333334]
0.39388041950481134
[69.49111111111111, 234.49555555555557]
0.29634297736038584
[79.64777777777778, 234.60333333333332]
0.339499770297855
[94.06888888888889, 234.87777777777777]
0.40050144283078676
[85.45555555555555, 235.63444444444445]
0.36266156145819084
[70.28, 235.22666666666666]
0.2987756490193856
[43.40111111111111, 234.19666666666666]
0.18531908130393734
[36.29333333333334, 234.53666666666666]
0.1547448160202385
[34.16, 234.5011111111111]
0.1456709515709473
[34.397777777777776, 235.07777777777778]
0.14632509334971877
[34.11555555555555, 235.07555555555555]
0.14512591696286772
[35.754444444444445, 235.66333333333333]
0.15171831756224746
[39.17777777777778, 235.57555555555555]
0.16630663434236714
[43.18222222222222, 235.64888888888888]
0.18324814696063824
[45.78666666666667, 235.3188888888889]
0.19457284913616038
[53.394444444444446, 234.05333333333334]
0.22812939121187953
[65.39111111111112, 234.0]
0.2794491927825261
[73.45111111111112, 235.75333333333333]
0.31155916258990096
[77.69222222222223, 235.7577777777778]
0.3295425625170844
[80.43777777777778, 234.17]
0.3435016346149284
[84.58555555555556, 232.10111111111112]
0.36443408284703505
[93.85444444444444, 232.36666666666667]
0.40390666092860894
[93.54, 235.04666666666665]
0.39796352497376414
[88.88, 236.12777777777777]
0.376406371314966
[83.70111111111112, 235.10888888888888]
0.3560099811907485
[79.36777777777777, 234.80777777777777]
0.33801170697544564
[75.92111111111112, 235.0811111111111]
0.3229570880972525
[75.30333333333333, 234.93]
0.3205351948807446
[74.37666666666667, 234.22]
0.3175504511428002
[73.16555555555556, 233.4611111111111]
0.31339504557028297
[69.75666666666666, 233.31]
0.29898704156129896
[61.94777777777778, 234.68333333333334]
0.26396326018511945
[52.06333333333333, 236.56222222222223]
0.22008304134218856
[44.973333333333336, 235.95444444444445]
0.1906017639939913
[37.03333333333333, 234.77]
0.15774303928667774
[33.83222222222222, 235.0288888888889]
0.1439492071896599
[33.123333333333335, 235.16222222222223]
0.14085312266709507
[31.02, 236.01444444444445]
0.13143263359587218
[29.903333333333332, 235.27777777777777]
0.12709799291617474
[39.81444444444445, 238.70444444444445]
0.1667938966830204
[101.61111111111111, 240.85666666666665]
0.42187377462852504
[107.43444444444444, 240.86777777777777]
0.4460307868309492
[68.41222222222223, 240.23777777777778]
0.28476879388013726
[69.65, 238.8388888888889]
0.29161917610662696
[106.02888888888889, 237.2788888888889]
0.446853444844557
[107.7388888888889, 236.7411111111111]
0.45509159090802426
[92.28666666666666, 236.3011111111111]
0.39054690108195284
[76.2388888888889, 237.2711111111111]
0.3213155134304874
[81.17555555555556, 237.95111111111112]
0.3411438390705841
[93.77111111111111, 236.80777777777777]
0.3959798617725582
[109.10333333333334, 232.00333333333333]
0.4702662318070143
[89.04222222222222, 230.82666666666665]
0.38575361983980283
[57.53888888888889, 226.98333333333332]
0.25349389333529143
[37.022222222222226, 226.13]
0.16372096679884238
[41.02333333333333, 228.29555555555555]
0.1796939639648409
[57.208888888888886, 229.06222222222223]
0.24975261452492284
[146.7711111111111, 228.5588888888889]
0.6421588406586194
[145.8011111111111, 231.38333333333333]
0.6301279742610867
[182.6811111111111, 230.81333333333333]
0.7914668900313866
[219.35888888888888, 234.96444444444444]
0.9335833317570507
[182.28, 234.32444444444445]
0.7778957950040779
[62.285555555555554, 229.45555555555555]
0.27144932448791825
[50.85444444444445, 228.70444444444445]
0.22235879397961464
[95.91, 229.93]
0.4171269516809463
[91.66888888888889, 232.21777777777777]
0.39475396658309253
[82.03222222222222, 234.74666666666667]
0.349449998106706
[58.58111111111111, 240.8088888888889]
0.24326805950315603
[40.223333333333336, 239.88888888888889]
0.167674849467346
[43.82111111111111, 238.55777777777777]
0.1836918147013069
[48.352222222222224, 237.51333333333332]
0.20357687521636214
[61.937777777777775, 234.4688888888889]
0.2641620304991896
[223.0822222222222, 231.3788888888889]
0.9641425079595276
[243.5688888888889, 234.5388888888889]
1.0385010777648815
[243.93, 234.63333333333333]
1.0396221054127008
[245.07888888888888, 232.4188888888889]
1.0544706157942794
[244.91444444444446, 233.76777777777778]
1.0476826480220163
[240.7488888888889, 235.56666666666666]
1.0219989623130985
[218.6977777777778, 238.01111111111112]
0.9188553288828719
[186.9922222222222, 238.9322222222222]
0.7826161766005236
[83.04777777777778, 236.45111111111112]
0.351225999266938
[101.87, 230.29777777777778]
0.44234035162205454
[113.28555555555556, 230.28222222222223]
0.4919422544317601
[101.4088888888889, 229.64888888888888]
0.44158231890228566
[101.81333333333333, 230.52666666666667]
0.4416553399462101
[87.14444444444445, 232.26444444444445]
0.3751949406328036
[55.76777777777778, 234.0]
0.23832383665717
[84.46333333333334, 228.64666666666668]
0.3694054873604105
[92.88666666666667, 227.85111111111112]
0.40766387406981164
[93.33444444444444, 229.09333333333333]
0.4074079463003919
[59.156666666666666, 228.79444444444445]
0.25855814292305074
[56.58111111111111, 227.83666666666667]
0.24834067289920167
[112.49333333333334, 228.63]
0.4920322500692531
[142.99555555555557, 230.0288888888889]
0.6216417261599992
[122.46666666666667, 230.01]
0.5324406185238323
[106.14222222222222, 229.75]
0.4619900858420989
[128.71444444444444, 229.58666666666667]
0.5606355382619974
[123.25, 229.62222222222223]
0.5367511855221135
[93.75, 228.68333333333334]
0.4099555425989359
[73.62666666666667, 228.65222222222224]
0.322002847604562
[69.70222222222222, 229.09333333333333]
0.3042525123190936
[53.16777777777778, 229.73444444444445]
0.2314314595112231
[54.034444444444446, 229.61666666666667]
0.23532457477438243
[54.257777777777775, 228.55333333333334]
0.2373965716730352
[56.702222222222225, 228.11555555555555]
0.24856797724350235
[58.86, 230.29]
0.25559077684658477
[53.574444444444445, 229.60222222222222]
0.23333591428654388
[51.724444444444444, 228.1677777777778]
0.22669478113084426
[51.117777777777775, 229.25666666666666]
0.22297182682195113
[51.79222222222222, 230.65777777777777]
0.2245414081467494
[61.12222222222222, 230.34444444444443]
0.2653514061067966
[58.89888888888889, 227.31]
0.2591126166419818
[55.33, 226.73555555555555]
0.24402877556820965
[53.21, 229.06222222222223]
0.23229496109742137
[51.26777777777778, 231.0077777777778]
0.22193095951555264
[49.47, 229.24777777777777]
0.21579271336690528
[49.88, 230.1988888888889]
0.2166821926932749
[50.467777777777776, 231.04888888888888]
0.2184290001154157
[49.785555555555554, 231.08]
0.21544727174811992
[48.42777777777778, 229.7511111111111]
0.21078364994003174
[49.15888888888889, 229.22]
0.2144616040872912
[48.96333333333333, 230.10333333333332]
0.21278845735973692
[49.31444444444445, 231.21444444444444]
0.2132844449356778
[54.70666666666666, 231.6822222222222]
0.2361280297725812
[56.78333333333333, 231.47]
0.24531616768191702
[52.85, 232.03]
0.22777227082704823
[48.614444444444445, 231.95333333333335]
0.2095871774973893
[45.75666666666667, 231.38444444444445]
0.19775169751159685
[43.553333333333335, 231.05]
0.18850176729423646
[43.29555555555555, 232.87555555555556]
0.1859171326602668
[43.04222222222222, 233.95333333333335]
0.18397781133939342
[42.45777777777778, 233.86555555555555]
0.18154780286869476
[43.03666666666667, 233.85111111111112]
0.18403447587733884
[43.666666666666664, 234.52666666666667]
0.18619062508883139
[43.48888888888889, 234.38111111111112]
0.18554775460669468
[45.278888888888886, 234.70111111111112]
0.1929214935307791
[47.22, 236.56666666666666]
0.19960546709877414
[47.26, 236.40777777777777]
0.19990882044677982
[48.92777777777778, 233.70777777777778]
0.20935451204495642
[48.6, 233.92777777777778]
0.20775643004726055
[49.983333333333334, 236.26444444444445]
0.21155673021755284
[49.92666666666667, 237.07666666666665]
0.21059291649677322
[48.91111111111111, 235.6988888888889]
0.2075152383691056
[48.44888888888889, 235.43555555555557]
0.20578407868159249
[51.85444444444445, 236.42333333333335]
0.21932879345430278
[52.09222222222222, 235.2111111111111]
0.22147007416505265
[51.71, 234.70666666666668]
0.22031755950690224
[51.455555555555556, 235.94555555555556]
0.2180823259603204
[52.15222222222222, 237.56444444444443]
0.21952873606226148
[52.29222222222222, 237.92777777777778]
0.21978191327900623
[51.95666666666666, 236.2211111111111]
0.2199492942111675
[52.291111111111114, 235.01555555555555]
0.22250063825562374
[52.25666666666667, 235.65222222222224]
0.22175333707393663
[52.03777777777778, 236.39444444444445]
0.2201311367535428
[52.693333333333335, 236.36666666666667]
0.2229304752503173
[52.55222222222222, 236.10666666666665]
0.22257830735637377
[52.82111111111111, 236.3011111111111]
0.22353306280593027
[53.278888888888886, 237.05444444444444]
0.224753807142288
[52.443333333333335, 236.45555555555555]
0.22178938959635358
[53.096666666666664, 235.34777777777776]
0.22560938186041463
[53.35, 235.62555555555556]
0.22641856429457283
[53.687777777777775, 236.48555555555555]
0.22702349685440032
[53.74333333333333, 236.08555555555554]
0.22764346258653878
[54.14666666666667, 235.51333333333332]
0.229909134656212
[54.486666666666665, 236.5011111111111]
0.2303865145101503
[54.88444444444445, 236.38]
0.23218734429496762
[53.84777777777778, 234.51333333333332]
0.22961499464612295
[52.88, 233.94]
0.22604086517910577
[53.611111111111114, 235.10888888888888]
0.2280267299312848
[52.99, 235.72555555555556]
0.22479531281669363
[51.68333333333333, 235.0888888888889]
0.2198459211645713
[51.59777777777778, 234.63666666666666]
0.2199050067953763
[52.776666666666664, 235.23666666666668]
0.2243556134956285
[52.95111111111111, 235.78]
0.2245784676864497
[52.885555555555555, 235.42555555555555]
0.22463812575808348
[53.12222222222222, 234.63333333333333]
0.22640526589951224
[53.422222222222224, 235.23333333333332]
0.22710311274857117
[53.852222222222224, 236.0688888888889]
0.2281207933654018
[53.64333333333333, 236.35555555555555]
0.22696032342986083
[52.873333333333335, 235.44444444444446]
0.22456819254365265
[51.763333333333335, 235.0]
0.2202695035460993
[52.91111111111111, 235.2577777777778]
0.2249069578523794
[53.12444444444444, 235.05444444444444]
0.22600910427371435
[53.05444444444444, 234.35111111111112]
0.22638870450795576
[52.67888888888889, 234.52444444444444]
0.22462003486961796
[52.525555555555556, 235.45555555555555]
0.22308055306498042
[52.10333333333333, 235.33]
0.22140540234280937
[51.81666666666667, 233.97333333333333]
0.2214639844996581
[52.03111111111111, 234.59777777777776]
0.2217885932423344
[52.37888888888889, 235.26666666666668]
0.2226362520071786
[52.528888888888886, 235.12222222222223]
0.22341099191909644
[53.25111111111111, 234.91222222222223]
0.22668514480586127
[54.04555555555555, 235.34444444444443]
0.22964449270572682
[54.187777777777775, 235.14333333333335]
0.23044573286269837
[53.68666666666667, 234.48444444444445]
0.22895619704694933
[52.83888888888889, 234.21777777777777]
0.22559725991005522
[52.593333333333334, 234.3111111111111]
0.22445940819423368
[52.172222222222224, 234.44555555555556]
0.2225344903578656
[51.284444444444446, 235.11]
0.2181295752815467
[51.58777777777778, 235.13]
0.21940108781430606
[51.565555555555555, 234.68]
0.2197270988390811
[51.03666666666667, 234.76666666666668]
0.2173931563254295
[51.99888888888889, 235.30444444444444]
0.2209855789662565
[52.51555555555556, 235.48111111111112]
0.22301387702717368
[52.50111111111111, 234.93444444444444]
0.22347132296952812
[52.09777777777778, 234.7577777777778]
0.22192141308772162
[52.458888888888886, 235.3111111111111]
0.2229341769761073
[52.93666666666667, 235.59444444444443]
0.2246940363619214
[52.916666666666664, 235.37555555555556]
0.22481802131817707
[52.55222222222222, 235.33]
0.22331288922883702
[52.723333333333336, 235.05555555555554]
0.22430158354998822
[53.06777777777778, 235.15444444444444]
0.22567201697229716
[52.70666666666666, 235.11222222222221]
0.22417663432592472
[52.925555555555555, 234.95666666666668]
0.2252566667139567
[52.885555555555555, 234.9777777777778]
0.2250662001134859
[52.245555555555555, 234.7211111111111]
0.2225856690445872
[52.37555555555556, 235.04888888888888]
0.22282834776689484
[51.97666666666667, 234.75555555555556]
0.22140761075350246
[51.894444444444446, 234.89444444444445]
0.22092665736382772
[52.14666666666667, 235.69555555555556]
0.22124586330765678
[52.18, 235.60111111111112]
0.22147603529506085
[51.74777777777778, 234.82777777777778]
0.2203648063592704
[51.91777777777778, 234.52666666666667]
0.22137259918322486
[52.464444444444446, 235.03333333333333]
0.22322129248806316
[52.55, 235.27666666666667]
0.22335406542651912
[52.47222222222222, 235.05444444444444]
0.22323433341684432
[52.30888888888889, 234.92666666666668]
0.2226604992574515
[51.84777777777778, 235.18555555555557]
0.2204547709373686
[52.16555555555556, 235.63444444444445]
0.22138340461449232
[51.76777777777778, 235.4477777777778]
0.2198694685776039
[51.867777777777775, 235.04888888888888]
0.22066804069129825
[51.68, 234.75333333333333]
0.22014596881833415
[51.98888888888889, 235.17444444444445]
0.2210652140018993
[52.06666666666667, 235.52777777777777]
0.2210638046939498
[52.03888888888889, 235.41]
0.22105640749708547
[51.66777777777778, 235.14333333333335]
0.21972886513663062
[52.38666666666666, 235.4011111111111]
0.22254213847758672
[52.37444444444444, 235.3188888888889]
0.2225679574289262
[52.28888888888889, 235.1988888888889]
0.2223177547135049
[52.39222222222222, 235.31222222222223]
0.22264981277829454
[52.22888888888889, 235.20777777777778]
0.22205425935461318
[51.87888888888889, 235.02555555555554]
0.22073722479352129
[52.422222222222224, 235.45333333333335]
0.22264378881401362
[53.19, 235.52666666666667]
0.22583430043307196
[51.95777777777778, 234.81555555555556]
0.2212705953608979
[52.34111111111111, 234.48666666666668]
0.22321572418237473
[52.00222222222222, 235.14555555555555]
0.22114907551351173
[51.852222222222224, 235.42888888888888]
0.22024579254882345
[51.54666666666667, 235.04444444444445]
0.21930604141060792
[51.56333333333333, 234.8188888888889]
0.21958767276908445
[52.05222222222222, 235.65444444444444]
0.22088368562254526
[52.25555555555555, 235.70666666666668]
0.2216974016668552
[52.22, 235.30666666666667]
0.22192316409791477
[51.88333333333333, 235.15777777777777]
0.22063201065950994
[51.84, 235.79777777777778]
0.2198494001451338
[52.34111111111111, 236.4788888888889]
0.2213352378177991
[51.49666666666667, 236.07888888888888]
0.2181332981912826
[51.13111111111111, 234.99777777777777]
0.21758125372343948
[51.55555555555556, 235.50333333333333]
0.21891645789396708
[52.01555555555556, 236.19]
0.2202275945448815
[51.75222222222222, 235.78444444444443]
0.21948955260454464
[51.74888888888889, 234.86777777777777]
0.2203320071340376
[51.68, 235.08666666666667]
0.21983382015143352
[52.05777777777778, 235.39222222222222]
0.2211533468961969
[52.0, 235.11666666666667]
0.22116679662578861
[52.373333333333335, 234.8111111111111]
0.2230445275162069
[52.56333333333333, 235.24333333333334]
0.2234423929831522
[53.07555555555555, 235.41]
0.22546007202563847
[53.032222222222224, 235.15]
0.22552507855505943
[52.49111111111111, 234.93555555555557]
0.22342770121357156
[52.22666666666667, 235.28333333333333]
0.2219735071190763
[52.45333333333333, 235.70111111111112]
0.22254173128868482
[51.94111111111111, 235.25555555555556]
0.2207859065791338
[51.94555555555556, 235.49]
0.22058497412015607
[52.00333333333333, 235.42444444444445]
0.2208918171435044
[51.67, 235.27333333333334]
0.21961689949278854
[51.34, 234.86444444444444]
0.21859417725591124
[51.45111111111111, 235.26111111111112]
0.21869790067773395
[51.56777777777778, 235.76666666666668]
0.21872378528677128
[51.59888888888889, 235.48444444444445]
0.21911803563339874
[51.224444444444444, 235.09555555555556]
0.21788776195022355
[51.45666666666666, 235.10555555555555]
0.21886623029844748
[51.846666666666664, 236.06555555555556]
0.21962825768736555
[51.57222222222222, 235.62555555555556]
0.21887363660798914
[50.388888888888886, 234.45666666666668]
0.21491770571202448
[49.99666666666667, 233.90777777777777]
0.213745208225464
[50.13111111111111, 234.58555555555554]
0.21370075831134816
[50.88444444444445, 235.33777777777777]
0.21621876829521636
[51.28111111111111, 235.87666666666667]
0.2174064600615199
[51.72555555555556, 235.73444444444445]
0.2194229853743148
[51.86888888888889, 235.27333333333334]
0.2204622519433661
[52.791111111111114, 235.66333333333333]
0.22401071207985027
[54.053333333333335, 235.6977777777778]
0.22933323276512294
[54.48, 235.9011111111111]
0.23094422804282397
[54.782222222222224, 235.59]
0.2325320354099165
[53.78111111111111, 235.61444444444444]
0.2282589729926009
[53.89555555555555, 236.61444444444444]
0.22777796039501674
[54.25666666666667, 231.4477777777778]
0.23442293197889613
[53.54222222222222, 228.27444444444444]
0.2345519769088865
[53.526666666666664, 232.4]
0.23032128514056224
[53.15222222222222, 241.18333333333334]
0.22038099186879506
[52.52333333333333, 239.05777777777777]
0.21970978656949505
[52.22222222222222, 232.8311111111111]
0.22429228625422337
[51.824444444444445, 237.13666666666666]
0.2185425188475469
[51.602222222222224, 238.94666666666666]
0.21595707084798096
[51.45777777777778, 237.0822222222222]
0.21704612558231087
[51.33888888888889, 234.14777777777778]
0.21925849297452227
[51.53333333333333, 235.76555555555555]
0.21857871991479294
[51.53888888888889, 238.15444444444444]
0.21640951949948448
[51.577777777777776, 240.1611111111111]
0.21476323764139815
[51.54, 237.61]
0.21691006270779847
[51.51888888888889, 237.81333333333333]
0.21663583015623833
[51.53777777777778, 237.7811111111111]
0.21674462507534942
[51.35777777777778, 238.04444444444445]
0.2157486930545183
[51.48555555555556, 235.61777777777777]
0.2185130342928283
[50.83555555555556, 235.32222222222222]
0.21602530808820058
[51.44, 236.07555555555555]
0.21789634203738914
[52.17444444444445, 236.84666666666666]
0.2202878561844982
[51.57222222222222, 235.43333333333334]
0.2190523384775119
[51.904444444444444, 233.43]
0.2223555003403352
[51.492222222222225, 232.07444444444445]
0.2218780372198576
[51.776666666666664, 231.20777777777778]
0.22393998664020337
[51.653333333333336, 230.3311111111111]
0.22425686692587485
[51.87, 231.41555555555556]
0.22414223570872985
[52.43888888888889, 235.91666666666666]
0.22227716943365125
[52.53777777777778, 230.98444444444445]
0.22745158404125337
[51.93, 227.8]
0.22796312554872694
[51.53777777777778, 224.61777777777777]
0.22944656601832247
[51.70777777777778, 223.9911111111111]
0.2308474542640581
[52.23222222222222, 227.15444444444444]
0.229941449527732
[52.361111111111114, 225.78333333333333]
0.23190866366477206
[52.31333333333333, 221.03444444444443]
0.23667502802479254
[52.14666666666667, 217.56333333333333]
0.23968499593987957
[51.71666666666667, 217.47555555555556]
0.237804504209924
[51.32666666666667, 213.85777777777778]
0.2400037408038572
[52.403333333333336, 214.27555555555554]
0.24456048286733595
[51.4, 215.5611111111111]
0.23844746269426045
[51.25222222222222, 218.26444444444445]
0.23481709241592766
[51.64555555555555, 218.24]
0.23664569077875527
[51.452222222222225, 213.65444444444444]
0.24081980768530703
[51.63444444444445, 216.60888888888888]
0.2383763875495004
[52.20333333333333, 218.27333333333334]
0.2391649613634281
[51.69555555555556, 218.82222222222222]
0.23624454148471616
[51.89333333333333, 217.6677777777778]
0.2384061337103945
[52.36888888888889, 219.15444444444444]
0.23895882660123
[52.48111111111111, 221.10777777777778]
0.23735533701513087
[51.94444444444444, 222.13333333333333]
0.233843537414966
[52.06444444444445, 223.13555555555556]
0.23333100955074645
[52.23222222222222, 226.87555555555556]
0.23022410719532976
[52.294444444444444, 230.04222222222222]
0.22732541852220364
[51.90888888888889, 230.22444444444446]
0.2254707966139323
[51.65222222222222, 231.4688888888889]
0.22314973934582039
[52.50333333333333, 236.11111111111111]
0.2223670588235294
[52.69222222222222, 239.05]
0.22042343535754955
[52.39888888888889, 239.2788888888889]
0.21898667756360546
[51.21, 235.7722222222222]
0.2172011593110111
[51.07111111111111, 230.89777777777778]
0.2211849399445642
[51.33222222222222, 229.03444444444443]
0.2241244645395404
[51.74, 230.13444444444445]
0.22482510223492547
[51.083333333333336, 229.52333333333334]
0.22256270241224568
[53.888888888888886, 236.74777777777777]
0.22762151938537495
[53.10666666666667, 238.18444444444444]
0.22296446264799458
[52.044444444444444, 239.66666666666666]
0.2171534538711173
[52.95777777777778, 237.20333333333335]
0.22325899486141754
[55.67444444444445, 166.87444444444444]
0.3336307403437049
[53.181111111111115, 170.45333333333335]
0.31199807050479766
[47.76888888888889, 172.48333333333332]
0.2769478532547428
[42.14222222222222, 162.45444444444445]
0.2594094754768858
[48.48555555555556, 148.7188888888889]
0.32602150216291736
[61.46666666666667, 146.50555555555556]
0.4195517803647947
[65.3788888888889, 165.1611111111111]
0.3958491708432844
[55.28, 175.95888888888888]
0.3141642934271263
[44.035555555555554, 173.04888888888888]
0.25446887199506885
[45.33222222222222, 166.83666666666667]
0.27171618282684995
[54.54666666666667, 170.79777777777778]
0.31936403023718757
[58.181111111111115, 174.89333333333335]
0.33266626006962974
[52.65222222222222, 174.64555555555555]
0.30148045883408303
[47.373333333333335, 169.47222222222223]
0.2795345025405671
[49.55777777777778, 164.84555555555556]
0.3006315675952575
[54.147777777777776, 169.0088888888889]
0.32038420069950296
[54.596666666666664, 172.8411111111111]
0.31587778113488946
[52.025555555555556, 171.82777777777778]
0.3027773287206182
[50.812222222222225, 169.38222222222223]
0.2999855684710451
[52.623333333333335, 168.63444444444445]
0.31205566280778274
[53.15555555555556, 170.18444444444444]
0.31234085893736213
[51.79666666666667, 171.0988888888889]
0.30272941573748774
[51.73222222222222, 172.0822222222222]
0.3006250242132314
[52.62555555555556, 171.08555555555554]
0.3075978879962592
[53.275555555555556, 170.63555555555556]
0.31221837314093714
[52.65777777777778, 170.22]
0.30935129701432135
[52.09, 170.5688888888889]
0.30538980666006565
[52.45111111111111, 171.00333333333333]
0.3067256648668317
[53.32555555555555, 169.8411111111111]
0.31397319062915013
[53.00333333333333, 169.78444444444443]
0.3121801499941102
[52.51777777777778, 169.52444444444444]
0.30979471986996304
[52.63, 169.66555555555556]
0.31019849507855324
[53.22555555555556, 169.13111111111112]
0.31469996978018366
[53.37111111111111, 169.35111111111112]
0.31515064035271884
[52.86555555555555, 168.0677777777778]
0.3145490245337529
[52.86333333333334, 167.0588888888889]
0.31643532220840287
[53.32555555555555, 166.98777777777778]
0.31933807530823943
[53.32333333333333, 165.23666666666668]
0.3227088418631861
[52.99333333333333, 164.84777777777776]
0.32146829061154064
[53.254444444444445, 164.15777777777777]
0.3244101203449256
[53.76444444444444, 163.46555555555557]
0.3289038125599005
[52.833333333333336, 163.11777777777777]
0.32389684345326486
[53.471111111111114, 163.5988888888889]
0.32684275225993115
[53.30111111111111, 161.1288888888889]
0.33079798091245105
[53.81666666666667, 161.04333333333332]
0.3341750667522199
[54.486666666666665, 161.38666666666666]
0.33761566424322537
[54.08444444444444, 161.2588888888889]
0.3353889191293503
[53.96222222222222, 164.40222222222224]
0.32823292466984766
[53.39333333333333, 162.57]
0.32843288019519795
[54.06, 163.80666666666667]
0.33002319807903624
[53.57888888888889, 163.3022222222222]
0.32809650817842856
[53.721111111111114, 161.4188888888889]
0.3328056058426317
[53.888888888888886, 158.42666666666668]
0.34015036750266503
[54.02111111111111, 158.5088888888889]
0.34080808647254274
[54.275555555555556, 158.67666666666668]
0.34205127127842083
[54.163333333333334, 157.82777777777778]
0.34317997817593016
[54.29222222222222, 158.8177777777778]
0.34185229753176244
[54.14666666666667, 158.40777777777777]
0.34181823283087953
[54.64111111111111, 158.51555555555555]
0.34470504121572365
[53.846666666666664, 163.19666666666666]
0.3299495496231541
[54.38111111111111, 155.66222222222223]
0.3493533005938785
[53.96, 161.12222222222223]
0.33490104130749604
[54.10666666666667, 160.4988888888889]
0.3371155217412374
[54.50555555555555, 160.06]
0.3405320227137046
[54.50111111111111, 161.2588888888889]
0.33797275602378507
[53.99888888888889, 163.76222222222222]
0.3297395953482692
[54.59888888888889, 164.7588888888889]
0.331386605342487
[55.08444444444444, 165.36333333333334]
0.3331115993737695
[54.54555555555555, 164.45888888888888]
0.33166681305020507
[54.70111111111111, 165.7411111111111]
0.3300394859452828
[54.623333333333335, 165.61111111111111]
0.3298289164709829
[54.21888888888889, 166.55777777777777]
0.32552601032674683
[54.60888888888889, 166.96666666666667]
0.3270646170226925
[54.17666666666667, 166.4777777777778]
0.32542881932857237
[53.78111111111111, 165.92111111111112]
0.32413663789351027
[54.05888888888889, 166.3011111111111]
0.3250663121112306
[54.11888888888889, 166.68444444444444]
0.32467870093856654
[54.095555555555556, 166.86666666666667]
0.3241843121587428
[53.477777777777774, 167.32555555555555]
0.319603168805987
[53.355555555555554, 168.16555555555556]
0.31727992917032816
[54.29, 168.9911111111111]
0.32125950082844595
[54.602222222222224, 168.0011111111111]
0.3250110779690611
[53.57, 165.95777777777778]
0.3227929459969738
[53.53888888888889, 166.10333333333332]
0.3223227843444175
[54.65111111111111, 164.9922222222222]
0.3312344689648671
[54.51888888888889, 167.45222222222222]
0.3255787720543837
[54.14666666666667, 168.14444444444445]
0.32202471420075335
[53.89222222222222, 165.31]
0.3260070305621089
[54.166666666666664, 162.60444444444445]
0.33311922593341714
[54.47222222222222, 160.75333333333333]
0.3388559421612132
[54.27777777777778, 163.46333333333334]
0.3320486415573999
[54.093333333333334, 164.87666666666667]
0.3280836180579423
[54.05111111111111, 163.41222222222223]
0.33076541262383474
[54.224444444444444, 161.80666666666667]
0.33511872879842886
[54.696666666666665, 162.07777777777778]
0.3374717213957633
[54.30888888888889, 163.17333333333335]
0.332829438361388
[54.09888888888889, 162.71]
0.332486564371513
[53.92, 161.27444444444444]
0.3343369136117178
[53.40777777777778, 161.35333333333332]
0.3309989119806085
[54.26777777777778, 161.37555555555556]
0.3362825155950922
[53.63, 160.42444444444445]
0.3343006745993268
[54.345555555555556, 160.86222222222221]
0.33783914460960385
[53.96888888888889, 159.79222222222222]
0.3377441538664794
[53.71333333333333, 159.9411111111111]
0.3358319381439002
[53.903333333333336, 160.58]
0.3356789969693195
[53.91111111111111, 161.28]
0.3342702821869489
[53.98555555555556, 161.22]
0.3348564418530924
[53.37444444444444, 161.0288888888889]
0.33145881346342265
[53.48777777777778, 161.42333333333335]
0.33135096812384274
[53.672222222222224, 161.78666666666666]
0.3317468820394484
[53.44111111111111, 160.81222222222223]
0.3323199590965308
[53.31333333333333, 160.5222222222222]
0.3321243164670866
[52.70777777777778, 161.34333333333333]
0.32668085311516504
[53.291111111111114, 163.5377777777778]
0.32586422437221435
[53.61666666666667, 163.83555555555554]
0.327259040230041
[53.17111111111111, 165.44]
0.32139211261551687
[52.526666666666664, 166.97444444444446]
0.31457907730391205
[52.95111111111111, 166.83666666666667]
0.31738293607187334
[53.12111111111111, 166.51555555555555]
0.3190159077563658
[53.22555555555556, 166.45]
0.3197690330763326
[53.38777777777778, 166.0388888888889]
0.32153779235118946
[53.63777777777778, 167.45]
0.3203211572276965
[53.22888888888889, 167.29666666666665]
0.31817064828282426
[52.80444444444444, 168.67333333333335]
0.31305745490955555
[52.89555555555555, 170.69555555555556]
0.30988244177417884
[53.345555555555556, 171.18333333333334]
0.31162820887287834
[53.66888888888889, 169.76444444444445]
0.3161373929889782
[53.623333333333335, 168.89888888888888]
0.3174877803287964
[53.87777777777778, 169.17333333333335]
0.31847677595628415
[52.784444444444446, 169.96333333333334]
0.31056371635712277
[51.64111111111111, 167.90333333333334]
0.30756453779621873
[51.71333333333333, 166.28222222222223]
0.31099736726048083
[52.15777777777778, 167.29444444444445]
0.31177232424534257
[52.54555555555555, 167.17888888888888]
0.3143073620406617
[52.11666666666667, 166.98444444444445]
0.3121049199526237
[53.07222222222222, 163.52777777777777]
0.3245456089689146
[53.278888888888886, 158.6888888888889]
0.3357442935163142
[53.46111111111111, 157.05333333333334]
0.3404009961230438
[54.184444444444445, 158.98]
0.34082554059909703
[55.47666666666667, 161.13555555555556]
0.34428569458427
[55.123333333333335, 157.90555555555557]
0.34909052527882345
[53.89333333333333, 155.3111111111111]
0.3470024323937616
[53.784444444444446, 155.11666666666667]
0.34673543211203034
[53.18222222222222, 154.9322222222222]
0.3432612109954891
[52.714444444444446, 155.6288888888889]
0.33871888966630015
[50.81111111111111, 155.03222222222223]
0.32774548660135167
[51.87222222222222, 152.34666666666666]
0.3404880681486668
[52.65555555555556, 152.34777777777776]
0.34562732928314605
[52.47555555555556, 154.68666666666667]
0.33923774224597397
[51.54333333333334, 152.73666666666668]
0.33746535431352437
[51.91, 152.2788888888889]
0.3408876987398851
[52.51111111111111, 152.46444444444444]
0.344415455698232
[52.742222222222225, 150.24666666666667]
0.35103755306089246
[52.33, 147.99777777777777]
0.3535863901860388
[53.17, 144.59666666666666]
0.3677124876092118
[52.96888888888889, 147.18333333333334]
0.35988374287547653
[53.062222222222225, 148.57111111111112]
0.3571503357913158
[52.224444444444444, 151.17]
0.34546831014384105
[51.361111111111114, 151.88222222222223]
0.33816407450217273
[53.85333333333333, 142.4688888888889]
0.378000655113787
[54.33555555555556, 143.60222222222222]
0.3783754507048792
[52.80111111111111, 142.02333333333334]
0.3717777204058801
[51.955555555555556, 140.39777777777778]
0.3700596717263648
[52.675555555555555, 145.44222222222223]
0.36217512872618374
[54.29, 144.36444444444444]
0.3760621267163352
[54.81444444444445, 140.31666666666666]
0.39064813715009705
[53.404444444444444, 139.05777777777777]
0.38404500127844543
[52.51555555555556, 137.4388888888889]
0.3821011358583613
[52.94, 136.79222222222222]
0.3870103076035837
[54.153333333333336, 137.53222222222223]
0.39375015147965325
[53.69777777777778, 135.48222222222222]
0.3963455639936359
[52.72666666666667, 132.4411111111111]
0.3981140464944588
[53.318888888888885, 131.32777777777778]
0.4059985616988874
[54.29555555555555, 134.47555555555556]
0.40375780811051987
[54.02, 136.32666666666665]
0.3962540955547949
[54.32888888888889, 135.57222222222222]
0.4007376142277589
[53.78666666666667, 136.52666666666667]
0.3939645490502466
[54.44555555555556, 137.21666666666667]
0.3967852949512126
[55.28666666666667, 138.29555555555555]
0.3997718252374143
[54.63333333333333, 138.32888888888888]
0.39495244827143045
[53.534444444444446, 138.89]
0.38544491644066853
[54.12555555555556, 141.16333333333333]
0.38342503168118885
[54.71222222222222, 147.25555555555556]
0.3715460650418773
[53.69888888888889, 155.89444444444445]
0.34445671929011795
[54.14222222222222, 160.33777777777777]
0.33767601729681784
[55.065555555555555, 163.79777777777778]
0.33618011369032275
[54.45, 165.88333333333333]
0.3282427408821461
[53.803333333333335, 163.68]
0.32871049201694363
[53.845555555555556, 161.15222222222224]
0.33412853271923715
[54.41444444444444, 160.01888888888888]
0.3400501329704132
[53.77111111111111, 162.28222222222223]
0.3313432018294603
[51.91222222222222, 163.45555555555555]
0.3175922778872952
[51.882222222222225, 154.5311111111111]
0.3357396568831879
[53.63666666666666, 149.0011111111111]
0.3599749442584321
[55.07555555555555, 147.83444444444444]
0.37254887223696176
[54.05777777777778, 147.16666666666666]
0.3673235183087958
[50.73555555555556, 149.05666666666667]
0.34037763415852285
[53.40555555555556, 147.69222222222223]
0.36160032500018807
[53.33111111111111, 151.37]
0.3523228586319027
[51.653333333333336, 153.9477777777778]
0.3355250337416007
[51.38444444444445, 156.65555555555557]
0.32800907865806084
[53.68666666666667, 161.24666666666667]
0.3329474511101005
[53.38, 161.1611111111111]
0.33122134509979667
[53.17, 156.62777777777777]
0.33946724364203884
[53.34, 157.35111111111112]
0.3389871200994238
[53.507777777777775, 162.92777777777778]
0.32841408940566713
[52.05444444444444, 166.35555555555555]
0.3129107667646273
[51.852222222222224, 166.56333333333333]
0.31130634326615836
[52.40888888888889, 170.76444444444445]
0.30690750091093644
[53.044444444444444, 171.22]
0.30980285273008085
[53.885555555555555, 166.9788888888889]
0.3227087921959529
[55.49111111111111, 164.3311111111111]
0.3376786704350295
[54.16222222222222, 171.84222222222223]
0.31518576471957477
[52.29888888888889, 168.73555555555555]
0.3099458719100236
[52.28111111111111, 154.45888888888888]
0.3384791350449239
[55.47888888888889, 146.71333333333334]
0.37814483270474547
[56.57333333333333, 148.10333333333332]
0.3819855506290653
[53.64111111111111, 152.05333333333334]
0.3527782649362796
[48.696666666666665, 150.60777777777778]
0.32333434159369073
[48.76111111111111, 149.11888888888888]
0.3269948661396202
[52.52444444444444, 154.42888888888888]
0.34012058768509057
[53.44, 154.83777777777777]
0.34513541053719304
[51.94555555555556, 149.52555555555554]
0.3474025250235932
[53.03666666666667, 146.16555555555556]
0.362853385430524
[55.96222222222222, 142.4777777777778]
0.3927786009514154
[58.36888888888889, 142.34222222222223]
0.4100602616542292
[58.03333333333333, 148.23888888888888]
0.3914852153056253
[58.42777777777778, 154.53222222222223]
0.3780944642972699
[58.214444444444446, 157.34444444444443]
0.3699809335498906
[58.80777777777778, 160.15555555555557]
0.3671916192590537
[58.785555555555554, 165.20444444444445]
0.3558351941029297
[59.08, 164.51333333333332]
0.35911982818008675
[58.92777777777778, 159.22444444444446]
0.370092531855801
[60.78111111111111, 158.23888888888888]
0.3841098198925675
[60.73, 158.72555555555556]
0.38261009569277504
[60.19888888888889, 157.42]
0.38240940724742023
[60.34888888888889, 156.89333333333335]
0.3846491600804509
[59.343333333333334, 153.6811111111111]
0.3861459154237129
[59.04666666666667, 157.69]
0.37444775614602493
[58.86555555555555, 159.7277777777778]
0.3685367465479461
[57.477777777777774, 155.59444444444443]
0.369407648087978
[56.43, 153.7122222222222]
0.3671145936490267
[56.492222222222225, 153.63]
0.3677160855446347
[57.20333333333333, 151.5077777777778]
0.3775603746048974
[57.66777777777778, 154.24666666666667]
0.3738672544697526
[59.10111111111111, 155.24555555555557]
0.3806943838077311
[56.45444444444445, 148.1211111111111]
0.38113705751299615
[53.33, 144.86888888888888]
0.36812596830850886
[54.413333333333334, 151.0811111111111]
0.3601597375949637
[58.37222222222222, 157.54222222222222]
0.37051795638558976
[60.24111111111111, 158.6688888888889]
0.3796655509026484
[57.486666666666665, 160.26666666666668]
0.35869384359400996
[53.72888888888889, 158.9488888888889]
0.3380261998965426
[52.62444444444444, 156.2811111111111]
0.3367293978798888
[55.294444444444444, 148.55555555555554]
0.37221391174270757
[59.65, 146.85]
0.4061967994552264
[58.754444444444445, 153.9011111111111]
0.3817675130495051
[54.16, 148.96]
0.36358754027926954
[53.49111111111111, 149.24]
0.3584234193990291
[54.852222222222224, 147.81222222222223]
0.37109395554419644
[57.70333333333333, 154.44222222222223]
0.37362408092202765
[55.94111111111111, 160.35333333333332]
0.3488615418728087
[54.464444444444446, 157.17222222222222]
0.34652716411579654
[54.95333333333333, 152.9411111111111]
0.3593104099617137
[56.48777777777778, 157.67]
0.35826585766333346
[59.18666666666667, 169.78333333333333]
0.3486011583390596
[60.44111111111111, 171.32333333333332]
0.35278972183849905
[61.84, 176.33444444444444]
0.35069722307987977
[64.06111111111112, 175.27333333333334]
0.36549262738833316
[65.25333333333333, 172.91666666666666]
0.3773686746987952
[65.31222222222222, 172.76333333333332]
0.3780444667399847
[64.67111111111112, 173.18333333333334]
0.3734257209764861
[62.32, 168.58555555555554]
0.36966393588484586
[62.153333333333336, 160.24333333333334]
0.38786845006552534
[61.70333333333333, 158.44666666666666]
0.38942651575714227
[59.67777777777778, 146.37666666666667]
0.4077000736304359
[58.49, 143.7577777777778]
0.4068649425731554
[57.471111111111114, 142.4488888888889]
0.4034507503666033
[57.63333333333333, 140.61666666666667]
0.4098613251155624
[57.55555555555556, 139.57444444444445]
0.4123645684899337
[57.593333333333334, 141.36111111111111]
0.4074199253291413
[58.153333333333336, 144.53333333333333]
0.40235239852398524
[59.394444444444446, 150.57777777777778]
0.3944436245572609
[59.446666666666665, 158.72]
0.3745379704301075
[59.827777777777776, 160.82333333333332]
0.372009313187003
[60.617777777777775, 158.95]
0.3813638111215966
[61.565555555555555, 161.5688888888889]
0.3810483316370038
[62.19, 166.79555555555555]
0.3728516613818647
[64.3, 171.7188888888889]
0.3744491966845037
[64.67, 172.0377777777778]
0.3759058088016844
[64.99, 164.77777777777777]
0.394409979770735
[64.86111111111111, 157.43]
0.41199968945633686
[64.45333333333333, 158.5311111111111]
0.40656583355527837
[63.355555555555554, 162.65666666666667]
0.3895048192853386
[63.02111111111111, 163.92555555555555]
0.38444958077175956
[61.40888888888889, 167.11222222222221]
0.36747096096435533
[62.51222222222222, 168.54888888888888]
0.3708848075731407
[60.315555555555555, 160.0388888888889]
0.3768806192939216
[60.21, 161.89666666666668]
0.37190388931211266
[60.33444444444444, 158.52333333333334]
0.3806029256120725
[59.75, 156.81444444444443]
0.3810235735086762
[60.35666666666667, 160.5811111111111]
0.37586404932086936
[57.61666666666667, 161.42]
0.35693635650270517
[58.29333333333334, 158.61555555555555]
0.3675133446348264
[58.89666666666667, 155.2288888888889]
0.3794182068057206
[58.047777777777775, 154.01111111111112]
0.3769064281076401
[57.48, 155.32333333333332]
0.370066742494152
[58.044444444444444, 153.52]
0.3780904406230096
[57.66888888888889, 154.17777777777778]
0.3740415105217642
[58.51777777777778, 156.1211111111111]
0.3748229650769702
[56.952222222222225, 155.48777777777778]
0.3662810224454941
[56.214444444444446, 156.20666666666668]
0.3598722490148379
[56.45, 159.98666666666668]
0.35284190349195765
[56.57666666666667, 162.51888888888888]
0.34812363691058135
[56.09888888888889, 160.18]
0.3502240534953732
[57.12777777777778, 161.54111111111112]
0.35364234766519703
[57.22888888888889, 167.6811111111111]
0.34129597847766596
[56.17777777777778, 160.36888888888888]
0.3503034670066236
[57.79222222222222, 152.37444444444444]
0.37927765664991947
[59.94555555555556, 144.73111111111112]
0.41418569300925856
[59.876666666666665, 146.92222222222222]
0.407539892611359
[56.97555555555556, 145.57555555555555]
0.39138133691553834
[54.83, 147.33444444444444]
0.3721465147321664
[56.562222222222225, 158.29222222222222]
0.3573278675866716
[56.236666666666665, 153.45777777777778]
0.36646344995366076
[56.32333333333333, 152.91666666666666]
0.36832697547683924
[54.416666666666664, 152.95333333333335]
0.355773002658763
[55.653333333333336, 150.27555555555554]
0.3703418904530936
[56.278888888888886, 151.02555555555554]
0.37264480625059776
[57.65777777777778, 151.9411111111111]
0.379474504011057
[58.27333333333333, 151.4777777777778]
0.384698892393457
[58.434444444444445, 154.03555555555556]
0.3793568584453806
[57.55111111111111, 153.77555555555554]
0.3742539632075608
[57.153333333333336, 153.26777777777778]
0.37289855807917877
[57.56666666666667, 152.89666666666668]
0.3765070090911073
[58.361111111111114, 153.64222222222222]
0.3798507354749129
[58.12222222222222, 153.73111111111112]
0.3780771621445814
[57.406666666666666, 152.1811111111111]
0.3772259661368399
[57.724444444444444, 153.31555555555556]
0.3765074211502783
[58.91777777777778, 157.42222222222222]
0.3742659514398645
[60.34, 160.13555555555556]
0.3768057617851543
[60.29222222222222, 161.27777777777777]
0.3738408542886669
[59.93888888888889, 162.04]
0.36990180750980556
[60.39666666666667, 162.61777777777777]
0.37140260734100417
[60.797777777777775, 162.26222222222222]
0.37468843298912596
[61.10111111111111, 156.11444444444444]
0.39138666078304374
[59.92333333333333, 153.52777777777777]
0.39030939026596706
[57.66777777777778, 151.0377777777778]
0.38181029028793384
[54.31666666666667, 148.29555555555555]
0.3662730583069846
[54.818888888888885, 144.6888888888889]
0.37887421287052675
[56.26888888888889, 151.2122222222222]
0.3721186558993615
[56.73888888888889, 155.00666666666666]
0.36604160394535
[56.69555555555556, 151.70666666666668]
0.37371828675221186
[55.22, 149.15333333333334]
0.3702230366960175
[55.672222222222224, 148.79]
0.37416642396815797
[60.05777777777778, 151.22555555555556]
0.3971404010198159
[58.56666666666667, 149.83666666666667]
0.3908700585081533
[58.43, 151.3022222222222]
0.3861807126281468
[60.55222222222222, 155.55444444444444]
0.38926706619332996
[61.132222222222225, 149.83555555555554]
0.4079954320291876
[60.187777777777775, 150.75222222222223]
0.39924968859865706
[61.02111111111111, 153.3788888888889]
0.397845567621214
[62.45777777777778, 154.48777777777778]
0.40428944396895833
[62.83444444444444, 154.13888888888889]
0.4076482249053884
[62.46222222222222, 154.69333333333333]
0.4037809573062116
[62.74666666666667, 155.87333333333333]
0.4025490783114495
[62.574444444444445, 157.4688888888889]
0.3973765540988696
[62.35444444444445, 159.95888888888888]
0.3898154386891077
[62.48555555555556, 160.86555555555555]
0.3884334053971916
[62.422222222222224, 162.61888888888888]
0.38385591396380087
[63.791111111111114, 164.13555555555556]
0.38864894870093825
[63.4, 165.54]
0.3829890056783859
[63.044444444444444, 163.73888888888888]
0.3850303667763716
[62.34777777777778, 155.73888888888888]
0.4003353190882175
[61.6, 156.36444444444444]
0.3939514524472742
[61.187777777777775, 156.9411111111111]
0.389877307128647
[61.04, 154.0211111111111]
0.3963093082477871
[61.70111111111111, 157.25333333333333]
0.3923675880391159
[61.66888888888889, 166.26666666666668]
0.3709035017375033
[61.99888888888889, 174.37222222222223]
0.35555484754834804
[63.16555555555556, 179.57555555555555]
0.3517491863530052
[65.55222222222223, 179.33666666666667]
0.3655260435060067
[64.52111111111111, 177.95444444444445]
0.36257094512328375
[58.73888888888889, 174.51333333333332]
0.3365868255848009
[56.034444444444446, 151.89222222222222]
0.3689092412017293
[63.14111111111111, 153.64333333333335]
0.4109590031747409
[69.78888888888889, 143.6]
0.4859950479727639
[66.06222222222222, 151.51777777777778]
0.43600310927943914
[55.21888888888889, 142.76111111111112]
0.38679223255632955
[54.71222222222222, 135.4622222222222]
0.4038928442534204
[63.37777777777778, 135.07444444444445]
0.46920628130989495
[66.95555555555555, 145.66333333333333]
0.45965964133427917
[62.84444444444444, 148.39444444444445]
0.4234959380030699
[60.41555555555556, 140.22222222222223]
0.43085578446909667
[65.1, 146.22666666666666]
0.44519923406583384
[64.99111111111111, 150.57555555555555]
0.43161794005224396
[61.46111111111111, 150.74]
0.4077292763109401
[59.82111111111111, 151.25]
0.39551147842056933
[61.77111111111111, 153.46555555555557]
0.4025079822471926
[63.01444444444444, 154.20666666666668]
0.4086363177842145
[61.13, 156.27777777777777]
0.39116246000710986
[60.056666666666665, 156.23111111111112]
0.3844091374601729
[60.88777777777778, 224.89555555555555]
0.2707380216001502
[63.37888888888889, 222.15333333333334]
0.2852934409666997
[62.693333333333335, 222.2577777777778]
0.2820748680211166
[62.55222222222222, 224.11333333333334]
0.27910977580787494
[62.91444444444444, 227.32888888888888]
0.2767551662789106
[64.0111111111111, 230.4611111111111]
0.2777523322806933
[63.80777777777778, 233.2511111111111]
0.2735583014967179
[63.528888888888886, 234.63222222222223]
0.2707594391222196
[64.18666666666667, 233.02444444444444]
0.27545035809309465
[64.8711111111111, 230.02777777777777]
0.28201424948677695
[64.72777777777777, 228.98111111111112]
0.28267736785664027
[63.577777777777776, 228.33333333333334]
0.2784428223844282
[62.446666666666665, 229.29555555555555]
0.27234137406355696
[61.66444444444444, 234.33444444444444]
0.26314716383516434
[61.742222222222225, 238.87]
0.25847625161059246
[61.73, 218.77555555555554]
0.2821613221058619
[64.15222222222222, 221.2788888888889]
0.28991569211301976
[62.30444444444444, 228.57666666666665]
0.2725756979180338
[62.11888888888889, 224.4]
0.2768221429986136
[66.87, 228.7511111111111]
0.2923264489304242
[65.50111111111111, 234.49777777777777]
0.2793250824456996
[63.86222222222222, 236.84]
0.2696428906528552
[63.132222222222225, 235.13444444444445]
0.2684941475562444
[63.53111111111111, 230.82777777777778]
0.2752316541914366
[63.11222222222222, 221.93777777777777]
0.284368992310157
[62.85, 223.40777777777777]
0.28132413573584925
[61.19777777777778, 225.2577777777778]
0.27167886668113567
[58.42, 223.54222222222222]
0.26133765433326045
[56.21111111111111, 226.07888888888888]
0.24863494060578656
[55.74111111111111, 229.37333333333333]
0.24301478424305836
[58.05555555555556, 238.55666666666667]
0.24336169836190796
[58.656666666666666, 244.35444444444445]
0.24004747202379056
[57.925555555555555, 241.72]
0.2396390681596705
[56.9, 235.3411111111111]
0.24177671181783417
[57.696666666666665, 223.32444444444445]
0.25835356631109696
[57.6, 229.42888888888888]
0.25105818312137385
[57.772222222222226, 234.52777777777777]
0.24633424138339455
[56.74333333333333, 236.65777777777777]
0.23976956881009617
[56.62111111111111, 232.9311111111111]
0.24308092998406777
[59.62555555555556, 229.02777777777777]
0.2603420254699818
[59.01555555555556, 231.1677777777778]
0.2552931733084676
[57.79555555555555, 233.5822222222222]
0.24743131136311744
[56.215555555555554, 233.43444444444444]
0.2408194544268912
[57.09111111111111, 231.27666666666667]
0.24685201466257345
[57.32222222222222, 230.88777777777779]
0.24826875971491683
[58.01444444444444, 231.9911111111111]
0.2500718418330204
[57.41555555555556, 232.5588888888889]
0.2468860933670325
[57.71, 231.89777777777778]
0.2488596508039941
[58.733333333333334, 231.71777777777777]
0.2534692585808407
[58.516666666666666, 232.62222222222223]
0.2515523500191058
[59.12777777777778, 233.16333333333333]
0.2535895199836071
[59.714444444444446, 233.08555555555554]
0.2561910981661479
[59.77444444444444, 233.47333333333333]
0.25602257693003244
[59.35111111111111, 233.43444444444444]
0.25425172901266596
[56.91555555555556, 233.32]
0.24393774882374233
[57.62222222222222, 233.28333333333333]
0.24700531066180847
[56.486666666666665, 233.51222222222222]
0.241900257421691
[55.83777777777778, 233.7422222222222]
0.23888614237906908
[56.888888888888886, 234.2111111111111]
0.24289577304426205
[56.82, 233.7888888888889]
0.2430397794781617
[55.91777777777778, 233.72333333333333]
0.23924773355011386
[55.49111111111111, 233.23]
0.23792441414531199
[55.00888888888889, 233.44]
0.23564465768029855
[55.18555555555555, 233.89777777777778]
0.23593877667357058
[54.44, 234.98]
0.23167929185462593
[55.19777777777778, 236.25555555555556]
0.23363589333584162
[55.40222222222222, 235.78]
0.23497422267462134
[55.43222222222222, 235.2788888888889]
0.235602193141945
[56.596666666666664, 235.17222222222222]
0.24066050884694432
[58.42, 235.3388888888889]
0.24823776586954982
[61.39666666666667, 235.89]
0.26027668263456133
[59.92666666666667, 236.28]
0.2536256418937983
[59.57333333333333, 235.50666666666666]
0.25295816112778124
[60.57666666666667, 234.87777777777777]
0.257907185770377
[61.03111111111111, 234.15333333333334]
0.26064592052691016
[55.75666666666667, 233.10444444444445]
0.23919177860186658
[54.50222222222222, 233.21]
0.23370448189281
[51.12777777777778, 232.42666666666668]
0.2199738029677222
[48.03888888888889, 231.95777777777778]
0.2071018671980533
[46.98111111111111, 233.39777777777778]
0.20129202410762742
[46.54222222222222, 231.22555555555556]
0.20128494063036093
[48.08, 228.8088888888889]
0.21013169651528688
[54.07888888888889, 228.27]
0.23690756073460764
[52.525555555555556, 229.62777777777777]
0.22874216727554256
[40.46666666666667, 225.2288888888889]
0.1796690773830079
[37.26888888888889, 224.70333333333335]
0.16585819327211682
[36.95, 224.98888888888888]
0.16423033236209197
[44.126666666666665, 225.62222222222223]
0.19557766177484487
[42.123333333333335, 225.09333333333333]
0.1871371875370217
[32.53888888888889, 223.11555555555555]
0.14583872831218503
[33.28777777777778, 223.74777777777777]
0.14877366876393558
[35.068888888888885, 223.67888888888888]
0.15678229207544545
[31.876666666666665, 223.13]
0.14286141113551143
[33.00666666666667, 222.19222222222223]
0.14855005425732473
[37.952222222222225, 225.47444444444446]
0.16832161319095043
[40.97666666666667, 226.7111111111111]
0.18074397177024112
[38.94, 224.28444444444443]
0.1736188173747622
[36.11222222222222, 222.77333333333334]
0.16210298459819647
[36.455555555555556, 222.9788888888889]
0.16349330529546893
[37.184444444444445, 223.89888888888888]
0.16607694941665138
[36.202222222222225, 223.5377777777778]
0.16195124860823923
[33.864444444444445, 221.25444444444443]
0.15305656132456852
[33.12, 220.55333333333334]
0.1501677598766738
[33.96333333333333, 222.8788888888889]
0.15238470320203795
[33.88666666666666, 223.49]
0.15162497949199813
[32.196666666666665, 221.71]
0.14521973148106385
[31.612222222222222, 220.9911111111111]
0.14304748305613096
[32.09222222222222, 221.79888888888888]
0.14469063566093407
[32.48444444444444, 223.58444444444444]
0.1452893761243577
[31.252222222222223, 223.65555555555557]
0.13973371752198321
[29.333333333333332, 221.08777777777777]
0.1326773177068937
[30.065555555555555, 221.07444444444445]
0.13599742670895174
[30.587777777777777, 222.94444444444446]
0.13719910291552453
[31.083333333333332, 222.70777777777778]
0.13957003946377167
[30.08111111111111, 221.88666666666666]
0.13556971026249637
[30.486666666666668, 221.7288888888889]
0.13749523943153802
[31.77, 223.52777777777777]
0.14212998633030943
[30.86, 223.38111111111112]
0.13814955009624805
[30.013333333333332, 221.94]
0.1352317443152804
[30.247777777777777, 222.30333333333334]
0.1360653361523044
[30.50777777777778, 223.29666666666665]
0.13662442092482846
[30.843333333333334, 223.95888888888888]
0.13771872813958913
[30.107777777777777, 223.47]
0.13472849947544538
[31.022222222222222, 223.01777777777778]
0.13910201478706233
[31.29222222222222, 222.90222222222224]
0.14038542061292444
[31.218888888888888, 222.67]
0.140202491978663
[30.522222222222222, 222.54111111111112]
0.13715318517926775
[30.557777777777776, 222.1511111111111]
0.13755401728553138
[31.184444444444445, 222.8088888888889]
0.13996050426873055
[31.924444444444443, 223.58444444444444]
0.142784729607506
[31.145555555555557, 223.33]
0.13945979293223282
[30.34777777777778, 222.76444444444445]
0.13623259247436256
[30.177777777777777, 222.5677777777778]
0.13558915885797584
[30.676666666666666, 223.1511111111111]
0.13747037383735983
[30.90222222222222, 222.87555555555556]
0.13865236205555664
[30.925555555555555, 222.69222222222223]
0.1388712872275138
[31.227777777777778, 222.63666666666666]
0.14026340874269488
[31.747777777777777, 221.88888888888889]
0.1430796194291437
[31.82777777777778, 222.0588888888889]
0.14333034780563714
[33.12, 223.61555555555555]
0.14811134188637243
[32.75555555555555, 223.3388888888889]
0.14666301833287726
[32.33777777777778, 222.1822222222222]
0.14554619831569685
[32.56777777777778, 222.4611111111111]
0.14639762255575256
[32.70444444444445, 222.79222222222222]
0.14679347473729884
[33.04, 223.52444444444444]
0.14781381106714653
[33.184444444444445, 223.78666666666666]
0.14828606609469336
[33.577777777777776, 222.8488888888889]
0.15067509622863523
[33.208888888888886, 222.60555555555555]
0.1491826599116524
[33.83222222222222, 222.95444444444445]
0.15174500022426105
[35.507777777777775, 223.31333333333333]
0.15900428894129823
[36.967777777777776, 222.23888888888888]
0.1663425243106767
[37.62, 222.88777777777779]
0.16878449045109895
[36.69222222222222, 223.11]
0.1644579903286371
[34.93888888888889, 223.16666666666666]
0.1565596216081653
[35.50666666666667, 223.32444444444445]
0.15899140264289127
[36.17888888888889, 223.22333333333333]
0.16207485278818923
[36.47222222222222, 223.5077777777778]
0.16318099792699234
[36.68666666666667, 222.76777777777778]
0.16468569661481064
[35.99777777777778, 222.77777777777777]
0.1615860349127182
[35.56111111111111, 223.04555555555555]
0.15943429593356614
[35.07333333333333, 223.48111111111112]
0.1569409296336255
[35.44777777777778, 223.39777777777778]
0.1586756060440271
[34.547777777777775, 223.32333333333332]
0.15469846908568044
[33.88777777777778, 224.08]
0.15123071125391724
[34.20333333333333, 224.40333333333334]
0.1524190074419572
[34.28111111111111, 223.92555555555555]
0.1530915532443818
[34.333333333333336, 223.86222222222221]
0.1533681431038933
[34.10888888888889, 223.85222222222222]
0.15237234882139508
[34.638888888888886, 224.53555555555556]
0.15426905909482289
[35.48777777777778, 224.80555555555554]
0.15785987890769804
[35.46666666666667, 224.2577777777778]
0.15815133378255183
[34.60333333333333, 224.04222222222222]
0.15445005405727094
[34.37444444444444, 223.52444444444444]
0.15378382677509791
[35.83777777777778, 222.82222222222222]
0.16083574349257007
[38.233333333333334, 225.72]
0.1693838974540729
[39.0, 229.57]
0.1698828244108551
[37.56444444444445, 228.39666666666668]
0.16447019561484164
[37.77111111111111, 226.2422222222222]
0.16694987672995512
[39.39555555555555, 225.96555555555557]
0.17434318898160484
[41.92333333333333, 228.04444444444445]
0.18383843305398556
[42.95444444444445, 228.14222222222222]
0.18827924101924728
[41.80444444444444, 227.72666666666666]
0.18357289928471754
[47.776666666666664, 229.90333333333334]
0.20781197894767364
[48.72888888888889, 231.88222222222223]
0.2101449969812261
[55.343333333333334, 231.10555555555555]
0.2394721026947763
[54.278888888888886, 231.37555555555556]
0.23459214936755057
[56.065555555555555, 232.73444444444445]
0.24089926048285837
[120.84444444444445, 234.16444444444446]
0.5160665818892706
[131.88888888888889, 235.95666666666668]
0.5589538568757917
[140.02, 239.2511111111111]
0.5852428410874675
[167.15444444444444, 240.00666666666666]
0.6964575058100237
[120.1511111111111, 240.63333333333333]
0.4993120007387912
[149.15555555555557, 239.62]
0.6224670543174842
[170.95333333333335, 240.8311111111111]
0.709847380367985
[164.17, 242.73222222222222]
0.6763420138332593
[120.25777777777778, 244.57222222222222]
0.4917066079095018
[113.52777777777777, 243.61666666666667]
0.46600989715171826
[119.80666666666667, 245.01777777777778]
0.48897132180884834
[120.71777777777778, 244.4011111111111]
0.49393301539818424
[115.36, 244.88]
0.4710878797778504
[114.91777777777777, 245.51444444444445]
0.4680693147721564
[118.54444444444445, 246.84222222222223]
0.48024379045544163
[127.19888888888889, 248.57888888888888]
0.5117043102793212
[170.6, 248.85333333333332]
0.6855443634804972
[122.57222222222222, 247.80777777777777]
0.4946262111762253
[86.61333333333333, 249.31444444444443]
0.3474059977805805
[80.82222222222222, 249.68777777777777]
0.32369314566191554
[74.75222222222222, 248.63222222222223]
0.3006537992304564
[71.14555555555556, 249.30666666666667]
0.2853736585018006
[67.24333333333334, 248.76222222222222]
0.2703116764782077
[64.71777777777778, 249.4922222222222]
0.2593979772248523
[62.46666666666667, 249.74444444444444]
0.2501223472883392
[57.785555555555554, 250.03333333333333]
0.2311114073679065
[56.553333333333335, 249.53666666666666]
0.22663336049478366
[54.72888888888889, 249.7411111111111]
0.21914248977830375
[50.26555555555556, 250.44]
0.20070897442723032
[48.61888888888889, 250.39555555555555]
0.19416833809616785
[47.16555555555556, 249.07333333333332]
0.18936413193793886
[44.894444444444446, 246.32111111111112]
0.18225983246800698
[42.46, 246.06666666666666]
0.17255486318070984
[40.50222222222222, 245.9611111111111]
0.16466921148329683
[38.10111111111111, 245.35555555555555]
0.15528937596232226
[37.11888888888889, 244.66222222222223]
0.15171483587349452
[36.93, 243.61666666666667]
0.15159061366901552
[36.06333333333333, 243.81]
0.14791572672709624
[37.83888888888889, 244.33]
0.154867960908971
[57.32333333333333, 243.26222222222222]
0.23564420652610807
[54.21888888888889, 242.82222222222222]
0.2232863549007047
[60.217777777777776, 241.6811111111111]
0.2491621190457582
[71.17666666666666, 240.81222222222223]
0.2955691617719661
[58.492222222222225, 240.64333333333335]
0.24306604056718334
[62.903333333333336, 239.89777777777778]
0.262208903792356
[73.65444444444445, 239.59444444444443]
0.307412989542514
[72.04333333333334, 238.9622222222222]
0.3014841955492733
[66.46666666666667, 238.5888888888889]
0.2785824058119499
[64.99111111111111, 237.9988888888889]
0.27307317027623845
[61.26777777777778, 238.3177777777778]
0.2570843784675923
[53.132222222222225, 237.80555555555554]
0.2234271697231632
[55.25666666666667, 237.73333333333332]
0.2324312955692653
[48.983333333333334, 237.2488888888889]
0.2064639103800978
[38.568888888888885, 237.01333333333332]
0.16272877287728774
[36.6, 235.7788888888889]
0.15523018270413427
[39.53888888888889, 235.90777777777777]
0.1676031594267063
[41.91444444444444, 235.75444444444443]
0.17778856531513487
[43.72, 235.03]
0.1860188061098583
[43.98, 234.83777777777777]
0.18727821569499511
[38.693333333333335, 236.95111111111112]
0.16329669505195635
[42.63666666666666, 236.91444444444446]
0.17996651393142388
[70.25777777777778, 237.9311111111111]
0.29528621729912485
[82.45444444444445, 238.47333333333333]
0.3457596004211978
[86.22666666666667, 240.27333333333334]
0.358869065786188
[88.94333333333333, 242.74333333333334]
0.36640896420087055
[88.99333333333334, 242.61222222222221]
0.3668130670342705
[92.53, 241.01888888888888]
0.38391181880627157
[83.08666666666667, 242.7188888888889]
0.34231644289003743
[147.56555555555556, 243.9688888888889]
0.6048539886688649
[105.39222222222222, 244.36]
0.4312989941979956
[63.31777777777778, 243.77]
0.25974392984279354
[48.60888888888889, 242.5088888888889]
0.20044167911370947
[43.49666666666667, 244.79444444444445]
0.1776864943376529
[45.69222222222222, 249.27444444444444]
0.18330086874350893
[48.79666666666667, 249.3311111111111]
0.1957103004483106
[69.13222222222223, 247.42444444444445]
0.27940740607682707
[176.1811111111111, 248.09222222222223]
0.71014362938513
[125.64333333333333, 248.45444444444445]
0.5056996811398468
[110.38222222222223, 249.46]
0.4424846557452987
[191.3388888888889, 247.94222222222223]
0.7717075662788823
[249.29555555555555, 246.22666666666666]
1.0124636739409036
[253.65222222222224, 248.07888888888888]
1.0224659718458735
[253.40222222222224, 243.80777777777777]
1.0393524953629225
[253.38111111111112, 242.40666666666667]
1.0452728656160906
[242.47444444444446, 244.48333333333332]
0.9917831254118664
[239.98888888888888, 243.99333333333334]
0.9835878940226053
[234.17777777777778, 243.67333333333335]
0.9610316179219902
[232.28222222222223, 242.63666666666666]
0.9573253103634608
[227.77, 242.13333333333333]
0.9406800660792952
[214.54888888888888, 238.24555555555557]
0.900536794437112
[196.71333333333334, 240.45555555555555]
0.8180860403863038
[166.18555555555557, 238.83555555555554]
0.6958158100413117
[149.0288888888889, 235.83333333333334]
0.631924617196702
[146.66444444444446, 234.5077777777778]
0.6254139876905291
[147.0911111111111, 233.60222222222222]
0.6296648623966666
[147.22555555555556, 234.64444444444445]
0.6274410455535562
[146.15333333333334, 234.12222222222223]
0.6242608324237103
[146.37777777777777, 233.40555555555557]
0.6271392188132244
[145.99555555555557, 233.64222222222222]
0.6248680318435595
[145.49, 234.56555555555556]
0.6202530446357095
[146.5588888888889, 235.78333333333333]
0.6215829033246154
[144.5822222222222, 236.21333333333334]
0.612083239256416
[142.68, 236.30666666666667]
0.6037916831236246
[140.84222222222223, 234.67]
0.6001713990805055
[136.63666666666666, 230.66555555555556]
0.5923583446933751
[136.98777777777778, 235.63777777777779]
0.5813489630977866
[138.51222222222222, 237.36444444444444]
0.58354241953302
[139.0611111111111, 234.73222222222222]
0.5924244647565311
[141.0988888888889, 236.03555555555556]
0.5977865858251111
[142.23444444444445, 236.39111111111112]
0.6016911709408137
[143.14333333333335, 234.9188888888889]
0.6093308801619473
[143.99333333333334, 235.19222222222223]
0.6122367992138819
[144.50444444444443, 234.54555555555555]
0.6161039551662553
[145.49333333333334, 235.08333333333334]
0.6189010989010989
[144.62, 235.53333333333333]
0.6140107557316729
[144.9088888888889, 235.19]
0.6161354177001102
[144.01555555555555, 234.72666666666666]
0.6135457790148352
[145.80333333333334, 235.70666666666668]
0.6185795904514085
[147.18444444444444, 234.34222222222223]
0.6280748003868984
[147.48888888888888, 235.12777777777777]
0.6272712236845214
[147.82222222222222, 234.84222222222223]
0.6294533445623066
[149.26333333333332, 235.12333333333333]
0.6348299474034903
[148.32, 234.98]
0.6312026555451528
[146.95777777777778, 235.2888888888889]
0.6245844352096713
[148.06222222222223, 235.12444444444444]
0.6297185414815796
[147.93555555555557, 234.33]
0.6313129157835342
[148.2488888888889, 235.07666666666665]
0.6306405947941335
[148.3311111111111, 235.33]
0.6303110997795058
[148.68, 234.99333333333334]
0.6326987999659565
[149.17666666666668, 234.66444444444446]
0.6357020426329795
[148.8022222222222, 235.02333333333334]
0.6331380808524921
[148.4322222222222, 235.01222222222222]
0.6315936287001621
[149.10666666666665, 234.96777777777777]
0.63458346534513
[148.88666666666666, 234.84]
0.6339919377732356
[148.36777777777777, 234.95666666666668]
0.6314686868973475
[148.7188888888889, 235.11222222222221]
0.6325442696395576
[148.7588888888889, 235.02555555555554]
0.6329477172695168
[148.5, 234.96444444444444]
0.6320105169576484
[148.5211111111111, 234.94]
0.6321661322512604
[148.35666666666665, 234.94555555555556]
0.6314512582111221
[148.26777777777778, 234.9322222222222]
0.6311087358528938
[148.24777777777777, 235.04333333333332]
0.6307253036083181
[148.34444444444443, 234.89666666666668]
0.631530649410852
[148.61777777777777, 235.04111111111112]
0.6323054595649933
[148.4922222222222, 234.83333333333334]
0.6323302578660989
[148.44333333333333, 234.86555555555555]
0.6320353488284077
[148.1888888888889, 234.95777777777778]
0.6307043345849372
[148.58444444444444, 234.92888888888888]
0.6324656160729488
[148.42888888888888, 234.98888888888888]
0.6316421580216558
[148.4, 234.9611111111111]
0.6315938807840541
[148.37666666666667, 235.12555555555556]
0.6310529126282411
[148.2422222222222, 234.92888888888888]
0.6310089104977392
[148.1211111111111, 234.90333333333334]
0.6305619805782993
[148.23555555555555, 234.9688888888889]
0.6308731179541499
[148.26222222222222, 235.0511111111111]
0.6307658854339009
[148.12555555555556, 234.94555555555556]
0.6304675787771162
[148.3011111111111, 234.9322222222222]
0.6312506207464091
[148.20777777777778, 234.90777777777777]
0.6309189894852354
[148.43666666666667, 235.10777777777778]
0.6313558320770143
[148.33555555555554, 234.95222222222222]
0.6313434882742117
[148.43666666666667, 234.8388888888889]
0.6320787300986491
[148.3311111111111, 234.67]
0.6320838245668859
[148.11777777777777, 234.99444444444444]
0.6303033168632828
[148.0911111111111, 234.92777777777778]
0.6303686712228345
[148.02333333333334, 234.81444444444443]
0.6303842750540617
[147.63111111111112, 234.9388888888889]
0.6283809028352527
[148.06222222222223, 234.86222222222221]
0.6304216183483461
[147.87666666666667, 234.90444444444444]
0.6295183857265839
[147.91222222222223, 234.9]
0.6296816612269996
[147.57, 234.96777777777777]
0.6280435615285311
[148.0677777777778, 234.90666666666667]
0.6303259923563024
[148.66, 235.02333333333334]
0.6325329399917738
[148.1988888888889, 234.83777777777777]
0.63106920143456
[148.67333333333335, 234.97555555555556]
0.6327182969386888
[148.44666666666666, 235.00444444444443]
0.6316759966714578
[148.46444444444444, 235.14]
0.6313874476671109
[148.7411111111111, 235.0077777777778]
0.6329199506399315
[148.79, 234.95777777777778]
0.6332627138682126
[148.61333333333334, 235.0077777777778]
0.6323762334107146
[148.57777777777778, 234.9488888888889]
0.632383402536722
[148.17111111111112, 234.87333333333333]
0.6308554019660716
[148.00333333333333, 234.9111111111111]
0.6300397313404598
[147.90222222222224, 234.97555555555556]
0.6294366317063714
[147.40555555555557, 234.8411111111111]
0.6276820734586506
[147.24333333333334, 234.80333333333334]
0.6270921764313397
[147.5, 234.90666666666667]
0.6279089567487797
[147.17222222222222, 234.86333333333334]
0.6266291980679071
[146.9688888888889, 234.8022222222222]
0.6259263115056644
[146.18666666666667, 234.84]
0.6224947481973542
[146.38222222222223, 234.91]
0.6231417233077443
[146.15666666666667, 234.76]
0.6225790878627818
[146.0522222222222, 234.73888888888888]
0.6221901403450643
[145.7188888888889, 234.82111111111112]
0.620552761203564
[145.88333333333333, 234.7888888888889]
0.6213383181108324
[146.2211111111111, 234.69666666666666]
0.6230216780998641
[145.6811111111111, 234.84222222222223]
0.6203361121887981
[145.91222222222223, 234.83777777777777]
0.6213319833076261
[145.96666666666667, 234.87]
0.6214785484168547
[145.7422222222222, 234.94333333333333]
0.6203292519709244
[146.4111111111111, 234.79111111111112]
0.6235802983266449
[146.51222222222222, 234.88444444444445]
0.6237629851085167
[146.67333333333335, 234.80333333333334]
0.6246646129384875
[145.81333333333333, 234.8188888888889]
0.6209608350643758
[145.48111111111112, 234.82444444444445]
0.6195313756849088
[145.8711111111111, 234.7888888888889]
0.621286261890114
[145.73555555555555, 234.88]
0.6204681350287617
[146.10555555555555, 234.83777777777777]
0.6221552466478042
[145.70666666666668, 234.9611111111111]
0.6201309909441279
[145.84777777777776, 234.89]
0.6209194847706492
[145.4011111111111, 234.85111111111112]
0.6191203883311411
[145.88555555555556, 234.85777777777778]
0.6211655280737278
[146.62777777777777, 235.0611111111111]
0.6237857767483633
[145.93777777777777, 234.83444444444444]
0.6214496264507856
[146.09444444444443, 234.8]
0.622208025742949
[146.66, 234.82777777777778]
0.6245428091509143
[146.26, 234.8011111111111]
0.62291016983641
[145.89555555555555, 234.7877777777778]
0.621393315003147
[146.57222222222222, 234.85888888888888]
0.6240863307991087
[146.76666666666668, 234.87777777777777]
0.624863995458631
[146.49, 234.79222222222222]
0.6239133418199543
[146.44222222222223, 234.93444444444444]
0.6233322770891171
[146.92444444444445, 234.95]
0.6253434536899104
[146.6511111111111, 234.9477777777778]
0.624185989321504
[146.43777777777777, 234.79222222222222]
0.6236909229436901
[146.33777777777777, 234.94666666666666]
0.6228553052229348
[146.09555555555556, 234.90777777777777]
0.6219272811552525
[146.1988888888889, 234.84666666666666]
0.6225291206555578
[146.36777777777777, 234.76222222222222]
0.6234724496653825
[146.33666666666667, 234.95555555555555]
0.6228270122008891
[146.5288888888889, 234.9177777777778]
0.6237454239308317
[146.36666666666667, 234.88444444444445]
0.623143295048156
[146.0311111111111, 234.86333333333334]
0.6217705805267365
[145.7722222222222, 235.0]
0.6203073286052009
[145.55, 234.73555555555555]
0.620059452244133
[145.84777777777776, 234.5822222222222]
0.6217341467573558
[145.30666666666667, 234.70888888888888]
0.6190931555875364
[145.70888888888888, 234.79222222222222]
0.620586523309025
[145.5077777777778, 234.7122222222222]
0.6199412045956988
[145.4611111111111, 234.69333333333333]
0.6197922584554786
[145.60333333333332, 234.80666666666667]
0.6200988046903835
[146.3411111111111, 234.79111111111112]
0.6232821609752404
[145.9922222222222, 234.9188888888889]
0.621457997322953
[146.14333333333335, 234.80555555555554]
0.6224015142552941
[146.92111111111112, 234.89]
0.6254889995789992
[146.81, 234.73666666666668]
0.6254242342483066
[146.8388888888889, 235.0211111111111]
0.6247902079718607
[147.25444444444443, 234.9488888888889]
0.6267509718425757
[147.34444444444443, 234.89]
0.6272912616307397
[147.06444444444443, 234.94555555555556]
0.6259511659911752
[147.20777777777778, 234.89111111111112]
0.6267064644610741
[147.69222222222223, 234.9922222222222]
0.6284983427347478
[147.1511111111111, 234.9311111111111]
0.6263585542806874
[147.41333333333333, 235.03444444444443]
0.6271988502867192
[148.00222222222223, 235.01888888888888]
0.629746072419711
[148.04888888888888, 234.93777777777777]
0.6301621233045156
[148.41555555555556, 235.0211111111111]
0.6314988251646424
[148.83777777777777, 235.02777777777777]
0.6332773903793878
[148.35333333333332, 235.0511111111111]
0.6311535079840791
[148.8011111111111, 235.05]
0.6330615235529083
[148.85555555555555, 234.95]
0.6335626965548226
[149.36111111111111, 235.0388888888889]
0.6354740350296642
[149.33444444444444, 235.17444444444445]
0.6349943540728632
[149.60555555555555, 235.01444444444445]
0.6365802574782637
[149.25, 235.06666666666666]
0.6349262620533183
[149.1988888888889, 234.9777777777778]
0.6349489313410251
[149.40222222222224, 235.01]
0.6357270848994606
[148.9788888888889, 234.93]
0.6341416119222274
[149.23222222222222, 235.0688888888889]
0.6348446318336941
[149.51333333333332, 235.02444444444444]
0.6361607776023297
[149.86111111111111, 234.92222222222222]
0.6379179870406281
[149.81333333333333, 234.92888888888888]
0.6376965133657466
[150.36888888888888, 235.07111111111112]
0.6396740466241893
[150.35888888888888, 235.09]
0.6395801135262618
[150.17333333333335, 235.10111111111112]
0.6387606278149827
[149.20222222222222, 235.24666666666667]
0.634237348976488
[149.7211111111111, 235.0611111111111]
0.6369454751719411
[149.26666666666668, 234.90666666666667]
0.6354296741968442
[149.4111111111111, 235.13222222222223]
0.6354344364163897
[148.91, 234.76666666666668]
0.6342893653272753
[149.58444444444444, 234.9777777777778]
0.6365897484395687
[149.04, 235.0611111111111]
0.6340478835291059
[149.31555555555556, 235.0377777777778]
0.6352832168823924
[149.84666666666666, 235.13777777777779]
0.6372717650172003
[149.86, 234.9777777777778]
0.6377624361641763
[149.79666666666665, 234.92]
0.6376496963505307
[150.05, 235.09444444444443]
0.6382541295460454
[149.70111111111112, 234.87666666666667]
0.6373605059865934
[149.32777777777778, 234.93666666666667]
0.6356086510312472
[149.20222222222222, 234.89222222222222]
0.6351943917541378
[149.0011111111111, 234.92444444444445]
0.6342512013318703
[148.75333333333333, 234.90777777777777]
0.6332414138881926
[149.33666666666667, 235.0088888888889]
0.6354511413279876
[149.92333333333335, 234.96444444444444]
0.6380681710708004
[149.49777777777777, 234.81222222222223]
0.636669490041688
[150.20888888888888, 234.73]
0.6399219907506023
[149.07555555555555, 234.8088888888889]
0.6348803755299818
[149.15444444444444, 235.0822222222222]
0.6344777713707733
[149.2411111111111, 234.96]
0.6351766730980214
[148.92555555555555, 235.08444444444444]
0.6334981283321359
[149.24777777777777, 235.1911111111111]
0.6345808609546846
[149.23111111111112, 235.06666666666666]
0.634845906598601
[149.10777777777778, 235.34666666666666]
0.6335665590240402
[149.26666666666668, 234.7111111111111]
0.6359590986555578
[149.03222222222223, 234.7277777777778]
0.6349151499372796
[148.89111111111112, 235.45555555555555]
0.6323533575574537
[148.4488888888889, 235.37444444444444]
0.6306924663774506
[148.35111111111112, 235.05777777777777]
0.6311261533807292
[148.15333333333334, 234.79666666666665]
0.6309856755490567
[148.08555555555554, 234.8111111111111]
0.6306582122746416
[147.9088888888889, 235.01888888888888]
0.6293489412198547
[147.45777777777778, 234.99777777777777]
0.6274858391095897
[147.35, 234.9011111111111]
0.6272852405976983
[147.41222222222223, 234.95666666666668]
0.6274017431110228
[147.39444444444445, 235.02333333333334]
0.6271481318639757
[147.2277777777778, 235.02555555555554]
0.6264330592890609
[147.35, 234.89555555555555]
0.6273000766298024
[147.41222222222223, 235.03333333333333]
0.6271970878835154
[147.2811111111111, 234.98111111111112]
0.6267785117479892
[147.17333333333335, 235.03333333333333]
0.6261806835909801
[147.05666666666667, 234.94333333333333]
0.6259239816693387
[146.7411111111111, 234.98]
0.6244834075713299
[146.92333333333335, 235.0011111111111]
0.6252027177176468
[146.21777777777777, 234.93666666666667]
0.6223710408951821
^C[146.58, 234.89888888888888]
0.6240131687865702
Traceback (most recent call last):
  File "camera_detect_color.py", line 171, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:39:30] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:39:30] "GET /stream.mjpg HTTP/1.1" 200 -
[157.04111111111112, 239.50444444444443]
0.6556918451988829
[157.85777777777778, 239.23555555555555]
0.6598424611726239
[157.2511111111111, 239.01888888888888]
0.6579024437864046
[157.01, 238.96444444444444]
0.657043353729983
[155.50222222222223, 238.42666666666668]
0.6522014688886404
[154.79, 238.0288888888889]
0.6502992167150579
[154.61, 237.9]
0.6498949138293401
[154.29777777777778, 238.03555555555556]
0.6482131520967923
[151.58666666666667, 237.74666666666667]
0.6375974426560485
[151.32777777777778, 237.4622222222222]
0.6372709577195905
[150.71555555555557, 237.4477777777778]
0.6347313795314058
[149.67666666666668, 237.2577777777778]
0.6308609482419497
[149.4911111111111, 237.18555555555557]
0.6302707210013725
[149.29555555555555, 237.03222222222223]
0.6298534188975713
[149.35222222222222, 236.84444444444443]
0.6305920435353726
[149.02555555555554, 236.74555555555557]
0.6294756208024554
[148.66555555555556, 236.75444444444443]
0.6279314244951404
[148.28666666666666, 236.69333333333333]
0.62649278954484
[148.13444444444445, 236.86111111111111]
0.6254063562800516
[147.82111111111112, 236.62333333333333]
0.6247106277675255
[147.99, 236.6811111111111]
0.6252716970325756
[148.40777777777777, 236.4788888888889]
0.6275730509183343
[148.42222222222222, 236.84666666666666]
0.6266595359398016
[148.11666666666667, 236.6211111111111]
0.6259655614461
[147.87777777777777, 236.62]
0.6249589120859511
[148.59555555555556, 236.62777777777777]
0.6279717324442984
[148.64555555555555, 236.65666666666667]
0.628106351911583
192.168.1.171 - - [09/Nov/2021 18:39:31] "GET /index.html HTTP/1.1" 200 -
[148.08555555555554, 236.55333333333334]
0.6260133960863887
192.168.1.171 - - [09/Nov/2021 18:39:31] "GET /stream.mjpg HTTP/1.1" 200 -
[148.64, 236.51444444444445]
0.6284605591389767
WARNING:root:Removed streaming client ('192.168.1.171', 55042): [Errno 104] Connection reset by peer
[148.25555555555556, 236.50222222222223]
0.626867494785109
[147.79555555555555, 236.61555555555555]
0.6246231580529128
[147.85, 236.4088888888889]
0.6253994961648368
[147.69444444444446, 236.5511111111111]
0.6243658875695176
[147.8022222222222, 236.71]
0.6244021047789371
[147.9388888888889, 236.55555555555554]
0.6253875058713011
[147.74333333333334, 236.55333333333334]
0.6245666939097596
[147.57555555555555, 236.45777777777778]
0.6241095426949608
[147.49555555555557, 236.56666666666666]
0.6234841012634447
[148.11777777777777, 236.56666666666666]
0.6261143206049504
[147.58555555555554, 236.51555555555555]
0.6239993610944077
[148.4177777777778, 236.46333333333334]
0.6276566251756204
[148.0911111111111, 236.48222222222222]
0.6262251332024018
[147.65666666666667, 236.48555555555555]
0.624379219778516
[147.60333333333332, 236.4322222222222]
0.6242944889068514
[147.56333333333333, 236.5211111111111]
0.6238907497099155
[147.63777777777779, 236.5377777777778]
0.6241615151913719
[148.25555555555556, 236.4711111111111]
0.6269499680487164
[148.29222222222222, 236.58666666666667]
0.6267987300871656
[148.33666666666667, 236.44444444444446]
0.6273637218045113
[148.55555555555554, 236.39777777777778]
0.6284135026649996
[147.88555555555556, 236.39333333333335]
0.6255910582174717
[148.26, 236.57222222222222]
0.6267007960923373
[148.10111111111112, 236.42222222222222]
0.6264263558605133
[148.53666666666666, 236.35777777777778]
0.6284399356907137
[147.48777777777778, 236.56222222222223]
0.6234629366950672
[147.19333333333333, 236.3311111111111]
0.622826730857836
[147.45444444444445, 236.44666666666666]
0.6236266576441951
[147.74777777777777, 236.40222222222224]
0.6249847247158796
[148.03, 236.59222222222223]
0.6256756820220445
[148.0377777777778, 236.46]
0.6260584360051501
[148.1, 236.26111111111112]
0.6268488254520657
[148.01888888888888, 236.3488888888889]
0.6262728358265088
[148.25666666666666, 236.3488888888889]
0.6272788815028629
[148.27777777777777, 236.28333333333333]
0.6275422632903058
[147.88555555555556, 236.30666666666667]
0.6258204969060919
[147.99444444444444, 236.2811111111111]
0.6263490286993365
[148.07444444444445, 236.3322222222222]
0.6265520759382979
[147.73777777777778, 236.45444444444445]
0.6248044020694613
[147.87, 236.4322222222222]
0.6254223667576801
[147.50666666666666, 236.24555555555557]
0.6243785891327761
[147.52555555555554, 236.28555555555556]
0.6243528310847984
[147.32888888888888, 236.4488888888889]
0.6230897915452717
[147.21666666666667, 236.3011111111111]
0.6230045469292945
[147.39555555555555, 236.38111111111112]
0.6235504810969102
[147.59777777777776, 236.1988888888889]
0.6248876888121592
[147.47666666666666, 236.31444444444443]
0.6240696247466887
[147.35333333333332, 236.24]
0.6237442149226774
[148.2288888888889, 236.32888888888888]
0.6272144281039606
[147.4922222222222, 236.3488888888889]
0.6240444916648645
[147.8011111111111, 236.3388888888889]
0.6253778707599728
[148.29, 236.28222222222223]
0.6275969415106228
[147.8322222222222, 236.23444444444445]
0.6257860599874888
[147.72, 236.32444444444445]
0.6250728753314652
[148.17333333333335, 236.2277777777778]
0.627247712894805
[147.78, 236.3088888888889]
0.6253679271010636
[147.94444444444446, 236.2411111111111]
0.6262434330274625
[148.05444444444444, 236.26555555555555]
0.6266442186052418
[148.4, 236.25]
0.6281481481481481
[148.3388888888889, 236.26888888888888]
0.627839279164041
[148.79111111111112, 236.2877777777778]
0.6297029516738064
[148.39555555555555, 236.25]
0.6281293356848912
[148.0611111111111, 236.31]
0.6265545728539254
[148.07111111111112, 236.20888888888888]
0.6268651099779856
[147.66, 236.21]
0.6251217137293086
[147.61777777777777, 236.24444444444444]
0.6248518483679805
[148.03666666666666, 236.21]
0.6267163399799613
[148.2188888888889, 236.37555555555556]
0.6270482941458507
[148.25555555555556, 236.16]
0.6277758958145138
[148.28555555555556, 236.19444444444446]
0.6278113606962249
[148.33444444444444, 236.0377777777778]
0.6284351845749738
[147.9388888888889, 236.18444444444444]
0.6263701626788857
[148.03222222222223, 236.28666666666666]
0.6264941831485296
[147.8111111111111, 236.21777777777777]
0.6257408417844174
[148.45222222222222, 236.30444444444444]
0.6282244185937161
[148.44, 236.38222222222223]
0.6279660060918286
[147.96, 236.29222222222222]
0.6261738055044836
[148.34, 236.23333333333332]
0.6279384789050374
[148.16666666666666, 236.22666666666666]
0.6272224417226393
[148.73666666666668, 236.41]
0.6291471031964243
[148.9411111111111, 236.2277777777778]
0.6304978716398955
[148.5988888888889, 236.19555555555556]
0.6291349917206082
[148.73222222222222, 236.23111111111112]
0.6296047185430463
[149.22666666666666, 236.16]
0.6318879855465221
[148.6688888888889, 236.13888888888889]
0.6295824020703447
[148.7722222222222, 236.29777777777778]
0.6295963661669832
[148.76777777777778, 236.17222222222222]
0.6299122580038108
[148.53, 236.14]
0.6289912763614806
[148.5677777777778, 236.19444444444446]
0.6290062330942021
[148.49444444444444, 236.20555555555555]
0.6286661805865889
[148.2422222222222, 236.2111111111111]
0.6275836116468319
[148.64444444444445, 236.2211111111111]
0.6292597801494834
[148.5911111111111, 236.2711111111111]
0.6289008859878482
[147.98888888888888, 236.14222222222222]
0.6266938944515545
[148.5888888888889, 236.17222222222222]
0.6291548069911318
[148.0688888888889, 236.22555555555556]
0.6268114749086325
[148.04, 236.0988888888889]
0.6270253989618285
[148.52666666666667, 236.23111111111112]
0.6287345725466587
[147.98222222222222, 236.13444444444445]
0.6266863039417281
[147.91444444444446, 236.17222222222222]
0.6262990755333914
[147.88555555555556, 236.09444444444443]
0.626383038802739
[148.2211111111111, 236.09444444444443]
0.6278043155987482
[147.85, 236.23777777777778]
0.6258524838439613
[148.2411111111111, 236.17777777777778]
0.6276674821226947
[148.5222222222222, 236.1611111111111]
0.6289021148462678
[148.21333333333334, 236.26111111111112]
0.6273285207044936
[148.21444444444444, 236.12333333333333]
0.6276992720376827
[147.61222222222221, 236.1688888888889]
0.6250282283864654
[147.64222222222222, 236.3322222222222]
0.6247232003911631
[147.54555555555555, 236.09333333333333]
0.6249458782778938
[147.78333333333333, 236.17777777777778]
0.6257292058712834
[147.79, 236.1822222222222]
0.6257456577783632
[148.15222222222224, 236.26111111111112]
0.6270698614997531
[148.0811111111111, 236.14666666666668]
0.6270726290629176
[148.42555555555555, 236.11]
0.6286288406063086
[148.28333333333333, 236.17555555555555]
0.6278521627038267
[148.59444444444443, 236.17888888888888]
0.6291605703774446
[148.12666666666667, 236.08555555555554]
0.6274279098443597
[148.30666666666667, 236.11666666666667]
0.6281075739394367
[148.36, 236.09222222222223]
0.6283985071746917
[148.4988888888889, 236.19]
0.6287264020021546
[148.95777777777778, 236.1677777777778]
0.6307286251299687
[148.37222222222223, 236.11666666666667]
0.628385214465542
[148.4, 236.02333333333334]
0.6287513946361235
[148.45222222222222, 236.0688888888889]
0.6288512769342283
[148.7577777777778, 236.08555555555554]
0.6301011403587212
[148.5611111111111, 236.16666666666666]
0.6290519877675841
[148.7888888888889, 236.10666666666665]
0.6301765680295159
[148.60555555555555, 236.14555555555555]
0.6292964320499127
[148.4622222222222, 236.09666666666666]
0.6288196454371325
[148.0222222222222, 236.24444444444444]
0.6265638227824287
[148.28666666666666, 236.0677777777778]
0.6281529315968577
[147.8088888888889, 235.99333333333334]
0.6263265440643333
[148.12, 236.12666666666667]
0.6272904373358932
[148.32888888888888, 236.08444444444444]
0.6282874301097535
[148.63111111111112, 236.11111111111111]
0.6294964705882353
[148.5288888888889, 236.11444444444444]
0.6290546486402545
[148.5388888888889, 236.08555555555554]
0.6291739811838458
[148.93666666666667, 236.15777777777777]
0.6306659389673571
[148.61222222222221, 236.0911111111111]
0.6294697903822442
[148.82333333333332, 235.95666666666668]
0.6307231553816378
[149.05, 236.07111111111112]
0.6313775510204082
[148.63111111111112, 236.03555555555556]
0.6296979739398961
[148.9788888888889, 236.15777777777777]
0.6308447271598084
[148.91555555555556, 236.25333333333333]
0.6303215004608989
[148.5888888888889, 236.08444444444444]
0.6293887309625559
[148.76444444444445, 235.91333333333333]
0.6305893878166182
[148.31333333333333, 236.00555555555556]
0.6284315340975966
[148.76666666666668, 236.28]
0.6296202245922917
[148.50666666666666, 236.08333333333334]
0.6290434168725731
[147.9611111111111, 236.12666666666667]
0.62661754049145
[148.29444444444445, 236.08]
0.6281533566775858
[148.34555555555556, 236.03222222222223]
0.6284970507793192
[148.12444444444444, 236.05444444444444]
0.627501188520539
[148.22555555555556, 236.12333333333333]
0.6277463284253522
[148.0, 236.04111111111112]
0.6270094192631227
[148.33444444444444, 235.99]
0.6285624155449148
[148.42555555555555, 236.13666666666666]
0.6285578502091538
[148.2588888888889, 236.10666666666665]
0.6279318198930803
[148.50333333333333, 236.09444444444443]
0.6289996940960538
[148.0988888888889, 236.01666666666668]
0.6274933502812889
[148.6911111111111, 236.0311111111111]
0.6299640348729922
[149.2277777777778, 236.02666666666667]
0.632249651640116
[149.00333333333333, 235.98444444444445]
0.63141167496916
[148.66444444444446, 236.05777777777777]
0.6297799032251992
[148.54666666666665, 236.02]
0.6293816908171623
[148.47444444444446, 235.9388888888889]
0.6292919541312487
[147.99777777777777, 236.0822222222222]
0.6268908195826313
[148.5911111111111, 236.02444444444444]
0.6295581436950974
[148.55777777777777, 235.86666666666667]
0.6298379498775202
[148.4911111111111, 236.05777777777777]
0.6290456197164536
[148.66222222222223, 236.0]
0.629924670433145
[148.59222222222223, 236.0522222222222]
0.6294887666100252
[148.45444444444445, 236.07555555555555]
0.6288429316414708
[148.56444444444443, 236.01333333333332]
0.6294747942677438
[148.10777777777778, 236.05555555555554]
0.6274276300305955
[148.51555555555555, 236.08555555555554]
0.6290751469570824
[148.36222222222221, 236.13]
0.628307382468226
[147.83, 235.93555555555557]
0.6265694021908054
[147.85333333333332, 236.07666666666665]
0.6262937181424114
[148.53444444444443, 235.98444444444445]
0.6294247266768995
[147.86555555555555, 235.98888888888888]
0.6265784641461463
[148.03666666666666, 236.05444444444444]
0.6271293345697084
[148.2, 236.07222222222222]
0.6277739863036265
[148.1511111111111, 236.01222222222222]
0.6277264360132008
[148.55, 235.9388888888889]
0.629612187713391
[148.68, 236.14]
0.6296264927585331
[148.18333333333334, 236.04777777777778]
0.6277683896386325
[148.5988888888889, 235.98333333333332]
0.6297007792452387
[148.60444444444445, 236.00555555555556]
0.6296650267178269
[149.08777777777777, 236.07]
0.631540550589985
[148.89666666666668, 236.01111111111112]
0.630888376253472
[148.76111111111112, 235.9]
0.6306108991568933
[148.7, 236.08444444444444]
0.6298593723526421
[148.43777777777777, 236.04333333333332]
0.6288581663442212
[147.7511111111111, 236.1822222222222]
0.6255810014866111
[148.54333333333332, 236.04333333333332]
0.62930535353678
[147.9711111111111, 235.9622222222222]
0.6270966162191688
[148.25444444444443, 236.08]
0.6279839225874467
[148.94666666666666, 236.00666666666666]
0.6311121154769639
[148.96777777777777, 235.94444444444446]
0.6313680244878738
[148.99777777777777, 236.00666666666666]
0.6313286818639775
[149.02777777777777, 236.00666666666666]
0.6314557969172245
[149.00555555555556, 236.07222222222222]
0.6311863130397948
[149.50555555555556, 235.99444444444444]
0.6335130299677488
[149.29333333333332, 235.96333333333334]
0.6326971704643376
[149.7111111111111, 235.93777777777777]
0.6345364126134951
[149.60777777777778, 236.01444444444445]
0.6338924642088761
[149.04222222222222, 236.02777777777777]
0.6314605154760504
[149.0011111111111, 236.12777777777777]
0.6310189868950427
[148.8188888888889, 236.03]
0.6305083628728928
[148.73222222222222, 236.06222222222223]
0.6300551643634447
[148.74777777777777, 236.01555555555555]
0.6302456523581308
[148.78666666666666, 235.9788888888889]
0.6305083788097805
[148.6588888888889, 235.96]
0.6300173287374508
[148.85222222222222, 236.10777777777778]
0.6304418415318804
[148.79555555555555, 236.03333333333333]
0.6304006025514287
[148.57333333333332, 235.92444444444445]
0.6297496373603602
[149.38555555555556, 235.98222222222222]
0.6330373286123249
[149.43555555555557, 236.03666666666666]
0.6331031431086508
[149.38444444444445, 236.01555555555555]
0.6329432146657
[149.34, 236.04444444444445]
0.6326774618715872
[149.45111111111112, 235.99333333333334]
0.6332853093778543
[150.12, 236.0511111111111]
0.6359639626069684
[149.98888888888888, 235.84333333333333]
0.6359683217201626
[149.66444444444446, 236.06]
0.6340101857343237
[150.16666666666666, 236.02333333333334]
0.6362365302865536
[148.90333333333334, 235.90666666666667]
0.6311959532018312
[148.52666666666667, 235.98888888888888]
0.6293799143085833
[148.26555555555555, 235.96666666666667]
0.6283326270188822
[147.86333333333334, 235.9688888888889]
0.626622153579568
[147.6588888888889, 235.99666666666667]
0.625682095321497
[148.34777777777776, 235.9988888888889]
0.6285952382073361
[147.83333333333334, 235.9777777777778]
0.626471419154346
[148.02333333333334, 235.91]
0.6274567984966019
[148.1511111111111, 235.9788888888889]
0.6278151058710525
[147.81, 236.01111111111112]
0.6262840732545548
[148.57666666666665, 235.89444444444445]
0.6298438567155742
[148.43333333333334, 236.0211111111111]
0.6288985448570985
[149.28444444444443, 236.0511111111111]
0.6324242395714675
[148.32444444444445, 235.86777777777777]
0.6288457280679854
[149.0511111111111, 235.92444444444445]
0.6317747678164384
[149.25666666666666, 235.89666666666668]
0.6327205414800265
[148.89555555555555, 235.9322222222222]
0.6310946175690758
[149.79444444444445, 235.85111111111112]
0.6351229118181904
[149.7188888888889, 235.95888888888888]
0.6345126034196165
[149.2122222222222, 235.9922222222222]
0.6322760166295499
[148.9622222222222, 235.92555555555555]
0.631395025737874
[148.82222222222222, 236.0677777777778]
0.6304215832552797
[149.06555555555556, 236.07888888888888]
0.631422641207506
[148.96444444444444, 236.07333333333332]
0.6310091967656002
[149.10222222222222, 236.00555555555556]
0.6317742049386784
[148.73333333333332, 235.89555555555555]
0.6305050257646981
[148.85222222222222, 235.91555555555556]
0.630955520807822
[149.23444444444445, 235.91333333333333]
0.6325816448601652
[149.2488888888889, 235.96444444444444]
0.6325058389211181
[148.83, 236.02555555555554]
0.6305673114493252
[148.69222222222223, 236.09666666666666]
0.629793822680917
[149.27444444444444, 236.03333333333333]
0.6324295061902744
[149.3088888888889, 236.01444444444445]
0.6326260633765354
[149.61444444444444, 236.01333333333332]
0.6339236954597669
[149.12222222222223, 236.17]
0.631418987264353
[149.55555555555554, 236.04222222222222]
0.6335966258390683
[149.46555555555557, 235.86]
0.6337045516643584
[149.9311111111111, 236.04111111111112]
0.6351906682922466
[150.23444444444445, 236.03222222222223]
0.6364997246138709
[150.85888888888888, 236.0222222222222]
0.6391723943131532
[150.71444444444444, 235.99777777777777]
0.6386265407395549
[150.47555555555556, 236.02777777777777]
0.637533247028363
[151.07888888888888, 235.98777777777778]
0.6401979386879735
[150.30777777777777, 235.97444444444446]
0.6369663381627954
[150.06, 236.03333333333333]
0.6357576613472673
[149.54, 235.96333333333334]
0.633742530619164
[149.9622222222222, 235.84555555555556]
0.6358492610512528
[149.92555555555555, 235.95666666666668]
0.6353944462495467
[149.9011111111111, 236.06666666666666]
0.6349948225548339
[149.94333333333333, 236.02666666666667]
0.6352813241441645
[150.31444444444443, 236.04222222222222]
0.636811681525904
[150.24777777777777, 236.02444444444444]
0.6365771906864637
[149.51888888888888, 236.0822222222222]
0.6333339608610936
[149.25555555555556, 235.74666666666667]
0.6331184133627434
[149.17666666666668, 235.67]
0.6329896323955815
[148.99666666666667, 235.60222222222222]
0.6324077305439488
[149.46, 235.68333333333334]
0.6341560002828655
[149.2277777777778, 235.59333333333333]
0.633412565909241
[148.90444444444444, 235.64666666666668]
0.631897096406107
[148.86333333333334, 235.62777777777777]
0.6317732770612785
[149.14666666666668, 235.76888888888888]
0.6325968933795808
[149.10777777777778, 235.64777777777778]
0.6327569866514525
[148.98111111111112, 235.6688888888889]
0.6321628273189315
[149.02666666666667, 235.70777777777778]
0.632251799544634
[150.02666666666667, 235.6988888888889]
0.6365183449693347
[149.57888888888888, 235.57444444444445]
0.6349538008744582
[149.21333333333334, 235.55444444444444]
0.6334558181878217
[149.58666666666667, 235.67444444444445]
0.634717383207532
[148.95555555555555, 235.51777777777778]
0.6324599228178104
[148.51555555555555, 235.54444444444445]
0.6305203075616774
[147.84333333333333, 235.53]
0.6277048925119234
[147.38222222222223, 235.5688888888889]
0.6256438314812369
[147.4088888888889, 235.30777777777777]
0.6264514087932118
[146.92666666666668, 235.53]
0.6238129608400912
[147.07888888888888, 235.44333333333333]
0.6246891207603622
[146.59777777777776, 235.71333333333334]
0.6219324791884681
[146.67666666666668, 235.45111111111112]
0.6229601804573727
[146.59444444444443, 235.32222222222222]
0.6229519807356343
[146.67555555555555, 235.39777777777778]
0.6230966024412578
[146.6811111111111, 235.36111111111111]
0.6232172784137849
[146.50333333333333, 235.48222222222222]
0.6221417988619098
[146.39333333333335, 235.39555555555555]
0.6219035571331472
[145.9188888888889, 235.36444444444444]
0.6199699756406141
[146.3, 235.42444444444445]
0.6214307963866681
[146.2422222222222, 235.39666666666668]
0.6212586792034249
[146.8188888888889, 235.44]
0.6235936497149546
[146.3488888888889, 235.52666666666667]
0.6213686584203724
[147.2188888888889, 235.42555555555555]
0.6253309609548666
[146.65555555555557, 235.39555555555555]
0.6230175213352467
[146.48222222222222, 235.40666666666667]
0.622251800666459
[146.5011111111111, 235.5377777777778]
0.6219856215563438
[145.84, 235.42444444444445]
0.6194768786399978
[145.76888888888888, 235.45555555555555]
0.6190930111839932
[146.16444444444446, 235.42888888888888]
0.6208432836525302
[146.7277777777778, 235.5088888888889]
0.6230243727530926
[146.86444444444444, 235.34222222222223]
0.624046306088533
[147.00666666666666, 235.4711111111111]
0.624308714444801
[147.40333333333334, 235.5588888888889]
0.6257600128300072
[147.02666666666667, 235.57666666666665]
0.6241138765865324
[147.29333333333332, 235.49333333333334]
0.6254671045181746
[147.5011111111111, 235.43444444444444]
0.6265060809567183
[147.60888888888888, 235.38666666666666]
0.6270911219364828
[148.02444444444444, 235.48222222222222]
0.628601357026244
[148.0088888888889, 235.44444444444446]
0.6286361491269467
[147.91222222222223, 235.57888888888888]
0.6278670509053349
[148.23, 235.51666666666668]
0.6293822093270115
[147.99777777777777, 235.54333333333332]
0.6283250546018897
[148.26444444444445, 235.52]
0.629519550120773
[148.12666666666667, 235.61555555555555]
0.6286794873004047
[148.32888888888888, 235.4088888888889]
0.630090433666245
^X[147.87555555555556, 235.48555555555555]
0.627960195718539
[148.35666666666665, 235.61888888888888]
0.629646745922087
[148.04333333333332, 235.47222222222223]
0.6287082694349415
[147.95777777777778, 235.52777777777777]
0.6281967213114754
[147.8, 235.42666666666668]
0.6277963413943479
[147.66, 235.5222222222222]
0.6269472095107799
[147.34444444444443, 235.53222222222223]
0.6255808358375121
[147.6211111111111, 235.36888888888888]
0.6271904150458855
[147.68555555555557, 235.39444444444445]
0.6273960963866796
[147.69666666666666, 235.51111111111112]
0.6271324778260049
[148.1288888888889, 235.4188888888889]
0.6292141195127362
[147.78222222222223, 235.4088888888889]
0.6277682330507675
[147.20888888888888, 235.39]
0.6253829342320782
[147.50444444444443, 235.47333333333333]
0.626416768117173
[147.0, 235.4088888888889]
0.6244454094058565
[147.64, 235.58]
0.6267085491128278
[147.70666666666668, 235.37777777777777]
0.6275302114803626
[147.8011111111111, 235.6588888888889]
0.6271824152612298
[147.96666666666667, 235.42222222222222]
0.6285161412120068
[148.37222222222223, 235.51444444444445]
0.629992026910357
[148.00555555555556, 235.5677777777778]
0.6282928715962851
[147.90555555555557, 235.62444444444444]
0.627717365676076
[148.04, 235.62]
0.6282998047703929
[148.18777777777777, 235.55555555555554]
0.6290990566037736
[148.19555555555556, 235.47]
0.6293606640147601
[148.6977777777778, 235.49777777777777]
0.6314190273085852
[148.95777777777778, 235.4922222222222]
0.632537993705855
[148.7288888888889, 235.47555555555556]
0.6316107357215658
[148.56, 235.5]
0.630828025477707
[149.25555555555556, 235.46555555555557]
0.6338742632798381
[149.06333333333333, 235.40666666666667]
0.6332162782135878
[148.92333333333335, 235.47444444444446]
0.632439472082368
[149.57666666666665, 235.58333333333334]
0.6349204103289705
[149.61777777777777, 235.45555555555555]
0.6354395734038035
[149.30777777777777, 235.4988888888889]
0.6340062939669449
[149.48666666666668, 235.55333333333334]
0.634619194520703
[148.71444444444444, 235.40777777777777]
0.6317312276097741
[148.89333333333335, 235.3322222222222]
0.6326942053550773
[149.36444444444444, 235.41444444444446]
0.6344744257172928
[148.48666666666668, 235.45333333333335]
0.6306415991845518
[148.02777777777777, 235.51444444444445]
0.6285295075083859
[148.13444444444445, 235.54666666666665]
0.6288963734480547
[147.82333333333332, 235.57888888888888]
0.6274897297909169
[147.27555555555554, 235.51222222222222]
0.6253414543241445
[147.87444444444444, 235.51555555555555]
0.6278754882904644
[147.68333333333334, 235.44555555555556]
0.6272504613003242
[147.76888888888888, 235.44444444444446]
0.6276168003775365
[148.0822222222222, 235.49333333333334]
0.6288170460121542
[147.89222222222222, 235.4922222222222]
0.6280131922262118
[148.03444444444443, 235.38111111111112]
0.6289138654569657
[148.1888888888889, 235.30555555555554]
0.629772163853146
[147.88444444444445, 235.53222222222223]
0.6278735157727888
[147.88777777777779, 235.4622222222222]
0.6280743313388324
[147.8188888888889, 235.5011111111111]
0.6276780954088446
[148.0511111111111, 235.45555555555555]
0.6287858052947006
[148.4711111111111, 235.6688888888889]
0.6299987741746895
[148.12777777777777, 235.54777777777778]
0.628865104036454
[148.6611111111111, 235.57666666666665]
0.6310519340247808
[148.70333333333335, 235.58444444444444]
0.6312103232622415
[148.68666666666667, 235.59333333333333]
0.6311157644528708
[148.76111111111112, 235.51666666666668]
0.6316372986106197
[149.23222222222222, 235.53555555555556]
0.6335868139747715
[148.99666666666667, 235.5888888888889]
0.632443522143093
[149.13222222222223, 235.64111111111112]
0.6328786242732592
[149.39666666666668, 235.49555555555557]
0.6343927226746435
[148.35777777777778, 235.52]
0.629915836352657
[149.10888888888888, 235.54555555555555]
0.6330363081451571
[148.41666666666666, 235.59666666666666]
0.6299608087267787
[148.29555555555555, 235.56]
0.6295447255712157
[148.51888888888888, 235.47555555555556]
0.6307189234079499
[148.71333333333334, 235.4311111111111]
0.631663897908329
[148.6688888888889, 235.57111111111112]
0.6310998330298943
[149.05555555555554, 235.47]
0.6330129339429886
[149.33333333333334, 235.51555555555555]
0.6340699364042951
[148.63555555555556, 235.4188888888889]
0.6313663115864393
[148.60222222222222, 235.48]
0.631060906328445
[148.38666666666666, 235.40777777777777]
0.6303388446525414
[147.98888888888888, 235.50333333333333]
0.6283940307521007
[148.48222222222222, 235.47333333333333]
0.6305691609335334
[148.27777777777777, 235.36]
0.6300041543923256
[147.59222222222223, 235.53444444444443]
0.6266269146763154
[147.52666666666667, 235.47333333333333]
0.6265111406811812
[147.9, 235.45111111111112]
0.6281558804375525
[147.08666666666667, 235.55444444444444]
0.6244274737144987
[147.65777777777777, 235.57666666666665]
0.62679288177003
[147.36666666666667, 235.47666666666666]
0.6258227991449967
[147.25555555555556, 235.57555555555555]
0.6250884358875191
[147.4488888888889, 235.57222222222222]
0.6259179775015918
[147.65444444444444, 235.48222222222222]
0.6270301131484329
[147.51333333333332, 235.51]
0.626356984133724
[147.9111111111111, 235.5388888888889]
0.6279689600679292
[147.73222222222222, 235.43555555555557]
0.6274847563853283
[148.0077777777778, 235.4988888888889]
0.6284860980707623
[147.20777777777778, 235.52777777777777]
0.6250123835357944
[146.7288888888889, 235.57222222222222]
0.6228615899818409
[146.85666666666665, 235.48777777777778]
0.6236275532110654
[146.17666666666668, 235.49]
0.6207340722182116
[146.1977777777778, 235.41444444444446]
0.6210229713082838
[146.60555555555555, 235.46555555555557]
0.62261996328786
[146.75444444444443, 235.38666666666666]
0.6234611608322949
[146.68666666666667, 235.42555555555555]
0.6230702793522841
[147.06333333333333, 235.39444444444445]
0.6247527790233887
[147.12444444444444, 235.4111111111111]
0.6249681408410818
[147.4011111111111, 235.6688888888889]
0.6254585058132408
[147.1988888888889, 235.50333333333333]
0.6250395134770445
[147.55666666666667, 235.48222222222222]
0.6266148895410836
[147.26222222222222, 235.49444444444444]
0.6253320436905802
[147.40555555555557, 235.5611111111111]
0.6257635433126578
[147.57555555555555, 235.40555555555557]
0.6268992046822268
[147.12555555555556, 235.4488888888889]
0.6248725838115373
[147.03, 235.48444444444445]
0.6243724520609996
[146.95444444444445, 235.36666666666667]
0.6243638766935751
[146.96555555555557, 235.34333333333333]
0.6244729921769142
[146.07333333333332, 235.4111111111111]
0.6205031387171379
[146.35, 235.4611111111111]
0.6215463747257155
[147.0011111111111, 235.38777777777779]
0.6245061340860707
[146.91444444444446, 235.45777777777778]
0.6239523953339122
[147.00666666666666, 235.37777777777777]
0.6245562688821752
[146.89444444444445, 235.2811111111111]
0.6243359007900715
[146.89777777777778, 235.42555555555555]
0.6239670006560224
[146.72222222222223, 235.3488888888889]
0.6234243251154314
[146.69555555555556, 235.28222222222223]
0.6234876318747226
[146.88111111111112, 235.32444444444445]
0.624164274382413
[146.09777777777776, 235.28333333333333]
0.6209440154895988
[146.09777777777776, 235.28]
0.6209528127243189
[145.61, 235.36333333333334]
0.6186605106997691
[146.02444444444444, 235.26666666666668]
0.62067630112402
[145.65, 235.2211111111111]
0.6192046254351699
[145.67, 235.26666666666668]
0.6191697364692547
[145.51777777777778, 235.27444444444444]
0.6185022692175096
[145.79333333333332, 235.16444444444446]
0.6199633353492591
[146.15666666666667, 235.27555555555554]
0.6212148402818445
[145.76111111111112, 235.3022222222222]
0.6194633851500672
[145.88666666666666, 235.32222222222222]
0.6199442844326927
[145.75222222222223, 235.18333333333334]
0.6197387381003
[145.89555555555555, 235.23]
0.6202251224569806
[146.24666666666667, 235.28]
0.6215856284710416
[145.86888888888888, 235.24333333333334]
0.6200766109796475
[145.77555555555554, 235.17444444444445]
0.6198613794960715
[146.60444444444445, 235.28333333333333]
0.6230974475219003
[145.87444444444444, 235.2722222222222]
0.6200240855746298
[146.10555555555555, 235.33]
0.6208539308866509
[145.99444444444444, 235.2888888888889]
0.6204901775595013
[146.29555555555555, 235.35666666666665]
0.6215908715377607
[146.35222222222222, 235.27666666666667]
0.6220430793061597
[146.34444444444443, 235.32666666666665]
0.6218778624512498
[146.05555555555554, 235.38666666666666]
0.620492050904422
[146.00555555555556, 235.37444444444444]
0.6203118435400804
[146.46666666666667, 235.36111111111111]
0.6223061489437035
[146.39333333333335, 235.33777777777777]
0.6220562406753414
[146.6822222222222, 235.3022222222222]
0.6233779725365015
[147.02, 235.3711111111111]
0.6246306069847145
[146.78, 235.37333333333333]
0.6236050529655016
[146.62666666666667, 235.4388888888889]
0.6227801505462611
[146.14888888888888, 235.52666666666667]
0.620519497674243
[146.26666666666668, 235.36555555555555]
0.6214446558308825
[146.35444444444445, 235.25333333333333]
0.6221142220207059
[146.4922222222222, 235.3022222222222]
0.6225705003494324
[146.30666666666667, 235.34666666666666]
0.6216644949294657
[146.57444444444445, 235.2877777777778]
0.6229581741508035
[146.70111111111112, 235.29888888888888]
0.6234670796953284
[146.72222222222223, 235.4011111111111]
0.6232860224392409
[146.57, 235.21333333333334]
0.6231364435122725
[146.14111111111112, 235.28444444444443]
0.621125257371692
[146.88, 235.41333333333333]
0.6239238785681921
[146.82888888888888, 235.32555555555555]
0.6239394125396023
[146.76, 235.36888888888888]
0.6235318554326069
[147.10888888888888, 235.54888888888888]
0.6245365434870799
[146.46, 235.4177777777778]
0.6221280371538069
[146.43777777777777, 235.38111111111112]
0.6221305400697685
[146.38888888888889, 235.34666666666666]
0.6220138613487433
[146.63, 235.35333333333332]
0.623020706455542
[146.31444444444443, 235.50666666666666]
0.621275170318368
[146.42, 235.35666666666665]
0.6221196198677185
[146.35666666666665, 235.45666666666668]
0.6215864207143564
[145.95444444444445, 235.46777777777777]
0.6198489059602399
[146.4488888888889, 235.38]
0.6221806818289103
[146.32666666666665, 235.41]
0.6215822040978151
[146.63777777777779, 235.40666666666667]
0.6229125956972804
[147.28555555555556, 235.44]
0.6255757541435422
[147.66444444444446, 235.44]
0.627185034167705
[147.29, 235.5888888888889]
0.6251992642550582
[147.57222222222222, 235.4088888888889]
0.6268761681801877
[147.82333333333332, 235.53666666666666]
0.6276022133850355
[147.68666666666667, 235.49444444444444]
0.6271343980749723
[147.60333333333332, 235.43]
0.626952101827861
[146.98111111111112, 235.41333333333333]
0.6243533831747471
[146.68, 235.37777777777777]
0.6231684290030212
[146.63333333333333, 235.5211111111111]
0.6225910392557402
[146.87333333333333, 235.29333333333332]
0.6242137473791579
[146.77777777777777, 235.3488888888889]
0.6236603812779136
[146.25, 235.48111111111112]
0.6210689227255783
[146.6611111111111, 235.5288888888889]
0.6226884175567045
[146.73, 235.33777777777777]
0.6234868085588563
[146.57777777777778, 235.2122222222222]
0.6231724541903058
[146.95555555555555, 235.16555555555556]
0.624902550921573
[146.7877777777778, 235.23]
0.6240181004879386
[146.60777777777778, 235.3322222222222]
0.6229821670546132
[147.39444444444445, 235.4088888888889]
0.6261209809881624
[147.0222222222222, 235.38888888888889]
0.6245928723153173
[147.17333333333335, 235.4177777777778]
0.625158111348147
[147.44333333333333, 235.37666666666667]
0.6264143996148018
[147.60777777777778, 235.48444444444445]
0.6268260229503246
[147.85, 235.5688888888889]
0.6276295681376526
[148.02777777777777, 235.45666666666668]
0.6286837398719273
[147.9711111111111, 235.48222222222222]
0.6283748714222351
[147.84444444444443, 235.4488888888889]
0.6279258532165508
[148.45444444444445, 235.51333333333332]
0.6303441182853531
[148.26333333333332, 235.38444444444445]
0.6298773637453621
[148.20666666666668, 235.4111111111111]
0.629565299476094
[148.09666666666666, 235.48333333333332]
0.6289050888244038
[148.20444444444445, 235.44222222222223]
0.6294726708133158
[147.92222222222222, 235.46666666666667]
0.628208758021895
[148.12, 235.47555555555556]
0.6290249518704466
[148.11111111111111, 235.43777777777777]
0.6290881289701455
[148.3411111111111, 235.50555555555556]
0.6298837017291405
[148.01777777777778, 235.61111111111111]
0.6282291912284839
[147.88666666666666, 235.49333333333334]
0.6279866379798437
[147.87333333333333, 235.09444444444443]
0.6289954391851975
[147.75333333333333, 234.3711111111111]
0.6304246826021409
[148.4922222222222, 234.2577777777778]
0.6338838506488578
[148.17222222222222, 233.87333333333333]
0.6335575762758568
[146.32666666666665, 232.13222222222223]
0.6303591344013708
[145.69333333333333, 232.33444444444444]
0.6270845189645196
[146.0011111111111, 232.64222222222222]
0.6275778735110661
^C[147.0222222222222, 232.55333333333334]
0.6322086212003937
Traceback (most recent call last):
  File "camera_detect_color.py", line 171, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:40:37] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:40:37] "GET /stream.mjpg HTTP/1.1" 200 -
[128.5288888888889, 236.58555555555554]
0.5432660019631141
[129.07777777777778, 236.2722222222222]
0.5463095769945214
[129.13666666666666, 236.09666666666666]
0.5469652261079501
[128.4188888888889, 236.17444444444445]
0.5437459128610208
[128.89888888888888, 235.8788888888889]
0.5464621674965023
[127.68111111111111, 236.17666666666668]
0.5406169581151585
[128.02333333333334, 236.11]
0.5422190222071633
[127.67666666666666, 236.1]
0.5407736834674572
[128.26444444444445, 236.00333333333333]
0.5434857323107489
[127.79222222222222, 236.07]
0.541331902495964
[128.03555555555556, 236.2711111111111]
0.5419010176633247
[128.10888888888888, 236.1677777777778]
0.5424486358568061
[127.75, 236.04333333333332]
0.5412141838363013
[127.84777777777778, 236.11777777777777]
0.5414576529603871
[127.81111111111112, 236.12222222222223]
0.5412921744859065
[128.0588888888889, 236.1288888888889]
0.5423262248489525
[128.1, 236.06]
0.5426586461069219
[128.14555555555555, 236.07333333333332]
0.5428209690020992
[127.90666666666667, 236.13888888888889]
0.5416586283966592
[128.09222222222223, 236.07111111111112]
0.5426001581444386
[128.0288888888889, 236.04777777777778]
0.5423854869306121
[128.1588888888889, 236.10333333333332]
0.5428084689848607
[127.88666666666667, 236.0011111111111]
0.5418901040955552
[128.3311111111111, 235.99555555555557]
0.5437861353321155
[128.15777777777777, 236.14333333333335]
0.5427118181518756
[128.33666666666667, 236.00555555555556]
0.5437866340246228
[128.32777777777778, 235.99666666666667]
0.5437694506042929
[128.7888888888889, 236.03333333333333]
0.5456385632914372
[128.2188888888889, 235.89333333333335]
0.5435460471776321
[128.14555555555555, 236.17333333333335]
0.5425911289260241
[128.62333333333333, 236.08555555555554]
0.5448166154454365
[128.32333333333332, 236.01555555555555]
0.5437071002852919
[128.40444444444444, 235.97222222222223]
0.5441506768687463
[128.33777777777777, 236.07888888888888]
0.5436224237660668
[128.57444444444445, 235.98]
0.5448531419800172
[128.39666666666668, 235.86555555555555]
0.544363785395635
[128.23, 235.94222222222223]
0.5434805131199728
[128.67555555555555, 236.15777777777777]
0.544871131352862
[128.12333333333333, 235.96333333333334]
0.5429798415007981
[128.36444444444444, 236.01111111111112]
0.5438915305305776
[128.17555555555555, 235.93555555555557]
0.5432651100583021
[128.38777777777779, 236.0911111111111]
0.5438060635724439
[128.29111111111112, 235.85333333333332]
0.5439444475851283
[127.98777777777778, 235.98555555555555]
0.5423542872209692
[128.63, 235.96444444444444]
0.5451245008664205
[128.47444444444446, 236.04666666666665]
0.5442756140499525
[128.70111111111112, 235.99777777777777]
0.5453488262601344
[128.41333333333333, 236.0011111111111]
0.5441217320069115
[129.2411111111111, 235.93555555555557]
0.5477814092360437
[128.54, 236.17555555555555]
0.544256155966842
[128.40222222222224, 235.84666666666666]
0.5444309391224054
[128.33777777777777, 235.9088888888889]
0.544014167428103
[127.93555555555555, 235.92666666666668]
0.5422683131293151
[128.0888888888889, 235.95777777777778]
0.5428466486471215
[128.0222222222222, 236.00666666666666]
0.5424517198195907
[128.25444444444443, 235.89222222222222]
0.5436993353838617
[128.01, 236.01]
0.5423922715139189
[128.1611111111111, 235.88666666666666]
0.543316470244656
[127.98444444444445, 235.88888888888889]
0.5425624116815827
[127.94888888888889, 235.87444444444444]
0.5424448977092333
[128.0988888888889, 236.0011111111111]
0.542789346566165
[127.83111111111111, 235.78222222222223]
0.5421575465118471
[128.2722222222222, 235.78666666666666]
0.5440181331523788
[127.79, 235.78444444444443]
0.5419780779054316
[127.90555555555555, 235.85444444444445]
0.5423071668496106
[127.96444444444444, 235.95111111111112]
0.5423345702499576
[127.61333333333333, 235.75]
0.5413078826440438
[127.82444444444444, 235.84555555555556]
0.5419836898912188
[127.99222222222222, 235.81555555555556]
0.5427641188499487
[127.89111111111112, 235.87555555555556]
0.5421973922218872
[128.17888888888888, 235.76555555555555]
0.5436709725763352
[128.0822222222222, 235.6511111111111]
0.5435247965447978
[127.69333333333333, 235.66]
0.5418540835667204
[128.08666666666667, 235.62444444444444]
0.5436051720723185
[128.39333333333335, 235.81555555555556]
0.5444650715719442
[128.14333333333335, 235.87]
0.5432794901146112
[128.0288888888889, 235.66]
0.5432779805180722
[128.86888888888888, 235.86777777777777]
0.546360719989071
[128.26111111111112, 235.84333333333333]
0.5438403083025927
[128.32555555555555, 235.83666666666667]
0.5441289404625612
[128.5822222222222, 235.76888888888888]
0.5453740009048409
[128.9688888888889, 235.90333333333334]
0.5467022744721237
[129.42666666666668, 235.88333333333333]
0.5486893238182718
[130.33555555555554, 235.83555555555554]
0.5526543919491924
[132.9988888888889, 234.63111111111112]
0.5668425140172754
[133.38888888888889, 234.15222222222224]
0.5696674053441019
[103.82, 233.34666666666666]
0.44491743328952627
[102.22555555555556, 234.0677777777778]
0.43673484888042874
[113.65222222222222, 234.20111111111112]
0.4852761871326163
[106.23, 233.23777777777778]
0.4554579494459636
[136.49444444444444, 233.25222222222223]
0.5851796100549238
[137.23333333333332, 233.3022222222222]
0.5882212866477434
[133.8411111111111, 233.0811111111111]
0.574225472296244
[131.7511111111111, 233.09444444444443]
0.5652263031198608
[133.3311111111111, 233.12222222222223]
0.571936513988847
[129.65333333333334, 233.19333333333333]
0.5559907372995226
[125.00777777777778, 233.15222222222224]
0.5361637842706481
[121.75111111111111, 233.2877777777778]
0.5218923694626093
[122.41888888888889, 233.1811111111111]
0.5249948776106317
[124.64444444444445, 233.1911111111111]
0.5345162765876345
[125.75666666666666, 233.19666666666666]
0.5392730027587587
[124.24888888888889, 233.21444444444444]
0.5327666954114716
[122.18222222222222, 233.26777777777778]
0.5237852539523009
[120.54555555555555, 233.36111111111111]
0.5165623140102369
[119.07888888888888, 233.31222222222223]
0.5103842728627828
[117.65444444444445, 233.46]
0.503959755180521
[116.16111111111111, 233.4488888888889]
0.49758690934013633
[115.07444444444444, 233.3388888888889]
0.49316444846551266
[114.80777777777777, 233.4088888888889]
0.49187405982824606
[113.79777777777778, 233.45222222222222]
0.48745639126730667
[111.97555555555556, 233.2588888888889]
0.48004839639313496
[113.66444444444444, 234.00666666666666]
0.48573165057025913
[114.26, 233.85222222222222]
0.4885991628141229
[115.18555555555555, 233.8388888888889]
0.49258511320709886
[120.35666666666667, 233.96444444444444]
0.5144228942669352
[140.12555555555556, 233.76888888888888]
0.5994191794364805
[140.11555555555555, 235.03444444444443]
0.5961490278020716
[138.85555555555555, 235.70444444444445]
0.5891087708712417
[138.08444444444444, 236.26444444444445]
0.5844486874406267
[138.22, 236.2722222222222]
0.5850031743045921
[134.45888888888888, 236.3088888888889]
0.5689963230799612
[132.14555555555555, 236.2422222222222]
0.5593646822000019
[131.05666666666667, 235.98222222222222]
0.5553666942895887
[128.83555555555554, 235.80666666666667]
0.5463609548311705
[128.65777777777777, 235.75222222222223]
0.5457330436380945
[128.47555555555556, 235.8788888888889]
0.5446674611735778
[128.39, 235.7888888888889]
0.5445125111917439
[127.99666666666667, 235.75333333333333]
0.5429262223227668
[128.19555555555556, 235.82777777777778]
0.543598200193173
[127.94111111111111, 235.94]
0.5422612151865351
[127.81555555555556, 235.7211111111111]
0.5422321104506739
^C[127.53333333333333, 235.6677777777778]
0.5411572788435698
Traceback (most recent call last):
  File "camera_detect_color.py", line 171, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:41:06] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:41:06] "GET /stream.mjpg HTTP/1.1" 200 -
[135.48666666666668, 238.07222222222222]
0.5690990129045809
[134.47, 237.70888888888888]
0.5656919294375006
[134.3711111111111, 237.63555555555556]
0.5654503628338445
[133.80333333333334, 237.3788888888889]
0.5636698948235591
[132.84, 237.0211111111111]
0.5604564056647556
[132.51222222222222, 236.88]
0.5594065443356223
[131.57, 236.54333333333332]
0.5562194382988318
[130.39, 236.57555555555555]
0.5511558440338533
[129.58333333333334, 236.6211111111111]
0.5476406256603384
[129.60222222222222, 236.5988888888889]
0.5477718971160755
[128.82111111111112, 236.4411111111111]
0.5448338087473038
[128.4388888888889, 236.33333333333334]
0.543464974141984
[127.66777777777777, 236.14444444444445]
0.5406342633981085
[127.30444444444444, 236.2277777777778]
0.5389054819971308
[127.61111111111111, 236.14111111111112]
0.5404019254024195
[127.38555555555556, 236.17555555555555]
0.5393680783597888
[127.45777777777778, 236.10555555555555]
0.5398338784441987
[127.63222222222223, 236.10111111111112]
0.5405828952755646
[127.56777777777778, 236.05555555555554]
0.5404142151094375
[127.71333333333334, 235.92222222222222]
0.5413365986907173
[127.35111111111111, 236.0377777777778]
0.5395369856049408
[127.49555555555555, 235.97444444444446]
0.5402939112992461
[127.41, 235.98222222222222]
0.5399135528100045
[127.16777777777777, 236.13333333333333]
0.5385422548466027
[127.26555555555555, 236.09555555555556]
0.5390425722165224
[127.22777777777777, 235.95444444444445]
0.5392048370919057
[127.49555555555555, 236.01333333333332]
0.5402048848464306
[127.03888888888889, 236.13777777777779]
0.5379862980181062
[127.31444444444445, 235.98444444444445]
0.5395035454314314
[126.9088888888889, 235.99444444444444]
0.5377621883754327
[127.09777777777778, 235.89555555555555]
0.5387883526607821
[127.50666666666666, 236.04]
0.540190928091284
[127.04888888888888, 235.99]
0.5383655616292592
[127.49777777777778, 236.02666666666667]
0.540183783376643
[126.99888888888889, 235.96666666666667]
0.5382069030465696
[127.23, 236.04222222222222]
0.5390137357723195
[127.33777777777777, 235.89888888888888]
0.5397981244318423
[127.58333333333333, 235.9388888888889]
0.5407473686689114
[127.75222222222222, 235.98444444444445]
0.5413586582919778
[127.60555555555555, 235.89444444444445]
0.540943453993076
[127.71, 236.0211111111111]
0.5410956647004269
[127.75555555555556, 235.91666666666666]
0.5415283174378901
[127.57666666666667, 236.04]
0.5404874879963848
[127.26777777777778, 235.97222222222223]
0.5393337257210123
[127.32777777777778, 235.9411111111111]
0.5396591428181232
[127.47444444444444, 235.91444444444446]
0.540341837671849
[128.14888888888888, 236.0588888888889]
0.5428683049898094
[127.78222222222222, 235.91444444444446]
0.5416464537520663
[127.88444444444444, 235.82555555555555]
0.5422840800403311
[127.70222222222222, 235.66333333333333]
0.541884137918028
[127.48666666666666, 235.82888888888888]
0.5405896930919781
[127.80555555555556, 235.88111111111112]
0.5418219159369362
[127.50777777777778, 235.87666666666667]
0.5405696950854731
[127.74888888888889, 235.8711111111111]
0.5416046428369543
[127.69, 235.89222222222222]
0.5413065288761817
[127.74111111111111, 235.75666666666666]
0.5418345657716761
[128.00555555555556, 235.92555555555555]
0.5425675707497186
[127.62, 235.83666666666667]
0.5411372277423641
[127.62777777777778, 235.85333333333332]
0.5411319652514746
[127.53777777777778, 235.7722222222222]
0.5409364028370132
[127.50888888888889, 235.76111111111112]
0.5408393618776068
[127.47888888888889, 235.66555555555556]
0.5409313575264382
[127.44222222222223, 235.84555555555556]
0.540363043611403
[127.92222222222222, 235.70333333333335]
0.5427255542513423
[127.70333333333333, 235.69222222222223]
0.54182243321092
[127.70111111111112, 235.83]
0.5414964640254044
[127.36777777777777, 235.88555555555556]
0.539955816615402
[127.70444444444445, 235.8022222222222]
0.5415743890831299
[127.28111111111112, 235.75666666666666]
0.5398834014355668
[127.47666666666667, 235.61222222222221]
0.5410443714012195
[127.55888888888889, 235.85888888888888]
0.540827142406241
[127.35222222222222, 235.7277777777778]
0.5402512314109966
[127.46444444444444, 235.62]
0.5409746390138547
[127.10333333333334, 235.61333333333334]
0.5394573029256975
[127.49222222222222, 235.78444444444443]
0.5407151541426727
[127.53666666666666, 235.64555555555555]
0.5412224574572922
[127.47555555555556, 235.72222222222223]
0.5407871788828659
[127.58888888888889, 235.7211111111111]
0.5412705221330292
[127.70777777777778, 235.76]
0.5416855182294612
[127.56888888888889, 235.67555555555555]
0.5412902860806759
[127.55111111111111, 235.6911111111111]
0.5411791327632212
[127.76222222222222, 235.62555555555556]
0.5422256593559461
[128.21555555555557, 235.85555555555555]
0.543618975832666
[127.57, 235.68666666666667]
0.5412694820807287
[127.77888888888889, 235.6811111111111]
0.5421685610971511
[127.75888888888889, 235.6888888888889]
0.5420658118046389
[127.85222222222222, 235.7711111111111]
0.5422726373035995
[127.77333333333333, 235.73555555555555]
0.5420197773399572
[127.92888888888889, 235.61555555555555]
0.5429560394993729
[127.65333333333334, 235.62444444444444]
0.5417660872763626
[127.66444444444444, 235.60222222222222]
0.5418643476292433
[128.17777777777778, 235.72555555555556]
0.5437585139027022
[127.68888888888888, 235.57222222222222]
0.5420371200150933
[127.48444444444445, 235.51333333333332]
0.5413045734612808
[128.3088888888889, 235.60555555555555]
0.5445919498219718
[127.85333333333334, 235.58555555555554]
0.5427044668839346
[127.64222222222222, 235.55555555555554]
0.5418773584905661
[127.75666666666666, 235.5677777777778]
0.5423350675200814
[127.16222222222223, 235.60111111111112]
0.5397352398828529
[127.62222222222222, 235.62777777777777]
0.5416263881357132
[127.28111111111112, 235.53555555555556]
0.5403902218112858
[127.44, 235.55444444444444]
0.5410214199123581
[128.01222222222222, 235.53333333333333]
0.5434993867345976
[127.97, 235.5377777777778]
0.5433098724432033
[127.31222222222222, 235.5222222222222]
0.5405529084304382
[127.83888888888889, 235.6588888888889]
0.5424742919379706
[128.08444444444444, 235.5677777777778]
0.5437265047568286
[127.61555555555556, 235.5688888888889]
0.541733486783767
[127.92, 235.61333333333334]
0.54292343387471
[128.1588888888889, 235.66333333333333]
0.5438219305317851
[127.63888888888889, 235.55]
0.5418759876412179
[127.72, 235.56222222222223]
0.5421922021074875
[127.7388888888889, 235.56222222222223]
0.5422723885173061
[127.42111111111112, 235.49777777777777]
0.54107139487044
[127.44333333333333, 235.63888888888889]
0.5408416833667334
[126.89111111111112, 235.45222222222222]
0.5389250944990019
[127.56555555555556, 235.65555555555557]
0.5413220802489509
[127.58, 235.58333333333334]
0.5415493455960382
[127.19111111111111, 235.45666666666668]
0.5401890416259656
[127.66, 235.53444444444443]
0.5420014057863677
[127.72777777777777, 235.4688888888889]
0.5424401430715075
[127.19, 235.51444444444445]
0.5400518014936568
[127.72777777777777, 235.5077777777778]
0.5423505711064036
[127.22555555555556, 235.32555555555555]
0.5406363760841955
[127.13111111111111, 235.2877777777778]
0.5403217808924295
[127.40777777777778, 235.5388888888889]
0.54092034813784
^C[127.71555555555555, 235.57444444444445]
0.5421452053373078
Traceback (most recent call last):
  File "camera_detect_color.py", line 171, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
^[[Api@raspberrypi:~/final $ python3 camera_detect_color.py ^C
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:41:34] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:41:34] "GET /stream.mjpg HTTP/1.1" 200 -
[123.73333333333333, 172.89222222222222]
0.7156674357178204
[133.1677777777778, 183.23777777777778]
0.726748487090241
[140.65666666666667, 191.61666666666667]
0.7340523614856049
[196.9788888888889, 238.14444444444445]
0.8271403909858629
[197.11444444444444, 238.24]
0.8273776210730542
[196.79666666666665, 238.01111111111112]
0.8268381494794826
[197.44444444444446, 237.9]
0.8299472233898464
[197.76555555555555, 237.85888888888888]
0.8314406767784821
[197.82, 238.15444444444444]
0.8306374481545589
[197.17666666666668, 238.2422222222222]
0.8276310757492376
[197.08555555555554, 237.9688888888889]
0.8281988308462357
[197.25, 238.08444444444444]
0.828487558102634
[197.66222222222223, 238.31444444444443]
0.8294177160893871
[197.7811111111111, 238.1888888888889]
0.8303540607361104
[197.5088888888889, 238.13]
0.8294162385625032
[197.76777777777778, 238.18777777777777]
0.8303019559731118
[196.4088888888889, 237.52666666666667]
0.8268919513130689
[195.67111111111112, 237.34555555555556]
0.8244144730374372
[195.22555555555556, 237.16]
0.8231807874665018
[195.45, 237.18777777777777]
0.8240306555050148
[194.8188888888889, 236.88222222222223]
0.8224293366605064
[194.29555555555555, 236.7411111111111]
0.8207089788658027
[194.19333333333333, 236.8111111111111]
0.8200347205930653
[193.66444444444446, 236.47555555555556]
0.8189617907418197
[193.35777777777778, 236.46333333333334]
0.8177072320350348
[193.6611111111111, 236.4]
0.8192094378642601
[193.42444444444445, 236.29222222222222]
0.81858151159346
[193.07555555555555, 236.32555555555555]
0.8169897457838293
[192.41, 235.99333333333334]
0.8153196417977908
[192.62222222222223, 235.90666666666667]
0.8165187739030503
[192.6811111111111, 235.7511111111111]
0.8173073297639696
[192.60555555555555, 236.10333333333332]
0.8157680488298439
[191.94666666666666, 235.89]
0.8137126061582376
[191.9988888888889, 235.9322222222222]
0.8137883290398844
[191.95, 235.72444444444446]
0.8142982389984539
[191.82444444444445, 235.59555555555556]
0.8142107943934049
[192.17111111111112, 235.72666666666666]
0.8152285603853805
[191.9622222222222, 235.86]
0.8138820580947266
[192.57444444444445, 235.71555555555557]
0.816978090353722
[192.3022222222222, 235.7811111111111]
0.8155963864789847
[192.31666666666666, 235.75222222222223]
0.8157575986087088
[192.36555555555555, 235.91555555555556]
0.8154000489817448
[192.18, 235.71]
0.8153239149802723
[192.49444444444444, 235.8]
0.8163462444632927
[192.00666666666666, 235.70777777777778]
0.8145962279093227
[192.40666666666667, 235.8711111111111]
0.8157279870362345
[192.38333333333333, 235.8311111111111]
0.8157674041687083
[192.10222222222222, 235.6822222222222]
0.815089998774244
[192.0611111111111, 235.79555555555555]
0.8145238813284578
[192.59222222222223, 235.71333333333334]
0.8170612137153417
[192.44555555555556, 235.69]
0.8165198165198165
[192.6677777777778, 235.71]
0.8173933128750489
[192.59222222222223, 235.70666666666668]
0.817084323264321
[192.58444444444444, 235.7111111111111]
0.8170359196756859
[192.86666666666667, 235.7788888888889]
0.8179980301695091
[192.61666666666667, 235.72]
0.8171418066632729
[192.68444444444444, 235.87777777777777]
0.8168825663008149
[192.2277777777778, 235.70888888888888]
0.8155304565895786
[192.0077777777778, 235.69333333333333]
0.8146508645886369
[191.84, 235.76222222222222]
0.8137011866946924
[191.94333333333333, 235.6911111111111]
0.8143851179981332
[192.09777777777776, 235.6211111111111]
0.8152825392933098
[192.09333333333333, 235.6588888888889]
0.8151329841154588
[192.41555555555556, 235.63]
0.8166004140200974
[192.59, 235.57222222222222]
0.8175412117067189
[192.4688888888889, 235.65777777777777]
0.8167304754540483
[192.17, 235.5311111111111]
0.815900706677108
[192.35555555555555, 235.5511111111111]
0.8166191814939905
[192.55444444444444, 235.67]
0.8170511496772794
[192.32555555555555, 235.5688888888889]
0.816430202064034
[192.69555555555556, 235.57222222222222]
0.817989293210386
[192.59555555555556, 235.63555555555556]
0.8173450526236373
[192.54555555555555, 235.55444444444444]
0.8174142330860051
[192.51555555555555, 235.72333333333333]
0.8167013118014999
[192.27444444444444, 235.6822222222222]
0.8158207379050888
[192.4711111111111, 235.64888888888888]
0.8167707134908809
[192.5, 235.5811111111111]
0.8171283304169831
[192.62333333333333, 235.60444444444445]
0.8175708815151572
[192.33333333333334, 235.48]
0.8167714172470416
[192.33333333333334, 235.54111111111112]
0.8165595060074439
[192.40666666666667, 235.59444444444443]
0.8166859244935978
[192.14, 235.52777777777777]
0.8157848802924873
[192.48333333333332, 235.65222222222224]
0.8168110256639963
[192.69666666666666, 235.42222222222222]
0.81851519728148
[192.67222222222222, 235.4788888888889]
0.8182144188438689
[192.43, 235.60333333333332]
0.8167541489226242
[192.61111111111111, 235.43]
0.818124755176108
[192.57777777777778, 235.47666666666666]
0.8178210627143997
[192.37666666666667, 235.5211111111111]
0.8168128358392029
[192.58333333333334, 235.4488888888889]
0.8179411431591664
[192.64888888888888, 235.63]
0.8175906671004918
[192.36555555555555, 235.46]
0.8169776418735901
[192.55, 235.59666666666666]
0.8172866056395818
[192.4011111111111, 235.50333333333333]
0.8169782923572678
[192.44222222222223, 235.5688888888889]
0.816925457049601
[192.28666666666666, 235.43333333333334]
0.8167350984001133
[192.35888888888888, 235.67444444444445]
0.8162059715143771
[191.93333333333334, 235.37444444444444]
0.8154382850965601
[191.99777777777777, 235.4388888888889]
0.8154888034167865
[191.94444444444446, 235.38444444444445]
0.8154508463695326
[192.16444444444446, 235.59333333333333]
0.8156616391710764
[192.20888888888888, 235.46777777777777]
0.8162853138669598
[192.11777777777777, 235.43666666666667]
0.8160061918043541
[192.16555555555556, 235.40444444444444]
0.816320847336027
[192.36666666666667, 235.54444444444445]
0.8166894664842681
[192.90555555555557, 235.43666666666667]
0.8193522202243586
[192.62333333333333, 235.4011111111111]
0.8182770778954126
[192.22222222222223, 235.45]
0.8164035770746325
[192.27, 235.51333333333332]
0.8163868995385967
[191.7711111111111, 235.24777777777777]
0.815187768924491
[192.15, 235.3388888888889]
0.8164821415925025
[192.33, 235.40555555555557]
0.8170155523564534
[192.76, 235.52555555555554]
0.8184249880881056
[192.45333333333335, 235.38888888888889]
0.8175973566202502
[192.7577777777778, 235.46]
0.8186434119501307
[192.1911111111111, 235.39444444444445]
0.8164640910056405
[192.4911111111111, 235.58444444444444]
0.8170790374765359
[192.41222222222223, 235.43333333333334]
0.8172683939780074
[192.48666666666668, 235.34333333333333]
0.8178972564905175
[192.50333333333333, 235.40222222222224]
0.8177634497927896
[192.35555555555555, 235.32333333333332]
0.8174096160837807
[192.58333333333334, 235.26111111111112]
0.818593997213498
[192.46777777777777, 235.36555555555555]
0.8177397806721459
[192.39111111111112, 235.38]
0.8173638844044147
[192.46, 235.40333333333334]
0.8175755087013779
[192.36555555555555, 235.55777777777777]
0.8166385222780916
[192.40555555555557, 235.43777777777777]
0.8172246500608795
[192.5088888888889, 235.35444444444445]
0.8179530637006123
[192.49, 235.34777777777776]
0.8178959742791991
[192.67333333333335, 235.4988888888889]
0.8181496492080642
[192.59555555555556, 235.28666666666666]
0.8185570320837938
[192.36111111111111, 235.36555555555555]
0.8172865849340742
[192.44555555555556, 235.42222222222222]
0.8174485557862942
[192.63555555555556, 235.48444444444445]
0.818039408123207
[192.7111111111111, 235.32555555555555]
0.8189128063722597
[192.50666666666666, 235.25222222222223]
0.8182990360228029
[192.32333333333332, 235.3322222222222]
0.817241818894329
[192.42222222222222, 235.50444444444443]
0.8170640799418742
[192.46444444444444, 235.31222222222223]
0.8179109551848371
[192.46333333333334, 235.32888888888888]
0.8178483068613194
[192.47555555555556, 235.31444444444443]
0.8179504492806317
[192.78333333333333, 235.5377777777778]
0.818481583515737
[192.59333333333333, 235.4311111111111]
0.8180453824662086
[192.7411111111111, 235.31555555555556]
0.8190750953801986
[192.80444444444444, 235.3311111111111]
0.8192900782821367
[192.51555555555555, 235.48333333333332]
0.8175336777785642
[192.41666666666666, 235.29777777777778]
0.8177581126515809
[192.41, 235.44555555555556]
0.817216530360876
[192.22222222222223, 235.23777777777778]
0.8171401041027047
[192.50666666666666, 235.5311111111111]
0.8173301002934267
[192.3088888888889, 235.28444444444443]
0.8173463797956139
[192.27, 235.32222222222222]
0.8170499079276642
[192.0077777777778, 235.33777777777777]
0.8158816641800911
[192.32222222222222, 235.2811111111111]
0.8174146293086757
[192.55, 235.61333333333334]
0.8172287929375813
[192.54333333333332, 235.44555555555556]
0.8177828325491621
[192.54333333333332, 235.33444444444444]
0.8181689416008423
[192.45666666666668, 235.36444444444444]
0.817696432955039
[192.75222222222223, 235.42]
0.8187589084284354
[192.17666666666668, 235.27444444444444]
0.8168191284882431
[192.38, 235.33777777777777]
0.8174633151404128
[192.14, 235.17222222222222]
0.8170182608490232
[192.57111111111112, 235.29777777777778]
0.8184144913301349
[192.5822222222222, 235.23666666666668]
0.8186743374284998
[192.55777777777777, 235.5011111111111]
0.8176512495812711
[192.8088888888889, 235.34444444444443]
0.8192625466219726
[193.13222222222223, 235.25444444444443]
0.8209503657977888
[192.99333333333334, 235.26777777777778]
0.8203134962052696
[192.6822222222222, 235.45222222222222]
0.8183495590046577
[192.64222222222222, 235.37555555555556]
0.8184461711307697
[192.45444444444445, 235.30666666666667]
0.8178877682079178
[192.43666666666667, 235.25222222222223]
0.8180014830418416
[192.62, 235.2588888888889]
0.818757586205268
[192.68555555555557, 235.26444444444445]
0.8190168982421673
[192.20555555555555, 235.2111111111111]
0.8171618876659266
[192.4322222222222, 235.21]
0.8181294257141372
[192.60555555555555, 235.21666666666667]
0.8188431469803255
[192.60111111111112, 235.09444444444443]
0.8192499468298793
[192.64555555555555, 235.12222222222223]
0.8193421860970653
[192.83, 235.17444444444445]
0.8199445328999277
[192.99, 235.3188888888889]
0.8201211594668228
[192.9, 235.3411111111111]
0.8196612954246083
[192.94222222222223, 235.22555555555556]
0.8202434542732036
[192.71777777777777, 235.19]
0.8194131458726042
[192.89, 235.2811111111111]
0.8198278182599538
[192.67777777777778, 235.26555555555555]
0.8189799706242119
[192.7188888888889, 235.2188888888889]
0.8193172317038031
[192.95777777777778, 235.42222222222222]
0.8196243156503682
[192.8188888888889, 235.25333333333333]
0.819622345651024
[192.87444444444444, 235.25333333333333]
0.8198584976951561
[192.49666666666667, 235.20444444444445]
0.8184227433344041
[192.96555555555557, 235.4488888888889]
0.8195645197825431
[192.80555555555554, 235.22555555555556]
0.819662451642159
[192.7888888888889, 235.14888888888888]
0.8198588128561574
[192.7711111111111, 235.24666666666667]
0.8194424764549739
[192.45777777777778, 235.13444444444445]
0.8185009994282231
[192.59444444444443, 235.1211111111111]
0.8191286760014933
[192.82777777777778, 235.24555555555557]
0.8196872298921694
[192.63777777777779, 235.24555555555557]
0.8188795631987379
[192.76444444444445, 235.17666666666668]
0.8196580348579555
[192.61333333333334, 235.10888888888888]
0.8192515997315665
[192.77333333333334, 235.11222222222221]
0.8199205107726335
[192.54666666666665, 235.07888888888888]
0.8190725572030193
[192.85, 235.22666666666666]
0.8198475229565809
[192.59333333333333, 235.08666666666667]
0.8192439667640302
[192.73222222222222, 235.16222222222223]
0.8195713597233115
[192.91, 235.17]
0.8203002083599099
[192.84222222222223, 235.25555555555556]
0.8197137864261087
[192.81222222222223, 235.18777777777777]
0.8198224586500622
[193.21777777777777, 235.19222222222223]
0.8215313242595891
[192.67111111111112, 235.21666666666667]
0.819121849831125
[192.70111111111112, 235.2588888888889]
0.819102360047796
[192.38333333333333, 235.16333333333333]
0.8180838849593899
[192.34222222222223, 235.22555555555556]
0.8176927110149597
[192.8322222222222, 235.1511111111111]
0.8200353437033396
[192.9688888888889, 235.33333333333334]
0.8199811142587347
[192.5311111111111, 235.06333333333333]
0.8190605841451712
[192.56555555555556, 235.16444444444446]
0.8188548911400061
[192.8011111111111, 235.08777777777777]
0.8201239253423072
[192.84, 235.10888888888888]
0.8202156920197734
[193.1511111111111, 235.1977777777778]
0.8212284696567428
[192.95444444444445, 235.07]
0.8208382373099267
[192.80444444444444, 235.19444444444446]
0.8197661509389393
[192.96666666666667, 235.20444444444445]
0.8204210048940874
[192.77333333333334, 235.10333333333332]
0.8199515106832457
[192.69666666666666, 235.08777777777777]
0.8196796468458589
[192.89, 235.12222222222223]
0.8203818345068757
[192.87444444444444, 235.14444444444445]
0.8202381514908094
[192.63555555555556, 235.2888888888889]
0.8187193048734416
[192.83444444444444, 235.21]
0.8198394815035264
[192.63555555555556, 235.11444444444444]
0.8193267581272478
[192.97444444444446, 235.13333333333333]
0.8207022020602969
[192.92, 235.15444444444444]
0.8203969967728065
[192.82, 235.22]
0.8197432191140209
[192.72, 235.12444444444444]
0.8196510594862295
[192.9111111111111, 235.11777777777777]
0.8204871317448466
[192.54666666666665, 235.15333333333334]
0.8188132565985314
[192.88444444444445, 235.20888888888888]
0.8200559313706965
[193.06333333333333, 235.1977777777778]
0.820855261293096
[192.9788888888889, 235.11666666666667]
0.8207792821530682
[193.11111111111111, 235.15666666666667]
0.8212019410227697
[192.93, 235.25444444444443]
0.8200907764170238
[193.12666666666667, 235.1988888888889]
0.8211206591112014
[192.6911111111111, 235.14222222222222]
0.8194662332016557
[193.20444444444445, 235.15666666666667]
0.8215988395443227
[192.82333333333332, 235.0811111111111]
0.8202417132620892
[192.80666666666667, 235.16333333333333]
0.8198840522190252
[192.84222222222223, 235.19333333333333]
0.8199306480720354
[192.80444444444444, 235.14333333333335]
0.8199443365512288
[192.7577777777778, 235.08333333333334]
0.8199550986647761
[192.90333333333334, 235.19333333333333]
0.8201904815896143
[192.8788888888889, 235.09777777777776]
0.8204198725825662
[193.0, 235.20222222222222]
0.8205704783590481
[192.8188888888889, 235.17777777777778]
0.819885665690258
[192.89555555555555, 235.3311111111111]
0.8196772396339909
[193.0888888888889, 235.19222222222223]
0.8209833091608283
[192.76888888888888, 234.96444444444444]
0.8204172735354758
[193.04222222222222, 234.96555555555557]
0.8215766849987468
[192.84333333333333, 235.20444444444445]
0.8198966383855181
[192.43555555555557, 235.07444444444445]
0.8186153795251623
[192.7722222222222, 235.23555555555555]
0.8194859053808948
[192.5588888888889, 235.1988888888889]
0.8187066265430204
[192.7111111111111, 235.19444444444446]
0.8193693161686547
[192.98111111111112, 235.07888888888888]
0.8209206365711748
[193.2722222222222, 235.2122222222222]
0.8216929392369067
[193.35444444444445, 235.29777777777778]
0.8217436062105701
[193.21333333333334, 235.14111111111112]
0.8216909940603042
[193.71555555555557, 235.22666666666666]
0.823527188905264
[193.11888888888888, 235.12666666666667]
0.821339797933974
[192.77555555555554, 235.22444444444446]
0.8195387856515289
[192.8088888888889, 235.2588888888889]
0.8195604841947169
[192.68444444444444, 235.21777777777777]
0.8191746655581589
[192.7811111111111, 235.19444444444446]
0.8196669422463682
[193.44666666666666, 235.22666666666666]
0.822384083437252
[193.24333333333334, 235.01]
0.8222770662241323
[193.37, 235.10444444444445]
0.8224855147121374
[193.35888888888888, 235.18]
0.8221740321833867
[192.95555555555555, 235.17777777777778]
0.8204667863554758
[193.02555555555554, 235.34555555555556]
0.8201793108006665
[192.72555555555556, 235.08]
0.8198296560981604
[192.72666666666666, 235.04111111111112]
0.8199700288838359
[192.68666666666667, 235.0988888888889]
0.8195983723161412
[192.5888888888889, 235.07]
0.819283144973365
[192.4611111111111, 235.14111111111112]
0.8184919693611874
[192.71, 235.04333333333332]
0.8198913675492463
[192.6688888888889, 235.17]
0.8192749453114296
[192.9111111111111, 235.09777777777776]
0.8205569313949751
[192.77, 235.0811111111111]
0.8200148412131983
[192.85888888888888, 235.0822222222222]
0.8203890837248433
[193.03222222222223, 235.05555555555554]
0.8212195698416451
[193.01555555555555, 235.04444444444445]
0.8211874822728562
[192.67, 235.09777777777776]
0.81953135338488
[193.1288888888889, 235.26111111111112]
0.820912933619855
[192.93777777777777, 235.05]
0.8208371741237088
[193.12333333333333, 235.10444444444445]
0.8214363356238834
[192.82111111111112, 235.20222222222222]
0.8198099035345472
[192.9088888888889, 235.09444444444443]
0.8205591133586975
[192.95333333333335, 235.01777777777778]
0.8210159042341951
[192.98666666666668, 235.07333333333332]
0.8209636709112051
[192.9188888888889, 235.12666666666667]
0.8204891925865019
[192.74444444444444, 235.09333333333333]
0.8198635057471264
[193.01777777777778, 235.07]
0.8211076606022792
[192.6, 235.14777777777778]
0.8190594094493769
[192.9111111111111, 235.00333333333333]
0.8208867013706661
[192.81444444444443, 234.9088888888889]
0.8208052294506617
[193.0088888888889, 235.06666666666666]
0.8210814898846663
[193.30333333333334, 235.21666666666667]
0.8218096790193439
[192.73666666666668, 235.06555555555556]
0.819927301603808
[193.0688888888889, 235.09444444444443]
0.8212396909043648
[192.82555555555555, 235.0888888888889]
0.8202240287361754
[192.9388888888889, 235.07555555555555]
0.8207526658095743
[193.07777777777778, 235.04777777777778]
0.8214405581843881
[192.9788888888889, 235.01888888888888]
0.821120760979023
[192.97, 235.14444444444445]
0.820644521098143
[192.87222222222223, 235.0222222222222]
0.8206552571860818
[192.84, 235.2511111111111]
0.8197198265683006
[192.89555555555555, 235.04555555555555]
0.8206730610141769
[192.91666666666666, 235.0677777777778]
0.8206852869857865
[193.10777777777778, 234.99666666666667]
0.82174688057041
[192.95777777777778, 235.13777777777779]
0.8206158091709824
[193.1, 235.17]
0.8211081345409704
[192.71777777777777, 234.99777777777777]
0.8200834050440193
[193.16666666666666, 235.0988888888889]
0.8216400663550562
[192.90222222222224, 235.03222222222223]
0.8207479825461285
[192.94555555555556, 235.07444444444445]
0.8207849050182684
[192.95888888888888, 235.1]
0.8207523985065457
[193.01333333333332, 235.06666666666666]
0.8211003970504821
[193.0988888888889, 235.18555555555557]
0.8210491007100776
[192.77444444444444, 235.08333333333334]
0.8200259955098664
[192.98, 235.2111111111111]
0.8204544380934384
[193.10666666666665, 235.15666666666667]
0.8211830410931719
[192.8111111111111, 234.9477777777778]
0.8206551810567833
[192.73888888888888, 235.16]
0.8196074540265729
[192.87666666666667, 235.0911111111111]
0.8204336852851377
[192.83444444444444, 234.90777777777777]
0.8208942516448535
[192.47666666666666, 234.91666666666666]
0.8193401915572899
[192.98888888888888, 235.0311111111111]
0.8211206081464393
[192.8788888888889, 235.0611111111111]
0.8205478480773322
[192.88111111111112, 234.98333333333332]
0.8208289003948271
[192.8711111111111, 235.05777777777777]
0.8205263954016033
[193.08, 234.99555555555557]
0.8216325604266748
[193.13777777777779, 235.11333333333334]
0.8214667158155405
[193.2788888888889, 235.0222222222222]
0.8223855900151287
[192.5, 234.95777777777778]
0.8192961383132666
[192.82666666666665, 235.08666666666667]
0.8202365085216798
[192.79333333333332, 235.17333333333335]
0.8197924934799863
[192.4777777777778, 235.12555555555556]
0.8186170036812483
[192.69, 235.0688888888889]
0.8197171514733269
[192.76666666666668, 235.10777777777778]
0.8199076546453873
[192.65333333333334, 234.98222222222222]
0.8198634412059541
[192.65333333333334, 235.08666666666667]
0.8194991917874259
[192.7422222222222, 234.9922222222222]
0.8202068153555909
[192.86666666666667, 235.06666666666666]
0.8204764605785593
[192.85777777777778, 235.15222222222224]
0.8201401456267099
[192.5688888888889, 235.1822222222222]
0.8188071660745333
[192.47333333333333, 234.93333333333334]
0.8192678774120318
[192.65333333333334, 235.0211111111111]
0.8197277785919941
[192.70333333333335, 235.03222222222223]
0.8199017628788487
[192.82555555555555, 235.13111111111112]
0.8200767420540785
[193.2722222222222, 235.02666666666667]
0.8223416728125413
[192.73666666666668, 234.9988888888889]
0.82015990619341
[193.0077777777778, 235.0288888888889]
0.8212087402967011
[192.85555555555555, 235.06222222222223]
0.8204447049480988
[192.67, 235.00222222222223]
0.8198645875689118
[192.89555555555555, 235.22666666666666]
0.8200411895854589
[192.76777777777778, 235.04444444444445]
0.8201333081213955
[192.88555555555556, 235.0611111111111]
0.8205762094963485
[192.5911111111111, 235.04444444444445]
0.8193816772241655
[192.48555555555555, 235.11]
0.8187042471845329
[192.25222222222223, 235.05777777777777]
0.8178934729995463
[192.62222222222223, 234.96555555555557]
0.8197891889591382
[192.83555555555554, 235.04222222222222]
0.8204294263914758
[192.98222222222222, 235.16555555555556]
0.8206228236372485
[192.8188888888889, 235.0377777777778]
0.8203740297068083
[192.76111111111112, 235.01666666666668]
0.8202018769354419
[192.96, 234.89888888888888]
0.8214598243215758
[192.99333333333334, 235.0611111111111]
0.8210347191037792
[193.01555555555555, 235.11333333333334]
0.8209468719577319
[192.85777777777778, 235.14666666666668]
0.820159522189461
[192.5011111111111, 235.07]
0.818909733743613
[193.00666666666666, 235.04]
0.821165191740413
[192.72666666666666, 235.04111111111112]
0.8199700288838359
[192.90444444444444, 235.12777777777777]
0.8204238829950617
[192.95777777777778, 235.10111111111112]
0.820743793450572
[193.02777777777777, 235.01333333333332]
0.8213481977381898
[192.67444444444445, 235.0511111111111]
0.8197129702286973
[192.82555555555555, 234.99333333333334]
0.8205575571883835
[192.97666666666666, 235.03444444444443]
0.8210569609182579
^X[192.96444444444444, 235.05333333333334]
0.8209389831149432
[192.91555555555556, 235.17333333333335]
0.8203122047095286
[192.87, 235.1]
0.8203743088047639
[192.69666666666666, 235.0511111111111]
0.8198075123141065
[192.86444444444444, 234.9911111111111]
0.8207308077846917
[192.9488888888889, 235.07888888888888]
0.8207835667459151
[192.45222222222222, 234.9311111111111]
0.819185766040163
[192.92888888888888, 234.98222222222222]
0.8210361067503924
[192.93333333333334, 235.06333333333333]
0.8207717069158667
[193.09333333333333, 234.9988888888889]
0.8216776438659285
[192.9622222222222, 235.23555555555555]
0.8202936064087061
[192.87333333333333, 235.01888888888888]
0.820671624502995
[193.06, 234.98222222222222]
0.8215940685820204
[193.10222222222222, 235.03555555555556]
0.8215872775750241
[193.23333333333332, 235.2488888888889]
0.8213995579150214
[193.20777777777778, 235.07555555555555]
0.8218965060878772
[192.91666666666666, 235.03444444444443]
0.8208016791865023
^C[193.07888888888888, 235.03333333333333]
0.821495768921666
Traceback (most recent call last):
  File "camera_detect_color.py", line 171, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ python3 camera_detect_color.py
192.168.1.171 - - [09/Nov/2021 18:42:10] "GET /index.html HTTP/1.1" 200 -
192.168.1.171 - - [09/Nov/2021 18:42:11] "GET /stream.mjpg HTTP/1.1" 200 -
[253.8011111111111, 236.56555555555556]
1.072857417957907
[253.86333333333334, 236.40444444444444]
1.073851779436371
[253.74, 236.14333333333335]
1.0745168894597914
[253.67222222222222, 236.0377777777778]
1.074710262952258
[253.70555555555555, 235.9622222222222]
1.075195652788111
[253.6888888888889, 235.93]
1.0752718555880512
[253.6588888888889, 235.91555555555556]
1.0752105273073227
[253.56333333333333, 235.7188888888889]
1.0757022253437474
[253.61666666666667, 235.86888888888888]
1.075244250572352
[253.65, 235.79222222222222]
1.0757352282847894
[253.67222222222222, 235.84777777777776]
1.0755760542346051
[253.71555555555557, 235.86111111111111]
1.0756989753857025
[253.61888888888888, 235.75333333333333]
1.0757807124207033
[253.70777777777778, 235.8322222222222]
1.075797765831641
[253.66222222222223, 235.88111111111112]
1.0753816659051405
[253.75555555555556, 235.69222222222223]
1.076639496895669
[253.64333333333335, 235.7877777777778]
1.0757272311730417
[253.67444444444445, 235.7722222222222]
1.075930158580551
[253.66666666666666, 235.70222222222222]
1.0762166952652121
[253.60555555555555, 235.60111111111112]
1.076419183082517
[253.60777777777778, 235.62]
1.0763423214403607
[253.62666666666667, 235.47666666666666]
1.0770777005506562
[253.58444444444444, 235.54444444444445]
1.0765885183263362
[253.63333333333333, 235.63222222222223]
1.0763949469276508
[253.62666666666667, 235.60555555555555]
1.0764884812186093
[253.6288888888889, 235.44222222222223]
1.0772447120784527
[253.61222222222221, 235.38777777777779]
1.0774230702056653
[253.54555555555555, 235.42333333333335]
1.0769771711479557
[253.6588888888889, 235.59333333333333]
1.0766810983144213
[253.6822222222222, 235.57555555555555]
1.0768613985604996
[253.63444444444445, 235.45555555555555]
1.0772073049879667
[253.58444444444444, 235.5388888888889]
1.0766139113616529
[253.60222222222222, 235.63111111111112]
1.0762679895127978
[253.61, 235.50666666666666]
1.0768697276793298
[253.59555555555556, 235.5077777777778]
1.076803313879702
[253.5988888888889, 235.5388888888889]
1.0766752364554095
[253.63444444444445, 235.51666666666668]
1.0769277946830844
[253.62333333333333, 235.63111111111112]
1.07635758341664
[253.7211111111111, 235.61222222222221]
1.0768588688570202
[253.67777777777778, 235.56333333333333]
1.0768984042979712
[253.6977777777778, 235.55]
1.0770442699120262
[253.73222222222222, 235.51222222222222]
1.0773632885294937
[253.65777777777777, 235.55555555555554]
1.0768490566037736
[253.6211111111111, 235.62666666666667]
1.0763684548060963
[253.64666666666668, 235.5311111111111]
1.0769136419817151
[253.6911111111111, 235.42777777777778]
1.077575099700309
[253.60555555555555, 235.49555555555557]
1.0769016636313022
[253.6688888888889, 235.51222222222222]
1.0770943711343124
[253.65666666666667, 235.4188888888889]
1.0774694752143932
[253.5811111111111, 235.57111111111112]
1.0764524984199155
[253.70777777777778, 235.4311111111111]
1.0776306350524805
[253.6888888888889, 235.41]
1.0776470366122464
[253.61333333333334, 235.43444444444444]
1.0772142280700927
[253.6888888888889, 235.42333333333335]
1.0775860034642086
[253.62333333333333, 235.41666666666666]
1.077338053097345
[253.6688888888889, 235.47222222222223]
1.0772773386811372
[253.62222222222223, 235.45222222222222]
1.077170645613406
[253.67444444444445, 235.48333333333332]
1.0772501002665913
[253.6511111111111, 235.37222222222223]
1.0776594991384802
[253.71333333333334, 235.45333333333335]
1.0775525227929101
[253.62, 235.35444444444445]
1.0776087130993914
[253.66444444444446, 235.37]
1.0777263221499955
[253.59444444444443, 235.47]
1.0769713528026688
[253.60555555555555, 235.40666666666667]
1.0773082986415943
[253.73, 235.36777777777777]
1.0780150214085757
[253.63444444444445, 235.39333333333335]
1.0774920464093196
[253.66555555555556, 235.38444444444445]
1.0776649075271658
[253.67888888888888, 235.35555555555555]
1.0778538381644793
[253.68333333333334, 235.24666666666667]
1.0783716382803865
[253.6511111111111, 235.40222222222224]
1.0775221606517449
[253.56, 235.39333333333335]
1.0771757908748478
[253.5888888888889, 235.2811111111111]
1.077812356849726
[253.59222222222223, 235.38222222222223]
1.0773635316553691
[253.60111111111112, 235.4011111111111]
1.0773148432226791
[253.59222222222223, 235.25444444444443]
1.0779486985722315
[253.64111111111112, 235.46555555555557]
1.077189869714372
[253.60555555555555, 235.38333333333333]
1.077415091222356
[253.63222222222223, 235.42333333333335]
1.0773453023159225
[253.66, 235.37666666666667]
1.0776769150156487
[253.61555555555555, 235.33666666666667]
1.0776712322299495
[253.62222222222223, 235.41444444444446]
1.0773435029475205
[253.70222222222222, 235.27444444444444]
1.0783246043627537
[253.64888888888888, 235.37666666666667]
1.0776297093547458
[253.58666666666667, 235.30444444444444]
1.0776960344518214
[253.57111111111112, 235.3011111111111]
1.0776451922123427
[253.64888888888888, 235.3088888888889]
1.0779401070932768
[253.58777777777777, 235.4488888888889]
1.0770396028390214
[253.64777777777778, 235.42444444444445]
1.0774062921814973
[253.65555555555557, 235.46444444444444]
1.0772562972470485
[253.67555555555555, 235.38111111111112]
1.0777226530968689
[253.70444444444445, 235.30555555555554]
1.078191476803211
[253.61111111111111, 235.33666666666667]
1.0776523467561838
[253.66, 235.26444444444445]
1.0781909718614513
[253.61333333333334, 235.34333333333333]
1.0776312621276716
[253.59666666666666, 235.30555555555554]
1.0777334435131627
[253.6211111111111, 235.38333333333333]
1.0774811772758386
[253.64111111111112, 235.39333333333335]
1.0775203678004663
[253.63777777777779, 235.35444444444445]
1.0776842492883074
[253.6822222222222, 235.28222222222223]
1.078203953644323
[253.61777777777777, 235.35333333333332]
1.0776043584586767
[253.72333333333333, 235.2788888888889]
1.078393962720365
[253.66444444444446, 235.35111111111112]
1.0778128186728104
[253.6677777777778, 235.35444444444445]
1.0778117166071033
[253.68333333333334, 235.2422222222222]
1.0783920120159836
[253.6611111111111, 235.31333333333333]
1.077971687867713
[253.62, 235.36333333333334]
1.0775680154088005
[253.6988888888889, 235.2577777777778]
1.078386828632422
[253.6288888888889, 235.03222222222223]
1.079123902632736
[253.5677777777778, 235.11888888888888]
1.0784662133105238
[253.67333333333335, 235.22444444444446]
1.078431002068946
[253.68777777777777, 235.37555555555556]
1.077800016994118
[253.66444444444446, 235.16333333333333]
1.0786734515490417
[253.60222222222222, 235.32444444444445]
1.0776705446853516
[253.66222222222223, 235.19]
1.0785416991463168
[253.64888888888888, 235.11555555555555]
1.078826487211962
[253.63666666666666, 235.19666666666666]
1.0784024716903584
[253.58, 235.18555555555557]
1.0782124752559445
[253.63666666666666, 235.1211111111111]
1.0787490135107676
[253.58333333333334, 235.17777777777778]
1.0782623074742512
[253.72, 235.14333333333335]
1.0790014601023488
[253.59444444444443, 235.11222222222221]
1.078610214507493
[253.61555555555555, 235.17111111111112]
1.0784298902926475
[253.6588888888889, 235.07777777777778]
1.0790423973153094
[253.64888888888888, 235.22222222222223]
1.0783372697213036
[253.59555555555556, 235.19222222222223]
1.0782480524204787
[253.7122222222222, 235.21666666666667]
1.0786319941425162
[253.65333333333334, 235.02333333333334]
1.0792687250911257
[253.51555555555555, 235.17333333333335]
1.0779944816116718
[253.67222222222222, 235.2]
1.0785383597883598
[253.67444444444445, 235.22555555555556]
1.0784306315923724
[253.55444444444444, 235.12777777777777]
1.0783687356756375
[253.6611111111111, 235.2888888888889]
1.0780836796373252
[253.61444444444444, 235.14888888888888]
1.0785270797697912
[253.57555555555555, 235.10444444444445]
1.0785655547888882
[253.64333333333335, 235.18444444444444]
1.0784868613759415
[253.66333333333333, 235.16]
1.0786840165561036
[253.62222222222223, 235.0388888888889]
1.0790649301534025
[253.65444444444444, 235.18777777777777]
1.0785188194775805
[253.66333333333333, 235.11777777777777]
1.0788777255843407
[253.67, 235.09777777777776]
1.078997863772993
[253.65444444444444, 235.32111111111112]
1.0779077289188768
[253.62333333333333, 235.13888888888889]
1.078610750147667
[253.67666666666668, 234.96]
1.0796589490409716
[253.57666666666665, 235.11222222222221]
1.0785346004981073
[253.67333333333335, 235.07222222222222]
1.0791293455911894
[253.6677777777778, 235.13333333333333]
1.0788252528116435
[253.61777777777777, 235.10111111111112]
1.0787604387710252
[253.62333333333333, 235.0822222222222]
1.0788707497140482
[253.65222222222224, 235.12]
1.0788202714453141
[253.70111111111112, 235.28]
1.0782944198874156
[253.63, 235.08444444444444]
1.0788889098952623
[253.60111111111112, 234.90222222222224]
1.0796028607647625
[253.59222222222223, 234.9622222222222]
1.0792893420218854
[253.58, 235.0677777777778]
1.0787527001668549
[253.56666666666666, 235.0]
1.0790070921985815
[253.54, 234.93]
1.0792150853445706
[253.54666666666665, 235.04222222222222]
1.0787281717705566
[253.54777777777778, 235.03222222222223]
1.0787787962879793
[253.6611111111111, 235.10666666666665]
1.0789192612336718
[253.51333333333332, 235.14111111111112]
1.0781327524370707
[253.61777777777777, 235.0088888888889]
1.0791837660986818
[253.59666666666666, 235.0311111111111]
1.078991906508831
[253.64111111111112, 235.2111111111111]
1.0783551419528556
[253.68777777777777, 235.02555555555554]
1.0794050765165017
[253.66666666666666, 234.9688888888889]
1.079575546644473
[253.61555555555555, 235.05666666666667]
1.0789549564880336
[253.6288888888889, 235.11333333333334]
1.078751618604739
[253.59, 235.01111111111112]
1.0790553638125857
[253.52333333333334, 234.83]
1.0796036849352013
[253.55777777777777, 234.70555555555555]
1.0803228631618813
[253.58666666666667, 234.8111111111111]
1.0799602517389866
[253.47555555555556, 234.62777777777777]
1.0803305472024247
[253.44555555555556, 234.71444444444444]
1.0798038278191466
[253.5311111111111, 234.6822222222222]
1.0803166456768964
[253.51444444444445, 234.7722222222222]
1.0798315151801983
[253.5377777777778, 234.62]
1.0806315649892497
[253.49444444444444, 234.76]
1.0798025406561784
[253.58444444444444, 234.65666666666667]
1.0806615812226847
[253.46, 234.63555555555556]
1.0802284393764325
[253.43777777777777, 234.61222222222221]
1.0802411544345043
[253.55333333333334, 234.76444444444445]
1.0800329408201128
[253.51777777777778, 234.69444444444446]
1.0802035743875014
[253.52, 234.4711111111111]
1.0812419440442793
[253.60555555555555, 234.54555555555555]
1.0812635308942589
[253.53444444444443, 234.89222222222222]
1.079365004280923
[253.51888888888888, 234.69444444444446]
1.080208308675583
[253.51444444444445, 234.59444444444443]
1.0806498212044426
[253.4988888888889, 234.67444444444445]
1.080215144384419
[253.40777777777777, 234.59222222222223]
1.0802053681802464
[253.52444444444444, 234.65]
1.080436584037692
[253.48111111111112, 234.68777777777777]
1.0800780232838902
[253.51333333333332, 234.73777777777778]
1.079985231747955
[253.5688888888889, 234.62666666666667]
1.0807334583546437
[253.5, 234.72222222222223]
1.08
[253.50555555555556, 234.60777777777778]
1.0805505169384362
[253.51111111111112, 234.68]
1.0802416529363863
[253.4911111111111, 234.5677777777778]
1.0806732003543158
[253.5311111111111, 234.6688888888889]
1.0803780267232317
[253.4988888888889, 234.57555555555555]
1.0806705254881157
[253.44333333333333, 234.6888888888889]
1.079911940157182
[253.42111111111112, 234.71555555555557]
1.079694571206756
[253.47333333333333, 234.62]
1.0803568891540931
[253.5088888888889, 234.54333333333332]
1.0808616270862055
[253.51444444444445, 234.64111111111112]
1.080434895845665
[253.46555555555557, 234.50666666666666]
1.0808458418618756
[253.45222222222222, 234.51111111111112]
1.0807685018478157
[253.4488888888889, 234.53666666666666]
1.0806365268638403
[253.49555555555557, 234.48]
1.0810967057128777
[253.4911111111111, 234.54111111111112]
1.0807960698669268
[253.5588888888889, 234.59444444444443]
1.080839273450636
[253.49777777777777, 234.61666666666667]
1.0804764272690677
[253.5822222222222, 234.59666666666666]
1.080928496663304
[253.49777777777777, 234.64555555555555]
1.080343402105303
[253.51222222222222, 234.68777777777777]
1.0802105871157424
[253.56444444444443, 234.78555555555556]
1.0799831524748351
[253.59666666666666, 235.0077777777778]
1.0790990369113078
[253.42222222222222, 235.0]
1.0783924349881797
[253.49777777777777, 234.98777777777778]
1.0787700542344991
[253.59333333333333, 235.02555555555554]
1.0790032289632807
[253.46, 234.81]
1.0794259188279887
[253.56666666666666, 234.6911111111111]
1.0804272282243328
[253.52444444444444, 234.72333333333333]
1.080099029117022
[253.59777777777776, 234.6977777777778]
1.0805290965212944
[253.49666666666667, 234.47222222222223]
1.0811373060063973
[253.54555555555555, 234.57222222222222]
1.0808848258058403
[253.57777777777778, 234.65444444444444]
1.080643404722784
[253.61222222222221, 234.63111111111112]
1.0808976738899831
[253.51333333333332, 234.69444444444446]
1.0801846372351755
[253.5511111111111, 234.6911111111111]
1.080360947249813
[253.5511111111111, 234.62666666666667]
1.0806576878634615
[253.54444444444445, 234.52777777777777]
1.0810849224209405
[253.55, 234.56333333333333]
1.080944734186929
[253.5311111111111, 234.51]
1.0811100213684326
[253.52444444444444, 234.5311111111111]
1.0809842806924455
[253.5888888888889, 234.58555555555554]
1.0810081135998713
[253.62666666666667, 234.60555555555555]
1.081076985010301
[253.54111111111112, 234.74666666666667]
1.0800626680298384
[253.59777777777776, 234.62777777777777]
1.080851466862406
[253.5377777777778, 234.57]
1.0808619080776647
[253.55333333333334, 234.61333333333334]
1.0807285746760626
[253.49, 234.61666666666667]
1.08044327626625
[253.5588888888889, 234.63888888888889]
1.080634544808808
[253.5811111111111, 234.68]
1.080539931443289
[253.4322222222222, 234.61333333333334]
1.08021235886944
[253.6, 234.63555555555556]
1.0808251093895023
[253.58333333333334, 234.77444444444444]
1.0801147200386187
[253.54, 234.64666666666668]
1.0805182259851691
[253.54111111111112, 234.63555555555556]
1.0805741291459094
[253.55333333333334, 234.49666666666667]
1.0812662582268404
[253.56, 234.63333333333333]
1.0806648671686319
[253.53444444444443, 234.54333333333332]
1.080970585866625
[253.53222222222223, 234.49]
1.081206969261897
[253.47444444444446, 234.57444444444445]
1.080571436691503
[253.59555555555556, 234.59555555555556]
1.0809904516520157
[253.56666666666666, 234.47]
1.081446098292603
[253.60222222222222, 234.57111111111112]
1.0811315213581287
[253.4477777777778, 234.37222222222223]
1.081390001659279
[253.51444444444445, 234.53666666666666]
1.0809160377671343
[253.45666666666668, 234.39777777777778]
1.0813100237962059
[253.48555555555555, 234.36222222222221]
1.081597337454842
[253.38666666666666, 234.22666666666666]
1.081801104343371
[253.34666666666666, 234.07888888888888]
1.0823131802668615
[253.41222222222223, 234.28]
1.0816639159220687
[253.4188888888889, 234.24]
1.0818770871281116
[253.39777777777778, 234.14]
1.0822489868359861
[253.44, 234.1811111111111]
1.0822392924754345
[253.48666666666668, 234.21666666666667]
1.082274247491639
[253.40555555555557, 234.14111111111112]
1.0822770693836101
[253.40333333333334, 234.16555555555556]
1.0821546009708232
[253.43777777777777, 234.22222222222223]
1.0820398481973434
[253.5288888888889, 234.20888888888888]
1.0824904643528095
[253.37222222222223, 234.1588888888889]
1.0820525474155724
[253.41, 234.2811111111111]
1.0816493006976424
[253.49, 234.23333333333332]
1.0822114700441157
[253.43777777777777, 234.20111111111112]
1.0821373842993438
[253.39444444444445, 234.25333333333333]
1.081711157910714
[253.46, 234.2]
1.0822374039282665
[253.45666666666668, 234.19444444444446]
1.0822488435535524
[253.45666666666668, 234.2411111111111]
1.0820332326140683
[253.50222222222223, 234.1588888888889]
1.0826077259980165
[253.40333333333334, 234.13222222222223]
1.082308666992535
[253.44555555555556, 234.13222222222223]
1.0824890019409734
[253.38666666666666, 234.21444444444444]
1.0818575569397466
[253.49, 234.36666666666667]
1.081595790072536
[253.45444444444445, 234.2711111111111]
1.0818851852554496
[253.38888888888889, 234.07888888888888]
1.0824935563034306
[253.44, 234.3]
1.0816901408450703
[253.52444444444444, 234.35888888888888]
1.0817786585626035
[253.44333333333333, 234.08333333333334]
1.0827055891776431
[253.4111111111111, 234.00666666666666]
1.0829226137906802
[253.47444444444446, 234.14666666666668]
1.082545602945922
[253.55333333333334, 234.1811111111111]
1.0827232483879998
[253.45222222222222, 234.18777777777777]
1.0822606740080372
[253.52444444444444, 234.10777777777778]
1.0829390071999125
[253.44222222222223, 234.01111111111112]
1.0830349935900478
[253.5, 233.90666666666667]
1.0837656045146211
[253.45666666666668, 234.42666666666668]
1.0811767716983278
[253.38, 233.91222222222223]
1.0832268514779997
[253.34777777777776, 233.99555555555557]
1.0827033751828143
[253.45222222222222, 234.6911111111111]
1.0799395896260806
[253.45, 234.54666666666665]
1.0805951907225286
[253.4311111111111, 234.2488888888889]
1.0818882100709597
[253.4322222222222, 234.40777777777777]
1.0811596126408396
[253.45444444444445, 233.94666666666666]
1.083385576959611
[253.41222222222223, 233.73888888888888]
1.084167993725192
[253.38777777777779, 233.83777777777777]
1.0836049683066133
[253.37555555555556, 235.24555555555557]
1.0770684060626956
[253.35666666666665, 237.12777777777777]
1.0684394255324134
[253.22444444444446, 237.4322222222222]
1.0665125486103637
[253.48555555555555, 237.10888888888888]
1.0690681262242383
[253.53, 235.47333333333333]
1.076682426884856
[253.54111111111112, 232.1611111111111]
1.0920912201775588
[253.37333333333333, 231.45555555555555]
1.0946954058854592
[253.37666666666667, 233.76555555555555]
1.083892218699647
[253.50666666666666, 234.33555555555554]
1.0818105091464283
[253.53666666666666, 233.69333333333333]
1.084911850288127
[253.56, 234.01222222222222]
1.0835331487908988
[253.50555555555556, 236.61888888888888]
1.0713665200016906
[253.54777777777778, 237.27555555555554]
1.0685794294491169
[253.58777777777777, 236.30444444444444]
1.0731401111560417
[253.62555555555556, 235.3177777777778]
1.0778002323099733
[253.7111111111111, 235.5522222222222]
1.0770907135478334
[253.76444444444445, 235.9911111111111]
1.0753135711326227
[253.68666666666667, 235.14222222222222]
1.078864800498989
[253.8311111111111, 235.25666666666666]
1.0789539557268422
[253.89, 235.13222222222223]
1.0797754454940245
[253.92222222222222, 235.19222222222223]
1.0796369872397518
[253.87555555555556, 233.61111111111111]
1.0867443519619502
[253.91222222222223, 233.09666666666666]
1.0893000996248576
[253.92, 233.40666666666667]
1.0878866641912541
[253.95888888888888, 233.36222222222221]
1.0882605010808186
[253.90333333333334, 233.18333333333334]
1.0888571224358516
[253.95222222222222, 234.17111111111112]
1.084472892566689
[253.98333333333332, 233.9611111111111]
1.085579274808254
[253.96666666666667, 233.89888888888888]
1.0857968067873582
[253.9411111111111, 233.63444444444445]
1.0869164078736486
[253.97444444444446, 236.32111111111112]
1.0747006192139696
[254.09444444444443, 237.07111111111112]
1.0718068652631183
[254.0688888888889, 237.28222222222223]
1.0707455725483952
[254.11333333333334, 237.23444444444445]
1.0711485590906324
[254.09666666666666, 237.24777777777777]
1.0710181104611682
[254.0522222222222, 237.51]
1.0696485294186444
[254.15444444444444, 237.65444444444444]
1.0694285353617998
[254.09777777777776, 237.61333333333334]
1.0693750818322951
[254.09, 237.51111111111112]
1.0698025823353292
[254.13555555555556, 237.48666666666668]
1.0701045204876998
[254.09444444444443, 237.39777777777778]
1.0703320259480102
[254.3111111111111, 238.53555555555556]
1.0661350276222505
[254.29444444444445, 238.50666666666666]
1.0661942829457365
[254.29666666666665, 238.53]
1.0660993026733185
[254.29, 238.6677777777778]
1.0654559336315939
[254.23111111111112, 238.56555555555556]
1.0656656218416554
[254.33444444444444, 238.56]
1.0661235934123259
[254.2788888888889, 238.24666666666667]
1.0672925352808946
[254.30444444444444, 238.4911111111111]
1.0663057556303053
[254.1988888888889, 238.31222222222223]
1.0666632475603899
[254.26555555555555, 238.65222222222224]
1.0654229539031692
[254.22, 238.34444444444443]
1.0666076173604961
[254.2422222222222, 238.07111111111112]
1.0679255497890452
[254.28666666666666, 236.95]
1.0731659281142294
[254.22555555555556, 239.92444444444445]
1.0596067280440138
[254.24777777777777, 238.97222222222223]
1.0639218877135883
[254.0222222222222, 238.81555555555556]
1.0636753608084342
[254.18555555555557, 237.21444444444444]
1.071543329289485
[254.30666666666667, 239.04555555555555]
1.0638418525525122
[254.22555555555556, 239.11444444444444]
1.0631961450351528
[254.2111111111111, 237.72666666666666]
1.069342008095198
[254.15777777777777, 238.70222222222222]
1.064748268414389
[254.22444444444446, 236.57444444444445]
1.074606536819512
[254.18333333333334, 233.01888888888888]
1.090827162318744
[254.26111111111112, 237.08555555555554]
1.072444546506887
[254.20666666666668, 240.51111111111112]
1.056943546151714
[254.1688888888889, 242.41444444444446]
1.0484890430988252
[254.00555555555556, 240.51777777777778]
1.05607809078562
[253.94555555555556, 238.34777777777776]
1.0654412553085362
[253.6611111111111, 237.7722222222222]
1.066823991214748
[254.0088888888889, 235.66444444444446]
1.0778413752133447
[253.7722222222222, 231.7811111111111]
1.0948787888956535
[253.88888888888889, 233.02]
1.0895583593206115
[253.81666666666666, 234.62333333333333]
1.081804878741813
[253.79444444444445, 235.80333333333334]
1.076297102576064
[253.97222222222223, 236.61888888888888]
1.0733387491371498
[253.89888888888888, 235.2811111111111]
1.079129929682224
[253.88, 234.32666666666665]
1.0834447637201627
[253.8322222222222, 234.14666666666668]
1.084073610082949
[253.89222222222222, 233.36111111111111]
1.087980002380669
[253.80666666666667, 233.11555555555555]
1.0887590322396141
[253.92, 232.17777777777778]
1.0936447166921899
[253.83, 231.06]
1.0985458322513633
[253.83, 230.76444444444445]
1.0999528138361387
[253.84777777777776, 228.98666666666668]
1.1085701253833313
[253.86333333333334, 228.17666666666668]
1.1125735906388325
[253.88, 228.8322222222222]
1.1094591379419176
[254.09222222222223, 229.6911111111111]
1.106234459805923
[253.93666666666667, 227.0611111111111]
1.1183626532260038
[254.01, 227.20111111111112]
1.1179962930541223
[254.05666666666667, 229.51666666666668]
1.106920339844601
[254.05666666666667, 230.19]
1.103682465209899
[253.98444444444445, 229.78222222222223]
1.105326782847527
[253.99444444444444, 229.71]
1.1057178374665642
[254.0888888888889, 230.38222222222223]
1.1029014584458678
[254.05444444444444, 230.75222222222223]
1.100983739171887
[254.0911111111111, 230.58777777777777]
1.1019279233263786
[254.10666666666665, 230.32444444444445]
1.103255311348243
[254.14555555555555, 230.96666666666667]
1.1003559917255976
[254.18555555555557, 231.14666666666668]
1.099672165820643
[254.12555555555556, 231.20444444444445]
1.0991378481766978
[254.19, 231.79111111111112]
1.096633942438594
[254.11444444444444, 231.39222222222222]
1.0981978650967814
[254.13777777777779, 230.94555555555556]
1.100422899095987
[254.15777777777777, 231.51888888888888]
1.0977841980735914
[254.13333333333333, 231.69444444444446]
1.0968469008512167
[254.13111111111112, 231.6988888888889]
1.0968162701590667
[254.1811111111111, 231.7122222222222]
1.0969689413592532
[254.18666666666667, 232.95]
1.0911640552335982
[254.1988888888889, 234.13555555555556]
1.0856911001224363
[254.29555555555555, 234.22555555555556]
1.0856866363381925
[254.32222222222222, 233.28555555555556]
1.0901756073862743
[254.33777777777777, 232.88555555555556]
1.0921148680563175
[254.26888888888888, 233.36222222222221]
1.089588908039957
[254.30555555555554, 232.43666666666667]
1.0940853661451386
[254.2588888888889, 231.83777777777777]
1.0967103434393781
[254.30444444444444, 232.75222222222223]
1.0925972779827857
[254.38444444444445, 233.33444444444444]
1.0902138561244947
[254.35666666666665, 233.57333333333332]
1.0889799063820071
[254.35666666666665, 232.5]
1.0940071684587813
[254.26333333333332, 231.99444444444444]
1.0959888886228117
[254.2411111111111, 231.7122222222222]
1.0972278832459805
[254.3022222222222, 231.07111111111112]
1.1005366313400395
[254.32555555555555, 230.42]
1.10374774566251
[254.3488888888889, 228.94222222222223]
1.1109741419475074
[254.20333333333335, 227.07555555555555]
1.119465865497534
[254.38555555555556, 227.46444444444444]
1.1183530515147666
[254.35222222222222, 228.17777777777778]
1.1147107518504091
[254.36555555555555, 229.37333333333333]
1.1089587087523494
[254.37, 229.20666666666668]
1.109784473982723
[254.33666666666667, 229.38222222222223]
1.1087897928736121
[254.45333333333335, 230.13666666666666]
1.1056618531017801
[254.29333333333332, 228.25333333333333]
1.1140837665751504
[254.3311111111111, 227.59222222222223]
1.1174859519706297
[254.37555555555556, 227.6211111111111]
1.117539380744805
[254.37555555555556, 227.94]
1.1159759390872843
[254.32888888888888, 228.79333333333332]
1.111609701137368
[254.37, 229.4477777777778]
1.1086182767320572
[254.3111111111111, 229.58555555555554]
1.1076964772270808
[254.35, 229.52444444444444]
1.108160834963112
[254.2722222222222, 229.5]
1.1079399661099008
[254.34333333333333, 229.46555555555557]
1.1084161747829497
[254.3311111111111, 228.75444444444443]
1.1118083923081035
[254.38111111111112, 228.95888888888888]
1.1110340041637752
[254.38, 229.2711111111111]
1.1095161477920366
[254.2722222222222, 228.56333333333333]
1.1124803725687507
[254.25444444444443, 227.66555555555556]
1.1167892473852972
[254.29666666666665, 226.91555555555556]
1.1206665230335318
[254.29666666666665, 227.51888888888888]
1.1176947457353967
[254.3022222222222, 228.2288888888889]
1.1142420377204172
[254.2277777777778, 227.35222222222222]
1.1182110968296868
[254.28, 225.2188888888889]
1.1290349635169736
[254.39333333333335, 226.63555555555556]
1.1224775949640147
[254.28222222222223, 227.2711111111111]
1.1188497340425532
[254.2111111111111, 224.82555555555555]
1.1307038049253002
[254.2722222222222, 226.11888888888888]
1.1245067737227712
[254.23888888888888, 226.56]
1.1221702369742623
[254.3011111111111, 225.94555555555556]
1.1254972928581615
[254.23111111111112, 225.66222222222223]
1.1266002284633867
[254.3088888888889, 225.61666666666667]
1.1271724409642707
[254.18444444444444, 224.91666666666666]
1.130127207607756
[254.21666666666667, 224.98444444444445]
1.129929970467094
[254.27, 225.19222222222223]
1.129124254340736
[254.22444444444446, 226.11222222222221]
1.1243286273777526
[254.42444444444445, 227.34777777777776]
1.1190980045256167
[254.4322222222222, 226.44666666666666]
1.123585637039872
[254.42666666666668, 226.07666666666665]
1.1253999380741047
[254.35222222222222, 227.32888888888888]
1.1188732917554596
[254.3711111111111, 229.4]
1.108854015305628
[254.41444444444446, 230.28222222222223]
1.1047941173632354
[254.40777777777777, 231.38222222222223]
1.0995130712049326
[254.4311111111111, 231.60888888888888]
1.0985377648142463
[254.38888888888889, 233.64222222222222]
1.088796735749817
[254.38777777777779, 233.9611111111111]
1.0873079571628714
[254.4111111111111, 236.51]
1.075688601374619
[254.53, 236.75222222222223]
1.0750902255991965
[254.54, 238.34777777777776]
1.0679352766499
[254.4922222222222, 238.91]
1.0652221431594417
[254.53555555555556, 240.78666666666666]
1.0570998763312844
[254.45666666666668, 242.01666666666668]
1.0514014186350802
[254.4477777777778, 242.41666666666666]
1.0496298842672167
[254.38555555555556, 242.0811111111111]
1.0508277758143505
[254.51555555555555, 243.50555555555556]
1.045214574159841
[254.58, 245.43444444444444]
1.037262722338167
[254.58666666666667, 245.56222222222223]
1.036750133480539
[254.54111111111112, 245.15777777777777]
1.0382746711868094
[254.74, 248.2211111111111]
1.0262624273161474
[254.6811111111111, 244.9322222222222]
1.039802394313166
[254.4622222222222, 245.39222222222222]
1.0369612366596785
[254.60555555555555, 250.48555555555555]
1.0164480542235748
[254.73333333333332, 247.09333333333333]
1.0309194906108352
[254.6211111111111, 246.14333333333335]
1.0344424432015673
[254.63111111111112, 245.78555555555556]
1.0359889153598214
[254.5611111111111, 246.0311111111111]
1.0346704120526762
[254.5311111111111, 245.28222222222223]
1.0377071310146135
[254.57555555555555, 244.75444444444443]
1.0401263851751643
[254.52777777777777, 244.9188888888889]
1.0392329433327132
[254.53555555555556, 245.30333333333334]
1.0376359428009765
[254.51111111111112, 244.99555555555557]
1.0388397068427544
[254.49, 243.15555555555557]
1.0466139645403034
[254.4388888888889, 242.74555555555557]
1.0481711531507614
[254.51444444444445, 242.07555555555555]
1.0513843244533387
[254.38666666666666, 241.50555555555556]
1.0533367072301074
[254.2877777777778, 241.22333333333333]
1.0541591240943156
[254.42, 238.9011111111111]
1.0649594671900506
[254.35, 239.09]
1.0638253377389266
[254.43, 237.86]
1.0696628268729504
[254.42666666666668, 237.97444444444446]
1.0691344075227498
[254.39222222222222, 237.17222222222222]
1.0726054671944907
[254.35444444444445, 236.35333333333332]
1.0761618668847959
[254.42555555555555, 237.13444444444445]
1.0729169107070062
[254.45333333333335, 236.93444444444444]
1.0739398145759962
[254.42666666666668, 236.79888888888888]
1.074441978425199
[254.47444444444446, 237.16666666666666]
1.072977278051066
[254.5377777777778, 236.75666666666666]
1.0751028951431616
[254.41222222222223, 236.73888888888888]
1.0746532748222375
[254.48333333333332, 237.54555555555555]
1.0713032821774537
[254.4477777777778, 237.56444444444443]
1.0710684352316098
[254.55, 237.00333333333333]
1.074035526926485
[254.54, 236.39444444444445]
1.0767596531221357
[254.46555555555557, 235.77666666666667]
1.0792652180264752
[254.4911111111111, 235.4477777777778]
1.0808813466538936
[254.54555555555555, 235.16]
1.0824355994027708
[254.52444444444444, 235.3711111111111]
1.0813750389455894
[254.51777777777778, 236.45555555555555]
1.0763873878107233
[254.53666666666666, 236.98111111111112]
1.0740799782448671
[254.4477777777778, 236.55555555555554]
1.0756364490371066
[254.53, 236.6511111111111]
1.075549566638183
[254.45555555555555, 236.0077777777778]
1.0781659738144223
[254.37222222222223, 235.92555555555555]
1.078188505790433
[254.34666666666666, 236.13222222222223]
1.0771366324893303
[254.4688888888889, 236.66444444444446]
1.0752307533404069
[254.46444444444444, 236.31555555555556]
1.0767993831223788
[254.38333333333333, 235.32777777777778]
1.0809745272551288
[254.41, 235.85]
1.078694085223659
[254.41, 235.13]
1.0819971930421468
[254.36777777777777, 235.92]
1.078195056704721
[254.45888888888888, 237.9622222222222]
1.0693247294155002
[254.36, 238.17222222222222]
1.0679666907699845
[254.38222222222223, 237.3022222222222]
1.071975727155245
[253.61444444444444, 238.29777777777778]
1.0642753231251283
[254.16, 237.46444444444444]
1.0703076016058544
[254.29666666666665, 240.25444444444443]
1.0584472943037242
[254.75, 242.0077777777778]
1.0526521186187772
[254.5222222222222, 237.1288888888889]
1.0733497019904785
[254.23444444444445, 237.6822222222222]
1.0696401357554906
[254.32777777777778, 242.30444444444444]
1.0496207709309684
[254.48444444444445, 245.73777777777778]
1.0355934962290427
[254.43, 237.05333333333334]
1.0733027729343607
[254.5511111111111, 237.62]
1.071252887429977
[254.5611111111111, 236.64555555555555]
1.0757062836591058
[254.50666666666666, 235.05444444444444]
1.0827562408709093
[254.54777777777778, 235.28333333333333]
1.0818776416141296
[254.40222222222224, 237.07111111111112]
1.0731051161395548
[254.4622222222222, 237.9777777777778]
1.0692688392940517
[254.42222222222222, 239.8088888888889]
1.0609374131252662
[254.16222222222223, 241.98333333333332]
1.0503294533599652
[254.45, 242.59444444444443]
1.048869855955298
[254.4111111111111, 242.67333333333335]
1.0483686345613215
[254.41666666666666, 242.36555555555555]
1.0497228704115455
[254.46555555555557, 242.91555555555556]
1.047547387295082
[254.5588888888889, 243.14333333333335]
1.046949901521279
[254.65222222222224, 244.36111111111111]
1.0421143571672162
[254.63777777777779, 242.91666666666666]
1.048251572327044
[254.60444444444445, 242.36333333333334]
1.0505072732857463
[254.66, 242.68444444444444]
1.049346201743462
[254.64333333333335, 242.72333333333333]
1.0491094112638533
[254.6511111111111, 244.29666666666665]
1.042384714395521
[254.6588888888889, 246.46]
1.0332666107639734
[254.64555555555555, 246.13777777777779]
1.034565103555371
[254.52444444444444, 245.71777777777777]
1.035840575909128
[254.64, 246.23333333333332]
1.0341410586164885
[254.4688888888889, 243.46555555555557]
1.045194620274828
[254.67, 242.65]
1.0495363692561301
[254.69555555555556, 243.03222222222223]
1.0479908928399984
[254.4488888888889, 245.54555555555555]
1.0362593951789891
[254.1688888888889, 247.01555555555555]
1.0289590399165145
[254.42333333333335, 249.03222222222223]
1.0216482472147737
[254.48111111111112, 249.08555555555554]
1.021661455010996
[254.36333333333334, 248.09555555555556]
1.025263563322376
[254.38222222222223, 245.44555555555556]
1.0364099755093912
[254.44222222222223, 243.49777777777777]
1.0449467939474693
[254.40666666666667, 240.86111111111111]
1.0562380348287395
[254.38777777777779, 239.67444444444445]
1.0613888283644017
[253.91666666666666, 240.31444444444443]
1.056601767129178
[253.97333333333333, 243.26888888888888]
1.0440025212156645
[253.9622222222222, 241.64555555555555]
1.0509699697904644
[253.88, 239.09333333333333]
1.061844746821325
[253.75444444444443, 238.38666666666666]
1.064465760575722
[253.75, 240.0511111111111]
1.057066550641993
[253.67222222222222, 243.01888888888888]
1.0438374703383826
[253.57222222222222, 241.0388888888889]
1.0519971420010603
[253.47444444444446, 238.48]
1.0628750605687876
[253.5222222222222, 241.25555555555556]
1.0508451158292267
[253.46666666666667, 240.5011111111111]
1.053910584843683
[253.37444444444444, 238.86777777777777]
1.0607309483163627
[253.04222222222222, 235.00333333333333]
1.0767601405181013
[253.01666666666668, 233.18]
1.0850701889813306
[253.01666666666668, 236.1888888888889]
1.0712471185962271
[253.09444444444443, 236.99555555555557]
1.0679290750881403
[253.18333333333334, 235.26555555555555]
1.0761598005091173
[252.9411111111111, 235.87555555555556]
1.0723498266505878
[252.93666666666667, 239.7]
1.0552218050340705
[252.83777777777777, 237.62]
1.06404249548766
[252.69555555555556, 232.25444444444443]
1.0880117112936483
[252.53444444444443, 233.26111111111112]
1.0826255745826088
[252.89555555555555, 232.16666666666666]
1.0892845178272315
[253.01888888888888, 231.36]
1.0936155294298446
[253.01, 231.45]
1.093151868654137
[253.07, 231.19666666666666]
1.0946092071685
[253.0211111111111, 231.76333333333332]
1.0917219193909495
[253.14111111111112, 231.54888888888888]
1.0932512452373868
[252.97666666666666, 230.37]
1.0981319905659013
[253.09555555555556, 231.32333333333332]
1.0941203029910036
[253.02444444444444, 229.15555555555557]
1.1041602017067493
[252.90555555555557, 229.10444444444445]
1.1038876009971192
[253.06444444444443, 231.52555555555554]
1.0930302870333488
[253.09222222222223, 232.83555555555554]
1.086999885469955
[252.9388888888889, 230.95333333333335]
1.0951947964475748
[252.9177777777778, 231.49666666666667]
1.0925331298266834
[252.99, 231.5688888888889]
1.0925042703875016
[253.03666666666666, 231.25555555555556]
1.0941863258540334
[252.95444444444445, 231.04333333333332]
1.0948355046431888
[252.9188888888889, 230.47555555555556]
1.0973783674335191
[253.0677777777778, 231.66444444444446]
1.0923893754376541
[252.90222222222224, 232.78444444444443]
1.0864223458994016
[252.99777777777777, 234.2877777777778]
1.0798590527319203
[252.96777777777777, 233.11222222222221]
1.085175952450179
[253.01444444444445, 234.16444444444446]
1.0804989845692485
[253.05666666666667, 235.6811111111111]
1.07372485420507
[253.0388888888889, 236.35888888888888]
1.0705706482138744
[252.9488888888889, 240.36222222222221]
1.05236541146233
[253.01333333333332, 240.10555555555555]
1.0537587635067909
[253.11222222222221, 238.5988888888889]
1.0608273299214395
[252.97666666666666, 234.81555555555556]
1.0773420273122165
[253.1811111111111, 234.59777777777776]
1.0792135949000181
[253.01888888888888, 236.15666666666667]
1.0714026940684385
[252.96333333333334, 233.89777777777778]
1.081512341573717
[252.95888888888888, 230.6611111111111]
1.0966689949179893
[252.98555555555555, 231.50666666666666]
1.0927787056768223
[253.09777777777776, 230.67]
1.0972288454405765
[252.98444444444445, 233.82222222222222]
1.081952100361148
[252.98777777777778, 231.99]
1.0905115641957748
[252.98111111111112, 230.89]
1.095678076621383
[253.0088888888889, 232.14111111111112]
1.0898926419275632
[252.9177777777778, 231.8188888888889]
1.091014537210562
[252.94555555555556, 231.78444444444443]
1.091296511126238
[252.98111111111112, 231.42777777777778]
1.0931320066255372
[252.91444444444446, 231.88111111111112]
1.0907074027399097
[253.04333333333332, 231.52777777777777]
1.0929286142771446
[253.07555555555555, 231.84222222222223]
1.0915852735097624
[253.09333333333333, 231.90666666666667]
1.0913585925372276
[252.93666666666667, 231.65]
1.0918915029858263
[253.07666666666665, 231.7711111111111]
1.0919249834606939
[253.09, 231.67555555555555]
1.0924329042530743
[253.0088888888889, 231.59333333333333]
1.0924705182455838
[253.04555555555555, 231.30777777777777]
1.0939777208817496
[253.0611111111111, 230.82111111111112]
1.0963516720500242
[253.0011111111111, 230.57]
1.0972854712716793
[252.98777777777778, 231.16555555555556]
1.0944008382640629
[252.94444444444446, 231.50666666666666]
1.0926011249976004
[253.04666666666665, 231.84777777777776]
1.0914345140250068
[253.0677777777778, 231.54333333333332]
1.0929607608846916
[253.07111111111112, 231.40666666666667]
1.0936206581967292
[252.9488888888889, 231.26111111111112]
1.0937804790160233
[253.14777777777778, 232.02]
1.0910601576492447
[253.20666666666668, 231.94444444444446]
1.0916694610778443
[253.13888888888889, 232.00333333333333]
1.0911002236557903
[253.13777777777779, 231.95666666666668]
1.0913149486733633
[253.21, 232.02777777777777]
1.091291751466539
[253.10222222222222, 231.9188888888889]
1.0913394050601983
[253.13111111111112, 232.0222222222222]
1.090977875682406
[253.12666666666667, 232.01666666666668]
1.0909848430428848
[253.1688888888889, 232.17888888888888]
1.090404429534698
[253.17333333333335, 231.99]
1.0913114071008807
[253.16222222222223, 232.02777777777777]
1.0910858374236803
[253.18, 232.08444444444444]
1.0908960340106093
[253.26444444444445, 232.26333333333332]
1.0904193994364635
[253.17555555555555, 232.07222222222222]
1.090934335575611
[253.22, 232.0522222222222]
1.0912198882435467
[253.13555555555556, 232.11]
1.0905844451146247
[253.21, 232.3322222222222]
1.0898617401326645
[253.14222222222222, 232.08777777777777]
1.0907175924817718
[253.11666666666667, 232.04222222222222]
1.0908215937712487
[253.1977777777778, 232.01333333333332]
1.0913070130069153
[253.21444444444444, 232.2711111111111]
1.0901676202139263
[253.15444444444444, 232.01777777777778]
1.091099341046663
[253.14555555555555, 232.0677777777778]
1.090825956018596
[253.13111111111112, 232.12333333333333]
1.0905026542403224
[253.2122222222222, 232.18]
1.0905858481446387
[253.1, 232.07555555555555]
1.0905931018633779
[253.29666666666665, 232.08444444444444]
1.0913987246021561
[253.1977777777778, 232.17]
1.0905706067871723
[253.19555555555556, 232.23888888888888]
1.090237542760089
[253.2488888888889, 232.07333333333332]
1.0912451045167717
[253.19666666666666, 231.83777777777777]
1.0921285956655515
[253.17222222222222, 231.9088888888889]
1.0916883067104897
[253.29777777777778, 232.07111111111112]
1.0914662172514171
[253.23444444444445, 231.83333333333334]
1.0923124850227655
[253.2888888888889, 232.11666666666667]
1.09121370958091
[253.3388888888889, 232.12666666666667]
1.0913820998114057
[253.32, 232.27444444444444]
1.0906064186522648
[253.26888888888888, 232.04777777777778]
1.0914514731161686
[253.22444444444446, 232.22666666666666]
1.090419322118237
[253.25, 232.13444444444445]
1.0909626126622025
[253.36333333333334, 232.16444444444446]
1.0913097995673564
[253.33444444444444, 232.0522222222222]
1.0917130722490627
[253.23777777777778, 232.08]
1.0911658814968017
[253.19222222222223, 232.0988888888889]
1.0908808027229773
[253.30333333333334, 232.14666666666668]
1.0911349147090919
[253.21444444444444, 232.0011111111111]
1.091436343695672
[253.2711111111111, 232.08555555555554]
1.0912833868736147
[253.22444444444446, 232.07333333333332]
1.0911397738262811
[253.36333333333334, 232.2577777777778]
1.0908712541620422
[253.31222222222223, 232.15555555555557]
1.0911314252895568
[253.31, 232.07777777777778]
1.0914875281275433
[253.2288888888889, 232.02333333333334]
1.091394064773179
[253.32333333333332, 232.26666666666668]
1.0906572904707232
[253.27777777777777, 232.0677777777778]
1.0913957129382699
[253.23444444444445, 231.98888888888888]
1.0915800565161167
[253.21666666666667, 232.05333333333334]
1.0912002987818892
[253.32666666666665, 232.23]
1.0908438473352566
[253.18, 232.09555555555556]
1.090843809542047
[253.32, 232.14777777777778]
1.091201485643723
[253.29222222222222, 232.20333333333335]
1.090820784465722
[253.30777777777777, 232.30333333333334]
1.0904181792962266
[253.32555555555555, 232.08444444444444]
1.0915232003676822
[253.1688888888889, 232.11444444444444]
1.0907071703134947
[253.3022222222222, 231.94333333333333]
1.0920866686786523
[253.32333333333332, 232.33444444444444]
1.090339118416459
[253.22666666666666, 232.02555555555554]
1.0913740344693832
[253.3011111111111, 232.0522222222222]
1.0915694264222133
[253.26333333333332, 232.05444444444444]
1.0913961761847075
[253.24777777777777, 232.40222222222224]
1.0896960250905996
[253.3388888888889, 232.01666666666668]
1.0918995282905921
[253.3311111111111, 231.9488888888889]
1.0921850599269953
[253.26222222222222, 232.23111111111112]
1.0905611268468192
[253.27555555555554, 232.34333333333333]
1.0900917703207418
[253.33444444444444, 232.07333333333332]
1.0916137619334885
[253.2788888888889, 232.01111111111112]
1.0916670657535559
[253.23777777777778, 232.09777777777776]
1.0910823024778828
[253.29333333333332, 231.9988888888889]
1.0917868380595692
[253.27555555555554, 232.13333333333333]
1.0910779245644266
[253.29222222222222, 232.48111111111112]
1.0895174279391873
[253.23333333333332, 232.91555555555556]
1.087232377971988
[253.34555555555556, 232.9322222222222]
1.0876363653709473
[253.29666666666665, 233.50444444444443]
1.0847616509797577
[253.23888888888888, 233.06]
1.0865823774516814
[253.30666666666667, 233.7211111111111]
1.0837988295642005
[253.21777777777777, 233.69333333333333]
1.0835472889446758
[253.24444444444444, 233.9011111111111]
1.082698766335251
[253.23888888888888, 232.99444444444444]
1.0868880993824364
[253.1288888888889, 233.3011111111111]
1.0849879269041915
[252.99555555555557, 232.42777777777778]
1.0884910485933506
[252.9711111111111, 232.86555555555555]
1.0863397573230142
[252.98777777777778, 233.01777777777778]
1.0857016155181294
[252.79888888888888, 231.22]
1.09332622129958
[252.75222222222223, 232.85666666666665]
1.0854412108545552
[252.88666666666666, 231.95555555555555]
1.090237593408699
[253.0211111111111, 232.05]
1.0903732433144198
[252.91333333333333, 231.92222222222222]
1.090509270349255
[252.95777777777778, 232.1511111111111]
1.089625531263162
[253.04444444444445, 232.29222222222222]
1.0893367071169935
[253.10666666666665, 231.9088888888889]
1.0914056286472655
[253.01666666666668, 231.9622222222222]
1.0907666957263158
[252.90666666666667, 231.9777777777778]
1.0902193696714244
[253.03222222222223, 232.13]
1.0900453290062562
[252.99555555555557, 232.64333333333335]
1.087482507796866
[252.9922222222222, 232.4777777777778]
1.0882426038331021
[253.01888888888888, 232.61]
1.087738656501822
[253.03555555555556, 231.78444444444443]
1.0916848029299253
[252.95222222222222, 231.39888888888888]
1.0931436336484859
[253.05555555555554, 232.01777777777778]
1.0906731284959006
[253.02, 231.7422222222222]
1.0918165778067586
[253.10666666666665, 231.85333333333332]
1.0916671458968312
[253.07666666666665, 231.98333333333332]
1.0909260722753071
[252.97, 232.5]
1.0880430107526882
[252.98444444444445, 231.91555555555556]
1.0908472432494587
[252.8711111111111, 231.79]
1.0909491829289923
[253.0511111111111, 231.92444444444445]
1.0910928846559225
[253.14555555555555, 231.86222222222221]
1.0917930188426077
[253.05555555555554, 231.86666666666667]
1.0913839371286178
[252.95777777777778, 232.06]
1.090053338695931
[253.0522222222222, 233.85]
1.0821134155322738
[253.09222222222223, 233.70333333333335]
1.082963681400446
[253.11555555555555, 234.70777777777778]
1.0784284950079768
[253.04444444444445, 237.9922222222222]
1.0632466980713657
[252.8011111111111, 237.75222222222223]
1.0632965225234488
[252.88666666666666, 238.01333333333332]
1.062489496386757
[252.85666666666665, 238.44666666666666]
1.0604328011854502
[251.44333333333333, 236.24]
1.0643554577266057
[170.2888888888889, 235.0688888888889]
0.7244212098581031
[171.63333333333333, 235.15777777777777]
0.7298645826442767
[172.20444444444445, 232.30444444444444]
0.7412877737069172
[171.85, 233.70888888888888]
0.7353164906008425
[172.53444444444443, 232.87]
0.7409045580987007
[172.62, 233.26222222222222]
0.74002553159058
[172.70444444444445, 232.99]
0.7412526050235823
[172.95222222222222, 233.02333333333334]
0.7422098883755084
[172.69555555555556, 232.86111111111111]
0.7416247166885364
[172.71777777777777, 232.92333333333335]
0.741522007718324
[172.5522222222222, 233.01222222222222]
0.7405286322605872
[174.52666666666667, 233.60222222222222]
0.7471104726933724
[174.2722222222222, 233.51666666666668]
0.7462945780696119
[174.11222222222221, 233.53666666666666]
0.7455455484030583
[173.70555555555555, 233.76444444444445]
0.7430794532007529
[173.7888888888889, 233.42222222222222]
0.744525894897182
[173.73222222222222, 233.52777777777777]
0.7439467110741049
[173.4088888888889, 233.52333333333334]
0.7425762831218389
[173.58333333333334, 233.54666666666665]
0.7432490294587806
[173.23, 233.40444444444444]
0.7421880950567445
[173.20444444444445, 233.47555555555556]
0.7418525850909922
[173.4088888888889, 233.48]
0.7427141035158853
[173.52444444444444, 233.6911111111111]
0.7425376327726059
[173.21, 233.41333333333333]
0.7420741460070833
[172.97333333333333, 233.47222222222223]
0.7408732897085069
[173.13111111111112, 233.56222222222223]
0.7412633321598813
[173.07444444444445, 233.62555555555556]
0.7408198304028764
[172.8088888888889, 233.4622222222222]
0.7402006510689334
[172.58666666666667, 233.4911111111111]
0.7391573317090349
[173.0822222222222, 233.41]
0.7415373044095035
[173.19555555555556, 233.62777777777777]
0.7413311773238532
[172.97333333333333, 233.3]
0.7414202028861265
[173.29, 233.44]
0.7423320767649074
[172.90555555555557, 233.41666666666666]
0.7407592526478639
[172.94666666666666, 233.35555555555555]
0.7411294162460718
[175.2511111111111, 234.35111111111112]
0.7478142957385878
[174.79444444444445, 234.16444444444446]
0.7464602273805683
[174.97, 234.10888888888888]
0.7473872556929824
[174.96444444444444, 234.09]
0.7474238303406572
[174.90555555555557, 233.96666666666667]
0.7475661300280192
[174.84555555555556, 234.07888888888888]
0.7469514076450959
[174.8788888888889, 234.04222222222222]
0.7472108546416126
[174.93, 234.24444444444444]
0.7467839863390571
[174.70888888888888, 234.11888888888888]
0.7462400394861111
[175.04, 234.19333333333333]
0.7474166642944575
[175.1811111111111, 234.19666666666666]
0.7480085588085986
[175.08666666666667, 234.38444444444445]
0.7470063428555175
[175.09555555555556, 234.12333333333333]
0.7478774245293317
[175.29, 234.19222222222223]
0.7484877095263625
[175.59222222222223, 234.26333333333332]
0.7495506007010155
[175.7422222222222, 234.4177777777778]
0.7496966479599575
[176.1911111111111, 234.31333333333333]
0.7519465862425432
[176.36666666666667, 234.38]
0.7524817248343147
[176.48777777777778, 234.32555555555555]
0.753173410212762
[176.58333333333334, 234.56444444444443]
0.7528137256759574
[176.80444444444444, 234.3411111111111]
0.754474721085597
[177.14, 234.26888888888888]
0.7561396685669838
[177.20777777777778, 234.2811111111111]
0.7563895225583701
[177.19666666666666, 234.87555555555556]
0.7544278767006641
[177.56555555555556, 235.16666666666666]
0.755062603354595
[177.81555555555556, 234.19444444444446]
0.759264618669197
[177.96555555555557, 231.19222222222223]
0.769773108476352
[177.57222222222222, 235.1288888888889]
0.7552122712838348
[177.5677777777778, 233.05444444444444]
0.7619154322547427
[177.29666666666665, 230.2188888888889]
0.7701221542782954
[176.8711111111111, 233.00444444444443]
0.7590890016404075
[176.5211111111111, 234.34777777777776]
0.7532442286630032
[176.12666666666667, 234.9311111111111]
0.7496949460361902
[176.13222222222223, 229.92777777777778]
0.7660328122357262
[175.60222222222222, 229.4688888888889]
0.7652550333620631
[175.81666666666666, 228.0388888888889]
0.7709942261310205
[175.78, 227.73]
0.7718789794932596
[175.16666666666666, 232.35666666666665]
0.7538697691766968
[174.7877777777778, 233.84555555555556]
0.7474496462527499
[174.26444444444445, 236.10888888888888]
0.7380681229940989
[172.90666666666667, 236.0688888888889]
0.7324415660212179
[173.12555555555556, 234.43444444444444]
0.7384817361877996
[173.41444444444446, 233.45666666666668]
0.7428121326346551
[172.68666666666667, 233.63888888888889]
0.7391178218998931
[172.43444444444444, 233.69555555555556]
0.7378593231459734
[169.31666666666666, 234.87333333333333]
0.7208850160370128
[169.76777777777778, 232.16333333333333]
0.7312428510579239
[170.22555555555556, 233.0211111111111]
0.7305155946766865
[170.44555555555556, 234.10222222222222]
0.7280817496630152
[171.2122222222222, 232.82]
0.7353845125943742
[171.45111111111112, 232.75333333333333]
0.7366215067930761
[173.16555555555556, 232.9711111111111]
0.7432919675305475
[174.62777777777777, 232.51444444444445]
0.7510405566201382
[175.49777777777777, 232.83777777777777]
0.7537341210380141
[174.32555555555555, 233.01222222222222]
0.7481391057216836
[180.04333333333332, 232.92777777777778]
0.7729577599160445
[186.93, 232.1611111111111]
0.8051736102802174
[198.40444444444444, 232.30444444444444]
0.8540708074652993
[187.1911111111111, 232.47444444444446]
0.8052115644730363
[178.57444444444445, 228.35666666666665]
0.7819979466818476
[164.43333333333334, 229.71555555555557]
0.7158127926324342
[164.42888888888888, 231.03222222222223]
0.7117140947150229
[163.0011111111111, 230.96333333333334]
0.7057445385751465
[156.37777777777777, 231.5988888888889]
0.6752095337244949
[152.54222222222222, 230.7577777777778]
0.6610491039184907
[172.76888888888888, 230.85111111111112]
0.7483996419048352
[181.57666666666665, 231.64444444444445]
0.783859363008442
[163.34, 231.97444444444446]
0.7041292862719553
[153.75666666666666, 231.5677777777778]
0.6639812677833703
[148.7211111111111, 231.4777777777778]
0.6424854797676762
[141.25222222222223, 231.11555555555555]
0.6111757466202573
[137.85222222222222, 231.30333333333334]
0.5959802664130315
[136.96333333333334, 231.51666666666668]
0.5915916780649341
[135.1977777777778, 230.36333333333334]
0.5868893101236211
[134.10111111111112, 230.48222222222222]
0.581828436996828
[137.07, 230.98111111111112]
0.5934251477994833
[137.59333333333333, 230.7811111111111]
0.5962070841538158
[136.1888888888889, 232.41222222222223]
0.5859798920500452
[135.70333333333335, 234.26]
0.5792851247901193
[138.39555555555555, 236.04777777777778]
0.586303149550703
[140.69, 234.9711111111111]
0.5987544568126578
[136.20333333333335, 231.61666666666667]
0.5880549758940778
[134.39444444444445, 233.15444444444444]
0.5764181110279786
[134.57555555555555, 233.89444444444445]
0.5753687560865538
[133.59333333333333, 233.05777777777777]
0.5732198024333499
[130.86, 231.3]
0.5657587548638132
[129.85777777777778, 232.89222222222222]
0.5575874391110814
[129.7288888888889, 235.5011111111111]
0.5508631712046652
[127.8411111111111, 232.62444444444444]
0.5495600920892999
[126.54777777777778, 232.25555555555556]
0.5448643735348992
[126.54333333333334, 232.4911111111111]
0.544293210732071
[126.15666666666667, 230.7422222222222]
0.5467428780553576
[124.78, 230.33777777777777]
0.5417261606143635
[123.62333333333333, 232.15333333333334]
0.5325072509548288
[124.87222222222222, 232.85]
0.5362775272588457
[122.86777777777777, 232.39333333333335]
0.5287061208487526
[121.41555555555556, 232.40666666666667]
0.5224271631144641
[123.27888888888889, 232.19555555555556]
0.5309269964015007
[123.19555555555556, 232.12555555555556]
0.5307281021286373
[122.33222222222223, 232.39444444444445]
0.5263990820205111
[121.28111111111112, 232.67888888888888]
0.5212381393527561
[121.11111111111111, 231.8388888888889]
0.5223934245524909
[121.39444444444445, 231.2577777777778]
0.5249312936021371
[122.19, 231.46444444444444]
0.5278996534144913
[122.27, 231.79]
0.527503343543725
[121.82333333333334, 231.90444444444444]
0.5253169408856139
[122.11333333333333, 232.2888888888889]
0.525695972448101
[121.87222222222222, 231.7711111111111]
0.5258300814021496
[122.53777777777778, 231.50666666666666]
0.5293056115494634
[124.79666666666667, 232.36]
0.5370832616055545
[127.05111111111111, 232.22444444444446]
0.5471048123941398
[128.8388888888889, 231.9188888888889]
0.55553426245766
[131.94333333333333, 233.38111111111112]
0.5653556652685402
[135.90555555555557, 234.20333333333335]
0.5802887329623356
[136.15444444444444, 233.16555555555556]
0.5839389275145461
[137.64, 233.47444444444446]
0.5895291894901654
[142.18777777777777, 234.23]
0.6070434093744514
[144.67444444444445, 234.65]
0.6165542060278902
[143.31444444444443, 235.39222222222222]
0.608832539543929
[144.13666666666666, 234.48777777777778]
0.6146873326731077
[146.94555555555556, 234.05555555555554]
0.6278234037502968
[149.5611111111111, 234.7711111111111]
0.6370507444603254
[144.65444444444444, 234.20444444444445]
0.6176417564900561
[145.54444444444445, 234.15222222222224]
0.6215804533612986
[144.71777777777777, 234.0811111111111]
0.6182377428526674
[144.7811111111111, 234.35666666666665]
0.6177810649484878
[145.10333333333332, 235.08666666666667]
0.6172333607463913
[150.64777777777778, 234.85444444444445]
0.641451679290719
[146.02777777777777, 234.83777777777777]
0.6218240487523302
[148.16222222222223, 234.81444444444443]
0.6309757586368433
[159.38444444444445, 234.25444444444443]
0.6803902688909022
[151.45333333333335, 234.05]
0.6470981983906573
[156.17222222222222, 233.53333333333333]
0.6687363212484537
[160.7488888888889, 232.88777777777779]
0.6902418427568834
[171.76666666666668, 233.20555555555555]
0.7365462038735499
[191.70333333333335, 233.4188888888889]
0.8212845766076249
[173.41222222222223, 233.65666666666667]
0.7421668069484667
[165.69444444444446, 233.45888888888888]
0.709737141442938
[192.70111111111112, 233.1288888888889]
0.826586151675754
[198.53222222222223, 233.64333333333335]
0.8497234626377337
[184.23333333333332, 233.26888888888888]
0.7897895609263511
[149.65444444444444, 233.1811111111111]
0.6417948852346531
[147.17555555555555, 232.8177777777778]
0.6321491295051923
[147.74, 232.45888888888888]
0.6355532399994265
[161.5388888888889, 233.35555555555555]
0.6922435958480145
[162.86888888888888, 234.05777777777777]
0.695849078100374
[163.86111111111111, 235.08444444444444]
0.6970308541611525
[155.88333333333333, 236.2711111111111]
0.6597646771129211
[164.17111111111112, 236.86111111111111]
0.6931112935381729
[175.9911111111111, 238.03444444444443]
0.739351447736322
[190.64444444444445, 238.18555555555557]
0.8004030471107959
[196.98, 238.38]
0.8263277120563806
[204.07111111111112, 239.07]
0.8536040118421848
[208.4, 240.43333333333334]
0.8667683349507833
[205.65666666666667, 240.80333333333334]
0.8540441023795351
[211.54111111111112, 242.45555555555555]
0.8724943861417901
[215.1511111111111, 243.58777777777777]
0.8832590578801163
[217.79555555555555, 245.01]
0.8889251685872233
[215.38777777777779, 241.10888888888888]
0.8933215974340778
[213.03222222222223, 240.75444444444443]
0.8848527083842921
[210.45777777777778, 241.93555555555557]
0.8698918904024028
[190.39666666666668, 244.67]
0.7781774090271251
[185.11444444444444, 246.64444444444445]
0.7505315794215696
[184.2, 246.30666666666667]
0.7478482109023981
[182.8177777777778, 245.19555555555556]
0.7455998839928221
[178.86, 238.82444444444445]
0.7489183128471867
[178.27777777777777, 238.9088888888889]
0.7462165958198848
[177.99333333333334, 238.9911111111111]
0.7447696799509047
[201.79444444444445, 239.29111111111112]
0.843301046609894
[204.76888888888888, 239.78666666666666]
0.8539627817319099
[200.54666666666665, 239.10888888888888]
0.8387252669634476
[202.9711111111111, 237.48777777777778]
0.8546591871394551
[232.8088888888889, 239.78222222222223]
0.9709180552723768
[243.71777777777777, 242.67666666666668]
1.0042901162497881
[244.3188888888889, 238.76888888888888]
1.0232442343130503
[243.83444444444444, 245.96]
0.9913581250790553
[242.08, 247.2888888888889]
0.9789360172537743
[238.15666666666667, 246.61333333333334]
0.9657088019031141
[232.09555555555556, 245.63444444444445]
0.944881960998955
[224.63, 241.9711111111111]
0.92833396089524
[214.9788888888889, 224.36222222222221]
0.9581777482840249
[168.81222222222223, 226.0288888888889]
0.7468612665047732
[139.38666666666666, 225.0088888888889]
0.6194718233353743
[118.20444444444445, 212.34]
0.5566753529454858
[88.87, 204.27777777777777]
0.43504487353821053
[73.92, 201.74666666666667]
0.3664001057431763
[66.89888888888889, 202.3177777777778]
0.33066243423437275
[67.27444444444444, 203.39888888888888]
0.3307512878361621
[68.09222222222222, 204.28222222222223]
0.3333242681693082
[67.04444444444445, 205.90333333333334]
0.32561126310620414
[66.54777777777778, 205.85888888888888]
0.3232689058848294
[67.24444444444444, 205.09777777777776]
0.32786530001950287
[67.91, 206.29444444444445]
0.3291896695661541
[69.73333333333333, 205.7577777777778]
0.33890982924906304
[71.31777777777778, 207.14666666666668]
0.34428638860281496
[72.27111111111111, 206.26888888888888]
0.3503732991456675
[74.10666666666667, 205.2788888888889]
0.3610048118819384
[77.78444444444445, 207.92888888888888]
0.3740915697674419
[78.39888888888889, 211.9188888888889]
0.36994762146943017
[82.26777777777778, 214.42444444444445]
0.3836679068514162
[81.66222222222223, 213.82666666666665]
0.3819085032528944
[81.49333333333334, 212.60555555555555]
0.3833076380360083
[87.16666666666667, 215.65222222222224]
0.40420017827056937
[91.69777777777777, 217.71]
0.4211923098515354
[94.71444444444444, 219.28333333333333]
0.4319272377188315
[97.80666666666667, 219.61444444444444]
0.4453562556601721
[101.01444444444445, 219.79]
0.4595952702326969
[102.13777777777777, 220.04333333333332]
0.4641711986022955
[102.22111111111111, 221.35555555555555]
0.4617960044172272
[101.89, 221.86222222222221]
0.45924898335303194
[101.90444444444445, 222.62444444444444]
0.45774148790688857
[101.86555555555556, 221.4411111111111]
0.46001194197604584
[101.75111111111111, 220.62555555555556]
0.46119367656612764
[102.70555555555555, 221.7422222222222]
0.4631754589914215
[102.99333333333334, 221.94333333333333]
0.4640523857441089
[104.08777777777777, 223.33444444444444]
0.4660623578987169
[103.82666666666667, 224.30333333333334]
0.4628850812144269
[104.81111111111112, 224.1811111111111]
0.4675287342079569
[104.89222222222222, 224.43666666666667]
0.46735777972503995
[105.39666666666666, 226.07555555555555]
0.4662010733874614
[106.80222222222223, 227.11444444444444]
0.4702572858519689
[106.77222222222223, 227.02444444444444]
0.47031156703634464
[107.18777777777778, 227.28222222222223]
0.47160651954984995
[108.05222222222223, 227.4311111111111]
0.47509868678183387
[108.46555555555555, 227.58]
0.47660407573405195
[109.21111111111111, 227.44444444444446]
0.4801660967269174
[109.18333333333334, 227.82333333333332]
0.4792456142917758
[109.3488888888889, 228.11666666666667]
0.479355105818173
[110.85888888888888, 228.91222222222223]
0.48428558253770243
[110.96666666666667, 229.50444444444443]
0.4835055239792016
[110.61222222222223, 229.6688888888889]
0.48161604628886034
[110.29777777777778, 228.99444444444444]
0.4816613697566656
[111.47888888888889, 228.03222222222223]
0.4888734048307013
[113.42444444444445, 228.63]
0.49610481758493835
[113.22444444444444, 228.07333333333332]
0.4964387672580944
[115.49888888888889, 230.0]
0.5021690821256038
[118.77444444444444, 232.38444444444445]
0.5111118548764977
[123.60888888888888, 233.87666666666667]
0.528521680467863
[128.2, 233.88222222222223]
0.5481391393578914
[131.2588888888889, 235.25444444444443]
0.5579443533951419
[132.07333333333332, 235.46]
0.5609162207310512
[131.29888888888888, 233.52333333333334]
0.5622516902902874
[128.97444444444446, 232.89333333333335]
0.5537919123680846
[126.70333333333333, 233.28222222222223]
0.5431332577612239
[121.43444444444444, 232.51111111111112]
0.5222737264646851
[115.25888888888889, 231.72222222222223]
0.49740110285303285
[114.96222222222222, 230.8411111111111]
0.4980145073330863
[119.92666666666666, 231.36555555555555]
0.5183427860672625
[120.21333333333334, 231.3388888888889]
0.5196416992867606
[119.18222222222222, 231.14444444444445]
0.5156179397202326
[117.80555555555556, 231.04111111111112]
0.5098900147640871
[116.27666666666667, 231.04333333333332]
0.5032677852639477
[115.73777777777778, 231.7]
0.49951565721958474
[115.77777777777777, 231.73777777777778]
0.4996068353119426
[116.15222222222222, 231.59555555555556]
0.5015304457963116
[117.93666666666667, 231.46444444444444]
0.5095239009591106
[118.55555555555556, 231.78]
0.5115003691239777
[119.55222222222223, 231.79333333333332]
0.5157707536406952
[120.09333333333333, 232.24555555555557]
0.5170963683074906
[119.90222222222222, 232.65444444444444]
0.5153661367120527
[120.00555555555556, 232.89]
0.5152885720965072
[120.19, 232.55333333333334]
0.5168276811054094
[120.34222222222222, 232.13888888888889]
0.5184061266004547
[120.1288888888889, 232.04888888888888]
0.517687843557871
[121.07777777777778, 232.74777777777777]
0.5202102418927499
[121.05, 232.9711111111111]
0.5195923195055181
[121.69777777777777, 233.38666666666666]
0.5214427178549665
[121.34333333333333, 232.53666666666666]
0.5218245151302303
[113.20555555555555, 233.10444444444445]
0.4856430593820604
[108.35, 233.40333333333334]
0.46421787749389465
[110.04333333333334, 232.87777777777777]
0.4725368576745074
[111.55333333333333, 232.62]
0.47955177256183185
[117.38444444444444, 233.15555555555557]
0.503459778879146
[133.2711111111111, 234.44222222222223]
0.5684603645532185
[155.23222222222222, 235.57]
0.6589643087923854
[112.10888888888888, 242.45]
0.46240003666277124
[138.7277777777778, 238.90444444444444]
0.5806831183085753
[120.4888888888889, 238.04222222222222]
0.5061660396381594
[117.98666666666666, 230.2811111111111]
0.5123592903359662
[153.7888888888889, 238.65333333333334]
0.644402853045794
[155.9622222222222, 237.35333333333332]
0.6570888221030062
[158.73555555555555, 234.09444444444443]
0.6780833946412891
[154.80666666666667, 236.00333333333333]
0.6559511871301253
[155.11888888888888, 234.05]
0.6627596192646394
[153.79666666666665, 232.79333333333332]
0.660657521693061
[153.17444444444445, 232.5377777777778]
0.6587077846371437
[153.09333333333333, 231.93]
0.6600842208137513
[150.25555555555556, 232.64666666666668]
0.6458530341672158
[148.28, 233.8488888888889]
0.6340846890679641
[152.0311111111111, 233.65777777777777]
0.650657181442946
[175.9988888888889, 232.9311111111111]
0.7555834343010333
[184.86666666666667, 232.57777777777778]
0.7948595451939614
[189.45333333333335, 234.05]
0.8094566688029623
[194.66555555555556, 236.07444444444445]
0.8245939369407955
[212.2877777777778, 233.15555555555557]
0.9104984750285933
[217.36666666666667, 232.14777777777778]
0.9363288709777776
[213.83, 233.12333333333333]
0.9172398015356679
[212.7588888888889, 233.2711111111111]
0.9120670273977822
[199.8111111111111, 232.38666666666666]
0.8598217530170024
[190.17555555555555, 231.73555555555555]
0.8206576461675664
[191.14666666666668, 229.88]
0.8315062931384491
[188.13555555555556, 243.71333333333334]
0.7719542996781282
[182.64888888888888, 245.64666666666668]
0.7435431197474239
[173.3711111111111, 245.38222222222223]
0.7065349296335874
[174.04111111111112, 245.32777777777778]
0.7094227677257184
[158.85888888888888, 245.05333333333334]
0.6482625097484448
[155.54111111111112, 244.58777777777777]
0.6359316582549324
[164.36444444444444, 243.54222222222222]
0.6748909611840064
[164.76777777777778, 242.95]
0.6781962452264985
[156.87, 241.9922222222222]
0.6482439747833952
[153.4488888888889, 240.58333333333334]
0.6378201131509064
[153.2877777777778, 237.6588888888889]
0.6449907196588949
[145.6811111111111, 219.10666666666665]
0.6648867116980061
[134.29777777777778, 208.17888888888888]
0.645107573080844
[126.88111111111111, 205.5677777777778]
0.6172227597277999
[119.79777777777778, 203.26]
0.5893819628937212
[113.54777777777778, 203.57888888888888]
0.5577581172463856
[109.20222222222222, 201.88]
0.540926402923629
[107.00333333333333, 203.2288888888889]
0.5265163526620231
[107.50333333333333, 203.1611111111111]
0.5291531078235664
[109.48444444444445, 203.27666666666667]
0.5385981885662124
[103.68777777777778, 206.04222222222222]
0.5032355827823856
[103.7311111111111, 207.6677777777778]
0.4995050855800664
[102.42888888888889, 210.88666666666666]
0.4857058556992171
[100.66777777777777, 205.39555555555555]
0.49011663132384126
[102.24444444444444, 203.78]
0.5017393485349123
[105.12444444444445, 204.76444444444445]
0.5133920819586734
[107.74555555555555, 206.08777777777777]
0.5228139034607692
[120.09333333333333, 204.66444444444446]
0.5867816154355638
[115.13444444444444, 204.21666666666667]
0.5637857395467777
[85.35888888888888, 201.88444444444445]
0.4228106287425149
[86.60666666666667, 203.17444444444445]
0.4262675205215004
[90.37444444444445, 206.89222222222222]
0.43681895565592394
[86.80222222222223, 207.08666666666667]
0.4191589136056831
[90.88444444444444, 215.5588888888889]
0.42162234604619514
[93.11888888888889, 214.51111111111112]
0.4340982078110432
[93.38666666666667, 213.63666666666666]
0.4371284579738185
[93.35555555555555, 215.5377777777778]
0.4331285054437479
[110.31, 214.59333333333333]
0.5140420640591506
[128.56555555555556, 213.5611111111111]
0.602008272417471
[144.88, 213.40555555555557]
0.6788951656991122
[148.7422222222222, 214.88333333333333]
0.6921999017554745
[152.66555555555556, 216.33444444444444]
0.7056923179644686
[153.77666666666667, 217.5222222222222]
0.7069469275169843
[138.05444444444444, 218.54222222222222]
0.6317060522248434
[126.7388888888889, 216.6211111111111]
0.5850717330310476
[118.66333333333333, 217.64555555555555]
0.545213675650012
[116.53888888888889, 218.20555555555555]
0.5340784683147899
[116.11333333333333, 215.94555555555556]
0.5376972590827935
[117.01333333333334, 214.80333333333334]
0.5447463571328812
[118.67666666666666, 216.25666666666666]
0.5487769163185721
[118.25333333333333, 217.21]
0.544419379095499
[120.37444444444445, 217.20555555555555]
0.5541959741156611
[120.35777777777778, 216.83444444444444]
0.5550676143089198
[121.07444444444444, 218.24555555555557]
0.5547624744808345
[119.72555555555556, 218.62555555555556]
0.5476283650889648
[117.65222222222222, 218.44444444444446]
0.5385910478128179
[117.25555555555556, 218.73444444444445]
0.5360635168977096
[116.80333333333333, 219.18555555555557]
0.5328970380246062
[115.28777777777778, 218.50333333333333]
0.5276248010454964
[113.07555555555555, 218.0388888888889]
0.5186026957474457
[112.27666666666667, 218.00333333333333]
0.5150227060748307
[110.55222222222223, 220.28222222222223]
0.5018662927355816
[112.57666666666667, 219.7188888888889]
0.5123668121387429
[114.6288888888889, 220.1977777777778]
0.5205724146978978
[116.02555555555556, 221.29777777777778]
0.5242960716580977
[116.7611111111111, 220.58]
0.5293367989441976
[119.6, 221.20111111111112]
0.5406844450248893
[120.61, 221.29111111111112]
0.5450286701278356
[122.56555555555556, 222.34]
0.5512528359969217
[123.70444444444445, 221.95444444444445]
0.5573415966239318
[125.98666666666666, 222.39333333333335]
0.5665037920800983
[126.33555555555556, 222.4411111111111]
0.5679505686898405
[127.65666666666667, 222.76444444444445]
0.5730567415506165
[129.02444444444444, 222.48555555555555]
0.5799227914920819
[130.45555555555555, 222.91666666666666]
0.585221183800623
[130.97555555555556, 222.97]
0.5874133540635761
[132.45333333333335, 223.4777777777778]
0.5926912941878387
[132.0888888888889, 223.38222222222223]
0.591313344342532
[132.06444444444443, 223.67444444444445]
0.5904315299517652
[134.67666666666668, 223.93]
0.6014230637550425
[131.78555555555556, 224.11888888888888]
0.5880162810413124
[133.9111111111111, 224.31222222222223]
0.5969853527573173
[137.6211111111111, 224.80333333333334]
0.6121844772962045
[140.23555555555555, 224.70888888888888]
0.624076583035829
[139.74555555555557, 224.69333333333333]
0.621939037898568
[138.23444444444445, 224.8788888888889]
0.6147061875281016
[118.82888888888888, 225.39555555555555]
0.5272015616989392
[120.39, 225.91333333333333]
0.5329034733083483
[120.53333333333333, 225.6977777777778]
0.5340474971446575
[125.80333333333333, 225.92444444444445]
0.5568380776267385
[127.72555555555556, 226.04888888888888]
0.5650350956528578
[133.45666666666668, 226.33444444444444]
0.589643644361098
[144.58333333333334, 225.98888888888888]
0.6397807168494027
[144.1511111111111, 226.2888888888889]
0.6370224884611607
[142.3488888888889, 226.49333333333334]
0.6284904142383392
[142.68777777777777, 226.64222222222222]
0.6295727970663503
[142.61111111111111, 226.54888888888888]
0.6294937565597811
[143.7288888888889, 226.96666666666667]
0.6332599011112743
[144.45888888888888, 226.81]
0.6369158718261491
[146.14111111111112, 227.02]
0.6437367241261172
[149.67333333333335, 226.79888888888888]
0.6599385652487031
[148.2511111111111, 226.73222222222222]
0.6538599130643588
[147.67222222222222, 226.80555555555554]
0.6510961420698101
[148.7511111111111, 227.67222222222222]
0.6533564334691686
[148.32888888888888, 227.5911111111111]
0.6517341040462428
[146.8022222222222, 227.48]
0.6453412265791376
[147.45, 227.5677777777778]
0.6479388314104222
[146.7788888888889, 227.76555555555555]
0.644429701105913
[146.86888888888888, 227.47555555555556]
0.6456469071157829
[148.32, 228.03666666666666]
0.6504217158059377
[147.68777777777777, 228.03222222222223]
0.6476618801436443
[148.4911111111111, 228.30666666666667]
0.6504019934201561
[148.07666666666665, 228.13333333333333]
0.6490794856808884
[147.42111111111112, 227.90333333333334]
0.6468580733546875
[146.56444444444443, 228.13]
0.642460195697385
[146.73444444444445, 228.89222222222222]
0.6410634796580633
[144.55777777777777, 229.01555555555555]
0.6312137943080043
[142.26444444444445, 228.88111111111112]
0.6215648104547242
[141.86666666666667, 228.71333333333334]
0.620281575188737
[141.08666666666667, 228.94555555555556]
0.616245492620759
[140.07666666666665, 228.73888888888888]
0.6123867583124863
[137.90555555555557, 228.68333333333334]
0.6030415664553118
[140.2511111111111, 229.4322222222222]
0.611296485527074
[139.82444444444445, 229.5611111111111]
0.6090946492098449
[140.4411111111111, 229.34555555555556]
0.6123559306432311
[142.27777777777777, 229.32666666666665]
0.6204153221508377
[144.02777777777777, 229.31666666666666]
0.6280737456695011
[142.54555555555555, 229.51666666666668]
0.6210684288238568
[141.4388888888889, 229.35]
0.6166945231693434
[139.80444444444444, 229.17777777777778]
0.6100261805488219
[139.78, 229.27555555555554]
0.6096594103165527
[140.79222222222222, 230.20444444444445]
0.6115964553247355
[137.13444444444445, 230.11888888888888]
0.5959286745498704
[136.35777777777778, 230.1811111111111]
0.5923934293285964
[137.98, 230.09666666666666]
0.5996610120384186
[139.44333333333333, 230.21444444444444]
0.6057106176366962
[139.79222222222222, 230.13555555555556]
0.6074342657950387
[144.6211111111111, 230.10222222222222]
0.6285081026790026
[143.45888888888888, 230.01888888888888]
0.6236830791674114
[141.86222222222221, 230.15555555555557]
0.6163753982813556
[142.58777777777777, 229.93444444444444]
0.6201236101110945
[146.2188888888889, 230.84777777777776]
0.6333995947305344
[146.07666666666665, 230.85444444444445]
0.6327652344671245
[145.8, 230.95444444444445]
0.6312933286506719
[147.33444444444444, 230.84666666666666]
0.6382350959270704
[147.37333333333333, 230.82]
0.6384773127689687
[146.9622222222222, 230.8788888888889]
0.6365338248528569
[147.47222222222223, 231.00444444444443]
0.6383956056641528
[147.89888888888888, 230.85666666666665]
0.6406524490905853
[147.41333333333333, 230.92777777777778]
0.6383525392739432
[201.91, 230.89555555555555]
0.8744646449091942
[210.84666666666666, 230.9688888888889]
0.9128790794334974
[211.92, 230.75222222222223]
0.9183876885740837
[215.7488888888889, 230.76333333333332]
0.9349357446542154
[217.15666666666667, 230.72666666666666]
0.9411858187176746
[217.0688888888889, 230.91333333333333]
0.9400448460701947
[215.70222222222222, 230.76222222222222]
0.9347380179694346
[210.8711111111111, 230.8322222222222]
0.9135254561995485
[212.38444444444445, 230.73111111111112]
0.9204846430188098
[211.54888888888888, 230.90666666666667]
0.9161662239673557
[210.2411111111111, 230.7811111111111]
0.9109979152925091
[210.91333333333333, 230.68777777777777]
0.9142804849267168
[211.79222222222222, 231.36555555555555]
0.9154008327370348
[212.34222222222223, 231.64777777777778]
0.9166598715482798
[215.30777777777777, 231.35666666666665]
0.9306313964489653
[219.97666666666666, 231.28555555555556]
0.9511042146072435
[224.0688888888889, 231.41444444444446]
0.9682580075189775
[223.7722222222222, 231.49444444444444]
0.9666418680553889
[225.57333333333332, 231.5077777777778]
0.9743661120096756
[228.96777777777777, 231.38777777777779]
0.9895413663450964
[228.57222222222222, 231.46]
0.9875236421939956
[231.72, 231.2811111111111]
1.0018976425994341
[231.16, 231.59222222222223]
0.9981336928413447
[231.44333333333333, 231.33666666666667]
1.0004610884569387
[232.3188888888889, 231.63555555555556]
1.002950036455735
[232.8177777777778, 231.4711111111111]
1.0058178606401569
[231.80777777777777, 231.42777777777778]
1.001641980939578
[231.6288888888889, 231.48444444444445]
1.0006239920129023
[232.11555555555555, 231.50444444444443]
1.0026397381379768
[230.6688888888889, 231.54888888888888]
0.9961995067036479
[229.25555555555556, 231.52666666666667]
0.9901907147724764
[229.23555555555555, 231.55444444444444]
0.9899855565525746
[228.76333333333332, 231.73222222222222]
0.9871882776576412
[228.88444444444445, 231.58444444444444]
0.9883411858405382
[230.4622222222222, 231.62777777777777]
0.9949679802364906
[230.81333333333333, 231.58]
0.9966894089875349
[231.8322222222222, 231.82555555555555]
1.0000287572552158
[231.42333333333335, 231.55444444444444]
0.9994337784730254
[231.15333333333334, 231.47222222222223]
0.9986223448937958
[230.30333333333334, 231.46555555555557]
0.9949788545451926
[229.00666666666666, 231.70666666666668]
0.9883473357118194
[228.01888888888888, 231.57444444444445]
0.9846461660996942
[228.42444444444445, 231.56444444444443]
0.9864400598825381
[229.30333333333334, 231.59444444444443]
0.9901072276728957
[229.60444444444445, 231.60111111111112]
0.9913788554075254
[229.3188888888889, 231.3411111111111]
0.9912586992752406
[230.18555555555557, 231.4311111111111]
0.994618028883085
[231.01, 231.4177777777778]
0.9982379150742283
[232.92111111111112, 231.34777777777776]
1.0068007281005509
[232.5311111111111, 231.47555555555556]
1.0045601167389884
[232.52444444444444, 231.42777777777778]
1.0047386993782557
[233.13222222222223, 231.42777777777778]
1.0073649086588088
[233.13777777777779, 231.5011111111111]
1.0070698004809193
[232.6977777777778, 231.66444444444446]
1.0044604744410017
[231.74333333333334, 231.4388888888889]
1.0013154420413355
[232.36666666666667, 231.35888888888888]
1.0043559068882881
[232.44666666666666, 231.63111111111112]
1.003520924074678
[233.11222222222221, 231.75444444444443]
1.0058586914310645
[232.93666666666667, 231.44666666666666]
1.0064377682403434
[232.87333333333333, 231.56333333333333]
1.0056571996142165
[231.39888888888888, 231.31333333333333]
1.0003698686726037
[231.38444444444445, 231.97333333333333]
0.9974613940299651
[232.02777777777777, 231.6588888888889]
1.0015923796002744
[233.29555555555555, 231.45222222222222]
1.0079642066757237
[236.03333333333333, 232.63]
1.0146298127212026
[230.00333333333333, 230.51777777777778]
0.9977683090241293
[230.26444444444445, 231.88333333333333]
0.9930185198495413
[228.8488888888889, 230.74444444444444]
0.9917850435787547
[234.54111111111112, 231.41555555555556]
1.0135062465790257
[233.51777777777778, 231.08666666666667]
1.01052034349787
[233.48111111111112, 231.37333333333333]
1.0091098561247815
[233.98111111111112, 231.69444444444446]
1.0098693202253926
[233.87333333333333, 231.17]
1.0116941356289022
[234.10111111111112, 231.20888888888888]
1.0125091307523741
[233.75444444444443, 231.51111111111112]
1.0096899596851603
[233.45111111111112, 231.19]
1.009780315373118
[232.95, 231.2]
1.007569204152249
[232.17444444444445, 231.15777777777777]
1.0043981503734822
[233.14444444444445, 232.09777777777776]
1.0045095936578454
[234.0311111111111, 231.85111111111112]
1.0094025859507538
[235.12555555555556, 231.8188888888889]
1.014264008780801
[235.88111111111112, 231.88666666666666]
1.0172258478758782
[236.13888888888889, 231.9111111111111]
1.018230164814105
[236.03444444444443, 231.92888888888888]
1.0177017859880424
[235.7577777777778, 231.9111111111111]
1.0165868148715984
[235.60888888888888, 231.92]
1.015905867923805
[236.13, 232.08444444444444]
1.0174313947030773
[235.37333333333333, 231.82444444444445]
1.0153085188984001
[235.10777777777778, 231.83555555555554]
1.0141144105975501
[234.81666666666666, 231.7722222222222]
1.013135501809727
[235.29444444444445, 232.04333333333332]
1.0140107930032227
[235.22666666666666, 231.88444444444445]
1.0144133093111511
[234.84333333333333, 231.77333333333334]
1.0132456998216648
[234.7711111111111, 231.82777777777778]
1.0126962064751133
[234.60888888888888, 232.04444444444445]
1.0110515226968013
[234.98111111111112, 231.74]
1.0139859804570255
[234.97666666666666, 231.82444444444445]
1.0135974540121355
[235.08, 231.81555555555556]
1.014082076746839
[235.35111111111112, 231.99333333333334]
1.014473595984559
[235.19, 231.84777777777776]
1.0144155887723267
[235.04666666666665, 231.86555555555555]
1.0137196363793195
[234.8711111111111, 231.79666666666665]
1.0132635403634411
[235.07555555555555, 231.7288888888889]
1.014442164214887
[235.20333333333335, 231.87444444444444]
1.0143564285269329
[235.5822222222222, 231.7588888888889]
1.0164970299592968
[235.98555555555555, 231.81555555555556]
1.017988439084713
[235.82444444444445, 231.95]
1.0167037915259516
[235.5522222222222, 231.89333333333335]
1.0157783272002452
[235.76111111111112, 231.94222222222223]
1.0164648284055415
[235.8322222222222, 231.78333333333333]
1.0174684211787828
[236.2111111111111, 231.94444444444446]
1.0183952095808382
[235.95333333333335, 231.79555555555555]
1.017937262721939
[235.89888888888888, 231.87]
1.01737563673131
[235.73111111111112, 231.71444444444444]
1.0173345545043468
[235.7, 231.96555555555557]
1.0160991334920413
[235.69, 231.67888888888888]
1.0173132352729592
[235.8411111111111, 231.79666666666665]
1.0174482424730487
[235.85666666666665, 231.85777777777778]
1.0172471630118078
[235.90444444444444, 231.97444444444446]
1.0169415213361623
[236.32666666666665, 231.78]
1.0196163028158887
[236.39888888888888, 231.7888888888889]
1.0198887876899476
[236.54444444444445, 231.95]
1.0198079087926037
[236.46333333333334, 231.79555555555555]
1.020137477470568
[236.89555555555555, 231.71666666666667]
1.0223500923062168
[236.62666666666667, 231.69333333333333]
1.0212925130920183
[237.04888888888888, 231.72222222222223]
1.0229872932150563
[236.7411111111111, 231.74]
1.021580698675719
[237.08333333333334, 231.94]
1.0221752752148545
[236.99333333333334, 231.80444444444444]
1.0223847687706114
[237.0888888888889, 231.82]
1.0227283620433478
[237.07888888888888, 231.69555555555556]
1.023234512722634
[237.7277777777778, 231.95666666666668]
1.0248801260771887
[237.57777777777778, 231.86666666666667]
1.0246310139927162
[237.39111111111112, 231.85888888888888]
1.023860298169864
[237.79222222222222, 231.81]
1.0258065753083223
[237.8022222222222, 231.77777777777777]
1.025992329817833
[237.76444444444445, 231.78]
1.0258195031687136
[237.41222222222223, 231.72]
1.0245650881331876
[237.7722222222222, 231.7811111111111]
1.0258481421647818
[237.85777777777778, 231.81444444444443]
1.0260697013415903
[237.78444444444443, 231.92555555555555]
1.0252619374991017
[237.6588888888889, 231.77333333333334]
1.0253935837695833
[238.34444444444443, 231.67777777777778]
1.0287755982926479
[238.08777777777777, 231.78444444444443]
1.0271948074360278
[238.38555555555556, 231.98333333333332]
1.0275977680388917
[238.29555555555555, 231.6977777777778]
1.0284757922197498
[238.9111111111111, 231.73777777777778]
1.0309545271475422
[238.95777777777778, 231.81555555555556]
1.0308099351016613
[238.09333333333333, 231.94555555555556]
1.0265052622502406
[237.85777777777778, 231.8188888888889]
1.0260500294770343
[237.6888888888889, 231.72444444444446]
1.0257393839426139
[238.24555555555557, 231.73333333333332]
1.02810222477944
[236.6677777777778, 231.9088888888889]
1.0205205109286215
[236.59777777777776, 231.89444444444445]
1.0202822165257182
[236.74, 231.96]
1.0206070012071047
[237.74555555555557, 231.74666666666667]
1.0258855455190534
[238.54444444444445, 231.64777777777778]
1.0297722116431556
[239.36555555555555, 231.82888888888888]
1.0325096095779454
[241.3011111111111, 231.78555555555556]
1.0410532724213473
[242.37777777777777, 231.76222222222222]
1.0458036493340876
[244.90444444444444, 231.93777777777777]
1.0559057984900164
[245.01888888888888, 231.86333333333334]
1.0567384043282202
[245.57666666666665, 231.81222222222223]
1.0593775613403569
[244.34555555555556, 231.79888888888888]
1.0541273805358093
[244.20888888888888, 231.6911111111111]
1.054027872358792
[230.38777777777779, 232.55555555555554]
0.9906784519827999
[165.93666666666667, 231.02666666666667]
0.7182576325965256
[167.76222222222222, 232.79888888888888]
0.7206315417694815
[167.83666666666667, 231.63222222222223]
0.7245825518422403
[164.84, 231.64555555555555]
0.7116044147907963
[166.47555555555556, 231.42666666666668]
0.7193447408346296
[166.32555555555555, 231.76888888888888]
0.7176353839073406
[166.5288888888889, 231.57111111111112]
0.7191263542756245
[167.04333333333332, 231.45]
0.7217253546482322
[167.05777777777777, 231.68444444444444]
0.7210573768919412
[166.44, 231.55333333333334]
0.7187976851985144
[166.85, 231.5311111111111]
0.7206374953210032
[169.24333333333334, 232.29333333333332]
0.728575938468603
[168.71666666666667, 232.34555555555556]
0.7261454442855708
[168.57555555555555, 232.46777777777777]
0.7251566525348794
[168.65666666666667, 232.20888888888888]
0.7263144295366242
[168.88444444444445, 232.1511111111111]
0.7274763563962171
[168.2577777777778, 232.06]
0.725061526233637
[168.03, 232.44222222222223]
0.7228893201655847
[168.3177777777778, 232.32888888888888]
0.7244806213413935
[168.01111111111112, 232.36777777777777]
0.723039625880429
[168.4177777777778, 232.37333333333333]
0.7247723969091883
[168.73444444444445, 232.34]
0.7262393235966448
[168.61666666666667, 232.30444444444444]
0.7258434812554407
[169.2411111111111, 232.18666666666667]
0.7289010757627962
[169.0088888888889, 232.34777777777776]
0.7273961924892284
[169.3011111111111, 232.4988888888889]
0.7281803019369268
[169.26666666666668, 232.22333333333333]
0.728896033990268
[169.04666666666665, 232.27666666666667]
0.7277815249056441
[168.61666666666667, 232.1588888888889]
0.7262985598943252
[168.15333333333334, 232.37777777777777]
0.7236205412642249
[168.06666666666666, 232.26111111111112]
0.7236108785610065
[167.6888888888889, 232.23]
0.7220810786241609
[167.9, 232.29555555555555]
0.7227861058230416
[167.79111111111112, 232.31222222222223]
0.7222655334535419
[167.6588888888889, 232.24777777777777]
0.7218966333848429
[167.48111111111112, 232.12555555555556]
0.7215108681604304
[167.37666666666667, 232.19444444444446]
0.7208469912668979
[167.17444444444445, 232.4]
0.7193392618091413
[167.6988888888889, 232.27333333333334]
0.7219894185968638
[167.15222222222224, 232.21444444444444]
0.7198183671223439
[167.67888888888888, 232.20666666666668]
0.7221105720000383
[167.17111111111112, 232.34]
0.719510678794487
[167.11, 232.30555555555554]
0.71935429869664
[169.42111111111112, 232.89888888888888]
192.168.1.171 - - [09/Nov/2021 18:43:08] "GET /index.html HTTP/1.1" 200 -
0.7274449093311833
[169.62333333333333, 232.92444444444445]
0.7282332849946573
[169.28222222222223, 233.0988888888889]
0.7262249212303791
WARNING:root:Removed streaming client ('192.168.1.171', 55201): [Errno 32] Broken pipe
192.168.1.171 - - [09/Nov/2021 18:43:08] "GET /stream.mjpg HTTP/1.1" 200 -
[169.62444444444444, 232.76222222222222]
0.7287455963644348
[169.76111111111112, 232.90555555555557]
0.7288839062090022
[170.34333333333333, 232.95222222222222]
0.731237211254573
[170.57777777777778, 233.19444444444446]
0.7314830256104824
[170.98333333333332, 232.99777777777777]
0.7338410476017893
[171.25555555555556, 232.95444444444445]
0.7351461182205391
[171.7711111111111, 233.0]
0.7372150691463997
[172.41444444444446, 232.99333333333334]
0.7399973294419487
[172.59777777777776, 232.97666666666666]
0.740837184458148
[173.13444444444445, 233.01222222222222]
0.7430273090109722
[171.03, 233.08777777777777]
0.7337579071308377
[172.08333333333334, 233.01333333333332]
0.7385128175783933
[170.65333333333334, 233.17555555555555]
0.7318663095998247
[171.23444444444445, 232.97]
0.7350064147505878
[171.8411111111111, 232.98888888888888]
0.7375506700367209
[171.72444444444446, 233.03222222222223]
0.7369128732793272
[171.82666666666665, 233.21333333333334]
0.7367789148705047
[171.15666666666667, 232.91666666666666]
0.7348407871198569
[169.70777777777778, 232.98333333333332]
0.7284116651167227
[168.65777777777777, 232.41555555555556]
0.7256733628462428
[167.8088888888889, 232.08]
0.7230648435405416
[168.04888888888888, 231.88111111111112]
0.7247200433172171
[170.45222222222222, 232.20666666666668]
0.734053955767372
[171.70333333333335, 232.92888888888888]
0.737149153771299
[171.82888888888888, 233.32666666666665]
0.7364305646828004
192.168.1.171 - - [09/Nov/2021 18:43:09] "GET /index.html HTTP/1.1" 200 -
[172.12222222222223, 233.22]
0.7380251360184471
192.168.1.171 - - [09/Nov/2021 18:43:09] "GET /stream.mjpg HTTP/1.1" 200 -
[171.67222222222222, 233.0677777777778]
0.7365763893192728
WARNING:root:Removed streaming client ('192.168.1.171', 55251): [Errno 32] Broken pipe
[171.67222222222222, 233.0677777777778]
0.7365763893192728
[171.51555555555555, 233.2411111111111]
0.7353573078883558
[171.41555555555556, 233.08]
0.7354365692275423
[171.56666666666666, 233.0811111111111]
0.7360813832094693
[171.2511111111111, 233.09333333333333]
0.7346890134614651
[171.0588888888889, 233.32777777777778]
0.7331269792137909
[171.27666666666667, 232.99777777777777]
0.7351000009537526
[171.33777777777777, 233.04888888888888]
0.7352010069417957
[171.39333333333335, 232.92555555555555]
0.7358288055792743
[171.35, 232.9388888888889]
0.7356006582556226
[171.37555555555556, 233.21444444444444]
0.7348410856960452
[171.2788888888889, 232.99666666666667]
0.7351130440588087
[171.4988888888889, 233.08555555555554]
0.7357765627309001
[171.34444444444443, 233.17777777777778]
0.7348232154769846
[171.32666666666665, 232.92555555555555]
0.7355425910996837
[171.22555555555556, 233.1588888888889]
0.7343728406475317
[170.89111111111112, 233.03]
0.733343823160585
[170.9477777777778, 232.98666666666668]
0.7337234367250391
[171.05444444444444, 233.04111111111112]
0.7340097360027081
[171.00444444444443, 233.2]
0.7332952163140842
[170.9711111111111, 232.96]
0.7339075854700854
[170.92444444444445, 233.06222222222223]
0.7333854573885848
[171.14888888888888, 233.3011111111111]
0.7335965442846869
[171.04888888888888, 232.98111111111112]
0.734174921190559
[171.47555555555556, 233.04222222222222]
0.7358132527248281
[170.85, 232.93]
0.7334821620229253
[170.92, 233.0888888888889]
0.7332824864143387
[170.98, 232.93]
0.7340402696088953
[170.88222222222223, 232.9611111111111]
0.7335225240264232
[171.0588888888889, 233.0522222222222]
0.733993811592061
[170.57222222222222, 233.16333333333333]
0.7315568009073278
[170.62, 233.02666666666667]
0.7321908794415518
[170.57222222222222, 232.98333333333332]
0.7321219925125785
[170.85666666666665, 233.03666666666666]
0.7331750368325441
[170.61666666666667, 233.07222222222222]
0.7320334660215003
[172.52, 233.67333333333335]
0.7382956263729994
[172.62, 233.7511111111111]
0.7384777731300148
[172.73888888888888, 233.7122222222222]
0.7391093510062232
[173.2877777777778, 233.93666666666667]
0.7407465458362426
[173.29666666666665, 233.82444444444445]
0.7411400766006785
[173.50222222222223, 233.71777777777777]
0.7423578294809505
[173.01555555555555, 233.81666666666666]
0.7399624587164683
[173.1911111111111, 233.78666666666666]
0.7408083342838675
[173.09555555555556, 233.82]
0.7402940533553827
[172.79555555555555, 233.8088888888889]
0.7390461345448324
[172.96555555555557, 233.7511111111111]
0.7399560786401491
[173.0688888888889, 233.91666666666666]
0.7398741242132764
[173.05333333333334, 233.70888888888888]
0.7404653462522227
[172.9777777777778, 233.7288888888889]
0.7400787236874632
[173.3788888888889, 233.7122222222222]
0.7418477614920534
[173.6211111111111, 234.02666666666667]
0.7418860148890914
[173.9, 233.83444444444444]
0.7436885545804012
[174.06333333333333, 233.85444444444445]
0.7443233920434839
[174.1911111111111, 233.86666666666667]
0.7448308627898137
[173.57666666666665, 233.7811111111111]
0.7424751548219369
[173.0822222222222, 233.82777777777778]
0.74021240704222
[173.26666666666668, 233.82222222222222]
0.7410188177152633
[173.34666666666666, 233.89111111111112]
0.7411426019705276
[173.76777777777778, 233.76777777777778]
0.743335028589626
[174.1511111111111, 233.48666666666668]
0.7458717604621724
[173.01666666666668, 233.14555555555555]
0.742097211565498
[173.01444444444445, 233.47444444444446]
0.7410423220242995
[174.6677777777778, 233.76888888888888]
0.747181451766227
[174.92, 233.92111111111112]
0.7477734658883098
[174.83444444444444, 233.85111111111112]
0.7476314464093963
[174.92777777777778, 233.75333333333333]
0.7483434579661371
[174.82888888888888, 233.70777777777778]
0.7480661985290272
[174.4322222222222, 233.83555555555554]
0.7459610742592134
[174.74, 233.73444444444445]
0.7476005533345059
[174.31222222222223, 233.73333333333332]
0.7457739113899982
[174.89333333333335, 233.75222222222223]
0.7481996606092871
[175.7711111111111, 233.9411111111111]
0.7513476800904312
[175.14555555555555, 233.76666666666668]
0.7492323779647321
[175.14333333333335, 233.76777777777778]
0.7492193107119601
[175.14222222222222, 233.85666666666665]
0.7489297813000366
[175.38, 233.67777777777778]
0.7505206599781276
[175.5811111111111, 233.59222222222223]
0.7516564954122331
[175.88888888888889, 233.82333333333332]
0.7522298411431233
[176.4088888888889, 233.7288888888889]
0.7547585997071631
[175.86666666666667, 233.9111111111111]
0.7518525555766674
[175.59777777777776, 233.88333333333333]
0.750792180336825
[175.61888888888888, 233.84777777777776]
0.7509966122311285
[175.73888888888888, 233.77777777777777]
0.7517347908745247
[175.59, 233.73888888888888]
0.7512228745276068
[175.45, 233.86]
0.7502351834430855
[175.36444444444444, 233.91444444444446]
0.7496948076932212
[175.55666666666667, 233.88111111111112]
0.7506235361745996
[175.67444444444445, 233.9]
0.7510664576504679
[176.0611111111111, 233.99777777777777]
0.7524050560784052
[176.23777777777778, 233.86777777777777]
0.7535787078168575
[177.09666666666666, 233.89333333333335]
0.7571685098620453
[174.86888888888888, 233.75222222222223]
0.7480950864400575
[176.04, 233.73888888888888]
0.7531480997314192
[175.29666666666665, 233.76333333333332]
0.7498894893695903
[175.63444444444445, 233.67222222222222]
0.7516273983024655
[175.4111111111111, 233.74]
0.7504539706986869
[175.2722222222222, 233.91666666666666]
0.7492934330839568
[175.65555555555557, 233.6988888888889]
0.7516319670611281
[175.09777777777776, 233.86444444444444]
0.7487148300534973
[175.4788888888889, 233.95222222222222]
0.7500629283281962
[175.18444444444444, 233.65333333333334]
0.7497622308453169
[175.23444444444445, 233.82111111111112]
0.7494380794434492
[175.11555555555555, 233.6977777777778]
0.7493248640219086
[175.50666666666666, 233.91555555555556]
0.7502992532917862
[175.8322222222222, 233.82444444444445]
0.7519839195597836
[176.05666666666667, 233.7288888888889]
0.7532516305691305
[175.7111111111111, 233.97555555555556]
0.7509806342542905
[175.55444444444444, 234.0988888888889]
0.7499157526021767
[175.1, 233.79777777777778]
0.7489378285127698
[175.19333333333333, 233.9322222222222]
0.748906378390702
[174.9611111111111, 233.7411111111111]
0.7485251964424078
[175.2277777777778, 233.96444444444444]
0.7489504578093538
[174.16555555555556, 233.88222222222223]
0.7446720571607742
[174.39777777777778, 233.69555555555556]
0.7462605669294333
[174.17666666666668, 233.82666666666665]
0.7448965045332726
[174.42111111111112, 233.92444444444445]
0.7456301179868143
[174.62333333333333, 233.76333333333332]
0.7470090832608479
[174.52333333333334, 233.71333333333334]
0.7467410217645549
[174.70666666666668, 233.8177777777778]
0.7471915451728791
[174.65, 233.94333333333333]
0.7465483094196601
[174.7, 233.7877777777778]
0.7472589100276128
[174.99444444444444, 233.86222222222221]
0.748280088941257
[175.01333333333332, 233.8322222222222]
0.748456870785796
[174.98222222222222, 233.95666666666668]
0.7479257792278722
[174.98333333333332, 233.71444444444444]
0.7487056854756279
[175.08555555555554, 233.81]
0.7488368998569588
[174.9388888888889, 233.79111111111112]
0.7482700606429291
[175.06666666666666, 233.90777777777777]
0.7484431186079984
[174.79333333333332, 233.77666666666667]
0.7476936677455691
[174.85777777777778, 233.72333333333333]
0.7481400135963224
[175.51555555555555, 233.76666666666668]
0.7508151528114454
[175.45111111111112, 233.84666666666666]
0.750282711368323
[174.79555555555555, 233.79555555555555]
0.7476427648087598
[174.51222222222222, 233.73111111111112]
0.7466366860304814
[174.93777777777777, 233.76111111111112]
0.748361337547829
[175.17111111111112, 233.97333333333333]
0.7486798115644708
[174.80333333333334, 233.65444444444444]
0.7481275768109602
[174.96444444444444, 233.8022222222222]
0.748343804355058
[174.52444444444444, 233.72444444444446]
0.7467102761086178
[174.94666666666666, 233.94444444444446]
0.7478128710520066
[177.35666666666665, 233.71666666666667]
0.7588533124153176
[180.96777777777777, 233.6888888888889]
0.7743961582350704
[180.92222222222222, 233.8]
0.7738332858093336
[177.43444444444444, 233.97222222222223]
0.7583568799715066
[176.5688888888889, 233.89777777777778]
0.7548976760978205
[176.3488888888889, 233.7877777777778]
0.7543118402729921
[176.18666666666667, 233.87222222222223]
0.7533458441219089
[176.42888888888888, 233.94222222222223]
0.754155821950339
[176.5688888888889, 234.04888888888888]
0.7544102846508802
[176.51888888888888, 233.9388888888889]
0.7545512835735828
[177.98666666666668, 233.86333333333334]
0.7610712809475619
[178.1511111111111, 233.9488888888889]
0.7614958632939768
[179.03333333333333, 233.91444444444446]
0.7653795547279869
[177.1977777777778, 233.83333333333334]
0.7577952007602756
[175.82333333333332, 233.89444444444445]
0.7517208617372508
[175.15, 233.98333333333332]
0.7485575895719069
[175.29555555555555, 233.87777777777777]
0.7495177918190888
[176.20333333333335, 233.8311111111111]
0.7535495704402038
[176.2411111111111, 233.9177777777778]
0.7534318801478201
[175.86111111111111, 234.07555555555555]
0.7513006246795907
[175.64666666666668, 233.89222222222222]
0.7509726702232273
[178.82444444444445, 233.92]
0.7644683842529261
[179.76444444444445, 233.92222222222222]
0.7684795516078469
[180.1911111111111, 234.07111111111112]
0.7698135419435688
[180.14777777777778, 233.88444444444445]
0.7702426649437518
[178.09666666666666, 233.84444444444443]
0.761603154993823
[172.9777777777778, 233.88111111111112]
0.7395970412317749
[162.90333333333334, 233.83666666666667]
0.6966543598808285
[154.47444444444446, 233.85777777777778]
0.6605486715572618
[152.04666666666665, 233.78666666666666]
0.6503650051328846
[147.58333333333334, 233.82777777777778]
0.6311625365297346
[143.81555555555556, 233.7722222222222]
0.6151952280234797
[140.88777777777779, 233.96333333333334]
0.6021788789316465
[138.71777777777777, 233.93666666666667]
0.5929715070080696
[137.67222222222222, 233.83777777777777]
0.5887509859636785
[138.23666666666668, 233.82555555555555]
0.5911957157044901
[138.06222222222223, 233.8788888888889]
0.5903150253455017
[138.14222222222222, 233.8177777777778]
0.5908114581155315
[138.17444444444445, 233.6677777777778]
0.5913286194549717
[138.26888888888888, 233.75333333333333]
0.5915162231792297
[137.20333333333335, 233.76222222222222]
0.5869354424724079
[135.96333333333334, 233.65666666666667]
0.5818936616402984
[136.35888888888888, 233.64222222222222]
0.5836226328955002
[134.88222222222223, 233.72]
0.5771103124346322
[135.66444444444446, 233.69333333333333]
0.5805233829710352
[135.76111111111112, 233.89777777777778]
0.5804292473445191
[135.59555555555556, 233.68333333333334]
0.5802534293797399
[135.0611111111111, 233.63888888888889]
0.5780763286172869
[134.95111111111112, 233.66555555555556]
0.5775395983813523
[135.01666666666668, 233.79111111111112]
0.5775098378419482
[135.13333333333333, 233.56666666666666]
0.5785642928500071
[135.84777777777776, 233.68555555555557]
0.581327234603004
[136.07333333333332, 233.65333333333334]
0.5823727459484136
[136.04222222222222, 233.73]
0.582048612596681
[135.95777777777778, 233.63]
0.5819363000375712
[135.66666666666666, 233.60111111111112]
0.5807620778059465
[135.52666666666667, 233.66555555555556]
0.5800027579779267
[135.2422222222222, 233.78222222222223]
0.578496606528393
[134.9411111111111, 233.61666666666667]
0.5776176547525623
[136.12777777777777, 233.6977777777778]
0.5824949602525579
[137.07555555555555, 233.63111111111112]
0.5867179028668176
[137.2122222222222, 233.85]
0.5867531418525646
[137.18777777777777, 233.61]
0.587251306783861
[137.4088888888889, 233.59444444444443]
0.588236972911266
[137.7122222222222, 233.72444444444446]
0.5892076139043126
[137.89888888888888, 233.87]
0.5896390682382899
[138.84777777777776, 233.60333333333332]
0.5943741289840803
[140.47, 233.78222222222223]
0.6008583487005951
[140.45111111111112, 233.83777777777777]
0.6006348180600036
[140.62, 233.86777777777777]
0.6012799255039648
[140.40444444444444, 233.62444444444444]
0.6009835348279765
[148.9922222222222, 233.76]
0.6373726138869876
[157.48, 233.85111111111112]
0.6734199348113233
[159.24, 233.6988888888889]
0.6813896324329979
[156.96444444444444, 233.7488888888889]
0.6715088366433114
[154.23444444444445, 233.72666666666666]
0.6598923719064055
[157.11666666666667, 233.78222222222223]
0.6720642193114199
[158.78666666666666, 233.67111111111112]
0.6795305842970176
[157.89, 234.00555555555556]
0.6747275705704993
[157.9188888888889, 233.71777777777777]
0.6756819716086828
[157.75333333333333, 233.75555555555556]
0.6748645308489399
[158.76222222222222, 233.77777777777777]
0.679115969581749
[159.20666666666668, 233.88555555555556]
0.6807032879328447
[159.60222222222222, 233.5811111111111]
0.6832839413384835
[159.26222222222222, 232.88555555555556]
0.6838647499725664
[159.27333333333334, 232.48222222222222]
0.685098980089278
[162.34666666666666, 233.43555555555557]
0.6954667479009196
[162.3177777777778, 233.3011111111111]
0.6957436979392393
[162.45555555555555, 233.1688888888889]
0.6967291233821932
[163.11, 233.08666666666667]
0.6997826273489117
[163.24, 233.34444444444443]
0.6995666873006048
[163.8711111111111, 233.14333333333335]
0.7028771046900094
[164.08, 233.04888888888888]
0.7040582805706004
[163.2588888888889, 232.91555555555556]
0.7009359615311224
[163.13111111111112, 232.82444444444445]
0.7006614425747583
[162.70555555555555, 232.76888888888888]
0.6990004391575811
[162.14777777777778, 232.68777777777777]
0.6968469909607056
[162.45444444444445, 232.7511111111111]
0.6979749470106361
[162.10444444444445, 232.79444444444445]
0.6963415507242918
[162.50333333333333, 232.67]
0.6984283892780906
[163.04888888888888, 232.6988888888889]
0.700686151392596
[163.29777777777778, 232.55333333333334]
0.7021949564735449
[164.85, 232.82555555555555]
0.7080408317147315
[165.12555555555556, 232.9088888888889]
0.7089706036695322
[168.85, 233.13333333333333]
0.7242636545610524
[165.13777777777779, 233.25444444444443]
0.7079726955303937
[162.4911111111111, 233.1211111111111]
0.6970244365113032
[158.5377777777778, 233.14444444444445]
0.6799980936948959
[152.1688888888889, 233.07777777777778]
0.6528674262287267
[144.21555555555557, 232.92888888888888]
0.6191398423934821
[142.78555555555556, 233.0522222222222]
0.6126762242129804
[145.0222222222222, 233.9111111111111]
0.6199885996579897
[144.95444444444445, 233.71]
0.6202321015123206
[145.4111111111111, 233.87777777777777]
0.6217397501068934
[146.03444444444443, 233.7422222222222]
0.6247670748402798
[146.32555555555555, 234.01777777777778]
0.6252753826869754
[146.48777777777778, 233.72]
0.6267661209044061
[146.09, 233.77]
0.6249304872310391
[146.33333333333334, 233.82]
0.6258375388475466
[145.9922222222222, 233.9111111111111]
0.6241354740642219
[145.45222222222222, 233.7888888888889]
0.6221519889739081
[144.89555555555555, 233.77444444444444]
0.619809217812041
[144.7111111111111, 233.7422222222222]
0.6191055673866748
[143.70333333333335, 233.66444444444446]
0.6149987161076187
[143.57333333333332, 233.78222222222223]
0.6141328111632858
[143.55444444444444, 233.73444444444445]
0.6141775329077158
[143.63666666666666, 233.7788888888889]
0.6144124790281414
[143.61, 233.96444444444444]
0.613811215379355
[143.70888888888888, 233.95111111111112]
0.6142688880867797
[143.72666666666666, 233.87666666666667]
0.6145404272907372
[143.5388888888889, 234.05555555555554]
0.6132684547828151
[143.36111111111111, 233.89444444444445]
0.612930809244436
[142.96444444444444, 233.94555555555556]
0.611101348366904
[143.56, 233.91444444444446]
0.613728666226493
[143.63888888888889, 233.98666666666668]
0.6138763842194237
[142.79111111111112, 233.88111111111112]
0.6105286161535063
[143.38555555555556, 233.57888888888888]
0.6138635055489223
[141.84777777777776, 233.69222222222223]
0.6069854461946624
[141.80666666666667, 233.98111111111112]
0.6060603182593087
[141.42555555555555, 233.92]
0.6045894132846937
[141.44222222222223, 233.87777777777777]
0.6047698227944321
[140.2, 233.98666666666668]
0.5991794404239557
[140.1211111111111, 234.00222222222223]
0.5988024805082572
[139.98, 233.8322222222222]
0.5986343484644736
[140.04333333333332, 234.03444444444443]
0.5983877017153221
[139.74444444444444, 233.72333333333333]
0.5979054057266189
[140.38444444444445, 233.79]
0.6004724087618994
[140.21777777777777, 233.88444444444445]
0.5995173304955913
[139.9, 233.84]
0.5982723229558673
[140.0911111111111, 233.87333333333333]
0.5990042093060821
[139.93444444444444, 233.94444444444446]
0.598152457848492
[139.5611111111111, 233.88]
0.5967210155255306
[139.57888888888888, 233.95222222222222]
0.5966127936853204
[139.23555555555555, 233.99444444444444]
0.5950378688952729
[139.54666666666665, 234.21666666666667]
0.5958016081975378
[139.70222222222222, 234.17666666666668]
0.596567643611898
[139.4911111111111, 234.43444444444444]
0.5950111616135285
[139.56, 234.2788888888889]
0.5957002812412556
[139.43777777777777, 234.19222222222223]
0.5953988414075806
[139.35666666666665, 234.25222222222223]
0.5949000839550911
[140.02666666666667, 234.33444444444444]
0.5975505094807516
[140.24555555555557, 234.36111111111111]
0.5984164987554819
[139.87222222222223, 234.28555555555556]
0.5970159871382027
[140.6211111111111, 234.30777777777777]
0.6001555409077329
[140.37777777777777, 234.26555555555555]
0.5992250010671649
[139.98888888888888, 234.3711111111111]
0.5972958366124
[140.67111111111112, 234.36222222222221]
0.6002294643619089
[140.67444444444445, 234.32777777777778]
0.6003319187273287
[140.2122222222222, 234.39777777777778]
0.5981806805146047
[140.42, 234.45444444444445]
0.5989223208488736
[140.88111111111112, 234.61444444444444]
0.6004792733231354
[140.85555555555555, 234.46777777777777]
0.6007458973277541
[140.9011111111111, 234.5588888888889]
0.600706763996722
[140.65333333333334, 234.59666666666666]
0.5995538441864761
[140.83333333333334, 234.64777777777778]
0.6001903562313254
[140.64111111111112, 234.4911111111111]
0.5997716094426702
[140.54444444444445, 234.54777777777778]
0.5992145641968232
[140.7211111111111, 234.60666666666665]
0.5998171881068076
[140.73444444444445, 234.81666666666666]
0.599337544656588
[140.59666666666666, 234.72444444444446]
0.5989860451025315
[140.45222222222222, 234.68333333333334]
0.5984754870629453
[141.60777777777778, 234.66222222222223]
0.6034536638951495
[141.39222222222222, 234.91666666666666]
0.6018824642308147
[142.24, 234.65222222222224]
0.6061736754629783
[142.3011111111111, 234.69222222222223]
0.606330749965676
[140.7577777777778, 234.75222222222223]
0.5996014710545872
[140.49444444444444, 234.99666666666667]
0.5978571800072814
[140.38111111111112, 234.79555555555555]
0.5978865774479927
[140.46, 234.80777777777777]
0.5981914284497485
[140.3411111111111, 234.88]
0.5975013245534363
[139.9988888888889, 235.00222222222223]
0.5957343192972171
[140.38444444444445, 234.87555555555556]
0.5976971256646546
[140.35333333333332, 234.9922222222222]
0.5972679946854033
[140.35444444444445, 234.8311111111111]
0.5976824952211519
[140.35, 235.06444444444443]
0.5970703069607389
[140.28666666666666, 234.9488888888889]
0.597094403510929
[140.22333333333333, 234.95222222222222]
0.5968163740145751
[141.2711111111111, 235.07777777777778]
0.6009547667438673
[142.22555555555556, 235.29111111111112]
0.6044663348476119
[143.00222222222223, 235.17333333333335]
0.6080715878595456
[145.46555555555557, 235.35777777777778]
0.6180613911680563
[147.2288888888889, 235.15333333333334]
0.6260973927177539
[149.33555555555554, 235.36666666666667]
0.6344804796298918
[152.02777777777777, 235.30777777777777]
0.6460805469904664
[152.68333333333334, 235.17555555555555]
0.6492313071086375
[153.14444444444445, 235.26888888888888]
0.6509336834449472
[153.14666666666668, 235.29]
0.6508847238160002
[151.0311111111111, 235.2788888888889]
0.6419237689550462
[146.87444444444444, 235.15222222222224]
0.6245930531995822
[143.88666666666666, 235.17888888888888]
0.6118179541814505
[143.04555555555555, 235.31]
0.6079025776871172
[142.64888888888888, 235.34666666666666]
0.6061224104394463
[142.22555555555556, 235.29111111111112]
0.6044663348476119
[143.21444444444444, 235.35444444444445]
0.6085053748719426
[144.39444444444445, 235.23222222222222]
0.6138378623487901
[146.79333333333332, 235.24333333333334]
0.6240063480367846
[148.61111111111111, 235.06222222222223]
0.6322203104615326
[149.82333333333332, 235.02333333333334]
0.6374828031259308
[148.94, 234.8111111111111]
0.6342970709317182
[148.08, 234.72666666666666]
0.6308614274759295
[147.18333333333334, 234.61777777777777]
0.6273323987952035
[146.06444444444443, 234.6822222222222]
0.6223924550455936
[146.35777777777778, 234.55333333333334]
0.6239850685463624
[145.61666666666667, 234.72555555555556]
0.6203698882382735
[145.96555555555557, 234.67]
0.6220034753294225
[145.98333333333332, 234.7411111111111]
0.6218907827535771
[145.70111111111112, 234.5211111111111]
0.6212707692745026
[145.76333333333332, 234.56555555555556]
0.6214183194463523
[146.18444444444444, 234.66222222222223]
0.6229568741832231
[146.5222222222222, 234.55777777777777]
0.6246743280499474
[146.09666666666666, 234.7188888888889]
0.6224325079172721
[146.17333333333335, 234.64666666666668]
0.6229508196721312
[145.85111111111112, 234.64666666666668]
0.6215775965754657
[145.79, 234.73111111111112]
0.6210936390574557
[145.75666666666666, 234.72555555555556]
0.6209663294722442
[145.59555555555556, 234.6]
0.6206119162640902
[145.64444444444445, 234.38333333333333]
0.6213942022802152
[146.0077777777778, 231.9688888888889]
0.6294282758224283
[146.20888888888888, 232.56666666666666]
0.6286751707992929
[154.36777777777777, 232.39888888888888]
0.6642362987009882
[199.62444444444444, 234.57666666666665]
0.8509987258370871
[145.00222222222223, 235.36111111111111]
0.6160840316298832
[121.69333333333333, 235.57333333333332]
0.5165836540638442
[120.11666666666666, 236.32555555555555]
0.5082677850234846
[135.0077777777778, 236.52777777777777]
0.5707903699354082
[174.0377777777778, 236.57555555555555]
0.7356541015790117
[196.25, 236.59777777777776]
0.8294667931510581
[205.96, 240.38888888888889]
0.8567783683845621
[208.14666666666668, 243.48888888888888]
0.8548507803230811
[206.8711111111111, 243.3]
0.8502717267205553
[209.60333333333332, 240.99666666666667]
0.8697354043624392
[212.76333333333332, 238.41333333333333]
0.8924137352497064
[209.67777777777778, 238.67]
0.8785259051316788
[203.56444444444443, 240.46666666666667]
0.8465391368635061
[193.72333333333333, 237.4622222222222]
0.8158069587677105
[184.9111111111111, 233.69333333333333]
0.791255396435975
[169.87222222222223, 233.2]
0.7284400609872309
[138.37555555555556, 232.76]
0.5944988638750454
[111.3, 232.1822222222222]
0.47936486667559963
[118.68888888888888, 232.13333333333333]
0.5112961899291595
[130.33777777777777, 231.40555555555557]
0.5632439440136364
[105.88, 229.91666666666666]
0.46051467923160566
[124.55333333333333, 229.13333333333333]
0.5435845213849287
[156.88333333333333, 228.84666666666666]
0.6855390800244705
[180.39666666666668, 228.4477777777778]
0.7896626021993842
[191.71444444444444, 227.8]
0.8415910642864111
[160.53333333333333, 228.03333333333333]
0.7039906446425961
[127.99444444444444, 228.45222222222222]
0.5602678897119261
[117.29222222222222, 228.38777777777779]
0.5135661083245358
[109.26555555555555, 227.87]
0.4795082966408722
[104.35777777777778, 227.36222222222221]
0.45899348078934255
[100.49666666666667, 226.84444444444443]
0.4430201802507837
[105.26333333333334, 226.30777777777777]
0.46513352023056115
[115.68777777777778, 226.54888888888888]
0.5106525939949189
[116.08, 226.39555555555555]
0.5127309134454936
[112.87222222222222, 226.2111111111111]
0.49896851515300356
[120.54888888888888, 225.9411111111111]
0.5335411882152183
[129.12444444444444, 225.7111111111111]
0.5720783695973221
[130.02555555555554, 225.61111111111111]
0.5763260280719034
[123.99666666666667, 225.28666666666666]
0.5503950522297517
[117.05444444444444, 225.40333333333334]
0.5193110621453887
[116.19, 225.40555555555557]
0.5154708796490276
[145.2188888888889, 225.39666666666668]
0.6442814396348167
[164.41222222222223, 224.64]
0.731892014878126
[174.35, 223.9477777777778]
0.7785297167494405
[180.18666666666667, 223.60888888888888]
0.805811734775004
[184.77777777777777, 223.78555555555556]
0.8256912619720267
[186.09, 223.88555555555556]
0.8311835908226922
[187.7, 223.6811111111111]
0.83914103907845
[188.54888888888888, 223.8]
0.8424883328368582
[189.35888888888888, 223.73666666666668]
0.8463471442121938
[188.06333333333333, 223.62333333333333]
0.8409826046775083
[186.71444444444444, 224.73222222222222]
0.8308307664924676
[186.79777777777778, 233.41555555555556]
0.8002799013680894
[187.01222222222222, 242.09444444444443]
0.7724763063083737
[187.79555555555555, 235.1677777777778]
0.7985598934094335
[188.79777777777778, 222.14444444444445]
0.8498874606112139
[190.04444444444445, 212.73222222222222]
0.893350534579205
[190.0077777777778, 210.27333333333334]
0.9036227978398487
[190.64777777777778, 212.32333333333332]
0.8979125128865305
[189.71444444444444, 231.61111111111111]
0.8191076996881745
[183.30555555555554, 228.99444444444444]
0.8004803609985686
[148.28222222222223, 227.7411111111111]
0.6510999331599722
[112.08555555555556, 227.50666666666666]
0.49266932348746806
[79.22444444444444, 228.74444444444444]
0.3463447806868412
[67.18222222222222, 229.15777777777777]
0.2931701593273921
[46.92111111111111, 229.60777777777778]
0.20435331749311628
[39.26, 229.68666666666667]
0.17092851130525644
[37.013333333333335, 229.82222222222222]
0.16105202088570877
[35.275555555555556, 229.99555555555557]
0.15337494444337088
[34.806666666666665, 229.7511111111111]
0.15149727241072464
[34.595555555555556, 230.12222222222223]
0.15033557046979865
[34.26111111111111, 230.36222222222221]
0.14872712539671823
[34.14111111111111, 230.2711111111111]
0.148264847233213
[36.16444444444444, 230.40333333333334]
0.15696146371339148
[35.66111111111111, 230.12555555555556]
0.1549637154596766
[34.73555555555556, 230.18444444444444]
0.15090314047671916
[33.666666666666664, 230.68]
0.14594532107970637
[33.315555555555555, 230.2211111111111]
0.1447111231231811
[34.184444444444445, 230.1977777777778]
0.1485003233934105
[35.346666666666664, 230.04111111111112]
0.1536536947502137
[36.57888888888889, 230.10666666666665]
0.15896492447946847
[34.91555555555556, 229.92555555555555]
0.15185591471635748
[36.66222222222222, 230.04]
0.15937324909677544
[50.30111111111111, 229.65555555555557]
0.21902849678262132
[81.65222222222222, 229.32666666666665]
0.35605201701599853
[140.59, 228.00444444444443]
0.6166107873140875
[169.76666666666668, 227.04333333333332]
0.7477280401685436
[171.7288888888889, 227.01111111111112]
0.7564779012285252
[156.57555555555555, 227.27666666666667]
0.6889205031557231
[139.35888888888888, 226.95]
0.6140510636214536
[135.79444444444445, 227.17888888888888]
0.597742356733069
[134.48888888888888, 227.32222222222222]
0.5916222689281001
[133.63, 226.66]
0.5895614576899321
[134.35666666666665, 227.1822222222222]
0.591404843884498
[135.93666666666667, 227.21]
0.5982864603964028
[138.4777777777778, 227.04444444444445]
0.6099148478026818
[141.7577777777778, 227.22333333333333]
0.6238698099275799
[145.70888888888888, 226.97666666666666]
0.6419553649665408
[150.0311111111111, 226.88333333333333]
0.6612698645902201
[157.15, 226.80555555555554]
0.692884262094305
[168.7288888888889, 226.82222222222222]
0.7438816498481434
[161.7577777777778, 226.88777777777779]
0.7129417871781939
[207.89444444444445, 226.84444444444443]
0.916462578369906
[232.84555555555556, 226.62777777777777]
1.0274360797195599
[137.68444444444444, 226.39555555555555]
0.6081587781464104
[67.77888888888889, 226.21]
0.2996281724454661
[53.30111111111111, 226.39333333333335]
0.2354358687436811
[79.01666666666667, 226.36]
0.3490752194145019
[111.52777777777777, 226.70222222222222]
0.4919571439774153
[114.26777777777778, 226.7788888888889]
0.503873082444476
[114.45, 226.3388888888889]
0.5056576912692373
[115.72, 226.5811111111111]
0.5107221843538983
[116.81777777777778, 225.97555555555556]
0.5169487358514687
[117.75555555555556, 228.92666666666668]
0.5143811215624605
[115.88777777777777, 229.70222222222222]
0.5045130894104444
[115.15555555555555, 230.14111111111112]
0.5003693386183355
[114.69444444444444, 230.21555555555557]
0.49820458121374167
[114.88777777777777, 230.35444444444445]
0.49874348226645887
[115.13777777777777, 230.54222222222222]
0.4994216533004318
[114.64888888888889, 230.6822222222222]
0.4969992389723237
[114.71888888888888, 230.54666666666665]
0.4975950880033929
[115.16444444444444, 230.52666666666667]
0.4995710305869651
[114.67222222222222, 230.2277777777778]
0.49808160999975865
[116.02444444444444, 230.94]
0.5024008159887609
[115.92, 231.22]
0.5013407144710665
[116.25666666666666, 230.92888888888888]
0.5034305895032621
[116.05888888888889, 231.01555555555555]
0.5023856017391807
[116.35666666666667, 230.94222222222223]
0.5038345329279088
[118.38111111111111, 231.72666666666666]
0.510865291483261
[118.65555555555555, 231.54555555555555]
0.5124501537974289
[118.61666666666666, 231.51444444444445]
0.5123510412117314
[118.79888888888888, 231.52333333333334]
0.5131184281881835
[118.74, 231.52555555555554]
0.512859151617532
[118.72777777777777, 231.5077777777778]
0.5128457407238537
[118.97666666666667, 231.54666666666665]
0.5138345042036163
[121.0911111111111, 232.16444444444446]
0.5215747458697857
[121.47777777777777, 232.27777777777777]
0.5229849318344894
[121.60555555555555, 232.5611111111111]
0.5228972074245718
[122.19555555555556, 232.29777777777778]
0.5260298084833642
[122.64666666666666, 232.31333333333333]
0.5279364077251987
[122.37777777777778, 232.22666666666666]
0.5269755602763584
[124.36444444444444, 232.62]
0.534624900887475
[124.18888888888888, 231.9911111111111]
0.5353174451128395
[120.55111111111111, 230.64222222222222]
0.5226758134291688
[107.38777777777777, 231.21666666666667]
0.4644465268266897
[101.64888888888889, 231.47]
0.43914498159108695
[103.18222222222222, 231.26666666666668]
0.4461612376285192
[116.25444444444445, 232.26222222222222]
0.5005310090128017
[121.17888888888889, 232.05777777777777]
0.5221927489322583
[125.84, 232.28222222222223]
0.5417547619275402
[128.85333333333332, 232.2511111111111]
0.5548017949920105
[130.1888888888889, 232.4788888888889]
0.5600030588201558
[130.24777777777777, 232.62555555555556]
0.5599031347468272
[131.89555555555555, 232.66222222222223]
0.5668971709106191
[133.37777777777777, 232.7588888888889]
0.5730297923936548
[136.25222222222223, 233.22444444444446]
0.5842107269106536
[136.78, 233.31666666666666]
0.5862418744196014
[137.26222222222222, 233.30333333333334]
0.5883423106780395
[137.46777777777777, 233.2788888888889]
0.5892851189086977
[138.0677777777778, 233.27777777777777]
0.5918599666587283
[138.5, 233.2288888888889]
0.593837241431879
[139.49444444444444, 233.34]
0.5978162528689657
[140.23222222222222, 233.42666666666668]
0.6007549361207898
[140.90444444444444, 233.60555555555555]
0.6031724892387452
[168.04222222222222, 233.56666666666666]
0.7194614908900623
[220.42222222222222, 233.6977777777778]
0.9431934882659465
[239.83555555555554, 233.66444444444446]
1.0264101417987808
[229.53333333333333, 233.78]
0.9818347734337126
[191.96444444444444, 233.75444444444443]
0.8212226505497222
[159.41, 235.04666666666665]
0.6782057463766061
[149.37333333333333, 232.62555555555556]
0.6421191901147767
[145.4322222222222, 232.59222222222223]
0.6252669192148395
[138.85222222222222, 232.65555555555557]
0.5968145565690816
[141.59333333333333, 230.99666666666667]
0.6129669980807804
[148.17, 230.87]
0.6417897518083769
[155.59555555555556, 230.64222222222222]
0.6746186975498367
[159.02, 230.36888888888888]
0.690284181891845
[168.5522222222222, 230.48222222222222]
0.7313024865740428
[169.15555555555557, 231.0611111111111]
0.7320814599312352
[161.61222222222221, 231.51444444444445]
0.6980653954876825
[154.34444444444443, 231.23777777777778]
0.6674707131668219
[146.05, 230.95111111111112]
0.6323849203294589
[150.44, 230.96444444444444]
0.6513556680200897
[158.14444444444445, 230.91333333333333]
0.6848649324903042
[169.75, 230.79555555555555]
0.7354994319166555
[181.11666666666667, 230.87]
0.7844963254934234
[190.39333333333335, 231.05777777777777]
0.8240074632607526
[195.80444444444444, 231.3177777777778]
0.8464738262899522
[193.81222222222223, 231.39555555555555]
0.8375797095881992
[186.77333333333334, 231.57333333333332]
0.806540764624597
[164.8388888888889, 231.10111111111112]
0.7132760552139276
[156.3011111111111, 231.09666666666666]
0.6763451561876463
[148.5822222222222, 231.31]
0.6423510536605517
[139.3788888888889, 231.20666666666668]
0.6028324827234893
[122.22111111111111, 231.25]
0.5285237237237237
[118.31666666666666, 230.89444444444445]
0.5124275161810351
[116.42666666666666, 230.90222222222224]
0.5042249725713626
[116.52111111111111, 230.88777777777779]
0.5046655662443034
[116.5411111111111, 230.97]
0.5045725034035204
[116.55, 230.9322222222222]
0.5046935368241764
[115.87333333333333, 230.5911111111111]
0.5025056376847908
[117.38666666666667, 230.67888888888888]
0.5088747706046405
[125.20666666666666, 230.67666666666668]
0.5427799372859557
[130.0211111111111, 230.72222222222223]
0.5635396099205393
[138.6688888888889, 230.88777777777779]
0.6005899932145967
[150.21555555555557, 230.61888888888888]
0.6513584220238297
[171.57444444444445, 230.62666666666667]
0.7439488543292672
[179.36222222222221, 230.62555555555556]
0.7777204993182792
[182.96555555555557, 230.5588888888889]
0.7935740688086438
[185.9177777777778, 230.3488888888889]
0.8071138466287854
[191.01555555555555, 230.04444444444445]
0.8303419629057187
[191.99333333333334, 229.82333333333332]
0.8353953036390271
[191.5611111111111, 230.06]
0.832657181218426
[190.6211111111111, 229.85444444444445]
0.8293122700839661
[187.8711111111111, 229.75555555555556]
0.8176999709836541
[182.62444444444444, 229.77]
0.7948141378093068
[178.10666666666665, 229.6511111111111]
0.7755532546955285
[177.21444444444444, 229.73888888888888]
0.771373298188765
[178.5311111111111, 229.69222222222223]
0.777262326881866
[184.54555555555555, 229.82777777777778]
0.8029732408325074
[188.1822222222222, 229.8177777777778]
0.8188323115898585
[190.92888888888888, 229.95222222222222]
0.8302980812439299
[189.96333333333334, 229.78222222222223]
0.8267103150809462
[176.60888888888888, 229.90555555555557]
0.7681801706014546
[166.82777777777778, 230.0377777777778]
0.7252190461470096
[156.01888888888888, 230.32333333333332]
0.6773907212565909
[151.28555555555556, 230.24666666666667]
0.657058613467682
[151.0311111111111, 230.3411111111111]
0.6556845644382485
[146.46666666666667, 230.23444444444445]
0.6361631380573425
[141.1988888888889, 230.45777777777778]
0.612688754749002
[134.3177777777778, 230.1977777777778]
0.5834885943488208
[127.31888888888889, 230.2877777777778]
0.5528686329664816
[122.46333333333334, 230.1511111111111]
0.532099683299861
[119.57, 230.01777777777778]
0.5198293851682961
[119.66888888888889, 229.96444444444444]
0.520379962119748
[122.35111111111111, 229.76777777777778]
0.5324989965714175
[122.93888888888888, 229.79777777777778]
0.5349872835053041
[120.25666666666666, 229.7577777777778]
0.5234062926173457
[117.72444444444444, 229.78444444444443]
0.5123255611539317
[115.23, 229.72333333333333]
0.5016033779764064
[115.39, 229.71666666666667]
0.5023144453312051
[117.22222222222223, 229.97444444444446]
0.5097184711344739
[122.57666666666667, 229.98111111111112]
0.5329858007662465
[130.81333333333333, 230.15666666666667]
0.568366475009776
[141.5611111111111, 229.71]
0.616260115411219
[156.10666666666665, 229.45555555555555]
0.6803350927315868
[162.59222222222223, 229.39222222222222]
0.7087957065288468
[170.70888888888888, 229.51111111111112]
0.7437935708752904
[172.70888888888888, 229.07]
0.7539568205740118
[176.25, 229.10444444444445]
0.7692997856387673
[186.56555555555556, 229.05555555555554]
0.8144991511035654
[182.33444444444444, 229.27]
0.7952826119616366
[154.13888888888889, 229.0688888888889]
0.672893161688381
[150.0522222222222, 229.08777777777777]
0.654998811712153
[146.13222222222223, 228.87444444444444]
0.638482040128746
[145.76444444444445, 228.87444444444444]
0.6368751426060868
[147.32777777777778, 228.75]
0.6440558591378264
[150.26777777777778, 228.29555555555555]
0.6582159578713753
[150.4111111111111, 227.88]
0.6600452479862695
[149.49, 227.57888888888888]
0.6568711216135065
[148.92, 227.42]
0.6548236742590801
[147.58666666666667, 226.62]
0.6512517282970023
[147.14, 226.36666666666667]
0.6500073626859078
[147.3311111111111, 226.04]
0.6517922098350342
[147.07111111111112, 226.27333333333334]
0.6499710281567034
[147.68555555555557, 226.41666666666666]
0.6522733406943934
[147.45777777777778, 226.22555555555556]
0.6518175076005757
[147.36, 226.45666666666668]
0.6507205204822115
[146.9788888888889, 226.46555555555557]
0.6490121136891065
[146.56555555555556, 226.3322222222222]
0.6475682256663018
[145.52666666666667, 226.04333333333332]
0.6437998613835106
[145.56555555555556, 226.07222222222222]
0.6438896124640602
[144.91222222222223, 226.17444444444445]
0.64070997312792
[144.04333333333332, 225.75666666666666]
0.6380468646182468
[141.13, 225.49333333333334]
0.6258721617786187
[141.14555555555555, 225.41444444444446]
0.6261602086034119
[140.4388888888889, 225.69222222222223]
0.6222584345445863
[140.38222222222223, 225.36777777777777]
0.6229028107143385
[139.34222222222223, 225.24555555555557]
0.6186236255740648
[140.27777777777777, 225.87333333333333]
0.6210462107572582
[140.50555555555556, 226.15777777777777]
0.621272268131393
[140.94222222222223, 226.1211111111111]
0.6233041290557175
[142.91444444444446, 226.3388888888889]
0.6314179818855699
[143.59222222222223, 226.1977777777778]
0.6348082798730708
[146.88555555555556, 227.26555555555555]
0.6463168393313745
[147.41, 227.18555555555557]
0.6488528711234576
[148.4388888888889, 227.3322222222222]
0.6529601806460442
[150.08333333333334, 227.97]
0.658346858504774
[151.6677777777778, 228.4188888888889]
0.6639896486474655
[152.72666666666666, 228.8188888888889]
0.6674565522465608
[153.85555555555555, 229.13444444444445]
0.6714641088928868
[154.85333333333332, 229.13888888888889]
0.675805552188144
[155.4488888888889, 229.2811111111111]
0.6779838432201132
[154.3388888888889, 229.64333333333335]
0.6720808596906314
[153.92222222222222, 229.44666666666666]
0.6708409603781077
[153.96666666666667, 229.67111111111112]
0.6703788992956111
[155.08555555555554, 229.86666666666667]
0.6746761407579273
[155.88666666666666, 230.15222222222224]
0.677319841457586
[158.0677777777778, 230.0511111111111]
0.6870985191696531
[173.89333333333335, 230.39111111111112]
0.7547744897565493
[175.62666666666667, 230.51888888888888]
0.7618753825909663
[175.30444444444444, 230.69222222222223]
0.7599061760980238
[179.17888888888888, 230.63222222222223]
0.776903102100988
[170.70444444444445, 230.76666666666668]
0.7397274784534643
[152.7122222222222, 230.85222222222222]
0.6615150625460251
[139.58555555555554, 230.9622222222222]
0.6043653122684807
[138.42222222222222, 230.89333333333335]
0.5995072279648129
[144.2277777777778, 231.04]
0.6242545783317944
[149.08777777777777, 231.10333333333332]
0.6451130566894078
[148.94333333333333, 230.8388888888889]
0.6452263483430001
[146.78555555555556, 230.63888888888889]
0.6364302059496568
[146.72555555555556, 230.40444444444444]
0.6368173839239213
[153.83777777777777, 230.38555555555556]
0.6677405508640105
[155.60222222222222, 230.59777777777776]
0.674777631084428
[157.46666666666667, 230.95]
0.6818214620769286
[164.59, 230.68555555555557]
0.713482036634765
[176.54777777777778, 231.01777777777778]
0.764217280055407
[180.85333333333332, 230.85111111111112]
0.7834198088233878
[187.17333333333335, 230.8711111111111]
0.8107265236976862
[191.25444444444443, 230.66444444444446]
0.8291457528492566
[192.66, 230.38777777777779]
0.8362422775127925
[190.64444444444445, 230.52333333333334]
0.8270071479869475
[189.34555555555556, 230.52777777777777]
0.8213567899746959
[188.4788888888889, 230.56555555555556]
0.8174633389395158
[185.9711111111111, 230.3188888888889]
0.807450539590037
[184.2, 230.33777777777777]
0.7996951337166672
[184.37, 230.57666666666665]
0.7996038916918452
[186.5511111111111, 230.37666666666667]
0.8097656494918949
[192.16666666666666, 230.75333333333333]
0.8327795914829688
[179.36444444444444, 230.89]
0.7768393799837345
[171.63888888888889, 231.26333333333332]
0.7421794298947328
[171.40222222222224, 231.14777777777778]
0.7415265847245389
[170.6588888888889, 231.03555555555556]
0.7386693726795298
[163.78333333333333, 230.6811111111111]
0.7099988921695655
[148.29888888888888, 230.61888888888888]
0.6430474520252268
[144.62444444444444, 229.79555555555555]
0.6293613646913198
[175.32333333333332, 228.97666666666666]
0.7656820927896583
[180.7588888888889, 228.60333333333332]
0.790709768983635
[169.6688888888889, 228.84222222222223]
0.7414230085745637
[160.15, 228.64444444444445]
0.7004325007289338
[158.92, 228.96333333333334]
0.6940849335410327
[162.16333333333333, 229.17]
0.707611525650536
[166.22, 229.08666666666667]
0.7255769286732823
[174.15333333333334, 229.3188888888889]
0.759437367663661
[180.0, 229.75]
0.7834602829162133
[172.22555555555556, 229.31444444444443]
0.7510453864901664
[167.24, 227.74666666666667]
0.7343246882501024
[163.01222222222222, 226.39222222222222]
0.7200433858642572
[159.80666666666667, 227.91555555555556]
0.7011661239055401
[158.78333333333333, 228.04222222222222]
0.6962891862130794
[159.1288888888889, 227.32555555555555]
0.7000043989774821
[157.73333333333332, 226.85222222222222]
0.695313150509142
[156.1811111111111, 226.13666666666666]
0.6906492140937388
[152.4911111111111, 225.88]
0.675097888751156
[151.06333333333333, 225.67]
0.6693992703209701
[149.67, 225.65333333333334]
0.6632740486882533
[149.37333333333333, 225.52333333333334]
0.6623409255509407
[149.84777777777776, 225.60444444444445]
0.6642057879080395
[149.14888888888888, 225.5811111111111]
0.6611763199243434
[150.39333333333335, 225.67777777777778]
0.6664073654669884
[151.89444444444445, 225.89888888888888]
0.672400139688848
[152.79555555555555, 225.83777777777777]
0.6765721707813869
[151.23444444444445, 226.2]
0.6685872875528048
[148.91444444444446, 226.87]
0.6563866727396502
[145.89, 227.26111111111112]
0.6419488107169922
[143.67444444444445, 226.99666666666667]
0.6329363622569103
[136.04888888888888, 227.11666666666667]
0.5990264426016976
[133.82555555555555, 227.26666666666668]
0.5888481470616994
[130.85222222222222, 227.59]
0.5749471515542081
[128.94333333333333, 227.4188888888889]
0.5669860316498678
[122.80222222222223, 227.4788888888889]
0.5398400828404101
[123.28222222222222, 227.6977777777778]
0.5414291848844471
[123.38666666666667, 227.5611111111111]
0.5422133248699983
[124.63333333333334, 228.18444444444444]
0.5461955727822522
[124.93666666666667, 228.02777777777777]
0.5479010841759046
[128.92777777777778, 227.78666666666666]
0.5660023023491766
[133.56222222222223, 227.73333333333332]
0.5864851678376269
[137.93, 227.7711111111111]
0.6055640652897158
[149.71444444444444, 227.48888888888888]
0.6581176125818111
[156.10555555555555, 227.36777777777777]
0.6865773025592408
[158.45111111111112, 227.46333333333334]
0.6966006731243619
[160.26333333333332, 227.03444444444443]
0.7058987623023427
[159.33666666666667, 227.50555555555556]
0.7003638494786453
[156.97333333333333, 227.39555555555555]
0.6903095926823548
[156.82111111111112, 227.49555555555557]
0.6893370322252937
[158.82333333333332, 227.34777777777776]
0.6985919760719016
[163.87666666666667, 227.24777777777777]
0.7211364980955687
[164.88555555555556, 227.23222222222222]
0.7256257670811553
[166.08, 227.4688888888889]
0.7301218237414641
[166.57, 227.33]
0.7327233537148637
[165.58555555555554, 227.31444444444443]
0.72844273473358
[165.14444444444445, 228.05444444444444]
0.7241448192195821
[161.62555555555556, 228.30666666666667]
0.70793182658802
[158.54555555555555, 228.13111111111112]
0.6949755988271851
[157.71666666666667, 228.14]
0.6913152742468076
[158.37777777777777, 228.22666666666666]
0.6939494849175284
[159.19666666666666, 228.15666666666667]
0.6977515449910149
[159.60777777777778, 228.16555555555556]
0.6995261725160581
[159.27777777777777, 228.17888888888888]
0.6980390629184704
[161.88777777777779, 228.2122222222222]
0.7093738284540219
[164.12333333333333, 228.0311111111111]
0.7197409710175999
[167.88777777777779, 228.56555555555556]
0.7345279010641246
[168.88222222222223, 228.28333333333333]
0.739792168601397
[168.91666666666666, 228.46333333333334]
0.7393600723675571
[168.88444444444445, 228.50444444444443]
0.7390860377138301
[168.67, 228.45111111111112]
0.7383198933883252
[168.3088888888889, 228.2488888888889]
0.7373919308357348
[168.76666666666668, 228.61777777777777]
0.7382044752036393
[169.04777777777778, 228.55]
0.7396533702812417
[169.79666666666665, 228.67333333333335]
0.7425293723215065
[170.42777777777778, 228.75333333333333]
0.7450286091763083
[170.69444444444446, 228.84555555555556]
0.7458936400580692
[171.63666666666666, 228.6988888888889]
0.7504919131900752
[172.35444444444445, 228.62]
0.7538904927147426
[172.68444444444444, 228.66666666666666]
0.7551797862001943
[173.10777777777778, 229.0]
0.7559291606016497
[173.65777777777777, 228.92777777777778]
0.7585701458490062
[174.72333333333333, 229.39333333333335]
0.7616757243744369
[174.5211111111111, 229.57444444444445]
0.7601939821021503
[174.39444444444445, 229.67777777777778]
0.7593004692564462
[173.5222222222222, 229.7711111111111]
0.755195992146774
[173.28666666666666, 229.5911111111111]
0.7547620891246274
[172.5677777777778, 229.67777777777778]
0.7513472981471627
[172.47333333333333, 229.70111111111112]
0.7508598129936971
[171.02555555555554, 229.8711111111111]
0.7440063030490516
[170.38777777777779, 229.84333333333333]
0.7413213831643777
[168.02777777777777, 229.83333333333334]
0.7310853275320279
[165.62666666666667, 230.2511111111111]
0.7193305859303369
[165.64333333333335, 230.42888888888888]
0.7188479453772194
[165.14222222222222, 230.39888888888888]
0.7167665739128758
[164.73111111111112, 230.42111111111112]
0.7149132747288781
[164.65, 230.5288888888889]
0.7142271877229174
[164.85666666666665, 230.42777777777778]
0.7154374713696747
[164.64777777777778, 230.32555555555555]
0.7148480652988765
[164.39222222222222, 230.23333333333332]
0.7140244196708653
[163.35111111111112, 230.08666666666667]
0.7099547030587509
[164.39222222222222, 230.61777777777777]
0.7128341266935189
[163.07333333333332, 230.66555555555556]
0.7069687233560855
[162.4922222222222, 230.29555555555555]
0.7055812337768858
[160.86333333333334, 230.04666666666665]
0.6992639174660215
[158.66222222222223, 229.99444444444444]
0.6898524118940071
[154.32222222222222, 229.7511111111111]
0.6716930398111967
[151.62444444444444, 229.73777777777778]
0.6599891663926022
[149.07444444444445, 229.64222222222222]
0.6491595622175559
[147.98444444444445, 229.22555555555556]
0.645584407400765
[147.47555555555556, 228.9711111111111]
0.6440793113153528
[148.49, 230.62333333333333]
0.6438637316258835
[148.95222222222222, 231.70777777777778]
0.6428451545768856
[150.82555555555555, 230.24666666666667]
0.6550607560973255
[151.66444444444446, 230.76777777777778]
0.6572167306238595
[152.35444444444445, 231.17777777777778]
0.6590358550418149
[152.71, 231.99777777777777]
0.6582390635925632
[152.65222222222224, 232.02333333333334]
0.6579175466069026
[152.81222222222223, 232.59333333333333]
0.6569931305951255
[151.76777777777778, 232.85222222222222]
0.6517772359197774
[151.12555555555556, 232.6677777777778]
0.649533669848759
[151.43777777777777, 232.8411111111111]
0.6503910630520574
[151.12555555555556, 232.84777777777776]
0.6490315561430215
[151.8788888888889, 232.76111111111112]
0.6525097262333819
[152.5211111111111, 232.7488888888889]
0.6553032834623868
[153.37, 232.89888888888888]
0.6585261129054574
[152.85222222222222, 232.7722222222222]
0.6566600634860021
[155.3088888888889, 233.40333333333334]
0.6654099008392721
[155.33, 233.12333333333333]
0.6662996697027325
[154.2577777777778, 232.72333333333333]
0.6628376087963295
[153.9711111111111, 232.5888888888889]
0.6619882482205129
[153.60222222222222, 232.67444444444445]
0.6601594025032592
[153.24444444444444, 232.62222222222223]
0.6587695834925487
[153.57777777777778, 233.15666666666667]
0.658689198011828
[154.25666666666666, 233.36444444444444]
0.6610118650846554
[155.18666666666667, 233.27444444444444]
0.6652536116257913
[156.45666666666668, 233.35666666666665]
0.6704615252760439
[156.0611111111111, 233.39]
0.6686709418188916
[158.38, 234.16555555555556]
0.6763590811818798
[158.46, 233.95]
0.6773242145757641
[158.47555555555556, 233.71777777777777]
0.6780637616118206
[158.67555555555555, 233.61333333333334]
0.6792230276049692
[158.74, 233.84777777777776]
0.6788176544095638
[158.4688888888889, 233.75444444444443]
0.6779288807342939
[157.87, 233.77]
0.67532189759165
[158.25222222222223, 233.8111111111111]
0.6768379033407784
[158.18666666666667, 233.90666666666667]
0.676281137775751
[157.88, 233.74444444444444]
0.6754385130959738
[157.7277777777778, 233.21666666666667]
0.6763143476500155
[159.73555555555555, 234.0211111111111]
0.682568998998191
[159.83444444444444, 234.15333333333334]
0.6826058897778284
[160.03333333333333, 233.9311111111111]
0.684104532198463
[159.7188888888889, 233.91444444444446]
0.6828090042418168
[159.6822222222222, 233.97]
0.6824901578075061
[159.65666666666667, 234.10666666666665]
0.6819825720469302
[159.63888888888889, 233.94666666666666]
0.6823730004939398
[159.42777777777778, 233.90444444444444]
0.6815936232269588
[159.65, 233.95]
0.6824107715323787
[160.04111111111112, 233.90666666666667]
0.6842092762545365
[160.49444444444444, 233.75222222222223]
0.6866007215617677
[162.48111111111112, 234.43444444444444]
0.6930769558891138
[162.31444444444443, 234.48666666666668]
0.6922118291492526
[162.69222222222223, 234.53333333333333]
0.6936848588213
[162.8411111111111, 234.57777777777778]
0.69418813944676
[162.6588888888889, 234.4188888888889]
0.6938813235565963
[162.58666666666667, 234.34555555555556]
0.6937902717259887
[162.82666666666665, 234.38555555555556]
0.694695824069553
[163.23111111111112, 234.33777777777777]
0.6965633653226113
[163.42666666666668, 234.26888888888888]
0.6976029443848949
[163.7111111111111, 234.36888888888888]
0.6985189539756889
[165.63222222222223, 235.00222222222223]
0.7048113020207847
[164.94333333333333, 235.08666666666667]
0.7016277684825454
[164.50444444444443, 235.15666666666667]
0.6995525441667729
[164.76555555555555, 234.98]
0.7011896993597564
[164.39222222222222, 235.04555555555555]
0.6994057889487144
[164.59777777777776, 235.09555555555556]
0.700131388655204
[164.55555555555554, 235.29777777777778]
0.6993502323297193
[164.5211111111111, 235.08333333333334]
0.6998416637126315
[164.61, 235.13777777777779]
0.7000576494159453
[164.63888888888889, 235.07]
0.7003823920061637
[164.56, 234.90222222222224]
0.7005467996140238
[164.29777777777778, 235.08777777777777]
0.6988784331148177
[164.4011111111111, 235.09]
0.6993113748398958
[166.25444444444443, 235.67777777777778]
0.7054311442176229
[166.29666666666665, 235.67777777777778]
0.7056102965442459
[165.9777777777778, 235.79888888888888]
0.7038955041725765
[166.30777777777777, 235.6288888888889]
0.7058038535173011
[166.29, 235.72666666666666]
0.7054356740858055
[166.41333333333333, 235.70111111111112]
0.7060354215084075
[166.62555555555556, 235.68555555555557]
0.7069824672232777
[166.9622222222222, 235.63666666666666]
0.7085579022317786
[166.50333333333333, 235.60333333333332]
0.7067104313747683
[166.57777777777778, 235.73555555555555]
0.7066298394622977
[166.18555555555557, 235.7877777777778]
0.7048098808250357
[166.7211111111111, 235.95333333333335]
0.7065851062827865
[166.45666666666668, 235.7722222222222]
0.7060062678196942
[166.56666666666666, 235.72]
0.7066293342383619
[166.43666666666667, 235.75444444444443]
0.7059746723285528
[168.63777777777779, 236.51888888888888]
0.712999196681496
[168.63, 236.33]
0.7135361570685058
[168.73555555555555, 236.35888888888888]
0.7138955355086192
[168.82333333333332, 236.5088888888889]
0.713813904105084
[169.18, 236.39777777777778]
0.7156581656153941
[169.5522222222222, 236.39888888888888]
0.7172293533998562
[169.2422222222222, 236.2511111111111]
0.7163658254399744
[169.75666666666666, 236.33444444444444]
0.7182899939351484
[169.07666666666665, 236.27555555555554]
0.715591023663519
[169.37555555555556, 236.50333333333333]
0.7161656166462301
[169.60333333333332, 236.34]
0.7176243265352176
[169.62555555555556, 236.2811111111111]
0.7178972316402779
[169.46444444444444, 236.3411111111111]
0.7170332899246381
[168.9911111111111, 236.35888888888888]
0.7149767538065935
[169.34444444444443, 236.07888888888888]
0.7173214226882727
[169.1511111111111, 236.15777777777777]
0.716263138579669
[168.9788888888889, 236.30444444444444]
0.7150897617950478
[168.5888888888889, 236.24]
0.7136339692215073
[168.38333333333333, 236.14777777777778]
0.7130422099156366
[168.25333333333333, 236.21555555555557]
0.7122872705720763
[168.37777777777777, 236.36666666666667]
0.7123583885676679
[170.7788888888889, 236.95555555555555]
0.7207211854074839
[170.98555555555555, 237.09666666666666]
0.7211638947077376
[171.22666666666666, 237.0077777777778]
0.7224516776289572
[170.91666666666666, 237.11888888888888]
0.7208057842526253
[170.46444444444444, 237.04444444444445]
0.7191244023624261
[169.91222222222223, 237.12777777777777]
0.7165428859264813
[170.0511111111111, 237.02444444444444]
0.7174412390658254
[169.9788888888889, 237.05]
0.7170592233237244
[170.03222222222223, 237.07111111111112]
0.7172203370765452
[169.65666666666667, 237.25]
0.7150965929048121
[169.6588888888889, 237.16555555555556]
0.71536057793665
[169.7488888888889, 237.14444444444445]
0.7158037764138125
[169.61555555555555, 237.07777777777778]
0.7154426582931058
[169.89777777777778, 237.25666666666666]
0.7160927453156685
[170.04777777777778, 237.1888888888889]
0.7169297793600974
[170.2277777777778, 237.13222222222223]
0.7178601717747717
[169.74777777777777, 237.01444444444445]
0.7161916995213605
[169.34777777777776, 237.23777777777778]
0.713831411523366
[169.83666666666667, 237.17444444444445]
0.7160833329429347
[169.53222222222223, 237.14222222222222]
0.7148968270330042
[169.62, 237.25222222222223]
0.7149353477546165
[169.17111111111112, 237.29666666666665]
0.7129097660219041
[168.89555555555555, 237.30444444444444]
0.7117252099974716
[169.09333333333333, 237.31555555555556]
0.7125252827927185
[168.8388888888889, 237.26444444444445]
0.7116063651434406
[169.22333333333333, 237.3488888888889]
0.7129729324856985
[169.77666666666667, 237.34333333333333]
0.7153209836664186
[169.4, 237.33666666666667]
0.7137540203087035
[169.7588888888889, 237.40555555555557]
0.7150586198020266
[169.17, 237.43777777777777]
0.7124813986354319
[169.34444444444443, 237.54666666666665]
0.7128891632989074
[169.22333333333333, 237.48111111111112]
0.712575970954415
[169.15777777777777, 237.4911111111111]
0.7122699329097697
[169.04111111111112, 237.48]
0.7118119888458444
[168.82777777777778, 237.51111111111112]
0.7108205464071856
[168.84444444444443, 237.44666666666666]
0.7110836585525638
[168.62333333333333, 237.46555555555557]
0.7100959671344148
[168.64555555555555, 237.42777777777778]
0.710302548143295
[168.54222222222222, 237.46555555555557]
0.7097543971289403
[168.51444444444445, 237.43666666666667]
0.7097237625940017
[168.97222222222223, 237.41555555555556]
0.7117150425414417
[169.15444444444444, 237.52777777777777]
0.7121459478423576
[169.23444444444445, 237.46444444444444]
0.7126727744036534
[169.15222222222224, 237.5811111111111]
0.7119767284155587
[169.50222222222223, 237.4388888888889]
0.7138772549661901
[169.34444444444443, 237.53333333333333]
0.7129291795303583
[171.39333333333335, 238.22333333333333]
0.7194649278688067
[171.28666666666666, 238.36111111111111]
0.7186015615895583
[171.20555555555555, 238.28]
0.718505772853599
[171.38555555555556, 238.23777777777778]
0.7193886593226189
[171.02, 238.40666666666667]
0.7173457118089539
[171.60111111111112, 238.50666666666666]
0.7194814028026238
[171.2788888888889, 238.34]
0.7186325790420781
[171.43444444444444, 238.38222222222223]
0.7191578417480796
[171.22666666666666, 238.29555555555555]
0.7185474620685797
[171.20333333333335, 238.5511111111111]
0.7176798822521147
[171.3388888888889, 238.4622222222222]
0.7185158608864205
[170.68777777777777, 238.34555555555556]
0.7161357692612499
[170.79777777777778, 238.12444444444444]
0.7172626824442869
[170.87333333333333, 238.2111111111111]
0.7173189047996642
[170.89333333333335, 238.11]
0.7177075021348677
[170.74, 238.0388888888889]
0.7172777557355241
[171.24666666666667, 238.13555555555556]
0.7191142299903883
[171.25333333333333, 238.3788888888889]
0.718408136440121
[171.25333333333333, 238.38666666666666]
0.7183846971307121
[171.82111111111112, 238.4711111111111]
0.7205112196212913
[171.57, 238.45444444444445]
0.7195085015073924
[171.74444444444444, 238.44222222222223]
0.7202769830100932
[171.5388888888889, 238.4411111111111]
0.7194182584099499
[171.38, 238.48444444444445]
0.7186212937251906
[171.33333333333334, 238.46]
0.7184992591350052
[171.47, 238.63888888888889]
0.7185333488534513
[171.43777777777777, 238.51444444444445]
0.7187731467462953
[171.4688888888889, 238.4988888888889]
0.7189504726320645
[171.21444444444444, 238.52666666666667]
0.7178000130430326
[171.30444444444444, 238.46666666666667]
0.718358028142764
[171.25, 238.41333333333333]
0.7182903640735977
[171.48666666666668, 238.46555555555557]
0.7191255201077258
[171.54111111111112, 238.54888888888888]
0.7191025366335343
[171.37222222222223, 238.47]
0.7186322062407106
[171.92333333333335, 238.51444444444445]
0.7208088958041209
[171.57888888888888, 238.41555555555556]
0.7196631465135571
[171.10444444444445, 238.62333333333333]
0.717048253640093
[171.84444444444443, 238.57444444444445]
0.7202969490072979
[171.35666666666665, 238.50222222222223]
0.7184698954586959
[170.9111111111111, 238.29666666666665]
0.7172198986324236
[170.3022222222222, 238.15]
0.7151048592157137
[169.72, 237.97666666666666]
0.7131791632232852
[169.36222222222221, 237.55]
0.7129539979887275
[168.95555555555555, 237.53555555555556]
0.7112853280444564
[169.08, 237.68444444444444]
0.7113633388806823
[169.04222222222222, 237.41666666666666]
0.712006552006552
[168.77555555555554, 237.41444444444446]
0.7108900048204498
[169.0811111111111, 237.32555555555555]
0.7124437598610441
[168.64, 237.64777777777778]
0.7096216155561685
[168.42111111111112, 237.39111111111112]
0.7094667964727688
[168.61666666666667, 237.4477777777778]
0.7101210558578962
[168.40555555555557, 237.38222222222223]
0.7094278332178765
[168.56555555555556, 237.4488888888889]
0.7099024819376334
[168.28222222222223, 237.43444444444444]
0.7087523573758371
[168.26, 237.25444444444443]
0.7091964089186948
[168.13888888888889, 237.45555555555555]
0.7080857236441908
[167.99, 237.4622222222222]
0.7074388440734434
[168.1688888888889, 237.33333333333334]
0.7085767790262172
[168.2711111111111, 237.30444444444444]
0.7090938035528669
[168.21777777777777, 237.34444444444443]
0.7087495903749824
[168.00555555555556, 237.50444444444443]
0.707378575371689
[167.88666666666666, 237.34444444444443]
0.7073545246009082
[168.14444444444445, 237.45888888888888]
0.7080991797410546
[168.36888888888888, 237.29333333333332]
0.7095390608904122
[168.57444444444445, 237.4988888888889]
0.7097904551600241
[168.25222222222223, 237.4188888888889]
0.7086724354984393
[168.50555555555556, 237.32666666666665]
0.7100152626010094
[168.57444444444445, 237.40444444444444]
0.7100728246218362
[169.0388888888889, 237.5822222222222]
0.7114963708470519
[168.78222222222223, 237.3322222222222]
0.7111643781103845
[168.75333333333333, 237.37222222222223]
0.7109228356776744
[168.24555555555557, 237.4488888888889]
0.708554823494179
[168.6211111111111, 237.43666666666667]
0.7101730051990472
[168.30666666666667, 237.54]
0.7085403160169516
[168.3111111111111, 237.50444444444443]
0.7086651010039579
[168.35111111111112, 237.46333333333334]
0.7089562365183865
[168.32333333333332, 237.7211111111111]
0.7080706149596399
[168.41, 237.50444444444443]
0.7090814674813103
[168.80666666666667, 237.6211111111111]
0.7104026484739946
[168.88444444444445, 237.67777777777778]
0.710560516104904
[168.86555555555555, 237.44333333333333]
0.711182551158405
[168.82777777777778, 237.38333333333333]
0.7112031641274077
[168.89444444444445, 237.50555555555556]
0.7111178685878693
[168.7277777777778, 237.55555555555554]
0.7102666043030871
[168.90777777777777, 237.42]
0.7114302829491104
[168.54777777777778, 237.32444444444445]
0.7101998202179857
[168.21666666666667, 237.39666666666668]
0.7085890001263707
[168.35, 237.3388888888889]
0.7093232836310011
[168.05444444444444, 237.31]
0.7081641921724514
[167.88666666666666, 237.26666666666668]
0.7075864006743466
[168.12777777777777, 237.4088888888889]
0.7081781080929291
[168.32555555555555, 237.36888888888888]
0.709130654583583
[168.05, 237.31]
0.7081454637394127
[168.16222222222223, 237.38444444444445]
0.708396131919156
[168.51555555555555, 237.32111111111112]
0.7100740206658582
[168.63555555555556, 237.5511111111111]
0.7098916724354057
[168.66666666666666, 237.42555555555555]
0.7103981130927589
[168.58, 237.23555555555555]
0.7106017460376935
[168.29333333333332, 237.35555555555555]
0.7090347345754142
[168.25555555555556, 237.53444444444443]
0.7083417141841418
[168.4922222222222, 237.26666666666668]
0.710138615716025
[168.01555555555555, 237.3411111111111]
0.7079075123942568
[168.2588888888889, 237.33]
0.7089659498963
[168.07222222222222, 237.35333333333332]
0.7081098034809801
[168.26888888888888, 237.34222222222223]
0.7089715740983483
[168.21666666666667, 237.30333333333334]
0.708867693950078
[168.10666666666665, 237.28444444444443]
0.7084605443068797
[168.5988888888889, 237.49333333333334]
0.7099099857773785
[168.26777777777778, 237.3011111111111]
0.7090897172368907
[168.34555555555556, 237.2722222222222]
0.7095038516471939
[168.41, 237.39111111111112]
0.7094199913878644
[168.37444444444444, 237.2877777777778]
0.7095790858732246
[168.16555555555556, 237.2511111111111]
0.7088082950085705
[168.37666666666667, 237.33333333333334]
0.7094522471910112
[167.6611111111111, 237.41666666666666]
0.7061893061893062
[167.8488888888889, 237.32888888888888]
0.7072417086462294
[168.0377777777778, 237.23]
0.7083327478724352
[167.92333333333335, 237.19555555555556]
0.7079531188517679
[168.06222222222223, 237.47333333333333]
0.7077098715177377
[168.01, 237.25222222222223]
0.7081493206948067
[168.29, 237.35333333333332]
0.7090273291576552
[168.21777777777777, 237.27777777777777]
0.708948723952236
[167.87444444444444, 237.4788888888889]
0.7069026018687041
[167.70111111111112, 237.35444444444445]
0.7065429573212121
[168.10555555555555, 237.32111111111112]
0.7083464036069272
[168.03, 237.29]
0.708120864764634
[168.04888888888888, 237.40444444444444]
0.7078590684439119
[167.8488888888889, 237.23888888888888]
0.7075100110062525
[168.11888888888888, 237.29333333333332]
0.7084855125395666
[168.28, 237.57777777777778]
0.7083154054812459
[168.59222222222223, 237.2888888888889]
0.710493538115752
[168.04555555555555, 237.3322222222222]
0.7080604309945271
[168.4322222222222, 237.16444444444446]
0.7101917094561672
[168.17555555555555, 237.35111111111112]
0.7085517938731181
[168.54888888888888, 237.22666666666666]
0.7104972272182254
[168.28444444444443, 237.3088888888889]
0.7091367088370524
[168.37666666666667, 237.3011111111111]
0.7095485810339419
[168.02444444444444, 237.46333333333334]
0.7075805855406916
[167.82, 237.13888888888889]
0.7076865409394401
[168.21, 237.35666666666665]
0.7086803263724073
[167.96333333333334, 237.35555555555555]
0.7076444153169179
[168.19333333333333, 237.50222222222223]
0.7081758299337549
[167.91, 237.3011111111111]
0.7075820219037229
[168.0077777777778, 237.45222222222222]
0.7075435058280731
[167.9011111111111, 237.38333333333333]
0.7072994921481898
[168.32222222222222, 237.43666666666667]
0.7089141899828258
[167.85, 237.17]
0.7077202006999199
[167.99666666666667, 237.48111111111112]
0.7074106478643916
[168.45555555555555, 237.47]
0.7093761551166696
[168.10666666666665, 237.57666666666665]
0.7075891291232304
[167.99, 237.45555555555555]
0.7074587057227084
[167.91555555555556, 237.43666666666667]
0.7072014525510897
[168.17111111111112, 237.61555555555555]
0.707744535991845
[168.29888888888888, 237.60666666666665]
0.708308782955959
[167.81555555555556, 237.55]
0.7064430880048644
[168.18666666666667, 237.54666666666665]
0.7080152671755726
[168.09222222222223, 237.51111111111112]
0.7077236152694611
[168.04333333333332, 237.54333333333332]
0.7074218037410718
[168.1511111111111, 237.68777777777777]
0.7074453414610203
[167.7711111111111, 237.52444444444444]
0.7063319798663997
[168.03222222222223, 237.54666666666665]
0.7073651025295615
[168.09, 237.7188888888889]
0.7070956825755912
[167.79333333333332, 237.56333333333333]
0.7063098963083528
[167.72444444444446, 237.60777777777778]
0.7058878544005761
[168.0688888888889, 237.5677777777778]
0.7074565854890534
[168.17111111111112, 237.70555555555555]
0.7074765699862108
[168.64333333333335, 237.51777777777778]
0.7100240449837674
[168.72222222222223, 237.57]
0.7102000346096823
[168.36666666666667, 237.52444444444444]
0.7088393241397377
[168.3, 237.61888888888888]
0.7082770262371586
[168.48333333333332, 237.52666666666667]
0.7093238653905526
[168.25666666666666, 237.55777777777777]
0.7082768168679432
[168.41444444444446, 237.5]
0.7091134502923977
[168.43777777777777, 237.7]
0.7086149675127378
[168.46666666666667, 237.54666666666665]
0.7091939829366862
[168.03555555555556, 237.53]
0.7074287692314889
[168.07666666666665, 237.56555555555556]
0.707495942640394
[167.98666666666668, 237.74444444444444]
0.7065850352853205
[167.89777777777778, 237.70777777777778]
0.7063200848848026
[168.19222222222223, 237.65222222222224]
0.7077241721095718
[168.0611111111111, 237.59333333333333]
0.7073477557357576
[168.38111111111112, 237.7411111111111]
0.7082540765632084
[168.34666666666666, 237.57777777777778]
0.7085960153400056
[168.27777777777777, 237.57]
0.7083292409722515
[168.2711111111111, 237.54]
0.7083906336242785
[167.7511111111111, 237.54555555555555]
0.7061850124654452
[167.8788888888889, 237.54333333333332]
0.706729532389412
[167.61222222222221, 237.63222222222223]
0.7053429903352052
[167.8711111111111, 237.34666666666666]
0.7072823624140966
[167.51666666666668, 237.47555555555556]
0.7054059365174428
[167.95, 237.39444444444445]
0.707472326882123
[167.61666666666667, 237.23222222222222]
0.7065510119011377
[167.5077777777778, 237.36222222222221]
0.7057052980442456
[167.62, 237.18333333333334]
0.7067107019886164
[167.9011111111111, 237.29444444444445]
0.707564441739049
[168.42333333333335, 237.37333333333333]
0.7095292928158176
[169.04333333333332, 237.63444444444445]
0.7113587162354876
[169.25444444444443, 237.58777777777777]
0.7123870008277642
[169.8488888888889, 237.80666666666667]
0.714230981282648
[168.11555555555555, 237.4911111111111]
0.7078814645694341
[167.4, 237.2188888888889]
0.7056773631479599
[166.20777777777778, 236.98777777777778]
0.7013348086399205
[165.57333333333332, 237.13333333333333]
0.6982288445319089
[164.53555555555556, 236.70555555555555]
0.6951064379092637
[163.0388888888889, 236.17444444444445]
0.6903324755242123
[162.11666666666667, 235.62]
0.6880428939252469
[163.59444444444443, 235.15222222222224]
0.6956959321857709
[165.20111111111112, 235.92444444444445]
0.700228886837594
[165.36333333333334, 236.5677777777778]
0.699010384620804
[164.43777777777777, 236.32111111111112]
0.6958234793524817
[164.4311111111111, 235.9922222222222]
0.696764959297152
[164.14444444444445, 236.15444444444444]
0.6950724337650973
[164.01333333333332, 235.9488888888889]
0.6951222957891068
[163.35444444444445, 235.92333333333335]
0.6924047830980874
[162.72666666666666, 235.84]
0.6899875621890547
[162.35666666666665, 236.0]
0.6879519774011299
[162.16333333333333, 235.85333333333332]
0.6875600655774775
[162.01, 235.77666666666667]
0.6871333041154765
[161.5888888888889, 235.67777777777778]
0.6856348121257838
[161.70222222222222, 235.80666666666667]
0.6857406726791251
[161.57, 235.69]
0.6855191140905427
[161.43444444444444, 235.59444444444443]
0.6852217794232084
[161.27666666666667, 235.68777777777777]
0.6842809932160722
[161.07777777777778, 235.70555555555555]
0.6833855799373041
[161.34, 235.5811111111111]
0.6848596614518236
[160.49777777777777, 235.30777777777777]
0.6820759572569259
[159.88555555555556, 234.77444444444444]
0.6810177144020029
[156.07444444444445, 231.99]
0.6727636727636728
[143.0822222222222, 229.57111111111112]
0.6232588304761535
[136.62333333333333, 227.78333333333333]
0.5997951269481232
[137.98333333333332, 227.73111111111112]
0.6059046243620644
[139.3711111111111, 228.48888888888888]
0.6099688776502626
[140.57444444444445, 228.90777777777777]
0.6141095152341798
[143.80777777777777, 230.41]
0.6241386128109795
[149.50222222222223, 232.38888888888889]
0.6433277551996175
[154.04777777777778, 233.47444444444446]
0.6598057365307647
[155.91666666666666, 234.1677777777778]
0.6658331395817813
[156.97333333333333, 234.35333333333332]
0.6698148095468381
[157.60666666666665, 234.58444444444444]
0.6718547218248818
[158.12777777777777, 234.58555555555554]
0.6740729513515562
[158.0222222222222, 234.54]
0.6737538254550278
[157.6677777777778, 234.36111111111111]
0.6727557188574138
[157.04333333333332, 233.71333333333334]
0.6719485409475996
[156.17222222222222, 233.34666666666666]
0.669271279736396
[154.70888888888888, 233.37222222222223]
0.6629276073035446
[153.2588888888889, 233.23444444444445]
0.657102295734859
[150.9711111111111, 232.77777777777777]
0.648563245823389
[145.2788888888889, 231.2588888888889]
0.628208885664455
[140.67, 230.52]
0.6102290473711608
[136.12666666666667, 229.61666666666667]
0.5928431443710532
[129.21666666666667, 229.83]
0.56222715340324
[122.50333333333333, 229.68555555555557]
0.5333523609572507
[123.61444444444444, 228.8322222222222]
0.5401968448499386
[124.46666666666667, 228.11333333333334]
0.5456352105678464
[116.65444444444445, 227.57444444444445]
0.5125990518365174
[115.57444444444444, 226.47]
0.5103300412612904
[119.34555555555555, 225.69222222222223]
0.5287978220093243
[119.25888888888889, 224.51]
0.5311963337441045
[116.56444444444445, 224.75555555555556]
0.5186276448487246
[112.67333333333333, 224.76777777777778]
0.5012877488370714
[110.86333333333333, 225.2122222222222]
0.49226161990418915
[107.02555555555556, 224.92666666666668]
0.4758242192517067
[97.86333333333333, 224.8322222222222]
0.4352727218815018
[107.08111111111111, 225.15666666666667]
0.4755849013773126
[109.76555555555555, 225.12666666666667]
0.4875724283613176
[106.37, 225.85777777777778]
0.4709600928804754
[104.08111111111111, 225.88888888888889]
0.46076242006886375
[102.72111111111111, 225.97444444444446]
0.45456959243178924
[105.51777777777778, 226.69333333333333]
0.4654648472728699
[105.14333333333333, 226.6611111111111]
0.4638790166425648
[105.13, 226.62666666666667]
0.4638906865917515
[105.21444444444444, 226.42666666666668]
0.46467337965689154
[105.89444444444445, 226.41]
0.46771098646015835
[107.36666666666666, 226.20555555555555]
0.4746420414077658
[109.12777777777778, 226.11222222222221]
0.48262662099940545
[111.21555555555555, 226.05333333333334]
0.49198812472966064
[113.12666666666667, 225.79888888888888]
0.5010063035444521
[116.68222222222222, 225.8111111111111]
0.5167248929783989
[118.10666666666667, 225.67444444444445]
0.5233497614557844
[119.60111111111111, 226.19444444444446]
0.5287535306398133
[120.79222222222222, 226.0688888888889]
0.534315990209474
[121.5911111111111, 226.19222222222223]
0.5375565521950356
[122.88888888888889, 226.27777777777777]
0.5430886324576479
[123.18333333333334, 226.68777777777777]
0.5434052710776938
[123.21, 226.76333333333332]
0.5433418101103941
[123.56888888888889, 227.99444444444444]
0.54198201710568
[123.99, 228.5588888888889]
0.5424860113853468
[124.62666666666667, 229.15222222222224]
0.5438597341893064
[124.43333333333334, 229.54444444444445]
0.5420881940074543
[125.20777777777778, 229.87444444444444]
0.5446789793462131
[125.77666666666667, 230.32]
0.5460952877156421
[125.50888888888889, 230.49777777777777]
0.5445123597238827
[126.28555555555556, 230.83555555555554]
0.5470801725133814
[129.12, 231.09555555555556]
0.5587299145134769
[131.06222222222223, 231.06555555555556]
0.5672079592612006
[133.1822222222222, 231.19]
0.5760725906060912
[135.8322222222222, 231.54333333333332]
0.5866384502061049
[134.44444444444446, 231.53666666666666]
0.5806615702816449
[136.3488888888889, 231.79888888888888]
0.5882206318695805
[137.85111111111112, 232.42333333333335]
0.5931035801530732
[140.88333333333333, 233.45777777777778]
0.6034638668900396
[146.89666666666668, 234.19555555555556]
0.6272393441378525
[156.38222222222223, 234.92333333333335]
0.6656734348321675
[161.80333333333334, 236.05555555555554]
0.6854459872911274
[169.05777777777777, 237.5811111111111]
0.7115792033597882
[173.0522222222222, 238.33]
0.7261033953854832
[171.18333333333334, 237.89888888888888]
0.7195633999504926
[173.62222222222223, 237.69666666666666]
0.7304360833368393
[179.14333333333335, 239.71444444444444]
0.7473197276389038
[178.02666666666667, 239.98333333333332]
0.7418292937009515
[176.59777777777776, 240.26111111111112]
0.7350243947557055
[175.43555555555557, 240.31333333333333]
0.7300283888626886
[173.79777777777778, 240.15666666666667]
0.7236850019200429
[172.15222222222224, 239.86666666666667]
0.7176996479525662
[170.15, 239.20222222222222]
0.7113228230878569
[168.75, 238.72333333333333]
0.7068852367454654
[167.78222222222223, 238.52444444444444]
0.7034173064023255
[167.2411111111111, 238.12444444444444]
0.7023265146142074
[166.2811111111111, 237.7288888888889]
0.6994568976798967
[165.28555555555556, 237.66555555555556]
0.6954543967012469
[164.93, 237.29]
0.695056681697501
[161.7122222222222, 236.34]
0.6842355175688508
[160.38111111111112, 235.96555555555557]
0.6796801793105397
[159.8322222222222, 235.86888888888888]
0.6776316409304605
[159.3711111111111, 235.65]
0.6763043119503972
[158.66666666666666, 235.31333333333333]
0.6742782672748392
[156.80777777777777, 235.04111111111112]
0.6671504275847724
[156.58666666666667, 234.89666666666668]
0.6666193645432743
[156.88222222222223, 235.16222222222223]
0.6671234041748958
[157.01666666666668, 235.12777777777777]
0.6677929258322899
[156.73666666666668, 235.33]
0.6660292638705931
[156.75666666666666, 235.37222222222223]
0.665994760072698
[157.07888888888888, 235.32555555555555]
0.6674960928831453
[156.75666666666666, 235.32444444444445]
0.6661299765807962
[156.39555555555555, 235.40444444444444]
0.6643695955896235
[155.74777777777777, 235.40222222222224]
0.6616240760495039
[154.7277777777778, 235.31555555555556]
0.6575331469799418
[154.09333333333333, 235.46555555555557]
0.6544198490932857
[153.62444444444444, 235.54222222222222]
0.6522161631790478
[153.35777777777778, 235.5]
0.6512007548950224
[152.48777777777778, 235.44]
0.6476714992260354
[152.72222222222223, 235.53222222222223]
0.6484132862217484
[151.8188888888889, 235.46]
0.6447757109015921
[151.66, 235.47333333333333]
0.6440644375867048
[151.8322222222222, 235.42666666666668]
0.6449236374620074
[151.84222222222223, 235.36666666666667]
0.6451305291979418
[151.14444444444445, 235.44555555555556]
0.6419507222712493
[151.39222222222222, 235.25555555555556]
0.6435224106172955
[151.49777777777777, 235.3088888888889]
0.6438251376441367
[151.07777777777778, 235.31444444444443]
0.642025091721243
[150.82222222222222, 235.26444444444445]
0.6410752911617187
[150.51444444444445, 235.27444444444444]
0.6397398782509316
[150.52666666666667, 235.24333333333334]
0.6398764399982997
[150.17333333333335, 235.28222222222223]
0.6382689347072547
[150.08555555555554, 235.3488888888889]
0.6377151651921025
[150.50444444444443, 235.07333333333332]
0.6402446517871492
[149.51222222222222, 235.24555555555557]
0.6355581165779493
[147.6511111111111, 235.21444444444444]
0.6277297784999977
[147.0588888888889, 235.3788888888889]
0.6247751851624568
[146.17333333333335, 235.02777777777777]
0.6219406689516607
[146.52666666666667, 235.07111111111112]
0.6233291108128037
[146.56666666666666, 235.1911111111111]
0.6231811481915417
[146.79888888888888, 235.35333333333332]
0.6237383036380288
[146.63666666666666, 235.20444444444445]
0.6234434345533908
[146.4611111111111, 235.39777777777778]
0.6221856148929944
[146.2211111111111, 235.1677777777778]
0.6217735800917548
[146.12, 235.0988888888889]
0.6215256936797282
[146.39666666666668, 235.2]
0.6224348072562359
[145.90333333333334, 235.37666666666667]
0.619871695013666
[145.53444444444443, 235.12555555555556]
0.6189648084002399
[145.95444444444445, 235.14]
0.6207129558749871
[145.6511111111111, 235.14333333333335]
0.6194141634653095
[144.96444444444444, 234.97666666666666]
0.6169312319426515
[145.02666666666667, 235.1288888888889]
0.6167964615151973
[144.4688888888889, 235.12444444444444]
0.6144358542993782
[144.4688888888889, 235.04222222222222]
0.6146507956017359
[143.61333333333334, 235.09777777777776]
0.6108664007410629
[143.26333333333332, 235.24666666666667]
0.6089919800493099
[143.36, 234.94444444444446]
0.6101868053913455
[203.69555555555556, 235.02333333333334]
0.8667035424378666
[204.64555555555555, 234.84777777777776]
0.8713966020542858
[204.69222222222223, 234.97]
0.8711419424701972
[205.11888888888888, 234.81]
0.8735526122775388
[206.19, 234.85888888888888]
0.877931429274316
[207.53555555555556, 234.75222222222223]
0.8840621553694913
[209.14888888888888, 234.8711111111111]
0.8904836695303334
[208.96, 234.69222222222223]
0.8903575841646033
[211.88555555555556, 234.39555555555555]
0.903965755892224
[212.7288888888889, 234.38333333333333]
0.9076109886463296
[214.04555555555555, 234.36555555555555]
0.9132978395573866
[215.32, 234.09777777777776]
0.9197866038882139
[216.09333333333333, 233.79555555555555]
0.9242833244620181
[216.07, 233.5811111111111]
0.925031989839361
[216.0688888888889, 233.62222222222223]
0.9248644535337202
[216.1588888888889, 233.51]
0.9256943552262811
[216.29111111111112, 233.26555555555555]
0.9272312433611669
[216.03555555555556, 233.01]
0.9271514336533005
[216.2, 233.0011111111111]
0.9278925708508782
[216.9088888888889, 232.7188888888889]
0.9320639589012972
[217.10222222222222, 232.55777777777777]
0.9335410077304565
[217.69222222222223, 232.2411111111111]
0.9373543778735701
[217.61777777777777, 232.17111111111112]
0.9373163471386047
[217.47555555555556, 232.36888888888888]
0.9359065088078343
[219.57111111111112, 232.2888888888889]
0.9452501674160528
[219.8177777777778, 231.4011111111111]
0.949942620077691
[219.69555555555556, 232.31555555555556]
0.9456773354249967
[219.00222222222223, 231.42888888888888]
0.9463046004052121
[219.11555555555555, 231.5377777777778]
0.9463490479115478
[219.10555555555555, 231.4622222222222]
0.9466147583478945
[218.46444444444444, 231.3177777777778]
0.9444343039397461
[218.73222222222222, 231.23111111111112]
0.945946335556538
[218.78666666666666, 231.42333333333335]
0.9453958834459215
[218.13777777777779, 231.27333333333334]
0.9432033284329269
[217.63, 230.99444444444444]
0.9421438707039611
[217.66555555555556, 231.1211111111111]
0.9417813652293892
[218.18777777777777, 231.45222222222222]
0.942690356061006
[217.28222222222223, 231.29333333333332]
0.9394227628216215
[216.43777777777777, 231.16666666666666]
0.9362845469838981
[215.79888888888888, 231.13444444444445]
0.9336509294734665
[215.2588888888889, 231.32777777777778]
0.9305362760873219
[215.32, 230.87444444444444]
0.9326281239923576
[215.08333333333334, 229.60666666666665]
0.9367469004965013
[214.4011111111111, 229.53555555555556]
0.9340649233718329
[212.98666666666668, 229.51333333333332]
0.9279925639759492
[211.87666666666667, 229.55]
0.9230087853045814
[212.06333333333333, 230.07666666666665]
0.9217072570012895
[214.04666666666665, 231.20333333333335]
0.9257940341113882
[216.26666666666668, 232.52777777777777]
0.9300680922231515
[217.44333333333333, 234.11111111111111]
0.9288039867109634
[218.30777777777777, 236.14333333333335]
0.92447148389161
[218.2577777777778, 237.49444444444444]
0.9190016140728439
[218.60666666666665, 237.7277777777778]
0.919567198710009
[218.54, 238.04444444444445]
0.918063853622106
[218.33333333333334, 237.82777777777778]
0.9180312551099068
[218.2122222222222, 237.82222222222222]
0.917543449822463
[218.16555555555556, 237.9622222222222]
0.9168075231362588
[218.44, 237.96666666666667]
0.9179436895923798
[218.23666666666668, 237.80777777777777]
0.9177019721810801
[217.79666666666665, 237.45888888888888]
0.9171973628183592
[216.97222222222223, 237.20333333333335]
0.9147098363804144
[217.23555555555555, 237.3022222222222]
0.9154383533421985
[217.02333333333334, 237.1688888888889]
0.9150581863838241
[217.05666666666667, 237.10777777777778]
0.9154346124828372
[216.81555555555556, 237.01666666666668]
0.914769237981389
[216.59, 237.0088888888889]
0.9138475819003506
[216.50666666666666, 236.78333333333333]
0.9143661575279791
[216.27666666666667, 236.60666666666665]
0.9140768082048971
[216.29111111111112, 236.55666666666667]
0.9143310740672895
[216.36, 236.66666666666666]
0.9141971830985917
[215.98555555555555, 236.5611111111111]
0.9130222399661821
[216.24333333333334, 236.45333333333335]
0.9145285891507837
[216.03222222222223, 236.4622222222222]
0.9136014209457937
[215.96666666666667, 236.6822222222222]
0.9124752363694406
[215.85333333333332, 236.5211111111111]
0.9126176192869793
[215.91222222222223, 236.46]
0.9131025214506564
[215.73, 236.44666666666666]
0.9123833422618208
[215.89777777777778, 236.66222222222223]
0.9122612631223121
[215.70111111111112, 236.40777777777777]
0.9124112291849771
[215.83777777777777, 236.50666666666666]
0.9126075844702521
[215.80777777777777, 236.45444444444445]
0.9126822643779163
[215.56, 236.38444444444445]
0.9119043366267756
[215.63, 236.4011111111111]
0.9121361527723596
[215.59666666666666, 236.27777777777777]
0.9124711968022572
[215.7411111111111, 236.3088888888889]
0.9129623186225185
[215.54222222222222, 236.3788888888889]
0.9118505600706963
[215.82777777777778, 236.52]
0.9125138583535336
[215.63222222222223, 236.4411111111111]
0.9119912404780143
[215.56555555555556, 236.41333333333333]
0.9118164044141147
[215.72555555555556, 236.3488888888889]
0.9127419915943473
[215.5011111111111, 236.63777777777779]
0.9106792378412387
[215.6888888888889, 236.4322222222222]
0.9122652016786583
[215.37, 236.4177777777778]
0.91097210211678
[215.69, 236.45888888888888]
0.9121670198719064
[215.52555555555554, 236.45444444444445]
0.9114887058348096
[215.47333333333333, 236.3388888888889]
0.9117134058907876
[215.64111111111112, 236.37]
0.9123032157681225
[215.42111111111112, 236.41666666666666]
0.9111925743155916
[215.66333333333333, 236.58444444444444]
0.9115702168828607
[215.55666666666667, 236.4188888888889]
0.9117573797919888
[215.53222222222223, 236.45]
0.911534033504852
[215.59666666666666, 236.40555555555557]
0.9119780039010175
[215.42666666666668, 236.46333333333334]
0.911036242405447
[215.60666666666665, 236.38111111111112]
0.9121146171671922
[215.72, 236.3488888888889]
0.9127184858542455
[215.7, 236.45111111111112]
0.9122393165606232
[215.60333333333332, 236.45111111111112]
0.911830493501123
[215.61444444444444, 236.38222222222223]
0.9121432331816643
[215.70666666666668, 236.39333333333335]
0.9124904819650864
[215.5677777777778, 236.40555555555557]
0.911855803351115
[215.57444444444445, 236.43]
0.9117897239962968
[215.73888888888888, 236.45666666666668]
0.9123823486567892
[215.4111111111111, 236.39555555555555]
0.911231645641016
[215.5, 236.41555555555556]
0.9115305441454313
[215.37555555555556, 236.36444444444444]
0.9112011582866384
[215.39111111111112, 236.36888888888888]
0.9112498354737417
[214.9622222222222, 236.33777777777777]
0.9095550624341808
[215.23111111111112, 236.35777777777778]
0.9106157332104813
[214.99555555555557, 236.34777777777776]
0.9096576137800699
[215.14, 236.39]
0.9101061804644867
[215.29555555555555, 236.2411111111111]
0.9113382278933482
[215.31555555555556, 236.17444444444445]
0.9116801610862028
[215.04, 236.31333333333333]
0.9099782774282732
[214.98333333333332, 236.38]
0.9094819076628028
[215.2811111111111, 236.51888888888888]
0.9102068427703683
[215.07666666666665, 236.41222222222223]
0.9097527388600889
[215.1977777777778, 236.36666666666667]
0.9104404644384901
[215.13222222222223, 236.31222222222223]
0.9103728118637772
[215.3, 236.54555555555555]
0.9101840848133552
[215.31, 236.25333333333333]
0.9113522207799537
[215.13444444444445, 236.36555555555555]
0.9101767977097622
[215.2411111111111, 236.48333333333332]
0.9101745483590575
[215.36111111111111, 236.37555555555556]
0.9110972181744681
[215.2277777777778, 236.45666666666668]
0.9102208062553158
[215.0811111111111, 236.27666666666667]
0.9102934883305352
[215.29, 236.4322222222222]
0.9105780843934602
[215.14111111111112, 236.42222222222222]
0.9099868408685027
[215.14888888888888, 236.29444444444445]
0.9105118378670678
[215.3022222222222, 236.42777777777778]
0.9106468971027093
[215.23777777777778, 236.3188888888889]
0.9107937955775388
[215.31333333333333, 236.4477777777778]
0.9106168616043946
[215.2422222222222, 236.27555555555554]
0.9109796471163614
[215.21555555555557, 236.32555555555555]
0.9106740701386506
[215.08777777777777, 236.31555555555556]
0.9101718982151924
[214.96333333333334, 236.46333333333334]
0.9090768124726878
[214.97, 236.2788888888889]
0.9098146728677504
[214.88111111111112, 236.32333333333332]
0.9092674349173214
[215.05555555555554, 236.2877777777778]
0.9101425286491518
[215.26, 236.55444444444444]
0.9099807890126304
[215.12777777777777, 236.30444444444444]
0.9103839679509483
[215.26111111111112, 236.25555555555556]
0.9111367163617552
[215.04777777777778, 236.3011111111111]
0.9100582590009921
[215.2188888888889, 236.46666666666667]
0.910144723240297
[215.10888888888888, 236.30333333333334]
0.9103083137022565
[214.97222222222223, 236.25333333333333]
0.9099224937449443
[214.95555555555555, 236.3188888888889]
0.9095995523938933
[215.20333333333335, 236.35555555555555]
0.9105067694622039
[214.87333333333333, 236.3011111111111]
0.9093200295291789
[214.98, 236.2488888888889]
0.9099725336744675
[215.06444444444443, 236.32777777777778]
0.9100260937022496
[215.10333333333332, 236.49333333333334]
0.9095534757850819
[215.01777777777778, 236.26555555555555]
0.910068237717446
[215.10444444444445, 236.34777777777776]
0.9101183284519517
[215.03222222222223, 236.29777777777778]
0.910005266424662
[214.71777777777777, 236.5088888888889]
0.9078634582679532
[214.6211111111111, 236.26777777777778]
0.9083807920391646
[214.59666666666666, 236.15555555555557]
0.9087089489037358
[214.69222222222223, 236.22555555555556]
0.908844183760342
[214.9177777777778, 236.17777777777778]
0.9099830636055702
[214.69666666666666, 236.2877777777778]
0.908623665116454
[214.8177777777778, 236.29111111111112]
0.9091233976921124
[214.6688888888889, 236.2111111111111]
0.9088009784091443
[214.82, 236.31666666666666]
0.9090344876225404
[214.90777777777777, 236.41]
0.9090469006293209
[214.65777777777777, 236.30444444444444]
0.908395008322597
[214.6611111111111, 236.28333333333333]
0.9084902776798099
[214.79777777777778, 236.29666666666665]
0.9090173839852916
[214.79, 236.35777777777778]
0.9087494476358815
[214.6688888888889, 236.2422222222222]
0.9086812969739158
[214.5688888888889, 236.2122222222222]
0.9083733554101538
[214.86888888888888, 236.32222222222222]
0.9092199915369786
[214.56333333333333, 236.46777777777777]
0.9073681638560105
[214.57777777777778, 236.2488888888889]
0.9082699977424937
[214.73888888888888, 236.2488888888889]
0.90895195274287
[214.68555555555557, 236.34666666666666]
0.9083502576253338
[214.84444444444443, 236.4088888888889]
0.9087832756805534
[214.57666666666665, 236.28444444444443]
0.9081286208712662
[214.56666666666666, 236.07555555555555]
0.9088898092889283
[214.27777777777777, 236.11222222222221]
0.9075251410581597
[214.54666666666665, 236.35222222222222]
0.9077412712665184
[214.39555555555555, 236.24444444444444]
0.9075157558084846
[214.41, 236.31444444444443]
0.9073080594123649
[214.56333333333333, 236.14111111111112]
0.908623374912364
[214.46333333333334, 236.44333333333333]
0.9070390368375791
[214.45333333333335, 236.26444444444445]
0.9076834808453804
[214.4, 236.23]
0.9075900605342252
[214.45555555555555, 236.2111111111111]
0.907897831506656
[214.39888888888888, 236.4322222222222]
0.9068090925752741
[214.20222222222222, 236.32111111111112]
0.9064032460540977
[214.16444444444446, 236.29333333333332]
0.9063499228830456
[214.22333333333333, 236.28666666666666]
0.90662472138363
[214.21555555555557, 236.1611111111111]
0.9070737961372887
[214.45444444444445, 236.26555555555555]
0.9076839149920758
[214.26444444444445, 236.2277777777778]
0.9070247642341431
[214.24, 236.29666666666665]
0.9066568861177334
[214.33444444444444, 236.34]
0.9068902616757402
[214.45333333333335, 236.45555555555555]
0.9069498613786947
[214.35, 236.36888888888888]
0.9068452324991069
[214.41, 236.30555555555554]
0.9073421887857059
[214.5688888888889, 236.31333333333333]
0.9079846907589735
[214.85, 236.42555555555555]
0.9087427097089523
[214.50666666666666, 236.26444444444445]
0.9079092166028649
[214.4922222222222, 236.26777777777778]
0.907835271655043
[214.41666666666666, 236.29111111111112]
0.9074258682792412
[214.47555555555556, 236.46444444444444]
0.9070097454162712
[214.43555555555557, 236.2511111111111]
0.9076594583917301
[214.60333333333332, 236.34222222222223]
0.9080194444966808
[214.19555555555556, 236.36]
0.906225907749008
[214.18333333333334, 236.44555555555556]
0.9058463071132185
[214.07555555555555, 236.34222222222223]
0.9057863361979803
[214.09777777777776, 236.4111111111111]
0.9056163932885275
[214.07222222222222, 236.29]
0.905972416192908
[214.17222222222222, 236.4488888888889]
0.9057865453656886
[213.9188888888889, 236.30444444444444]
0.905268156897411
[214.0377777777778, 236.26555555555555]
0.9059203626804114
[213.96777777777777, 236.35666666666665]
0.9052749846042469
[213.88555555555556, 236.1988888888889]
0.9055315906086678
[214.01888888888888, 236.25555555555556]
0.9058787565254197
[213.98444444444445, 236.25222222222223]
0.9057457425444557
[214.27555555555554, 236.26]
0.9069480892049249
[213.98777777777778, 236.21777777777777]
0.9058919264708649
[214.0211111111111, 236.4388888888889]
0.905185742146197
[214.10333333333332, 236.31444444444443]
0.906010353436805
[214.34555555555556, 236.26222222222222]
0.9072358396508587
[213.99666666666667, 236.32222222222222]
0.9055291739150877
[214.36111111111111, 236.45555555555555]
0.9065598421126827
[214.0522222222222, 236.33666666666667]
0.9057088992632919
[213.88333333333333, 236.2577777777778]
0.9052964746604462
[213.6288888888889, 236.30333333333334]
0.904045177337979
[214.11555555555555, 236.44]
0.9055809319724054
[213.89333333333335, 236.22555555555556]
0.9054622935706458
[213.89333333333335, 236.33444444444444]
0.9050451102721662
[213.9788888888889, 236.28666666666666]
0.9055901964656867
[213.86111111111111, 236.5011111111111]
0.9042710628561764
[213.9311111111111, 236.2722222222222]
0.9054433445413718
[213.89111111111112, 236.2588888888889]
0.9053251376785353
[213.82555555555555, 236.32444444444445]
0.9047966073006977
[213.79444444444445, 236.38111111111112]
0.9044480899489055
[213.63666666666666, 236.31]
0.9040525862920175
[213.61555555555555, 236.16333333333333]
0.9045246463135213
[213.60333333333332, 236.32222222222222]
0.9038647797263623
[213.83, 236.38555555555556]
0.9045814982114907
[213.5688888888889, 236.30777777777777]
0.9037742680214598
[213.81333333333333, 236.2577777777778]
0.9050001881184393
[213.8788888888889, 236.23777777777778]
0.9053543040439482
[213.82888888888888, 236.19444444444446]
0.9053087145713277
[213.93666666666667, 236.32]
0.9052837959828481
[213.63888888888889, 236.16222222222223]
0.9046277041205197
[213.8111111111111, 236.07555555555555]
0.9056893273339985
[214.07111111111112, 236.2277777777778]
0.9062063451000683
[213.95, 236.32111111111112]
0.905335960016738
[213.8, 236.17222222222222]
0.9052715767683659
[213.76555555555555, 236.33333333333334]
0.9045086976962858
[213.78222222222223, 236.29555555555555]
0.9047238392596842
[213.77777777777777, 236.45333333333335]
0.9041013495733242
[213.6677777777778, 236.22333333333333]
0.9045159712324966
[213.7211111111111, 236.30444444444444]
0.9044311951625492
[213.86222222222221, 236.29888888888888]
0.9050496311169
[213.92444444444445, 236.42111111111112]
0.9048449330056068
[213.75333333333333, 236.24333333333334]
0.9048015464281178
[213.6977777777778, 236.23444444444445]
0.9046004204862401
[213.74666666666667, 236.20666666666668]
0.9049137760718015
[213.9088888888889, 236.3711111111111]
0.9049705265730913
[213.89666666666668, 236.23777777777778]
0.9054295577901738
[213.98888888888888, 236.2811111111111]
0.905653811608583
[213.64444444444445, 236.27666666666667]
0.9042130459113374
[213.91222222222223, 236.41333333333333]
0.904823003026714
[213.74666666666667, 236.24555555555557]
0.9047648162693243
[213.73333333333332, 236.30444444444444]
0.9044829175169508
[213.61777777777777, 236.2888888888889]
0.904053418602464
[213.61555555555555, 236.33777777777777]
0.9038570031593199
[213.50666666666666, 236.18333333333334]
0.903987015736363
[213.5211111111111, 236.36222222222221]
0.9033639517501387
[213.64888888888888, 236.2422222222222]
0.9043636945131645
[213.8011111111111, 236.45222222222222]
0.904204278994582
[213.68777777777777, 236.3088888888889]
0.9042731265104994
[213.67111111111112, 236.30777777777777]
0.9042068488835182
[213.52555555555554, 236.22666666666666]
0.9039011495550413
[213.79222222222222, 236.1822222222222]
0.9052003161400802
[213.72555555555556, 236.29111111111112]
0.9045010392077569
[213.48666666666668, 236.24555555555557]
0.9036642664647424
[213.68555555555557, 236.23888888888888]
0.9045316652164712
[213.77666666666667, 236.29666666666665]
0.9046960741440845
[213.61777777777777, 236.4111111111111]
0.9035860318653945
[213.64222222222222, 236.3177777777778]
0.9040463406148029
[213.62444444444444, 236.18777777777777]
0.904468666644713
[213.74666666666667, 236.25666666666666]
0.9047222653329007
[213.63777777777779, 236.45666666666668]
0.9034965297846446
[213.57444444444445, 236.3188888888889]
0.9037552835857386
[213.5911111111111, 236.17111111111112]
0.9043913546675197
[213.49666666666667, 236.22444444444446]
0.9037873585384897
[213.42333333333335, 236.37555555555556]
0.902899340973404
[213.24, 236.23111111111112]
0.9026753461770018
[213.13666666666666, 236.22333333333333]
0.9022676280920597
[213.52444444444444, 236.32222222222222]
0.9035309605529174
[213.2811111111111, 236.41222222222223]
0.9021577188620629
[213.35222222222222, 236.30333333333334]
0.9028743658104226
[213.2577777777778, 236.29333333333332]
0.9025128841740964
[213.1822222222222, 236.21333333333334]
0.9024986829231579
[213.2577777777778, 236.44555555555556]
0.9019318518240046
[213.14555555555555, 236.31222222222223]
0.9019658549658878
[213.06666666666666, 236.26666666666668]
0.901805869074492
[213.39555555555555, 236.31333333333333]
0.9030195315071327
[213.40555555555557, 236.37666666666667]
0.9028198872797184
[213.32111111111112, 236.29777777777778]
0.9027639325145297
[213.32, 236.37555555555556]
0.9024621835309159
[213.13888888888889, 236.22222222222223]
0.9022812793979303
[213.40222222222224, 236.3088888888889]
0.9030647269581245
[213.38444444444445, 236.5077777777778]
0.9022301357249233
[213.5511111111111, 236.2488888888889]
0.9039242982918203
[213.51888888888888, 236.40777777777777]
0.9031804744156754
[213.35777777777778, 236.2877777777778]
0.9029573166430764
[213.26666666666668, 236.28222222222223]
0.9025929444073472
[213.2411111111111, 236.16444444444446]
0.9029348664772192
[213.16666666666666, 236.3]
0.9021018479334179
[212.99, 236.14333333333335]
0.9019522041697838
[213.35666666666665, 236.28222222222223]
0.9029738448371533
[213.44333333333333, 236.1977777777778]
0.9036635964210783
[213.40222222222224, 236.30777777777777]
0.903068973137669
[213.26555555555555, 236.13111111111112]
0.9031658494809851
[213.2211111111111, 236.25555555555556]
0.9025019987772186
[213.24777777777777, 236.21555555555557]
0.9027677168687732
[213.17222222222222, 236.4188888888889]
0.9016717032386019
[213.33444444444444, 236.29444444444445]
0.9028330943032469
[213.11333333333334, 236.2788888888889]
0.9019567272197168
[213.11888888888888, 236.35333333333332]
0.9016961423104768
[213.11222222222221, 236.35444444444445]
0.9016636971779671
[213.0222222222222, 236.35]
0.9012998613167853
[212.94333333333333, 236.26888888888888]
0.901275383038158
[213.25333333333333, 236.21444444444444]
0.9027954824476817
[213.38555555555556, 236.36555555555555]
0.9027777124886593
[213.3388888888889, 236.31222222222223]
0.9027839816438704
[213.39666666666668, 236.21]
0.9034192738100278
[213.2411111111111, 236.2288888888889]
0.9026885412453082
[213.44, 236.32111111111112]
0.9031778794389931
[213.17222222222222, 236.18444444444444]
0.9025667322149356
[213.29222222222222, 236.31444444444443]
0.9025780151681141
[213.13444444444445, 236.24666666666667]
0.9021691076182146
[213.23444444444445, 236.41555555555556]
0.9019476063804789
[213.29666666666665, 236.37222222222223]
0.9023761957364795
[213.17888888888888, 236.26111111111112]
0.9023020669221905
[213.15444444444444, 236.27333333333334]
0.9021519332599719
[212.92555555555555, 236.17666666666668]
0.901552039668986
[212.90666666666667, 236.20666666666668]
0.9013575682312099
[212.67111111111112, 236.0811111111111]
0.9008391654469039
[212.78666666666666, 236.23111111111112]
0.9007563214930764
[212.80666666666667, 236.20222222222222]
0.9009511623749894
[212.64777777777778, 236.22]
0.9002107263473786
[212.86222222222221, 236.24333333333334]
0.9010295411040405
[212.83333333333334, 236.29333333333332]
0.9007166234059362
[212.7277777777778, 236.32111111111112]
0.9001640893511184
[212.8188888888889, 236.31444444444443]
0.900575034205837
[213.22444444444446, 236.44555555555556]
0.9017908750428805
[212.80444444444444, 236.21]
0.9009120885840753
[212.86666666666667, 236.24666666666667]
0.9010356407145075
[212.93444444444444, 236.23555555555555]
0.901364927661656
[212.98444444444445, 236.31333333333333]
0.9012798450268477
[212.88111111111112, 236.17888888888888]
0.9013553756333477
[212.55555555555554, 236.27777777777777]
0.8996002821537737
[212.58666666666667, 236.30777777777777]
0.8996177301729854
[212.82777777777778, 236.45444444444445]
0.900079413934561
[212.99333333333334, 236.27]
0.9014827668909863
[212.4911111111111, 236.1677777777778]
0.8997464138018639
[212.61333333333334, 236.31222222222223]
0.8997136556627061
[212.7711111111111, 236.22333333333333]
0.900720128315483
[212.71666666666667, 236.20111111111112]
0.9005743692992318
[212.80444444444444, 236.21333333333334]
0.9008993753292692
[212.76666666666668, 236.14333333333335]
0.9010064508843499
[212.8, 236.23888888888888]
0.9007831056134328
[212.98555555555555, 236.41666666666666]
0.9008906121489837
[212.5677777777778, 236.14555555555555]
0.9001557419858751
[212.77777777777777, 236.30444444444444]
0.9004391698091915
[212.73222222222222, 236.32555555555555]
0.9001659669100535
[212.66222222222223, 236.20444444444445]
0.9003311632107779
[212.64444444444445, 236.25666666666666]
0.9000569060955365
[212.67444444444445, 236.2211111111111]
0.900319380617971
[212.78, 236.30444444444444]
0.9004485738736282
[212.94666666666666, 236.21444444444444]
0.9014972270959063
[212.76333333333332, 236.41444444444446]
0.8999591113534141
[212.85111111111112, 236.28222222222223]
0.9008342189660199
[212.73111111111112, 236.3022222222222]
0.9002501504664461
[212.63666666666666, 236.31444444444443]
0.8998039335536926
[212.95333333333335, 236.39666666666668]
0.9008305249651011
[212.86111111111111, 236.25555555555556]
0.9009782250858298
[212.84, 236.0888888888889]
0.9015248493975904
[212.5088888888889, 236.05666666666667]
0.9002452330184372
[212.5311111111111, 236.44555555555556]
0.8988585579954981
[212.41555555555556, 236.18444444444444]
0.8993630213674811
[212.18666666666667, 236.22444444444446]
0.8982417851196132
[212.5988888888889, 236.17555555555555]
0.9001731292164963
[212.31444444444443, 236.2111111111111]
0.8988334352509525
[212.37, 236.1811111111111]
0.8991828305020159
[212.3711111111111, 236.19444444444446]
0.899136775255792
[212.4111111111111, 236.17666666666668]
0.8993738209156045
[212.17555555555555, 236.25555555555556]
0.8980764708648826
[212.42888888888888, 236.4488888888889]
0.8984135636548185
[212.1822222222222, 236.19444444444446]
0.8983370575091143
[212.32555555555555, 236.13777777777779]
0.8991596243247821
[212.25, 236.17]
0.8987170258711945
[212.2488888888889, 236.13777777777779]
0.8988349551109522
[212.51, 236.12666666666667]
0.8999830599395804
[212.55444444444444, 236.10444444444445]
0.9002560072284393
[212.4688888888889, 236.2211111111111]
0.8994491977855024
[212.4922222222222, 236.0888888888889]
0.9000517695783131
[212.53666666666666, 236.11222222222221]
0.9001510581126677
[212.49333333333334, 236.09222222222223]
0.9000437682073389
[212.53333333333333, 236.23444444444445]
0.8996712305572148
[212.49666666666667, 236.16]
0.8997995709123758
[212.47222222222223, 236.21777777777777]
0.8994760014299423
[212.33333333333334, 236.15]
0.8991460230079752
[212.29, 236.1677777777778]
0.8988948534704612
[211.96555555555557, 236.17333333333335]
0.8974999529535745
[212.04555555555555, 236.1511111111111]
0.8979231753679376
[212.01555555555555, 236.17111111111112]
0.897720108772359
[212.3322222222222, 236.08444444444444]
0.8993909900412281
[212.02777777777777, 235.83]
0.8990704226679292
[212.02444444444444, 235.08]
0.9019246403115724
[211.9088888888889, 235.13222222222223]
0.9012328760650037
[211.9322222222222, 235.1977777777778]
0.9010808870076247
[211.98777777777778, 235.12444444444444]
0.9015982080411319
[211.91222222222223, 235.25222222222223]
0.90078733463375
[211.84666666666666, 235.3388888888889]
0.9001770496447203
[212.3111111111111, 235.5011111111111]
0.9015291270152064
[212.23111111111112, 235.45555555555555]
0.9013637865131424
[212.48555555555555, 235.37222222222223]
0.9027639436353765
[212.36777777777777, 234.9188888888889]
0.9040046919267644
[212.07888888888888, 234.54666666666665]
0.9042076440604098
[212.4411111111111, 234.51888888888888]
0.9058592769120706
[212.2488888888889, 234.13]
0.9065428987694396
[212.2422222222222, 233.38666666666666]
0.9094016605728215
[212.3411111111111, 233.1822222222222]
0.9106230701787825
[212.36888888888888, 233.09222222222223]
0.9110938445917923
[212.48666666666668, 232.74555555555557]
0.9129569248249161
[212.63222222222223, 232.57222222222222]
0.9142631918400497
[212.35555555555555, 232.3711111111111]
0.9138638384958926
[212.2711111111111, 232.26666666666668]
0.9139112131649445
[212.55666666666667, 232.0822222222222]
0.9158679395233491
[212.35333333333332, 231.74444444444444]
0.9163254542839334
[212.55444444444444, 231.6911111111111]
0.917404398576649
[212.42111111111112, 231.52666666666667]
0.9174801078829412
[212.40666666666667, 231.40555555555557]
0.9178978705015245
[212.70222222222222, 231.18555555555557]
0.92004979165365
[212.4611111111111, 231.17444444444445]
0.919051029285244
[212.4177777777778, 230.7711111111111]
0.9204695369148844
[213.4988888888889, 231.30777777777777]
0.923007825071934
[213.17222222222222, 231.2]
0.9220251826220685
[213.04111111111112, 230.73444444444445]
0.9233173296863638
[212.99, 230.60111111111112]
0.9236295478965602
[212.85222222222222, 230.47666666666666]
0.9235304610252183
[213.1677777777778, 230.34777777777776]
0.9254171229011207
[213.22333333333333, 230.33555555555554]
0.9257074220219776
[213.21444444444444, 230.45666666666668]
0.9251823673768508
[213.41666666666666, 230.67]
0.9252033930145518
[213.49444444444444, 230.86555555555555]
0.9247565923409007
[213.37222222222223, 231.11555555555555]
0.923227437933886
[213.08333333333334, 230.8]
0.9232380127094165
[212.92111111111112, 230.61222222222221]
0.923286324806915
[212.78444444444443, 230.60444444444445]
0.9227248197972477
[213.14444444444445, 231.18555555555557]
0.9219626370351858
[212.79666666666665, 230.69333333333333]
0.9224222633221593
[209.97666666666666, 230.34]
0.9115944545743973
[201.88777777777779, 229.25]
0.8806446140797286
[201.49777777777777, 226.90666666666667]
0.8880205272848356
[200.59222222222223, 224.07444444444445]
0.8952034790025141
[199.26555555555555, 223.14111111111112]
0.893002434931558
[197.8788888888889, 223.09333333333333]
0.886978046059447
[198.9088888888889, 223.78333333333333]
0.8888458578486135
[202.14666666666668, 224.84444444444443]
0.8990511958885156
[205.61222222222221, 225.34666666666666]
0.9124262864130327
[208.23333333333332, 225.6]
0.9230200945626477
[210.07555555555555, 225.75555555555556]
0.9305443449158382
[211.26444444444445, 226.0822222222222]
0.9344584566087069
[211.5288888888889, 226.14444444444445]
0.935370707021078
[211.39, 225.75666666666666]
0.9363621598476235
[211.83555555555554, 225.84666666666666]
0.937961842351251
[212.30666666666667, 225.84444444444443]
0.9400570697628654
[213.2211111111111, 226.40333333333334]
0.9417754940789054
[213.5288888888889, 226.46777777777777]
0.9428665348516592
[213.59, 226.61]
0.9425444596443228
[214.10444444444445, 226.5988888888889]
0.9448609633272694
[214.24666666666667, 227.01222222222222]
0.9437671001561345
[214.96777777777777, 227.46555555555557]
0.9450563943747282
[215.87444444444444, 228.5311111111111]
0.9446173144429643
[215.75555555555556, 228.8411111111111]
0.942818161072457
[216.2211111111111, 229.09666666666666]
0.9437985905997953
[216.12777777777777, 229.44666666666666]
0.9419521360567936
[215.4922222222222, 229.82111111111112]
0.9376519901952726
[214.0888888888889, 229.61555555555555]
0.9323797264993662
[211.49666666666667, 229.31222222222223]
0.9223087396611122
[207.53222222222223, 229.44333333333333]
0.9045031695068741
[204.8022222222222, 230.28222222222223]
0.8893531608557614
[215.16555555555556, 229.8188888888889]
0.9362396476452473
[218.5822222222222, 231.8388888888889]
0.9428194867125158
[218.74555555555557, 236.00222222222223]
0.9268792195930359
[217.55555555555554, 236.95111111111112]
0.9181453276812844
[218.00444444444443, 237.59444444444443]
0.9175485771739893
[217.96777777777777, 237.63]
0.9172569868189108
[217.96, 237.65777777777777]
0.91711704972603
[217.85666666666665, 237.70111111111112]
0.9165151380585328
[217.23222222222222, 237.66333333333333]
0.9140333899026167
[217.4988888888889, 237.42555555555555]
0.916071938338567
[218.68666666666667, 237.60222222222222]
0.9203898205216936
[219.2888888888889, 237.48777777777778]
0.9233691558395988
[219.61777777777777, 237.4988888888889]
0.9247107588807433
[220.11444444444444, 237.56222222222223]
0.9265549142680748
[220.30444444444444, 237.79333333333332]
0.9264534095900269
[220.28, 237.70555555555555]
0.9266926870311076
[220.61111111111111, 237.79777777777778]
0.9277257053145063
[220.08444444444444, 237.79222222222222]
0.925532561106101
[220.46444444444444, 237.68666666666667]
0.9275423293037519
[220.64222222222222, 237.62222222222223]
0.928542036846535
[220.51111111111112, 237.52]
0.9283896560757456
[220.61, 237.39777777777778]
0.9292841831337934
[220.5677777777778, 237.27444444444444]
0.9295892707460185
[220.67333333333335, 236.81555555555556]
0.9318363095517375
[220.35555555555555, 236.54444444444445]
0.9315608999953027
[220.38888888888889, 236.06222222222223]
0.933605075874534
[220.2577777777778, 235.11]
0.9368286239537994
[219.83777777777777, 234.60666666666665]
0.9370482983338543
[219.58777777777777, 233.9922222222222]
0.9384404989719507
[219.28333333333333, 232.81444444444443]
0.9418802766151394
[218.93666666666667, 231.16333333333333]
0.9471081053800343
[218.88444444444445, 230.4688888888889]
0.9497353221934028
[218.62222222222223, 230.24333333333334]
0.9495268291035088
[218.4611111111111, 229.50666666666666]
0.9518726156587076
[218.55555555555554, 228.8188888888889]
0.9551464768351485
[218.25222222222223, 228.89666666666668]
0.9534967258394133
[218.13888888888889, 229.48777777777778]
0.9505468700826478
[218.53444444444443, 229.52666666666667]
0.9521091715317512
[218.40555555555557, 229.85666666666665]
0.9501815140836561
[218.41555555555556, 229.95444444444445]
0.9498209790344947
[218.4388888888889, 230.2588888888889]
0.948666476864206
[218.2811111111111, 230.1288888888889]
0.948516773209216
[218.26333333333332, 230.41]
0.9472823806837087
[218.42555555555555, 230.45555555555555]
0.9477990453690758
[218.18333333333334, 230.74444444444444]
0.9455626715462031
[218.12333333333333, 230.76444444444445]
0.945220715688918
[218.39111111111112, 230.7511111111111]
0.9464357942179165
[218.29444444444445, 230.72555555555556]
0.9461216548761636
[218.21555555555557, 230.70666666666668]
0.9458571731299004
[218.0888888888889, 230.73222222222222]
0.9452034344767143
[217.91444444444446, 230.75555555555556]
0.9443518875192605
[218.33, 230.88111111111112]
0.9456382072543349
[218.0088888888889, 230.8]
0.944579241286347
[218.09444444444443, 231.21555555555557]
0.9432516074466346
[218.18555555555557, 231.0]
0.9445262145262145
[217.93666666666667, 230.95555555555555]
0.9436303281054557
[218.17888888888888, 231.00666666666666]
0.9444700970630958
[218.02555555555554, 230.96666666666667]
0.9439697888103141
[218.63888888888889, 231.0988888888889]
0.9460836871180687
[218.63444444444445, 231.32333333333332]
0.9451465241052688
[218.83777777777777, 231.38666666666666]
0.9457665859936231
[218.7411111111111, 231.31444444444443]
0.9456439766935821
[218.75333333333333, 231.3022222222222]
0.9457467863113195
[218.86, 231.10555555555555]
0.9470131493545518
[218.60777777777778, 231.18555555555557]
0.9455944479422493
[218.4711111111111, 231.12333333333333]
0.9452577027176446
[218.26111111111112, 230.86555555555555]
0.9454035297118574
[218.2277777777778, 230.97222222222223]
0.9448226097414312
[217.91555555555556, 230.56]
0.945157683707302
[217.64222222222222, 230.0]
0.9462705314009662
[217.87333333333333, 229.34]
0.9500014534461207
[217.9188888888889, 228.97333333333333]
0.9517216949086745
[217.8111111111111, 227.97222222222223]
0.9554282929206774
[217.36333333333334, 226.63444444444445]
0.9590922238945733
[216.96666666666667, 226.4477777777778]
0.9581311364405823
[216.71444444444444, 226.31444444444443]
0.9575811432471046
[216.16666666666666, 225.60333333333332]
0.9581714218170535
[216.02777777777777, 225.33444444444444]
0.9586984285087351
[215.76555555555555, 225.18777777777777]
0.9581583764660604
[215.8177777777778, 225.21]
0.9582957141236081
[215.79444444444445, 225.23111111111112]
0.9581022949266926
[216.04777777777778, 225.64888888888888]
0.9574511039766797
[216.08, 226.27777777777777]
0.9549324821998527
[216.4311111111111, 226.0088888888889]
0.9576221190906945
[216.8088888888889, 226.12]
0.9588222576016668
[216.80666666666667, 226.3388888888889]
0.9578851770943275
[218.02, 225.63888888888889]
0.9662341499446018
[226.66555555555556, 226.0388888888889]
1.0027723842996534
[235.40555555555557, 226.33444444444444]
1.040078350130829
[241.46, 225.90333333333334]
1.0688642634755279
[248.0377777777778, 226.11444444444444]
1.0969568016196323
[249.0911111111111, 226.11777777777777]
1.101598970054937
[247.29222222222222, 226.41333333333333]
1.092215809826669
[243.19, 226.2411111111111]
1.0749151593432769
[241.57555555555555, 226.2877777777778]
1.0675590079495627
[238.1511111111111, 226.35333333333332]
1.0521210693213168
[242.21777777777777, 226.53333333333333]
1.0692368059642927
[243.90555555555557, 226.9477777777778]
1.074721056728665
[245.14444444444445, 226.69555555555556]
1.0813817846745022
[243.67444444444445, 226.83777777777777]
1.074223380389314
[242.7488888888889, 227.12444444444444]
1.0687924388000705
[240.00555555555556, 226.84666666666666]
1.058007856506108
[227.01888888888888, 226.87666666666667]
1.0006268702035859
[212.92555555555555, 227.09666666666666]
0.937598770959014
[200.53555555555556, 227.43666666666667]
0.8817204301075269
[192.52555555555554, 227.40333333333334]
0.8466259167509514
[192.08, 227.46444444444444]
0.844439668226536
[195.95444444444445, 227.62555555555556]
0.860863113397734
[200.18555555555557, 228.0222222222222]
0.8779212552382809
[200.17666666666668, 228.06333333333333]
0.8777240240284132
[192.64111111111112, 227.96333333333334]
0.8450530543410978
[186.11444444444444, 227.7488888888889]
0.8171914486715388
[181.17555555555555, 227.9788888888889]
0.7947032132604871
[175.87222222222223, 227.39555555555555]
0.7734197873504809
[177.68555555555557, 227.2711111111111]
0.7818220040675845
[177.18666666666667, 227.06444444444443]
0.7803364683545543
[175.11888888888888, 227.2488888888889]
0.7706039389020358
[173.18555555555557, 227.20666666666668]
0.762238001623583
[169.05777777777777, 227.2411111111111]
0.7439577150065765
[166.82111111111112, 227.17333333333335]
0.7343340376413507
[166.22555555555556, 227.05777777777777]
0.732084834011901
[169.91, 227.33444444444444]
0.7474010390956056
[170.90777777777777, 227.04888888888888]
0.7527355831343225
[179.46444444444444, 227.05]
0.7904181653576059
[180.45222222222222, 226.86444444444444]
0.7954187032883072
[176.23222222222222, 226.57111111111112]
0.7778230038153339
[174.88, 227.13333333333333]
0.769944232462577
[174.9411111111111, 226.92666666666668]
0.770914735058805
[173.9111111111111, 227.45111111111112]
0.7646087559719792
[170.76888888888888, 227.3111111111111]
0.7512562322807703
[164.29, 227.64111111111112]
0.7217061944483762
[162.25222222222223, 227.69666666666666]
0.7125805774739298
[163.63222222222223, 227.95888888888888]
0.7178146156958126
[164.09777777777776, 227.67222222222222]
0.7207632805446426
[165.32333333333332, 227.64111111111112]
0.7262455033996007
[165.76444444444445, 227.64444444444445]
0.7281725888324874
[167.23111111111112, 227.8488888888889]
0.7339562282994577
[170.26, 227.61]
0.7480339176661833
[178.3711111111111, 228.00444444444443]
0.7823141849086762
[178.04888888888888, 228.45444444444445]
0.7793627710849232
[176.86666666666667, 228.94222222222223]
0.7725384376455972
[171.28, 229.0522222222222]
0.7477770717012617
[165.05555555555554, 229.62777777777777]
0.7187961193235429
[165.2577777777778, 230.31666666666666]
0.717524181682225
[165.64666666666668, 230.86222222222221]
0.7175130910210997
[164.02777777777777, 230.83]
0.71059991239344
[163.40333333333334, 230.9]
0.707680092392089
[161.45333333333335, 231.33666666666667]
0.6979150156337806
[160.88222222222223, 231.5]
0.6949556035517159
[160.26111111111112, 231.76555555555555]
0.6914794164601202
[160.34333333333333, 231.80666666666667]
0.6917114837076874
[163.21777777777777, 232.41555555555556]
0.7022670121525619
[163.23111111111112, 233.10222222222222]
0.7002554911531422
[162.09333333333333, 233.34777777777776]
0.6946427125939824
[159.87666666666667, 233.88777777777779]
0.6835614420971121
[157.92777777777778, 234.0611111111111]
0.6747288220075479
[156.89333333333335, 234.37444444444444]
0.6694131423126337
[156.62222222222223, 234.43777777777777]
0.6680758694560036
[156.5377777777778, 234.79777777777778]
0.6666919050909057
[157.64555555555555, 234.9488888888889]
0.6709780850681472
[157.96777777777777, 235.31333333333333]
0.6713082320499381
[157.88444444444445, 235.19222222222223]
0.671299598909639
[158.68333333333334, 235.49666666666667]
0.6738241164064601
[159.19333333333333, 235.55666666666667]
0.6758175668982693
[159.94444444444446, 236.00666666666666]
0.6777115524043578
[159.87222222222223, 235.73777777777778]
0.6781782017684433
[160.50222222222223, 235.8]
0.6806710017905947
[161.08777777777777, 235.94555555555556]
0.6827328338458495
[161.81222222222223, 235.87333333333333]
0.6860132085959508
[162.0211111111111, 235.93555555555557]
0.6867176535965565
[162.08777777777777, 236.0511111111111]
0.6866639051806106
[161.25666666666666, 235.98888888888888]
0.6833231319741984
[160.66333333333333, 236.11444444444444]
0.6804468642795631
[160.7588888888889, 235.97555555555556]
0.681252295435497
[161.7277777777778, 236.10888888888888]
0.6849711526696722
[160.99666666666667, 236.07222222222222]
0.6819805615042478
[160.38888888888889, 235.23111111111112]
0.6818353581347893
[159.75555555555556, 234.04222222222222]
0.6825928844747862
[159.79777777777778, 233.63222222222223]
0.6839714841464981
[160.6977777777778, 233.24666666666667]
0.6889606615790628
[163.0222222222222, 233.35333333333332]
0.6986067860850023
[165.03555555555556, 233.40555555555557]
0.7070763811201295
[165.64444444444445, 233.63777777777779]
0.7089797121850537
[165.50222222222223, 233.58777777777777]
0.708522611057466
[165.9411111111111, 233.58444444444444]
0.7104116522218945
[166.12777777777777, 233.66444444444446]
0.7109672940303758
[166.26888888888888, 233.55444444444444]
0.7119063363764813
[165.41333333333333, 233.20111111111112]
0.709316231578847
[165.04222222222222, 233.17555555555555]
0.7078024187784121
[165.11888888888888, 232.89333333333335]
0.7089893322646513
[164.34333333333333, 232.73111111111112]
0.7061511138271157
[163.13555555555556, 231.98222222222222]
0.7032243850103457
[162.79, 229.7111111111111]
0.7086727290316339
[162.7511111111111, 226.53666666666666]
0.7184316495244821
[162.2888888888889, 225.6511111111111]
0.7192027023034577
[161.71444444444444, 225.62555555555556]
0.7167381551538192
[161.57444444444445, 226.4477777777778]
0.7135174653955045
[161.92111111111112, 227.52777777777777]
0.7116542546697595
[161.10111111111112, 228.76555555555555]
0.7042192637780552
[163.20777777777778, 227.37666666666667]
0.7177859547789034
[162.88333333333333, 226.45]
0.7192904982704056
[162.5588888888889, 227.01888888888888]
0.7160588693060295
[162.69444444444446, 227.00333333333333]
0.7167050899888892
[162.79666666666665, 227.4388888888889]
0.7157820171474633
[162.05777777777777, 228.28222222222223]
0.7099009997371674
[162.02, 229.13777777777779]
0.7070854992629374
[162.53444444444443, 229.93777777777777]
0.7068627261481367
[163.09555555555556, 230.58777777777777]
0.7073035575750859
[163.4911111111111, 230.5011111111111]
0.7092855662300978
[164.2511111111111, 230.45222222222222]
0.7127339000130178
[164.92333333333335, 230.07222222222222]
0.716832878564702
[163.51888888888888, 229.61555555555555]
0.7121420345117927
[162.40444444444444, 229.32777777777778]
0.7081760701567382
[161.42333333333335, 228.70333333333335]
0.7058197665097433
[160.35444444444445, 230.99666666666667]
0.6941851012761128
[161.54777777777778, 230.89333333333335]
0.6996641065619525
[161.4088888888889, 230.90333333333334]
0.6990323030801731
[161.0677777777778, 230.64111111111112]
0.6983480828800879
[160.54666666666665, 230.2488888888889]
0.6972744469752538
[158.98333333333332, 229.82555555555555]
0.691756549653602
[159.76444444444445, 229.71666666666667]
0.6954847759317033
[160.3711111111111, 228.81]
0.7008920550286749
[161.5377777777778, 227.98777777777778]
0.7085370073444484
[164.98888888888888, 227.5511111111111]
0.7250629895115138
[172.00666666666666, 227.60666666666665]
0.7557189303183856
[171.86555555555555, 227.2511111111111]
0.7562803751112328
[171.67111111111112, 227.87555555555556]
0.7533546575128726
[170.75, 228.15555555555557]
0.7483929093211259
[169.89111111111112, 228.8711111111111]
0.7423003728444928
[169.13777777777779, 228.67555555555555]
0.7396408302884242
[171.40666666666667, 229.04666666666665]
0.7483482259801496
[168.5988888888889, 229.14666666666668]
0.7357684549439466
[165.89444444444445, 229.4988888888889]
0.7228551094413432
[165.88111111111112, 229.2488888888889]
0.7235852348733061
[163.64888888888888, 229.1]
0.7143120422910907
[142.29444444444445, 229.35]
0.6204248722234335
[141.36777777777777, 229.27]
0.6165995454170967
[142.28222222222223, 229.48555555555555]
0.6200051322523326
[140.17888888888888, 229.5688888888889]
0.6106179699146225
[126.43444444444444, 229.6511111111111]
0.5505501098284354
[113.93555555555555, 229.7277777777778]
0.4959589852724238
[110.43, 229.80666666666667]
0.48053436221751616
[110.06111111111112, 229.8488888888889]
0.47884117101090573
[109.00888888888889, 229.9688888888889]
0.47401580890168715
[107.03555555555556, 229.87333333333333]
0.4656284137157662
[102.92222222222222, 229.9]
0.44768256729979217
[99.80555555555556, 229.86555555555555]
0.4341910005365455
[99.17222222222222, 229.86777777777777]
0.4314315959416283
[99.43777777777778, 229.88666666666666]
0.43255130547419507
[99.11444444444444, 229.97]
0.43098858305189564
[100.55777777777777, 230.26444444444445]
0.4367056234860402
[98.05555555555556, 230.45333333333335]
0.4254898557432693
[93.30333333333333, 230.48]
0.4048218211269235
[90.46222222222222, 230.98777777777778]
0.39163207288504925
[89.21, 230.94666666666666]
0.38627966052768314
[93.61888888888889, 230.92444444444445]
0.40540917664267295
[98.90555555555555, 230.9922222222222]
0.4281769948964131
[102.14444444444445, 231.35222222222222]
0.44151053948524854
[103.30555555555556, 231.52]
0.4462057513629732
[104.25888888888889, 231.40555555555557]
0.45054617914676015
[104.22444444444444, 231.38777777777779]
0.45043193484722616
[108.09666666666666, 231.09]
0.46776869040922003
[114.47777777777777, 230.94333333333333]
0.4956963949790473
[118.40555555555555, 230.84444444444443]
0.5129235656526762
[121.26555555555555, 230.68666666666667]
0.5256721478869847
[132.12444444444444, 230.61666666666667]
0.5729180217291802
[140.69333333333333, 230.45777777777778]
0.6104950533238193
[142.1688888888889, 230.45111111111112]
0.6169156147845288
[157.1688888888889, 230.32111111111112]
0.68239028602579
[163.73555555555555, 228.5822222222222]
0.7163092298419241
[163.23777777777778, 226.42666666666668]
0.7209300043182978
[161.43666666666667, 225.52555555555554]
0.7158242721938386
[160.14333333333335, 225.15666666666667]
0.7112529053843991
[153.39222222222222, 225.41222222222223]
0.680496473128244
[149.75555555555556, 227.05777777777777]
0.6595482305042281
[150.25222222222223, 229.58777777777777]
0.6544434711487739
[149.70111111111112, 229.82555555555555]
0.6513684291950901
[147.71777777777777, 230.25333333333333]
0.6415445789179068
[148.99, 231.0077777777778]
0.6449566392665952
[150.07333333333332, 231.26111111111112]
0.6489345857256107
[150.77, 231.46777777777777]
0.6513649608056797
[151.63666666666666, 231.87333333333333]
0.6539633708058997
[152.24333333333334, 232.28555555555556]
0.6554145520121307
[152.3788888888889, 232.71666666666667]
0.6547828785600038
[152.7511111111111, 232.83555555555554]
0.65604718637856
[152.86111111111111, 233.3188888888889]
0.6551596051184121
[152.91444444444446, 233.10444444444445]
0.655991115093854
[152.34666666666666, 233.14666666666668]
0.6534370353425597
[152.61777777777777, 232.9477777777778]
0.6551587623358597
[153.42222222222222, 232.7]
0.6593133743971733
[153.2788888888889, 232.63333333333333]
0.6588861823565937
[153.84555555555556, 232.8111111111111]
0.6608170667684818
[152.4188888888889, 232.80777777777777]
0.6546984398192118
[151.9988888888889, 233.3388888888889]
0.6514082998023857
[151.89666666666668, 233.14444444444445]
0.6515131296764047
[151.76777777777778, 233.19444444444446]
0.6508207266229898
[151.88888888888889, 233.28333333333333]
0.6510919006453764
[151.53222222222223, 233.2188888888889]
0.6497424927464424
[151.63777777777779, 233.3111111111111]
0.6499380893418422
[151.90444444444444, 233.45333333333335]
0.650684409922516
[151.59666666666666, 233.5311111111111]
0.6491497682916385
[152.6977777777778, 233.55333333333334]
0.6538026051627513
[152.82111111111112, 233.76333333333332]
0.6537428643404773
[152.4488888888889, 233.58555555555554]
0.6526469007311145
[151.75222222222223, 233.4411111111111]
0.6500663979019216
[149.92888888888888, 233.36555555555555]
0.642463659780316
[147.68, 233.4688888888889]
0.6325468061411942
[146.11, 233.38777777777779]
0.6260396383700947
[145.7188888888889, 233.22222222222223]
0.6248070509766556
[145.94555555555556, 233.32111111111112]
0.6255137173851963
[146.7111111111111, 233.17777777777778]
0.629181359001239
[146.60666666666665, 232.9911111111111]
0.6292371668923945
[147.82444444444445, 232.74444444444444]
0.6351362963670216
[150.05444444444444, 232.65777777777777]
0.644957782532284
[149.64444444444445, 232.46333333333334]
0.64373353981751
[149.5611111111111, 232.76888888888888]
0.6425305023580853
[148.57444444444445, 232.3022222222222]
0.6395739266855438
[149.4088888888889, 232.19222222222223]
0.6434706876007905
[149.06, 232.2111111111111]
0.6419158811426384
[149.53555555555556, 232.45555555555555]
0.6432866497777353
[150.2888888888889, 232.11777777777777]
0.6474682393038017
[150.57111111111112, 232.29333333333332]
0.6481938545134505
[150.29333333333332, 232.30333333333334]
0.6469701970125267
[150.51777777777778, 232.60111111111112]
0.6471068734743791
[150.59555555555556, 232.45888888888888]
0.6478373714826517
[150.14888888888888, 232.90333333333334]
0.6446832973145749
[150.75333333333333, 232.90333333333334]
0.647278556196419
[151.8188888888889, 232.77555555555554]
0.6522114769592073
[152.99333333333334, 233.28666666666666]
0.6558168776612465
[152.78666666666666, 233.12]
0.655399222145962
[153.89666666666668, 233.43666666666667]
0.6592651825620083
[154.27777777777777, 233.04111111111112]
0.6620195768986874
[154.95333333333335, 233.0222222222222]
0.6649723440778181
[156.32, 232.93666666666667]
0.6710836994318913
[156.45555555555555, 232.96777777777777]
0.6715759451712444
[156.80555555555554, 232.97222222222223]
0.6730654584475974
[157.17, 233.01]
0.6745204068494914
[157.99, 232.95555555555555]
0.6781980349136698
[157.53222222222223, 233.10777777777778]
0.6757913602196409
[157.06222222222223, 233.1677777777778]
0.6736017460007339
[156.75222222222223, 233.11666666666667]
0.672419627749577
[156.2722222222222, 233.03555555555556]
0.6705939007876718
[155.65222222222224, 233.09222222222223]
0.667770982396095
[155.56444444444443, 233.0088888888889]
0.6676330898201308
[155.5011111111111, 233.3188888888889]
0.6664745912842223
[155.67777777777778, 233.07777777777778]
0.6679220098202794
[155.11555555555555, 233.0]
0.665731998092513
[155.28666666666666, 232.97333333333333]
0.6665426658272764
[154.13111111111112, 233.3]
0.6606562842310807
[154.42888888888888, 233.09777777777776]
0.6625069117394703
[153.16, 233.05]
0.6571980261746406
[153.2488888888889, 232.98444444444445]
0.6577644668695097
[152.28222222222223, 232.93666666666667]
0.6537494693359664
[151.72444444444446, 232.86888888888888]
0.6515445028676128
[150.80555555555554, 232.94222222222223]
0.6473946806074944
[150.79888888888888, 233.01222222222222]
0.6471715837509715
[150.26, 233.09]
0.6446436998584237
[150.1811111111111, 232.89777777777778]
0.6448370291210259
[150.42666666666668, 232.9711111111111]
0.6456880681438806
[150.15333333333334, 232.96666666666667]
0.6445271140363429
[150.26, 232.9777777777778]
0.6449542159481113
[150.12222222222223, 233.13111111111112]
0.6439390328761116
[149.79333333333332, 233.32666666666665]
0.6419897711363182
[150.75, 232.97]
0.6470790230501782
[151.56444444444443, 232.9411111111111]
0.6506556258854169
[151.84444444444443, 233.06444444444443]
0.6515126955825284
[152.72333333333333, 233.43555555555557]
0.6542419511452126
[154.48111111111112, 233.09555555555556]
0.6627372655944629
[156.07888888888888, 233.13]
0.6694929390850122
[157.85444444444445, 232.98555555555555]
0.6775288882954118
[157.9711111111111, 233.42222222222222]
0.6767612338156892
[157.24666666666667, 232.9011111111111]
0.6751649484044253
[159.67777777777778, 232.97555555555556]
0.6853842558589838
[160.07111111111112, 232.98333333333332]
0.6870496220521259
[161.3022222222222, 233.1911111111111]
0.6917168559884119
[162.70222222222222, 232.90666666666667]
0.6985726280436608
[164.70222222222222, 232.98]
0.7069371715264067
[164.96777777777777, 233.26666666666668]
0.7072068209964751
[165.69222222222223, 234.06222222222223]
0.7078981847182135
[165.8322222222222, 234.67777777777778]
0.7066379432792007
[166.0511111111111, 236.27555555555554]
0.7027858244610813
[166.71555555555557, 236.75333333333333]
0.7041740583260591
[166.11, 237.46555555555557]
0.6995119760058769
[163.6511111111111, 237.82]
0.688130145114419
[159.67777777777778, 237.91]
0.6711688360210911
[153.79555555555555, 237.84777777777776]
0.6466133801731266
[147.85888888888888, 237.73444444444445]
0.6219497945887335
[145.60666666666665, 237.62555555555556]
0.6127567648447837
[146.34777777777776, 238.02666666666667]
0.6148377399357681
[145.63555555555556, 238.46444444444444]
0.6107223066098836
[144.5688888888889, 238.38888888888889]
0.6064413889536239
[146.1211111111111, 238.34777777777776]
0.6130584160400535
[151.64555555555555, 238.66555555555556]
0.6353893640100745
[147.55444444444444, 238.8088888888889]
0.6178766842849698
[142.66666666666666, 238.86444444444444]
0.5972704183683911
[140.5522222222222, 238.72]
0.5887743893357164
[139.9111111111111, 238.34222222222223]
0.5870177336043411
[142.38888888888889, 237.70555555555555]
0.5990137191202936
[154.32555555555555, 236.82111111111112]
0.6516545540703484
[169.38222222222223, 235.63555555555556]
0.7188313402995209
[168.8022222222222, 235.3388888888889]
0.7172729633389201
[168.41222222222223, 235.19444444444446]
0.7160552734144325
[168.10888888888888, 234.61888888888888]
0.7165189882409772
[164.1288888888889, 233.01888888888888]
0.7043587310518461
[163.02444444444444, 232.73888888888888]
0.7004606974912276
[161.3177777777778, 234.2722222222222]
0.6885911451540232
[161.21666666666667, 235.82777777777778]
0.683620344413296
[158.53, 235.59333333333333]
0.6728967995698804
[146.35666666666665, 235.47444444444446]
0.6215394923723734
[134.25333333333333, 235.5]
0.5700778485491861
[187.0611111111111, 235.65222222222224]
0.7938016002866747
[188.14888888888888, 235.69666666666666]
0.7982670758555016
[95.66111111111111, 235.93]
0.40546395588145256
[78.45, 236.05444444444444]
0.3323385847897613
[87.38555555555556, 236.06444444444443]
0.37017669374652873
[80.87333333333333, 235.96666666666667]
0.3427320242972171
[78.24555555555555, 235.35222222222222]
0.3324615115878329
[80.41222222222223, 196.96444444444444]
0.40825755353476095
[82.44222222222223, 40.07888888888889]
2.056998697014222
[84.77, 32.486666666666665]
2.6093782064436692
[78.46555555555555, 28.15111111111111]
2.7872987053994316
[98.7388888888889, 24.49888888888889]
4.030341512086716
[99.24333333333334, 24.59]
4.035922461705301
[104.14333333333333, 24.19]
4.305222543750861
[108.87222222222222, 23.34888888888889]
4.662843818406776
[112.55888888888889, 25.864444444444445]
4.351877309047169
[113.84555555555555, 30.255555555555556]
3.7627983841351447
[110.68, 29.256666666666668]
3.7830693858949527
[103.57555555555555, 29.89]
3.465224341102561
[98.59222222222222, 33.13444444444445]
2.975520606284162
[91.68777777777778, 34.44888888888889]
2.6615597987356474
[78.0911111111111, 38.29]
2.039464902353385
[72.07, 35.87888888888889]
2.0087021151404416
[66.56555555555556, 30.506666666666668]
2.1820002913752914
[67.6588888888889, 31.30666666666667]
2.161165530948325
[75.34333333333333, 37.10888888888889]
2.0303311575543446
[75.94555555555556, 37.797777777777775]
2.0092598036333706
[76.02222222222223, 37.98777777777778]
2.0012284652958554
[77.27777777777777, 37.49]
2.06129041818559
[79.61777777777777, 36.94111111111111]
2.1552621289138867
[83.43222222222222, 35.84111111111111]
2.327835818582013
[88.76, 34.14]
2.5998828353837142
[95.99666666666667, 32.876666666666665]
2.9199026665314816
[112.70111111111112, 31.95]
3.527421318031647
[138.89777777777778, 30.441111111111113]
4.562835346935795
[153.48666666666668, 28.455555555555556]
5.393908629441625
[149.1811111111111, 28.76222222222222]
5.186703237271112
[146.7411111111111, 29.692222222222224]
4.942072372113909
[149.3188888888889, 29.776666666666667]
5.014627411470578
[151.86333333333334, 30.04111111111111]
5.055183637237859
[147.46555555555557, 30.247777777777777]
4.875252543804871
[143.09666666666666, 29.891111111111112]
4.787264887368969
[148.44222222222223, 29.834444444444443]
4.975531637555399
[130.40777777777777, 26.38222222222222]
4.9430171832884096
[110.64888888888889, 24.68111111111111]
4.483140503308873
[94.27333333333333, 24.48111111111111]
3.850860073526074
[77.60444444444444, 24.516666666666666]
3.165375028325402
[66.94777777777777, 23.56]
2.8415864931145065
[61.09111111111111, 24.265555555555554]
2.5176061174962223
[63.35333333333333, 24.08888888888889]
2.629981549815498
[75.02222222222223, 24.543333333333333]
3.0567250667753183
[97.50555555555556, 24.965555555555557]
3.9056032756241934
[120.11777777777777, 24.164444444444445]
4.970847894059223
[129.57777777777778, 23.275555555555556]
5.567118579339317
[136.59666666666666, 22.47111111111111]
6.078767800632911
[143.37333333333333, 22.54]
6.360839988169181
[133.41222222222223, 22.628888888888888]
5.895659432387313
[122.32666666666667, 21.9]
5.585692541856925
[111.31, 21.06222222222222]
5.284817472040515
[97.00444444444445, 20.73777777777778]
4.677668238319759
[83.01222222222222, 20.335555555555555]
4.082122172440171
[69.98777777777778, 19.92]
3.5134426595269965
[60.30555555555556, 19.452222222222222]
3.1001884960301593
[55.48222222222222, 19.176666666666666]
2.893215134132916
[52.60444444444445, 19.33222222222222]
2.721075923903673
[51.312222222222225, 19.22888888888889]
2.6684964752109095
[51.67, 18.855555555555554]
2.7403064230995877
[52.66, 18.215555555555557]
2.8909357081859213
[54.88777777777778, 18.793333333333333]
2.920598320917583
[55.885555555555555, 19.616666666666667]
2.8488813367318038
[56.18, 19.303333333333335]
2.910378173027111
[56.187777777777775, 17.31222222222222]
3.24555548424363
[56.12, 16.27777777777778]
3.447645051194539
[56.32333333333333, 15.453333333333333]
3.644736842105263
[55.94, 15.077777777777778]
3.7100957995578483
[56.52, 14.824444444444444]
3.812621795832709
[57.01, 14.896666666666667]
3.827030655627657
[58.24666666666667, 14.727777777777778]
3.9548849490758204
[58.94444444444444, 14.484444444444444]
4.069499846578705
[59.047777777777775, 14.103333333333333]
4.186795871740329
[59.49666666666667, 14.2]
4.189906103286385
[60.05222222222222, 15.192222222222222]
3.952826738828348
[60.25333333333333, 16.034444444444443]
3.7577437461021415
[60.37555555555556, 16.26888888888889]
3.711105040295042
[59.65111111111111, 16.662222222222223]
3.5800213390237396
[59.21333333333333, 17.537777777777777]
3.3763304612265586
[58.74333333333333, 17.89666666666667]
3.2823617060905192
[58.50111111111111, 18.51]
3.160513836364727
[58.15, 19.215555555555557]
3.0261940557418754
[59.093333333333334, 19.83111111111111]
2.97982967279247
[59.85111111111111, 19.845555555555556]
3.0158445775712446
[60.742222222222225, 20.055555555555557]
3.028698060941828
[61.78888888888889, 19.753333333333334]
3.1280233997075038
[62.82555555555555, 19.90222222222222]
3.1567105850826263
[63.45333333333333, 19.81111111111111]
3.202916432978127
[63.60666666666667, 19.044444444444444]
3.3399066511085183
[62.89888888888889, 18.36]
3.425865407891552
[61.38666666666666, 17.16]
3.577311577311577
[60.34888888888889, 15.55]
3.8809574848160056
[59.51777777777778, 14.848888888888888]
4.008231068542353
[59.452222222222225, 13.74]
4.32694484877891
[58.91111111111111, 13.0]
4.5316239316239315
[59.507777777777775, 11.962222222222222]
4.974642392717816
[66.68111111111111, 11.03888888888889]
6.040563663814796
[188.33333333333334, 10.508888888888889]
17.92133643476422
[243.64777777777778, 10.905555555555555]
22.34161996943454
[246.1, 15.145555555555555]
16.248991269899495
[249.39666666666668, 30.373333333333335]
8.211040386303775
[250.62555555555556, 226.8177777777778]
1.1049643375004898
[251.84555555555556, 230.69555555555556]
1.0916792694556559
[252.38222222222223, 229.99]
1.0973617210410114
[252.52555555555554, 230.4411111111111]
1.0958355231753594
[252.77777777777777, 230.6677777777778]
1.0958521394405614
[252.98, 231.0911111111111]
1.094719735361714
[253.21333333333334, 231.4622222222222]
1.093972618521861
[253.32111111111112, 232.66444444444446]
1.0887830829329792
[253.24555555555557, 233.84222222222223]
1.082976175769037
[253.25, 233.76666666666668]
1.0833452160273778
[253.35888888888888, 234.02777777777777]
1.0826017804154302
[253.28333333333333, 233.81222222222223]
1.083276703527522
[253.36666666666667, 233.79333333333332]
1.0837206649747642
[253.4177777777778, 233.97]
1.0831208179586178
[253.4688888888889, 234.3411111111111]
1.0816236540276047
[253.45333333333335, 233.88666666666666]
1.083658752102158
[253.4788888888889, 233.99333333333334]
1.0832739774162607
[253.46555555555557, 233.95777777777778]
1.0833816168159498
[253.4922222222222, 234.16444444444446]
1.0825393360791087
[253.41333333333333, 234.06666666666666]
1.0826545143833666
[253.42777777777778, 234.05777777777777]
1.082757343865712
[253.4622222222222, 234.1288888888889]
1.0825755993849542
[253.32888888888888, 233.95555555555555]
1.0828077507598783
[253.2588888888889, 234.04555555555555]
1.0820922802303445
[253.27444444444444, 233.90222222222224]
1.0828218818879682
[253.30777777777777, 233.80555555555554]
1.0834121420933824
[253.20777777777778, 233.83333333333334]
1.082855785222143
[253.23666666666668, 233.92222222222222]
1.0825678050634115
[253.35888888888888, 234.30555555555554]
1.0813183165382336
[252.96666666666667, 234.18333333333334]
1.0802078143904348
[252.93444444444444, 233.97555555555556]
1.0810293572927845
[252.69666666666666, 233.88666666666666]
1.0804235669697575
[252.62666666666667, 233.8]
1.0805246649558027
[252.54555555555555, 233.5522222222222]
1.0813237106143285
[252.55555555555554, 233.38333333333333]
1.0821490632959603
[252.50666666666666, 233.29777777777778]
1.0823363560161547
[252.51777777777778, 233.6677777777778]
1.0806700871607837
[252.4988888888889, 233.7811111111111]
1.0800653983070585
[252.41555555555556, 234.10333333333332]
1.0782228170845733
[252.4322222222222, 233.82555555555555]
1.079574991803006
[252.38888888888889, 233.89777777777778]
1.0790563779048776
[252.25444444444443, 234.64666666666668]
1.0750395393546797
[251.83333333333334, 234.17666666666668]
1.0753989153488108
[251.82777777777778, 234.43777777777777]
1.0741774647620312
[251.74333333333334, 234.10888888888888]
1.0753258217923285
[251.95222222222222, 234.20555555555555]
1.0757738928291862
[252.09222222222223, 234.19222222222223]
1.076432939702903
[252.09666666666666, 234.3188888888889]
1.0758700156956094
[251.9922222222222, 233.65222222222224]
1.0784927266069704
[251.92666666666668, 233.78666666666666]
1.0775921067640015
[251.8788888888889, 233.55333333333334]
1.0784641147870104
[251.85, 233.82555555555555]
1.0770850063912794
[251.78333333333333, 233.94444444444446]
1.0762526715744478
[251.63444444444445, 233.9411111111111]
1.0756315691983265
[251.71444444444444, 234.47666666666666]
1.073515962261111
[251.6288888888889, 234.13]
1.074740054195912
[251.62777777777777, 234.20555555555555]
1.0743885950138767
[251.54555555555555, 234.14222222222222]
1.0743280437341027
[251.3022222222222, 234.2122222222222]
1.0729680109682103
[251.1822222222222, 234.33]
1.0719166228063934
[251.2711111111111, 234.75555555555556]
1.0703521393411586
[251.17888888888888, 234.52666666666667]
1.0710035343055042
[251.11777777777777, 234.55555555555554]
1.0706110847939365
[250.93666666666667, 234.52666666666667]
1.0699707211688791
[251.06555555555556, 234.86111111111111]
1.0689958604376109
[250.95333333333335, 234.69]
1.0692970869373783
[250.83555555555554, 234.2722222222222]
1.0707012260191135
[250.76444444444445, 234.57333333333332]
1.069023664715133
[250.83666666666667, 234.72555555555556]
1.0686380785124945
[250.8022222222222, 233.53555555555556]
1.0739359222007592
[250.63333333333333, 235.51666666666668]
1.0641851249026961
[250.57777777777778, 234.28]
1.0695653823534992
[250.59666666666666, 235.33555555555554]
1.0648483017157535
[250.35888888888888, 235.08]
1.0649944227024368
[250.10777777777778, 234.93555555555557]
1.0645803577340358
[250.23222222222222, 234.59777777777776]
1.066643616970891
[250.27, 235.33333333333334]
1.063470254957507
[250.26111111111112, 235.53555555555556]
1.062519459199366
[250.25555555555556, 235.90666666666667]
1.0608244315077526
[250.28333333333333, 235.65777777777777]
1.062062689776135
[250.22666666666666, 235.17333333333335]
1.0640095248894432
[250.0, 235.91555555555556]
1.0597012113562292
[249.82555555555555, 236.52555555555554]
1.0562307103296331
[249.69, 236.92]
1.0539000506500085
[249.7111111111111, 237.2711111111111]
1.052429475892556
[249.55555555555554, 237.15666666666667]
1.0522814267174534
[249.2877777777778, 236.88333333333333]
1.0523652055629824
[249.29777777777778, 236.92888888888888]
1.0522050685625317
[249.35444444444445, 237.0077777777778]
1.052093930344527
[249.2288888888889, 236.96666666666667]
1.0517466122755192
[249.2122222222222, 237.5811111111111]
1.0489563798094685
[249.20555555555555, 237.1688888888889]
1.0507514570020426
[249.07555555555555, 237.1688888888889]
1.050203324400802
[248.88222222222223, 236.74666666666667]
1.0512596680934145
[248.85555555555555, 236.67111111111112]
1.051482601265704
[248.95, 236.18]
1.054068930476755
[248.89666666666668, 236.13444444444445]
1.0540464236475453
[248.79666666666665, 235.9322222222222]
1.0545260173590343
[248.45333333333335, 236.80777777777777]
1.04917725112257
[248.35888888888888, 236.30555555555554]
1.0510074056659222
[248.29222222222222, 236.82888888888888]
1.0484034417723063
[248.28333333333333, 236.58333333333334]
1.04945403311025
[248.39222222222222, 236.9922222222222]
1.0481028444440277
[248.46, 236.98111111111112]
1.0484379908384633
[248.39666666666668, 237.68666666666667]
1.0450593217962023
[248.42777777777778, 238.23111111111112]
1.0428015745681132
[247.80333333333334, 239.8711111111111]
1.0330686850345556
[248.34333333333333, 240.67888888888888]
1.0318451048192383
[248.32333333333332, 238.7577777777778]
1.040063848996193
[248.42444444444445, 239.57]
1.03695973804919
[248.61444444444444, 241.99777777777777]
1.0273418488691357
[248.46555555555557, 241.58777777777777]
1.0284690634643954
[248.2577777777778, 240.97222222222223]
1.0302340057636887
[247.96555555555557, 239.18777777777777]
1.0366982705359342
[247.52555555555554, 239.04666666666665]
1.035469596824423
[247.36666666666667, 238.48]
1.0372637817287265
[247.23888888888888, 238.48]
1.036727980916173
[247.04333333333332, 237.84666666666666]
1.038666367687866
[246.63777777777779, 237.24444444444444]
1.0395934807043836
[246.53555555555556, 236.79777777777778]
1.0411227582841431
[246.41444444444446, 236.2422222222222]
1.0430584428411518
[246.20777777777778, 236.38888888888889]
1.0415370152761456
[246.07888888888888, 237.18777777777777]
1.0374855365416056
[245.83444444444444, 237.35666666666665]
1.0357174622345182
[245.90666666666667, 238.26888888888888]
1.0320552876768543
[245.80444444444444, 239.69666666666666]
1.0254812795802102
[245.77666666666667, 240.63222222222223]
1.0213788677049809
[245.42333333333335, 240.79777777777778]
1.0192092950285625
[245.83333333333334, 240.1511111111111]
1.0236610282414778
[245.35222222222222, 240.0077777777778]
1.0222677968769531
[245.99444444444444, 240.75666666666666]
1.0217554838679903
[245.54111111111112, 240.13666666666666]
1.0225057027711073
[245.7788888888889, 240.20333333333335]
1.02321181591522
[245.68444444444444, 240.66]
1.0208777713140715
[245.9777777777778, 240.3311111111111]
1.0234953628789911
[245.9322222222222, 238.55333333333334]
1.0309318205106708
[245.12444444444444, 237.20777777777778]
1.0333743975042977
[244.81666666666666, 238.49333333333334]
1.0265136691451893
[244.36444444444444, 242.62]
1.0071900273862189
[245.67888888888888, 241.60666666666665]
1.0168547593425494
[245.3322222222222, 239.61333333333334]
1.0238671563444808
[244.92888888888888, 240.1288888888889]
1.0199892650243387
[243.4011111111111, 239.99555555555557]
1.0141900775940293
[242.7588888888889, 239.7122222222222]
1.012709684297375
[242.66555555555556, 239.33333333333334]
1.0139229340761373
[242.48666666666668, 240.01777777777778]
1.010286275090734
[243.82777777777778, 238.48]
1.0224244287897426
[245.45333333333335, 237.9477777777778]
1.0315428688834618
[245.60111111111112, 235.3411111111111]
1.0435962928515112
[247.77, 236.82777777777778]
1.0462032888409298
[250.89222222222222, 238.10777777777778]
1.0536918388964847
[251.7577777777778, 239.09444444444443]
1.0529637288844484
[251.15, 239.73444444444445]
1.0476175026997465
[249.44222222222223, 241.51444444444445]
1.0328252738506554
[246.54777777777778, 240.29777777777778]
1.0260093957497178
[246.70777777777778, 239.92222222222222]
1.0282823137127772
[251.07222222222222, 237.37666666666667]
1.05769545822626
[251.94, 236.18666666666667]
1.0666986564299423
[251.39333333333335, 234.21777777777777]
1.0733315622687338
[247.84444444444443, 232.05]
1.068064832770715
[236.6288888888889, 231.4322222222222]
1.0224543782917006
[236.88, 231.50555555555556]
1.0232151856206955
[238.81444444444443, 231.22333333333333]
1.0328302122527042
[239.7, 230.86666666666667]
1.0382616228703436
[238.56, 231.4488888888889]
1.0307243259850987
[233.58666666666667, 232.37444444444444]
1.0052166761500836
[224.33444444444444, 232.07111111111112]
0.9666625172360962
[213.0988888888889, 232.29666666666665]
0.9173566368676072
[206.10555555555555, 232.4777777777778]
0.886560244706782
[194.27666666666667, 232.54]
0.835454832143574
[184.12666666666667, 232.41444444444446]
0.7922341793634934
[187.3011111111111, 231.64888888888888]
0.8085560522630034
[200.32222222222222, 230.87666666666667]
0.8676590194861133
[203.72666666666666, 231.20777777777778]
0.8811410611907519
[208.06, 230.78]
0.9015512609411561
[217.34777777777776, 230.49666666666667]
0.9429541039398014
[225.07444444444445, 229.63]
0.980161322320448
[232.23111111111112, 228.83]
1.0148630472888656
[232.69555555555556, 228.11666666666667]
1.0200725749494655
[235.0, 228.05666666666667]
1.0304456494730843
[235.00333333333333, 227.72333333333333]
1.0319686168889148
[234.63888888888889, 227.36444444444444]
1.0319946439392458
[238.89, 227.28444444444443]
1.051061811924363
[242.83555555555554, 227.23888888888888]
1.068635552404469
[240.0222222222222, 227.15555555555557]
1.056642535707298
[238.0388888888889, 227.29777777777778]
1.0472556802627977
[234.45, 227.36222222222221]
1.0311739466147998
[233.5677777777778, 227.3788888888889]
1.0272183970954012
[221.9088888888889, 226.95888888888888]
0.9777492742200008
[73.47111111111111, 227.42666666666668]
0.32305407359637295
[64.53666666666666, 47.035555555555554]
1.3720825852782763
[61.062222222222225, 20.45]
2.985927737027982
[59.385555555555555, 20.914444444444445]
2.839451734580035
[58.82222222222222, 18.49222222222222]
3.1809169020008414
[58.50333333333333, 16.104444444444443]
3.632744583965779
[56.18, 16.005555555555556]
3.5100312391530717
[51.44111111111111, 17.446666666666665]
2.9484779009043436
[48.58, 24.70888888888889]
1.966094073208022
[47.096666666666664, 21.526666666666667]
2.187829049241251
[46.69222222222222, 19.036666666666665]
2.45275199906613
[50.03888888888889, 19.41888888888889]
2.5768152428906563
[50.65555555555556, 19.952222222222222]
2.5388427911121014
[50.836666666666666, 23.717777777777776]
2.1433992317061747
[48.73222222222222, 26.563333333333333]
1.834567281549337
[48.07666666666667, 25.914444444444445]
1.8552073060926981
[47.43222222222222, 25.003333333333334]
1.8970359507621206
[48.99444444444445, 33.44888888888889]
1.4647555142173798
[50.181111111111115, 36.367777777777775]
1.3798234090006418
[51.413333333333334, 36.154444444444444]
1.4220473892867023
[52.02444444444444, 69.83666666666667]
0.7449445531637311
[50.736666666666665, 164.61111111111111]
0.30822139723253456
[52.55222222222222, 158.61666666666667]
0.3313158908619663
[53.35444444444445, 91.58888888888889]
0.5825427635569574
[53.3, 76.75222222222222]
0.694442433805753
[54.29, 46.63777777777778]
1.164077762424358
[54.28333333333333, 40.05777777777778]
1.3551259292133584
[54.82666666666667, 31.573333333333334]
1.7364864864864864
[57.37, 25.20111111111111]
2.276486927384154
[58.04333333333334, 22.724444444444444]
2.554224525718756
[58.458888888888886, 22.482222222222223]
2.600227340120589
[58.943333333333335, 22.973333333333333]
2.565728380731283
[59.19777777777778, 23.3]
2.5406771578445397
[59.15888888888889, 23.18777777777778]
2.5512961809382335
[59.483333333333334, 23.52]
2.5290532879818595
[59.007777777777775, 24.11]
2.447439974192359
[59.41444444444444, 23.858888888888888]
2.4902435616821124
[60.17333333333333, 23.473333333333333]
2.5634762851462654
[60.602222222222224, 24.005555555555556]
2.5245082156908123
[61.45444444444445, 23.77111111111111]
2.5852575488454708
[61.63666666666666, 24.176666666666666]
2.5494278229698057
[62.242222222222225, 24.14666666666667]
2.5776734769004235
[63.38444444444445, 24.025555555555556]
2.6382093141562226
[63.11, 24.25777777777778]
2.6016397947966285
[62.486666666666665, 24.522222222222222]
2.548164929768917
[62.14111111111111, 26.015555555555554]
2.3886136499530197
[61.63, 26.563333333333333]
2.3201154473585146
[60.76777777777778, 26.86777777777778]
2.261734419585625
[58.656666666666666, 36.24666666666667]
1.6182637483906566
[57.306666666666665, 41.99]
1.3647693895371913
[56.56444444444445, 66.8711111111111]
0.8458726571846339
[56.565555555555555, 115.79444444444445]
0.48849973612243913
[56.10777777777778, 141.80666666666667]
0.3956638929371758
[56.025555555555556, 155.8388888888889]
0.35950946490321195
[55.67, 167.90666666666667]
0.33155324386563967
[55.32, 161.44222222222223]
0.342661289212515
[55.68888888888889, 154.44444444444446]
0.3605755395683453
[55.79, 129.12444444444444]
0.43206381440815067
[55.65111111111111, 96.22666666666667]
0.5783335642695487
[54.98222222222222, 86.11777777777777]
0.6384537971253839
[54.724444444444444, 101.32777777777778]
0.540073468940183
[54.083333333333336, 109.68666666666667]
0.4930711724305598
[52.38, 61.66777777777778]
0.8493901010792598
[51.403333333333336, 48.13777777777778]
1.0678376881174407
[50.55777777777778, 40.51]
1.2480320359856278
[49.27, 33.02111111111111]
1.492075776439315
[49.13111111111111, 37.28666666666667]
1.317658978485011
[49.37888888888889, 48.95444444444445]
1.0086701922422205
[49.516666666666666, 88.07777777777778]
0.5621925066229342
[51.032222222222224, 203.29333333333332]
0.25102752454034677
[53.184444444444445, 236.26444444444445]
0.22510557849490684
[57.093333333333334, 238.82777777777778]
0.2390565028263044
[57.437777777777775, 238.90666666666667]
0.2404193176321762
[56.473333333333336, 231.61]
0.2438294259027388
[54.73777777777778, 127.75888888888889]
0.42844594418305315
[56.37555555555556, 204.8311111111111]
0.27522945733070064
[62.385555555555555, 238.88]
0.26115855473692046
[69.87555555555555, 239.11111111111111]
0.29223048327137546
[82.32333333333334, 237.17222222222222]
0.3471036049752876
[248.18666666666667, 175.4177777777778]
1.4148318933846815
[254.21555555555557, 229.51222222222222]
1.1076340645136304
[253.98333333333332, 229.6511111111111]
1.105952991494344
[253.64333333333335, 230.17222222222222]
1.1019719533682508
[253.37444444444444, 229.99666666666667]
1.1016439851785291
[253.12222222222223, 228.32222222222222]
1.1086184242542216
[253.05, 227.62333333333333]
1.1117050097383103
[253.11, 227.55555555555554]
1.1122998046875001
[252.89222222222222, 227.4322222222222]
1.1119454391784611
[252.78222222222223, 227.74555555555557]
1.1099326246151895
[252.88444444444445, 228.6288888888889]
1.1060913853600691
[252.78666666666666, 229.6588888888889]
1.1007049101807995
[252.80555555555554, 230.01555555555555]
1.099080255441661
[252.93555555555557, 230.45333333333335]
1.0975565069814086
[252.8411111111111, 231.1211111111111]
1.0939767029311231
[252.92777777777778, 231.77]
1.0912878188625696
[252.9322222222222, 232.33444444444444]
1.0886557213977934
[252.9477777777778, 232.27444444444444]
1.0890039082120289
[253.14444444444445, 232.49]
1.088840141272504
[253.19555555555556, 233.02555555555554]
1.0865570299871736
[253.29444444444445, 233.43]
1.0850980784151327
[253.38888888888889, 233.8411111111111]
1.0835942734145219
[253.26111111111112, 233.94]
1.0825900278323977
[253.1888888888889, 233.76333333333332]
1.0830992409226807
[252.92111111111112, 234.73111111111112]
1.0774929233449146
[252.76444444444445, 235.10888888888888]
1.0750952277431733
[252.43, 235.00666666666666]
1.0741397407165754
[251.90777777777777, 234.85555555555555]
1.0726072763400671
[251.85111111111112, 234.48444444444445]
1.0740631930097235
[252.02555555555554, 234.7122222222222]
1.0737640893576532
[251.96, 234.42333333333335]
1.0748076841042558
[252.06222222222223, 234.62333333333333]
1.0743271721577374
[252.35555555555555, 235.0611111111111]
1.073574247831533
[252.0, 237.45555555555555]
1.0612512283000328
[252.03, 237.38888888888889]
1.0616756377252516
[252.08444444444444, 237.7788888888889]
1.0601632702650923
[251.85444444444445, 237.8711111111111]
1.0587853365968498
[251.88444444444445, 238.23555555555555]
1.057291569501707
[251.9411111111111, 238.50555555555556]
1.0563322540821318
[251.91222222222223, 238.9188888888889]
1.0543838680723816
[251.80666666666667, 238.86111111111111]
1.0541969996511222
[251.53333333333333, 238.99333333333334]
1.052470082847499
[251.48333333333332, 238.96777777777777]
1.0523734022718079
[251.30777777777777, 239.15222222222224]
1.0508276922648057
[251.09, 239.11666666666667]
1.050073186031923
[251.0311111111111, 239.41666666666666]
1.048511428239935
[250.88444444444445, 239.4488888888889]
1.047757814240107
[250.88444444444445, 239.57]
1.0472281355947926
[250.70777777777778, 239.30444444444444]
1.0476519914195772
[250.5811111111111, 239.31555555555556]
1.0470740630687516
[250.6588888888889, 239.20111111111112]
1.0479001862681798
[250.46444444444444, 239.19666666666666]
1.0471067508372933
[250.5088888888889, 239.2288888888889]
1.0471514960103294
[250.50444444444443, 239.04222222222222]
1.04795061774303
[250.43555555555557, 239.29]
1.0465776069018997
[250.3011111111111, 239.10777777777778]
1.0468129202544645
[250.32666666666665, 238.75666666666666]
1.0484593798427966
[250.13, 239.18333333333334]
1.0457668455159919
[249.85, 239.95777777777778]
1.04122484511164
[250.04666666666665, 238.43333333333334]
1.0487068362924645
[250.22666666666666, 236.64333333333335]
1.0574000253546123
[249.52444444444444, 235.83444444444444]
1.0580491964702168
[248.8322222222222, 235.63444444444445]
1.0560095439734805
[248.70444444444445, 235.83777777777777]
1.0545572757168298
[248.81444444444443, 235.34222222222223]
1.0572452409729565
[248.62, 235.53444444444443]
1.055556865945533
[248.5311111111111, 234.07333333333332]
1.061766018246893
[248.51666666666668, 234.83777777777777]
1.0582482470168533
[248.3311111111111, 236.2422222222222]
1.0511715847200143
[248.2588888888889, 235.64555555555555]
1.0535267185650765
[248.36333333333334, 236.30777777777777]
1.0510163299275428
[249.1, 236.49555555555557]
1.0532967497627392
[248.95666666666668, 235.08]
1.0590295502240372
[248.61777777777777, 236.09666666666666]
1.053033832657998
[249.17666666666668, 236.18555555555557]
1.0550038340852532
[248.92222222222222, 235.81222222222223]
1.055595082716474
[248.9111111111111, 236.0911111111111]
1.0543010702083
[248.77666666666667, 236.76888888888888]
1.0507151840519589
[248.18666666666667, 236.2788888888889]
1.0503971295691061
[248.12222222222223, 236.50666666666666]
1.0491130153718946
[248.45111111111112, 235.79111111111112]
1.0536915914274405
[248.49555555555557, 235.48111111111112]
1.055267466605012
[248.83, 236.01333333333332]
1.0543048415343768
[248.95444444444445, 235.74333333333334]
1.0560402320791444
[248.85777777777778, 235.86666666666667]
1.0550781986056152
[248.89, 235.48888888888888]
1.0569076153628385
[248.77555555555554, 235.88888888888889]
1.0546302402260952
[248.57777777777778, 236.04111111111112]
1.053112216798392
[248.67, 235.9311111111111]
1.0539941037402631
[248.59, 235.7811111111111]
1.0543253394155596
[248.5011111111111, 235.81]
1.053819223574535
[248.49333333333334, 235.73333333333332]
1.0541289592760181
[248.79222222222222, 236.7]
1.0510867014035583
[248.77777777777777, 236.70666666666668]
1.0509960757806192
[248.77333333333334, 236.62777777777777]
1.051327682952598
[248.76444444444445, 236.58333333333334]
1.0514876130092756
[248.74777777777777, 236.59777777777776]
1.0513529759836198
[248.59444444444443, 236.60111111111112]
1.0506900972569866
[248.57222222222222, 236.60111111111112]
1.0505961745272163
[248.61222222222221, 236.50666666666666]
1.0511848385763145
[248.58777777777777, 236.61222222222221]
1.0506125822372283
[248.64777777777778, 236.72666666666666]
1.0503581251701446
[248.55, 236.45555555555555]
1.0511489121751798
[248.38111111111112, 236.65666666666667]
1.049541999427206
[248.40555555555557, 236.4922222222222]
1.05037515915487
[248.39777777777778, 236.5988888888889]
1.0498687417523327
[248.38, 236.55555555555554]
1.0499859088774073
[248.3, 236.51888888888888]
1.0498104450196601
[248.3388888888889, 236.4388888888889]
1.0503301299372636
[248.26444444444445, 236.54444444444445]
1.0495467142655832
[248.24, 236.42222222222222]
1.0499859009305386
[248.39888888888888, 236.4622222222222]
1.0504802270505977
[248.18555555555557, 236.42]
1.0497654832736467
[248.48222222222222, 237.20333333333335]
1.0475494535864682
[248.61888888888888, 237.1911111111111]
1.0481796207465148
[248.53, 237.08]
1.0482959338619875
[248.38444444444445, 236.97666666666666]
1.0481388228564463
[248.50222222222223, 237.11]
1.0480461482949779
[248.32444444444445, 237.18777777777777]
1.0469529533562252
[248.54666666666665, 237.3411111111111]
1.047212872237333
[248.29888888888888, 237.24555555555557]
1.0465902651261467
[248.3177777777778, 237.09]
1.0473566062582893
[248.32333333333332, 237.18444444444444]
1.0469629823953228
[248.2888888888889, 237.26444444444445]
1.0464647978345774
[248.20333333333335, 237.13444444444445]
1.0466776933853745
[248.23333333333332, 237.1811111111111]
1.0465982395075493
[248.25666666666666, 237.20222222222222]
1.0466034607133154
[248.03666666666666, 237.23666666666668]
1.0455241601213976
[248.0288888888889, 237.11]
1.046049887768921
[248.02, 237.15555555555557]
1.0458114692653673
[248.05666666666667, 237.0611111111111]
1.0463827892479671
[247.9111111111111, 237.12333333333333]
1.0454943747042091
[247.81444444444443, 237.0611111111111]
1.045361018021607
[247.9622222222222, 237.08666666666667]
1.0458716456241974
[247.7877777777778, 237.13333333333333]
1.0449301846125012
[247.83666666666667, 237.08555555555554]
1.045346968042479
[247.90222222222224, 237.32222222222222]
1.044580738798633
[247.87222222222223, 237.14666666666668]
1.0452275197721055
[248.10888888888888, 237.87666666666667]
1.0430148209389554
[248.2811111111111, 237.96777777777777]
1.043339200918892
[248.32555555555555, 238.06666666666666]
1.0430925044338655
[248.12555555555556, 237.84222222222223]
1.0432359453979763
[248.16222222222223, 237.92555555555555]
1.043024662242625
[247.94555555555556, 237.8188888888889]
1.0425814228381074
[248.10333333333332, 237.95222222222222]
1.0426602912816298
[247.9711111111111, 237.94333333333333]
1.042143554254281
[247.88555555555556, 237.79666666666665]
1.0424265362097405
[247.93666666666667, 237.76777777777778]
1.0427681538008609
[247.9111111111111, 237.95777777777778]
1.0418281487845649
[247.90333333333334, 237.73444444444445]
1.0427741504292838
[247.8088888888889, 237.7188888888889]
1.042445091541363
[247.92333333333335, 237.74333333333334]
1.042819286906047
[247.86333333333334, 237.9177777777778]
1.0418024901226381
[247.71555555555557, 237.7277777777778]
1.0420135075132622
[247.7711111111111, 237.72222222222223]
1.0422715587754148
[247.91222222222223, 237.8322222222222]
1.0423828188872641
[247.91333333333333, 237.9388888888889]
1.041920194260898
[247.89666666666668, 237.75333333333333]
1.042663264447747
[247.80555555555554, 237.73333333333332]
1.0423677322864087
[247.76444444444445, 237.6911111111111]
1.0423799328727295
[247.73888888888888, 237.96777777777777]
1.0410606478001223
[247.7511111111111, 237.76333333333332]
1.0420072247379515
[247.8311111111111, 237.82]
1.0420953288668369
[247.61, 237.89666666666668]
1.0408300522635878
[247.76222222222222, 237.89]
1.0414991055623282
[247.7188888888889, 237.8022222222222]
1.0417013204250032
[247.54888888888888, 237.74555555555557]
1.0412345598235273
[247.45888888888888, 237.6888888888889]
1.0411041510845176
[247.68777777777777, 237.91555555555556]
1.0410743307616148
[247.65333333333334, 237.76333333333332]
1.0415959848028151
[247.4922222222222, 237.7722222222222]
1.0408794598004627
[247.48333333333332, 237.83]
1.0405892163870551
[247.44444444444446, 237.79111111111112]
1.040595854438069
[247.38222222222223, 237.72666666666666]
1.0406162072221132
[247.44666666666666, 237.84222222222223]
1.0403815788244306
[247.43333333333334, 237.7711111111111]
1.040636653364113
[247.85888888888888, 238.7588888888889]
1.0381137642344904
[247.83555555555554, 238.97333333333333]
1.0370845654559318
[247.89222222222222, 238.71666666666667]
1.0384370127301077
[247.7711111111111, 238.8111111111111]
1.0375191922951659
[247.73111111111112, 238.7111111111111]
1.0377862595419847
[247.84555555555556, 238.80777777777777]
1.0378454079757313
[247.81222222222223, 238.75666666666666]
1.0379279694342451
[247.7588888888889, 238.69555555555556]
1.0379702643069275
[247.75333333333333, 238.59666666666666]
1.03837717766384
[247.77555555555554, 238.55666666666667]
1.038644440407823
[247.7577777777778, 238.69555555555556]
1.0379656093768912
[247.7277777777778, 238.65444444444444]
1.0380187067307918
[247.81666666666666, 238.70888888888888]
1.0381543302395293
[247.7211111111111, 238.54444444444445]
1.0384694210256649
[247.6822222222222, 238.63]
1.037934133270009
[247.68, 238.64777777777778]
1.0378475018972637
[247.6888888888889, 238.60111111111112]
1.0380877429088995
[247.67666666666668, 238.58666666666667]
1.0380993629149435
[247.61777777777777, 238.67222222222222]
1.0374805055748237
[247.45888888888888, 238.7422222222222]
1.0365107880186906
[247.60444444444445, 238.62777777777777]
1.0376178613833726
[247.4477777777778, 238.59666666666666]
1.0370965413505824
[247.54333333333332, 238.65555555555557]
1.0372410261185343
[247.48444444444445, 238.60444444444445]
1.0372164065119398
[247.3388888888889, 238.63777777777779]
1.0364615828731598
[247.47555555555556, 238.60888888888888]
1.0371598338517705
^C[247.47222222222223, 238.54666666666665]
1.0374163918543775
Traceback (most recent call last):
  File "camera_detect_color.py", line 171, in <module>
    server.serve_forever()
  File "/usr/lib/python3.7/socketserver.py", line 232, in serve_forever
    ready = selector.select(poll_interval)
  File "/usr/lib/python3.7/selectors.py", line 415, in select
    fd_event_list = self._selector.poll(timeout)
KeyboardInterrupt
^[[A^[[Api@raspberrypi:~/nano python3 camera_detect_c^Cor.py
pi@raspberrypi:~/final $ nano camera_detect_color.py
pi@raspberrypi:~/final $ ls
camera_detect_color.py  __pycache__  send_command.py
pi@raspberrypi:~/final $ cp send_command.py trigger_led.py
pi@raspberrypi:~/final $ nano trigger_led.py

  GNU nano 3.2                     trigger_led.py

            ser.write(b'v')
            time.sleep(0.05)
        elif char == curses.KEY_RIGHT:
            ser.write(b'a')
            time.sleep(0.05)
        elif char == curses.KEY_UP:
            ser.write(b'c')
            time.sleep(0.05)
finally:
    # shut down
    curses.nocbreak(); screen.keypad(0); curses.echo()
    curses.endwin()








^G Get Help  ^O Write Out ^W Where Is  ^K Cut Text  ^J Justify   ^C Cur Pos
^X Exit      ^R Read File ^\ Replace   ^U Uncut Text^T To Spell  ^_ Go To Line
