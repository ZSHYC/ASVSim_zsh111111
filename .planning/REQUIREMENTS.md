# Requirements: 本科毕业论文

**项目**: Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting
**定义**: 2026-03-13
**Core Value**: 展示完整的"仿真-感知-重建-规划"技术链条工程实现

---

## v1 Requirements

论文需在2026年5月前完成，包含以下核心章节内容：

### Content Update

- [ ] **CONT-01**: 更新Chapter 3 (Methodology) — 补充DA3深度估计和SAM3分割的详细实现
- [ ] **CONT-02**: 更新Chapter 4 (Experiments) — 添加DA3批量处理性能数据、深度对比分析、SAM3分割质量评估
- [ ] **CONT-03**: 更新Chapter 5 (Discussion) — 讨论DA3位姿预测限制、深度-分割融合策略、未来改进方向
- [ ] **CONT-04**: 完善Chapter 2 (Literature Review) — 补充SAM3、Depth Anything 3等2025年最新研究
- [ ] **CONT-05**: 修订Chapter 1 (Introduction) — 根据实际进展调整研究目标和贡献描述

### Figures and Tables

- [ ] **FIG-01**: 添加系统架构图 (Fig. 1) — 展示完整技术链条
- [ ] **FIG-02**: 添加DA3深度估计结果图 — RGB、仿真深度、DA3深度对比
- [ ] **FIG-03**: 添加SAM3分割可视化图 — 实例掩码、置信度、边界框
- [ ] **FIG-04**: 添加深度对齐分析图 — 误差分布、尺度对比
- [ ] **FIG-05**: 添加采集样本图 — 展示RGB、深度、分割结果
- [ ] **TAB-01**: 添加DA3性能对比表 — CPU vs GPU单张 vs GPU批量
- [ ] **TAB-02**: 添加深度统计表 — 范围、对齐因子、误差指标
- [ ] **TAB-03**: 添加SAM3分割质量表 — 实例数、覆盖比例、置信度
- [ ] **TAB-04**: 添加实验环境配置表 — 硬件、软件版本

### Format and Quality

- [ ] **FMT-01**: 确保所有章节符合Harvard引用格式
- [ ] **FMT-02**: 检查图表编号连续、引用正确
- [ ] **FMT-03**: 验证LaTeX编译无错误
- [ ] **FMT-04**: 字数控制在1万5千词以内
- [ ] **FMT-05**: 页边距、行距、字体符合规范

### Front Matter

- [ ] **FRONT-01**: 完善封面信息（日期、学号等）
- [ ] **FRONT-02**: 补充致谢部分个性化内容
- [ ] **FRONT-03**: 更新中英文摘要（反映最新进展）
- [ ] **FRONT-04**: 更新目录结构

### References

- [ ] **REF-01**: 补充Phase 4相关文献（SAM3、DA3论文）
- [ ] **REF-02**: 添加ASVSim官方文档引用
- [ ] **REF-03**: 添加技术博客和GitHub仓库引用
- [ ] **REF-04**: 检查所有引用格式统一

---

## v2 Requirements

以下内容为论文提交后或未来版本可考虑补充：

### Extended Content

- **EXT-01**: Phase 5 (3DGS重建) 完整实验结果
- **EXT-02**: Phase 6 (路径规划) 实验验证
- **EXT-03**: 真实极地图像的域适应实验
- **EXT-04**: 完整LiDAR-相机联合标定流程

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Phase 5-6完整实验 | 论文截稿前可能无法完成，改为方法描述 |
| 真实极地数据验证 | 受条件限制，聚焦仿真环境 |
| 长篇数学推导 | 本科论文侧重工程实现，简化理论部分 |
| 多场景泛化实验 | 时间有限，聚焦LakeEnv验证 |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONT-01 | Phase 1 | Pending |
| CONT-02 | Phase 2 | Pending |
| CONT-03 | Phase 3 | Pending |
| CONT-04 | Phase 4 | Pending |
| CONT-05 | Phase 5 | Pending |
| FIG-01 | Phase 2 | Pending |
| FIG-02 | Phase 2 | Pending |
| FIG-03 | Phase 2 | Pending |
| FIG-04 | Phase 3 | Pending |
| FIG-05 | Phase 2 | Pending |
| TAB-01 | Phase 2 | Pending |
| TAB-02 | Phase 3 | Pending |
| TAB-03 | Phase 2 | Pending |
| TAB-04 | Phase 1 | Pending |
| FMT-01 | Phase 5 | Pending |
| FMT-02 | Phase 5 | Pending |
| FMT-03 | Phase 5 | Pending |
| FMT-04 | Phase 5 | Pending |
| FMT-05 | Phase 5 | Pending |
| FRONT-01 | Phase 5 | Pending |
| FRONT-02 | Phase 5 | Pending |
| FRONT-03 | Phase 5 | Pending |
| FRONT-04 | Phase 5 | Pending |
| REF-01 | Phase 4 | Pending |
| REF-02 | Phase 4 | Pending |
| REF-03 | Phase 4 | Pending |
| REF-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---

*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after initialization*
