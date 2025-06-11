import rhinoscriptsyntax as rs
import random
import math


# Parameters

voxel_size = 10
grid_limit = 25  # Space range in each axis
max_recursion = 15
taper_amount = 0.6
number_of_trees = 20


# Voxel Grid Management

occupied_voxels = set()  # Set of x y z voxel indices

def point_to_voxel_index(pt):
    return (
        int(round(pt[0] / voxel_size)),
        int(round(pt[1] / voxel_size)),
        int(round(pt[2] / voxel_size))
    )

def voxel_index_to_center(index):
    return [
        index[0] * voxel_size,
        index[1] * voxel_size,
        index[2] * voxel_size
    ]

def is_voxel_occupied(index):
    return index in occupied_voxels

def occupy_voxel(index):
    occupied_voxels.add(index)

def add_voxel_at_index(index, size):
    center = voxel_index_to_center(index)
    half = size / 2.0
    x, y, z = center
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
    rs.AddBox(corners)


# Recursive Branching

def recursive_branch_voxel(center, direction, size, depth, max_depth, taper):
    if depth > max_depth:
        return

    voxel_idx = point_to_voxel_index(center)

    if is_voxel_occupied(voxel_idx):
        return

    occupy_voxel(voxel_idx)
    scale_factor = (1 - (depth / max_depth)) * taper + (1 - taper)
    actual_size = size * scale_factor
    add_voxel_at_index(voxel_idx, actual_size)

    next_center = [
        center[0] + direction[0] * size,
        center[1] + direction[1] * size,
        center[2] + direction[2] * size
    ]

    recursive_branch_voxel(next_center, direction, size, depth + 1, max_depth, taper)

    if random.random() < 0.6 * (1 - depth / max_depth):
        num_branches = random.choice([1, 2])
        for _ in range(num_branches):
            dx = random.uniform(-0.5, 0.5)
            dy = random.uniform(-0.5, 0.5)
            dz = -1
            new_dir = rs.VectorUnitize([dx, dy, dz])
            new_center = [
                center[0] + new_dir[0] * size,
                center[1] + new_dir[1] * size,
                center[2] + new_dir[2] * size
            ]
            recursive_branch_voxel(new_center, new_dir, size, depth + 1, max_depth, taper)


# Launch Multiple Trees

def launch_multiple_trees(num_trees):
    for _ in range(num_trees):
        # Random starting point within limits
        x = random.randint(-grid_limit, grid_limit) * voxel_size
        y = random.randint(-grid_limit, grid_limit) * voxel_size
        z = 0  # Start from ground plane

        origin = [x, y, z]

        # Slightly randomized downward direction
        dx = random.uniform(-0.3, 0.3)
        dy = random.uniform(-0.3, 0.3)
        dz = -1
        direction = rs.VectorUnitize([dx, dy, dz])

        recursive_branch_voxel(origin, direction, voxel_size, 0, max_recursion, taper_amount)


# Run

rs.EnableRedraw(False)
launch_multiple_trees(number_of_trees)
rs.EnableRedraw(True)
