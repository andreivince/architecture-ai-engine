import rhinoscriptsyntax as rs
import random
import os
import time
import json
import shutil
import math

# --- CONFIG ---
NUM_VARIATIONS = 5
CELL_SIZE = 2.0
LAYER_HEIGHT = 1.0
MAX_BASE = 12
MAX_LAYERS = 30
MAX_VOXELS = 400

BIRTH_OPTIONS = [2, 3]
SURV_MIN_OPTIONS = [2, 3]
SURV_MAX_OPTIONS = [4, 5, 6]

# --- NEW: Grid layout configuration ---
GRID_SPACING = (MAX_BASE * CELL_SIZE) * 1.5 # Spacing between items in the final grid

# --- IMPORTANT: SET YOUR OUTPUT DIRECTORY ---
ROOT_DIR = "/Users/andreivince/Desktop/architecture-ai-engine/images_CA_Andrei"
os.makedirs(ROOT_DIR, exist_ok=True)

# --- UTILITIES ---

def compute_next(g, b, smin, smax):
    """Computes the next generation of the cellular automaton."""
    w, h = len(g), len(g[0])
    nxt = [[0] * h for _ in range(w)]
    for x in range(w):
        for y in range(h):
            cnt = sum(g[x + dx][y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if not (dx == dy == 0) and 0 <= x + dx < w and 0 <= y + dy < h)
            nxt[x][y] = 1 if (g[x][y] and smin <= cnt <= smax) or (not g[x][y] and cnt >= b) else 0
    return nxt

def classify_shape(b, smin, smax, layers, vox):
    """Classifies the shape of the generated building based on its parameters."""
    if smin <= 2 and smax >= 6: return "fragmented"
    if layers >= 25 and b >= 3: return "tapered"
    if vox >= 380: return "dense"
    if layers >= 20 and vox < 300: return "eroded"
    return "mixed"

def get_bounding_box_center_coords(bbox_points):
    """Calculates the center coords of a bounding box from its 8 corner points."""
    if not bbox_points or len(bbox_points) < 8: return None
    min_pt, max_pt = bbox_points[0], bbox_points[6]
    return ((min_pt[0] + max_pt[0]) / 2.0,
            (min_pt[1] + max_pt[1]) / 2.0,
            (min_pt[2] + max_pt[2]) / 2.0)

def setup_twopoint_perspective_view(target_point, camera_distance, building_height, lens_length):
    """Sets up a dynamic, elevated two-point perspective view."""
    view_z = building_height * 0.5
    camera_location = (target_point[0] - camera_distance, target_point[1] - camera_distance, view_z)
    target_location = list(target_point)
    target_location[2] = view_z

    rs.Command("_-SetActiveViewport Perspective", False)
    rs.ViewCameraTarget(camera=camera_location, target=target_location)
    rs.Command("_-Lens " + str(lens_length), False)

def capture_view(filepath):
    """Captures the current view to a file in Shaded mode."""
    rs.UnselectAllObjects()
    rs.Command("_-SetDisplayMode Mode=Shaded _Enter", False)
    
    command = (
        f"-_ViewCaptureToFile \"{filepath}\" "
        "Width=1024 Height=1024 "
        "LockAspectRatio=No "
        "TransparentBackground=Yes "
        "_Enter"
    )
    rs.Command(command, False)
    time.sleep(0.1)

# --- MAIN ---
rs.EnableRedraw(False)
rs.DeleteObjects(rs.AllObjects()) # Clean slate before starting

grid_cols = int(math.ceil(NUM_VARIATIONS**0.5))
all_tower_layers = [] # List to keep track of all created tower layers

for idx in range(NUM_VARIATIONS):
    layer_name = f"T{idx}"
    if rs.IsLayer(layer_name):
        rs.PurgeLayer(layer_name)
    rs.AddLayer(layer_name)
    all_tower_layers.append(layer_name)
    
    cell_centers = []
    current_seed = 42 + idx
    
    random.seed(current_seed)
    b = random.choice(BIRTH_OPTIONS)
    smin = random.choice(SURV_MIN_OPTIONS)
    smax = random.choice(SURV_MAX_OPTIONS)
    xc = random.randint(4, MAX_BASE)
    yc = random.randint(4, MAX_BASE)
    layers = random.randint(10, MAX_LAYERS)

    while True:
        grid = [[random.choice([0, 1]) for _ in range(yc)] for _ in range(xc)]
        if sum(map(sum, grid)) >= 0.5 * xc * yc: break

    vox, building_objs = 0, []
    actual_layers_created = 0
    
    for z in range(layers):
        for i in range(xc):
            for j in range(yc):
                if grid[i][j]:
                    x0, y0, z0 = i * CELL_SIZE, j * CELL_SIZE, z * LAYER_HEIGHT
                    corners = [(x0,y0,z0), (x0+CELL_SIZE,y0,z0), (x0+CELL_SIZE,y0+CELL_SIZE,z0), (x0,y0+CELL_SIZE,z0), (x0,y0,z0+LAYER_HEIGHT), (x0+CELL_SIZE,y0,z0+LAYER_HEIGHT), (x0+CELL_SIZE,y0+CELL_SIZE,z0+LAYER_HEIGHT), (x0,y0+CELL_SIZE,z0+LAYER_HEIGHT)]
                    building_objs.append(rs.AddBox(corners))
                    
                    center_x, center_y, center_z = x0+CELL_SIZE/2.0, y0+CELL_SIZE/2.0, z0+LAYER_HEIGHT/2.0
                    cell_centers.append([center_x, center_y, center_z])
                    
                    vox += 1
                    if vox >= MAX_VOXELS: break
            if vox >= MAX_VOXELS: break
        
        if vox >= MAX_VOXELS: actual_layers_created = z + 1; break
        grid = compute_next(grid, b, smin, smax)
        if not any(map(sum, grid)): actual_layers_created = z + 1; break
        actual_layers_created = z + 1

    if not building_objs:
        print(f"Tower {idx:03d} resulted in no geometry. Skipping.")
        continue

    rs.ObjectLayer(building_objs, layer_name)
    
    bbox = rs.BoundingBox(building_objs)
    if bbox:
        move_vector = rs.VectorSubtract((0, 0, 0), ((bbox[0][0] + bbox[6][0])/2, (bbox[0][1] + bbox[6][1])/2, bbox[0][2]))
        rs.MoveObjects(building_objs, move_vector)
    
    # --- IMAGE CAPTURE STAGE ---
    
    for l in all_tower_layers:
        if l != layer_name:
            rs.LayerVisible(l, False)
    
    # --- MODIFIED: This section is now fixed ---
    ground_plane_size = (MAX_BASE * CELL_SIZE) * 5.0
    ground_plane = rs.AddPlaneSurface(rs.WorldXYPlane(), ground_plane_size, ground_plane_size)
    if ground_plane:
        # Move the plane by a vector to center it at the origin
        plane_origin_vector = (-ground_plane_size / 2.0, -ground_plane_size / 2.0, 0)
        rs.MoveObject(ground_plane, plane_origin_vector)
    
    tower_dir = os.path.join(ROOT_DIR, f"tower_{idx:03d}"); os.makedirs(tower_dir, exist_ok=True)

    tower_bbox_at_origin = rs.BoundingBox(building_objs)
    if tower_bbox_at_origin:
        target_coords = get_bounding_box_center_coords(tower_bbox_at_origin)
        if target_coords:
            building_height = tower_bbox_at_origin[6][2] - tower_bbox_at_origin[0][2]
            cam_dist = max(tower_bbox_at_origin[6][0]-tower_bbox_at_origin[0][0], tower_bbox_at_origin[6][1]-tower_bbox_at_origin[0][1]) * 2.2
            
            setup_twopoint_perspective_view(target_coords, cam_dist, building_height, 50)
            
            filepath = os.path.join(tower_dir, "perspective.png")
            capture_view(filepath)
    
    if ground_plane: rs.DeleteObject(ground_plane)

    for l in all_tower_layers:
        rs.LayerVisible(l, True)

    # --- JSON SAVING ---
    output_data = { "tower_info": { "ID": idx, "unit_cell_size": CELL_SIZE, "layer_height": LAYER_HEIGHT, "actual_layers_created": actual_layers_created, "total_cells": vox, "seed": current_seed, "prompt": "WILL Be pasted from GPT" }, "cell_centers": cell_centers }
    with open(os.path.join(tower_dir, "params.json"), "w") as fp:
        json.dump(output_data, fp, indent=2)

    # --- FINAL PLACEMENT IN GRID ---
    grid_row = idx // grid_cols
    grid_col = idx % grid_cols
    grid_position = (grid_col * GRID_SPACING, grid_row * GRID_SPACING, 0)
    
    rs.MoveObjects(building_objs, rs.VectorCreate(grid_position, (0,0,0)))
    
    dot_position = (grid_position[0], grid_position[1], 0)
    dot = rs.AddTextDot(layer_name, dot_position)
    if dot: rs.ObjectLayer(dot, layer_name)

    print(f"Generated, captured, and placed tower {idx:03d} on layer '{layer_name}'")

# --- FINAL ---
rs.Command("_-Zoom _Extents", False)
rs.EnableRedraw(True)

print(f"\nProcess complete. Generated {NUM_VARIATIONS} towers in {ROOT_DIR}")
print("The Rhino scene now contains all variations arranged in a grid.")
print("You may now save the .3dm file.")