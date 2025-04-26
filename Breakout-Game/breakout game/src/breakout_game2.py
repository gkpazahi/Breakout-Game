"""
Breakout Game Class
--------------
This is a Python implementation of the classic Breakout game using the Pygame library.
The game includes features such as multiple levels, power-ups, particle effects, and background music.
It also has user authentication for tracking high scores and progress, with login and registration functionality.
"""

import random
import pygame
from pathlib import Path
from paddle import Paddle
from ball import Ball
from brick import Brick
from particle import Particle
from power_up import PowerUp
from star import Star
from user_auth import load_users_from_file, register_user, login_user, get_high_score, update_high_score
from text_input_box import TextInputBox
from passtext_input_box import PassTextInputBox
from button import Button

# Game States
MAIN_MENU = 0  # Initial menu where the user can log in or register
GAME_RUNNING = 1  # The game loop where gameplay occurs
PAUSED = 2  # Pauses the game
GAME_OVER = 3  # Displays when the player loses all lives
POST_LOGIN_MENU = 4  # Menu shown after a successful login, before starting the game

# Power-up variables
POWER_UP_SIZE = 20
POWER_UP_DURATION = 5000  # Duration in milliseconds (5 seconds)
SPECIAL_BRICK_TYPES = ["increase_paddle_size", "slow_ball", "extra_life"]  # Power-up types

# File paths
current_dir = Path(__file__).parent.resolve()  # Get the current directory
sounds_dir = current_dir.parent / "sounds"  # Navigate to the sounds directory


