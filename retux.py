#!/usr/bin/env python3

# reTux
# Copyright (C) 2014, 2015 Julian Marchant <onpon4@riseup.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

__version__ = "0.1a1"

import argparse
import json
import math
import os
import random
import sys
import warnings
import weakref

import sge
import six
import xsge_gui
import xsge_path
import xsge_physics
import xsge_tmx


if getattr(sys, "frozen", False):
    __file__ = sys.executable

DATA = os.path.join(os.path.dirname(__file__), "data")
CONFIG = os.path.join(os.path.expanduser("~"), ".config", "retux")
JOYSTICK_THRESHOLD = 0.7

parser = argparse.ArgumentParser()
parser.add_argument(
    "--scale-basic",
    help="Use basic rather than smooth scaling. Faster if you're in fullscreen or resizing the window, but much uglier.",
    action="store_true")
parser.add_argument(
    "--nodelta",
    help="Disable delta timing. Causes the game to slow down when it can't run at 60 FPS instead of becoming choppier.",
    action="store_true")
parser.add_argument(
    "--js-threshold", default=JOYSTICK_THRESHOLD, type=float,
    help="The threshold at which an axis is considered to be triggered, as a float between 0 and 1. (Default: {})".format(JOYSTICK_THRESHOLD))
parser.add_argument(
    "-d", "--datadir",
    help='Where to load the game data from (Default: "{}")'.format(DATA))
parser.add_argument(
    "--record",
    help="Start the indicated level and record player actions in a timeline. Useful for making cutscenes.")
args = parser.parse_args()

SCALE_SMOOTH = not args.scale_basic
DELTA = not args.nodelta
JOYSTICK_THRESHOLD = args.js_threshold
if args.datadir:
    DATA = args.datadir
RECORD = args.record

xsge_gui.joystick_threshold = JOYSTICK_THRESHOLD

SCREEN_SIZE = [800, 448]
TILE_SIZE = 32
FPS = 60
DELTA_MIN = 20

DEFAULT_LEVEL_TIME_BONUS = 30000

TUX_ORIGIN_X = 28
TUX_ORIGIN_Y = 16
TUX_KICK_TIME = 10

GRAVITY = 0.25

PLAYER_WALK_SPEED = 2
PLAYER_RUN_SPEED = 4
PLAYER_MAX_SPEED = 5
PLAYER_ACCELERATION = 0.2
PLAYER_AIR_ACCELERATION = 0.1
PLAYER_FRICTION = 0.17
PLAYER_AIR_FRICTION = 0.03
PLAYER_JUMP_HEIGHT = 4 * TILE_SIZE + 2
PLAYER_RUN_JUMP_HEIGHT = 5 * TILE_SIZE + 2
PLAYER_STOMP_HEIGHT = TILE_SIZE / 2
PLAYER_FALL_SPEED = 5
PLAYER_SLIDE_ACCEL = 0.3
PLAYER_SLIDE_SPEED = 1
PLAYER_WALK_FRAMES_PER_PIXEL = 2 / 17
PLAYER_RUN_IMAGE_SPEED = 0.25
PLAYER_HITSTUN = 120
PLAYER_DIE_HEIGHT = 6 * TILE_SIZE
PLAYER_DIE_FALL_SPEED = 8

SNOWMAN_WALK_SPEED = 2
SNOWMAN_STRONG_WALK_SPEED = 3
SNOWMAN_FINAL_WALK_SPEED = 4
SNOWMAN_STUNNED_WALK_SPEED = 6
SNOWMAN_ACCELERATION = 0.1
SNOWMAN_STRONG_ACCELERATION = 0.2
SNOWMAN_FINAL_ACCELERATION = 0.5
SNOWMAN_HOP_HEIGHT = 2 * TILE_SIZE
SNOWMAN_JUMP_HEIGHT = 7 * TILE_SIZE
SNOWMAN_JUMP_TRIGGER = 2 * TILE_SIZE
SNOWMAN_STOMP_DELAY = 30
SNOWMAN_WALK_FRAMES_PER_PIXEL = 1 / 4
SNOWMAN_HP = 5
SNOWMAN_STRONG_STAGE = 2
SNOWMAN_FINAL_STAGE = 3
SNOWMAN_HITSTUN = 120

MAX_HP = 5
HP_POINTS = 1000
TIMER_FRAMES = 40
HEAL_COINS = 20

CEILING_LAX = 10
STOMP_LAX = 8

BLOCK_HIT_HEIGHT = 8
ITEM_HIT_HEIGHT = 16
COIN_COLLECT_TIME = 30
COIN_COLLECT_SPEED = 2
ITEM_SPAWN_SPEED = 1

SECOND_POINTS = 100
COIN_POINTS = 100
ENEMY_KILL_POINTS = 50
AMMO_POINTS = 50
TUXDOLL_POINTS = 5000

CAMERA_SPEED_FACTOR = 1 / 2
CAMERA_OFFSET_FACTOR = 10
CAMERA_MARGIN_TOP = 4 * TILE_SIZE
CAMERA_MARGIN_BOTTOM = 5 * TILE_SIZE

WARP_LAX = 12
WARP_SPEED = 1.5

SHAKE_FRAME_TIME = FPS / DELTA_MIN
SHAKE_AMOUNT = 3

ENEMY_WALK_SPEED = 1
ENEMY_FALL_SPEED = 5
ENEMY_SLIDE_SPEED = 0.3
ENEMY_HIT_BELOW_HEIGHT = TILE_SIZE * 3 / 4
SNOWBALL_BOUNCE_HEIGHT = TILE_SIZE * 3 + 2
KICK_FORWARD_SPEED = 8
KICK_FORWARD_HEIGHT = TILE_SIZE * 3 / 4
KICK_UP_HEIGHT = 5.5 * TILE_SIZE
ICEBLOCK_GRAVITY = 0.6
ICEBLOCK_FALL_SPEED = 9
ICEBLOCK_FRICTION = 0.1
ICEBLOCK_DASH_SPEED = 7
JUMPY_BOUNCE_HEIGHT = TILE_SIZE * 4
BOMB_GRAVITY = 0.6
BOMB_TICK_TIME = 8
EXPLOSION_TIME = FPS * 3 / 4
ICICLE_SHAKE_TIME = FPS
ICICLE_GRAVITY = 0.75
ICICLE_FALL_SPEED = 12
CRUSHER_GRAVITY = 1
CRUSHER_FALL_SPEED = 15
CRUSHER_RISE_SPEED = 2
CRUSHER_CRUSH_TIME = FPS * 2 / 3
CRUSHER_SHAKE_NUM = 2
THAW_FPS = 15
THAW_TIME_DEFAULT = FPS * 5
THAW_WARN_TIME = FPS

ROCK_GRAVITY = 0.6
ROCK_FALL_SPEED = 10
ROCK_FRICTION = 0.4

SPRING_JUMP_HEIGHT = 8 * TILE_SIZE + 11

FLOWER_FALL_SPEED = 5
FLOWER_THROW_SPEED = 8
FLOWER_THROW_HEIGHT = TILE_SIZE / 2
FLOWER_THROW_UP_HEIGHT = TILE_SIZE * 3 / 2

FIREBALL_AMMO = 19
FIREBALL_SPEED = 8
FIREBALL_GRAVITY = 0.5
FIREBALL_FALL_SPEED = 5
FIREBALL_BOUNCE_HEIGHT = TILE_SIZE / 2
FIREBALL_UP_HEIGHT = TILE_SIZE * 3 / 2

ICEBULLET_AMMO = 19
ICEBULLET_SPEED = 8

COINBRICK_COINS = 20
COINBRICK_DECAY_TIME = 25

ICE_CRACK_TIME = 20
ICE_REFREEZE_RATE = 2/3

ENEMY_ACTIVE_RANGE = 32
ICEBLOCK_ACTIVE_RANGE = 800
BULLET_ACTIVE_RANGE = 200
ROCK_ACTIVE_RANGE = 800
TILE_ACTIVE_RANGE = 928
DEATHZONE = 2 * TILE_SIZE

DEATH_FADE_TIME = 3000
DEATH_RESTART_WAIT = FPS

WIN_COUNT_START_TIME = 120
WIN_COUNT_CONTINUE_TIME = 45
WIN_COUNT_MULT = 111
WIN_COUNT_AMOUNT = 1
WIN_FINISH_DELAY = 120

MAP_SPEED = 5

TEXT_SPEED = 1000

SAVE_NSLOTS = 10
MENU_MAX_ITEMS = 14

backgrounds = {}
loaded_music = {}
tux_grab_sprites = {}

fullscreen = False
sound_enabled = True
music_enabled = True
left_key = ["left"]
right_key = ["right"]
up_key = ["up"]
down_key = ["down"]
jump_key = ["space"]
action_key = ["ctrl_left"]
sneak_key = ["shift_left"]
left_js = [(0, "axis-", 0)]
right_js = [(0, "axis+", 0)]
up_js = [(0, "axis-", 1)]
down_js = [(0, "axis+", 1)]
jump_js = [(0, "button", 1)]
action_js = [(0, "button", 0)]
sneak_js = [(0, "button", 2)]
save_slots = [None for _ in six.moves.range(SAVE_NSLOTS)]

current_save_slot = None
current_levelset = "retux.json"
worldmaps = []
levels = []
level_names = {}
level_timers = {}
cleared_levels = []
tuxdolls_available = []
tuxdolls_found = []
current_worldmap = None
current_worldmap_space = None
current_level = 0

score = 0

current_areas = {}
main_area = None
level_cleared = False


class Game(sge.Game):

    def event_mouse_button_press(self, button):
        if button == "middle":
            self.event_close()

    def event_close(self):
        global level_timers
        global score

        if main_area is not None:
            if level_timers.setdefault(main_area, 0) < 0:
                score -= level_timers[main_area] * SECOND_POINTS
                level_timers[main_area] = 0
        save_game()
        self.end()

    def event_paused_close(self):
        self.event_close()


class Level(sge.Room):

    """Handles levels."""

    def __init__(self, objects=(), width=None, height=None, views=None,
                 background=None, background_x=0, background_y=0, name=None,
                 bgname=None, music=None, time_bonus=DEFAULT_LEVEL_TIME_BONUS,
                 spawn=None, timeline=None):
        self.fname = None
        self.name = name
        self.music = music
        self.time_bonus = time_bonus
        self.spawn = spawn
        self.points = 0
        self.timeline_objects = {}
        self.warps = []
        self.shake_queue = 0
        self.view_frozen = False

        if bgname is not None:
            background = backgrounds.get(bgname, background)

        self.load_timeline(timeline)

        super(Level, self).__init__(objects, width, height, views, background,
                                    background_x, background_y)
        self.add(gui_handler)

    def load_timeline(self, timeline):
        self.timeline = {}
        self.timeline_step = 0
        if timeline is not None:
            fname = os.path.join(DATA, "timelines", timeline)
            with open(fname, 'r') as f:
                jt = json.load(f)

            for i in jt:
                self.timeline[eval(i)] = jt[i]

    def add_timeline_object(self, obj):
        if obj.ID is not None:
            self.timeline_objects[obj.ID] = weakref.ref(obj)

    def add_points(self, x):
        if main_area not in cleared_levels:
            self.points += x

    def show_hud(self):
        if self.points:
            score_text = "{}+{}".format(score, self.points)
        else:
            score_text = str(score)
        time_bonus = level_timers.get(main_area, 0)
        text = "Score\n{}\n\nTime {}\n{}".format(
            score_text, "Bonus" if time_bonus >= 0 else "Penalty",
            abs(time_bonus))
        sge.game.project_text(font, text, sge.game.width / 2, 0,
                              color=sge.Color("white"), halign="center")

        if main_area in tuxdolls_available:
            if main_area in tuxdolls_found:
                s = tuxdoll_sprite
            else:
                s = tuxdoll_transparent_sprite
            sge.game.project_sprite(s, 0, sge.game.width / 2, font.size * 6)

    def shake(self, num=1):
        shaking = (self.shake_queue or "shake_up" in self.alarms or
                   "shake_down" in self.alarms)
        self.shake_queue = max(self.shake_queue, num)
        if not shaking:
            self.event_alarm("shake_down")

    def die(self):
        global current_areas
        current_areas = {}
        self.death_time = DEATH_FADE_TIME
        self.death_time_bonus = level_timers.setdefault(main_area, 0)
        if "timer" in self.alarms:
            del self.alarms["timer"]
        sge.Music.clear_queue()
        sge.Music.stop(DEATH_FADE_TIME)

    def return_to_map(self):
        m = Worldmap.load(current_worldmap)

        for obj in m.objects:
            if (isinstance(obj, MapSpace) and
                    obj.level == main_area):
                x = obj.x
                y = obj.y
                if obj.sprite:
                    x += obj.sprite.width / 2
                    y += obj.sprite.height / 2
                arg = (x, y)
                break
        else:
            arg = None

        save_game()
        m.start(transition="iris_out", transition_time=750, transition_arg=arg)

    def event_room_start(self):
        global level_timers

        self.add(coin_animation)
        self.add(bonus_animation)

        self.event_room_resume()

    def event_room_resume(self):
        global main_area

        self.won = False
        self.win_count_points = False
        self.win_count_time = False
        self.death_time = None
        self.alarms["timer"] = TIMER_FRAMES
        play_music(self.music)

        if main_area is None:
            main_area = self.fname

        if main_area not in level_timers:
            level_timers[main_area] = self.time_bonus

        players = []
        spawn_point = None

        for obj in self.objects:
            if isinstance(obj, (Spawn, WarpSpawn)):
                if self.spawn is not None and obj.spawn_id == self.spawn:
                    spawn_point = obj

                if isinstance(obj, Warp) and obj not in self.warps:
                    self.warps.append(obj)
            elif isinstance(obj, Player):
                players.append(obj)

        del_warps = []
        for warp in self.warps:
            if warp not in self.objects:
                del_warps.append(warp)
        for warp in del_warps:
            self.warps.remove(warp)

        if spawn_point is not None:
            for player in players:
                player.x = spawn_point.x
                player.y = spawn_point.y
                if player.view is not None:
                    player.view.x = player.x - player.view.width / 2
                    player.view.y = player.y - player.view.height / 2

                # This is deliberate. It's so other kinds of spawn
                # points can exist, like checkpoints.
                if isinstance(spawn_point, WarpSpawn):
                    player.visible = False
                    player.tangible = False
                    player.warping = True
                    spawn_point.follow_start(player, WARP_SPEED)

    def event_step(self, time_passed, delta_mult):
        global level_timers
        global current_level
        global score
        global current_areas
        global main_area
        global level_cleared

        self.show_hud()

        # Timeline events
        t_keys = sorted(self.timeline.keys())
        for i in t_keys:
            if i <= self.timeline_step:
                for command in self.timeline[i]:
                    command = command.split(None, 1)
                    if command:
                        if len(command) >= 2:
                            command, arg = command[:2]
                        else:
                            command = command[0]
                            arg = ""

                        if command == "setattr":
                            args = arg.split(None, 2)
                            if len(args) >= 3:
                                obj, name, value = args[:3]

                                try:
                                    value = int(value)
                                except ValueError:
                                    try:
                                        value = float(value)
                                    except ValueError:
                                        pass

                                if obj in self.timeline_objects:
                                    obj = self.timeline_objects[obj]()
                                    if obj is not None:
                                        setattr(obj, name, value)
                                elif obj == "__level__":
                                    setattr(self, name, value)
                        elif command == "call":
                            args = arg.split(None, 1)
                            if len(args) >= 2:
                                obj, method = args[:2]

                                if obj in self.timeline_objects:
                                    obj = self.timeline_objects[obj]()
                                    if obj is not None:
                                        getattr(obj, method, lambda: None)()
                                elif obj == "__level__":
                                    getattr(self, method, lambda: None)()
                        elif command == "dialog":
                            args = arg.split(None, 1)
                            if len(args) >= 2:
                                portrait, text = args[:2]
                                sprite = portrait_sprites.get(portrait)
                                DialogBox(gui_handler, text, sprite).show()
                        elif command == "play_music":
                            self.music = arg
                            play_music(arg)
                        elif command == "timeline":
                            self.load_timeline(arg)
                del self.timeline[i]
            else:
                break

        self.timeline_step += delta_mult

        if self.death_time is not None:
            a = int(255 * (DEATH_FADE_TIME - self.death_time) / DEATH_FADE_TIME)
            sge.game.project_rectangle(0, 0, sge.game.width, sge.game.height,
                                       fill=sge.Color((0, 0, 0, min(a, 255))))

            time_bonus = level_timers.setdefault(main_area, 0)
            if time_bonus < 0:
                amt = int(math.copysign(
                    min(math.ceil(abs(self.death_time_bonus) * 3 * time_passed /
                                  DEATH_FADE_TIME),
                        abs(time_bonus)),
                    time_bonus))
                if amt:
                    score += amt
                    level_timers[main_area] -= amt
                    play_sound(coin_sound)

            if self.death_time < 0:
                self.death_time = None
                self.alarms["death"] = DEATH_RESTART_WAIT
            else:
                self.death_time -= time_passed
        elif "death" in self.alarms:
            sge.game.project_rectangle(0, 0, sge.game.width, sge.game.height,
                                       fill=sge.Color("black"))

        if self.won:
            if self.win_count_points:
                if self.points:
                    amt = int(math.copysign(
                        min(WIN_COUNT_AMOUNT * delta_mult * WIN_COUNT_MULT,
                            abs(self.points)),
                        self.points))
                    score += amt
                    self.points -= amt
                    play_sound(coin_sound)
                else:
                    self.win_count_points = False
                    self.alarms["win_count_time"] = WIN_COUNT_CONTINUE_TIME
            elif self.win_count_time:
                time_bonus = level_timers.setdefault(main_area, 0)
                if time_bonus:
                    amt = int(math.copysign(
                        min(WIN_COUNT_AMOUNT * delta_mult * WIN_COUNT_MULT,
                            abs(time_bonus)),
                        time_bonus))
                    score += amt
                    level_timers[main_area] -= amt
                    play_sound(coin_sound)
                else:
                    self.win_count_time = False
                    if main_area not in cleared_levels:
                        self.alarms["win_count_hp"] = WIN_COUNT_CONTINUE_TIME
                    else:
                        self.alarms["win"] = WIN_FINISH_DELAY
            elif (not level_win_music.playing and
                  "win_count_points" not in self.alarms and
                  "win_count_time" not in self.alarms and
                  "win_count_hp" not in self.alarms and
                  "win" not in self.alarms):
                if main_area not in cleared_levels:
                    cleared_levels.append(main_area)

                current_areas = {}
                level_cleared = True

                if current_worldmap:
                    self.return_to_map()
                else:
                    current_level += 1
                    save_game()
                    if current_level < len(levels):
                        level = self.__class__.load(levels[current_level])
                        level.start(transition="fade")
                    else:
                        # TODO: Ending
                        if current_save_slot is not None:
                            save_slots[current_save_slot] = None
                        sge.game.start_room.start()

    def event_paused_step(self, time_passed, delta_mult):
        self.show_hud()

    def event_alarm(self, alarm_id):
        global level_timers
        global score

        if alarm_id == "timer":
            level_timers.setdefault(main_area, 0)
            level_timers[main_area] -= SECOND_POINTS
            self.alarms["timer"] = TIMER_FRAMES
        elif alarm_id == "shake_down":
            self.shake_queue -= 1
            for view in self.views:
                view.yport += SHAKE_AMOUNT
            self.alarms["shake_up"] = SHAKE_FRAME_TIME
        elif alarm_id == "shake_up":
            for view in self.views:
                view.yport -= SHAKE_AMOUNT
            if self.shake_queue:
                self.alarms["shake_down"] = SHAKE_FRAME_TIME
        elif alarm_id == "death":
            if current_worldmap:
                self.return_to_map()
            elif main_area is not None:
                save_game()
                r = self.__class__.load(main_area)
                r.start()
        elif alarm_id == "win_count_points":
            if self.points > 0:
                self.win_count_points = True
            else:
                self.win_count_time = True
        elif alarm_id == "win_count_time":
            self.win_count_time = True
        elif alarm_id == "win_count_hp":
            for obj in self.objects:
                if isinstance(obj, Player) and obj.hp > 0:
                    obj.hp -= 1
                    score += HP_POINTS
                    play_sound(heal_sound)
                    self.alarms["win_count_hp"] = WIN_COUNT_CONTINUE_TIME
                    break
            else:
                self.alarms["win"] = WIN_FINISH_DELAY

    def event_key_press(self, key, char):
        global level_timers
        global score

        if self.death_time is not None or "death" in self.alarms:
            if level_timers.setdefault(main_area, 0) >= 0:
                sge.Music.stop()
                self.alarms["death"] = 0
        else:
            if key == "f11":
                sge.game.fullscreen = not sge.game.fullscreen
            elif key == "escape":
                sge.game.mouse.visible = True
                m = "Are you sure you want to quit?"
                if xsge_gui.show_message(message=m, buttons=["No", "Yes"],
                                         default=0):
                    if level_timers.setdefault(main_area, 0) < 0:
                        score -= level_timers[main_area] * SECOND_POINTS
                        level_timers[main_area] = 0
                    save_game()
                    sge.game.start_room.start()
                sge.game.mouse.visible = False
            elif key in ("enter", "p"):
                if not self.won:
                    sge.Music.pause()
                    play_sound(pause_sound)
                    sge.game.pause(pause_sprite)

    def event_paused_key_press(self, key, char):
        if key in ("enter", "p"):
            play_sound(pause_sound)
            sge.Music.unpause()
            sge.game.unpause()
        else:
            self.event_key_press(key, char)

    @classmethod
    def load(cls, fname):
        if fname in current_areas:
            return current_areas[fname]
        else:
            try:
                r = xsge_tmx.load(os.path.join(DATA, "levels", fname), cls=cls,
                                  types=TYPES)
            except IOError as e:
                m = "An error occurred when trying to load the level:\n\n{}".format(e)
                if sge.game.current_room is not None:
                    xsge_gui.show_message(message=m, title="Error",
                                          buttons=["Ok"])
                else:
                    print(m)
                return None
            else:
                r.fname = fname
                current_areas[fname] = r
                return r


