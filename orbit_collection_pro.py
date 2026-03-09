import cosysairsim as airsim
import time
import math
import os
import cv2
import numpy as np

# ================= 🎥 导演参数 (已修正) =================
OUTPUT_DIR = "dataset_ice_final_v2"

# 1. 目标中心 (AirSim NED坐标: Z是负的表示向上)
# 还是维持之前的设定，中心在水面上 28米处 (即 AirSim Z = -28)
TARGET_CENTER = airsim.Vector3r(0, 0, -28.0) 

# 2. 拍摄半径
RADIUS = 120.0       

# 3. 扫描层数
# 我们加大俯视角，确保一定能拍到头顶
HEIGHT_LAYERS = 3    
MIN_PITCH = -15.0    # 底层: 稍微俯视
MAX_PITCH = -55.0    # 顶层: 也就是要在天上俯瞰

SPEED_DEG = 3.0      # 采样间隔
# =======================================================

def to_quaternion(pitch, roll, yaw):
    t0 = math.cos(yaw * 0.5)
    t1 = math.sin(yaw * 0.5)
    t2 = math.cos(roll * 0.5)
    t3 = math.sin(roll * 0.5)
    t4 = math.cos(pitch * 0.5)
    t5 = math.sin(pitch * 0.5)
    q = airsim.Quaternionr()
    q.w_val = t0 * t2 * t4 + t1 * t3 * t5
    q.x_val = t0 * t3 * t4 - t1 * t2 * t5
    q.y_val = t0 * t2 * t5 + t1 * t3 * t4
    q.z_val = t1 * t2 * t4 - t0 * t3 * t5
    return q

def save_image(client, filename):
    responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
    if not responses: return False
    response = responses[0]
    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    try:
        img_rgb = img1d.reshape(response.height, response.width, -1)
    except ValueError: return False
    if img_rgb.shape[2] == 4: img_rgb = img_rgb[:, :, :3]
    
    filepath = os.path.join(OUTPUT_DIR, "images", filename)
    cv2.imwrite(filepath, img_rgb)
    return True

def main():
    if not os.path.exists(os.path.join(OUTPUT_DIR, "images")):
        os.makedirs(os.path.join(OUTPUT_DIR, "images"))
        
    client = airsim.VehicleClient()
    client.confirmConnection()
    print(f"✅ 连接成功，准备起飞...")

    count = 0
    pitch_steps = np.linspace(MIN_PITCH, MAX_PITCH, HEIGHT_LAYERS)
    
    for layer_idx, pitch_deg in enumerate(pitch_steps):
        pitch_rad = math.radians(pitch_deg)
        
        # 🔥🔥🔥 核心修正点 🔥🔥🔥
        # 之前的代码是: cam_z = Center - R * sin(pitch)
        # 因为 pitch 是负的，sin也是负的，减负=加正，导致 Z 变大 (下潜)
        # 现在的代码是: cam_z = Center + R * sin(pitch)
        # 加上一个负数 = Z 变小 (升空)
        cam_z = TARGET_CENTER.z_val + RADIUS * math.sin(pitch_rad)
        
        radius_xy = RADIUS * math.cos(pitch_rad)
        
        print(f"✈️ Layer {layer_idx}: 高度 Z = {cam_z:.2f} (负数才是天空!)")

        for yaw_deg in np.arange(0, 360, SPEED_DEG):
            yaw_rad = math.radians(yaw_deg)
            
            cam_x = TARGET_CENTER.x_val - radius_xy * math.cos(yaw_rad)
            cam_y = TARGET_CENTER.y_val - radius_xy * math.sin(yaw_rad)
            
            # 始终看向圆心
            look_yaw = yaw_rad 
            
            pose = airsim.Pose(
                airsim.Vector3r(cam_x, cam_y, cam_z),
                to_quaternion(pitch_rad, 0, look_yaw)
            )
            
            client.simSetVehiclePose(pose, True)
            time.sleep(0.02)
            
            fname = f"img_L{layer_idx}_{int(yaw_deg):03d}.jpg"
            save_image(client, fname)
            print(f"📸 Saved {fname} | Z: {cam_z:.1f}m", end="\r")
            count += 1

    print(f"\n✅ 采集完成！共 {count} 张。")

if __name__ == "__main__":
    main()