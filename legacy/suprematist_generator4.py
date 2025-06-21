import rhinoscriptsyntax as rs
import random
import math

def add_grounded_box(center, width, depth, height):
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

def generate_pyramidal_ground_mass(base_point=(0,0,0), blocks_count=30, base_size=10):
    blocks = []
    centers = []

    # Initial central block
    w = base_size * random.uniform(0.9, 1.2)
    d = base_size * random.uniform(0.9, 1.2)
    h = base_size * random.uniform(10, 14)
    z = 0
    center = base_point
    base_block = add_grounded_box(center, w, d, h)
    blocks.append(base_block)
    centers.append(center)

    # Grow mass around it
    for _ in range(blocks_count - 1):
        parent_index = random.randint(0, len(blocks) - 1)
        parent_box = blocks[parent_index]
        bb = rs.BoundingBox(parent_box)
        if not bb: continue

        pw = abs(bb[1][0] - bb[0][0])
        pd = abs(bb[3][1] - bb[0][1])

        new_w = base_size * random.uniform(0.8, 1.2)
        new_d = base_size * random.uniform(0.8, 1.2)

        direction = random.choice(["left", "right", "front", "back"])
        if direction == "left":
            cx = bb[0][0] - new_w / 2
            cy = (bb[0][1] + bb[3][1]) / 2
        elif direction == "right":
            cx = bb[1][0] + new_w / 2
            cy = (bb[1][1] + bb[2][1]) / 2
        elif direction == "front":
            cx = (bb[0][0] + bb[1][0]) / 2
            cy = bb[0][1] - new_d / 2
        else:  # back
            cx = (bb[3][0] + bb[2][0]) / 2
            cy = bb[3][1] + new_d / 2

        new_center = (cx, cy, 0)
        centers.append(new_center)

        # Calculate height based on distance to main center
        dx = new_center[0] - base_point[0]
        dy = new_center[1] - base_point[1]
        dist = math.sqrt(dx**2 + dy**2)

        max_radius = base_size * 5  # controls pyramid spread
        t = max(0.05, 1 - dist / max_radius)  # closer = taller
        new_h = base_size * random.uniform(5, 14) * t

        new_box = add_grounded_box(new_center, new_w, new_d, new_h)
        blocks.append(new_box)

    unioned = rs.BooleanUnion(blocks)
    return unioned if unioned else blocks

def generate_pyramidal_city(rows=6, cols=6, spacing=100):
    for i in range(rows):
        for j in range(cols):
            x = i * spacing
            y = j * spacing
            generate_pyramidal_ground_mass((x, y, 0), blocks_count=random.randint(20, 35), base_size=10)

generate_pyramidal_city()
