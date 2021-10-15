# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 15:07:04 2021

@author: egeaa
"""

import io
# # import picamera # Camera

# #### THIS IS IMPORTANT FOR LIFE STREAMING ####
import logging
import socketserver
from threading import Condition
from http import server

# #### THIS IS IMPORTANT FOR IMAGE PROCESSING ####
import numpy as np
import cv2
import time

#%%
myCam = cv2.VideoCapture(0)


def faceDetection(frame):

    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = det.detectMultiScale(gray,
                                 scaleFactor=1.1,
                                 minNeighbors=5,
                                 minSize=(50,50), # adjust to your image size, maybe smaller, maybe larger?
                                 flags=cv2.CASCADE_SCALE_IMAGE)
    # print(rects)
    
    # cv2.imwrite("test_face.jpg", im) (edited) 
    return rects
    
counter = 0
start_time = time.time()
while (int(time.time() - start_time) < 10):
    
    ret,frame = myCam.read()

    rects = faceDetection(frame)

    for (x, y, w, h) in rects:
    # x: x location
    # y: y location
    # w: width of the rectangle
    # h: height of the rectangle
    # Remember, order in images: [y, x, channel]
    
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 10)
        
    cv2.imshow('Input', frame)


    
    counter = counter + 1
    # print(counter)
    # # c = 
    #if cv2.waitKey(1):
    #     break
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    # break
        
myCam.release()
cv2.destroyAllWindows()

#%%
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
        elif '/stream.' in self.path:
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

# Open the camera and stream a low-res image (width 640, height 480 px)

# with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
#     camera.vflip = True # Flips image vertically, depends on your camera mounting
#     camera.awb_gains = (1.2, 1.5)
#     camera.awb_mode = 'off'


while (int(time.time() - start_time) < 10):
    output = StreamingOutput() 

    ret,output = myCam.read()
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    try:
        address = ('', 8000) # port 8000
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        myCam.release()
        cv2.destroyAllWindows()