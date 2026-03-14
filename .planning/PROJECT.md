# 本科毕业论文写作项目

**论文题目（英文）**: Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting
**论文题目（中文）**: 基于 Unreal Engine 和 3D Gaussian Splatting 的极地路径规划与三维重建

---

## Current State (v1.0 SHIPPED)

**状态**: ✅ 已完成并归档
**版本**: v1.0 Thesis Writing
**完成时间**: 2026-03-14
**交付物**: 82页PDF论文 (`thesis/main.pdf`)

### What Shipped

- **Phase 1**: 内容审计，识别25项更新需求
- **Phase 2**: 数据准备，生成系统架构图和实验图表
- **Phase 3**: 核心内容更新，Chapter 3-5更新完成 (+520行)
- **Phase 4**: 文献更新，添加SAM3/DA3引用，更新Chapter 1-2
- **Phase 5**: 前置内容与润色，完成HEU模板所有页面

### Key Metrics

| 指标 | 数值 |
|------|------|
| PDF页数 | 82页 |
| LaTeX代码 | 2,325行 |
| 字数 | 8,087词 |
| 参考文献 | 50篇 |
| DA3处理 | 126帧，11 FPS，2.67m中位误差 |
| SAM3分割 | 94帧，8.7实例/帧，0.947置信度 |

---

## What This Is

这是一个本科毕业论文写作项目，基于实际的极地路径规划与3D Gaussian Splatting重建研究。论文系统性地阐述了如何利用Unreal Engine 5和ASVSim仿真平台进行极地冰水环境仿真，结合3DGS技术实现环境重建，并开发智能路径规划算法的完整技术链条。

论文为英文撰写，遵循哈尔滨工程大学本科生毕业论文（英语类）撰写规范，正文控制在1万5千词以内，采用Harvard引用格式。

---

## Core Value

论文的核心价值在于展示一个完整的"仿真-感知-重建-规划"技术链条的工程实现，特别是将前沿的3D Gaussian Splatting神经渲染技术应用于极地航行这一特殊场景，为智能船舶导航提供新的技术路径。

---

## Requirements

### Validated (v1.0)

- ✓ Chapter 3更新 — 补充DA3深度估计和SAM3分割的详细实现 (v1.0)
- ✓ Chapter 4更新 — 添加DA3批量处理性能数据、深度对比分析 (v1.0)
- ✓ Chapter 5更新 — 讨论DA3位姿预测限制、深度-分割融合策略 (v1.0)
- ✓ Chapter 2完善 — 补充SAM3、Depth Anything 3最新研究 (v1.0)
- ✓ Chapter 1修订 — 根据实际进展调整研究目标描述 (v1.0)
- ✓ 实验图表 — 系统架构图、DA3深度对比、SAM3分割可视化 (v1.0)
- ✓ 格式检查 — Harvard引用、图表编号、LaTeX编译 (v1.0)
- ✓ 前置内容 — 封面、致谢、中英文摘要、目录 (v1.0)
- ✓ 参考文献 — 50篇引用，格式统一 (v1.0)

### Active (Future Work)

暂无 — 论文已完成

### Out of Scope

- Phase 5-6完整实验 — 已在Chapter 6中以"Future Work"形式说明
- 真实极地场景数据验证 — 在Discussion中说明此局限性
- 长篇理论推导 — 已简化处理

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

### 技术链条

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

### 研究进展 (Completed)

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
| Phase 4.6 | 仿真位姿获取 | ⚠️ 部分 | 论文使用替代方案描述 |
| Phase 5 | 3DGS重建 | 📋 方法框架 | 论文描述方法框架 |
| Phase 6 | 路径规划 | 📋 方法框架 | 论文描述方法框架 |

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 640×480分辨率 | 单帧采集从数分钟降至15秒 | ✓ Good — 显著提升采集效率 |
| 禁用simPause | v3.0.1有bug会导致场景卡死 | ✓ Good — 避免场景冻结问题 |
| DA3深度+仿真位姿组合 | DA3位姿不可用但深度质量良好 | ✓ Good — 论文中披露此限制作为贡献 |
| Phase 5-6方法描述 | 实验无法在截稿前完成 | ✓ Good — 以Future Work形式处理 |

---

*Last updated: 2026-03-14 after v1.0 milestone completion*
