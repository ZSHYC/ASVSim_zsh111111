import cosysairsim as airsim
import cv2
import numpy as np
import os
import time
import json
import math

# ================= 配置区域 =================
OUTPUT_DIR = "dataset_ice_auto_v1"  # 改个名，区分自动采集的数据
TRIGGER_DISTANCE = 1.0              # 每隔 1.0 米采集一次
TARGET_VESSEL = "Vessel1"
CAMERA_NAMES = ["front_center", "front_left", "front_right"]

# 🤖 自动驾驶参数
AUTO_PILOT_THRUST = 0.6    # 油门 (0.0 ~ 1.0)，0.6 是个比较稳的速度
AUTO_PILOT_RUDDER = 0.15   # 舵角 (-1.0 ~ 1.0)，0.15 会走一个大圆圈
# ===========================================

def get_vessel_pose(client):
    state = client.getVesselState(TARGET_VESSEL)
    return state.kinematics_estimated.position

def calc_distance(pos1, pos2):
    dx = pos1.x_val - pos2.x_val
    dy = pos1.y_val - pos2.y_val
    dz = pos1.z_val - pos2.z_val
    return math.sqrt(dx*dx + dy*dy + dz*dz)

def save_snapshot(client, frame_index):
    # (这部分代码和之前一样，负责拍照和存数据)
    requests = []
    for cam_name in CAMERA_NAMES:
        requests.append(airsim.ImageRequest(cam_name, airsim.ImageType.Scene, False, False))
    
    responses = client.simGetImages(requests)
    snapshot_records = []
    
    for i, response in enumerate(responses):
        if response.pixels_as_float: continue
        cam_name = CAMERA_NAMES[i]
        
        img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
        img_rgb = img1d.reshape(response.height, response.width, -1)
        if img_rgb.shape[2] == 4: img_rgb = img_rgb[:, :, :3]
            
        file_name = f"frame_{frame_index:05d}_{cam_name}.jpg"
        save_path = os.path.join(OUTPUT_DIR, "images", file_name)
        cv2.imwrite(save_path, img_rgb)
        
        cam_info = client.simGetCameraInfo(cam_name, vehicle_name=TARGET_VESSEL)
        pose = cam_info.pose
        snapshot_records.append({
            "file_path": f"images/{file_name}",
            "camera_name": cam_name,
            "timestamp": response.time_stamp,
            "transform": {
                "position": [pose.position.x_val, pose.position.y_val, pose.position.z_val],
                "orientation": [pose.orientation.w_val, pose.orientation.x_val, pose.orientation.y_val, pose.orientation.z_val]
            }
        })
    return snapshot_records

def main():
    # --- 初始化 ---
    if not os.path.exists(os.path.join(OUTPUT_DIR, "images")):
        os.makedirs(os.path.join(OUTPUT_DIR, "images"))
    
    try:
        client = airsim.VesselClient()
        client.confirmConnection()
        print(f"✅ 连接成功! 准备接管 {TARGET_VESSEL}...")
        
        # 🔥 关键步骤：开启 API 控制权限 🔥
        # 这就是之前没动的原因，我们现在强制接管控制权
        client.enableApiControl(True, TARGET_VESSEL)
        print("🤖 自动驾驶模式：已启动 (API Control Enabled)")
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    print(f"🌊 正在起航... 油门: {AUTO_PILOT_THRUST}, 转向: {AUTO_PILOT_RUDDER}")
    print("⌨️  按 Ctrl+C 紧急停车并保存数据")

    last_pos = get_vessel_pose(client)
    frame_count = 0
    all_data_log = []

    try:
        while True:
            # 1. 发送驾驶指令 (每 0.1秒发一次，保持动力)
            # VesselControls(thrust, angle)
            # angle > 0 是右转，angle < 0 是左转
            client.setVesselControls(TARGET_VESSEL, airsim.VesselControls(thrust=AUTO_PILOT_THRUST, angle=AUTO_PILOT_RUDDER))
            
            # 2. 检查位置并拍照
            current_pos = get_vessel_pose(client)
            dist = calc_distance(last_pos, current_pos)
            
            if dist >= TRIGGER_DISTANCE:
                print(f"📸 [第 {frame_count} 组] 移动 {dist:.2f}m -> 咔嚓!", end="\r")
                records = save_snapshot(client, frame_count)
                all_data_log.extend(records)
                
                with open(os.path.join(OUTPUT_DIR, "transforms_log.json"), "w") as f:
                    json.dump(all_data_log, f, indent=4)
                
                last_pos = current_pos
                frame_count += 1
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 正在停车...")
        # 停车指令：油门归零
        client.setVesselControls(TARGET_VESSEL, airsim.VesselControls(thrust=0, angle=0))
        client.enableApiControl(False, TARGET_VESSEL) # 交还控制权
        print(f"💾 采集完成！共 {frame_count} 组数据。")

if __name__ == "__main__":
    main()