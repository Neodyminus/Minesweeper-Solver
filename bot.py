from dotenv import load_dotenv
import os
import time
import cv2 as cv
import numpy as np
import pyautogui
from common import find_minefield_bounds, \
    extract_grid_coordinates, \
    parse_game_state, \
    get_neighbors

Position = tuple[int, int]
Color = tuple[int, int, int]
HintChange = tuple[Position, str]
GridCoords = tuple[list[int], list[int]]

UNCLICKABLE = "0"
EMPTY = "1"
SAFE = "2"
DANGEROUS = "3"


def analyze_tile_neighbors(tile_index: tuple[int, int],
                           minefield: list[str],
                           hint: list[str]) -> list[HintChange]:
    y, x = tile_index
    neighbours = get_neighbors(tile_index, minefield)
    changes: list[HintChange] = []
    num_mines = int(minefield[y][x])

    num_flags = sum(1 for i, j in neighbours if minefield[i][j] == "F")
    num_unknowns = sum(1 for i, j in neighbours if minefield[i][j] == "?")
    num_dangerous = sum(1 for i, j in neighbours if hint[i][j] == DANGEROUS)
    num_safe = sum(1 for i, j in neighbours if hint[i][j] == SAFE)
    num_correct_flags = sum(1 for i, j in neighbours if
                            hint[i][j] == UNCLICKABLE and
                            minefield[i][j] == "F")

    if num_correct_flags == num_mines:
        changes.extend(((i, j), SAFE) for i, j in neighbours if
                       minefield[i][j] == "?" and hint[i][j] != SAFE)
    if num_correct_flags + num_dangerous == num_mines:
        changes.extend(((i, j), SAFE) for i, j in neighbours if
                       minefield[i][j] == "?" and
                       hint[i][j] in {EMPTY, UNCLICKABLE})
    if num_unknowns - num_safe + num_flags == num_mines:
        changes.extend(((i, j), DANGEROUS) for i, j in neighbours if
                       minefield[i][j] == "?" and
                       hint[i][j] in {EMPTY, UNCLICKABLE})
    return changes


def generate_hint_map(minefield: list[str]) -> list[str]:
    hint = [len(row) * UNCLICKABLE for row in minefield]
    non_important = {"?", "0", "F"}
    change_count = 1
    while change_count > 0:
        change_count = 0
        for y, row in enumerate(minefield):
            for x, tile in enumerate(row):
                if tile not in non_important:
                    changes = analyze_tile_neighbors((y, x), minefield, hint)
                    for (i, j), new_label in changes:
                        hint[i] = hint[i][:j] + new_label + hint[i][j + 1:]
                        change_count += 1
                if minefield[y][x] == "?" and hint[y][x] == UNCLICKABLE:
                    hint[y] = hint[y][:x] + EMPTY + hint[y][x + 1:]
    return hint


def apply_clicks(hint: list[str],
                 field_grid: GridCoords,
                 random_click: bool,
                 screen_scaling: float,
                 click_delay: float,
                 turbo_mode: bool) -> True:
    x_coords, y_coords = field_grid
    tile_size = field_grid[0][1] - field_grid[0][0]
    click = False

    for y_idx, y in enumerate(y_coords[:-1]):
        for x_idx, x in enumerate(x_coords[:-1]):
            label = hint[y_idx][x_idx]
            if label == UNCLICKABLE or (label == EMPTY and not random_click):
                continue
            click = True
            if label == EMPTY:
                pyautogui.click((x + tile_size // 2) / screen_scaling,
                                (y + tile_size // 2) / screen_scaling)
                random_click = False
                if not turbo_mode:
                    return True
                time.sleep(click_delay)
            if label == SAFE:
                pyautogui.click((x + tile_size // 2) / screen_scaling,
                                (y + tile_size // 2) / screen_scaling)
                if not turbo_mode:
                    return True
                time.sleep(click_delay)
            if label == DANGEROUS:
                pyautogui.click((x + tile_size // 2) / screen_scaling,
                                (y + tile_size // 2) / screen_scaling,
                                button="right")
                if not turbo_mode:
                    return True
                time.sleep(click_delay)
                return True
    return click


def main() -> None:
    load_dotenv("config.env")

    screen_scaling = float(os.getenv("SCREEN_SCALING", 1))
    main_color: Color = tuple(
        map(int, os.getenv("MAIN_COLOR",
                           "198,198,198").split(",")))   # type: ignore
    click_delay = float(os.getenv("CLICK_DELAY", 1))
    tile_padding = int(os.getenv("TILE_PADDING", 5))
    field_padding = int(os.getenv("FIELD_PADDING", 12))
    turbo_mode = int(os.getenv("TURBO_MODE", 0)) != 0

    last_click = True
    click = True
    while last_click or click:
        screenshot = np.array(pyautogui.screenshot())
        screenshot = cv.cvtColor(screenshot, cv.COLOR_RGB2BGR)

        field = find_minefield_bounds(screenshot, main_color)
        if field is None:
            print("Coudn't find the minefield. Trying again in 1 second.")
            click = True
            time.sleep(1)
            continue
        grid = extract_grid_coordinates(
            screenshot, field, main_color, tile_padding, field_padding)
        if grid is None:
            print("Coudn't extract the grid coordinates. Trying again in 1 second.")
            click = True
            time.sleep(1)
            continue
        game_state = parse_game_state(screenshot, grid)
        hint = generate_hint_map(game_state)

        last_click = click
        click = apply_clicks(
            hint, grid, not last_click, screen_scaling, click_delay, turbo_mode)

        if not turbo_mode:
            time.sleep(click_delay)


if __name__ == "__main__":
    main()
