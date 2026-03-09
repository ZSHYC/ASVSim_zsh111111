# -*- coding: utf-8 -*-
import math
import matplotlib.pyplot as plt
# 导入刚才写好的地图转换工具
from coordinate_utils import MapConverter

class AStarPlanner:
    """
    A* (A-Star) 路径规划器类
    这是一种启发式搜索算法，能找到网格地图上的最短路径。
    """
    def __init__(self, resolution=10):
        # 分辨率：决定了多少个像素合并成一个“网格点”
        # resolution=10 意味着每 10x10 个像素算作一步。
        # 数值越小：路径越平滑，但计算越慢；数值越大：计算越快，但路径越粗糙。
        self.resolution = resolution

    class Node:
        """ 节点类：存储每个格子在算法中的状态 """
        def __init__(self, x, y, cost, parent_index):
            self.x = x  # 网格坐标 X
            self.y = y  # 网格坐标 Y
            self.cost = cost  # 从起点走到这里的代价 (G值)
            self.parent_index = parent_index # 父节点索引（用于回溯路径）

    def planning(self, start_u, start_v, goal_u, goal_v, map_img):
        """
        核心规划函数
        输入：起点和终点的像素坐标 (u, v)，以及地图图片
        输出：路径点的列表 rx, ry
        """
        # 1. 初始化
        # 将像素坐标转换为网格坐标 (除以分辨率)
        sx = round(start_u / self.resolution)
        sy = round(start_v / self.resolution)
        gx = round(goal_u / self.resolution)
        gy = round(goal_v / self.resolution)

        # 创建起点和终点节点
        start_node = self.Node(sx, sy, 0.0, -1)
        goal_node = self.Node(gx, gy, 0.0, -1)

        # Open List: 待探索的节点 (用字典存储，方便查找)
        # Closed List: 已经探索过的节点
        open_set = dict()
        closed_set = dict()
        
        # 生成唯一索引 ID
        start_id = self.calc_grid_index(start_node)
        open_set[start_id] = start_node

        print("A* 算法正在计算中，请稍候...")

        # 2. 主循环
        while True:
            # 如果待探索列表空了，说明无路可走
            if not open_set:
                print("搜索失败：无法找到到达终点的路径！(可能被障碍物包围)")
                return [], []

            # 从 Open Set 中找到 综合代价(F值 = G + H) 最小的节点
            c_id = min(open_set, key=lambda o: open_set[o].cost + self.calc_heuristic(goal_node, open_set[o]))
            current = open_set[c_id]

            # 3. 判断是否到达终点 (会有一定的误差容忍度)
            # 如果当前节点和终点的距离小于 1 个网格，就认为到了
            if math.hypot(current.x - goal_node.x, current.y - goal_node.y) <= 1.0:
                print("成功找到路径！")
                goal_node.parent_index = current.parent_index
                goal_node.cost = current.cost
                break

            # 将当前节点从 Open 移到 Closed
            del open_set[c_id]
            closed_set[c_id] = current

            # 4. 探索周围邻居 (8个方向)
            # 动作模型：[dx, dy, 代价]
            # 上下左右代价是1，斜着走代价是 1.414 (根号2)
            motions = [[1, 0, 1], [0, 1, 1], [-1, 0, 1], [0, -1, 1],
                       [1, 1, 1.414], [1, -1, 1.414], [-1, 1, 1.414], [-1, -1, 1.414]]

            for move in motions:
                node = self.Node(current.x + move[0],
                                 current.y + move[1],
                                 current.cost + move[2], c_id)
                
                n_id = self.calc_grid_index(node)

                # 如果已经在 Closed Set 里，跳过
                if n_id in closed_set:
                    continue

                # 如果是障碍物，跳过 (碰撞检测)
                if not self.verify_node(node, map_img):
                    continue

                # 如果不在 Open Set，加入
                if n_id not in open_set:
                    open_set[n_id] = node
                else:
                    # 如果已经在 Open Set，但现在这条路更短，更新它
                    if open_set[n_id].cost > node.cost:
                        open_set[n_id] = node

        # 5. 回溯路径
        rx, ry = self.calc_final_path(goal_node, closed_set)
        return rx, ry

    def calc_final_path(self, goal_node, closed_set):
        # 从终点倒推回起点
        rx, ry = [goal_node.x * self.resolution], [goal_node.y * self.resolution]
        parent_index = goal_node.parent_index
        while parent_index != -1:
            n = closed_set[parent_index]
            rx.append(n.x * self.resolution)
            ry.append(n.y * self.resolution)
            parent_index = n.parent_index
        return rx, ry

    def calc_heuristic(self, n1, n2):
        # 启发函数 (H值)：这里使用欧几里得距离
        # 也就是两点间的直线距离
        return math.hypot(n1.x - n2.x, n1.y - n2.y)

    def calc_grid_index(self, node):
        # 为每个节点生成唯一的 ID 字符串，防止混淆
        return f"{node.x}_{node.y}"

    def verify_node(self, node, map_img):
        # 碰撞检测函数
        # 还原回像素坐标
        px = int(node.x * self.resolution)
        py = int(node.y * self.resolution)

        # 检查边界
        height, width = map_img.shape
        if px < 0 or px >= width or py < 0 or py >= height:
            return False

        # 检查颜色：在 opencv 灰度图里，py是行(高), px是列(宽)
        # 如果像素值小于 128 (黑色)，说明是障碍
        if map_img[py, px] < 128:
            return False
            
        return True

