import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle, Polygon
from matplotlib.collections import PatchCollection
import matplotlib.patheffects as path_effects

# Set up figure with 16:9 aspect ratio
fig, ax = plt.subplots(figsize=(16, 9), facecolor='black')
ax.set_facecolor('black')

# Define geological layers (from top to bottom)
layers = [
    {"name": "Surface Soil & Sediment", "y_start": 10, "thickness": 1, "color": "#8B7355", "texture_density": 20},
    {"name": "Quaternary Deposits", "y_start": 9, "thickness": 1, "color": "#D2B48C", "texture_density": 15},
    {"name": "Tertiary Rocks", "y_start": 7, "thickness": 2, "color": "#CD853F", "texture_density": 25},
    {"name": "Mesozoic Strata", "y_start": 5, "thickness": 2, "color": "#A0522D", "texture_density": 30},
    {"name": "Paleozoic Layers", "y_start": 3, "thickness": 2, "color": "#8B4513", "texture_density": 35},
    {"name": "Precambrian Supergroup", "y_start": 1.5, "thickness": 1.5, "color": "#654321", "texture_density": 40},
    {"name": "Vishnu Basement Rocks", "y_start": -1.5, "thickness": 3, "color": "#2C1810", "texture_density": 50},
]

# Animation parameters
fps = 30
duration = 10  # seconds
total_frames = fps * duration

def create_texture(x, y, width, height, density, seed):
    """Create random texture points for geological detail"""
    np.random.seed(seed)
    num_points = int(density * width * height)
    x_points = np.random.uniform(x, x + width, num_points)
    y_points = np.random.uniform(y, y + height, num_points)
    return x_points, y_points

def add_rim_lighting(ax, x, y, width, height, intensity=0.3):
    """Add rim lighting effect to layer edges"""
    # Top rim light
    rim_color = (1.0, 0.9, 0.7, intensity)
    ax.plot([x, x + width], [y + height, y + height],
            color=rim_color, linewidth=3, zorder=10)
    # Bottom rim light (dimmer)
    ax.plot([x, x + width], [y, y],
            color=(1.0, 0.9, 0.7, intensity * 0.5), linewidth=2, zorder=10)

def init():
    """Initialize animation"""
    ax.clear()
    ax.set_xlim(0, 20)
    ax.set_ylim(-5, 12)
    ax.axis('off')
    return []

