# Phase 1：生产级 settings.json 配置完成记录

**完成时间**：2026-03-10
**关联阶段**：Phase 1 — 传感器配置与验证

---

## 一、问题诊断（修改前状态）

旧版 `settings.json` 存在以下 3 个关键缺陷：

| # | 缺陷 | 位置 | 影响 |
|---|------|------|------|
| 1 | `"Cameras"` 使用顶层块 | Vehicles.Vessel1 | ASVSim Vessel 模式不识别，相机数据无法获取 |
| 2 | 缺少 `"Wind"`, `"Range"` | 全局/Sensors | 风力未定义，LiDAR 探测距离默认值不稳定 |
| 3 | `CameraDefaults` 仅含 ImageType:0 | CameraDefaults | Depth/Seg 分辨率回退系统默认 256×144 |

> **关于 Z 值**：`Z: 0` 在 LakeEnv 中完全正常，不是缺陷。`Z: -2` 是调试阶段误写，已确认无需此技巧，已还原为 0。

---

## 二、修改对照表

| 字段                                  | 旧值               | 新值                         | 原因                                                                                            |
| ------------------------------------- | ------------------ | ---------------------------- | ----------------------------------------------------------------------------------------------- |
| `Vehicles.Vessel1.Z`                | `0`              | `0`（保持不变）            | LakeEnv 中 Z=0 船只落在水面，物理引擎自动激活；`Z:-2`（空中坠落）是调试阶段误写，已确认不需要 |
| `Vehicles.Vessel1.Cameras`          | 独立块（错误写法） | 删除                         | ASVSim 不支持 Vessel 模式下的顶层 Cameras 块                                                    |
| `Sensors.top_lidar.Z`               | `0`              | `-1.0`                     | 安装在甲板上方 1m，避免自遮挡                                                                   |
| `Sensors.top_lidar.PointsPerSecond` | `100000`         | `300000`                   | 提高点云密度，改善近场感知精度                                                                  |
| `Sensors.top_lidar.DrawDebugPoints` | `true`           | `false`                    | 关闭调试点绘制，减少渲染开销                                                                    |
| `Sensors.top_lidar.Range`           | 未设置             | `100.0`                    | 显式设置 100m 最大测距，与 RL 观测对齐                                                          |
| `Sensors.front_camera`              | 旧 Cameras 块      | 新增（SensorType:1）         | 正确的 ASVSim 相机注册方式                                                                      |
| `Sensors.down_camera`               | 无                 | 新增（Pitch:-45）            | 斜向下看冰面，用于 3DGS 冰面重建                                                                |
| `Wind`                              | 未设置             | `{X:0,Y:0,Z:0}`            | 显式定义初始无风环境                                                                            |
| `CameraDefaults`                    | 仅 ImageType:0     | ImageType 0/1/5 各 1280×720 | 非 Scene 类型分辨率需在此单独配置，否则回退 256×144                                            |

---

## 三、最终配置（生产版）