class LevelRecorder(Level):

    def __init__(self, *args, **kwargs):
        super(LevelRecorder, self).__init__(*args, **kwargs)
        self.recording = {}

    def add_recording_event(self, command):
        self.recording.setdefault(self.timeline_step, []).append(command)

    def event_key_press(self, key, char):
        if key == "escape":
            jt = self.recording

            import time
            fname = "recording_{}.json".format(time.time())
            with open(fname, 'w') as f:
                json.dump(jt, f, indent=4, sort_keys=True)

            sge.game.end()
        if key in left_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == left_key.index(key)):
                    self.add_recording_event(
                        "setattr {} left_pressed 1".format(obj.ID))
        if key in right_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == right_key.index(key)):
                    self.add_recording_event(
                        "setattr {} right_pressed 1".format(obj.ID))
        if key in up_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == up_key.index(key)):
                    self.add_recording_event(
                        "setattr {} up_pressed 1".format(obj.ID))
        if key in down_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == down_key.index(key)):
                    self.add_recording_event(
                        "setattr {} down_pressed 1".format(obj.ID))
        if key in jump_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == jump_key.index(key)):
                    self.add_recording_event("call {} jump".format(obj.ID))
                    self.add_recording_event(
                        "setattr {} jump_pressed 1".format(obj.ID))
        if key in action_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == action_key.index(key)):
                    self.add_recording_event("call {} action".format(obj.ID))
                    self.add_recording_event(
                        "setattr {} action_pressed 1".format(obj.ID))
        if key in sneak_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == sneak_key.index(key)):
                    self.add_recording_event(
                        "setattr {} sneak_pressed 1".format(obj.ID))

    def event_key_release(self, key):
        if key in left_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == left_key.index(key)):
                    self.add_recording_event(
                        "setattr {} left_pressed 0".format(obj.ID))
        if key in right_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == right_key.index(key)):
                    self.add_recording_event(
                        "setattr {} right_pressed 0".format(obj.ID))
        if key in up_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == up_key.index(key)):
                    self.add_recording_event(
                        "setattr {} up_pressed 0".format(obj.ID))
        if key in down_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == down_key.index(key)):
                    self.add_recording_event(
                        "setattr {} down_pressed 0".format(obj.ID))
        if key in jump_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == jump_key.index(key)):
                    self.add_recording_event(
                        "call {} jump_release".format(obj.ID))
                    self.add_recording_event(
                        "setattr {} jump_pressed 0".format(obj.ID))
        if key in action_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == action_key.index(key)):
                    self.add_recording_event(
                        "setattr {} action_pressed 0".format(obj.ID))
        if key in sneak_key:
            for i in self.timeline_objects:
                obj = self.timeline_objects[i]()
                if (isinstance(obj, Player) and obj.human and
                        obj.player == sneak_key.index(key)):
                    self.add_recording_event(
                        "setattr {} sneak_pressed 0".format(obj.ID))


class TitleScreen(Level):

    def show_hud(self):
        pass

    def event_room_resume(self):
        super(TitleScreen, self).event_room_resume()
        MainMenu.create()

    def event_key_press(self, key, char):
        if self.death_time is not None or "death" in self.alarms:
            sge.Music.stop()
            self.alarms["death"] = 0
        else:
            if key == "f11":
                sge.game.fullscreen = not sge.game.fullscreen


class Worldmap(sge.Room):

    """Handles worldmaps."""

    def __init__(self, objects=(), width=None, height=None, views=None,
                 background=None, background_x=0, background_y=0, music=None):
        self.music = music
        super(Worldmap, self).__init__(objects, width, height, views,
                                       background, background_x, background_y)

    def event_room_start(self):
        self.level_text = None
        self.level_tuxdoll_available = False
        self.level_tuxdoll_found = False
        self.event_room_resume()

    def event_room_resume(self):
        global level_names
        global level_cleared

        for obj in self.objects:
            if isinstance(obj, MapSpace):
                if obj.level and obj.level not in level_names:
                    name = Level.load(obj.level).name
                    if name:
                        level_names[obj.level] = name
                    elif obj.level in levels:
                        level_names[obj.level] = "Level {}".format(
                            levels.index(level) + 1)
                    else:
                        level_names[obj.level] = "???"

                obj.update_sprite()

        play_music(self.music)
        level_cleared = False

    def event_step(self, time_passed, delta_mult):
        text = " {}/{}".format(len(tuxdolls_found), len(tuxdolls_available))
        w = tuxdoll_sprite.width + font.get_width(text)

        x = sge.game.width / 2 + tuxdoll_sprite.origin_x - w / 2
        y = tuxdoll_sprite.origin_y + 16
        sge.game.project_sprite(tuxdoll_shadow_sprite, 0, x + 2, y + 2)
        sge.game.project_sprite(tuxdoll_sprite, 0, x, y)

        x += tuxdoll_sprite.width - tuxdoll_sprite.origin_x
        sge.game.project_text(font, text, x + 2, y + 2,
                              color=sge.Color("black"), halign="left",
                              valign="middle")
        sge.game.project_text(font, text, x, y, color=sge.Color("white"),
                              halign="left", valign="middle")

        if self.level_text:
            x = sge.game.width / 2
            y = sge.game.height - font.size
            sge.game.project_text(font, self.level_text, x + 2, y + 2,
                                  color=sge.Color("black"), halign="center",
                                  valign="bottom")
            sge.game.project_text(font, self.level_text, x, y,
                                  color=sge.Color("white"), halign="center",
                                  valign="bottom")

        if self.level_tuxdoll_available:
            x = sge.game.width / 2
            y = sge.game.height - font.size * 4
            if self.level_tuxdoll_found:
                sge.game.project_sprite(tuxdoll_shadow_sprite, 0, x + 2, y + 2)
                sge.game.project_sprite(tuxdoll_sprite, 0, x, y)
            else:
                sge.game.project_sprite(tuxdoll_transparent_sprite, 0, x, y)

    def event_key_press(self, key, char):
        if key == "escape":
            sge.game.mouse.visible = True
            m = "Are you sure you want to quit?"
            if xsge_gui.show_message(message=m, buttons=["No", "Yes"],
                                     default=0):
                save_game()
                sge.game.start_room.start()
            sge.game.mouse.visible = False

    @classmethod
    def load(cls, fname):
        r = xsge_tmx.load(os.path.join(DATA, "worldmaps", fname), cls=cls,
                          types=TYPES)
        return r


class Tile(sge.Object):

    out_frames = 0

    def event_step(self, time_passed, delta_mult):
        for view in sge.game.current_room.views:
            if (self.bbox_left <= view.x + view.width + TILE_ACTIVE_RANGE and
                    self.bbox_right >= view.x - TILE_ACTIVE_RANGE and
                    self.bbox_top <= (view.y + view.height +
                                      TILE_ACTIVE_RANGE) and
                    self.bbox_bottom >= view.y - TILE_ACTIVE_RANGE):
                self.out_frames = 0
                self.tangible = True
                break
        else:
            if self.tangible:
                self.out_frames += 1
                if self.out_frames >= 3:
                    self.tangible = False


class SolidLeft(xsge_physics.SolidLeft, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidLeft, self).__init__(*args, **kwargs)


class SolidRight(xsge_physics.SolidRight, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidRight, self).__init__(*args, **kwargs)


class SolidTop(xsge_physics.SolidTop, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidTop, self).__init__(*args, **kwargs)


class SolidBottom(xsge_physics.SolidBottom, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidBottom, self).__init__(*args, **kwargs)


class Solid(xsge_physics.Solid, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(Solid, self).__init__(*args, **kwargs)


class SlopeTopLeft(xsge_physics.SlopeTopLeft, Tile):

    xsticky_top = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeTopLeft, self).__init__(*args, **kwargs)


class SlopeTopRight(xsge_physics.SlopeTopRight, Tile):

    xsticky_top = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeTopRight, self).__init__(*args, **kwargs)


class SlopeBottomLeft(xsge_physics.SlopeBottomLeft, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeBottomLeft, self).__init__(*args, **kwargs)


class SlopeBottomRight(xsge_physics.SlopeBottomRight, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeBottomRight, self).__init__(*args, **kwargs)


class MovingPlatform(xsge_physics.SolidTop, xsge_physics.MobileWall, Tile):

    sticky_top = True

    def event_create(self):
        self.sprite = platform_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None


class HurtLeft(SolidLeft):

    pass


class HurtRight(SolidRight):

    pass


class HurtTop(SolidTop):

    pass


class HurtBottom(SolidBottom):

    pass


class SpikeLeft(HurtLeft, xsge_physics.Solid):

    pass


class SpikeRight(HurtRight, xsge_physics.Solid):

    pass


class SpikeTop(HurtTop, xsge_physics.Solid):

    pass


class SpikeBottom(HurtBottom, xsge_physics.Solid):

    pass