# ================= 主程序入口 =================
def main():
    # 1. 加载地图
    print("--- 步骤1：加载地图 ---")
    try:
        map_cv = MapConverter('USV_Path_Planning\\local_map.png')
        print("地图加载成功！")
        print(f"地图尺寸: {map_cv.width} x {map_cv.height}")
    except Exception as e:
        print(e)
        return

    # 2. 交互式选择起点和终点
    print("\n--- 步骤2：选择路径 ---")
    print("请在弹出的窗口中：")
    print("  -> 点击第 1 下：选择 起点")
    print("  -> 点击第 2 下：选择 终点")
    print("(注意：请点在白色区域，点完后请耐心等待计算)")

    plt.figure("A* Path Planning (毕设演示)")
    plt.imshow(map_cv.grid_map, cmap='gray')
    plt.title("Click Start and Goal Points")
    
    # 获取用户鼠标点击 (n=2 表示取两个点)
    points = plt.ginput(n=2, timeout=0)
    
    if len(points) < 2:
        print("错误：你没有选取足够的点！")
        return

    # 提取点击的像素坐标
    start_u, start_v = points[0]
    goal_u, goal_v = points[1]

    # 3. 执行规划
    print(f"\n--- 步骤3：开始规划 ---")
    print(f"起点像素: ({int(start_u)}, {int(start_v)})")
    print(f"终点像素: ({int(goal_u)}, {int(goal_v)})")

    # 创建 A* 规划器，分辨率设为 10 像素
    planner = AStarPlanner(resolution=10)
    
    # 传入 map_cv.grid_map (这是处理过、膨胀过的地图)
    rx, ry = planner.planning(start_u, start_v, goal_u, goal_v, map_cv.grid_map)

    # 4. 可视化结果
    if rx:
        # A* 返回的路径是倒序的(从终点到起点)，反转一下方便看
        rx = rx[::-1]
        ry = ry[::-1]
        
        # 绘制结果
        plt.plot(rx, ry, "-r", linewidth=2, label="Calculated Path") # 红线
        plt.plot(start_u, start_v, "og", markersize=8, label="Start") # 绿色起点
        plt.plot(goal_u, goal_v, "xb", markersize=8, label="Goal")   # 蓝色终点
        plt.legend()
        plt.grid(True)
        plt.title("Path Planning Result")
        plt.draw() # 更新绘图
        
        print("\n--- 步骤4：输出关键路径点 (世界坐标) ---")
        print("这些坐标可以直接发给 ASVSim 让船去跑：")
        
        # 为了演示，我们每隔 5 个点打印一次，避免刷屏
        for i in range(0, len(rx), 5):
            pixel_u = rx[i]
            pixel_v = ry[i]
            # 调用转换器，把像素转回 UE5 坐标
            world_x, world_y = map_cv.pixel_to_world(pixel_u, pixel_v)
            print(f"路点 {i}: X={world_x:.2f}, Y={world_y:.2f}")
            
        print("\n演示完成！你可以关闭图片窗口了。")
        plt.show() # 保持窗口显示
    else:
        print("规划失败。请重试，确保起点和终点不要选在黑色区域！")

if __name__ == '__main__':
    main()