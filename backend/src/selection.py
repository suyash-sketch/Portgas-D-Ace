import pygame

class SelectNumber:
    def __init__(self, pygame, font, scale_factor=1.0):
        self.pygame = pygame
        self.scale_factor = scale_factor
        self.btn_w = int(80 * scale_factor)
        self.btn_h = int(80 * scale_factor)
        self.my_font = font
        self.selected_number = 0

        self.color_selected = (0, 255, 0)
        self.color_normal = (200, 200, 200)

        self.btn_positions = [
            (int(950 * scale_factor), int(50 * scale_factor)),
            (int(1050 * scale_factor), int(50 * scale_factor)),
            (int(950 * scale_factor), int(150 * scale_factor)),
            (int(1050 * scale_factor), int(150 * scale_factor)),
            (int(950 * scale_factor), int(250 * scale_factor)),
            (int(1050 * scale_factor), int(250 * scale_factor)),
            (int(950 * scale_factor), int(350 * scale_factor)),
            (int(1050 * scale_factor), int(350 * scale_factor)),
            (int(1050 * scale_factor), int(450 * scale_factor))
        ]

    def draw(self, pygame, surface):
        for index, pos in enumerate(self.btn_positions):
            pygame.draw.rect(surface, self.color_normal,
                           [pos[0], pos[1], self.btn_w, self.btn_h],
                           width=int(3 * self.scale_factor),
                           border_radius=int(10 * self.scale_factor))

            if self.button_hover(pos):
                pygame.draw.rect(surface, self.color_selected,
                               [pos[0], pos[1], self.btn_w, self.btn_h],
                               width=int(3 * self.scale_factor),
                               border_radius=int(10 * self.scale_factor))
                text_surface = self.my_font.render(str(index + 1), False, (0, 255, 0))
            else:
                text_surface = self.my_font.render(str(index + 1), False, self.color_normal)

            if self.selected_number > 0:
                if self.selected_number - 1 == index:
                    pygame.draw.rect(surface, self.color_selected,
                                   [pos[0], pos[1], self.btn_w, self.btn_h],
                                   width=int(3 * self.scale_factor),
                                   border_radius=int(10 * self.scale_factor))
                    text_surface = self.my_font.render(str(index + 1), False, self.color_selected)

            text_x = pos[0] + int(26 * self.scale_factor)
            text_y = pos[1]
            surface.blit(text_surface, (text_x, text_y))

    def button_clicked(self, mouse_x: int, mouse_y: int) -> None:
        for index, pos in enumerate(self.btn_positions):
            if self.on_button(mouse_x, mouse_y, pos):
                self.selected_number = index + 1

    def button_hover(self, pos: tuple) -> bool|None:
        mouse_pos = self.pygame.mouse.get_pos()
        if self.on_button(mouse_pos[0], mouse_pos[1], pos):
            return True

    def on_button(self, mouse_x: int, mouse_y: int, pos: tuple) -> bool:
        return pos[0] < mouse_x < pos[0] + self.btn_w and pos[1] < mouse_y < pos[1] + self.btn_h