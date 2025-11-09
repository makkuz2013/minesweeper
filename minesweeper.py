import pygame
import random
import time
import threading

# Короче создать окно и прочее
pygame.init()
screen = pygame.display.set_mode((500, 600))
clock = pygame.time.Clock()

# Данные об нажатии на мышку (Для того чтобы небыло так что ты зажал и код выполнялся 100000 раз)
class TapData:
    def __init__(self):
        self.value = False
        self.data = None

def generategrid():
    global grid, mines
    grid = [] # Создать сетку
    for i in range(100):
        grid.append(Tile()) # Заполнить пустыми клетками

    mines = 10

    # Поставить мины
    for tile in random.sample(grid, 10):
        tile.content = "m"

    # Поставить цифры
    for i, tile in enumerate(grid):
        if grid[i].content == "m":
            continue
        grid[i].content = checksurround(i)

def reset_tapped():
    global tapped
    # Сброс данных о нажатии
    tapped = [TapData(), TapData()]

# Перезапуск игры
def startgame():
    global gameover, tick, tapped, state, running

    generategrid()

    gameover = None

    tick = 0

    reset_tapped()

    state = "smile_neutral"

    running = True

# Загрузить шрифты, спрайты и звуки
lcdfont = pygame.font.Font("fonts/digital-7.ttf", 48)

font = pygame.font.SysFont("Comic Sans MS", 45)

sprites = {
    "tile": pygame.image.load("graphics/tile.png"),
    "mine": pygame.image.load("graphics/mine.png"),
    "DebugDraw": pygame.image.load("graphics/DebugDraw.png"),
    "flag": pygame.image.load("graphics/flag.png"),
    "dugtile": pygame.image.load("graphics/dugtile.png"),
    "smile_neutral": pygame.image.load("graphics/smile_neutral.png"),
    "smile_click": pygame.image.load("graphics/smile_tap.png"),
    "smile_win": pygame.image.load("graphics/smile_win.png"),
    "smile_dead": pygame.image.load("graphics/smile_dead.png"),
    "smile_sad": pygame.image.load("graphics/smile_sad.png")
}

sounds = {
    "Expl": pygame.mixer.Sound("sounds/Expl.mp3"),
    "dig": pygame.mixer.Sound("sounds/dig.ogg"),
    "flag": pygame.mixer.Sound("sounds/flag.ogg")
}

class Sprite:
    def __init__(self, norm):
        self.norm = norm
        self.darkened = None
    def darken(self):
        dark_img = self.norm.copy()
        dark_img.fill((170, 170, 170, 255), special_flags=pygame.BLEND_RGBA_ADD)
        self.darkened = dark_img

# Преобразовать спрайты в объекты класса Sprite и изменить размер
for sprite in sprites.keys():
    sprites[sprite] = Sprite(pygame.transform.scale(sprites[sprite], (50, 50)))
    #sprites[sprite].darken()

# Класс клетки
class Tile:
    def __init__(self):
        self.content = 0
        self.unlocked = False
        self.pathfound = False
        self.dug = False
        self.flagged = False

# Направления для счёта мин
dirlookup = {
    "up": -10,
    "down" : 10,
    "left": -1,
    "right": 1,
    "upleft": -11,
    "upright": -9,
    "downleft": 9,
    "downright": 11
}

# Урезанная версия направлений для поиска пути
pathfind_dirs = {
    "up": -10,
    "down" : 10,
    "left": -1,
    "right": 1,
}

# Цветовая схема
colors = [(0,0,255),
          (0,255,0),
          (255,0,0),
          (64, 64, 255),
          (255, 64, 64),
          (64, 64, 64)]

# Двинуть индекс в направлении
def moveindex(i, dir):
    work_i = i + dirlookup[dir]
    row = int(i / 10)
    column = i % 10
    # Правила выхода за границы
    if row == 0:
        if dir == "up" or dir == "upleft" or dir == "upright":
            return None
    if row == 9:
        if dir == "down" or dir == "downleft" or dir == "downright":
            return None
    if column == 0:
        if dir == "left" or dir == "downleft" or dir == "upleft":
            return None
    if column == 9:
        if dir == "right" or dir == "downright" or dir == "upright":
            return None
    return work_i

# Проверить наличие мины в направлении
def checkdir(i, dir):
    work_i = moveindex(i, dir)
    if work_i == None:
        return 0
    try:
        if grid[work_i].content == "m":
            return 1
        else:
            return 0
    except IndexError:
        return 0
# Проверить наличие мин вокруг клетки
def checksurround(i):
    total_mines = 0
    for dir in dirlookup.keys():
        total_mines += checkdir(i, dir)
    return total_mines

branches = []

# Класс ветки для поиска пути
class Branch:
    def __init__(self, i, dir):
        self.dir = dir
        self.i = i
        branchout(moveindex(self.i, self.dir))

# Разветвление пути
def branchout(i):
    for dir in pathfind_dirs:
        work_i = moveindex(i, dir)
        if work_i == None:
            continue
        if grid[work_i].content > 0:
            grid[work_i].unlocked = True
            grid[work_i].dug = True
            continue
        if grid[work_i].pathfound:
            continue
        grid[work_i].dug = True
        grid[work_i].pathfound = True
        branches.append(Branch(i, dir))

# Поиск пути
def pathfind(start):
    global gameover
    if grid[start].pathfound:
        return
    if grid[start].content == "m":
        gameover = "mine"
        reset_tapped()
        sounds["Expl"].play()
        print("BOMB")
        return
    if grid[start].content > 0:
        grid[start].unlocked = True
        grid[start].dug = True
        sounds["dig"].play()
        return
    sounds["dig"].play()
    branchout(start)

