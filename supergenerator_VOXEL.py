# Andrei SUPER GENERATOR
import rhinoscriptsyntax as rs
import random

TOWER_COUNT_X = 2
TOWER_COUNT_Y = 2
cell_size = 2.0
layer_height = 1.0
max_base = 12
max_layers = 30
max_voxels_per_tower = 400 # MAKE MORE LIGHTWEIGHT 
tower_spacing = max_base * cell_size + 6

rs.EnableRedraw(False)
rs.DeleteObjects(rs.AllObjects())  

def compute_next(grid, birth, surv_min, surv_max):
    x_count = len(grid)
    y_count = len(grid[0])
    new = [[0]*y_count for _ in range(x_count)]
    for i in range(x_count):
        for j in range(y_count):
            cnt = 0
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: continue
                    nx, ny = i+dx, j+dy
                    if 0<=nx<x_count and 0<=ny<y_count:
                        cnt += grid[nx][ny]
            if grid[i][j] == 1:
                if surv_min <= cnt <= surv_max:
                    new[i][j] = 1
            else:
                if cnt >= birth:
                    new[i][j] = 1
    return new

for tx in range(TOWER_COUNT_X):
    for ty in range(TOWER_COUNT_Y):
        birth_threshold = random.choice([2, 3])
        survive_min    = random.choice([2, 3])
        survive_max    = random.choice([4, 5, 6])
        x_count        = random.randint(4, max_base)
        y_count        = random.randint(4, max_base)
        layers         = random.randint(10, max_layers)

        while True:
            seed_grid = [[random.choice([0,1]) for _ in range(y_count)] for _ in range(x_count)]
            alive = sum(sum(row) for row in seed_grid)
            if alive >= 0.5 * x_count * y_count:
                grid = seed_grid
                break

        base_x_offset = tx * tower_spacing
        base_y_offset = ty * tower_spacing
        voxel_count = 0

        for z in range(layers):
            for i in range(x_count):
                for j in range(y_count):
                    if grid[i][j] == 1:
                        x0 = base_x_offset + i * cell_size
                        y0 = base_y_offset + j * cell_size
                        z0 = z * layer_height
                        x1 = x0 + cell_size
                        y1 = y0 + cell_size
                        z1 = z0 + layer_height
                        corners = [
                            (x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0),
                            (x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1)
                        ]
                        rs.AddBox(corners)
                        voxel_count += 1
                        if voxel_count >= max_voxels_per_tower:
                            break
                if voxel_count >= max_voxels_per_tower:
                    break
            if voxel_count >= max_voxels_per_tower:
                break
            grid = compute_next(grid, birth_threshold, survive_min, survive_max)
            if not any(any(row) for row in grid):
                break

        # Descriptive prompt generation added in this version this will help with training
        if survive_min <= 2 and survive_max >= 6:
            shape_type = "fragmented"
        elif layers >= 25 and birth_threshold >= 3:
            shape_type = "tapered"
        elif voxel_count >= 380:
            shape_type = "dense"
        elif layers >= 20 and voxel_count < 300:
            shape_type = "eroded"
        else:
            shape_type = "mixed"

        prompt = f"CA_tower, {shape_type} form, b={birth_threshold}, s={survive_min}–{survive_max}, {layers} layers"
        label_pos = (base_x_offset, base_y_offset - 4, 0)
        rs.AddTextDot(prompt, label_pos)

rs.EnableRedraw(True)
