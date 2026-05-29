import pygame
from constants import TILE_SIZE, SOLID_TILES, TARGET_FPS

SPEED    = 3.0             # pixels per frame at TARGET_FPS (60)
ANIM_FPS = 10.0            # animation frames per second


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, assets):
        super().__init__()
        # animation state
        self._frames   = {
            "right": assets["walk_right"],
            "left":  assets["walk_left"],
            "front": assets["walk_front"],
            "back":  assets["walk_back"],
        }
        self._dir       = "right"   # last facing direction
        self._frame_idx = 0
        self._anim_acc  = 0.0       # time accumulator in seconds
        self._moving    = False

        self.image = self._frames[self._dir][0]
        self.rect  = self.image.get_rect(topleft=(x, y))
        self.vel   = pygame.math.Vector2(0, 0)
        self.pos   = pygame.math.Vector2(x, y)

    def handle_input(self, dt=None):
        """dt unused here — velocity is in px/frame units, scaled in move()."""
        keys = pygame.key.get_pressed()
        self.vel.x = 0
        self.vel.y = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.vel.x = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.vel.x =  SPEED
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.vel.y = -SPEED
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.vel.y =  SPEED

        # pick facing direction (horizontal takes priority)
        self._moving = self.vel.x != 0 or self.vel.y != 0
        if   self.vel.x > 0: self._dir = "right"
        elif self.vel.x < 0: self._dir = "left"
        elif self.vel.y < 0: self._dir = "back"
        elif self.vel.y > 0: self._dir = "front"

    def move(self, tilemap, dt=None):
        # scale velocity so movement is frame-rate independent
        scale = (dt * TARGET_FPS) if dt is not None else 1.0
        self.pos.x += self.vel.x * scale
        self.rect.x = round(self.pos.x)
        self._resolve_x(tilemap)

        self.pos.y += self.vel.y * scale
        self.rect.y = round(self.pos.y)
        self._resolve_y(tilemap)

    def update_anim(self, dt=None):
        frames = self._frames[self._dir]
        if self._moving:
            self._anim_acc += (dt if dt is not None else 1.0 / TARGET_FPS)
            frame_dur = 1.0 / ANIM_FPS
            while self._anim_acc >= frame_dur:
                self._anim_acc -= frame_dur
                self._frame_idx = (self._frame_idx + 1) % len(frames)
        else:
            self._frame_idx = 0
            self._anim_acc  = 0.0
        self.image = frames[self._frame_idx]

    def _resolve_x(self, tilemap):
        for tile_rect, _ in tilemap.get_solid_rects():
            if self.rect.colliderect(tile_rect):
                if self.vel.x > 0:
                    self.rect.right = tile_rect.left
                elif self.vel.x < 0:
                    self.rect.left = tile_rect.right
        self.pos.x = self.rect.x

    def _resolve_y(self, tilemap):
        for tile_rect, _ in tilemap.get_solid_rects():
            if self.rect.colliderect(tile_rect):
                if self.vel.y > 0:
                    self.rect.bottom = tile_rect.top
                elif self.vel.y < 0:
                    self.rect.top = tile_rect.bottom
        self.pos.y = self.rect.y

    def world_rect(self):
        return self.rect
