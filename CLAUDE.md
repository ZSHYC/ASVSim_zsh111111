# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**项目名称**: Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting
**核心目标**: 利用 Unreal Engine 5 和 ASVSim 仿真平台进行极地冰水环境仿真，结合 3D Gaussian Splatting (3DGS) 技术实现环境重建，开发智能路径规划算法

**技术链条**:

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
│  全局规划 (D* Lite)              │
│  局部实时避碰 (VFH+)             │
│  冰情触发动态重规划               │
└─────────────────────────────────┘
    ↓
与 UE5/ASVSim 动态交互验证
```

## Critical Project Structure

```
ASVSim_zsh/
├── cosysairsim/              # 核心 Python SDK（AirSim 修改版 v3.0.1）
│   ├── client.py            # VesselClient 主客户端（RPC 通信核心）
│   ├── types.py             # 数据结构定义（VesselControls, VesselState, ImageType）
│   └── utils.py             # 图像处理、坐标转换、颜色映射生成
│
├── dataset/                  # 采集的多模态数据集（.gitignore 忽略）
│   └── YYYY_MM_DD_HH_MM_SS/
│       ├── rgb/             # PNG 图像
│       ├── depth/           # NPY float32 深度图（单位：米）
│       ├── segmentation/    # PNG 实例分割图像
│       └── lidar/           # JSON 点云数据
│
├── analysis_records/         # 分析记录文档（每次对话必须在此记录）
│   └── YYYY-MM-DD_<主题>.md  # 按日期和主题命名的分析记录
│
├── .claude/skills/asvsim_mentor/   # ASVSim 超级导师技能配置
│   ├── SKILL.md                    # 核心技能定义（必须参考）
│   └── references/
│       ├── links.md               # ASVSim 技术文档和论文链接（必读）
│       └── project_introduction.md # 项目背景和研究内容（必读）

```

## Mandatory Documentation Checklist

**每次响应前必须检查并阅读以下文档**:

1. **`.claude/skills/asvsim_mentor/SKILL.md`** — 技能定义和工作模式（A/B/C/D 模式）
2. **`.claude/skills/asvsim_mentor/references/links.md`** — ASVSim 完整 API 文档（涉及 API 细节时必读，所有网址均需深入理解）
3. **`.claude/skills/asvsim_mentor/references/project_introduction.md`** — 项目背景和研究要求（必读，是完成项目的基础）
4. **`analysis_records/` 目录下的相关记录文件** — 了解项目历史进度和之前的分析结论（必须查看最新文件，避免重复工作或冲突决策）

### 如何查看 analysis_records/

```bash
# 列出所有分析记录文件（按时间倒序）
ls -la analysis_records/ | sort -k9 -r

# 快速查看最新记录
cat analysis_records/$(ls -t analysis_records/ | head -1)
```

**查看最新记录的目的是**：
- 了解当前项目阶段和已完成的工作
- 避免重复分析已解决的问题
- 确保建议与历史决策保持一致
- 识别需要迭代的未完成事项

**典型场景**：
- 如果用户询问数据采集问题 → 先查看 `2026-03-11_3-collect_dataset性能与颜色异常修复.md`
- 如果用户询问传感器配置 → 先查看 `2026-03-10_Phase1_settings配置完成.md`
- 如果用户询问整体规划 → 先查看 `2026-03-10_项目全局分析与规划.md`

**涉及具体技术时必须参考**:

- SAM3 官方: https://github.com/facebookresearch/sam3 (848M 参数, 文本+图像提示)
- Depth Anything 3: https://github.com/ByteDance-Seed/Depth-Anything-3 (depth-ray 表示, 多任务)
- 3D Gaussian Splatting: https://github.com/graphdeco-inria/gaussian-splatting (SIGGRAPH 2023, 实时渲染)
- ASVSim 论文: https://arxiv.org/abs/2506.22174
- ASVSim 文档: https://bavolesy.github.io/idlab-asvsim-docs/
- AirSim 文档：https://microsoft.github.io/AirSim/

## ASVSim Core Knowledge

### Platform Architecture

```
UE5.4（渲染 + 物理引擎）
  └── Cosys-AirSim Plugin
        ├── VesselEngine / LargeVesselEngine  ← Fossen 流体力学
        ├── PCG System（UE5 过程化内容生成）
        └── Python Client (cosysairsim)
              ├── VesselClient     ← 船舶控制 + 状态查询
              ├── Image API        ← RGB / Depth / Segmentation
              ├── LiDAR API        ← 16/45 线测距
              └── PCG API          ← 港口地形程序化生成
