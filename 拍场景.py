import cosysairsim as airsim
import time
import math
import os
import json
import cv2
import numpy as np

# ================= 🎥 导演参数配置 (基于你的场景数据) =================
OUTPUT_DIR = "3dgs_dataset_full_scene"
# 扫描范围: 基于 PlayerStart 中心，覆盖 500m x 430m
X_RANGE = 250 
Y_RANGE = 215 
STEP_SIZE = 35        # 每隔35米拍一处，确保 3DGS 所需的高重叠度

# 高度与角度: 考虑到 32m 落差，分两个高度层拍摄
Z_LAYERS = [-15.0, -45.0]  # AirSim 中负值代表向上
PITCH_DEG = -45            # 45度斜下俯视，最利于捕捉地形特征

# 相机内参 (需与 settings.json 中的 90度 FOV 匹配)
WIDTH, HEIGHT = 1920, 1080
FOV = 90
# =================================================================

def to_quaternion(pitch, roll, yaw):
    """手动实现欧拉角转四元数，修复 AttributeError"""
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

def main():
    # 1. 初始化目录
    img_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(img_dir, exist_ok=True)
    
    # 2. 连接仿真器 [cite: 419, 433]
    client = airsim.VehicleClient()
    client.confirmConnection()
    print("✅ 已连接到 ASVSim！开始全场景 3DGS 采集...")

    # 计算焦距用于 transforms.json
    focal_length = WIDTH / (2 * math.tan(math.radians(FOV / 2)))
    
    frames = []
    count = 0
    pitch_rad = math.radians(PITCH_DEG)

    # 3. 开始网格扫描
    for z in Z_LAYERS:
        print(f"✈️ 正在高度 {abs(z)} 米层级拍摄...")
        for x in range(-X_RANGE, X_RANGE, STEP_SIZE):
            for y in range(-Y_RANGE, Y_RANGE, STEP_SIZE):
                
                # 每个扫描点旋转 4 个方向，确保全方位覆盖
                for yaw_deg in [0, 90, 180, 270]:
                    yaw_rad = math.radians(yaw_deg)
                    
                    # 设定相机姿态
                    pose = airsim.Pose(
                        airsim.Vector3r(x, y, z),
                        to_quaternion(pitch_rad, 0, yaw_rad)
                    )
                    
                    # 设置相机位置 [cite: 446]
                    client.simSetVehiclePose(pose, True)
                    time.sleep(0.25) # 预留 3090 渲染高质量画面的时间

                    # 获取图像数据 [cite: 404, 405]
                    responses = client.simGetImages([
                        airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)
                    ])
                    
                    if responses:
                        response = responses[0]
                        img_1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
                        img_bgr = img_1d.reshape(response.height, response.width, 3)
                        
                        file_name = f"view_{count:04d}.jpg"
                        file_path = os.path.join(img_dir, file_name)
                        cv2.imwrite(file_path, img_bgr)

                        # 记录位姿数据 (3DGS 训练格式)
                        # 注意：此处简化了矩阵转换，正式训练建议仍通过 COLMAP 优化位姿
                        frames.append({
                            "file_path": f"images/{file_name}",
                            "transform_matrix": [
                                [math.cos(yaw_rad), -math.sin(yaw_rad), 0, x],
                                [math.sin(yaw_rad), math.cos(yaw_rad), 0, y],
                                [0, 0, 1, z],
                                [0, 0, 0, 1]
                            ]
                        })
                        
                        count += 1
                        print(f"📸 已保存: {file_name} (Total: {count})", end="\r")

    # 4. 导出为 3DGS 通用的 transforms.json
    meta_data = {
        "camera_angle_x": math.radians(FOV),
        "fl_x": focal_length,
        "fl_y": focal_length,
        "w": WIDTH,
        "h": HEIGHT,
        "frames": frames
    }
    
    with open(os.path.join(OUTPUT_DIR, "transforms.json"), "w") as f:
        json.dump(meta_data, f, indent=4)

    print(f"\n🎉 采集大功告成！共 {count} 张图片。")
    print(f"📂 请前往文件夹查看：{os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()