import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import random
import math
import os
import time

# —— CONFIG ———————————————————————————————————————————
NUM_VARIATIONS      = 100
CELL_SIZE           = 2.0
LAYER_HEIGHT        = 1.0
MAX_BASE            = 12
MAX_LAYERS          = 30
MAX_VOXELS          = 400

GRID_COLS           = 10
SPACING             = MAX_BASE * CELL_SIZE + 6.0

BIRTH_OPTIONS       = [2, 3]
SURV_MIN_OPTIONS    = [2, 3]
SURV_MAX_OPTIONS    = [4, 5, 6]

CAPTURE_PATH        = "/Users/andreivince/Desktop/architecture-ai-engine/images_CA_Andrei" # Change to where you want to save, I did manually here brutal force for fast prototype
os.makedirs(CAPTURE_PATH, exist_ok=True)

# —— UTILITIES ————————————————————————————————————————

def compute_next(grid, birth, surv_min, surv_max):
    x_count, y_count = len(grid), len(grid[0])
    nxt = [[0]*y_count for _ in range(x_count)]
    for i in range(x_count):
        for j in range(y_count):
            cnt = 0
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0:
                        continue
                    nx, ny = i+dx, j+dy
                    if 0<=nx<x_count and 0<=ny<y_count:
                        cnt += grid[nx][ny]
            if grid[i][j]:
                nxt[i][j] = 1 if surv_min <= cnt <= surv_max else 0
            else:
                nxt[i][j] = 1 if cnt >= birth else 0
    return nxt

def classify_shape(birth, surv_min, surv_max, layers, voxels):
    if surv_min <= 2 and surv_max >= 6:
        return "fragmented"
    if layers >= 25 and birth >= 3:
        return "tapered"
    if voxels >= 380:
        return "dense"
    if layers >= 20 and voxels < 300:
        return "eroded"
    return "mixed"

# —— MAIN ————————————————————————————————————————————
rs.EnableRedraw(False)
rs.DeleteObjects(rs.AllObjects())

for idx in range(NUM_VARIATIONS):
    random.seed(42 + idx)  # deterministic by index

    col = idx % GRID_COLS
    row = idx // GRID_COLS
    base_x = col * SPACING
    base_y = row * SPACING

    birth    = random.choice(BIRTH_OPTIONS)
    surv_min = random.choice(SURV_MIN_OPTIONS)
    surv_max = random.choice(SURV_MAX_OPTIONS)
    x_count  = random.randint(4, MAX_BASE)
    y_count  = random.randint(4, MAX_BASE)
    layers   = random.randint(10, MAX_LAYERS)

    # initial seed grid
    while True:
        seed = [[random.choice([0,1]) for _ in range(y_count)] for _ in range(x_count)]
        if sum(sum(r) for r in seed) >= 0.5 * x_count * y_count:
            break
    grid = seed

    voxels = 0
    objs = []
    for z in range(layers):
        for i in range(x_count):
            for j in range(y_count):
                if grid[i][j]:
                    x0 = base_x + i * CELL_SIZE
                    y0 = base_y + j * CELL_SIZE
                    z0 = z * LAYER_HEIGHT
                    corners = [
                        (x0,y0,z0), (x0+CELL_SIZE,y0,z0), (x0+CELL_SIZE,y0+CELL_SIZE,z0), (x0,y0+CELL_SIZE,z0),
                        (x0,y0,z0+LAYER_HEIGHT), (x0+CELL_SIZE,y0,z0+LAYER_HEIGHT),
                        (x0+CELL_SIZE,y0+CELL_SIZE,z0+LAYER_HEIGHT), (x0,y0+CELL_SIZE,z0+LAYER_HEIGHT)
                    ]
                    box_id = rs.AddBox(corners)
                    objs.append(box_id)
                    voxels += 1
                    if voxels >= MAX_VOXELS:
                        break
            if voxels >= MAX_VOXELS:
                break
        if voxels >= MAX_VOXELS:
            break
        grid = compute_next(grid, birth, surv_min, surv_max)
        if not any(any(r) for r in grid):
            break

    shape = classify_shape(birth, surv_min, surv_max, layers, voxels)

    label_text = f"tower_{idx:03d}: {shape}\nb={birth}, s={surv_min}-{surv_max}, L={layers}"
    rs.AddTextDot(label_text, (base_x, base_y - 4, 0))

    if objs:
        rs.SelectObjects(objs)
        rs.ZoomSelected()
        rs.UnselectAllObjects()
        time.sleep(0.2)

    img_path = os.path.join(CAPTURE_PATH, f"tower_{idx:03d}.png")
    rs.Command(f"-_ViewCaptureToFile \"{img_path}\" Width=800 Height=800 TransparentBackground=Yes Enter")

rs.EnableRedraw(True)
print(f"Generated {NUM_VARIATIONS} spaced towers and saved images to: {CAPTURE_PATH}")