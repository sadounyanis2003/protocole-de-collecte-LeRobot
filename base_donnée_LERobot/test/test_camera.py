import pyrealsense2 as rs
import numpy as np
import cv2

SERIAL_1 = "234322303360"  # Remplace par le numéro de ta première caméra
SERIAL_2 = "242422302403"  # Remplace par le numéro de ta deuxième caméra

# Pipeline pour la première caméra
pipe1 = rs.pipeline()
cfg1 = rs.config()
cfg1.enable_device(SERIAL_1)
cfg1.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipe1.start(cfg1)

# Pipeline pour la deuxième caméra
pipe2 = rs.pipeline()
cfg2 = rs.config()
cfg2.enable_device(SERIAL_2)
cfg2.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipe2.start(cfg2)

# Capture une image de chaque caméra
frames1 = pipe1.wait_for_frames()
color_frame1 = frames1.get_color_frame()
img1 = np.asanyarray(color_frame1.get_data())
cv2.imwrite("cam1.png", img1)

frames2 = pipe2.wait_for_frames()
color_frame2 = frames2.get_color_frame()
img2 = np.asanyarray(color_frame2.get_data())
cv2.imwrite("cam2.png", img2)

pipe1.stop()
pipe2.stop()
print("Images sauvegardées pour les deux caméras.")