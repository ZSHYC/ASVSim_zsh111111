# Phase 6 路径规划层技术文档

**项目**: ASVSim 极地路径规划与 3D Gaussian Splatting 重建
**阶段**: Phase 6 - 路径规划层 (Path Planning Layer)
**版本**: v1.0
**日期**: 2026-03-14
**状态**: 待实施（可与重建并行开发）

---

## 目录

1. [概述](#1-概述)
2. [技术原理详解](#2-技术原理详解)
3. [算法选择与对比](#3-算法选择与对比)
4. [实现方案](#4-实现方案)
5. [极地环境建模](#5-极地环境建模)
6. [备用方案分析](#6-备用方案分析)
7. [项目规划与里程碑](#7-项目规划与里程碑)
8. [风险分析与对策](#8-风险分析与对策)
9. [与论文写作的衔接](#9-与论文写作的衔接)
10. [附录](#10-附录)

---

## 1. 概述

### 1.1 设计目标

Phase 6 路径规划层的核心任务是**在极地冰水环境中为自主水面航行器（ASV）规划安全、高效的航行路径**，并支持实时避碰和动态重规划。

**核心目标**:
1. **全局路径规划**: 从起点到终点的最优/次优路径（离线/准实时）
2. **局部避碰**: 实时检测障碍物并执行规避动作（在线，10Hz+）
3. **冰情适应**: 根据海冰分布、厚度动态调整路径
4. **无需感知层**: 可直接使用仿真真值冰情数据，绕过智能感知层
5. **论文可展示**: 提供可视化路径规划效果、对比实验、性能指标

### 1.2 技术选型

**为何选择 A* + D*Lite 混合架构?**

| 算法 | 适用场景 | 优势 | 劣势 | 推荐度 |
|------|----------|------|------|--------|
| **A*** | 全局规划 | 最优性强，实现简单 | 静态环境，重规划慢 | ⭐⭐⭐⭐ |
| **D* Lite** | 动态环境 | 高效重规划，局部更新 | 实现复杂 | ⭐⭐⭐⭐⭐ |
| **Theta*** | 任意角度路径 | 路径平滑，减少转向 | 计算量大 | ⭐⭐⭐ |
| **RRT*** | 高维空间 | 快速探索 | 非最优，随机性 | ⭐⭐ |
| **Dijkstra** | 简单场景 | 完备性强 | 无启发，慢 | ⭐⭐ |

**官方论文**:
- A*: "A Formal Basis for the Heuristic Determination of Minimum Cost Paths" (IEEE TSSC, 1968) - Hart et al.
- D* Lite: "D* Lite" (AAAI, 2002) - Koenig & Likhachev
- POLARIS: "Polar Operational Limit Assessment Risk Indexing System" (IMO Polar Code)

### 1.3 技术路线概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 6 路径规划架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  环境感知层 (输入)                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │  │ 冰情地图 │  │ 障碍物   │  │ 船体状态 │             │   │
│  │  │ (栅格)   │  │ 位置     │  │ 速度/航向│             │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘             │   │
│  └───────┼─────────────┼─────────────┼─────────────────────┘   │
│          │             │             │                         │
│          ▼             ▼             ▼                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                代价地图构建 (Cost Map)                   │   │
│  │                                                         │   │
│  │   Cost(x,y) = α·RIO_ice(x,y) + β·dist_to_obstacle      │   │
│  │              + γ·wave_height + δ·wind_factor            │   │
│  │                                                         │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                       │
│         ┌──────────────┼──────────────┐                       │
│         ▼              ▼              ▼                       │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                  │
│  │ 全局层   │   │ 局部层   │   │ 执行层   │                  │
│  │ A*规划   │   │ D* Lite  │   │ 轨迹跟踪 │                  │
│  │          │   │ 动态避碰 │   │ PID控制  │                  │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘                  │
│       │              │              │                         │
│       └──────────────┼──────────────┘                         │
│                      ▼                                       │
│              ┌──────────┐                                     │
│              │ 平滑路径 │                                     │
│              │ B样条   │                                     │
│              └────┬─────┘                                     │
│                   ▼                                           │
│              ┌──────────┐                                     │
│              │ ASV执行  │                                     │
│              │ (仿真)   │                                     │
│              └──────────┘                                     │
│                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 技术原理详解

### 2.1 A*算法原理

**核心思想**: 结合Dijkstra算法的完备性和贪心搜索的效率，通过启发函数引导搜索方向。

**代价函数**:
```
f(n) = g(n) + h(n)

其中:
- g(n): 从起点到节点n的实际代价
- h(n): 从节点n到终点的启发估计（heuristic）
- f(n): 经过节点n的总估计代价
```

**启发函数选择**:

| 启发函数 | 公式 | 特性 | 适用 |
|----------|------|------|------|
| Manhattan | \|x₁-x₂\| + \|y₁-y₂\| | 可容许但非紧 | 4连通栅格 |
| **Euclidean** | √((x₁-x₂)²+(y₁-y₂)²) | 紧但计算稍慢 | **推荐** |
| Diagonal | max(\|Δx\|,\|Δy\|) + (√2-1)·min(\|Δx\|,\|Δy\|) | 8连通最优 | 8连通栅格 |

**算法流程**:

```python
def astar(grid, start, goal):
    open_set = PriorityQueue()  # 按f值排序
    open_set.put((0, start))
    came_from = {}              # 记录路径
    g_score = {start: 0}        # 实际代价
    f_score = {start: heuristic(start, goal)}

    while not open_set.empty():
        current = open_set.get()[1]

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in get_neighbors(current):
            tentative_g = g_score[current] + cost(current, neighbor)

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                open_set.put((f_score[neighbor], neighbor))

    return None  # 无路径
```

**关键性质**:
- **可容许性 (Admissible)**: 如果 h(n) ≤ h*(n)（真实代价），则A*保证找到最优解
- **一致性 (Consistent)**: 如果 h(n) ≤ cost(n→n') + h(n')，则保证不重复扩展节点
- **完备性**: 如果存在路径，A*一定能找到

### 2.2 D* Lite算法原理

**核心思想**: 针对动态环境优化的增量式路径规划算法。当环境变化时，只更新受影响节点的代价，而非重新计算整个路径。

**与A*的关键区别**:

| 特性 | A* | D* Lite |
|------|-----|---------|
| 重规划 | 重新搜索整个图 | 只更新变化区域 |
| 搜索方向 | 从起点向目标 | 从目标向起点（反向搜索） |
| 数据结构 | g值+父指针 | 双值估计（rhs, g） |
| 适用场景 | 静态/变化小 | 动态/频繁变化 |

**核心概念 - 双值估计**:
```
对于每个节点s:
- g(s): 从起点到s的实际代价（类似A*的g）
- rhs(s): one-step lookahead值：
  rhs(s) = min_{s'∈pred(s)}(g(s') + cost(s', s))

当g(s) = rhs(s)时，称s为"局部一致"
当g(s) < rhs(s)时，称s为"过一致"（需要增加代价）
当g(s) > rhs(s)时，称s为"欠一致"（需要降低代价）
```

**优先队列键值**:
```
key(s) = [min(g(s), rhs(s)) + h(s_start, s); min(g(s), rhs(s))]

两个元素比较时，先比较第一个分量，再比较第二个。
```

**算法流程**:

```python
def dstar_lite(grid, start, goal):
    # 初始化
    rhs[goal] = 0
    open_set.put((calculate_key(goal), goal))

    while True:
        # 计算最短路径
        compute_shortest_path()

        if start not in path:
            return None  # 无法到达

        # 执行路径直到检测到环境变化
        while start != goal and not environment_changed():
            start = get_next_step(start)
            execute_move(start)

        if start == goal:
            return  # 到达目标

        # 处理环境变化
        for changed_edge in detect_changes():
            update_edge_cost(changed_edge)
            update_vertex(changed_edge.u)
            update_vertex(changed_edge.v)

def compute_shortest_path():
    while (open_set.peek() < calculate_key(start) or
           rhs[start] != g[start]):
        k_old = open_set.peek()
        u = open_set.pop()

        if k_old < calculate_key(u):  # 需要重新插入
            open_set.put((calculate_key(u), u))
        elif g[u] > rhs[u]:  # 欠一致
            g[u] = rhs[u]
            for s in predecessors(u):
                update_vertex(s)
        else:  # 过一致
            g[u] = float('inf')
            update_vertex(u)
            for s in predecessors(u):
                update_vertex(s)

def update_vertex(s):
    if s != goal:
        rhs[s] = min([g[s'] + cost(s', s) for s' in successors(s)])

    if s in open_set:
        open_set.remove(s)

    if g[s] != rhs[s]:
        open_set.put((calculate_key(s), s))
```

**重规划效率**:
- A*重规划复杂度: O(b^d)（与首次搜索相同）
- D* Lite重规划复杂度: O(k log n)（k为变化节点数）
- **实际加速**: 10x-100x（取决于变化范围）

### 2.3 多目标优化

**目标**: 同时优化多个冲突目标（安全性 vs 效率 vs 经济性）

**Pareto最优**: 一组解，无法在不损害其他目标的情况下改进任一目标。

**加权和方法**（最简单）:
```
minimize: Σᵢ wᵢ·fᵢ(x)
subject to: Σᵢ wᵢ = 1

例如: Cost = 0.4·Risk + 0.3·Time + 0.3·Fuel
```

**NSGA-II/III**（多目标进化算法）:
- 生成Pareto前沿（一组非支配解）
- 决策者可从中选择最符合偏好的解
- 适合离线规划，计算量大

### 2.4 POLARIS风险评估系统

**官方标准**: IMO《极地水域航行船舶国际规则》(Polar Code)

**RIO (Risk Index Outcome) 计算**:

```
RIO = f(冰浓度, 冰厚度, 船型, 操作类型)

冰浓度等级:
- Open Water: 0%
- Very Open Ice: 1-10%
- Open Ice: 10-30%
- Close Ice: 30-50%
- Very Close Ice: 50-70%
- Consolidated Ice: 70-100%

RIO阈值:
- RIO < -10: 不可航行（需破冰船）
- -10 < RIO < 0: 高风险（限航速4节）
- 0 < RIO < 30: 中等风险（限航速）
- RIO ≥ 30: 正常航行（全速22节）
```

**应用到代价地图**:
```python
def calculate_cost(ice_concentration, ice_thickness, ship_class):
    """
    基于POLARIS计算网格航行代价
    """
    rio = compute_rio(ice_concentration, ice_thickness, ship_class)

    if rio < -10:
        return float('inf')  # 不可航行
    elif rio < 0:
        return 100 + (10 - abs(rio)) * 10  # 高风险区域
    elif rio < 30:
        return 10 + (30 - rio) * 3  # 中等风险
    else:
        return 1  # 正常水域
```

---

## 3. 算法选择与对比

### 3.1 详细算法对比

**全局规划算法**:

| 算法 | 最优性 | 时间复杂度 | 空间复杂度 | 动态支持 | 实现难度 | 推荐场景 |
|------|--------|-----------|-----------|----------|----------|----------|
| **Dijkstra** | ✓ | O(V²)或O(E+VlogV) | O(V) | ✗ | 低 | 教学、简单场景 |
| **A*** | ✓ | O(b^d) | O(b^d) | ✗ | 低 | **全局规划首选** |
| **Weighted A*** | ε-最优 | O(b^εd) | O(b^εd) | ✗ | 低 | 快速近似解 |
| **Anytime A*** | 渐进最优 | 可变 | O(b^d) | ✗ | 中 | 时间受限场景 |
| **LPA*** | ✓ | O(E) | O(V) | ✓ | 高 | 静态+少量变化 |
| **D* Lite** | ✓ | O(E) | O(V) | ✓✓✓ | 高 | **动态规划首选** |
| **RRT*** | 渐进最优 | O(n log n) | O(n) | ✓ | 中 | 高维空间 |

**局部避碰算法**:

| 算法 | 反应速度 | 最优性 | 适用场景 |
|------|----------|--------|----------|
| **VFH+** | 快 | 局部最优 | 已知地图避障 |
| **DWA** | 快 | 局部最优 | 机器人导航 |
| **APF** | 快 | 可能局部最优 | 简单避障 |
| **VO (Velocity Obstacle)** | 快 | 局部最优 | 动态障碍物 |
| **ORCA** | 快 | 局部最优 | 多智能体避碰 |
| **D* Lite局部** | 中 | 全局最优 | **推荐** |

### 3.2 本研究推荐架构

**双层混合架构**:

```
┌─────────────────────────────────────┐
│         全局规划层 (1-10Hz)          │
│  ┌─────────────────────────────┐   │
│  │ A* (或 Weighted A* 0.8)    │   │
│  │ - 粗粒度栅格 (10m×10m)      │   │
│  │ - 静态冰情地图              │   │
│  │ - 生成全局参考路径          │   │
│  └─────────────────────────────┘   │
└─────────────────┬───────────────────┘
                  │ 参考路径
┌─────────────────▼───────────────────┐
│         局部规划层 (10-50Hz)         │
│  ┌─────────────────────────────┐   │
│  │ D* Lite                    │   │
│  │ - 细粒度栅格 (1m×1m)        │   │
│  │ - 实时传感器数据            │   │
│  │ - 动态重规划                │   │
│  │ - 避碰窗口: 50m×50m         │   │
│  └─────────────────────────────┘   │
└─────────────────┬───────────────────┘
                  │ 控制指令
┌─────────────────▼───────────────────┐
│           执行层 (50-100Hz)          │
│  PID控制 → 推力/舵角 → ASV仿真       │
└─────────────────────────────────────┘
```

---

## 4. 实现方案

### 4.1 完整实现代码

#### 4.1.1 A*算法实现（Python + NumPy）

```python
"""
A*路径规划实现
支持8连通栅格、自定义代价函数、平滑处理
"""
import numpy as np
import heapq
from typing import List, Tuple, Dict, Optional
import math

class Node:
    """搜索节点"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.g = float('inf')  # 实际代价
        self.h = 0.0           # 启发值
        self.f = float('inf')  # 总估计
        self.parent = None

    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

class AStarPlanner:
    """A*路径规划器"""

    def __init__(self, cost_map: np.ndarray, resolution: float = 1.0):
        """
        Args:
            cost_map: 2D代价地图，值越大表示通过代价越高
            resolution: 栅格分辨率（米/像素）
        """
        self.cost_map = cost_map
        self.resolution = resolution
        self.height, self.width = cost_map.shape

        # 8方向移动: [dx, dy, cost]
        self.motions = [
            [1, 0, 1.0],    # 右
            [0, 1, 1.0],    # 下
            [-1, 0, 1.0],   # 左
            [0, -1, 1.0],   # 上
            [1, 1, math.sqrt(2)],   # 右下
            [-1, 1, math.sqrt(2)],  # 左下
            [-1, -1, math.sqrt(2)], # 左上
            [1, -1, math.sqrt(2)]   # 右上
        ]

    def heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """欧几里得距离启发"""
        return math.sqrt((x1-x2)**2 + (y1-y2)**2) * self.resolution

    def is_valid(self, x: int, y: int) -> bool:
        """检查坐标是否有效"""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_collision(self, x: int, y: int) -> bool:
        """检查是否碰撞（代价无穷大）"""
        if not self.is_valid(x, y):
            return True
        return self.cost_map[y, x] == float('inf')

    def plan(self, start: Tuple[int, int], goal: Tuple[int, int],
             max_iterations: int = 100000) -> Optional[List[Tuple[int, int]]]:
        """
        执行A*规划

        Returns:
            路径点列表 [(x1,y1), (x2,y2), ...]，失败返回None
        """
        start_node = Node(start[0], start[1])
        goal_node = Node(goal[0], goal[1])

        # 初始化起点
        start_node.g = 0
        start_node.h = self.heuristic(start[0], start[1], goal[0], goal[1])
        start_node.f = start_node.g + start_node.h

        # 开放列表（优先队列）和关闭列表
        open_list = []
        heapq.heappush(open_list, (start_node.f, start_node))
        open_set = {start}  # 用于O(1)查找
        closed_set = set()

        iterations = 0
        while open_list and iterations < max_iterations:
            iterations += 1

            # 取出f值最小的节点
            current = heapq.heappop(open_list)[1]
            open_set.remove((current.x, current.y))
            closed_set.add((current.x, current.y))

            # 到达目标
            if (current.x, current.y) == (goal[0], goal[1]):
                return self.reconstruct_path(current)

            # 扩展邻居
            for dx, dy, move_cost in self.motions:
                nx, ny = current.x + dx, current.y + dy

                if not self.is_valid(nx, ny):
                    continue
                if (nx, ny) in closed_set:
                    continue
                if self.is_collision(nx, ny):
                    continue

                # 计算新代价
                tentative_g = current.g + move_cost * self.resolution * \
                             (1 + self.cost_map[ny, nx])

                neighbor = Node(nx, ny)
                if (nx, ny) not in open_set or tentative_g < neighbor.g:
                    neighbor.g = tentative_g
                    neighbor.h = self.heuristic(nx, ny, goal[0], goal[1])
                    neighbor.f = neighbor.g + neighbor.h
                    neighbor.parent = current

                    if (nx, ny) not in open_set:
                        heapq.heappush(open_list, (neighbor.f, neighbor))
                        open_set.add((nx, ny))

        return None  # 未找到路径

    def reconstruct_path(self, node: Node) -> List[Tuple[int, int]]:
        """从目标节点回溯路径"""
        path = []
        current = node
        while current:
            path.append((current.x, current.y))
            current = current.parent
        return path[::-1]  # 反转得到起点到终点

    def smooth_path(self, path: List[Tuple[int, int]],
                   weight_data: float = 0.5,
                   weight_smooth: float = 0.3,
                   tolerance: float = 0.00001) -> List[Tuple[float, float]]:
        """
        梯度下降法路径平滑

        Args:
            path: 原始栅格路径
            weight_data: 保持原始位置的权重
            weight_smooth: 平滑权重
            tolerance: 收敛阈值

        Returns:
            平滑后的连续路径
        """
        if len(path) < 3:
            return [(float(x), float(y)) for x, y in path]

        # 转换为float
        new_path = [[float(x), float(y)] for x, y in path]

        change = tolerance
        while change >= tolerance:
            change = 0.0
            for i in range(1, len(path) - 1):
                for j in range(2):
                    aux = new_path[i][j]
                    # 梯度下降更新
                    new_path[i][j] += weight_data * (path[i][j] - new_path[i][j])
                    new_path[i][j] += weight_smooth * (new_path[i-1][j] + new_path[i+1][j] - 2*new_path[i][j])
                    change += abs(aux - new_path[i][j])

        return [(p[0], p[1]) for p in new_path]


# 使用示例
if __name__ == '__main__':
    # 创建简单代价地图
    cost_map = np.ones((100, 100), dtype=np.float32)
    cost_map[40:60, 20:80] = 10.0  # 高代价区域（薄冰）
    cost_map[45:55, 45:55] = float('inf')  # 障碍物（厚冰）

    planner = AStarPlanner(cost_map, resolution=1.0)

    start = (10, 50)
    goal = (90, 50)

    path = planner.plan(start, goal)
    if path:
        print(f"找到路径，共{len(path)}个节点")
        smooth = planner.smooth_path(path)
        print(f"平滑后路径长度: {len(smooth)}")
    else:
        print("未找到路径")
```

#### 4.1.2 D* Lite算法实现

```python
"""
D* Lite路径规划实现
支持动态环境更新、高效重规划
"""
import numpy as np
import heapq
from typing import List, Tuple, Dict, Optional, Set
import math

class DStarLiteNode:
    """D* Lite节点"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.g = float('inf')   # 实际代价
        self.rhs = float('inf') # one-step lookahead
        self.k = [float('inf'), float('inf')]  # 优先级键值

    def __lt__(self, other):
        return self.k < other.k

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

class DStarLitePlanner:
    """D* Lite路径规划器"""

    def __init__(self, cost_map: np.ndarray, resolution: float = 1.0):
        self.cost_map = cost_map.copy()
        self.resolution = resolution
        self.height, self.width = cost_map.shape

        self.start = None
        self.goal = None
        self.km = 0  # 累计偏移量

        self.nodes = {}
        self.open_set = set()
        self.queue = []

        # 8方向
        self.motions = [
            [1, 0, 1.0], [0, 1, 1.0], [-1, 0, 1.0], [0, -1, 1.0],
            [1, 1, math.sqrt(2)], [-1, 1, math.sqrt(2)],
            [-1, -1, math.sqrt(2)], [1, -1, math.sqrt(2)]
        ]

    def get_node(self, x: int, y: int) -> DStarLiteNode:
        """获取或创建节点"""
        key = (x, y)
        if key not in self.nodes:
            self.nodes[key] = DStarLiteNode(x, y)
        return self.nodes[key]

    def heuristic(self, s: DStarLiteNode, t: DStarLiteNode) -> float:
        """启发函数（欧几里得）"""
        return math.sqrt((s.x-t.x)**2 + (s.y-t.y)**2) * self.resolution

    def calculate_key(self, s: DStarLiteNode) -> List[float]:
        """计算节点键值"""
        k1 = min(s.g, s.rhs) + self.heuristic(s, self.start) + self.km
        k2 = min(s.g, s.rhs)
        return [k1, k2]

    def is_valid(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_cost(self, s: DStarLiteNode, t: DStarLiteNode) -> float:
        """获取从s到t的移动代价"""
        if not self.is_valid(t.x, t.y):
            return float('inf')
        if self.cost_map[t.y, t.x] == float('inf'):
            return float('inf')

        # 对角移动检查
        dx, dy = abs(t.x - s.x), abs(t.y - s.y)
        if dx == 1 and dy == 1:
            # 检查是否穿过障碍物角落
            if (self.cost_map[s.y, t.x] == float('inf') or
                self.cost_map[t.y, s.x] == float('inf')):
                return float('inf')
            return math.sqrt(2) * self.resolution * (1 + self.cost_map[t.y, t.x])

        return self.resolution * (1 + self.cost_map[t.y, t.x])

    def update_vertex(self, u: DStarLiteNode):
        """更新节点状态"""
        if u != self.goal:
            # rhs(u) = min(cost(u,s) + g(s)) for s in successors
            min_rhs = float('inf')
            for dx, dy, _ in self.motions:
                nx, ny = u.x + dx, u.y + dy
                if self.is_valid(nx, ny):
                    s = self.get_node(nx, ny)
                    cost = self.get_cost(u, s)
                    if cost < float('inf'):
                        min_rhs = min(min_rhs, cost + s.g)
            u.rhs = min_rhs

        # 从队列中移除（如果存在）
        if (u.x, u.y) in self.open_set:
            self.open_set.remove((u.x, u.y))
            # 重建队列（简单实现）
            new_queue = []
            for k, node in self.queue:
                if node != u:
                    heapq.heappush(new_queue, (node.k, node))
            self.queue = new_queue

        # 如果不一致，加入队列
        if u.g != u.rhs:
            u.k = self.calculate_key(u)
            heapq.heappush(self.queue, (u.k, u))
            self.open_set.add((u.x, u.y))

    def compute_shortest_path(self):
        """计算最短路径"""
        while self.queue:
            # 检查停止条件
            if not self.start:
                return

            top_k = self.queue[0][0]
            start_k = self.calculate_key(self.start)

            if top_k > start_k or self.start.rhs != self.start.g:
                # 继续处理
                k_old, u = heapq.heappop(self.queue)
                self.open_set.remove((u.x, u.y))

                k_new = self.calculate_key(u)

                if k_old < k_new:
                    # 过期键值，重新插入
                    u.k = k_new
                    heapq.heappush(self.queue, (u.k, u))
                    self.open_set.add((u.x, u.y))
                elif u.g > u.rhs:
                    # 过一致 -> 一致
                    u.g = u.rhs
                    # 更新前驱
                    for dx, dy, _ in self.motions:
                        nx, ny = u.x + dx, u.y + dy
                        if self.is_valid(nx, ny):
                            s = self.get_node(nx, ny)
                            self.update_vertex(s)
                else:
                    # 欠一致 -> 过一致
                    u.g = float('inf')
                    self.update_vertex(u)
                    for dx, dy, _ in self.motions:
                        nx, ny = u.x + dx, u.y + dy
                        if self.is_valid(nx, ny):
                            s = self.get_node(nx, ny)
                            self.update_vertex(s)
            else:
                break

    def initialize(self, start: Tuple[int, int], goal: Tuple[int, int]):
        """初始化规划器"""
        self.start = self.get_node(start[0], start[1])
        self.goal = self.get_node(goal[0], goal[1])
        self.km = 0

        # 初始化队列
        self.queue = []
        self.open_set = set()

        # 目标rhs=0
        self.goal.rhs = 0
        self.goal.k = self.calculate_key(self.goal)
        heapq.heappush(self.queue, (self.goal.k, self.goal))
        self.open_set.add((goal[0], goal[1]))

        # 计算初始路径
        self.compute_shortest_path()

    def get_next_step(self) -> Optional[Tuple[int, int]]:
        """获取下一步移动"""
        if self.start.g == float('inf'):
            return None  # 无路径

        if self.start == self.goal:
            return None  # 已到达

        # 选择g值最小的邻居
        min_g = float('inf')
        next_node = None

        for dx, dy, _ in self.motions:
            nx, ny = self.start.x + dx, self.start.y + dy
            if self.is_valid(nx, ny):
                n = self.get_node(nx, ny)
                cost = self.get_cost(self.start, n)
                if cost < float('inf'):
                    total = cost + n.g
                    if total < min_g:
                        min_g = total
                        next_node = (nx, ny)

        return next_node

    def move_to(self, new_pos: Tuple[int, int]):
        """移动到新位置"""
        old_start = self.start
        self.start = self.get_node(new_pos[0], new_pos[1])

        # 更新km
        self.km += self.heuristic(old_start, self.start)

    def update_costs(self, changes: List[Tuple[int, int, float]]):
        """
        更新代价地图

        Args:
            changes: [(x1, y1, new_cost), (x2, y2, new_cost), ...]
        """
        for x, y, new_cost in changes:
            if not self.is_valid(x, y):
                continue

            old_cost = self.cost_map[y, x]
            self.cost_map[y, x] = new_cost

            # 影响该节点及其邻居
            node = self.get_node(x, y)
            self.update_vertex(node)

            for dx, dy, _ in self.motions:
                nx, ny = x + dx, y + dy
                if self.is_valid(nx, ny):
                    neighbor = self.get_node(nx, ny)
                    self.update_vertex(neighbor)

        # 重新规划
        self.compute_shortest_path()

    def get_path(self) -> List[Tuple[int, int]]:
        """获取当前最优路径"""
        path = []
        current = self.start

        while current and current != self.goal:
            path.append((current.x, current.y))

            # 找最优邻居
            min_g = float('inf')
            next_node = None

            for dx, dy, _ in self.motions:
                nx, ny = current.x + dx, current.y + dy
                if self.is_valid(nx, ny):
                    n = self.get_node(nx, ny)
                    cost = self.get_cost(current, n)
                    if cost < float('inf') and n.g < min_g:
                        min_g = n.g
                        next_node = n

            if next_node is None or next_node == current:
                break
            current = next_node

        if current == self.goal:
            path.append((self.goal.x, self.goal.y))

        return path


# 使用示例（动态环境）
if __name__ == '__main__':
    # 创建代价地图
    cost_map = np.ones((50, 50), dtype=np.float32)
    cost_map[20:30, 10:40] = 5.0  # 冰区

    planner = DStarLitePlanner(cost_map, resolution=10.0)
    planner.initialize((5, 25), (45, 25))

    print("初始路径:", planner.get_path())

    # 模拟环境变化（出现新障碍物）
    changes = [(25, 25, float('inf')), (26, 25, float('inf'))]
    planner.update_costs(changes)

    print("重规划后路径:", planner.get_path())
```

#### 4.1.3 极地环境代价地图构建

```python
"""
极地环境代价地图构建
整合冰情数据、POLARIS风险评估、船体约束
"""
import numpy as np
from typing import Dict, List, Tuple
import cv2

class PolarCostMapBuilder:
    """极地代价地图构建器"""

    def __init__(self, map_bounds: Tuple[float, float, float, float],
                 resolution: float = 10.0):
        """
        Args:
            map_bounds: (xmin, xmax, ymin, ymax) 地图范围（米）
            resolution: 栅格分辨率（米/格）
        """
        self.resolution = resolution
        self.bounds = map_bounds

        # 计算栅格尺寸
        self.width = int((map_bounds[1] - map_bounds[0]) / resolution)
        self.height = int((map_bounds[3] - map_bounds[2]) / resolution)

        # 初始化代价地图
        self.cost_map = np.ones((self.height, self.width), dtype=np.float32)
        self.ice_map = np.zeros((self.height, self.width, 3), dtype=np.float32)
        # ice_map通道: [浓度, 厚度, 风险指数]

    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """世界坐标转栅格坐标"""
        gx = int((x - self.bounds[0]) / self.resolution)
        gy = int((y - self.bounds[2]) / self.resolution)
        return gx, gy

    def grid_to_world(self, gx: int, gy: int) -> Tuple[float, float]:
        """栅格坐标转世界坐标"""
        x = self.bounds[0] + (gx + 0.5) * self.resolution
        y = self.bounds[2] + (gy + 0.5) * self.resolution
        return x, y

    def add_ice_data(self, ice_data: List[Dict]):
        """
        添加海冰数据

        Args:
            ice_data: [{'x': float, 'y': float, 'concentration': 0-1,
                       'thickness': float, 'type': str}, ...]
        """
        for ice in ice_data:
            gx, gy = self.world_to_grid(ice['x'], ice['y'])
            if 0 <= gx < self.width and 0 <= gy < self.height:
                self.ice_map[gy, gx, 0] = ice['concentration']
                self.ice_map[gy, gx, 1] = ice['thickness']

    def calculate_rio(self, concentration: float, thickness: float,
                     ship_ice_class: str = 'PC7') -> float:
        """
        计算Risk Index Outcome (POLARIS)

        Args:
            concentration: 冰浓度 0-1
            thickness: 冰厚度（米）
            ship_ice_class: 船舶冰级 (PC1-PC7)

        Returns:
            RIO值，<=-10表示不可航行
        """
        # 简化RIO计算（基于POLARIS表）
        # 实际应用应查完整POLARIS表格

        ice_level = concentration * thickness

        # PC7级船限制（最低级别）
        limits = {
            'PC1': 10.0, 'PC2': 8.0, 'PC3': 6.0,
            'PC4': 4.0, 'PC5': 3.0, 'PC6': 2.0, 'PC7': 1.0
        }
        limit = limits.get(ship_ice_class, 1.0)

        if ice_level > limit * 1.5:
            return -20  # 不可航行
        elif ice_level > limit:
            return -5   # 高风险
        elif ice_level > limit * 0.5:
            return 10   # 中等风险
        else:
            return 30   # 低风险

    def build_cost_map(self, ship_ice_class: str = 'PC7',
                      safety_margin: float = 50.0) -> np.ndarray:
        """
        构建完整代价地图

        Args:
            ship_ice_class: 船舶冰级
            safety_margin: 安全距离（米）

        Returns:
            代价地图 numpy数组
        """
        h, w = self.height, self.width

        for gy in range(h):
            for gx in range(w):
                conc = self.ice_map[gy, gx, 0]
                thick = self.ice_map[gy, gx, 1]

                if conc == 0:
                    # 开水域
                    self.cost_map[gy, gx] = 1.0
                else:
                    # 计算RIO
                    rio = self.calculate_rio(conc, thick, ship_ice_class)

                    # RIO转代价
                    if rio <= -10:
                        self.cost_map[gy, gx] = float('inf')
                    elif rio < 0:
                        self.cost_map[gy, gx] = 50 + abs(rio) * 5
                    elif rio < 30:
                        self.cost_map[gy, gx] = 10 + (30 - rio) * 0.5
                    else:
                        self.cost_map[gy, gx] = 1.0 + (100 - rio) * 0.05

        # 应用安全距离（膨胀障碍物）
        margin_cells = int(safety_margin / self.resolution)
        if margin_cells > 0:
            obstacle_mask = (self.cost_map == float('inf')).astype(np.uint8)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                              (margin_cells*2+1, margin_cells*2+1))
            dilated = cv2.dilate(obstacle_mask, kernel, iterations=1)

            # 膨胀区域增加代价
            self.cost_map[dilated > 0] = np.maximum(
                self.cost_map[dilated > 0],
                20.0  # 接近障碍物的高代价
            )

        return self.cost_map

    def add_dynamic_obstacles(self, obstacles: List[Dict]):
        """
        添加动态障碍物（其他船只、移动冰山）

        Args:
            obstacles: [{'x': float, 'y': float, 'radius': float}, ...]
        """
        for obs in obstacles:
            gx, gy = self.world_to_grid(obs['x'], obs['y'])
            radius_cells = int(obs['radius'] / self.resolution)

            # 圆形区域设为无穷大（障碍物）
            for dy in range(-radius_cells, radius_cells+1):
                for dx in range(-radius_cells, radius_cells+1):
                    if dx*dx + dy*dy <= radius_cells*radius_cells:
                        nx, ny = gx + dx, gy + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            self.cost_map[ny, nx] = float('inf')


# 使用示例
if __name__ == '__main__':
    # 创建地图 (1000m x 1000m)
    builder = PolarCostMapBuilder((-500, 500, -500, 500), resolution=10.0)

    # 添加冰情数据
    ice_data = []
    for i in range(50):
        for j in range(50):
            x = -250 + i * 10
            y = -250 + j * 10
            conc = 0.3 + 0.4 * np.random.random()  # 30-70%浓度
            thick = 0.2 + 0.5 * np.random.random()  # 0.2-0.7m厚度
            ice_data.append({'x': x, 'y': y, 'concentration': conc, 'thickness': thick})

    builder.add_ice_data(ice_data)

    # 构建代价地图
    cost_map = builder.build_cost_map(ship_ice_class='PC7', safety_margin=30.0)

    print(f"代价地图大小: {cost_map.shape}")
    print(f"不可航行区域: {np.sum(cost_map == float('inf'))} 格")
    print(f"平均代价: {np.mean(cost_map[cost_map < float('inf')]):.2f}")
```

### 4.2 ASVSim集成方案

```python
"""
ASVSim路径规划集成
将规划器与ASVSim仿真环境对接
"""
import cosysairsim as airsim
import numpy as np
import time

class ASVPathPlanner:
    """ASV路径规划控制器"""

    def __init__(self, client: airsim.VesselClient):
        self.client = client
        self.planner = None
        self.current_path = []
        self.path_index = 0

        # ASV状态
        self.position = np.array([0.0, 0.0])
        self.heading = 0.0  # 航向角（弧度）
        self.velocity = 0.0

        # 控制参数
        self.lookahead_distance = 20.0  # 前瞻距离（米）
        self.max_speed = 5.0  # 最大速度（m/s）
        self.min_obstacle_dist = 30.0  # 最小避障距离

    def update_state(self):
        """更新ASV状态"""
        pose = self.client.simGetVehiclePose('Vessel1')
        self.position = np.array([pose.position.x_val, pose.position.y_val])

        # 从四元数提取航向
        q = pose.orientation
        self.heading = np.arctan2(2*(q.w_val*q.z_val + q.x_val*q.y_val),
                                  1 - 2*(q.y_val**2 + q.z_val**2))

        # 获取速度
        # self.velocity = ...

    def plan_global_path(self, goal: Tuple[float, float]):
        """
        规划全局路径

        Args:
            goal: 目标位置 (x, y)
        """
        # 从仿真获取环境信息构建代价地图
        # 或使用预构建的地图
        cost_map = self.build_cost_map_from_simulation()

        # 创建规划器
        self.planner = AStarPlanner(cost_map, resolution=10.0)

        # 当前位置转栅格
        start_gx = int(self.position[0] / 10)
        start_gy = int(self.position[1] / 10)
        goal_gx = int(goal[0] / 10)
        goal_gy = int(goal[1] / 10)

        # 规划路径
        path = self.planner.plan((start_gx, start_gy), (goal_gx, goal_gy))

        if path:
            # 平滑路径
            smooth_path = self.planner.smooth_path(path)
            # 转回世界坐标
            self.current_path = [
                (p[0] * 10 + 5, p[1] * 10 + 5) for p in smooth_path
            ]
            self.path_index = 0
            return True
        else:
            print("全局规划失败")
            return False

    def compute_control(self) -> Tuple[float, float]:
        """
        计算控制指令

        Returns:
            (thrust, angle) 推力和舵角
        """
        if not self.current_path or self.path_index >= len(self.current_path):
            return 0.0, 0.5  # 停止

        # 寻找前瞻点
        lookahead_idx = self.path_index
        while lookahead_idx < len(self.current_path):
            wp = np.array(self.current_path[lookahead_idx])
            dist = np.linalg.norm(wp - self.position)
            if dist >= self.lookahead_distance:
                break
            lookahead_idx += 1

        if lookahead_idx >= len(self.current_path):
            lookahead_idx = len(self.current_path) - 1

        # 计算目标航向
        target_wp = np.array(self.current_path[lookahead_idx])
        target_heading = np.arctan2(target_wp[1] - self.position[1],
                                    target_wp[0] - self.position[0])

        # 计算航向误差
        heading_error = target_heading - self.heading
        heading_error = np.arctan2(np.sin(heading_error), np.cos(heading_error))

        # PID控制
        angle = 0.5 + heading_error / np.pi * 0.3  # 映射到0-1
        angle = np.clip(angle, 0.3, 0.7)  # 限制舵角范围

        # 速度控制（根据转向角度调整）
        thrust = 0.3 * (1.0 - abs(heading_error) / np.pi)
        thrust = np.clip(thrust, 0.1, 0.5)

        # 检查是否到达当前路径点
        current_wp = np.array(self.current_path[self.path_index])
        if np.linalg.norm(current_wp - self.position) < 10.0:
            self.path_index += 1

        return thrust, angle

    def run_navigation_loop(self, goal: Tuple[float, float]):
        """
        主导航循环

        Args:
            goal: 目标位置
        """
        # 规划全局路径
        if not self.plan_global_path(goal):
            return

        print(f"规划路径共{len(self.current_path)}个航点")

        # 导航循环
        rate = 10  # Hz
        while True:
            self.update_state()

            # 检查是否到达目标
            if np.linalg.norm(self.position - np.array(goal)) < 20.0:
                print("到达目标")
                self.client.setVesselControls('Vessel1',
                    airsim.VesselControls(thrust=0.0, angle=0.5))
                break

            # 计算控制
            thrust, angle = self.compute_control()

            # 发送控制指令
            self.client.setVesselControls('Vessel1',
                airsim.VesselControls(thrust=thrust, angle=angle))

            # 可视化（可选）
            # self.visualize()

            time.sleep(1.0 / rate)
```

---

## 5. 极地环境建模

### 5.1 冰情数据来源

**数据来源**:
1. **ASVSim仿真真值**: 直接从仿真获取冰分布（推荐用于论文）
2. **历史冰图**: 从国家冰中心获取（如USNIC、CIS）
3. **卫星数据**: MODIS、SAR图像处理
4. **人工标注**: 专家标注的冰分布图

### 5.2 代价地图多层表示

```python
class MultiLayerCostMap:
    """多层代价地图"""

    def __init__(self, size: Tuple[int, int]):
        self.layers = {
            'static_ice': np.zeros(size),      # 静态冰情
            'dynamic_ice': np.zeros(size),      # 动态浮冰
            'ships': np.zeros(size),            # 其他船只
            'weather': np.ones(size),           # 天气影响
            'history': np.ones(size)            # 历史航迹
        }

    def combine(self, weights: Dict[str, float]) -> np.ndarray:
        """加权组合各层"""
        total = np.zeros_like(self.layers['static_ice'])
        for layer, weight in weights.items():
            total += self.layers[layer] * weight
        return total
```

---

## 6. 备用方案分析

### 6.1 方案对比矩阵

| 场景 | 推荐方案 | 预期效果 | 实施难度 | 时间估算 |
|------|----------|----------|----------|----------|
| **理想情况** | A* + D* Lite | ⭐⭐⭐⭐⭐ | 中 | 2-3天 |
| 纯静态环境 | 仅用A* | ⭐⭐⭐⭐ | 低 | 1天 |
| 动态复杂 | D* Lite + VO | ⭐⭐⭐⭐⭐ | 高 | 3-5天 |
| 快速演示 | 纯A* + 简单避障 | ⭐⭐⭐ | 低 | 半天 |
| 论文对比 | A* vs RRT*对比实验 | ⭐⭐⭐⭐ | 中 | 2天 |

### 6.2 快速演示方案（半天实现）

```python
# 简化版A* + 直接控制
# 特点: 代码量<200行，可快速展示效果

class SimplePlanner:
    def __init__(self):
        self.waypoints = []

    def plan_straight_line(self, start, goal):
        """直线插值"""
        num_points = int(np.linalg.norm(np.array(goal)-np.array(start)) / 10)
        self.waypoints = [
            (start[0] + (goal[0]-start[0])*i/num_points,
             start[1] + (goal[1]-start[1])*i/num_points)
            for i in range(num_points+1)
        ]
        return self.waypoints
```

### 6.3 失败回退策略

**如果规划失败**:

| 层级 | 方案 | 输出 |
|------|------|------|
| 1 | 纯A*（无动态） | 全局路径可视化 |
| 2 | 人工预设路径 | 演示视频 |
| 3 | 航点跟随 | 简单导航演示 |
| 4 | 截图展示 | 静态结果图 |

---

## 7. 项目规划与里程碑

### 7.1 前置依赖

```
□ 1. ASVSim环境运行正常
□ 2. 极地场景可用（LakeEnv + Ice）
□ 3. ASV可受控移动
□ 4. 可获取船体位姿
```

### 7.2 实施时间表

#### 第一阶段: 基础实现（1天）

| 任务 | 时间 | 产出 |
|------|------|------|
| A*算法实现与测试 | 3h | 可运行的A*规划器 |
| 代价地图构建 | 2h | 冰情代价地图生成器 |
| ASVSim集成测试 | 3h | 仿真中可规划路径 |

#### 第二阶段: 增强功能（1天）

| 任务 | 时间 | 产出 |
|------|------|------|
| D* Lite实现 | 4h | 动态重规划功能 |
| 路径平滑 | 2h | 平滑连续路径 |
| 可视化增强 | 2h | 路径可视化工具 |

#### 第三阶段: 实验与展示（1天）

| 任务 | 时间 | 产出 |
|------|------|------|
| 对比实验（A* vs D* Lite） | 3h | 性能对比数据 |
| 场景测试（多种冰情） | 3h | 测试视频 |
| 论文插图生成 | 2h | 图+表+视频 |

### 7.3 里程碑检查点

```
M1: 基础规划器（Day 1）
    └─ 验收标准: ASVSim中成功规划并跟随路径

M2: 动态规划（Day 2）
    └─ 验收标准: 添加障碍物后10秒内完成重规划

M3: 论文就绪（Day 3）
    └─ 验收标准: 3组对比实验+视频+性能表格
```

---

## 8. 风险分析与对策

### 8.1 技术风险

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| 规划器陷入局部最优 | 中 | 中 | 增加随机采样或RRT*混合 |
| 动态避碰不及时 | 中 | 高 | 提高局部规划频率，简化代价计算 |
| ASVSim控制延迟 | 中 | 中 | 增加前瞻距离，预测控制 |
| 冰情建模不准确 | 低 | 中 | 使用仿真真值数据 |

---

## 9. 与论文写作的衔接

### 9.1 论文结构建议

```
第6章 路径规划层
6.1 引言与问题描述
6.2 极地路径规划算法综述（A*、D* Lite对比）
6.3 基于POLARIS的冰情代价建模
6.4 双层规划架构设计（全局+局部）
6.5 实验结果与分析
    - 6.5.1 静态环境路径规划效果
    - 6.5.2 动态障碍物避碰实验
    - 6.5.3 算法性能对比（A* vs D* Lite）
6.6 本章小结
```

### 9.2 可展示素材

**必须产出**:
1. **路径对比图**: A* vs D* Lite路径对比
2. **代价地图可视化**: 热力图显示冰情风险
3. **导航视频**: ASV跟随规划路径
4. **性能表格**: 规划时间、路径长度、重规划次数
5. **避碰场景**: 动态障碍物出现与规避过程

---

## 10. 附录

### 10.1 参考资源

**论文**:
- A*: Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). "A Formal Basis for the Heuristic Determination of Minimum Cost Paths"
- D* Lite: Koenig, S., & Likhachev, M. (2002). "D* Lite". AAAI
- POLARIS: IMO Polar Code

**极地导航**:
- "Arctic weather routing: a review of ship performance models and ice routing algorithms" (Frontiers in Marine Science, 2023)
- "Fast Path Planning for Polar Surface Unmanned Vessels" (OpenReview, 2024)

**代码参考**:
- Python Robotics: https://github.com/AtsushiSakai/PythonRobotics

---

**文档版本**: v1.0
**最后更新**: 2026-03-14
**作者**: ASVSim Project Team
**状态**: 待实施，可立即开始