class Death(Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(Death, self).__init__(*args, **kwargs)


class LevelEnd(Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(LevelEnd, self).__init__(*args, **kwargs)


class Player(xsge_physics.Collider):

    @property
    def warping(self):
        return self.__warping

    @warping.setter
    def warping(self, value):
        self.__warping = value
        if self.held_object is not None:
            if value:
                self.held_object.x = -666
                self.held_object.y = -666 * (self.player + 1)
            else:
                self.held_object.x = self.x + self.held_object.image_origin_x
                self.held_object.y = self.y

    def __init__(self, x, y, z=0, sprite=None, visible=True, active=True,
                 checks_collisions=True, tangible=True, bbox_x=-13, bbox_y=2,
                 bbox_width=26, bbox_height=30, regulate_origin=True,
                 collision_ellipse=False, collision_precise=False, xvelocity=0,
                 yvelocity=0, xacceleration=0, yacceleration=0,
                 xdeceleration=0, ydeceleration=0, image_index=0,
                 image_origin_x=None, image_origin_y=None, image_fps=None,
                 image_xscale=1, image_yscale=1, image_rotation=0,
                 image_alpha=255, image_blend=None, ID="player", player=0,
                 human=True, lose_on_death=True):
        self.ID = ID
        self.player = player
        self.human = human
        self.lose_on_death = lose_on_death

        self.held_object = None
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_pressed = False
        self.action_pressed = False
        self.sneak_pressed = False
        self.hp = MAX_HP
        self.coins = 0
        self.hitstun = False
        self.warping = False
        self.facing = 1
        self.view = None

        super(Player, self).__init__(
            x, y, z=z, sprite=sprite, visible=visible, active=active,
            checks_collisions=checks_collisions, tangible=tangible,
            bbox_x=bbox_x, bbox_y=bbox_y, bbox_width=bbox_width,
            bbox_height=bbox_height, regulate_origin=regulate_origin,
            collision_ellipse=collision_ellipse,
            collision_precise=collision_precise, xvelocity=xvelocity,
            yvelocity=yvelocity, xacceleration=xacceleration,
            yacceleration=yacceleration, xdeceleration=xdeceleration,
            ydeceleration=ydeceleration, image_index=image_index,
            image_origin_x=image_origin_x, image_origin_y=image_origin_y,
            image_fps=image_fps, image_xscale=image_xscale,
            image_yscale=image_yscale, image_rotation=image_rotation,
            image_alpha=image_alpha, image_blend=image_blend)

    def refresh_input(self):
        if self.human:
            self.left_pressed = sge.keyboard.get_pressed(left_key[self.player])
            self.right_pressed = sge.keyboard.get_pressed(
                right_key[self.player])
            self.up_pressed = sge.keyboard.get_pressed(up_key[self.player])
            self.down_pressed = sge.keyboard.get_pressed(down_key[self.player])
            self.jump_pressed = sge.keyboard.get_pressed(jump_key[self.player])
            self.action_pressed = sge.keyboard.get_pressed(
                action_key[self.player])
            self.sneak_pressed = sge.keyboard.get_pressed(
                sneak_key[self.player])

            # Add current joystick state
            js_controls = [left_js, right_js, up_js, down_js, jump_js,
                           action_js, sneak_js]
            js_states = [False for i in js_controls]
            for i in six.moves.range(len(js_controls)):
                if js_controls[i][self.player] is not None:
                    j, t, c = js_controls[i][self.player]
                    if t == "axis+":
                        js_states[i] = (sge.joystick.get_axis(j, c) >
                                        JOYSTICK_THRESHOLD)
                    elif t == "axis-":
                        js_states[i] = (sge.joystick.get_axis(j, c) <
                                        -JOYSTICK_THRESHOLD)
                    elif t == "axis0":
                        js_states[i] = (abs(sge.joystick.get_axis(j, c)) <=
                                        JOYSTICK_THRESHOLD)
                    elif t == "hat":
                        js_states[i] = (sge.joystick.get_hat_x(j, c[0]) == c[1] and
                                        sge.joystick.get_hat_y(j, c[0]) == c[2])
                    elif t == "button":
                        js_states[i] = sge.joystick.get_pressed(j, c)

            self.left_pressed = self.left_pressed or js_states[0]
            self.right_pressed = self.right_pressed or js_states[1]
            self.up_pressed = self.up_pressed or js_states[2]
            self.down_pressed = self.down_pressed or js_states[3]
            self.jump_pressed = self.jump_pressed or js_states[4]
            self.action_pressed = self.action_pressed or js_states[5]
            self.sneak_pressed = self.sneak_pressed or js_states[6]

    def jump(self):
        if not self.warping and (self.on_floor or self.was_on_floor):
            for thin_ice in self.collision(ThinIce, y=(self.y + 1)):
                thin_ice.crack()

            if abs(self.xvelocity) >= PLAYER_RUN_SPEED:
                self.yvelocity = get_jump_speed(PLAYER_RUN_JUMP_HEIGHT)
            else:
                self.yvelocity = get_jump_speed(PLAYER_JUMP_HEIGHT)
            self.on_floor = []
            self.was_on_floor = []
            play_sound(jump_sound)

    def jump_release(self):
        if self.yvelocity < 0:
            self.yvelocity /= 2

    def action(self):
        if not self.warping and self.held_object is not None:
            if self.up_pressed:
                self.held_object.kick_up()
            elif self.down_pressed:
                self.held_object.drop()
            else:
                self.held_object.kick()

    def stomp_jump(self, other, jump_height=PLAYER_JUMP_HEIGHT):
        if self.jump_pressed:
            self.yvelocity = get_jump_speed(jump_height)
        else:
            self.yvelocity = get_jump_speed(PLAYER_STOMP_HEIGHT)
        T = math.floor(other.bbox_top / TILE_SIZE) * TILE_SIZE
        self.move_y(T - self.bbox_bottom)

    def hurt(self):
        if not self.hitstun:
            self.hp -= 1
            if self.hp <= 0:
                self.kill()
            else:
                play_sound(hurt_sound)
                self.hitstun = True
                self.image_alpha = 128
                self.alarms["hitstun"] = PLAYER_HITSTUN

    def kill(self, show_fall=True):
        if self.held_object is not None:
            self.held_object.drop()
        play_sound(kill_sound)
        if show_fall:
            DeadMan.create(self.x, self.y, 100000, sprite=tux_die_sprite,
                           yvelocity=get_jump_speed(PLAYER_DIE_HEIGHT))

        if self.lose_on_death and not sge.game.current_room.won:
            sge.game.current_room.die()

        self.destroy()

    def win_level(self, victory_walk=True):
        for obj in sge.game.current_room.objects:
            if isinstance(obj, WinPuffObject) and obj.active:
                obj.win_puff()

        self.human = False
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_pressed = False
        self.action_pressed = False
        self.sneak_pressed = True
        self.jump_release()

        if victory_walk:
            if self.xvelocity >= 0:
                self.right_pressed = True
            else:
                self.left_pressed = True

        if "timer" in sge.game.current_room.alarms:
            del sge.game.current_room.alarms["timer"]

        sge.game.current_room.won = True
        sge.game.current_room.alarms["win_count_points"] = WIN_COUNT_START_TIME
        sge.Music.clear_queue()
        sge.Music.stop()
        if music_enabled:
            level_win_music.play()

    def pickup(self, other):
        if self.held_object is None and other.parent is None:
            other.visible = False
            self.held_object = other
            other.parent = self
            return True
        else:
            return False

    def drop_object(self):
        if self.held_object is not None:
            self.held_object.visible = True
            self.held_object = None

    def do_kick(self):
        play_sound(kick_sound)
        self.alarms["fixed_sprite"] = TUX_KICK_TIME
        if self.held_object is not None:
            self.sprite = self.get_grab_sprite(tux_body_kick_sprite)
        else:
            self.sprite = tux_kick_sprite

    def kick_object(self):
        self.drop_object()
        self.do_kick()

    def show_hud(self):
        y = 0
        sge.game.project_text(font, "Tux", 0, y, color=sge.Color("white"))

        x = 0
        y += 36
        for i in six.moves.range(MAX_HP):
            if self.hp >= i + 1:
                sge.game.project_sprite(heart_full_sprite, 0, x, y)
            else:
                sge.game.project_sprite(heart_empty_sprite, 0, x, y)
            x += heart_empty_sprite.width

        y += 18
        sge.game.project_sprite(coin_icon_sprite, coin_animation.image_index,
                                0, y)
        sge.game.project_text(font, "x{}".format(self.coins), 16, y,
                              color=sge.Color("white"))

    def get_grab_sprite(self, body_sprite, arms_sprite=None):
        if arms_sprite is None: arms_sprite = tux_arms_grab_sprite

        if self.held_object is not None:
            obj_sprite = self.held_object.sprite
            obj_image_index = self.held_object.image_index

            i = (id(body_sprite), id(obj_sprite), obj_image_index)
            if i in tux_grab_sprites:
                return tux_grab_sprites[i]
            else:
                origin_x = body_sprite.origin_x
                origin_y = body_sprite.origin_y
                width = body_sprite.width
                height = body_sprite.height

                if obj_sprite.origin_x < 0:
                    origin_x -= obj_sprite.origin_x
                    width -= obj_sprite.origin_x
                width = max(width, origin_x + obj_sprite.width)

                top = body_sprite.origin_y - obj_sprite.origin_y
                if top < 0:
                    origin_y -= top
                    height -= top
                height = max(height, top + obj_sprite.height)

                grab_sprite = sge.Sprite(width=width, height=height,
                                         origin_x=origin_x, origin_y=origin_y)
                for j in six.moves.range(1, body_sprite.frames):
                    grab_sprite.append_frame()
                grab_sprite.draw_lock()
                for j in six.moves.range(grab_sprite.frames):
                    grab_sprite.draw_sprite(obj_sprite, obj_image_index,
                                            origin_x + obj_sprite.origin_x,
                                            origin_y, j)
                    grab_sprite.draw_sprite(body_sprite, j, origin_x, origin_y,
                                            j)
                    grab_sprite.draw_sprite(arms_sprite, j, origin_x, origin_y,
                                            j)
                grab_sprite.draw_unlock()
                tux_grab_sprites[i] = grab_sprite
                return grab_sprite
        else:
            i = id(body_sprite)
            if i in tux_grab_sprites:
                return tux_grab_sprites[i]
            else:
                grab_sprite = body_sprite.copy()
                grab_sprite.draw_lock()
                for j in six.moves.range(grab_sprite.frames):
                    grab_sprite.draw_sprite(arms_sprite, j,
                                            grab_sprite.origin_x,
                                            grab_sprite.origin_y, j)
                grab_sprite.draw_unlock()
                tux_grab_sprites[i] = grab_sprite
                return grab_sprite

    def event_create(self):
        sge.game.current_room.add_timeline_object(self)

        self.last_x = self.x
        self.last_y = self.y
        self.on_slope = self.get_bottom_touching_slope()
        self.on_floor = self.get_bottom_touching_wall() + self.on_slope
        self.was_on_floor = self.on_floor

        self.view = sge.game.current_room.views[self.player]
        self.view.x = self.x - self.view.width / 2
        self.view.y = self.y - self.view.height / 2

    def event_update_position(self, delta_mult):
        super(Player, self).event_update_position(delta_mult)

        held_object = self.held_object
        if not self.warping and held_object is not None:
            target_x = self.x + held_object.image_origin_x
            target_y = self.y
            if self.image_xscale < 0:
                target_x -= held_object.sprite.width
            if isinstance(held_object, xsge_physics.Collider):
                held_object.move_x(target_x - held_object.x)
                held_object.move_y(target_y - held_object.y)
            else:
                held_object.x = target_x
                held_object.y = target_y

    def event_begin_step(self, time_passed, delta_mult):
        if not self.warping:
            self.refresh_input()

            h_control = self.right_pressed - self.left_pressed
            current_h_movement = (self.xvelocity > 0) - (self.xvelocity < 0)

            self.xacceleration = 0
            self.yacceleration = 0
            self.xdeceleration = 0

            if h_control:
                self.facing = h_control
                self.image_xscale = h_control * abs(self.image_xscale)
                if (abs(self.xvelocity) < PLAYER_MAX_SPEED and
                        (not self.sneak_pressed or
                         abs(self.xvelocity) < PLAYER_WALK_SPEED)):
                    if self.on_floor or self.was_on_floor:
                        self.xacceleration = PLAYER_ACCELERATION * h_control
                    else:
                        self.xacceleration = PLAYER_AIR_ACCELERATION * h_control
                else:
                    if self.sneak_pressed:
                        if self.on_floor or self.was_on_floor:
                            dc = PLAYER_FRICTION
                        else:
                            dc = PLAYER_AIR_FRICTION

                        if self.xvelocity - dc * delta_mult > PLAYER_WALK_SPEED:
                            self.xdeceleration = dc
                        else:
                            self.xvelocity = (PLAYER_WALK_SPEED *
                                              current_h_movement)
                    else:
                        self.xvelocity = PLAYER_MAX_SPEED * current_h_movement

            if current_h_movement and h_control != current_h_movement:
                if self.on_floor or self.was_on_floor:
                    self.xdeceleration = PLAYER_FRICTION
                else:
                    self.xdeceleration = PLAYER_AIR_FRICTION

            if not self.on_floor and not self.was_on_floor:
                if self.yvelocity < PLAYER_FALL_SPEED:
                    self.yacceleration = GRAVITY
                else:
                    self.yvelocity = PLAYER_FALL_SPEED
            elif self.on_slope:
                self.yvelocity = (PLAYER_SLIDE_SPEED *
                                  (self.on_slope[0].bbox_height /
                                   self.on_slope[0].bbox_width))

    def event_step(self, time_passed, delta_mult):
        if self.warping:
            self.event_step_warp(time_passed, delta_mult)
        else:
            self.event_step_normal(time_passed, delta_mult)

        # Move view
        if not sge.game.current_room.view_frozen:
            view_target_x = (self.x - self.view.width / 2 +
                             self.xvelocity * CAMERA_OFFSET_FACTOR)
            if abs(view_target_x - self.view.x) > 0.5:
                self.view.x += ((view_target_x - self.view.x) *
                                CAMERA_SPEED_FACTOR)
            else:
                self.view.x = view_target_x

            view_min_y = self.y - self.view.height + CAMERA_MARGIN_BOTTOM
            view_max_y = self.y - CAMERA_MARGIN_TOP
            if self.view.y < view_min_y:
                self.view.y = view_min_y
            elif self.view.y > view_max_y:
                self.view.y = view_max_y

        self.last_x = self.x
        self.last_y = self.y

        while self.coins >= HEAL_COINS:
            self.coins -= HEAL_COINS
            play_sound(heal_sound)
            if self.hp < MAX_HP:
                self.hp += 1
            else:
                sge.game.current_room.add_points(HP_POINTS)

        self.show_hud()

    def event_step_normal(self, time_passed, delta_mult):
        on_floor = self.get_bottom_touching_wall()
        self.on_slope = self.get_bottom_touching_slope() if not on_floor else []
        self.was_on_floor = self.on_floor
        self.on_floor = on_floor + self.on_slope
        h_control = self.right_pressed - self.left_pressed
        v_control = self.down_pressed - self.up_pressed

        for block in self.on_floor:
            if block in self.was_on_floor and isinstance(block, HurtTop):
                self.hurt()

        # Set image
        if "fixed_sprite" not in self.alarms:
            hands_free = (self.held_object is None)

            if self.on_floor and self.was_on_floor:
                # This method was designed to adjust the walk animation
                # to account for slopes (so that the animation cycle is
                # slower when walking up and faster when walking down),
                # but it's so generic that it also causes nonsensical
                # animation when the player is on a moving platform.
                # TODO: Think of a way to achieve this effect without the
                # silly-looking side-effect on moving platforms.
                #xdiff = self.x - self.last_x
                #speed = (math.hypot(abs(xdiff), abs(self.y - self.last_y)) /
                #         delta_mult)
                #xm = (xdiff > 0) - (xdiff < 0)
                xm = (self.xvelocity > 0) - (self.xvelocity < 0)
                speed = abs(self.xvelocity)
                if speed > 0:
                    if xm != self.facing:
                        skidding = skid_sound.playing
                        s = speed + self.xdeceleration * delta_mult
                        if (not skidding and h_control and
                                s >= PLAYER_RUN_SPEED):
                            skidding = True
                            play_sound(skid_sound)
                    else:
                        skidding = False

                    if skidding:
                        if hands_free:
                            self.sprite = tux_skid_sprite
                        else:
                            self.sprite = self.get_grab_sprite(
                                tux_body_skid_sprite, tux_arms_skid_grab_sprite)
                    else:
                        if (xm != self.facing or
                                abs(self.xvelocity) < PLAYER_RUN_SPEED):
                            if hands_free:
                                self.sprite = tux_walk_sprite
                            else:
                                self.sprite = self.get_grab_sprite(
                                    tux_body_walk_sprite)

                            self.image_speed = (speed *
                                                PLAYER_WALK_FRAMES_PER_PIXEL)
                            if xm != self.facing:
                                self.image_speed *= -1
                        else:
                            if hands_free:
                                self.sprite = tux_run_sprite
                            else:
                                self.sprite = self.get_grab_sprite(
                                    tux_body_run_sprite)

                            self.image_speed = PLAYER_RUN_IMAGE_SPEED
                else:
                    if hands_free:
                        self.sprite = tux_stand_sprite
                    else:
                        self.sprite = self.get_grab_sprite(
                            tux_body_stand_sprite)
            else:
                if self.yvelocity < 0:
                    if hands_free:
                        self.sprite = tux_jump_sprite
                    else:
                        self.sprite = self.get_grab_sprite(tux_body_jump_sprite)
                else:
                    if hands_free:
                        self.sprite = tux_fall_sprite
                    else:
                        self.sprite = self.get_grab_sprite(tux_body_fall_sprite)

        # Enter warp pipes
        if h_control > 0 and self.xvelocity >= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "right" and self.bbox_right == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    warp.warp(self)
        elif h_control < 0 and self.xvelocity <= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "left" and self.bbox_left == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    warp.warp(self)

        if v_control > 0 and self.yvelocity >= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "down" and self.bbox_bottom == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    warp.warp(self)
        elif v_control < 0 and self.yvelocity <= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "up" and self.bbox_top == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    warp.warp(self)

        # Prevent moving off-screen to the right or left
        if self.bbox_left < self.view.x:
            self.bbox_left = self.view.x
        elif self.bbox_right > self.view.x + self.view.width:
            self.bbox_right = self.view.x + self.view.width

        # Off-screen death
        if self.bbox_top > self.view.y + self.view.height + DEATHZONE:
            self.kill(False)

    def event_step_warp(self, time_passed, delta_mult):
        hands_free = (self.held_object is None)

        if abs(self.xvelocity) >= WARP_SPEED / 2:
            if hands_free:
                self.sprite = tux_walk_sprite
            else:
                self.sprite = self.get_grab_sprite(tux_body_walk_sprite)

            self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
            if self.xvelocity > 0:
                self.image_xscale = abs(self.image_xscale)
            else:
                self.image_xscale = -abs(self.image_xscale)
        else:
            if hands_free:
                self.sprite = tux_jump_sprite
            else:
                self.sprite = self.get_grab_sprite(tux_body_jump_sprite)

    def event_paused_step(self, time_passed, delta_mult):
        self.show_hud()

    def event_alarm(self, alarm_id):
        if alarm_id == "hitstun":
            self.hitstun = False
            self.image_alpha = 255

    def event_key_press(self, key, char):
        if self.human:
            if key == jump_key[self.player]:
                self.jump()
            if key == action_key[self.player]:
                self.action()

    def event_key_release(self, key):
        if self.human:
            if key == jump_key[self.player]:
                self.jump_release()

    def event_joystick_axis_move(self, js_name, js_id, axis, value):
        if self.human:
            js_versions = [(js_id, "axis+", axis), (js_id, "axis-", axis)]
            if value > JOYSTICK_THRESHOLD:
                js = (js_id, "axis+", axis)
            elif value < -JOYSTICK_THRESHOLD:
                js = (js_id, "axis-", axis)
            else:
                js = (js_id, "axis0", axis)

            if js == jump_js[self.player]:
                self.jump()
            elif jump_js[self.player] in js_versions:
                self.jump_release()
            if js == action_js[self.player]:
                self.action()

    def event_joystick_hat_move(self, js_name, js_id, hat, x, y):
        if self.human:
            js_versions = [(js_id, "hatx+", hat), (js_id, "hatx-", hat)]
            if x > 0:
                js = (js_id, "hatx+", hat)
            elif x < 0:
                js = (js_id, "hatx-", hat)
            else:
                js = (js_id, "hatx0", hat)

            if js == jump_js[self.player]:
                self.jump()
            elif jump_js[self.player] in js_versions:
                self.jump_release()
            if js == action_js[self.player]:
                self.action()

            js_versions = [(js_id, "haty+", hat), (js_id, "haty-", hat)]
            if y > 0:
                js = (js_id, "haty+", hat)
            elif y < 0:
                js = (js_id, "haty-", hat)
            else:
                js = (js_id, "haty0", hat)

            if js == jump_js[self.player]:
                self.jump()
            elif jump_js[self.player] in js_versions:
                self.jump_release()
            if js == action_js[self.player]:
                self.action()

    def event_joystick_button_press(self, js_name, js_id, button):
        if self.human:
            js = (js_id, "button", button)

            if js == jump_js[self.player]:
                self.jump()
            if js == action_js[self.player]:
                self.action()

    def event_joystick_button_release(self, js_name, js_id, button):
        if self.human:
            js = (js_id, "button", button)

            if js == jump_js[self.player]:
                self.jump_release()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Death):
            self.kill()
        elif isinstance(other, LevelEnd):
            self.win_level()
            other.destroy()
        elif isinstance(other, Explosion):
            other.touch(self)
        elif isinstance(other, InteractiveObject):
            if (ydirection == 1 or
                    (xdirection and not ydirection and
                     self.bbox_bottom - other.bbox_top <= STOMP_LAX)):
                other.stomp(self)
            # This check is necessary to allow the player to drop held
            # objects. It also has a nice side-effect of preventing the
            # player from being hurt by the same object more than once
            # until the collision stops.
            elif xdirection or ydirection:
                other.touch(self)

    def event_physics_collision_left(self, other, move_loss):
        for block in self.get_left_touching_wall():
            if isinstance(block, HurtRight):
                self.hurt()

        if isinstance(other, xsge_physics.SolidRight):
            self.xvelocity = 0

        if self.left_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "left" and self.bbox_left == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
                    warp.warp(self)

    def event_physics_collision_right(self, other, move_loss):
        for block in self.get_right_touching_wall():
            if isinstance(block, HurtLeft):
                self.hurt()

        if isinstance(other, xsge_physics.SolidLeft):
            self.xvelocity = 0

        if self.right_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "right" and self.bbox_right == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
                    warp.warp(self)

    def event_physics_collision_top(self, other, move_loss):
        top_touching = self.get_top_touching_wall()

        xv = self.xvelocity
        for i in six.moves.range(CEILING_LAX):
            self.x -= 1
            if not self.get_top_touching_wall():
                self.move_y(-move_loss)
                break
        else:
            self.x += CEILING_LAX
            for i in six.moves.range(CEILING_LAX):
                self.x += 1
                if not self.get_top_touching_wall():
                    self.move_y(-move_loss)
                    break
            else:
                self.x -= CEILING_LAX
                self.yvelocity = 0

        for block in top_touching:
            if isinstance(block, HittableBlock):
                block.hit(self)
            elif isinstance(block, HurtBottom):
                self.hurt()

        if self.up_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "up" and self.bbox_top == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
                    warp.warp(self)
                    break

    def event_physics_collision_bottom(self, other, move_loss):
        for block in self.get_bottom_touching_wall():
            if isinstance(block, HurtTop):
                self.hurt()

        if isinstance(other, xsge_physics.SolidTop):
            self.yvelocity = 0
        elif isinstance(other, (xsge_physics.SlopeTopLeft,
                                xsge_physics.SlopeTopRight)):
            self.yvelocity = PLAYER_SLIDE_SPEED * (other.bbox_height /
                                                   other.bbox_width)

        if self.down_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "down" and self.bbox_bottom == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
                    warp.warp(self)


class DeadMan(sge.Object):

    """Object which falls off the screen, then gets destroyed."""

    gravity = GRAVITY
    fall_speed = PLAYER_DIE_FALL_SPEED

    def event_begin_step(self, time_passed, delta_mult):
        if self.yvelocity < self.fall_speed:
            self.yacceleration = self.gravity
        else:
            self.yvelocity = self.fall_speed
            self.yacceleration = 0

    def event_step(self, time_passed, delta_mult):
        if self.y - self.image_origin_y > sge.game.current_room.height:
            self.destroy()


class Corpse(xsge_physics.Collider):

    """Like DeadMan, but just falls to the floor, not off-screen."""

    gravity = GRAVITY
    fall_speed = ENEMY_FALL_SPEED

    def event_create(self):
        self.alarms["die"] = 90

    def event_begin_step(self, time_passed, delta_mult):
        if self.get_bottom_touching_wall() or self.get_bottom_touching_slope():
            self.yvelocity = 0
        else:
            if self.yvelocity < self.fall_speed:
                self.yacceleration = self.gravity
            else:
                self.yvelocity = min(self.yvelocity, self.fall_speed)
                self.yacceleration = 0

    def event_alarm(self, alarm_id):
        if alarm_id == "die":
            self.destroy()


class Smoke(sge.Object):

    def event_animation_end(self):
        self.destroy()


class InteractiveObject(sge.Object):

    active_range = ENEMY_ACTIVE_RANGE
    knockable = False
    burnable = False
    freezable = False
    parent = None
    warping = False

    def update_active(self):
        if not self.warping:
            for view in sge.game.current_room.views:
                if (self.bbox_left <= (view.x + view.width +
                                       self.active_range) and
                        self.bbox_right >= view.x - self.active_range and
                        self.bbox_top <= (view.y + view.height +
                                          self.active_range) and
                        self.bbox_bottom >= view.y - self.active_range):
                    self.tangible = True
                    self.active = True
                    break
            else:
                self.tangible = False
                self.active = False

            if self.bbox_top > sge.game.current_room.height + self.active_range:
                self.destroy()

    def get_nearest_player(self):
        player = None
        dist = 0
        for obj in sge.game.current_room.objects:
            if isinstance(obj, Player):
                ndist = math.hypot(self.x - obj.x, self.y - obj.y)
                if player is None or ndist < dist:
                    player = obj
                    dist = ndist
        return player

    def set_direction(self, direction):
        self.image_xscale = abs(self.image_xscale) * direction

    def move(self):
        pass

    def touch(self, other):
        pass

    def stomp(self, other):
        self.touch(other)

    def knock(self, other=None):
        pass

    def burn(self):
        pass

    def freeze(self):
        pass

    def kick(self):
        self.drop()

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None

    def kick_up(self):
        self.kick()

    def touch_death(self):
        play_sound(fall_sound)
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity, yvelocity=0,
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()

    def event_create(self):
        self.update_active()

    def event_begin_step(self, time_passed, delta_mult):
        if not self.warping:
            self.move()
        elif self.xvelocity:
            self.image_xscale = math.copysign(self.image_xscale, self.xvelocity)

    def event_step(self, time_passed, delta_mult):
        self.update_active()

    def event_inactive_step(self, time_passed, delta_mult):
        self.update_active()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Death):
            self.touch_death()

    def event_destroy(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None


class InteractiveCollider(InteractiveObject, xsge_physics.Collider):

    def stop_left(self):
        self.xvelocity = 0

    def stop_right(self):
        self.xvelocity = 0

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        self.yvelocity = 0

    def touch_hurt(self):
        play_sound(fall_sound)
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity, yvelocity=0,
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()

    def event_physics_collision_left(self, other, move_loss):
        if isinstance(other, HurtRight):
            self.touch_hurt()

        if isinstance(other, xsge_physics.SolidRight):
            self.stop_left()
        elif isinstance(other, xsge_physics.SlopeTopRight):
            self.stop_down()
        elif isinstance(other, xsge_physics.SlopeBottomRight):
            self.stop_up()

    def event_physics_collision_right(self, other, move_loss):
        if isinstance(other, HurtLeft):
            self.touch_hurt()

        if isinstance(other, xsge_physics.SolidLeft):
            self.stop_right()
        elif isinstance(other, xsge_physics.SlopeTopLeft):
            self.stop_down()
        elif isinstance(other, xsge_physics.SlopeBottomLeft):
            self.stop_up()

    def event_physics_collision_top(self, other, move_loss):
        if isinstance(other, HurtBottom):
            self.touch_hurt()
        if isinstance(other, (xsge_physics.SolidBottom,
                              xsge_physics.SlopeBottomLeft,
                              xsge_physics.SlopeBottomRight)):
            self.stop_up()

    def event_physics_collision_bottom(self, other, move_loss):
        if isinstance(other, HurtTop):
            self.touch_hurt()
        if isinstance(other, (xsge_physics.SolidTop, xsge_physics.SlopeTopLeft,
                              xsge_physics.SlopeTopRight)):
            self.stop_down()


class WinPuffObject(InteractiveObject):

    win_puff_score = ENEMY_KILL_POINTS

    def win_puff(self):
        play_sound(pop_sound)
        if self.sprite is None:
            x = self.x
            y = self.y
        else:
            x = self.x - self.image_origin_x + self.sprite.width / 2
            y = self.y - self.image_origin_y + self.sprite.height / 2
        Smoke.create(x, y, self.z, sprite=smoke_plume_sprite)
        self.destroy()
        sge.game.current_room.add_points(self.win_puff_score)


class FallingObject(InteractiveCollider):

    """
    Falls based on gravity. If on a slope, falls at a constant speed
    based on the steepness of the slope.
    """

    gravity = GRAVITY
    fall_speed = ENEMY_FALL_SPEED
    slide_speed = ENEMY_SLIDE_SPEED

    was_on_floor = False

    def move(self):
        on_floor = self.get_bottom_touching_wall()
        on_slope = self.get_bottom_touching_slope()
        if self.was_on_floor and (on_floor or on_slope) and self.yvelocity >= 0:
            self.yacceleration = 0
            if on_floor:
                if self.yvelocity > 0:
                    self.yvelocity = 0
                    self.stop_down()
            elif on_slope:
                self.yvelocity = self.slide_speed * (on_slope[0].bbox_height /
                                                     on_slope[0].bbox_width)
        else:
            if self.yvelocity < self.fall_speed:
                self.yacceleration = self.gravity
            else:
                self.yvelocity = self.fall_speed
                self.yacceleration = 0

        self.was_on_floor = on_floor or on_slope


class WalkingObject(FallingObject):

    """
    Walks toward the player.  Turns around at walls, and can also be set
    to turn around at ledges with the stayonplatform attribute.
    """

    walk_speed = ENEMY_WALK_SPEED
    stayonplatform = False

    def set_direction(self, direction):
        self.xvelocity = self.walk_speed * direction
        self.image_xscale = abs(self.image_xscale) * direction

    def move(self):
        super(WalkingObject, self).move()

        if not self.xvelocity:
            player = self.get_nearest_player()
            if player is not None:
                self.set_direction(1 if self.x < player.x else -1)
            else:
                self.set_direction(-1)

        on_floor = self.get_bottom_touching_wall()
        on_slope = self.get_bottom_touching_slope()
        if (on_floor or on_slope) and self.stayonplatform:
            if self.xvelocity < 0:
                for tile in on_floor:
                    if tile.bbox_left < self.x:
                        break
                else:
                    if not on_slope:
                        self.set_direction(1)
            else:
                for tile in on_floor:
                    if tile.bbox_right > self.x:
                        break
                else:
                    if not on_slope:
                        self.set_direction(-1)

    def stop_left(self):
        self.set_direction(1)

    def stop_right(self):
        self.set_direction(-1)

    def event_inactive_step(self, time_passed, delta_mult):
        self.xvelocity = 0
        self.update_active()


class CrowdBlockingObject(InteractiveObject):

    """Blocks CrowdObject instances, causing them to turn around."""

    pass


class CrowdObject(WalkingObject, CrowdBlockingObject):

    """
    Turns around when colliding with a CrowdBlockingObject.  (Note: this
    class is itself derived from CrowdBlockingObject.)
    """

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, CrowdBlockingObject):
            if xdirection:
                self.set_direction(-xdirection)
            else:
                if self.x > other.x:
                    self.set_direction(1)
                elif self.x < other.x:
                    self.set_direction(-1)
                elif id(self) > id(other):
                    self.set_direction(1)
                else:
                    self.set_direction(-1)
        else:
            super(CrowdObject, self).event_collision(other, xdirection,
                                                     ydirection)


class KnockableObject(InteractiveObject):

    """Provides basic knocking behavior."""

    knockable = True

    def knock(self, other=None):
        play_sound(fall_sound)
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity,
                       yvelocity=get_jump_speed(ENEMY_HIT_BELOW_HEIGHT),
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()


class BurnableObject(InteractiveObject):

    """Provides basic burn behavior."""

    burnable = True

    def burn(self):
        play_sound(fall_sound)
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity, yvelocity=0,
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()


class FreezableObject(InteractiveObject):

    """Provides basic freeze behavior."""

    freezable = True
    frozen_sprite = None
    frozen_time = THAW_TIME_DEFAULT
    frozen = False

    def update_active(self):
        if self.frozen:
            self.active = False
        else:
            super(FreezableObject, self).update_active()

    def freeze(self):
        if self.frozen_sprite is None:
            self.frozen_sprite = self.sprite.copy()
            colorizer = sge.Sprite(width=self.frozen_sprite.width,
                                   height=self.frozen_sprite.height)
            colorizer.draw_rectangle(0, 0, colorizer.width, colorizer.height,
                                     fill=sge.Color((128, 128, 255)))
            self.frozen_sprite.draw_sprite(colorizer, 0, 0, 0,
                                           blend_mode=sge.BLEND_RGB_MULTIPLY)

        frozen_self = FrozenObject.create(self.x, self.y, self.z,
                                          sprite=self.frozen_sprite,
                                          image_xscale=self.image_xscale,
                                          image_yscale=self.image_yscale)
        frozen_self.unfrozen = self
        self.frozen = True
        self.tangible = False
        self.active = False
        self.visible = False
        if self.frozen_time is not None:
            frozen_self.alarms["thaw_warn"] = self.frozen_time


class FrozenObject(InteractiveObject, xsge_physics.SolidTop):

    burnable = True
    freezable = True
    unfrozen = None

    def burn(self):
        if self.unfrozen is not None:
            self.unfrozen.frozen = False
            self.unfrozen.tangible = True
            self.unfrozen.visible = True
            self.unfrozen.update_active()
        self.destroy()

    def freeze(self):
        if self.unfrozen is not None:
            self.burn()
            self.unfrozen.freeze()

    def event_inactive_step(self, time_passed, delta_mult):
        self.burn()

    def event_alarm(self, alarm_id):
        if self.unfrozen is not None:
            if alarm_id == "thaw_warn":
                self.sprite = self.sprite.copy()
                self.sprite.append_frame()
                self.sprite.draw_sprite(self.unfrozen.sprite,
                                        self.unfrozen.image_index,
                                        self.unfrozen.image_origin_x,
                                        self.unfrozen.image_origin_y,
                                        frame=(self.sprite.frames - 1))
                self.image_fps = THAW_FPS
                self.alarms["thaw"] = THAW_WARN_TIME
            elif alarm_id == "thaw":
                self.burn()


class WalkingSnowball(CrowdObject, KnockableObject, BurnableObject,
                      WinPuffObject):

    freezable = True

    def event_create(self):
        super(WalkingSnowball, self).event_create()
        self.sprite = snowball_walk_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        play_sound(squish_sound)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        Corpse.create(self.x, self.y, self.z, sprite=snowball_squished_sprite,
                      image_xscale=self.image_xscale,
                      image_yscale=self.image_yscale)
        self.destroy()

    def knock(self, other=None):
        super(WalkingSnowball, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        super(WalkingSnowball, self).burn()
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)


