from __future__ import annotations

from importlib import resources

import pygame


ASSET_PACKAGE = "miniworlds_robot.assets.kenney_robot_pack"

ROBOT_ASSETS = {
    "standard": "robot_redBody.png",
    "red": "robot_redBody.png",
    "blue": "robot_blueBody.png",
    "green": "robot_greenBody.png",
    "yellow": "robot_yellowBody.png",
}


def _load_asset_surface(filename: str) -> pygame.Surface:
    surface = pygame.image.load(asset_path(filename))
    if pygame.display.get_surface():
        surface = surface.convert_alpha()
    return surface


def asset_path(filename: str) -> str:
    return str(resources.files(ASSET_PACKAGE).joinpath(filename))


def robot_asset_path(name: str) -> str:
    return asset_path(ROBOT_ASSETS.get(name, "robot_redBody.png"))


def make_robot_surface(name: str, tile_size: int) -> pygame.Surface:
    surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
    body = _load_asset_surface(ROBOT_ASSETS.get(name, "robot_redBody.png"))
    tracks = _load_asset_surface("tracks_short1.png")
    body_width = int(tile_size * 0.94)
    body_height = int(body.get_height() * body_width / body.get_width())
    body = pygame.transform.smoothscale(body, (body_width, body_height))
    tracks_width = int(tile_size * 0.70)
    tracks_height = int(tracks.get_height() * tracks_width / tracks.get_width())
    tracks = pygame.transform.smoothscale(tracks, (tracks_width, tracks_height))
    tracks_rect = tracks.get_rect(
        center=(tile_size // 2, int(tile_size * 0.78))
    )
    body_rect = body.get_rect(
        center=(tile_size // 2, int(tile_size * 0.43))
    )
    surface.blit(tracks, tracks_rect)
    surface.blit(body, body_rect)
    return surface


def make_world_background(width: int, height: int, tile_size: int) -> pygame.Surface:
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((139, 178, 110, 255))
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    track_long = pygame.transform.smoothscale(
        _load_asset_surface("track_long.png"),
        (int(tile_size * 0.70), int(tile_size * 0.34)),
    )
    track_short = pygame.transform.smoothscale(
        _load_asset_surface("track_short.png"),
        (int(tile_size * 0.44), int(tile_size * 0.34)),
    )
    track_long.set_alpha(42)
    track_short.set_alpha(36)
    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            tile_index = x // tile_size + y // tile_size
            rect = pygame.Rect(x, y, tile_size, tile_size)
            if tile_index % 3 == 0:
                pygame.draw.circle(
                    overlay,
                    (171, 205, 132, 58),
                    (
                        int(rect.centerx - tile_size * 0.16),
                        int(rect.centery - tile_size * 0.12),
                    ),
                    max(2, tile_size // 7),
                )
            if tile_index % 5 == 2:
                pygame.draw.circle(
                    overlay,
                    (91, 134, 79, 44),
                    (
                        int(rect.centerx + tile_size * 0.18),
                        int(rect.centery + tile_size * 0.14),
                    ),
                    max(2, tile_size // 9),
                )
            if tile_index % 6 == 0:
                track = track_long
            elif tile_index % 6 == 3:
                track = track_short
            else:
                continue
            track_rect = track.get_rect(center=rect.center)
            overlay.blit(track, track_rect)
    surface.blit(overlay, (0, 0))
    return surface


def make_leaf_surface(size: int) -> pygame.Surface:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.ellipse(
        surface,
        (87, 164, 72, 255),
        pygame.Rect(size * 0.20, size * 0.22, size * 0.60, size * 0.42),
    )
    pygame.draw.line(
        surface,
        (45, 110, 48, 255),
        (size * 0.28, size * 0.54),
        (size * 0.72, size * 0.32),
        max(1, size // 18),
    )
    return surface


def make_tree_surface(size: int) -> pygame.Surface:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    trunk = pygame.Rect(size * 0.42, size * 0.52, size * 0.16, size * 0.28)
    pygame.draw.rect(surface, (112, 78, 45, 255), trunk)
    pygame.draw.circle(
        surface,
        (42, 126, 66, 255),
        (size // 2, int(size * 0.38)),
        int(size * 0.25),
    )
    pygame.draw.circle(
        surface,
        (57, 148, 75, 255),
        (int(size * 0.38), int(size * 0.45)),
        int(size * 0.18),
    )
    pygame.draw.circle(
        surface,
        (33, 105, 58, 255),
        (int(size * 0.62), int(size * 0.46)),
        int(size * 0.19),
    )
    return surface


def make_mushroom_surface(size: int) -> pygame.Surface:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    stem = pygame.Rect(size * 0.40, size * 0.43, size * 0.20, size * 0.30)
    pygame.draw.rect(
        surface,
        (236, 220, 185, 255),
        stem,
        border_radius=max(1, size // 10),
    )
    cap = pygame.Rect(size * 0.22, size * 0.22, size * 0.56, size * 0.34)
    pygame.draw.ellipse(surface, (196, 50, 54, 255), cap)
    pygame.draw.circle(
        surface,
        (255, 238, 214, 255),
        (int(size * 0.40), int(size * 0.34)),
        max(1, size // 16),
    )
    pygame.draw.circle(
        surface,
        (255, 238, 214, 255),
        (int(size * 0.58), int(size * 0.31)),
        max(1, size // 18),
    )
    return surface
