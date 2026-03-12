---
name: thesis-helper
description: |
  帮助用户撰写本科毕业论文的专业skill。当用户提到"毕业论文"、"论文写作"、"论文结构"、
  "文献综述"、"研究方法"、"论文格式"、"参考文献"、"thesis"、"dissertation"等关键词时自动触发。

  特别适用于：计算机科学与技术、计算机视觉、机器人工程、人工智能、具身智能、船舶与海洋工程等理工科专业。
  支持中英文论文写作，可读取用户提供的格式要求文件。

  提供完整的论文写作指导，包括：
  - 论文结构规划（摘要、引言、文献综述、方法论、结果、讨论、结论）
  - 各章节写作模板和范例
  - 学术写作规范和格式要求
  - 逻辑梳理和论证结构优化
  - 理工科（计算机/AI/机器人/船舶海洋工程）论文写作特点
  - 参考文献管理和引用规范（GB/T 7714、APA、MLA、IEEE等）
  - 英文学术写作规范

  无论用户处于论文写作的哪个阶段（选题、开题、初稿、修改、生成完整论文），都应该使用此skill提供指导。
---
# 本科毕业论文写作助手

## 概述

本skill旨在帮助本科生完成毕业论文的撰写工作，特别针对**计算机科学、人工智能、计算机视觉、机器人工程、具身智能**等理工科专业，支持**中英文**论文写作。

## 格式要求文件

如果项目目录中有格式要求文件（如 `format-requirements.md`、`论文格式要求.docx`、`格式说明.pdf` 、`论文模板.docx`、`论文撰写规范.docx`等），**务必先读取该文件**，并按照其中的具体要求指导用户。

## 用户个人信息（用于自动生成封面和扉页）

以下是用户的个人信息，在生成论文封面、扉页等需要使用：

| 项目                            | 内容                                                                                     |
| ------------------------------- | ---------------------------------------------------------------------------------------- |
| **姓名（中文）**          | 张时昊                                                                                   |
| **姓名（英文）**          | Zhang Shihao                                                                             |
| **学院（英文）**          | Southampton Ocean Engineering Joint Institute                                            |
| **学院（中文）**          | 南安普顿海洋工程联合学院                                                                 |
| **专业（英文）**          | Naval Architecture and Ocean Engineering                                                 |
| **专业（中文）**          | 船舶与海洋工程                                                                           |
| **指导教师（中文）**      | 邢向磊                                                                                   |
| **指导教师（英文）**      | Xing Xianglei                                                                            |
| **指导教师职称（中文）**  | 副教授                                                                                   |
| **指导教师职称（英文）**  | Associate Professor                                                                      |
| **指导教师2（英文）**     | Dominic Taunton                                                                          |
| **指导教师2职称（英文）** | Professor                                                                                |
| **学校（英文）**          | Harbin Engineering University                                                            |
| **学校（中文）**          | 哈尔滨工程大学                                                                           |
| **论文题目（中文）**      | 基于 Unreal Engine 和 3D Gaussian Splatting 的极地路径规划与三维重建                     |
| **论文题目（英文）**      | Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting |
| **提交日期**              | May 2026                                                                                 |
| **答辩日期**              | May 2026                                                                                 |
| **学位授予单位**          | Harbin Engineering University                                                            |

**学科方向：** 船舶与海洋工程 + 计算机视觉/三维重建/机器人工程/具身智能

**研究关键词：** Unreal Engine, 3D Gaussian Splatting, Polar Route Planning, 3D Reconstruction, Naval Architecture

## 国际博士论文标准参考（格式冲突或缺失时使用）

当遇到以下情况时，请参考国际顶级大学的博士毕业论文标准（作为最高质量参考）：

- 无法找到具体的格式要求文件
- 格式要求文件内容不完整或存在冲突
- 需要判断哪种格式更专业、更符合学术规范

### 推荐参考标准（按优先级）