settings.json  ← 统一配置入口（ASCII 编码）
```

### Supported Vessel Types

| 船型        | 流体力学引擎         | 物理引擎          | 推进器数量 |
| ----------- | -------------------- | ----------------- | ---------- |
| milliampere | FossenCurrent        | VesselEngine      | 2          |
| cybership2  | FossenCurrent        | VesselEngine      | 2          |
| qiuxin5     | FossenCurrent        | VesselEngine      | 1          |
| mariner     | MarinerHydrodynamics | LargeVesselEngine | 1          |

### Core API Reference

```python
import cosysairsim as airsim
from cosysairsim.types import VesselControls, Vector2r
import numpy as np

# ── Connection ──────────────────────────────────────
client = airsim.VesselClient()
client.confirmConnection()
client.enableApiControl(True)

# ── Control (thrust: 0~1, angle: 0~1, 0.5=straight) ──
client.setVesselControls('Vessel1', VesselControls(thrust=0.7, angle=0.5))
# Multi-thruster (MilliAmpere has 2)
client.setVesselControls('Vessel1', VesselControls(thrust=[0.7,0.8], angle=[0.5,0.5]))

# ── State Query ────────────────────────────────────
state = client.getVesselState()          # Position/velocity/pose
pos = state.kinematics_estimated.position
vel = state.kinematics_estimated.linear_velocity

# ── Multi-modal Image Capture ──────────────────────────────
responses = client.simGetImages([
    airsim.ImageRequest(0, airsim.ImageType.Scene),             # RGB PNG
    airsim.ImageRequest(0, airsim.ImageType.DepthPlanar, True), # Float depth
    airsim.ImageRequest(0, airsim.ImageType.Segmentation),      # Instance segmentation
])
# Convert to NumPy
r = responses[0]
img = np.frombuffer(r.image_data_uint8, dtype=np.uint8).reshape(r.height, r.width, 3)
# ⚠️ CosysAirSim 3.0.1: Original image is already upright, DO NOT use flipud
# img = np.flipud(img)  # Only needed for standard AirSim

# ── LiDAR ──────────────────────────────────────
lidar = client.getLidarData(lidar_name='top_lidar', vehicle_name='Vessel1')

# ── Pause/Resume for synchronized capture ──────────────────────────────────
client.simPause(True)   # Pause simulation
# ... capture all sensors ...
client.simPause(False)  # Resume simulation
```

### Critical Configuration Constraints

**所有以下约束均来自 ASVSim 官方文档验证 (https://bavolesy.github.io/idlab-asvsim-docs/)**:

**settings.json requirements**:

- Must use **ASCII encoding** (not UTF-8 with BOM) — 官方文档: "always use ASCII format to save json file"
- Cameras must be defined under `"Sensors"` block with `"SensorType": 1` (not top-level `"Cameras"`)
- Instance segmentation only supports **StaticMesh / SkeletalMesh** (Landscape/Foliage must be replaced) — 官方文档: "static and skeletal meshes are supported", Landscape/Foliage "aren't supported"
- `CameraDefaults.CaptureSettings` must define each ImageType separately
- CosysAirSim `ImageType` values (官方文档枚举):
  - `Scene = 0`
  - `DepthPlanar = 1` (注意：官方文档确认 DepthPlanar=1, DepthPerspective=2)
  - `Segmentation = 5`
  - `Annotation = 10`
- **Must disable Lumen** for performance — 官方文档: "Due to the cameras using scene capture components enabling Lumen for them can be costly on performance"
  - `"LumenGIEnable": false` — disables Global Illumination
  - `"LumenReflectionEnable": false` — disables Reflections

**MSVC Version**: Must use **v14.38.33130** — 官方文档: "If you choose a later version, ASVSim will not compile"

**动态对象添加到分割系统**: 官方文档: `ASimModeBase::AddNewActorToSegmentation(AActor)`

## Current Project Phase Status

| 阶段    | 内容                               | 状态      | 关键文件                                         |
| ------- | ---------------------------------- | --------- | ------------------------------------------------ |
| Phase 0 | UE5.4 + ASVSim (LakeEnv) 部署      | ✅ 完成   | `1_ASVSim环境部署.md`                          |
| Phase 1 | settings.json 配置 + 传感器验证    | ✅ 完成   | `2_找到船并跑起来.md`, `2-verify_sensors.py` |
| Phase 3 | 数据采集 Pipeline                  | 🔄 进行中 | `3-collect_dataset.py`                         |
| Phase 2 | 极地冰水场景构建                   | ⏸️ 延后 | Pipeline 跑通后迁移                              |
| Phase 4 | 智能感知 (SAM3 + Depth Anything 3) | ⏳ 待开始 | —                                               |
| Phase 5 | 3DGS 重建                          | ⏳ 待开始 | —                                               |
| Phase 6 | 路径规划 (D* Lite + VFH+)          | ⏳ 待开始 | —                                               |
| Phase 7 | 集成验证                           | ⏳ 待开始 | —                                               |

## Knowledge Timeliness Protocol (Enforced)

**核心规则**: Training data has cut-off dates. AI models, library versions, and paper progress update continuously. Must actively verify timeliness when specific tech stacks are involved.

**强制触发条件**:

- Mentioning any AI model (SAM, YOLO, NeRF, 3DGS, Depth Anything, etc.)
- Mentioning any Python library version
- Discussing "latest", "best", "recommended" methods
- User explicitly provides a URL
- Planning research solutions

**Retrieval Implementation: Bash + curl (Primary)**:

```bash
# GitHub repository info (Stars, last update)
curl -s "https://api.github.com/repos/<owner>/<repo>" | python -c "
import json,sys; d=json.load(sys.stdin)
print('Stars:', d['stargazers_count'])
print('Last update:', d['pushed_at'])
print('Description:', d['description'])
"