class BouncingSnowball(WalkingSnowball):

    def event_create(self):
        super(BouncingSnowball, self).event_create()
        self.sprite = bouncing_snowball_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        self.yvelocity = get_jump_speed(SNOWBALL_BOUNCE_HEIGHT, self.gravity)


class WalkingIceblock(CrowdObject, KnockableObject, BurnableObject,
                      WinPuffObject):

    freezable = True
    stayonplatform = True

    def event_create(self):
        super(WalkingIceblock, self).event_create()
        self.sprite = iceblock_walk_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        play_sound(stomp_sound)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        FlatIceblock.create(self.x, self.y, self.z, sprite=iceblock_flat_sprite,
                            image_xscale=self.image_xscale,
                            image_yscale=self.image_yscale)
        self.destroy()

    def knock(self, other=None):
        super(WalkingIceblock, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        super(WalkingIceblock, self).burn()
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)


class Spiky(CrowdObject, KnockableObject, FreezableObject, WinPuffObject):

    burnable = True
    stayonplatform = True

    def event_create(self):
        super(Spiky, self).event_create()
        self.sprite = spiky_walk_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

        self.frozen_sprite = spiky_iced_sprite

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.hurt()

    def knock(self, other=None):
        super(Spiky, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def touch_hurt(self):
        pass


class WalkingBomb(CrowdObject, KnockableObject, FreezableObject,
                  WinPuffObject):

    burnable = True
    stayonplatform = True

    def event_create(self):
        super(WalkingBomb, self).event_create()
        self.sprite = bomb_walk_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

        self.frozen_sprite = bomb_iced_sprite

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        play_sound(stomp_sound)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        tb = TickingBomb.create(self.x, self.y, self.z,
                                sprite=bomb_ticking_sprite,
                                image_xscale=self.image_xscale,
                                image_yscale=self.image_yscale)
        tb.thrower = other
        self.destroy()

    def knock(self, other=None):
        super(WalkingBomb, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        Explosion.create(self.x, self.y, self.z)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        self.destroy()


class Jumpy(CrowdObject, KnockableObject, FreezableObject, WinPuffObject):

    burnable = True
    walk_speed = 0

    def event_create(self):
        super(Jumpy, self).event_create()
        self.sprite = jumpy_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

        self.frozen_sprite = jumpy_iced_sprite

    def move(self):
        super(Jumpy, self).move()

        y = self.y + (jumpy_sprite.height - jumpy_bounce_sprite.height)
        for obj in self.collision(xsge_physics.SolidTop, y=y):
            if not self.collision(obj):
                self.sprite = jumpy_bounce_sprite
                break
        else:
            self.sprite = jumpy_sprite

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.hurt()

    def knock(self, other=None):
        super(Jumpy, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        pass

    def touch_hurt(self):
        pass

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        self.yvelocity = get_jump_speed(JUMPY_BOUNCE_HEIGHT, self.gravity)


class FlyingSnowball(CrowdBlockingObject, KnockableObject, BurnableObject,
                     WinPuffObject):

    freezable = True
    had_xv = 0

    def event_create(self):
        super(FlyingSnowball, self).event_create()
        self.sprite = flying_snowball_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

    def update_active(self):
        super(FlyingSnowball, self).update_active()
        self.active = True

    def move(self):
        if abs(self.xvelocity) > abs(self.yvelocity):
            self.image_xscale = math.copysign(self.image_xscale, self.xvelocity)
            self.had_xv = 5
        elif self.had_xv > 0:
            self.had_xv -= 1
        else:
            player = self.get_nearest_player()
            if player is not None:
                if self.x < player.x:
                    self.image_xscale = abs(self.image_xscale)
                else:
                    self.image_xscale = -abs(self.image_xscale)

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        play_sound(squish_sound)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        Corpse.create(self.x, self.y, self.z,
                      sprite=flying_snowball_squished_sprite,
                      image_xscale=self.image_xscale,
                      image_yscale=self.image_yscale)
        self.destroy()

    def knock(self, other=None):
        super(FlyingSnowball, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        super(FlyingSnowball, self).burn()
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def freeze(self):
        pass


class FlatIceblock(CrowdBlockingObject, FallingObject, KnockableObject,
                   BurnableObject, WinPuffObject):

    freezable = True

    def touch(self, other):
        if self.parent is None:
            if other.pickup(self):
                self.gravity = 0
                if other.action_pressed:
                    other.action()
            else:
                other.do_kick()
                dib = DashingIceblock.create(other, self.x, self.y, self.z,
                                             sprite=self.sprite,
                                             image_xscale=self.image_xscale,
                                             image_yscale=self.image_yscale)
                dib.set_direction(-1 if other.image_xscale < 0 else 1)
                self.destroy()

    def knock(self, other=None):
        if self.parent is None:
            super(FlatIceblock, self).knock(other)

    def freeze(self):
        pass

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            dib = DashingIceblock.create(self.parent, self.x, self.y, self.z,
                                         sprite=self.sprite,
                                         image_xscale=self.image_xscale,
                                         image_yscale=self.image_yscale)
            dib.set_direction(-1 if self.parent.image_xscale < 0 else 1)
            self.parent = None
            self.destroy()

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            play_sound(kick_sound)
            tib = ThrownIceblock.create(
                self.parent, self.x, self.y, self.z, sprite=self.sprite,
                image_xscale=self.image_xscale, image_yscale=self.image_yscale,
                xvelocity=self.parent.xvelocity,
                yvelocity=get_jump_speed(KICK_UP_HEIGHT,
                                         ThrownIceblock.gravity))
            self.parent = None
            self.destroy()

    def event_end_step(self, time_passed, delta_mult):
        if self.parent is not None:
            direction = -1 if self.parent.image_xscale < 0 else 1
            self.image_xscale = abs(self.image_xscale) * direction


class ThrownIceblock(FallingObject, KnockableObject, BurnableObject,
                     WinPuffObject):

    freezable = True
    active_range = ICEBLOCK_ACTIVE_RANGE
    gravity = ICEBLOCK_GRAVITY
    fall_speed = ICEBLOCK_FALL_SPEED

    def __init__(self, thrower, *args, **kwargs):
        self.thrower = thrower
        super(ThrownIceblock, self).__init__(*args, **kwargs)

    def touch(self, other):
        fib = FlatIceblock.create(self.x, self.y, self.z, sprite=self.sprite,
                                  image_xscale=self.image_xscale,
                                  image_yscale=self.image_yscale)
        self.destroy()
        fib.touch(other)

    def freeze(self):
        pass

    def stop_left(self):
        play_sound(iceblock_bump_sound)
        self.xvelocity = abs(self.xvelocity)
        self.set_direction(1)
        for block in self.get_left_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def stop_right(self):
        play_sound(iceblock_bump_sound)
        self.xvelocity = -abs(self.xvelocity)
        self.set_direction(-1)
        for block in self.get_right_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def stop_up(self):
        self.yvelocity = 0
        for block in self.get_top_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def event_end_step(self, time_passed, delta_mult):
        if (self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
            self.xdeceleration = ICEBLOCK_FRICTION
            if abs(self.xvelocity) <= 0.05:
                FlatIceblock.create(self.x, self.y, self.z, sprite=self.sprite,
                                    image_xscale=self.image_xscale,
                                    image_yscale=self.image_yscale)
                self.destroy()
        else:
            self.xdeceleration = 0

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)
        elif isinstance(other, Coin):
            other.event_collision(self.thrower, -xdirection, -ydirection)

        super(ThrownIceblock, self).event_collision(other, xdirection,
                                                    ydirection)


class DashingIceblock(WalkingObject, KnockableObject, BurnableObject,
                      WinPuffObject):

    freezable = True
    gravity = ICEBLOCK_GRAVITY
    active_range = ICEBLOCK_ACTIVE_RANGE
    walk_speed = ICEBLOCK_DASH_SPEED

    def __init__(self, thrower, *args, **kwargs):
        self.thrower = thrower
        super(DashingIceblock, self).__init__(*args, **kwargs)

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        play_sound(stomp_sound)
        FlatIceblock.create(self.x, self.y, self.z, sprite=iceblock_flat_sprite,
                            image_xscale=self.image_xscale,
                            image_yscale=self.image_yscale)
        self.destroy()

    def stop_left(self):
        play_sound(iceblock_bump_sound)
        self.set_direction(1)
        for block in self.get_left_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def stop_right(self):
        play_sound(iceblock_bump_sound)
        self.set_direction(-1)
        for block in self.get_right_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)
        elif isinstance(other, Coin):
            other.event_collision(self.thrower, -xdirection, -ydirection)

        super(DashingIceblock, self).event_collision(other, xdirection,
                                                     ydirection)

    def event_inactive_step(self, time_passed, delta_mult):
        self.destroy()


class TickingBomb(CrowdBlockingObject, FallingObject, KnockableObject):

    active_range = ICEBLOCK_ACTIVE_RANGE
    burnable = True
    freezable = True
    gravity = BOMB_GRAVITY
    thrower = None

    def touch(self, other):
        if other.pickup(self):
            self.thrower = other
            self.gravity = 0
            self.xvelocity = 0
            self.yvelocity = 0
            if other.action_pressed:
                other.action()

    def burn(self):
        e = Explosion.create(self.x, self.y, self.z)
        e.detonator = self.thrower
        self.destroy()

    def freeze(self):
        if self.image_index > 0:
            self.image_index -= 1

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = self.parent.xvelocity + math.copysign(
                KICK_FORWARD_SPEED, self.parent.image_xscale)
            self.yvelocity = get_jump_speed(KICK_FORWARD_HEIGHT,
                                            self.__class__.gravity)
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = self.parent.xvelocity
            self.yvelocity = get_jump_speed(KICK_UP_HEIGHT,
                                            self.__class__.gravity)
            self.parent = None
            self.gravity = self.__class__.gravity

    def stop_left(self):
        if self.parent is None:
            play_sound(iceblock_bump_sound)
            self.xvelocity = abs(self.xvelocity)
            self.set_direction(1)
            for block in self.get_left_touching_wall():
                if isinstance(block, HittableBlock):
                    block.hit(self.thrower)

    def stop_right(self):
        if self.parent is None:
            play_sound(iceblock_bump_sound)
            self.xvelocity = -abs(self.xvelocity)
            self.set_direction(-1)
            for block in self.get_right_touching_wall():
                if isinstance(block, HittableBlock):
                    block.hit(self.thrower)

    def stop_up(self):
        if self.parent is None:
            self.yvelocity = 0
            for block in self.get_top_touching_wall():
                if isinstance(block, HittableBlock):
                    block.hit(self.thrower)

    def event_end_step(self, time_passed, delta_mult):
        if (self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
            self.xdeceleration = ROCK_FRICTION
        else:
            self.xdeceleration = 0

    def event_inactive_step(self, time_passed, delta_mult):
        self.destroy()

    def event_animation_end(self):
        e = Explosion.create(self.x, self.y, self.z)
        e.detonator = self.thrower
        self.destroy()


class Explosion(InteractiveObject):

    detonator = None

    def event_create(self):
        super(Explosion, self).event_create()
        self.sprite = explosion_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.__life = EXPLOSION_TIME
        play_sound(explosion_sound)

    def touch(self, other):
        other.hurt()

    def event_step(self, time_passed, delta_mult):
        self.__life -= delta_mult
        if self.__life <= 0:
            self.destroy()

    def event_inactive_step(self, time_passed, delta_mult):
        self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject):
            if other.burnable:
                other.burn()
            elif other.knockable:
                other.knock(self)
        if isinstance(other, HittableBlock):
            if self.detonator is not None:
                other.hit(self.detonator)

        super(Explosion, self).event_collision(other, xdirection, ydirection)


class Icicle(InteractiveObject):

    shaking = False

    def event_create(self):
        super(Icicle, self).event_create()
        self.sprite = icicle_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

        self.shake_counter = SHAKE_FRAME_TIME

    def event_step(self, time_passed, delta_mult):
        super(Icicle, self).event_step(time_passed, delta_mult)

        if self.active:
            if self.shaking:
                self.shake_counter -= delta_mult
                while self.shake_counter <= 0:
                    self.shake_counter += SHAKE_FRAME_TIME
                    if self.image_origin_x > self.sprite.origin_x:
                        self.image_origin_x = self.sprite.origin_x - 2
                    else:
                        self.image_origin_x = self.sprite.origin_x + 2
            else:
                players = []
                crash_y = sge.game.current_room.height
                for obj in sge.game.current_room.objects:
                    if (obj.bbox_top > self.bbox_bottom and
                            self.bbox_right >= obj.bbox_left and
                            self.bbox_left <= obj.bbox_right):
                        if isinstance(obj, Player):
                            players.append(obj)
                        elif isinstance(obj, xsge_physics.SolidTop):
                            crash_y = min(crash_y, obj.bbox_top)
                        elif isinstance(obj, xsge_physics.SlopeTopLeft):
                            crash_y = min(crash_y,
                                          obj.get_slope_y(self.bbox_right))
                        elif isinstance(obj, xsge_physics.SlopeTopRight):
                            crash_y = min(crash_y,
                                          obj.get_slope_y(self.bbox_left))

                for player in players:
                    if player.bbox_top < crash_y:
                        self.shaking = True
                        play_sound(icicle_shake_sound)
                        self.alarms["fall"] = ICICLE_SHAKE_TIME
                        break

    def event_inactive_step(self, time_passed, delta_mult):
        self.shaking = False
        super(Icicle, self).event_inactive_step(time_passed, delta_mult)

    def event_alarm(self, alarm_id):
        if alarm_id == "fall":
            FallingIcicle.create(self.x, self.y, self.z, sprite=self.sprite,
                                 image_xscale=self.image_xscale,
                                 image_yscale=self.image_yscale)
            self.destroy()


class FallingIcicle(FallingObject):

    gravity = ICICLE_GRAVITY
    fall_speed = ICICLE_FALL_SPEED

    def touch(self, other):
        other.hurt()

    def stop_down(self):
        play_sound(icicle_crash_sound)
        Corpse.create(self.x, self.y, self.z,
                      sprite=icicle_broken_sprite,
                      image_xscale=self.image_xscale,
                      image_yscale=self.image_yscale)
        self.destroy()

    def event_inactive_step(self, time_passed, delta_mult):
        self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)

        super(FallingIcicle, self).event_collision(other, xdirection,
                                                   ydirection)


class Crusher(FallingObject):

    burnable = True
    freezable = True
    gravity = 0
    fall_speed = CRUSHER_FALL_SPEED
    crushing = False

    def touch(self, other):
        other.hurt()

    def stop_up(self):
        self.yvelocity = 0
        self.crushing = False

    def stop_down(self):
        play_sound(brick_sound)
        self.yvelocity = 0
        self.gravity = 0
        sge.game.current_room.shake(CRUSHER_SHAKE_NUM)
        self.alarms["crush_end"] = CRUSHER_CRUSH_TIME

    def event_step(self, time_passed, delta_mult):
        if not self.crushing:
            super(Crusher, self).event_step(time_passed, delta_mult)
            if self.active:
                players = []
                crash_y = sge.game.current_room.height
                for obj in sge.game.current_room.objects:
                    if (obj.bbox_top > self.bbox_bottom and
                            self.bbox_right >= obj.bbox_left and
                            self.bbox_left <= obj.bbox_right):
                        if isinstance(obj, Player):
                            players.append(obj)
                        elif isinstance(obj, xsge_physics.SolidTop):
                            crash_y = min(crash_y, obj.bbox_top)
                        elif isinstance(obj, xsge_physics.SlopeTopLeft):
                            crash_y = min(crash_y,
                                          obj.get_slope_y(self.bbox_right))
                        elif isinstance(obj, xsge_physics.SlopeTopRight):
                            crash_y = min(crash_y,
                                          obj.get_slope_y(self.bbox_left))

                for player in players:
                    if player.bbox_top < crash_y:
                        self.crushing = True
                        self.gravity = CRUSHER_GRAVITY
                        break

    def event_alarm(self, alarm_id):
        if alarm_id == "crush_end":
            self.yvelocity = -CRUSHER_RISE_SPEED

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)

        super(Crusher, self).event_collision(other, xdirection, ydirection)


class Krush(Crusher):

    def event_create(self):
        super(Krush, self).event_create()
        self.sprite = krush_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None


class Krosh(Crusher):

    def event_create(self):
        super(Krosh, self).event_create()
        self.sprite = krosh_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None


class Circoflame(InteractiveObject):

    burnable = True
    freezable = True

    def __init__(self, center, *args, **kwargs):
        self.center = weakref.ref(center)
        kwargs["sprite"] = circoflame_sprite
        super(Circoflame, self).__init__(*args, **kwargs)

    def touch(self, other):
        other.hurt()

    def freeze(self):
        play_sound(sizzle_sound)
        center = self.center()
        if center is not None:
            center.destroy()
        self.destroy()


class CircoflameCenter(InteractiveObject):

    def __init__(self, x, y, z=0, radius=(TILE_SIZE * 4), pos=180,
                 rvelocity=2):
        self.radius = radius
        self.pos = pos
        self.rvelocity = rvelocity
        self.flame = Circoflame(self, x, y, z)
        super(CircoflameCenter, self).__init__(x, y, tangible=False)

    def event_create(self):
        sge.game.current_room.add(self.flame)

    def update_active(self):
        self.active = True
        self.tangible = False

    def event_step(self, time_passed, delta_mult):
        self.pos += self.rvelocity * delta_mult
        self.pos %= 360
        x = math.cos(math.radians(self.pos)) * self.radius
        y = math.sin(math.radians(self.pos)) * self.radius
        self.flame.x = self.x + x
        self.flame.y = self.y + y


class Snowman(FallingObject):

    burnable = True
    freezable = True
    knockable = True

    def __init__(self, x, y, ID="boss", **kwargs):
        self.ID = ID
        self.stage = 0
        self.hp = SNOWMAN_HP
        self.stunned = False
        self.stun_end = False
        self.stun_time = 0
        self.fixed_sprite = False
        kwargs["sprite"] = snowman_stand_sprite
        super(Snowman, self).__init__(x, y, **kwargs)

    def event_create(self):
        super(Snowman, self).event_create()
        sge.game.current_room.add_timeline_object(self)

    def jump(self):
        if self.was_on_floor:
            play_sound(bigjump_sound)
            self.yvelocity = get_jump_speed(SNOWMAN_JUMP_HEIGHT, self.gravity)

    def stun(self):
        self.stunned = True
        self.fixed_sprite = True
        self.sprite = snowman_hurt_walk_sprite
        self.xvelocity = 0
        self.xacceleration = 0
        self.image_speed = 0
        if self.yvelocity < 0:
            self.yvelocity = 0
        self.alarms["stun_start"] = SNOWMAN_STOMP_DELAY

    def next_stage(self):
        self.xvelocity = 0
        self.xacceleration = 0
        if self.stage == SNOWMAN_FINAL_STAGE:
            self.kill()
        else:
            if self.was_on_floor:
                play_sound(bigjump_sound)
                self.yvelocity = get_jump_speed(SNOWMAN_HOP_HEIGHT, self.gravity)
                self.stage += 1
                self.hp = SNOWMAN_HP
                self.stun_end = True
            else:
                self.alarms["stun"] = 1

    def kill(self):
        play_sound(fall_sound)
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       yvelocity=get_jump_speed(ENEMY_HIT_BELOW_HEIGHT),
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()

    def move(self):
        super(Snowman, self).move()

        if "stomp_delay" not in self.alarms and not self.stunned:
            self.xacceleration = 0
            if self.stage > 0:
                if self.get_bottom_touching_wall():
                    can_jump = False
                    if self.stage >= SNOWMAN_FINAL_STAGE:
                        walk_speed = SNOWMAN_FINAL_WALK_SPEED
                        accel = SNOWMAN_FINAL_ACCELERATION
                    elif self.stage >= SNOWMAN_STRONG_STAGE:
                        walk_speed = SNOWMAN_STRONG_WALK_SPEED
                        accel = SNOWMAN_STRONG_ACCELERATION
                        can_jump = True
                    else:
                        walk_speed = SNOWMAN_WALK_SPEED
                        accel = SNOWMAN_ACCELERATION

                    player = self.get_nearest_player()
                    if player is not None:
                        d = player.x - self.x
                        if (abs(self.xvelocity) < walk_speed or
                                (self.xvelocity > 0) != (d > 0)):
                            self.xacceleration = math.copysign(accel, d)
                        else:
                            self.xvelocity = math.copysign(walk_speed, d)

                        if (can_jump and self.yvelocity == 0 and
                                self.y - player.y >= SNOWMAN_JUMP_TRIGGER):
                            self.jump()
            else:
                player = self.get_nearest_player()
                if player is not None:
                    self.image_xscale = math.copysign(self.image_xscale,
                                                      player.x - self.x)

    def stop_left(self):
        self.xvelocity = abs(self.xvelocity)

    def stop_right(self):
        self.xvelocity = -abs(self.xvelocity)

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        if self.stage > 0 and self.yvelocity > 1:
            play_sound(brick_sound)
            self.yvelocity = 0
            if not self.stunned:
                self.xvelocity = 0
                self.xacceleration = 0
            sge.game.current_room.shake(3)
            self.alarms["stomp_delay"] = SNOWMAN_STOMP_DELAY
            if self.stun_end:
                self.fixed_sprite = False
                self.stunned = False
                self.stun_end = False

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        if self.stage > 0 and not self.stunned:
            play_sound(squish_sound)
            self.stun()

    def burn(self):
        if self.stage > 0:
            play_sound(sizzle_sound)
            self.hp -= 1
            if self.hp <= 0:
                self.next_stage()

    def knock(self, other=None):
        if self.stage > 0 and not self.stunned:
            play_sound(stomp_sound)
            self.stun()
            if other.knockable:
                other.knock(self)

    def touch_death(self):
        self.kill()

    def event_step(self, time_passed, delta_mult):
        super(Snowman, self).event_step(time_passed, delta_mult)

        if not self.fixed_sprite:
            if self.was_on_floor:
                speed = abs(self.xvelocity)
                if speed > 0:
                    self.sprite = snowman_walk_sprite
                    self.image_speed = (speed * SNOWMAN_WALK_FRAMES_PER_PIXEL)
                else:
                    self.sprite = snowman_stand_sprite
            else:
                self.sprite = snowman_jump_sprite

        if self.xvelocity:
            self.image_xscale = math.copysign(self.image_xscale,
                                              self.xvelocity)

    def event_alarm(self, alarm_id):
        if alarm_id == "stun_start":
            self.image_speed = (SNOWMAN_STUNNED_WALK_SPEED *
                                SNOWMAN_WALK_FRAMES_PER_PIXEL)
            self.xvelocity = math.copysign(SNOWMAN_STUNNED_WALK_SPEED,
                                           self.image_xscale)
            self.alarms["stun"] = SNOWMAN_HITSTUN
        elif alarm_id == "stun":
            self.next_stage()

    def event_destroy(self):
        player = self.get_nearest_player()
        if player is not None:
            player.win_level(False)


class FireFlower(FallingObject, WinPuffObject):

    fall_speed = FLOWER_FALL_SPEED
    slide_speed = 0
    win_puff_points = 0

    def event_create(self):
        super(FireFlower, self).event_create()
        self.sprite = fire_flower_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

        self.ammo = FIREBALL_AMMO

    def touch(self, other):
        if other.pickup(self):
            self.gravity = 0

    def knock(self, other=None):
        self.yvelocity = get_jump_speed(ITEM_HIT_HEIGHT)

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self, up=False):
        if self.parent is not None:
            d = (self.image_xscale >= 0) - (self.image_xscale < 0)
            if self.ammo > 0:
                if up:
                    yv = get_jump_speed(FIREBALL_UP_HEIGHT, Fireball.gravity)
                else:
                    yv = FIREBALL_FALL_SPEED
                Fireball.create(self.x, self.y, self.parent.z,
                                sprite=fire_bullet_sprite,
                                xvelocity=(FIREBALL_SPEED * d), yvelocity=yv,
                                image_xscale=self.image_xscale)
                self.ammo -= 1
                play_sound(shoot_sound)

                self.sprite = fire_flower_sprite.copy()
                lightness = int((self.ammo / FIREBALL_AMMO) * 230 + 25)
                darkener = sge.Sprite(width=self.sprite.width,
                                      height=self.sprite.height)
                darkener.draw_rectangle(0, 0, darkener.width, darkener.height,
                                        fill=sge.Color([lightness] * 3))
                self.sprite.draw_sprite(darkener, 0, 0, 0,
                                        blend_mode=sge.BLEND_RGB_MULTIPLY)
            else:
                h = FLOWER_THROW_UP_HEIGHT if up else FLOWER_THROW_HEIGHT
                yv = get_jump_speed(h, ThrownFlower.gravity)
                self.parent.kick_object()
                play_sound(kick_sound)
                ThrownFlower.create(self.parent, self.x, self.y, self.z,
                                    sprite=self.sprite,
                                    xvelocity=(FIREBALL_SPEED * d),
                                    yvelocity=yv,
                                    image_xscale=self.image_xscale)
                self.parent = None
                self.destroy()
                pass

    def kick_up(self):
        self.kick(True)

    def win_puff(self):
        super(FireFlower, self).win_puff()
        sge.game.current_room.add_points(AMMO_POINTS * (self.ammo + 1))

    def event_end_step(self, time_passed, delta_mult):
        if self.parent is not None:
            direction = -1 if self.parent.image_xscale < 0 else 1
            self.image_xscale = abs(self.image_xscale) * direction


