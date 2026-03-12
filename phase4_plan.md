# Phase 4: 智能感知层详细规划

## 上下文与背景

**当前状态**: Phase 3 数据采集已完成，获得 8 帧极地冰水环境多模态数据。

**用户决策**:
- 接受第一帧光晕问题（自动曝光不稳定），从第二帧开始使用
- 接受船体可见问题，后续从建模层面解决
- 正式进入 Phase 4 智能感知层

**Phase 4 目标**: 实现三大感知模块——SAM 3 海冰分割、Depth Anything 3 深度估计与位姿预测、相机-LiDAR 联合标定

---

## 技术选型更新

### 1. 实例分割: SAM 3 (最新版)

**版本确认**: SAM 3 已正式发布（2024年12月）

**核心特性**:
- 统一基础模型，支持图像和视频
- 开放词汇概念分割（支持文本提示）
- 848M 参数，DETR 检测器 + SAM 2 跟踪器
- 三种提示模式：文本提示 / 视觉提示 / 示例提示

**系统要求**:
- Python 3.12+
- PyTorch 2.7+
- CUDA 12.6+

**安装方式**:
```bash
# 方式1: 官方仓库
conda create -n sam3 python=3.12
pip install torch==2.7.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
git clone https://github.com/facebookresearch/sam3.git && cd sam3
pip install -e .

# 方式2: Ultralytics (推荐，更简单)
pip install -U ultralytics>=8.3.237
```

**权重下载**:
- 需先在 Hugging Face 申请权限: https://huggingface.co/facebook/sam3
- 手动下载 `sam3.pt` (848M)

### 2. 深度估计与几何预测: Depth Anything 3 (最新版)

**版本确认**: DA3 已正式发布（2025年，arXiv:2511.10647）

**核心特性**:
- **支持任意数量视觉输入**: 单视图到多视图统一处理
- **预测相机位姿**: 无需已知相机位姿，可直接估计
- **空间一致几何**: 预测空间一致的几何结构
- **3DGS 渲染参数**: 直接输出 3D Gaussian Splatting 渲染参数
- **深度射线表示**: 使用 depth-ray 表示统一几何预测
- **架构简化**: 单一 plain transformer (DINOv2 编码器)，无需复杂多任务学习

**模型版本**:
| 模型 | 参数量 | 能力 | 许可证 |
|------|--------|------|--------|
| DA3-GIANT-1.1 | 1.15B | Depth + Pose + 3D Gaussians | CC BY-NC 4.0 |
| DA3-LARGE-1.1 | 0.35B | Depth + Pose | CC BY-NC 4.0 |
| DA3-BASE/SMALL | 0.12B/0.08B | 基础深度 | Apache 2.0 |
| DA3NESTED-GIANT-LARGE-1.1 | 1.40B | 完整pipeline + Metric Depth | CC BY-NC 4.0 |
| DA3METRIC-LARGE | 0.35B | Metric Depth + Sky Seg | Apache 2.0 |
| DA3MONO-LARGE | 0.35B | 相对单目深度 | Apache 2.0 |

**性能提升** (对比 VGGT):
- 相机位姿精度: **+44.3%**
- 几何精度: **+25.1%**
- 单目深度估计: **超越 DA2**

**系统要求**:
- Python >= 3.8
- PyTorch >= 2.0
- 推荐 CUDA 支持

**安装方式**:
```bash
# 克隆仓库
git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git
cd Depth-Anything-3

# 安装依赖
pip install xformers torch>=2 torchvision
pip install -e .

# 完整安装（含Gradio UI）
pip install -e ".[app]"
```

**权重下载**:
- 从 Hugging Face 下载: https://huggingface.co/depth-anything
- 推荐 DA3NESTED-GIANT-LARGE-1.1 (1.40B) 用于完整功能

