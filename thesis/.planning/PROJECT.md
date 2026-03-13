# 论文格式校对项目

## What This Is

将现有 LaTeX 论文按照哈尔滨工程大学本科生毕业论文（英语类）模板进行格式校对，确保排版完全符合学校规范。

## Core Value

论文排版格式 100% 符合哈尔滨工程大学英文论文模板要求，包括字体、字号、行距、页边距、页眉页脚、章节编号等所有细节。

## Requirements

### Validated

(暂无)

### Active

- [ ] 封面格式校对（中英文封面、扉页）
- [ ] 页眉页脚格式校对（双页/单页不同设置）
- [ ] 章节标题格式校对（罗马数字/阿拉伯数字）
- [ ] 正文格式校对（字体、行距、缩进）
- [ ] 图表标题格式校对
- [ ] 参考文献格式校对（Harvard 格式）
- [ ] 目录格式校对
- [ ] 摘要格式校对
- [ ] 书脊格式校对

### Out of Scope

- 内容修改（只调整格式，不改内容）
- 新增章节
- 参考文献内容补充

## Context

**现有文件：**
- main.tex - 主文档
- cover.tex / cover_chinese.tex - 英文/中文封面
- titlepage_en.tex / titlepage_zh.tex - 英文/中文扉页
- abstract.tex - 摘要
- acknowledgements.tex - 致谢
- chapter1-6.tex - 正文各章
- appendix.tex - 附录
- references.bib - 参考文献
- spine.tex - 书脊

**格式规范来源：**
- 哈尔滨工程大学本科生毕业论文(英语类)撰写规范.md
- thesis-helper/SKILL.md（个人信息）
- 22级论文模板.pdf（视觉参考）

## Constraints

- **工具:** LaTeX (XeLaTeX/pdflatex)
- **时间:** 立即执行
- **目标:** 可直接编译通过的完整格式

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 一次性服务而非工具 | 用户只需要当前论文格式调整 | — Pending |
| 先修复已知问题再全面检查 | 提高效率 | — Pending |

---
*Last updated: 2026-03-14 after initialization*