# Latest release version
curl -s "https://api.github.com/repos/<owner>/<repo>/releases/latest" | python -c "
import json,sys; d=json.load(sys.stdin)
print('Latest version:', d['tag_name'])
print('Published:', d['published_at'])
"

# arXiv latest papers
curl -s "https://export.arxiv.org/api/query?search_query=all:<keyword>&sortBy=submittedDate&sortOrder=descending&max_results=3" | python -c "
import sys,re
xml=sys.stdin.read()
titles=re.findall(r'<title>(.*?)</title>',xml)[1:]
ids=re.findall(r'<id>https://arxiv.org/abs/(.*?)</id>',xml)
dates=re.findall(r'<published>(.*?)</published>',xml)
for t,i,d in zip(titles,ids,dates): print(f'[{d[:10]}] {t} — https://arxiv.org/abs/{i}')
"

# PyPI latest version
curl -s "https://pypi.org/pypi/<package>/json" | python -c "
import json,sys; d=json.load(sys.stdin)
print('Latest version:', d['info']['version'])
"
```

**Windows Known Issue**: Local curl uses schannel TLS which fails on `*.github.io` HTTPS. **Use PowerShell for ASVSim docs**:

```bash
powershell.exe -Command "(Invoke-WebRequest -Uri 'https://bavolesy.github.io/idlab-asvsim-docs/vessel/vessel_api/' -UseBasicParsing).Content"
```

**Quick Check Commands for This Project**:

```bash
# SAM3
curl -s "https://api.github.com/repos/facebookresearch/sam3" | python -c "import json,sys;d=json.load(sys.stdin);print('SAM3 Stars:',d['stargazers_count'],'| Updated:',d['pushed_at'][:10])"

# Depth Anything 3
curl -s "https://api.github.com/repos/ByteDance-Seed/Depth-Anything-3" | python -c "import json,sys;d=json.load(sys.stdin);print('DA3 Stars:',d['stargazers_count'],'| Updated:',d['pushed_at'][:10])"

# 3D Gaussian Splatting
curl -s "https://api.github.com/repos/graphdeco-inria/gaussian-splatting" | python -c "import json,sys;d=json.load(sys.stdin);print('3DGS Stars:',d['stargazers_count'],'| Updated:',d['pushed_at'][:10])"

