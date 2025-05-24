from xmlrpc.client import MAXINT

import pygame
import random
import sys
import math
import os
import urllib.request
from collections import deque

# 迷宫参数
CELL_SIZE = 30  # 增大格子尺寸
MAZE_WIDTH = 40  # 增加迷宫宽度
MAZE_HEIGHT = 27  # 增加迷宫高度
PATH_WIDTH = 2  # 扩宽迷宫道路
WALL = 1
PATH = 0

# 玩家尺寸 - 恢复原来的尺寸
PLAYER_SIZE = CELL_SIZE - 8  # 恢复为原来的尺寸

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (180, 180, 180)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARK = (30, 30, 30)

# 小地图参数
MINIMAP_SCALE = 0.25
MINIMAP_MARGIN = 10

# 材质缓存
textures = {}

def load_texture_from_url(url, size=None):
    """从URL或本地文件路径加载材质"""
    if url in textures:
        return textures[url]

    try:
        # 判断是否为本地文件路径
        if os.path.isfile(url):
            # 直接加载本地文件
            texture = pygame.image.load(url)
        else:
            # 创建临时文件目录
            temp_dir = "temp_textures"
            os.makedirs(temp_dir, exist_ok=True)

            # 生成唯一文件名
            filename = os.path.join(temp_dir, f"texture_{hash(url) % 10000}.png")

            # 下载图片
            urllib.request.urlretrieve(url, filename)

            # 加载图片
            texture = pygame.image.load(filename)

        # 调整大小
        if size:
            texture = pygame.transform.scale(texture, size)

        # 缓�����并返回
        textures[url] = texture
        return texture
    except Exception as e:
        print(f"无法加载材质 {url}: {e}")
        # 返回默认彩色矩形作为纹理
        surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surf.fill((random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)))
        return surf