1. **MIT博士论文标准**（计算机/工程领域标杆）

   - 结构：Abstract → Acknowledgments → Contents → List of Figures/Tables → Chapters → Bibliography → Appendices
   - 页边距：左侧1.5英寸（装订边），其他边1英寸
   - 字体：12pt Times New Roman或Computer Modern
   - 行距：双倍行距或1.5倍行距
   - 章节编号：阿拉伯数字连续编号
2. **Stanford博士论文标准**（理工科综合标准）

   - 封面：Title → Author → Degree → Department → University → Year
   - 版权声明页（可选）
   - 签名页（Committee approval）
   - 前言部分使用小写罗马数字页码
   - 正文使用阿拉伯数字页码
3. **CMU/Stanford CS博士论文标准**

   - 强调技术贡献的清晰阐述
   - 要求包含相关工作深度综述
   - 方法论需详尽到可复现
   - 实验部分需有baseline对比和消融实验
4. **剑桥大学博士论文标准**（人文社科+理工科通用）

   - 严格的引用规范（通常使用Harvard或Numeric）
   - 强调文献综述的批判性分析
   - 方法论章节的哲学基础说明

### 国际通用格式冲突解决原则

当不同格式要求冲突时，按以下优先级决策：

1. **用户所在学校的硬性规定** > 国际标准（必须遵守）
2. **学科领域惯例** > 通用标准（如CS领域优先IEEE/ACM格式）
3. **最新版本标准** > 旧版标准
4. **更详细的规范** > 简略规范
5. **国际顶级大学标准** > 一般学校标准

### 博士论文级别的质量标准（本科论文应尽可能向此靠拢）

**内容深度：**

- Introduction：不仅说明做了什么，更要说明为什么重要，与领域的关联
- Related Work：系统性综述，能画出领域发展脉络图，明确指出research gap
- Methodology：形式化定义，算法伪代码，复杂度分析，正确性证明（如适用）
- Experiments：多数据集验证，消融实验，参数敏感性分析，统计显著性检验
- Results：可视化质量高，表格符合 publication-ready 标准
- Discussion：深入分析成功/失败原因，与理论的关联
- Conclusion：总结贡献，明确指出局限性，提出有价值的未来方向

**写作质量：**

- 每章开头有mini-intro说明本章内容和与前后章的关联
- 图表清晰自明（self-contained），标题和注释充分
- 数学符号全文统一，首次出现有定义
- 代码片段精选关键部分，不是全文复制
- 引用全面且最新（近5年文献占50%以上）

## 哈尔滨工程大学英文论文格式要求

以下内容基于哈尔滨工程大学本科生毕业论文（英语类）撰写规范：

### 内容要求

**摘要：**

- 英文摘要约250个实词
- 包含目的、方法、结果和结论
- 中文摘要另起一页，与英文摘要内容一致

**目录：**

- 至多体现三级标题
- 一级标题用罗马数字(I, II, III…)
- 二级、三级用阿拉伯数字(1.1, 1.1.1…)

**正文字数：** 1万五千词以内

### 排版格式

| 项目     | 格式                           |
| -------- | ------------------------------ |
| 论文题目 | 2号Times New Roman Bold        |
| 章标题   | 小2号Times New Roman Bold      |
| 节标题   | 小3号Times New Roman Bold      |
| 条标题   | 4号Times New Roman Bold        |
| 款标题   | 小4号Times New Roman Bold      |
| 正文     | 小4号Times New Roman           |
| 行距     | 固定值22磅                     |
| 页边距   | 上28mm、下28mm、左25mm、右25mm |

### 页码设置

- 封面、扉页：不编页码
- 摘要、目录：罗马数字连续编排
- 正文至附录：阿拉伯数字连续编排
- 页码位置：页面底端居中

### 装订顺序

1. 封面及书脊
2. 扉页
3. 致谢
4. 英文摘要
5. 中文摘要
6. 目录
7. 正文
8. 参考文献
9. 攻读学士学位期间取得的学术成果
10. 附录

