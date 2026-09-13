import pygame
import random
import math

# Inicializar Pygame
pygame.init()

# Configuración de la pantalla
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Brick Breaker")
clock = pygame.time.Clock()
FPS = 60

# Colores (Estilo Neón)
BG_COLOR = (10, 15, 25)
WHITE = (255, 255, 255)
BRICK_COLORS = [
    (0, 150, 255),   # Azul
    (0, 255, 100),   # Verde
    (255, 200, 0),   # Amarillo
    (255, 0, 100),   # Rosa/Rojo
    (0, 255, 255)    # Cian
]

font = pygame.font.SysFont("impact", 24)
title_font = pygame.font.SysFont("impact", 36)

class Paddle(pygame.Rect):
    def __init__(self):
        super().__init__(WIDTH // 2 - 60, HEIGHT - 50, 120, 15)
        self.speed = 8
        self.color = (100, 200, 255)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self, border_radius=8)
        # Efecto de brillo (Glow)
        glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*self.color, 100), glow_surf.get_rect(), border_radius=12, width=3)
        surface.blit(glow_surf, (self.x - 10, self.y - 10))

class Ball:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 12, 12)
        # Velocidad inicial
        self.dx = random.choice([-5, 5])
        self.dy = -5
        self.color = (255, 100, 255)
        self.trail = []

    def draw(self, surface):
        # Dibujar estela (Trail)
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            radius = int(6 * (i / len(self.trail)))
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (radius, radius), radius)
            surface.blit(surf, (pos[0] - radius, pos[1] - radius))

        # Dibujar bola principal
        pygame.draw.circle(surface, WHITE, self.rect.center, 6)
        # Brillo exterior
        pygame.draw.circle(surface, self.color, self.rect.center, 9, 2)

    def update(self):
        self.trail.append(self.rect.center)
        if len(self.trail) > 15:
            self.trail.pop(0)
        self.rect.x += self.dx
        self.rect.y += self.dy

class Brick(pygame.Rect):
    def __init__(self, x, y, w, h, color):
        super().__init__(x, y, w, h)
        self.color = color

    def draw(self, surface):
        # Interior más oscuro
        inner_color = (max(0, self.color[0]-80), max(0, self.color[1]-80), max(0, self.color[2]-80))
        pygame.draw.rect(surface, inner_color, self, border_radius=5)
        # Borde brillante
        pygame.draw.rect(surface, self.color, self, border_radius=5, width=2)
        
        # Efecto de luz (brillo superior)
        pygame.draw.line(surface, WHITE, (self.x + 5, self.y + 2), (self.right - 5, self.y + 2), 2)

class PowerUp(pygame.Rect):
    def __init__(self, x, y):
        super().__init__(x, y, 20, 20)
        self.dy = 3
        self.color = (255, 255, 0)
        
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.center, 10)
        pygame.draw.circle(surface, WHITE, self.center, 10, 2)

def spawn_extra_ball(x, y):
    b = Ball(x, y)
    b.dy = -abs(b.dy)
    return b

def create_bricks():
    bricks = []
    rows = 5
    cols = 6
    brick_width = 80
    brick_height = 30
    padding = 10
    offset_x = (WIDTH - (cols * (brick_width + padding) - padding)) // 2
    offset_y = 120

    for row in range(rows):
        color = BRICK_COLORS[row % len(BRICK_COLORS)]
        for col in range(cols):
            x = offset_x + col * (brick_width + padding)
            y = offset_y + row * (brick_height + padding)
            bricks.append(Brick(x, y, brick_width, brick_height, color))
    return bricks

