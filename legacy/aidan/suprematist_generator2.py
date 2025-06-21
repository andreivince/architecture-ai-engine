import rhinoscriptsyntax as rs
import random

def add_box(center, width, depth, height):
    x, y, z = center
    corner = (x - width / 2, y - depth / 2, z)
    return rs.AddBox([
        corner,
        (corner[0] + width, corner[1], corner[2]),
        (corner[0] + width, corner[1] + depth, corner[2]),
        (corner[0], corner[1] + depth, corner[2]),
        (corner[0], corner[1], corner[2] + height),
        (corner[0] + width, corner[1], corner[2] + height),
        (corner[0] + width, corner[1] + depth, corner[2] + height),
        (corner[0], corner[1] + depth, corner[2] + height)
    ])

def generate_towers(center=(0,0,0), base_width=20, base_depth=20, base_height=6, levels=6, step_back=0.8):
    x, y, z = center
    tower = []

    width = base_width
    depth = base_depth

    wing_tiers = random.randint(0, min(3, levels - 1))

    for i in range(levels):
        height = base_height * random.uniform(0.9, 1.2)
        tier_center = (x, y, z)
        box = add_box(tier_center, width, depth, height)
        tower.append(box)

        # Add 4-sided podium wings if this tier qualifies
        if i < wing_tiers:
            # Consistent wing dimensions for all 4 sides this tier
            wing_scale_x = random.uniform(0.3, 0.6)
            wing_scale_y = random.uniform(0.3, 0.6)
            wing_height = height * random.uniform(0.5, 1.0)

            # Left & Right wings
            wing_w = width * wing_scale_x
            wing_d = depth * wing_scale_y
            dx = (width + wing_w) / 2
            tower.append(add_box((x + dx, y, z), wing_w, wing_d, wing_height))
            tower.append(add_box((x - dx, y, z), wing_w, wing_d, wing_height))

            # Front & Back wings
            wing_w_fb = width * wing_scale_y
            wing_d_fb = depth * wing_scale_x
            dy = (depth + wing_d_fb) / 2
            tower.append(add_box((x, y + dy, z), wing_w_fb, wing_d_fb, wing_height))
            tower.append(add_box((x, y - dy, z), wing_w_fb, wing_d_fb, wing_height))

        # Move up for next tier
        z += height
        width *= step_back
        depth *= step_back

    return tower

def generate_tower_city(rows=3, cols=3, spacing=90):
    for i in range(rows):
        for j in range(cols):
            x = i * spacing
            y = j * spacing
            center = (x, y, 0)
            base_width = random.uniform(18, 25)
            base_depth = random.uniform(18, 25)
            base_height = random.uniform(5, 8)
            levels = random.randint(6, 9)
            step_back = random.uniform(0.75, 0.85)
            generate_towers(center, base_width, base_depth, base_height, levels, step_back)

generate_tower_city(rows=10, cols=10, spacing=70)