## 论文基本结构（理工科/英文）

英文毕业论文通常包含以下章节：

1. **Title Page** - 封面
2. **Declaration/Originality Statement** - 原创性声明
3. **Abstract** - 摘要（英文300-500 words）
4. **Acknowledgements** - 致谢
5. **Table of Contents** - 目录
6. **List of Figures/Tables** - 图表目录
7. **Main Body** - 正文
   - Chapter 1 Introduction
   - Chapter 2 Literature Review / Related Work
   - Chapter 3 Methodology / System Design
   - Chapter 4 Experiments / Implementation
   - Chapter 5 Results and Discussion
   - Chapter 6 Conclusion and Future Work
8. **References** - 参考文献
9. **Appendices** - 附录（如有）

## 各章节写作指导

### 第1章 绪论/引言

**核心内容：**

- 研究背景：说明研究的现实意义和理论价值
- 研究目的：明确要解决什么问题
- 研究意义：分理论意义和实践意义
- 研究方法：简要说明采用的方法
- 论文结构：概述各章节安排

**写作模板：**

```
1.1 研究背景
[描述研究领域现状，指出存在的问题或空白]

1.2 研究目的与意义
1.2.1 研究目的
[具体说明本研究要达到的目标]

1.2.2 研究意义
理论意义：[对学科理论的贡献]
实践意义：[对实际工作的指导价值]

1.3 研究方法
[说明采用的研究方法，如文献研究法、问卷调查法、案例分析法等]

1.4 论文结构安排
[简述各章节主要内容]
```

### 第2章 文献综述

**核心内容：**

- 国内外研究现状
- 主要理论框架
- 研究述评（已有研究的不足）

**写作要点：**

- 按主题或时间顺序组织，不是简单罗列
- 要有批判性分析，指出研究gap
- 引用规范，避免抄袭

**模板结构：**

```
2.1 [主题1]相关研究
2.2 [主题2]相关研究
2.3 理论框架
2.4 研究述评
```

### 第3章 研究设计/方法论

**核心内容：**

- 研究思路/技术路线
- 研究方法详述
- 数据来源与收集
- 分析方法

**学科要点：**

**理工科：**

- 实验设计要详细（设备、材料、步骤）
- 控制变量说明
- 数据处理方法

### 第4章 研究结果

**写作要点：**

- 客观呈现数据和分析结果
- 多用图表辅助说明
- 避免在此章过度解释

### 第5章 讨论

**核心内容：**

- 结果解释（为什么会出现这样的结果）
- 与文献对比（与已有研究一致或矛盾）
- 理论贡献
- 实践启示

### 第6章 结论与展望

**结构：**

```
6.1 研究结论
[分点总结主要发现，对应研究目的]

6.2 研究创新点
[明确说明本研究的创新之处]

6.3 研究局限
[客观说明不足之处]

6.4 未来研究展望
[提出后续研究方向]
```

## 学科特点指南

### 计算机/AI/机器人工程专业论文特点

**计算机科学与技术：**

- **系统设计重点：** 架构图、类图、流程图清晰展示
- **代码实现：** 关键算法伪代码或代码片段
- **性能评估：** 时间复杂度、空间复杂度分析
- **实验对比：** 与现有方法的性能对比

**计算机视觉：**

- **数据集说明：** 训练集/测试集划分，数据预处理
- **网络结构：** 模型架构图，参数量说明
- **评价指标：** Accuracy、Precision、Recall、F1、mAP等
- **可视化结果：** 检测/分割效果对比图

**机器人工程：**

- **硬件架构：** 机械结构、传感器配置
- **控制算法：** 运动规划、路径规划算法
- **系统集成：** 软硬件协同设计
- **实验验证：** 实物测试或仿真验证

**人工智能/具身智能：**