**使用示例**:
```python
from depth_anything_3.api import DepthAnything3

# 加载模型
model = DepthAnything3.from_pretrained("depth-anything/DA3NESTED-GIANT-LARGE")

# 推理 - 返回 depth, confidence, extrinsics, intrinsics
prediction = model.inference(images)

# 提取结果
depth = prediction['depth']           # HxW 深度图
pose = prediction['extrinsics']       # 4x4 相机位姿矩阵
intrinsics = prediction['intrinsics'] # 3x3 内参矩阵
```

### 3. 相机-LiDAR 联合标定（优化方案）

**标定方法**:
- **方案A**: 利用 DA3 预测的位姿作为初始值
- **方案B**: 基于 DA3 深度与 LiDAR 点云的对应关系优化外参
- **方案C**: 传统方法（如 DA3 不可用）

**关键洞察**: DA3 可以直接预测相机位姿，可能**减少或替代**部分标定工作

---

## Phase 4 任务分解

### Task 4.1: SAM 3 海冰实例分割

**目标**: 部署 SAM 3，实现对极地海冰的自动实例分割

**输入**:
- `dataset/2026_03_12_20_53_24/rgb/*.png` (8帧 RGB 图像)

**输出**:
- `dataset/2026_03_12_20_53_24/segmentation/*.png` (实例掩码，每个像素值为实例ID)
- `dataset/2026_03_12_20_53_24/segmentation_vis/*.png` (可视化结果)

**技术方案**:

1. **安装 SAM 3**
   ```bash
   pip install -U ultralytics>=8.3.237
   ```

2. **下载权重**
   - 访问 https://huggingface.co/facebook/sam3 申请权限
   - 下载 `sam3.pt` 到 `models/sam3.pt`

3. **编写推理脚本** (`4-1_sam3_segmentation.py`)

   **方案 A: 文本提示分割** (推荐，无需手动标注)
   ```python
   from ultralytics.models.sam import SAM3SemanticPredictor

   predictor = SAM3SemanticPredictor(overrides=dict(model="models/sam3.pt", task="segment"))
   predictor.set_image("rgb/0001.png")
   results = predictor(text=["sea ice", "water", "sky", "boat"])
   ```

   **方案 B: 自动分割** (无提示，生成所有候选区域)
   ```python
   from ultralytics import SAM
   model = SAM("models/sam3.pt")
   results = model.predict(source="rgb/0001.png")
   ```

4. **后处理**
   - 过滤小面积区域
   - 合并相似实例
   - 生成实例ID映射表

**预期挑战**:
- SAM 3 需要 Python 3.12，可能与现有环境冲突
- 权重需申请权限，可能需要等待
- 海冰纹理复杂，自动分割可能需要调优

**备选方案**: 如 SAM 3 部署困难，回退到 SAM 2
```bash
pip install git+https://github.com/facebookresearch/sam2.git
```

---

### Task 4.2: Depth Anything 3 深度估计与位姿预测

**目标**: 部署 Depth Anything 3，生成高质量深度图和相机位姿，直接输出3DGS渲染参数

**输入**:
- `dataset/2026_03_12_20_53_24/rgb/*.png` (RGB 图像序列，多视图)
- `dataset/2026_03_12_20_53_24/depth/*.npy` (仿真 Depth，作为参考真值)
- `dataset/2026_03_12_20_53_24/poses.json` (仿真位姿，用于对比验证)

**输出**:
- `dataset/2026_03_12_20_53_24/depth_da3/*.npy` (DA3 估计深度)
- `dataset/2026_03_12_20_53_24/poses_da3/*.json` (DA3 预测位姿)
- `dataset/2026_03_12_20_53_24/gaussians_da3/*.ply` (DA3 输出的3DGS初始化参数)
- `dataset/2026_03_12_20_53_24/depth_fused/*.npy` (DA3深度与仿真深度融合)

**技术方案**:

1. **安装 Depth Anything 3**
   ```bash
   git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git
   cd Depth-Anything-3
   pip install xformers torch>=2 torchvision
   pip install -e ".[all]"
   ```

