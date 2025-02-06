import cv2 as cv
from cv2.typing import MatLike
import numpy as np

Position = tuple[int, int]
Color = tuple[int, int, int]
GridCoords = tuple[list[int], list[int]]


VICINITY = [(-1, 1), (0, 1), (1, 1),
            (-1, 0), (1, 0),
            (-1, -1), (0, -1), (1, -1)]


def find_minefield_bounds(image: MatLike,
                          main_color: Color) \
        -> tuple[Position, Position] | None:
    mask = cv.inRange(image, np.array(main_color), np.array(main_color))

    masked_image = cv.bitwise_and(image, image, mask=mask)
    grayscale_image = cv.cvtColor(masked_image, cv.COLOR_BGR2GRAY)

    contours, _ = cv.findContours(
        grayscale_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        return None

    field_contour = max(contours, key=cv.contourArea)
    x, y, w, h = cv.boundingRect(field_contour)
    return (x, y), (x + w, y + h)


def extract_grid_coordinates(image: MatLike,
                             minefield_position: tuple[Position, Position],
                             main_color: Color,
                             tile_padding: int,
                             field_padding: int) -> GridCoords | None:
    (x_start, y_start), (x_end, y_end) = minefield_position
    image = image[y_start:y_end, x_start:x_end]

    mask = cv.inRange(image, np.array(main_color), np.array(main_color))
    masked_image = cv.bitwise_and(image, image, mask=mask)
    grayscale_image = cv.cvtColor(masked_image, cv.COLOR_BGR2GRAY)

    contours, _ = cv.findContours(
        grayscale_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    sorted_contours = sorted(contours, key=cv.contourArea, reverse=True)

    if len(sorted_contours) < 2:
        return None

    second_largest_contour_idx = next(
        i for i, c in enumerate(contours) if
        cv.contourArea(c) == cv.contourArea(sorted_contours[1])
    )

    second_largest_contour = contours[second_largest_contour_idx]

    child_contours = [
        i for i, c in enumerate(contours)
        if i != second_largest_contour_idx and
        cv.pointPolygonTest(second_largest_contour,
                            tuple(map(int, c[0][0])),
                            False) >= 0
    ]

    if not child_contours:
        return None

    child_index = max(
        child_contours, key=lambda i: cv.contourArea(contours[i]))

    max_size = contours[child_index][2][0][0] - \
        contours[child_index][0][0][0]

    tile_size = max_size + tile_padding

    x, y, w, h = cv.boundingRect(contours[second_largest_contour_idx])

    x += field_padding
    y += field_padding
    w -= field_padding
    h -= field_padding

    x_cords = [i + x + x_start for i in range(0, w, tile_size)]
    y_cords = [i + y + y_start for i in range(0, h, tile_size)]

    return x_cords, y_cords


def classify_tile(tile: MatLike) -> str:
    unique_colors = np.unique(tile.reshape(-1, tile.shape[2]), axis=0)
    is_red = is_five = is_black = False

    for unique_color in unique_colors:
        if cv.inRange(unique_color, np.array([210, 0, 0], dtype=np.uint8),
                      np.array([255, 30, 30], dtype=np.uint8)).all():
            return "1"
        if cv.inRange(unique_color, np.array([0, 90, 0], dtype=np.uint8),
                      np.array([30, 140, 30], dtype=np.uint8)).all():
            return "2"
        if cv.inRange(unique_color, np.array([90, 0, 0], dtype=np.uint8),
                      np.array([140, 30, 30], dtype=np.uint8)).all():
            return "4"
        if cv.inRange(unique_color, np.array([50, 50, 0], dtype=np.uint8),
                      np.array([170, 170, 40], dtype=np.uint8)).all():
            return "6"
        if cv.inRange(unique_color, np.array([0, 0, 210], dtype=np.uint8),
                      np.array([30, 30, 255], dtype=np.uint8)).all():
            is_red = True
        elif cv.inRange(unique_color, np.array([0, 0, 50], dtype=np.uint8),
                        np.array([40, 40, 170], dtype=np.uint8)).all():
            is_five = True
        elif cv.inRange(unique_color, np.array([0, 0, 0], dtype=np.uint8),
                        np.array([50, 50, 50], dtype=np.uint8)).all():
            is_black = True
    if is_black and is_red:
        return "F"
    if is_black:
        return "7"
    if is_red:
        return "3"
    if is_five:
        return "5"

    total_pixels = tile.shape[0] * tile.shape[1]

    white_mask = cv.inRange(tile, np.array([230, 230, 230], dtype=np.uint8),
                            np.array([255, 255, 255], dtype=np.uint8))
    if cv.countNonZero(white_mask) / total_pixels > 0.1:
        return "?"

    gray_mask = cv.inRange(tile, np.array([70, 70, 70], dtype=np.uint8),
                           np.array([180, 180, 180], dtype=np.uint8))
    if cv.countNonZero(gray_mask) / total_pixels > 0.5:
        return "8"

    return "0"


def parse_game_state(image: MatLike,
                     field_grid: GridCoords) -> list[str]:
    game_state = []
    x_cords, y_cords = field_grid
    tile_size = y_cords[1] - y_cords[0]
    for y in y_cords[:-1]:
        line = ""
        for x in x_cords[:-1]:
            tile = image[y:y + tile_size, x:x + tile_size]
            tile_symbol = classify_tile(tile)
            line += tile_symbol
        game_state.append(line)
    return game_state


def get_neighbors(tile_index: Position,
                  minefield: list[str]) -> list[Position]:
    y, x = tile_index
    return [(y + i, x + j) for i, j in VICINITY if
            0 <= y + i < len(minefield) and
            0 <= x + j < len(minefield[0])]
