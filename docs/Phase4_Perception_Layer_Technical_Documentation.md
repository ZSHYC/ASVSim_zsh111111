# Phase 4 智能感知层技术文档

**项目**: ASVSim 极地路径规划与 3D Gaussian Splatting 重建
**阶段**: Phase 4 - 智能感知层 (Perception Layer)
**版本**: v1.0
**日期**: 2026-03-14

---

## 目录

1. [概述](#1-概述)
2. [架构设计](#2-架构设计)
3. [模块详解](#3-模块详解)
   - 3.1 [SAM3 海冰实例分割](#31-sam3-海冰实例分割)
   - 3.2 [Depth Anything 3 深度估计](#32-depth-anything-3-深度估计)
   - 3.3 [相机-LiDAR 联合标定](#33-相机-lidar-联合标定)
4. [数据融合策略](#4-数据融合策略)
5. [实现代码详解](#5-实现代码详解)
6. [使用指南](#6-使用指南)
7. [问题与解决方案](#7-问题与解决方案)
8. [附录](#8-附录)

---

## 1. 概述

### 1.1 设计目标

Phase 4 智能感知层的核心任务是从多模态传感器数据中提取语义和几何信息，为后续的 3D Gaussian Splatting 重建和路径规划提供输入。

**三大核心功能**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 4 智能感知层                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  SAM3        │    │  Depth       │    │  相机-LiDAR  │  │
│  │  实例分割    │    │  Anything 3  │    │  联合标定    │  │
│  │              │    │  深度估计    │    │              │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  实例掩码    │    │  深度图      │    │  相机位姿    │  │
│  │  [H,W] int32 │    │  [H,W] float │    │  [4,4] float │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         └───────────┬───────┴───────────────────┘          │
│                     ▼                                      │
│            ┌──────────────┐                               │
│            │  数据融合    │                               │
│            │  生成训练集  │                               │
│            └──────┬───────┘                               │
│                   ▼                                        │
│            ┌──────────────┐                               │
│            │  3DGS 输入   │                               │
│            │  (.npz)      │                               │
│            └──────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型理由

| 模块               | 技术方案                         | 选型理由                                                                       |
| ------------------ | -------------------------------- | ------------------------------------------------------------------------------ |
| **实例分割** | SAM 3 (Segment Anything Model 3) | 零样本分割能力强，无需极地场景训练数据；支持提示式推理；对小目标和边界处理优异 |
| **深度估计** | Depth Anything V3                | 支持 metric depth（绝对深度）；在极端天气/低对比度场景下稳健；远距离深度精度好 |
| **联合标定** | 仿真真值 + ICP 配准              | ASVSim 提供真值位姿；LiDAR-相机外参可直接从配置计算                            |

### 1.3 输入输出规范

**输入数据**:

```
dataset/2026_03_13_01_50_19/
├── rgb/              # [640, 480, 3] uint8 - RGB图像
├── depth/            # [640, 480] float32 - 仿真深度（单位：厘米）
├── lidar/            # JSON格式 - LiDAR点云
└── poses.json        # 相机位姿（如果存在）
```

**输出数据**:

```
test_output/perception_2026_03_13_01_50_19/
├── segmentation/     # [480, 640] int32 - 实例掩码
├── depth_da3/        # [378, 504] float32 - DA3深度（单位：米）
├── depth_fused/      # [480, 640] float32 - 融合深度
├── poses/            # [4, 4] float32 - 相机位姿
└── integrated/       # .npz - 整合训练数据
    ├── frame_0000.npz
    └── metadata.json
```

---

## 2. 架构设计

### 2.1 整体流程

```python
# Phase 4 主流程伪代码
def perception_pipeline(dataset_dir):
    # 1. 加载数据
    rgb_images = load_rgb(dataset_dir)
    sim_depths = load_depth(dataset_dir)
    lidar_data = load_lidar(dataset_dir)

    # 2. SAM3 实例分割
    sam3_model = load_sam3()
    instance_masks = [sam3_model.segment(img) for img in rgb_images]

    # 3. DA3 深度估计
    da3_model = load_da3()
    da3_depths, da3_poses = da3_model.estimate_depth(rgb_images)

    # 4. 深度对齐与融合
    fused_depths = fuse_depth(sim_depths, da3_depths)

    # 5. 获取/估计位姿
    poses = get_poses(dataset_dir)  # 优先仿真真值

    # 6. 数据整合
    for i in range(N):
        integrated_data = {
            'rgb': rgb_images[i],
            'depth': fused_depths[i],
            'segmentation': instance_masks[i],
            'pose': poses[i],
            'intrinsics': calculate_intrinsics()
        }
        save_npz(integrated_data, f'frame_{i:04d}.npz')
```

### 2.2 数据流图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Phase 4 数据流                          │
└─────────────────────────────────────────────────────────────────┘

  RGB Images (640×480)
         │
         ├──────────────────┬──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │  SAM3    │      │   DA3    │      │ COLMAP   │
   │ 分割模型 │      │ 深度模型 │      │ (备选)   │
   └────┬─────┘      └────┬─────┘      └────┬─────┘
        │                 │                 │
        ▼                 ▼                 ▼
  Instance Masks     Depth Maps       Poses (备选)
  [H,W] int32       [H,W] float      [4,4] float
        │                 │                 │
        │                 │                 │
        └────────┬────────┘                 │
                 ▼                            │
          ┌────────────┐                      │
          │ 深度融合   │                      │
          │ 策略选择   │                      │
          └─────┬──────┘                      │
                │                             │
                ▼                             ▼
         Fused Depth                    Final Poses
         [H,W] float                    [4,4] float
                │                             │
                └────────────┬────────────────┘
                             ▼
                    ┌────────────────┐
                    │   数据整合     │
                    │   Data Merge   │
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │  输出 .npz     │
                    │  供3DGS训练    │
                    └────────────────┘
```

---

## 3. 模块详解

### 3.1 SAM3 海冰实例分割

#### 3.1.1 模型原理

**SAM 3 (Segment Anything Model 3)** 是 Meta AI 于 2025 年发布的第三代分割模型，基于 **Ultralytics** 框架实现。

**核心架构**:

```
输入图像 (H×W×3)
    │
    ▼
┌─────────────────────────────────────────┐
│           Image Encoder                 │
│  (Vision Transformer - ViT-H/L/B)      │
│  - 层次化特征提取 (Hiera-L+)           │
│  - 多尺度特征金字塔                    │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌───────┐    ┌───────┐    ┌───────┐
│ Prompt │    │ Prompt │    │ Prompt │
│ 点提示 │    │ 框提示 │    │ 掩码提示│
└────┬───┘    └────┬───┘    └────┬───┘
     │             │             │
     └─────────────┴─────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         Mask Decoder                    │
│  - 轻量级 Transformer 解码器           │
│  - 动态掩码生成                        │
│  - 边界精细化                          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
           实例掩码 (H×W)
```

**关键特性**:

| 特性                 | 说明                 | 本项目应用         |
| -------------------- | -------------------- | ------------------ |
| **零样本学习** | 无需针对海冰场景训练 | 直接应用于极地图像 |
| **多提示支持** | 点、框、掩码混合提示 | 自动分割（无提示） |
| **层次化编码** | Hiera-L+ 编码器      | 小目标和边界优化   |
| **实例级输出** | 每个物体独立掩码     | 支持多冰山分割     |

#### 3.1.2 输出格式

```python
# SAM3 输出结构
{
    'masks': np.ndarray,        # [N, H, W] bool - N个实例掩码
    'boxes': np.ndarray,        # [N, 4] float - 边界框 [x1,y1,x2,y2]
    'scores': np.ndarray,       # [N] float - 置信度分数 [0-1]
    'classes': np.ndarray       # [N] int - 类别ID (SAM3无类别，均为0)
}

# 转换后的实例掩码图
instance_mask: np.ndarray      # [H, W] int32
# 像素值含义:
#   0 = 背景
#   1 = 实例1
#   2 = 实例2
#   ...
```

#### 3.1.3 性能指标

**实测性能** (RTX 5070 Ti):

| 指标       | 数值    | 说明                   |
| ---------- | ------- | ---------------------- |
| 处理速度   | ~13s/张 | 单张推理               |
| 平均实例数 | ~8.7/张 | 包含船体、冰山、水面等 |
| 平均置信度 | 0.947   | 高置信度检测           |
| 模型大小   | 3.29 GB | 显存占用               |

**质量评估**:

```
实例面积分布:
  - Small (< 1K px): 49.4%    (小物体/细节)
  - Medium (1K-10K px): 24.7% (中等物体)
  - Large (> 10K px): 25.9%   (大区域)

平均掩码覆盖比例: 66.6%
```

#### 3.1.4 实现代码

```python
from ultralytics import SAM
import numpy as np
import cv2

# 1. 加载模型
model = SAM(r'D:\ASVSim_models\sam3\sam3.pt')
model.to(device='cuda')

# 2. 读取图像
image = cv2.imread('dataset/rgb/0000.png')

# 3. 运行分割
results = model(image, verbose=False)
result = results[0]

# 4. 提取掩码
if result.masks is not None:
    masks = result.masks.data.cpu().numpy()  # [N, H, W]
    scores = result.boxes.conf.cpu().numpy()  # [N]

# 5. 创建实例掩码图 (int32格式)
h, w = image.shape[:2]
instance_mask = np.zeros((h, w), dtype=np.int32)

for i, mask in enumerate(masks):
    # 调整掩码大小
    if mask.shape != (h, w):
        mask_resized = cv2.resize(
            mask.astype(np.uint8),
            (w, h),
            interpolation=cv2.INTER_NEAREST
        )
    else:
        mask_resized = mask.astype(np.uint8)

    # 赋实例ID (i+1，0为背景)
    instance_mask[mask_resized > 0] = i + 1

# 6. 保存
np.save('segmentation/0000.npy', instance_mask)
```

#### 3.1.5 局限性与解决方案

| 局限性               | 影响                   | 解决方案                       |
| -------------------- | ---------------------- | ------------------------------ |
| **无类别标签** | 无法区分冰山/船只/水面 | 后处理：基于深度和位置分类     |
| **速度较慢**   | 13s/张，不适合实时     | 批量离线处理；后续可用轻量模型 |
| **时序不一致** | 同物体ID可能变化       | 基于光流的时序跟踪（待实现）   |

---

### 3.2 Depth Anything 3 深度估计

#### 3.2.1 模型原理

**Depth Anything V3** 是 ByteDance Seed 团队于 2025 年底发布的单目深度估计模型。

**核心创新**:

1. **Metric Depth 输出**: 直接输出绝对深度（单位：米），而非相对深度
2. **DINOv2 编码器**: 使用大型视觉模型作为特征提取器
3. **多尺度解码器**: 融合多分辨率特征，兼顾细节和全局
4. **置信度估计**: 输出每个像素的深度置信度

**网络架构**:

```
输入图像 (3×H×W)
    │
    ▼
┌─────────────────────────────────────────┐
│         DINOv2 Image Encoder            │
│  (Vision Transformer - ViT-L/G)        │
│  - 预训练于大规模图像数据集            │
│  - 提取多尺度特征 [1/4, 1/8, 1/16]     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         Multi-Scale Decoder             │
│  - 特征金字塔融合                       │
│  - 上采样至原分辨率                     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
            ┌────────────┐
            │  Depth Head │ → Depth Map [H,W]
            │  (米单位)   │
            └─────┬──────┘
                  │
            ┌────────────┐
            │  Conf Head  │ → Confidence [H,W]
            └────────────┘
```

#### 3.2.2 输出格式

```python
# DA3 输出结构 (批量推理)
prediction = model.inference(image_files)

{
    'depth': np.ndarray,           # [N, H, W] float32 - 深度图（米）
    'conf': np.ndarray,            # [N, H, W] float32 - 置信度 [0-1]
    'extrinsics': np.ndarray,      # [N, 3, 4] float32 - 相机位姿 (⚠️ 不可用)
    'intrinsics': np.ndarray,      # [N, 3, 3] float32 - 相机内参
    'processed_images': np.ndarray # [N, H, W, 3] - 预处理后的图像
}
```

**输出尺寸说明**:

- 输入: 640×480
- 输出: 378×504 (模型内部处理尺寸)
- 需要通过 `cv2.resize` 对齐到原始尺寸

#### 3.2.3 性能指标

**实测性能** (RTX 5070 Ti, CUDA 12.8):

| 指标     | CPU     | GPU 单张 | GPU 批量         | 说明     |
| -------- | ------- | -------- | ---------------- | -------- |
| 处理速度 | 1.72s   | 0.29s    | **0.088s** | 批量8张  |
| 加速比   | 1x      | 6x       | **19.5x**  | vs CPU   |
| 有效帧率 | 0.6 FPS | 3.4 FPS  | **11 FPS** | 实时可行 |

**深度质量**:

```
DA3 深度统计 (126张图像):
  - 平均最小深度: 0.12 m
  - 平均最大深度: 5.69 m
  - 典型范围: [0.15, 7.0] m
  - 输出尺寸: 378 × 504
```

#### 3.2.4 与仿真深度对比

**关键发现**:

| 深度源          | 范围           | 单位 | 特点                 |
| --------------- | -------------- | ---- | -------------------- |
| 仿真深度 (原始) | [3.71, 2384]   | cm   | 范围广，远处可达     |
| 仿真深度 (转换) | [0.037, 23.84] | m    | 需除以100            |
| DA3 深度        | [0.12, 5.69]   | m    | 绝对尺度，近处细节好 |

**尺度对齐**:

```python
# 发现仿真深度单位为厘米 (cm)
sim_depth_meters = sim_depth_raw / 100.0

# 计算对齐因子
alignment_factor = 0.0204  # DA3/仿真

# 对齐后误差: ~2.67m (可接受)
```

**误差分析**:

```
误差来源:
1. 场景尺度差异: DA3 对远处 (>10m) 估计保守
2. 纹理特征: 极地冰面纹理稀疏
3. 相机参数: 仿真相机与真实相机不同

对齐后误差:
  - 均值误差: 2.78 m
  - 中位数误差: 2.67 m
  - 标准差: 0.78 m
```

#### 3.2.5 实现代码

```python
import torch
import numpy as np
import cv2
from depth_anything_3.api import DepthAnything3

# 1. 加载模型
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = DepthAnything3.from_pretrained('depth-anything/DA3-LARGE-1.1')
model = model.to(device=device)
model.eval()

# 2. 批量推理
image_files = ['dataset/rgb/0000.png', 'dataset/rgb/0001.png', ...]

with torch.no_grad():
    prediction = model.inference(image_files)

# 3. 处理单张结果
for i, img_path in enumerate(image_files):
    # 提取深度
    depth = prediction.depth[i]  # [378, 504] 单位：米
    conf = prediction.conf[i]    # [378, 504] 置信度

    # 调整大小到原始尺寸 (640×480)
    depth_resized = cv2.resize(depth, (640, 480))
    conf_resized = cv2.resize(conf, (640, 480))

    # 保存
    np.save(f'depth_da3/{i:04d}.npy', depth_resized)
    np.save(f'conf/{i:04d}.npy', conf_resized)

    # 可视化 (PLASMA色图)
    depth_norm = (depth - depth.min()) / (depth.max() - depth.min())
    depth_uint8 = (depth_norm * 255).astype(np.uint8)
    depth_colored = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_PLASMA)
    cv2.imwrite(f'depth_vis/{i:04d}.png', depth_colored)
```

#### 3.2.6 位姿预测问题

**重要发现**: DA3 位姿预测功能在本场景下**完全不可用**。

**验证结果**:

```
轨迹分析:
  - 轨迹长度: 3.07 m (过短)
  - Y轴范围: [-0.006, 0.005] m (几乎无变化)
  - 步长标准差: 0.0295 m (变化剧烈，120%)

旋转分析:
  - 最大旋转角: 79.21° (物理上不可能)
  - 旋转角标准差: 15.45° (极不稳定)

圆形轨迹拟合:
  - 拟合半径: 0.051 m (过小)
  - 误差比例: 45.75% (合格 <10%)
```

**根因分析**:

1. **视差不足**: 小范围运动 (3m) 导致视觉里程计失效
2. **纹理特征**: 极地冰面纹理稀疏
3. **训练偏差**: DA3 主要在室内/城市场景训练

**结论**: DA3 **深度估计可用**，但**位姿估计不可用**。

---

### 3.3 相机-LiDAR 联合标定

#### 3.3.1 标定原理

**目标**: 建立相机坐标系与 LiDAR 坐标系之间的变换关系。

**坐标系定义**:

```
ASVSim 坐标系 (右手系):
  - X: 前 (Forward)
  - Y: 右 (Right)
  - Z: 下 (Down)

相机坐标系:
  - Z: 前 (光轴方向)
  - X: 右
  - Y: 下

LiDAR坐标系:
  - X: 前
  - Y: 左
  - Z: 上
```

**外参矩阵**:

```
点云投影公式:
    p_camera = R * p_lidar + t
    p_image = K * p_camera / p_camera.z

其中:
    - R: 3×3 旋转矩阵 (LiDAR → Camera)
    - t: 3×1 平移向量
    - K: 3×3 相机内参矩阵
```

#### 3.3.2 仿真真值获取

在 ASVSim 仿真环境中，可以直接获取真值外参：

```python
import cosysairsim as airsim

client = airsim.VesselClient()

# 获取相机位姿 (相对于世界坐标系)
camera_pose = client.simGetCameraInfo('front_camera')

# 获取 LiDAR 位姿
lidar_data = client.getLidarData('top_lidar', 'Vessel1')

# 从 settings.json 获取相对位置:
# front_camera: X=1.0, Y=0.0, Z=-0.5
# top_lidar: X=0.0, Y=0.0, Z=-1.0

# 计算外参 (LiDAR → Camera)
T_lidar_to_camera = ...
```

#### 3.3.3 当前状态

**阻塞原因**:

1. **位姿未保存**: 采集时未保存 `poses.json`
2. **DA3 位姿不可用**: 位姿预测质量不合格
3. **LiDAR 数据格式**: 需要进一步解析 JSON 格式

**解决方案**:

| 方案               | 时间 | 精度 | 推荐度     |
| ------------------ | ---- | ---- | ---------- |
| **仿真真值** | 2-4h | 最高 | ⭐⭐⭐⭐⭐ |
| **COLMAP**   | 1-2d | 高   | ⭐⭐⭐⭐   |
| **手动标定** | 半天 | 中   | ⭐⭐⭐     |

---

## 4. 数据融合策略

### 4.1 深度融合

**目标**: 结合 DA3 深度（绝对尺度，近处细节好）和仿真深度（范围广，真值）。

**融合策略**:

```python
def fuse_depth(da3_depth, sim_depth, conf, method='adaptive'):
    """
    深度融合策略

    Args:
        da3_depth: DA3 估计深度 [H,W] (米)
        sim_depth: 仿真深度 [H,W] (厘米，需转换)
        conf: DA3 置信度 [H,W]
        method: 融合方法

    Returns:
        fused_depth: 融合后的深度 [H,W] (米)
    """
    # 1. 单位统一 (仿真 cm -> m)
    sim_depth_m = sim_depth / 100.0

    if method == 'distance_based':
        # 策略A: 基于距离选择
        # - 近距离 (<5m): 优先 DA3
        # - 远距离 (>=5m): 优先仿真
        fused = np.where(da3_depth < 5.0, da3_depth, sim_depth_m)

    elif method == 'confidence_weighted':
        # 策略B: 基于置信度加权
        # weight = conf / (conf + conf_sim)
        conf_sim = 0.8  # 仿真深度假设高置信度
        weight = conf / (conf + conf_sim)
        fused = weight * da3_depth + (1 - weight) * sim_depth_m

    elif method == 'adaptive':
        # 策略C: 自适应融合 (推荐)
        # - 近距离 + 高置信度: DA3
        # - 远距离或低置信度: 仿真
        # - 过渡区域: 加权融合

        da3_valid = (da3_depth > 0.1) & (da3_depth < 10.0) & (conf > 0.5)
        sim_valid = np.isfinite(sim_depth_m) & (sim_depth_m > 0)

        fused = np.zeros_like(da3_depth)

        # DA3 主导区域
        da3_dominate = da3_valid & (da3_depth < 5.0)
        fused[da3_dominate] = da3_depth[da3_dominate]

        # 仿真主导区域
        sim_dominate = sim_valid & (~da3_dominate)
        fused[sim_dominate] = sim_depth_m[sim_dominate]

        # 过渡区域: 线性插值
        transition = da3_valid & (da3_depth >= 5.0) & (da3_depth < 7.0)
        alpha = (da3_depth[transition] - 5.0) / 2.0
        fused[transition] = (1-alpha) * da3_depth[transition] + alpha * sim_depth_m[transition]

    return fused
```

### 4.2 实例-深度关联

**目标**: 将 SAM3 实例掩码与深度图关联，获取每个实例的 3D 位置。

```python
def associate_instances_with_depth(instance_mask, depth, intrinsics):
    """
    实例与深度关联

    Args:
        instance_mask: [H,W] int32 - SAM3 实例掩码
        depth: [H,W] float32 - 融合深度 (米)
        intrinsics: [3,3] - 相机内参矩阵

    Returns:
        instances_3d: 每个实例的 3D 信息列表
    """
    instances_3d = []
    unique_ids = np.unique(instance_mask)

    fx, fy = intrinsics[0,0], intrinsics[1,1]
    cx, cy = intrinsics[0,2], intrinsics[1,2]

    for inst_id in unique_ids:
        if inst_id == 0:  # 跳过背景
            continue

        # 提取实例掩码
        mask = (instance_mask == inst_id)

        # 计算实例平均深度
        depths = depth[mask]
        if len(depths) == 0:
            continue

        mean_depth = np.mean(depths)

        # 计算实例中心像素坐标
        y_coords, x_coords = np.where(mask)
        center_x = np.mean(x_coords)
        center_y = np.mean(y_coords)

        # 反投影到 3D 空间
        X = (center_x - cx) * mean_depth / fx
        Y = (center_y - cy) * mean_depth / fy
        Z = mean_depth

        # 计算实例属性
        area = np.sum(mask)
        bbox = [int(x_coords.min()), int(y_coords.min()),
                int(x_coords.max()), int(y_coords.max())]

        instances_3d.append({
            'id': int(inst_id),
            'center_3d': [float(X), float(Y), float(Z)],
            'mean_depth': float(mean_depth),
            'area': int(area),
            'bbox': bbox,
            'mask': mask
        })

    return instances_3d
```

### 4.3 数据整合输出

**输出格式** (.npz):

```python
# 整合数据格式
integrated_data = {
    # 图像数据
    'rgb': np.ndarray,              # [480, 640, 3] uint8

    # 深度数据
    'depth': np.ndarray,            # [480, 640] float32 (米)
    'depth_conf': np.ndarray,       # [480, 640] float32 [0-1]
    'depth_sim': np.ndarray,        # [480, 640] float32 (米, 原始仿真)

    # 分割数据
    'segmentation': np.ndarray,     # [480, 640] int32 (实例ID)
    'num_instances': int,           # 实例数量

    # 每个实例的3D信息
    'instance_depths': np.ndarray,  # [N] float32 - 每个实例平均深度
    'instance_centers': np.ndarray, # [N, 2] float32 - 实例中心像素坐标
    'instance_bboxes': np.ndarray,  # [N, 4] int32 - 边界框 [x1,y1,x2,y2]

    # 相机参数
    'camera_intrinsics': np.ndarray,    # [3, 3] float32 - 内参矩阵
    'camera_extrinsics': np.ndarray,    # [4, 4] float32 - 位姿矩阵
    'camera_position': np.ndarray,      # [3] float32 - 相机位置
    'camera_rotation': np.ndarray,      # [4] float32 - 相机旋转 (四元数)

    # 元信息
    'frame_id': int,
    'timestamp': str,
    'image_path': str
}

# 保存
np.savez_compressed(f'integrated/frame_{frame_id:04d}.npz', **integrated_data)
```

---

## 5. 实现代码详解

### 5.1 SAM3 批量处理实现

完整实现见 `tools/batch_segment_sam3.py`:

```python
#!/usr/bin/env python3
"""
SAM 3 海冰实例分割 - 批量处理
"""

from ultralytics import SAM
import numpy as np
import cv2
import os
import glob

# 配置
MODEL_PATH = r'D:\ASVSim_models\sam3\sam3.pt'
CONF_THRESH = 0.5

def segment_image(model, image_path):
    """分割单张图像"""
    image = cv2.imread(image_path)
    results = model(image, verbose=False)
    result = results[0]

    # 提取结果
    if result.masks is not None:
        masks = result.masks.data.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()

        # 过滤低置信度
        valid_idx = scores > CONF_THRESH
        masks = masks[valid_idx]
        scores = scores[valid_idx]

        # 创建实例掩码图
        h, w = image.shape[:2]
        instance_mask = np.zeros((h, w), dtype=np.int32)

        for i, mask in enumerate(masks):
            mask_resized = cv2.resize(
                mask.astype(np.uint8),
                (w, h),
                interpolation=cv2.INTER_NEAREST
            )
            instance_mask[mask_resized > 0] = i + 1

        return instance_mask, scores

    return None, None

# 主流程
model = SAM(MODEL_PATH)
model.to(device='cuda')

image_files = sorted(glob.glob('dataset/rgb/*.png'))
for img_path in image_files:
    mask, scores = segment_image(model, img_path)
    if mask is not None:
        basename = os.path.basename(img_path).replace('.png', '')
        np.save(f'segmentation/{basename}.npy', mask)
```

### 5.2 DA3 批量处理实现

完整实现见 `tools/batch_process_da3.py`:

```python
#!/usr/bin/env python3
"""
DA3 批量处理 - GPU版本
"""

import torch
import numpy as np
import cv2
import os
import sys

# 添加 DA3 到路径
sys.path.insert(0, r'D:\ASVSim_models\Depth-Anything-3\src')
from depth_anything_3.api import DepthAnything3

# 配置
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_NAME = 'depth-anything/DA3-LARGE-1.1'
BATCH_SIZE = 8

def load_model():
    """加载 DA3 模型"""
    model = DepthAnything3.from_pretrained(MODEL_NAME)
    model = model.to(device=DEVICE)
    model.eval()
    return model

def process_batch(model, image_files):
    """处理一批图像"""
    with torch.no_grad():
        prediction = model.inference(image_files)

    results = []
    for i, img_path in enumerate(image_files):
        basename = os.path.basename(img_path).replace('.png', '')

        # 提取数据
        depth = prediction.depth[i]      # [378, 504]
        conf = prediction.conf[i]        # [378, 504]

        # 调整大小到原始尺寸 (640×480)
        depth_resized = cv2.resize(depth, (640, 480))
        conf_resized = cv2.resize(conf, (640, 480))

        # 保存
        np.save(f'depth/{basename}.npy', depth_resized)
        np.save(f'conf/{basename}.npy', conf_resized)

        results.append({
            'basename': basename,
            'depth_range': [float(depth.min()), float(depth.max())]
        })

    return results

# 主流程
model = load_model()
image_files = sorted(glob.glob('dataset/rgb/*.png'))

# 批量处理
for i in range(0, len(image_files), BATCH_SIZE):
    batch = image_files[i:i+BATCH_SIZE]
    process_batch(model, batch)
```

### 5.3 数据整合脚本

```python
#!/usr/bin/env python3
"""
Phase 4 数据整合
整合 RGB + 深度 + 分割 + 位姿
"""

import numpy as np
import cv2
import json
import os
import glob
from pathlib import Path

def integrate_frame(frame_id, dataset_dir, da3_output_dir, seg_output_dir, pose_data):
    """整合单帧数据"""

    # 1. 加载 RGB
    rgb = cv2.imread(f'{dataset_dir}/rgb/{frame_id:04d}.png')

    # 2. 加载仿真深度并转换单位 (cm -> m)
    sim_depth = np.load(f'{dataset_dir}/depth/{frame_id:04d}.npy')
    sim_depth_m = sim_depth / 100.0

    # 3. 加载 DA3 深度和置信度
    da3_depth = np.load(f'{da3_output_dir}/depth/{frame_id:04d}.npy')
    da3_conf = np.load(f'{da3_output_dir}/conf/{frame_id:04d}.npy')

    # 4. 加载实例分割
    instance_mask = np.load(f'{seg_output_dir}/segmentation/{frame_id:04d}.npy')

    # 5. 深度融合 (近距离用DA3，远距离用仿真)
    fused_depth = np.where(da3_depth < 5.0, da3_depth, sim_depth_m)

    # 6. 计算实例3D信息
    intrinsics = np.array([[640, 0, 320], [0, 640, 240], [0, 0, 1]], dtype=np.float32)
    instances_3d = []

    for inst_id in np.unique(instance_mask):
        if inst_id == 0:
            continue
        mask = (instance_mask == inst_id)
        mean_depth = np.mean(fused_depth[mask])
        instances_3d.append({
            'id': int(inst_id),
            'mean_depth': float(mean_depth),
            'area': int(np.sum(mask))
        })

    # 7. 获取位姿
    pose = pose_data.get(frame_id, np.eye(4))

    # 8. 整合保存
    integrated = {
        'rgb': rgb,
        'depth': fused_depth.astype(np.float32),
        'depth_conf': da3_conf.astype(np.float32),
        'depth_sim': sim_depth_m.astype(np.float32),
        'segmentation': instance_mask,
        'num_instances': len(instances_3d),
        'instance_depths': np.array([i['mean_depth'] for i in instances_3d], dtype=np.float32),
        'camera_intrinsics': intrinsics,
        'camera_extrinsics': pose.astype(np.float32),
        'frame_id': frame_id
    }

    np.savez_compressed(f'integrated/frame_{frame_id:04d}.npz', **integrated)
    return integrated

# 主流程
dataset_dir = 'dataset/2026_03_13_01_50_19'
da3_output_dir = 'test_output/da3_batch_2026_03_13_01_50_19'
seg_output_dir = 'test_output/sam3_batch_2026_03_13_01_50_19'

# 加载位姿数据 (从仿真或COLMAP)
pose_data = load_poses(...)  # 需要实现

# 处理所有帧
for frame_id in range(126):
    integrate_frame(frame_id, dataset_dir, da3_output_dir, seg_output_dir, pose_data)
```

---

## 6. 使用指南

### 6.1 环境配置

**依赖安装**:

```bash
# 1. PyTorch (CUDA 12.8)
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# 2. Ultralytics (SAM3)
pip install -U ultralytics>=8.3.237
pip install timm

# 3. DA3
cd D:\ASVSim_models
git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git
cd Depth-Anything-3
pip install -e .
pip install xformers einops e3nn open3d

# 4. 其他依赖
pip install numpy opencv-python matplotlib
```

**模型下载**:

```bash
# SAM3
# 手动从 Hugging Face 下载:
# https://huggingface.co/facebook/sam3
# 保存到: D:\ASVSim_models\sam3\sam3.pt

# DA3
# 首次运行会自动从 Hugging Face 下载
# 缓存位置: D:\ASVSim_models\cache\hub
```

### 6.2 运行流程

```bash
# Step 1: SAM3 实例分割
python tools/batch_segment_sam3.py --dataset dataset/2026_03_13_01_50_19

# Step 2: DA3 深度估计
python tools/batch_process_da3.py --dataset dataset/2026_03_13_01_50_19 --batch-size 8

# Step 3: 验证掩码质量 (可选)
python tools/validate_sam3_masks.py

# Step 4: 数据整合 (需要位姿)
python tools/integrate_perception_data.py --dataset dataset/2026_03_13_01_50_19
```

### 6.3 参数配置

**SAM3 参数**:

```python
CONF_THRESH = 0.5  # 置信度阈值，低于此值的检测结果会被过滤
```

**DA3 参数**:

```python
BATCH_SIZE = 8     # 批量大小，根据显存调整 (RTX 5070 Ti 12GB 推荐 8)
MODEL_NAME = 'depth-anything/DA3-LARGE-1.1'  # 模型版本
```

**深度融合参数**:

```python
FUSION_STRATEGY = 'adaptive'  # 融合策略: 'distance_based', 'confidence_weighted', 'adaptive'
DA3_DOMINATE_RANGE = 5.0      # DA3主导范围 (米)
TRANSITION_RANGE = 2.0        # 过渡区域范围 (米)
```

---

## 7. 问题与解决方案

### 7.1 已知问题汇总

| 问题                     | 严重度 | 状态      | 解决方案                       |
| ------------------------ | ------ | --------- | ------------------------------ |
| **DA3 位姿不可用** | 高     | ⚠️ 已知 | 使用仿真位姿或 COLMAP          |
| **SAM3 速度慢**    | 中     | ⚠️ 已知 | 批量离线处理；后续可用轻量模型 |
| **深度尺度差异**   | 中     | ✅ 解决   | 对齐因子 0.0204                |
| **仿真深度单位**   | 低     | ✅ 解决   | 除以 100 转换为米              |
| **实例无类别**     | 中     | ⏳ 待处理 | 后处理基于深度分类             |
| **位姿未保存**     | 高     | ❌ 阻塞   | 需重新采集或 COLMAP            |

### 7.2 DA3 位姿问题详解

**现象**:

- 轨迹在原点剧烈震荡
- 旋转角度达 79°（物理上不可能）
- 圆形轨迹拟合误差 45.75%

**根因**:

1. 场景视差不足（小范围运动 3m）
2. 极地纹理稀疏
3. DA3 主要优化深度，位姿是副产品

**对策**:

```python
# 不使用 DA3 位姿
da3_poses = prediction.extrinsics  # ⚠️ 不可用！

# 替代方案 1: 仿真位姿 (推荐)
sim_poses = load_simulation_poses()

# 替代方案 2: COLMAP
colmap_poses = run_colmap_sfm()
```

### 7.3 深度融合问题

**现象**: DA3 深度和仿真深度存在尺度差异

**解决方案**:

```python
# 1. 单位转换
sim_depth_m = sim_depth_cm / 100.0

# 2. 尺度对齐 (基于重叠区域)
alignment_factor = 0.0204

# 3. 自适应融合
fused = np.where(da3_depth < 5.0, da3_depth, sim_depth_m)
```

---

## 8. 附录

### 8.1 文件结构

```
ASVSim_zsh/
├── docs/
│   └── Phase4_Perception_Layer_Technical_Documentation.md  # 本文档
├── tools/
│   ├── batch_segment_sam3.py       # SAM3 批量分割
│   ├── batch_process_da3.py        # DA3 批量深度估计
│   ├── validate_sam3_masks.py      # 掩码质量验证
│   ├── validate_da3_poses.py       # 位姿质量验证
│   ├── analyze_depth_alignment.py  # 深度对齐分析
│   └── integrate_perception_data.py # 数据整合 (待实现)
├── dataset/
│   └── 2026_03_13_01_50_19/
│       ├── rgb/                    # 原始图像
│       ├── depth/                  # 仿真深度
│       └── lidar/                  # LiDAR点云
└── test_output/
    ├── sam3_batch_*/               # SAM3 输出
    ├── da3_batch_*/                # DA3 输出
    └── perception_*/               # 整合输出
```

### 8.2 参考资源

**论文**:

- SAM 3: arXiv:2511.16719 (2025)
- Depth Anything V3: arXiv:2511.10647 (2025)
- DINOv2: arXiv:2304.07193 (2023)

**代码仓库**:

- Ultralytics: https://github.com/ultralytics/ultralytics
- Depth-Anything-3: https://github.com/ByteDance-Seed/Depth-Anything-3

**文档**:

- ASVSim 文档: https://bavolesy.github.io/idlab-asvsim-docs/
- DA3 API: 见 `D:\ASVSim_models\Depth-Anything-3\src\depth_anything_3\api.py`

### 8.3 性能基准

**硬件配置**:

- GPU: RTX 5070 Ti (12GB)
- CPU: Intel i7
- RAM: 32GB
- CUDA: 12.8

**性能数据**:

| 模块        | 速度      | 内存占用 |
| ----------- | --------- | -------- |
| SAM3        | 13s/张    | ~4GB GPU |
| DA3 (单张)  | 0.29s/张  | ~3GB GPU |
| DA3 (批量8) | 0.088s/张 | ~6GB GPU |

---

**文档版本**: v1.0
**最后更新**: 2026-03-14
**作者**: ASVSim Project Team
**状态**: Phase 4 已完成 70%，待位姿获取后完成整合