# Плейсхолдеры для LCD дисплеев
lcdplaceholders = (lcdfont.render("000", False, "red"), lcdfont.render("010", False, "red"))

# Отрисовка LCD дисплея
def lcd(surf: pygame.Surface,text: any, pos: tuple, data: str):
    if not type(text) == str:
        text = str(text)
    if int(text) < 0:
        text = text.removeprefix("-")
        for i in range(2 - len(text)):
            text = "0" + text
        text = "-" + text
    if len(text) < 3:
        for i in range(3 - len(text)):
            text = "0" + text
    text_surf = lcdfont.render(text, False, "red")
    if data == "clock":
        text_rect = lcdplaceholders[0].get_rect()
    else:
        text_rect = lcdplaceholders[1].get_rect()
    text_rect.center = pos
    background = text_rect.copy()
    background.width += 25
    background.center = text_rect.center
    pygame.draw.rect(surf, "black", background, border_radius=7)
    surf.blit(text_surf, text_rect)

# Рисовать смайлик
def drawsmile(surf: pygame.Surface, state: str):
    global smilerect
    smilerect = pygame.Rect(0,0,50,50)
    smilerect.center = (surf.get_width() / 2, 50)
    surf.blit(sprites[state].norm, smilerect)

# Проверить поле на правильность флагов
def checkfield(minecount: int):
    correct = 0

    for tile in grid:
        if tile.flagged:
            if tile.content == "m":
                correct += 1
            else:
                return False
    
    for tile in grid:
        if not tile.unlocked:
            if not tile == "m":
                tile.unlocked = True
                if type(tile.content) == int:
                    if not tile.content > 0:
                        if not tile.dug:
                            tile.dug = True
    
    if correct == minecount:
        return True

# Главный цикл игры
def mainloop():
    global running, mines, tick, state, gameover
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        screen.fill("lightgray")

        lcd(screen, mines, (150, 50), "mines")
        lcd(screen, int(tick / 1000), (350, 50), "clock")

        drawsmile(screen, state)

        # Если мин не осталось, проверить правильность флагов
        if mines == 0:
            if checkfield(10):
                gameover = "win"
                reset_tapped()
            else:
                gameover = "incorrect"
                reset_tapped()

        # Отрисовка клеток
        for i in range(10):
            for j in range(10):
                index = i + j * 10
                rect = pygame.Rect(0, 0, 50, 50)
                rect.center = (i*50 + 25, j*50 + 125)
                if rect.collidepoint(pygame.mouse.get_pos()):
                    if not gameover:
                        if pygame.mouse.get_pressed()[0]:
                            state = "smile_click"
                            if not tapped[0].value or not tapped[0].data == index:
                                tapped[0].value = True
                                tapped[0].data = index
                                threading.Thread(target=pathfind, args=(index,), daemon=True).start()
                        else:
                            tapped[0].value = False
                        if pygame.mouse.get_pressed()[2]:
                            state = "smile_click"
                            if not tapped[1].value or not tapped[1].data == index:
                                tapped[1].value = True
                                tapped[1].data = index
                                if grid[index].flagged:
                                    grid[index].flagged = False
                                    mines += 1
                                    condition = True
                                    # Если уже флаг стоит, снять его
                                else:
                                    # Проверить можно ли поставить флаг
                                    if type(grid[index].content) == int:
                                        condition = grid[index].content > 0 and grid[index].unlocked or grid[index].dug
                                    else:
                                        condition = False
                                if not condition:
                                    # Поставить флаг
                                    grid[index].flagged = True
                                    sounds["flag"].play()
                                    mines -= 1
                        else:
                            tapped[1].value = False
                        if not pygame.mouse.get_pressed()[0] and not pygame.mouse.get_pressed()[2]:
                            state = "smile_neutral"
                else:
                    if smilerect.collidepoint(pygame.mouse.get_pos()):
                        if pygame.mouse.get_pressed()[0]:
                            if tapped[0].value == False:
                                tapped[0].value = True
                        else:
                            if tapped[0].value == True:
                                # Если нажал на смайлик, перезапустить игру
                                running = False
                                print("PUK")
                                startgame()
                                mainloop()
                    if gameover == "mine":
                        state = "smile_dead"
                    elif gameover == "incorrect":
                        state = "smile_sad"
                    elif gameover == "win":
                        state = "smile_win"
                darken = index % 2 == 0
                if j % 2 == 0:
                    darken = not darken
                if grid[index].dug:
                    #if darken:
                        #screen.blit(sprites["dugtile"].darkened, rect)
                    #else:
                        #screen.blit(sprites["dugtile"].norm, rect)
                    screen.blit(sprites["dugtile"].norm, rect)
                else:
                    #if darken:
                        #screen.blit(sprites["tile"].darkened, rect)
                    #else:
                        #screen.blit(sprites["tile"].norm, rect)
                    screen.blit(sprites["tile"].norm, rect)
                #if grid[index].pathfound:
                    #screen.blit(debugdraw, rect)
                if grid[index].flagged:
                    screen.blit(sprites["flag"].norm, rect)
                if grid[index].content == "m": 
                    if gameover == "mine" or gameover == "incorrect":
                        screen.blit(sprites["mine"].norm, rect)
                    else:
                        continue
                elif grid[index].content > 0 and grid[index].unlocked:
                        text_surf = font.render(str(grid[index].content), False, colors[grid[index].content - 1])
                        text_rect = text_surf.get_rect()
                        text_rect.center = (i*50 + 25, j*50 + 125)
                        screen.blit(text_surf, text_rect)

        pygame.display.flip()

        ftime = clock.tick(60)
        if not gameover:
            tick += ftime

startgame()
mainloop()

pygame.quit()