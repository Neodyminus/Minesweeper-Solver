from dotenv import load_dotenv, set_key
import os
import time
import cv2 as cv
from cv2.typing import MatLike
import numpy as np
import pyautogui
from common import find_minefield_bounds, \
    extract_grid_coordinates

Color = tuple[int, int, int]
GridCoords = tuple[list[int], list[int]]


def draw_grid_overlay(image: MatLike, field_grid: GridCoords) -> MatLike:
    x_coords, y_coords = field_grid
    overlay = image.copy()

    for x in x_coords:
        cv.line(overlay, (x, y_coords[0]), (x, y_coords[-1]), (0, 255, 0), 1)

    for y in y_coords:
        cv.line(overlay, (x_coords[0], y), (x_coords[-1], y), (0, 255, 0), 1)

    return overlay


def main() -> None:
    load_dotenv("config.env")

    main_color: Color = tuple(
        map(int, os.getenv("MAIN_COLOR",
                           "198,198,198").split(",")))   # type: ignore
    tile_padding = int(os.getenv("TILE_PADDING", 5))
    field_padding = int(os.getenv("FIELD_PADDING", 12))

    while True:
        screenshot = np.array(pyautogui.screenshot())
        right_side = screenshot[:, len(screenshot[0]) // 2:]
        right_side = cv.cvtColor(right_side, cv.COLOR_RGB2BGR)

        field = find_minefield_bounds(right_side, main_color)
        if field is None:
            print("Coudn't find the minefield. Trying again in 1 second.")
            time.sleep(1)
            continue

        grid = extract_grid_coordinates(
            right_side, field, main_color, tile_padding, field_padding)
        if grid is None:
            print("Coudn't extract the grid coordinates. Trying again in 1 second.")
            time.sleep(1)
            continue

        grid_overlay = draw_grid_overlay(right_side, grid)
        (x_start, y_start), (x_end, y_end) = field

        cv.imshow("Grid Overlay", grid_overlay[y_start: y_end,
                                               x_start: x_end])
        key = cv.waitKey(0)

        if key == ord('w'):
            field_padding += 1
        elif key == ord('s'):
            field_padding -= 1
        elif key == ord('a'):
            tile_padding -= 1
        elif key == ord('d'):
            tile_padding += 1
        elif key == 13:  # Enter key
            set_key("config.env", "TILE_PADDING", str(tile_padding))
            set_key("config.env", "FIELD_PADDING", str(field_padding))
            break

        print(f"Tile Padding: {tile_padding}, Field Padding: {field_padding}")

    cv.destroyAllWindows()
    print("Calibration complete. Settings saved.")


if __name__ == "__main__":
    main()
