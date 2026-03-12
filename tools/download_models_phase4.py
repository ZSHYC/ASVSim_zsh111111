#!/usr/bin/env python3
"""
模型下载脚本 - Phase 4 环境部署
下载 SAM 3 和 Depth Anything 3 模型到 D 盘
"""

from huggingface_hub import hf_hub_download, list_repo_files
import os
import sys

# 设置缓存到 D 盘
os.environ['HF_HOME'] = r'D:\ASVSim_models\cache\hub'

DRIVE_D = r'D:\ASVSim_models'

def download_da3_large():
    """下载 DA3-LARGE"""
    print('='*60)
    print('Downloading Depth Anything 3 - LARGE')
    print('='*60)

    try:
        # 查看可用文件
        print('Checking available files...')
        files = list_repo_files('depth-anything/DA3-LARGE-1.1')
        print('Available:', files)

        # 下载模型
        print('\nDownloading da3_large_1.1.pth...')
        model_path = hf_hub_download(
            repo_id='depth-anything/DA3-LARGE-1.1',
            filename='da3_large_1.1.pth',
            local_dir=os.path.join(DRIVE_D, 'depth_anything_3'),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print('[OK] Downloaded to:', model_path)

        # 检查文件大小
        size = os.path.getsize(model_path) / (1024**3)
        print('[OK] File size: {:.2f} GB'.format(size))
        return True

    except Exception as e:
        print('[Error]', str(e))
        print()
        print('Manual download:')
        print('  1. Visit https://huggingface.co/depth-anything/DA3-LARGE-1.1')
        print('  2. Download da3_large_1.1.pth')
        print('  3. Place to:', os.path.join(DRIVE_D, 'depth_anything_3'))
        return False

def download_da3_mono():
    """下载 DA3-MONO"""
    print()
    print('='*60)
    print('Downloading Depth Anything 3 - MONO')
    print('='*60)

    try:
        print('Downloading da3_mono_large_1.1.pth...')
        model_path = hf_hub_download(
            repo_id='depth-anything/DA3MONO-LARGE',
            filename='da3_mono_large_1.1.pth',
            local_dir=os.path.join(DRIVE_D, 'depth_anything_3'),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print('[OK] Downloaded to:', model_path)

        size = os.path.getsize(model_path) / (1024**3)
        print('[OK] File size: {:.2f} GB'.format(size))
        return True

    except Exception as e:
        print('[Error]', str(e))
        return False

def download_sam3():
    """下载 SAM 3"""
    print()
    print('='*60)
    print('Downloading SAM 3')
    print('='*60)
    print('Note: SAM 3 requires Hugging Face login and permission!')
    print('Visit: https://huggingface.co/facebook/sam3')

    try:
        print('\nDownloading sam3.pt...')
        model_path = hf_hub_download(
            repo_id='facebook/sam3',
            filename='sam3.pt',
            local_dir=os.path.join(DRIVE_D, 'sam3'),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print('[OK] Downloaded to:', model_path)

        size = os.path.getsize(model_path) / (1024**3)
        print('[OK] File size: {:.2f} GB'.format(size))
        return True

    except Exception as e:
        print('[Error]', str(e))
        print()
        print('Manual download steps:')
        print('  1. Visit https://huggingface.co/facebook/sam3')
        print('  2. Click "Access repository" and request permission')
        print('  3. Login with: huggingface-cli login')
        print('  4. Download sam3.pt')
        print('  5. Place to:', os.path.join(DRIVE_D, 'sam3'))
        return False

def main():
    print('='*60)
    print('Phase 4 Model Download')
    print('='*60)
    print('Models will be downloaded to:', DRIVE_D)
    print()

    results = {
        'DA3-LARGE': download_da3_large(),
        'DA3-MONO': download_da3_mono(),
        'SAM3': download_sam3()
    }

    print()
    print('='*60)
    print('Download Summary')
    print('='*60)

    for model, success in results.items():
        status = '[OK]' if success else '[FAIL]'
        print(f'{status} {model}')

    print()
    if all(results.values()):
        print('All models downloaded successfully!')
        return 0
    else:
        print('Some models failed. Please download manually.')
        return 1

if __name__ == '__main__':
    sys.exit(main())
