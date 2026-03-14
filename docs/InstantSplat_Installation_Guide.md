# InstantSplat 详细安装配置指南

**文档版本**: v1.0
**创建时间**: 2026-03-14
**适用平台**: Windows 10/11
**CUDA版本**: 12.1
**Python版本**: 3.10.13

---

## 目录

1. [项目简介](#1-项目简介)
2. [环境要求](#2-环境要求)
3. [安装步骤](#3-安装步骤)
4. [常见问题与解决方案](#4-常见问题与解决方案)
5. [验证安装](#5-验证安装)
6. [使用方法](#6-使用方法)
7. [ASVSim项目专用配置](#7-asvsim项目专用配置)

---

## 1. 项目简介

**InstantSplat** 是 NVIDIA 实验室开源的稀疏视角三维重建框架，能够在几秒钟内从少量未标定图像重建3D Gaussian Splatting场景。

### 核心特性

- ✅ **无需预先知道相机位姿** - 自动从照片估计
- ✅ **端到端联合优化** - MASt3R位姿估计 + 3DGS联合训练
- ✅ **快速重建** - < 2分钟完成126张图像的重建
- ✅ **支持多种GS变体** - 3D-GS, 2D-GS, Mip-Splatting

### 技术架构

```
输入图像 (126张极地照片)
    ↓
MASt3R几何基础模型 (秒级位姿估计)
    ↓
初始点云 + 相机位姿
    ↓
3D Gaussian Splatting初始化
    ↓
联合优化 (位姿 + 高斯参数)
    ↓
输出: 可渲染的3D高斯场景
```

---

## 2. 环境要求

### 2.1 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **GPU** | NVIDIA RTX 3060 (12GB) | RTX 4070/5070 Ti (16GB+) |
| **显存** | 8GB | 16GB+ |
| **内存** | 16GB | 32GB+ |
| **硬盘** | 10GB可用空间 | SSD 50GB+ |

### 2.2 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| **Windows** | 10/11 | 操作系统 |
| **CUDA Toolkit** | 12.1 | GPU计算 |
| **Python** | 3.10.13 | 编程环境 |
| **Conda** | 最新版 | 环境管理 |
| **Git** | 最新版 | 代码克隆 |

### 2.3 前置检查清单

在安装前，请确认以下事项：

```bash
# 检查NVIDIA驱动
nvidia-smi
# 应显示CUDA Version: 12.1 或更高

# 检查Git
git --version

# 检查Conda
conda --version
```

---

## 3. 安装步骤

### 3.1 克隆仓库（含子模块）

```bash
# 进入项目目录
cd C:\Users\zsh\Desktop\ASVSim_zsh

# 克隆InstantSplat仓库（--recursive包含子模块）
git clone --recursive https://github.com/NVlabs/InstantSplat.git

# 进入目录
cd InstantSplat
```

**子模块说明**：
- `submodules/diff-gaussian-rasterization` - 可微高斯光栅化
- `submodules/simple-knn` - K近邻搜索加速
- `submodules/fused-ssim` - 融合SSIM损失函数
- `mast3r/` - MASt3R位姿估计模块
- `dust3r/` - DUSt3R几何基础模型
- `croco/` - 跨视图对应模型

### 3.2 创建Conda环境

```bash
# 创建Python 3.10.13环境（包含cmake）
conda create -n instantsplat python=3.10.13 cmake=3.14.0 -y

# 激活环境
conda activate instantsplat
```

### 3.3 安装PyTorch（CUDA 12.1版本）

```bash
# 安装PyTorch + CUDA 12.1
conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia -y

# 验证安装
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"
```

**预期输出**：
```
PyTorch: 2.5.1
CUDA available: True
CUDA version: 12.1
```

### 3.4 安装Python依赖

```bash
# 安装requirements.txt中的所有依赖
pip install -r requirements.txt
```

**主要依赖包**：
- `torch` / `torchvision` - 深度学习框架
- `roma` - 旋转矩阵运算
- `gradio` - Web界面
- `open3d` - 3D可视化
- `trimesh` - 网格处理
- `plyfile` - PLY文件读写
- `huggingface-hub` - 模型下载

### 3.5 安装CUDA子模块（关键步骤）

**⚠️ 注意：此步骤需要已安装CUDA Toolkit 12.1**

#### 3.5.1 安装CUDA Toolkit（如未安装）

1. 访问：https://developer.nvidia.com/cuda-12-1-0-download-archive
2. 选择：Windows → x86_64 → 10/11 → exe(local)
3. 下载并运行安装程序
4. 重启终端，验证安装：

```bash
nvcc --version
```

**预期输出**：
```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2023 NVIDIA Corporation
Built on Mon Apr 24 19:05:07 Pacific_Daylight_Time_2023
Cuda compilation tools, release 12.1, V12.1.66
```

#### 3.5.2 编译安装Submodules

```bash
# 设置CUDA环境变量（根据实际安装路径调整）
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1
set PATH=%CUDA_HOME%\bin;%PATH%
set LIB=%CUDA_HOME%\lib\x64;%LIB%

# 验证环境变量
python -c "import os; print(os.environ.get('CUDA_HOME'))"

# 安装simple-knn
pip install submodules/simple-knn --no-build-isolation

# 安装diff-gaussian-rasterization
pip install submodules/diff-gaussian-rasterization --no-build-isolation

# 安装fused-ssim
pip install submodules/fused-ssim --no-build-isolation
```

**安装成功标志**：
```
Successfully installed diff-gaussian-rasterization-0.0.0
Successfully installed simple-knn-0.0.0
Successfully installed fused-ssim-0.0.0
```

### 3.6 编译RoPE CUDA Kernels（可选但推荐）

```bash
# 进入croco目录
cd croco/models/curope/

# 编译CUDA扩展
python setup.py build_ext --inplace

# 返回项目根目录
cd ../../../..
```

**作用**：加速DUSt3R/MASt3R的RoPE位置编码计算

### 3.7 下载MASt3R预训练模型

```bash
# 创建checkpoints目录
mkdir -p mast3r/checkpoints

# 下载预训练权重（约2.4GB）
curl -o mast3r/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth \
  https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth

# 或使用wget（如已安装）
wget https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth -P mast3r/checkpoints/
```

**验证下载**：
```bash
dir mast3r\checkpoints\
# 应显示: MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth (2,447,793 KB)
```

---

## 4. 常见问题与解决方案

### 4.1 CUDA_HOME环境变量未设置

**错误信息**：
```
OSError: CUDA_HOME environment variable is not set. Please set it to your CUDA install root.
```

**解决方案**：
```bash
# 设置CUDA_HOME（根据实际安装路径）
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1
set PATH=%CUDA_HOME%\bin;%PATH%

# 如果CUDA安装在D盘
set CUDA_HOME=D:\CUDA\v12.1
```

### 4.2 编译错误：找不到cl.exe

**错误信息**：
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**解决方案**：
1. 安装Visual Studio 2022 Community（包含C++工具链）
2. 或使用Build Tools for Visual Studio 2022
3. 下载地址：https://visualstudio.microsoft.com/downloads/

### 4.3 PyTorch CUDA版本不匹配

**错误信息**：
```
RuntimeError: CUDA error: no kernel image is available for execution on the device
```

**解决方案**：
```bash
# 检查PyTorch CUDA版本
python -c "import torch; print(torch.version.cuda)"

# 如果不匹配，重新安装
conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia -y --force-reinstall
```

### 4.4 下载模型速度慢/失败

**解决方案**：
```bash
# 使用镜像（如适用）
# 或手动下载后放到 mast3r/checkpoints/ 目录
# 或使用gdown（Google Drive）
pip install gdown
gdown https://drive.google.com/uc?id=MODEL_ID
```

### 4.5 Windows下路径问题

**错误信息**：
```
FileNotFoundError: [WinError 3] The system cannot find the path specified
```

**解决方案**：
```bash
# 使用正斜杠或双反斜杠
# 错误: C:\Users\name\path
# 正确: C:/Users/name/path 或 C:\\Users\\name\\path
```

---

## 5. 验证安装

### 5.1 基础功能验证

```bash
# 激活环境
conda activate instantsplat

# 运行Python测试
python -c "
import torch
import torchvision
from submodules.diff_gaussian_rasterization import GaussianRasterizationSettings, GaussianRasterizer
from submodules.simple_knn._C import distCUDA2
from submodules.fused_ssim import ssim
print('✓ 所有核心模块导入成功')
print(f'✓ PyTorch版本: {torch.__version__}')
print(f'✓ CUDA可用: {torch.cuda.is_available()}')
print(f'✓ CUDA版本: {torch.version.cuda}')
print(f'✓ GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')
"
```

### 5.2 下载示例数据测试

```bash
# 下载示例数据集（来自Hugging Face）
# 访问: https://huggingface.co/datasets/kairunwen/InstantSplat
# 或使用scripts中的示例

# 运行推理脚本（无GT参考，生成插值视频）
bash scripts/run_infer.sh

# 或运行评估脚本（需要GT参考）
bash scripts/run_eval.sh
```

### 5.3 检查模型文件

```bash
# 验证MASt3R模型存在
dir mast3r\checkpoints\

# 验证Python模块安装
pip list | findstr gaussian
pip list | findstr knn
pip list | findstr ssim
```

---

## 6. 使用方法

### 6.1 基本命令结构

```bash
# 基本推理命令
python train.py \
  -s <scene_path> \
  -m <output_path> \
  --iterations 30000 \
  --save_iterations 7000 30000
```

### 6.2 ASVSim数据采集推理

假设你的126张极地照片存储在 `dataset/2026_03_13_01_50_19/rgb`：

```bash
# 准备数据目录结构
mkdir -p assets/examples/asvsim_polar/images

# 复制照片
copy dataset\2026_03_13_01_50_19\rgb\*.png assets\examples\asvsim_polar\images\

# 运行InstantSplat
python train.py \
  -s assets/examples/asvsim_polar \
  -m output/asvsim_polar \
  --iterations 30000 \
  --save_iterations 7000 30000 \
  --checkpoint_iterations 7000 30000
```

### 6.3 关键参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-s` | 必需 | 场景数据路径（包含images/目录） |
| `-m` | 必需 | 模型输出路径 |
| `--iterations` | 30000 | 总训练迭代次数 |
| `--save_iterations` | 7000 30000 | 保存检查点的迭代 |
| `--resolution` | -1 (原始) | 训练图像分辨率 |
| `--sh_degree` | 3 | 球谐函数阶数 |
| `--white_background` | False | 白色背景 |

### 6.4 使用Gradio Web界面

```bash
# 启动Web界面
python -m gradio_interface

# 或使用预训练模型快速测试
python demo.py
```

---

## 7. ASVSim项目专用配置

### 7.1 针对126张极地照片的优化配置

```bash
# 创建项目专用配置
mkdir -p configs/asvsim

# 创建配置文件 configs/asvsim/polar_scene.yaml
```

**推荐配置内容**：
```yaml
# configs/asvsim/polar_scene.yaml
model:
  sh_degree: 3
  source_path: "assets/examples/asvsim_polar"
  model_path: "output/asvsim_polar"
  images: "images"
  resolution: -1  # 使用原始分辨率(640x480)

training:
  iterations: 30000
  save_iterations: [7000, 15000, 30000]
  checkpoint_iterations: [7000, 30000]
  test_iterations: [7000, 15000, 30000]

optimization:
  densify_from_iter: 500
  densify_until_iter: 15000
  densification_interval: 100
  opacity_reset_interval: 3000
  densify_grad_threshold: 0.0002
```

### 7.2 自动化脚本

创建 `run_asvsim_reconstruction.bat`：

```batch
@echo off
chcp 65001

:: 激活环境
call conda activate instantsplat

:: 设置CUDA路径
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1
set PATH=%CUDA_HOME%\bin;%PATH%

:: 进入项目目录
cd /d C:\Users\zsh\Desktop\ASVSim_zsh\InstantSplat

:: 准备数据（如需要）
if not exist "assets\examples\asvsim_polar\images" (
    echo 准备数据...
    mkdir assets\examples\asvsim_polar\images
    xcopy /Y "..\..\dataset\2026_03_13_01_50_19\rgb\*.png" "assets\examples\asvsim_polar\images\"
)

:: 运行重建
echo 开始InstantSplat重建...
python train.py ^
  -s assets/examples/asvsim_polar ^
  -m output/asvsim_polar ^
  --iterations 30000 ^
  --save_iterations 7000 15000 30000 ^
  --checkpoint_iterations 30000 ^
  --resolution -1

echo 重建完成！
pause
```

### 7.3 输出文件说明

运行完成后，`output/asvsim_polar/` 目录结构：

```
output/asvsim_polar/
├── point_cloud/                    # 点云输出
│   ├── iteration_7000/
│   │   └── point_cloud.ply        # 第7000迭代点云
│   └── iteration_30000/
│       └── point_cloud.ply        # 最终点云（用于渲染）
├── cameras.json                    # 估计的相机参数
├── cfg_args                        # 训练配置
├── input.ply                      # 初始点云
└── test/                          # 测试渲染结果
    ├── ours_30000/
    │   ├── gt/                    # 真值图像（如有）
    │   ├── renders/               # 渲染结果
    │   └── metrics.json           # 评估指标
```

### 7.4 查看重建结果

```bash
# 使用Open3D查看点云
python -c "
import open3d as o3d
pcd = o3d.io.read_point_cloud('output/asvsim_polar/point_cloud/iteration_30000/point_cloud.ply')
o3d.visualization.draw_geometries([pcd])
"

# 渲染新视角
python render.py \
  -m output/asvsim_polar \
  --iteration 30000 \
  --skip_train \
  --skip_test \
  --quiet
```

---

## 8. 故障排除检查表

如果运行出现问题，请按以下顺序检查：

- [ ] **环境激活**：是否运行了 `conda activate instantsplat`
- [ ] **CUDA路径**：`echo %CUDA_HOME%` 是否显示正确路径
- [ ] **PyTorch CUDA**：`python -c "import torch; print(torch.cuda.is_available())"` 是否返回True
- [ ] **模型文件**：`dir mast3r\checkpoints\` 是否显示模型文件
- [ ] **数据路径**：`-s` 参数指向的目录是否包含 `images/` 子目录
- [ ] **图像格式**：照片是否为 `.png` 或 `.jpg` 格式
- [ ] **显存充足**：`nvidia-smi` 检查GPU显存是否充足（建议>8GB）

---

## 9. 参考资源

| 资源 | 链接 |
|------|------|
| **InstantSplat GitHub** | https://github.com/NVlabs/InstantSplat |
| **MASt3R GitHub** | https://github.com/naver/mast3r |
| **论文 (arXiv)** | https://arxiv.org/abs/2403.20309 |
| **项目主页** | https://instantsplat.github.io/ |
| **HuggingFace Demo** | https://huggingface.co/spaces/kairunwen/InstantSplat |
| **数据集** | https://huggingface.co/datasets/kairunwen/InstantSplat |
| **CUDA Toolkit** | https://developer.nvidia.com/cuda-12-1-0-download-archive |

---

## 10. 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-03-14 | 初始版本，基于InstantSplat官方文档 |

---

*文档由ASVSim项目自动生成*
*配合 Photo_To_3DGS_No_Pose_Required_Guide.md 使用*