2. **下载权重** (推荐 DA3NESTED-GIANT-LARGE-1.1 用于完整功能)
   ```bash
   # 从 Hugging Face 下载
   huggingface-cli download depth-anything/DA3NESTED-GIANT-LARGE-1.1
   ```

3. **编写推理脚本** (`4-2_depth_anything_v3.py`)

   **方案 A: 多视图联合推理** (推荐，利用DA3的多视图能力)
   ```python
   from depth_anything_3.api import DepthAnything3
   import cv2
   import numpy as np
   import glob

   # 加载模型
   model = DepthAnything3.from_pretrained("depth-anything/DA3NESTED-GIANT-LARGE")

   # 读取多帧图像
   image_paths = sorted(glob.glob("rgb/*.png"))[1:]  # 跳过第一帧
   images = [cv2.imread(p) for p in image_paths]

   # 多视图联合推理
   prediction = model.inference(images)

   # 提取结果
   depths = prediction['depth']           # [N, H, W] 深度图序列
   poses = prediction['extrinsics']       # [N, 4, 4] 相机位姿序列
   intrinsics = prediction['intrinsics']  # [3, 3] 内参矩阵
   confidences = prediction['conf']       # [N, H, W] 置信度

   # 保存结果
   for i, (depth, pose) in enumerate(zip(depths, poses)):
       np.save(f"depth_da3/{i+1:04d}.npy", depth)
       np.save(f"poses_da3/{i+1:04d}.npy", pose)
   ```

   **方案 B: 单目深度 + 与仿真位姿融合**
   ```python
   # 如果多视图推理不稳定，使用单目模式
   from depth_anything_3.api import DepthAnything3

   model = DepthAnything3.from_pretrained("depth-anything/DA3MONO-LARGE")

   for img_path in image_paths:
       img = cv2.imread(img_path)
       prediction = model.inference([img])
       depth = prediction['depth'][0]

       # 与仿真深度对齐尺度
       depth_aligned = align_depth_to_simulation(depth, sim_depth)
   ```

4. **深度融合策略**
   ```python
   def fuse_depth_da3_sim(depth_da3, depth_sim, confidence_da3):
       """
       融合 DA3 深度与仿真深度

       策略：
       - DA3 深度：基于视觉，近处细节丰富，但尺度可能偏移
       - 仿真深度：真值，但远处可能噪声大，近处有遮挡问题
       - 置信度加权：DA3 提供每像素置信度
       """
       # 基于置信度的加权融合
       conf_mask = confidence_da3 / confidence_da3.max()

       # 仿真深度置信度：近处高，远处低
       conf_sim = np.clip(1.0 - depth_sim / 50.0, 0.3, 1.0)

       # 加权融合
       depth_fused = (depth_da3 * conf_mask + depth_sim * conf_sim) / \
                     (conf_mask + conf_sim + 1e-6)

       return depth_fused
   ```

5. **位姿验证与融合**
   ```python
   def validate_and_fuse_poses(poses_da3, poses_sim, threshold=0.1):
       """
       验证 DA3 预测的位姿与仿真位姿的一致性

       输入:
       - poses_da3: DA3 预测的 [N, 4, 4] 位姿矩阵
       - poses_sim: 仿真真值的 [N, 4, 4] 位姿矩阵

       输出:
       - poses_fused: 融合后的位姿
       - error_report: 误差分析报告
       """
       errors = []
       for i, (da3_pose, sim_pose) in enumerate(zip(poses_da3, poses_sim)):
           # 计算位置误差
           pos_error = np.linalg.norm(da3_pose[:3, 3] - sim_pose[:3, 3])

           # 计算旋转误差（角度）
           rot_error = compute_rotation_error(da3_pose[:3, :3], sim_pose[:3, :3])

           errors.append({'frame': i, 'pos_error': pos_error, 'rot_error': rot_error})

           # 如果误差小，优先使用 DA3 位姿（更平滑）
           # 如果误差大，使用仿真位姿（真值）
           if pos_error < threshold:
               poses_fused[i] = 0.7 * da3_pose + 0.3 * sim_pose
           else:
               poses_fused[i] = sim_pose

       return poses_fused, errors
   ```

