import sys
import math
import pygame
import valkey
import threading
import time
import json
from robot import Robot

class Canvas:
    def __init__(self, width=800, height=600, robo_id: int | None = None):
        """Initialize the canvas for visualizing robots"""
        # Screen dimensions
        self.WIDTH = width
        self.HEIGHT = height
        
        # Initialize pygame
        if not pygame.get_init():
            pygame.init()
            
        # Create screen
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Robot Visualization Canvas")
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRID_BG = (20, 20, 20)
        self.GRID_COLOR = (45, 45, 45)
        self.OBSTACLE_COLOR = (100, 100, 100)
        
        # Canvas settings
        self.canvas_pos = [0, 0]  # Top-left corner of the canvas in the world space
        self.zoom = 1.0
        
        # Key state tracking
        self.keys_pressed = {
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_w: False,
            pygame.K_s: False
        }
        
        # Clock for controlling framerate
        self.clock = pygame.time.Clock()
        
        # Valkey connection
        self.vk = valkey.Valkey(host='127.0.0.1', port=6379)
        
        # Robot data storage
        self.robo_id = robo_id
        self.robots = {}  # {robot_id: Robot()}
        self.robots_lock = threading.Lock()
        self.robot_scan_data = {}  # {robot_id: [(end_pos, distance), ...]}
        
        # Map data (occupancy grid)
        self.grid_size = 0.5  # Size of each grid cell in world units
        self.occupancy_grid = {}  # {(grid_x, grid_y): confidence} where confidence is 0-100
        
        # Start the data fetching thread
        self.running = True
        self.data_thread = threading.Thread(target=self.fetch_robot_data, daemon=True)
        self.data_thread.start()
        
    def fetch_robot_data(self):
        """Thread function to fetch robot data from Valkey"""
        while self.running:
            if robo_id:
                active_robots = [f'{self.robo_id}'.encode()]
            else:
                # Get list of active robots
                active_robots = self.vk.smembers("active_robots")
            
            for robot_id in active_robots:
                # Get the latest data for this robot
                latest_data = self.vk.lrange(f"robot:{robot_id.decode('utf-8')}:history", -1, -1)
                if latest_data:
                    try:
                        data_str = latest_data[0].decode('utf-8')
                        self.process_robot_data(data_str)
                    except Exception as e:
                        print(f"Error processing robot data: {e}")
            
            # Check for new robots at a slower rate
            time.sleep(0.05)
    
    def process_robot_data(self, data_str):
        """Process robot data from string format"""
        # Split by / to separate the parts
        data = data_str.split('/')
        
        # Extract metadata (timestamp, robot_id, position, orientation)
        metadata = data[0].split(',')
        if len(metadata) < 7:
            return
        
        timestamp, robot_id, commRange = metadata[0], metadata[1], metadata[2]
        pos_x, pos_y, pos_z, orientation = metadata[3], metadata[4], metadata[5], metadata[6]
        
        # Create or update robot
        robot_id = int(robot_id)
        if robot_id not in self.robots:
            # Create new robot with a color based on its ID
            color = ((robot_id * 83) % 256, (robot_id * 157) % 256, (robot_id * 223) % 256)
            with self.robots_lock:
                self.robots[robot_id] = Robot(
                    x=float(pos_x), 
                    y=float(pos_z),  # Use z as y in 2D visualization
                    theta=float(orientation),
                    size=1,
                    color=color
                )
        else:
            # Update existing robot
            self.robots[robot_id].set_pose(
                float(pos_x),
                float(pos_z),  # Use z as y in 2D visualization
                float(orientation)
            )
        
        # Get robot position and orientation
        robot_x, robot_y = float(pos_x), float(pos_z)
        robot_theta = float(orientation)
        
        # Calculate ray direction and distance
        robot_pos = (robot_x, robot_y)

        # Get ray endpoint and collision flag
        collision_flag = False
        update_data = []
        self.robot_scan_data[robot_id] = []
        for datapoint in data[1:]:
            ray_data = datapoint.split(',')
            if len(ray_data) < 4:
                break
            
            end_x, end_y, end_z, collFlag = int(ray_data[0]), int(ray_data[1]), int(ray_data[2]), int(ray_data[3])
            
            # Calculate distance between robot position and end position
            end_pos = (end_x, end_z)  # Use z as y in 2D visualization
            distance = math.sqrt((end_pos[0] - robot_pos[0])**2 + (end_pos[1] - robot_pos[1])**2)
            
            print(end_x, end_z, collFlag)
            if collFlag == 1:
                print("here")
                collision_flag = True
                update_data.append((end_pos, distance))
            
            # Store scan data for visualization (single ray)
            # TODO: instead, append the data to the array and clear the array every time stamp
            self.robot_scan_data[robot_id].append((end_pos, distance))
        
        # Update occupancy grid if collision was detected
        if collision_flag:
            self.update_occupancy_grid(robot_id, update_data)
    
    def update_occupancy_grid(self, robot_id, scan_data):
        """Update the occupancy grid with new scan data"""
        if robot_id not in self.robots:
            return
            
        robot = self.robots[robot_id]
        
        for end_pos, distance in scan_data:
            if distance >= 19.9:  # Skip max-range readings (likely no obstacle)
                continue
                
            # Calculate world coordinates of the obstacle
            obstacle_x = end_pos[0]
            obstacle_y = end_pos[1]
            
            # Convert to grid coordinates
            grid_x = int(obstacle_x / self.grid_size)
            grid_y = int(obstacle_y / self.grid_size)
            
            # Update occupancy grid
            grid_key = (grid_x, grid_y)
            if grid_key in self.occupancy_grid:
                self.occupancy_grid[grid_key] = min(100, self.occupancy_grid[grid_key] + 5)
            else:
                self.occupancy_grid[grid_key] = 50  # Initial confidence
        
    def world_to_screen(self, pos):
        """Convert world coordinates to screen coordinates"""
        x, y = pos
        return (x - self.canvas_pos[0]) * self.zoom + self.WIDTH / 2, (y - self.canvas_pos[1]) * self.zoom + self.HEIGHT / 2
        
    def screen_to_world(self, pos):
        """Convert screen coordinates to world coordinates"""
        x, y = pos
        return (x - self.WIDTH / 2) / self.zoom + self.canvas_pos[0], (y - self.HEIGHT / 2) / self.zoom + self.canvas_pos[1]
        
    def get_center_coords(self):
        """Get the world coordinates of the center of the screen"""
        center_screen = (self.WIDTH / 2, self.HEIGHT / 2)
        center_world = self.screen_to_world(center_screen)
        return center_world
        
    def draw_grid(self):
        """Draw a grid to help visualize the infinite canvas"""
        # Calculate grid size based on zoom level
        if self.zoom > 2:
            grid_spacing = 10
        elif self.zoom > 0.5:
            grid_spacing = 50
        else:
            grid_spacing = 100
        
        # Calculate the visible area in world coordinates
        top_left = self.screen_to_world((0, 0))
        bottom_right = self.screen_to_world((self.WIDTH, self.HEIGHT))
        
        # Calculate starting grid lines
        start_x = (int(top_left[0] / grid_spacing) * grid_spacing)
        start_y = (int(top_left[1] / grid_spacing) * grid_spacing)
        
        # Draw vertical grid lines
        x = start_x
        while x <= bottom_right[0]:
            start_point = self.world_to_screen((x, top_left[1]))
            end_point = self.world_to_screen((x, bottom_right[1]))
            # Make axis lines thicker
            line_width = 2 if abs(x) < 0.1 else 1
            pygame.draw.line(self.screen, self.GRID_COLOR, start_point, end_point, line_width)
            x += grid_spacing
        
        # Draw horizontal grid lines
        y = start_y
        while y <= bottom_right[1]:
            start_point = self.world_to_screen((top_left[0], y))
            end_point = self.world_to_screen((bottom_right[0], y))
            # Make axis lines thicker
            line_width = 2 if abs(y) < 0.1 else 1
            pygame.draw.line(self.screen, self.GRID_COLOR, start_point, end_point, line_width)
            y += grid_spacing
        
        # Draw axes
        origin_screen = self.world_to_screen((0, 0))
        
        # X-axis
        pygame.draw.line(self.screen, self.WHITE, 
                         (0, origin_screen[1]), 
                         (self.WIDTH, origin_screen[1]), 3)
        
        # Y-axis
        pygame.draw.line(self.screen, self.WHITE, 
                         (origin_screen[0], 0), 
                         (origin_screen[0], self.HEIGHT), 3)
                         
    def draw_occupancy_grid(self):
        """Draw the occupancy grid on the canvas"""
        # Calculate the visible area in world coordinates
        top_left = self.screen_to_world((0, 0))
        bottom_right = self.screen_to_world((self.WIDTH, self.HEIGHT))
        
        # Clear the screen
        self.screen.fill(self.BLACK)
        
        # Calculate grid cell dimensions in screen coordinates
        grid_cell_screen = self.world_to_screen((self.grid_size, 0))[0] - self.world_to_screen((0, 0))[0]
        
        # Only draw cells within the visible area
        min_grid_x = int(top_left[0] / self.grid_size) - 1
        max_grid_x = int(bottom_right[0] / self.grid_size) + 1
        min_grid_y = int(top_left[1] / self.grid_size) - 1
        max_grid_y = int(bottom_right[1] / self.grid_size) + 1
        
        # for (grid_x, grid_y), confidence in self.occupancy_grid.items():
        color_dict = {}
        with self.robots_lock:
            for idx, robo in self.robots.items():
                keys = self.vk.keys(f"robot:{idx}:km:{idx}:*")
                for key in keys:
                    x, y = key.decode("utf-8").split(":")[-2:]
                    grid_x, grid_y = int(int(x)/self.grid_size), int(int(y)/self.grid_size)
                    value = self.vk.get(key).decode("utf-8")
                    value = int(value)
                    
                    if value != 1:
                        continue

                    # Skip if outside visible area
                    if grid_x < min_grid_x or grid_x > max_grid_x or grid_y < min_grid_y or grid_y > max_grid_y:
                        continue
                    
                    # Convert grid coordinates to world coordinates
                    world_x = grid_x * self.grid_size
                    world_y = grid_y * self.grid_size
                    
                    # Convert to screen coordinates
                    screen_x, screen_y = self.world_to_screen((world_x, world_y))
                    if (screen_x, screen_y) not in color_dict.keys():
                        color_dict[(screen_x, screen_y)] = robo.color
                    else:
                        r, g, b = color_dict[(screen_x, screen_y)]
                        r = min(255, r + robo.color[0])
                        g = min(255, g + robo.color[1])
                        b = min(255, b + robo.color[2])
                        color_dict[(screen_x, screen_y)] = (r, g, b)
                
        # Draw cell
        for (screen_x, screen_y), color in color_dict.items():
            rect = pygame.Rect(
                screen_x, 
                screen_y, 
                max(1, grid_cell_screen), 
                max(1, grid_cell_screen)
            )
            pygame.draw.rect(self.screen, color, rect)

    def draw_solo_occupancy_grid(self):
        """Draw the occupancy grid on the canvas"""
        # Calculate the visible area in world coordinates
        top_left = self.screen_to_world((0, 0))
        bottom_right = self.screen_to_world((self.WIDTH, self.HEIGHT))
        
        # Clear the screen
        self.screen.fill(self.BLACK)
        
        # Calculate grid cell dimensions in screen coordinates
        grid_cell_screen = self.world_to_screen((self.grid_size, 0))[0] - self.world_to_screen((0, 0))[0]
        
        # Only draw cells within the visible area
        min_grid_x = int(top_left[0] / self.grid_size) - 1
        max_grid_x = int(bottom_right[0] / self.grid_size) + 1
        min_grid_y = int(top_left[1] / self.grid_size) - 1
        max_grid_y = int(bottom_right[1] / self.grid_size) + 1
        
        # for (grid_x, grid_y), confidence in self.occupancy_grid.items():
        color_dict = {}
        for idx in self.vk.smembers("active_robots"):
            other_idx = int(idx.decode('utf-8'))
            keys = self.vk.keys(f"robot:{self.robo_id}:km:{other_idx}:*")
            for key in keys:
                x, y = key.decode("utf-8").split(":")[-2:]
                grid_x, grid_y = int(int(x)/self.grid_size), int(int(y)/self.grid_size)
                value = self.vk.get(key).decode("utf-8")
                value = int(value)
                
                if value != 1:
                    continue

                # Skip if outside visible area
                if grid_x < min_grid_x or grid_x > max_grid_x or grid_y < min_grid_y or grid_y > max_grid_y:
                    continue
                
                # Convert grid coordinates to world coordinates
                world_x = grid_x * self.grid_size
                world_y = grid_y * self.grid_size
                
                # Convert to screen coordinates
                screen_x, screen_y = self.world_to_screen((world_x, world_y))
                if (screen_x, screen_y) not in color_dict.keys():
                    color_dict[(screen_x, screen_y)] = ((other_idx * 83) % 256, (other_idx * 157) % 256, (other_idx * 223) % 256)
                else:
                    r, g, b = color_dict[(screen_x, screen_y)]
                    r = min(255, r + (other_idx * 83) % 256)
                    g = min(255, g + (other_idx * 157) % 256)
                    b = min(255, b + (other_idx * 223) % 256)
                    color_dict[(screen_x, screen_y)] = (r, g, b)
                
        # Draw cell
        for (screen_x, screen_y), color in color_dict.items():
            rect = pygame.Rect(
                screen_x, 
                screen_y, 
                max(1, grid_cell_screen), 
                max(1, grid_cell_screen)
            )
            pygame.draw.rect(self.screen, color, rect)
            
    def draw_scan_data(self):
        """Draw the LiDAR scan data for all robots"""
        for robot_id, scan_data in self.robot_scan_data.items():
            if robot_id not in self.robots:
                continue
                
            robot = self.robots[robot_id]
            robot_x, robot_y = robot.x, robot.y
            robot_theta = robot.theta
            
            for end_pos, distance in scan_data:
                
                # Calculate world coordinates of the scan endpoint
                end_x = end_pos[0]
                end_y = end_pos[1]
                
                # Draw line from robot to scan endpoint
                start_screen = self.world_to_screen((robot_x, robot_y))
                end_screen = self.world_to_screen((end_x, end_y))
                
                # Color based on distance (red to green)
                intensity = min(1.0, distance / 20.0)
                color = (int(255 * (1 - intensity)), int(255 * intensity), 0)
                
                pygame.draw.line(self.screen, color, start_screen, end_screen, 1)
                pygame.draw.circle(self.screen, color, end_screen, 2)
                         
    def draw_hud(self, robot_count):
        """Draw HUD with current position information"""
        font = pygame.font.SysFont(None, 24)
        
        # Display center coordinates
        center_x, center_y = self.get_center_coords()
        coords_text = font.render(f"Center: ({center_x:.2f}, {center_y:.2f})", True, self.WHITE)
        self.screen.blit(coords_text, (10, 10))
        
        # Display zoom level
        zoom_text = font.render(f"Zoom: {self.zoom:.2f}x", True, self.WHITE)
        self.screen.blit(zoom_text, (10, 40))
        
        # Display number of connected robots
        robot_text = font.render(f"Connected Robots: {robot_count}", True, self.WHITE)
        self.screen.blit(robot_text, (10, 70))
        
        # Navigation instructions
        nav_text = font.render("Pan: WASD | Zoom: +/- or Mouse Wheel", True, self.WHITE)
        self.screen.blit(nav_text, (10, self.HEIGHT - 30))
        
    def zoom_at_center(self, factor):
        """Zoom in/out centered on the screen center"""
        # Get the world coordinates of the screen center before zooming
        center_x, center_y = self.get_center_coords()
        
        # Apply zoom
        old_zoom = self.zoom
        self.zoom *= factor
        self.zoom = max(0.1, self.zoom)  # Limit zoom range
        
        # Get new world coordinates of the screen center after zooming
        new_center_x, new_center_y = self.get_center_coords()
        
        # Adjust canvas position to keep the center point fixed
        if old_zoom != self.zoom:
            self.canvas_pos[0] += center_x - new_center_x
            self.canvas_pos[1] += center_y - new_center_y

            
    def handle_continuous_movement(self):
        """Handle continuous movement when arrow keys are held down"""
        pan_speed = 10 / self.zoom  # Adjust speed based on zoom level
        
        if self.keys_pressed[pygame.K_a]:
            self.canvas_pos[0] -= pan_speed
        if self.keys_pressed[pygame.K_d]:
            self.canvas_pos[0] += pan_speed
        if self.keys_pressed[pygame.K_w]:
            self.canvas_pos[1] -= pan_speed
        if self.keys_pressed[pygame.K_s]:
            self.canvas_pos[1] += pan_speed
            
    def handle_events(self):
        """Handle pygame events like keyboard and mouse"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            
            # Mouse events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Mouse wheel up (zoom in)
                    self.zoom_at_center(1.1)
                elif event.button == 5:  # Mouse wheel down (zoom out)
                    self.zoom_at_center(0.9)
            
            # Keyboard events
            elif event.type == pygame.KEYDOWN:
                # Update key state for arrow keys
                if event.key in self.keys_pressed:
                    self.keys_pressed[event.key] = True
            
                # Zoom around mouse position
                if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    mouse_pos = pygame.mouse.get_pos()
                    self.zoom_at_center(1.1)
                elif event.key == pygame.K_MINUS:
                    mouse_pos = pygame.mouse.get_pos()
                    self.zoom_at_center(0.9)
                # Clear map on 'c'
                elif event.key == pygame.K_c:
                    self.occupancy_grid = {}

            elif event.type == pygame.KEYUP:
                # Update key state for arrow keys
                if event.key in self.keys_pressed:
                    self.keys_pressed[event.key] = False
                    
    def update(self):
        """Update the canvas with the current robots"""
        dt = self.clock.get_time() / 1000.0  # Time since last frame in seconds
        
        # Handle events
        self.handle_events()
        
        # Handle continuous movement when arrow keys are held down
        self.handle_continuous_movement()
        
        # Clear screen
        self.screen.fill(self.WHITE)
        
        # Draw occupancy grid
        if not self.robo_id:
            self.draw_occupancy_grid()
        else:
            self.draw_solo_occupancy_grid()
        
        # Draw grid
        self.draw_grid()
        
        # Draw scan data
        self.draw_scan_data()
        
        # Update and draw all robots
        with self.robots_lock:
            for robot in self.robots.values():
                robot.update(dt)
                robot.draw(self.screen, self.world_to_screen)
        
        # Draw a small crosshair at the center of the screen
        center_screen = (self.WIDTH // 2, self.HEIGHT // 2)
        pygame.draw.line(self.screen, self.WHITE, (center_screen[0] - 10, center_screen[1]), (center_screen[0] + 10, center_screen[1]), 1)
        pygame.draw.line(self.screen, self.WHITE, (center_screen[0], center_screen[1] - 10), (center_screen[0], center_screen[1] + 10), 1)
        
        # Draw HUD
        self.draw_hud(len(self.robots))
        
        # Update display
        pygame.display.flip()
        self.clock.tick(60)

# For standalone execution
if __name__ == "__main__":

    args = sys.argv[1:]
    if len(args) > 1:
        print(f"Invalid Usage. Valid Usage: python3 {sys.argv[0]} [robot_id]. [] implies it is optional, not a list.")
        exit()

    if len(args) == 1:
        robo_id = int(args[0])
    else:
        robo_id = None

    canvas = Canvas(width=1024, height=768, robo_id=robo_id)
    
    # Main loop
    try:
        while canvas.running:
            canvas.update()
    except KeyboardInterrupt:
        canvas.running = False
        print("Shutting down...")
