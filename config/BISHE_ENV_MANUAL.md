# bishe 环境使用手册

**环境名称**: bishe
**Python 版本**: 3.12.13
**PyTorch 版本**: 2.6.0+cu126
**CUDA 版本**: 12.6
**GPU**: RTX 5070 Ti (12GB)
**创建时间**: 2026-03-12

---

## 目录结构

### C 盘 - 代码和配置
```
C:\Users\zsh\Desktop\ASVSim_zsh\          ← 项目代码
├── config\                               ← 配置文件
│   ├── model_paths.yaml                  ← 模型路径配置
│   └── setup_bishe_env.bat              ← 环境部署脚本
├── tools\                                ← 工具脚本
│   ├── download_models.py               ← 模型下载助手
│   └── download_models_phase4.py        ← Phase 4 模型下载
├── perception\                           ← Phase 4 感知模块代码
│   └── (待创建)
└── analysis_records\                     ← 分析记录文档
```

### D 盘 - 模型和数据（大文件）
```
D:\ASVSim_models\                         ← 模型存储
├── sam3\                                 ← SAM 3 模型
│   └── sam3.pt                          ← (~850MB, 需权限)
├── depth_anything_3\                     ← DA3 模型
│   ├── model.safetensors                ← (~1.4GB, DA3-LARGE)
│   └── model.safetensors                ← (~350MB, DA3-MONO)
├── cache\                                ← 下载缓存
│   ├── hub\                             ← HuggingFace 缓存
│   └── torch\                           ← PyTorch 缓存
├── datasets\                             ← 数据集备份
├── logs\                                 ← 日志文件
└── temp\                                 ← 临时文件
```

### Conda 环境
```
D:\miniforge3\envs\bishe\                 ← Conda 环境目录
```

---

## 快速开始

### 1. 激活环境

```bash
conda activate bishe
```

### 2. 验证安装

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'GPU: {torch.cuda.get_device_name(0)}'); print(f'Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB')"
```

**期望输出**:
```
PyTorch: 2.6.0+cu126
GPU: NVIDIA GeForce RTX 5070 Ti Laptop GPU
Memory: 12.82 GB
```

### 3. 检查模型路径

```bash
python -c "import os; print('HF_HOME:', os.environ.get('HF_HOME')); print('TORCH_HOME:', os.environ.get('TORCH_HOME'))"
```

**期望输出**:
```
HF_HOME: D:\ASVSim_models\cache\hub
TORCH_HOME: D:\ASVSim_models\cache\torch
```

---

## 模型下载

### Depth Anything 3 (公开，可立即下载)

**方法 1: 浏览器下载**
1. 访问 https://huggingface.co/depth-anything/DA3-LARGE-1.1
2. 点击 "Files and versions"
3. 下载 `model.safetensors` (约 1.4GB)
4. 放置到 `D:\ASVSim_models\depth_anything_3\`

**方法 2: 命令行下载**
```bash
conda activate bishe
huggingface-cli download depth-anything/DA3-LARGE-1.1 --local-dir D:\ASVSim_models\depth_anything_3
```

### SAM 3 (需权限，等待批准)

**步骤 1: 申请权限**
1. 访问 https://huggingface.co/facebook/sam3
2. 点击 "Access repository"
3. 填写申请理由，提交
4. 等待 Meta AI 批准（通常 1-3 天）

**步骤 2: 登录 Hugging Face**
```bash
conda activate bishe
huggingface-cli login
# 输入你的 Access Token
```

**步骤 3: 下载模型**
```bash
huggingface-cli download facebook/sam3 --local-dir D:\ASVSim_models\sam3
```

**备选方案**:
如果 SAM 3 权限等待时间长，可以先使用 SAM 2:
```bash
pip install git+https://github.com/facebookresearch/sam2.git
```

---

## 模型验证

下载完成后，验证模型文件:

```bash
conda activate bishe
python << 'EOF'
import os

models = {
    'DA3-LARGE': r'D:\ASVSim_models\depth_anything_3\model.safetensors',
    'SAM3': r'D:\ASVSim_models\sam3\sam3.pt'
}

print('='*60)
print('Model Verification')
print('='*60)

for name, path in models.items():
    if os.path.exists(path):
        size = os.path.getsize(path) / (1024**3)
        print(f'[OK] {name}: {size:.2f} GB')
        print(f'     Path: {path}')
    else:
        print(f'[MISSING] {name}')
        print(f'     Expected: {path}')

print('='*60)
EOF
```

---

## 显存管理

### 12GB 显存使用建议

**单模型推理**:
- DA3-LARGE: ~4GB 显存
- SAM 3: ~3GB 显存
- 可以同时加载两个模型 (~7GB)，有余量

**显存清理**:
```python
import torch