**关键优势**:
- **位姿预测**: DA3 可直接预测相机位姿，可能减少标定工作量
- **多视图一致性**: 联合推理保证多帧几何一致性
- **3DGS就绪**: 直接输出3DGS渲染参数，Phase 5 可直接使用
- **置信度**: 提供每像素置信度，便于融合决策

**预期挑战**:
- 模型较大 (1.4B)，推理速度慢
- 多视图推理需要较多显存
- DA3 预测的位姿与仿真坐标系需要对齐

---

### Task 4.3: 相机-LiDAR 联合标定与验证

**目标**: 基于 DA3 输出和仿真数据，验证并优化相机-LiDAR 外参

**背景变化**:
- DA3 可直接预测相机位姿，传统标定需求降低
- 重点转为：**验证 DA3 位姿质量** 和 **LiDAR-相机数据关联**

**输入**:
- `dataset/2026_03_12_20_53_24/rgb/*.png` (RGB 图像)
- `dataset/2026_03_12_20_53_24/depth_da3/*.npy` (DA3 深度)
- `dataset/2026_03_12_20_53_24/poses_da3/*.json` (DA3 位姿)
- `dataset/2026_03_12_20_53_24/lidar/*.json` (LiDAR 点云)
- `dataset/2026_03_12_20_53_24/poses.json` (仿真真值位姿)

**输出**:
- `dataset/2026_03_12_20_53_24/calibration/validation_report.json` (验证报告)
  ```json
  {
    "da3_pose_accuracy": {
      "mean_position_error": 0.05,  // 米
      "mean_rotation_error": 1.2,   // 度
      "max_position_error": 0.15,
      "status": "good"  // good/fair/poor
    },
    "lidar_depth_consistency": {
      "mean_error": 0.08,
      "std_error": 0.05,
      "status": "good"
    },
    "recommended_pose_source": "da3_fused"  // da3 / simulation / fused
  }
  ```
- `dataset/2026_03_12_20_53_24/calibration/lidar_to_camera_transform.json` (LiDAR-相机外参)
- `dataset/2026_03_12_20_53_24/calibration/projection_vis/*.png` (投影验证图)

**技术方案**:

1. **LiDAR-深度配准** (替代传统标定)
   ```python
   def align_lidar_to_depth(lidar_points, depth_map, camera_intrinsics):
       """
       将 LiDAR 点云与 DA3 深度图配准，求解 LiDAR-相机外参

       原理：
       - DA3 提供深度图 (已融合仿真真值)
       - LiDAR 提供稀疏但精确的点云
       - ICP/点云配准求解外参
       """
       # 深度图转点云
       depth_points = depth_to_pointcloud(depth_map, camera_intrinsics)

       # 提取边缘特征（海冰边界）
       depth_edges = extract_edge_points(depth_points)
       lidar_edges = extract_edge_points(lidar_points)

       # ICP 配准
       from sklearn.neighbors import NearestNeighbors
       from scipy.spatial.transform import Rotation

       # 初始估计：单位矩阵（假设LiDAR和相机接近同位置）
       R_init = np.eye(3)
       t_init = np.array([0.0, 0.0, 0.0])

       # ICP 迭代优化
       R_opt, t_opt = icp_registration(lidar_edges, depth_edges, R_init, t_init)

       return R_opt, t_opt
   ```

