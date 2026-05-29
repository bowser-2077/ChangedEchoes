from constants import *

# Shorthand aliases
V=VOID; W=WALL; G=GROUND; GL=GLASS
LW=LIB_WALL;  LG=LIB_GROUND
IW=INF_WALL;  IG=INF_GROUND; T1=INF_WALLTOP1; T2=INF_WALLTOP2
GT=INF_GROUNDTOP; PG=PAWS_GROUND
GW=GOO_WALL;  GG=GOO_GROUND

# ── Layout (64px tiles) ──────────────────────────────────────────────────
# Each room: 20 cols wide x 8 rows tall — camera scrolls on X only.
#   row 0: VOID  (black ceiling void)
#   row 1: WALL  (top wall band)
#   row 2: WALL  (lower wall band / deco row)
#   row 3: GROUND (walkable floor, top)
#   row 4: GROUND (walkable floor, bottom)
#   row 5: VOID  (black pit)
#   row 6: VOID
#   row 7: VOID
#
# GOO rooms use GOO_WALL / GOO_GROUND and have "goo_room": True
# which causes the sanity bar to drain while the player is inside.
#
# STORY: Dr. Chen wakes up in Research Facility OMEGA-7 after an emergency.
# The facility has been partially overrun by a black latex organism ("the Goo").
# She must navigate through 8 rooms to reach the emergency exit.

T = TILE_SIZE  # 64