class IceFlower(FallingObject, WinPuffObject):

    fall_speed = FLOWER_FALL_SPEED
    slide_speed = 0
    win_puff_points = 0

    def event_create(self):
        super(IceFlower, self).event_create()
        self.sprite = ice_flower_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

        self.ammo = ICEBULLET_AMMO

    def touch(self, other):
        if other.pickup(self):
            self.gravity = 0

    def knock(self, other=None):
        self.yvelocity = get_jump_speed(ITEM_HIT_HEIGHT)

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            d = (self.image_xscale >= 0) - (self.image_xscale < 0)
            if self.ammo > 0:
                IceBullet.create(self.x, self.y, self.parent.z,
                                 sprite=ice_bullet_sprite,
                                 xvelocity=(ICEBULLET_SPEED * d))
                self.ammo -= 1
                play_sound(shoot_sound)

                self.sprite = ice_flower_sprite.copy()
                lightness = int((self.ammo / ICEBULLET_AMMO) * 230 + 25)
                darkener = sge.Sprite(width=self.sprite.width,
                                      height=self.sprite.height)
                darkener.draw_rectangle(0, 0, darkener.width, darkener.height,
                                        fill=sge.Color([lightness] * 3))
                self.sprite.draw_sprite(darkener, 0, 0, 0,
                                        blend_mode=sge.BLEND_RGB_MULTIPLY)
            else:
                yv = get_jump_speed(FLOWER_THROW_HEIGHT, ThrownFlower.gravity)
                self.parent.kick_object()
                play_sound(kick_sound)
                ThrownFlower.create(self.parent, self.x, self.y, self.z,
                                    sprite=self.sprite,
                                    xvelocity=(FIREBALL_SPEED * d),
                                    yvelocity=yv,
                                    image_xscale=self.image_xscale)
                self.parent = None
                self.destroy()
                pass

    def win_puff(self):
        super(IceFlower, self).win_puff()
        sge.game.current_room.add_points(AMMO_POINTS * (self.ammo + 1))

    def event_end_step(self, time_passed, delta_mult):
        if self.parent is not None:
            direction = -1 if self.parent.image_xscale < 0 else 1
            self.image_xscale = abs(self.image_xscale) * direction


class ThrownFlower(FallingObject, WinPuffObject):

    active_range = BULLET_ACTIVE_RANGE
    fall_speed = FLOWER_FALL_SPEED

    def __init__(self, thrower, *args, **kwargs):
        self.thrower = thrower
        super(ThrownFlower, self).__init__(*args, **kwargs)

    def stop_left(self):
        play_sound(stomp_sound)
        self.destroy()

    def stop_right(self):
        play_sound(stomp_sound)
        self.destroy()

    def stop_up(self):
        play_sound(stomp_sound)
        self.destroy()

    def stop_down(self):
        play_sound(stomp_sound)
        self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)
            play_sound(stomp_sound)
            self.destroy()
        elif isinstance(other, Coin):
            other.event_collision(self.thrower, -xdirection, -ydirection)

        super(ThrownFlower, self).event_collision(other, xdirection, ydirection)

    def event_inactive_step(self, time_passed, delta_mult):
        self.destroy()

    def event_destroy(self):
        Smoke.create(self.x, self.y, self.z, sprite=smoke_puff_sprite)


class Fireball(FallingObject):

    active_range = BULLET_ACTIVE_RANGE
    gravity = FIREBALL_GRAVITY
    fall_speed = FIREBALL_FALL_SPEED

    def stop_left(self):
        self.destroy()

    def stop_right(self):
        self.destroy()

    def stop_down(self):
        self.yvelocity = get_jump_speed(FIREBALL_BOUNCE_HEIGHT, self.gravity)

    def event_inactive_step(self, time_passed, delta_mult):
        self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.burnable:
            other.burn()
            self.destroy()

        super(Fireball, self).event_collision(other, xdirection, ydirection)

    def event_physics_collision_left(self, other, move_loss):
        super(Fireball, self).event_physics_collision_left(other, move_loss)
        self.event_collision(other, -1, 0)

    def event_physics_collision_right(self, other, move_loss):
        super(Fireball, self).event_physics_collision_right(other, move_loss)
        self.event_collision(other, 1, 0)

    def event_physics_collision_top(self, other, move_loss):
        super(Fireball, self).event_physics_collision_top(other, move_loss)
        self.event_collision(other, 0, -1)

    def event_physics_collision_bottom(self, other, move_loss):
        super(Fireball, self).event_physics_collision_bottom(other, move_loss)
        self.event_collision(other, 0, 1)

    def event_destroy(self):
        Smoke.create(self.x, self.y, self.z, sprite=fireball_smoke_sprite)


class IceBullet(InteractiveObject, xsge_physics.Collider):

    active_range = BULLET_ACTIVE_RANGE

    def stop_left(self):
        self.destroy()

    def stop_right(self):
        self.destroy()

    def stop_down(self):
        self.destroy()

    def event_inactive_step(self, time_passed, delta_mult):
        self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.freezable:
            other.freeze()
            self.destroy()

        super(IceBullet, self).event_collision(other, xdirection, ydirection)

    def event_physics_collision_left(self, other, move_loss):
        if isinstance(other, InteractiveObject) and other.freezable:
            other.freeze()

        self.destroy()

    def event_physics_collision_right(self, other, move_loss):
        if isinstance(other, InteractiveObject) and other.freezable:
            other.freeze()

        self.destroy()

    def event_physics_collision_top(self, other, move_loss):
        if isinstance(other, InteractiveObject) and other.freezable:
            other.freeze()

        self.destroy()

    def event_physics_collision_bottom(self, other, move_loss):
        if isinstance(other, InteractiveObject) and other.freezable:
            other.freeze()

        self.destroy()

    def event_destroy(self):
        # TODO: Some kind of ice breaking sparkly effect, and some kind
        # of glass-breaking-esque sound.
        #Smoke.create(self.x, self.y, self.z, sprite=fireball_smoke_sprite)
        pass


class TuxDoll(FallingObject):

    fall_speed = FLOWER_FALL_SPEED
    slide_speed = 0

    def event_create(self):
        super(TuxDoll, self).event_create()
        self.sprite = tuxdoll_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

    def touch(self, other):
        play_sound(tuxdoll_sound)
        sge.game.current_room.add_points(TUXDOLL_POINTS)
        if main_area and main_area not in tuxdolls_found:
            tuxdolls_found.append(main_area)

        self.destroy()

    def knock(self, other=None):
        self.yvelocity = get_jump_speed(ITEM_HIT_HEIGHT)


class CarriedRock(InteractiveObject):

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            Rock.create(self.x - self.image_origin_x,
                        self.y - self.image_origin_y, self.z,
                        sprite=self.sprite, image_xscale=self.image_xscale,
                        image_yscale=self.image_yscale)
            self.destroy()

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            xv = self.parent.xvelocity + math.copysign(
                KICK_FORWARD_SPEED, self.parent.image_xscale)
            yv = get_jump_speed(KICK_FORWARD_HEIGHT, Rock.gravity)
            Rock.create(self.x - self.image_origin_x,
                        self.y - self.image_origin_y, self.z,
                        sprite=self.sprite, xvelocity=xv, yvelocity=yv,
                        image_xscale=self.image_xscale,
                        image_yscale=self.image_yscale)
            self.destroy()

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            xv = self.parent.xvelocity
            yv = get_jump_speed(KICK_UP_HEIGHT, Rock.gravity)
            Rock.create(self.x - self.image_origin_x,
                        self.y - self.image_origin_y, self.z,
                        sprite=self.sprite, xvelocity=xv, yvelocity=yv,
                        image_xscale=self.image_xscale,
                        image_yscale=self.image_yscale)
            self.destroy()


class Rock(FallingObject, xsge_physics.MobileColliderWall,
           xsge_physics.SolidTop):

    sticky_top = True
    active_range = ROCK_ACTIVE_RANGE
    gravity = ROCK_GRAVITY
    fall_speed = ROCK_FALL_SPEED

    def event_create(self):
        super(Rock, self).event_create()
        self.sprite = rock_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

    def touch(self, other):
        cr = CarriedRock.create(self.x, self.y, self.z, sprite=self.sprite,
                                image_xscale=self.image_xscale,
                                image_yscale=self.image_yscale)
        if other.pickup(cr):
            self.destroy()
            if other.action_pressed:
                other.action()
        else:
            cr.destroy()

    def stop_left(self):
        self.xvelocity = 0

    def stop_right(self):
        self.xvelocity = 0

    def stop_up(self):
        self.yvelocity = 0

    def touch_hurt(self):
        pass

    def touch_death(self):
        pass

    def event_end_step(self, time_passed, delta_mult):
        if (self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
            self.xdeceleration = ROCK_FRICTION
        else:
            self.xdeceleration = 0


class FixedSpring(FallingObject):

    active_range = ROCK_ACTIVE_RANGE
    gravity = ROCK_GRAVITY
    fall_speed = ROCK_FALL_SPEED
    jump_height = SPRING_JUMP_HEIGHT
    normal_sprite = None
    expand_sprite = None

    def event_create(self):
        self.update_active()

        self.normal_sprite = fixed_spring_sprite
        self.expand_sprite = fixed_spring_expand_sprite

        self.sprite = self.normal_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

    def stomp(self, other):
        if other is not self.parent:
            other.stomp_jump(self, self.jump_height)
            play_sound(spring_sound)
            self.sprite = self.expand_sprite
            self.image_index = 0
            self.image_fps = None

    def event_animation_end(self):
        if self.sprite == self.expand_sprite:
            self.sprite = self.normal_sprite


class Spring(FixedSpring):

    def event_create(self):
        self.update_active()

        self.normal_sprite = spring_sprite
        self.expand_sprite = spring_expand_sprite

        self.sprite = self.normal_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

    def touch(self, other):
        if other.pickup(self):
            self.gravity = 0

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = self.parent.xvelocity + math.copysign(
                KICK_FORWARD_SPEED, self.parent.image_xscale)
            self.yvelocity = get_jump_speed(KICK_FORWARD_HEIGHT, Rock.gravity)
            self.gravity = self.__class__.gravity
            self.parent = None

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = self.parent.xvelocity
            self.yvelocity = get_jump_speed(KICK_UP_HEIGHT, Rock.gravity)
            self.gravity = self.__class__.gravity
            self.parent = None


class RustySpring(Spring):

    def event_create(self):
        self.update_active()

        self.normal_sprite = rusty_spring_sprite
        self.expand_sprite = rusty_spring_expand_sprite

        self.sprite = self.normal_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

    def event_animation_end(self):
        if self.sprite == self.expand_sprite:
            Corpse.create(self.x, self.y, self.z,
                          sprite=rusty_spring_dead_sprite)
            self.destroy()


class TimelineSwitcher(InteractiveObject):

    def __init__(self, x, y, timeline=None, **kwargs):
        self.timeline = timeline
        kwargs["visible"] = False
        super(TimelineSwitcher, self).__init__(x, y, **kwargs)

    def touch(self, other):
        sge.game.current_room.load_timeline(self.timeline)
        self.destroy()


class Iceblock(InteractiveObject, xsge_physics.Solid):

    burnable = True

    def event_create(self):
        self.update_active()

        self.sprite = iceblock_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None

    def burn(self):
        play_sound(sizzle_sound)
        Smoke.create(self.x, self.y, self.z, sprite=iceblock_melt_sprite)
        self.destroy()


class BossBlock(InteractiveObject):

    def __init__(self, x, y, ID=None, **kwargs):
        self.ID = ID
        kwargs["visible"] = False
        super(BossBlock, self).__init__(x, y, **kwargs)

    def event_create(self):
        super(BossBlock, self).event_create()
        sge.game.current_room.add_timeline_object(self)

    def activate(self):
        self.child = xsge_physics.Solid.create(
            self.x, self.y, self.z, sprite=boss_block_sprite)
        self.child.x += self.child.image_origin_x
        self.child.y += self.child.image_origin_y
        Smoke.create(self.child.x, self.child.y, z=(self.child.z + 0.5),
                     sprite=item_spawn_cloud_sprite)
        play_sound(pop_sound)

    def deactivate(self):
        if self.child is not None:
            Smoke.create(self.child.x, self.child.y, z=self.child.z,
                         sprite=smoke_plume_sprite)
            self.child.destroy()
            self.child = None
            play_sound(pop_sound)


class HittableBlock(xsge_physics.SolidBottom, Tile):

    hit_sprite = None

    def event_create(self):
        self.hit_obj = None

    def event_destroy(self):
        if self.hit_obj is not None:
            self.hit_obj.destroy()

    def event_begin_step(self, time_passed, delta_mult):
        if self.hit_obj is not None:
            if self.hit_obj.y > self.y:
                self.hit_obj.destroy()
                self.hit_obj = None
                self.visible = True
                self.event_hit_end()

    def hit(self, other):
        play_sound(brick_sound)
        if self.hit_obj is not None:
            self.hit_obj.destroy()
            self.hit_obj = None
            self.visible = True
            self.event_hit_end()

        if isinstance(self, xsge_physics.SolidTop):
            for obj in self.collision(InteractiveObject, y=(self.y - 1)):
                if obj.knockable:
                    obj.knock()

        if self in sge.game.current_room.objects:
            if self.hit_sprite is not None:
                s = self.hit_sprite
            else:
                s = self.sprite

            self.visible = False
            self.hit_obj = sge.Object.create(
                self.x, self.y, self.z, sprite=s, tangible=False,
                yvelocity=get_jump_speed(BLOCK_HIT_HEIGHT),
                yacceleration=GRAVITY, image_index=self.image_index,
                image_origin_x=self.image_origin_x,
                image_origin_y=self.image_origin_y,
                image_fps=self.image_fps, image_xscale=self.image_xscale,
                image_yscale=self.image_yscale,
                image_rotation=self.image_rotation)

            self.event_hit(other)

    def event_hit(self, other):
        pass

    def event_hit_end(self):
        pass


class Brick(HittableBlock, xsge_physics.Solid):

    def event_create(self):
        super(Brick, self).event_create()
        self.sprite = brick_sprite

    def event_hit(self, other):
        # TODO: Create brick shards (probably DeadMan objects)
        sge.game.current_room.add_points(10)
        self.destroy()


class CoinBrick(Brick):

    def event_create(self):
        super(CoinBrick, self).event_create()
        self.coins = COINBRICK_COINS

    def event_alarm(self, alarm_id):
        if alarm_id == "decay":
            self.coins -= 1
            self.alarms["decay"] = COINBRICK_DECAY_TIME

    def event_hit(self, other):
        if self.coins > 0:
            self.coins -= 1
            CoinCollect.create(self.x, self.y, z=(self.z + 0.5))
            other.coins += 1

            if "decay" not in self.alarms:
                self.alarms["decay"] = COINBRICK_DECAY_TIME
        else:
            super(CoinBrick, self).event_hit(other)


class EmptyBlock(HittableBlock, xsge_physics.Solid):

    pass


class ItemBlock(HittableBlock, xsge_physics.Solid):

    def __init__(self, x, y, item=None, **kwargs):
        super(ItemBlock, self).__init__(x, y, **kwargs)
        self.item = item

    def event_create(self):
        super(ItemBlock, self).event_create()
        self.sprite = bonus_full_sprite
        self.image_fps = None
        self.hit_sprite = bonus_empty_sprite

    def event_hit(self, other):
        if self.item and self.item in TYPES:
            obj = TYPES[self.item].create(self.x, self.y, z=self.z)
            if obj.sprite is not None and self.sprite is not None:
                obj.x = (self.bbox_left + self.sprite.width / 2 +
                         obj.image_origin_x - obj.sprite.width / 2)
            else:
                obj.bbox_left = self.bbox_left
            obj.bbox_bottom = self.bbox_top
            Smoke.create(obj.x, obj.y, z=(obj.z + 0.5),
                         sprite=item_spawn_cloud_sprite)
            play_sound(find_powerup_sound)
        else:
            CoinCollect.create(self.x, self.y, z=(self.z + 0.5))
            other.coins += 1

    def event_hit_end(self):
        EmptyBlock.create(self.x, self.y, z=self.z, sprite=bonus_empty_sprite)
        self.destroy()


class HiddenItemBlock(HittableBlock):

    def __init__(self, x, y, item=None, **kwargs):
        super(HiddenItemBlock, self).__init__(x, y, **kwargs)
        self.item = item

    def event_create(self):
        super(HiddenItemBlock, self).event_create()
        self.sprite = None

    def hit(self, other):
        b = ItemBlock.create(self.x, self.y, item=self.item, z=self.z)
        b.hit(other)
        self.destroy()


class InfoBlock(HittableBlock, xsge_physics.Solid):

    def __init__(self, x, y, text="(null)", **kwargs):
        super(InfoBlock, self).__init__(x, y, **kwargs)
        self.text = text.replace("\\n", "\n")

    def event_hit_end(self):
        DialogBox(gui_handler, self.text, self.sprite).show()


class ThinIce(xsge_physics.Solid):

    def event_create(self):
        super(ThinIce, self).event_create()
        self.sprite = thin_ice_sprite
        self.image_index = 0
        self.image_fps = 0
        self.crack_time = 0
        self.freeze_time = 0

    def event_step(self, time_passed, delta_mult):
        if self.sprite is thin_ice_sprite:
            players = self.collision(Player, y=(self.y - 1))
            if players:
                for player in players:
                    self.crack_time += delta_mult
                    while self.crack_time >= ICE_CRACK_TIME:
                        self.crack_time -= ICE_CRACK_TIME
                        self.crack()
            elif self.image_index > 0:
                rfa = delta_mult * ICE_REFREEZE_RATE
                self.crack_time -= rfa
                self.rfa = max(0, -self.crack_time)
                self.crack_time = max(0, self.crack_time)
                self.freeze_time += rfa
                while self.freeze_time >= ICE_CRACK_TIME:
                    self.freeze_time -= ICE_CRACK_TIME
                    if self.image_index > 0:
                        self.image_index -= 1
            else:
                self.crack_time -= delta_mult * ICE_REFREEZE_RATE
                self.crack_time = max(0, self.crack_time)

    def event_animation_end(self):
        if self.sprite is thin_ice_sprite:
            self.sprite = thin_ice_break_sprite
            self.image_index = 0
            self.image_fps = None
            play_sound(ice_shatter_sound)
        else:
            self.destroy()

    def crack(self):
        if self.image_index + 1 < self.sprite.frames:
            play_sound(random.choice(ice_crack_sounds))
        self.image_index += 1
        self.freeze_time = 0


class Lava(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = lava_body_sprite
        self.image_fps = None
        self.active = True


class LavaSurface(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = lava_surface_sprite
        self.image_fps = None
        self.active = True


class Goal(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = goal_sprite
        self.image_fps = None
        self.active = True


class GoalTop(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = goal_top_sprite
        self.image_fps = None
        self.active = True


class Coin(Tile):

    def __init__(self, x, y, **kwargs):
        super(Coin, self).__init__(x, y, **kwargs)
        self.sprite = coin_sprite
        self.image_fps = None
        self.checks_collisions = False
        self.active = False

    def event_inactive_step(self, time_passed, delta_mult):
        self.image_index = coin_animation.image_index
        Tile.event_step(self, time_passed, delta_mult)

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Player) and self in sge.game.current_room.objects:
            CoinCollect.create(self.x, self.y, z=self.z,
                               image_index=self.image_index)
            self.destroy()
            other.coins += 1


class CoinCollect(sge.Object):

    def __init__(self, x, y, **kwargs):
        super(CoinCollect, self).__init__(x, y, **kwargs)
        self.sprite = coin_sprite
        self.image_fps = coin_sprite.fps
        self.tangible = False

    def event_create(self):
        play_sound(coin_sound)
        sge.game.current_room.add_points(COIN_POINTS)
        self.alarms["destroy"] = COIN_COLLECT_TIME
        self.yvelocity = -COIN_COLLECT_SPEED

    def event_step(self, time_passed, delta_mult):
        T = self.alarms.get("destroy", COIN_COLLECT_TIME)
        self.image_alpha = 255 * (T / COIN_COLLECT_TIME)

    def event_alarm(self, alarm_id):
        if alarm_id == "destroy":
            self.destroy()


class Spawn(sge.Object):

    def __init__(self, x, y, spawn_id=None, **kwargs):
        super(Spawn, self).__init__(x, y, **kwargs)
        self.spawn_id = spawn_id


class WarpSpawn(xsge_path.Path):

    def __init__(self, x, y, points=(), dest=None, spawn_id=None, **kwargs):
        super(WarpSpawn, self).__init__(x, y, points=points, **kwargs)
        self.dest = dest
        self.spawn_id = spawn_id
        self.direction = None
        self.end_direction = None
        self.warps_out = []

        if points:
            xm, ym = points[0]
            if abs(xm) > abs(ym):
                self.direction = "right" if xm > 0 else "left"
            elif ym:
                self.direction = "down" if ym > 0 else "up"
            else:
                warnings.warn("Warp at position ({}, {}) has no direction".format(x, y))

            if len(points) >= 2:
                x1, y1 = points[-2]
                x2, y2 = points[-1]
                xm = x2 - x1
                ym = y2 - y1
                if abs(xm) > abs(ym):
                    self.end_direction = "right" if xm > 0 else "left"
                elif ym:
                    self.end_direction = "down" if ym > 0 else "up"
                else:
                    warnings.warn("Warp at position ({}, {}) has no end direction".format(x, y))
            else:
                self.end_direction = self.direction



    def event_step(self, time_passed, delta_mult):
        super(WarpSpawn, self).event_step(time_passed, delta_mult)

        x, y = self.points[-1]
        x += self.x
        y += self.y
        finished = []
        for obj in self.warps_out:
            left_edge = obj.x - obj.image_origin_x
            top_edge = obj.y - obj.image_origin_y
            if self.end_direction == "left":
                if obj.bbox_right <= x:
                    obj.bbox_right = x
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        math.ceil(x - left_edge), 0, warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.end_direction == "right":
                if obj.bbox_left >= x:
                    obj.bbox_left = x
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, math.floor(x - left_edge),
                                           warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.end_direction == "up":
                if obj.bbox_bottom <= y:
                    obj.bbox_bottom = y
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        0, math.ceil(y - top_edge), warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.end_direction == "down":
                if obj.bbox_top >= y:
                    obj.bbox_top = y
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, warp_sprite.width,
                                           math.floor(y - top_edge))
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)

        for obj in finished:
            obj.visible = True
            obj.tangible = True
            obj.warping = False
            obj.speed = 0
            self.warps_out.remove(obj)

    def event_follow_end(self, obj):
        global level_timers
        global score

        if self.dest and (':' in self.dest or self.dest == "__map__"):
            if self.dest == "__map__":
                sge.game.current_room.return_to_map()
            else:
                cr = sge.game.current_room
                level_f, spawn = self.dest.split(':', 1)
                if level_f == "__main__":
                    level_f = main_area
                level = sge.game.current_room.__class__.load(level_f)
                if level is not None:
                    level.spawn = spawn
                    level.points = cr.points

                    for nobj in level.objects:
                        if isinstance(nobj, Player):
                            for cobj in cr.objects:
                                if (isinstance(cobj, Player) and
                                        cobj.player == nobj.player):
                                    nobj.hp = cobj.hp
                                    nobj.coins = cobj.coins

                                    held_object = cobj.held_object
                                    if held_object is not None:
                                        cobj.drop_object()
                                        cr.remove(held_object)
                                        level.add(held_object)
                                        nobj.pickup(held_object)

                                    break

                    level.start()
                else:
                    # Error occurred; restart the game.
                    if level_timers.setdefault(main_area, 0) < 0:
                        score -= level_timers[main_area] * SECOND_POINTS
                        level_timers[main_area] = 0
                    save_game()
                    sge.game.start_room.start()
        else:
            play_sound(pipe_sound)
            self.warps_out.append(obj)
            x, y = self.points[-1]
            x += self.x
            y += self.y
            if self.end_direction == "left":
                obj.x = x + obj.sprite.origin_x
                obj.y = y
                obj.move_direction = 180
            elif self.end_direction == "right":
                obj.x = x + obj.sprite.origin_x - obj.sprite.width
                obj.y = y
                obj.move_direction = 0
            elif self.end_direction == "up":
                obj.x = x
                obj.y = y + obj.sprite.origin_y
                obj.move_direction = 90
            elif self.end_direction == "down":
                obj.x = x
                obj.y = y + obj.sprite.origin_y - obj.sprite.height
                obj.move_direction = 270

            obj.speed = WARP_SPEED
            obj.xacceleration = 0
            obj.yacceleration = 0
            obj.xdeceleration = 0
            obj.ydeceleration = 0


class Warp(WarpSpawn):

    def __init__(self, x, y, **kwargs):
        super(Warp, self).__init__(x, y, **kwargs)
        self.warps_in = []

    def warp(self, other):
        play_sound(pipe_sound)
        self.warps_in.append(other)
        other.visible = False
        other.tangible = False
        other.warping = True
        other.move_direction = {"right": 0, "up": 90, "left": 180,
                                "down": 270}.get(self.direction, 0)
        other.speed = WARP_SPEED
        other.xacceleration = 0
        other.yacceleration = 0
        other.xdeceleration = 0
        other.ydeceleration = 0

    def event_create(self):
        if self not in sge.game.current_room.warps:
            sge.game.current_room.warps.append(self)

    def event_end_step(self, time_passed, delta_mult):
        super(Warp, self).event_step(time_passed, delta_mult)

        finished = []
        for obj in self.warps_in:
            left_edge = obj.x - obj.image_origin_x
            top_edge = obj.y - obj.image_origin_y
            if self.direction == "left":
                if obj.x <= self.x + obj.image_origin_x - obj.sprite.width:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        0, 0, math.floor(self.x - left_edge),
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.direction == "right":
                if obj.x >= self.x + obj.image_origin_x:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        math.ceil(self.x - left_edge), 0, warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.direction == "up":
                if obj.y <= self.y + obj.image_origin_y - obj.sprite.height:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, warp_sprite.width,
                                           math.floor(self.y - top_edge))
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.direction == "down":
                if obj.y >= self.y + obj.image_origin_y:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        0, math.ceil(self.y - top_edge), warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)

        for obj in finished:
            obj.x = self.x
            obj.y = self.y
            self.follow_start(obj, WARP_SPEED)
            self.warps_in.remove(obj)

    def event_destroy(self):
        while self in sge.game.current_room.warps:
            sge.game.current_room.warps.remove(self)


