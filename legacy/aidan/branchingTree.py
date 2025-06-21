import rhinoscriptsyntax as rs
import random

def add_voxel(center, size):
    x, y, z = center
    half = size / 2.0
    corners = [
        [x - half, y - half, z - half],
        [x + half, y - half, z - half],
        [x + half, y + half, z - half],
        [x - half, y + half, z - half],
        [x - half, y - half, z + half],
        [x + half, y - half, z + half],
        [x + half, y + half, z + half],
        [x - half, y + half, z + half]
    ]
    return rs.AddBox(corners)

def recursive_branch_voxel(center, direction, size, depth, max_depth, taper):
    if depth > max_depth:
        return

    # taper scale based on depth
    scale_factor = (1 - (depth / max_depth)) * taper + (1 - taper)
    actual_size = size * scale_factor

    add_voxel(center, actual_size)

    # Primary downward direction
    next_center = [
        center[0] + direction[0] * size,
        center[1] + direction[1] * size,
        center[2] + direction[2] * size
    ]

    # Keep main branch going
    recursive_branch_voxel(next_center, direction, size, depth + 1, max_depth, taper)

    # Branch probability decreases over depth
    if random.random() < 0.6 * (1 - depth / max_depth):
        num_branches = random.choice([1, 2])
        for _ in range(num_branches):
            dx = random.uniform(-0.5, 0.5)
            dy = random.uniform(-0.5, 0.5)
            dz = -1  # always grow downward

            new_dir = rs.VectorUnitize([dx, dy, dz])
            new_center = [
                center[0] + new_dir[0] * size,
                center[1] + new_dir[1] * size,
                center[2] + new_dir[2] * size
            ]

            recursive_branch_voxel(new_center, new_dir, size, depth + 1, max_depth, taper)

# Clear and build
rs.EnableRedraw(False)
origin = [0, 0, 0]
initial_direction = [0, 0, -1]
voxel_size = 4
max_recursion = 15
taper_amount = 0.6  

recursive_branch_voxel(origin, initial_direction, voxel_size, 0, max_recursion, taper_amount)
rs.EnableRedraw(True)
