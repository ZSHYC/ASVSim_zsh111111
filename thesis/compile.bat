@echo off
chcp 65001 >nul
echo ==========================================
echo    论文编译脚本
echo ==========================================
echo.

echo [1/4] 第一次编译...
xelatex -interaction=nonstopmode dissertation.tex > compile.log 2>&1

echo [2/4] 处理参考文献...
bibtex dissertation > compile.log 2>&1

echo [3/4] 第二次编译...
xelatex -interaction=nonstopmode dissertation.tex > compile.log 2>&1

echo [4/4] 第三次编译...
xelatex -interaction=nonstopmode dissertation.tex > compile.log 2>&1

echo.
echo ==========================================
if exist dissertation.pdf (
    echo    编译成功！
    echo    输出文件: dissertation.pdf
) else (
    echo    编译失败，请检查错误
    echo    查看 compile.log 了解详情
)
echo ==========================================

pause
