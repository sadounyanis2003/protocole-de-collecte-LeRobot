import pyrealsense2 as rs

ctx = rs.context()
devices = ctx.query_devices()
for dev in devices:
    print(f"Nom caméra: {dev.get_info(rs.camera_info.name)}")
    print(f"Serial number: {dev.get_info(rs.camera_info.serial_number)}\n")
