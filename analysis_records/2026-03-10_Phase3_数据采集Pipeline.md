# Phase 3：多模态数据采集 Pipeline

**完成时间**：2026-03-10
**关联脚本**：`3-collect_dataset.py`
**依赖**：Phase 1 已完成（settings.json + 传感器验证 6/6 通过）

---

## 一、官方控制 API 核查（重要！）

**来源**：https://bavolesy.github.io/idlab-asvsim-docs/vessel/vessel_api/（PowerShell 抓取，2026-03-10）

### 1.1 VesselControls 参数约定

```python
from cosysairsim.types import VesselControls

# 单推进器
VesselControls(thrust=0.7, angle=0.6)   # 70% 推力，轻微右转

# 多推进器（MilliAmpere 有 2 个推进器）
VesselControls(thrust=[0.7, 0.8], angle=[0.6, 0.7])
```

**参数范围（官方文档原文）**：

| 参数       | 范围      | 含义                                             |
| ---------- | --------- | ------------------------------------------------ |
| `thrust` | 0.0 ~ 1.0 | 推力大小（0=停止, 1=全速）                       |
| `angle`  | 0.0 ~ 1.0 | **0.5 = 直行，< 0.5 = 左转，> 0.5 = 右转** |

### 1.2 VesselControls 实现细节（来自 types.py）

- 单个 float 会广播到 10 个推进器槽位（`MAX_THRUSTER_COUNT=10`）
- MilliAmpere 只用到前 2 个槽位
- 传单值等价于两个推进器同参数

---

## 二、Phase 3 设计决策

### 2.1 为什么必须 simPause

不暂停时，Python 端连续发出多个请求，服务端物理引擎同时运行，导致：

- 第 1 个请求（RGB）和第 5 个请求（LiDAR）对应不同的船位置
- 3DGS 训练用位置不一致的数据会产生错误重建

```python
client.simPause(True)
try:
    responses = client.simGetImages([...])    # 同一时刻
    lidar_data = client.getLidarData(...)     # 同一时刻
    state = client.getVesselState(...)        # 同一时刻
finally:
    client.simPause(False)   # finally 保证即使异常也恢复，避免 UE5 死锁
```

### 2.2 轨迹策略：匀速右圆弧

```python
THRUST = 0.3    # 30% 推力，速度适中
ANGLE  = 0.6    # 0.5=直行，0.6=右转（官方文档约定）
```

**效果**：船缓慢绕右圆弧，约 50~100 帧走完一圈。调整指南：

| 需求                     | 调整方式                  |
| ------------------------ | ------------------------- |
| 圆圈更大（转弯不那么急） | 减小 ANGLE，如 0.55       |
| 帧间距更大               | 增大 MOVE_SECONDS，如 2.0 |
| 左转圆圈                 | ANGLE = 0.4               |
| 直行（直线采集）         | ANGLE = 0.5               |

### 2.3 数据格式选择

| 传感器    | 格式               | 原因                                                           |
| --------- | ------------------ | -------------------------------------------------------------- |
| RGB / Seg | `.png`           | 无损，uint8                                                    |
| Depth     | `.npy` (float32) | 保留精度，PNG 只能存整数，会丢小数部分，3DGS 需要 float32 米值 |
| LiDAR     | `.json`          | 可读，便于调试                                                 |
| Pose      | `poses.json`     | 统一存储，后续转 COLMAP 格式用                                 |

### 2.4 图像解码注意事项

```python
# ⚠️ CosysAirSim 3.0.1 实测（2026-03-10）：
# 原始图像已经是正向，不需要 flipud。
# 标准 AirSim 文档说需要 flipud，但本版本已修正。
# 实证：seg 图（无 flipud）方向正确；rgb 图（有 flipud）倒置 → 去掉 flipud。
img_rgb = np.frombuffer(r.image_data_uint8, dtype=np.uint8).reshape(h, w, 3)
# 不要 np.flipud()

# cosysairsim 返回 RGB 顺序，cv2 写入需要 BGR
img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
```

**性能优化（2026-03-10 实测过慢后修正）**：
- 将两次独立的 `simGetImages`（front + down 分开）合并为一次调用，减少一次 RPC 往返
- `MOVE_SECONDS` 从 1.0s 缩短为 0.3s

### 2.5 本次不做坐标变换

ASVSim 世界坐标（X=前, Y=右, Z=下）与 COLMAP/NeRF 的相机坐标系不同，但**本脚本只存原始值**。坐标变换由后续 `4-convert_poses.py` 处理，先跑通采集，再对齐格式。

