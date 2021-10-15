import io
import picamera # Camera

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

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<img src="stream.mjpg" width="640" height="480" style="width:100%;height:100%;" />
</body>
</html>
"""

def faceDetection(frame):

    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = det.detectMultiScale(gray, scaleFactor=1.1,minNeighbors=5,minSize=(50,50), flags=cv2.CASCADE_SCALE_IMAGE)
    # print(rects)

    # cv2.imwrite("test_face.jpg", im) (edited)
    return rects

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
                        face_det_rects = faceDetection(frame)
                        for (x,y,w,h) in face_det_rects:
                                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0),2)
                        if len(face_det_rects)>0:
                                ser.write(b'o')
                        else:
                                ser.write(b'x')

                       
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
    camera.vflip = True # Flips image vertically, depends on your camera mounting
    camera.awb_gains = (1.2, 1.5)
    camera.awb_mode = 'off'
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000) # port 8000
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