def animate(frame):
    """Animation function for each frame"""
    ax.clear()
    ax.set_facecolor('black')
    ax.axis('off')

    # Calculate camera descent (zoom into Vishnu Basement Rocks)
    progress = frame / total_frames

    # Smooth easing function (ease-in-out)
    if progress < 0.5:
        ease = 2 * progress * progress
    else:
        ease = 1 - pow(-2 * progress + 2, 2) / 2

    # Start view: full view of all layers
    # End view: zoomed into Vishnu Basement Rocks
    start_y_center = 5
    end_y_center = 0  # Center on Vishnu Basement Rocks
    start_y_range = 17
    end_y_range = 6

    y_center = start_y_center + (end_y_center - start_y_center) * ease
    y_range = start_y_range + (end_y_range - start_y_range) * ease

    ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
    ax.set_xlim(0, 20)

    # Draw each geological layer
    for i, layer in enumerate(layers):
        y_bottom = layer["y_start"]
        thickness = layer["thickness"]
        y_top = y_bottom + thickness

        # Main layer rectangle
        rect = Rectangle((0, y_bottom), 20, thickness,
                         facecolor=layer["color"],
                         edgecolor='none',
                         zorder=1)
        ax.add_patch(rect)

        # Add texture (small dots/points for geological detail)
        x_tex, y_tex = create_texture(0, y_bottom, 20, thickness,
                                      layer["texture_density"], seed=i)

        # Texture color (slightly lighter than base)
        base_rgb = np.array(plt.matplotlib.colors.to_rgb(layer["color"]))
        texture_rgb = np.clip(base_rgb + 0.15, 0, 1)

        ax.scatter(x_tex, y_tex, s=0.5, c=[texture_rgb],
                  alpha=0.6, zorder=2)

        # Add rim lighting effect (backlit)
        rim_intensity = 0.4 if layer["name"] == "Vishnu Basement Rocks" else 0.25
        add_rim_lighting(ax, 0, y_bottom, 20, thickness, rim_intensity)

        # Add stratification lines for sedimentary layers
        if "Strata" in layer["name"] or "Layers" in layer["name"] or "Deposits" in layer["name"]:
            num_lines = int(thickness * 3)
            for j in range(num_lines):
                y_line = y_bottom + (j + 0.5) * thickness / num_lines
                line_color = np.clip(base_rgb - 0.1, 0, 1)
                ax.plot([0, 20], [y_line, y_line],
                       color=line_color, linewidth=0.5, alpha=0.4, zorder=3)

        # Add crystalline texture for Vishnu Basement Rocks
        if layer["name"] == "Vishnu Basement Rocks":
            # Add angular fragments to represent metamorphic/igneous texture
            for _ in range(15):
                np.random.seed(frame + _)
                x_pos = np.random.uniform(0.5, 19.5)
                y_pos = np.random.uniform(y_bottom + 0.2, y_top - 0.2)
                size = np.random.uniform(0.2, 0.5)

                # Create irregular polygon (crystal-like)
                angles = np.random.uniform(0, 2*np.pi, 6)
                radii = np.random.uniform(size*0.5, size, 6)
                x_verts = x_pos + radii * np.cos(angles)
                y_verts = y_pos + radii * np.sin(angles)

                poly = Polygon(list(zip(x_verts, y_verts)),
                              facecolor=np.clip(base_rgb + 0.2, 0, 1),
                              edgecolor=(1, 0.9, 0.7, 0.3),
                              linewidth=0.5, zorder=4)
                ax.add_patch(poly)

        # Layer labels
        label_alpha = 0.9
        label_size = 14

        # Increase label prominence for Vishnu Basement Rocks as we zoom in
        if layer["name"] == "Vishnu Basement Rocks":
            label_alpha = 0.5 + 0.5 * ease
            label_size = 14 + 8 * ease

        text = ax.text(1, y_bottom + thickness/2, layer["name"],
                      fontsize=label_size,
                      color='white',
                      alpha=label_alpha,
                      verticalalignment='center',
                      fontweight='bold' if layer["name"] == "Vishnu Basement Rocks" else 'normal',
                      zorder=20)

        # Add text outline for better visibility
        text.set_path_effects([
            path_effects.Stroke(linewidth=3, foreground='black', alpha=0.8),
            path_effects.Normal()
        ])

    # Add depth scale on the right
    depth_x = 19
    scale_alpha = 0.7 * (1 - ease * 0.5)
    for layer in layers:
        y_pos = layer["y_start"] + layer["thickness"]/2
        depth_km = (10 - layer["y_start"]) * 0.5  # Approximate depth in km

        ax.text(depth_x, y_pos, f'{depth_km:.1f} km',
               fontsize=9, color='white', alpha=scale_alpha,
               verticalalignment='center', horizontalalignment='right',
               zorder=20)

    # Add title with fade in
    title_alpha = min(1.0, frame / (fps * 2))
    title_text = ax.text(10, ax.get_ylim()[1] * 0.95,
                        'EARTH\'S CRUST CROSS-SECTION',
                        fontsize=20, color='white', alpha=title_alpha,
                        horizontalalignment='center', fontweight='bold',
                        zorder=30)
    title_text.set_path_effects([
        path_effects.Stroke(linewidth=4, foreground='black', alpha=0.8),
        path_effects.Normal()
    ])

    # Add subtitle in later frames focusing on Vishnu Basement Rocks
    if progress > 0.5:
        subtitle_alpha = (progress - 0.5) * 2
        subtitle = ax.text(10, ax.get_ylim()[0] * 0.9,
                          'Vishnu Basement Rocks: 1.7 Billion Years Old',
                          fontsize=14, color='#FFD700', alpha=subtitle_alpha,
                          horizontalalignment='center', fontweight='bold',
                          style='italic', zorder=30)
        subtitle.set_path_effects([
            path_effects.Stroke(linewidth=3, foreground='black', alpha=0.8),
            path_effects.Normal()
        ])

    return []

# Create animation
print("Creating animation...")
anim = animation.FuncAnimation(fig, animate, init_func=init,
                              frames=total_frames, interval=1000/fps,
                              blit=False)

# Save animation as MP4
output_file = 'earth_crust_animation.mp4'
print(f"Saving animation to {output_file}...")

writer = animation.FFMpegWriter(fps=fps, bitrate=5000,
                                codec='libx264',
                                extra_args=['-pix_fmt', 'yuv420p'])

anim.save(output_file, writer=writer, dpi=150)
print(f"Animation saved successfully to {output_file}")

plt.close()
