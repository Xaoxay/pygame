"""Neon Brick Breaker: portrait touch interface."""
from kivy.app import App
from kivy.core.audio import SoundLoader
import math
import random
import wave
import struct
import os
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.storage.jsonstore import JsonStore
from os.path import join
import webbrowser
import math

from game import Game, LEVELS

BG = (.025, .035, .075)
PANEL = (.055, .075, .13)
WHITE = (.93, .96, 1)
MUTED = (.57, .66, .79)
PALETTES = [
    [(.20, .90, .93), (.28, .62, 1), (.58, .43, 1)],
    [(1, .48, .62), (1, .69, .37), (.79, .48, 1)],
    [(.42, .94, .65), (.20, .83, .88), (.46, .64, 1)],
]




def get_sfx_path(name):
    from kivy.app import App
    try:
        data_dir = App.get_running_app().user_data_dir
    except Exception:
        data_dir = '.'
    return os.path.join(data_dir, name)

def create_sfx():
    if os.path.exists(get_sfx_path('bounce.wav')): return
    def save(name, freq_start, freq_end, duration, vol=0.5, wave_type='sq'):
        with wave.open(get_sfx_path(name), 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            frames = []
            for i in range(int(44100 * duration)):
                t = i / 44100.0
                f_cur = freq_start + (freq_end - freq_start) * (t / duration)
                phase = int(t * f_cur * 2)
                if wave_type == 'sq':
                    val = 1.0 if phase % 2 == 0 else -1.0
                elif wave_type == 'noise':
                    val = random.uniform(-1, 1)
                else: # sine
                    val = math.sin(t * f_cur * math.pi * 2)
                env = 1.0 - (t / duration)
                sample = int(val * vol * env * 32767.0)
                frames.append(struct.pack('<h', sample))
            f.writeframes(b''.join(frames))
            
    save('bounce.wav', 600, 800, 0.1, 0.4, 'sine')
    save('hit.wav', 800, 1000, 0.1, 0.5, 'sq')
    save('break.wav', 1200, 600, 0.2, 0.6, 'noise')
    save('powerup.wav', 400, 1200, 0.3, 0.5, 'sine')
    save('die.wav', 300, 100, 0.5, 0.6, 'noise')
    save('win.wav', 800, 1600, 0.6, 0.5, 'sq')

class BrickBreakerGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        create_sfx()
        self.sounds = {
            'bounce': SoundLoader.load(get_sfx_path('bounce.wav')),
            'hit': SoundLoader.load(get_sfx_path('hit.wav')),
            'break': SoundLoader.load(get_sfx_path('break.wav')),
            'powerup': SoundLoader.load(get_sfx_path('powerup.wav')),
            'die': SoundLoader.load(get_sfx_path('die.wav')),
            'win': SoundLoader.load(get_sfx_path('win.wav'))
        }

        self.game = Game()
        self.labels, self.buttons = {}, []
        self.record, self.store = 0, None
        try:
            self.store = JsonStore(join(App.get_running_app().user_data_dir, 'record.json'))
            if self.store.exists('best'):
                self.record = self.store.get('best')['score']
        except (OSError, ValueError, KeyError):
            pass
        self.active_touch = None
        self.light_time = 0
        self.bind(size=self.redraw, pos=self.redraw)
        Window.bind(on_keyboard=self.keyboard)
        self.event = Clock.schedule_interval(self.update, 1 / 60)

    @property
    def accent(self):
        return PALETTES[(self.game.level // 3) % 3][0]


    def transform(self):
        self.scale = max(.01, min(self.width / 400, self.height / 800))
        # Shake effect
        sx = 0
        sy = 0
        if hasattr(self.game, 'shake') and self.game.shake > 0:
            sx = (random.random() - 0.5) * self.game.shake * self.scale
            sy = (random.random() - 0.5) * self.game.shake * self.scale
        
        self.ox = self.x + (self.width - 400 * self.scale) / 2 + sx
        self.oy = self.y + (self.height - 800 * self.scale) / 2 + sy


    def box(self, x, y, w, h, color, radius=0, alpha=1):
        Color(*color, alpha)
        args = dict(pos=(self.ox + x * self.scale, self.oy + y * self.scale),
                    size=(w * self.scale, h * self.scale))
        if radius:
            RoundedRectangle(**args, radius=[radius * self.scale])
        else:
            Rectangle(**args)

    def dot(self, x, y, radius, color, alpha=1):
        Color(*color, alpha)
        Ellipse(pos=(self.ox + (x - radius) * self.scale,
                     self.oy + (y - radius) * self.scale),
                size=(radius * 2 * self.scale, radius * 2 * self.scale))

    def text(self, key, value, x, y, w, h, size=14, color=WHITE, bold=False, align='left'):
        self.used_labels.add(key)
        label = self.labels[key]
        label.text = value
        label.pos = (self.ox + x * self.scale, self.oy + y * self.scale)
        label.size = (w * self.scale, h * self.scale)
        label.text_size = label.size
        label.font_size = size * self.scale
        label.color, label.bold, label.halign = (*color, 1), bold, align
        label.opacity = 1

    def button(self, key, title, y, action):
        self.box(48, y, 304, 52, self.accent, 16)
        self.text(key, title, 48, y, 304, 52, 16, BG, True, 'center')
        self.buttons.append(((48, y, 304, 52), action))

    def update(self, dt):
        if self.game.state != 'paused':
            self.light_time += min(dt, .1)
        self.game.tick(dt)
        # Process events for sounds
        if hasattr(self.game, 'events'):
            for ev in self.game.events:
                if ev in self.sounds and self.sounds[ev]:
                    self.sounds[ev].volume = 0.5
                    self.sounds[ev].play()
            self.game.events.clear()

        if self.game.state == 'playing':
            for ball in self.game.balls:
                ball['trail'].append((ball['x'], ball['y']))
                ball['trail'] = ball['trail'][-8:]
        if self.game.state in ('clear', 'won', 'over') and self.game.score > self.record:
            self.record = self.game.score
            if self.store:
                try:
                    self.store.put('best', score=self.record)
                except OSError:
                    pass
        self.redraw()

    def redraw(self, *args):
        self.transform()
        self.used_labels, self.buttons = set(), []
        g = self.game
        # Create widget canvases outside canvas.before: clearing the playfield
        # must never remove label canvases during the next animation frame.
        keys = ['brand', 'level', 'pause', 'score', 'lives', 'ready', 'help',
                'footer', 'counter', 'combo', 'eyebrow', 'title', 'subtitle',
                'result', 'primary', 'legend', 'speed1', 'speed2', 'speed3']
        keys.extend('drop' + str(i) for i in range(len(g.drops)))
        for key in keys:
            if key not in self.labels:
                label = Label(valign='middle', font_name='Roboto')
                self.labels[key] = label
                self.add_widget(label)
        self.canvas.before.clear()
        colors = PALETTES[(g.level // 3) % 3]
        with self.canvas.before:
            Color(*BG, 1)
            Rectangle(pos=self.pos, size=self.size)
            self.box(14, 72, 372, 574, PANEL, 20, .4)
            # Animated Scrolling Grid
            grid_offset = (self.light_time * 40) % 32
            Color(0.12, 0.12, 0.25, 0.3)
            for x in range(24, 400, 32):
                Line(points=[self.ox + x * self.scale, self.oy + 82 * self.scale, self.ox + x * self.scale, self.oy + 650 * self.scale], width=1)
            for y in range(82, 650 + 32, 32):
                yy = y - grid_offset
                if 82 <= yy <= 650:
                    Line(points=[self.ox + 24 * self.scale, self.oy + yy * self.scale, self.ox + 376 * self.scale, self.oy + yy * self.scale], width=1)
            
            for x in range(24, 400, 32):
                for y in range(82, 650, 32):
                    self.dot(x, y, .7, MUTED, .18)
            self.box(14, 72, 372, 2, self.accent, alpha=.3)
            self.text('brand', 'NEON / BRICK BREAKER', 24, 755, 315, 23, 13, self.accent, True)
            self.text('level', f'{g.level + 1:02d} / {LEVELS[g.level][0]}', 24, 712, 292, 38, 21, WHITE, True)
            self.box(328, 711, 48, 44, PANEL, 12)
            self.text('pause', 'II', 328, 711, 48, 44, 19, WHITE, True, 'center')
            if g.state in ('playing', 'ready'):
                self.buttons.append(((328, 711, 48, 44), g.pause))
            self.text('score', f'PUNTOS  {g.score:06d}', 24, 669, 210, 27, 15, WHITE, True)
            self.text('lives', f'VIDAS  {g.lives} / 3', 248, 669, 128, 27, 14, MUTED, align='right')
            progress = 1 - len(g.bricks) / g.total_bricks
            self.box(24, 659, 352, 3, PANEL, 1)
            if progress:
                self.box(24, 659, 352 * progress, 3, self.accent, 1)

            for b in g.bricks:
                color = colors[b['row'] % len(colors)]
                pulse = .85 + .15 * math.sin(self.light_time * 2 + b['row'] * .8)
                for spread, alpha in ((9, .05), (6, .09), (3, .18)):
                    self.box(b['x'] - spread, b['y'] - spread, b['w'] + spread * 2,
                             b['h'] + spread * 2, color, 8, alpha * pulse)
                self.box(b['x'], b['y'], b['w'], b['h'], color, 5, .75 if b['hp'] == 1 else .95)
                self.box(b['x'] + 3, b['y'] + b['h'] - 3, b['w'] - 6, 2, WHITE, 1, .8)
                self.box(b['x'] + 5, b['y'] + b['h'] - 4, b['w'] - 10, 1, WHITE, alpha=.45)
                for hit in range(b['hp']):
                    self.dot(b['x'] + b['w'] / 2 + (hit - (b['hp'] - 1) / 2) * 6,
                             b['y'] + 9, 1.5, BG, .7)
            for p in g.particles:
                self.dot(p['x'], p['y'], 2, colors[p['row'] % 3], p['life'] / .4)
            for i, drop in enumerate(g.drops):
                self.box(drop['x'] - 14, drop['y'] - 14, 28, 28, self.accent, 8)
                self.text('drop' + str(i), '+' if drop['kind'] == 'multi' else '<>',
                          drop['x'] - 14, drop['y'] - 14, 28, 28, 17, BG, True, 'center')
            px, py, pw, ph = g.paddle
            paddle_pulse = .85 + .15 * math.sin(self.light_time * 4)
            self.box(px - 8, py - 6, pw + 16, ph + 12, self.accent, 12, .1 * paddle_pulse)
            self.box(px - 5, py - 4, pw + 10, ph + 8, self.accent, 10, .2 * paddle_pulse)
            
            self.box(px, py, pw, ph, self.accent, 6)
            self.box(px + 12, py + ph - 4, pw - 24, 2, WHITE, 1, .7)
            for ball in g.balls:
                for i, (x, y) in enumerate(ball['trail']):
                    trail_color = colors[i % len(colors)]
                    self.dot(x, y, 2 + i * .3, trail_color, .1 + i * .05)
                flash = min(1, ball.get('flash', 0) / .22)
                self.dot(ball['x'], ball['y'], 24 + 12 * flash, self.accent, .05 + .12 * flash)
                self.dot(ball['x'], ball['y'], 15 + 6 * flash, self.accent, .18 + .28 * flash)
                self.dot(ball['x'], ball['y'], 9 + 3 * flash, WHITE, .18 + .40 * flash)
                self.dot(ball['x'], ball['y'], 6, WHITE)
            if g.state == 'ready':
                self.dot(g.paddle_x, 135, 6, WHITE)
                self.text('ready', 'TOCA PARA LANZAR', 35, 265, 330, 36, 19, WHITE, True, 'center')
                self.text('help', 'Deslizá el dedo para mover la paleta', 35, 234, 330, 30, 13, MUTED, align='center')
            footer = f'PALETA ANCHA  {g.wide_time:.0f}s' if g.wide_time else 'VELOCIDAD'
            self.text('footer', footer, 24, 20, 170, 40, 11, MUTED)
            self.speed_selector(200, 18, 56, 4)
            if g.combo > 1 and g.state == 'playing':
                self.text('combo', f'COMBO x{min(g.combo, 5)}', 70, 336, 260, 34, 18, self.accent, True, 'center')
            if g.state in ('menu', 'paused', 'clear', 'over', 'won'):
                for label in self.labels.values():
                    label.opacity = 0
                self.used_labels.clear()
                self.buttons.clear()
                self.box(0, 0, 400, 800, BG, alpha=.94)
                self.box(24, 174, 352, 454, PANEL, 26)
                self.box(48, 600, 46, 4, self.accent, 2)
                self.text('eyebrow', 'NEON / ARCADE', 48, 546, 304, 34, 13, self.accent, True)
                titles = {'menu': 'BRICK\nBREAKER', 'paused': 'EN PAUSA', 'clear': 'NIVEL\nSUPERADO',
                          'over': 'OTRA\nOPORTUNIDAD', 'won': 'GALAXIA\nCOMPLETADA'}
                self.text('title', titles[g.state], 48, 426, 304, 115, 34, WHITE, True)
                subtitles = {'menu': '10 niveles. Tres vidas. Un nuevo récord.\nRompé ladrillos y atrapá bonificaciones.',
                             'paused': 'Tomate un respiro.\nTu partida te espera.',
                             'clear': f'{LEVELS[g.level][0]} completado\n+1 vida, hasta un máximo de 3',
                             'over': f'Llegaste al nivel {g.level + 1} de 10.\nCada intento te lleva más lejos.',
                             'won': 'Superaste los 10 niveles.\nVolvé a jugar para mejorar tu marca.'}
                self.text('subtitle', subtitles[g.state], 48, 349, 304, 68, 14, MUTED)
                self.text('result', f'RÉCORD  {self.record:06d}' if g.state == 'menu' else f'PUNTOS  {g.score:06d}',
                          48, 319, 304, 30, 16, self.accent, True)
                self.speed_selector(48, 274, 96, 8)
                actions = {'menu': ('JUGAR', g.new_game), 'paused': ('CONTINUAR', g.resume),
                           'clear': ('SIGUIENTE NIVEL', g.advance),
                           'over': ('VOLVER A JUGAR', g.new_game), 'won': ('JUGAR DE NUEVO', g.new_game)}
                title, action = actions[g.state]
                self.button('primary', title, 207, action)
                
                if g.state == 'menu':
                    self.button('update_btn', 'BUSCAR ACTUALIZACION', 145, lambda: webbrowser.open("https://github.com/Xaoxay/pygame/releases/latest"))
                    
                self.text('legend', 'BONUS:  + multibola    <> paleta ancha', 24, 105 if g.state == 'menu' else 125, 352, 30, 12, MUTED, align='center')
        for key, label in self.labels.items():
            if key not in self.used_labels:
                label.opacity = 0

    def speed_selector(self, x, y, width, gap):
        for rate in (1, 2, 3):
            bx = x + (rate - 1) * (width + gap)
            selected = self.game.rate == rate
            self.box(bx, y, width, 44, self.accent if selected else (.10, .14, .22), 12)
            self.text('speed' + str(rate), f'x{rate}', bx, y, width, 44, 16,
                      BG if selected else WHITE, True, 'center')
            self.buttons.append(((bx, y, width, 44), lambda value=rate: self.game.set_rate(value)))

    def on_touch_down(self, touch):
        self.transform()
        x, y = (touch.x - self.ox) / self.scale, (touch.y - self.oy) / self.scale
        if not (0 <= x <= 400 and 0 <= y <= 800):
            return False
        for (bx, by, bw, bh), action in self.buttons:
            if bx <= x <= bx + bw and by <= y <= by + bh:
                action()
                self.redraw()
                return True
        if self.game.state in ('ready', 'playing') and y < 650 and self.active_touch is None:
            self.active_touch = touch.uid
            touch.grab(self)
            self.game.move_paddle(x)
            self.game.launch()
            return True
        return True

    def on_touch_move(self, touch):
        if touch.uid == self.active_touch and self.game.state in ('ready', 'playing'):
            self.game.move_paddle((touch.x - self.ox) / self.scale)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.uid == self.active_touch:
            touch.ungrab(self)
            self.active_touch = None
            return True
        return super().on_touch_up(touch)

    def keyboard(self, window, key, *args):
        if key == 27:
            self.game.resume() if self.game.state == 'paused' else self.game.pause()
            return True
        return False


class NeonApp(App):
    def build(self):
        Window.clearcolor = (*BG, 1)
        return BrickBreakerGame()

    def on_pause(self):
        self.root.game.pause()
        self.root.active_touch = None
        return True


if __name__ == '__main__':
    NeonApp().run()
