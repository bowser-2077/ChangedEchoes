import pygame
import sys
import argparse
import logging
from constants import *
import assets as asset_loader
from player import Player
from room import Room
from room_data import ROOMS

# ── CLI args ──────────────────────────────────────────────────────────────
_parser = argparse.ArgumentParser(description="Changed: Echoes")
_parser.add_argument("--debug", action="store_true", help="Enable debug mode (windowed, verbose logs)")
_args = _parser.parse_args()

DEBUG = _args.debug

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("changed")

if DEBUG:
    log.info("Debug mode ON — windowed, verbose logging enabled")

FADE_SPEED = 6

# ── Game states ───────────────────────────────────────────────────────────
STATE_INTRO    = "intro"
STATE_WARNING  = "warning"
STATE_MENU     = "menu"
STATE_SETTINGS = "settings"
STATE_PLAYING  = "playing"
STATE_DEAD     = "dead"

MENU_ITEMS     = ["Play", "Settings", "Quit"]

# Intro timing (frames at 60 fps)
INTRO_FADE_IN  = 90
INTRO_HOLD     = 120
INTRO_FADE_OUT = 90
INTRO_TOTAL    = INTRO_FADE_IN + INTRO_HOLD + INTRO_FADE_OUT

# ── Settings definition ───────────────────────────────────────────────────
# Each entry: (label, type, key, values)
#   type "toggle"  → values = [False, True]
#   type "choice"  → values = list of display strings, stored as index
FPS_OPTIONS   = [60, 75, 120, 144, 165, 240]
FPS_LABELS    = ["60 Hz", "75 Hz", "120 Hz", "144 Hz", "165 Hz", "240 Hz"]

SETTINGS_DEFS = [
    ("Text Speed",   "choice", "text_speed",   ["Slow", "Normal", "Fast"]),
    ("Music Volume", "choice", "music_vol",    ["Off", "25%", "50%", "75%", "100%"]),
    ("SFX Volume",   "choice", "sfx_vol",      ["Off", "25%", "50%", "75%", "100%"]),
    ("Frame Rate",   "choice", "fps_idx",      FPS_LABELS),
    ("VSync",        "toggle", "vsync",        [False, True]),
    ("Fullscreen",   "toggle", "fullscreen",   [False, True]),
]

COL1  = (230, 220, 180)   # selected text
COL2  = (120, 115, 100)   # unselected text
COL3  = (80,  75,  60)    # decorative / dim
COL4  = (55,  52,  45)    # hint text
COLW  = (200, 195, 170)   # value highlight


def _dline(surface, color, x1, y1, x2, y2, w=1):
    pygame.draw.line(surface, color, (x1, y1), (x2, y2), w)


