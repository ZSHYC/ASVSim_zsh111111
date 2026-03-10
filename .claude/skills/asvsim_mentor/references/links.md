# IDLab-ASVSim 文档参考链接

IDLab-ASVSim 是基于 Cosys-AirSim 的船舶仿真平台，支持流体动力学、传感器建模、强化学习训练和数据集生成。

---

## 目录

1. [Windows 安装](#1-windows-安装)
2. [Vessel API](#2-vessel-api)
3. [Procedural Generation（过程化生成）](#3-procedural-generation过程化生成)
4. [Data Generation（数据集生成）](#4-data-generation数据集生成)
5. [Reinforcement Learning（强化学习）](#5-reinforcement-learning强化学习)
6. [Core APIs（通用 API）](#6-core-apis通用-api)
7. [Image APIs（图像 API）](#7-image-apis图像-api)
8. [Instance Segmentation（实例分割）](#8-instance-segmentation实例分割)
9. [Settings（配置文件）](#9-settings配置文件)
10. [ASVSim 论文链接](#10-asvsim-论文链接)

---

## 1. Windows 安装

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/installation/install_windows/

从源码在 Windows 上构建 ASVSim 的完整步骤。

**关键依赖版本：**
- Unreal Engine **5.4.X**
- Visual Studio 2022，必须选择 MSVC **v14.38.33130**（更高版本会导致编译失败）
- Windows SDK 10.0.X（最新版）

**构建流程：**
```bash
git lfs install
git clone https://github.com/BavoLesy/ASVSim.git
cd ASVSim
build.cmd
```
构建产物输出至 `Unreal\Plugins`。之后进入 `Unreal\Environments\Blocks`，运行 `update_from_git.bat`，用 VS2022 以 "Develop Editor + x64" 配置启动。

---

## 2. Vessel API

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/vessel/vessel_api/

核心船舶控制 API，支持流体动力学（Fossen 模型）、环境干扰（风/浪/流）、传感器建模。

**settings.json 基本配置：**
```json
{
  "SettingsVersion": 2.0,
  "SimMode": "Vessel",
  "PhysicsEngineName": "VesselEngine",
  "Vehicles": {
    "Vessel1": {
      "VehicleType": "MilliAmpere",
      "HydroDynamics": { "hydrodynamics_engine": "FossenCurrent" },
      "PawnPath": "DefaultVessel",
      "AutoCreate": true
    }
  }
}
```

**支持的船型：**
| 船型 | 流体动力学引擎 | 物理引擎 | 推进器数量 |
|------|-------------|---------|-----------|
| milliampere | FossenCurrent | VesselEngine | 2 |
| cybership2 | FossenCurrent | VesselEngine | 2 |
| qiuxin5 | FossenCurrent | VesselEngine | 1 |
| mariner | MarinerHydrodynamics | LargeVesselEngine | 1 |

**关键 API — setVesselControls（官方文档确认，2026-03-10）：**
```python
from cosysairsim.types import VesselControls

# 单推进器（单值会广播到所有推进器槽位）
controls = VesselControls(thrust=0.7, angle=0.6)
client.setVesselControls('VesselName', controls)

# 多推进器（MilliAmpere 有 2 个）
controls = VesselControls(thrust=[0.7, 0.8], angle=[0.6, 0.7])
client.setVesselControls('VesselName', controls)
```

**⚠️ angle 参数约定（与直觉不同，务必注意）：**
- `thrust`: 0.0–1.0（推力大小，0=停止，1=全速）
- `angle`: **0.0–1.0（0.5 = 直行，< 0.5 = 左转，> 0.5 = 右转）**
- 常用值：0.5=直行，0.6=轻微右转，0.4=轻微左转

> `hello_ship.py` 中使用了错误的约定（angle=0.0 标注为直行），以官方文档为准。

**setDisturbanceControls（风/流干扰）：**
```python
from cosysairsim.types import DisturbanceControls
import math
disturbances = DisturbanceControls(
    wind_force=15.0, wind_angle=math.pi/4,     # 风力(N)和方向(rad)
    current_velocity=5.0, current_angle=0.0    # 流速(m/s)和方向(rad)
)
client.setDisturbanceControls('VesselName', disturbances)
```

**getVesselState：**
```python
state = client.getVesselState('VesselName')
pos = state.kinematics_estimated.position     # 位置，单位米
vel = state.kinematics_estimated.linear_velocity  # 速度，单位 m/s
```

其他 API：`simAddObstacle()`、`simGetImages()`、`getLidarData()`

---

## 3. Procedural Generation（过程化生成）

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/vessel/procedural_generation/

运行时动态生成港口环境，基于 Unreal Engine 5 PCG 系统，支持固定 seed 可重复生成。

**启用 PCG 插件（.uproject）：**
```json
"Plugins": [
  { "Name": "PCG", "Enabled": true },
  { "Name": "PCGGeometryScriptInterop", "Enabled": true }
]
```

**关键 API：**
```python
# 1. 激活生成系统（必须先调用）
client.activateGeneration()

# 2. 生成港口地形
client.generatePortTerrain(
    port_name="port",
    seed=12345,       # 随机种子（相同 seed 产生相同结果）
    length=10,        # 地形段数
    mina=-45.0,       # 相邻段最小转角（度）
    maxa=45.0,        # 相邻段最大转角（度）
    mind=3000.0,      # 相邻点最小距离（厘米）
    maxd=6000.0       # 相邻点最大距离（厘米）
)

# 3. 获取导航目标位置
goal_loc, border_pts = client.getGoal(
    initial_location=Vector2r(x=0.0, y=0.0),
    distance=5        # 目标所在地形段索引
)

# 4. 获取船舶绝对/相对位置
abs_loc, rel_loc = client.getLocation(initial_location=Vector2r(x=0.0, y=0.0))
```

---

## 4. Data Generation（数据集生成）

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/vessel/data_generation/

自动化数据集生成套件，同步采集 RGB、语义分割、深度图像。脚本位于 `PythonClient/Vessel/data_generation/`。

**安装依赖：**
```bash
pip install cosysairsim opencv-python matplotlib pillow pandas numpy pdf2image
```

**使用示例：**
```python
import cosysairsim as airsim
from dataset_generation import initialize_data_collection, generate_dataset

client = airsim.VesselClient()
client.confirmConnection()
client.enableApiControl(True)

seg_folder, rgb_folder, depth_folder = initialize_data_collection(
    client, dataset_path="Vessel/data_generation/dataset"
)
generate_dataset(client, seg_folder, rgb_folder, depth_folder,
                 max_depth=255, num_images=100)
```

**输出目录结构：**
```
dataset/YYYY_MM_DD_HH_MM_SS/
├── rgb/            # RGB 彩色图像 (*.png)
├── segmentation/   # 实例分割图像
└── depth/          # 深度图像
```

---

## 5. Reinforcement Learning（强化学习）

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/vessel/reinforcement_learning/

基于 Gymnasium 接口的船舶强化学习环境 `ShippingSim`，支持 SAC 等连续动作算法。

**环境规格：**
| 规格 | 详情 |
|------|------|
| 动作空间 | Box(2,) — [thrust, rudder] |
| 动作范围 | thrust: [0, 1]，rudder: [0.4, 0.6] |
| 观测空间 | Box(57,) — 船舶状态 + LiDAR |
| 最大步数 | 200 timesteps |
| 成功条件 | 距目标点 ≤ 10 米 |

**观测向量（57维）：**
```
[dist_goal_x, dist_goal_y,          # 当前与目标的 XY 距离
 prev_dist_goal_x, prev_dist_goal_y, # 上一步距离
 heading,                            # 船艏角（弧度）
 vel_x, vel_y,                       # 线速度
 acc_x, acc_y,                       # 线加速度
 ang_acc_z,                          # 角加速度
 prev_thrust, prev_rudder,           # 上一步动作
 lidar[0:45]]                        # 45 个 LiDAR 测距值
```

**SAC 训练示例：**
```python
import gymnasium as gym
from stable_baselines3 import SAC
from Vessel.envs.Shipsim_gym import ShippingSim

env = gym.make("ship-sim-v0")
model = SAC("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100000)
```

---

## 6. Core APIs（通用 API）

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/usage/apis/

AirSim Python API 入门：连接仿真器、控制载具、获取状态。

**安装：**
```bash
pip install msgpack-rpc-python
# 或在 PythonClient 目录下：
pip install .
```

**VesselClient 连接模板：**
```python
import cosysairsim as airsim

client = airsim.VesselClient()
client.confirmConnection()
client.enableApiControl(True)
```

**核心 API：**
- `confirmConnection()` — 确认与仿真器连接
- `enableApiControl(True/False)` — 启用/禁用 API 控制
- `getVesselState()` — 获取船舶状态（位置/速度/姿态）
- `simGetImages([ImageRequest, ...])` — 批量获取相机图像

**⚠️ 重大性能注意（image_apis 文档 Lumen 节，2026-03-10 实测验证）：**

UE5 Lumen GI/Reflections 对每个 SceneCapture 组件默认生效，是 `simGetImages` 极慢的主因。**务必在 `CaptureSettings` 中显式禁用：**

```json
"CameraDefaults": {
  "CaptureSettings": [
    {
      "ImageType": 0, "Width": 1280, "Height": 720, "FOV_Degrees": 90,
      "LumenGIEnable": false, "LumenReflectionEnable": false,
      "MotionBlurAmount": 0
    },
    {
      "ImageType": 1, "Width": 1280, "Height": 720, "FOV_Degrees": 90,
      "LumenGIEnable": false, "LumenReflectionEnable": false
    },
    {
      "ImageType": 5, "Width": 1280, "Height": 720, "FOV_Degrees": 90,
      "LumenGIEnable": false, "LumenReflectionEnable": false
    }
  ]
}
```

Lumen 参数说明（来自官方文档）：

| 参数 | 类型 | 说明 |
|---|---|---|
| `LumenGIEnable` | bool | 全局光照，默认 true，关闭可大幅提速 |
| `LumenReflectionEnable` | bool | Lumen 反射，默认 true，关闭可提速 |
| `LumenFinalQuality` | 0.25–2 | 质量倍率，不如直接关闭 |
| `MotionBlurAmount` | float | 运动模糊，数据集采集应设为 0 |

---

## 7. Image APIs（图像 API）

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/usage/image_apis/

批量图像采集，支持压缩/非压缩 RGB、浮点深度图，与 NumPy 集成。

**批量获取多类型图像：**
```python
responses = client.simGetImages([
    airsim.ImageRequest(0, airsim.ImageType.Scene),                   # PNG 压缩
    airsim.ImageRequest(1, airsim.ImageType.Scene, False, False),      # 非压缩 RGB
    airsim.ImageRequest(1, airsim.ImageType.DepthPlanar, True)         # 浮点深度图
])
```

**转换为 NumPy 数组：**
```python
response = responses[0]
img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8)
img_rgb = img1d.reshape(response.height, response.width, 3)
# ⚠️ flipud 版本差异（2026-03-10 实测）：
# - 标准 AirSim：需要 np.flipud(img_rgb)
# - CosysAirSim 3.0.1：原始图像已正向，flipud 反而导致倒置，不要加
# img_rgb = np.flipud(img_rgb)  # 标准 AirSim 才需要
```

**ImageType 枚举：**
`Scene`, `DepthVis`, `DepthPlanar`, `DepthPerspective`, `Segmentation`, `SurfaceNormals`, `Infrared`

**辅助函数：**
- `airsim.string_to_uint8_array(binary)` — 二进制转 uint8 NumPy 数组
- `airsim.list_to_2d_float_array(data, w, h)` — 浮点列表转二维 NumPy 数组
- `airsim.write_pfm(filename, array)` — 保存为 PFM 格式
- `client.simPause(True/False)` — 暂停/恢复仿真

---

## 8. Instance Segmentation（实例分割）

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/usage/instance_segmentation/

内置实例分割系统，为每个场景对象分配独立颜色，用于生成分割标注数据集。

**关键参数：**
- 最大可分配颜色数：**2,744,000** 种
- 默认：仿真启动时自动为每个对象随机分配颜色
- 禁用自动分配：`settings.json` 中设置 `"InitialInstanceSegmentation": false`

**支持 / 不支持的对象类型：**
| 支持 | 不支持（替代方案） |
|------|-----------------|
| StaticMesh | Landscape → 用 StaticMesh 地形替代 |
| SkeletalMesh | Foliage → 用 StaticMesh 对象替代 |
| — | Brush → 转换为 StaticMesh |

**参考脚本：**
- `PythonClient/segmentation/segmentation_test.py` — 使用示例
- `PythonClient/segmentation/segmentation_generate_list.py` — 生成对象-颜色映射表

动态添加新对象后，调用 `ASimModeBase::AddNewActorToSegmentation(AActor)` 注册到分割系统。

---

## 9. Settings（配置文件）

**链接:** https://bavolesy.github.io/idlab-asvsim-docs/settings/

`settings.json` 的查找优先级和常用全局参数。

**文件查找优先级（从高到低）：**
1. 命令行 `-settings="C:\path\to\settings.json"`
2. 命令行内联 JSON `-settings={"foo":"bar"}`
3. 可执行文件同目录
4. 启动脚本目录
5. `~/Documents/AirSim/settings.json`

**常用全局参数：**
```json
{
  "SettingsVersion": 2.0,
  "SimMode": "Vessel",
  "LocalHostIp": "127.0.0.1",
  "ApiServerPort": 41451,
  "InitialInstanceSegmentation": true,
  "ClockSpeed": 1,
  "Wind": { "X": 0, "Y": 0, "Z": 0 },
  "CameraDefaults": {
    "CaptureSettings": [
      { "ImageType": 0, "Width": 256, "Height": 144, "FOV_Degrees": 90 }
    ]
  }
}
```

**注意：** `settings.json` 必须使用 **ASCII 编码**保存。只需覆盖需要改变的字段，无需复制所有默认值。

---

## 10. ASVSim 论文链接

**链接:** https://arxiv.org/abs/2506.22174

ASVSim 的核心论文，详细介绍了平台架构、功能模块及其在仿真与强化学习中的应用。