class ObjectWarpSpawn(WarpSpawn):

    def __init__(self, x, y, cls=None, interval=180, **kwargs):
        # If dest is defined, that will cause the player to
        # automatically switch to the destination room whenever an
        # object spawns, which is not desirable at all.
        kwargs["dest"] = None
        self.cls = TYPES.get(cls)
        self.interval = interval
        self.__steps_passed = 0
        super(ObjectWarpSpawn, self).__init__(x, y, **kwargs)

    def event_begin_step(self, time_passed, delta_mult):
        in_view = False
        for view in sge.game.current_room.views:
            if (self.x <= view.x + view.width and self.x >= view.x and
                    self.y <= view.y + view.height and self.y >= view.y):
                in_view = True
                break

        if in_view and self.cls is not None:
            self.__steps_passed += delta_mult
            while self.__steps_passed >= self.interval:
                self.__steps_passed -= self.interval
                obj = self.cls.create(self.x, self.y, z=self.z)
                obj.warping = True
                obj.visible = False
                obj.tangible = False
                self.follow_start(obj, WARP_SPEED)


class MovingObjectPath(xsge_path.PathLink):

    cls = None
    default_speed = ENEMY_WALK_SPEED
    default_accel = None
    default_decel = None
    default_loop = None

    def __init__(self, x, y, path_speed=None, path_accel=None, path_decel=None,
                 path_loop=None, path_id=None, prime=False, parent=None,
                 **kwargs):
        if path_speed is None:
            path_speed = self.default_speed
        if path_accel is None:
            path_accel = self.default_accel
        if path_decel is None:
            path_decel = self.default_decel
        if path_loop is None:
            path_loop = self.default_loop

        self.path_speed = path_speed
        self.path_accel = path_accel if path_accel != -1 else None
        self.path_decel = path_decel if path_decel != -1 else None
        self.path_loop = path_loop if path_loop != -1 else None
        self.path_id = path_id
        self.prime = prime
        self.parent = parent
        super(MovingObjectPath, self).__init__(x, y, **kwargs)

    def event_create(self):
        if self.parent is not None:
            for obj in sge.game.current_room.objects:
                if (isinstance(obj, self.__class__) and
                        obj.path_id == self.parent):
                    obj.next_path = self
                    obj.next_speed = self.path_speed
                    obj.next_accel = self.path_accel
                    obj.next_decel = self.path_decel
                    obj.next_loop = self.path_loop
                    break
        else:
            self.prime = True

        if self.prime and self.cls in TYPES:
            obj = TYPES[self.cls].create(self.x, self.y, z=self.z)
            self.follow_start(obj, self.path_speed, accel=self.path_accel,
                              decel=self.path_decel, loop=self.path_loop)


class MovingPlatformPath(MovingObjectPath):

    cls = "moving_platform"
    default_speed = 3
    default_accel = 0.02
    default_decel = 0.02


class FlyingSnowballPath(MovingObjectPath):

    cls = "flying_snowball"
    default_speed = 2
    default_accel = 0.02
    default_decel = 0.02


class CircoflamePath(xsge_path.Path):

    def __init__(self, x, y, z=0, points=(), rvelocity=2):
        self.rvelocity = rvelocity
        x += TILE_SIZE / 2
        y += TILE_SIZE / 2
        super(CircoflamePath, self).__init__(x, y, z=z, points=points)

    def event_create(self):
        if self.points:
            fx, fy = self.points[0]
            radius = math.hypot(fx, fy)
            pos = math.degrees(math.atan2(fy, fx))
            CircoflameCenter.create(self.x, self.y, z=self.z, radius=radius,
                                    pos=pos, rvelocity=self.rvelocity)
        self.destroy()