class BreakoutGame:
    """
    BreakoutGame Class:
    Handles all aspects of the game, including initializing the game, running game states,
    managing player input, collisions, power-ups, scoring, and rendering graphics.
    """

    def __init__(self):
        # Initialize Pygame modules
        pygame.init()
        pygame.mixer.init()

        # Set up the display and clock
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Breakout Game")
        self.clock = pygame.time.Clock()

        # Initialize game objects
        self.paddle = Paddle()
        self.ball = Ball()
        self.default_ball_dx = self.ball.dx
        self.default_ball_dy = self.ball.dy
        self.row_range = 5  # Number of rows of bricks in the current level
        self.bricks = self.create_bricks(self.row_range, 10)  # Create the brick layout

        self.particles = []  # Particle effects
        self.fragments = []  # Brick fragments
        self.stars = [Star() for _ in range(100)]  # Background stars for visual effects

        # Game variables
        self.level = 1
        self.score = 0
        self.current_high_score = 0
        self.lives = 3
        self.stage_bricks = len(self.bricks)  # Tracks the number of bricks in the current stage
        self.active_power_up = None  # Tracks the active power-up
        self.power_ups = []  # List of power-ups
        self.power_up_start_time = 0
        self.paddle_width_default = self.paddle.rect.width

        # Load background music
        pygame.mixer.music.load(sounds_dir / "background_music.mp3")  # Load background music
        pygame.mixer.music.set_volume(0.5)  # Set volume (0.0 to 1.0)

        # Game state variables
        self.game_state = MAIN_MENU
        self.logged_in = False  # Tracks if a user is logged in
        self.current_user = None  # Stores the current logged-in user
        self.focused = True  # Track if the window is in focus

        # User input for authentication
        self.username_input = TextInputBox(300, 250, 200, 50)
        self.password_input = PassTextInputBox(300, 350, 200, 50)

        # Buttons for login and registration
        self.login_button = Button(300, 450, 200, 50, "Login")
        self.register_button = Button(300, 520, 200, 50, "Register")

        # Font for rendering text
        self.font = pygame.font.Font(None, 36)  # Font for text

        # Load user data
        load_users_from_file()

        pygame.mixer.music.play(-1)  # Start playing background music (loop it indefinitely)

    def create_bricks(self, rows, cols):
        """
        Creates a grid of bricks with optional power-ups assigned to some bricks.
        Arguments:
            - rows: The number of rows of bricks
            - cols: The number of columns of bricks
        Returns:
            - bricks: A list of Brick objects
        """
        bricks = []
        for row in range(rows):
            for col in range(cols):
                brick = Brick(col * 80 + 10, row * 30 + 10)
                if random.random() < 0.2:  # 20% chance of being a special brick
                    brick.power_up_type = random.choice(SPECIAL_BRICK_TYPES)
                bricks.append(brick)
        return bricks

    def activate_power_up(self, power_up_type):
        """
        Activates the specified power-up for the player.
        Arguments:
            - power_up_type: The type of power-up to activate
        """
        activate_power_up = pygame.mixer.Sound(sounds_dir / "power_up_activate.wav")  # Load activation sound for power up
        pygame.mixer.Sound.play(activate_power_up)  # Play activation sound for power up

        # Activate power-up based on its type
        if power_up_type == "increase_paddle_size":
            self.paddle.rect.width = self.paddle_width_default * 1.5  # Increase paddle size
        elif power_up_type == "slow_ball":
            self.ball.dx *= 0.7  # Slow down the ball speed
            self.ball.dy *= 0.7
        elif power_up_type == "extra_life":
            self.lives += 1  # Add extra life

        # Track the activated power-up and its start time
        self.active_power_up = power_up_type
        self.power_up_start_time = pygame.time.get_ticks()

    def reset_power_ups(self):
        """
        Resets any active power-up effects back to the default state.
        """
        if self.active_power_up == "increase_paddle_size":
            self.paddle.rect.width = self.paddle_width_default  # Reset paddle size
        elif self.active_power_up == "slow_ball":
            # Preserve current direction of the ball
            direction_x = 1 if self.ball.dx > 0 else -1
            direction_y = 1 if self.ball.dy > 0 else -1

            # Reset speed and apply preserved direction
            self.ball.dx = self.default_ball_dx * direction_x
            self.ball.dy = self.default_ball_dy * direction_y

        self.active_power_up = None  # Clear the active power-up

    def run(self):
        """
        Activates main game loop.
        """
        while True:
            self.handle_events()  # Handle events such as quit, focus loss, etc.
            if self.focused:  # Update game if the window is focused
                if self.game_state == GAME_RUNNING:  # If the game is in the running state
                    self.update_game()  # Update game elements like ball, paddle, etc.
                elif self.game_state == POST_LOGIN_MENU:
                    self.draw_post_login_menu()  # Only update the game if in focus and not game over
            self.draw_game()  # Draw the game regardless of focus to keep screen updated
            self.clock.tick(60)  # Limit the frame rate to 60 FPS

    def handle_events(self):
        """
        Handles the various events of the main game loop.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # If the user closes the window
                pygame.quit()
                exit()

            # Handle window focus loss and regain
            if event.type == pygame.WINDOWFOCUSLOST:
                self.focused = False  # Pause the game when focus is lost
            if event.type == pygame.WINDOWFOCUSGAINED:
                self.focused = True  # Resume game when focus is regained

            # Handle events in the main menu
            if self.game_state == MAIN_MENU:
                self.username_input.handle_event(event)  # Handle username input
                self.password_input.handle_event(event)  # Handle password input

                if self.login_button.handle_event(event):  # If the login button is pressed
                    self.login_user()  # Handle user login
                elif self.register_button.handle_event(event):  # If the register button is pressed
                    self.register_user()  # Handle user registration

            # Handle events in the post login menu
            if self.game_state == POST_LOGIN_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.game_state = GAME_RUNNING  # Start the game when Enter is pressed
                        pygame.mixer.music.play(-1)  # Play background music in a loop

            # Handle key presses when the game is running
            if self.game_state == GAME_RUNNING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.game_state = PAUSED  # Pause the game if 'P' is pressed
                        pygame.mixer.music.pause()  # Pause background music

            # Handle key presses in the pause screen
            if self.game_state == PAUSED:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.game_state = GAME_RUNNING  # Resume the game when Enter is pressed
                    pygame.mixer.music.unpause()  # Resume background music

            # Handle key presses in the game over screen
            if self.game_state == GAME_OVER:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_game()

    def check_collision_with_bricks(self, bricks, particles, fragments):
        """
        Check for collisions between the ball and the bricks, handle brick destruction,
        power-up creation, particle effects, and breaking bricks into fragments.

        Parameters:
            - bricks (list): A list of brick objects currently in the game.
            - particles (list): A list that will store particle effects (e.g., fire particles)
                        created when a brick is destroyed.
            - fragments (list): A list that will store the brick fragments generated upon breaking.
                        These fragments are used for visual effects when a brick is destroyed.
        """

        # Load sound effects for brick breaking and power-up drop
        brick_break_sound = pygame.mixer.Sound(sounds_dir / "destroy_sound.wav")  # Load brick break sound
        power_up_drop_sound = pygame.mixer.Sound(sounds_dir / "power_up_drop.wav")  # Load power-up drop sound

        # Check collision between ball and bricks
        for brick in bricks[:]:  # Iterate through a copy of the bricks list
            if self.ball.rect.colliderect(brick.rect):  # If ball collides with a brick
                self.ball.dy = -self.ball.dy  # Bounce off the brick
                pygame.mixer.Sound.play(brick_break_sound)  # Play brick break sound

                if brick.power_up_type:  # If the brick has a power-up
                    power_up = PowerUp(brick.rect.x + 25, brick.rect.y, brick.power_up_type)
                    self.power_ups.append(power_up)  # Add power-up to the list
                    pygame.mixer.Sound.play(power_up_drop_sound)  # Play power-up drop sound

                bricks.remove(brick)  # Remove the brick from the list

                # Create fire particles when a brick is destroyed
                for _ in range(10):
                    particles.append(Particle(brick.rect.centerx, brick.rect.centery))

                # Break the brick into fragments
                num_fragments = random.randint(4, 10)  # Random number of fragments
                for _ in range(num_fragments):
                    fragments.append(brick.break_into_fragments())

    def update_game(self):
        """
        Update the game state, handle user input for paddle movement,
        check for collisions, update particles and fragments, manage power-ups,
        and determine game over or level up conditions.
        """
        game_over = pygame.mixer.Sound(sounds_dir / "game_over.wav")  # Load sound for game over sound
        lose_life = pygame.mixer.Sound(sounds_dir / "lost_life.wav")  # Load sound for a lost life
        if self.game_state == GAME_RUNNING:
            self.ball.move()
            self.ball.check_collision_with_walls()

            # Paddle movement with arrow keys
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.paddle.move(-9)
            if keys[pygame.K_RIGHT]:
                self.paddle.move(9)

            # Update star background
            for star in self.stars:
                star.update()

            self.ball.check_collision_with_paddle(self.paddle, self.particles)
            self.check_collision_with_bricks(self.bricks, self.particles, self.fragments)

            # Update particles and fragments
            for particle in self.particles[:]:
                particle.update()
                if particle.lifetime <= 0 or particle.size <= 0:
                    self.particles.remove(particle)

            for fragment in self.fragments[:]:
                fragment.update()
                if fragment.width <= 0 or fragment.height <= 0:
                    self.fragments.remove(fragment)

            # Check to update score (when brick destroyed)
            if len(self.bricks) < self.stage_bricks:
                self.scoring()

            # Check for level up (all bricks are cleared)
            if len(self.bricks) == 0:
                self.level_up()

            # Check for game over (if ball hits bottom)
            if self.ball.rect.bottom >= 600 and self.lives > 1:
                self.lives -= 1  # Deducts a life
                pygame.mixer.Sound.play(lose_life)  # Play sound for a lost life
                self.ball = Ball()
            if self.ball.rect.bottom >= 600 and self.lives == 1:
                self.update_high_score()
                self.current_high_score = get_high_score(self.current_user)  # Get the current high score for the logged-in user
                pygame.mixer.Sound.play(game_over)  # Play game over sound
                self.game_state = GAME_OVER  # Change to GAME_OVER state when player loses

            # Power-up movement and collection
            for power_up in self.power_ups[:]:
                power_up.move()  # Power-ups fall downwards

                if power_up.rect.colliderect(self.paddle.rect):
                    self.activate_power_up(power_up.power_up_type)
                    self.power_ups.remove(power_up)

                if power_up.rect.top >= 600:
                    self.power_ups.remove(power_up)

            if self.active_power_up and pygame.time.get_ticks() - self.power_up_start_time > POWER_UP_DURATION:
                self.reset_power_ups()

    def scoring(self):
        """
        Update the player's score based on the number of bricks destroyed
        in the current level. The score is incremented based on the level
        and the number of bricks that were present.
        """
        bricks_destroyed = self.stage_bricks - len(self.bricks)  # Only count bricks from the current level
        self.score += bricks_destroyed * (self.level * 100)  # Add points incrementally
        self.stage_bricks = len(self.bricks)  # Update stage_bricks to reflect the remaining bricks

    def level_up(self):
        """
        Handle the transition to the next level by increasing the level number,
        adjusting paddle and ball speed, and creating a new set of bricks.
        The game state is set back to GAME_RUNNING.
        """
        speed_increase = 1.1
        self.level += 1
        self.row_range += 1

        # Set the next level
        self.paddle = Paddle()
        self.ball = Ball()
        self.ball.dx *= speed_increase
        self.ball.dy *= speed_increase
        self.default_ball_dx = self.ball.dx
        self.default_ball_dy = self.ball.dy
        self.particles = []
        self.fragments = []

        if self.row_range > 10:
            self.row_range = 10

        self.bricks = self.create_bricks(self.row_range, 10)
        self.stage_bricks = len(self.bricks)
        self.game_state = GAME_RUNNING

    def draw_game(self):
        """
        Render the current game state on the screen, including the main menu,
        game running visuals, post-login menu, paused screen, or game over screen.
        """
        self.screen.fill((0, 0, 0))  # Black background

        if self.game_state == MAIN_MENU:
            self.draw_main_menu()
        elif self.game_state == GAME_RUNNING:
            self.draw_game_running()
        elif self.game_state == POST_LOGIN_MENU:
            self.draw_post_login_menu()
        elif self.game_state == PAUSED:
            self.draw_paused_screen()
        elif self.game_state == GAME_OVER:
            self.draw_game_over_screen()

        pygame.display.flip()

    def draw_main_menu(self):
        """
        Draw the main menu interface, including the title, input fields for
        username and password, and buttons for login and registration.
        """
        self.screen.fill((0, 0, 0))  # Set background color to black

        # Draw the main menu title
        title_font = pygame.font.Font