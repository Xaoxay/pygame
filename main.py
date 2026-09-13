from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.metrics import dp
import random

class BrickBreakerGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_over = False
        self.score = 0
        self.combo = 0
        
        self.paddle_rect = [Window.width/2 - dp(60), dp(50), dp(120), dp(15)]
        self.balls = [{'x': Window.width/2, 'y': dp(150), 'dx': random.choice([-dp(5), dp(5)]), 'dy': dp(5), 'color': (1, 0.4, 1)}]
        self.bricks = []
        self.powerups = []
        
        self.brick_colors = [
            (0, 0.6, 1),
            (0, 1, 0.4),
            (1, 0.8, 0),
            (1, 0, 0.4),
            (0, 1, 1)
        ]
        
        self.create_bricks()
        
        # UI
        self.score_label = Label(text="SCORE: 0", pos=(Window.width - dp(100), Window.height - dp(50)), font_size=dp(20), bold=True)
        self.combo_label = Label(text="COMBO: 0", pos=(Window.width - dp(100), Window.height - dp(80)), font_size=dp(20), color=(1,0.8,0,1), bold=True)
        self.title_label = Label(text="NEON BRICK BREAKER", pos=(dp(120), Window.height - dp(50)), font_size=dp(20), color=(0,0.6,1,1), bold=True)
        
        self.add_widget(self.score_label)
        self.add_widget(self.combo_label)
        self.add_widget(self.title_label)
        
        self.game_over_label = Label(text="GAME OVER\nToca la pantalla para reiniciar", pos=(Window.width/2 - dp(50), Window.height/2), font_size=dp(24), halign="center", color=(1,0.2,0.2,1), bold=True)
        
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def create_bricks(self):
        self.bricks = []
        rows = 5
        cols = 6
        b_width = (Window.width - dp(20)) / cols - dp(10)
        b_height = dp(30)
        
        offset_y = Window.height - dp(120)
        for r in range(rows):
            for c in range(cols):
                x = dp(15) + c * (b_width + dp(10))
                y = offset_y - r * (b_height + dp(10))
                self.bricks.append({'rect': [x, y, b_width, b_height], 'color': self.brick_colors[r % len(self.brick_colors)]})

    def on_touch_move(self, touch):
        if not self.game_over:
            self.paddle_rect[0] = touch.x - self.paddle_rect[2]/2
            
    def on_touch_down(self, touch):
        if self.game_over:
            self.reset_game()
        else:
            self.paddle_rect[0] = touch.x - self.paddle_rect[2]/2

    def reset_game(self):
        self.game_over = False
        self.score = 0
        self.combo = 0
        self.balls = [{'x': Window.width/2, 'y': dp(150), 'dx': random.choice([-dp(5), dp(5)]), 'dy': dp(5), 'color': (1, 0.4, 1)}]
        self.powerups = []
        self.create_bricks()
        self.remove_widget(self.game_over_label)

    def spawn_ball(self, x, y):
        self.balls.append({'x': x, 'y': y, 'dx': random.choice([-dp(5), dp(5)]), 'dy': dp(5), 'color': (1, 0.4, 1)})

    def rect_collide(self, r1, r2):
        return (r1[0] < r2[0] + r2[2] and r1[0] + r1[2] > r2[0] and
                r1[1] < r2[1] + r2[3] and r1[1] + r1[3] > r2[1])

    def update(self, dt):
        if self.game_over:
            return

        for ball in self.balls[:]:
            ball['x'] += ball['dx']
            ball['y'] += ball['dy']
            
            # Rebote Paredes
            if ball['x'] <= 0 or ball['x'] >= Window.width:
                ball['dx'] *= -1
            if ball['y'] >= Window.height:
                ball['dy'] *= -1
                
            # Caída al vacío
            if ball['y'] <= 0:
                self.balls.remove(ball)
                if len(self.balls) == 0:
                    self.game_over = True
                    self.add_widget(self.game_over_label)
                self.combo = 0
                continue
                
            # Colisión Paleta
            ball_rect = [ball['x']-dp(6), ball['y']-dp(6), dp(12), dp(12)]
            if self.rect_collide(ball_rect, self.paddle_rect) and ball['dy'] < 0:
                ball['dy'] *= -1
                offset = (ball['x'] - (self.paddle_rect[0] + self.paddle_rect[2]/2)) / (self.paddle_rect[2]/2)
                ball['dx'] = offset * dp(6)
                
            # Colisión Ladrillos
            for b in self.bricks[:]:
                if self.rect_collide(ball_rect, b['rect']):
                    self.bricks.remove(b)
                    ball['dy'] *= -1
                    self.score += 100
                    self.combo += 1
                    # Probabilidad de powerup 15%
                    if random.random() < 0.15:
                        self.powerups.append({'rect': [b['rect'][0] + b['rect'][2]/2, b['rect'][1], dp(20), dp(20)]})
                    break

        # Powerups
        for p in self.powerups[:]:
            p['rect'][1] -= dp(4)
            if self.rect_collide(p['rect'], self.paddle_rect):
                self.spawn_ball(self.paddle_rect[0] + self.paddle_rect[2]/2, self.paddle_rect[1] + dp(30))
                self.powerups.remove(p)
            elif p['rect'][1] < 0:
                self.powerups.remove(p)

        if len(self.bricks) == 0:
            self.create_bricks()
            self.spawn_ball(Window.width/2, dp(150))
            
        self.score_label.text = f"SCORE: {self.score}"
        self.combo_label.text = f"COMBO: {self.combo}"

        self.draw()

    def draw(self):
        self.canvas.before.clear()
        with self.canvas.before:
            # Fondo
            Color(0.04, 0.06, 0.1)
            Rectangle(pos=(0,0), size=(Window.width, Window.height))
            
            # Grid
            Color(0.12, 0.12, 0.2, 0.6)
            for x in range(0, int(Window.width), int(dp(50))):
                Line(points=[x, 0, x, Window.height])
            for y in range(0, int(Window.height), int(dp(50))):
                Line(points=[0, y, Window.width, y])

            # Paleta
            Color(0.4, 0.8, 1, 1)
            Rectangle(pos=(self.paddle_rect[0], self.paddle_rect[1]), size=(self.paddle_rect[2], self.paddle_rect[3]))
            # Brillo Paleta
            Color(0.4, 0.8, 1, 0.4)
            Rectangle(pos=(self.paddle_rect[0]-dp(5), self.paddle_rect[1]-dp(5)), size=(self.paddle_rect[2]+dp(10), self.paddle_rect[3]+dp(10)))
            
            # Ladrillos
            for b in self.bricks:
                # Interior
                Color(b['color'][0]*0.5, b['color'][1]*0.5, b['color'][2]*0.5, 1)
                Rectangle(pos=(b['rect'][0], b['rect'][1]), size=(b['rect'][2], b['rect'][3]))
                # Borde
                Color(*b['color'], 1)
                Line(rectangle=(b['rect'][0], b['rect'][1], b['rect'][2], b['rect'][3]), width=1.5)
                
            # Powerups
            Color(1, 1, 0)
            for p in self.powerups:
                Ellipse(pos=(p['rect'][0], p['rect'][1]), size=(p['rect'][2], p['rect'][3]))
                
            # Bolas
            for ball in self.balls:
                Color(1, 1, 1) # Centro blanco
                Ellipse(pos=(ball['x']-dp(4), ball['y']-dp(4)), size=(dp(8), dp(8)))
                Color(*ball['color'], 0.5) # Brillo neon
                Ellipse(pos=(ball['x']-dp(9), ball['y']-dp(9)), size=(dp(18), dp(18)))


class NeonApp(App):
    def build(self):
        return BrickBreakerGame()

if __name__ == "__main__":
    NeonApp().run()