# 清理显存缓存
torch.cuda.empty_cache()

# 查看显存使用
print(f"Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print(f"Reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")
```

**混合精度推理** (节省显存 + 加速):
```python
from torch.cuda.amp import autocast

with autocast():
    output = model(input)
```

---

## 环境变量说明

### 已配置的环境变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `HF_HOME` | `D:\ASVSim_models\cache\hub` | HuggingFace 模型缓存 |
| `TORCH_HOME` | `D:\ASVSim_models\cache\torch` | PyTorch 模型缓存 |
| `PYTHONPATH` | `C:\Users\zsh\Desktop\ASVSim_zsh` | Python 模块搜索路径 |

### 查看环境变量

```bash
conda activate bishe
conda env config vars list
```

### 临时设置环境变量

```bash
# Windows CMD
set HF_HOME=D:\ASVSim_models\cache\hub

# Windows PowerShell
$env:HF_HOME="D:\ASVSim_models\cache\hub"

# Bash (Git Bash)
export HF_HOME="D:\ASVSim_models\cache\hub"
```

---

## 常见问题

### Q1: 激活环境失败

**症状**:
```
CondaError: Run 'conda init' before 'conda activate'
```

**解决**:
```bash
conda init bash  # 或 conda init powershell
# 重启终端
conda activate bishe
```

### Q2: CUDA 不可用

**症状**:
```
torch.cuda.is_available() returns False
```

**排查**:
1. 检查 NVIDIA 驱动: `nvidia-smi`
2. 检查 PyTorch CUDA 版本: `python -c "import torch; print(torch.version.cuda)"`
3. 重新安装 PyTorch:
   ```bash
   pip uninstall torch torchvision torchaudio
   pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126
   ```

### Q3: 显存不足 (OOM)

**症状**:
```
RuntimeError: CUDA out of memory
```

**解决**:
```python
# 1. 减小输入尺寸
input = input.resize((518, 518))  # 而非原始尺寸

# 2. 使用混合精度
with torch.cuda.amp.autocast():
    output = model(input)

# 3. 分批处理
for batch in data_loader:
    output = model(batch)
    torch.cuda.empty_cache()
```

### Q4: 模型下载慢

**症状**: HuggingFace 下载速度很慢

**解决** (使用镜像):
```bash
# 设置镜像地址
export HF_ENDPOINT=https://hf-mirror.com

# 或者使用代理
huggingface-cli download --resume-download model_name --local-dir path
```

### Q5: 找不到模型文件

**症状**:
```
FileNotFoundError: Model file not found
```

**检查**:
1. 确认模型已下载到 `D:\ASVSim_models\`
2. 检查文件名是否正确 (`.safetensors` vs `.pt`)
3. 检查 `model_paths.yaml` 配置

---

## 性能优化

### PyTorch 性能设置

创建 `C:\Users\zsh\.ptconfig`:
```python
import torch

# 启用 TF32 (加速计算)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# 启用 cudnn 基准测试 (选择最优算法)
torch.backends.cudnn.benchmark = True

# 设置确定性 (可复现性 vs 性能)
# torch.backends.cudnn.deterministic = True
```

### 在代码中自动加载配置

```python
import os
config_path = os.path.expanduser('~/.ptconfig')
if os.path.exists(config_path):
    exec(open(config_path).read())
```

---

## 备份和恢复

### 导出环境配置

```bash
conda activate bishe
conda env export > bishe_env_backup.yml
pip freeze > bishe_requirements.txt
```

### 恢复环境

```bash
# 从 yml 恢复
conda env create -f bishe_env_backup.yml

# 从 requirements 恢复
conda create -n bishe python=3.12
conda activate bishe
pip install -r bishe_requirements.txt
```

### 删除环境

```bash
conda deactivate
conda remove -n bishe --all
```

---

## 相关文档

- **部署日志**: `analysis_records/2026-03-12-8_Phase4环境部署执行日志.md`
- **RTX 5070 Ti 指南**: `analysis_records/2026-03-12-6_RTX5070Ti环境部署指南.md`
- **Phase 4 规划**: `.claude/plans/noble-petting-bonbon.md`

---

## 联系和支持

- **Hugging Face**: https://huggingface.co/
- **PyTorch 文档**: https://pytorch.org/docs/
- **SAM 3 GitHub**: https://github.com/facebookresearch/sam3
- **Depth Anything 3**: https://github.com/ByteDance-Seed/Depth-Anything-3

---

*文档创建: 2026-03-12*
*适用环境: bishe (Python 3.12, PyTorch 2.6, CUDA 12.6)*
