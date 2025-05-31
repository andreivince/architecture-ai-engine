"""
Re‑worked voxel‑tower generator with:
  • Pure‑numpy .npy output per sample
  • Lightweight JSON (no embedded grid)
  • Optional Rhino geometry toggle
  • Clean flag layout for shape functions
  • Ready for large‑scale, headless generation

Run inside Rhino OR pure CPython (geometry disabled).
"""
import rhinoscriptsyntax as rs  # Safe even in CPython; fails gracefully if Rhino absent
import numpy as np
import json, os, random, sys, inspect

# ------------------------- GLOBAL CONFIG -------------------------
GRID_RESOLUTION = (32, 32, 32)   # (X,Y,Z) voxel grid size
CELL_SIZE       = 1.0            # Rhino unit per voxel
SPACING_FACTOR  = 2.0            # World‑space gap between towers when geometry enabled

# Toggle: turn off to run headless in CPython
GENERATE_GEOMETRY = True if 'rs' in sys.modules and rs.DocumentPath() else False

# ------------------------- HELPERS -------------------------------

def _new_grid():
    """Return empty 3‑D numpy grid (uint8)."""
    return np.zeros(GRID_RESOLUTION, dtype=np.uint8)   # z‑axis is last index


def _stamp_cuboid(grid, x, y, z, w, d, h, offset_x, offset_y):
    """Fill grid with 1s and optionally drop a Rhino box per voxel."""
    w = int(w); d = int(d); h = int(h)
    gx_max, gy_max, gz_max = GRID_RESOLUTION
    voxels = 0
    for i in range(w):
        for j in range(d):
            for k in range(h):
                gx, gy, gz = x+i, y+j, z+k
                if 0<=gx<gx_max and 0<=gy<gy_max and 0<=gz<gz_max:
                    if grid[gx,gy,gz] == 0:
                        grid[gx,gy,gz] = 1; voxels += 1
                    if GENERATE_GEOMETRY:
                        rhx = offset_x + gx*CELL_SIZE
                        rhy = offset_y + gy*CELL_SIZE
                        rhz = gz*CELL_SIZE
                        rs.AddBox([
                            (rhx,          rhy,          rhz),
                            (rhx+CELL_SIZE, rhy,          rhz),
                            (rhx+CELL_SIZE, rhy+CELL_SIZE, rhz),
                            (rhx,          rhy+CELL_SIZE, rhz),
                            (rhx,          rhy,          rhz+CELL_SIZE),
                            (rhx+CELL_SIZE, rhy,          rhz+CELL_SIZE),
                            (rhx+CELL_SIZE, rhy+CELL_SIZE, rhz+CELL_SIZE),
                            (rhx,          rhy+CELL_SIZE, rhz+CELL_SIZE)
                        ])
    return voxels

# ------------------------- SHAPE GENERATORS ----------------------

def gen_I(num_floors, stem_len, stem_wid, off_x=0, off_y=0):
    grid=_new_grid()
    sx=(GRID_RESOLUTION[0]-stem_wid)//2
    sy=(GRID_RESOLUTION[1]-stem_len)//2
    vox=_stamp_cuboid(grid,sx,sy,0,stem_wid,stem_len,num_floors,off_x,off_y)
    return grid,{"shape":"I","floors":num_floors,"stem_len":stem_len,"stem_wid":stem_wid,"voxels":vox}

def gen_L(num_floors, arm_y, arm_x, thick, off_x=0, off_y=0):
    grid=_new_grid(); vox=0
    sx=(GRID_RESOLUTION[0]-arm_x)//2
    sy=(GRID_RESOLUTION[1]-arm_y)//2
    vox+=_stamp_cuboid(grid,sx,sy,0,thick,arm_y,num_floors,off_x,off_y)
    vox+=_stamp_cuboid(grid,sx+thick,sy,0,arm_x-thick,thick,num_floors,off_x,off_y)
    return grid,{"shape":"L","floors":num_floors,"arm_y":arm_y,"arm_x":arm_x,"thickness":thick,"voxels":vox}

def gen_O(num_floors, out_y, out_x, thick, off_x=0, off_y=0):
    grid=_new_grid(); vox=0
    sx=(GRID_RESOLUTION[0]-out_x)//2
    sy=(GRID_RESOLUTION[1]-out_y)//2
    vox+=_stamp_cuboid(grid,sx,sy,0,thick,out_y,num_floors,off_x,off_y)
    vox+=_stamp_cuboid(grid,sx+out_x-thick,sy,0,thick,out_y,num_floors,off_x,off_y)
    vox+=_stamp_cuboid(grid,sx+thick,sy,0,out_x-2*thick,thick,num_floors,off_x,off_y)
    vox+=_stamp_cuboid(grid,sx+thick,sy+out_y-thick,0,out_x-2*thick,thick,num_floors,off_x,off_y)
    return grid,{"shape":"O","floors":num_floors,"out_y":out_y,"out_x":out_x,"thickness":thick,"voxels":vox}

