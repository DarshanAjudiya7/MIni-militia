"""
╔══════════════════════════════════════════════════════════╗
║           MINI MILITIA CLONE — Python Edition            ║
║         Local Multiplayer 2D Shooter (2-4 Players)      ║
╚══════════════════════════════════════════════════════════╝

Requirements: pip install pygame
Run:          python game.py

Controls:
  Player 1 (WASD + Mouse/Space)
    Move:   A/D    |  Jetpack: W  |  Aim: Mouse  |  Shoot: Left Click
    Grenade: G     |  Reload: R   |  Melee: F     |  Respawn: Enter

  Player 2 (Arrow Keys + Numpad)
    Move:   ←/→    |  Jetpack: ↑  |  Aim: Numpad  |  Shoot: Numpad 0
    Grenade: .     |  Reload: /   |  Melee: ,      |  Respawn: Enter

  Player 3 & 4: Gamepad support (Xbox/PS controllers)
  ESC: Pause/Menu  |  TAB: Scoreboard
"""

import pygame
import sys
import math
import random
import json
import time
import socket
import threading
try:
    import socketio
except ImportError:
    socketio = None
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum, auto
from collections import deque

# ─────────────────────────────────────────────
#  CONSTANTS & CONFIG
# ─────────────────────────────────────────────
W, H = 1280, 720
FPS = 90
GRAVITY = 0.45
MAX_JETPACK_FUEL = 100
FUEL_RECHARGE_RATE = 0.8
FUEL_DRAIN_RATE = 2.2

# Palette
DEFAULT_SERVER_IP = "localhost" # Set this to the host's IP address for cross-PC play (e.g., "192.168.1.5")
C = {
    "bg":        (12,  14,  22),
    "sky":       (15,  25,  55),
    "ground":    (34,  85,  34),
    "dirt":      (80,  55,  30),
    "rock":      (90,  90, 100),
    "water":     (20,  80, 180),
    "ui_bg":     (10,  12,  20, 200),
    "ui_panel":  (20,  25,  45),
    "ui_border": (60,  90, 180),
    "hp_full":   (60, 200,  60),
    "hp_low":    (220, 60,  60),
    "hp_empty":  (50,  50,  50),
    "shield":    (80, 160, 255),
    "fuel":      (255, 180,  20),
    "ammo":      (200, 200, 200),
    "kill_feed": (255, 220,  80),
    "white":     (255, 255, 255),
    "yellow":    (255, 220,  40),
    "red":       (220,  50,  50),
    "green":     (50,  200,  60),
    "blue":      (60,  140, 255),
    "orange":    (255, 140,  30),
    "purple":    (160,  80, 220),
    "cyan":      (40,  220, 220),
    "dark":      (8,   10,  18),
    "shadow":    (0,    0,   0, 120),
    "blood":     (200,  10,  10),
    "flash":     (255, 255, 200),
    "smoke":     (140, 140, 140, 100),
    "mid_gray":  (120, 120, 140),
    "gold":      (255, 215,  0),
    "neon_blue": (0,   191, 255),
    "neon_green":(57,  255,  20),
    "dark_panel":(15,  18,  32, 230),
}

PLAYER_COLORS = [
    (60,  180, 255),   # Blue
    (255,  80,  80),   # Red
    (80,  220,  80),   # Green
    (255, 200,  40),   # Yellow
]

PLAYER_NAMES = ["Alpha", "Bravo", "Charlie", "Delta"]

# ─────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────
class GameState(Enum):
    MAIN_MENU = auto()
    GAME_MODE  = auto()
    LOADING    = auto()
    PLAYING    = auto()
    PAUSED     = auto()
    GAME_OVER  = auto()
    SCOREBOARD = auto()
    MAP_SELECT = auto()
    MULTIPLAYER = auto()
    SETTINGS = auto()

class WeaponType(Enum):
    # Assault
    AK47    = auto()
    M4      = auto()
    XM8     = auto()
    # SMG
    UZI     = auto()
    MP5     = auto()
    TEC9    = auto()
    # Sniper
    SNIPER  = auto()
    # Shotgun
    SHOTGUN = auto()
    # Special
    ROCKET  = auto()
    EMP     = auto()
    PHASR   = auto()
    FLAMETHROWER = auto()
    # Handguns
    MAGNUM  = auto()
    DEAGLE  = auto()

# ─────────────────────────────────────────────
#  WEAPON DEFINITIONS
# ─────────────────────────────────────────────
WEAPONS = {
    # -- ASSAULT --
    WeaponType.AK47: {
        "name": "AK-47", "damage": 26, "speed": 17, "ammo": 30, "max_ammo": 30,
        "fire_rate": 0.12, "reload_time": 2.0, "spread": 0.08, "bullets": 1,
        "color": (150, 100, 50), "length": 34, "recoil": 2.5,
    },
    WeaponType.M4: {
        "name": "M4 / AR-15", "damage": 21, "speed": 20, "ammo": 30, "max_ammo": 30,
        "fire_rate": 0.09, "reload_time": 1.6, "spread": 0.04, "bullets": 1,
        "color": (60, 60, 60), "length": 32, "recoil": 1.8,
    },
    WeaponType.XM8: {
        "name": "XM8", "damage": 22, "speed": 18, "ammo": 30, "max_ammo": 30,
        "fire_rate": 0.1, "reload_time": 1.8, "spread": 0.03, "bullets": 1,
        "color": (180, 180, 180), "length": 35, "recoil": 1.5,
    },
    # -- SMG --
    WeaponType.UZI: {
        "name": "Uzi", "damage": 12, "speed": 15, "ammo": 32, "max_ammo": 32,
        "fire_rate": 0.05, "reload_time": 1.5, "spread": 0.15, "bullets": 1,
        "color": (40, 40, 40), "length": 18, "recoil": 1.2,
    },
    WeaponType.MP5: {
        "name": "MP5", "damage": 16, "speed": 18, "ammo": 30, "max_ammo": 30,
        "fire_rate": 0.08, "reload_time": 1.7, "spread": 0.06, "bullets": 1,
        "color": (50, 50, 70), "length": 24, "recoil": 1.4,
    },
    WeaponType.TEC9: {
        "name": "Tec-9", "damage": 14, "speed": 16, "ammo": 40, "max_ammo": 40,
        "fire_rate": 0.07, "reload_time": 1.8, "spread": 0.1, "bullets": 2, # special: dual
        "color": (90, 90, 120), "length": 20, "recoil": 2.2,
    },
    # -- SNIPER & SHOTGUN --
    WeaponType.SNIPER: {
        "name": "Barrett (Sniper)", "damage": 95, "speed": 26, "ammo": 5, "max_ammo": 5,
        "fire_rate": 1.6, "reload_time": 3.0, "spread": 0.005, "bullets": 1,
        "color": (100, 100, 220), "length": 45, "recoil": 7.0,
    },
    WeaponType.SHOTGUN: {
        "name": "Super 90 (Shotgun)", "damage": 16, "speed": 12, "ammo": 6, "max_ammo": 6,
        "fire_rate": 0.9, "reload_time": 2.5, "spread": 0.25, "bullets": 8,
        "color": (180, 120, 50), "length": 30, "recoil": 5.5,
    },
    # -- SPECIAL --
    WeaponType.ROCKET: {
        "name": "Rocket Launcher", "damage": 85, "speed": 10, "ammo": 3, "max_ammo": 3,
        "fire_rate": 1.4, "reload_time": 3.2, "spread": 0.01, "bullets": 1,
        "color": (220, 80, 50), "length": 40, "recoil": 9.0, "explosive": True,
    },
    WeaponType.EMP: {
        "name": "EMP Shock Gun", "damage": 15, "speed": 10, "ammo": 5, "max_ammo": 5,
        "fire_rate": 1.5, "reload_time": 3.5, "spread": 0.05, "bullets": 1,
        "color": (57, 255, 20), "length": 32, "recoil": 4.0, "emp": True,
    },
    WeaponType.PHASR: {
        "name": "PHASR Laser", "damage": 4, "speed": 35, "ammo": 80, "max_ammo": 80,
        "fire_rate": 0.02, "reload_time": 2.0, "spread": 0.01, "bullets": 1,
        "color": (255, 50, 255), "length": 38, "recoil": 0.2, "beam": True,
    },
    WeaponType.FLAMETHROWER: {
        "name": "Flamethrower", "damage": 8, "speed": 11, "ammo": 100, "max_ammo": 100,
        "fire_rate": 0.04, "reload_time": 3.0, "spread": 0.2, "bullets": 1,
        "color": (255, 120, 0), "length": 42, "recoil": 0.5, "fire": True,
    },
    # -- HANDGUNS --
    WeaponType.MAGNUM: {
        "name": ".44 Magnum", "damage": 45, "speed": 18, "ammo": 6, "max_ammo": 6,
        "fire_rate": 0.5, "reload_time": 1.8, "spread": 0.05, "bullets": 1,
        "color": (200, 180, 50), "length": 25, "recoil": 4.5,
    },
    WeaponType.DEAGLE: {
        "name": "Desert Eagle", "damage": 38, "speed": 19, "ammo": 7, "max_ammo": 7,
        "fire_rate": 0.4, "reload_time": 1.6, "spread": 0.04, "bullets": 2, # special: dual
        "color": (160, 160, 170), "length": 23, "recoil": 4.0,
    },
}

# ─────────────────────────────────────────────
#  PARTICLES
# ─────────────────────────────────────────────
class Particle:
    __slots__ = ['x','y','vx','vy','life','max_life','color','size','gravity']
    def __init__(self, x, y, vx, vy, color, life=40, size=3, gravity=0.15):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life = self.max_life = life
        self.size = size
        self.gravity = gravity

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.life -= 1
        return self.life > 0

    def draw(self, surf, cam_x, cam_y):
        alpha = self.life / self.max_life
        r = max(1, int(self.size * alpha))
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        if -10 < sx < W+10 and -10 < sy < H+10:
            pygame.draw.circle(surf, self.color, (sx, sy), r)

class BloodParticle(Particle):
    def __init__(self, x, y):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1, 5)
        super().__init__(x, y, math.cos(angle)*speed, math.sin(angle)*speed,
                         C["blood"], life=random.randint(25,50), size=random.randint(2,5), gravity=0.3)

