# -*- coding: utf-8 -*-
import cosysairsim as airsim
# 【修改】必须导入这个 VesselControls 类型，否则无法发指令
from cosysairsim.types import VesselControls 

import time
import math
import matplotlib.pyplot as plt
from coordinate_utils import MapConverter
from step2_astar import AStarPlanner

# ================= 配置区域 =================
# 【修改】必须指定船的名字！
# 请在 UE5 的大纲(Outliner)里确认你的船叫什么。通常是 'Boat_Blueprint' 或 'Boat_Blueprint7'
# 如果填错了名字，船是不会动的！
VESSEL_NAME = 'Vessel1'

# ================= 辅助函数 =================
def to_euler_yaw(q):
    """ 将四元数 (x,y,z,w) 转换为 偏航角 (Yaw, 弧度) """
    siny_cosp = 2 * (q.w_val * q.z_val + q.x_val * q.y_val)
    cosy_cosp = 1 - 2 * (q.y_val * q.y_val + q.z_val * q.z_val)
    return math.atan2(siny_cosp, cosy_cosp)

def normalize_angle(angle):
    """ 将角度限制在 -pi 到 +pi 之间 """
    while angle > math.pi: angle -= 2.0 * math.pi
    while angle < -math.pi: angle += 2.0 * math.pi
    return angle

# ================= 主程序 =================
def main():
# 1. 连接 ASVSim
    print("正在连接 ASVSim 仿真器...")
    client = airsim.VesselClient() # <--- 改成 VesselClient
    client.confirmConnection()
    
    # 【修改】获取控制权时最好指定船名，虽然文档没强制，但更稳妥
    # 如果报错，可以改回 client.enableApiControl(True)
    try:
        client.enableApiControl(True, VESSEL_NAME)
    except:
        print("提示: enableApiControl 使用默认参数")
        client.enableApiControl(True)

    # 2. 重新跑一遍 A* 规划
    print("--- 阶段1: 路径规划 ---")
    # 注意：请确保你的 local_map.png 路径是正确的
    map_cv = MapConverter('USV_Path_Planning\\local_map.png') 
    
    print("请在弹出的窗口点击起点和终点...")
    plt.imshow(map_cv.grid_map, cmap='gray')
    points = plt.ginput(2)
    plt.close()
    
    if len(points) < 2: return
    
    start_u, start_v = points[0]
    goal_u, goal_v = points[1]
    
    planner = AStarPlanner(resolution=10)
    rx, ry = planner.planning(start_u, start_v, goal_u, goal_v, map_cv.grid_map)
    
    if not rx:
        print("路径规划失败，程序终止")
        return

    # 3. 将路径转换为世界坐标
    path_world = []
    for i in range(len(rx)-1, -1, -1):
        wx, wy = map_cv.pixel_to_world(rx[i], ry[i])
        path_world.append((wx, wy))
    
    print(f"路径生成完毕，共 {len(path_world)} 个路点。准备出发！")

    # 在 UE5 画线 (Debug)
    try:
        debug_points = [airsim.Vector3r(p[0], p[1], 100) for p in path_world] 
        client.simPlotLineList(debug_points, color_rgba=[1,0,0,1], thickness=50.0, is_persistent=True)
    except:
        print("警告：画线功能可能不可用，跳过")

    # 4. 开启控制循环
    print(f"--- 阶段2: 自动驾驶开始 (控制目标: {VESSEL_NAME}) ---")
    
    target_idx = 0
    drive_speed = 0.6 # 【建议】稍微加大一点推力，0.5有时候船跑得很慢
    
    try:
        while True:
            # === A. 感知 (Sensing) ===
            # 【建议】优先尝试 ASVSim 专用 API，如果失败回退到通用 API
            try:
                state = client.getVesselState(VESSEL_NAME)
                pos = state.kinematics_estimated.position
                ori = state.kinematics_estimated.orientation
            except:
                # 回退方案
                pose = client.simGetVehiclePose()
                pos = pose.position
                ori = pose.orientation
            
            current_x = pos.x_val
            current_y = pos.y_val
            current_yaw = to_euler_yaw(ori)
            
            # === B. 决策 (Decision) ===
            target_x, target_y = path_world[target_idx]
            dist_to_target = math.hypot(target_x - current_x, target_y - current_y)
            
            if dist_to_target < 8.0:
                print(f"到达路点 {target_idx}，切换下一个...")
                target_idx += 1
                if target_idx >= len(path_world):
                    print("=== 已到达终点！停车！===")
                    # 【修改】使用正确的停车指令
                    stop_ctrl = VesselControls(thrust=0.0, angle=0.5)
                    client.setVesselControls(VESSEL_NAME, stop_ctrl)
                    break
            
            # 计算航向误差
            target_angle = math.atan2(target_y - current_y, target_x - current_x)
            angle_error = normalize_angle(target_angle - current_yaw)
            
            # === C. 控制 (Control) ===
            # 【关键修改】方向修正
            # 如果 angle_error > 0 (目标在左)，我们需要左转 (angle < 0.5)
            # 所以应该是 0.5 - 误差，而不是 +
            k_p = 0.3
            steer_cmd = 0.5 - (angle_error * k_p)
            
            # 限制范围
            steer_cmd = max(0.0, min(1.0, steer_cmd))
            
            # === D. 执行 (Action) ===
            # 【修改】使用 VesselControls 对象发送指令
            controls = VesselControls(thrust=float(drive_speed), angle=float(steer_cmd))
            client.setVesselControls(VESSEL_NAME, controls)
            
            # 打印状态
            print(f"Idx:{target_idx} | 误差:{angle_error:.2f} | 舵角:{steer_cmd:.2f} | 距离:{dist_to_target:.1f}")
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        # 【修改】紧急停车也要用对格式
        stop_ctrl = VesselControls(thrust=0.0, angle=0.5)
        client.setVesselControls(VESSEL_NAME, stop_ctrl)
        print("手动停止。")

if __name__ == '__main__':
    main()