---

## 三、输出目录结构

```
dataset/YYYY_MM_DD_HH_MM_SS/
├── rgb/              0000.png, 0001.png ...   uint8, HxWx3, BGR
├── depth/            0000.npy, 0001.npy ...   float32, HxW, 单位米, inf=无效
├── segmentation/     0000.png, 0001.png ...   uint8, HxWx3, BGR（实例颜色）
├── lidar/            0000.json ...            [[x,y,z], ...] SensorLocalFrame
└── poses.json        每帧位置+四元数+相机内参
```

**poses.json 单帧结构**：

```json
{
  "frame_id": 0,
  "position":    {"x": 12.3, "y": -5.1, "z": 0.02},
  "orientation": {"w": 0.99, "x": 0.0, "y": 0.0, "z": 0.1},
  "camera_intrinsics": {
    "fx": 640.0, "fy": 640.0, "cx": 640.0, "cy": 360.0,
    "width": 1280, "height": 720, "fov_deg": 90.0
  },
  "timestamp": "2026-03-10T14:30:00"
}
```

---

## 四、运行方法

```bash
# 前提：UE5 + ASVSim 已运行，Phase 1 settings.json 已加载

# 安装依赖（若未安装）
pip install opencv-python

# 运行
python 3-collect_dataset.py
```

**正常输出示例**：

```
[  1/100] pos=(  1.2,  0.3, 0.01) lidar= 8192pts depth_valid= 614400px
[  2/100] pos=(  2.5,  0.8, 0.01) lidar= 8192pts depth_valid= 614400px
...
[采集] 完成：100 帧，输出：dataset/2026_03_10_14_30_00/
```

**depth_valid 接近 0 的情况**：LakeEnv 水面开阔，前方天空的 depth = inf，这是正常现象，不影响 pipeline 验证。

---

## 五、自检验证

脚本自带采集完成后的快速自检（`_quick_check`），输出：

- 各子目录文件数量（应均为 NUM_FRAMES）
- 首帧 RGB 形状（期望 `(720, 1280, 3)`）
- 首帧 Depth 有效像素数和范围

---

## 六、已知限制与后续

| 限制                 | 说明                                                      |
| -------------------- | --------------------------------------------------------- |
| Pose 坐标系未转换    | ASVSim 原始坐标，需 `4-convert_poses.py` 转 COLMAP 格式 |
| LakeEnv 无明显3D结构 | 3DGS 重建质量不高，但 pipeline 验证本身是有效的           |
| LiDAR 存 JSON        | 数据量大时考虑改为 `.npy` 节省空间                      |

**下一步**：`4-convert_poses.py` — 将 `poses.json` 转为 COLMAP `transforms.json` 格式，供 3DGS 训练使用。

---

## 七、实测踩坑记录（2026-03-10）

### 坑 1：simPause 导致 UE5 永久卡死
- **现象**：脚本一启动，UE5 画面立即冻结，Python 侧无输出
- **根因**：`simPause(True)` 暂停物理引擎后，某个 API 调用挂起，`simPause(False)` 永远不被执行
- **处理**：暂时注释掉 `simPause`，先跑通采集流程；重新启用前需排查挂起原因
- **注意**：无 simPause 时各传感器数据时间戳不严格对齐，但对 pipeline 验证无影响

### 坑 2：缺少 `armDisarm(True)` 导致控制指令无效
- **现象**：`enableApiControl(True)` 之后发送控制指令，船不动
- **根因**：`armDisarm(True)` 是激活推进器的必要步骤，漏掉了
- **修复**：在 `enableApiControl` 之后立即调用 `client.armDisarm(True, VESSEL_NAME)`

### 坑 3：RGB 图像倒置
- **现象**：rgb/ 目录下的图像上下颠倒（水面在上，天空在下）
- **根因**：标准 AirSim 图像需要 `flipud` 修正，但 **CosysAirSim v3.0.1 已修复该 bug**，不需要 `flipud`；加了反而倒置
- **实证**：seg 图（未加 `flipud`）方向正确；rgb 图（加了 `flipud`）倒置 → 去掉即可
- **修复**：删除所有 `np.flipud()` 调用

### 坑 4：两次 simGetImages 导致采集过慢
- **现象**：每帧耗时远超预期（原 `MOVE_SECONDS=1.0` + 两次 RPC ≈ 3s/帧）
- **根因**：front_camera 和 down_camera 分两次调用 `simGetImages`，每次都是独立 RPC 往返
- **修复**：将两次合并为一次，在同一个列表内混合不同相机索引，同时将 `MOVE_SECONDS` 从 1.0 降至 0.3