2. **DA3 位姿质量验证**
   ```python
   def validate_da3_poses(poses_da3, poses_sim, lidar_data):
       """
       验证 DA3 预测的位姿质量

       三个验证维度：
       1. 与仿真位姿对比 (绝对精度)
       2. LiDAR-深度一致性 (相对精度)
       3. 轨迹平滑性 (时序一致性)
       """
       report = {}

       # 验证1: 与仿真位姿对比
       position_errors = []
       rotation_errors = []
       for da3_pose, sim_pose in zip(poses_da3, poses_sim):
           pos_err = np.linalg.norm(da3_pose[:3, 3] - sim_pose[:3, 3])
           rot_err = rotation_matrix_distance(da3_pose[:3, :3], sim_pose[:3, :3])
           position_errors.append(pos_err)
           rotation_errors.append(rot_err)

       report['da3_pose_accuracy'] = {
           'mean_position_error': np.mean(position_errors),
           'mean_rotation_error': np.mean(rotation_errors),
           'max_position_error': np.max(position_errors),
           'status': 'good' if np.mean(position_errors) < 0.1 else 'fair' if np.mean(position_errors) < 0.3 else 'poor'
       }

       # 验证2: LiDAR-深度一致性
       lidar_depth_errors = []
       for i, (lidar, depth, pose) in enumerate(zip(lidar_data, depth_maps, poses_da3)):
           # 投影 LiDAR 到图像
           projected = project_lidar_to_image(lidar, K, pose)
           # 对比深度值
           for pt_img, pt_3d in projected:
               if is_valid_projection(pt_img, depth.shape):
                   depth_lidar = pt_3d[2]
                   depth_da = depth[int(pt_img[1]), int(pt_img[0])]
                   lidar_depth_errors.append(abs(depth_lidar - depth_da))

       report['lidar_depth_consistency'] = {
           'mean_error': np.mean(lidar_depth_errors),
           'std_error': np.std(lidar_depth_errors),
           'status': 'good' if np.mean(lidar_depth_errors) < 0.1 else 'fair'
       }

       # 验证3: 轨迹平滑性
       trajectory_jerk = compute_trajectory_smoothness(poses_da3)
       report['trajectory_smoothness'] = {
           'jerk_score': trajectory_jerk,
           'status': 'good' if trajectory_jerk < 0.5 else 'fair'
       }

       return report
   ```

3. **位姿融合决策**
   ```python
   def select_best_pose_source(validation_report):
       """
       根据验证报告选择最佳位姿源

       决策逻辑：
       - 如果 DA3 位姿误差 < 阈值：使用 DA3（更平滑，多视图一致）
       - 如果 DA3 误差较大：使用仿真位姿（真值）
       - 如果误差中等：融合两者
       """
       pos_err = validation_report['da3_pose_accuracy']['mean_position_error']

       if pos_err < 0.05:  # 5cm
           return 'da3', poses_da3
       elif pos_err < 0.15:  # 15cm
           # 融合：平滑的DA3轨迹 + 绝对位置修正
           poses_fused = fuse_poses(poses_da3, poses_sim, alpha=0.7)
           return 'da3_fused', poses_fused
       else:
           return 'simulation', poses_sim
   ```

4. **投影可视化验证**
   ```python
   def visualize_lidar_projection(rgb, lidar_points, depth_map, K, pose):
       """可视化 LiDAR 投影到 RGB 图像，验证对齐质量"""
       vis_img = rgb.copy()

       # 投影 LiDAR 点
       projected = project_lidar_to_image(lidar_points, K, pose)

       # 根据深度误差着色
       for pt_img, pt_3d in projected:
           x, y = int(pt_img[0]), int(pt_img[1])
           if 0 <= x < rgb.shape[1] and 0 <= y < rgb.shape[0]:
               depth_lidar = pt_3d[2]
               depth_map_val = depth_map[y, x]
               error = abs(depth_lidar - depth_map_val)

               # 颜色：绿色=误差小，红色=误差大
               color = (0, 255, 0) if error < 0.1 else (0, 255, 255) if error < 0.3 else (0, 0, 255)
               cv2.circle(vis_img, (x, y), 2, color, -1)

       return vis_img
   ```

**与传统标定的区别**:

