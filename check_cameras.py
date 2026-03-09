import cosysairsim as airsim
import cv2
import numpy as np
import os
import time

# 1. 连接到模拟器
client = airsim.VesselClient()
client.confirmConnection()

print("✅ 连接成功！开始验证相机阵列...")

# 2. 定义我们在 settings.json 里配置好的相机名字
camera_names = ["front_center", "front_left", "front_right"]
image_types = [
    airsim.ImageType.Scene,  # 普通 RGB 图 (Type 0)
]

# 3. 创建保存目录
output_dir = "camera_test_output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 4. 抓取图片
print("📸 正在从三个角度拍照...")
for cam_name in camera_names:
    # 请求图片数据
    responses = client.simGetImages([
        airsim.ImageRequest(cam_name, airsim.ImageType.Scene, False, False)
    ])
    
    response = responses[0]
    
    # 检查是否有数据
    if response.pixels_as_float:
        print(f"❌ 错误：{cam_name} 返回了浮点数据（可能配置成了深度图？）")
        continue
        
    # 将二进制数据转为图片
    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    
    # 注意：如果分辨率不对，这里 reshape 会报错
    # 我们配置的是 1280x720，即 height=720, width=1280
    # AirSim 返回的 image_data_uint8 是 BGRA 格式 (4通道) 或 BGR (3通道)
    try:
        img_rgb = img1d.reshape(response.height, response.width, 3)
    except ValueError:
        # 有时候 AirSim 返回的是 4 通道 (BGRA)
        img_rgb = img1d.reshape(response.height, response.width, 4)
    
    # 保存图片
    filename = os.path.join(output_dir, f"test_{cam_name}.png")
    cv2.imwrite(filename, img_rgb)
    print(f"✅ 已保存: {filename} (分辨率: {response.width}x{response.height})")

print(f"\n🎉 验证完成！请打开文件夹 '{output_dir}' 查看图片。")
print("预期结果：")
print("1. front_center: 正对着前方水道")
print("2. front_left:   应该能看到左边的岸壁或船只")
print("3. front_right:  应该能看到右边的水面")