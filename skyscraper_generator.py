import rhinoscriptsyntax as rs
import Rhino
import scriptcontext
import System
import random

def create_skyscraper(params):
    rs.DeleteObjects(rs.AllObjects())
    rs.EnableRedraw(False)

    width = params.get('width', 20.0)
    depth = params.get('depth', 20.0)
    base_height = params.get('base_height', 100.0)
    num_tiers = params.get('tiers', 3)
    tier_step = params.get('tier_step', 0.8)
    windows_per_face = params.get('windows_per_face', 5)
    include_spire = params.get('has_spire', True)

    wall_color = (180, 180, 180)
    glass_color = (100, 150, 200)
    spire_color = (80, 80, 80)

    current_x = 0
    current_y = 0
    current_z = 0
    current_width = width
    current_depth = depth

    total_geometry = []

    tier_height = base_height / num_tiers
    window_offset = 0.1
    window_thickness = 0.1

    for i in range(num_tiers):
        pt1 = (current_x, current_y, current_z)
        pt2 = (current_x + current_width, current_y + current_depth, current_z + tier_height)
        box = rs.AddBox([
            pt1,
            (pt2[0], pt1[1], pt1[2]),
            (pt2[0], pt2[1], pt1[2]),
            (pt1[0], pt2[1], pt1[2]),
            (pt1[0], pt1[1], pt2[2]),
            (pt2[0], pt1[1], pt2[2]),
            pt2,
            (pt1[0], pt2[1], pt2[2])
        ])
        if box:
            rs.ObjectColor(box, wall_color)
            total_geometry.append(box)

        win_width = current_width / windows_per_face
        win_height = tier_height / windows_per_face
        win_depth = current_depth / windows_per_face

        for row in range(windows_per_face):
            for col in range(windows_per_face):
                wz = current_z + row * win_height + win_height * 0.1
                wh = win_height * 0.8
                ww = win_width * 0.8
                wd = win_depth * 0.8

                # Front (-Y)
                wx = current_x + col * win_width + win_width * 0.1
                wy = current_y - window_offset
                pane = rs.AddBox([
                    (wx, wy, wz),
                    (wx + ww, wy, wz),
                    (wx + ww, wy, wz + wh),
                    (wx, wy, wz + wh),
                    (wx, wy + window_thickness, wz),
                    (wx + ww, wy + window_thickness, wz),
                    (wx + ww, wy + window_thickness, wz + wh),
                    (wx, wy + window_thickness, wz + wh)
                ])
                if pane:
                    rs.ObjectColor(pane, glass_color)
                    total_geometry.append(pane)

                # Back (+Y)
                wyb = current_y + current_depth + window_offset
                pane = rs.AddBox([
                    (wx, wyb, wz),
                    (wx + ww, wyb, wz),
                    (wx + ww, wyb, wz + wh),
                    (wx, wyb, wz + wh),
                    (wx, wyb - window_thickness, wz),
                    (wx + ww, wyb - window_thickness, wz),
                    (wx + ww, wyb - window_thickness, wz + wh),
                    (wx, wyb - window_thickness, wz + wh)
                ])
                if pane:
                    rs.ObjectColor(pane, glass_color)
                    total_geometry.append(pane)

                # Left (-X)
                wy = current_y + col * win_depth + win_depth * 0.1
                wxl = current_x - window_offset
                pane = rs.AddBox([
                    (wxl, wy, wz),
                    (wxl, wy + wd, wz),
                    (wxl, wy + wd, wz + wh),
                    (wxl, wy, wz + wh),
                    (wxl + window_thickness, wy, wz),
                    (wxl + window_thickness, wy + wd, wz),
                    (wxl + window_thickness, wy + wd, wz + wh),
                    (wxl + window_thickness, wy, wz + wh)
                ])
                if pane:
                    rs.ObjectColor(pane, glass_color)
                    total_geometry.append(pane)

                # Right (+X)
                wxr = current_x + current_width + window_offset
                pane = rs.AddBox([
                    (wxr, wy, wz),
                    (wxr, wy + wd, wz),
                    (wxr, wy + wd, wz + wh),
                    (wxr, wy, wz + wh),
                    (wxr - window_thickness, wy, wz),
                    (wxr - window_thickness, wy + wd, wz),
                    (wxr - window_thickness, wy + wd, wz + wh),
                    (wxr - window_thickness, wy, wz + wh)
                ])
                if pane:
                    rs.ObjectColor(pane, glass_color)
                    total_geometry.append(pane)

        current_z += tier_height
        current_x += (1 - tier_step) * current_width / 2
        current_y += (1 - tier_step) * current_depth / 2
        current_width *= tier_step
        current_depth *= tier_step

    if include_spire:
        spire_height = tier_height * 1.5
        base_center = (current_x + current_width / 2, current_y + current_depth / 2, current_z)
        spire = rs.AddCone(base_center, spire_height, current_width / 6)
        if spire:
            rs.ObjectColor(spire, spire_color)
            total_geometry.append(spire)

    rs.EnableRedraw(True)
    return total_geometry

# --- Example usage ---
params = {
    'width': 20,
    'depth': 20,
    'base_height': 120,
    'tiers': 4,
    'tier_step': 0.7,
    'windows_per_face': 3,
    'has_spire': True
}

if __name__ == '__main__':
    skyscraper = create_skyscraper(params)
    if skyscraper:
        print("Generated skyscraper with " + str(len(skyscraper)) + " components.")
    else:
        print("Failed to generate skyscraper.")
