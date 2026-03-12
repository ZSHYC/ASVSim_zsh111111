# LaTeX 论文编译踩坑记录

> 论文：Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting
> 记录时间：2026-03-12
> 编译环境：TeX Live 2026 + Windows 11

---

## 📁 保留文件清单

清理后保留的必要文件：

```
thesis/
├── main.tex              # 主文档（导言区+文档结构）
├── cover.tex             # 封面
├── acknowledgements.tex  # 致谢
├── abstract.tex          # 中英文摘要
├── chapter1.tex          # Chapter I: Introduction
├── chapter2.tex          # Chapter II: Literature Review
├── chapter3.tex          # Chapter III: Methodology
├── chapter4.tex          # Chapter IV: Experiments
├── chapter5.tex          # Chapter V: Discussion
├── chapter6.tex          # Chapter VI: Conclusion
├── appendix.tex          # 附录（代码）
├── references.bib        # 参考文献数据库
├── compile.bat           # Windows编译脚本
├── compile.sh            # Linux/macOS编译脚本
├── README.md             # 使用说明
├── main.pdf              # 生成的PDF（可选保留）
└── out/                  # 输出目录
    └── thesis.pdf        # 备份PDF
```

**可删除的临时文件**：
- `main.aux` - 交叉引用辅助文件
- `main.bbl` - 参考文献格式化文件
- `main.bcf` - biblatex控制文件
- `main.blg` - biber日志
- `main.log` - 编译日志
- `main.out` - hyperref书签文件
- `main.run.xml` - 运行配置
- `main.toc` - 目录文件

---

## 🕳️ 踩过的坑及解决方案

### 坑 1：fontspec 包不兼容 pdflatex

**症状**：
```
! Fatal Package fontspec Error: The fontspec package requires either XeTeX or
(fontspec)                      LuaTeX.
(fontspec)
(fontspec)                      You must change your typesetting engine to,
(fontspec)                      e.g., "xelatex" or "lualatex" instead of
(fontspec)                      "latex" or "pdflatex".
```

**原因**：
`fontspec` 包只能与 XeLaTeX 或 LuaLaTeX 一起使用，不能与 pdfLaTeX 一起使用。

**解决方案**：
移除 `fontspec` 包，改用 `times` + `ctex` 组合：

```latex
% 修改前（错误）
\usepackage{times}
\usepackage{fontspec}
\setmainfont{Times New Roman}

% 修改后（正确）
\usepackage{times}
\usepackage[T1]{fontenc}
\usepackage[UTF8]{ctex}  % 中文支持
```

**位置**：`main.tex` 第 13-16 行

---

### 坑 2：中文内容导致 Unicode 错误

**症状**：
```
! LaTeX Error: Unicode character 统 (U+7EDF)
               not set up for use with LaTeX.
```

**原因**：
pdfLaTeX 默认不支持 Unicode 字符，无法直接处理中文。

**解决方案**：
添加 `ctex` 宏包提供中文支持：

```latex
\usepackage[UTF8]{ctex}
```

**位置**：`main.tex` 第 17 行

**注意**：`ctex` 包会自动处理中文字体，不需要额外配置。

---

### 坑 3：listings 包不支持 json 语言

**症状**：
```
! Package Listings Error: Couldn't load requested language.
! Package Listings Error: language json undefined.
```

**原因**：
listings 包默认不支持 JSON 语言定义。

**解决方案**：
将 `language=json` 改为 `language={}`（空语言）或使用 `Python` 语言：

```latex
% 修改前（错误）
\begin{lstlisting}[language=json, caption={...}]

% 修改后（正确）
\begin{lstlisting}[language={}, caption={...}]
% 或者使用 Python 语法高亮
\begin{lstlisting}[language=Python, caption={...}]
```

**位置**：多处出现
- `chapter3.tex` 第 125, 259, 293 行
- `chapter4.tex` 第 263 行
- `appendix.tex` 第 85 行

---

### 坑 4：\citecite 命令不存在

**症状**：
```
! Undefined control sequence.
l.67 ...e, with \citecite{zhang2024marine} proposin...
```

**原因**：
biblatex 中没有 `\citecite` 命令，应该是 `\cite`。