# 生成迷宫（递归回溯法）
def generate_maze(width, height):
    maze = [[WALL for _ in range(width)] for _ in range(height)]
    stack = []
    start_x, start_y = random.randrange(1, width, 2), random.randrange(1, height, 2)
    maze[start_y][start_x] = PATH
    stack.append((start_x, start_y))
    dirs = [(-2,0),(2,0),(0,-2),(0,2)]
    while stack:
        x, y = stack[-1]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 < nx < width and 0 < ny < height and maze[ny][nx] == WALL:
                maze[ny][nx] = PATH
                maze[y + dy//2][x + dx//2] = PATH
                stack.append((nx, ny))
                break
        else:
            stack.pop()
    return maze

def get_path_cells(maze):
    return [(x, y) for y, row in enumerate(maze) for x, v in enumerate(row) if v == PATH]

def find_unique_path(maze, start, end):
    queue = deque([(start, [start])])
    visited = set([start])
    while queue:
        (x, y), path = queue.popleft()
        if (x, y) == end:
            return path
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAZE_WIDTH and 0 <= ny < MAZE_HEIGHT and maze[ny][nx] == PATH and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
    return None

def random_start_end(maze):
    path_cells = get_path_cells(maze)
    while True:
        start = random.choice(path_cells)
        end = random.choice(path_cells)
        if start != end:
            path = find_unique_path(maze, start, end)
            if path:
                return start, end, path

def find_dead_ends(maze):
    dead_ends = []
    for y in range(1, MAZE_HEIGHT-1):
        for x in range(1, MAZE_WIDTH-1):
            if maze[y][x] == PATH:
                cnt = 0
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    if maze[y+dy][x+dx] == PATH:
                        cnt += 1
                if cnt == 1:
                    dead_ends.append((x, y))
    return dead_ends

def place_balls(maze):
    # 获取所有路径格子而不是死胡同
    path_cells = get_path_cells(maze)

    # 移除起点和终点(如果有的话)
    try:
        start_end = random_start_end(maze)
        if start_end:
            start, end, _ = start_end
            if start in path_cells:
                path_cells.remove(start)
            if end in path_cells:
                path_cells.remove(end)
    except:
        pass

    # 确保有足够的路径格子放置球
    if len(path_cells) < 4:
        raise ValueError("路径格子数量不足以放置4个球")

    balls = random.sample(path_cells, 4)
    numbers = random.sample([1, 2, 3, 4], 4)
    return [(balls[i], numbers[i]) for i in range(4)]

def clamp(val, minv, maxv):
    return max(minv, min(val, maxv))

# 迷雾视野
VISION_RADIUS = 2

def get_visible(maze, px, py, radius):
    visible = set()
    for dy in range(-radius, radius+1):
        for dx in range(-radius, radius+1):
            nx, ny = px+dx, py+dy
            if 0 <= nx < MAZE_WIDTH and 0 <= ny < MAZE_HEIGHT:
                visible.add((nx, ny))
    return visible

class Player:
    def __init__(self, x, y, texture_url=None):
        self.x = x
        self.y = y
        self.collected = []
        self.texture_url = texture_url
        self.texture = None
        self.ghost_mode = False  # 添加穿墙模式标志
        if texture_url:
            self.load_texture(texture_url)

    def load_texture(self, url):
        """加载玩家材质"""
        self.texture_url = url
        self.texture = load_texture_from_url(url, (PLAYER_SIZE, PLAYER_SIZE))

    def move(self, dx, dy, maze):
        """按格子移动玩家，只能水平或垂直移动"""
        # 确保只能水平或垂直移动，不能斜着走
        if dx != 0 and dy != 0:
            return False

        # 计算新位置
        nx, ny = self.x + dx, self.y + dy

        # 检查是否有效
        if 0 <= nx < MAZE_WIDTH and 0 <= ny < MAZE_HEIGHT:
            # 如果是穿墙模式，或者是正常模式但目标是路径
            if self.ghost_mode or maze[ny][nx] == PATH:
                self.x = nx
                self.y = ny
                return True
        return False

    def get_pos(self):
        """获取玩家的网格位置"""
        return self.x, self.y

    def draw(self, surface, x=None, y=None, size=None):
        """绘制玩家"""
        # 计算像素位置
        if x is None:
            x = self.x * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2
        if y is None:
            y = self.y * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2

        if self.texture:
            if size:
                # 如果提供了尺寸参数，缩放纹理
                scaled_texture = pygame.transform.scale(self.texture, size)
                surface.blit(scaled_texture, (x, y))
            else:
                surface.blit(self.texture, (x, y))
        else:
            # 默认绘制方式，穿墙模式下使用半透明颜色
            color = GREEN
            if self.ghost_mode:
                # 创建半透明的颜色
                surface_temp = pygame.Surface((size[0] if size else PLAYER_SIZE, size[1] if size else PLAYER_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(surface_temp, (*GREEN, 128), (0, 0, size[0] if size else PLAYER_SIZE, size[1] if size else PLAYER_SIZE))
                surface.blit(surface_temp, (x, y))
            else:
                pygame.draw.rect(surface, color, (x, y, size[0] if size else PLAYER_SIZE, size[1] if size else PLAYER_SIZE))

class MazeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((MAZE_WIDTH*CELL_SIZE+200, MAZE_HEIGHT*CELL_SIZE))
        pygame.display.set_caption('Maze Game')
        self.clock = pygame.time.Clock()

        # 材质URL设置
        self.path_texture_url = None
        self.wall_texture_url = None
        self.goal_texture_url = None
        self.ball_texture_url = None

        # 材质对象
        self.path_texture = None
        self.wall_texture = None
        self.goal_texture = None
        self.ball_texture = None

        # 整体背景材质
        self.background_texture = None
        self.background_surface = None

        # Shift键挑战相关变量
        self.shift_counter = 0
        self.shift_timer = 0
        self.shift_challenge_active = False
        self.shift_challenge_result = None

        # 关卡系统
        self.level = 1  # 初始为第1关

        self.reset_game()

    def reset_game(self):
        self.maze = generate_maze(MAZE_WIDTH, MAZE_HEIGHT)
        self.start, self.end, self.path = random_start_end(self.maze)
        self.balls = place_balls(self.maze)
        self.player = Player(*self.start)
        self.fog_on = True
        self.minimap_memory = set()
        self.event_triggered = set()

    def set_textures(self, player_url=None, path_url=None, wall_url=None, goal_url=None, ball_url=None):
        """设置游戏中使用的材质URL"""
        if player_url:
            self.player.load_texture(player_url)

        if path_url:
            self.path_texture_url = path_url
            self.path_texture = load_texture_from_url(path_url, (CELL_SIZE, CELL_SIZE))

            # 创建整体背景
            try:
                # 加载原始材质
                self.background_texture = load_texture_from_url(path_url)
                # 创建背景表面
                self.background_surface = pygame.Surface((MAZE_WIDTH*CELL_SIZE, MAZE_HEIGHT*CELL_SIZE))
                # 铺满整个背景
                for y in range(0, MAZE_HEIGHT*CELL_SIZE, self.background_texture.get_height()):
                    for x in range(0, MAZE_WIDTH*CELL_SIZE, self.background_texture.get_width()):
                        self.background_surface.blit(self.background_texture, (x, y))
            except Exception as e:
                print(f"创建背景材质失败: {e}")

        if wall_url:
            self.wall_texture_url = wall_url
            self.wall_texture = load_texture_from_url(wall_url, (CELL_SIZE, CELL_SIZE))

        if goal_url:
            self.goal_texture_url = goal_url
            self.goal_texture = load_texture_from_url(goal_url, (CELL_SIZE, CELL_SIZE))

        if ball_url:
            self.ball_texture_url = ball_url
            self.ball_texture = load_texture_from_url(ball_url, (CELL_SIZE, CELL_SIZE))

    def refresh_ball(self):
        """刷新一个新球"""
        path_cells = get_path_cells(self.maze)
        # 移除已有球的位置
        for (bx, by), _ in self.balls:
            if (bx, by) in path_cells:
                path_cells.remove((bx, by))
        # 移除玩家当前位置
        px, py = self.player.get_pos()
        if (px, py) in path_cells:
            path_cells.remove((px, py))
        # 移除终点位置
        if self.end in path_cells:
            path_cells.remove(self.end)

        if path_cells:
            new_ball_pos = random.choice(path_cells)
            new_ball_num = random.choice([1, 2, 3, 4])
            self.balls.append((new_ball_pos, new_ball_num))
            print(f"刷新新球: 位置({new_ball_pos[0]}, {new_ball_pos[1]}), 数字{new_ball_num}")

    def refresh_all_balls(self):
        """在所有可行路径上刷新满小球"""
        # 清空现有的球
        self.balls = []

        # 获取所有路径单元格
        path_cells = get_path_cells(self.maze)

        # 移除起点和终点
        if (self.start[0], self.start[1]) in path_cells:
            path_cells.remove((self.start[0], self.start[1]))
        if (self.end[0], self.end[1]) in path_cells:
            path_cells.remove((self.end[0], self.end[1]))

        # 移除玩家当前位置
        px, py = self.player.get_pos()
        if (px, py) in path_cells:
            path_cells.remove((px, py))

        # 在所有可行路径上放置小球，而不仅仅是4个
        ball_numbers = []
        for _ in range(len(path_cells)):
            ball_numbers.append(random.choice([1, 2, 3, 4]))

        # 添加新球到所有可行路径上
        for i, pos in enumerate(path_cells):
            self.balls.append((pos, ball_numbers[i]))
            print(f"刷新新球: 位置({pos[0]}, {pos[1]}), 数字{ball_numbers[i]}")

    def collect_all_balls(self):
        """收��地图上所有的金色小球"""
        for (bx, by), num in self.balls[:]:
            self.player.collected.append(num)
            print(f"收集到小球: {num}")
        self.balls = []  # 清空地图上的小球列表
        print("一键收集了地图上所有的金色小球!")

    def run(self):
        running = True
        # Shift键挑战相关变量
        shift_counter = 0
        shift_timer = 0
        shift_challenge_active = False
        shift_challenge_result = None

        # 球刷新计时器
        ball_refresh_timer = 0
        ball_refresh_interval = 1000  # 默认每秒刷新一个球

        # 用于玩家拾取小球后的��新计时
        ball_pickup_refresh_timer = 0
        ball_pickup_refresh_interval = 500  # 缩短刷新时间，确保小球快速刷新

        # 记录玩家是否已经达成首次收集4个球并到达终点的成就
        first_completed = False

        # 添加移动控制变量
        move_cooldown = 100  # 移动冷却时间（毫秒）
        last_move_time = 0   # 上次移动时间

        # 确保游戏开始时有4个小球
        while len(self.balls) < 4:
            self.refresh_ball()

        while running:
            # 获取当前位置和可见区域
            px, py = self.player.get_pos()
            visible = get_visible(self.maze, px, py, VISION_RADIUS)
            self.minimap_memory.update(visible)

            # 获取当前时间
            current_time = pygame.time.get_ticks()

            # 始终确保地图上有4个小球
            if len(self.balls) < 4:
                self.refresh_ball()
                print(f"当前球数量: {len(self.balls)}/4，已自动刷新")

            # 持续移动逻辑：检查按键状态并移动
            keys = pygame.key.get_pressed()
            if current_time - last_move_time >= move_cooldown:
                moved = False
                # 只有在非挑战状态下或挑战结果为成功时才允许移动
                if not shift_challenge_active and shift_challenge_result != "失败":
                    if keys[pygame.K_w]:
                        moved = self.player.move(0, -1, self.maze)
                    elif keys[pygame.K_s]:
                        moved = self.player.move(0, 1, self.maze)
                    elif keys[pygame.K_a]:
                        moved = self.player.move(-1, 0, self.maze)
                    elif keys[pygame.K_d]:
                        moved = self.player.move(1, 0, self.maze)

                if moved:
                    last_move_time = current_time

            # 检查小球收集
            for (bx, by), num in self.balls[:]:
                if (px, py) == (bx, by):
                    self.player.collected.append(num)
                    self.balls.remove(((bx, by), num))
                    print(f"收集到小球: {num}")

                    # 设置小球拾取刷新计时器
                    ball_pickup_refresh_timer = current_time

            # 到达终点
            if (px, py) == self.end:
                if len(self.player.collected) >= 4:
                    print("你成功收集了所有小球并到达了终点!")

                    # 如果是首次完成，则清空玩家身上的球并刷新所有路径上的球
                    if not first_completed:
                        first_completed = True
                        self.player.collected = []  # 清空玩家身上的球
                        self.refresh_all_balls()    # 刷新所有路径上的球
                        print("首次完成任务！已在所有路径上刷新满小球")
                    else:
                        # 第二次完成任务时，关卡递增并刷新迷宫
                        self.level += 1  # 关卡递增
                        print(f"恭喜通过第{self.level-1}关！进入第{self.level}关")
                        self.reset_game()  # 重置游戏，生成新迷宫
                        self.player.collected = []  # 清空玩家身上的球
                        first_completed = False  # 重置首次完成标志
                else:
                    print("你到达了终点，但没有收集齐所有小球")

            # 处理小球拾���后的刷新
            if current_time - ball_pickup_refresh_timer >= ball_pickup_refresh_interval and first_completed:
                ball_pickup_refresh_timer = current_time
                # 只有当球的数量少于4个时才刷新
                if len(self.balls) < 4:
                    self.refresh_ball()
                    print("小球拾取3秒后，刷新了一个新球")

            # 死角事件处理 - 添加Shift键挑战
            if (px, py) in find_dead_ends(self.maze) and (px, py) not in self.event_triggered:
                self.event_triggered.add((px, py))
                # 启动shift按键挑战
                print(f"死角事件触发: 位置({px},{py})! 请在3秒内连续按击5次shift键!")
                shift_challenge_active = True
                shift_counter = 0
                shift_timer = pygame.time.get_ticks()  # 记录开始时间
                shift_challenge_result = None  # 重置挑战结果

            # 处理shift按键挑战
            if shift_challenge_active:
                current_time = pygame.time.get_ticks()
                # 检查是否超过3秒
                if current_time - shift_timer > 3000:
                    shift_challenge_active = False
                    if shift_counter >= 5:
                        print("挑战成功!")
                        shift_challenge_result = "成功"
                    else:
                        print(f"挑战失败! 你只按了{shift_counter}次shift键，未达到5次。")
                        shift_challenge_result = "失败"
                        print("*你死了*")
                        running = False  # 挑战失败，退出游戏

            # 处理玩家输入
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    # 处理shift按键挑战
                    if shift_challenge_active and (event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT):
                        shift_counter += 1
                        print(f"按键次数: {shift_counter}/10")

                    if event.key == pygame.K_l:
                        self.level += 1  # 设置为最大关卡
                    if event.key == pygame.K_r:
                        self.level -= 1
                    # 雾模式切换
                    if event.key == pygame.K_f:
                        self.fog_on = not self.fog_on

                    # 穿墙模式切换
                    elif event.key == pygame.K_g:
                        self.player.ghost_mode = not self.player.ghost_mode
                        if self.player.ghost_mode:
                            print("穿墙模式已开启")
                        else:
                            print("穿墙模式已关闭")

                    # 一键收集所有小球
                    elif event.key == pygame.K_o:
                        self.collect_all_balls()

            self.draw()
            self.clock.tick(30)

        pygame.quit()

    def draw(self):
        """绘制游戏界面"""
        self.screen.fill(BLACK)

        # 绘制整体背景
        if self.background_surface:
            self.screen.blit(self.background_surface, (0, 0))

        # 获取玩家位置和可见区域
        px, py = self.player.get_pos()
        visible = get_visible(self.maze, px, py, VISION_RADIUS)

        # 绘制主迷宫
        for y in range(MAZE_HEIGHT):
            for x in range(MAZE_WIDTH):
                rect = (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if not self.fog_on or (x, y) in visible:
                    if self.maze[y][x] == PATH:
                        if self.path_texture:
                            self.screen.blit(self.path_texture, rect)
                        else:
                            pygame.draw.rect(self.screen, WHITE, rect)
                    else:
                        if self.wall_texture:
                            self.screen.blit(self.wall_texture, rect)
                        else:
                            pygame.draw.rect(self.screen, GRAY, rect)
                else:
                    pygame.draw.rect(self.screen, DARK, rect)

        # 绘制终点
        if not self.fog_on or self.end in visible:
            if self.goal_texture:
                self.screen.blit(self.goal_texture, (self.end[0]*CELL_SIZE, self.end[1]*CELL_SIZE))
            else:
                pygame.draw.rect(self.screen, RED, (self.end[0]*CELL_SIZE, self.end[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # 绘制小球
        for (bx, by), num in self.balls:
            if not self.fog_on or (bx, by) in visible:
                if self.ball_texture:
                    self.screen.blit(self.ball_texture, (bx*CELL_SIZE, by*CELL_SIZE))
                else:
                    pygame.draw.circle(self.screen, YELLOW,
                                     (bx*CELL_SIZE+CELL_SIZE//2, by*CELL_SIZE+CELL_SIZE//2), CELL_SIZE//3)

                font = pygame.font.SysFont(None, 24)
                img = font.render(str(num), True, BLUE)
                self.screen.blit(img, (bx*CELL_SIZE+CELL_SIZE//2-8, by*CELL_SIZE+CELL_SIZE//2-12))

        # 绘制玩家
        self.player.draw(self.screen)

        # 绘制小地图
        self.draw_minimap()

        pygame.display.flip()

    def draw_minimap(self):
        """绘制小地图"""
        minimap_w = int(MAZE_WIDTH*MINIMAP_SCALE)
        minimap_h = int(MAZE_HEIGHT*MINIMAP_SCALE)
        minimap_s = int(CELL_SIZE*MINIMAP_SCALE)
        minimap_x = MAZE_WIDTH*CELL_SIZE + MINIMAP_MARGIN
        minimap_y = MINIMAP_MARGIN

        # 小地图边框
        pygame.draw.rect(self.screen, GRAY, (minimap_x-2, minimap_y-2,
                                           minimap_w*minimap_s+4, minimap_h*minimap_s+4), 2)

        # 小地图内容
        for y in range(MAZE_HEIGHT):
            for x in range(MAZE_WIDTH):
                if (x, y) in self.minimap_memory:
                    color = WHITE if self.maze[y][x] == PATH else GRAY
                    pygame.draw.rect(self.screen, color,
                                   (minimap_x+x*minimap_s, minimap_y+y*minimap_s, minimap_s, minimap_s))

        # 小地图终点
        pygame.draw.rect(self.screen, RED,
                       (minimap_x+self.end[0]*minimap_s, minimap_y+self.end[1]*minimap_s, minimap_s, minimap_s))

        # 小地图玩家
        px, py = self.player.get_pos()
        mini_player_size = max(2, int(minimap_s - 2))
        mini_px = minimap_x + px * minimap_s + (minimap_s - mini_player_size) // 2
        mini_py = minimap_y + py * minimap_s + (minimap_s - mini_player_size) // 2
        pygame.draw.rect(self.screen, GREEN, (mini_px, mini_py, mini_player_size, mini_player_size))

        # 小地图小球
        for (bx, by), num in self.balls:
            pygame.draw.circle(self.screen, YELLOW,
                             (minimap_x+bx*minimap_s+minimap_s//2, minimap_y+by*minimap_s+minimap_s//2),
                             max(2, minimap_s//3))

        # 显示已收集小球
        font = pygame.font.SysFont(None, 28)
        for i, num in enumerate(sorted(self.player.collected)):
            pygame.draw.circle(self.screen, YELLOW,
                             (minimap_x+minimap_w*minimap_s//2-40+i*40, minimap_y+minimap_h*minimap_s+30), 16)
            img = font.render(str(num), True, BLUE)
            self.screen.blit(img, (minimap_x+minimap_w*minimap_s//2-48+i*40+8, minimap_y+minimap_h*minimap_s+18))

        # 显示当前关卡
        level_font = pygame.font.SysFont(None, 36)
        level_text = f"The Number {self.level} "
        level_img = level_font.render(level_text, True, WHITE)
        # 在小地图下方居中显示关卡文本
        level_x = minimap_x + (minimap_w * minimap_s - level_img.get_width()) // 2
        level_y = minimap_y + minimap_h * minimap_s + 60  # 在球的显示下方
        self.screen.blit(level_img, (level_x, level_y))

def main(player_texture=None, path_texture=None, wall_texture=None, goal_texture=None, ball_texture=None):
    """入口函数，支持设置各种材质URL"""
    game = MazeGame()
    game.set_textures(player_texture, path_texture, wall_texture, goal_texture, ball_texture)
    game.run()

if __name__ == "__main__":
    # 使用本地texture目录下的材质
    current_dir = os.path.dirname(os.path.abspath(__file__))
    wall_texture = os.path.join(current_dir, "texture/wall.png")
    floor_texture = os.path.join(current_dir, "texture/floor.png")
    player_texture = os.path.join(current_dir, "texture/player.png")

    # 检查材质文件是否存在
    textures_exist = os.path.exists(wall_texture) and os.path.exists(floor_texture)
    player_exists = os.path.exists(player_texture)

    if textures_exist and player_exists:
        print(f"使用本地材质: 墙壁、地板和玩家")
        main(player_texture, floor_texture, wall_texture)
    elif textures_exist:
        print(f"使用本地材质: 墙壁和地板")
        main(None, floor_texture, wall_texture)
    else:
        print("本地材质文件不存在，使用默认渲染")
        main()
