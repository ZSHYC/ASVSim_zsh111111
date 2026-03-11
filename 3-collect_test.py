"""
Phase 3 — 极简测试版（单帧调试）
================================

目的：测试最基础的采集功能，找出 IOLoop 和超时的根本原因

使用：
    python 3-collect_test.py
"""

import cosysairsim as airsim
import numpy as np
import time

print("=== 极简采集测试 ===\n")

# 连接
print("1. 连接 ASVSim...")
client = airsim.VesselClient()
client.confirmConnection()
print("   连接成功\n")

# 只采集一张 RGB（最简单的情况）
print("2. 尝试采集单张 RGB...")
print("   发送请求...")

start = time.time()
try:
    # 最简单的请求：只采一张 RGB
    responses = client.simGetImages([
        airsim.ImageRequest(0, airsim.ImageType.Scene, False, False),
    ])
    elapsed = time.time() - start

    print(f"   采集成功！耗时: {elapsed:.2f}s")
    print(f"   图像大小: {responses[0].width}x{responses[0].height}")
    print(f"   数据字节数: {len(responses[0].image_data_uint8)}")

except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

print("\n3. 测试完成")