```json
{
  "SettingsVersion": 2.0,
  "SimMode": "Vessel",
  "PhysicsEngineName": "VesselEngine",
  "ViewMode": "SpringArmChase",
  "InitialInstanceSegmentation": true,
  "ClockSpeed": 1,
  "Wind": { "X": 0, "Y": 0, "Z": 0 },

  "PawnPaths": {
    "BlueResearchBoat": {
      "PawnBP": "Class'/AirSim/Blueprints/BP_VesselPawn.BP_VesselPawn_C'"
    }
  },

  "Vehicles": {
    "Vessel1": {
      "VehicleType": "MilliAmpere",
      "AutoCreate": true,
      "PawnPath": "BlueResearchBoat",
      "HydroDynamics": { "hydrodynamics_engine": "FossenCurrent" },
      "X": 0, "Y": 0, "Z": 0,
      "Sensors": {
        "top_lidar": {
          "SensorType": 6, "Enabled": true,
          "NumberOfLasers": 16, "PointsPerSecond": 300000,
          "RotationsPerSecond": 10, "Range": 100.0,
          "DrawDebugPoints": false, "DataFrame": "SensorLocalFrame",
          "X": 0.0, "Y": 0.0, "Z": -1.0
        },
        "front_camera": {
          "SensorType": 1, "Enabled": true, "Width": 1280, "Height": 720,
          "X": 1.0, "Y": 0.0, "Z": -0.5, "Pitch": 0.0, "Roll": 0.0, "Yaw": 0.0
        },
        "down_camera": {
          "SensorType": 1, "Enabled": true, "Width": 1280, "Height": 720,
          "X": 0.5, "Y": 0.0, "Z": -1.0, "Pitch": -45.0, "Roll": 0.0, "Yaw": 0.0
        }
      }
    }
  },

  "CameraDefaults": {
    "CaptureSettings": [
      { "ImageType": 0, "Width": 1280, "Height": 720, "FOV_Degrees": 90 },
      { "ImageType": 1, "Width": 1280, "Height": 720, "FOV_Degrees": 90 },
      { "ImageType": 5, "Width": 1280, "Height": 720, "FOV_Degrees": 90 }
    ]
  }
}
```

> ImageType 0=Scene, **1=DepthPlanar**（CosysAirSim 特有，标准 AirSim 是 2）, 5=Segmentation

---

## 四、传感器布局（俯视图）

```
         [船头]
    X+ →
           ★ front_camera (X:1.0, Z:-0.5, Pitch:0°)
             朝前平视，采集前方冰情 RGB/Depth/Seg

           ◆ down_camera (X:0.5, Z:-1.0, Pitch:-45°)
             斜向下45°，采集正前方冰面细节，用于3DGS重建

           ▲ top_lidar (X:0, Z:-1.0)
             安装在桅杆上，360°水平扫描，16线垂直
         [船尾]
```

---

## 五、相机数据请求方式（Python API）

```python
import cosysairsim as airsim
import numpy as np

client = airsim.VesselClient()
client.confirmConnection()

# 请求多类型图像（同一相机，三种模态同时采集）
responses = client.simGetImages([
    # front_camera → 整数索引 0（SensorType:1 的第一个）
    airsim.ImageRequest(0, airsim.ImageType.Scene, False, False),
    airsim.ImageRequest(0, airsim.ImageType.DepthPlanar, True, False),
    airsim.ImageRequest(0, airsim.ImageType.Segmentation, False, False),
    # down_camera → 整数索引 1（SensorType:1 的第二个）
    airsim.ImageRequest(1, airsim.ImageType.Scene, False, False),
])

# 解码 RGB
r = responses[0]
img_rgb = np.frombuffer(r.image_data_uint8, dtype=np.uint8).reshape(r.height, r.width, 3)
img_rgb = np.flipud(img_rgb)   # AirSim 图像上下翻转，需修正

# 解码 Depth（单位：米）
rd = responses[1]
depth = np.array(rd.image_data_float, dtype=np.float32).reshape(rd.height, rd.width)

# 解码 Segmentation
rs = responses[2]
img_seg = np.frombuffer(rs.image_data_uint8, dtype=np.uint8).reshape(rs.height, rs.width, 3)
```

### CosysAirSim ImageType 枚举速查（⚠️ 与标准 AirSim 不同）

| 枚举名 | CosysAirSim 值 | 标准 AirSim 值 | 数据类型 |
|-------|:--------------:|:--------------:|---------|
| `ImageType.Scene` | **0** | 0 | uint8, HxWx3 |
| **`ImageType.DepthPlanar`** | **1** | **2** ← 踩坑 | float32, HxW（单位：米） |
| `ImageType.DepthVis` | 3 | 1 | uint8 |
| `ImageType.Segmentation` | **5** | 5 | uint8, HxWx3 |

> `CameraDefaults` 里写数字 `1` 是 DepthPlanar，写 `2` 是 DepthPerspective（无法设置 Depth 分辨率）。

---

## 六、验证脚本

