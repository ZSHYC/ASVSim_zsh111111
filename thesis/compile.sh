#!/bin/bash

echo "=========================================="
echo "   论文编译脚本"
echo "=========================================="
echo

echo "[1/4] 第一次编译..."
xelatex -interaction=nonstopmode dissertation.tex

echo "[2/4] 处理参考文献..."
bibtex dissertation

echo "[3/4] 第二次编译..."
xelatex -interaction=nonstopmode dissertation.tex

echo "[4/4] 第三次编译..."
xelatex -interaction=nonstopmode dissertation.tex

echo
echo "=========================================="
if [ -f "dissertation.pdf" ]; then
    echo "   编译成功！"
    echo "   输出文件: dissertation.pdf"
else
    echo "   编译失败，请检查错误"
fi
echo "=========================================="
