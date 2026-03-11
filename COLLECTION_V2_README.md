# 多模态数据采集系统v2.0 — 使用指南

## 核心优化策略

本版本针对采集速度慢的问题进行了系统性优化：

### 1. 分辨率优化（640×480）

| 分辨率 | 预估单帧时间 | 质量评价 | 推荐度 |
|--------|-------------|----------|--------|
| 320×240 | ~5s | 过低，不利于3DGS | ❌ |
| **640×480** | ~15s | **平衡速度与质量** | **✓** |
| 1280×720 | ~60s | 高质量但太慢 | ⚠️ |

### 2. 传感器选择（跳过实时Seg）

```
实时采集（耗时）：
  RGB (~15s) + Depth (~15s) + Seg (~15s) = ~45s/帧

优化采集（本方案）：
  RGB (~15s) + Depth (~15s) = ~30s/帧
  Segmentation事后离线生成（节省30%时间）
```

### 3. 关键修复

- **无simPause**：避免CosysAirSim v3.0.1冻结bug
- **无多线程**：避免msgpack-rpc的IOLoop错误
- **重试机制**：单帧失败自动重试3次
- **数据验证**：采集后自动验证完整性

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `3-collect_dataset_v2.py` | **主采集脚本（推荐）** |
| `config/collection_default.json` | 配置文件示例 |
| `tools/validate_dataset.py` | 数据验证工具 |
| `tools/generate_segmentation.py` | 事后生成分割真值 |

---

## 快速开始

### 1. 基础使用（默认配置）

```bash
python 3-collect_dataset_v2.py
```

默认配置：
- 分辨率：640×480
- 帧数：200帧（增加帧数补偿分辨率）
- 轨迹：圆弧（右转）
- 传感器：RGB + Depth + LiDAR + Pose

### 2. 使用自定义配置

```bash
# 编辑配置文件
notepad config/collection_default.json

# 使用配置运行
python 3-collect_dataset_v2.py --config config/collection_default.json
```

### 3. 配置参数说明

```json
{
  "vessel_name": "Vessel1",      // 船只名称
  "num_frames": 200,              // 采集帧数（建议200-300）
  "move_seconds": 0.3,            // 运动间隔
  "thrust": 0.3,                  // 推力
  "angle": 0.6,                   // 转向（0.5直行，0.6右转）
  "trajectory_mode": "circle",    // 轨迹模式：circle/line/random
  "cam_w": 640,                   // 分辨率宽
  "cam_h": 480,                   // 分辨率高
  "max_retries": 3,               // 单帧重试次数
  "max_fail_ratio": 0.2           // 最大允许失败比例
}
```

---

## 高级使用

### 采集后数据验证

```bash
python tools/validate_dataset.py dataset/2026_03_12_10_30_00
```

验证内容：
- 文件数量一致性
- 图像质量（分辨率、像素范围）
- 深度图有效性（NaN比例、范围）
- 位姿连续性

### 事后生成分割真值

如果后续需要Segmentation进行SAM3训练：

```bash
# 全量生成
python tools/generate_segmentation.py dataset/2026_03_12_10_30_00

# 部分生成（例如前50帧）
python tools/generate_segmentation.py dataset/2026_03_12_10_30_00 --start 0 --end 50
```

**注意**：
- 需要ASVSim正在运行
- 船只位置应与采集时一致（或重新定位到对应位置）
- 这是一个简化实现，完整方案需要记录并重放船只轨迹

---

## 输出目录结构

```
dataset/2026_03_12_10_30_00/
├── rgb/                    # RGB图像（BGR格式）
│   ├── 0000.png
│   └── ...
├── depth/                  # 深度图（float32，单位：米）
│   ├── 0000.npy
│   └── ...
├── lidar/                  # LiDAR点云（JSON格式）
│   ├── 0000.json
│   └── ...
├── meta/                   # 元数据
│   ├── collection_config.json    # 采集配置
│   └── collection_report.json    # 采集报告
├── colmap/                 # COLMAP格式（用于3DGS）
│   └── transforms.json
└── poses.json              # 相机位姿（真值）
```

---

## 与后续流程的衔接

### Phase 4: 智能感知（SAM3 + DA3）

```python
# SAM3训练数据
rgb/0000.png          → SAM3输入
segmentation/0000.png → 分割真值（事后生成或实时采集）

# DA3训练数据
rgb/0000.png          → DA3输入
depth/0000.npy        → 深度真值（监督信号）
```

### Phase 5: 3DGS重建

```python
# 直接输入
rgb/              → 纹理输入
poses.json        → 相机位姿（替代COLMAP SfM）
lidar/            → 初始点云（可选）

# 生成COLMAP格式
colmap/transforms.json  → 3DGS训练输入
```

---

## 故障排除

### 问题1: 采集速度仍然很慢（>30s/帧）

可能原因：
- settings.json中Lumen未禁用
- UE5编辑器未切换到"独立游戏"模式
- 其他程序占用GPU资源

解决：
1. 检查settings.json中`LumenGIEnable: false`和`LumenReflectionEnable: false`
2. 使用"Launch"而非"Play"启动ASVSim
3. 关闭UE5编辑器中的其他视口

### 问题2: IOLoop错误

原因：使用了多线程超时（旧版本问题）

解决：
- 使用本版本（v2.0），已移除多线程

### 问题3: 场景冻结

原因：simPause在v3.0.1有bug

解决：
- 本版本不使用simPause
- 或升级ASVSim到v3.3.0+（待验证）

### 问题4: 失败率过高（>20%）

可能原因：
- ASVSim连接不稳定
- 船只位置异常（如搁浅）

解决：
- 检查网络连接
- 重置ASVSim场景
- 调整`max_fail_ratio`容忍度

---

## 技术细节

### 为什么跳过实时Segmentation？

| 传感器 | 渲染开销 | 事后生成可行？ |
|--------|----------|---------------|
| RGB | 高 | 不可行（需要场景状态） |
| Depth | 高 | 不可行（需要场景状态） |
| Seg | 高 | **可行**（仅需对象ID） |
| LiDAR | 低 | 不可行（需要物理仿真） |

Segmentation只依赖于场景中的对象ID，不依赖于光照、材质等渲染状态，因此可以在事后通过重新定位相机位置来生成。

### 640×480对3DGS的影响

```
分辨率影响分析：
  1280×720 → 3DGS质量最佳，但采集太慢
  640×480  → 质量良好，采集可接受（本方案）
  320×240  → 质量下降，但采集快

补偿策略：
  1. 增加帧数：200帧（原为100）
  2. 多尺度3DGS：粗尺度用640×480，细尺度补充高分辨率patch
  3. 深度约束：利用LiDAR和仿真Depth真值增强几何精度
```

---

## 推荐工作流

### 阶段1: 快速验证（2-4小时）

```bash
# 1. 用最低配置快速验证全流程
python 3-collect_dataset_v2.py

# 2. 验证数据质量
python tools/validate_dataset.py dataset/[最新目录]

# 3. （可选）生成分割真值
python tools/generate_segmentation.py dataset/[最新目录]
```

### 阶段2: 生产采集（8-12小时）

```bash
# 编辑配置，增加帧数，使用circle轨迹
# config/production.json

python 3-collect_dataset_v2.py --config config/production.json
```

---

## 联系与支持

- ASVSim文档: https://bavolesy.github.io/idlab-asvsim-docs/
- 项目分析记录: analysis_records/

---

*最后更新: 2026-03-12*
