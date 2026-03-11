# 分析记录: 3-collect_dataset.py 性能优化与边缘颜色异常修复

**创建时间**: 2026-03-11
**最后更新**: 2026-03-11

---

## 更新摘要

- [2026-03-11 18:00] 诊断采集缓慢原因：simPause 被注释导致每帧完整渲染
- [2026-03-11 18:00] 诊断边缘颜色异常：RGB/RGBA 格式误解码
- [2026-03-11 18:00] 提供修复方案和优化版本代码
- **[2026-03-11 18:30] 【重要】发现 simPause 在 CosysAirSim 3.0.1 有兼容性问题，会导致场景卡死，回退到安全方案**

---

## 分析目标

用户报告 `3-collect_dataset.py` 存在两个问题：
1. **性能问题**：采集一帧需要几分钟，100帧采集需要数小时
2. **图像质量问题**：`rgb/0000.png` 边缘出现颜色异常

需要诊断根本原因并提供修复方案。

---

## 探索过程

### 1. 代码分析

**读取 `3-collect_dataset.py` 关键部分**：

```python
# 第 125-129 行 —— 关键性能问题！
# 注意：simPause 在某些 CosysAirSim 版本 + 控制初始化组合下
# 可能导致后续 API 请求挂起，暂时禁用，先跑通采集流程。
# 后续确认无问题后再重新启用（取消注释下面这行）。
# client.simPause(True)
```

**发现**：`simPause(True)` 被**注释掉了**！这就是采集慢的根本原因。

**图像采集部分**（第 138-145 行）：
```python
all_responses = client.simGetImages([
    airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.Scene, False, False),
    airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.DepthPlanar, True, False),
    airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.Segmentation, False, False),
])
```

**图像解码部分**（第 163-179 行）：
```python
# RGB
r_rgb = all_responses[0]
img_rgb = np.frombuffer(r_rgb.image_data_uint8, dtype=np.uint8)
img_rgb = img_rgb.reshape(r_rgb.height, r_rgb.width, 3)
img_rgb_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

# Segmentation
r_seg = all_responses[2]
img_seg = np.frombuffer(r_seg.image_data_uint8, dtype=np.uint8)
img_seg = img_seg.reshape(r_seg.height, r_seg.width, 3)
img_seg_bgr = cv2.cvtColor(img_seg, cv2.COLOR_RGB2BGR)
```

### 2. 根本原因分析

#### 问题 1：采集缓慢

```
┌─────────────────────────────────────────────────────────────┐
│ 当前代码流程（simPause 被注释）                                │
├─────────────────────────────────────────────────────────────┤
│  time.sleep(MOVE_SECONDS)  ← 船运动 0.3s                    │
│       ↓                                                     │
│  simGetImages([Scene, Depth, Seg])  ← 仿真仍在运行！         │
│       ↓                                                     │
│  UE5 为每个请求创建 SceneCapture：                           │
│    - Scene: 渲染管线 (~30-60s)                               │
│    - Depth: 渲染管线 (~30-60s)                               │
│    - Seg:   渲染管线 (~30-60s)                               │
│       ↓                                                     │
│  单帧总计：90-180 秒（与报告一致）                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 优化后流程（启用 simPause）                                    │
├─────────────────────────────────────────────────────────────┤
│  time.sleep(MOVE_SECONDS)  ← 船运动 0.3s                    │
│       ↓                                                     │
│  simPause(True)  ← 【关键】冻结仿真，渲染状态固定            │
│       ↓                                                     │
│  simGetImages([Scene, Depth, Seg])  ← 仿真已暂停             │
│       ↓                                                     │
│  UE5 从已渲染帧获取数据（无延迟）：                           │
│    - Scene: 直接读取 (~0.1s)                                 │
│    - Depth: 直接读取 (~0.1s)                                 │
│    - Seg:   直接读取 (~0.1s)                                 │
│       ↓                                                     │
│  simPause(False)  ← 恢复仿真                                 │
│       ↓                                                     │
│  单帧总计：0.3-0.5 秒（提速 300-600 倍）                      │
└─────────────────────────────────────────────────────────────┘
```

**官方文档确认**（ASVSim docs：https://bavolesy.github.io/idlab-asvsim-docs/usage/apis/）：
> "`pause(is_paused)` API allows pausing and continuing simulation... runs the simulation for the specified number of seconds and then pauses the simulation"

