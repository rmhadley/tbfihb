from typing import Tuple

import numpy as np  # type: ignore

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # Unicode codepoint.
        ("fg", "3B"),  # 3 unsigned bytes, for RGB colors.
        ("bg", "3B"),
    ]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("walkable", np.bool),  # True if this tile can be walked over.
        ("transparent", np.bool),  # True if this tile doesn't block FOV.
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light", graphic_dt),  # Graphics for when the tile is in FOV.
        ("dark1", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light1", graphic_dt),  # Graphics for when the tile is in FOV.
        ("dark2", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light2", graphic_dt),  # Graphics for when the tile is in FOV.
        ("dark3", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light3", graphic_dt),  # Graphics for when the tile is in FOV.
        ("dark4", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light4", graphic_dt),  # Graphics for when the tile is in FOV.
    ]
)


def new_tile(
    *,  # Enforce the use of keywords, so that parameter order doesn't matter.
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    dark1: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light1: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    dark2: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light2: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    dark3: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light3: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    dark4: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light4: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light, dark1, light1, dark2, light2, dark3, light3, dark4, light4), dtype=tile_dt)

# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)
ocean = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (100, 100, 100), (0, 0, 0)),
    light=(ord("."), (10, 92, 14), (66, 230, 245)),
    dark1=(ord("."), (100, 100, 100), (0, 0, 0)),
    light1=(ord("."), (23, 44, 120), (23, 44, 120)),
    dark2=(ord("."), (100, 100, 100), (0, 0, 0)),
    light2=(ord("."), (23, 23, 120), (23, 23, 120)),
    dark3=(ord("."), (100, 100, 100), (0, 0, 0)),
    light3=(ord("."), (42, 23, 120), (42, 23, 120)),
    dark4=(ord("."), (100, 100, 100), (0, 0, 0)),
    light4=(ord("."), (24, 8, 89), (24, 8, 89)),
)

wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("#"), (100, 100, 100), (0, 0, 0)),
    light=(ord("#"), (200, 200, 200), (0, 0, 0)),
    dark1=(ord("#"), (100, 100, 100), (0, 0, 0)),
    light1=(ord("#"), (200, 200, 200), (0, 0, 0)),
    dark2=(ord("#"), (100, 100, 100), (0, 0, 0)),
    light2=(ord("#"), (200, 200, 200), (0, 0, 0)),
    dark3=(ord("#"), (100, 100, 100), (0, 0, 0)),
    light3=(ord("#"), (200, 200, 200), (0, 0, 0)),
    dark4=(ord("#"), (100, 100, 100), (0, 0, 0)),
    light4=(ord("#"), (200, 200, 200), (0, 0, 0)),
)
down_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light=(ord(">"), (255, 255, 255), (200, 180, 50)),
    dark1=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light1=(ord(">"), (255, 255, 255), (200, 180, 50)),
    dark2=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light2=(ord(">"), (255, 255, 255), (200, 180, 50)),
    dark3=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light3=(ord(">"), (255, 255, 255), (200, 180, 50)),
    dark4=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light4=(ord(">"), (255, 255, 255), (200, 180, 50)),
)
up_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("<"), (0, 0, 100), (50, 50, 150)),
    light=(ord("<"), (255, 255, 255), (200, 180, 50)),
    dark1=(ord("<"), (0, 0, 100), (50, 50, 150)),
    light1=(ord("<"), (255, 255, 255), (200, 180, 50)),
    dark2=(ord("<"), (0, 0, 100), (50, 50, 150)),
    light2=(ord("<"), (255, 255, 255), (200, 180, 50)),
    dark3=(ord("<"), (0, 0, 100), (50, 50, 150)),
    light3=(ord("<"), (255, 255, 255), (200, 180, 50)),
    dark4=(ord("<"), (0, 0, 100), (50, 50, 150)),
    light4=(ord("<"), (255, 255, 255), (200, 180, 50)),
)
