# CLAUDE.md

> **文件定位**：本项目为 **极地路径规划与 3D Gaussian Splatting 重建**。
>
> **必读前置**：响应用户前必须阅读：
>
> 1. [`.claude/skills/asvsim_mentor/SKILL.md`](.claude/skills/asvsim_mentor/SKILL.md) — 技能定义和工作模式（A/B/C/D）
> 2. `analysis_records/` 最新记录 — 了解历史进度和决策

---

## 快速决策指南

| 用户问...       | 先查看...                                                              | 再执行...                         |
| --------------- | ---------------------------------------------------------------------- | --------------------------------- |
| "采集很慢/报错" | `analysis_records/2026-03-11_3-collect_dataset性能与颜色异常修复.md` | 确认是否使用 v2 版本脚本          |
| "相机没数据"    | `analysis_records/2026-03-10_Phase1_settings配置完成.md`             | 检查 ImageType 值是否为 1（非 2） |
| "怎么开始采集"  | `COLLECTION_V2_README.md`                                            | 运行 `3-collect_dataset_v2.py`  |
| "整体规划"      | `analysis_records/2026-03-10_项目全局分析与规划.md`                  | 根据当前阶段给出建议              |
| "怎么配置"      | `.claude/skills/asvsim_mentor/references/links.md`                   | 参考 settings.json 模板           |

---

## 项目概述

**项目名称**：Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting

**核心目标**：利用 Unreal Engine 5 和 ASVSim 仿真平台进行极地冰水环境仿真，结合 3D Gaussian Splatting (3DGS) 技术实现环境重建，开发智能路径规划算法。

**技术链条**：

```
UE5 极地场景渲染
    ↓
多模态数据采集 (RGB / Depth / LiDAR / Segmentation)
    ↓
┌─────────────────────────────────┐
│      智能感知层                  │
│  SAM3 海冰实例分割               │
│  Depth Anything 3 半监督深度估计 │
│  相机-LiDAR 联合标定             │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│      环境重建层                  │
│  多尺度渐进式 3DGS               │
│  分块建模 + 深度融合              │
│  RNN 无监督优化修复              │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│      路径规划层                  │
│  全局规划            │
│  局部实时避碰        │
│  冰情触发动态重规划               │
└─────────────────────────────────┘
    ↓
与 UE5/ASVSim 动态交互验证
```

---

## 当前项目阶段状态

| 阶段              | 内容                            | 状态                | 关键文件                              |
| ----------------- | ------------------------------- | ------------------- | ------------------------------------- |
| Phase 0           | UE5.4 + ASVSim (LakeEnv) 部署   | ✅ 完成             | 环境部署文档                          |
| Phase 1           | settings.json 配置 + 传感器验证 | ✅ 完成             | `2-verify_sensors.py`               |
| **Phase 3** | **数据采集 Pipeline**     | **🔄 进行中** | **`3-collect_dataset_v2.py`** |
| Phase 2           | 极地冰水场景构建                | ⏸️ 延后           | Pipeline 跑通后迁移                   |
| Phase 4           | 智能感知 (SAM3 + DA3)           | ⏳ 待开始           | —                                    |
| Phase 5           | 3DGS 重建                       | ⏳ 待开始           | —                                    |
| Phase 6           | 路径规划                       | ⏳ 待开始           | —                                    |
| Phase 7           | 集成验证                        | ⏳ 待开始           | —                                    |

**当前阶段关键决策**（2026-03-11）：

- ✅ 分辨率妥协：1280×720 → **640×480**（单帧从数分钟降至 ~15 秒）
- ✅ simPause 禁用：发现 CosysAirSim v3.0.1 会导致场景卡死，已回退到无暂停方案
- ✅ Segmentation 事后生成：跳过实时采集，节省 30% 时间
- ✅ V2 采集系统：使用 `3-collect_dataset_v2.py` + `config/` + `tools/`

---

## 文档检查清单

**每次响应前必须检查**：

1. **`.claude/skills/asvsim_mentor/SKILL.md`** — 工作模式定义（A/B/C/D）和技能能力范围
2. **`analysis_records/` 记录** — 了解项目历史进度（要看所有的）
3. **`.claude/skills/asvsim_mentor/references/links.md`** — ASVSim API 细节
4. **`.claude/skills/asvsim_mentor/references/project_introduction.md`** — 项目背景

### 如何查看 analysis_records/

```bash
# 列出所有分析记录（按时间倒序）
ls -la analysis_records/

```

---

## 关键陷阱速查表（Top 10）

| #  | 陷阱                                   | 症状                                  | 解决方案                                                 |
| -- | -------------------------------------- | ------------------------------------- | -------------------------------------------------------- |
| 1  | **ImageType.DepthPlanar 值错误** | Depth 分辨率 256×144（非 1280×720） | CosysAirSim 用 `1`，**不是**标准 AirSim 的 `2` |
| 2  | **simGetImages 传 vehicle_name** | RPC 阻塞卡死                          | 不传第二个参数：`simGetImages([...])`                  |
| 3  | **flipud 图像**                  | 图像上下颠倒                          | CosysAirSim 3.0.1**不需要** `np.flipud()`        |
| 4  | **Lumen 未禁用**                 | 每帧采集数分钟                        | settings.json 添加 `"LumenGIEnable": false`            |
| 5  | **simPause 卡死**                | UE5 画面冻结                          | v3.0.1 有 bug，**禁用 simPause**                   |
| 6  | **相机定义在顶层 Cameras**       | 相机数据为空                          | 必须放在 `"Sensors"` 块，`"SensorType": 1`           |
| 7  | **settings.json UTF-8 编码**     | 配置不生效/乱码                       | 必须**ASCII 编码**保存                             |
| 8  | **simGetCameraInfo 崩溃**        | UE5 空指针崩溃                        | 离线计算内参：`fx = W / (2*tan(FOV/2))`                |
| 9  | **分割对象不显示**               | Segmentation 全黑                     | Landscape/Foliage 不支持，换 StaticMesh                  |
| 10 | **使用旧采集脚本**               | 性能差、颜色异常                      | 改用 `3-collect_dataset_v2.py`                         |

