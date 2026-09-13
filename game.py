"""Game rules in a 400 x 800 logical playfield, independent of Kivy."""
import math
import random

LEVELS = [
    ("PRIMERA LUZ", ["1111111", "1111111", "0111110"]),
    ("ESCALERA", ["1000001", "1100011", "1110111", "1111111"]),
    ("DIAMANTE", ["0001000", "0012100", "0122210", "0012100", "0001000"]),
    ("PORTALES", ["1110111", "1210121", "1110111", "0100010", "1111111"]),
    ("PULSO", ["1020201", "0122210", "0012100", "0122210", "1020201"]),
    ("FORTALEZA", ["2121212", "2111112", "2010102", "2111112", "2222222"]),
    ("ORBITAS", ["0222220", "2100012", "2013102", "2100012", "0222220"]),
    ("INTERFERENCIA", ["3210123", "0123210", "2321232", "0123210", "3210123"]),
    ("SUPERNOVA", ["1030301", "0232320", "3323233", "0232320", "1030301"]),
    ("NUCLEO FINAL", ["3333333", "3211123", "3123213", "3211123", "2333332", "0123210"]),
]


class Game:
    floor = 72
    ceiling = 644

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.new_game()
        self.state = 'menu'

    def new_game(self):
        self.level, self.score, self.lives, self.combo = 0, 0, 3, 0
        self.events = []
        self.shake = 0
        self.load_level()

    @property
    def speed(self):
        # Más difícil: aumenta velocidad base y el escalado por nivel
        return 320 + self.level * 35

    @property
    def paddle_width(self):
        # Paleta más chica para subir la dificultad
        return 128 if self.wide_time > 0 else max(60, 100 - self.level * 4)

    @property
    def paddle(self):
        return (self.paddle_x - self.paddle_width / 2, 112, self.paddle_width, 13)

    def load_level(self):
        self.bricks, self.particles, self.drops = [], [], []
        self.wide_time = self.combo = 0
        for row, line in enumerate(LEVELS[self.level][1]):
            for col, strength in enumerate(line):
                if strength != '0':
                    self.bricks.append(dict(x=23 + col * 51, y=584 - row * 31,
                                            w=46, h=23, hp=int(strength), row=row))
        self.total_bricks = len(self.bricks)
        self.paddle_x, self.balls, self.state = 200, [], 'ready'

    def move_paddle(self, x):
        half = self.paddle_width / 2
        self.paddle_x = min(386 - half, max(14 + half, x))

    def launch(self):
        if self.state == 'ready':
            self.balls = [dict(x=self.paddle_x, y=135, vx=self.speed * .4,
                               vy=self.speed * math.sqrt(.84), trail=[])]
            self.state = 'playing'

    def advance(self):
        if self.state == 'clear' and self.level < len(LEVELS) - 1:
            self.level += 1
            self.lives = min(3, self.lives + 1)
            self.load_level()

    def pause(self):
        if self.state in ('playing', 'ready'):
            self.resume_state, self.state = self.state, 'paused'

    def resume(self):
        if self.state == 'paused':
            self.state = self.resume_state

    @staticmethod
    def overlaps(ball, rect):
        x, y, w, h = rect
        return (ball['x'] + 6 > x and ball['x'] - 6 < x + w
                and ball['y'] + 6 > y and ball['y'] - 6 < y + h)

    def burst(self, x, y, row):
        # Más partículas para más espectacularidad
        for _ in range(15):
            angle, speed = self.rng.random() * math.tau, self.rng.uniform(50, 160)
            self.particles.append(dict(x=x, y=y, vx=math.cos(angle) * speed,
                                       vy=math.sin(angle) * speed, life=self.rng.uniform(0.3, 0.7), row=row))

    def tick(self, dt):
        if self.state != 'playing':
            self.shake = max(0, self.shake - dt * 60)
            return
        
        self.shake = max(0, self.shake - dt * 50)
        
        # Substeps prevent fast balls tunnelling through bricks on slower phones.
        dt = min(max(dt, 0), .1)
        steps = max(1, math.ceil(dt / (1 / 240)))
        for _ in range(steps):
            if self.state != 'playing':
                break
            self.step(dt / steps)

    def step(self, dt):
        self.wide_time = max(0, self.wide_time - dt)
        self.move_paddle(self.paddle_x)
        for p in self.particles[:]:
            p['life'] -= dt
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            if p['life'] <= 0:
                self.particles.remove(p)
                
        for ball in self.balls[:]:
            # Guardar rastro para el neón
            ball['trail'].append((ball['x'], ball['y']))
            if len(ball['trail']) > 8:
                ball['trail'].pop(0)
                
            old_x, old_y = ball['x'], ball['y']
            ball['x'] += ball['vx'] * dt
            ball['y'] += ball['vy'] * dt
            
            if ball['x'] < 20 or ball['x'] > 380:
                ball['x'] = min(380, max(20, ball['x']))
                ball['vx'] = abs(ball['vx']) * (1 if ball['x'] == 20 else -1)
                self.events.append('bounce')
                self.shake = min(self.shake + 2, 10)
                
            if ball['y'] > self.ceiling - 6:
                ball['y'], ball['vy'] = self.ceiling - 6, -abs(ball['vy'])
                self.events.append('bounce')
                self.shake = min(self.shake + 2, 10)
                
            if ball['y'] < self.floor:
                self.balls.remove(ball)
                continue
                
            if ball['vy'] < 0 and self.overlaps(ball, self.paddle):
                offset = (ball['x'] - self.paddle_x) / (self.paddle_width / 2)
                angle = min(.95, max(-.95, offset)) * math.radians(60)
                ball['vx'], ball['vy'] = self.speed * math.sin(angle), self.speed * math.cos(angle)
                ball['y'], self.combo = 131, 0
                self.events.append('bounce')
                self.shake = min(self.shake + 4, 15)
                
            for brick in self.bricks[:]:
                if not self.overlaps(ball, (brick['x'], brick['y'], brick['w'], brick['h'])):
                    continue
                if old_y - 6 >= brick['y'] + brick['h'] or old_y + 6 <= brick['y']:
                    ball['vy'] *= -1
                    ball['y'] = brick['y'] + brick['h'] + 6 if old_y > brick['y'] else brick['y'] - 6
                else:
                    ball['vx'] *= -1
                    ball['x'] = brick['x'] - 6 if old_x < brick['x'] else brick['x'] + brick['w'] + 6
                brick['hp'] -= 1
                self.score += 25
                self.burst(ball['x'], ball['y'], brick['row'])
                
                if brick['hp'] == 0:
                    self.bricks.remove(brick)
                    self.combo += 1
                    self.score += 75 * min(self.combo, 5)
                    self.events.append('break')
                    self.shake = min(self.shake + 8, 20)
                    if self.rng.random() < .18:
                        self.drops.append(dict(x=brick['x'] + 23, y=brick['y'],
                                               kind=self.rng.choice(('wide', 'multi'))))
                else:
                    self.events.append('hit')
                    self.shake = min(self.shake + 4, 15)
                break
                
        # Completing the level wins over losing a ball on the same step.
        if not self.bricks:
            self.score += (self.level + 1) * 500
            self.state = 'won' if self.level == len(LEVELS) - 1 else 'clear'
            self.drops.clear()
            self.events.append('win')
            return
            
        if not self.balls:
            self.lives -= 1
            self.combo, self.wide_time = 0, 0
            self.drops.clear()
            self.state = 'ready' if self.lives else 'over'
            self.events.append('die')
            self.shake = 15
            return
            
        for drop in self.drops[:]:
            drop['y'] -= 110 * dt
            if self.overlaps(drop, self.paddle):
                self.events.append('powerup')
                self.shake = min(self.shake + 5, 15)
                if drop['kind'] == 'wide':
                    self.wide_time = 12
                else:
                    for direction in (-1, 1):
                        if len(self.balls) < 5:
                            self.balls.append(dict(x=self.paddle_x, y=135,
                                                   vx=self.speed * .55 * direction,
                                                   vy=self.speed * math.sqrt(1 - .55 ** 2), trail=[]))
                self.drops.remove(drop)
            elif drop['y'] < self.floor:
                self.drops.remove(drop)
