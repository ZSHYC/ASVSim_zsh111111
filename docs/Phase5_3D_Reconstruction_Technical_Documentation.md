# Phase 5 环境重建层技术文档

**项目**: ASVSim 极地路径规划与 3D Gaussian Splatting 重建
**阶段**: Phase 5 - 环境重建层 (3D Reconstruction Layer)
**版本**: v1.0
**日期**: 2026-03-14
**状态**: 待实施（依赖位姿获取方案确定）

---

## 目录

1. [概述](#1-概述)
2. [技术原理详解](#2-技术原理详解)
3. [输入数据要求](#3-输入数据要求)
4. [实现方案](#4-实现方案)
5. [备用方案分析](#5-备用方案分析)
6. [项目规划与里程碑](#6-项目规划与里程碑)
7. [风险分析与对策](#7-风险分析与对策)
8. [与论文写作的衔接](#8-与论文写作的衔接)
9. [附录](#9-附录)

---

## 1. 概述

### 1.1 设计目标

Phase 5 环境重建层的核心任务是**利用多视角图像序列重建极地冰水环境的三维几何与外观**，为路径规划提供可交互、可可视化的数字孪生环境。

**核心目标**:
1. **高质量重建**: 生成细节丰富、视觉效果逼真的3D场景
2. **实时渲染**: 支持≥30fps的新视角合成（1080p）
3. **无需感知层**: 可直接从仿真真值数据训练，绕过智能感知层的复杂性
4. **论文可展示**: 提供足够 visual impact 的效果用于论文插图和演示视频

### 1.2 技术选型: 3D Gaussian Splatting

**为何选择 3DGS 而非 NeRF?**

| 对比维度 | NeRF (2020) | 3D Gaussian Splatting (2023) |
|---------|-------------|------------------------------|
| **训练速度** | 12-48小时 | 10-60分钟 |
| **渲染速度** | 0.02fps (慢) | 100+fps (实时) |
| **渲染质量** | 优秀 | 优秀（相当或更好） |
| **内存占用** | 中等 | 较高（可接受） |
| **动态场景** | 困难 | 中等（4DGS发展） |
| **编辑能力** | 有限 | 强（可直接操作高斯） |

**官方论文**: "3D Gaussian Splatting for Real-Time Radiance Field Rendering" (SIGGRAPH 2023)
**作者**: Kerbl et al., INRIA / University of Tübingen / Max Planck Institute
**论文链接**: [arXiv:2308.04075](https://arxiv.org/abs/2308.04075)

### 1.3 技术路线概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 5 环境重建流程                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │ RGB序列     │    │ 相机位姿    │    │ 初始化点云          │ │
│  │ (126帧)     │    │ (4×4矩阵)   │    │ (COLMAP/随机)       │ │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘ │
│         │                  │                       │            │
│         └──────────────────┼───────────────────────┘            │
│                            ▼                                    │
│              ┌─────────────────────────┐                       │
│              │  3D Gaussian 初始化      │                       │
│              │  (位置/协方差/颜色/不透明度) │                      │
│              └────────────┬────────────┘                       │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                  │
│         ▼                 ▼                 ▼                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │ 自适应密度   │   │ 各向异性协方差│   │ 球谐系数    │          │
│  │ 控制        │   │ 优化        │   │ 优化        │          │
│  │ (克隆/分裂) │   │             │   │ (颜色细节)  │          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
│                           │                                     │
│                           ▼                                     │
│              ┌─────────────────────────┐                       │
│              │  可微分光栅化渲染        │                       │
│              │  (Tile-based Rasterizer) │                       │
│              └────────────┬────────────┘                       │
│                           │                                     │
│                           ▼                                     │
│              ┌─────────────────────────┐                       │
│              │  与GT图像计算L1+SSIM损失 │                       │
│              │  ← 反向传播优化高斯参数  │                       │
│              └────────────┬────────────┘                       │
│                           │                                     │
│              ┌────────────┴────────────┐                       │
│              │      30,000 迭代        │                       │
│              └────────────┬────────────┘                       │
│                           ▼                                     │
│              ┌─────────────────────────┐                       │
│              │      .ply 输出文件      │                       │
│              │  (可导入UE5/Web查看器)   │                       │
│              └─────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 技术原理详解

### 2.1 核心概念: 3D Gaussian

**场景表示**: 使用一组3D高斯分布（椭球体）来表示场景，每个高斯由以下参数定义：

```
G(x) = exp(-0.5 * (x - μ)^T Σ^(-1) (x - μ))

其中:
- μ ∈ R³: 高斯中心位置 (XYZ)
- Σ ∈ R³ˣ³: 协方差矩阵（定义椭球形状和方向）
- c ∈ R³: 颜色 (RGB，或用球谐函数SH表示视角相关颜色)
- α ∈ R: 不透明度 (0-1)
```

**总参数量**: 每个高斯约 60 个参数
- 位置 μ: 3 floats
- 协方差 Σ: 6 floats (对称矩阵，存3×3的上三角)
- 颜色 SH: 48 floats (3阶球谐，3×16)
- 不透明度 α: 1 float

### 2.2 协方差矩阵的分解表示

**关键创新**: 为了避免直接优化协方差矩阵（需要保持半正定性），使用以下分解：

```
Σ = RSS^TR^T = (RS)(RS)^T

其中:
- R: 旋转矩阵 (用四元数 q 表示，4 floats)
- S: 对角缩放矩阵 (3 floats，表示XYZ轴的缩放)

实际存储: 7 floats (4 for quaternion + 3 for scale)
```

**优势**:
- 通过构造保证 Σ 是正定的
- 优化空间更小（7 vs 6 params，但更易优化）
- 直观的物理意义：旋转+各向异性缩放

### 2.3 可微分光栅化 (Differentiable Rasterization)

**核心问题**: 如何将3D高斯高效地投影到2D屏幕？

**解决方案**: 视角相关的投影 + Tile-based光栅化

#### 2.3.1 3D到2D投影

给定相机位姿，将3D高斯投影到图像平面：

```python
# 3D协方差投影到2D (EWA Splatting)
Σ_2D = J * W * Σ * W^T * J^T

其中:
- W: 视图矩阵 (world to camera)
- J: 投影变换的雅可比矩阵 (affine approximation of projection)
- Σ_2D: 2D投影后的协方差 (椭圆)
```

**截断处理**: 投影后的2D高斯只在一定范围内有贡献（通常3σ），超出部分截断为0。

#### 2.3.2 Tile-based光栅化

**动机**: 对于1080p图像，直接遍历所有高斯计算每个像素的贡献是 O(N×H×W)，太慢。

**解决方案**:
1. **屏幕分块**: 将图像分成 16×16 像素的 tiles
2. **视锥剔除**: 只保留在视锥内的高斯
3. **Tile排序**: 为每个tile建立影响它的高斯列表（基于投影后的2D包围盒）
4. **α-混合**: 对每个tile，按深度排序高斯，从前到后α-混合

```
α-混合公式:
C_final = Σᵢ(Cᵢ × αᵢ × Tᵢ)
其中 Tᵢ = ∏ⱼ₌₁ⁱ⁻¹(1 - αⱼ)

当累积透明度 T < ε (如 1/255) 时提前终止
```

**并行策略**: 每个tile由一个CUDA block处理，利用GPU共享内存加速。

### 2.4 自适应密度控制 (Adaptive Density Control)

**目标**: 自动调整高斯数量，在细节丰富的区域增加密度，在平滑区域减少数量。

**三种操作**:

#### 2.4.1 克隆 (Clone)

**条件**: 高斯梯度较大（视图空间位置梯度 > τ_pos）且尺度较小
**操作**: 创建一个完全相同的副本，沿梯度方向移动一小步

```python
if ||∇_view μ|| > τ_pos and max(scale) < τ_size:
    new_gaussian = copy(gaussian)
    new_gaussian.μ += ε * normalize(∇_view μ)
```

**目的**: 解决欠重建（under-reconstruction）问题

#### 2.4.2 分裂 (Split)

**条件**: 高斯梯度较大且尺度较大
**操作**: 用两个较小的高斯替换原高斯

```python
if ||∇_view μ|| > τ_pos and max(scale) > τ_size:
    # 沿最大尺度方向分裂
    axis = argmax(scale)
    offset = scale[axis] * eigenvector[axis]

    g1 = copy(gaussian)
    g1.scale[axis] *= 0.5
    g1.μ -= 0.5 * offset

    g2 = copy(gaussian)
    g2.scale[axis] *= 0.5
    g2.μ += 0.5 * offset
```

**目的**: 解决过重建（over-reconstruction，大高斯试图覆盖复杂几何）

#### 2.4.3 剪枝 (Prune)

**条件**:
- 不透明度 α < τ_α (几乎透明)
- 或在相机平面后方
- 或在视锥外且巨大

**操作**: 直接删除高斯

**目的**: 减少冗余，控制内存占用

### 2.5 优化目标函数

**损失函数**: L1 Loss + SSIM Loss

```python
L = (1 - λ) * ||I_render - I_GT||₁ + λ * (1 - SSIM(I_render, I_GT))

其中:
- λ: 通常取 0.2
- SSIM: 结构相似性指标，捕获局部结构信息
```

**优化器**: Adam
- 位置 μ: 学习率 0.00016
- 协方差: 学习率 0.005
- 颜色 SH: 学习率 0.0025
- 不透明度 α: 学习率 0.05 (使用 sigmoid 激活)

**学习率衰减**:
- 位置学习率使用指数衰减（每轮乘以0.99995）
- 其他参数固定学习率

### 2.6 球谐函数 (Spherical Harmonics) 表示颜色

**动机**: 物体的外观会随视角变化（如高光、反射），简单的RGB无法表达。

**解决方案**: 使用球谐函数（SH）表示视角相关的颜色：

```
c(view_dir) = Σₗ₌₀ⁿ Σₘ₌₋ₗˡ cₗₘ * Yₗₘ(view_dir)

其中:
- Yₗₘ: 球谐基函数 (l阶，m次)
- cₗₘ: 可学习的系数
- 通常使用3阶 (l=0,1,2)，共16个基函数 × 3通道 = 48参数
```

**基函数示例**:
- l=0: DC分量（与视角无关的基础颜色）
- l=1: 线性项（捕捉主要光照方向）
- l=2: 二次项（捕捉高光、反射细节）

---

## 3. 输入数据要求

### 3.1 数据来源分析

#### 方案A: 直接使用ASVSim仿真数据（推荐，无需感知层）

```
dataset/2026_03_13_01_50_19/
├── rgb/                    # 126张 PNG 图像 [640×480]
├── depth/                  # 126张 NPY 深度图 (可选，用于验证)
└── (需要补充: poses.json)   # 相机位姿 [4×4] 矩阵
```

**位姿获取方法**:
1. **重新采集**: 修改采集脚本，保存 `client.simGetVehiclePose()` 输出
2. **COLMAP估计**: 使用COLMAP SfM从RGB序列估计位姿
3. **FlowMap**: 使用无位姿3DGS方法（实验性，见备用方案）

#### 方案B: 使用智能感知层输出（如果Phase 4完成）

```
test_output/perception_2026_03_13_01_50_19/
├── rgb/                    # 原始图像
├── depth_da3/              # DA3估计深度（可选，用于初始化）
├── segmentation/           # SAM3实例分割（可选，用于约束）
└── poses/                  # 位姿（仿真真值或估计）
```

### 3.2 COLMAP格式要求（最常用）

**标准COLMAP输出结构**:

```
dataset/
├── images/                 # 去畸变后的JPG图像
└── sparse/
    └── 0/
        ├── cameras.bin     # 相机内参
        ├── images.bin      # 相机位姿和外参
        └── points3D.bin    # 稀疏点云（用于初始化）
```

**cameras.bin 内容**:
```
camera_id: 1
model: "PINHOLE"
width: 640
height: 480
params: [fx, fy, cx, cy]
```

**images.bin 内容** (每帧):
```
image_id: 1
qvec: [qw, qx, qy, qz]      # 旋转四元数 (world to camera)
tvec: [tx, ty, tz]          # 平移向量
camera_id: 1
name: "0000.png"
points2D: [(x1,y1,id1), ...]  # 2D特征点和对应的3D点ID
```

**points3D.bin 内容** (每个点):
```
point3D_id: 1
xyz: [X, Y, Z]              # 3D坐标
rgb: [R, G, B]              # 颜色
error: 0.5                  # 重投影误差
track: [(image_id, point2D_idx), ...]  # 观测记录
```

### 3.3 Nerfstudio格式要求

**transforms.json 结构**:

```json
{
  "camera_model": "OPENCV",
  "fl_x": 609.523,           # fx 焦距（像素）
  "fl_y": 609.523,           # fy 焦距
  "cx": 320.0,               # 主点X
  "cy": 240.0,               # 主点Y
  "w": 640,
  "h": 480,
  "k1": 0.0,                 # 畸变系数（可选）
  "k2": 0.0,
  "p1": 0.0,
  "p2": 0.0,
  "frames": [
    {
      "file_path": "images/0000.png",
      "transform_matrix": [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 5.0],
        [0.0, 0.0, 0.0, 1.0]
      ]
    }
  ]
}
```

**transform_matrix**: camera-to-world 矩阵（4×4），即相机在世界坐标系中的位姿。

### 3.4 数据集质量要求

**图像数量和覆盖**:
- **最小**: 20-30张（仅能重建局部）
- **推荐**: 100-200张（完整场景）
- **我们的数据**: 126张（符合要求）

**视角覆盖**:
- 需要足够的视角重叠（相邻图像≥50%重叠）
- 覆盖待重建区域的全方位视角
- 避免纯旋转（需要平移运动产生视差）

**光照条件**:
- 尽量保持光照一致（或关闭仿真中的动态光照）
- 避免过曝和欠曝

**运动模糊**:
- 采集时ASV应低速运动，避免运动模糊

---

## 4. 实现方案

### 4.1 方案选择矩阵

| 方案 | 需要位姿? | 复杂度 | 质量 | 推荐度 | 备注 |
|------|----------|--------|------|--------|------|
| **A. 仿真位姿+官方3DGS** | 是（真值） | 低 | 最高 | ⭐⭐⭐⭐⭐ | **首选方案** |
| **B. COLMAP+官方3DGS** | 是（估计） | 中 | 高 | ⭐⭐⭐⭐ | 如果无法获取仿真位姿 |
| **C. Nerfstudio Splatfacto** | 是 | 低 | 高 | ⭐⭐⭐⭐⭐ | 推荐新手使用 |
| **D. FlowMap (无位姿)** | 否 | 中 | 中 | ⭐⭐⭐ | 备用方案，实验性 |

### 4.2 首选方案: Nerfstudio Splatfacto（详细步骤）

**为什么选择 Nerfstudio?**
- 封装完善，一行命令即可训练
- 自动处理数据格式转换
- 内置可视化viewer
- 支持多种splatting变体（splatfacto, splatfacto-big）

#### 4.2.1 环境安装

```bash
# 1. 创建conda环境
conda create -n nerfstudio python=3.10
conda activate nerfstudio

# 2. 安装PyTorch (CUDA 12.1)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. 安装Nerfstudio
pip install nerfstudio

# 4. 安装gsplat后端
pip install gsplat

# 5. 验证安装
ns-train --help
```

#### 4.2.2 数据准备

**步骤1: 获取相机位姿**

如果使用仿真位姿（推荐），需要转换格式：

```python
# tools/convert_asvsim_to_nerfstudio.py
import json
import numpy as np
from pathlib import Path

def convert_asvsim_to_nerfstudio(dataset_dir, poses_file, output_dir):
    """
    将ASVSim数据集转换为Nerfstudio格式

    Args:
        dataset_dir: RGB图像目录
        poses_file: poses.json (从仿真导出)
        output_dir: 输出目录
    """
    # 加载位姿
    with open(poses_file, 'r') as f:
        poses_data = json.load(f)

    # ASVSim相机参数 (640x480, FOV=90°)
    W, H = 640, 480
    fov = 90.0
    fx = fy = W / (2 * np.tan(np.radians(fov) / 2))
    cx, cy = W / 2, H / 2

    transforms = {
        "camera_model": "OPENCV",
        "fl_x": fx,
        "fl_y": fy,
        "cx": cx,
        "cy": cy,
        "w": W,
        "h": H,
        "k1": 0.0,
        "k2": 0.0,
        "frames": []
    }

    for pose in poses_data:
        frame_id = pose['frame_id']

        # ASVSim位姿是world-to-camera还是camera-to-world?
        # 需要根据实际情况调整，可能需要求逆
        T = np.array(pose['transform_matrix'])

        transforms['frames'].append({
            "file_path": f"images/{frame_id:04d}.png",
            "transform_matrix": T.tolist()
        })

    # 保存
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "transforms.json", 'w') as f:
        json.dump(transforms, f, indent=2)

    print(f"Saved transforms.json with {len(transforms['frames'])} frames")

if __name__ == '__main__':
    convert_asvsim_to_nerfstudio(
        "dataset/2026_03_13_01_50_19/rgb",
        "dataset/2026_03_13_01_50_19/poses.json",
        "data/nerfstudio/asvsim_polar"
    )
```

**步骤2: 复制图像**

```bash
mkdir -p data/nerfstudio/asvsim_polar/images
cp dataset/2026_03_13_01_50_19/rgb/*.png data/nerfstudio/asvsim_polar/images/
```

#### 4.2.3 训练

```bash
# 基础训练（推荐）
ns-train splatfacto --data data/nerfstudio/asvsim_polar

# 高质量训练（更多高斯，更慢）
ns-train splatfacto-big --data data/nerfstudio/asvsim_polar

# 带自定义参数
ns-train splatfacto \
    --data data/nerfstudio/asvsim_polar \
    --pipeline.model.cull-alpha-thresh=0.005 \
    --pipeline.model.use-scale-regularization=True \
    --max-num-iterations 40000
```

**关键参数说明**:
- `--max-num-iterations`: 训练迭代次数（默认30000，增加可提升质量）
- `--pipeline.model.cull-alpha-thresh`: 剪枝阈值（降低保留更多高斯）
- `--pipeline.model.use-scale-regularization`: 抑制细长高斯

#### 4.2.4 可视化和导出

```bash
# 查看训练结果（自动打开浏览器）
# 训练时会自动启动viewer，访问 http://localhost:7007

# 导出.ply文件（用于其他查看器）
ns-export gaussian-splat \
    --load-config outputs/asvsim_polar/splatfacto/.../config.yml \
    --output-dir exports/asvsim_polar
```

#### 4.2.5 预期训练结果

**训练时间** (RTX 5070 Ti):
- 30k iterations: ~15-25分钟
- 40k iterations: ~20-30分钟

**输出文件**:
```
exports/asvsim_polar/
└── splat.ply          # 可直接用3D Gaussian Splatting Viewer打开
```

**渲染效果**:
- 新视角合成: ≥100fps @ 1080p
- 视觉质量: PSNR ~30dB
- 高斯数量: ~100万-300万个

### 4.3 备用方案: 官方3D Gaussian Splatting

如果Nerfstudio遇到问题，使用官方实现。

#### 4.3.1 安装

```bash
# 克隆仓库
git clone https://github.com/graphdeco-inria/gaussian-splatting.git
cd gaussian-splatting

# 创建环境
conda env create -f environment.yml
conda activate gaussian_splatting

# 安装子模块 (diff-gaussian-rasterization等)
pip install submodules/diff-gaussian-rasterization
pip install submodules/simple-knn
```

#### 4.3.2 COLMAP处理（如果需要）

```bash
# 使用提供的convert.py脚本
python convert.py -s data/asvsim_polar --skip_matching

# 或手动运行COLMAP
colmap feature_extractor \
    --database_path data/asvsim_polar/database.db \
    --image_path data/asvsim_polar/images

colmap exhaustive_matcher \
    --database_path data/asvsim_polar/database.db

colmap mapper \
    --database_path data/asvsim_polar/database.db \
    --image_path data/asvsim_polar/images \
    --output_path data/asvsim_polar/sparse
```

#### 4.3.3 训练

```bash
python train.py -s data/asvsim_polar --data_device cpu

# 参数说明:
# -s: 数据目录（包含images/和sparse/）
# --data_device: 数据加载设备（cpu避免显存不足）
# --iterations: 迭代次数（默认30000）
# --resolution: 训练分辨率（-1为原始分辨率）
```

#### 4.3.4 渲染

```bash
# 渲染测试集视角
python render.py -m output/<timestamp> --mode test

# 渲染任意视角（需要指定相机路径）
python render.py -m output/<timestamp> --mode video
```

### 4.4 无位姿方案: FlowMap（备用）

**官方论文**: "FlowMap: High-Quality Camera Poses, Intrinsics, and Depth via Gradient Descent" (CVPR 2024)
**作者**: Smith et al., Brown University
**arXiv**: [2404.15259](https://arxiv.org/abs/2404.15259)

**原理**: 从光流和重投影误差联合优化位姿、内参和深度。

**适用场景**: 无法获取任何位姿信息时使用。

**限制**:
- 需要较大的视角运动（ASV数据采集满足）
- 计算开销大（需要多轮迭代）
- 质量略低于COLMAP

**使用步骤**:

```bash
# 安装FlowMap
pip install flowmap

# 运行（自动估计位姿+训练3DGS）
flowmap overfit \
    --data_dir data/asvsim_polar/images \
    --output_dir output/flowmap

# 导出位姿供后续使用
# 导出.ply供可视化
```

---

## 5. 备用方案分析

### 5.1 方案对比总览

| 场景 | 推荐方案 | 预期质量 | 实施难度 | 时间估算 |
|------|----------|----------|----------|----------|
| 有位姿（理想） | Nerfstudio Splatfacto | ⭐⭐⭐⭐⭐ | 低 | 半天 |
| 无位姿，可COLMAP | COLMAP + 官方3DGS | ⭐⭐⭐⭐ | 中 | 1-2天 |
| 无位姿，COLMAP失败 | FlowMap | ⭐⭐⭐ | 中 | 1-2天 |
| 时间极紧 | 简化流程（低分辨率） | ⭐⭐⭐ | 低 | 2-3小时 |
| 质量要求极高 | splatfacto-big + 长训练 | ⭐⭐⭐⭐⭐ | 低 | 1天 |

### 5.2 关键备用方案详解

#### 备用方案A: 简化训练流程（时间紧迫）

**适用**: 只有几小时时间，需要快速出结果展示

```bash
# 1. 降低分辨率（加速处理）
ns-process-data images \
    --data images/ \
    --output-dir processed/ \
    --downscale-factor 4  # 640x480 -> 160x120

# 2. 减少训练迭代
ns-train splatfacto \
    --data processed/ \
    --max-num-iterations 10000  # 默认30000的1/3

# 预期时间: 5-10分钟
# 预期质量: 可接受，细节减少
```

#### 备用方案B: 使用仿真深度辅助初始化

**如果DA3深度已生成**，可用于改进初始化：

```python
# 将DA3深度转换为点云初始化COLMAP
# 代替随机初始化，加速收敛并提高质量

import numpy as np
import json

def depth_to_pointcloud(depth_dir, poses_file, output_dir):
    """将深度图和位姿转换为点云初始化"""
    # 对每个帧，将深度反投影为3D点
    # 保存为COLMAP points3D.bin格式
    pass
```

**优势**:
- 更准确的初始化 → 更快收敛
- 更好的几何精度

#### 备用方案C: 分段重建+融合

**适用**: 单场景太大，显存不足（12GB RTX 5070 Ti通常足够）

```
将126帧分成3段（每段42帧）
    ↓
分别重建3个sub-map
    ↓
基于重叠区域ICP配准
    ↓
融合为完整场景
```

### 5.3 失败回退策略

**如果3DGS完全失败**:

| 回退层级 | 方案 | 输出形式 | 论文可用性 |
|---------|------|----------|-----------|
| 1 | 深度图可视化 | 2D图像序列 | ⭐⭐⭐ 可用 |
| 2 | 点云拼接 | 3D点云（Meshlab查看） | ⭐⭐⭐⭐ 可用 |
| 3 | TSDF融合 | 3D网格（.obj文件） | ⭐⭐⭐⭐⭐ 推荐 |
| 4 | 纯仿真截图 | 视频展示 | ⭐⭐ 下策 |

**TSDF融合快速实现**:

```bash
# 使用Open3D的TSDF集成
pip install open3d

# 运行融合脚本（使用仿真深度+位姿）
python tools/tsdf_fusion.py \
    --rgb_dir dataset/rgb \
    --depth_dir dataset/depth \
    --poses dataset/poses.json \
    --output mesh.ply
```

---

## 6. 项目规划与里程碑

### 6.1 前置依赖（必须先解决）

```
□ 1. 获取相机位姿（最关键）
   ├─ 方案A: 修改采集脚本，重新采集（推荐，半天）
   ├─ 方案B: 从LiDAR数据解析位姿（1天）
   └─ 方案C: 使用COLMAP估计位姿（1天）

□ 2. 数据格式验证
   └─ 运行验证脚本，确保图像-位姿对应正确
```

### 6.2 实施时间表

#### 第一阶段: 数据准备（半天-1天）

| 任务 | 时间 | 产出 |
|------|------|------|
| 获取/生成位姿 | 2-4h | poses.json |
| 格式转换验证 | 1h | transforms.json |
| 环境安装 | 1h | 可运行的nerfstudio |
| 数据预处理 | 1h | 标准格式数据集 |

#### 第二阶段: 训练与调优（1-2天）

| 任务 | 时间 | 产出 |
|------|------|------|
| 初次训练 | 1h | baseline模型 |
| 质量评估 | 1h | PSNR/SSIM指标 |
| 参数调优 | 2-4h | 优化模型 |
| 多次运行 | 2-4h | 对比结果 |

#### 第三阶段: 导出与展示（半天）

| 任务 | 时间 | 产出 |
|------|------|------|
| 导出PLY | 0.5h | splat.ply |
| 渲染视频 | 2h | 演示视频.mp4 |
| 新视角截图 | 1h | 论文插图（5-10张） |
| Web查看器 | 1h | 可交互演示 |

### 6.3 里程碑检查点

```
M1: 数据就绪（Day 1）
    └─ 验收标准: transforms.json通过ns-process-data验证

M2: 训练完成（Day 2）
    └─ 验收标准: PSNR > 25dB, 无明显伪影

M3: 展示就绪（Day 3）
    └─ 验收标准: 渲染视频+论文插图+Web查看器
```

---

## 7. 风险分析与对策

### 7.1 技术风险

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| COLMAP位姿估计失败 | 中 | 高 | 使用仿真位姿或FlowMap |
| 显存不足（OOM） | 低 | 高 | 降低分辨率或使用分块训练 |
| 训练不收敛 | 低 | 高 | 检查位姿准确性，调整学习率 |
| 重建质量差（模糊） | 中 | 中 | 增加迭代次数，使用splatfacto-big |
| 动态物体干扰 | 中 | 低 | 使用SAM3掩码排除（如有） |

### 7.2 缓解策略详解

#### 位姿估计失败

**症状**: COLMAP只注册少量图像，或位姿明显错误（轨迹混乱）

**对策**:
1. **增加图像重叠**: 如果原始数据采集间隔过大，可插值生成中间帧
2. **特征匹配参数**: 调整COLMAP的`SiftExtraction`参数
3. **序列匹配**: 使用时间序列匹配代替暴力匹配
4. **回退到仿真位姿**: 最可靠的方案

#### 显存不足

**症状**: CUDA out of memory错误

**对策**:
```bash
# 1. 降低训练分辨率
ns-train splatfacto --data . --pipeline.model.resolution 512

# 2. 减少batch大小（nerfstudio自动处理）
# 3. 使用CPU卸载
ns-train splatfacto --data . --pipeline.datamanager.cpu-only
```

#### 重建质量差

**症状**: 模糊、漂浮伪影、空洞

**对策**:
1. **增加训练迭代**: `--max-num-iterations 50000`
2. **调整密度控制**: `--pipeline.model.densify-until-iter 15000`
3. **使用更大的模型**: `splatfacto-big`
4. **检查初始化**: 确保COLMAP点云足够密集（>1000点）

---

## 8. 与论文写作的衔接

### 8.1 智能感知层的论文表述策略

**核心策略**: 在论文中完整描述智能感知层的设计和**理论价值**，但可以标注为"待实现"或"原型验证阶段"。

**建议表述**:

```
4.1 智能感知层设计

为实现高质量的环境感知，本研究设计了基于SAM 3和Depth Anything V3的
多模态感知框架。该框架理论上可提供：
(1) 海冰实例分割，用于识别可航行区域；
(2) 绝对深度估计，用于度量障碍物距离；
(3) 相机位姿估计，用于SLAM和建图。

由于感知层的复杂性和时间限制，本研究在实验阶段采用仿真真值位姿
替代感知层输出，以确保三维重建和路径规划模块的可行性验证。
未来工作将完善感知层的实际部署。
```

### 8.2 论文结构建议

```
第4章 智能感知层（技术方案章节，可详细描述原理）
4.1 感知层架构设计
4.2 SAM 3海冰分割原理
4.3 Depth Anything V3深度估计原理
4.4 多模态数据融合策略
4.5 *本节实验结果基于仿真真值，感知层原型待完善

第5章 环境重建层（核心实现章节）
5.1 3D Gaussian Splatting技术原理
5.2 训练数据准备与位姿获取
5.3 模型训练与参数调优
5.4 实验结果与质量评估（PSNR、渲染视频）

第6章 路径规划层（核心实现章节）
...（详见路径规划文档）
```

### 8.3 可展示的论文素材

**必须产出**（用于论文）:
1. **对比图**: 原始RGB vs 渲染新视角 vs GT
2. **渲染视频**: 环绕场景飞行视频（30秒）
3. **高斯图可视化**: 显示高斯分布的3D视图
4. **指标表格**: PSNR、SSIM、训练时间、渲染FPS
5. **消融实验**: 不同训练迭代数的效果对比

**可选增强**:
- 与NeRF的对比（如果时间允许）
- 不同场景尺度的重建效果
- 实时Web查看器链接（QR码）

### 8.4 论文化表述示例

**技术原理部分**:
```
5.1.1 3D Gaussian Splatting原理

本研究采用3D Gaussian Splatting (3DGS) [Kerbl et al., 2023]
作为环境重建的核心技术。与传统NeRF使用隐式MLP表示场景不同，
3DGS使用显式的3D高斯集合来表示辐射场：

G(x) = exp(-0.5(x-μ)^T Σ^{-1} (x-μ))

其中μ∈R³为高斯中心，Σ∈R^{3×3}为各向异性协方差矩阵。
场景由数百万个此类高斯组成，每个高斯附加颜色c和不透明度α。

渲染时，采用Tile-based光栅化算法将高斯投影到图像平面，
通过α-混合累积颜色。该表示支持可微分渲染，可通过梯度下降
优化高斯参数以重建输入图像。
```

**实验结果部分**:
```
5.4.1 重建质量评估

在ASVSim采集的126帧极地场景数据集上，本文方法在RTX 5070 Ti
上训练30分钟，达到以下指标：

- PSNR: 30.2 dB
- SSIM: 0.91
- 渲染速度: 120 fps @ 1080p
- 高斯数量: 1.2M

图5-1展示了新视角合成效果与真实图像的对比。
视频附件1展示了环绕场景的实时渲染效果。
```

---

## 9. 附录

### 9.1 参考资源

**官方论文**:
- 3D Gaussian Splatting: [arXiv:2308.04075](https://arxiv.org/abs/2308.04075)
- Nerfstudio Splatfacto: [docs.nerf.studio](https://docs.nerf.studio/nerfology/methods/splat.html)
- FlowMap (无位姿): [arXiv:2404.15259](https://arxiv.org/abs/2404.15259)

**代码仓库**:
- 官方3DGS: https://github.com/graphdeco-inria/gaussian-splatting
- Nerfstudio: https://github.com/nerfstudio-project/nerfstudio
- gsplat: https://github.com/nerfstudio-project/gsplat

**工具**:
- 在线PLY查看器: https://projects.markkellogg.org/threejs/demo_gaussian_splats_3d.php
- WebGL Splat Viewer: https://github.com/antimatter15/splat

### 9.2 关键参数速查表

**Nerfstudio Splatfacto参数**:

| 参数 | 默认值 | 调整建议 |
|------|--------|----------|
| `cull-alpha-thresh` | 0.1 | 降低保留更多高斯（0.005） |
| `continue-cull-post-densification` | True | 设为False保留细节 |
| `use-scale-regularization` | False | 设为True抑制细长高斯 |
| `densify-until-iter` | 10000 | 增加以提升细节 |
| `max-num-iterations` | 30000 | 增加提升质量 |

### 9.3 故障排除FAQ

**Q: 训练时报"No images found"?**
A: 检查`transforms.json`中的`file_path`是否正确指向图像文件。

**Q: 渲染结果全黑?**
A: 可能是位姿坐标系错误。检查`transform_matrix`是camera-to-world还是world-to-camera。

**Q: 如何确定训练是否收敛?**
A: 观察loss曲线，当PSNR不再明显提升（ plateau ）时即收敛。通常20k-30k iterations。

**Q: 如何查看.ply文件?**
A: 使用以下工具:
- Windows: https://github.com/williamhyun/gaussian-splatting-viewer
- Web: https://playcanvas.com/viewer
- Python: `open3d.visualization.draw_geometries([ply])`

---

**文档版本**: v1.0
**最后更新**: 2026-03-14
**作者**: ASVSim Project Team
**状态**: 待实施，依赖位姿获取方案

