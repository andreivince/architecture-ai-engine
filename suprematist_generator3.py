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

def generate_suprematist_tower(base_point=(0,0,0), levels=12, base_size=10):
    placed_blocks = []

    # First base block on ground
    base_w = base_size * random.uniform(0.6, 1.2)
    base_d = base_size * random.uniform(0.6, 1.2)
    base_h = base_size * random.uniform(0.6, 1.2)
    base_center = (base_point[0], base_point[1], base_point[2])
    first_block = add_box(base_center, base_w, base_d, base_h)
    placed_blocks.append(first_block)

    # For each level, place smaller blocks that intersect previous level
    current_z = base_point[2]
    for level in range(1, levels):
        new_blocks = []
        for _ in range(random.randint(2, 4)):
            prev = rs.BoundingBox(placed_blocks[-1])
            if not prev: continue
            prev_center = rs.PointDivide(rs.PointAdd(prev[0], prev[6]), 2)

            shrink = 1.0 - (level / float(levels))
            w = base_size * random.uniform(0.3, 1.0) * shrink
            d = base_size * random.uniform(0.3, 1.0) * shrink
            h = base_size * random.uniform(0.5, 1.5)

            offset_x = random.uniform(-base_size * 0.3, base_size * 0.3) * shrink
            offset_y = random.uniform(-base_size * 0.3, base_size * 0.3) * shrink
            new_center = (
                prev_center.X + offset_x,
                prev_center.Y + offset_y,
                prev_center.Z + h * 0.5
            )

            new_box = add_box(new_center, w, d, h)
            new_blocks.append(new_box)

        placed_blocks.extend(new_blocks)

    # Merge all into one unioned solid
    unioned = rs.BooleanUnion(placed_blocks)
    return unioned if unioned else placed_blocks

def generate_tower_grid(rows=10, cols=10, spacing=90, min_levels=10, max_levels=18, min_size=8, max_size=15):
    for i in range(rows):
        for j in range(cols):
            x = i * spacing
            y = j * spacing
            levels = random.randint(min_levels, max_levels)
            size = random.uniform(min_size, max_size)
            generate_suprematist_tower((x, y, 0), levels, size)

generate_tower_grid(rows=10, cols=10, spacing=90)
