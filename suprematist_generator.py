import rhinoscriptsyntax as rs
import random

def generate_suprematist_tower(base_point=(0,0,0), levels=12, base_size=10):
    blocks = []
    max_height = base_size * levels

    for level in range(levels):
        num_blocks = random.randint(3, 6)

        for _ in range(num_blocks):
            size_factor = 1.0 - (level / float(levels))
            w = base_size * random.uniform(0.3, 1.0) * size_factor
            d = base_size * random.uniform(0.3, 1.0) * size_factor
            h = base_size * random.uniform(0.8, 2.0) * (1.0 + level / levels)

            x = base_point[0] + random.uniform(-base_size, base_size) * size_factor
            y = base_point[1] + random.uniform(-base_size, base_size) * size_factor
            z = base_point[2] + level * (base_size * 0.6)

            corner = (x - w/2, y - d/2, z)
            box = rs.AddBox([
                corner,
                (corner[0] + w, corner[1], corner[2]),
                (corner[0] + w, corner[1] + d, corner[2]),
                (corner[0], corner[1] + d, corner[2]),
                (corner[0], corner[1], corner[2] + h),
                (corner[0] + w, corner[1], corner[2] + h),
                (corner[0] + w, corner[1] + d, corner[2] + h),
                (corner[0], corner[1] + d, corner[2] + h)
            ])
            blocks.append(box)

    return blocks

def generate_tower_grid(rows=3, cols=3, spacing=80, min_levels=10, max_levels=18, min_size=8, max_size=15):
    for i in range(rows):
        for j in range(cols):
            x = i * spacing
            y = j * spacing
            levels = random.randint(min_levels, max_levels)
            size = random.uniform(min_size, max_size)
            generate_suprematist_tower((x, y, 0), levels, size)

# Generate a 4x4 grid of unique towers
generate_tower_grid(rows=10, cols=10, spacing=90)
