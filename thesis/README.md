# ============================================================
# 毕业论文编译和使用说明
# Thesis Compilation and Usage Guide
# ============================================================

## 论文信息

- **题目 (Title)**: Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting
- **作者 (Author)**: Zhang Shihao (张时昊)
- **指导教师 (Supervisor)**: Associate Professor Xing Xianglei (邢向磊)
- **第二导师 (Second Supervisor)**: Professor Dominic Taunton
- **学校 (University)**: Harbin Engineering University (哈尔滨工程大学)
- **学院 (College)**: Southampton Ocean Engineering Joint Institute (南安普顿海洋工程联合学院)
- **专业 (Major)**: Naval Architecture and Ocean Engineering (船舶与海洋工程)

## 论文结构

论文共包含以下章节：

1. **Chapter I: Introduction** (~1,800 words)
   - Research Background
   - Problem Statement
   - Research Objectives
   - Research Significance
   - Thesis Organization

2. **Chapter II: Literature Review** (~2,500 words)
   - Autonomous Navigation in Polar Environments
   - Simulation for Marine Autonomous Systems
   - 3D Reconstruction and Neural Rendering
   - Multi-Modal Perception for Navigation
   - Research Gaps

3. **Chapter III: Methodology** (~3,500 words)
   - System Architecture Overview
   - Simulation Environment Configuration
   - Multi-Modal Data Collection Pipeline
   - Output Data Structure
   - COLMAP Format Conversion
   - Error Handling and Validation

4. **Chapter IV: Experiments and Results** (~2,200 words)
   - Experimental Setup
   - Sensor Validation
   - Data Collection Experiments
   - Data Quality Analysis
   - Dataset Validation

5. **Chapter V: Discussion** (~1,800 words)
   - Interpretation of Results
   - Technical Challenges and Solutions
   - Limitations
   - Comparison with Related Work
   - Future Research Directions

6. **Chapter VI: Conclusion** (~1,200 words)
   - Summary of Work
   - Key Findings
   - Contributions
   - Limitations
   - Future Work

## 文件列表

```
thesis/
├── main.tex              # 主文档 (包含导言区和文档结构)
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
├── references.bib        # 参考文献数据库
├── compile.bat           # Windows编译脚本
├── compile.sh            # Linux/macOS编译脚本
├── README.md             # 本文件
└── out/                  # 输出目录
    └── thesis.pdf        # 生成的PDF
```

## 编译说明

### 方法一：使用编译脚本 (推荐)

#### Windows:
```batch
cd thesis
compile.bat
```

#### Linux/macOS:
```bash
cd thesis
chmod +x compile.sh
./compile.sh
```

### 方法二：手动编译

```bash
# 步骤1: 首次编译生成辅助文件
pdflatex main.tex

# 步骤2: 运行biber处理参考文献
biber main

# 步骤3: 再次编译更新引用
pdflatex main.tex

# 步骤4: 最终编译生成完整PDF
pdflatex main.tex
```

### 编译要求

需要安装以下软件：

- **TeX Live** (推荐) 或 **MiKTeX** (Windows)
- **Biber** (用于处理参考文献)
- 以下LaTeX宏包 (通常已包含在发行版中):
  - geometry
  - fontspec
  - setspace
  - titlesec
  - fancyhdr
  - graphicx
  - caption
  - enumitem
  - amsmath
  - amssymb
  - listings
  - biblatex
  - hyperref
  - booktabs
  - xcolor

### 字体要求

- **Times New Roman**: 论文正文使用的主字体
- **宋体**: 中文摘要部分使用

## 踩坑记录

如果在编译过程中遇到问题，请参考 `TROUBLESHOOTING.md` 文件，其中记录了常见错误和解决方案。

### 已知问题速查

| 问题 | 解决方案 |
|------|----------|
| fontspec 错误 | 使用 `\usepackage[UTF8]{ctex}` 替代 |
| Unicode 字符错误 | 添加 `ctex` 包 |
| json 语言不支持 | 改为 `language={}` |
| 引用未找到 | 检查 `references.bib` |

---

## 格式规范

本论文遵循哈尔滨工程大学本科生毕业论文（英语类）撰写规范：

- **正文**: 1万5千词以内
- **一级标题**: 罗马数字 (I, II, III...)
- **二级标题**: 阿拉伯数字 (1.1, 1.2...)
- **三级标题**: 阿拉伯数字 (1.1.1, 1.1.2...)
- **引用格式**: Harvard格式
- **行距**: 固定值22磅
- **页边距**: 上28mm、下28mm、左25mm、右25mm

## 技术特色

本论文基于你的实际项目进展撰写，包含以下技术内容：

1. **UE5 + ASVSim仿真平台配置**
   - 生产级settings.json配置
   - 相机和LiDAR传感器布局
   - 渲染优化策略

2. **多模态数据采集系统**
   - V2版本采集脚本
   - 640×480分辨率优化
   - 9倍性能提升

3. **3DGS重建流程**
   - COLMAP格式转换
   - 位姿同步机制

4. **实验验证**
   - 200帧数据集采集
   - 传感器验证结果
   - 数据质量分析

## 注意事项

1. **编译前请确保**: 已安装完整的LaTeX发行版

2. **首次编译**: 可能需要下载缺失的宏包，请保持网络连接

3. **参考文献**: 使用Biber处理，支持Harvard格式

4. **图片占位符**: 论文中包含图片占位符，请替换为实际图表:
   - Fig. 1: System Architecture
   - Fig. 2: Sample RGB frames
   - Table 1-8: 各种配置参数和实验结果

5. **代码片段**: 附录中包含核心代码，可根据需要调整

## 后续工作

论文初稿已完成，建议后续：

1. 添加实际采集的图像作为Figure
2. 补充实验数据的具体数值
3. 根据导师反馈修改内容
4. 检查引用格式和参考文献
5. 添加致谢部分的个性化内容

## 联系方式

如有编译问题或需要修改论文内容，请随时联系。

---

**论文生成日期**: 2026年3月12日
**字数统计**: 约13,000词 (正文部分)
