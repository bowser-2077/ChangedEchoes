import pygame
from constants import *
from door import Door

TILE_TEXTURES = {
    WALL:          "wall",
    GROUND:        "ground",
    GLASS:         "glass",
    LIB_WALL:      "lib_wall",
    LIB_GROUND:    "lib_ground",
    INF_WALL:      "inf_wall",
    INF_GROUND:    "inf_ground",
    INF_WALLTOP1:  "inf_walltop1",
    INF_WALLTOP2:  "inf_walltop2",
    INF_GROUNDTOP: "inf_groundtop",
    PAWS_GROUND:   "paws_ground",
    GOO_WALL:      "goo_wall",
    GOO_GROUND:    "goo_ground",
    VOID:          None,
}


class Room:
    def __init__(self, data, assets):
        self.name       = data["name"]
        self.message    = data.get("message", "")
        self.goo_room   = data.get("goo_room", False)
        self.tiles      = data["tiles"]
        self.exits      = data["exits"]
        self.pipe_decos = data.get("pipe_decos", [])
        self.assets     = assets
        self.map_cols   = len(self.tiles[0])
        self.map_rows   = len(self.tiles)
        self.map_w      = self.map_cols * TILE_SIZE
        self.map_h      = self.map_rows * TILE_SIZE
        self._solid     = self._build_solid_rects()
        self.doors      = [
            Door(d["col"], d["target"], d["spawn"])
            for d in data.get("doors", [])
        ]

    def _build_solid_rects(self):
        rects = []
        for r, row in enumerate(self.tiles):
            for c, tid in enumerate(row):
                if tid not in SOLID_TILES:
                    continue
                # Row 2 is the decorative lower-wall band — not a collision barrier.
                # Only rows 0–1 (void/wall ceiling) and rows 5+ (void floor) block movement.
                if r == 2:
                    continue
                rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE,
                                         TILE_SIZE, TILE_SIZE))
        return rects

    def get_solid_rects(self):
        return [(r, 0) for r in self._solid]

    # camera_x: world pixel of the left edge of the screen
    def get_camera_x(self, player_rect):
        cx = player_rect.centerx - SCREEN_W // 2
        return max(0, min(cx, self.map_w - SCREEN_W))

    def check_exit(self, player_rect):
        return None  # transitions now handled by doors

    def update_doors(self, player_rect):
        """Update all doors. Returns first triggered exit dict or None."""
        for door in self.doors:
            result = door.update(player_rect)
            if result:
                return result
        return None

    def draw(self, surface, camera_x):
        # only draw tiles that are on screen
        first_col = max(0, camera_x // TILE_SIZE)
        last_col  = min(self.map_cols, (camera_x + SCREEN_W) // TILE_SIZE + 2)

        for r, row in enumerate(self.tiles):
            for c in range(first_col, last_col):
                tid = row[c]
                sx  = c * TILE_SIZE - camera_x
                sy  = r * TILE_SIZE + MAP_OFFSET_Y
                if tid == VOID:
                    pygame.draw.rect(surface, (0, 0, 0),
                                     (sx, sy, TILE_SIZE, TILE_SIZE))
                    continue
                if tid == EMPTY:
                    continue
                key = TILE_TEXTURES.get(tid)
                if key:
                    surface.blit(self.assets[key], (sx, sy))

        self._draw_decos(surface, camera_x)
        for door in self.doors:
            door.draw(surface, self.assets, camera_x)

    def _draw_decos(self, surface, camera_x):
        # Pipe rail: horizontal bar drawn across the bottom of row 2 (wall face)
        # Wall face bottom y = row 3 start → row2_bottom = 3 * TILE_SIZE
        wall_face_y = 3 * TILE_SIZE + MAP_OFFSET_Y   # top of the floor = bottom of wall face
        # Draw a thin horizontal divider line across the whole wall bottom (like the screenshot)
        line_sx  = 0 - camera_x
        line_ex  = self.map_w - camera_x
        line_y   = wall_face_y - 4
        pygame.draw.line(surface, (50, 50, 55), (line_sx, line_y), (line_ex, line_y), 2)

        for col, deco_type in self.pipe_decos:
            wx  = col * TILE_SIZE          # world x
            sx  = wx  - camera_x           # screen x
            if sx + TILE_SIZE < 0 or sx > SCREEN_W:
                continue

            if deco_type == "pipe_h":
                self._draw_pipe_h(surface, sx, wall_face_y)
            elif deco_type == "glass":
                # small glass panel on wall
                self._draw_glass_panel(surface, sx, wall_face_y - TILE_SIZE)
            elif deco_type == "lib_shelf":
                surface.blit(self.assets["lib_wall"], (sx, wall_face_y - TILE_SIZE))
            elif deco_type == "inf_drip":
                surface.blit(self.assets["inf_walltop1"], (sx, wall_face_y - TILE_SIZE // 2))
            elif deco_type == "paws":
                surface.blit(self.assets["paws_ground"], (sx, wall_face_y - TILE_SIZE // 2))

    def _draw_pipe_h(self, surface, sx, wall_face_y):
        # horizontal pipe rail: a rounded rect fixed to the wall face
        pipe_h  = 10
        pipe_w  = TILE_SIZE + 12
        pipe_y  = wall_face_y - pipe_h - 6
        pipe_x  = sx - 6
        bar_col = (200, 200, 205)
        shad    = (120, 120, 128)
        pygame.draw.rect(surface, shad,    (pipe_x + 2, pipe_y + 3, pipe_w, pipe_h), border_radius=4)
        pygame.draw.rect(surface, bar_col, (pipe_x,     pipe_y,     pipe_w, pipe_h), border_radius=4)
        pygame.draw.rect(surface, (240, 240, 245), (pipe_x, pipe_y, pipe_w, 3), border_radius=4)
        # end caps
        cap_col = (170, 170, 178)
        pygame.draw.rect(surface, cap_col, (pipe_x - 4,          pipe_y - 2, 6, pipe_h + 4), border_radius=2)
        pygame.draw.rect(surface, cap_col, (pipe_x + pipe_w - 2, pipe_y - 2, 6, pipe_h + 4), border_radius=2)

    def _draw_glass_panel(self, surface, sx, top_y):
        pw, ph = TILE_SIZE - 8, TILE_SIZE - 8
        px, py = sx + 4, top_y + 4
        pygame.draw.rect(surface, (180, 210, 230, 120), (px, py, pw, ph))
        pygame.draw.rect(surface, (140, 170, 200), (px, py, pw, ph), 2)
        pygame.draw.line(surface, (200, 225, 240), (px + 4, py + 4), (px + 4, py + ph - 4), 1)