ROOMS = [

    # ════════════════════════════════════════════════════════════════════
    # ROOM 0 · Wake-Up Corridor
    # The player starts here. Dark, flickering lights. No goo yet.
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Wake-Up Corridor",
        "goo_room": False,
        "message": "...My head is throbbing.\nThe emergency lights are on. Something went wrong.\nI need to find a way out of OMEGA-7.",
        "tiles": [
            [V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V],
            [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
            [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
            [G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G, G],
            [V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V],
            [V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V],
            [V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V, V],
        ],
        "pipe_decos": [(3,"pipe_h"),(9,"pipe_h"),(15,"pipe_h")],
        "doors": [
            {"col": 17, "target": 1, "spawn": (3*T, 2*T)},
        ],
        "exits": [],
    },

    # ════════════════════════════════════════════════════════════════════
    # ROOM 1 · Main Junction — Research Block A
    # Hub room. Three doors: left=0, right=2 (library), far right=3 (goo corridor)
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Research Block A — Junction",
        "goo_room": False,
        "message": "The main junction. Two paths ahead.\nA sign reads: ARCHIVE → | SUBLEVEL B ↓\nThe air smells wrong. Like rubber.",
        "tiles": [
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W],
            [W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W],
            [G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G],
            [G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
        ],
        "pipe_decos": [(5,"pipe_h"),(10,"glass"),(14,"pipe_h")],
        "doors": [
            {"col": 1,  "target": 0, "spawn": (16*T, 2*T)},   # ← Wake-Up Corridor
            {"col": 17, "target": 2, "spawn": (3*T,  2*T)},   # → Archive
        ],
        "exits": [],
    },

    # ════════════════════════════════════════════════════════════════════
    # ROOM 2 · Archive & Reading Room
    # Library with shelves. A note warns about Sublevel C.
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Archive — Reading Room",
        "goo_room": False,
        "message": "Research logs line the shelves.\nLog 47: 'Subject escaped containment. Do NOT enter Sublevel C.'\nLog 48: [REDACTED]",
        "tiles": [
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW],
            [LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW, LW],
            [LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG],
            [LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG, LG],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
        ],
        "pipe_decos": [(4,"lib_shelf"),(8,"lib_shelf"),(13,"lib_shelf"),(17,"lib_shelf")],
        "doors": [
            {"col": 1,  "target": 1, "spawn": (16*T, 2*T)},   # ← Junction
            {"col": 17, "target": 3, "spawn": (3*T,  2*T)},   # → Deep Archive (goo)
        ],
        "exits": [],
    },

    # ════════════════════════════════════════════════════════════════════
    # ROOM 3 · Deep Archive — GOO ROOM ⚠
    # Sanity drains. Shelves coated in black goo. A keycard lies somewhere.
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Deep Archive — Sector C",
        "goo_room": True,
        "message": "It's everywhere.\nBlack latex coating every surface, still pulsing.\n...It's watching me. I need to move fast.",
        "tiles": [
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW],
            [GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW],
            [GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG],
            [GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
        ],
        "pipe_decos": [(6,"inf_drip"),(12,"inf_drip"),(16,"paws")],
        "doors": [
            {"col": 1,  "target": 2, "spawn": (16*T, 2*T)},   # ← Reading Room
            {"col": 17, "target": 4, "spawn": (3*T,  2*T)},   # → Maintenance (goo)
        ],
        "exits": [],
    },

    # ════════════════════════════════════════════════════════════════════
    # ROOM 4 · Maintenance Corridor — GOO ROOM ⚠
    # Pipes and valves. Partially flooded with goo. The exit sign is visible ahead.
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Maintenance Corridor — Goo Flooded",
        "goo_room": True,
        "message": "The pipes are broken. Goo drips from the ceiling.\nI can see the emergency exit sign at the far end.\nJust a little further...",
        "tiles": [
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW],
            [GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW],
            [GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG],
            [GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
        ],
        "pipe_decos": [(3,"inf_drip"),(8,"inf_drip"),(13,"inf_drip"),(17,"paws")],
        "doors": [
            {"col": 1,  "target": 3, "spawn": (16*T, 2*T)},   # ← Deep Archive
            {"col": 17, "target": 5, "spawn": (3*T,  2*T)},   # → Decontamination
        ],
        "exits": [],
    },

    # ════════════════════════════════════════════════════════════════════
    # ROOM 5 · Decontamination Chamber
    # Safe room. Bright lights. Sanity regens faster here.
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Decontamination Chamber",
        "goo_room": False,
        "message": "The decontamination lights are still running.\nThe goo can't reach in here. I can breathe.\nThe emergency exit is just beyond Security.",
        "tiles": [
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W],
            [W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W],
            [G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G],
            [G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
        ],
        "pipe_decos": [(4,"glass"),(9,"pipe_h"),(14,"glass")],
        "doors": [
            {"col": 1,  "target": 4, "spawn": (16*T, 2*T)},   # ← Maintenance
            {"col": 17, "target": 6, "spawn": (3*T,  2*T)},   # → Security Wing
        ],
        "exits": [],
    },

    # ════════════════════════════════════════════════════════════════════
    # ROOM 6 · Security Wing — GOO ROOM ⚠
    # The goo got here too. Security monitors show the organism spreading.
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Security Wing — Compromised",
        "goo_room": True,
        "message": "The monitors are still on. I can see it on camera.\nIt's everywhere in the lower levels.\nThe organism — it moves with purpose.",
        "tiles": [
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW],
            [GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW, GW],
            [GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG],
            [GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG, GG],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
        ],
        "pipe_decos": [(5,"inf_drip"),(10,"paws"),(15,"inf_drip")],
        "doors": [
            {"col": 1,  "target": 5, "spawn": (16*T, 2*T)},   # ← Decontamination
            {"col": 17, "target": 7, "spawn": (3*T,  2*T)},   # → Emergency Exit
        ],
        "exits": [],
    },

    # ════════════════════════════════════════════════════════════════════
    # ROOM 7 · Emergency Exit Lobby — ENDING ROOM
    # The exit is here. Clean room. Story concludes.
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Emergency Exit — Lobby",
        "goo_room": False,
        "message": "The emergency exit. I made it.\nI can hear the alarms outside. Quarantine is in effect.\nI don't know what I saw in there... but I'm alive.",
        "tiles": [
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W],
            [W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W,  W],
            [G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G],
            [G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G,  G],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
            [V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V,  V],
        ],
        "pipe_decos": [(6,"pipe_h"),(13,"pipe_h")],
        "doors": [
            {"col": 1, "target": 6, "spawn": (16*T, 2*T)},    # ← Security Wing
        ],
        "exits": [],
    },
]