| 传统方法 | DA3时代新方法 |
|----------|---------------|
| 需要标定板或特定场景 | 利用DA3预测的深度和位姿 |
| 离线计算外参 | 在线验证+必要时优化 |
| 重点：求解外参矩阵 | 重点：验证数据一致性 |
| 输入：标定数据 | 输入：DA3输出 + 仿真真值 |

**预期输出**:
- 验证报告：DA3位姿质量评估
- 推荐位姿源：da3 / simulation / da3_fused
- LiDAR-相机外参（如需要）
- 投影验证可视化

---

### Task 4.4: 感知层数据整合

**目标**: 整合所有感知输出，生成标准格式的训练数据

**输入**: Task 4.1-4.3 的所有输出

**输出**:
```
dataset/2026_03_12_20_53_24/
├── rgb/                    # 原始 RGB
├── depth/                  # 原始仿真 Depth
├── depth_fused/            # 融合后的优化 Depth
├── segmentation/           # SAM 3 实例分割
├── segmentation_colored/   # 彩色可视化分割
├── lidar/                  # LiDAR 点云
├── calibration/            # 标定参数
└── integrated/             # 整合后的统一格式
    ├── frame_0001.npz      # 每帧一个文件，包含所有模态
    └── metadata.json       # 数据集元信息
```

**技术方案**:

1. **数据整合脚本** (`4-4_integrate_perception_data.py`)
   ```python
   def integrate_frame(frame_id, rgb, depth_fused, segmentation, lidar, calibration):
       """将多模态数据整合为统一格式"""
       data = {
           'rgb': rgb,                    # HxWx3 uint8
           'depth': depth_fused,          # HxW float32 (米)
           'segmentation': segmentation,  # HxW int32 (实例ID)
           'lidar': lidar,                # Nx3 float32
           'camera_intrinsics': calibration['K'],
           'camera_extrinsics': calibration['pose'],
       }
       np.savez_compressed(f'integrated/frame_{frame_id:04d}.npz', **data)
   ```

2. **数据验证**
   - 检查所有模态尺寸一致性
   - 验证分割掩码与 RGB 对齐
   - 验证深度图与 LiDAR 投影对齐

---

## 执行计划

### 推荐执行顺序（基于DA3能力优化）

```
Phase 4.2 (Depth Anything 3)  ← 优先，提供深度+位姿+3DGS参数
        ↓
Phase 4.3 (验证与标定)        ← 验证DA3输出质量，必要时优化
        ↓
Phase 4.1 (SAM 3 分割)        ← 实例分割（可并行）
        ↓
Phase 4.4 (数据整合)          ← 整合所有输出
```

**新执行顺序理由**:
1. **DA3 优先**: DA3 同时输出深度、位姿、3DGS参数，是Phase 4的核心
2. **验证其次**: 基于DA3输出验证位姿质量，决定使用策略
3. **SAM 3 随后**: 分割相对独立，可与4.2-4.3并行
4. **整合最后**: 依赖前三项输出

**并行策略**:
```
主线:    4.2 ──→ 4.3 ──→ 4.4
          ↓
并行:    4.1 (SAM 3，可与4.2同时运行)
```

### 时间估算

| 任务 | 预计时间 | 主要耗时环节 |
|------|----------|--------------|
| 4.2 Depth Anything V2 | 20分钟 | 下载权重 (300MB) |
| 4.3 相机-LiDAR 标定 | 30分钟 | 算法调试 |
| 4.1 SAM 3 | 40分钟 | 申请权限 + 下载 |
| 4.4 数据整合 | 15分钟 | 数据验证 |
| **总计** | **~2小时** | |

---

## 风险与备选方案

### 风险 1: SAM 3 权限申请受阻

**可能性**: 中
**影响**: 高
**应对**:
- 使用 SAM 2 作为备选
- 或使用传统分割方法（如 Mask R-CNN）
- 或手动标注少量数据作为种子

### 风险 2: DA3 模型过大显存不足

