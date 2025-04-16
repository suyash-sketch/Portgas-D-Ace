import pygame
import os
from grid import Grid

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (400, 100)

# Set scale factor and window size
SCALE_FACTOR = 0.75
surface = pygame.display.set_mode((int(1200*SCALE_FACTOR), int(900*SCALE_FACTOR)))
pygame.display.set_caption('Sudoku')

# Initialize fonts with scaled sizes
pygame.font.init()
game_font = pygame.font.SysFont('Comic Sans MS', int(50*SCALE_FACTOR))
game_font2 = pygame.font.SysFont('Comic Sans MS', int(25*SCALE_FACTOR))

# Create grid instance
grid = Grid(pygame, game_font, SCALE_FACTOR)
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and not grid.win:
            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                grid.get_mouse_click(pos[0], pos[1])
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and grid.win:
                grid.restart()

    # Draw everything
    surface.fill((0, 0, 0))
    grid.draw_all(pygame, surface)

    # Win message
    if grid.win:
        won_surface = game_font.render("You Won!", False, (0, 255, 0))
        surface.blit(won_surface, (int(950*SCALE_FACTOR), int(650*SCALE_FACTOR)))

        press_space_surf = game_font2.render("Press Space to Restart!", False, (0, 255, 200))
        surface.blit(press_space_surf, (int(920*SCALE_FACTOR), int(750*SCALE_FACTOR)))

    pygame.display.flip()