from dotenv import load_dotenv
import os
import time
import cv2 as cv
from cv2.typing import MatLike
import numpy as np
import pyautogui
from common import find_minefield_bounds, \
    extract_grid_coordinates, \
    parse_game_state, \
    get_neighbors

from itertools import product

Position = tuple[int, int]
Color = tuple[int, int, int]
HintChange = tuple[Position, str]
GridCoords = tuple[list[int], list[int]]

NO_LABEL = "0"
WRONG_FLAG = "1"
SAFE = "2"
DANGEROUS = "3"
WRONG_FLAG_NEAR = "4"
LABEL_COLORS = {WRONG_FLAG: (0, 255, 255),
                SAFE: (0, 255, 0),
                DANGEROUS: (0, 0, 255),
                WRONG_FLAG_NEAR: (255, 0, 255)}


def analyze_tile_neighbors(tile_index: Position,
                           minefield: list[str],
                           hint: list[str]) -> list[HintChange]:
    y, x = tile_index
    neighbours = get_neighbors(tile_index, minefield)
    changes: list[HintChange] = []
    num_mines = int(minefield[y][x])

    num_flags = sum(1 for i, j in neighbours if minefield[i][j] == "F")
    num_unknowns = sum(1 for i, j in neighbours if minefield[i][j] == "?")
    num_dangerous = sum(1 for i, j in neighbours if hint[i][j] in
                        {DANGEROUS, WRONG_FLAG_NEAR})
    num_safe = sum(1 for i, j in neighbours if hint[i][j] == SAFE)
    num_correct_flags = 0

    if num_flags > num_mines:
        changes.extend(((i, j), WRONG_FLAG) for i, j in neighbours if
                       minefield[i][j] == "F" and hint[i][j] == NO_LABEL)
    else:
        num_correct_flags = sum(1 for i, j in neighbours if
                                hint[i][j] == NO_LABEL and
                                minefield[i][j] == "F")

    if num_correct_flags == num_mines:
        changes.extend(((i, j), SAFE) for i, j in neighbours if
                       minefield[i][j] == "?" and hint[i][j] != SAFE)
    if num_correct_flags + num_dangerous == num_mines:
        changes.extend(((i, j), SAFE) for i, j in neighbours if
                       minefield[i][j] == "?" and hint[i][j] == NO_LABEL)

    if num_unknowns - num_safe + num_flags == num_mines:
        changes.extend(((i, j), DANGEROUS) for i, j in neighbours if
                       minefield[i][j] == "?" and hint[i][j] == NO_LABEL)
        changes.extend(((i, j), WRONG_FLAG_NEAR) for i, j in neighbours if
                       minefield[i][j] == "F" and hint[i][j] == WRONG_FLAG)
    return changes


def validate_mine_flags(tile_index: Position,
                        minefield: list[str],
                        hint: list[str]) -> list[HintChange]:
    y, x = tile_index
    changes: list[HintChange] = []
    neighbours = get_neighbors(tile_index, minefield)

    num_mines = int(minefield[y][x])
    num_flags = sum(1 for i, j in neighbours if minefield[i][j] == "F")

    if num_flags > num_mines:
        changes.extend(((i, j), WRONG_FLAG) for i, j in neighbours if
                       minefield[i][j] == "F" and hint[i][j] == NO_LABEL)
    return changes

