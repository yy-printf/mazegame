import pygame
import random

# 初始化Pygame
pygame.init()

# 设置颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
FOG_COLOR = (30, 30, 30, 255)  # 添加alpha通道

# 设置游戏窗口
WINDOW_SIZE = (800, 600)
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption('迷宫游戏')

# 定义网格大小
CELL_SIZE = 40
GRID_WIDTH = WINDOW_SIZE[0] // CELL_SIZE
GRID_HEIGHT = WINDOW_SIZE[1] // CELL_SIZE

# 创建迷雾层
fog_surface = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
VISION_RADIUS = 3  # 可视范围半径（以格子为单位）

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visual_x = x * CELL_SIZE + 2
        self.visual_y = y * CELL_SIZE + 2
        self.target_x = self.visual_x
        self.target_y = self.visual_y
        self.progress = 0
        self.size = CELL_SIZE - 4
        self.move_speed = 5
        self.is_moving = False
        self.move_direction = (0, 0)  # 当前移动方向
        # 视野中心点
        self.vision_center_x = self.visual_x + self.size // 2
        self.vision_center_y = self.visual_y + self.size // 2
    
    def try_move(self, dx, dy, maze):
        new_x = self.x + dx
        new_y = self.y + dy
        if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and
            maze[new_y][new_x] != 1):  # 1代表墙
            self.x = new_x
            self.y = new_y
            self.target_x = new_x * CELL_SIZE + 2
            self.target_y = new_y * CELL_SIZE + 2
            self.is_moving = True
            self.move_direction = (dx, dy)
            return True
        return False

    def update(self, maze):
        # 处理连续移动
        keys = pygame.key.get_pressed()
        if not self.is_moving:
            if keys[pygame.K_LEFT]:
                self.try_move(-1, 0, maze)
            elif keys[pygame.K_RIGHT]:
                self.try_move(1, 0, maze)
            elif keys[pygame.K_UP]:
                self.try_move(0, -1, maze)
            elif keys[pygame.K_DOWN]:
                self.try_move(0, 1, maze)

        if self.is_moving:
            # 计算当前位置到目标位置的距离
            dx = self.target_x - self.visual_x
            dy = self.target_y - self.visual_y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            if distance < self.move_speed:
                self.visual_x = self.target_x
                self.visual_y = self.target_y
                self.is_moving = False
                # 到达目标后立即检查是否需要继续移动
                if any([keys[pygame.K_LEFT], keys[pygame.K_RIGHT], 
                       keys[pygame.K_UP], keys[pygame.K_DOWN]]):
                    self.try_move(self.move_direction[0], self.move_direction[1], maze)
            else:
                move_ratio = self.move_speed / distance
                self.visual_x += dx * move_ratio
                self.visual_y += dy * move_ratio

            # 平滑更新视野中心点
            self.vision_center_x = self.visual_x + self.size // 2
            self.vision_center_y = self.visual_y + self.size // 2

    def draw(self, screen):
        pygame.draw.rect(screen, RED,
                        (self.visual_x,
                         self.visual_y,
                         self.size, self.size))

    def update_vision(self):
        # 更新迷雾效果
        fog_surface.fill((30, 30, 30, 255))
        
        # 使用平滑移动的视野中心点创建圆形视野
        vision_size = VISION_RADIUS * CELL_SIZE
        pygame.draw.circle(fog_surface, (30, 30, 30, 0),
                          (self.vision_center_x, self.vision_center_y), 
                          vision_size)
        
        # 创建一个圆形视野
        center_x = self.x * CELL_SIZE + CELL_SIZE // 2
        center_y = self.y * CELL_SIZE + CELL_SIZE // 2
        vision_size = VISION_RADIUS * CELL_SIZE
        
        # 创建渐变视野效果
        for radius in range(vision_size, 0, -1):
            alpha = int(255 * (radius / vision_size))
            alpha = max(0, min(255, alpha))
            temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (0, 0, 0, alpha), 
                             (radius, radius), radius)
            fog_surface.blit(temp_surface, 
                            (center_x - radius, center_y - radius), 
                            special_flags=pygame.BLEND_RGBA_SUB)

