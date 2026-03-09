import cosysairsim as airsim
import time
import math
import os

# ================= 配置区域 =================
TARGET_SHIP = "Vessel1"      # 船只名称
CAMERA_NAME = "0"            # <--- 改成这个！"0" 代表默认主相机
OUTPUT_FOLDER = "dataset_v1" # 数据保存的文件夹名
TOTAL_IMAGES = 50            # 咱们先拍 50 张试试水
INTERVAL = 0.5               # 每隔 0.5 秒拍一张
THROTTLE = 0.3    # <--- 改成 0.3 (30% 动力)，船会更平稳               # 油门 (0.0 - 1.0)
STEERING_ANGLE = 0.8         # 舵角 (0.0=左, 0.5=直, 1.0=右)
# ===========================================

# --- 辅助函数：欧拉角转四元数 (用于设置上帝视角) ---
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

# --- 1. 初始化环境 ---
print(f"🚀 初始化采集任务: 目标 [{TARGET_SHIP}]")

# 创建输出目录
image_dir = os.path.join(OUTPUT_FOLDER, "images")
if not os.path.exists(image_dir):
    os.makedirs(image_dir)
    print(f"📂 创建目录: {image_dir}")

# 打开日志文件 (用于记录位姿)
log_path = os.path.join(OUTPUT_FOLDER, "transforms.txt")
log_file = open(log_path, "w")
log_file.write("ImageID, X, Y, Z, QW, QX, QY, QZ\n") # 写表头

# 连接 AirSim
client = airsim.VesselClient()
client.confirmConnection()
client.enableApiControl(True, TARGET_SHIP)

# --- 2. 调整上帝视角 (方便你看着它跑) ---
# 把视口摄像机挂在空中，看着船
print("📷 调整上帝视角观测...")
cam_pose = airsim.Pose(airsim.Vector3r(-10, 0, -10), to_quaternion(-0.6, 0, 0))
client.simSetCameraPose("0", cam_pose)

# --- 3. 启动引擎 ---
print(f"⚓ 引擎启动! 推力: {THROTTLE}, 舵角: {STEERING_ANGLE} (右转圈)")
# 让船开始画圆圈航行
controls = airsim.VesselControls(thrust=THROTTLE, angle=STEERING_ANGLE)
client.setVesselControls(TARGET_SHIP, controls)

# 等待船只加速 (物理引擎需要时间反应)
print("⏳ 等待船只加速 (3秒)...")
time.sleep(3)

# --- 4. 循环采集 ---
print("📸 开始采集数据...")
start_time = time.time()

for i in range(TOTAL_IMAGES):
    # A. 获取图像
    # request: [相机名, 图像类型(Scene=RGB), 是否像素数据(False=压缩png)]
    responses = client.simGetImages([
        airsim.ImageRequest(CAMERA_NAME, airsim.ImageType.Scene, False, True)
    ], vehicle_name=TARGET_SHIP)
    
    response = responses[0] # 我们只请求了一张图

    # B. 获取当时的位姿 (Ground Truth)
    # 注意：我们要的是“相机的位置”，不是“船中心的位置”。
    # 但 ASVSim 里获取相机相对位置比较麻烦，通常我们直接用船的位姿代替，
    # 或者后期通过外参矩阵修正。这里为了毕设简单，我们记录船只位姿。
    state = client.getVesselState(TARGET_SHIP)
    pos = state.kinematics_estimated.position
    ori = state.kinematics_estimated.orientation

    # C. 保存图像
    filename = f"{i:05d}.png" # 例如 00001.png
    filepath = os.path.join(image_dir, filename)
    
    # 将二进制数据写入文件
    if response.image_data_uint8:
        with open(filepath, "wb") as f:
            f.write(response.image_data_uint8)
    else:
        print(f"⚠️ 第 {i} 张图片为空!")

    # D. 记录数据到 txt
    # 格式: ID, x, y, z, qw, qx, qy, qz
    log_line = f"{filename}, {pos.x_val:.4f}, {pos.y_val:.4f}, {pos.z_val:.4f}, {ori.w_val:.4f}, {ori.x_val:.4f}, {ori.y_val:.4f}, {ori.z_val:.4f}\n"
    log_file.write(log_line)

    print(f"✅ [{i+1}/{TOTAL_IMAGES}] 已保存: {filename} | 速度: {state.kinematics_estimated.linear_velocity.x_val:.2f} m/s")
    
    # E. 保持这一步的节奏
    time.sleep(INTERVAL)

# --- 5. 收尾工作 ---
print("🛑 采集完成，正在停船...")
client.setVesselControls(TARGET_SHIP, airsim.VesselControls(0, 0.5)) # 停船回正
client.enableApiControl(False, TARGET_SHIP)
log_file.close()

print(f"🎉 任务结束！数据已保存在: {os.path.abspath(OUTPUT_FOLDER)}")