def gen_U(num_floors, arm_y, base_x, thick, off_x=0, off_y=0):
    grid=_new_grid(); vox=0
    sx=(GRID_RESOLUTION[0]-base_x)//2
    sy=(GRID_RESOLUTION[1]-arm_y)//2
    vox+=_stamp_cuboid(grid,sx,sy,0,base_x,thick,num_floors,off_x,off_y)
    vox+=_stamp_cuboid(grid,sx,sy+thick,0,thick,arm_y-thick,num_floors,off_x,off_y)
    vox+=_stamp_cuboid(grid,sx+base_x-thick,sy+thick,0,thick,arm_y-thick,num_floors,off_x,off_y)
    return grid,{"shape":"U","floors":num_floors,"arm_y":arm_y,"base_x":base_x,"thickness":thick,"voxels":vox}

SHAPE_FUNCS={"I":gen_I,"L":gen_L,"O":gen_O,"U":gen_U}

# ------------------------- DATASET GENERATOR ---------------------

def generate_dataset(n=100, out_dir="voxel_dataset", geom=GENERATE_GEOMETRY):
    global GENERATE_GEOMETRY
    GENERATE_GEOMETRY=geom  # override per call

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    vox_dir=os.path.join(out_dir,"voxels"); lbl_dir=os.path.join(out_dir,"labels")
    os.makedirs(vox_dir,exist_ok=True); os.makedirs(lbl_dir,exist_ok=True)

    if GENERATE_GEOMETRY: rs.EnableRedraw(False)

    cols=int(n**0.5)+1
    space_x=GRID_RESOLUTION[0]*CELL_SIZE*SPACING_FACTOR
    space_y=GRID_RESOLUTION[1]*CELL_SIZE*SPACING_FACTOR

    for idx in range(n):
        shape=random.choice(list(SHAPE_FUNCS))
        floors=random.randint(5,GRID_RESOLUTION[2]-2)
        thick=random.randint(2,(min(GRID_RESOLUTION[:2])//2)-1)
        if shape=="I":
            sw=random.randint(thick,GRID_RESOLUTION[0]-2)
            sl=random.randint(thick,GRID_RESOLUTION[1]-2)
            gen=SHAPE_FUNCS[shape]
            off_x=(idx%cols)*space_x; off_y=(idx//cols)*space_y
            grid,meta=gen(floors,sl,sw,off_x,off_y)
        elif shape=="L":
            ax=random.randint(thick+1,GRID_RESOLUTION[0]-2)
            ay=random.randint(thick+1,GRID_RESOLUTION[1]-2)
            gen=SHAPE_FUNCS[shape]
            off_x=(idx%cols)*space_x; off_y=(idx//cols)*space_y
            grid,meta=gen(floors,ay,ax,thick,off_x,off_y)
        elif shape=="O":
            ox=random.randint(2*thick+1,GRID_RESOLUTION[0]-2)
            oy=random.randint(2*thick+1,GRID_RESOLUTION[1]-2)
            gen=SHAPE_FUNCS[shape]
            off_x=(idx%cols)*space_x; off_y=(idx//cols)*space_y
            grid,meta=gen(floors,oy,ox,thick,off_x,off_y)
        else:  # U
            bx=random.randint(2*thick+1,GRID_RESOLUTION[0]-2)
            ay=random.randint(thick+1,GRID_RESOLUTION[1]-2)
            gen=SHAPE_FUNCS[shape]
            off_x=(idx%cols)*space_x; off_y=(idx//cols)*space_y
            grid,meta=gen(floors,ay,bx,thick,off_x,off_y)

        # ---------- save files ----------
        base=f"{shape}_{idx:04d}"
        npy_path=os.path.join(vox_dir,base+".npy")
        np.save(npy_path, grid)
        meta["voxel_path"] = os.path.relpath(npy_path, lbl_dir)
        json_path=os.path.join(lbl_dir,base+".json")
        with open(json_path,'w') as f: json.dump(meta,f,indent=4)

        if idx%max(1,n//10)==0 or idx==n-1:
            print(f"saved {idx+1}/{n}")

    if GENERATE_GEOMETRY:
        rs.EnableRedraw(True); rs.ZoomExtentsAll()
    print("Dataset complete ->", out_dir)

# ------------------------- OPTIONAL MASKED SET -------------------

def create_masked_variants(src_vox_dir, pct_mask=0.3):
    """Create *_mask.npy files with random holes for evaluation."""
    for f in os.listdir(src_vox_dir):
        if not f.endswith('.npy'): continue
        full=os.path.join(src_vox_dir,f)
        vox=np.load(full)
        mask=np.random.rand(*vox.shape) < pct_mask
        vox_masked=vox.copy(); vox_masked[mask]=0
        np.save(full.replace('.npy','_mask.npy'), vox_masked)

# ------------------------- MAIN (inside Rhino OR CLI) -----------
if __name__=="__main__":
    # Example: generate 50 towers, no Rhino geometry when run outside Rhino
    generate_dataset(n=50, out_dir="voxel_dataset", geom=GENERATE_GEOMETRY)