def main():
    paddle = Paddle()
    balls = [Ball(WIDTH // 2, HEIGHT - 150)]
    bricks = create_bricks()
    powerups = []
    
    score = 0
    combo = 0
    
    running = True
    game_over = False

    # Fondo "cyberpunk/grid"
    grid_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for x in range(0, WIDTH, 50):
        pygame.draw.line(grid_surface, (30, 30, 50, 30), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(grid_surface, (30, 30, 50, 30), (0, y), (WIDTH, y))

    while running:
        screen.fill(BG_COLOR)
        screen.blit(grid_surface, (0, 0))

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_SPACE:
                    main() # Reiniciar juego
                    return

        if not game_over:
            # Controles de movimiento
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and paddle.left > 0:
                paddle.x -= paddle.speed
            if keys[pygame.K_RIGHT] and paddle.right < WIDTH:
                paddle.x += paddle.speed
                
            # Soporte táctil / Mouse
            mouse_pressed = pygame.mouse.get_pressed()
            if mouse_pressed[0]:
                mouse_x, _ = pygame.mouse.get_pos()
                if mouse_x < WIDTH // 2 and paddle.left > 0:
                    paddle.x -= paddle.speed
                elif mouse_x > WIDTH // 2 and paddle.right < WIDTH:
                    paddle.x += paddle.speed

            # Actualizar bolas y chequear colisiones
            for ball in balls[:]:
                ball.update()

                # Rebote en paredes
                if ball.rect.left <= 0 or ball.rect.right >= WIDTH:
                    ball.dx *= -1
                # Rebote en techo
                if ball.rect.top <= 0:
                    ball.dy *= -1
                    
                # Si cae la bola por abajo
                if ball.rect.bottom >= HEIGHT:
                    balls.remove(ball)
                    if len(balls) == 0:
                        game_over = True
                    combo = 0
                    continue

                # Colisión con la paleta (paddle)
                if ball.rect.colliderect(paddle) and ball.dy > 0:
                    ball.rect.bottom = paddle.top # Evitar que se quede pegada adentro
                    ball.dy *= -1
                    # Cambiar ángulo dependiendo de dónde pegue en la paleta
                    offset = (ball.rect.centerx - paddle.centerx) / (paddle.width / 2)
                    ball.dx = offset * 6 

                # Colisión con ladrillos (bricks)
                for brick in bricks[:]:
                    if ball.rect.colliderect(brick):
                        bricks.remove(brick)
                        ball.dy *= -1
                        score += 100
                        combo += 1
                        
                        # Drop de powerup (Probabilidad de 15% de Multiball)
                        if random.random() < 0.15: 
                            powerups.append(PowerUp(brick.centerx, brick.centery))
                        break # Solo romper un bloque por iteración

            # Actualizar powerups
            for powerup in powerups[:]:
                powerup.y += powerup.dy
                # Agarrar powerup
                if powerup.colliderect(paddle):
                    balls.append(spawn_extra_ball(paddle.centerx, paddle.top - 20))
                    powerups.remove(powerup)
                # Caída al vacío
                elif powerup.top > HEIGHT:
                    powerups.remove(powerup)
            
            # Pasar al siguiente nivel si no hay ladrillos
            if len(bricks) == 0:
                bricks = create_bricks()
                balls.append(spawn_extra_ball(WIDTH // 2, HEIGHT - 150)) # Bola extra de premio

        # Dibujar todos los objetos
        paddle.draw(screen)
        for brick in bricks:
            brick.draw(screen)
        for powerup in powerups:
            powerup.draw(screen)
        for ball in balls:
            ball.draw(screen)

        # Interfaz de Usuario (Textos)
        score_text = font.render(f"SCORE: {score}", True, WHITE)
        combo_text = font.render(f"COMBO: {combo}", True, (255, 200, 0))
        screen.blit(score_text, (WIDTH - 150, 20))
        screen.blit(combo_text, (WIDTH - 150, 50))
        
        title = title_font.render("PYTHON BRICK BREAKER", True, (0, 150, 255))
        screen.blit(title, (20, 20))

        if game_over:
            go_text = title_font.render("GAME OVER", True, (255, 50, 50))
            restart_text = font.render("Presiona ESPACIO para reiniciar", True, WHITE)
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 50))
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