class Game:
    def __init__(self):
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.clock  = pygame.time.Clock()
        pygame.mixer.set_num_channels(8)
        # detect native monitor refresh rate
        info = pygame.display.Info()
        native_hz = getattr(info, 'refresh_rate', 0) or 60
        log.info(f"Display info: {info.current_w}x{info.current_h}, refresh={native_hz} Hz")
        best = max((f for f in FPS_OPTIONS if f <= native_hz), default=60)
        self._target_fps = best
        self._vsync      = not DEBUG   # no vsync in debug (easier to measure raw FPS)
        # settings must exist before _make_display reads fullscreen key
        self.settings    = {"fullscreen": 0 if DEBUG else 1,
                            "fps_idx": 0, "vsync": 0 if DEBUG else 1,
                            "text_speed": 1, "music_vol": 4, "sfx_vol": 4}
        self.screen = self._make_display(vsync=self._vsync)
        log.info(f"Window created: {SCREEN_W}x{SCREEN_H}, fullscreen={'no' if DEBUG else 'yes'}, vsync={self._vsync}, target={self._target_fps} Hz")

        self.font_big    = pygame.font.SysFont("monospace", 26, bold=True)
        self.font_menu   = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_sub    = pygame.font.SysFont("monospace", 14)
        self.font_hud    = pygame.font.SysFont("monospace", 13, bold=True)
        self.font_msg    = pygame.font.SysFont("monospace", 12)
        self.font_warn   = pygame.font.SysFont("monospace", 13)

        log.info("Loading assets...")
        self.assets = asset_loader.load_all()
        log.info(f"Assets loaded: {len(self.assets)} keys")
        self.rooms  = [Room(d, self.assets) for d in ROOMS]
        log.info(f"Rooms loaded: {len(self.rooms)}")

        # ── logo image (scaled to fit nicely on screen) ──
        raw_logo = pygame.image.load(
            __import__("os").path.join(
                __import__("os").path.dirname(__file__), "textures", "intrologo.png"
            )
        ).convert_alpha()
        lw, lh   = raw_logo.get_size()
        max_w, max_h = int(SCREEN_W * 0.7), int(SCREEN_H * 0.42)
        scale    = min(max_w / lw, max_h / lh)
        self.logo_img = pygame.transform.smoothscale(
            raw_logo, (round(lw * scale), round(lh * scale))
        )

        # ── settings state — update fps_idx to match detected refresh rate ──
        default_fps_idx = FPS_OPTIONS.index(self._target_fps) if self._target_fps in FPS_OPTIONS else 0
        self.settings["fps_idx"] = default_fps_idx
        self.settings_index = 0   # currently highlighted setting row

        # ── intro state ──
        self.state      = STATE_INTRO
        self.intro_tick = 0

        # ── menu state ──
        self.menu_index = 0

        # ── warning state ──
        self.warn_accepted = False

        # ── fade ──
        self.fade_surf  = pygame.Surface((SCREEN_W, SCREEN_H))
        self.fade_surf.fill((0, 0, 0))
        self.fade_alpha = 0
        self.fading_out = False
        self.next_room  = None
        self.next_spawn = None

        # ── gameplay ──
        self.room     = None
        self.room_idx = None
        self.player   = None
        self.msg_text = ""
        self.msg_timer= 0
        self.camera_x = 0
        self.sanity   = float(SANITY_MAX)
        self.dead_timer = 0    # frames to show death screen before returning to menu
        # goo overlay surface for sanity drain visual
        self._goo_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        # ── sound state ──
        self._ambient_ch      = pygame.mixer.Channel(0)
        self._ambient_playing = None   # key of currently looping ambient
        self._footstep_timer  = 0
        self._footstep_period = 22     # frames between footstep sounds
        self._sanity_low_playing = False

    # ── helpers ───────────────────────────────────────────────────────────

    def _load_room(self, idx, spawn):
        log.debug(f"Loading room {idx}: '{self.rooms[idx].name}' | spawn={spawn} | goo={self.rooms[idx].goo_room}")
        self.room_idx  = idx
        self.room      = self.rooms[idx]
        self.player    = Player(*spawn, self.assets)
        self.msg_text  = self.room.message
        self.msg_timer = 270

    def _play_sfx(self, key):
        """Play a one-shot sfx by key, silently ignoring missing sounds."""
        snd = self.assets["sfx"].get(key)
        if snd:
            snd.play()

    def _set_ambient(self, key):
        """Switch the looping ambient track."""
        if self._ambient_playing == key:
            return
        snd = self.assets["sfx"].get(key)
        self._ambient_ch.stop()
        if snd:
            self._ambient_ch.play(snd, loops=-1)
        self._ambient_playing = key

    def _start_game(self):
        log.info("Game started")
        self._load_room(0, spawn=(2 * TILE_SIZE, 2 * TILE_SIZE))
        self.state      = STATE_PLAYING
        self.fade_alpha = 255
        self.camera_x   = 0
        self.sanity     = float(SANITY_MAX)
        self._ambient_playing = None
        self._sanity_low_playing = False

    def _make_display(self, vsync=True):
        fs = bool(self.settings.get("fullscreen", 1))
        flag = pygame.FULLSCREEN if fs else 0
        try:
            return pygame.display.set_mode((SCREEN_W, SCREEN_H), flag, vsync=1 if vsync else 0)
        except Exception:
            return pygame.display.set_mode((SCREEN_W, SCREEN_H), flag)

    def _set_fullscreen(self, on):
        self.screen = self._make_display(vsync=self._vsync)

    def _apply_display_settings(self):
        fps_idx = self.settings["fps_idx"]
        self._target_fps = FPS_OPTIONS[fps_idx]
        self._vsync      = bool([False, True][self.settings["vsync"]])
        self.screen      = self._make_display(vsync=self._vsync)

    # ── main loop ─────────────────────────────────────────────────────────

    def run(self):
        self._dbg_fps_acc = 0.0
        self._dbg_fps_frames = 0
        self._dbg_fps_display = 0
        while True:
            dt = self.clock.tick(self._target_fps) / 1000.0
            dt = min(dt, 0.05)   # clamp to avoid spiral of death on lag spike
            if DEBUG:
                self._dbg_fps_acc    += dt
                self._dbg_fps_frames += 1
                if self._dbg_fps_acc >= 0.5:
                    self._dbg_fps_display = self._dbg_fps_frames / self._dbg_fps_acc
                    self._dbg_fps_acc = self._dbg_fps_frames = 0
            self._events()
            self._update(dt)
            self._draw()

    # ── events ────────────────────────────────────────────────────────────

    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if ev.type == pygame.KEYDOWN:
                if self.state == STATE_INTRO:
                    # any key skips intro → warning
                    self.state = STATE_WARNING

                elif self.state == STATE_WARNING:
                    if ev.key in (pygame.K_y, pygame.K_RETURN):
                        self.warn_accepted = True
                        self.state = STATE_MENU
                    elif ev.key in (pygame.K_n, pygame.K_ESCAPE):
                        pygame.quit(); sys.exit()

                elif self.state == STATE_MENU:
                    self._menu_key(ev.key)

                elif self.state == STATE_SETTINGS:
                    self._settings_key(ev.key)

                elif self.state == STATE_PLAYING:
                    if ev.key == pygame.K_ESCAPE:
                        self.state      = STATE_MENU
                        self.fade_alpha = 0
                        self._set_ambient(None)
                elif self.state == STATE_DEAD:
                    pass   # any input handled by timer

    def _menu_key(self, key):
        n = len(MENU_ITEMS)
        if key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % n
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % n
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            choice = MENU_ITEMS[self.menu_index]
            if choice == "Play":
                self._start_game()
            elif choice == "Settings":
                self.settings_index = 0
                self.state = STATE_SETTINGS
            elif choice == "Quit":
                pygame.quit(); sys.exit()

    def _settings_key(self, key):
        n = len(SETTINGS_DEFS)
        if key in (pygame.K_UP, pygame.K_w):
            self.settings_index = (self.settings_index - 1) % n
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.settings_index = (self.settings_index + 1) % n
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._settings_change(-1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._settings_change(+1)
        elif key == pygame.K_ESCAPE:
            self.state = STATE_MENU

    def _settings_change(self, delta):
        _, stype, skey, svals = SETTINGS_DEFS[self.settings_index]
        cur = self.settings[skey]
        nv  = (cur + delta) % len(svals)
        self.settings[skey] = nv
        if skey in ("fullscreen", "fps_idx", "vsync"):
            self._apply_display_settings()

    # ── update ────────────────────────────────────────────────────────────

    def _update(self, dt=1/60):
        if self.state == STATE_INTRO:
            self.intro_tick += 1
            if self.intro_tick >= INTRO_TOTAL:
                self.state = STATE_WARNING
            return

        if self.state == STATE_DEAD:
            self.dead_timer -= dt
            if self.dead_timer <= 0:
                self._ambient_ch.stop()
                self._ambient_playing = None
                self.state = STATE_MENU
                self.menu_index = 0
            return

        if self.state in (STATE_WARNING, STATE_MENU, STATE_SETTINGS):
            return

        if self.fading_out:
            self.fade_alpha = min(255, self.fade_alpha + FADE_SPEED)
            if self.fade_alpha >= 255:
                self._load_room(self.next_room, self.next_spawn)
                self.camera_x = self.room.get_camera_x(self.player.world_rect())
                px = self.player.rect.centerx
                for door in self.room.doors:
                    if abs(door.world_rect.centerx - px) < TILE_SIZE * 3:
                        door.start_closing()
                        break
                self.fading_out = False
            return

        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - FADE_SPEED)

        self.player.handle_input(dt)
        self.player.move(self.room, dt)
        self.player.update_anim(dt)
        self.camera_x = self.room.get_camera_x(self.player.world_rect())

        # ── ambient ──
        if self.room.goo_room:
            self._set_ambient("ambiant_goo")
        else:
            self._set_ambient("ambiant_normal")

        # ── footsteps ──
        moving = self.player.vel.length_squared() > 0
        if moving:
            self._footstep_timer -= dt
            if self._footstep_timer <= 0:
                self._footstep_timer = self._footstep_period / TARGET_FPS
                key = "footstep_goo" if self.room.goo_room else "footstep_normal"
                self._play_sfx(key)
        else:
            self._footstep_timer = 0

        # ── sanity ──
        if self.room.goo_room:
            self.sanity = max(0, self.sanity - SANITY_DRAIN_RATE * dt)
            if self.sanity <= 0:
                log.info("Player died — sanity reached 0")
                self._set_ambient(None)
                self._play_sfx("player_death")
                self.state      = STATE_DEAD
                self.dead_timer = 4.0   # 4 seconds
                return
            if self.sanity < SANITY_MAX * 0.25 and not self._sanity_low_playing:
                self._play_sfx("sanity_low")
                self._sanity_low_playing = True
            elif self.sanity >= SANITY_MAX * 0.25:
                self._sanity_low_playing = False
        else:
            self.sanity = min(SANITY_MAX, self.sanity + SANITY_REGEN_RATE * dt)
            self._sanity_low_playing = False

        if self.msg_timer > 0:
            self.msg_timer -= 1

        door_exit = self.room.update_doors(self.player.world_rect())
        if door_exit and not self.fading_out:
            log.debug(f"Door triggered → room {door_exit['target']}, spawn={door_exit['spawn']}")
            self.fading_out = True
            self.next_room  = door_exit["target"]
            self.next_spawn = door_exit["spawn"]
            self.fade_alpha = 0
            self._play_sfx("room_enter")

    # ── draw ──────────────────────────────────────────────────────────────

    def _draw(self):
        if   self.state == STATE_INTRO:    self._draw_intro()
        elif self.state == STATE_WARNING:  self._draw_warning()
        elif self.state == STATE_MENU:     self._draw_menu()
        elif self.state == STATE_SETTINGS: self._draw_settings()
        elif self.state == STATE_DEAD:     self._draw_dead()
        else:                              self._draw_game()
        pygame.display.flip()

    # ── intro ─────────────────────────────────────────────────────────────

    def _draw_intro(self):
        t = self.intro_tick
        if t < INTRO_FADE_IN:
            a = int(255 * t / INTRO_FADE_IN)
        elif t < INTRO_FADE_IN + INTRO_HOLD:
            a = 255
        else:
            a = int(255 * (1 - (t - INTRO_FADE_IN - INTRO_HOLD) / INTRO_FADE_OUT))

        self.screen.fill((0, 0, 0))
        logo_r = self.logo_img.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
        tmp = self.logo_img.copy()
        tmp.set_alpha(a)
        self.screen.blit(tmp, logo_r)

        skip = self.font_warn.render("Press any key to skip", True, (60, 57, 50))
        skip.set_alpha(min(255, a))
        self.screen.blit(skip, skip.get_rect(centerx=SCREEN_W // 2, y=SCREEN_H - 36))

    # ── warning ───────────────────────────────────────────────────────────

    def _draw_warning(self):
        self.screen.fill((0, 0, 0))
        cx = SCREEN_W // 2
        cy = SCREEN_H // 2

        # box
        bw, bh = 680, 340
        bx, by = cx - bw // 2, cy - bh // 2
        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        box.fill((10, 8, 6, 230))
        self.screen.blit(box, (bx, by))
        pygame.draw.rect(self.screen, (140, 110, 60), (bx, by, bw, bh), 2)
        pygame.draw.rect(self.screen, (80, 60, 30),   (bx+3, by+3, bw-6, bh-6), 1)

        # title
        title = self.font_big.render("!  CONTENT WARNING  !", True, (220, 175, 80))
        self.screen.blit(title, title.get_rect(centerx=cx, y=by + 28))
        _dline(self.screen, (100, 78, 40), bx + 20, by + 68, bx + bw - 20, by + 68)

        # warning text
        lines = [
            "This game contains themes of body transformation",
            "and non-consensual species change (\"transfur\").",
            "",
            "It is a fan-made work inspired by the game  Changed",
            "by DragonSnow. Content is kept tasteful.",
            "",
            "By continuing, you confirm you are comfortable",
            "with these themes and are of appropriate age.",
            "",
        ]
        for i, line in enumerate(lines):
            col  = (200, 190, 160) if line else (0, 0, 0)
            surf = self.font_warn.render(line, True, col)
            self.screen.blit(surf, surf.get_rect(centerx=cx, y=by + 90 + i * 22))

        _dline(self.screen, (100, 78, 40), bx + 20, by + bh - 72, bx + bw - 20, by + bh - 72)

        # buttons
        accept = self.font_sub.render("[Y]  Accept  —  I understand", True, (130, 200, 120))
        refuse = self.font_sub.render("[N / Esc]  Decline  —  Quit", True, (200, 100, 100))
        self.screen.blit(accept, accept.get_rect(centerx=cx - 150, y=by + bh - 56))
        self.screen.blit(refuse, refuse.get_rect(centerx=cx + 150, y=by + bh - 56))

    # ── menu ──────────────────────────────────────────────────────────────

    def _draw_menu(self):
        self.screen.fill((0, 0, 0))
        cx = SCREEN_W // 2

        # logo image
        logo_r = self.logo_img.get_rect(centerx=cx, y=40)
        self.screen.blit(self.logo_img, logo_r)

        # divider
        div_y = logo_r.bottom + 18
        _dline(self.screen, COL3, cx - 200, div_y, cx + 200, div_y)

        # menu items
        item_y = div_y + 36
        for i, label in enumerate(MENU_ITEMS):
            sel   = (i == self.menu_index)
            color = COL1 if sel else COL2
            pre   = "> " if sel else "  "
            surf  = self.font_menu.render(pre + label, True, color)
            r     = surf.get_rect(centerx=cx, y=item_y + i * 48)
            self.screen.blit(surf, r)
            if sel:
                _dline(self.screen, COL3, r.left + 2, r.bottom + 3, r.right - 2, r.bottom + 3)

        hint = self.font_warn.render(
            "↑↓ / W S  Navigate     Enter  Confirm     Esc  Back to menu in-game",
            True, COL4)
        self.screen.blit(hint, hint.get_rect(centerx=cx, y=SCREEN_H - 28))

    # ── settings ──────────────────────────────────────────────────────────

    def _draw_settings(self):
        self.screen.fill((0, 0, 0))
        cx = SCREEN_W // 2

        # header
        header = self.font_big.render("S E T T I N G S", True, COL1)
        self.screen.blit(header, header.get_rect(centerx=cx, y=60))
        _dline(self.screen, COL3, cx - 220, 100, cx + 220, 100)

        row_h   = 60
        start_y = 130
        col_lbl = cx - 200
        col_val = cx + 80

        for i, (label, stype, skey, svals) in enumerate(SETTINGS_DEFS):
            sel    = (i == self.settings_index)
            y      = start_y + i * row_h
            lcolor = COL1 if sel else COL2
            cur    = self.settings[skey]

            # row highlight
            if sel:
                hl = pygame.Surface((SCREEN_W - 160, row_h - 8), pygame.SRCALPHA)
                hl.fill((255, 255, 255, 12))
                self.screen.blit(hl, (80, y - 4))
                pygame.draw.rect(self.screen, COL3,
                                 (80, y - 4, SCREEN_W - 160, row_h - 8), 1)

            # label
            lsurf = self.font_menu.render(("→ " if sel else "  ") + label, True, lcolor)
            self.screen.blit(lsurf, (col_lbl, y + 4))

            # value with < > arrows
            val_str = str(svals[cur])
            left_a  = self.font_sub.render("◄", True, COLW if sel else COL3)
            right_a = self.font_sub.render("►", True, COLW if sel else COL3)
            val_s   = self.font_sub.render(val_str, True, COLW if sel else COL2)

            self.screen.blit(left_a,  (col_val, y + 8))
            self.screen.blit(val_s,   (col_val + 24, y + 8))
            self.screen.blit(right_a, (col_val + 24 + val_s.get_width() + 8, y + 8))

        _dline(self.screen, COL3, cx - 220, start_y + len(SETTINGS_DEFS) * row_h + 4,
               cx + 220, start_y + len(SETTINGS_DEFS) * row_h + 4)

        hint = self.font_warn.render(
            "↑↓  Select     ◄►  Change value     Esc  Back", True, COL4)
        self.screen.blit(hint, hint.get_rect(centerx=cx, y=SCREEN_H - 28))

    # ── game ──────────────────────────────────────────────────────────────

    def _draw_dead(self):
        self.screen.fill((0, 0, 0))
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        # red vignette
        vign = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        vign.fill((60, 0, 0, 180))
        self.screen.blit(vign, (0, 0))
        t1 = self.font_big.render("CONSUMED", True, (200, 50, 50))
        t2 = self.font_warn.render("The goo took over. Dr. Chen is gone.", True, (160, 100, 100))
        t3 = self.font_warn.render("Returning to menu...", True, (100, 80, 80))
        self.screen.blit(t1, t1.get_rect(centerx=cx, centery=cy - 40))
        self.screen.blit(t2, t2.get_rect(centerx=cx, centery=cy + 10))
        self.screen.blit(t3, t3.get_rect(centerx=cx, centery=cy + 40))

    def _draw_game(self):
        self.screen.fill((0, 0, 0))
        self.room.draw(self.screen, self.camera_x)
        pr = self.player.rect
        self.screen.blit(self.player.image, (pr.x - self.camera_x, pr.y + MAP_OFFSET_Y))

        if DEBUG:
            self._draw_debug_overlay()

        # goo room tint — green-black vignette that intensifies as sanity drops
        if self.room.goo_room:
            danger = 1.0 - (self.sanity / SANITY_MAX)
            a = int(30 + danger * 120)
            self._goo_overlay.fill((0, 20, 0, a))
            self.screen.blit(self._goo_overlay, (0, 0))

        label = self.font_hud.render(self.room.name, True, (180, 180, 180))
        self.screen.blit(label, (10, 8))

        self._draw_sanity_bar()

        if self.msg_text and self.msg_timer > 0:
            self._draw_message(min(255, self.msg_timer * 3))

        if self.fade_alpha > 0:
            self.fade_surf.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surf, (0, 0))

    def _draw_sanity_bar(self):
        ratio = self.sanity / SANITY_MAX
        bx    = SCREEN_W - SANITY_BAR_W - 12
        by    = 10
        # background
        pygame.draw.rect(self.screen, (30, 30, 30), (bx - 1, by - 1, SANITY_BAR_W + 2, SANITY_BAR_H + 2))
        # fill — shifts red as sanity drops
        r = int(80 + (1 - ratio) * 160)
        g = int(ratio * 170)
        fill_w = int(SANITY_BAR_W * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, (r, g, 60), (bx, by, fill_w, SANITY_BAR_H))
        # border
        pygame.draw.rect(self.screen, (100, 100, 80), (bx - 1, by - 1, SANITY_BAR_W + 2, SANITY_BAR_H + 2), 1)
        # label
        lbl = self.font_hud.render("SANITY", True, (140, 135, 110))
        self.screen.blit(lbl, (bx - lbl.get_width() - 6, by))

    def _draw_message(self, alpha):
        lines  = self.msg_text.split("\n")
        pad    = 10
        line_h = 18
        box_w  = SCREEN_W - 40
        box_h  = len(lines) * line_h + pad * 2
        box_x  = 20
        box_y  = SCREEN_H - box_h - 16

        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, int(alpha * 0.72)))
        self.screen.blit(bg, (box_x, box_y))
        pygame.draw.rect(self.screen, (100, 100, 80),
                         pygame.Rect(box_x, box_y, box_w, box_h), 1)

        for i, line in enumerate(lines):
            col  = (230, 220, 190) if i == 0 else (190, 185, 165)
            surf = self.font_msg.render(line, True, col)
            self.screen.blit(surf, (box_x + pad, box_y + pad + i * line_h))


    def _draw_debug_overlay(self):
        pr   = self.player.rect
        cam  = self.camera_x
        lines = [
            f"FPS: {self._dbg_fps_display:.1f}  target={self._target_fps}",
            f"Room: {self.room_idx} '{self.room.name}'  goo={self.room.goo_room}",
            f"Player world: ({pr.x}, {pr.y})  cam_x={cam}",
            f"Sanity: {self.sanity:.1f}  Fade: {self.fade_alpha}",
            f"State: {self.state}  FadingOut: {self.fading_out}",
        ]
        y = MAP_OFFSET_Y + 4
        for line in lines:
            surf = self.font_hud.render(line, True, (0, 255, 100))
            # dark bg for readability
            bg = pygame.Surface((surf.get_width() + 4, surf.get_height()), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            self.screen.blit(bg, (4, y))
            self.screen.blit(surf, (6, y))
            y += surf.get_height() + 2
        # player hitbox
        pygame.draw.rect(self.screen, (0, 255, 0),
            (pr.x - cam, pr.y + MAP_OFFSET_Y, pr.width, pr.height), 1)
        # door hitboxes
        for door in self.room.doors:
            dr = door.world_rect
            pygame.draw.rect(self.screen, (255, 200, 0),
                (dr.x - cam, dr.y + MAP_OFFSET_Y, dr.width, dr.height), 1)
            cr = door.contact_rect
            pygame.draw.rect(self.screen, (255, 80, 0),
                (cr.x - cam, cr.y + MAP_OFFSET_Y, cr.width, cr.height), 1)


if __name__ == "__main__":
    Game().run()
