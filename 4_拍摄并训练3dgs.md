# 冰山3DGS数据采集记录

**项目名称**：基于 AirSim 与 UE5 的冰山三维高斯泼溅（3DGS）数据采集系统
**硬件环境**：NVIDIA RTX 3090
**软件环境**：Unreal Engine 5.4, CosysAirSim, Python 3.10
**最终产出**：高质量、无遮挡、多角度覆盖的冰山图像数据集（含位姿）

---

## 📑 目录 (Table of Contents)

1. **第一阶段：初始方案与试错 (The Failed "Vessel" Approach)**
2. **第二阶段：场景与坐标系构建 (Environment Setup)**
3. **第三阶段：光照与大气渲染调试 (Lighting & Atmosphere)**
4. **第四阶段：算法逻辑与数学推导 (Algorithm & Math)**
5. **最终配置文件解析 (Configuration)**
6. **最终脚本代码 (Final Script)**
7. **操作指南 (Operation Manual)**

---

## 1. 第一阶段：初始方案与试错 (The Failed "Vessel" Approach)

### 1.1 初始设想

* **思路**：使用 `SimMode: Vessel`（船只模式），在船体上挂载左、中、右三个相机，模拟真实的无人船在海上巡航，一边开船一边采集数据。
* **代码尝试**：编写了 `data_collection_3dgs.py`，利用 PID 或简单逻辑控制船只绕岛航行。

### 1.2 遇到的问题 (Issues)

1. **自身遮挡 (Self-Occlusion)**：

* *现象*：相机视场（FOV）中大量充斥着船头、桅杆和甲板。
* *后果*：3DGS 算法会将动态变化的船体误认为是场景的一部分，导致重建结果中出现严重的伪影（Ghosting artifacts）。

2. **视角受限 (Limited Perspective)**：

* *现象*：船只能在水面上行驶（Z=0）。
* *后果*：对于高耸的冰山（高约 76米），相机只能仰拍到底部，无法采集到冰山顶部的纹理。重建后的模型会是一个“空心”的无顶模型。

3. **物理干扰 (Physics Instability)**：

* *现象*：波浪导致船体晃动，惯性导致轨迹难以精确控制（无法画出完美的圆）。

### 1.3 决策调整

* **放弃**：第一人称视角（Ego-Centric）。
* **采用**：计算机视觉“上帝模式”（ComputerVision Mode）。移除船只实体，将摄像机作为一个自由飞行的刚体，执行精确的 **“半球形螺旋扫描” (Hemispherical Orbit Scan)**。

---

## 2. 第二阶段：场景与坐标系构建 (Environment Setup)

在这一步，我们解决了一个核心问题：**“为什么摄像机拍不到东西？”**

### 2.1 坐标系对齐问题

* **现象**：运行脚本后，得到的图像是空荡荡的海面或奇怪的远处风景，看不到冰山。
* **排查过程**：
* UE5 视口中，冰山位于 `(0,0,0)`。
* AirSim 的坐标系原点是 `PlayerStart`（玩家出生点）。
* 检查发现：`PlayerStart` 位于地图边缘 `(73400, 8180, 250)`。
* **冲突**：脚本控制相机飞往 AirSim 的 `(0,0,0)`，实际上相机飞到了距离冰山 70公里远的地方。
* **解决方案**：
* 将 UE5 中的 **`PlayerStart`** 的 Location 和 Rotation 全部归零 `(0,0,0)`。
* 将目标资产 **`wall_of_ice1`** 的 Location 归零，Z轴设为 `-1000`（使其半浮于水面）。 设置冰山的XYZ 坐标为 `(0,0,-1000)`, 并根据其原始尺寸和缩放倍数，计算出最终尺寸。

### 2.2 资产尺寸估算 (Metric Scale)

为了确定拍摄半径 `RADIUS`，我们对冰山进行了尺寸计算：

* **原始尺寸 (Approx Size)**:
  ![1769441063137](image/README_3dgs拍摄并运行/1769441063137.png)
* **缩放倍数 (Scale)**:
  ![1769441104400](image/README_3dgs拍摄并运行/1769441104400.png)
* **最终尺寸**: 长约 **138米**，高约 **76米**。
* **决策**：设定拍摄半径 `RADIUS = 120.0` 米，以确保冰山在画面中占比合适且不爆框。
  **1. 原始尺寸 (Approx Size)**
  从这张图里读取的数据：
* 长 (X): 6,133 cm
* 宽 (Y): 1,273 cm
* 高 (Z): 1,523 cm

**2. 你的缩放设定 (Scale)**
从上一张图读取的数据：

* X 缩放: 2.25倍
* Y 缩放: 6.5倍
* Z 缩放: 5.0倍

