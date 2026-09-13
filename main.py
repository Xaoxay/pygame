"""Neon Brick Breaker: portrait touch interface."""
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.storage.jsonstore import JsonStore
from os.path import join

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


class BrickBreakerGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        self.bind(size=self.redraw, pos=self.redraw)
        Window.bind(on_keyboard=self.keyboard)
        self.event = Clock.schedule_interval(self.update, 1 / 60)

    @property
    def accent(self):
        return PALETTES[(self.game.level // 3) % 3][0]

    def transform(self):
        self.scale = max(.01, min(self.width / 400, self.height / 800))
        self.ox = self.x + (self.width - 400 * self.scale) / 2
        self.oy = self.y + (self.height - 800 * self.scale) / 2

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
        self.game.tick(dt)
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
                'result', 'primary', 'legend']
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
                self.box(b['x'], b['y'] - 3, b['w'], b['h'] + 6, color, 6, .10)
                self.box(b['x'], b['y'], b['w'], b['h'], color, 5, .75 if b['hp'] == 1 else .95)
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
            self.box(px - 5, py - 4, pw + 10, ph + 8, self.accent, 10, .12)
            self.box(px, py, pw, ph, self.accent, 6)
            self.box(px + 12, py + ph - 4, pw - 24, 2, WHITE, 1, .7)
            for ball in g.balls:
                for i, (x, y) in enumerate(ball['trail']):
                    self.dot(x, y, 2 + i * .3, self.accent, .04 + i * .035)
                self.dot(ball['x'], ball['y'], 11, self.accent, .16)
                self.dot(ball['x'], ball['y'], 6, WHITE)
            if g.state == 'ready':
                self.dot(g.paddle_x, 135, 6, WHITE)
                self.text('ready', 'TOCA PARA LANZAR', 35, 265, 330, 36, 19, WHITE, True, 'center')
                self.text('help', 'Deslizá el dedo para mover la paleta', 35, 234, 330, 30, 13, MUTED, align='center')
            footer = f'PALETA ANCHA  {g.wide_time:.0f}s' if g.wide_time else 'DESLIZÁ PARA MOVER'
            self.text('footer', footer, 24, 25, 255, 30, 11, MUTED)
            self.text('counter', f'{g.level + 1:02d} / 10', 298, 25, 78, 30, 13, self.accent, True, 'right')
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
                          48, 303, 304, 30, 16, self.accent, True)
                actions = {'menu': ('JUGAR', g.new_game), 'paused': ('CONTINUAR', g.resume),
                           'clear': ('SIGUIENTE NIVEL', g.advance),
                           'over': ('VOLVER A JUGAR', g.new_game), 'won': ('JUGAR DE NUEVO', g.new_game)}
                title, action = actions[g.state]
                self.button('primary', title, 231, action)
                self.text('legend', 'BONUS:  + multibola    <> paleta ancha', 24, 125, 352, 30, 12, MUTED, align='center')
        for key, label in self.labels.items():
            if key not in self.used_labels:
                label.opacity = 0

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
