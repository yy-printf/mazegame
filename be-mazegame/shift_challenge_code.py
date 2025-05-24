# 在MazeGame.run方法中添加以下代码，主要修改死角事件处理部分

def run(self):
    running = True
    # Shift键挑战相关变量
    shift_counter = 0
    shift_timer = 0
    shift_challenge_active = False
    shift_challenge_result = None

    while running:
        # 获取当前位置和可见区域等信息
        px, py = self.player.get_pos()
        visible = get_visible(self.maze, px, py, VISION_RADIUS)
        self.minimap_memory.update(visible)

        # 检查小球收集
        for (bx, by), num in self.balls[:]:
            if (px, py) == (bx, by):
                self.player.collected.append(num)
                self.balls.remove(((bx, by), num))
                print(f"收集到小球: {num}")

        # 死角事件处理 - 添加Shift键挑战
        if (px, py) in find_dead_ends(self.maze) and (px, py) not in self.event_triggered:
            self.event_triggered.add((px, py))
            # 启动shift按键挑战
            print(f"死角事件触发: 位置({px},{py})! 请在3秒内连续按击20次shift键!")
            shift_challenge_active = True
            shift_counter = 0
            shift_timer = pygame.time.get_ticks()  # 记录开始时间

        # 处理shift按键挑战
        if shift_challenge_active:
            current_time = pygame.time.get_ticks()
            # 检查是否超过3秒
            if current_time - shift_timer > 4000:  # 3000毫秒 = 4秒
                shift_challenge_active = False
                if shift_counter >= 20:
                    print("行吧")
                    shift_challenge_result = "成功"
                else:
                    print(f"挑战失败! 你只按了{shift_counter}次shift键，未达到20次。")
                    shift_challenge_result = "失败"

        # 处理玩家输入
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # 处理shift按键挑战
                if shift_challenge_active and (event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT):
                    shift_counter += 1
                    print(f"按键次数: {shift_counter}/20")

                # 正常的移动控制
                if event.key == pygame.K_w:
                    self.player.move(0, -1, self.maze)
                elif event.key == pygame.K_s:
                    self.player.move(0, 1, self.maze)
                elif event.key == pygame.K_a:
                    self.player.move(-1, 0, self.maze)
                elif event.key == pygame.K_d:
                    self.player.move(1, 0, self.maze)
                elif event.key == pygame.K_f:
                    self.fog_on = not self.fog_on

        # 到达终点
        if (px, py) == self.end:
            if len(self.player.collected) == 4:
                print("你死了,但你拿到了所有的球")
            else:
                print("你没拿完球")

        self.draw()
        self.clock.tick(30)