**3. 最终真实尺寸 (Real World Dimensions)**
乘一下就知道它有多大了：

* **真实长度**:  **138 米** (好家伙，这是一艘驱逐舰的长度！)
* **真实宽度**:  **83 米**
* **真实高度**:  **76 米** (相当于25层楼高！)

---

### 🧮 导出脚本所需的 3 个核心参数

根据上面的计算，这块冰山是个庞然大物。我们的脚本参数必须大幅调整，否则摄像机会直接撞在冰山上，或者只能拍到一个角落。

#### 1. 目标中心点 (Target Center)

* **底部位置**: 你设定的 `Z = -1000` (即水下 10米)。
* **顶部位置**:  (水面上 66米)。
* **中间点 (UE5坐标)**:  (水面上 28米)。
* **AirSim坐标转换 (NED)**: UE5 的 **向上 28米** = AirSim 的 **Z -28**。
* *结论*: `TARGET_CENTER = airsim.Vector3r(0, 0, -28)`

#### 2. 拍摄半径 (Radius)

* 冰山最长对角线约 160米。为了把整个冰山拍进去，且留一点余量（不爆框），半径至少要是长度的一半多一点。
* 建议半径：**120 米**。
* *结论*: `RADIUS = 120.0`

#### 3. 拍摄高度层 (Pitch Layers)

* 因为冰山很高（76米），如果只平拍，头顶肯定拍不到。
* 我们需要分三层：
* **底层**: 拍侧壁纹理。
* **中层**: 拍整体结构。
* **顶层**: 俯视拍顶部积雪。

---

## 3. 第三阶段：光照与大气渲染调试 (Lighting & Atmosphere) 尚未解决！！！

在这一步，我们解决了一个视觉问题：**“为什么编辑器里是蓝天，拍出来是黄昏？”**

### 3.1 “薛定谔的太阳”现象

* **现象**：UE5 编辑器视口显示的是清透的蓝天白云，但 AirSim 采集回来的图片是浑浊的黄色（类似沙尘暴或黄昏）。
* **原因分析**：
* AirSim 的 `TimeOfDay` 系统默认开启。
* 它读取系统默认时间（通常是 `20xx-xx-xx` 的冬天或默认时刻）。
* 在默认经纬度（西雅图），该时刻太阳角度极低。
* **物理原理**：低角度阳光穿过大气层发生**瑞利散射 (Rayleigh Scattering)**，短波（蓝光）散尽，只剩长波（红黄光），且水面反射天空颜色，导致整体画面偏黄。

### 3.2 尝试与最终方案

* *尝试 1*：在 `settings.json` 里强制设置时间为 `12:00:00`。
* *结果*：失败。因为如果是“1月1日”的 12点，太阳依然很低（由于季节原因）。
* *最终方案*：**彻底禁用 AirSim 的时间接管**。
* 配置项：`"TimeOfDay": { "Enabled": false }`
* *效果*：AirSim 不再干涉光照，完全沿用 UE5 编辑器中手动调整好的“正午阳光”设置。

---

## 4. 第四阶段：算法逻辑与数学推导 (Algorithm & Math)

这是代码开发中最关键的一步，解决了 **“潜水艇问题”**。

### 4.1 坐标轴定义的冲突

* **UE5**: Z 轴 **向上** 为正 (+)。
* **AirSim (NED)**: Z 轴 **向下** 为正 (+)。

### 4.2 Z 轴公式的演变

我们需要相机随着 `pitch`（俯视角，如 -45°）的增加而**升空**。

* **错误公式 (v1)**: `cam_z = CenterZ - R * sin(pitch)`
* *推导*: `pitch` 是负数  `sin` 是负数  `- (负数)` = `+ 正数`。
* *AirSim 含义*: Z 变大 = **向下钻入水底**。
* *后果*: 拍到了浑浊的水下画面。
* **修正公式 (v2)**: `cam_z = CenterZ + R * sin(pitch)`
* *推导*: `+ (负数)` = `负数`。
* *AirSim 含义*: Z 变小 (负值增大) = **向上飞向天空**。
* *结果*: 成功拍到俯视画面。

---

## 5. 最终配置文件解析 (`settings.json`)

请将此文件覆盖至 `Documents\AirSim\settings.json`。

