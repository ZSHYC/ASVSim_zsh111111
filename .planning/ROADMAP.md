# Roadmap: 本科毕业论文写作项目

**项目**: Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting
**Created**: 2026-03-13
**Due**: May 2026

---

## Phase Overview

| # | Phase | Goal | Requirements | Est. Duration |
|---|-------|------|--------------|---------------|
| 1 | Content Audit | 审查现有论文，识别需要更新的内容 | CONT审核, FIG审核 | 2-3 hours |
| 2 | Data Preparation | 提取实验数据，生成图表 | FIG-01~05, TAB-01~04 | 4-6 hours |
| 3 | Core Content Update | 更新核心章节（Ch3-Ch5） | CONT-01~03 | 8-12 hours |
| 4 | Literature Update | 更新文献综述和引言 | CONT-04~05, REF-01~03 | 4-6 hours |
| 5 | Front Matter & Polish | 完善前置内容和格式检查 | FRONT-01~04, FMT-01~05, REF-04 | 4-6 hours |

---

## Phase Details

### Phase 1: Content Audit

**Goal**: 全面审查现有论文内容，识别需要更新的部分，制定更新计划

**Requirements**: CONT审核, FIG审核, REF审核

**Success Criteria**:
1. 生成论文内容审计报告，标记所有需要更新的段落
2. 识别所有占位符图表位置
3. 列出缺失的引用和参考文献
4. 确定需要精简或扩展的章节

**Key Tasks**:
- 读取现有thesis/所有.tex文件
- 对比analysis_records/最新进展
- 标记需要更新的内容位置
- 生成更新任务清单

---

### Phase 2: Data Preparation

**Goal**: 从Phase 4实验中提取数据，生成论文所需的图表和表格

**Requirements**: FIG-01~05, TAB-01~04

**Success Criteria**:
1. 生成系统架构图（技术链条可视化）
2. 从DA3输出中提取深度对比图（RGB vs Sim vs DA3）
3. 从SAM3输出中提取分割可视化图
4. 生成性能对比表格和深度统计表
5. 所有图表符合论文格式要求

**Key Tasks**:
- 使用tools/中的分析脚本生成可视化
- 整理DA3性能数据
- 整理SAM3分割统计数据
- 导出高分辨率图表

---

### Phase 3: Core Content Update

**Goal**: 根据最新研究进展更新核心章节（Ch3方法论、Ch4实验、Ch5讨论）

**Requirements**: CONT-01~03

**Success Criteria**:
1. Chapter 3更新：添加Phase 4智能感知层详细实现（DA3部署、SAM3部署、深度对齐分析）
2. Chapter 4更新：添加DA3批量处理实验（126张图像、11 FPS性能）、深度对比分析、SAM3分割质量评估
3. Chapter 5更新：讨论DA3位姿预测限制（重要发现）、深度-分割融合策略、未来改进方向
4. 所有更新内容与analysis_records一致

**Key Tasks**:
- 撰写DA3部署和性能测试段落
- 撰写SAM3部署和分割质量段落
- 撰写深度对比和尺度对齐分析
- 撰写DA3位姿不可用结论及影响分析

---

### Phase 4: Literature Update

**Goal**: 更新文献综述，补充最新研究进展

**Requirements**: CONT-04~05, REF-01~03

**Success Criteria**:
1. Chapter 2补充SAM3（arXiv:2511.16719, Feb 2026）相关研究
2. Chapter 2补充Depth Anything 3（arXiv:2511.10647, Dec 2025）相关研究
3. Chapter 1根据实际进展调整研究目标和贡献描述
4. references.bib添加所有新引用

**Key Tasks**:
- 检索SAM3和DA3相关文献
- 撰写文献综述段落
- 更新研究动机和贡献描述
- 添加BibTeX条目

---

### Phase 5: Front Matter & Polish

**Goal**: 完善前置内容，进行最终格式检查和润色

**Requirements**: FRONT-01~04, FMT-01~05, REF-04

**Success Criteria**:
1. 封面信息完整（日期、学号等）
2. 致谢部分个性化内容完成
3. 中英文摘要更新（反映最新进展）
4. 目录结构正确生成
5. 字数控制在1万5千词以内
6. LaTeX编译无错误
7. 所有引用格式统一为Harvard格式

**Key Tasks**:
- 更新cover.tex
- 完善acknowledgements.tex
- 更新abstract.tex
- 字数统计和调整
- 格式检查（页边距、行距、字体）
- 引用格式检查
- 最终编译测试

---

## Dependency Graph

```
Phase 1 (Content Audit)
    ↓
Phase 2 (Data Preparation) ───→ Phase 4 (Literature Update)
    ↓                              ↓
Phase 3 (Core Content Update) ←────┘
    ↓
Phase 5 (Front Matter & Polish)
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Phase 5-6实验无法及时完成 | High | Medium | 调整论文表述，改为方法描述和未来工作 |
| 图表生成脚本出错 | Medium | Medium | 手动截图和绘图作为备选方案 |
| 字数超限 | Medium | High | 精简描述性段落，聚焦关键实验 |
| LaTeX编译错误 | Low | Medium | 分阶段编译，及时修复 |

---

## Milestones

| Milestone | Target | Deliverable |
|-----------|--------|-------------|
| M1: Content Audited | Day 1 | 审计报告 + 更新清单 |
| M2: Data Ready | Day 2-3 | 所有图表和表格 |
| M3: Core Updated | Day 4-6 | Ch3-Ch5更新完成 |
| M4: Literature Complete | Day 6-7 | Ch1-Ch2更新完成 |
| M5: Final Draft | Day 8-9 | 完整论文PDF |

---

## State Tracking

| Phase | Status | Progress | Notes |
|-------|--------|----------|-------|
| 1 | Not Started | 0% | |
| 2 | Not Started | 0% | |
| 3 | Not Started | 0% | |
| 4 | Not Started | 0% | |
| 5 | Not Started | 0% | |

---

*Last updated: 2026-03-13*