- **问题建模：** MDP、POMDP等形式化描述
- **算法设计：** 强化学习、模仿学习等算法细节
- **仿真环境：** Isaac Sim、Mujoco等环境配置
- **真实部署：** sim-to-real迁移策略

**船舶与海洋工程（结合计算机技术方向）：**

- **应用场景：** 极地航行路径规划、船舶三维重建、海洋环境仿真
- **技术融合：** 结合UE/Unreal Engine进行海洋环境可视化、3D Gaussian Splatting进行船舶/海洋结构物重建
- **实验验证：** 数值仿真与物理模型试验结合
- **评价指标：** 路径规划效率、重建精度、实时性、鲁棒性
- **特色图表：** 海洋环境渲染图、船舶航线可视化、点云重建对比图
- **数据来源：** AIS数据、卫星遥感、声呐数据、仿真生成数据

### 英文学术写作规范

**常用句型：**

*Introduction部分：*

- In recent years, ... has become an increasingly important area of research.
- Despite significant progress in ..., ... remains a challenging problem.
- This paper presents a novel approach to ...

*Methodology部分：*

- We propose a ... method that ...
- The architecture consists of three main components: ...
- Formally, we define ... as follows:

*Results部分：*

- Experimental results demonstrate that ...
- As shown in Table 1, our method achieves ...
- Compared with the baseline, ...

*Conclusion部分：*

- In this paper, we have presented ...
- Our approach outperforms existing methods by ...
- Future work will focus on ...

## 学术规范

### 引用规范

**Harvard格式（哈尔滨工程大学英文论文要求）：**

*期刊论文：*

- Author(s) Year, 'Title of article', Title of Journal, Volume number(issue number), pp. page range.
- 示例：Smith, J. & Jones, M. 2023, 'Deep learning for computer vision', IEEE Transactions, 45(2), pp. 112-128.

*书籍：*

- Author(s) Year, Title of Book, Edition (if not first), Publisher, Place of publication.
- 示例：Goodfellow, I., Bengio, Y. & Courville, A. 2016, Deep Learning, MIT Press, Cambridge.

*会议论文：*

- Author(s) Year, 'Title of paper', in Title of Conference Proceedings, Place, Date, pp. page range.
- 示例：Wang, L. et al. 2022, 'Vision transformers for image recognition', in Proceedings of CVPR, New Orleans, 19-24 June, pp. 12156-12165.

*学位论文：*

- Author Year, Title of thesis, Degree statement, Name of Institution, Place.
- 示例：Zhang, Y. 2021, Multi-modal robot perception using deep learning, PhD thesis, Stanford University, California.

*网页/电子资源：*