**可能性**: 中
**影响**: 高
**应对**:
- 使用 DA3-LARGE (0.35B) 替代 GIANT-LARGE (1.4B)
- 或使用 DA3MONO-LARGE 单目版本
- 或使用 DA2 作为备选

### 风险 3: DA3 位姿预测不准确

**可能性**: 中
**影响**: 中
**应对**:
- 回退到仿真位姿（真值）
- 或使用融合策略 (DA3 + Simulation)
- 或使用传统COLMAP标定

### 风险 4: CUDA 版本不兼容

**可能性**: 低
**影响**: 中
**应对**:
- SAM 3 要求 CUDA 12.6+，如不满足则使用 SAM 2
- DA3 兼容性较好，支持 CPU 推理（慢）

### 风险 5: 海冰分割效果不佳

**可能性**: 中
**影响**: 高
**应对**:
- 使用文本提示 "sea ice", "ice floe", "floating ice"
- 调整置信度阈值
- 后处理合并小区域

---

## 文件结构规划

```
ASVSim_zsh/
├── models/                          # 预训练模型权重
│   ├── sam3/
│   │   └── sam3.pt                 # SAM 3 权重 (需申请)
│   └── depth_anything_v2/
│       └── depth_anything_v2_vitl.pth
│
├── perception/                      # Phase 4 感知模块
│   ├── __init__.py
│   ├── sam3_segmentor.py           # SAM 3 封装
│   ├── depth_estimator.py          # DA2 封装
│   └── calibrator.py               # 标定算法
│
├── scripts/                         # Phase 4 执行脚本
│   ├── 4-1_sam3_segmentation.py
│   ├── 4-2_depth_anything_v2.py
│   ├── 4-3_camera_lidar_calibration.py
│   └── 4-4_integrate_perception_data.py
│
├── dataset/                         # 数据目录
│   └── 2026_03_12_20_53_24/
│       ├── rgb/
│       ├── depth/
│       ├── lidar/
│       ├── segmentation/           # 新生成
│       ├── depth_fused/            # 新生成
│       ├── calibration/            # 新生成
│       └── integrated/             # 新生成
│
└── analysis_records/
    └── 2026-03-12-5_Phase4_执行记录.md
```

---

## 验证清单

### Task 4.1 验证
- [ ] SAM 3 成功加载
- [ ] 对单张图像生成分割掩码
- [ ] 掩码与 RGB 对齐
- [ ] 能区分海冰/海水/天空

### Task 4.2 验证
- [ ] DA2 成功加载
- [ ] 生成相对深度图
- [ ] 深度图与仿真深度尺度对齐
- [ ] 融合深度质量提升

### Task 4.3 验证
- [ ] 标定参数收敛
- [ ] 重投影误差 < 5cm
- [ ] LiDAR 点投影到图像对齐

### Task 4.4 验证
- [ ] 所有帧整合完成
- [ ] 数据格式符合 3DGS 输入要求
- [ ] 无缺失或损坏文件

---

## 与 Phase 5 (3DGS) 的衔接

Phase 4 的输出将直接作为 Phase 5 的输入：

```
Phase 4 输出                         Phase 5 输入
────────────────────────────────────────────────────────
integrated/frame_*.npz        →  3DGS 训练数据
├── rgb (HxWx3)               →  图像
├── depth (HxW)               →  深度监督
├── segmentation (HxW)        →  实例掩码（可选，用于分割3DGS）
├── camera_intrinsics         →  相机内参
├── camera_extrinsics         →  相机位姿（来自DA3/仿真/融合）
└── gaussians_init.ply        →  DA3 提供的3DGS初始化（如可用）
```

**DA3 的潜在加速**:
- DA3 可直接输出 3DGS 渲染参数，可能**跳过 Phase 5 的初始化阶段**
- 如果 DA3 位姿质量高，可直接用于训练，无需COLMAP

**备选方案**:
- 如果 DA3 输出不稳定，回退到传统COLMAP+3DGS流程

---

*规划创建时间: 2026-03-12*
*版本: Phase 4 Plan v1.0*
