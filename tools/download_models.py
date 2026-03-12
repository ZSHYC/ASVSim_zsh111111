"""
模型下载辅助脚本
将 SAM 3 和 Depth Anything 3 模型下载到 D 盘

使用方法：
    python download_models.py [--model {sam3|da3|all}]

示例：
    python download_models.py --model sam3
    python download_models.py --model da3
    python download_models.py --model all
"""

import os
import sys
import argparse
from pathlib import Path

# D 盘模型目录
DRIVE_D_MODELS = Path("D:/ASVSim_models")

def setup_dirs():
    """创建必要的目录结构"""
    dirs = [
        DRIVE_D_MODELS / "sam3",
        DRIVE_D_MODELS / "depth_anything_3",
        DRIVE_D_MODELS / "cache" / "hub",
        DRIVE_D_MODELS / "cache" / "torch",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"✓ 目录已创建/存在: {d}")

def download_sam3():
    """下载 SAM 3 模型"""
    print("\n" + "="*60)
    print("下载 SAM 3 模型")
    print("="*60)
    print("\n⚠️  注意：SAM 3 需要先在 Hugging Face 申请权限！")
    print("    访问: https://huggingface.co/facebook/sam3")
    print()

    try:
        from huggingface_hub import hf_hub_download, login

        # 检查是否已登录
        try:
            login()
            print("✓ Hugging Face 登录成功")
        except Exception as e:
            print(f"⚠️  登录失败: {e}")
            print("    尝试使用本地缓存或继续下载...")

        # 下载 SAM 3
        print("\n正在下载 SAM 3...")
        model_path = hf_hub_download(
            repo_id='facebook/sam3',
            filename='sam3.pt',
            local_dir=str(DRIVE_D_MODELS / "sam3"),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print(f"✓ SAM 3 下载完成: {model_path}")

    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        print("\n手动下载步骤：")
        print("  1. 访问 https://huggingface.co/facebook/sam3")
        print("  2. 申请权限并登录")
        print("  3. 下载 sam3.pt")
        print(f"  4. 放置到: {DRIVE_D_MODELS / 'sam3' / 'sam3.pt'}")
        return False

    return True

def download_da3():
    """下载 Depth Anything 3 模型"""
    print("\n" + "="*60)
    print("下载 Depth Anything 3 模型")
    print("="*60)

    models_to_download = [
        ("depth-anything/DA3-LARGE-1.1", "da3_large_1.1.pth", "DA3-LARGE (推荐, 0.35B)"),
        ("depth-anything/DA3MONO-LARGE", "da3_mono_large_1.1.pth", "DA3-MONO (备选, 0.35B)"),
    ]

    # 可选：完整版（显存占用高）
    # models_to_download.append(
    #     ("depth-anything/DA3NESTED-GIANT-LARGE-1.1", "da3_nested_giant_large_1.1.pth", "DA3-NESTED (完整版, 1.4B)")
    # )

    try:
        from huggingface_hub import hf_hub_download

        for repo_id, filename, desc in models_to_download:
            print(f"\n正在下载 {desc}...")
            try:
                model_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=str(DRIVE_D_MODELS / "depth_anything_3"),
                    local_dir_use_symlinks=False,
                    resume_download=True
                )
                print(f"✓ {desc} 下载完成: {model_path}")
            except Exception as e:
                print(f"⚠️  {desc} 下载失败: {e}")
                continue

    except ImportError:
        print("\n❌ 请先安装 huggingface_hub: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        print("\n手动下载步骤：")
        print("  1. 访问 https://huggingface.co/depth-anything")
        print("  2. 下载 DA3-LARGE-1.1 和 DA3MONO-LARGE")
        print(f"  3. 放置到: {DRIVE_D_MODELS / 'depth_anything_3'}")
        return False

    return True

def check_existing():
    """检查已下载的模型"""
    print("\n" + "="*60)
    print("检查现有模型")
    print("="*60)

    sam3_path = DRIVE_D_MODELS / "sam3" / "sam3.pt"
    da3_large_path = DRIVE_D_MODELS / "depth_anything_3" / "da3_large_1.1.pth"
    da3_mono_path = DRIVE_D_MODELS / "depth_anything_3" / "da3_mono_large_1.1.pth"

    existing = []
    missing = []

    if sam3_path.exists():
        size = sam3_path.stat().st_size / (1024**3)  # GB
        existing.append(f"SAM 3: {size:.2f} GB")
    else:
        missing.append("SAM 3")

    if da3_large_path.exists():
        size = da3_large_path.stat().st_size / (1024**3)
        existing.append(f"DA3-LARGE: {size:.2f} GB")
    else:
        missing.append("DA3-LARGE")

    if da3_mono_path.exists():
        size = da3_mono_path.stat().st_size / (1024**3)
        existing.append(f"DA3-MONO: {size:.2f} GB")
    else:
        missing.append("DA3-MONO")

    if existing:
        print("\n✓ 已下载的模型:")
        for item in existing:
            print(f"    - {item}")

    if missing:
        print("\n⚠️  未下载的模型:")
        for item in missing:
            print(f"    - {item}")

    return len(missing) == 0

def main():
    parser = argparse.ArgumentParser(description="下载 Phase 4 模型到 D 盘")
    parser.add_argument(
        "--model",
        choices=["sam3", "da3", "all"],
        default="all",
        help="选择要下载的模型 (默认: all)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检查已下载的模型"
    )

    args = parser.parse_args()

    print("="*60)
    print("Phase 4 模型下载助手")
    print("="*60)
    print(f"\n模型将下载到: {DRIVE_D_MODELS}")

    # 创建目录
    setup_dirs()

    if args.check:
        check_existing()
        return

    # 下载模型
    success = True

    if args.model in ["sam3", "all"]:
        if not download_sam3():
            success = False

    if args.model in ["da3", "all"]:
        if not download_da3():
            success = False

    # 最终检查
    print("\n" + "="*60)
    print("下载完成")
    print("="*60)
    check_existing()

    if success:
        print("\n✓ 所有模型准备就绪！")
        print("\n下一步:")
        print("  conda activate bishe")
        print("  python scripts/4-2_depth_anything_v3.py")
    else:
        print("\n⚠️  部分模型下载失败，请手动下载或重试")

if __name__ == "__main__":
    main()