**解决方案**：
将 `\citecite` 改为 `\cite`：

```latex
% 修改前（错误）
with \citecite{zhang2024marine} proposing

% 修改后（正确）
with \cite{zhang2024marine} proposing
```

**位置**：`chapter2.tex` 第 67 行

---

### 坑 5：headheight 太小警告

**症状**：
```
Package fancyhdr Warning: \headheight is too small (12.0pt):
(fancyhdr)                Make it at least 15.74998pt
```

**原因**：
页眉高度太小，可能导致内容被截断。

**解决方案（可选）**：
在导言区添加：

```latex
\setlength{\headheight}{15.75pt}
```

**影响**：这是警告，不影响编译，可以忽略。

---

### 坑 6：参考文献条目未找到

**症状**：
```
LaTeX Warning: Citation 'xu2022point' on page 7 undefined
Package biblatex Warning: The following entry could not be found
(biblatex)                in the database: xu2022point
```

**原因**：
`chapter2.tex` 中引用了 `xu2022point`，但 `references.bib` 中没有这个条目。

**解决方案（可选）**：
1. 在 `references.bib` 中添加该条目
2. 或从 `chapter2.tex` 中删除该引用

**影响**：这是警告，不影响编译，只是该引用会显示为问号。

---

### 坑 7：compile.bat 脚本过于严格

**症状**：
即使 PDF 生成了，脚本也报告失败。

**原因**：
脚本使用 `if errorlevel 1` 检查，但 pdflatex 遇到警告也会返回非零退出码。

**解决方案**：
改为检查 PDF 文件是否存在：

```batch
% 修改前（过于严格）
pdflatex -interaction=nonstopmode main.tex
if errorlevel 1 (
    echo ERROR: First pdflatex pass failed.
    exit /b 1
)

% 修改后（更健壮）
pdflatex -interaction=nonstopmode main.tex
if not exist main.pdf (
    echo ERROR: First pdflatex pass failed - no PDF generated.
    exit /b 1
)
```

---

## ✅ 正确的编译流程

### 方法一：使用脚本（推荐）

```batch
cd thesis
compile.bat
```

### 方法二：手动编译

```batch
% 第1次：生成辅助文件
pdflatex main.tex

% 处理参考文献
biber main

% 第2次：更新引用
pdflatex main.tex

% 第3次：最终编译
pdflatex main.tex
```

### 清理临时文件

```batch
% Windows
del main.aux main.bbl main.bcf main.blg main.log main.out main.run.xml main.toc

% Linux/macOS
rm -f main.aux main.bbl main.bcf main.blg main.log main.out main.run.xml main.toc
```

---

## 📋 文件修改汇总

### main.tex
- 移除 `\usepackage{fontspec}` 和 `\setmainfont{Times New Roman}`
- 添加 `\usepackage[T1]{fontenc}`
- 添加 `\usepackage[UTF8]{ctex}`

### chapter2.tex
- 第67行：将 `\citecite` 改为 `\cite`

### chapter3.tex
- 第125行：将 `language=json` 改为 `language={}`
- 第259行：将 `language=json` 改为 `language={}`
- 第293行：将 `language=json` 改为 `language={}`

### chapter4.tex
- 第263行：将 `language=json` 改为 `language={}`

### appendix.tex
- 第85行：将 `language=json` 改为 `language={}`

### compile.bat
- 将 `if errorlevel 1` 改为 `if not exist main.pdf`

---

## 💡 建议

1. **首次编译**：确保网络连接，以便自动下载缺失的宏包
2. **遇到警告**：大多数警告可以忽略，重点关注错误（以 `!` 开头的）
3. **清理文件**：提交前删除所有临时文件，只保留源代码和 PDF
4. **版本控制**：将 `.tex`, `.bib`, `.bat`, `.sh` 等源文件加入 git，忽略临时文件

---

## 🔗 相关链接

- TeX Live: https://tug.org/texlive/
- ctex 宏包文档: https://ctan.org/pkg/ctex
- listings 宏包文档: https://ctan.org/pkg/listings
- biblatex 文档: https://ctan.org/pkg/biblatex

---

*记录者：Claude Code*
*论文作者：Zhang Shihao*