文件位置：`ASVSim_zsh/2-verify_sensors.py`

**运行方式**（UE5 仿真运行中执行）：

```bash
python 2-verify_sensors.py
```

**验证覆盖项**：

- [X] ASVSim 连接
- [X] Vessel1 生成确认
- [X] 物理引擎激活状态（判断速度/高度）
- [X] front_camera RGB / Depth / Seg 三通道
- [X] down_camera RGB
- [X] LiDAR 点云数量和距离范围
- [X] 相机内参矩阵 K 计算

---

## 七、下一步

Phase 1 完成后，进入 **Phase 2：极地 UE5 场景构建**，关键任务：

- 在 Fab Marketplace 获取 Arctic/Ice 资产包
- 替换 LakeEnv 的水面材质和背景
- 添加冰山 StaticMesh Actor（确保实例分割兼容）
- 测试 `front_camera + down_camera` 能正确分割冰山

*记录生成于 2026-03-10*

---

## 八、最终验证结果（2026-03-10 实测，6/6 全通过）

```
验证通过 6/6 — Phase 1 配置完成，可进入 Phase 2
```

### 实测数据

| 步骤               | 结果                       | 备注                                          |
| ------------------ | -------------------------- | --------------------------------------------- |
| Vessel1 生成       | ✅                         | listVehicles: ['Vessel1']                     |
| 物理引擎           | ✅                         | 速度=0 正常（无外力静止）                     |
| front_camera RGB   | ✅ 1280×720               | index=0                                       |
| front_camera Depth | ✅ 1280×720（两轮修复后） | CosysAirSim DepthPlanar=1，非标准 AirSim 的 2 |
| front_camera Seg   | ✅ 4 个分割对象            |                                               |
| down_camera RGB    | ✅ 1280×720               | index=1，Pitch=-45°                          |
| LiDAR top_lidar    | ✅ 8192 点，0~99m          |                                               |
| 相机内参 K         | ✅ fx=640, cx=640, cy=360  | FOV=90° 离线计算                             |

### 关键发现：相机寻址规则

`simGetImages` 使用**整数索引**，不用传感器名字符串：

- `Sensors` 块中所有 `SensorType:1` 相机按 JSON 顺序依次编号，排除非相机传感器（LiDAR等）
- `front_camera`（第1个SensorType:1）→ index `0`
- `down_camera`（第2个SensorType:1）→ index `1`
- LiDAR（SensorType:6）不占相机索引

### 第二次修复（第一轮）：Depth / Seg 分辨率问题

**问题**：Depth 和 Seg 图像实际输出 256×144，而非期望的 1280×720。

**原因**：`CameraDefaults.CaptureSettings` 仅配置了 `ImageType: 0`（RGB），Depth 和 Segmentation 回退到系统默认 256×144。

**第一轮修复**（按标准 AirSim 枚举写入）：

```json
{ "ImageType": 2, "Width": 1280, "Height": 720 },   ← 错！CosysAirSim DepthPlanar ≠ 2
{ "ImageType": 5, "Width": 1280, "Height": 720 }    ← 正确，Segmentation=5 两者一致
```

**结果**：Seg 升到 1280×720 ✅，Depth 仍是 256×144 ❌。

---

### 第三次修复（第二轮）：CosysAirSim ImageType 枚举与标准 AirSim 不同

**根因**：`cosysairsim/types.py` 实测枚举值：

| 名称                      | CosysAirSim 实际值 |   标准 AirSim 值   |
| ------------------------- | :----------------: | :-----------------: |
| `Scene`                 |         0         |          0          |
| **`DepthPlanar`** |    **1**    | **2** ← 踩坑 |
| `DepthVis`              |         3         |          1          |
| `Segmentation`          |         5         |          5          |

`ImageType: 2` 在 CosysAirSim 中是 `DepthPerspective`，不是 `DepthPlanar`。

**最终正确配置**（已写入 settings.json）：