### 坑 5：`finally` 块仅含注释语法报错
- **现象**：`IndentationError: expected an indented block after 'finally' statement`
- **根因**：Python 不把注释视为语句，空 `finally` 块非法
- **修复**：加 `pass` 占位

### 坑 6：UE5 Lumen 导致每帧采集耗时数分钟（重大性能坑）
- **现象**：合并 RPC 调用 + `MOVE_SECONDS=0.3` 之后，每帧仍需数分钟才能完成
- **根因排查来源**：官方文档 image_apis 页面（Performance Notes 节）明确指出：
  > *"Lumen uses scene capture components and can be costly on performance."*
  - UE5 Lumen GI（全局光照）和 Lumen Reflections 默认对每个 SceneCapture 组件生效
  - `simGetImages` 底层触发 UE5 SceneCapture，每次渲染需要跑完整的 Lumen GI pass
  - 1280×720 分辨率 × 3 种图像类型 = 3 个 Lumen 渲染 pass，每 pass 在中端 GPU 上约 10~60 秒
- **settings.json 中的根因**：`CaptureSettings` 里没有显式禁用 Lumen，UE5 默认启用

```json
// 修复前（Lumen 默认开启）
{ "ImageType": 0, "Width": 1280, "Height": 720, "FOV_Degrees": 90 }

// 修复后（显式关闭 Lumen GI + Reflections）
{
  "ImageType": 0, "Width": 1280, "Height": 720, "FOV_Degrees": 90,
  "LumenGIEnable": false, "LumenReflectionEnable": false,
  "MotionBlurAmount": 0
}
```

- **修复**：在 `~/Documents/AirSim/settings.json` 的三个 `CaptureSettings` 条目（ImageType 0/1/5）中均加入 Lumen 禁用标志；**修复后需重启 UE5 + ASVSim 使配置生效**
- **预期效果**：每帧耗时从数分钟 → 约 1~3 秒

### 坑 7：down_camera 渲染未保存导致多余 render pass
- **现象**：`collect_one_frame` 请求了 down_camera (`ImageType.Scene`)，但 `save_frame` 完全没有写入该图像
- **根因**：down_camera RGB 被添加进 `simGetImages` 列表后，代码只是解码了变量 `img_down_bgr`，既没有独立目录也没有在 `save_frame` 里落盘
- **影响**：强迫 UE5 多渲染一个 1280×720 SceneCapture，然后丢弃结果，纯粹浪费时间
- **修复**：从 `simGetImages` 请求列表中移除 `DOWN_CAM_IDX` 条目，同时删除解码和返回字典中的 `down_rgb` 字段
- **后续**：若需要 down_camera 数据用于 3DGS 多视角采集，需完整实现：①再加回请求 ②在 `save_frame` 里建立 `rgb_down/` 子目录并写入

---

## 八、性能调优汇总（2026-03-10 官方文档研究后）

**来源**：ASVSim image_apis 官方文档（Lumen 节）+ AirSim readthedocs（Performance Tips 节）

| 优化项 | 状态 | 说明 |
| --- | --- | --- |
| 所有图像类型合并为一次 `simGetImages` | ✅ 已完成 | 减少 RPC 往返 |
| `compress=False`（RGB/Seg 使用非压缩 uint8） | ✅ 已完成 | 不需 PNG 解码，NumPy 直接 reshape |
| `pixels_as_float=True`（Depth 返回 float32 列表） | ✅ 已完成 | 直接转 NumPy，无需额外转换 |
| `MOVE_SECONDS` 缩短至 0.3 | ✅ 已完成 | 减少等待时间 |
| **禁用 Lumen GI/Reflections** | ✅ 已完成（需重启 UE5） | **主要性能瓶颈**，settings.json 已改 |
| **移除未保存的 down_camera 渲染** | ✅ 已完成 | 消除无效 render pass |
| 降低分辨率（可选） | ⬜ 未做 | 640×360 比 1280×720 快 4 倍，pipeline 验证阶段够用 |
| 减少采集图像类型数（可选） | ⬜ 未做 | 如只需 RGB+Depth 可去掉 Seg，再省 1 pass |

**关键结论**：在 ASVSim/UE5 环境下，`simGetImages` 慢的根因几乎都是 Lumen 渲染，而非网络/Python 层。优先在 `settings.json` 里关 Lumen，比任何代码层优化都有效。

---

*记录更新于 2026-03-10（Lumen 性能排查 + 修复后补充）*
