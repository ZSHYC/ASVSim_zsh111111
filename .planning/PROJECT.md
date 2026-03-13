# 本科毕业论文写作项目

**论文题目（英文）**: Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting
**论文题目（中文）**: 基于 Unreal Engine 和 3D Gaussian Splatting 的极地路径规划与三维重建

---

## What This Is

这是一个本科毕业论文写作项目，基于实际的极地路径规划与3D Gaussian Splatting重建研究。论文将系统性地阐述如何利用Unreal Engine 5和ASVSim仿真平台进行极地冰水环境仿真，结合3DGS技术实现环境重建，并开发智能路径规划算法的完整技术链条。

论文为英文撰写，遵循哈尔滨工程大学本科生毕业论文（英语类）撰写规范，正文控制在1万5千词以内，采用Harvard引用格式。

---

## Core Value

论文的核心价值在于展示一个完整的"仿真-感知-重建-规划"技术链条的工程实现，特别是将前沿的3D Gaussian Splatting神经渲染技术应用于极地航行这一特殊场景，为智能船舶导航提供新的技术路径。

---

## Requirements

### Validated

(None yet — 论文初稿已完成但需根据最新研究进展更新)

### Active

- [ ] 更新Chapter 3 (Methodology) — 补充Phase 4智能感知层内容（DA3深度估计、SAM3分割）
- [ ] 更新Chapter 4 (Experiments and Results) — 添加DA3深度对比实验、SAM3分割结果
- [ ] 更新Chapter 5 (Discussion) — 讨论DA3位姿预测限制、深度-分割融合策略
- [ ] 完善Chapter 2 (Literature Review) — 补充SAM3、Depth Anything 3最新研究
- [ ] 更新Chapter 1 (Introduction) — 根据最新进展调整研究目标描述
- [ ] 添加实际实验图表 — 替换论文中的占位符图表
- [ ] 补充致谢部分个性化内容
- [ ] 检查引用格式和参考文献完整性
- [ ] 字数控制和格式调整

### Out of Scope

- Phase 5 (3DGS重建) 和 Phase 6 (路径规划) 的完整实验 — 论文截稿前可能无法完成全部实验，将在Chapter 6中以"Future Work"形式说明
- 真实极地场景数据验证 — 受条件限制，本论文主要基于仿真数据，将在Discussion中说明此局限性
- 长篇理论推导 — 本科论文侧重工程实现，复杂的数学推导放入附录或简化处理

---

## Context

### 论文基础信息

| 项目 | 内容 |
|------|------|
| 姓名（中文/英文） | 张时昊 / Zhang Shihao |
| 学院 | 南安普顿海洋工程联合学院 / Southampton Ocean Engineering Joint Institute |
| 专业 | 船舶与海洋工程 / Naval Architecture and Ocean Engineering |
| 指导教师 | 邢向磊 副教授 / Xing Xianglei, Associate Professor |
| 第二导师 | Dominic Taunton, Professor |
| 学校 | 哈尔滨工程大学 / Harbin Engineering University |
| 提交日期 | May 2026 |

### 格式要求

- **正文字数**: 1万5千词以内
- **一级标题**: 罗马数字 (I, II, III...)
- **二级标题**: 阿拉伯数字 (1.1, 1.2...)
- **三级标题**: 阿拉伯数字 (1.1.1, 1.1.2...)
- **引用格式**: Harvard格式
- **行距**: 固定值22磅
- **页边距**: 上28mm、下28mm、左25mm、右25mm

### 论文文件结构

```
thesis/
├── main.tex              # 主文档
├── cover.tex             # 封面
├── acknowledgements.tex  # 致谢
├── abstract.tex          # 中英文摘要
├── chapter1.tex          # Chapter I: Introduction
├── chapter2.tex          # Chapter II: Literature Review
├── chapter3.tex          # Chapter III: Methodology
├── chapter4.tex          # Chapter IV: Experiments and Results
├── chapter5.tex          # Chapter V: Discussion
├── chapter6.tex          # Chapter VI: Conclusion
├── appendix.tex          # 附录
└── references.bib        # 参考文献
```

### 研究项目技术链条

```
UE5 极地场景渲染
    ↓
多模态数据采集 (RGB / Depth / LiDAR / Segmentation)
    ↓
┌─────────────────────────────────┐
│      智能感知层 (Phase 4)        │
│  SAM3 海冰实例分割               │
│  Depth Anything 3 半监督深度估计 │
│  相机-LiDAR 联合标定             │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│      环境重建层 (Phase 5)        │
│  多尺度渐进式 3DGS               │
│  分块建模 + 深度融合              │
│  RNN 无监督优化修复              │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│      路径规划层 (Phase 6)        │
│  全局规划 (D* Lite)              │
│  局部实时避碰                    │
│  冰情触发动态重规划               │
└─────────────────────────────────┘
    ↓
与 UE5/ASVSim 动态交互验证
```

### 当前研究进展

| 阶段 | 内容 | 状态 | 论文相关成果 |
|------|------|------|--------------|
| Phase 0 | UE5.4 + ASVSim部署 | ✅ 完成 | 环境配置、船只控制验证 |
| Phase 1 | settings.json配置 | ✅ 完成 | 生产级传感器配置 |
| Phase 3 | 数据采集Pipeline | ✅ 完成 | V2采集系统、640×480优化 |
| Phase 4.1 | PyTorch Nightly升级 | ✅ 完成 | RTX 5070 Ti GPU加速 |
| Phase 4.2 | DA3深度估计部署 | ✅ 完成 | 126张图像深度估计、11 FPS |
| Phase 4.3 | DA3深度对比分析 | ✅ 完成 | 深度对齐因子0.0204、误差2.67m |
| Phase 4.4 | DA3位姿验证 | ✅ 完成 | 发现位姿不可用（重要结论） |
| Phase 4.5 | SAM3分割部署 | ✅ 完成 | 94张图像实例分割、平均置信度0.947 |
| Phase 4.6 | 仿真位姿获取 | ❌ 未完成 | 阻塞后续数据整合 |
| Phase 5 | 3DGS重建 | ⏳ 待开始 | 论文可描述方法框架 |
| Phase 6 | 路径规划 | ⏳ 待开始 | 论文可描述方法框架 |

---

## Constraints

- **Timeline**: 论文需在2026年5月提交，当前为2026年3月，剩余约2个月
- **Content Limit**: 正文1万5千词，当前约1万3千词，新增内容需精简
- **Technical Reality**: Phase 5-6实验可能无法在截稿前完全完成，需调整论文表述
- **Data Availability**: DA3位姿不可用，需使用仿真位姿替代
- **Format Compliance**: 必须严格遵循哈尔滨工程大学英文论文格式要求

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Phase 4优先于Phase 2 | 感知pipeline跑通后再迁移到极地场景 | — Pending |
| 640×480分辨率 | 单帧采集从数分钟降至15秒 | ✓ Good |
| 禁用simPause | v3.0.1有bug会导致场景卡死 | ✓ Good |
| DA3深度+仿真位姿组合 | DA3位姿不可用但深度质量良好 | — Pending |
| 跳过复杂LiDAR标定 | 时间有限，优先保证核心流程 | — Pending |

---

*Last updated: 2026-03-13 after project initialization*