class MapPlayer(sge.Object):

    moving = False

    def _follow_path(self, space, path):
        if path is not None:
            if path.points:
                x, y = path.points[-1]
            else:
                x = 0
                y = 0
            target_space = MapSpace.get_at(path.x + x, path.y + y)
            if target_space is not None:
                if space.cleared or target_space.cleared:
                    self.moving = True
                    path.follow_start(self, MAP_SPEED)
            else:
                print("Space at position ({}, {}) doesn't exist!".format(
                    path.x + x, path.y + y))

    def move_left(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            path = space.get_left_exit()
            self._follow_path(space, path)

    def move_right(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            path = space.get_right_exit()
            self._follow_path(space, path)

    def move_up(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            path = space.get_up_exit()
            self._follow_path(space, path)

    def move_down(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            path = space.get_down_exit()
            self._follow_path(space, path)

    def move_forward(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            paths = []
            for path in space.get_exits():
                if path is not None and path.forward:
                    paths.append(path)

            if len(paths) == 1:
                self._follow_path(space, paths[0])

    def start_level(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            space.start_level()

    def event_create(self):
        start_space = MapSpace.get_at(self.x,self.y)
        if start_space is None:
            MapSpace.create(self.x, self.y, free=True)
        else:
            start_space.free = True

        if current_worldmap_space is not None:
            for obj in sge.game.current_room.objects:
                if (isinstance(obj, MapSpace) and
                        obj.ID == current_worldmap_space):
                    self.x = obj.x
                    self.y = obj.y

    def event_step(self, time_passed, delta_mult):
        room = sge.game.current_room
        space = MapSpace.get_at(self.x, self.y)

        if space is not None:
            room.level_text = level_names.get(space.level)
            room.level_tuxdoll_available = space.level in tuxdolls_available
            room.level_tuxdoll_found = space.level in tuxdolls_found

            for key in sneak_key:
                if sge.keyboard.get_pressed(key):
                    self.move_forward()
            for key in left_key:
                if sge.keyboard.get_pressed(key):
                    self.move_left()
            for key in right_key:
                if sge.keyboard.get_pressed(key):
                    self.move_right()
            for key in up_key:
                if sge.keyboard.get_pressed(key):
                    self.move_up()
            for key in down_key:
                if sge.keyboard.get_pressed(key):
                    self.move_down()

            for j in six.moves.range(sge.joystick.get_joysticks()):
                x = sge.joystick.get_axis(j, 0)
                if x > JOYSTICK_THRESHOLD:
                    self.move_right()
                elif x < -JOYSTICK_THRESHOLD:
                    self.move_left()

                y = sge.joystick.get_axis(j, 1)
                if y > JOYSTICK_THRESHOLD:
                    self.move_down()
                elif y < -JOYSTICK_THRESHOLD:
                    self.move_up()

                for h in six.moves.range(sge.joystick.get_hats(j)):
                    x = sge.joystick.get_hat_x(j, h)
                    if x > 0:
                        self.move_right()
                    elif x < 0:
                        self.move_left()

                    y = sge.joystick.get_hat_y(j, h)
                    if y > 0:
                        self.move_down()
                    elif y < 0:
                        self.move_up()

        if room.views:
            view = room.views[0]
            view.x = self.x - view.width / 2 + self.sprite.width / 2
            view.y = self.y - view.height / 2 + self.sprite.height / 2

    def event_key_press(self, key, char):
        if key in jump_key or key in action_key or key == "enter":
            self.start_level()

    def event_joystick_button_press(self, js_name, js_id, button):
        self.start_level()

    def event_stop(self):
        self.moving = False


class MapSpace(sge.Object):

    def __init__(self, x, y, level=None, ID=None, free=False, **kwargs):
        super(MapSpace, self).__init__(x, y, **kwargs)
        self.level = level
        self.ID = ID if ID is not None else level
        self.free = free

    @property
    def cleared(self):
        if self.free:
            return True
        else:
            if self.level is not None:
                return self.level in cleared_levels
            else:
                connected_spaces = []
                already_checked = []
                for path in self.get_exits():
                    if path is not None:
                        x, y = path.points[-1]
                        space = MapSpace.get_at(self.x + x, self.y + y)
                        if space is not None:
                            connected_spaces.append(space)

                while connected_spaces:
                    space = connected_spaces.pop(0)
                    already_checked.append(space)
                    if space.free or space.level in cleared_levels:
                        return True
                    elif space.level is None:
                        for path in space.get_exits():
                            if path is not None:
                                x, y = path.points[-1]
                                new_space = MapSpace.get_at(space.x + x,
                                                            space.y + y)
                                if (new_space is not None and
                                        new_space not in connected_spaces and
                                        new_space not in already_checked):
                                    connected_spaces.append(new_space)
                return False

    def update_sprite(self):
        if self.level is not None:
            if self.cleared:
                self.sprite = worldmap_level_complete_sprite
            else:
                self.sprite = worldmap_level_incomplete_sprite
                self.image_fps = None
        else:
            self.sprite = None

    def get_exits(self):
        """
        Return the exits of this space as a tuple in the form:
        (up, right, down, left)
        """
        exits = []
        diagonal_exits = []
        left_exit = None
        right_exit = None
        up_exit = None
        down_exit = None

        for obj in sge.game.current_room.objects:
            if (isinstance(obj, MapPath) and obj.points and
                    abs(self.x - obj.x) < 1 and abs(self.y - obj.y) < 1):
                exits.append(obj)

        # First do exits that are unambiguously one direction
        for obj in exits:
            x, y = obj.points[0]
            if x == 0:
                if y > 0:
                    if down_exit is None:
                        down_exit = obj
                elif y < 0:
                    if up_exit is None:
                        up_exit = obj
                else:
                    warnings.warn("Path at ({}, {}) has no direction!".format(
                        obj.x, obj.y))
            elif y == 0:
                if x > 0:
                    if right_exit is None:
                        right_exit = obj
                elif x < 0:
                    if left_exit is None:
                        left_exit = obj
                else:
                    warnings.warn("Path at ({}, {}) has no direction!".format(
                        obj.x, obj.y))
            else:
                diagonal_exits.append(obj)

        # And now do diagonal exits
        for obj in diagonal_exits:
            x, y = obj.points[0]
            assert x and y
            if abs(y) > abs(x):
                # Mostly vertical
                if y > 0:
                    if down_exit is None:
                        down_exit = obj
                    else:
                        if x > 0:
                            if right_exit is None:
                                right_exit = obj
                        else:
                            if left_exit is None:
                                left_exit = obj
                else:
                    if up_exit is None:
                        up_exit = obj
                    else:
                        if x > 0:
                            if right_exit is None:
                                right_exit = obj
                        else:
                            if left_exit is None:
                                left_exit = obj
            else:
                # Mostly horizontal, or equal
                if x > 0:
                    if right_exit is None:
                        right_exit = obj
                    else:
                        if y > 0:
                            if down_exit is None:
                                down_exit = obj
                        else:
                            if up_exit is None:
                                up_exit = obj
                else:
                    if left_exit is None:
                        left_exit = obj
                    else:
                        if y > 0:
                            if down_exit is None:
                                down_exit = obj
                        else:
                            if up_exit is None:
                                up_exit = obj

        return (up_exit, right_exit, down_exit, left_exit)

    def get_left_exit(self):
        return self.get_exits()[3]

    def get_right_exit(self):
        return self.get_exits()[1]

    def get_up_exit(self):
        return self.get_exits()[0]

    def get_down_exit(self):
        return self.get_exits()[2]

    def start_level(self):
        global main_area

        if self.level:
            main_area = None
            level = Level.load(self.level)
            x = self.x
            y = self.y
            if self.sprite:
                x += self.sprite.width / 2
                y += self.sprite.height / 2
            level.start(transition="iris_in", transition_time=750,
                        transition_arg=(x, y))

    @classmethod
    def get_at(cls, x, y):
        for obj in sge.game.current_room.objects:
            if (isinstance(obj, MapSpace) and abs(x - obj.x) < 1 and
                    abs(y - obj.y) < 1):
                return obj

        return None


class MapWarp(MapSpace):

    def __init__(self, x, y, dest=None, **kwargs):
        super(MapWarp, self).__init__(x, y, **kwargs)
        self.dest = dest

    def update_sprite(self):
        self.sprite = worldmap_warp_sprite
        self.image_fps = None

    def start_level(self):
        global main_area
        global current_worldmap
        global current_worldmap_space

        if self.dest and ':' in self.dest:
            map_f, spawn = self.dest.split(':', 1)
            current_worldmap = map_f
            current_worldmap_space = spawn
        else:
            current_worldmap_space = None

        if self.level:
            main_area = None
            level = Level.load(self.level)
            x = self.x
            y = self.y
            if self.sprite:
                x += self.sprite.width / 2
                y += self.sprite.height / 2
            level.start(transition="iris_in", transition_time=750,
                        transition_arg=(x, y))
        else:
            m = Worldmap.load(current_worldmap)
            m.start(transition="dissolve", transition_time=750)
            play_sound(warp_sound)


class MapPath(xsge_path.Path):

    forward = True

    def event_create(self):
        if self.points:
            if self.forward:
                rx, ry = self.points[-1]
                rx += self.x
                ry += self.y
                rp = []
                for x, y in sorted(self.points[:-1], reverse=True) + [(0, 0)]:
                    x = x + self.x - rx
                    y = y + self.y - ry
                    rp.append((x, y))
                # Not using Object.create to prevent infinite recursion.
                m = MapPath(rx, ry, rp)
                m.forward = False
                sge.game.current_room.add(m)

            if MapSpace.get_at(self.x, self.y) is None:
                MapSpace.create(self.x, self.y)
        else:
            warnings.warn("MapPath at ({}, {}) has only one point!".format(
                self.x, self.y))

    def event_follow_end(self, obj):
        global current_worldmap_space

        if self.points:
            x, y = self.points[-1]
        else:
            x = 0
            y = 0

        obj.x = self.x + x
        obj.y = self.y + y
        obj.moving = False

        space = MapSpace.get_at(obj.x, obj.y)
        if space is not None and space.ID is not None:
            current_worldmap_space = space.ID

        save_game()


class Menu(xsge_gui.MenuWindow):

    items = []

    @classmethod
    def create(cls, default=0):
        if cls.items:
            self = cls.from_text(
                gui_handler, sge.game.width / 2, sge.game.height * 2 / 3,
                cls.items, font_normal=font, color_normal=sge.Color("white"),
                color_selected=sge.Color((0, 128, 255)),
                background_color=sge.Color((64, 64, 255, 64)), margin=9,
                halign="center", valign="middle")
            default %= len(self.widgets)
            self.keyboard_focused_widget = self.widgets[default]
            self.show()
            return self

    def event_change_selection(self, selection):
        play_sound(select_sound)


class MainMenu(Menu):

    items = ["New Game", "Load Game", "Select Levelset", "Options", "Quit"]

    def event_choose(self):
        if self.choice == 0:
            NewGameMenu.create_page()
        elif self.choice == 1:
            LoadGameMenu.create_page()
        elif self.choice == 2:
            LevelsetMenu.create_page(default=-1, refreshlist=True)
        elif self.choice == 3:
            OptionsMenu.create_page()
        else:
            sge.game.end()


class NewGameMenu(Menu):

    @classmethod
    def create_page(cls, default=0):
        cls.items = []
        for slot in save_slots:
            if slot is None:
                cls.items.append("-Empty-")
            elif slot.get("levelset") is None:
                cls.items.append("-No Levelset-")
            else:
                fname = os.path.join(DATA, "levelsets", slot["levelset"])
                try:
                    with open(fname, 'r') as f:
                        data = json.load(f)
                except (IOError, ValueError):
                    cls.items.append("-Corrupt Levelset-")
                    continue
                else:
                    levelset_name = data.get("name", slot["levelset"])
                    completion = slot.get("completion", 0)
                    cls.items.append("{} ({}%)".format(levelset_name,
                                                       completion))

        cls.items.append("Back")

        return cls.create(default)

    def event_choose(self):
        global current_save_slot

        if self.choice in six.moves.range(len(save_slots)):
            current_save_slot = self.choice
            m = "Are you sure to override the existing saved game in this slot? This cannot be undone!"
            sge.game.mouse.visible = True
            if (save_slots[current_save_slot] is None or
                    xsge_gui.show_message(message=m, buttons=["No", "Yes"],
                                          default=0)):
                set_new_game()
                start_levelset()
            else:
                NewGameMenu.create(default=self.choice)
            sge.game.mouse.visible = False
        else:
            MainMenu.create(default=0)


class LoadGameMenu(NewGameMenu):

    def event_choose(self):
        global current_save_slot

        if self.choice in six.moves.range(len(save_slots)):
            current_save_slot = self.choice
            load_game()
            if not start_levelset():
                m = "An error occurred when trying to load the game."
                xsge_gui.show_message(message=m, buttons=["Ok"])
                MainMenu.create(default=1)
        else:
            MainMenu.create(default=1)


class LevelsetMenu(Menu):

    levelsets = []
    current_levelsets = []
    page = 0

    @classmethod
    def create_page(cls, default=0, page=0, refreshlist=False):
        if refreshlist or not cls.levelsets:
            cls.levelsets = []
            for fname in os.listdir(os.path.join(DATA, "levelsets")):
                try:
                    with open(os.path.join(DATA, "levelsets", fname), 'r') as f:
                        data = json.load(f)
                except (IOError, ValueError):
                    continue
                else:
                    cls.levelsets.append((fname, str(data.get("name", "???"))))

            cls.levelsets.sort(key=lambda T: T[1].lower() + T[0].lower())

        cls.current_levelsets = []
        cls.items = []
        if cls.levelsets:
            page_size = MENU_MAX_ITEMS - 2
            n_pages = math.ceil(len(cls.levelsets) / page_size)
            page %= n_pages
            page_start = page * page_size
            page_end = min(page_start + page_size, len(cls.levelsets))
            current_page = cls.levelsets[page_start:page_end]
            cls.current_levelsets = []
            cls.items = []
            for fname, name in current_page:
                cls.current_levelsets.append(fname)
                cls.items.append(name)

        cls.items.append("Next page")
        cls.items.append("Back")

        self = cls.create(default)
        self.page = page
        return self

    def event_choose(self):
        if self.choice == len(self.items) - 2:
            self.create_page(default=-2, page=self.page)
        else:
            if self.choice is not None and self.choice < len(self.items) - 2:
                load_levelset(self.current_levelsets[self.choice])

            MainMenu.create(default=2)


class OptionsMenu(Menu):

    @classmethod
    def create_page(cls, default=0):
        cls.items = [
            "Fullscreen: {}".format("On" if sge.game.fullscreen else "Off"),
            "Sound: {}".format("On" if sound_enabled else "Off"),
            "Music: {}".format("On" if music_enabled else "Off"),
            "Configure keyboard", "Configure joysticks", "Back"]
        return cls.create(default)

    def event_choose(self):
        global fullscreen
        global sound_enabled
        global music_enabled

        if self.choice == 0:
            fullscreen = not fullscreen
            sge.game.fullscreen = fullscreen
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 1:
            sound_enabled = not sound_enabled
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 2:
            music_enabled = not music_enabled
            play_music(sge.game.current_room.music)
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 3:
            KeyboardMenu.create_page()
        elif self.choice == 4:
            JoystickMenu.create_page()
        else:
            MainMenu.create(default=3)


class KeyboardMenu(Menu):

    page = 0

    @classmethod
    def create_page(cls, default=0, page=0):
        page %= min(len(left_key), len(right_key), len(up_key), len(down_key),
                    len(jump_key), len(action_key), len(sneak_key))
        cls.items = ["Player {}".format(page + 1),
                     "Left: {}".format(left_key[page]),
                     "Right: {}".format(right_key[page]),
                     "Up: {}".format(up_key[page]),
                     "Down: {}".format(down_key[page]),
                     "Jump: {}".format(jump_key[page]),
                     "Action: {}".format(action_key[page]),
                     "Sneak: {}".format(sneak_key[page]),
                     "Back"]
        self = cls.create(default)
        self.page = page
        return self

    def event_choose(self):
        if self.choice == 0:
            KeyboardMenu.create_page(default=self.choice, page=(self.page + 1))
        elif self.choice == 1:
            k = wait_key()
            if k is not None:
                left_key[self.page] = k
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 2:
            k = wait_key()
            if k is not None:
                right_key[self.page] = k
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 3:
            k = wait_key()
            if k is not None:
                up_key[self.page] = k
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 4:
            k = wait_key()
            if k is not None:
                down_key[self.page] = k
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 5:
            k = wait_key()
            if k is not None:
                jump_key[self.page] = k
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 6:
            k = wait_key()
            if k is not None:
                action_key[self.page] = k
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 7:
            k = wait_key()
            if k is not None:
                sneak_key[self.page] = k
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        else:
            OptionsMenu.create_page(default=3)


class JoystickMenu(Menu):

    page = 0

    @classmethod
    def create_page(cls, default=0, page=0):
        page %= min(len(left_js), len(right_js), len(up_js), len(down_js),
                    len(jump_js), len(action_js), len(sneak_js))
        js_template = "Joystick {} {} {}"
        cls.items = ["Player {}".format(page + 1),
                     "Left: {}".format(js_template.format(*left_js[page])),
                     "Right: {}".format(js_template.format(*right_js[page])),
                     "Up: {}".format(js_template.format(*up_js[page])),
                     "Down: {}".format(js_template.format(*down_js[page])),
                     "Jump: {}".format(js_template.format(*jump_js[page])),
                     "Action: {}".format(js_template.format(*action_js[page])),
                     "Sneak: {}".format(js_template.format(*sneak_js[page])),
                     "Back"]
        cls.create(default)

        self = cls.create(default)
        self.page = page
        return self

    def event_choose(self):
        if self.choice == 0:
            JoystickMenu.create_page(default=self.choice, page=(self.page + 1))
        elif self.choice == 1:
            js = wait_js()
            if js is not None:
                left_js[self.page] = js
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 2:
            js = wait_js()
            if js is not None:
                right_js[self.page] = js
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 3:
            js = wait_js()
            if js is not None:
                up_js[self.page] = js
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 4:
            js = wait_js()
            if js is not None:
                down_js[self.page] = js
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 5:
            js = wait_js()
            if js is not None:
                jump_js[self.page] = js
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 6:
            js = wait_js()
            if js is not None:
                action_js[self.page] = js
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 7:
            js = wait_js()
            if js is not None:
                sneak_js[self.page] = js
            JoystickMenu.create_page(default=self.choice, page=self.page)
        else:
            OptionsMenu.create_page(default=4)


class DialogLabel(xsge_gui.ProgressiveLabel):

    def event_add_character(self):
        if self.text[-1] not in (' ', '\n', '\t'):
            play_sound(type_sound)


class DialogBox(xsge_gui.Dialog):

    def __init__(self, parent, text, portrait=None, rate=TEXT_SPEED):
        width = sge.game.width / 2
        x_padding = 16
        y_padding = 16
        label_x = 8
        label_y = 8
        if portrait is not None:
            x_padding += 8
            label_x += 8
            portrait_w = portrait.width
            portrait_h = portrait.height
            label_x += portrait_w
        else:
            portrait_w = 0
            portrait_h = 0
        label_w = max(1, width - portrait_w - x_padding)
        height = max(1, portrait_h + y_padding,
                     font.get_height(text, width=label_w) + y_padding)
        x = sge.game.width / 2 - width / 2
        y = sge.game.height / 2 - height / 2
        super(DialogBox, self).__init__(
            parent, x, y, width, height,
            background_color=sge.Color((64, 64, 255, 64)), border=False)
        label_h = max(1, height - y_padding)

        self.label = DialogLabel(self, label_x, label_y, 0, text, font=font,
                                 width=label_w, height=label_h,
                                 color=sge.Color("white"), rate=rate)

        if portrait is not None:
            xsge_gui.Widget(self, 8, 8, 0, sprite=portrait)

    def event_key_press(self, key, char):
        if key == "enter" or key in jump_key or key in action_key:
            if len(self.label.text) < len(self.label.full_text):
                self.label.text = self.label.full_text
            else:
                self.destroy()

    def event_joystick_button_press(self, js_name, js_id, button):
        self.event_key_press("enter", "\n")


def get_object(x, y, cls=None, **kwargs):
    cls = TYPES.get(cls, xsge_tmx.Decoration)
    return cls(x, y, **kwargs)


def get_scaled_copy(obj):
    s = obj.sprite.copy()
    if obj.image_xscale < 0:
        s.mirror()
    if obj.image_yscale < 0:
        s.flip()
    s.width *= abs(obj.image_xscale)
    s.height *= abs(obj.image_yscale)
    s.rotate(obj.image_rotation)
    s.origin_x = obj.image_origin_x
    s.origin_y = obj.image_origin_y
    return s


def get_jump_speed(height, gravity=GRAVITY):
    # Get the speed to achieve a given height using a kinematic
    # equation: v[f]^2 = v[i]^2 + 2ad
    return -math.sqrt(2 * gravity * height)


def wait_key():
    # Wait for a key press and return it.
    while True:
        # Input events
        sge.game.pump_input()
        while sge.game.input_events:
            event = sge.game.input_events.pop(0)
            if isinstance(event, sge.input.KeyPress):
                sge.game.pump_input()
                sge.game.input_events = []
                if event.key == "escape":
                    return None
                else:
                    return event.key

        # Regulate speed
        sge.game.regulate_speed(fps=10)

        # Project text
        text = "Press the key you wish to use for this function, or Escape to cancel."
        sge.game.project_text(font, text, sge.game.width / 2,
                              sge.game.height / 2, width=sge.game.width,
                              height=sge.game.height,
                              color=sge.Color("white"),
                              halign="center", valign="middle")

        # Refresh
        sge.game.refresh()


def wait_js():
    # Wait for a joystick press and return it.
    while True:
        # Input events
        sge.game.pump_input()
        while sge.game.input_events:
            event = sge.game.input_events.pop(0)
            if isinstance(event, sge.input.KeyPress):
                if event.key == "escape":
                    sge.game.pump_input()
                    sge.game.input_events = []
                    return None
            elif isinstance(event, sge.input.JoystickAxisMove):
                if event.value > JOYSTICK_THRESHOLD:
                    sge.game.pump_input()
                    sge.game.input_events = []
                    return (event.js_id, "axis+", event.axis)
                elif event.value < -JOYSTICK_THRESHOLD:
                    sge.game.pump_input()
                    sge.game.input_events = []
                    return (event.js_id, "axis-", event.axis)
            elif isinstance(event, sge.input.JoystickHatMove):
                sge.game.pump_input()
                sge.game.input_events = []
                t = ("hatx+" if event.x > 0 else
                     "hatx-" if event.x < 0 else
                     "haty+" if event.y > 0 else
                     "haty-" if event.y < 0 else
                     "hatx0")
                return (event.js_id, t, event.hat)
            elif isinstance(event, sge.input.JoystickButtonPress):
                sge.game.pump_input()
                sge.game.input_events = []
                return (event.js_id, "button", event.button)

        # Regulate speed
        sge.game.regulate_speed(fps=10)

        # Project text
        text = "Press the joystick button, axis, or hat direction you wish to use for this function, or Escape to cancel."
        sge.game.project_text(font, text, sge.game.width / 2,
                              sge.game.height / 2, width=sge.game.width,
                              height=sge.game.height,
                              color=sge.Color("white"),
                              halign="center", valign="middle")

        # Refresh
        sge.game.refresh()


def play_sound(sound, *args, **kwargs):
    if sound_enabled and sound:
        sound.play(*args, **kwargs)


def play_music(music, force_restart=False):
    """Play the given music file, starting with its start piece."""
    if music_enabled and music:
        music_object = loaded_music.get(music)
        if music_object is None:
            try:
                music_object = sge.Music(os.path.join(DATA, "music", music))
            except IOError:
                sge.Music.clear_queue()
                sge.Music.stop()
                return
            else:
                loaded_music[music] = music_object

        name, ext = os.path.splitext(music)
        music_start = ''.join((name, "-start", ext))
        music_start_object = loaded_music.get(music_start)
        if music_start_object is None:
            try:
                music_start_object = sge.Music(os.path.join(DATA, "music",
                                                            music_start))
            except IOError:
                music_start_object = music_object
            else:
                loaded_music[music_start] = music_start_object

        if (force_restart or
                (not music_object.playing and not music_start_object.playing)):
            sge.Music.clear_queue()
            sge.Music.stop()
            music_start_object.play()
            music_object.queue(loops=None)
    else:
        sge.Music.clear_queue()
        sge.Music.stop()


def load_levelset(fname):
    global current_levelset
    global worldmaps
    global levels
    global tuxdolls_available

    current_levelset = fname

    with open(os.path.join(DATA, "levelsets", fname), 'r') as f:
        data = json.load(f)

    worldmaps = data.get("worldmaps", [])
    levels = data.get("levels", [])
    tuxdolls_available = []

    for level in levels:
        subrooms = [level]
        already_checked = []

        while subrooms:
            subroom = subrooms.pop(0)
            already_checked.append(subroom)
            r = Level.load(subroom)
            if r is not None:
                for obj in r.objects:
                    if (isinstance(obj, TuxDoll) or
                            (isinstance(obj, (ItemBlock, HiddenItemBlock)) and
                             obj.item == "tuxdoll")):
                        tuxdolls_available.append(level)
                        subrooms = []
                        break
                    elif isinstance(obj, Warp):
                        if obj.dest and ':' in obj.dest:
                            map_f = obj.dest.split(':', 1)[0]
                            if (map_f not in subrooms and
                                    map_f not in already_checked):
                                subrooms.append(map_f)


def set_new_game():
    global level_timers
    global cleared_levels
    global tuxdolls_found
    global current_worldmap
    global current_worldmap_space
    global current_level
    global score

    level_timers = {}
    cleared_levels = []
    tuxdolls_found = []
    if worldmaps:
        current_worldmap = worldmaps[0]
    else:
        current_worldmap = None
    current_worldmap_space = None
    current_level = 0
    score = 0


def save_game():
    global save_slots

    if current_save_slot is not None:
        save_slots[current_save_slot] = {
            "levelset": current_levelset, "level_timers": level_timers,
            "cleared_levels": cleared_levels, "tuxdolls_found": tuxdolls_found,
            "current_worldmap": current_worldmap,
            "current_worldmap_space": current_worldmap_space,
            "current_level": current_level, "score": score,
            "completion": int(100 * (len(cleared_levels) +
                                     len(tuxdolls_found)) /
                              (len(levels) + len(tuxdolls_available)))}


def load_game():
    global level_timers
    global cleared_levels
    global tuxdolls_found
    global current_worldmap
    global current_worldmap_space
    global current_level
    global score

    if (current_save_slot is not None and
            save_slots[current_save_slot].get("levelset") is not None):
        slot = save_slots[current_save_slot]
        load_levelset(slot["levelset"])
        level_timers = slot.get("level_timers", {})
        cleared_levels = slot.get("cleared_levels", [])
        tuxdolls_found = slot.get("tuxdolls_found", [])
        current_worldmap = slot.get("current_worldmap")
        current_worldmap_space = slot.get("current_worldmap_space")
        current_level = slot.get("current_level", 0)
        score = slot.get("score", 0)
    else:
        set_new_game()


def start_levelset():
    global main_area
    global level_cleared
    global current_areas
    current_areas = {}
    main_area = None
    level_cleared = True

    if current_worldmap:
        m = Worldmap.load(current_worldmap)
        m.start()
    elif current_level < len(levels):
        level = Level.load(levels[current_level])
        level.start()
    else:
        print("Invalid save file: current level does not exist.")
        return False

    return True


TYPES = {"solid_left": SolidLeft, "solid_right": SolidRight,
         "solid_top": SolidTop, "solid_bottom": SolidBottom, "solid": Solid,
         "slope_topleft": SlopeTopLeft, "slope_topright": SlopeTopRight,
         "slope_bottomleft": SlopeBottomLeft,
         "slope_bottomright": SlopeBottomRight,
         "moving_platform": MovingPlatform, "spike_left": SpikeLeft,
         "spike_right": SpikeRight, "spike_top": SpikeTop,
         "spike_bottom": SpikeBottom, "death": Death, "level_end": LevelEnd,
         "creatures": get_object, "hazards": get_object,
         "special_blocks": get_object, "decoration_small": get_object,
         "map_objects": get_object, "player": Player,
         "walking_snowball": WalkingSnowball,
         "bouncing_snowball": BouncingSnowball,
         "walking_iceblock": WalkingIceblock, "spiky": Spiky,
         "bomb": WalkingBomb, "jumpy": Jumpy,
         "flying_snowball": FlyingSnowball, "icicle": Icicle,
         "krush": Krush, "krosh": Krosh, "circoflame": CircoflamePath,
         "snowman": Snowman, "fireflower": FireFlower, "iceflower": IceFlower,
         "tuxdoll": TuxDoll, "rock": Rock, "fixed_spring": FixedSpring,
         "spring": Spring, "rusty_spring": RustySpring,
         "timeline_switcher": TimelineSwitcher, "iceblock": Iceblock,
         "boss_block": BossBlock, "brick": Brick, "coinbrick": CoinBrick,
         "emptyblock": EmptyBlock, "itemblock": ItemBlock,
         "hiddenblock": HiddenItemBlock, "infoblock": InfoBlock,
         "thin_ice": ThinIce, "lava": Lava, "lava_surface": LavaSurface,
         "goal": Goal, "goal_top": GoalTop, "coin": Coin, "warp": Warp,
         "moving_platform_path": MovingPlatformPath,
         "flying_snowball_path": FlyingSnowballPath, "warp_spawn": WarpSpawn,
         "object_warp_spawn": ObjectWarpSpawn, "map_player": MapPlayer,
         "map_level": MapSpace, "map_warp": MapWarp, "map_path": MapPath}


Game(SCREEN_SIZE[0], SCREEN_SIZE[1], scale_smooth=(not args.scale_basic),
     fps=FPS, delta=(not args.nodelta), delta_min=DELTA_MIN,
     window_text="reTux {}".format(__version__),
     window_icon=os.path.join(DATA, "images", "misc", "icon.png"))
xsge_gui.init()

gui_handler = xsge_gui.Handler()

# Load sprites
d = os.path.join(DATA, "images", "objects", "tux")
tux_body_stand_sprite = sge.Sprite(
    "tux_body_stand", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_stand_sprite = sge.Sprite(
    "tux_arms_stand", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_idle_sprite = sge.Sprite(
    "tux_body_idle", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_idle_sprite = sge.Sprite(
    "tux_arms_stand", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_walk_sprite = sge.Sprite(
    "tux_body_walk", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_walk_sprite = sge.Sprite(
    "tux_arms_walk", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
# TODO: Proper separate run sprite
tux_body_run_sprite = sge.Sprite(
    "tux_body_walk", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_run_sprite = sge.Sprite(
    "tux_arms_kick", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_skid_sprite = sge.Sprite(
    "tux_body_skid", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_skid_sprite = sge.Sprite(
    "tux_arms_skid", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_jump_sprite = sge.Sprite(
    "tux_body_jump", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_jump_sprite = sge.Sprite(
    "tux_arms_jump", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_fall_sprite = tux_body_jump_sprite.copy()
tux_arms_fall_sprite = sge.Sprite(
    "tux_arms_fall", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_kick_sprite = sge.Sprite(
    "tux_body_kick", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_kick_sprite = sge.Sprite(
    "tux_arms_kick", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_grab_sprite = sge.Sprite(
    "tux_arms_grab", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_skid_grab_sprite = sge.Sprite(
    "tux_arms_skid_grab", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_die_sprite = sge.Sprite("tux_die", d, origin_x=32, origin_y=11, fps=8)

tux_stand_sprite = tux_body_stand_sprite.copy()
tux_idle_sprite = tux_body_idle_sprite.copy()
tux_walk_sprite = tux_body_walk_sprite.copy()
tux_run_sprite = tux_body_run_sprite.copy()
tux_skid_sprite = tux_body_skid_sprite.copy()
tux_jump_sprite = tux_body_jump_sprite.copy()
tux_fall_sprite = tux_body_fall_sprite.copy()
tux_kick_sprite = tux_body_kick_sprite.copy()

for bs, a in [(tux_stand_sprite, tux_arms_stand_sprite),
              (tux_idle_sprite, tux_arms_idle_sprite),
              (tux_walk_sprite, tux_arms_walk_sprite),
              (tux_run_sprite, tux_arms_run_sprite),
              (tux_skid_sprite, tux_arms_skid_sprite),
              (tux_jump_sprite, tux_arms_jump_sprite),
              (tux_fall_sprite, tux_arms_fall_sprite),
              (tux_kick_sprite, tux_arms_kick_sprite)]:
    for i in six.moves.range(bs.frames):
        bs.draw_sprite(a, i, bs.origin_x, bs.origin_y, i)

d = os.path.join(DATA, "images", "objects", "enemies")
snowball_walk_sprite = sge.Sprite("snowball", d, origin_x=19, origin_y=4,
                                  fps=8, bbox_x=-13, bbox_y=0,
                                  bbox_width=26, bbox_height=32)
bouncing_snowball_sprite = sge.Sprite("bouncing_snowball", d, origin_x=17,
                                      origin_y=0, fps=8, bbox_x=-13, bbox_y=0,
                                      bbox_width=26, bbox_height=32)
snowball_squished_sprite = sge.Sprite("snowball_squished", d, origin_x=17,
                                      origin_y=-19, bbox_x=-13, bbox_y=19,
                                      bbox_width=26, bbox_height=13)
iceblock_walk_sprite = sge.Sprite("iceblock", d, origin_x=18, origin_y=6,
                                  fps=10, bbox_x=-13, bbox_y=1, bbox_width=25,
                                  bbox_height=31)
iceblock_flat_sprite = sge.Sprite("iceblock_flat", d, origin_x=18, origin_y=6,
                                  bbox_x=-16, bbox_y=1, bbox_width=31,
                                  bbox_height=28)
spiky_walk_sprite = sge.Sprite("spiky", d, origin_x=22, origin_y=10, fps=8,
                               bbox_x=-13, bbox_y=0, bbox_width=26,
                               bbox_height=32)
spiky_iced_sprite = sge.Sprite("spiky_iced", d, origin_x=22, origin_y=10,
                               fps=8, bbox_x=-13, bbox_y=0, bbox_width=26,
                               bbox_height=32)
bomb_walk_sprite = sge.Sprite("bomb", d, origin_x=21, origin_y=8, fps=8,
                              bbox_x=-13, bbox_y=0, bbox_width=26,
                              bbox_height=32)
bomb_iced_sprite = sge.Sprite("bomb_iced", d, origin_x=21, origin_y=8,
                              bbox_x=-13, bbox_y=0, bbox_width=26,
                              bbox_height=32)
bomb_ticking_sprite = sge.Sprite("bomb_ticking", d, origin_x=21, origin_y=8,
                                 bbox_x=-13, bbox_y=0, bbox_width=26,
                                 bbox_height=29)
bomb_ticking_sprite.fps = bomb_ticking_sprite.frames / BOMB_TICK_TIME
jumpy_sprite = sge.Sprite("jumpy", d, origin_x=24, origin_y=13, bbox_x=-17,
                          bbox_y=0, bbox_width=33, bbox_height=32)
jumpy_bounce_sprite = sge.Sprite("jumpy_bounce", d, origin_x=24, origin_y=13,
                                 bbox_x=-17, bbox_y=0, bbox_width=33,
                                 bbox_height=32)
jumpy_iced_sprite = sge.Sprite("jumpy_iced", d, origin_x=24, origin_y=13,
                               bbox_x=-17, bbox_y=0, bbox_width=33,
                               bbox_height=32)
flying_snowball_sprite = sge.Sprite("flying_snowball", d, origin_x=20,
                                    origin_y=11, fps=15, bbox_x=-13, bbox_y=0,
                                    bbox_width=26, bbox_height=32)
flying_snowball_squished_sprite = sge.Sprite(
    "flying_snowball_squished", d, origin_x=20, origin_y=-11, bbox_x=-13,
    bbox_y=11, bbox_width=26, bbox_height=21)
icicle_sprite = sge.Sprite("icicle", d, bbox_x=8, bbox_y=0, bbox_width=16,
                           bbox_height=48)
icicle_broken_sprite = sge.Sprite("icicle_broken", d, bbox_x=12, bbox_y=32,
                                  bbox_width=8, bbox_height=16)
krush_sprite = sge.Sprite("krush", d, origin_x=1, bbox_x=0, bbox_y=0,
                          bbox_width=64, bbox_height=64)
krosh_sprite = sge.Sprite("krosh", d, origin_x=2, bbox_x=0, bbox_y=0,
                          bbox_width=128, bbox_height=128)
circoflame_sprite = sge.Sprite("circoflame", d, origin_x=16, origin_y=16,
                               fps=8, bbox_x=-8, bbox_y=-8, bbox_width=16,
                               bbox_height=16)
snowman_stand_sprite = sge.Sprite("snowman_stand", d, origin_x=28, origin_y=43,
                                  bbox_x=-14, bbox_y=-40, bbox_width=28,
                                  bbox_height=72)
snowman_walk_sprite = sge.Sprite("snowman_walk", d, origin_x=28, origin_y=43,
                                 bbox_x=-14, bbox_y=-40, bbox_width=28,
                                 bbox_height=72)
snowman_jump_sprite = sge.Sprite("snowman_jump", d, origin_x=28, origin_y=43,
                                 bbox_x=-14, bbox_y=-40, bbox_width=28,
                                 bbox_height=72)
snowman_hurt_walk_sprite = sge.Sprite("snowman_hurt_walk", d, origin_x=28,
                                      origin_y=43, bbox_x=-14, bbox_y=-8,
                                      bbox_width=28, bbox_height=40)
snowman_hurt_jump_sprite = sge.Sprite("snowman_hurt_jump", d, origin_x=28,
                                      origin_y=43, bbox_x=-14, bbox_y=-8,
                                      bbox_width=28, bbox_height=40)

d = os.path.join(DATA, "images", "objects", "bonus")
bonus_empty_sprite = sge.Sprite("bonus_empty", d)
bonus_full_sprite = sge.Sprite("bonus_full", d, fps=8)
brick_sprite = sge.Sprite("brick", d)
coin_sprite = sge.Sprite("coin", d, fps=8)
fire_flower_sprite = sge.Sprite("fire_flower", d, origin_x=16, origin_y=16,
                                fps=8, bbox_x=-8, bbox_y=-8, bbox_width=16,
                                bbox_height=24)
ice_flower_sprite = sge.Sprite("ice_flower", d, origin_x=16, origin_y=16,
                               fps=8, bbox_x=-8, bbox_y=-8, bbox_width=16,
                               bbox_height=24)
tuxdoll_sprite = sge.Sprite("tuxdoll", d, origin_x=16, origin_y=16, bbox_x=-16,
                            bbox_y=-16, bbox_width=32, bbox_height=32)

tuxdoll_transparent_sprite = tuxdoll_sprite.copy()
eraser = sge.Sprite(width=tuxdoll_transparent_sprite.width,
                    height=tuxdoll_transparent_sprite.height)
eraser.draw_rectangle(0, 0, eraser.width, eraser.height,
                      fill=sge.Color((0, 0, 0, 128)))
tuxdoll_transparent_sprite.draw_sprite(eraser, 0, 0, 0,
                                       blend_mode=sge.BLEND_RGBA_SUBTRACT)
del eraser

tuxdoll_shadow_sprite = tuxdoll_sprite.copy()
darkener = sge.Sprite(width=tuxdoll_shadow_sprite.width,
                      height=tuxdoll_shadow_sprite.height)
darkener.draw_rectangle(0, 0, darkener.width, darkener.height,
                        fill=sge.Color("black"))
tuxdoll_shadow_sprite.draw_sprite(darkener, 0, 0, 0,
                                  blend_mode=sge.BLEND_RGB_MINIMUM)
del darkener

d = os.path.join(DATA, "images", "objects", "decoration")
lava_body_sprite = sge.Sprite("lava_body", d, transparent=False, fps=5)
lava_surface_sprite = sge.Sprite("lava_surface", d, fps=5)
goal_sprite = sge.Sprite("goal", d, fps=8)
goal_top_sprite = sge.Sprite("goal_top", d, fps=8)

d = os.path.join(DATA, "images", "objects", "spring")
fixed_spring_sprite = sge.Sprite(
    "fixed_spring", d, origin_x=16, origin_y=16, bbox_x=-16, bbox_y=-7,
    bbox_width=32, bbox_height=23)
fixed_spring_expand_sprite = sge.Sprite(
    "fixed_spring_expand", d, origin_x=16, origin_y=16, fps=16, bbox_x=-16,
    bbox_y=-7, bbox_width=32, bbox_height=23)
spring_sprite = sge.Sprite("spring", d, origin_x=16, origin_y=16, bbox_x=-16,
                           bbox_y=-7, bbox_width=32, bbox_height=23)
spring_expand_sprite = sge.Sprite(
    "spring_expand", d, origin_x=16, origin_y=16, fps=16, bbox_x=-16,
    bbox_y=-7, bbox_width=32, bbox_height=23)
rusty_spring_sprite = sge.Sprite(
    "rusty_spring", d, origin_x=16, origin_y=16, bbox_x=-16, bbox_y=-7,
    bbox_width=32, bbox_height=23)
rusty_spring_expand_sprite = sge.Sprite(
    "rusty_spring_expand", d, origin_x=16, origin_y=26, fps=16, bbox_x=-16,
    bbox_y=-7, bbox_width=32, bbox_height=23)
rusty_spring_dead_sprite = sge.Sprite(
    "rusty_spring_dead", d, origin_x=16, origin_y=26, bbox_x=-16, bbox_y=-7,
    bbox_width=32, bbox_height=23)

d = os.path.join(DATA, "images", "objects", "misc")
platform_sprite = sge.Sprite("platform", d)
rock_sprite = sge.Sprite("rock", d, origin_x=16, origin_y=16)
iceblock_sprite = sge.Sprite("iceblock", d)
iceblock_melt_sprite = sge.Sprite("iceblock_melt", d, fps=30)
thin_ice_sprite = sge.Sprite("thin_ice", d, fps=0)
thin_ice_break_sprite = sge.Sprite("thin_ice_break", d, fps=8)
boss_block_sprite = sge.Sprite("boss_block", d, origin_x=16, origin_y=16)

d = os.path.join(DATA, "images", "misc")
logo_sprite = sge.Sprite("logo", d, origin_x=140)
fire_bullet_sprite = sge.Sprite("fire_bullet", d, origin_x=8, origin_y=8,
                                fps=8, bbox_x=-12, bbox_width=24)
ice_bullet_sprite = sge.Sprite("ice_bullet", d, origin_x=8, origin_y=7,
                               bbox_x=-12, bbox_width=24)
explosion_sprite = sge.Sprite("explosion", d, origin_x=32, origin_y=19, fps=15,
                              bbox_x=-32, bbox_y=-4, bbox_width=64,
                              bbox_height=40)
smoke_puff_sprite = sge.Sprite("smoke_puff", d, width=48, height=48,
                               origin_x=24, origin_y=24, fps=24)
smoke_plume_sprite = sge.Sprite("smoke_plume", d, width=64, height=64,
                                origin_x=32, origin_y=32, fps=30)
fireball_smoke_sprite = sge.Sprite("smoke_plume", d, width=16, height=16,
                                   origin_x=8, origin_y=8, fps=30)
item_spawn_cloud_sprite = sge.Sprite("smoke_plume", d, width=80, height=80,
                                     origin_x=40, origin_y=40, fps=30)
item_spawn_cloud_sprite.delete_frame(0)
heart_empty_sprite = sge.Sprite("heart_empty", d, origin_y=-1)
heart_half_sprite = sge.Sprite("heart_half", d, origin_y=-1)
heart_full_sprite = sge.Sprite("heart_full", d, origin_y=-1)

coin_icon_sprite = coin_sprite.copy()
coin_icon_sprite.width = 16
coin_icon_sprite.height = 16
coin_icon_sprite.origin_y = -1

portrait_sprites = {"tux": tux_stand_sprite}

d = os.path.join(DATA, "images", "worldmap")
worldmap_tux_sprite = sge.Sprite("tux", d)
worldmap_level_complete_sprite = sge.Sprite("level_complete", d)
worldmap_level_incomplete_sprite = sge.Sprite("level_incomplete", d, fps=8)
worldmap_warp_sprite = sge.Sprite("warp", d, fps=3)

# Load backgrounds
d = os.path.join(DATA, "images", "backgrounds")

layers = [
    sge.BackgroundLayer(
        sge.Sprite("arctis1-middle", d), 0, 0, -100000, xscroll_rate=0.5,
        yscroll_rate=0.5, repeat_left=True, repeat_right=True),
    sge.BackgroundLayer(
        sge.Sprite("arctis1-bottom", d), 0, 352, -100000, xscroll_rate=0.5,
        yscroll_rate=0.5, repeat_left=True, repeat_right=True,
        repeat_down=True),
    sge.BackgroundLayer(
        sge.Sprite("arctis2-middle", d), 0, 0, -100010, xscroll_rate=0.25,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True),
    sge.BackgroundLayer(
        sge.Sprite("arctis2-bottom", d), 0, 352, -100010, xscroll_rate=0.25,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True,
        repeat_down=True),
    sge.BackgroundLayer(
        sge.Sprite("arctis3", d), 0, 0, -100020, xscroll_rate=0,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True)]
backgrounds["arctis"] = sge.Background(layers, sge.Color((109, 92, 230)))

cave_edge_spr = sge.Sprite("cave-edge", d)
layers = [
    sge.BackgroundLayer(
        sge.Sprite("cave-middle", d), 0, 128, -100000, xscroll_rate=0.7,
        yscroll_rate=0.7, repeat_left=True, repeat_right=True),
    sge.BackgroundLayer(
        cave_edge_spr, 0, 0, -100000, xscroll_rate=0.7, yscroll_rate=0.7,
        repeat_left=True, repeat_right=True, repeat_up=True),
    sge.BackgroundLayer(
        cave_edge_spr, 0, 256, -100000, xscroll_rate=0.7, yscroll_rate=0.7,
        repeat_left=True, repeat_right=True, repeat_down=True)]
del cave_edge_spr
backgrounds["cave"] = sge.Background(layers, sge.Color("black"))

nightsky_bottom_spr = sge.Sprite("nightsky-bottom", d)
layers = [
    sge.BackgroundLayer(
        sge.Sprite("nightsky1-middle", d), 0, 306, -100000, xscroll_rate=0.5,
        yscroll_rate=0.5, repeat_left=True, repeat_right=True),
    sge.BackgroundLayer(
        nightsky_bottom_spr, 0, 664, -100000, xscroll_rate=0.5,
        yscroll_rate=0.5, repeat_left=True, repeat_right=True,
        repeat_down=True),
    sge.BackgroundLayer(
        sge.Sprite("nightsky2-middle", d), 0, 0, -100010, xscroll_rate=0.25,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True),
    sge.BackgroundLayer(
        sge.Sprite("nightsky2-top", d), 0, -600, -100010, xscroll_rate=0.25,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True,
        repeat_up=True),
    sge.BackgroundLayer(
        nightsky_bottom_spr, 0, 600, -100010, xscroll_rate=0.25,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True,
        repeat_down=True)]
del nightsky_bottom_spr
backgrounds["nightsky"] = sge.Background(layers, sge.Color("black"))

layers = [
    sge.BackgroundLayer(
        sge.Sprite("bluemountain-middle", d), 0, -128, -100000,
        xscroll_rate=0.1, yscroll_rate=0.1, repeat_left=True,
        repeat_right=True),
    sge.BackgroundLayer(
        sge.Sprite("bluemountain-top", d), 0, -704, -100000, xscroll_rate=0.1,
        yscroll_rate=0.1, repeat_left=True, repeat_right=True, repeat_up=True),
    sge.BackgroundLayer(
        sge.Sprite("bluemountain-bottom", d), 0, 448, -100000,
        xscroll_rate=0.1, yscroll_rate=0.1, repeat_left=True,
        repeat_right=True, repeat_down=True)]
backgrounds["bluemountain"] = sge.Background(layers, sge.Color((86, 142, 206)))

castle_spr = sge.Sprite("castle", d)
castle_bottom_spr = sge.Sprite("castle-bottom", d)
for i in list(backgrounds.keys()):
    layers = backgrounds[i].layers + [
        sge.BackgroundLayer(castle_spr, 0, -64, -99000,
                            xscroll_rate=0.75, yscroll_rate=0.75,
                            repeat_left=True, repeat_right=True,
                            repeat_up=True),
        sge.BackgroundLayer(castle_bottom_spr, 0, 536, -99000,
                            xscroll_rate=0.75, yscroll_rate=0.75,
                            repeat_left=True, repeat_right=True,
                            repeat_down=True)]

    backgrounds["{}_castle".format(i)] = sge.Background(layers,
                                                        backgrounds[i].color)
del castle_spr
del castle_bottom_spr

# Load fonts
chars = (['\x00'] + [six.unichr(i) for i in six.moves.range(33, 128)] +
         [six.unichr(i) for i in six.moves.range(160, 384)])

font_sprite = sge.Sprite.from_tileset(
    os.path.join(DATA, "images", "misc", "font.png"), columns=16, rows=20,
    width=16, height=18)
font = sge.Font.from_sprite(font_sprite, chars, size=18)

font_big_sprite = sge.Sprite.from_tileset(
    os.path.join(DATA, "images", "misc", "font_big.png"), columns=16, rows=20,
    width=20, height=22)
font_big = sge.Font.from_sprite(font_big_sprite, chars, size=22)

pause_sprite = sge.Sprite.from_text(font_big, "Paused",
                                    color=sge.Color("white"))

# Load sounds
jump_sound = sge.Sound(os.path.join(DATA, "sounds", "jump.wav"))
bigjump_sound = sge.Sound(os.path.join(DATA, "sounds", "bigjump.wav"))
skid_sound = sge.Sound(os.path.join(DATA, "sounds", "skid.wav"), 50)
hurt_sound = sge.Sound(os.path.join(DATA, "sounds", "hurt.wav"))
kill_sound = sge.Sound(os.path.join(DATA, "sounds", "kill.wav"))
brick_sound = sge.Sound(os.path.join(DATA, "sounds", "brick.wav"))
coin_sound = sge.Sound(os.path.join(DATA, "sounds", "coin.wav"))
find_powerup_sound = sge.Sound(os.path.join(DATA, "sounds", "upgrade.wav"))
tuxdoll_sound = sge.Sound(os.path.join(DATA, "sounds", "tuxdoll.wav"))
ice_crack_sounds = [sge.Sound(os.path.join(DATA, "sounds", "ice_crack-0.wav")),
                    sge.Sound(os.path.join(DATA, "sounds", "ice_crack-1.wav")),
                    sge.Sound(os.path.join(DATA, "sounds", "ice_crack-2.wav")),
                    sge.Sound(os.path.join(DATA, "sounds", "ice_crack-3.wav"))]
ice_shatter_sound = sge.Sound(os.path.join(DATA, "sounds", "ice_shatter.wav"))
heal_sound = sge.Sound(os.path.join(DATA, "sounds", "heal.wav"))
shoot_sound = sge.Sound(os.path.join(DATA, "sounds", "shoot.wav"))
squish_sound = sge.Sound(os.path.join(DATA, "sounds", "squish.wav"))
stomp_sound = sge.Sound(os.path.join(DATA, "sounds", "stomp.wav"))
sizzle_sound = sge.Sound(os.path.join(DATA, "sounds", "sizzle.ogg"))
spring_sound = sge.Sound(os.path.join(DATA, "sounds", "spring.wav"))
kick_sound = sge.Sound(os.path.join(DATA, "sounds", "kick.wav"))
iceblock_bump_sound = sge.Sound(os.path.join(DATA, "sounds",
                                             "iceblock_bump.wav"))
icicle_shake_sound = sge.Sound(os.path.join(DATA, "sounds", "icicle_shake.wav"))
icicle_crash_sound = sge.Sound(os.path.join(DATA, "sounds", "icicle_crash.wav"))
explosion_sound = sge.Sound(os.path.join(DATA, "sounds", "explosion.wav"))
fall_sound = sge.Sound(os.path.join(DATA, "sounds", "fall.wav"))
pop_sound = sge.Sound(os.path.join(DATA, "sounds", "pop.wav"))
pipe_sound = sge.Sound(os.path.join(DATA, "sounds", "pipe.ogg"))
warp_sound = sge.Sound(os.path.join(DATA, "sounds", "warp.wav"))
pause_sound = sge.Sound(os.path.join(DATA, "sounds", "select.ogg"))
select_sound = sge.Sound(os.path.join(DATA, "sounds", "select.ogg"))
type_sound = sge.Sound(os.path.join(DATA, "sounds", "type.wav"))

# Load music
invincible_music = sge.Music(os.path.join(DATA, "music", "invincible.ogg"))
level_win_music = sge.Music(os.path.join(DATA, "music", "leveldone.ogg"))
no_music = sge.Music(None)
loaded_music["invincible.ogg"] = invincible_music
loaded_music["leveldone.ogg"] = level_win_music
loaded_music[None] = no_music

# Create objects
coin_animation = sge.Object(0, 0, sprite=coin_sprite, visible=False,
                            tangible=False)
bonus_animation = sge.Object(0, 0, sprite=bonus_empty_sprite, visible=False,
                             tangible=False)

# Create rooms
if RECORD:
    sge.game.start_room = LevelRecorder.load(RECORD)
else:
    sge.game.start_room = TitleScreen.load(os.path.join("special",
                                                        "title_screen.tmx"))

sge.game.mouse.visible = False
load_levelset(current_levelset)

if not os.path.exists(CONFIG):
    os.makedirs(CONFIG)

try:
    with open(os.path.join(CONFIG, "config.json")) as f:
        cfg = json.load(f)
except (IOError, ValueError):
    pass
else:
    fullscreen = cfg.get("fullscreen", fullscreen)
    sge.game.fullscreen = fullscreen
    sound_enabled = cfg.get("sound_enabled", sound_enabled)
    music_enabled = cfg.get("music_enabled", music_enabled)

    keys_cfg = cfg.get("keys", {})
    left_key = keys_cfg.get("left", left_key)
    right_key = keys_cfg.get("right", right_key)
    up_key = keys_cfg.get("up", up_key)
    down_key = keys_cfg.get("down", down_key)
    jump_key = keys_cfg.get("jump", jump_key)
    action_key = keys_cfg.get("action", action_key)
    sneak_key = keys_cfg.get("sneak", sneak_key)

    js_cfg = cfg.get("js", {})
    left_js = js_cfg.get("left", left_js)
    right_js = js_cfg.get("right", right_js)
    up_js = js_cfg.get("up", up_js)
    down_js = js_cfg.get("down", down_js)
    jump_js = js_cfg.get("jump", jump_js)
    action_js = js_cfg.get("action", action_js)
    sneak_js = js_cfg.get("sneak", sneak_js)

try:
    with open(os.path.join(CONFIG, "save_slots.json")) as f:
        loaded_slots = json.load(f)
except (IOError, ValueError):
    pass
else:
    for i in six.moves.range(min(len(loaded_slots), len(save_slots))):
        save_slots[i] = loaded_slots[i]


if __name__ == '__main__':
    try:
        sge.game.start()
    finally:
        keys_cfg = {"left": left_key, "right": right_key, "up": up_key,
                    "down": down_key, "jump": jump_key, "action": action_key,
                    "sneak": sneak_key}
        js_cfg = {"left": left_js, "right": right_js, "up": up_js,
                  "down": down_js, "jump": jump_js, "action": action_js,
                  "sneak": sneak_js}

        cfg = {"fullscreen": fullscreen, "sound_enabled": sound_enabled,
               "music_enabled": music_enabled, "keys": keys_cfg,
               "joystick": js_cfg}

        with open(os.path.join(CONFIG, "config.json"), 'w') as f:
            json.dump(cfg, f)

        with open(os.path.join(CONFIG, "save_slots.json"), 'w') as f:
            json.dump(save_slots, f)