```json
{
  "SettingsVersion": 2.0,
  "SimMode": "ComputerVision",,  // [关键] 纯视觉模式，移除物理属性
  "ViewMode": "SpringArmChase",
  "ClockSpeed": 1,
  
  // [关键] 禁用时间系统，解决"黄天"问题，沿用UE5蓝天设置
  "TimeOfDay": {
    "Enabled": false,
    "StartDateTime": "2024-06-01 12:00:00",
    "isStartDateTimeDst": false,
    "CelestialClockSpeed": 0,
    "UpdateInterval": 0,
    "MoveSun": false
  },

  "CameraDefaults": {
    "CaptureSettings": [
      {
        "ImageType": 0,         // RGB Scene 图像
        "Width": 1280,          // 720P 分辨率 (3090显卡训练3DGS的效率甜点)
        "Height": 720,
        "FOV_Degrees": 90,      // 90度广角，利于 COLMAP 特征匹配
        "AutoExposureSpeed": 100, // 快速自动曝光，防止明暗剧烈变化
        "MotionBlurAmount": 0,  // [绝对禁止] 关闭运动模糊，否则重建会失败
        "TargetGamma": 1.0
      }
    ]
  }
}

```

### 1. 核心模式切换

```json
  "SimMode": "ComputerVision",

```

* **含义**：仿真模式设为“计算机视觉模式”。
* **为什么要改？**
* **之前 (Vessel)**：你需要模拟水的浮力、船的惯性、阻力。那是为了跑路径规划。
* **现在 (ComputerVision)**：我们要让摄像机像“上帝”一样，指哪打哪。在这个模式下，**没有重力，没有碰撞，没有物理引擎**。
* **作用**：这让我们的 Python 脚本可以强制把摄像机瞬移到空中任意位置（比如冰山头顶），而不会掉下来，也不会被弹开。

### 2. 视角设置

```json
  "ViewMode": "SpringArmChase",

```

* **含义**：视角模式为“弹簧臂跟随”。
* **解析**：在 `ComputerVision` 模式下，这一行其实权级不高。因为此时没有“载具”可供跟随。AirSim 会默认生成一个自由摄像机。
* **结论**：这就好比你买了一辆车，配置单上写着“送马鞍”。虽然用不上，但放着也没坏处，不用删。

```json
  "ClockSpeed": 1,

```

* **含义**：仿真时间流逝速度 = 现实时间 x 1。
* **作用**：保持正常速度。如果你想让云彩飘得快一点，可以改大，但在采集数据时，保持 `1` 最稳定，防止电脑渲染跟不上导致掉帧。

### 3. 相机参数 (3DGS 的生命线)

这是最关键的部分，直接决定了你重建出来的冰山是“高清大片”还是“马赛克”。

```json
  "CameraDefaults": {
    "CaptureSettings": [
      {
        "ImageType": 0,

```

* **含义**：图像类型 = 0 (Scene / RGB)。
* **作用**：这就是我们要的人眼看到的彩色图像。3DGS 算法吃的就是这种图。

```json
        "Width": 1280,
        "Height": 720,

```

* **含义**：分辨率 1280x720 (720P)。
* **为什么是这个数？**
* 你的 3090 显卡很强，其实可以跑 1920x1080。
* 但 1280x720 是一个**“黄金平衡点”**。
* **训练速度**：分辨率翻倍，3DGS 训练时间可能会翻 4 倍。720P 既能保证看清冰面纹理，又能让你在一两个小时内跑完训练。对于毕设演示来说，效率第一。

```json
        "FOV_Degrees": 90,

```

* **含义**：视场角 90度。
* **作用**：相当于相机的广角镜头。90度能一次拍到更多的冰山，有利于 COLMAP（特征匹配软件）找到相邻照片的共同点。如果设太小（比如 45度），你就得拍更多照片才能覆盖全景。

```json
        "AutoExposureSpeed": 100,

```

* **含义**：自动曝光调整速度 = 100 (非常快)。
* **作用**：当摄像机从背光面转到向阳面时，画面会瞬间变亮。这个参数让相机迅速适应光线变化，防止拍出“一片漆黑”或“一片惨白”的废片。

```json
        "MotionBlurAmount": 0,

```

* **含义**：运动模糊 = 0 (彻底关闭)。
* **⭐ 最重要的一行**：**必须是 0**。
* **原理**：3DGS 假设场景是静态的、清晰的。如果你转得太快，画面有了拖影（模糊），算法会误以为物体边缘就是模糊的，重建出来的冰山就会像“融化了一样”。
* **结论**：绝对不能改。

```json
        "TargetGamma": 1.0

```

* **含义**：伽马值 = 1.0 (线性)。
* **作用**：保证光影的线性关系，让色彩更真实。

---

## 6. 最终脚本代码 (`orbit_correction.py`)

该脚本实现了三层螺旋扫描轨迹，已修正 Z 轴方向。

