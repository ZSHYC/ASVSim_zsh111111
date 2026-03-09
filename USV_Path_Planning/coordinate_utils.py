# -*- coding: utf-8 -*-
import numpy as np
import cv2

class MapConverter:
    """
    地图转换器类
    负责：
    1. 读取地图图片并进行二值化处理（区分水和岸）。
    2. 提供 UE5 世界坐标与 图片像素坐标 之间的相互转换功能。
    """
    def __init__(self, map_path='local_map.png'):
        # 1. 读取灰度图
        # cv2.imread 读取图片，0 表示以灰度模式读取
        # 结果是一个二维矩阵，数值范围 0(黑) ~ 255(白)
        self.grid_map_raw = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
        
        if self.grid_map_raw is None:
            raise ValueError(f"错误：找不到地图文件 {map_path}，请确认文件名和路径！")

        # 获取图片尺寸：高度(rows) 和 宽度(cols)
        self.height, self.width = self.grid_map_raw.shape
        
        # ================= 地图预处理 (关键步骤) =================
        # 2. 二值化 (Binarization)
        # 你的图片里，障碍物是黑色，水面是深灰色。
        # 我们设定阈值 20：亮度大于 20 的像素视为“路(255)”，小于 20 的视为“墙(0)”
        # 这里的 20 是根据你发的黑底图调整的，如果水面被误判为墙，可以将这个数调小
        _, self.binary_map = cv2.threshold(self.grid_map_raw, 20, 255, cv2.THRESH_BINARY)
        
        # 3. 障碍物膨胀 (Inflation) - 给船留安全距离
        # 原理：让黑色的区域向外扩张一圈。这样算法生成的路径就不会贴着岸边走。
        # kernel 大小 (5, 5) 决定了膨胀的厚度，数字越大，离岸越远
        kernel = np.ones((5, 5), np.uint8) 
        # erode 在图像处理中是腐蚀白色区域，也就是让黑色区域变大
        self.grid_map = cv2.erode(self.binary_map, kernel, iterations=1)

        # ================= 坐标系标定 (你刚才测量的核心数据) =================
        # 这里的坐标对应 local_map.png 的四个边缘
        
        # 左边界 (对应图片的左边缘 X)
        self.UE_LEFT_X = -10870.0   
        
        # 上边界 (对应图片的上边缘 Y)
        # 注意：在UE5里，Y轴向上是正方向，所以上边界是正数
        self.UE_TOP_Y  = 2160.0    
        
        # 右边界 (对应图片的右边缘 X)
        self.UE_RIGHT_X = 110.0  
        
        # 下边界 (对应图片的下边缘 Y)
        self.UE_BOTTOM_Y = -1390.0 
        # ===================================================================

    def world_to_pixel(self, x, y):
        """
        将 UE5 世界坐标 (x, y) 转换为 图片像素坐标 (u, v)
        """
        # 防止坐标超出地图范围，做一个强制限制 (clip)
        x = np.clip(x, self.UE_LEFT_X, self.UE_RIGHT_X)
        y = np.clip(y, self.UE_BOTTOM_Y, self.UE_TOP_Y)

        # 计算 X 方向的比例 (0.0 ~ 1.0)
        # 公式：(当前X - 最左X) / 总宽度
        ratio_x = (x - self.UE_LEFT_X) / (self.UE_RIGHT_X - self.UE_LEFT_X)
        u = ratio_x * self.width
        
        # 计算 Y 方向的比例
        # 注意：图片坐标系 v 是向下的(0在上面)，而 UE5 Y 是向上的
        # 所以需要用 (1.0 - ratio) 来反转坐标轴
        ratio_y = (y - self.UE_BOTTOM_Y) / (self.UE_TOP_Y - self.UE_BOTTOM_Y)
        v = (1.0 - ratio_y) * self.height
        
        return int(u), int(v)

    def pixel_to_world(self, u, v):
        """
        将 图片像素坐标 (u, v) 转换为 UE5 世界坐标 (x, y)
        """
        # 防止像素坐标越界
        u = np.clip(u, 0, self.width - 1)
        v = np.clip(v, 0, self.height - 1)
        
        # 反向计算 X
        ratio_x = u / self.width
        x = self.UE_LEFT_X + ratio_x * (self.UE_RIGHT_X - self.UE_LEFT_X)
        
        # 反向计算 Y (同样需要注意反转)
        ratio_y = 1.0 - (v / self.height)
        y = self.UE_BOTTOM_Y + ratio_y * (self.UE_TOP_Y - self.UE_BOTTOM_Y)
        
        return x, y

    def is_obstacle(self, u, v):
        """
        检查像素坐标 (u, v) 是否是障碍物
        """
        if u < 0 or u >= self.width or v < 0 or v >= self.height:
            return True # 出界也算障碍
        
        # 这里的 grid_map 中，0(黑)代表障碍，255(白)代表水
        # 如果像素值小于 128，我们认为是障碍
        return self.grid_map[v, u] < 128