# Ultralytics YOLO latest
curl -s "https://api.github.com/repos/ultralytics/ultralytics/releases/latest" | python -c "import json,sys;d=json.load(sys.stdin);print('YOLO Latest:',d['tag_name'],'| Published:',d['published_at'][:10])"
```

## Authority Source Access Protocol

**When encountering uncertain or ambiguous technical questions, must proactively access external authoritative sources**:

### When to Access External Sources

- Configuration parameters are uncertain or undocumented in local files
- API behavior differs from expectations
- Encountering errors not covered in local documentation
- Need to verify latest version/feature of a technology
- Technical details are ambiguous or conflicting

### Priority of Authoritative Sources

**Tier 1 (Primary - Always check first)**:
1. **ASVSim Official Docs**: https://bavolesy.github.io/idlab-asvsim-docs/
   - Use PowerShell for HTML pages: `powershell.exe -Command "(Invoke-WebRequest -Uri '<URL>' -UseBasicParsing).Content"`
2. **ASVSim GitHub**: https://github.com/BavoLesy/ASVSim
3. **ASVSim Paper**: https://arxiv.org/abs/2506.22174

**Tier 2 (Technology-specific)**:
| Technology | Official Source | API Docs |
|------------|-----------------|----------|
| SAM3 | https://github.com/facebookresearch/sam3 | Paper: arXiv:2511.16719 |
| Depth Anything 3 | https://github.com/ByteDance-Seed/Depth-Anything-3 | Paper: arXiv:2511.10647 |
| 3D Gaussian Splatting | https://github.com/graphdeco-inria/gaussian-splatting | Paper: SIGGRAPH 2023 |
| COLMAP | https://colmap.github.io/ | CLI docs: colmap.github.io/cli.html |
| stable-baselines3 | https://stable-baselines3.readthedocs.io/ | - |
| Ultralytics YOLO | https://docs.ultralytics.com/ | - |

**Tier 3 (General Research)**:
- arXiv: https://arxiv.org/search/?query=<keywords>
- Semantic Scholar: https://www.semanticscholar.org/
- Papers With Code: https://paperswithcode.com/

### Execution Process

```
Step 1: Identify uncertainty or ambiguity in the question
    ↓
Step 2: Determine which Tier 1/2/3 source is most relevant
    ↓
Step 3: Access using appropriate method:
    - GitHub API: curl (for version/feature info)
    - Documentation HTML: PowerShell Invoke-WebRequest (for ASVSim docs)
    - arXiv API: curl (for papers)
    ↓
Step 4: Extract relevant information
    ↓
Step 5: Integrate with project context and provide answer
    ↓
Step 6: Record full process in analysis_records/
```

### Example Scenarios

**Scenario 1**: User asks "ImageType.DepthPlanar 的值是多少？"
- Action: Must verify from official ASVSim docs (already confirmed: DepthPlanar=1)
- Method: WebFetch or PowerShell on https://bavolesy.github.io/idlab-asvsim-docs/usage/image_apis/

**Scenario 2**: User encounters "simGetImages 返回空数据"
- Action: Check ASVSim docs for Lumen settings, verify camera configuration
- Method: WebFetch on image_apis page + check local settings.json

**Scenario 3**: User asks "SAM3 最新版本有什么新功能？"
- Action: Query GitHub API for releases + read SAM3 paper
- Method: `curl -s "https://api.github.com/repos/facebookresearch/sam3/releases/latest"`

### Documentation Requirement

When accessing external sources:
1. **Always cite the source** in responses: "根据 ASVSim 官方文档..."
2. **Include the URL** in analysis_records
3. **Note the access timestamp** for version-sensitive info
4. **If sources conflict**, prefer: Official Docs > GitHub > Paper > Community

## Working Modes (from SKILL.md)

### Mode A: Deep Explanation

**Trigger**: "是什么", "怎么理解", "讲一下", "原理", "架构是怎样的"

**Output Structure**:

```
## 核心概念
[精确定义 + 直觉解释，结合 ASVSim 项目语境]

## 原理 / 架构
[结构图或分层说明]

## 在本项目中的应用
[该技术/模块如何在 ASVSim 研究栈中使用，附代码片段]

## 学习路径
[入门 → 进阶的资源推荐，含论文/代码/课程]
```

### Mode B: Solution Planning

**Trigger**: "怎么实现", "规划一下", "我想做 X，怎么搞", "应该怎么做"

**Output Structure**:

```
## 目标确认
[复述目标 + 已知条件 + 约束]

## 整体架构
[模块图或数据流，说明各模块职责]

## 分步实现计划
步骤1: [名称]
  - 用到：[ASVSim API / 算法 / 库]
  - 关键参数：[说明]
  - 预期产出：[说明]
步骤2: ...

## 技术选型
[若有多种路径，对比并推荐，说明理由]

## 风险与规避
[潜在问题 + 解决思路]

## 相关资源
[论文 / 代码仓库 / 文档]
```

### Mode C: Code Generation

**Trigger**: "帮我写", "实现这个函数", "写段代码"

**Code Quality Requirements**:

- Complete type annotations (Python 3.10+ style)
- API calls strictly aligned with ASVSim interfaces
- Boundary handling: connection failure, empty data, array bounds, timeout
- Chinese inline comments + Google style docstring
- Avoid bare `except`, mutable default arguments, magic numbers

**Output Structure**:

```
## 实现
[代码块，注释完整]

## 使用示例
[最小可运行示例 + 预期输出]

