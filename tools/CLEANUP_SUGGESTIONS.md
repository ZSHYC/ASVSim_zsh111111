# Tools 文件夹清理建议与 test_output 位置问题分析

**日期**: 2026-03-13
**分析对象**: `tools/` 文件夹

---

## 第一部分：test_output 位置问题 ❗

### 问题描述

**当前状态**:
```
ASVSim_zsh/
├── tools/
│   ├── test_output/          ❌ 不应该在这里！
│   │   ├── da3_batch_*/      # 202MB
│   │   └── sam3_batch_*/     # 135MB
│   └── *.py
└── test_output/              ✅ 应该在这里！
    └── ...
```

### 原因分析

脚本中的输出路径使用了相对路径：
```python
output_dir = os.path.join('test_output', f'da3_batch_{dataset_name}')
# 当脚本在 tools/ 目录运行时，创建 tools/test_output/
```

当在 `tools/` 目录运行脚本时，`test_output` 创建在 `tools/` 下。
当在项目根目录运行脚本时，`test_output` 创建在项目根目录。

### 解决方案

#### 方案 1：移动现有数据（推荐）

将 `tools/test_output/` 移动到项目根目录：

```bash
# 在项目根目录执行
mv tools/test_output/da3_batch_2026_03_13_01_50_19 test_output/
mv tools/test_output/sam3_batch_2026_03_13_01_50_19 test_output/
```

然后删除空的 `tools/test_output/` 目录。

#### 方案 2：修改脚本路径

修改所有脚本，使用绝对路径：
```python
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_dir = os.path.join(PROJECT_ROOT, 'test_output', f'da3_batch_{dataset_name}')
```

---

## 第二部分：Tools 文件分析

### 当前文件清单

| 文件 | 大小 | 用途 | 状态评估 |
|------|------|------|----------|
| `analyze_depth_alignment.py` | 12K | 深度对齐分析 | ⭐ 保留 |
| `batch_process_da3.py` | 15K | DA3 批量深度估计 | ⭐ 保留 |
| `batch_segment_sam3.py` | 11K | SAM 3 批量分割 | ⭐ 保留 |
| `download_models_phase4.py` | 4.2K | 模型下载 | ⚠️ 可删除 |
| `generate_segmentation.py` | 4.4K | ASVSim 分割生成 | ⭐ 保留 |
| `test_da3_cpu.py` | 6.8K | DA3 CPU 测试 | ⚠️ 可删除 |
| `test_da3_inference.py` | 11K | DA3 推理测试 | ⚠️ 可删除 |
| `test_da3_official.py` | 9.4K | DA3 GPU 测试 | ⚠️ 可删除 |
| `test_models.py` | 7.5K | 模型加载验证 | ⚠️ 可删除 |
| `validate_da3_poses.py` | 16K | DA3 位姿验证 | ⭐ 保留 |
| `validate_dataset.py` | 8.7K | 数据集验证 | ⭐ 保留 |
| `validate_sam3_masks.py` | 12K | SAM 3 掩码验证 | ⭐ 保留 |
| `verify_camera_settings.py` | 3.8K | 相机设置验证 | ⭐ 保留 |
| `verify_gpu_support.py` | 1.7K | GPU 验证 | ⭐ 保留 |
| `CLEANUP_RECORD.md` | - | 清理记录 | ⭐ 保留 |

### 可以删除的文件（测试脚本）

以下文件为**一次性测试脚本**，已完成使命，可以删除：

1. **download_models_phase4.py** (4.2K)
   - 用途：Phase 4 初始时下载模型
   - 状态：模型已下载完成
   - 建议：🗑️ 删除

2. **test_da3_cpu.py** (6.8K)
   - 用途：测试 DA3 CPU 推理
   - 状态：已升级 GPU，不再需要 CPU 版本
   - 建议：🗑️ 删除

3. **test_da3_inference.py** (11K)
   - 用途：早期 DA3 测试
   - 状态：已被 `batch_process_da3.py` 替代
   - 建议：🗑️ 删除

4. **test_da3_official.py** (9.4K)
   - 用途：DA3 GPU 测试
   - 状态：已被 `batch_process_da3.py` 替代
   - 建议：🗑️ 删除

5. **test_models.py** (7.5K)
   - 用途：模型加载验证
   - 状态：Phase 4 初期使用，已完成
   - 建议：🗑️ 删除

**可释放空间**: ~38.9K (很小，主要是整理)

### 必须保留的核心脚本

以下脚本是**生产级工具**，需要保留：

| 脚本 | 用途 | 优先级 |
|------|------|--------|
| `batch_process_da3.py` | 批量深度估计 | 🔴 高 |
| `batch_segment_sam3.py` | 批量分割 | 🔴 高 |
| `validate_sam3_masks.py` | 掩码质量验证 | 🟡 中 |
| `validate_da3_poses.py` | 位姿质量验证 | 🟡 中 |
| `analyze_depth_alignment.py` | 深度对齐分析 | 🟡 中 |
| `generate_segmentation.py` | ASVSim 分割 | 🟢 低 |
| `validate_dataset.py` | 数据集验证 | 🟢 低 |
| `verify_camera_settings.py` | 相机验证 | 🟢 低 |
| `verify_gpu_support.py` | GPU 验证 | 🟢 低 |

---

## 第三部分：清理执行计划

### 步骤 1：移动 test_output（立即执行）