```json
"CameraDefaults": {
  "CaptureSettings": [
    { "ImageType": 0, "Width": 1280, "Height": 720, "FOV_Degrees": 90 },
    { "ImageType": 1, "Width": 1280, "Height": 720, "FOV_Degrees": 90 },
    { "ImageType": 5, "Width": 1280, "Height": 720, "FOV_Degrees": 90 }
  ]
}
```

重启 UE5 后三种 ImageType 均以 1280×720 输出。

### 最终确认（重启 UE5 后实测）

- Depth 分辨率 ✅ 1280×720（`ImageType:1` 生效）
- `front_camera` Depth 范围：min=1.70m, max=65504m — 正常（远端为天空，float16 max=65504；近端为水面 ~1.7m）
- `down_camera` Depth 范围：min=0.35m, max=65504m — 正常（Pitch=-45° 向下，近端更接近水面）
- 所有传感器 6/6 验证通过，Phase 1 完成

---

## 九、Phase 1 深度复盘

### 9.1 完整问题链时间线

| 轮次 | 发现的问题                                       | 根因                                                                                           | 修复方案                                                 |
| ---- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 0    | 配置阶段误将 `Z:0` 改为 `Z:-2`               | 混淆了"调试阶段落水技巧"与生产配置；`2_找到船并跑起来.md` 中 Z:-2 是早期调试用法，非最终配置 | 回退为 `Z:0`（LakeEnv 中水面即 Z=0，物理引擎自动激活） |
| 1    | UE5 崩溃（`this` is nullptr）                  | `simGetCameraInfo("front_camera")` 对传感器相机无效                                          | 改为离线计算内参 K                                       |
| 2    | `invalid map<K, T> key`（相机访问失败）        | `simGetImages("front_camera", ...)` 传感器名不在服务端相机映射表                             | 改用整数索引 `ImageRequest(0, ...)`                    |
| 3    | Depth/Seg 分辨率 256×144                        | `CameraDefaults` 缺少非 Scene ImageType 的分辨率配置                                         | 补充 ImageType 1 和 5                                    |
| 4    | Seg 修好但 Depth 仍 256×144                     | CosysAirSim `DepthPlanar=1`，非标准 AirSim 的 `2`                                          | 将 `ImageType:2` 改为 `ImageType:1`                  |
| 5    | 脚本卡死在 Step 3（`simGetImages` 永远不返回） | `simGetImages(..., vessel_name)` 传入 vehicle_name 参数导致服务端 RPC 阻塞                   | 去掉第二个参数，改为 `simGetImages([...])`             |

---

### 9.2 核心知识点总结

#### 知识点A：SensorType:1 相机寻址

```
写法（settings.json）：  "Sensors": { "front_camera": { "SensorType": 1 } }
访问方式（Python）：      simGetImages([ImageRequest(0, ...)])  ← 整数索引
                         NOT ImageRequest("front_camera", ...)  ← 字符串无效
                         NOT simGetImages([...], "Vessel1")     ← ⚠️ 传 vehicle_name 会导致 RPC 阻塞卡死

原理：
  simGetImages 查的是服务端 cameras_map["0"] / cameras_map["1"]
  SensorType:1 传感器按 Sensors JSON 声明顺序依次编为 "0"、"1"…
  LiDAR（SensorType:6）不占相机索引
  vehicle_name 参数在相机 RPC 中不被支持，传入会导致服务端阻塞

对比：getLidarData("top_lidar", "Vessel1") 走传感器名查询，规则不同，且必须传 vehicle_name
```

#### 知识点B：CosysAirSim ImageType 枚举（与标准 AirSim 不同）

```python
# cosysairsim/types.py 实测值
class ImageType:
    Scene       = 0   # RGB
    DepthPlanar = 1   # ← 标准 AirSim 是 2，CosysAirSim 改为 1
    DepthVis    = 3
    Segmentation= 5

# CameraDefaults 必须用数字值，不是 Python 枚举名：
# 正确：{ "ImageType": 1, ... }   ← DepthPlanar
# 错误：{ "ImageType": 2, ... }   ← 在CosysAirSim中是DepthPerspective
```

