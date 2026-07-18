	import pygame
	import socket
	import threading
	import sys
	import copy
	import time
	import os
	import json
	from queue import Queue
	# ===================== 全局常量 =====================
	WIDTH = 720
	HEIGHT = 760
	BOARD_SIZE = 15
	GRID = 40
	MARGIN = 60
	PIECE_R = 18
	FPS = 60
	PORT = 8888
	LOG_FILE = "game_log.txt"
	SAVE_FILE = "save.dat"
	BG_IMG_PATH = "./pic/bg.png"
	BG_MUSIC_PATH = "./music/bg.mp3"
	# 颜色定义
	WHITE = (255, 255, 255)
	BLACK = (0, 0, 0)
	BOARD_COLOR = (240, 200, 140)
	RED = (200, 30, 30)
	BLUE = (30, 30, 200)
	GRAY = (100, 100, 100)
	GREEN = (0, 180, 0)
	DARK_GRAY = (60, 60, 60)
	LIGHT_GRAY = (220, 220, 220)
	# 游戏模式枚举
	MODE_AI = 0
	MODE_NET_HOST = 1
	MODE_NET_CLIENT = 2
	# ===================== 日志工具 =====================
	def write_log(content):
	    stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	    log_line = f"[{stamp}] {content}\n"
	    try:
	        with open(LOG_FILE, "a", encoding="utf-8") as f:
	            f.write(log_line)
	    except:
	        pass
	    print(log_line.strip())
	# ===================== UI组件：按钮、输入框、弹窗 =====================
	class Button:
	    def __init__(self, rect, text, font, color=BLACK, bg=(200,200,200), hover=(160,160,160)):
	        self.rect = pygame.Rect(rect)
	        self.text = text
	        self.font = font
	        self.color = color
	        self.bg = bg
	        self.hover = hover
	        self.clicked = False
	    def draw(self, screen):
	        mouse = pygame.mouse.get_pos()
	        col = self.hover if self.rect.collidepoint(mouse) else self.bg
	        pygame.draw.rect(screen, col, self.rect, border_radius=6)
	        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=6)
	        txt = self.font.render(self.text, True, self.color)
	        tx = self.rect.centerx - txt.get_width() // 2
	        ty = self.rect.centery - txt.get_height() // 2
	        screen.blit(txt, (tx, ty))
	    def is_click(self, event):
	        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
	            return self.rect.collidepoint(event.pos)
	        return False
	class InputBox:
	    def __init__(self, rect, font, hint=""):
	        self.rect = pygame.Rect(rect)
	        self.font = font
	        self.text = ""
	        self.hint = hint
	        self.active = False
	    def handle_event(self, event):
	        if event.type == pygame.MOUSEBUTTONDOWN:
	            self.active = self.rect.collidepoint(event.pos)
	        if event.type == pygame.KEYDOWN and self.active:
	            if event.key == pygame.K_RETURN:
	                return self.text
	            elif event.key == pygame.K_BACKSPACE:
	                self.text = self.text[:-1]
	            else:
	                self.text += event.unicode
	        return None
	    def draw(self, screen):
	        col = BLUE if self.active else GRAY
	        pygame.draw.rect(screen, col, self.rect, 2)
	        # 修复文字不重叠，内边距统一
	        if self.text:
	            surf = self.font.render(self.text, True, BLACK)
	        else:
	            surf = self.font.render(self.hint, True, GRAY)
	        screen.blit(surf, (self.rect.x + 8, self.rect.y + 6))
	class Popup:
	    def __init__(self, screen, title, content, btn_text="确定"):
	        self.screen = screen
	        self.title = title
	        self.content = content
	        self.btn_text = btn_text
	        self.w = 420
	        self.h = 220
	        self.x = (WIDTH - self.w) // 2
	        self.y = (HEIGHT - self.h) // 2
	        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
	        self.btn = Button((self.x + 140, self.y + 140, 140, 40), btn_text, pygame.font.SysFont("simhei",24))
	        self.closed = False
	    def draw(self):
	        pygame.draw.rect(self.screen, LIGHT_GRAY, self.rect, border_radius=8)
	        pygame.draw.rect(self.screen, BLACK, self.rect, 3, border_radius=8)
	        ft = pygame.font.SysFont("simhei", 28)
	        st = ft.render(self.title, True, RED)
	        self.screen.blit(st, (self.x + 20, self.y + 12))
	        ct = pygame.font.SysFont("simhei",22).render(self.content, True, DARK_GRAY)
	        self.screen.blit(ct, (self.x + 20, self.y + 65))
	        self.btn.draw(self.screen)
	    def update(self, event):
	        if self.btn.is_click(event):
	            self.closed = True
	        return self.closed
	# ===================== AI逻辑模块 =====================
	class GobangAI:
	    def __init__(self):
	        self.score_map = {0:0,1:10,2:100,3:1000,4:10000,5:100000}
	    def get_point_score(self, board, x, y, color):
	        score = 0
	        dirs = [(1,0),(0,1),(1,1),(1,-1)]
	        for dx, dy in dirs:
	            cnt = 1
	            tx, ty = x+dx, y+dy
	            while 0<=tx<BOARD_SIZE and 0<=ty<BOARD_SIZE and board[ty][tx]==color:
	                cnt +=1
	                tx += dx
	                ty += dy
	            tx, ty = x-dx, y-dy
	            while 0<=tx<BOARD_SIZE and 0<=ty<BOARD_SIZE and board[ty][tx]==color:
	                cnt +=1
	                tx -= dx
	                ty -= dy
	            score += self.score_map[min(cnt,5)]
	        return score
	    def get_best_pos(self, board, ai_color, player_color):
	        max_score = -1
	        best_x, best_y =7,7
	        log_list = []
	        for y in range(BOARD_SIZE):
	            for x in range(BOARD_SIZE):
	                if board[y][x] !=0:
	                    continue
	                board[y][x] = ai_color
	                ai_s = self.get_point_score(board, x, y, ai_color)
	                board[y][x] = player_color
	                p_s = self.get_point_score(board, x, y, player_color)
	                board[y][x] =0
	                total = ai_s + p_s *1.1
	                log_list.append(f"AI评估({x},{y}) AI分:{ai_s} 防守分:{p_s} 总分:{total}")
	                if total>max_score:
	                    max_score = total
	                    best_x, best_y = x,y
	        for line in log_list[-12:]:
	            write_log(line)
	        write_log(f"AI最终选择落子点 ({best_x},{best_y}) 最高分数 {max_score}")
	        return best_x, best_y
	# ===================== 网络通信模块 =====================
	class NetWork:
	    def __init__(self, msg_queue):
	        self.sock = None
	        self.conn = None
	        self.addr = None
	        self.is_host = False
	        self.running = False
	        self.msg_queue = msg_queue
	        self.lock = threading.Lock()
	        self.local_ip = "127.0.0.1"
	    def get_local_ip(self):
	        try:
	            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	            s.connect(("8.8.8.8", 80))
	            ip = s.getsockname()[0]
	            s.close()
	            return ip
	        except:
	            return "127.0.0.1"
	    def start_host(self, port=PORT):
	        self.is_host = True
	        self.local_ip = self.get_local_ip()
	        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	        self.sock.bind(("0.0.0.0", port))
	        self.sock.listen(1)
	        self.running = True
	        threading.Thread(target=self._accept_loop, daemon=True).start()
	        write_log(f"服务端启动 IP:{self.local_ip}:{port}")
	        return self.local_ip
	    def start_client(self, ip, port=PORT):
	        self.is_host = False
	        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	        self.sock.settimeout(3.0)
	        try:
	            self.sock.connect((ip, port))
	            self.conn = self.sock
	            self.running = True
	            threading.Thread(target=self._recv_loop, daemon=True).start()
	            write_log(f"客户端成功连接 {ip}:{port}")
	            return True
	        except Exception as e:
	            write_log(f"客户端连接失败 {ip}:{port} 错误:{str(e)}")
	            self.close()
	            return False
	    def _accept_loop(self):
	        while self.running:
	            try:
	                new_conn, addr = self.sock.accept()
	                if self.conn:
	                    self.conn.close()
	                self.conn = new_conn
	                self.addr = addr
	                write_log(f"客户端接入 {addr}")
	                threading.Thread(target=self._recv_loop, daemon=True).start()
	                self.msg_queue.put("connected")
	                break
	            except Exception as e:
	                write_log(f"服务端accept异常:{e}")
	                break
	    def _recv_loop(self):
	        buf = ""
	        while self.running and self.conn:
	            try:
	                data = self.conn.recv(1024).decode("utf-8")
	                if not data:
	                    break
	                buf += data
	                while "\n" in buf:
	                    line, buf = buf.split("\n",1)
	                    line = line.strip()
	                    if line:
	                        self.msg_queue.put(line)
	            except ConnectionResetError:
	                break
	            except Exception as e:
	                write_log(f"接收消息异常:{e}")
	                continue
	        self.msg_queue.put("disconnect")
	        write_log("对方断开连接")
	        self.close()
	    def send_msg(self, msg):
	        if self.conn and self.running:
	            try:
	                with self.lock:
	                    self.conn.sendall((str(msg)+"\n").encode("utf-8"))
	            except Exception as e:
	                write_log(f"发送消息失败:{e}")
	                self.msg_queue.put("disconnect")
	                self.close()
	    def close(self):
	        self.running = False
	        if self.conn:
	            self.conn.close()
	        if self.sock:
	            self.sock.close()
	        self.sock = self.conn = None
	# ===================== 主游戏类 =====================
	class GobangGame:
	    def __init__(self):
	        pygame.init()
	        pygame.mixer.init()
	        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
	        pygame.display.set_caption("五子棋完整版")
	        self.clock = pygame.time.Clock()
	        self.font = pygame.font.SysFont("simhei", 24)
	        self.big_font = pygame.font.SysFont("simhei", 36)
	        self.small_font = pygame.font.SysFont("simhei", 20)
	        # 加载背景图
	        self.bg_img = None
	        try:
	            self.bg_img = pygame.image.load(BG_IMG_PATH).convert()
	            self.bg_img = pygame.transform.scale(self.bg_img, (WIDTH, HEIGHT))
	            write_log("主界面背景图加载成功")
	        except Exception as e:
	            write_log(f"主界面背景图加载失败 {BG_IMG_PATH} 错误:{str(e)}")
	        # 加载背景音乐
	        self.music_play = False
	        try:
	            pygame.mixer.music.load(BG_MUSIC_PATH)
	            pygame.mixer.music.set_volume(0.4)
	            pygame.mixer.music.play(-1)
	            self.music_play = True
	            write_log("背景音乐加载并播放成功")
	        except Exception as e:
	            write_log(f"背景音乐加载失败 {BG_MUSIC_PATH} 错误:{str(e)}")
	        # 游戏基础数据
	        self.mode = None
	        self.in_wait_room = False  # 主机创建房间后等待页面标记
	        self.board = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
	        self.history = []
	        self.current = 1
	        self.winner = 0
	        self.game_over = False
	        self.ai = GobangAI()
	        self.msg_queue = Queue()
	        self.net = NetWork(self.msg_queue)
	        self.wait_opponent = False
	        self.disconnect_tip = ""
	        self.popup = None
	        # 联机专属
	        self.my_name = "玩家"
	        self.opp_name = "对手"
	        self.start_ticks = 0
	        self.step_count = 0
	        # 底部操作按钮
	        self.btn_restart = Button((30, HEIGHT + 10, 110, 36), "重新开局", self.font, bg=GREEN)
	        self.btn_back_menu = Button((150, HEIGHT + 10, 110, 36), "返回菜单", self.font, bg=RED)
	        self.btn_save = Button((270, HEIGHT + 10, 110, 36), "保存棋局", self.font)
	        self.btn_load = Button((390, HEIGHT + 10, 110, 36), "读取存档", self.font)
	        self.btn_undo = Button((510, HEIGHT + 10, 110, 36), "悔棋", self.font, bg=BLUE)
	        # 主机等待房间UI
	        self.wait_name_box = InputBox((200, 360, 320, 36), self.font, hint="修改你的昵称")
	        self.wait_back_btn = Button((260, 500, 180, 44), "返回菜单", self.font)
	    def reset_game(self):
	        self.board = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
	        self.history.clear()
	        self.current = 1
	        self.winner = 0
	        self.game_over = False
	        self.wait_opponent = False
	        self.disconnect_tip = ""
	        self.start_ticks = pygame.time.get_ticks()
	        self.step_count = 0
	        write_log("游戏重置，新对局开始")
	    def save_board(self):
	        data = {
	            "board": self.board,
	            "history": self.history,
	            "current": self.current,
	            "step": self.step_count
	        }
	        try:
	            with open(SAVE_FILE, "w", encoding="utf-8") as f:
	                json.dump(data, f)
	            write_log("棋局保存成功 save.dat")
	            self.popup = Popup(self.screen, "提示", "棋局保存成功！")
	        except Exception as e:
	            write_log(f"保存棋局失败:{e}")
	            self.popup = Popup(self.screen, "失败", "棋局保存失败")
	    def load_board(self):
	        if not os.path.exists(SAVE_FILE):
	            self.popup = Popup(self.screen, "提示", "无存档文件")
	            return
	        try:
	            with open(SAVE_FILE, "r", encoding="utf-8") as f:
	                data = json.load(f)
	            self.board = data["board"]
	            self.history = data["history"]
	            self.current = data["current"]
	            self.step_count = data["step"]
	            self.game_over = False
	            self.winner = 0
	            write_log("读取存档成功")
	            self.popup = Popup(self.screen, "提示", "读取存档完成！")
	        except Exception as e:
	            write_log(f"读取存档失败:{e}")
	            self.popup = Popup(self.screen, "失败", "存档读取损坏")
	    # ========== 修复人机悔棋失效BUG：重写完整悔棋逻辑 ==========
	    def undo_move(self):
	        if self.mode != MODE_AI:
	            self.popup = Popup(self.screen, "提示", "联机模式无法悔棋！")
	            return
	        if not self.history:
	            self.popup = Popup(self.screen, "提示", "暂无棋子可悔！")
	            return
	        if self.game_over:
	            self.popup = Popup(self.screen, "提示", "对局已结束，不能悔棋！")
	            return
	        # 人机对战需要撤销自己+AI两步
	        if len(self.history) >= 2:
	            # 先撤销AI棋子
	            x2, y2, c2 = self.history.pop()
	            self.board[y2][x2] = 0
	            self.step_count -= 1
	            # 再撤销玩家棋子
	            x1, y1, c1 = self.history.pop()
	            self.board[y1][x1] = 0
	            self.step_count -= 1
	            self.current = 1  # 回到玩家黑棋回合
	            write_log(f"人机悔棋，撤销AI({x2},{y2}) 玩家({x1},{y1})，回到黑方回合")
	        elif len(self.history) == 1:
	            # 仅玩家下了一步，AI还没走
	            x, y, c = self.history.pop()
	            self.board[y][x] = 0
	            self.step_count -= 1
	            self.current = 1
	            write_log(f"人机悔棋，撤销玩家首子({x},{y})")
	    def handle_network_msg(self):
	        while not self.msg_queue.empty():
	            data = self.msg_queue.get()
	            if data == "disconnect":
	                self.disconnect_tip = "对手断开连接"
	                self.popup = Popup(self.screen, "断线", "对手已退出，点击返回菜单")
	                self.in_wait_room = False
	                continue
	            if data == "connected":
	                # 对手连接成功，退出等待房间进入棋局
	                self.in_wait_room = False
	                self.popup = Popup(self.screen, "连接成功", "对手已加入房间！")
	                write_log("对手成功加入对局")
	                self.reset_game()
	                self.net.send_msg(f"name:{self.my_name}")
	                continue
	            if data.startswith("name:"):
	                _, n = data.split(":",1)
	                self.opp_name = n.strip()
	                write_log(f"对方昵称更新:{self.opp_name}")
	            elif data.startswith("pos:"):
	                _,x,y = data.split(":")
	                x,y = int(x),int(y)
	                self.place_piece(x,y,self.current)
	                self.wait_opponent = False
	            elif data == "restart":
	                self.reset_game()
	    def check_win(self, x, y, color):
	        dirs = [(1,0),(0,1),(1,1),(1,-1)]
	        for dx,dy in dirs:
	            cnt=1
	            tx,ty=x+dx,y+dy
	            while 0<=tx<BOARD_SIZE and 0<=ty<BOARD_SIZE and self.board[ty][tx]==color:
	                cnt+=1;tx+=dx;ty+=dy
	            tx,ty=x-dx,y-dy
	            while 0<=tx<BOARD_SIZE and 0<=ty<BOARD_SIZE and self.board[ty][tx]==color:
	                cnt+=1;tx-=dx;ty-=dy
	            if cnt>=5:
	                return True
	        return False
	    def place_piece(self, x, y, color):
	        if self.board[y][x]!=0 or self.game_over:
	            return False
	        self.board[y][x] = color
	        self.history.append((x,y,color))
	        self.step_count +=1
	        write_log(f"落子({x},{y}) 颜色:{'黑' if color==1 else '白'} 总步数:{self.step_count}")
	        if self.check_win(x,y,color):
	            self.winner = color
	            self.game_over = True
	            win = "黑方" if color==1 else "白方"
	            write_log(f"{win}获胜，对局结束")
	        self.current = 2 if color==1 else 1
	        return True
	    def ai_auto_play(self):
	        if self.mode != MODE_AI or self.game_over or self.current !=2:
	            return
	        x,y = self.ai.get_best_pos(copy.deepcopy(self.board),2,1)
	        self.place_piece(x,y,2)
	    def mouse_to_board(self, mx, my):
	        # 修复棋盘坐标错位，严格限制棋盘范围
	        board_max = MARGIN + (BOARD_SIZE-1)*GRID
	        if mx < MARGIN or mx > board_max or my < MARGIN or my > board_max:
	            return None
	        x = round((mx - MARGIN) / GRID)
	        y = round((my - MARGIN) / GRID)
	        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
	            return x, y
	        return None
	    def draw_ui_info(self):
	        # 1. 联机昵称文字移到【左上角】(修复左下角遮挡问题)
	        if self.mode in (MODE_NET_HOST, MODE_NET_CLIENT) and not self.in_wait_room:
	            name_txt = f"我:{self.my_name} 对手:{self.opp_name}"
	            ns = self.small_font.render(name_txt, True, BLUE)
	            self.screen.blit(ns, (10, 10)) # 窗口左上角
	        # 2. 右下角时间步数 (修复：修改Y坐标避开按钮)
	        sec = (pygame.time.get_ticks() - self.start_ticks) // 1000
	        h = sec // 3600
	        m = (sec % 3600) // 60
	        s = sec % 60
	        time_str = f"{h:02d}:{m:02d}:{s:02d} 步数:{self.step_count}"
	        surf = self.small_font.render(time_str, True, BLACK)
	        self.screen.blit(surf, (WIDTH - surf.get_width() - 15, HEIGHT - 60)) # 原来是 HEIGHT - 28
	    def draw_control_buttons(self):
	        self.btn_restart.draw(self.screen)
	        self.btn_back_menu.draw(self.screen)
	        if self.mode == MODE_AI:
	            self.btn_save.draw(self.screen)
	            self.btn_load.draw(self.screen)
	            self.btn_undo.draw(self.screen)
	    def draw_board(self):
	        self.screen.fill(BOARD_COLOR)
	        board_max = MARGIN + (BOARD_SIZE-1)*GRID
	        # 修复棋盘绘制：严格15*15网格，边界对齐
	        for i in range(BOARD_SIZE):
	            offset = MARGIN + i * GRID
	            # 竖线
	            pygame.draw.line(self.screen, BLACK, (offset, MARGIN), (offset, board_max), 1)
	            # 横线
	            pygame.draw.line(self.screen, BLACK, (MARGIN, offset), (board_max, offset), 1)
	        # 标准五子棋星位
	        stars = [(3,3),(3,11),(7,7),(11,3),(11,11)]
	        for x,y in stars:
	            cx = MARGIN + x * GRID
	            cy = MARGIN + y * GRID
	            pygame.draw.circle(self.screen, BLACK, (cx, cy), 6)
	        # 绘制棋子
	        for y in range(BOARD_SIZE):
	            for x in range(BOARD_SIZE):
	                val = self.board[y][x]
	                if val == 0:
	                    continue
	                cx = MARGIN + x * GRID
	                cy = MARGIN + y * GRID
	                if val == 1:
	                    pygame.draw.circle(self.screen, BLACK, (cx, cy), PIECE_R)
	                else:
	                    pygame.draw.circle(self.screen, WHITE, (cx, cy), PIECE_R)
	                    pygame.draw.circle(self.screen, BLACK, (cx, cy), PIECE_R, 1)
	        # 状态提示文字
	        if self.disconnect_tip:
	            tip = self.disconnect_tip
	        elif self.mode == MODE_AI:
	            tip = "人机对战 | 使用下方按钮操作"
	        else:
	            tip = "联机对局 | 等待对手落子" if self.wait_opponent else "联机对局 | 你的回合"
	        self.screen.blit(self.font.render(tip, True, BLACK), (10, board_max + 12))
	        # 胜利提示居中
	        if self.game_over:
	            wt = f"黑方胜利!" if self.winner == 1 else "白方胜利!"
	            surf = self.big_font.render(wt, True, RED)
	            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, board_max + 48))
	        self.draw_ui_info()
	        self.draw_control_buttons()
	    def draw_host_wait_room(self):
	        """主机创建房间后的等待界面：显示本机IP、修改昵称、等待对手"""
	        if self.bg_img:
	            self.screen.blit(self.bg_img, (0,0))
	        else:
	            self.screen.fill(BOARD_COLOR)
	        # 标题
	        title = self.big_font.render("等待对手连接", True, BLACK)
	        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 120))
	        # 本机IP
	        ip_text = self.font.render(f"你的房间IP：{self.net.local_ip}:{PORT}", True, RED)
	        self.screen.blit(ip_text, (WIDTH//2 - ip_text.get_width()//2, 180))
	        # 昵称标签
	        label = self.small_font.render("修改你的昵称：", True, BLACK)
	        self.screen.blit(label, (200, 320))
	        # 昵称输入框
	        self.wait_name_box.text = self.my_name
	        self.wait_name_box.draw(self.screen)
	        # 提示
	        tip = self.font.render("请把IP发给好友，等待对方加入...", True, DARK_GRAY)
	        self.screen.blit(tip, (WIDTH//2 - tip.get_width()//2, 420))
	        # 返回按钮
	        self.wait_back_btn.draw(self.screen)
	    def handle_host_wait_event(self, event):
	        # 等待房间事件处理
	        self.wait_name_box.handle_event(event)
	        if self.wait_back_btn.is_click(event):
	            self.net.close()
	            self.in_wait_room = False
	            return True
	        # 更新昵称
	        if self.wait_name_box.text.strip():
	            self.my_name = self.wait_name_box.text.strip()
	        return False
	    def show_connect_popup(self):
	        # 修复：IP/端口/昵称标签文字大幅左移，不压输入框
	        ip_box = InputBox((200,240,320,36), self.font, hint="输入服务端IP")
	        port_box = InputBox((200,300,320,36), self.font, hint=f"{PORT}")
	        name_box = InputBox((200,360,320,36), self.font, hint="输入你的昵称")
	        confirm_btn = Button((260,440,180,44), "连接", self.big_font, bg=GREEN)
	        back_btn = Button((260,500,180,44), "返回菜单", self.font)
	        running = True
	        while running:
	            if self.bg_img:
	                self.screen.blit(self.bg_img,(0,0))
	            else:
	                self.screen.fill(BOARD_COLOR)
	            title = self.big_font.render("加入局域网房间", True, BLACK)
	            self.screen.blit(title, (WIDTH//2-title.get_width()//2,160))
	            # ========== 标签文字左移到x=80，远离输入框 ==========
	            self.screen.blit(self.small_font.render("IP地址",True,BLACK),(80,242))
	            self.screen.blit(self.small_font.render("端口",True,BLACK),(80,302))
	            self.screen.blit(self.small_font.render("昵称",True,BLACK),(80,362))
	            ip_box.draw(self.screen)
	            port_box.draw(self.screen)
	            name_box.draw(self.screen)
	            confirm_btn.draw(self.screen)
	            back_btn.draw(self.screen)
	            for event in pygame.event.get():
	                if event.type == pygame.QUIT:
	                    pygame.quit();sys.exit()
	                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
	                    return None
	                ip_box.handle_event(event)
	                port_box.handle_event(event)
	                name_box.handle_event(event)
	                if back_btn.is_click(event):
	                    return None
	                if confirm_btn.is_click(event):
	                    ip = ip_box.text.strip()
	                    p_str = port_box.text.strip()
	                    name = name_box.text.strip()
	                    if not ip:
	                        self.popup = Popup(self.screen,"输入错误","IP不能为空")
	                        continue
	                    p = PORT
	                    if p_str:
	                        try: p=int(p_str)
	                        except: pass
	                    if name:
	                        self.my_name = name
	                    write_log(f"客户端输入 IP:{ip} PORT:{p} NAME:{self.my_name}")
	                    succ = self.net.start_client(ip,p)
	                    if succ:
	                        self.net.send_msg(f"name:{self.my_name}")
	                        return MODE_NET_CLIENT
	                    else:
	                        self.popup = Popup(self.screen,"连接失败","无法连接服务端，请检查IP/防火墙")
	            if self.popup:
	                self.popup.draw()
	                for e in pygame.event.get():
	                    if self.popup.update(e):
	                        self.popup = None
	            pygame.display.flip()
	            self.clock.tick(FPS)
	    def menu_select(self):
	        btns = [
	            Button((220,220,280,60), "1.人机对战", self.big_font),
	            Button((220,300,280,60), "2.创建房间(服务端)", self.big_font),
	            Button((220,380,280,60), "3.加入房间(客户端)", self.big_font),
	            Button((220,460,280,60), "退出游戏", self.big_font, bg=RED)
	        ]
	        while True:
	            if self.bg_img:
	                self.screen.blit(self.bg_img, (0,0))
	            else:
	                self.screen.fill(BOARD_COLOR)
	            title = pygame.font.SysFont("simhei", 48).render("五子棋完整版", True, BLACK)
	            self.screen.blit(title, (WIDTH//2-title.get_width()//2,100))
	            for b in btns:
	                b.draw(self.screen)
	            pygame.display.flip()
	            for event in pygame.event.get():
	                if event.type == pygame.QUIT:
	                    self.net.close()
	                    pygame.quit();sys.exit()
	                for idx,b in enumerate(btns):
	                    if b.is_click(event):
	                        if idx ==0:
	                            self.mode = MODE_AI
	                            self.reset_game()
	                            write_log("进入人机对战模式")
	                            return
	                        elif idx ==1:
	                            # 创建房间，进入等待页面，不直接进棋盘
	                            self.mode = MODE_NET_HOST
	                            self.net.start_host(PORT)
	                            self.in_wait_room = True
	                            self.wait_room_loop()
	                            return
	                        elif idx ==2:
	                            res = self.show_connect_popup()
	                            if res:
	                                self.mode = res
	                                self.reset_game()
	                                return
	                        elif idx ==3:
	                            self.net.close()
	                            pygame.quit()
	                            sys.exit()
	    def wait_room_loop(self):
	        """主机等待房间循环，对手连接成功才退出"""
	        running = True
	        while running and self.in_wait_room:
	            self.handle_network_msg()
	            # 收到connected信号自动退出等待
	            if not self.in_wait_room:
	                break
	            self.draw_host_wait_room()
	            if self.popup:
	                self.popup.draw()
	            for event in pygame.event.get():
	                if self.popup:
	                    if self.popup.update(event):
	                        self.popup = None
	                    continue
	                if event.type == pygame.QUIT:
	                    self.net.close()
	                    pygame.quit();sys.exit()
	                # 处理等待房间UI事件
	                exit_wait = self.handle_host_wait_event(event)
	                if exit_wait:
	                    self.reset_game()  # 修复bug：退出前重置游戏状态和计时器
	                    running = False
	            pygame.display.flip()
	            self.clock.tick(FPS)
	    def run_game(self):
	        self.menu_select()
	        while True:
	            self.handle_network_msg()
	            self.draw_board()
	            self.ai_auto_play()
	            if self.popup:
	                self.popup.draw()
	            for event in pygame.event.get():
	                if self.popup:
	                    if self.popup.update(event):
	                        self.popup = None
	                    continue
	                if event.type == pygame.QUIT:
	                    self.net.close()
	                    pygame.quit();sys.exit()
	                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
	                    # 底部按钮事件
	                    if self.btn_restart.is_click(event):
	                        self.reset_game()
	                        if self.mode != MODE_AI:
	                            self.net.send_msg("restart")
	                            write_log("发送重开指令")
	                    elif self.btn_back_menu.is_click(event):
	                        self.net.close()
	                        return
	                    elif self.mode == MODE_AI:
	                        if self.btn_save.is_click(event):
	                            self.save_board()
	                        elif self.btn_load.is_click(event):
	                            self.load_board()
	                        elif self.btn_undo.is_click(event):
	                            self.undo_move()
	                    # 棋盘落子
	                    if self.game_over or self.disconnect_tip:
	                        continue
	                    if self.mode != MODE_AI and self.wait_opponent:
	                        continue
	                    pos = self.mouse_to_board(*event.pos)
	                    if pos is None:
	                        continue
	                    x,y = pos
	                    if self.place_piece(x,y,self.current):
	                        if self.mode != MODE_AI:
	                            self.net.send_msg(f"pos:{x}:{y}")
	                            self.wait_opponent = True
	            pygame.display.flip()
	            self.clock.tick(FPS)
	if __name__ == "__main__":
	    write_log("===== 程序启动 =====")
	    game = GobangGame()
	    while True:
	        game.run_game()