---

## 项目结构

```
ASVSim_zsh/
├── cosysairsim/              # Python SDK（v3.0.1）
│   ├── client.py            # VesselClient 主客户端
│   ├── types.py             # 数据结构定义
│   └── utils.py             # 图像处理工具
│
├── dataset/                  # 采集的多模态数据集
│   └── YYYY_MM_DD_HH_MM_SS/
│       ├── rgb/             # PNG 图像 (640×480)
│       ├── depth/           # NPY float32 深度图
│       ├── segmentation/    # PNG 实例分割（事后生成）
│       └── lidar/           # JSON 点云数据
│
├── analysis_records/         # 分析记录（每次对话记录）
│   └── YYYY-MM-DD_<主题>.md
│
├── config/                   # 采集配置文件
│   └── collection_default.json
│
├── tools/                    # 辅助工具
│   ├── validate_dataset.py
│   └── generate_segmentation.py
│
├── .claude/skills/asvsim_mentor/
│   ├── SKILL.md             # 技能定义（工作模式 A/B/C/D）
│   └── references/
│       ├── links.md         # ASVSim 文档链接
│       └── project_introduction.md
│
├── 2-verify_sensors.py      # Phase 1 传感器验证
├── 3-collect_dataset_v2.py  # Phase 3 主采集脚本（推荐）
└── COLLECTION_V2_README.md  # V2 使用指南
```

---

## 核心 API 快速参考

```python
import cosysairsim as airsim
from cosysairsim.types import VesselControls
import numpy as np

# ── 连接 ──────────────────────────────────────
client = airsim.VesselClient()
client.confirmConnection()
client.enableApiControl(True)

# ── 控制（thrust: 0~1，angle: 0.5=直行）───────
client.setVesselControls('Vessel1', VesselControls(thrust=0.3, angle=0.6))

# ── 图像采集（640×480，禁用 Lumen）────────────
responses = client.simGetImages([
    airsim.ImageRequest(0, airsim.ImageType.Scene),            # RGB
    airsim.ImageRequest(0, airsim.ImageType.DepthPlanar, True), # Depth（类型=1）
    airsim.ImageRequest(0, airsim.ImageType.Segmentation),     # Seg
])

# 解码（注意：不需要 flipud）
r = responses[0]
img = np.frombuffer(r.image_data_uint8, dtype=np.uint8).reshape(r.height, r.width, 3)

# ── LiDAR ─────────────────────────────────────
lidar = client.getLidarData('top_lidar', 'Vessel1')
```

---

## 常用命令

```bash
# 传感器验证
python 2-verify_sensors.py

# 数据采集（推荐 v2 版本）
python 3-collect_dataset_v2.py
# 或带配置
python 3-collect_dataset_v2.py --config config/collection_default.json

# 数据验证
python tools/validate_dataset.py dataset/2026_03_12_XX_XX_XX

# 事后生成分割真值
python tools/generate_segmentation.py dataset/2026_03_12_XX_XX_XX
```

---

## 权威来源优先级

**遇到问题时的查证顺序**：

| 优先级 | 来源                           | 用途                |
| ------ | ------------------------------ | ------------------- |
| 1      | ASVSim 官方文档                | API 行为不确定时    |
| 2      | `analysis_records/` 历史记录 | 类似问题是否已解决  |
| 3      | GitHub API (curl)              | 验证模型/库最新版本 |
| 4      | ASVSim 论文 arXiv:2506.22174   | 架构设计参考        |

**访问方式**：

```bash
# ASVSim 文档（HTML 用 PowerShell）
powershell.exe -Command "(Invoke-WebRequest -Uri 'https://bavolesy.github.io/idlab-asvsim-docs/' -UseBasicParsing).Content"

# GitHub API
curl -s "https://api.github.com/repos/facebookresearch/sam3"
```

---

## 文档记录规范

**每次对话必须记录在 `analysis_records/YYYY-MM-DD_<主题>.md`**：

```markdown
# 分析记录: <主题>

**创建时间**: 2026-03-12
**最后更新**: 2026-03-12

---

## 更新摘要
- [2026-03-12 10:00] 初始分析

---

## 分析目标
[用户原始问题]

---

## 探索过程
[网络检索、代码阅读、验证]

---

## 核心内容
[概念、原理、方案]

---

## 代码示例
```python
# 代码
```

---

## 总结结论

[技术结论和建议]

---

## 学习路径

[推荐资源]

```

**规则**：
- 相关主题 → 追加到原文件
- 新主题 → 创建新文件
- 必须在顶部添加时间戳和更新摘要

---

*项目执行手册 v2.0*
*配合 SKILL.md 使用*
```