class SmokeParticle(Particle):
    def __init__(self, x, y):
        super().__init__(x, y, random.uniform(-0.5,0.5), random.uniform(-1.5,-0.3),
                         (140+random.randint(0,60),)*3, life=random.randint(30,60), size=random.randint(4,10), gravity=-0.02)

class ExplosionParticle(Particle):
    def __init__(self, x, y):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2, 10)
        color = random.choice([(255,180,20),(255,100,20),(255,220,80),(200,50,20)])
        super().__init__(x, y, math.cos(angle)*speed, math.sin(angle)*speed,
                         color, life=random.randint(20,45), size=random.randint(3,8), gravity=0.2)

# ─────────────────────────────────────────────
#  BULLET / ROCKET
# ─────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, angle, weapon_data, owner_id):
        self.x, self.y = x, y
        self.angle = angle
        spread = random.uniform(-weapon_data["spread"], weapon_data["spread"])
        a = angle + spread
        self.vx = math.cos(a) * weapon_data["speed"]
        self.vy = math.sin(a) * weapon_data["speed"]
        self.damage = weapon_data["damage"]
        self.owner_id = owner_id
        self.alive = True
        self.explosive = weapon_data.get("explosive", False)
        self.emp = weapon_data.get("emp", False)
        self.beam = weapon_data.get("beam", False)
        self.fire = weapon_data.get("fire", False)
        self.trail = deque(maxlen=8)
        self.color = weapon_data["color"]
        self.life = 60 if self.fire else 120

    def update(self, map_rects):
        self.trail.append((self.x, self.y))
        self.x += self.vx
        self.y += self.vy
        if self.fire:
            self.vx *= 0.98
            self.vy *= 0.98
        else:
            self.vy += 0.05
        
        r = pygame.Rect(self.x-3, self.y-3, 6, 6)
        for rect in map_rects:
            if r.colliderect(rect):
                self.alive = False
                return
        self.life -= 1
        if self.life <= 0 or not (0 < self.x < 3200 and -200 < self.y < 1200):
            self.alive = False

    def draw(self, surf, cam_x, cam_y):
        if not self.alive: return
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i+1) / len(self.trail)
            r = max(1, int(3 * alpha))
            col = tuple(int(c * alpha) for c in self.color)
            pygame.draw.circle(surf, col, (int(tx-cam_x), int(ty-cam_y)), r)
        pygame.draw.circle(surf, self.color, (int(self.x-cam_x), int(self.y-cam_y)), 4)