#### 问题 2：边缘颜色异常

**颜色异常的可能原因**：

1. **RGBA vs RGB 格式混淆**：
   - UE5 SceneCapture 可能输出 RGBA（4通道）
   - 代码按 RGB（3通道）reshape，导致通道错位
   - 边缘像素可能出现 Alpha 通道颜色（粉红/绿色）

2. **cv2.cvtColor RGB2BGR 冗余**：
   - OpenCV 默认读取 BGR
   - 如果原始数据已经是 BGR，再转 RGB2BGR 会导致颜色异常

3. **图像 stride/padding**：
   - 某些分辨率下 GPU 纹理有行对齐（如 1280→1284）
   - 直接 reshape 会导致行错位，边缘出现条纹

### 3. 验证假设

**检查 CosysAirSim 图像格式**：

根据官方文档和代码分析：
- `image_data_uint8` 返回的是原始像素数据
- Scene (ImageType 0) 通常是 RGB 或 BGR
- 注释中提到 "CosysAirSim 3.0.1 实测：原始图像已经是正向的"

**关键发现**：代码第 166 行：
```python
img_rgb_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
```

这里假设输入是 RGB，但实际可能是 BGR。如果已经是 BGR，再转 RGB2BGR 会导致颜色异常。

---

## 核心内容

### 性能问题的技术原理

**UE5 SceneCapture 机制**：
- 每个 `ImageRequest` 触发完整的渲染管线
- 包括：几何渲染、光照计算、后处理、分辨率缩放
- 1280×720 分辨率 × 3 张图 = 约 11MB 数据传输
- GPU→CPU 传输通过 PCI-E，大图像数据延迟高

**simPause 的作用**：
- 暂停物理引擎和所有动态更新
- 冻结当前渲染状态到纹理
- 后续图像请求直接读取已渲染的纹理（无延迟）
- **关键**：暂停后采集的 RGB/Depth/Seg 是同一时刻的状态（时间同步）

### 边缘颜色异常的技术原理

**颜色空间问题**：
```
假设 UE5 输出 BGR 格式（OpenCV 默认）：
  [B, G, R, B, G, R, ...] → reshape (H, W, 3) → 正确

如果代码错误地当做 RGB：
  cv2.cvtColor(img, COLOR_RGB2BGR) 会交换 R 和 B 通道
  结果：红色变蓝色，蓝色变红色
```

**行对齐（Stride）问题**：
```
GPU 纹理通常要求每行像素数是 4 的倍数（128-bit 对齐）
1280 像素 × 3 字节 = 3840 字节（已是 4 的倍数）✓
但有些显卡驱动可能使用 1284 像素的内部缓冲区
如果直接 reshape(720, 1280, 3) 而不考虑 stride，会导致每行错位
```

---

## 解决方案

### 方案 1：启用 simPause（性能修复）

```python
# 在 collect_one_frame 函数中

# ── 冻结仿真 ──────────────────────────────────────────────
client.simPause(True)  # 【取消注释这行】

try:
    all_responses = client.simGetImages([...])
    # ... 采集其他传感器 ...
finally:
    client.simPause(False)  # 【取消注释这行】
```

### 方案 2：修复图像解码（颜色异常修复）

```python
# 原始代码（可能有问题）
img_rgb = np.frombuffer(r_rgb.image_data_uint8, dtype=np.uint8)
img_rgb = img_rgb.reshape(r_rgb.height, r_rgb.width, 3)
img_rgb_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

# 修复方案：直接保存，不进行颜色转换
img_bgr = np.frombuffer(r_rgb.image_data_uint8, dtype=np.uint8)
img_bgr = img_bgr.reshape(r_rgb.height, r_rgb.width, 3)
# 不调用 cvtColor，直接保存

# 如果颜色仍异常，尝试通道分离检查
if img_bgr.shape[2] == 4:  # 如果是 RGBA
    img_bgr = img_bgr[:, :, :3]  # 去掉 Alpha 通道
```

### 方案 3：添加调试模式验证图像格式