```python
import cosysairsim as airsim
import time
import math
import os
import cv2
import numpy as np

# ================= 🎥 导演参数配置 (Configuration) =================
OUTPUT_DIR = "dataset_ice_final_v2"

# 1. 目标中心 (Target Center)
# 坐标系: AirSim NED (Z轴向下为正)。
# 冰山在UE5中 Z=-1000(底) 到 Z=+1500(顶,预估)。
# 我们将中心选在水面上方约 28米处，即 AirSim Z = -28.0
TARGET_CENTER = airsim.Vector3r(0, 0, -28.0) 

# 2. 拍摄半径 (Radius)
# 冰山最长处约138米，留出余量防止爆框
RADIUS = 120.0     

# 3. 扫描层数 (Scan Layers)
# 层数越多，覆盖越全。3层足以覆盖侧面和顶部。
HEIGHT_LAYERS = 3  
MIN_PITCH = -15.0    # Layer 0: -15度 (轻微俯视，看侧壁)
MAX_PITCH = -55.0    # Layer 2: -55度 (大角度俯视，看顶部)

SPEED_DEG = 3.0      # 采样密度: 每隔 3 度采集一张 (每圈120张)
# =================================================================

def to_quaternion(pitch, roll, yaw):
    """欧拉角 -> 四元数转换 (AirSim需要四元数控制姿态)"""
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
    """获取图像并保存到硬盘"""
    responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
    if not responses: return False
  
    response = responses[0]
    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
  
    # 图像解码 (H, W, 3)
    try:
        img_rgb = img1d.reshape(response.height, response.width, -1)
    except ValueError: return False
  
    if img_rgb.shape[2] == 4: img_rgb = img_rgb[:, :, :3]
  
    filepath = os.path.join(OUTPUT_DIR, "images", filename)
    cv2.imwrite(filepath, img_rgb)
    return True

def main():
    # 1. 创建目录
    if not os.path.exists(os.path.join(OUTPUT_DIR, "images")):
        os.makedirs(os.path.join(OUTPUT_DIR, "images"))
      
    # 2. 连接仿真器
    client = airsim.VehicleClient()
    client.confirmConnection()
    print(f"✅ 已连接到虚拟摄影棚 (Virtual Studio Connected)")

    count = 0
    pitch_steps = np.linspace(MIN_PITCH, MAX_PITCH, HEIGHT_LAYERS)
  
    # 3. 开始循环采集
    for layer_idx, pitch_deg in enumerate(pitch_steps):
        pitch_rad = math.radians(pitch_deg)
      
        # 🔥 [核心修正] Z轴高度计算 🔥
        # 用加号 (+) 确保当 pitch 为负时，Z 值减小 (向上升空)
        cam_z = TARGET_CENTER.z_val + RADIUS * math.sin(pitch_rad)
      
        radius_xy = RADIUS * math.cos(pitch_rad)
      
        print(f"✈️ Layer {layer_idx}: Pitch={pitch_deg:.1f}°, AirSim Z={cam_z:.2f} (Check: Negative is Sky)")

        for yaw_deg in np.arange(0, 360, SPEED_DEG):
            yaw_rad = math.radians(yaw_deg)
          
            # 计算相机 XY 坐标
            cam_x = TARGET_CENTER.x_val - radius_xy * math.cos(yaw_rad)
            cam_y = TARGET_CENTER.y_val - radius_xy * math.sin(yaw_rad)
          
            # 计算 Yaw (始终朝向中心)
            look_yaw = yaw_rad 
          
            pose = airsim.Pose(
                airsim.Vector3r(cam_x, cam_y, cam_z),
                to_quaternion(pitch_rad, 0, look_yaw)
            )
          
            # 执行移动与拍摄
            client.simSetVehiclePose(pose, True)
            time.sleep(0.02) # 等待渲染
          
            fname = f"img_L{layer_idx}_{int(yaw_deg):03d}.jpg"
            save_image(client, fname)
            print(f"📸 Saved {fname} | Z: {cam_z:.1f}m", end="\r")
            count += 1

    print(f"\n✅ 采集完成！共 {count} 张图像。")
    print(f"📂 数据集路径: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()

```

---

## 7. 操作指南 (Operation Manual)

1. **UE5 准备**:

* 打开项目，确保 `wall_of_ice1` 在 `(0,0,-1000)`，`PlayerStart` 在 `(0,0,0)`。
* 调整 `Light Source` 角度，确保视口中呈现理想的蓝天白云效果。
* **关键**: 重启 UE5 以加载新的 `settings.json`。

2. **启动仿真**:

* 点击 UE5 上方的 **Play**。

3. **运行脚本**:

* 在终端运行 `python orbit_correction.py`。

4. **监控**:

* 观察终端输出的 Z 值是否为**负数**。
* 观察 UE5 画面是否平滑绕转且无遮挡。

5. **后续**:

* 采集完成后，使用 `COLMAP` 或 `Postshot` 导入 `dataset_ice_final_v2` 文件夹进行 SfM 和 3DGS 重建。
