import pygame
import math

class Robot:
    def __init__(self, x: float = 0, y: float = 0, theta: float = 0, size=20, color=(0, 0, 255)):
        """
        Initialize a robot with position and orientation
        
        Args:
            x (float): x-coordinate in world space
            y (float): y-coordinate in world space
            theta (float): orientation in radians (0 is facing right, increases counter-clockwise)
            size (float): radius of the robot in world units
            color (tuple): RGB color tuple for the robot
        """
        self.x = x
        self.y = y
        self.theta = theta
        self.size = size
        self.color = color
        self.trail = []  # Store positions for drawing a trail
        self.max_trail_length = 100  # Maximum number of positions to store
        
        # Movement control
        self.move_forward = False
        self.move_backward = False
        self.turn_left = False
        self.turn_right = False
        self.speed = 50  # Units per second
        self.turn_speed = math.pi  # Radians per second (180 degrees)
        
    def set_pose(self, x, y, theta):
        """Set the robot's position and orientation"""
        self.x = x
        self.y = y
        self.theta = theta
        self._update_trail()
        
    def move(self, distance, turn_angle=0):
        """
        Move the robot forward by distance and turn by angle
        
        Args:
            distance (float): Distance to move in the direction of current heading
            turn_angle (float): Angle to turn in radians (positive is counter-clockwise)
        """
        # Update orientation
        self.theta += turn_angle
        
        # Move in the direction of the current heading
        self.x += distance * math.cos(self.theta)
        self.y += distance * math.sin(self.theta)
        
        self._update_trail()
        
    def update(self, dt):
        """
        Update robot position based on current movement controls
        
        Args:
            dt (float): Time since last update in seconds
        """
        # Calculate distance and angle changes based on controls
        distance = 0
        angle = 0
        
        if self.move_forward:
            distance += self.speed * dt
        if self.move_backward:
            distance -= self.speed * dt
        if self.turn_left:
            angle += self.turn_speed * dt
        if self.turn_right:
            angle -= self.turn_speed * dt
            
        # Apply movement if needed
        if distance != 0 or angle != 0:
            self.move(distance, angle)
        
    def _update_trail(self):
        """Update the trail of the robot's movement"""
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
    
    def draw(self, screen, world_to_screen_func):
        """
        Draw the robot on the screen
        
        Args:
            screen: Pygame screen object
            world_to_screen_func: Function to convert world coordinates to screen coordinates
        """
        # Convert robot position to screen coordinates
        center_screen = world_to_screen_func((self.x, self.y))
        
        # Calculate the radius in screen coordinates based on zoom
        test_point = (self.x + 1, self.y)
        test_screen = world_to_screen_func(test_point)
        screen_size = math.sqrt((test_screen[0] - center_screen[0])**2 + 
                               (test_screen[1] - center_screen[1])**2) * self.size
        
        # Draw the robot body (circle)
        pygame.draw.circle(screen, self.color, center_screen, screen_size)
        
        # Draw a line indicating the robot's orientation
        end_x = center_screen[0] + screen_size * -math.sin(self.theta)
        end_y = center_screen[1] + screen_size * math.cos(self.theta)
        pygame.draw.line(screen, (0, 0, 0), center_screen, (end_x, end_y), 2)
        
        # Draw the trail if it exists
        if len(self.trail) > 1:
            trail_points = [world_to_screen_func(point) for point in self.trail]
            pygame.draw.lines(screen, (255, 0, 0), False, trail_points, 1)

    def get_pose(self):
        """Return the current pose of the robot"""
        return (self.x, self.y, self.theta)