def analyze_double_tile_patterns(minefield: list[str], hint: list[str]) -> list[HintChange]:
    height = len(minefield)
    width = len(minefield[0]) if height > 0 else 0
    changes: list[HintChange] = []
    directions = [(0, 1), (1, 0)]  # right and down only to avoid redundancy

    def is_number(s: str) -> bool:
        return s.isdigit() and s != "0"

    for y in range(height):
        for x in range(width):
            if not is_number(minefield[y][x]):
                continue
            for dy, dx in directions:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < height and 0 <= nx < width):
                    continue
                if not is_number(minefield[ny][nx]):
                    continue

                # Fetch tile values
                val1 = int(minefield[y][x])
                val2 = int(minefield[ny][nx])

                # Get neighbors
                n1 = set(get_neighbors((y, x), minefield))
                n2 = set(get_neighbors((ny, nx), minefield))
                shared = n1 & n2
                only1 = n1 - n2
                only2 = n2 - n1

                # Get counts
                f1 = sum(1 for i, j in n1 if minefield[i][j] == "F")
                f2 = sum(1 for i, j in n2 if minefield[i][j] == "F")
                u1 = [pos for pos in only1 if minefield[pos[0]][pos[1]] == "?"]
                u2 = [pos for pos in only2 if minefield[pos[0]][pos[1]] == "?"]
                shared_unknown = [pos for pos in shared if minefield[pos[0]][pos[1]] == "?"]

                rem1 = val1 - f1
                rem2 = val2 - f2

                # Example inference rule: If rem2 - rem1 == len(u2), then all u2 are mines
                if rem2 > rem1 and rem2 - rem1 == len(u2):
                    for pos in u2:
                        if hint[pos[0]][pos[1]] == NO_LABEL:
                            changes.append((pos, DANGEROUS))
                # Or vice versa: if rem1 - rem2 == len(u1), u1 are mines
                if rem1 > rem2 and rem1 - rem2 == len(u1):
                    for pos in u1:
                        if hint[pos[0]][pos[1]] == NO_LABEL:
                            changes.append((pos, DANGEROUS))
                # Safe inference: if rem1 == rem2 and shared_unknown and u1/u2 exist, maybe they're safe
                if rem1 == rem2 and shared_unknown and not u1 and not u2:
                    for pos in shared_unknown:
                        if hint[pos[0]][pos[1]] == NO_LABEL:
                            changes.append((pos, SAFE))
    return changes


def generate_hint_map(minefield: list[str]) -> list[str]:
    hint = [len(row) * NO_LABEL for row in minefield]
    non_important = {"?", "0", "F"}

    for y, row in enumerate(minefield):
        for x, tile in enumerate(row):
            if tile in non_important:
                continue

            changes = validate_mine_flags((y, x), minefield, hint)
            for (i, j), new_label in changes:
                hint[i] = hint[i][:j] + new_label + hint[i][j + 1:]

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
    # Add pattern inference after normal rules
    changes = analyze_double_tile_patterns(minefield, hint)
    for (i, j), new_label in changes:
        hint[i] = hint[i][:j] + new_label + hint[i][j + 1:]

    return hint


def generate_overlay(image: MatLike, hint: list[str],
                     field_grid: GridCoords) -> MatLike:
    x_coords, y_coords = field_grid
    tile_size = field_grid[0][1] - field_grid[0][0]
    overlay = np.zeros_like(image, dtype=np.uint8)

    for y_idx, y in enumerate(y_coords[:-1]):
        for x_idx, x in enumerate(x_coords[:-1]):
            label = hint[y_idx][x_idx]
            if label != NO_LABEL:
                cv.rectangle(overlay, (x, y), (x + tile_size, y + tile_size),
                             LABEL_COLORS[label], thickness=-1)
    image = cv.addWeighted(image, 1, overlay, 0.5, 0)
    return image


def main() -> None:
    load_dotenv("config.env")

    main_color: Color = tuple(
        map(int, os.getenv("MAIN_COLOR",
                           "198,198,198").split(",")))   # type: ignore
    check_delay = int(os.getenv("CHECK_DELAY", 2))
    tile_padding = int(os.getenv("TILE_PADDING", 5))
    field_padding = int(os.getenv("FIELD_PADDING", 12))

    while True:
        screenshot = np.array(pyautogui.screenshot())
        right_side = screenshot[:, len(screenshot[0]) // 2:]
        right_side = cv.cvtColor(right_side, cv.COLOR_RGB2BGR)

        field = find_minefield_bounds(right_side, main_color)
        if field is None:
            print("Coudn't find the minefield. Trying again in 1 second.")
            time.sleep(check_delay)
            continue
        grid = extract_grid_coordinates(
            right_side, field, main_color, tile_padding, field_padding)
        if grid is None:
            print("Coudn't extract the grid coordinates. Trying again in 1 second.")
            time.sleep(check_delay)
            continue
        game_state = parse_game_state(right_side, grid)
        hint = generate_hint_map(game_state)
        (x_start, y_start), (x_end, y_end) = field
        output = generate_overlay(right_side, hint, grid)[y_start: y_end,
                                                          x_start: x_end]
        cv.imshow("Hint", output)

        key = cv.waitKey(check_delay)
        if key == ord("q"):
            break
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