# ─────────────────────────────────────────────
#  GRENADE
# ─────────────────────────────────────────────
class Grenade:
    def __init__(self, x, y, vx, vy, owner_id):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.owner_id = owner_id
        self.alive = True
        self.timer = 180
        self.bounced = 0

    def update(self, map_rects):
        self.timer -= 1
        self.vy += GRAVITY * 0.5
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.99
        r = pygame.Rect(self.x-5, self.y-5, 10, 10)
        for rect in map_rects:
            if r.colliderect(rect):
                if abs(self.vy) > abs(self.vx):
                    self.vy *= -0.5
                else:
                    self.vx *= -0.5
                self.bounced += 1
        return self.timer <= 0

    def draw(self, surf, cam_x, cam_y):
        sx, sy = int(self.x-cam_x), int(self.y-cam_y)
        blink = (self.timer < 60 and (self.timer // 5) % 2 == 0)
        col = (255, 80, 20) if blink else (60, 160, 60)
        pygame.draw.circle(surf, col, (sx, sy), 6)
        pygame.draw.circle(surf, C["white"], (sx, sy), 6, 1)
        frac = self.timer / 180
        pygame.draw.line(surf, C["yellow"], (sx, sy-6), (sx, int(sy-6-8*frac)), 2)

# ─────────────────────────────────────────────
#  WEAPON PICKUP
# ─────────────────────────────────────────────
class WeaponPickup:
    def __init__(self, x, y, wtype):
        self.x, self.y = x, y
        self.wtype = wtype
        self.rect = pygame.Rect(x-15, y-15, 30, 30)
        self.bob = 0
        self.alive = True
        self.respawn_timer = 0

    def update(self):
        self.bob = math.sin(pygame.time.get_ticks() * 0.003) * 5
        if not self.alive:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.alive = True

    def draw(self, surf, cam_x, cam_y):
        if not self.alive: return
        data = WEAPONS[self.wtype]
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + self.bob)
        glow = pygame.Surface((50,50), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*data["color"], 40), (25,25), 22)
        surf.blit(glow, (sx-25, sy-25))
        pygame.draw.rect(surf, C["ui_panel"], (sx-16, sy-16, 32, 32), border_radius=6)
        pygame.draw.rect(surf, data["color"], (sx-16, sy-16, 32, 32), 2, border_radius=6)
        pygame.draw.rect(surf, data["color"], (sx-10, sy-4, data["length"]//2, 5), border_radius=2)
        pygame.draw.rect(surf, data["color"], (sx-10, sy+1, 8, 7), border_radius=2)

# ─────────────────────────────────────────────
#  HEALTH PACK
# ─────────────────────────────────────────────
class HealthPack:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.rect = pygame.Rect(x-12, y-12, 24, 24)
        self.alive = True
        self.bob = 0

    def update(self):
        self.bob = math.sin(pygame.time.get_ticks() * 0.004) * 4

    def draw(self, surf, cam_x, cam_y):
        if not self.alive: return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + self.bob)
        pygame.draw.rect(surf, (180, 30, 30), (sx-12, sy-12, 24, 24), border_radius=5)
        pygame.draw.rect(surf, (255, 255, 255), (sx-3, sy-9, 6, 18), border_radius=2)
        pygame.draw.rect(surf, (255, 255, 255), (sx-9, sy-3, 18, 6), border_radius=2)

# ─────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────
class Player:
    W, H = 28, 40

    def __init__(self, pid, x, y, color, name):
        self.pid = pid
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.color = color
        self.name = name
        self.facing = 1
        self.aim_angle = 0.0
        self.hp = 100
        self.max_hp = 100
        self.shield = 0
        self.max_shield = 50
        self.fuel = MAX_JETPACK_FUEL
        self.kills = 0
        self.deaths = 0
        self.alive = True
        self.respawn_timer = 0
        self.weapons = [dict(type=WeaponType.AK47, **WEAPONS[WeaponType.AK47])]
        self.weapon_slot = 0
        self.fire_cooldown = 0
        self.reload_timer = 0
        self.reloading = False
        self.recoil = 0.0
        self.on_ground = False
        self.using_jetpack = False
        self.crouching = False
        self.is_shooting = False
        self.shoot_flash = 0
        self.hit_flash = 0
        self.invincible = 0
        self.walk_frame = 0
        self.walk_timer = 0
        self.lean_angle = 0.0
        self.grenades = 3

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    @property
    def center(self):
        return (self.x + self.W//2, self.y + self.H//2)

    def current_weapon(self):
        if self.weapons:
            return self.weapons[self.weapon_slot]
        return None

    def pickup_weapon(self, wtype):
        for i, w in enumerate(self.weapons):
            if w["type"] == wtype:
                w["ammo"] = w["max_ammo"]
                return
        if len(self.weapons) < 2:
            self.weapons.append(dict(type=wtype, **WEAPONS[wtype]))
        else:
            self.weapons[1] = dict(type=wtype, **WEAPONS[wtype])
            self.weapon_slot = 1

    def switch_weapon(self):
        if len(self.weapons) > 1:
            self.weapon_slot = 1 - self.weapon_slot
            self.reloading = False
            self.reload_timer = 0

    def start_reload(self):
        w = self.current_weapon()
        if w and w["ammo"] < w["max_ammo"] and not self.reloading:
            self.reloading = True
            self.reload_timer = int(w["reload_time"] * FPS)

    def update_reload(self):
        if self.reloading:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                w = self.current_weapon()
                if w:
                    w["ammo"] = w["max_ammo"]
                self.reloading = False

    def take_damage(self, dmg, attacker_id=None):
        if self.invincible > 0: return 0
        actual = dmg
        if self.shield > 0:
            absorb = min(self.shield, dmg)
            self.shield -= absorb
            actual -= absorb
        self.hp -= actual
        self.hit_flash = 12
        return actual

    def update(self, map_rects, map_width):
        if not self.alive:
            self.respawn_timer -= 1
            return
        self.vy += GRAVITY
        if self.using_jetpack and self.fuel > 0:
            self.vy -= 0.9
            self.fuel = max(0, self.fuel - FUEL_DRAIN_RATE)
        elif self.on_ground:
            self.fuel = min(MAX_JETPACK_FUEL, self.fuel + FUEL_RECHARGE_RATE)
        else:
            self.fuel = min(MAX_JETPACK_FUEL, self.fuel + FUEL_RECHARGE_RATE * 0.3)
        self.vy = max(-12, min(18, self.vy))
        self.vx = max(-7, min(7, self.vx))
        self.x += self.vx
        self.x = max(0, min(map_width - self.W, self.x))
        r = self.rect
        for rect in map_rects:
            if r.colliderect(rect):
                if self.vx > 0: self.x = rect.left - self.W
                elif self.vx < 0: self.x = rect.right
                self.vx = 0
                r = self.rect
        self.on_ground = False
        self.y += self.vy
        r = self.rect
        for rect in map_rects:
            if r.colliderect(rect):
                if self.vy > 0:
                    self.y = rect.top - self.H
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = rect.bottom
                    self.vy = 0
                r = self.rect
        if self.y > 900: self.hp = 0
        if self.on_ground: self.vx *= 0.78
        else: self.vx *= 0.92
        if self.fire_cooldown > 0: self.fire_cooldown -= 1
        if self.hit_flash > 0: self.hit_flash -= 1
        if self.shoot_flash > 0: self.shoot_flash -= 1
        if self.invincible > 0: self.invincible -= 1
        if self.recoil > 0: self.recoil -= 0.3
        self.update_reload()
        if abs(self.vx) > 0.5 and self.on_ground:
            self.walk_timer += 1
            if self.walk_timer > 6:
                self.walk_frame = (self.walk_frame + 1) % 4
                self.walk_timer = 0
        else: self.walk_frame = 0
        target_lean = self.aim_angle * 0.3 if abs(self.aim_angle) < math.pi/2 else 0
        self.lean_angle += (target_lean - self.lean_angle) * 0.2

    def draw(self, surf, cam_x, cam_y):
        if not self.alive: return
        blink = self.invincible > 0 and (self.invincible // 4) % 2 == 0
        if blink: return
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        cx, cy = sx + self.W // 2, sy + self.H // 2
        col = self.color
        dark_col = tuple(max(0, c - 60) for c in col)
        light_col = tuple(min(255, c + 60) for c in col)
        shadow_surf = pygame.Surface((30, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0,0,0,80), (0,0,30,8))
        surf.blit(shadow_surf, (cx-15, sy+self.H-2))
        if self.using_jetpack and self.fuel > 0:
            for _ in range(3):
                fx = cx + random.randint(-5, 5)
                fy = sy + self.H - 2
                flen = random.randint(8, 20)
                fcol = random.choice([(255,180,20),(255,100,20),(255,220,80)])
                pygame.draw.line(surf, fcol, (fx, fy), (fx+random.randint(-3,3), fy+flen), random.randint(2,4))
        leg_swing = math.sin(self.walk_frame * math.pi / 2) * 8
        pygame.draw.line(surf, dark_col, (cx-5, sy+24), (cx-5+int(leg_swing), sy+self.H), 5)
        pygame.draw.line(surf, dark_col, (cx+5, sy+24), (cx+5-int(leg_swing), sy+self.H), 5)
        body_rect = pygame.Rect(sx+4, sy+14, self.W-8, 22)
        pygame.draw.rect(surf, col, body_rect, border_radius=6)
        pygame.draw.rect(surf, light_col, (sx+7, sy+17, self.W-14, 8), border_radius=3)
        arm_angle = self.aim_angle
        arm_len = 14
        arm_x = cx + int(math.cos(arm_angle) * arm_len * self.facing)
        arm_y = (sy+20) + int(math.sin(arm_angle) * arm_len)
        pygame.draw.line(surf, dark_col, (cx, sy+20), (arm_x, arm_y), 6)
        head_col = tuple(min(255, c+30) for c in col)
        pygame.draw.ellipse(surf, head_col, (sx+5, sy+1, self.W-10, 22))
        visor_col = (40, 160, 255) if self.shield > 0 else (50, 50, 80)
        visor_x = cx + (3 * self.facing)
        pygame.draw.ellipse(surf, visor_col, (visor_x-6, sy+6, 12, 8))
        if self.hit_flash > 0:
            flash = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            alpha = int(200 * self.hit_flash / 12)
            flash.fill((255, 50, 50, alpha))
            surf.blit(flash, (sx, sy))
        if self.shoot_flash > 0:
            w = self.current_weapon()
            if w:
                muzzle_dist = w["length"] + 8
                mx = cx + int(math.cos(self.aim_angle) * muzzle_dist)
                my = (sy+20) + int(math.sin(self.aim_angle) * muzzle_dist)
                gsurf = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(gsurf, (255, 220, 80, 180), (15,15), 12)
                pygame.draw.circle(gsurf, (255, 255, 200, 240), (15,15), 6)
                surf.blit(gsurf, (mx-15, my-15))
        self._draw_weapon(surf, cx, sy+20, self.aim_angle)
        if self.shield > 0:
            s_surf = pygame.Surface((self.W+20, self.H+20), pygame.SRCALPHA)
            alpha = 40 + int(math.sin(pygame.time.get_ticks()*0.01)*15)
            pygame.draw.ellipse(s_surf, (80, 160, 255, alpha), (0, 0, self.W+20, self.H+20), 3)
            surf.blit(s_surf, (sx-10, sy-10))
        jet_x = cx - (6 * self.facing)
        pygame.draw.rect(surf, (60, 60, 80), (jet_x-4, sy+16, 8, 16), border_radius=3)
        pygame.draw.rect(surf, (100, 100, 120), (jet_x-3, sy+18, 6, 8), border_radius=2)
        name_surf = SMALL_FONT.render(self.name, True, col)
        surf.blit(name_surf, (cx - name_surf.get_width()//2, sy - 18))
        bar_w = 36
        bar_x = cx - bar_w//2
        bar_y = sy - 10
        pygame.draw.rect(surf, C["hp_empty"], (bar_x, bar_y, bar_w, 4), border_radius=2)
        hp_w = int(bar_w * self.hp / self.max_hp)
        hp_col = C["hp_full"] if self.hp > 40 else C["hp_low"]
        if hp_w > 0:
            pygame.draw.rect(surf, hp_col, (bar_x, bar_y, hp_w, 4), border_radius=2)
        if self.shield > 0:
            sh_w = int(bar_w * self.shield / self.max_shield)
            pygame.draw.rect(surf, C["shield"], (bar_x, bar_y-5, sh_w, 3), border_radius=1)

    def _draw_weapon(self, surf, cx, cy, angle):
        w = self.current_weapon()
        if not w: return
        length = w["length"]
        col = w["color"]
        recoil_offset = self.recoil * 0.4
        end_x = cx + int(math.cos(angle) * (length - recoil_offset))
        end_y = cy + int(math.sin(angle) * (length - recoil_offset))
        start_x = cx + int(math.cos(angle) * (6 - recoil_offset * 0.5))
        start_y = cy + int(math.sin(angle) * (6 - recoil_offset * 0.5))
        pygame.draw.line(surf, col, (start_x, start_y), (end_x, end_y), 5)
        pygame.draw.line(surf, tuple(min(255, c+80) for c in col), (start_x, start_y-1), (end_x, end_y-1), 2)
        if w["type"] == WeaponType.SNIPER:
            mid_x = (start_x+end_x)//2
            mid_y = (start_y+end_y)//2
            pygame.draw.circle(surf, (80, 80, 80), (mid_x, mid_y), 4)
            pygame.draw.circle(surf, (180, 180, 200), (mid_x, mid_y), 4, 1)

# ─────────────────────────────────────────────
#  MAP
# ─────────────────────────────────────────────
class Map:
    def __init__(self, map_id=0):
        self.width = 3000
        self.height = 900
        self.mid = map_id
        self.platforms = []
        self.spawn_points = []
        self.weapon_spawns = []
        self.health_spawns = []
        self._build(map_id)
        self.bg_layers = self._build_background(map_id)

    def _build(self, mid):
        W, H = self.width, self.height
        self.platforms = [pygame.Rect(0, 680, W, 40)]
        if mid == 0:
            self.platforms += [pygame.Rect(200, 560, 200, 20), pygame.Rect(500, 480, 160, 20), pygame.Rect(750, 560, 220, 20), pygame.Rect(1000, 440, 180, 20), pygame.Rect(1250, 520, 150, 20), pygame.Rect(1450, 460, 200, 20), pygame.Rect(1700, 540, 180, 20), pygame.Rect(1950, 480, 160, 20), pygame.Rect(2200, 560, 200, 20), pygame.Rect(2450, 440, 180, 20), pygame.Rect(2700, 520, 200, 20), pygame.Rect(2900, 460, 200, 20), pygame.Rect(400, 680, 60, -300), pygame.Rect(1100, 680, 60, -200), pygame.Rect(1800, 680, 60, -250), pygame.Rect(2500, 680, 60, -180), pygame.Rect(1540, 580, 120, 100), pygame.Rect(1560, 500, 80,  80), pygame.Rect(1580, 440, 40,  60)]
            self.spawn_points = [(100, 600),(200,600),(2900,600),(3000,600),(1500,400),(600,420)]
            self.weapon_spawns = [(400, 540, WeaponType.AK47), (1000, 400, WeaponType.SHOTGUN), (1580, 400, WeaponType.SNIPER), (2200, 520, WeaponType.ROCKET), (2700, 480, WeaponType.AK47)]
            self.health_spawns = [(700,540),(1300,490),(1800,510),(2400,420),(600,650)]
        elif mid == 1:
            self.platforms += [pygame.Rect(100, 580, 250, 20), pygame.Rect(450, 500, 200, 20), pygame.Rect(700, 580, 180, 20), pygame.Rect(950, 460, 200, 20), pygame.Rect(1200, 540, 160, 20), pygame.Rect(1420, 480, 220, 20), pygame.Rect(1700, 560, 200, 20), pygame.Rect(1960, 500, 180, 20), pygame.Rect(2200, 580, 200, 20), pygame.Rect(2480, 460, 200, 20), pygame.Rect(2740, 540, 200, 20), pygame.Rect(2980, 480, 180, 20), pygame.Rect(1560, 380, 80,  20), pygame.Rect(1580, 320, 40,  20)]
            self.spawn_points = [(120, 540),(220,540),(3000,540),(3100,540),(1400,440),(1800,440)]
            self.weapon_spawns = [(500, 460, WeaponType.AK47), (960, 420, WeaponType.SHOTGUN), (1580, 280, WeaponType.SNIPER), (2200, 540, WeaponType.ROCKET), (2480, 420, WeaponType.AK47)]
            self.health_spawns = [(700,540),(1300,490),(1800,510),(2500,420),(600,640)]
        elif mid == 2:
            for x in range(300, 3000, 400):
                self.platforms.append(pygame.Rect(x, 500, 150, 25))
                self.platforms.append(pygame.Rect(x + 200, 400, 120, 25))
            self.platforms += [pygame.Rect(800, 250, 600, 20), pygame.Rect(1800, 250, 600, 20), pygame.Rect(1500, 580, 200, 40)]
            self.spawn_points = [(200, 600), (3000, 600), (1600, 500), (800, 200)]
            self.weapon_spawns = [(1500, 200, WeaponType.SNIPER), (400, 450, WeaponType.AK47), (2600, 450, WeaponType.SHOTGUN)]
            self.health_spawns = [(900, 200), (2200, 200), (1500, 630)]
        elif mid == 3:
            self.platforms += [pygame.Rect(100, 300, 400, 20), pygame.Rect(600, 450, 400, 20), pygame.Rect(1100, 300, 400, 20), pygame.Rect(1600, 450, 400, 20), pygame.Rect(2100, 300, 400, 20), pygame.Rect(2600, 450, 400, 20), pygame.Rect(400, 580, 2400, 30)]
            self.spawn_points = [(300, 200), (2800, 200), (1500, 500)]
            self.weapon_spawns = [(1500, 530, WeaponType.ROCKET), (800, 400, WeaponType.AK47), (2200, 400, WeaponType.AK47)]
            self.health_spawns = [(500, 250), (2500, 250), (1500, 400)]

    def _build_background(self, mid):
        themes = [{"sky": (15, 25, 55),  "m1": (30, 50, 80), "m2": (20, 55, 30)}, {"sky": (20, 60, 40),  "m1": (10, 40, 20), "m2": (30, 80, 40)}, {"sky": (160, 200, 255),"m1": (100, 150, 220), "m2": (200, 230, 255)}, {"sky": (20, 10, 10),  "m1": (40, 20, 20), "m2": (60, 30, 30)}]
        theme = themes[mid % 4]
        layers = []
        for i in range(3):
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            if i == 0:
                s.fill(theme["sky"])
                for _ in range(200):
                    x, y = random.randint(0, self.width), random.randint(0, 400)
                    pygame.draw.circle(s, (255,255,255, random.randint(100, 200)), (x,y), random.randint(1,2))
            elif i == 1:
                pts = [(0, 400)]
                for x in range(0, self.width+100, 100): pts.append((x, 350 + random.randint(-100, 100)))
                pts += [(self.width, 900), (0, 900)]
                pygame.draw.polygon(s, theme["m1"], pts)
            else:
                pts = [(0, 500)]
                for x in range(0, self.width+100, 80): pts.append((x, 460 + random.randint(-60, 60)))
                pts += [(self.width, 900), (0, 900)]
                pygame.draw.polygon(s, theme["m2"], pts)
            layers.append(s)
        return layers

    def draw_bg(self, surf, cam_x):
        surf.fill(C["sky"])
        parallax = [0.1, 0.3, 0.5]
        for layer, p in zip(self.bg_layers, parallax):
            ox = int(cam_x * p) % self.width
            surf.blit(layer, (-ox, 0))
            if ox > 0: surf.blit(layer, (self.width - ox, 0))

    def draw_terrain(self, surf, cam_x, cam_y):
        for rect in self.platforms:
            sr = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.width, rect.height)
            if -50 < sr.x < W+50 and -50 < sr.y < H+50:
                pygame.draw.rect(surf, C["ground"], sr)
                pygame.draw.rect(surf, C["dirt"], (sr.x, sr.y+sr.height-6, sr.width, 6))
                pygame.draw.rect(surf, (50, 120, 50), sr, 2)

    def get_spawn(self): return random.choice(self.spawn_points)

# ─────────────────────────────────────────────
#  KILL FEED
# ─────────────────────────────────────────────
class KillFeed:
    def __init__(self): self.entries = deque(maxlen=5)
    def add(self, killer, victim, weapon=""): self.entries.append({"killer": killer, "victim": victim, "weapon": weapon, "timer": 300})
    def update(self):
        for e in list(self.entries):
            e["timer"] -= 1
            if e["timer"] <= 0: self.entries.remove(e)
    def draw(self, surf):
        y = 80
        for e in reversed(self.entries):
            alpha = min(255, e["timer"] * 3)
            text = f"{e['killer']}  ✕  {e['victim']}"
            ts = SMALL_FONT.render(text, True, C["kill_feed"])
            panel = pygame.Surface((ts.get_width()+16, 22), pygame.SRCALPHA)
            panel.fill((10, 12, 22, int(alpha * 0.8)))
            surf.blit(panel, (W - ts.get_width() - 24, y-2))
            ts.set_alpha(alpha)
            surf.blit(ts, (W - ts.get_width() - 16, y))
            y += 26

# ─────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────
def draw_hud(surf, players, active_players):
    for i, pid in enumerate(active_players):
        p = players[pid]
        col = p.color
        positions = [(14, H-90), (W-180, H-90), (14, 14), (W-180, 14)]
        px, py = positions[i]
        panel = pygame.Surface((166, 80), pygame.SRCALPHA)
        panel.fill(C["dark_panel"])
        pygame.draw.rect(panel, (*col, 80), (0, 0, 166, 80), 2, border_radius=10)
        pygame.draw.rect(panel, (255,255,255, 30), (2, 2, 162, 38), border_radius=8)
        surf.blit(panel, (px, py))
        if not p.alive:
            t = FONT.render(f"DEAD ({max(0,p.respawn_timer)//FPS+1}s)", True, C["red"])
            surf.blit(t, (px+8, py+26))
            continue
        ns = SMALL_FONT.render(p.name, True, col)
        surf.blit(ns, (px+8, py+6))
        bar_x, bar_y = px+8, py+24
        pygame.draw.rect(surf, C["hp_empty"], (bar_x, bar_y, 100, 9), border_radius=4)
        hp_frac = max(0, p.hp / p.max_hp)
        hc = C["hp_full"] if hp_frac > 0.4 else C["hp_low"]
        if hp_frac > 0: pygame.draw.rect(surf, hc, (bar_x, bar_y, int(100*hp_frac), 9), border_radius=4)
        hs = TINY_FONT.render(f"{p.hp}", True, C["white"])
        surf.blit(hs, (bar_x+104, bar_y))
        if p.max_shield > 0:
            sbar_y = bar_y + 13
            pygame.draw.rect(surf, C["hp_empty"], (bar_x, sbar_y, 100, 5), border_radius=2)
            sf = p.shield / p.max_shield
            if sf > 0: pygame.draw.rect(surf, C["shield"], (bar_x, sbar_y, int(100*sf), 5), border_radius=2)
        fuel_y = py + 42
        pygame.draw.rect(surf, C["hp_empty"], (px+8, fuel_y, 80, 5), border_radius=2)
        ff = p.fuel / MAX_JETPACK_FUEL
        if ff > 0: pygame.draw.rect(surf, C["fuel"], (px+8, fuel_y, int(80*ff), 5), border_radius=2)
        fuel_s = TINY_FONT.render("JET", True, C["fuel"])
        surf.blit(fuel_s, (px+92, fuel_y-1))
        w = p.current_weapon()
        if w:
            wname = TINY_FONT.render(w["name"], True, tuple(min(255,c+80) for c in w["color"]))
            surf.blit(wname, (px+8, py+52))
            if p.reloading:
                reload_pct = 1 - p.reload_timer / (w["reload_time"]*FPS)
                rtext = TINY_FONT.render(f"RELOADING {int(reload_pct*100)}%", True, C["yellow"])
                surf.blit(rtext, (px+8, py+64))
            else:
                ammo_s = SMALL_FONT.render(f"{w['ammo']}/{w['max_ammo']}", True, C["ammo"])
                surf.blit(ammo_s, (px+8, py+62))
        for g in range(p.grenades): pygame.draw.circle(surf, (60, 160, 60), (px+120+g*14, py+70), 5)
        kd = TINY_FONT.render(f"K:{p.kills} D:{p.deaths}", True, C["mid_gray"])
        surf.blit(kd, (px+100, py+6))
    if active_players:
        max_kills = max(players[pid].kills for pid in active_players)
        leader = next((players[pid] for pid in active_players if players[pid].kills == max_kills), None)
        if leader and max_kills > 0:
            ts = FONT.render(f"🏆 {leader.name}: {leader.kills}", True, leader.color)
            surf.blit(ts, (W//2 - ts.get_width()//2, 8))

def draw_minimap(surf, players, game_map, active_players):
    mw, mh = 200, 50
    mx, my = W//2 - mw//2, H - mh - 8
    bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
    bg.fill((8, 10, 20, 180))
    pygame.draw.rect(bg, (*C["ui_border"], 180), (0, 0, mw, mh), 1, border_radius=4)
    surf.blit(bg, (mx, my))
    sx, sy = mw / game_map.width, mh / game_map.height
    for rect in game_map.platforms:
        r = pygame.Rect(int(rect.x*sx)+mx, int(rect.y*sy)+my, max(1, int(rect.width*sx)), max(1, int(abs(rect.height)*sy)))
        pygame.draw.rect(surf, (50, 100, 50), r)
    for pid in active_players:
        p = players[pid]
        if p.alive:
            px2, py2 = int(p.x * sx) + mx, int(p.y * sy) + my
            pygame.draw.circle(surf, p.color, (px2, py2), 3)

# ─────────────────────────────────────────────
#  MAIN MENU UI
# ─────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, color=None, text_color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color or C["ui_border"]
        self.text_color = text_color or C["white"]
        self.hover = False
        self.pressed = False

    def update(self, mouse_pos, mouse_click):
        self.hover = self.rect.collidepoint(mouse_pos)
        self.pressed = self.hover and mouse_click
        return self.pressed

    def draw(self, surf):
        scale = 1.04 if self.hover else 1.0
        r = self.rect.inflate(int(self.rect.width*(scale-1)), int(self.rect.height*(scale-1)))
        col = tuple(min(255, c+40) for c in self.color) if self.hover else self.color
        pygame.draw.rect(surf, col, r, border_radius=8)
        pygame.draw.rect(surf, tuple(min(255, c+60) for c in col), r, 2, border_radius=8)
        if self.hover:
            glow = pygame.Surface((r.width+20, r.height+20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.color, 40), (10,10,r.width,r.height), border_radius=8)
            surf.blit(glow, (r.x-10, r.y-10))
        ts = FONT.render(self.text, True, self.text_color)
        surf.blit(ts, (r.centerx - ts.get_width()//2, r.centery - ts.get_height()//2))

# ─────────────────────────────────────────────
#  NETWORK MANAGER
# ─────────────────────────────────────────────
class NetworkManager:
    def __init__(self, game):
        self.game = game
        self.sio = socketio.Client() if socketio else None
        self.active = False
        self.room_code = None
        self.my_id = None
        self.remote_players = {}
        self.last_sync = 0
        if self.sio: self._setup_events()

    def _setup_events(self):
        @self.sio.on('room_created')
        def on_created(data):
            self.room_code = data['passcode']
            self.my_id = data['id']
        @self.sio.on('room_joined')
        def on_joined(data):
            self.room_code = data['passcode']
            self.my_id = data['id']
        @self.sio.on('player_moved')
        def on_moved(data):
            self.remote_players[data['id']] = data
        @self.sio.on('player_shot')
        def on_shot(data):
            # Remote player shot - create bullet locally
            if data['id'] in self.remote_players:
                wtype = WeaponType[data['wtype_name']]
                w_data = WEAPONS[wtype]
                b = Bullet(data['cx'], data['cy'], data['angle'], w_data, data['id'])
                self.game.bullets.append(b)

        @self.sio.on('player_hit')
        def on_hit(data):
            # If I'm the one being hit
            if data['target_id'] == self.my_id:
                victim = self.game.players.get(0)
                if victim:
                    self.game._hit_player(0, data['dmg'], data['attacker_id'])

        @self.sio.on('player_left')
        def on_left(data):
            if data['id'] in self.remote_players: del self.remote_players[data['id']]

    def emit_shoot(self, cx, cy, angle, wtype):
        if self.active and self.room_code:
            self.sio.emit('shoot', {'cx': cx, 'cy': cy, 'angle': angle, 'wtype_name': wtype.name})

    def emit_hit(self, target_id, dmg, attacker_id):
        if self.active and self.room_code:
            self.sio.emit('hit', {'target_id': target_id, 'dmg': dmg, 'attacker_id': attacker_id})

    def connect(self, addr=None):
        if self.active: return True
        if not self.sio:
            print("Socket.io not installed. Multiplayer disabled.")
            return False
            
        if not addr:
            addr = f"http://{DEFAULT_SERVER_IP}:3000"
            
        try:
            self.sio.connect(addr)
            self.active = True
            return True
        except Exception as e:
            print(f"Connection Error: {e}")
            self.active = False
            return False

    def create_room(self):
        if self.active: self.sio.emit('create_room', {})

    def join_room(self, code):
        if self.active: self.sio.emit('join_room', code)

    def sync(self, player):
        if not self.active or not self.room_code: return
        now = time.time()
        if now - self.last_sync > 0.03: # 30Hz sync
            self.sio.emit('sync_pos', {
                'x': player.x, 'y': player.y,
                'vx': player.vx, 'vy': player.vy,
                'aim': player.aim_angle,
                'facing': player.facing,
                'hp': player.hp,
                'max_hp': player.max_hp,
                'name': player.name,
                'color': list(player.color)
            })
            self.last_sync = now

    def draw_settings_preview(self):
        self.game.screen.fill(C["bg"])
        t = BIG_FONT.render("CHOOSE YOUR LOADOUT", True, C["white"])
        self.game.screen.blit(t, (W//2 - t.get_width()//2, 40))
        
        cls = self.game.player_classes[self.game.player_class_id]
        ct = FONT.render(f"CLASS: {cls['name']}", True, C["neon_green"])
        self.game.screen.blit(ct, (W//2 - ct.get_width()//2, 100))
        
        # Weapon Previews
        for idx, wt in enumerate(cls['weapons']):
            w = WEAPONS[wt]
            y = 150 + idx * 75
            pygame.draw.rect(self.game.screen, C["ui_panel"], (W//2 - 240, y, 480, 65), border_radius=10)
            pygame.draw.rect(self.game.screen, w["color"], (W//2 - 240, y, 480, 65), 1, border_radius=10)
            
            # Icon
            pygame.draw.rect(self.game.screen, w['color'], (W//2 - 220, y + 20, 40, 20), border_radius=4)
            # Text
            name_t = FONT.render(w['name'], True, C["white"])
            self.game.screen.blit(name_t, (W//2 - 160, y + 10))
            # Stats
            stat_str = f"Damage: {w['damage']}  |  Fire Rate: {int(1/w['fire_rate'])} sps  |  Ammo: {w['max_ammo']}"
            stat_t = TINY_FONT.render(stat_str, True, C["mid_gray"])
            self.game.screen.blit(stat_t, (W//2 - 160, y + 36))

    def draw_multi_menu(self):
        self.game.screen.fill(C["bg"])
        t = BIG_FONT.render("MULTIPLAYER ROOMS", True, C["white"])
        self.game.screen.blit(t, (W//2 - t.get_width()//2, 80))
        
        status_col = C["neon_green"] if self.active else C["red"]
        status_txt = "Connected to Server" if self.active else "Disconnected from Server"
        st = SMALL_FONT.render(status_txt, True, status_col)
        self.game.screen.blit(st, (W//2 - st.get_width()//2, 140))

        if self.room_code:
            status = FONT.render(f"ROOM CODE: {self.room_code}", True, C["yellow"])
            self.game.screen.blit(status, (W//2 - status.get_width()//2, 190))
            hint = SMALL_FONT.render("Waiting for players...", True, C["mid_gray"])
            self.game.screen.blit(hint, (W//2 - hint.get_width()//2, 220))
            
            # Start game if room ready (simplified)
            play_btn = Button(W//2-110, 500, 220, 48, "🏁 START", (30, 150, 50))
            if play_btn.update(pygame.mouse.get_pos(), self.game.mouse_click):
                self.game.start_game()
            play_btn.draw(self.game.screen)
        else:
            for br, btn in self.game.multi_buttons.items():
                if br != "back" and not self.active:
                    btn.text_color = C["mid_gray"] # Dim if disconnected
                btn.draw(self.game.screen)

# ─────────────────────────────────────────────
#  GAME MANAGER
# ─────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((W, H), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Mini Militia — Python Edition")
        pygame.display.set_icon(self._make_icon())
        self.clock = pygame.time.Clock()

        global FONT, SMALL_FONT, TINY_FONT, BIG_FONT
        FONT       = pygame.font.SysFont("Arial", 18, bold=True)
        SMALL_FONT = pygame.font.SysFont("Arial", 14, bold=True)
        TINY_FONT  = pygame.font.SysFont("Arial", 11)
        BIG_FONT   = pygame.font.SysFont("Arial", 48, bold=True)

        self.state = GameState.MAIN_MENU
        self.num_players = 2
        self.map_id = 0
        self.score_limit = 15
        self.time_options = [60, 180, 300, 600] # 1, 3, 5, 10 minutes
        self.time_idx = 2 # Default 5 min
        self.game_time = self.time_options[self.time_idx] * FPS

        self.players = {}
        self.bullets = []
        self.grenades = []
        self.particles = []
        self.weapon_pickups = []
        self.health_packs = []
        self.kill_feed = KillFeed()
        self.game_map = None
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.active_players = []
        self.player_class_id = 0
        self.player_classes = [
            {"name": "ASSAULT PACK", "weapons": [WeaponType.AK47, WeaponType.M4, WeaponType.XM8]},
            {"name": "SMG SURGE",    "weapons": [WeaponType.UZI, WeaponType.MP5, WeaponType.TEC9]},
            {"name": "SHARP SHOOTER", "weapons": [WeaponType.SNIPER, WeaponType.MAGNUM, WeaponType.DEAGLE]},
            {"name": "SPECIAL OPS",  "weapons": [WeaponType.ROCKET, WeaponType.EMP, WeaponType.PHASR, WeaponType.FLAMETHROWER]},
        ]
        self.map_names = ["URBAN", "JUNGLE", "FROZEN", "CATACOMBS"]
        self.net = NetworkManager(self)
        self.winner = None

        # Sounds (generated)
        self.sounds = self._gen_sounds()

        # Menus
        self._build_menus()

        # Joysticks
        pygame.joystick.init()
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            self.joysticks.append(j)

        # BG surface
        self.bg_surf = pygame.Surface((W, H))

        self.running = True

    def _make_icon(self):
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(icon, (60, 180, 255), (16, 14), 10)
        pygame.draw.rect(icon, (40, 120, 200), (10, 20, 12, 10), border_radius=3)
        pygame.draw.rect(icon, (60, 180, 255), (18, 21, 14, 4), border_radius=2)
        return icon

    def _gen_sounds(self):
        """Generate better arcade sounds using pygame mixer"""
        sounds = {}
        sr = 22050

        def play_tone(freq, dur, vol=0.1, wave='sine'):
            try:
                frames = int(sr * dur)
                arr = []
                for i in range(frames):
                    t = i / sr
                    if wave == 'sine':
                        v = math.sin(2 * math.pi * freq * t)
                    elif wave == 'square':
                        v = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
                    elif wave == 'noise':
                        v = random.uniform(-1, 1)
                    v *= max(0, 1 - i/frames)
                    arr.append([int(v * vol * 32767), int(v * vol * 32767)])
                
                import numpy as np
                sound_arr = np.array(arr, dtype=np.int16)
                return pygame.sndarray.make_sound(sound_arr)
            except Exception:
                return None

        # Try to generate sounds if numpy is available, otherwise silent
        try:
            import numpy as np
            sounds["shoot"] = play_tone(440, 0.08, 0.05, 'square')
            sounds["hit"]   = play_tone(150, 0.12, 0.08, 'noise')
            sounds["kill"]  = play_tone(600, 0.3,  0.1,  'sine')
            sounds["jump"]  = play_tone(300, 0.1,  0.05, 'sine')
            sounds["pickup"]= play_tone(880, 0.15, 0.08, 'sine')
            sounds["reload"]= play_tone(220, 0.2,  0.05, 'square')
            sounds["explode"]= play_tone(60, 0.5,  0.15, 'noise')
        except ImportError:
            pass
        return sounds

    def play_snd(self, name):
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def _build_menus(self):
        cx = W // 2
        self.menu_buttons = {
            "play":     Button(cx-120, 250, 240, 52, "LOCAL PLAY", (30, 100, 200)),
            "multi":    Button(cx-120, 318, 240, 52, "ONLINE",     (60, 40, 180)),
            "map":      Button(cx-120, 386, 240, 52, "MAPS",       (40, 80, 140)),
            "players":  Button(cx-120, 454, 240, 52, "PLAYERS",    (40, 80, 140)),
            "settings": Button(cx-120, 522, 240, 52, "SETTINGS",   (30, 50, 80)),
            "quit":     Button(cx-120, 590, 240, 52, "QUIT",        (100, 30, 30)),
        }
        self.multi_buttons = {
            "create": Button(cx-110, 280, 220, 48, "CREATE ROOM", (30, 100, 50)),
            "join":   Button(cx-110, 348, 220, 48, "JOIN ROOM",   (40, 60, 100)),
            "back":   Button(cx-110, 416, 220, 48, "<< BACK",    (100, 30, 30)),
        }
        self.pause_buttons = {
            "resume": Button(cx-110, 280, 220, 48, "RESUME",   (30, 100, 50)),
            "menu":   Button(cx-110, 348, 220, 48, "MAIN MENU", (40, 60, 100)),
            "quit":   Button(cx-110, 416, 220, 48, "QUIT",      (100, 30, 30)),
        }
        self.gameover_buttons = {
            "rematch": Button(cx-110, 440, 220, 48, "REMATCH",    (30, 100, 50)),
            "menu":    Button(cx-110, 508, 220, 48, "MAIN MENU",  (40, 60, 100)),
        }
        self.map_buttons = {
            0: Button(cx-110, 200, 220, 48, "URBAN",      (60, 80, 140)),
            1: Button(cx-110, 260, 220, 48, "JUNGLE",     (40, 120, 60)),
            2: Button(cx-110, 320, 220, 48, "FROZEN",     (80, 160, 255)),
            3: Button(cx-110, 380, 220, 48, "CATACOMBS",  (100, 70, 40)),
            "back": Button(cx-110, 500, 220, 48, "<< BACK",      (80, 80, 80)),
        }

    def start_game(self):
        self.game_map = Map(self.map_id)
        self.players = {}
        self.active_players = list(range(self.num_players))
        self.bullets = []
        self.grenades = []
        self.particles = []
        self.kill_feed = KillFeed()
        self.timer = self.game_time
        self.winner = None

        for i in range(self.num_players):
            sx, sy = self.game_map.get_spawn()
            sx += i * 60
            p = Player(i, sx, sy - 60, PLAYER_COLORS[i], PLAYER_NAMES[i])
            # Load weapons from class
            p.weapons = []
            for wt in self.player_classes[self.player_class_id]["weapons"]:
                p.weapons.append(dict(type=wt, **WEAPONS[wt]))
            p.weapon_slot = 0
            self.players[i] = p

        # Weapon pickups
        self.weapon_pickups = []
        for (x, y, wt) in self.game_map.weapon_spawns:
            self.weapon_pickups.append(WeaponPickup(x, y, wt))

        # Health packs
        self.health_packs = []
        for (x, y) in self.game_map.health_spawns:
            self.health_packs.append(HealthPack(x, y))

        self.state = GameState.PLAYING

    def respawn_player(self, pid):
        p = self.players[pid]
        sx, sy = self.game_map.get_spawn()
        p.x, p.y = float(sx), float(sy - 60)
        p.vx = p.vy = 0
        p.hp = p.max_hp
        p.shield = 0
        p.fuel = MAX_JETPACK_FUEL
        p.alive = True
        p.respawn_timer = 0
        p.invincible = 120
        # Start with selected class weapons
        p.weapons = []
        for wt in self.player_classes[self.player_class_id]["weapons"]:
            p.weapons.append(dict(type=wt, **WEAPONS[wt]))
        p.weapon_slot = 0
        p.grenades = 3
        # Spawn particles
        for _ in range(20):
            self.particles.append(Particle(
                sx, sy, random.uniform(-4, 4), random.uniform(-5, 0),
                p.color, life=40, size=4))

    def handle_shoot(self, pid):
        p = self.players[pid]
        if not p.alive: return
        w = p.current_weapon()
        if not w: return
        if p.fire_cooldown > 0: return
        if p.reloading: return
        if w["ammo"] <= 0:
            p.start_reload()
            return

        w["ammo"] -= 1
        p.fire_cooldown = int(w["fire_rate"] * FPS)
        p.shoot_flash = 5
        p.recoil = w["recoil"]

        cx = p.x + Player.W // 2
        cy = p.y + 20

        for _ in range(w["bullets"]):
            b = Bullet(cx, cy, p.aim_angle, w, pid)
            self.bullets.append(b)

        self.play_snd("shoot")
        if self.net.active and pid == 0:
            self.net.emit_shoot(cx, cy, p.aim_angle, w["type"])
        if w["type"] == WeaponType.SNIPER: self.cam_shake = 12
        if w["type"] == WeaponType.ROCKET: self.cam_shake = 15

        # Recoil push
        p.vx -= math.cos(p.aim_angle) * w["recoil"] * 0.15
        p.vy -= math.sin(p.aim_angle) * w["recoil"] * 0.08

    def throw_grenade(self, pid):
        p = self.players[pid]
        if not p.alive or p.grenades <= 0: return
        p.grenades -= 1
        cx = p.x + Player.W // 2
        cy = p.y + 10
        speed = 12
        vx = math.cos(p.aim_angle) * speed
        vy = math.sin(p.aim_angle) * speed - 2
        self.grenades.append(Grenade(cx, cy, vx, vy, pid))

    def explode(self, x, y, radius=120, damage=80, owner_id=None):
        # Particles
        for _ in range(40):
            self.particles.append(ExplosionParticle(x, y))
        for _ in range(15):
            self.particles.append(SmokeParticle(x, y))
        # Screen shake
        self.cam_shake = 18
        # Damage players in radius
        for pid, p in self.players.items():
            if not p.alive: continue
            px, py = p.center
            dist = math.hypot(px - x, py - y)
            if dist < radius:
                dmg = int(damage * (1 - dist/radius))
                self._hit_player(pid, dmg, owner_id)
        self.play_snd("explode")

    def _hit_player(self, pid, damage, attacker_id):
        p = self.players[pid]
        if not p.alive: return
        actual = p.take_damage(damage, attacker_id)
        # Blood particles
        for _ in range(8):
            self.particles.append(BloodParticle(*p.center))
        if p.hp <= 0:
            p.alive = False
            p.deaths += 1
            p.respawn_timer = 4 * FPS
            if attacker_id is not None and attacker_id != pid:
                self.players[attacker_id].kills += 1
                self.kill_feed.add(self.players[attacker_id].name, p.name)
                self.play_snd("kill")
            else:
                self.play_snd("hit")
            for _ in range(25):
                self.particles.append(BloodParticle(*p.center))

    def update_camera(self):
        if not self.active_players: return
        # Average position of alive players (focus on player 1 if alive)
        if 0 in self.active_players and self.players[0].alive:
            focus = self.players[0]
        else:
            alive = [self.players[pid] for pid in self.active_players if self.players[pid].alive]
            if not alive: return
            focus = alive[0]

        target_x = focus.x - W // 2 + Player.W // 2
        target_y = focus.y - H // 2 + Player.H // 2
        target_x = max(0, min(self.game_map.width - W, target_x))
        target_y = max(-200, min(self.game_map.height - H, target_y))
        shake = getattr(self, 'cam_shake', 0)
        if shake > 0:
            target_x += random.randint(-shake, shake) * 0.3
            target_y += random.randint(-shake, shake) * 0.3
            self.cam_shake = max(0, shake - 1)
        self.cam_x += (target_x - self.cam_x) * 0.1
        self.cam_y += (target_y - self.cam_y) * 0.1

    def get_player_input(self, events, keys, mouse_pos, mouse_buttons):
        """
        Player 1: WASD + Mouse aim + LMB shoot + G grenade + R reload + F melee + Q switch
        Player 2: Arrow keys + aim via IJKL + Numpad0 shoot + . grenade + / reload
        """
        mx, my = mouse_pos
        world_mx = mx + self.cam_x
        world_my = my + self.cam_y

        for pid in self.active_players:
            p = self.players[pid]
            if not p.alive:
                # Respawn on Enter
                if p.respawn_timer <= 0:
                    for ev in events:
                        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                            self.respawn_player(pid)
                continue

            if pid == 0:
                # --- Player 1 (WASD + Mouse) ---
                # Movement
                if keys[pygame.K_a]: 
                    p.vx -= 1.4
                if keys[pygame.K_d]: 
                    p.vx += 1.4
                
                # Jetpack: W, Space or Right Click
                p.using_jetpack = keys[pygame.K_w] or keys[pygame.K_SPACE] or mouse_buttons[2]
                
                # Aim at mouse
                cx, cy = p.center
                dx = world_mx - cx
                dy = world_my - cy
                p.aim_angle = math.atan2(dy, dx)
                
                # Facing is determined by aim for P1
                p.facing = 1 if dx >= 0 else -1
                
                # Shoot: Left Click
                if mouse_buttons[0]:
                    self.handle_shoot(0)
                # Reload
                if keys[pygame.K_r]:
                    p.start_reload()
                # Switch weapon
                for ev in events:
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_q: p.switch_weapon()
                        if ev.key == pygame.K_g: self.throw_grenade(0)
                        if ev.key == pygame.K_f:
                            # Melee
                            for pid2, p2 in self.players.items():
                                if pid2 == 0 or not p2.alive: continue
                                if math.hypot(p.x-p2.x, p.y-p2.y) < 60:
                                    self._hit_player(pid2, 35, 0)

            elif pid == 1:
                # --- Player 2: Arrow keys ---
                if keys[pygame.K_LEFT]:  p.vx -= 1.4; p.facing = -1
                if keys[pygame.K_RIGHT]: p.vx += 1.4; p.facing = 1
                p.using_jetpack = keys[pygame.K_UP]
                # Aim via I/J/K/L
                aim_dx, aim_dy = 0, 0
                if keys[pygame.K_i]: aim_dy = -1
                if keys[pygame.K_k]: aim_dy = 1
                if keys[pygame.K_j]: aim_dx = -1; p.facing = -1
                if keys[pygame.K_l]: aim_dx = 1;  p.facing = 1
                if aim_dx or aim_dy:
                    p.aim_angle = math.atan2(aim_dy, aim_dx)
                else:
                    # Default aim direction
                    p.aim_angle = 0 if p.facing == 1 else math.pi
                # Shoot: Numpad 0 or right ctrl
                if keys[pygame.K_KP0] or keys[pygame.K_RCTRL]:
                    self.handle_shoot(1)
                if keys[pygame.K_KP_DIVIDE]:
                    p.start_reload()
                for ev in events:
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_KP_PERIOD: self.throw_grenade(1)
                        if ev.key == pygame.K_RSHIFT: p.switch_weapon()
                        if ev.key == pygame.K_KP_ENTER:
                            if p.respawn_timer <= 0: self.respawn_player(1)

            elif pid == 2:
                # Player 3 — simplified (gamepad or TFGH)
                if keys[pygame.K_t] and False: pass
                if keys[pygame.K_h]: p.vx -= 1.4; p.facing = -1
                if keys[pygame.K_j] and False: pass
                # Very basic control for P3
                p.aim_angle = 0 if p.facing == 1 else math.pi

            elif pid == 3:
                p.aim_angle = 0 if p.facing == 1 else math.pi

        # Joystick support (P3, P4)
        for ji, joy in enumerate(self.joysticks[:2]):
            pid = ji + 2
            if pid not in self.active_players: continue
            p = self.players[pid]
            if not p.alive: continue
            ax = joy.get_axis(0)
            ay = joy.get_axis(1)
            if abs(ax) > 0.2:
                p.vx += ax * 1.5
                p.facing = 1 if ax > 0 else -1
            p.using_jetpack = joy.get_button(0) if joy.get_numbuttons() > 0 else False
            # Right stick aim
            rx = joy.get_axis(2) if joy.get_numaxes() > 3 else 0
            ry = joy.get_axis(3) if joy.get_numaxes() > 3 else 0
            if abs(rx) > 0.2 or abs(ry) > 0.2:
                p.aim_angle = math.atan2(ry, rx)
            # Shoot: RT axis 5
            if joy.get_numaxes() > 5 and joy.get_axis(5) > 0.5:
                self.handle_shoot(pid)

    def update(self, events, keys, mouse_pos, mouse_buttons):
        if self.state != GameState.PLAYING: return

        self.timer -= 1
        self.get_player_input(events, keys, mouse_pos, mouse_buttons)

        # Players
        for pid in self.active_players:
            p = self.players[pid]
            p.update(self.game_map.platforms, self.game_map.width)
            if self.net.active and pid == 0: # Sync local player (usually ID 0)
                self.net.sync(p)
            # Respawn check
            if not self.players[pid].alive and self.players[pid].respawn_timer <= 0:
                pass  # Wait for Enter key

        # Bullets
        for b in self.bullets[:]:
            b.update(self.game_map.platforms)
            if not b.alive:
                self.bullets.remove(b)
                continue
            # Check player hits
            for pid, p in self.players.items():
                if pid == b.owner_id or not p.alive: continue
                if p.rect.collidepoint(b.x, b.y):
                    if b.explosive:
                        self.explode(b.x, b.y, owner_id=b.owner_id)
                    else:
                        self._hit_player(pid, b.damage, b.owner_id)
                        if b.emp:
                            self.players[pid].fuel = -100 # Disable jetpack for a while
                            self.players[pid].fuel_disabled = 600 # 10 sec disable
                    b.alive = False
                    break
            
            # Check remote player hits (Online)
            if b.alive and self.net.active:
                for rid, rdata in self.net.remote_players.items():
                    if rid == b.owner_id: continue
                    # Create a temporary rect for the remote player
                    r_rect = pygame.Rect(int(rdata['x']), int(rdata['y']), Player.W, Player.H)
                    if r_rect.collidepoint(b.x, b.y):
                        if b.explosive:
                            self.explode(b.x, b.y, owner_id=b.owner_id)
                        else:
                            # We can't hit them locally, we tell the server we hit them
                            self.net.emit_hit(rid, b.damage, b.owner_id)
                        b.alive = False
                        break

        # Grenades
        for g in self.grenades[:]:
            exploded = g.update(self.game_map.platforms)
            if exploded:
                self.explode(g.x, g.y, owner_id=g.owner_id)
                self.grenades.remove(g)

        # Particles
        self.particles = [p for p in self.particles if p.update()]

        # Weapon pickups
        for wp in self.weapon_pickups:
            wp.update()
            if wp.alive:
                for pid in self.active_players:
                    p = self.players[pid]
                    if p.alive and p.rect.colliderect(wp.rect):
                        p.pickup_weapon(wp.wtype)
                        wp.alive = False
                        wp.respawn_timer = 600

        # Health packs
        for hp in self.health_packs:
            hp.update()
            if hp.alive:
                for pid in self.active_players:
                    p = self.players[pid]
                    if p.alive and p.rect.colliderect(hp.rect):
                        p.hp = min(p.max_hp, p.hp + 40)
                        p.shield = min(p.max_shield, p.shield + 20)
                        hp.alive = False

        self.kill_feed.update()
        self.update_camera()

        # Win conditions
        for pid in self.active_players:
            if self.players[pid].kills >= self.score_limit:
                self.winner = pid
                self.state = GameState.GAME_OVER
        if self.timer <= 0:
            best = max(self.active_players, key=lambda pid: self.players[pid].kills)
            self.winner = best
            self.state = GameState.GAME_OVER

    def draw_game(self):
        # Background
        self.game_map.draw_bg(self.screen, self.cam_x)
        self.game_map.draw_terrain(self.screen, int(self.cam_x), int(self.cam_y))

        # Particles (behind players)
        for pt in self.particles:
            pt.draw(self.screen, self.cam_x, self.cam_y)

        # Weapon pickups
        for wp in self.weapon_pickups:
            wp.draw(self.screen, int(self.cam_x), int(self.cam_y))
        for hp in self.health_packs:
            hp.draw(self.screen, int(self.cam_x), int(self.cam_y))

        # Grenades
        for g in self.grenades:
            g.draw(self.screen, int(self.cam_x), int(self.cam_y))

        # Bullets
        for b in self.bullets:
            b.draw(self.screen, int(self.cam_x), int(self.cam_y))

        # Players
        for pid in self.active_players:
            self.players[pid].draw(self.screen, int(self.cam_x), int(self.cam_y))

        # Remote Players (Online)
        if self.net.active:
            for rid, rdata in self.net.remote_players.items():
                self._draw_remote_player(rdata)

        # --- UI & HUD (Always Draw) ---
        draw_hud(self.screen, self.players, self.active_players)
        draw_minimap(self.screen, self.players, self.game_map, self.active_players)
        self.kill_feed.draw(self.screen)

        # Crosshair
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(self.screen, (255, 255, 255, 150), (mx, my), 8, 1)
        pygame.draw.line(self.screen, (255, 255, 255, 150), (mx-12, my), (mx+12, my), 1)
        pygame.draw.line(self.screen, (255, 255, 255, 150), (mx, my-12), (mx, my+12), 1)

        # Timer
        secs = max(0, self.timer // FPS)
        mins = secs // 60
        ssec = secs % 60
        t_str = f"{mins}:{ssec:02d}"
        ts = BIG_FONT.render(t_str, True, C["white"] if secs > 30 else C["red"])
        self.screen.blit(ts, (W//2 - ts.get_width()//2, H-ts.get_height()-60))

        # Dead players: respawn prompt
        for pid in self.active_players:
            p = self.players[pid]
            if not p.alive and p.respawn_timer <= 0:
                pt = FONT.render("Press ENTER to Respawn", True, p.color)
                self.screen.blit(pt, (W//2 - pt.get_width()//2, H//2 + pid * 28))

    def _draw_remote_player(self, data):
        # Enhanced draw for remote players (no more simple rectangle!)
        sx = int(data['x'] - self.cam_x)
        sy = int(data['y'] - self.cam_y)
        cx, cy = sx + Player.W//2, sy + Player.H//2
        col = tuple(data.get('color', (200, 200, 200)))
        
        facing = data.get('facing', 1)
        aim_angle = data.get('aim', 0)
        hp = data.get('hp', 100)
        max_hp = data.get('max_hp', 100)

        # Shadow
        shadow_surf = pygame.Surface((30, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0,0,0,80), (0,0,30,8))
        self.screen.blit(shadow_surf, (cx-15, sy+Player.H-2))
        
        # Body
        body_rect = pygame.Rect(sx+4, sy+14, Player.W-8, 22)
        pygame.draw.rect(self.screen, col, body_rect, border_radius=6)
        
        # Head
        head_col = tuple(min(255, c+30) for c in col)
        pygame.draw.ellipse(self.screen, head_col, (sx+5, sy+1, Player.W-10, 22))
        
        # Visor
        visor_col = (40, 160, 255) if hp > 0 else (50, 50, 80)
        visor_x = cx + (3 * facing)
        pygame.draw.ellipse(self.screen, visor_col, (visor_x-6, sy+6, 12, 8))

        # Weapon (simplified line)
        w_len = 25
        w_end_x = cx + int(math.cos(aim_angle) * w_len)
        w_end_y = (sy+20) + int(math.sin(aim_angle) * w_len)
        pygame.draw.line(self.screen, (40, 40, 40), (cx, sy+20), (w_end_x, w_end_y), 5)

        # Name
        ns = SMALL_FONT.render(data['name'], True, col)
        self.screen.blit(ns, (cx - ns.get_width()//2, sy - 18))
        
        # HP Bar
        bar_w = 30
        pygame.draw.rect(self.screen, C["hp_empty"], (cx-15, sy-8, bar_w, 4))
        hp_pct = max(0, min(1, hp / max_hp))
        pygame.draw.rect(self.screen, C["hp_full"], (cx-15, sy-8, int(bar_w*hp_pct), 4))

    def draw_menu(self):
        # Animated background
        t = pygame.time.get_ticks() * 0.001
        self.screen.fill(C["bg"])
        # Scrolling star field
        for i in range(100):
            x = (i * 13 + int(t * (10 + (i % 5)*5))) % W
            y = (i * 27) % H
            r = 1 if i % 2 == 0 else 2
            pygame.draw.circle(self.screen, (200, 200, 255, 150), (x, y), r)

        # Title with neon glow
        off = math.sin(t * 1.5) * 6
        for blur in range(4, 0, -1):
            ts = BIG_FONT.render("MINI MILITIA", True, (*PLAYER_COLORS[0], 50))
            self.screen.blit(ts, (W//2 - ts.get_width()//2, 100 + off + blur*2))
        
        title_surf = BIG_FONT.render("MINI MILITIA", True, C["white"])
        self.screen.blit(title_surf, (W//2 - title_surf.get_width()//2, 100 + off))
        
        sub = FONT.render("Python Edition  •  Advanced Combat  •  Multiplayer Royale", True, C["mid_gray"])
        self.screen.blit(sub, (W//2 - sub.get_width()//2, 168))
        
        # Add decorative lines
        pygame.draw.line(self.screen, (60, 90, 180, 100), (W//2 - 200, 195), (W//2 + 200, 195), 2)

        # Player count / map selector
        info_x = W//2 - 60
        mname = self.map_names[self.map_id]
        cname = self.player_classes[self.player_class_id]["name"]
        ps = FONT.render(f"Players: {self.num_players}   Map: {mname}   Class: {cname}", True, (160, 200, 255))
        self.screen.blit(ps, (W//2 - ps.get_width()//2, 220))

        # Visual Player List
        px_start = W//2 - (self.num_players * 50)
        for i in range(self.num_players):
            col = PLAYER_COLORS[i]
            x = px_start + i * 100
            y = 260
            # Small player icon
            pygame.draw.circle(self.screen, col, (x + 25, y), 12)
            pygame.draw.rect(self.screen, col, (x + 10, y + 5, 30, 20), border_radius=4)
            name_ts = TINY_FONT.render(PLAYER_NAMES[i], True, col)
            self.screen.blit(name_ts, (x + 25 - name_ts.get_width()//2, y + 30))

        for btn in self.menu_buttons.values():
            btn.draw(self.screen)

        # Controls hint
        ctrl = TINY_FONT.render("P1: WASD+Mouse  |  P2: Arrows+IJKL  |  P3/P4: Controller", True, (80, 100, 140))
        self.screen.blit(ctrl, (W//2 - ctrl.get_width()//2, H-30))

    def draw_map_select(self):
        self.screen.fill(C["bg"])
        t = BIG_FONT.render("SELECT MAP", True, C["white"])
        self.screen.blit(t, (W//2 - t.get_width()//2, 100))
        for btn in self.map_buttons.values():
            btn.draw(self.screen)

    def draw_pause(self):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((5, 8, 20, 180))
        self.screen.blit(overlay)

        t = BIG_FONT.render("PAUSED", True, C["white"])
        self.screen.blit(t, (W//2 - t.get_width()//2, 190))

        for btn in self.pause_buttons.values():
            btn.draw(self.screen)

    def draw_gameover(self):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((10, 15, 30, 220))
        self.screen.blit(overlay, (0, 0))
        
        t = BIG_FONT.render("BATTLE ENDED", True, C["white"])
        self.screen.blit(t, (W//2 - t.get_width()//2, 100))
        
        # Show winner stats
        sy = 200
        sorted_pids = sorted(self.active_players, key=lambda pid: self.players[pid].kills, reverse=True)
        for rank, pid in enumerate(sorted_pids):
            p = self.players[pid]
            y = sy + rank * 44
            
            # Use a temporary surface for transparency blending
            row_surf = pygame.Surface((400, 36), pygame.SRCALPHA)
            pygame.draw.rect(row_surf, (*p.color, 60), (0, 0, 400, 36), border_radius=6)
            pygame.draw.rect(row_surf, (*p.color, 180), (0, 0, 400, 36), 2, border_radius=6)
            self.screen.blit(row_surf, (W//2-200, y))
            
            kd_val = p.kills / max(1, p.deaths)
            txt = FONT.render(f"#{rank+1}  {p.name:<10}  {p.kills} K / {p.deaths} D  ({kd_val:.1f} K/D)", True, C["white"])
            self.screen.blit(txt, (W//2 - txt.get_width()//2, y + 8))
        
        for btn in self.gameover_buttons.values():
            btn.draw(self.screen)

    def draw_scoreboard(self):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((5, 8, 20, 220))
        self.screen.blit(overlay)
        t = BIG_FONT.render("SCOREBOARD", True, C["white"])
        self.screen.blit(t, (W//2 - t.get_width()//2, 80))
        y = 160
        for pid in sorted(self.active_players, key=lambda p: self.players[p].kills, reverse=True):
            p = self.players[pid]
            row = FONT.render(f"{p.name}   K:{p.kills}  D:{p.deaths}  HP:{p.hp}", True, p.color)
            self.screen.blit(row, (W//2 - row.get_width()//2, y))
            y += 36
        hint = SMALL_FONT.render("[TAB] Close", True, (100, 120, 160))
        self.screen.blit(hint, (W//2 - hint.get_width()//2, H-40))

    def run(self):
        self.cam_shake = 0
        show_scoreboard = False

        while self.running:
            self.mouse_click = False
            events = pygame.event.get()
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            mouse_buttons = pygame.mouse.get_pressed()
            
            for ev in events:
                if ev.type == pygame.QUIT:
                    self.running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.mouse_click = True
                
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        if self.state == GameState.PLAYING:
                            self.state = GameState.PAUSED
                        elif self.state == GameState.PAUSED:
                            self.state = GameState.PLAYING
                    if ev.key == pygame.K_TAB:
                        show_scoreboard = not show_scoreboard
                    if ev.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()

            # State machine
            if self.state == GameState.MAIN_MENU:
                pygame.mouse.set_visible(True)
                self.draw_menu()
                if self.menu_buttons["play"].update(mouse_pos, self.mouse_click):
                    pygame.mouse.set_visible(False)
                    self.start_game()
                if self.menu_buttons["multi"].update(mouse_pos, self.mouse_click):
                    self.state = GameState.MULTIPLAYER
                    self.net.connect() # Default addr
                if self.menu_buttons["players"].update(mouse_pos, self.mouse_click):
                    self.num_players = (self.num_players % 4) + 1
                    if self.num_players < 2: self.num_players = 2
                if self.menu_buttons["map"].update(mouse_pos, self.mouse_click):
                    self.state = GameState.MAP_SELECT
                    self.play_snd("pickup")
                if self.menu_buttons["settings"].update(mouse_pos, self.mouse_click):
                    self.state = GameState.SETTINGS
                    self.play_snd("pickup")
                if self.menu_buttons["quit"].update(mouse_pos, self.mouse_click):
                    self.running = False

            elif self.state == GameState.MULTIPLAYER:
                self.net.draw_multi_menu()
                if not self.net.room_code:
                    if self.multi_buttons["create"].update(mouse_pos, self.mouse_click) and self.net.active:
                        self.net.create_room()
                    if self.multi_buttons["join"].update(mouse_pos, self.mouse_click) and self.net.active:
                        # Simple logic: for demo, join a fixed room or random
                        import tkinter.simpledialog as sd
                        import tkinter as tk
                        root = tk.Tk(); root.withdraw()
                        code = sd.askstring("Join", "Enter 4-char Room Code:")
                        if code: self.net.join_room(code)
                        root.destroy()
                    if self.multi_buttons["back"].update(mouse_pos, self.mouse_click):
                        self.state = GameState.MAIN_MENU

            elif self.state == GameState.PLAYING:
                pygame.mouse.set_visible(False)
                self.update(events, keys, mouse_pos, mouse_buttons)
                self.draw_game()
                # Scoreboard if TAB held (implied in run)
                # Buttons hover=False
                for btn in self.menu_buttons.values(): btn.hover = False

            elif self.state == GameState.PAUSED:
                pygame.mouse.set_visible(True)
                self.draw_game()
                self.draw_pause()
                if self.pause_buttons["resume"].update(mouse_pos, self.mouse_click):
                    pygame.mouse.set_visible(False)
                    self.state = GameState.PLAYING
                if self.pause_buttons["menu"].update(mouse_pos, self.mouse_click):
                    self.state = GameState.MAIN_MENU
                if self.pause_buttons["quit"].update(mouse_pos, self.mouse_click):
                    self.running = False

            elif self.state == GameState.SETTINGS:
                self.net.draw_settings_preview()
                
                # Cycling Time
                time_btn = Button(W//2-110, 420, 220, 48, f"⏰ TIME: {self.time_options[self.time_idx]//60}m", (150, 100, 30))
                if time_btn.update(mouse_pos, self.mouse_click):
                    self.time_idx = (self.time_idx + 1) % len(self.time_options)
                    self.game_time = self.time_options[self.time_idx] * FPS
                    self.play_snd("pickup")
                time_btn.draw(self.screen)

                # Cycling button
                btn_cycle = Button(W//2-110, 480, 220, 48, "🔄 CYCLE CLASS", (40, 100, 200))
                if btn_cycle.update(mouse_pos, self.mouse_click):
                    self.player_class_id = (self.player_class_id + 1) % len(self.player_classes)
                    self.play_snd("pickup")
                btn_cycle.draw(self.screen)
                
                btn_back = Button(W//2-110, 540, 220, 48, "↩  BACK", (100, 30, 30))
                if btn_back.update(mouse_pos, self.mouse_click):
                    self.state = GameState.MAIN_MENU
                btn_back.draw(self.screen)

            elif self.state == GameState.GAME_OVER:
                pygame.mouse.set_visible(True)
                self.draw_game()
                self.draw_gameover()
                if self.gameover_buttons["rematch"].update(mouse_pos, self.mouse_click):
                    self.start_game()
                if self.gameover_buttons["menu"].update(mouse_pos, self.mouse_click):
                    self.state = GameState.MAIN_MENU

            elif self.state == GameState.MAP_SELECT:
                self.draw_map_select()
                for mid, btn in self.map_buttons.items():
                    if mid == "back":
                        if btn.update(mouse_pos, self.mouse_click):
                            self.state = GameState.MAIN_MENU
                    elif btn.update(mouse_pos, self.mouse_click):
                        self.map_id = mid
                        self.state = GameState.MAIN_MENU
                        self.play_snd("pickup")
            # --- New Settings Selection state (hijacking the button) ---
            # I'll just change GameState.MAIN_MENU to allow a new settings sub-view if needed
            # But the user asked for it in settings, so I'll just keep it in menu for now or add a mode.

            elif self.state == GameState.MULTIPLAYER:
                self.net.draw_multi_menu()
                if not self.net.room_code:
                    if self.multi_buttons["create"].update(mouse_pos, self.mouse_click) and self.net.active:
                        self.net.create_room()
                    if self.multi_buttons["join"].update(mouse_pos, self.mouse_click) and self.net.active:
                        # Simple logic: for demo, join a fixed room or random
                        import tkinter.simpledialog as sd
                        import tkinter as tk
                        root = tk.Tk(); root.withdraw()
                        code = sd.askstring("Join", "Enter 4-char Room Code:")
                        if code: self.net.join_room(code)
                        root.destroy()
                    if self.multi_buttons["back"].update(mouse_pos, self.mouse_click):
                        self.state = GameState.MAIN_MENU

            # FPS counter
            fps = int(self.clock.get_fps())
            fps_s = TINY_FONT.render(f"FPS: {fps}", True, (80, 100, 80))
            self.screen.blit(fps_s, (W-60, H-18))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Make globals available before Game init calls font render
    FONT = SMALL_FONT = TINY_FONT = BIG_FONT = None
    Game().run()