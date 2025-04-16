from random import sample
from selection import SelectNumber
from copy import deepcopy


def create_line_coordinates(cell_size: int) -> list[list[tuple]]:
    points = []

    for y in range(1, 9):
        temp = [(0, y * cell_size), (9 * cell_size, y * cell_size)]
        points.append(temp)

    for x in range(1, 10):
        temp = [(x * cell_size, 0), (x * cell_size, 9 * cell_size)]
        points.append(temp)

    return points


SUB_GRID_SIZE = 3
GRID_SIZE = SUB_GRID_SIZE * SUB_GRID_SIZE


def is_valid(grid, row, col, num):
    for x in range(GRID_SIZE):
        if grid[row][x] == num:
            return False

    for x in range(GRID_SIZE):
        if grid[x][col] == num:
            return False

    start_row = row - row % SUB_GRID_SIZE
    start_col = col - col % SUB_GRID_SIZE
    for i in range(SUB_GRID_SIZE):
        for j in range(SUB_GRID_SIZE):
            if grid[i + start_row][j + start_col] == num:
                return False

    return True


def solve(grid):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if grid[row][col] == 0:
                for num in range(1, GRID_SIZE + 1):
                    if is_valid(grid, row, col, num):
                        grid[row][col] = num
                        if solve(grid):
                            return True
                        grid[row][col] = 0
                return False
    return True

def create_grid(sub_grid: int) -> list[list]:
    grid = [[0 for _ in range(sub_grid * sub_grid)] for _ in range(sub_grid * sub_grid)]

    def fill_diagonal():
        for i in range(0, GRID_SIZE, SUB_GRID_SIZE):
            nums = sample(range(1, GRID_SIZE + 1), GRID_SIZE)
            for row in range(SUB_GRID_SIZE):
                for col in range(SUB_GRID_SIZE):
                    grid[row + i][col + i] = nums.pop()

    fill_diagonal()
    solve(grid)
    return grid

def remove_numbers(grid: list[list]) -> None:
    num_of_cells = GRID_SIZE * GRID_SIZE
    empties = num_of_cells * 3 // 7
    for i in sample(range(num_of_cells), empties):
        grid[i // GRID_SIZE][i % GRID_SIZE] = 0


class Grid:
    def __init__(self, pygame, font, scale_factor=1.0):
        self.scale_factor = scale_factor
        self.cell_size = int(100 * scale_factor)
        self.line_coordinates = create_line_coordinates(self.cell_size)
        self.grid = create_grid(SUB_GRID_SIZE)
        self.__test_grid = deepcopy(self.grid)
        self.win = False

        remove_numbers(self.grid)
        self.occupied_cell_coordinates = self.pre_occupied_cells()
        self.game_font = font
        self.selection = SelectNumber(pygame, self.game_font, scale_factor)

    def restart(self) -> None:
        self.grid = create_grid(SUB_GRID_SIZE)
        self.__test_grid = deepcopy(self.grid)
        remove_numbers(self.grid)
        self.occupied_cell_coordinates = self.pre_occupied_cells()
        self.win = False

    def check_grids(self):
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                if self.grid[y][x] != self.__test_grid[y][x]:
                    return False
        return True

    def is_cell_preoccupied(self, x:int, y:int) -> bool:
        for cell in self.occupied_cell_coordinates:
            if x == cell[1] and y == cell[0]:
                return True
        return False

    def get_mouse_click(self, x: int, y: int) -> None:
        if x <= 9 * self.cell_size:
            grid_x, grid_y = x // self.cell_size, y // self.cell_size
            if not self.is_cell_preoccupied(grid_x, grid_y):
                self.set_cell(grid_x, grid_y, self.selection.selected_number)
        self.selection.button_clicked(x, y)
        if self.check_grids():
            self.win = True

    def pre_occupied_cells(self) -> list[tuple]:
        occupied_cell_coordinates = []
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                if self.get_cell(x, y) != 0:
                    occupied_cell_coordinates.append((y,x))
        return occupied_cell_coordinates

    def __draw_lines(self, pg, surface) -> None:
        for index, point in enumerate(self.line_coordinates):
            if index == 2 or index == 5 or index == 10 or index == 13:
                pg.draw.line(surface, (255, 200, 0), point[0], point[1], int(4 * self.scale_factor))
            else:
                pg.draw.line(surface, (0, 50, 0), point[0], point[1], int(2 * self.scale_factor))

    def __draw_numbers(self, surface) -> None:
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                num = self.grid[y][x]
                if num != 0:
                    if (y, x) in self.occupied_cell_coordinates:
                        text_surface = self.game_font.render(str(self.get_cell(x, y)), False, (0, 200, 255))
                    else:
                        text_surface = self.game_font.render(str(self.get_cell(x, y)), False, (0, 255, 0))

                    if self.get_cell(x, y) != self.__test_grid[y][x]:
                        text_surface = self.game_font.render(str(self.get_cell(x, y)), False, (255, 0, 0))
                    surface.blit(text_surface, (x * self.cell_size + int(30 * self.scale_factor),
                                             y * self.cell_size + int(20 * self.scale_factor)))

    def draw_all(self, pg, surface):
        self.__draw_lines(pg, surface)
        self.__draw_numbers(surface)
        self.selection.draw(pg, surface)

    def get_cell(self, x: int, y: int) -> int:
        return self.grid[y][x]

    def set_cell(self, x: int, y: int, value: int) -> None:
        self.grid[y][x] = value

    def show(self):
        for cell in self.grid:
            print(cell)


if __name__ == "__main__":
    grid = Grid(font=None)
    grid.show()