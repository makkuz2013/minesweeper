import pygame
import random
import time
import threading

pygame.init()
screen = pygame.display.set_mode((500, 600))
clock = pygame.time.Clock()
running = True

tilespr = pygame.image.load("graphics/tile.png")
tilespr = pygame.transform.scale(tilespr, (50, 50))

minespr = pygame.image.load("graphics/mine.png")
minespr = pygame.transform.scale(minespr, (50, 50))

debugdraw = pygame.image.load("graphics/debugdraw.png")
debugdraw = pygame.transform.scale(debugdraw, (50, 50))

font = pygame.font.SysFont("Comic Sans MS", 45)

class Tile:
    def __init__(self):
        self.content = 0
        self.unlocked = False
        self.pathfound = False

grid = []
for i in range(100):
    grid.append(Tile())
workgrid = grid.copy()
for i in range(10):
    index = random.randrange(0, len(workgrid))
    grid[index].content = "m"
    workgrid.pop(index)

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

pathfind_dirs = {
    "up": -10,
    "down" : 10,
    "left": -1,
    "right": 1,
}

colors = [(0,0,255),
          (0,255,0),
          (255,0,0),
          (64, 64, 255),
          (255, 64, 64),
          (64, 64, 64)]

def moveindex(i, dir):
    work_i = i + dirlookup[dir]
    row = int(i / 10)
    column = i % 10
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
        
def checksurround(i):
    total_mines = 0
    for dir in dirlookup.keys():
        total_mines += checkdir(i, dir)
    return total_mines

for i, tile in enumerate(grid):
    if grid[i].content == "m":
        continue
    grid[i].content = checksurround(i)

branches = []

class Branch:
    def __init__(self, i, dir):
        self.dir = dir
        self.i = i
        time.sleep(0.5)
        branchout(moveindex(i, dir))

def branchout(i):
    for dir in pathfind_dirs:
        work_i = moveindex(i, dir)
        if work_i == None:
            continue
        if grid[work_i].content > 0:
            continue
        if grid[work_i].pathfound:
            continue
        grid[work_i].pathfound = True
        branches.append(Branch(i, dir))

def pathfind(start):
    branchout(start)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill("lightgray")

    for i in range(10):
        for j in range(10):
            index = i + j * 10
            rect = pygame.Rect(0, 0, 50, 50)
            rect.center = (i*50 + 25, j*50 + 125)
            screen.blit(tilespr, rect)
            if grid[index].pathfound:
                screen.blit(debugdraw, rect)
            if grid[index].content == "m":
                screen.blit(minespr, rect)
            elif grid[index].content > 0:
                text_surf = font.render(str(grid[index].content), False, colors[grid[index].content - 1])
                text_rect = text_surf.get_rect()
                text_rect.center = (i*50 + 25, j*50 + 125)
                screen.blit(text_surf, text_rect)
            if rect.collidepoint(pygame.mouse.get_pos()):
                if pygame.mouse.get_pressed()[0]:
                    threading.Thread(target=pathfind, args=(index,), daemon=True).start()

    pygame.display.flip()

    clock.tick(60)

pygame.quit()