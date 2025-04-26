import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Paddle settings
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 8

# Ball settings
BALL_RADIUS = 10
BALL_SPEED_X = 5
BALL_SPEED_Y = 5

# Brick settings
BRICK_WIDTH = 75
BRICK_HEIGHT = 30
BRICK_ROWS = 5
BRICK_COLS = 10

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Breakout Game")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Font for displaying text
font = pygame.font.Font(None, 36)


class Paddle:
    def __init__(self):
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = SCREEN_HEIGHT - self.height - 10
        self.speed = PADDLE_SPEED
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self, direction):
        if direction == "left" and self.rect.left > 0:
            self.rect.x -= self.speed
        if direction == "right" and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

    def draw(self):
        pygame.draw.rect(screen, BLUE, self.rect)


class Ball:
    def __init__(self):
        self.radius = BALL_RADIUS
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.speed_x = BALL_SPEED_X * random.choice([-1, 1])
        self.speed_y = -BALL_SPEED_Y
        self.rect = pygame.Rect(self.x, self.y, self.radius * 2, self.radius * 2)

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Ball collision with walls
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed_x *= -1
        if self.rect.top <= 0:
            self.speed_y *= -1

    def draw(self):
        pygame.draw.circle(screen, RED, self.rect.center, self.radius)

    def reset(self):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed_x = BALL_SPEED_X * random.choice([-1, 1])
        self.speed_y = -BALL_SPEED_Y


class Brick:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.color = random.choice([RED, GREEN, BLUE])

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)


def create_bricks():
    bricks = []
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            brick = Brick(col * (BRICK_WIDTH + 5) + 30, row * (BRICK_HEIGHT + 5) + 50)
            bricks.append(brick)
    return bricks


def main():
    paddle = Paddle()
    ball = Ball()
    bricks = create_bricks()
    score = 0
    lives = 3
    running = True

    while running:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Paddle movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            paddle.move("left")
        if keys[pygame.K_RIGHT]:
            paddle.move("right")

        # Ball movement
        ball.move()

        # Ball collision with paddle
        if ball.rect.colliderect(paddle.rect):
            ball.speed_y *= -1

        # Ball collision with bricks
        for brick in bricks[:]:
            if ball.rect.colliderect(brick.rect):
                ball.speed_y *= -1
                bricks.remove(brick)
                score += 10

        # Ball out of bounds
        if ball.rect.bottom >= SCREEN_HEIGHT:
            lives -= 1
            if lives == 0:
                running = False
            else:
                ball.reset()

        # Draw everything
        paddle.draw()
        ball.draw()
        for brick in bricks:
            brick.draw()

        # Display score and lives
        score_text = font.render(f"Score: {score}", True, WHITE)
        lives_text = font.render(f"Lives: {lives}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (SCREEN_WIDTH - 150, 10))

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()