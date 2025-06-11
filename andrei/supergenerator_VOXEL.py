import rhinoscriptsyntax as rs, random, os, time, json

# —— CONFIG ———————————————————————————————————————————
NUM_VARIATIONS      = 5
CELL_SIZE           = 2.0
LAYER_HEIGHT        = 1.0
MAX_BASE            = 12
MAX_LAYERS          = 30
MAX_VOXELS          = 400

GRID_COLS           = 10
SPACING             = (MAX_BASE * CELL_SIZE + 6.0) * 2

BIRTH_OPTIONS       = [2, 3]
SURV_MIN_OPTIONS    = [2, 3]
SURV_MAX_OPTIONS    = [4, 5, 6]

ROOT_DIR            = "/Users/andreivince/Desktop/architecture-ai-engine/images_CA_Andrei" # CHANGE FOR WHERE YOU WANT PITCURES
os.makedirs(ROOT_DIR, exist_ok=True)

# —— UTILITIES ————————————————————————————————————————

def compute_next(g, b, smin, smax):
    w, h = len(g), len(g[0])
    nxt = [[0]*h for _ in range(w)]
    for x in range(w):
        for y in range(h):
            cnt = sum(g[x+dx][y+dy] for dx in (-1,0,1) for dy in (-1,0,1)
                      if not (dx==dy==0) and 0<=x+dx<w and 0<=y+dy<h)
            nxt[x][y] = 1 if (g[x][y] and smin<=cnt<=smax) or (not g[x][y] and cnt>=b) else 0
    return nxt

def classify_shape(b, smin, smax, layers, vox):
    if smin<=2 and smax>=6: return "fragmented"
    if layers>=25 and b>=3: return "tapered"
    if vox>=380:           return "dense"
    if layers>=20 and vox<300: return "eroded"
    return "mixed"

# —— MAIN ————————————————————————————————————————————
rs.EnableRedraw(False)
rs.DeleteObjects(rs.AllObjects())

for idx in range(NUM_VARIATIONS):
    random.seed(42+idx) # SEED BLOCKED
    col,row = idx%GRID_COLS, idx//GRID_COLS
    base_x, base_y = col*SPACING, row*SPACING

    b  = random.choice(BIRTH_OPTIONS)
    smin = random.choice(SURV_MIN_OPTIONS)
    smax = random.choice(SURV_MAX_OPTIONS)
    xc = random.randint(4,MAX_BASE)
    yc = random.randint(4,MAX_BASE)
    layers = random.randint(10,MAX_LAYERS)

    while True:
        grid=[[random.choice([0,1]) for _ in range(yc)] for _ in range(xc)]
        if sum(map(sum,grid))>=0.5*xc*yc: break

    vox, objs = 0, []
    for z in range(layers):
        for i in range(xc):
            for j in range(yc):
                if grid[i][j]:
                    x0,y0,z0 = base_x+i*CELL_SIZE, base_y+j*CELL_SIZE, z*LAYER_HEIGHT
                    corners=[(x0,y0,z0),(x0+CELL_SIZE,y0,z0),(x0+CELL_SIZE,y0+CELL_SIZE,z0),(x0,y0+CELL_SIZE,z0),
                             (x0,y0,z0+LAYER_HEIGHT),(x0+CELL_SIZE,y0,z0+LAYER_HEIGHT),(x0+CELL_SIZE,y0+CELL_SIZE,z0+LAYER_HEIGHT),(x0,y0+CELL_SIZE,z0+LAYER_HEIGHT)]
                    objs.append(rs.AddBox(corners))
                    vox+=1
                    if vox>=MAX_VOXELS: break
            if vox>=MAX_VOXELS: break
        if vox>=MAX_VOXELS: break
        grid=compute_next(grid,b,smin,smax)
        if not any(map(sum,grid)): break

    shape=classify_shape(b,smin,smax,layers,vox)
    # rs.AddTextDot(f"tower_{idx:03d}: {shape}\nb={b}, s={smin}-{smax}, L={layers}", (base_x, base_y-4, 0))

    tower_dir=os.path.join(ROOT_DIR,f"tower_{idx:03d}")
    os.makedirs(tower_dir,exist_ok=True)

    def cap(view_cmd, filename):
        if objs: rs.SelectObjects(objs)

        rs.Command(view_cmd, False)
        time.sleep(0.05)
        rs.Command("_Zoom _Extents", False)

        rs.UnselectAllObjects()

        rs.Command("_SetDisplayMode _Shaded", False)

        if "Perspective" in view_cmd:
            rs.Command("_Zoom _Scale 0.7 _Enter", False)

        rs.Command(
            f"-_ViewCaptureToFile \"{os.path.join(tower_dir, filename)}\" "
            "Width=800 Height=800 TransparentBackground=Yes Enter",
            False
        )

    if objs: rs.SelectObjects(objs)
    cap("SetView World Front","front.png")
    cap("SetView World Back","back.png")
    cap("SetView World Right","right.png")
    cap("SetView World Left","left.png")
    cap("SetView World Top","top.png")
    cap("SetView World Perspective","iso.png")
    rs.UnselectAllObjects()

    # write params json
    meta={"id":f"tower_{idx:03d}","birth":b,"survive_min":smin,"survive_max":smax,"layers":layers,"voxels":vox,"shape":shape}
    with open(os.path.join(tower_dir,"params.json"),"w") as fp: json.dump(meta,fp,indent=2)

rs.EnableRedraw(True)
print(f"Generated {NUM_VARIATIONS} towers with 6 views + params.json each → {ROOT_DIR}")