class Item:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.size = CELL_SIZE // 2
    
    def draw(self, screen):
        if not self.collected:
            pygame.draw.circle(screen, YELLOW,
                             (self.x * CELL_SIZE + CELL_SIZE // 2,
                              self.y * CELL_SIZE + CELL_SIZE // 2),
                             self.size // 2)

# 生成迷宫（简单版本）
def create_maze():
    # 初始化迷宫，全部都是通道
    maze = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    
    # 设置外墙
    for x in range(GRID_WIDTH):
        maze[0][x] = 1
        maze[GRID_HEIGHT-1][x] = 1
    for y in range(GRID_HEIGHT):
        maze[y][0] = 1
        maze[y][GRID_WIDTH-1] = 1
    
    def divide(x1, y1, x2, y2):
        # 如果区域太小，就不再分割
        if x2 - x1 < 2 or y2 - y1 < 2:
            return
        
        # 随机选择一个点作为分割点
        wall_x = random.randint(x1 + 1, x2 - 1)
        wall_y = random.randint(y1 + 1, y2 - 1)
        
        # 创建十字墙
        for x in range(x1, x2 + 1):
            maze[wall_y][x] = 1
        for y in range(y1, y2 + 1):
            maze[y][wall_x] = 1
        
        # 在墙上随机开三个洞
        holes = [(wall_x, wall_y)]
        # 水平墙上开洞
        hole_x = random.randint(x1, wall_x - 1)
        holes.append((hole_x, wall_y))
        hole_x = random.randint(wall_x + 1, x2)
        holes.append((hole_x, wall_y))
        # 垂直墙上开洞
        hole_y = random.randint(y1, wall_y - 1)
        holes.append((wall_x, hole_y))
        hole_y = random.randint(wall_y + 1, y2)
        holes.append((wall_x, hole_y))
        
        # 在墙上开洞
        for hole_x, hole_y in holes:
            maze[hole_y][hole_x] = 0
        
        # 递归处理四个象限
        divide(x1, y1, wall_x - 1, wall_y - 1)  # 左上
        divide(wall_x + 1, y1, x2, wall_y - 1)  # 右上
        divide(x1, wall_y + 1, wall_x - 1, y2)  # 左下
        divide(wall_x + 1, wall_y + 1, x2, y2)  # 右下
    
    # 从整个迷宫开始递归分割
    divide(1, 1, GRID_WIDTH - 2, GRID_HEIGHT - 2)
    
    # 确保起点和终点可达
    maze[1][1] = 0  # 起点
    maze[GRID_HEIGHT-2][GRID_WIDTH-2] = 0  # 终点
    
    # 确保起点和终点周围有路
    maze[1][2] = maze[2][1] = 0  # 起点周围
    maze[GRID_HEIGHT-2][GRID_WIDTH-3] = maze[GRID_HEIGHT-3][GRID_WIDTH-2] = 0  # 终点周围
    
    return maze

# 生成物品
def create_items():
    items = []
    for _ in range(4):  # 创建4个物品
        while True:
            x = random.randint(1, GRID_WIDTH-2)
            y = random.randint(1, GRID_HEIGHT-2)
            if maze[y][x] == 0 and not any(item.x == x and item.y == y for item in items):
                items.append(Item(x, y))
                break
    return items

# 创建迷宫和游戏对象
maze = create_maze()
player = Player(1, 1)
items = create_items()

# 游戏主循环
running = True
clock = pygame.time.Clock()

while running:
    # 在主循环中，将原来的键盘事件处理改为：
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 更新玩家位置和状态
    player.update(maze)
    
    # 检查物品收集
    for item in items:
        if not item.collected and player.x == item.x and player.y == item.y:
            item.collected = True
            player.progress += 1
    
    # 检查是否到达终点
    if (player.x == GRID_WIDTH-2 and player.y == GRID_HEIGHT-2):
        if player.progress >= 4:
            print("恭喜通关！")
            running = False
        else:
            print(f"需要收集更多物品！当前进度：{player.progress}/4")

    # 绘制游戏画面
    screen.fill(BLACK)
    
    # 绘制迷宫
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if maze[y][x] == 1:
                pygame.draw.rect(screen, BLUE,
                               (x * CELL_SIZE, y * CELL_SIZE,
                                CELL_SIZE, CELL_SIZE))
    
    # 绘制物品
    for item in items:
        item.draw(screen)
    
    # 删除这行重复的更新调用
    # player.update()  # 删除这行
    
    # 绘制玩家
    player.draw(screen)
    
    # 绘制终点
    pygame.draw.rect(screen, GREEN,
                     ((GRID_WIDTH-2) * CELL_SIZE,
                      (GRID_HEIGHT-2) * CELL_SIZE,
                      CELL_SIZE, CELL_SIZE))
    
    # 更新并绘制迷雾
    player.update_vision()
    screen.blit(fog_surface, (0, 0))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()