## 质量反馈
- 潜在问题：[...]
- 优化建议：[...]
- 假设说明：[若有歧义]
```

### Mode D: Information Retrieval

**Trigger**: "查论文", "有没有相关工作", "有没有开源代码", "推荐资料", "最新进展"

**Execution**: Use Bash curl commands (not WebFetch), handle failures with fallback protocol.

## CRITICAL: Documentation Recording Requirement

**每次对话都必须完整记录在一个 .md 文件中**，这是本项目最重要的规则：

### Recording Rules

1. **存储路径**: `analysis_records/YYYY-MM-DD_<主题>.md`
2. **记录内容必须包含**:

   - **分析目标**: 用户提出的问题或需求
   - **探索过程**: 我进行的网络检索、代码阅读、技术验证等完整过程
   - **核心内容**: 分析的核心概念、原理、架构或方案
   - **代码示例**: 相关代码片段及其解释
   - **总结结论**: 最终的技术结论和建议
   - **学习路径**: 推荐的学习资源（论文、代码、课程等）
3. **迭代更新**:

   - 如果新提问与已有记录主题相关，追加到原文件
   - 如果新提问是全新主题，创建新的 .md 文件
   - 每次更新时在文件顶部添加时间戳和更新摘要
4. **文件格式示例**:

```markdown
# 分析记录: <主题>

**创建时间**: 2026-03-11
**最后更新**: 2026-03-11

---

## 更新摘要

- [2026-03-11 14:30] 初始分析完成，涵盖 X、Y、Z 三个方面
- [2026-03-11 16:00] 补充了关于 A 的最新发现

---

## 分析目标

[用户原始问题]

---

## 探索过程

### 1. 网络检索
[执行的 curl 命令和结果]

### 2. 代码阅读
[阅读的代码文件和发现]

### 3. 技术验证
[验证的假设和结论]

---

## 核心内容

### 核心概念
[详细解释]

### 原理 / 架构
[结构说明]

### 在本项目中的应用
[具体应用方案]

---

## 代码示例

```python
# 完整可运行的代码示例
```

---

## 总结结论

[最终技术结论]

---

## 学习路径

- [论文/资源 1]
- [论文/资源 2]

```

## Key Technical Integrations

### SAM3 (Segmentation)
- **Architecture**: 848M parameters, detector-tracker with shared backbone
- **Key Innovation**: Presence token for disambiguating similar text prompts
- **Installation**: Python 3.12+, PyTorch 2.7+, CUDA 12.6+
- **Access**: Requires HuggingFace authentication request

### Depth Anything 3
- **Architecture**: Plain transformer backbone (DinoV2) + DualDPT head
- **Key Innovation**: Depth-ray representation unifies depth/pose/3DGS tasks
- **Improvement over DA2**: Direct depth prediction (not disparity), superior geometric accuracy
- **Multi-task**: Depth estimation, camera pose estimation, 3D Gaussian generation

### 3D Gaussian Splatting
- **Input**: COLMAP SfM sparse point cloud or NeRF Synthetic
- **Representation**: 3D Gaussians with anisotropic covariance
- **Training**: 30,000 iterations with adaptive density control
- **Rendering**: Real-time (≥30 fps) anisotropic splatting at 1080p
- **Hardware**: CUDA 7.0+, 24GB VRAM recommended for high quality

### Path Planning Stack
- **Global**: D* Lite (incremental updates for dynamic replanning)
- **Local**: VFH+ (Vector Field Histogram) for real-time obstacle avoidance
- **RL Alternative**: SAC/PPO via stable-baselines3 with ShippingSim env

## Common Development Commands

```bash
# Verify sensor configuration
python 2-verify_sensors.py

# Collect multi-modal dataset
python 3-collect_dataset.py

# Check technology versions (run before making recommendations)
curl -s "https://api.github.com/repos/facebookresearch/sam3" | python -c "import json,sys;d=json.load(sys.stdin);print(d['stargazers_count'],d['pushed_at'][:10])"
```

## Important Notes

1. **Always check SKILL.md first** before responding to any ASVSim-related query
2. **Always verify technology versions** using curl commands when discussing specific models/libraries
3. **Always record the conversation** in `analysis_records/` with complete exploration and conclusions
4. **Use PowerShell** for ASVSim documentation website (github.io has TLS issues with curl on Windows)
5. **Camera intrinsics must be calculated offline**: `fx = W / (2 * tan(FOV/2))` (simGetCameraInfo doesn't work for SensorType:1)
6. **DepthPlanar is type 1 in CosysAirSim** (not 2 like standard AirSim)
7. **Do NOT use flipud on images from CosysAirSim 3.0.1** (already upright)