- Author/Organisation Year, Title of webpage, Website name, Date viewed, `<URL>`.
- 示例：PyTorch 2023, PyTorch Documentation, PyTorch.org, viewed 15 March 2023, [https://pytorch.org/docs/](https://pytorch.org/docs/).

**GB/T 7714-2015（中国国家标准）：**

- 期刊：作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.
- 专著：作者. 书名[M]. 出版地: 出版者, 出版年: 起止页码.
- 学位论文：作者. 题名[D]. 保存地: 保存单位, 年份.
- 网页：作者. 题名[EB/OL]. (发布日期)[引用日期]. 网址.

**IEEE格式（计算机领域常用）：**

- 期刊：[1] A. Author, B. Author, "Title of article," Title of Journal, vol. x, no. x, pp. xxx-xxx, Month Year.
- 会议：[1] A. Author et al., "Title of paper," in Proc. Conference Name, Location, Year, pp. xxx-xxx.
- 书籍：[1] A. Author, Title of Book, xth ed. City, State: Publisher, Year.

**APA格式（第7版）：**

- 期刊：Author, A. A. (Year). Title of article. Title of Journal, vol(issue), pp-pp. https://doi.org/xx
- 书籍：Author, A. A. (Year). Title of work. Publisher.

### 避免学术不端

- 引用比例控制在合理范围（通常<30%）
- 直接引用要加引号并标注
- 间接引用也要标注来源
- 使用查重工具检测

## 格式要求

### 排版规范（通用）

- **字体：** 正文宋体/Times New Roman小四，标题黑体
- **行距：** 1.5倍行距
- **页边距：** 上下2.54cm，左右3.17cm
- **页码：** 底部居中，从正文开始
- **图表：** 编号连续，表题在上，图题在下

### 标题层级

- 一级标题：第1章 （居中，三号黑体）
- 二级标题：1.1 （左对齐，四号黑体）
- 三级标题：1.1.1 （左对齐，小四黑体）
- 四级标题：1. （左对齐，小四宋体加粗）

## 写作流程建议

1. **选题阶段：** 确定研究问题，明确研究范围
2. **开题阶段：** 完成文献综述，确定研究方法
3. **初稿阶段：** 先写方法论和结果，再写引言和结论
4. **修改阶段：** 检查逻辑连贯性，完善论证
5. **定稿阶段：** 格式调整，语言润色，查重

## 常见错误提醒

1. **结构问题：** 章节之间逻辑跳跃
2. **文献问题：** 引用过时文献，或缺少重要文献
3. **方法问题：** 方法与问题不匹配
4. **结果问题：** 结果与数据不符，过度解读
5. **格式问题：** 参考文献格式不统一
6. **语言问题：** 口语化，错别字，标点错误

## LaTeX论文排版指南

由于用户要求使用LaTeX格式书写论文，提供以下LaTeX排版支持：

### 推荐的LaTeX模板

**哈尔滨工程大学英文论文LaTeX模板结构：**

```latex
\documentclass[12pt,a4paper]{article}

% 页面设置
\usepackage[top=28mm,bottom=28mm,left=25mm,right=25mm]{geometry}
\usepackage{setspace}
\usepackage{times}

% 章节标题格式
\usepackage{titlesec}
\titleformat{\section}{\centering\fontsize{15pt}{22pt}\selectfont\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\fontsize{13pt}{22pt}\selectfont\bfseries}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\fontsize{14pt}{22pt}\selectfont\bfseries}{\thesubsubsection}{1em}{}

% 行距设置
\setlength{\parindent}{2em}
\linespread{1.0}  % 固定值22磅对应1.0

% 页眉页脚
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\fontsize{10.5pt}{15.75pt}\selectfont 哈尔滨工程大学本科生毕业论文}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% 图表
\usepackage{graphicx}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}

% 参考文献
\usepackage[backend=biber,style=authoryear]{biblatex}
\addbibresource{references.bib}

\begin{document}

% 封面
\input{cover}

% 摘要
\input{abstract}

% 目录
\tableofcontents
\newpage

% 正文
\input{chapter1}
\input{chapter2}
\input{chapter3}
\input{chapter4}
\input{chapter5}
\input{chapter6}

% 参考文献
\printbibliography[title=References]

% 附录（如有）
\appendix
\input{appendix}

\end{document}
```

### LaTeX格式要求对照

| Word格式要求              | LaTeX设置                                        |
| ------------------------- | ------------------------------------------------ |
| 2号Times New Roman Bold   | `\fontsize{22pt}{33pt}\selectfont\bfseries`    |
| 小2号Times New Roman Bold | `\fontsize{18pt}{27pt}\selectfont\bfseries`    |
| 小3号Times New Roman Bold | `\fontsize{15pt}{22.5pt}\selectfont\bfseries`  |
| 4号Times New Roman Bold   | `\fontsize{14pt}{21pt}\selectfont\bfseries`    |
| 小4号Times New Roman      | `\fontsize{12pt}{18pt}\selectfont`             |
| 固定值22磅行距            | `\linespread{1.0}` 或使用 `\setstretch{1.0}` |
| 段首缩进2字符             | `\setlength{\parindent}{2em}`                  |
| 页边距28/28/25/25mm       | `geometry` 包设置                              |

### 章节标题编号

```latex
% 一级标题：罗马数字
\renewcommand{\thesection}{\Roman{section}.}

% 二级标题：阿拉伯数字
\renewcommand{\thesubsection}{\thesection\arabic{subsection}}

% 三级标题
\renewcommand{\thesubsubsection}{\thesubsection.\arabic{subsubsection}}
```

### 图表编号

```latex
% 图表按章编号
\renewcommand{\thefigure}{\arabic{section}.\arabic{figure}}
\renewcommand{\thetable}{\arabic{section}.\arabic{table}}
\makeatletter
\@addtoreset{figure}{section}
\@addtoreset{table}{section}
\makeatother

% 使用示例
\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{figure1.png}
\caption{System Architecture}
\label{fig:architecture}
\end{figure}
```

### 页码设置

```latex
% 罗马数字页码（摘要、目录）
\pagenumbering{roman}

% 阿拉伯数字页码（正文）
\newpage
\pagenumbering{arabic}
\setcounter{page}{1}
```

### 生成完整LaTeX论文

当用户要求生成完整论文时，应：

1. 生成主文档 `.tex` 文件（包含导言区和文档结构）
2. 生成各章节 `.tex` 文件（chapter1.tex, chapter2.tex, ...）
3. 生成参考文献 `.bib` 文件
4. 提供编译说明（需要编译两次：pdflatex -> biber -> pdflatex）

### LaTeX写作模板示例

**Chapter 1: Introduction**

```latex
% chapter1.tex
\section{INTRODUCTION}

\subsection{Research Background}
In recent years, deep learning has revolutionized the field of computer vision...

\subsection{Problem Statement}
Despite significant progress, existing methods still face challenges in...

\subsection{Research Objectives}
The main objectives of this thesis are:
\begin{enumerate}
    \item To develop a novel approach for...
    \item To improve the accuracy of...
    \item To validate the proposed method through extensive experiments
\end{enumerate}

\subsection{Contributions}
The main contributions of this work are summarized as follows:
\begin{itemize}
    \item We propose...
    \item We design...
\end{itemize}

\subsection{Thesis Organization}
The remainder of this thesis is organized as follows: Chapter 2 reviews...
```

当用户提出以下请求时：

**"帮我规划论文结构" / "论文应该怎么安排"** →

1. 询问学科和研究主题
2. 读取格式要求文件（如有）
3. 提供定制化结构建议

**"帮我写/修改XX章节"** →

1. 读取用户已有的内容（如有）
2. 提供该章节的写作模板和要点
3. 帮助组织内容，提供英文表达建议

**"检查我的论文逻辑"** →

1. 分析章节间的逻辑关系
2. 指出可能的断层或跳跃
3. 提供改进建议

**"参考文献格式" / "References格式"** →

1. 询问使用哪种格式（Harvard/IEEE/APA/MLA/GB/T 7714）
2. 提供示例和转换建议
3. 哈尔滨工程大学要求使用Harvard格式

**"论文修改建议"** →

1. 读取用户论文文件
2. 提供检查清单
3. 逐章给出修改建议

**"生成完整论文" / "帮我写一篇论文"** →

1. 询问论文主题、研究方向、字数要求
2. 读取格式要求文件
3. 按章节顺序生成完整的英文毕业论文
4. 确保符合格式规范和学术规范

## 生成完整论文的流程

当用户要求生成完整论文时，按以下步骤执行：

### 步骤1：信息收集

- 论文主题/标题
- 学科方向（CV/机器人/AI/具身智能等）
- 目标字数
- 格式要求文件路径
- 是否有实验数据/代码需要包含

### 步骤2：深度理解项目内容（关键步骤）

在写作之前，**必须全面理解用户的项目**，这是生成高质量论文的基础：

**2.1 扫描项目文件夹结构**
使用 `find`、`ls` 或 `glob` 工具扫描项目目录，识别所有相关内容：

```
- 代码文件：*.py, *.cpp, *.java, *.m, *.ipynb 等
- 文档文件：*.md, *.txt, *.docx, *.pdf 等
- 数据文件：*.csv, *.json, *.yaml, *.xml 等
- 图片/图表：*.png, *.jpg, *.pdf, *.svg 等
- 网址/链接：*.url, bookmarks 等
- 配置文件：*.cfg, *.ini, *.conf 等
```

**2.2 阅读并理解所有关键文件**

*必须阅读的内容：*

- **README.md**：项目概述、安装说明、使用方法
- **代码文件**：核心算法实现、模型定义、训练脚本
- **实验脚本**：数据预处理、训练配置、评估代码
- **文档/笔记**：研究笔记、实验记录、问题解决方案
- **结果文件**：实验日志、输出结果、对比数据

*阅读策略：*

1. 从高层文档（README、overview）开始，建立整体认知
2. 深入核心代码（模型架构、关键算法），理解技术细节
3. 查看实验配置和数据，理解实验设计
4. 阅读注释和commit历史（如有），了解开发过程

**2.3 提取关键信息**

从项目中提取论文所需的关键信息：

| 论文章节     | 需要从项目提取的信息                       |
| ------------ | ------------------------------------------ |
| Introduction | 研究动机、解决的问题、应用场景             |
| Related Work | 项目参考的论文、方法对比的baseline         |
| Methodology  | 模型架构图、算法流程、创新点设计、公式推导 |
| Experiments  | 数据集信息、训练参数、硬件环境、评估指标   |
| Results      | 实验结果数据、对比表格、可视化图表         |
| Discussion   | 实验观察、失败案例分析、改进过程           |

**2.4 构建项目知识图谱**

将理解的内容组织成：

- **核心贡献**：项目的3-5个主要创新点
- **技术路线图**：从输入到输出的完整流程
- **实验证据**：支持每个claim的数据和图表
- **对比优势**：与现有方法的具体差异和优势

**2.5 识别缺失信息**

如果项目中缺少某些必要信息：

- 向用户询问缺失的细节
- 根据已有内容合理推断（需标注为推测）
- 使用学术惯例补充标准内容

### 步骤3：格式确认

- 读取并解析格式要求文件
- 确认论文结构模板
- 确定各章节字数分配
- **格式冲突处理**：如遇格式要求不明确或冲突，参考"国际博士论文标准参考"章节

### 步骤4：逐章生成（LaTeX格式）

按顺序生成各章节内容，每个章节保存为单独的 `.tex` 文件：

1. **main.tex** - 主文档（导言区、文档结构）
2. **cover.tex** - 封面
3. **abstract.tex** - 中英文摘要
4. **chapter1.tex** - Chapter 1 Introduction (~1500 words)
5. **chapter2.tex** - Chapter 2 Related Work (~2000 words)
6. **chapter3.tex** - Chapter 3 Methodology (~2500 words)
7. **chapter4.tex** - Chapter 4 Experiments (~1000 words)
8. **chapter5.tex** - Chapter 5 Results (~1000 words)
9. **chapter6.tex** - Chapter 6 Discussion (~800 words)
10. **chapter7.tex** - Chapter 7 Conclusion (~500 words)
11. **references.bib** - BibTeX参考文献
12. **appendix.tex** - 附录（如有）

### 步骤5：格式整理（LaTeX）

- 应用Harvard格式要求的LaTeX设置（字体、行距、页边距）
- 设置章节编号格式（一级罗马数字，二三级阿拉伯数字）
- 配置页眉页脚
- 设置图表编号（按章编号）
- 生成目录
- 配置参考文献样式（Harvard风格）

### 步骤6：编译说明

提供编译指令：

```bash
# 编译LaTeX文档
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

或提供Makefile：

```makefile
all:
	pdflatex main
	biber main
	pdflatex main
	pdflatex main

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc
```