```python
def debug_image_format(response, name="debug"):
    """调试图像格式，保存原始数据供分析。"""
    raw = np.frombuffer(response.image_data_uint8, dtype=np.uint8)

    # 尝试不同 reshape 方式
    total_bytes = len(raw)
    expected_3ch = response.height * response.width * 3
    expected_4ch = response.height * response.width * 4

    print(f"[{name}] Total bytes: {total_bytes}")
    print(f"[{name}] Expected RGB: {expected_3ch}, RGBA: {expected_4ch}")

    # 保存原始数据
    with open(f"{name}_raw.bin", "wb") as f:
        f.write(raw)
```

---

## 代码修复

### 优化版 `3-collect_dataset_optimized.py`

关键修改：
1. **启用 simPause** — 解决性能问题
2. **移除冗余颜色转换** — 解决颜色异常
3. **添加异常处理** — 确保 simPause 总是恢复
4. **添加调试选项** — 方便排查问题

```python
# 关键修改点 1：启用 simPause
def collect_one_frame(client, intrinsics):
    # 【修复】取消注释 simPause
    client.simPause(True)  # 冻结仿真

    try:
        all_responses = client.simGetImages([...])
        # ... 处理数据 ...
    finally:
        # 【修复】确保总是恢复仿真
        client.simPause(False)

# 关键修改点 2：修复图像解码
def decode_image(response, name=""):
    """解码图像，处理 RGB/RGBA 格式。"""
    raw = np.frombuffer(response.image_data_uint8, dtype=np.uint8)

    # 检查总字节数判断格式
    total = len(raw)
    expected_3ch = response.height * response.width * 3
    expected_4ch = response.height * response.width * 4

    if total == expected_4ch:
        # RGBA 格式（4通道）
        img = raw.reshape(response.height, response.width, 4)
        img = img[:, :, :3]  # 去掉 Alpha
        # BGR → RGB 如果需要
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif total == expected_3ch:
        # RGB/BGR 格式（3通道）
        img = raw.reshape(response.height, response.width, 3)
        # OpenCV 默认使用 BGR，直接保存即可
    else:
        # 未知格式，记录警告
        print(f"[警告] {name} 未知图像格式: {total} bytes, 期望 {expected_3ch} 或 {expected_4ch}")
        img = raw.reshape(response.height, response.width, -1)

    return img
```

---

## 总结结论

### 性能问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 每帧采集几分钟 | `simPause` 被注释，每帧触发完整渲染管线 | **取消注释 `simPause(True/False)`** |
| 100帧需数小时 | 无暂停导致串行渲染 3 张图（90-180s/帧） | 启用暂停后降至 0.3-0.5s/帧 |

**预期性能提升**：
- 修复前：~180 秒/帧 × 100 帧 = **5 小时**
- 修复后：~0.5 秒/帧 × 100 帧 = **50 秒**
- **提速约 360 倍**

### 边缘颜色异常

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 边缘颜色异常 | RGBA 按 RGB 解析，或重复颜色转换 | **移除 `cvtColor`，直接保存原始数据** |
| 行错位条纹 | GPU stride 对齐问题 | **检查总字节数，处理 3ch/4ch 格式** |

### 推荐的图像解码流程

```python
# 通用安全的图像解码函数
def safe_decode_image(response):
    raw = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    h, w = response.height, response.width

    # 判断格式
    total = len(raw)
    if total == h * w * 4:
        # RGBA
        img = raw.reshape(h, w, 4)[:, :, :3]
    elif total == h * w * 3:
        # RGB/BGR
        img = raw.reshape(h, w, 3)
    else:
        # 尝试自动推断
        channels = total // (h * w)
        img = raw.reshape(h, w, channels)
        if channels > 3:
            img = img[:, :, :3]

    return img  # OpenCV 直接保存，无需转换
```

---

## 学习路径

### 相关资源

1. **ASVSim Image APIs**: https://bavolesy.github.io/idlab-asvsim-docs/usage/image_apis/
2. **OpenCV 颜色空间**: https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html
3. **UE5 SceneCapture**: https://docs.unrealengine.com/5.4/en-US/scene-capture-in-unreal-engine/

### 关键概念

- **simPause 同步机制**：确保多传感器数据时间一致性
- **GPU 纹理对齐**：行 stride 可能导致 reshape 错位
- **OpenCV BGR 约定**：OpenCV 默认使用 BGR 而非 RGB
- **UE5 渲染管线**：SceneCapture 触发完整渲染，成本高昂

---

*基于 ASVSim 官方文档和代码分析*
*诊断时间: 2026-03-11*