#### 知识点C：settings.json 三层分辨率优先级

```
高 ←────────────────────────────────── 低
传感器 Width/Height   >   CameraDefaults   >   系统默认(256×144)

实测行为：
  - Scene(0)：传感器 Width/Height 生效 → 1280×720
  - DepthPlanar(1)：传感器 Width/Height 不覆盖此类型 → 回退 CameraDefaults
  - Segmentation(5)：同上 → 回退 CameraDefaults

结论：传感器的 Width/Height 字段仅对 Scene 类型有效，
      非 Scene 类型的分辨率需在 CameraDefaults.CaptureSettings 中单独配置。
```

#### 知识点D：`simGetCameraInfo` 的适用范围

```
适用：传统 AirSim 相机（"Cameras" 块 或 默认 "0" 摄像头）
不适用：Sensors 块中 SensorType:1 传感器相机
        → 调用会返回 nullptr → UE5 C++ 空指针崩溃

替代方案：从 settings.json 已知参数离线计算内参
  fx = W / (2 * tan(fov_rad / 2))
  K = [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
```

---

### 9.3 最终 settings.json 各字段速查

```json
{
  // 全局层
  "SettingsVersion": 2.0,         // 固定 2.0
  "SimMode": "Vessel",            // 船只模式，必须
  "PhysicsEngineName": "VesselEngine",
  "ViewMode": "SpringArmChase",   // 追踪视角
  "InitialInstanceSegmentation": true,  // 分割系统启动
  "ClockSpeed": 1,                // 仿真时钟倍速
  "Wind": { "X": 0, "Y": 0, "Z": 0 },

  // 相机全局默认分辨率（非 Scene 类型必须在此配置）
  "CameraDefaults": {
    "CaptureSettings": [
      { "ImageType": 0, "Width": 1280, "Height": 720, "FOV_Degrees": 90 },  // Scene
      { "ImageType": 1, "Width": 1280, "Height": 720, "FOV_Degrees": 90 },  // DepthPlanar
      { "ImageType": 5, "Width": 1280, "Height": 720, "FOV_Degrees": 90 }   // Segmentation
    ]
  },

  // 船只
  "Vehicles": {
    "Vessel1": {
      "X": 0, "Y": 0, "Z": 0,    // Z=0 正常，物理引擎自动激活
      "Sensors": {
        // LiDAR — 通过 getLidarData("top_lidar", "Vessel1") 访问
        "top_lidar": { "SensorType": 6, ... },

        // 相机 — 通过 simGetImages([ImageRequest(0,...)]) 访问（索引=0）
        "front_camera": { "SensorType": 1, ... },

        // 相机 — 通过 simGetImages([ImageRequest(1,...)]) 访问（索引=1）
        "down_camera": { "SensorType": 1, ... }
      }
    }
  }
}
```

---

### 9.4 Phase 1 最终状态

| 传感器             | 访问方式                                    | 分辨率           | 状态 |
| ------------------ | ------------------------------------------- | ---------------- | ---- |
| front_camera RGB   | `ImageRequest(0, ImageType.Scene)`        | 1280×720        | ✅   |
| front_camera Depth | `ImageRequest(0, ImageType.DepthPlanar)`  | 1280×720        | ✅   |
| front_camera Seg   | `ImageRequest(0, ImageType.Segmentation)` | 1280×720        | ✅   |
| down_camera RGB    | `ImageRequest(1, ImageType.Scene)`        | 1280×720        | ✅   |
| down_camera Depth  | `ImageRequest(1, ImageType.DepthPlanar)`  | 1280×720        | ✅   |
| down_camera Seg    | `ImageRequest(1, ImageType.Segmentation)` | 1280×720        | ✅   |
| LiDAR              | `getLidarData("top_lidar", "Vessel1")`    | 8192点/帧, 0~99m | ✅   |

*Phase 1 完成，可进入 Phase 2（极地 UE5 场景构建）*