```bash
# 1. 确认数据存在
ls tools/test_output/
# 应该看到：da3_batch_2026_03_13_01_50_19  sam3_batch_2026_03_13_01_50_19

# 2. 移动 DA3 输出
mv tools/test_output/da3_batch_2026_03_13_01_50_19 test_output/

# 3. 移动 SAM 3 输出
mv tools/test_output/sam3_batch_2026_03_13_01_50_19 test_output/

# 4. 删除空的 tools/test_output/
rmdir tools/test_output

# 5. 验证
ls test_output/
# 应该看到：
# - da3_batch_2026_03_13_01_50_19 (来自 tools/)
# - sam3_batch_2026_03_13_01_50_19 (来自 tools/)
# - da3_cpu (原有的)
# - da3_official (原有的)
# - ...
```

**涉及数据量**: 337 MB
- DA3: 202 MB (126张深度图)
- SAM 3: 135 MB (94张分割)

### 步骤 2：删除测试脚本（可选）

```bash
# 删除一次性测试脚本
cd tools/
rm download_models_phase4.py
rm test_da3_cpu.py
rm test_da3_inference.py
rm test_da3_official.py
rm test_models.py

# 验证剩余文件
ls *.py
# 应该剩下 9 个核心脚本
```

**可释放空间**: ~39K (可忽略不计)

### 步骤 3：修改脚本路径（推荐）

修改核心脚本，使用绝对路径避免 future 问题：

```python
# 在 batch_process_da3.py 和 batch_segment_sam3.py 顶部添加：
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_dir = os.path.join(PROJECT_ROOT, 'test_output', ...)
```

---

## 第四部分：清理后结构

### 清理后的 tools/ 目录

```tools/
├── analyze_depth_alignment.py      # 深度对齐分析
├── batch_process_da3.py            # DA3 批量深度估计 ⭐核心
├── batch_segment_sam3.py           # SAM 3 批量分割 ⭐核心
├── generate_segmentation.py        # ASVSim 分割生成
├── validate_da3_poses.py           # DA3 位姿验证
├── validate_dataset.py             # 数据集验证
├── validate_sam3_masks.py          # SAM 3 掩码验证
├── verify_camera_settings.py       # 相机设置验证
├── verify_gpu_support.py           # GPU 验证
└── CLEANUP_RECORD.md               # 清理记录
```

**文件数**: 14 → 9 (删除 5 个测试脚本)

### 移动后的 test_output/ 目录

```test_output/
├── da3_batch_2026_03_13_01_50_19/   # 从 tools/ 移动 (202MB)
│   ├── depth/
│   ├── depth_vis/
│   ├── conf/
│   ├── extrinsics/
│   ├── intrinsics/
│   └── ...
├── sam3_batch_2026_03_13_01_50_19/  # 从 tools/ 移动 (135MB)
│   ├── segmentation/
│   └── segmentation_vis/
├── da3_cpu/                         # 原有
├── da3_official/                    # 原有
├── depth_alignment_analysis/        # 原有
├── pose_analysis/                   # 原有
└── sam3_mask_validation/            # 原有
```

---

## 第五部分：注意事项

### ⚠️ 重要提醒

1. **先移动再删除**
   - 确保数据移动成功后再删除 tools/test_output/
   - 建议在移动前备份或确认数据完整性

2. **脚本路径问题**
   - 修改后的脚本需要在项目根目录运行
   - 或者使用绝对路径

3. **不要删除 core 脚本**
   - `batch_process_da3.py` 和 `batch_segment_sam3.py` 是核心生产力工具
   - 后续可能还需要重新运行

### 📋 验证清单

- [ ] `tools/test_output/` 已移动到 `test_output/`
- [ ] `tools/test_output/` 空目录已删除
- [ ] 可选：删除 5 个测试脚本
- [ ] 可选：修改脚本使用绝对路径
- [ ] 验证核心脚本仍可正常运行

---

## 附录：文件保留/删除速查表

| 文件 | 操作 | 原因 |
|------|------|------|
| `batch_process_da3.py` | ⭐ 保留 | 核心工具 |
| `batch_segment_sam3.py` | ⭐ 保留 | 核心工具 |
| `validate_sam3_masks.py` | ⭐ 保留 | 质量验证 |
| `validate_da3_poses.py` | ⭐ 保留 | 质量验证 |
| `analyze_depth_alignment.py` | ⭐ 保留 | 分析工具 |
| `generate_segmentation.py` | ⭐ 保留 | ASVSim 工具 |
| `validate_dataset.py` | ⭐ 保留 | 数据验证 |
| `verify_camera_settings.py` | ⭐ 保留 | 配置验证 |
| `verify_gpu_support.py` | ⭐ 保留 | 环境验证 |
| `download_models_phase4.py` | 🗑️ 删除 | 一次性使用 |
| `test_da3_cpu.py` | 🗑️ 删除 | 测试脚本 |
| `test_da3_inference.py` | 🗑️ 删除 | 测试脚本 |
| `test_da3_official.py` | 🗑️ 删除 | 测试脚本 |
| `test_models.py` | 🗑️ 删除 | 测试脚本 |
| `CLEANUP_RECORD.md` | ⭐ 保留 | 文档记录 |
| `tools/test_output/` | 🗑️ 删除 | 移动到根目录 |

---

**分析完成时间**: 2026-03-13
**数据量**: tools/test_output/ 占用 337 MB
**建议操作**: 移动数据 + 可选删除测试脚本
