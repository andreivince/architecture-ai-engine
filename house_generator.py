# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import math
import Rhino # For RhinoCommon
import scriptcontext # For adding objects to doc
import System # For System.Guid

# --- Helper Function to Replace rs.AddBox ---
def create_box_rhinocommon(point1_coords, point2_coords, add_to_doc=True):
    try:
        p0 = Rhino.Geometry.Point3d(float(point1_coords[0]), float(point1_coords[1]), float(point1_coords[2]))
        p1 = Rhino.Geometry.Point3d(float(point2_coords[0]), float(point2_coords[1]), float(point2_coords[2]))
        min_x = min(p0.X, p1.X); min_y = min(p0.Y, p1.Y); min_z = min(p0.Z, p1.Z)
        max_x = max(p0.X, p1.X); max_y = max(p0.Y, p1.Y); max_z = max(p0.Z, p1.Z)
        if abs(max_x - min_x) < Rhino.RhinoMath.ZeroTolerance or \
           abs(max_y - min_y) < Rhino.RhinoMath.ZeroTolerance or \
           abs(max_z - min_z) < Rhino.RhinoMath.ZeroTolerance:
            pass # print(f"Warning: Degenerate box for points {point1_coords}, {point2_coords}")
        bbox = Rhino.Geometry.BoundingBox(min_x, min_y, min_z, max_x, max_y, max_z)
        brep = Rhino.Geometry.Brep.CreateFromBox(bbox)
        if brep and brep.IsValid:
            if add_to_doc:
                guid = scriptcontext.doc.Objects.AddBrep(brep)
                return guid if guid != System.Guid.Empty else None
            else: return brep
        return None
    except Exception as e: # print(f"Ex in create_box_rhinocommon: {e}");
        return None

# --- Main House Generation Function ---
def generate_house(params):
    rs.DeleteObjects(rs.AllObjects())
    rs.EnableRedraw(False)
    # rs.Command("_-Purge _All=_Yes _Enter", False) # Optional

    raw_width = params.get('width', 10.0); raw_depth = params.get('depth', 8.0)
    width = float(raw_width); depth = float(raw_depth)
    num_floors = max(1, min(params.get('floors', 1), 3))
    roof_type = params.get('roof_type', "flat"); window_style = params.get('window_style', "square")
    door_position = params.get('door_position', "center"); has_balcony = params.get('has_balcony', False)

    _afhc = min(width, depth) / 3.5; floor_height = float(max(2.8, min(_afhc, 4.5)))
    _awtc = min(width, depth) / 25.0; wall_thickness = float(max(0.15, min(_awtc, 0.35)))

    color_walls=(220,220,220); color_roof=(50,50,50); color_door=(100,60,40)
    color_windows=(120,180,255); color_balcony=(150,150,150)
    
    final_geometry_guids = []; all_cutter_guids = []
    total_house_height = float(num_floors * floor_height)

    outer_shell_box_guid = create_box_rhinocommon((0,0,0), (width, depth, total_house_height))
    if not outer_shell_box_guid: print("FATAL ERROR: outer_shell_box creation failed."); rs.EnableRedraw(True); return
    
    inner_shell_box_guid = create_box_rhinocommon(
        (wall_thickness, wall_thickness, wall_thickness), 
        (width - wall_thickness, depth - wall_thickness, total_house_height)
    )
    if not inner_shell_box_guid:
        print("FATAL ERROR: inner_shell_box creation failed."); rs.DeleteObject(outer_shell_box_guid); rs.EnableRedraw(True); return

    initial_walls_obj_guid = None
    if rs.IsBrep(outer_shell_box_guid) and rs.IsBrep(inner_shell_box_guid):
        # Using delete_input=True for initial shell, as inputs are meant to be consumed fully.
        diff_result_guids = rs.BooleanDifference([outer_shell_box_guid], [inner_shell_box_guid], delete_input=True)
        if diff_result_guids and len(diff_result_guids) == 1 and rs.IsBrep(diff_result_guids[0]):
            initial_walls_obj_guid = diff_result_guids[0]
        else:
            rs.DeleteObjects(diff_result_guids) 
            if rs.IsObject(outer_shell_box_guid): rs.DeleteObject(outer_shell_box_guid) 
            if rs.IsObject(inner_shell_box_guid): rs.DeleteObject(inner_shell_box_guid)
            print("Error: BooleanDifference for house shell failed."); rs.EnableRedraw(True); return
    else:
        if rs.IsObject(outer_shell_box_guid): rs.DeleteObject(outer_shell_box_guid)
        if rs.IsObject(inner_shell_box_guid): rs.DeleteObject(inner_shell_box_guid)
        print("Error: Initial box GUIDs invalid before Boolean."); rs.EnableRedraw(True); return

    if not initial_walls_obj_guid: print("FATAL ERROR: Initial walls GUID missing after shell."); rs.EnableRedraw(True); return
    else:
        print("DEBUG 1: Initial walls created. GUID: {initial_walls_obj_guid}, IsBrep: {rs.IsBrep(initial_walls_obj_guid)}")
        if not rs.IsBrep(initial_walls_obj_guid):
            print("ERROR: initial_walls_obj_guid is NOT a valid Brep after creation!"); rs.DeleteObject(initial_walls_obj_guid); rs.EnableRedraw(True); return

    intermediate_slabs_guids = []
    for i_floor in range(num_floors - 1):
        s_pt1 = (wall_thickness, wall_thickness, (i_floor + 1) * floor_height - wall_thickness)
        s_pt2 = (width - wall_thickness, depth - wall_thickness, (i_floor + 1) * floor_height)
        slab_guid = create_box_rhinocommon(s_pt1, s_pt2)
        if slab_guid and rs.IsBrep(slab_guid): intermediate_slabs_guids.append(slab_guid)
        else: print("Warning: Failed to create slab for floor {i_floor + 1}.")

    processed_walls_obj_guid = initial_walls_obj_guid # Start with the shell
    if intermediate_slabs_guids:
        # Combine current walls (shell) with new slabs for union attempt
        objects_to_try_union = [processed_walls_obj_guid] + intermediate_slabs_guids
        valid_union_guids = [g for g in objects_to_try_union if g and rs.IsBrep(g)]

        if len(valid_union_guids) > 1:
            # *** MODIFIED HERE: delete_input=False ***
            union_result_guids = rs.BooleanUnion(valid_union_guids, delete_input=False) 
            
            if union_result_guids and len(union_result_guids) == 1 and rs.IsBrep(union_result_guids[0]):
                # Union successful, new object created. Delete original inputs.
                new_processed_wall = union_result_guids[0]
                for guid_to_delete in valid_union_guids:
                    if guid_to_delete != new_processed_wall: # Don't delete the result itself
                        if rs.IsObject(guid_to_delete): rs.DeleteObject(guid_to_delete)
                processed_walls_obj_guid = new_processed_wall
                print("DEBUG: Slabs successfully unioned with walls.")
            else: # Union FAILED or produced multiple/no objects
                rs.DeleteObjects(union_result_guids) # Delete any fragments from the failed union
                print("Warning: Failed to union slabs. Slabs (if any exist and are valid) will be kept separate.")
                # The original objects in valid_union_guids (like initial_walls_obj_guid) still exist.
                # Add successfully created slabs to final geometry if they weren't unioned and are still valid.
                for s_guid in intermediate_slabs_guids: 
                    if s_guid and rs.IsObject(s_guid) and rs.IsBrep(s_guid): 
                        rs.ObjectColor(s_guid, color_walls)
                        final_geometry_guids.append(s_guid)
                # processed_walls_obj_guid remains as initial_walls_obj_guid (which should still be valid)
        elif len(valid_union_guids) == 1 and valid_union_guids[0] == processed_walls_obj_guid:
            # Only the main shell was valid, no valid slabs to union. Delete attempted slabs if they exist.
            rs.DeleteObjects(intermediate_slabs_guids) # Deletes GUIDs from this list if they are objects
        else: # No valid objects to union or only invalid slabs
            rs.DeleteObjects(intermediate_slabs_guids)
            # processed_walls_obj_guid remains initial_walls_obj_guid

    print("DEBUG 2: After slab union. processed_walls_obj_guid: {processed_walls_obj_guid}, IsBrep: {rs.IsBrep(processed_walls_obj_guid)}")
    if not processed_walls_obj_guid or not rs.IsBrep(processed_walls_obj_guid):
        print("ERROR: processed_walls_obj_guid invalid before applying cutters!"); rs.DeleteObject(processed_walls_obj_guid); rs.EnableRedraw(True); return

    # --- (The rest of the script: Door, Windows, Cutters, Balcony, Roof, Finalize) ---
    # --- This part should be the same as the last fully converted script ---
    # --- For brevity, I will assume the rest of the script from "--- 2. Door ---" onwards is correctly copied from the previous full version ---
    # --- Ensure all create_box_rhinocommon calls and DEBUG prints are maintained ---

    # --- 2. Door ---
    door_clear_span_h = floor_height - wall_thickness; door_h = min(door_clear_span_h * 0.85, 2.2) 
    door_w = max(0.9, min(width * 0.2, 1.5)); door_z_start = wall_thickness 
    if door_position == "center": door_x = width / 2.0 - door_w / 2.0
    elif door_position == "left": door_x = max(wall_thickness * 1.5, width * 0.1) 
    elif door_position == "right": door_x = min(width * 0.9 - door_w, width - wall_thickness * 1.5 - door_w)
    else: door_x = width / 2.0 - door_w / 2.0
    door_x = max(wall_thickness, min(door_x, width - wall_thickness - door_w))

    door_cutout_guid = create_box_rhinocommon(
        (door_x, -0.01, door_z_start), 
        (door_x + door_w, wall_thickness + 0.01, door_z_start + door_h)
    )
    if door_cutout_guid: all_cutter_guids.append(door_cutout_guid)
    else: print("Warning: Failed to create door cutout box.")

    door_panel_guid = create_box_rhinocommon(
        (door_x, 0, door_z_start), 
        (door_x + door_w, wall_thickness, door_z_start + door_h)
    )
    if door_panel_guid: rs.ObjectColor(door_panel_guid, color_door); final_geometry_guids.append(door_panel_guid)
    else: print("Warning: Failed to create door panel.")

    # --- 3. Windows ---
    for i_floor in range(num_floors):
        clear_floor_z_start = i_floor * floor_height + wall_thickness
        clear_floor_h_available = floor_height - (wall_thickness if i_floor == num_floors - 1 else 2 * wall_thickness)
        if clear_floor_h_available < 0.5: continue

        win_actual_h = clear_floor_h_available * 0.5; win_actual_w = max(0.6, width * 0.15)
        win_sill_abs_z = clear_floor_z_start + clear_floor_h_available * 0.25
        if win_sill_abs_z + win_actual_h > clear_floor_z_start + clear_floor_h_available - 0.1:
            win_actual_h = clear_floor_z_start + clear_floor_h_available - win_sill_abs_z - 0.1
        if win_actual_h < 0.3: continue

        if window_style == "strip":
            strip_w = max(width * 0.75 - (2 * wall_thickness), win_actual_w * 2); strip_h = clear_floor_h_available * 0.25
            strip_x = (width - strip_w) / 2.0; strip_sill_abs_z = clear_floor_z_start + clear_floor_h_available * 0.65
            if strip_sill_abs_z + strip_h > clear_floor_z_start + clear_floor_h_available - 0.1:
                strip_h = clear_floor_z_start + clear_floor_h_available - strip_sill_abs_z - 0.1
            if strip_h < 0.2: continue
            win_cut_guid = create_box_rhinocommon((strip_x, -0.01, strip_sill_abs_z), (strip_x + strip_w, wall_thickness + 0.01, strip_sill_abs_z + strip_h))
            if win_cut_guid: all_cutter_guids.append(win_cut_guid)
            else: print("Warning: Failed strip win cut flr {i_floor}")
            win_pane_guid = create_box_rhinocommon((strip_x, wall_thickness * 0.4, strip_sill_abs_z), (strip_x + strip_w, wall_thickness * 0.6, strip_sill_abs_z + strip_h))
            if win_pane_guid: rs.ObjectColor(win_pane_guid, color_windows); final_geometry_guids.append(win_pane_guid)
            else: print("Warning: Failed strip win pane flr {i_floor}")
        else: 
            num_side_windows = 1 if width < (2 * win_actual_w + 3 * wall_thickness) else 2
            win_spacing = max((width - (num_side_windows * win_actual_w) - (2 * wall_thickness)) / (num_side_windows + 1), wall_thickness * 0.5)
            for k_win in range(num_side_windows):
                win_x = wall_thickness + win_spacing + k_win * (win_actual_w + win_spacing)
                if i_floor == 0 and (door_x < win_x + win_actual_w and door_x + door_w > win_x): continue
                win_cut_guid, win_pane_guid = None, None; current_style_is_square = False
                if window_style == "arched":
                    arch_radius = win_actual_w / 2.0; rect_h = win_actual_h - arch_radius
                    if rect_h < 0: current_style_is_square = True
                    elif rect_h < 0.05 and win_actual_h > arch_radius: rect_h = 0
                    if not current_style_is_square:
                        cut_rect_guid, cut_arch_guid = None, None
                        if rect_h > 0.01: cut_rect_guid = create_box_rhinocommon((win_x, -0.01, win_sill_abs_z), (win_x + win_actual_w, wall_thickness + 0.01, win_sill_abs_z + rect_h))
                        arch_o = Rhino.Geometry.Point3d(win_x + arch_radius, wall_thickness / 2.0, win_sill_abs_z + rect_h)
                        arc_plane = rs.PlaneFromPoints(arch_o, arch_o + Rhino.Geometry.Vector3d(arch_radius,0,0), arch_o + Rhino.Geometry.Vector3d(0,0,arch_radius))
                        arc_c = rs.AddArc(arc_plane, arch_radius, 180.0)
                        if arc_c:
                            line_c = rs.AddLine(rs.CurveStartPoint(arc_c), rs.CurveEndPoint(arc_c))
                            if line_c:
                                prof_c = rs.JoinCurves([arc_c, line_c], True)
                                if prof_c and rs.IsCurveClosed(prof_c[0]):
                                    srf_c_l = rs.AddPlanarSrf(prof_c[0])
                                    if srf_c_l:
                                        extr_s = arch_o - Rhino.Geometry.Vector3d(0, (wall_thickness/2.0+0.01),0); extr_e = arch_o + Rhino.Geometry.Vector3d(0,(wall_thickness/2.0+0.01),0)
                                        extr_p = rs.AddLine(extr_s, extr_e)
                                        cut_arch_guid = rs.ExtrudeSurface(srf_c_l[0], extr_p)
                                        rs.DeleteObject(extr_p); rs.DeleteObjects(srf_c_l)
                                rs.DeleteObjects(prof_c)
                            rs.DeleteObject(line_c)
                        rs.DeleteObject(arc_c)
                        if not cut_arch_guid: current_style_is_square = True
                        if not current_style_is_square:
                            if cut_rect_guid and cut_arch_guid:
                                u_res = rs.BooleanUnion([cut_rect_guid, cut_arch_guid]); 
                                if u_res and len(u_res)==1: win_cut_guid = u_res[0]
                                else: rs.DeleteObjects(u_res); rs.DeleteObject(cut_rect_guid); rs.DeleteObject(cut_arch_guid); current_style_is_square=True
                            elif cut_rect_guid: win_cut_guid = cut_rect_guid; rs.DeleteObject(cut_arch_guid)
                            elif cut_arch_guid: win_cut_guid = cut_arch_guid; rs.DeleteObject(cut_rect_guid)
                            else: current_style_is_square = True
                        if not current_style_is_square: # Arched Pane
                            pane_rect_guid, pane_arch_guid = None, None; pane_y_s = wall_thickness*0.4; pane_t = wall_thickness*0.2
                            if rect_h > 0.01: pane_rect_guid = create_box_rhinocommon((win_x, pane_y_s, win_sill_abs_z), (win_x + win_actual_w, pane_y_s + pane_t, win_sill_abs_z + rect_h))
                            arch_po = Rhino.Geometry.Point3d(win_x + arch_radius, pane_y_s + pane_t / 2.0, win_sill_abs_z + rect_h)
                            arc_pp = rs.PlaneFromPoints(arch_po, arch_po + Rhino.Geometry.Vector3d(arch_radius,0,0), arch_po + Rhino.Geometry.Vector3d(0,0,arch_radius))
                            arc_pc = rs.AddArc(arc_pp, arch_radius, 180.0)
                            if arc_pc:
                                line_pc = rs.AddLine(rs.CurveStartPoint(arc_pc), rs.CurveEndPoint(arc_pc))
                                if line_pc:
                                    prof_pc = rs.JoinCurves([arc_pc, line_pc], True)
                                    if prof_pc and rs.IsCurveClosed(prof_pc[0]):
                                        srf_pc_l = rs.AddPlanarSrf(prof_pc[0])
                                        if srf_pc_l:
                                            extr_ps = arch_po - Rhino.Geometry.Vector3d(0,pane_t/2.0,0); extr_pe = arch_po + Rhino.Geometry.Vector3d(0,pane_t/2.0,0)
                                            extr_pp = rs.AddLine(extr_ps, extr_pe)
                                            pane_arch_guid = rs.ExtrudeSurface(srf_pc_l[0], extr_pp)
                                            rs.DeleteObject(extr_pp); rs.DeleteObjects(srf_pc_l)
                                    rs.DeleteObjects(prof_pc)
                                rs.DeleteObject(line_pc)
                            rs.DeleteObject(arc_pc)
                            if not pane_arch_guid: current_style_is_square = True
                            if not current_style_is_square:
                                if pane_rect_guid and pane_arch_guid:
                                    u_resp = rs.BooleanUnion([pane_rect_guid, pane_arch_guid])
                                    if u_resp and len(u_resp)==1: win_pane_guid = u_resp[0]
                                    else: rs.DeleteObjects(u_resp); rs.DeleteObject(pane_rect_guid); rs.DeleteObject(pane_arch_guid); current_style_is_square=True
                                elif pane_rect_guid: win_pane_guid = pane_rect_guid; rs.DeleteObject(pane_arch_guid)
                                elif pane_arch_guid: win_pane_guid = pane_arch_guid; rs.DeleteObject(pane_rect_guid)
                                else: current_style_is_square = True
                if current_style_is_square or window_style == "square" or (window_style == "arched" and (not win_cut_guid or not win_pane_guid)):
                    if not win_cut_guid: win_cut_guid = create_box_rhinocommon((win_x, -0.01, win_sill_abs_z), (win_x + win_actual_w, wall_thickness + 0.01, win_sill_abs_z + win_actual_h))
                    if not win_pane_guid: win_pane_guid = create_box_rhinocommon((win_x, wall_thickness * 0.4, win_sill_abs_z), (win_x + win_actual_w, wall_thickness * 0.6, win_sill_abs_z + win_actual_h))
                if win_cut_guid and rs.IsBrep(win_cut_guid): all_cutter_guids.append(win_cut_guid)
                else: print("Warning: Failed win cut flr {i_floor} win {k_win}"); rs.DeleteObject(win_cut_guid)
                if win_pane_guid and rs.IsBrep(win_pane_guid): rs.ObjectColor(win_pane_guid, color_windows); final_geometry_guids.append(win_pane_guid)
                else: print("Warning: Failed win pane flr {i_floor} win {k_win}"); rs.DeleteObject(win_pane_guid)

    print("DEBUG 3: Before wall cuts. processed_walls_obj_guid: {processed_walls_obj_guid}, IsBrep: {rs.IsBrep(processed_walls_obj_guid)}, Num cutters: {len(all_cutter_guids)}")
    if processed_walls_obj_guid and rs.IsBrep(processed_walls_obj_guid) and all_cutter_guids:
        valid_cutter_guids = [c for c in all_cutter_guids if c and rs.IsBrep(c)]
        if valid_cutter_guids:
            current_wall_guid = processed_walls_obj_guid
            print("DEBUG: Starting wall cuts. Initial current_wall_guid: {current_wall_guid}, IsBrep: {rs.IsBrep(current_wall_guid)}")
            for i, cutter_guid in enumerate(valid_cutter_guids):
                print("DEBUG: Attempting cut {i+1} with cutter: {cutter_guid}, IsBrep: {rs.IsBrep(cutter_guid)}")
                if not current_wall_guid or not rs.IsBrep(current_wall_guid): print("ERROR: current_wall_guid ({current_wall_guid}) invalid before cut {i+1}. Aborting."); break
                temp_diff_guids = rs.BooleanDifference([current_wall_guid], [cutter_guid], delete_input=False)
                if temp_diff_guids and len(temp_diff_guids) == 1 and rs.IsBrep(temp_diff_guids[0]):
                    new_wall_cand = temp_diff_guids[0]
                    if current_wall_guid != processed_walls_obj_guid and current_wall_guid != new_wall_cand:
                        if rs.IsObject(current_wall_guid): rs.DeleteObject(current_wall_guid)
                    current_wall_guid = new_wall_cand
                    print("DEBUG: Cut {i+1} successful. New current_wall_guid: {current_wall_guid}")
                else: rs.DeleteObjects(temp_diff_guids); print("Warning: Wall cut {i+1} failed. current_wall_guid ({current_wall_guid}) unchanged.")
            if current_wall_guid != processed_walls_obj_guid:
                if rs.IsObject(processed_walls_obj_guid): rs.DeleteObject(processed_walls_obj_guid)
            processed_walls_obj_guid = current_wall_guid
            print("DEBUG: After all wall cuts. Final processed_walls_obj_guid: {processed_walls_obj_guid}, IsBrep: {rs.IsBrep(processed_walls_obj_guid)}")
        rs.DeleteObjects(all_cutter_guids)
    else: print("DEBUG: Skipping wall cuts. Conditions not met. walls: {processed_walls_obj_guid}, cutters: {len(all_cutter_guids)}")

    print("DEBUG 4: After wall cuts, before balcony. processed_walls_obj_guid: {processed_walls_obj_guid}, IsBrep: {rs.IsBrep(processed_walls_obj_guid)}")
    if num_floors >= 2 and has_balcony:
        b_flr_idx = 1; b_base_z = b_flr_idx * floor_height; b_w = width*0.5; b_d = max(1.2, depth*0.20)
        b_x = (width-b_w)/2.0; b_slab_h = wall_thickness*0.8
        slab_b_guid = create_box_rhinocommon((b_x,-b_d,b_base_z),(b_x+b_w,0,b_base_z+b_slab_h))
        if slab_b_guid:
            rs.ObjectColor(slab_b_guid,color_balcony); final_geometry_guids.append(slab_b_guid)
            rail_h=1.0; rail_t=max(0.08,wall_thickness*0.4); rail_base_z=b_base_z+b_slab_h
            rail_defs=[((b_x,-b_d,rail_base_z),(b_x+b_w,-b_d+rail_t,rail_base_z+rail_h)),((b_x,-b_d+rail_t,rail_base_z),(b_x+rail_t,0,rail_base_z+rail_h)),((b_x+b_w-rail_t,-b_d+rail_t,rail_base_z),(b_x+b_w,0,rail_base_z+rail_h))]
            for r_def in rail_defs:
                rail_p_guid = create_box_rhinocommon(r_def[0],r_def[1])
                if rail_p_guid: rs.ObjectColor(rail_p_guid,color_balcony); final_geometry_guids.append(rail_p_guid)
            if processed_walls_obj_guid and rs.IsBrep(processed_walls_obj_guid):
                bd_h=door_h; bd_w=door_w*0.9; bd_x=b_x+(b_w-bd_w)/2.0; bd_z_s=b_base_z+wall_thickness # CHECK: b_door_z_start might need to be on floor itself, not wall_thickness above
                bd_cut_guid = create_box_rhinocommon((bd_x,-0.01,bd_z_s),(bd_x+bd_w,wall_thickness+0.01,bd_z_s+bd_h))
                if bd_cut_guid:
                    temp_w_l = rs.BooleanDifference([processed_walls_obj_guid],[bd_cut_guid],delete_input=False)
                    if temp_w_l and len(temp_w_l)==1 and rs.IsBrep(temp_w_l[0]):
                        if rs.IsObject(processed_walls_obj_guid): rs.DeleteObject(processed_walls_obj_guid)
                        processed_walls_obj_guid = temp_w_l[0]
                    else: rs.DeleteObjects(temp_w_l); print("Warning: Balcony door cutout failed.")
                    rs.DeleteObject(bd_cut_guid)
                else: print("Warning: Failed balcony door cutter.")
                bd_panel_guid = create_box_rhinocommon((bd_x,0,bd_z_s),(bd_x+bd_w,wall_thickness,bd_z_s+bd_h))
                if bd_panel_guid: rs.ObjectColor(bd_panel_guid,color_door); final_geometry_guids.append(bd_panel_guid)
        else: print("Warning: Failed balcony slab.")
    
    print("DEBUG 5: After balcony, before roof. processed_walls_obj_guid: {processed_walls_obj_guid}, IsBrep: {rs.IsBrep(processed_walls_obj_guid)}")
    roof_place_z = num_floors*floor_height; roof_obj_guid=None
    if roof_type=="flat": roof_obj_guid=create_box_rhinocommon((0,0,roof_place_z),(width,depth,roof_place_z+wall_thickness))
    elif roof_type=="gable" or roof_type=="asymmetric":
        ridge_h=width/3.5; ridge_x=width/2.0 if roof_type=="gable" else width*0.33
        prof_pts=[Rhino.Geometry.Point3d(0,0,0),Rhino.Geometry.Point3d(width,0,0),Rhino.Geometry.Point3d(ridge_x,0,ridge_h),Rhino.Geometry.Point3d(0,0,0)]
        prof_c=rs.AddPolyline(prof_pts)
        if prof_c and rs.IsCurveClosed(prof_c):
            srf_l=rs.AddPlanarSrf(prof_c)
            if srf_l and len(srf_l)>0:
                path_l=rs.AddLine(Rhino.Geometry.Point3d(0,0,0),Rhino.Geometry.Point3d(0,depth,0))
                prism_guid=rs.ExtrudeSurface(srf_l[0],path_l)       
                rs.DeleteObject(path_l); rs.DeleteObjects(srf_l)
                if prism_guid and rs.IsBrep(prism_guid):
                    capped = rs.CapPlanarHoles(prism_guid)
                    if capped and len(capped) == 1:
                        rs.DeleteObject(prism_guid)
                        prism_guid = capped[0]
                    else:
                        print("Cap failed – roof will stay an open surface")
                
                    roof_base_z = rs.BoundingBox(prism_guid)[0].Z
                    move_vector = Rhino.Geometry.Vector3d(0, 0, roof_place_z - roof_base_z)
                    rs.MoveObject(prism_guid, move_vector)
                    roof_obj_guid = prism_guid
                else:
                    rs.DeleteObject(prism_guid)
                    print("Warning: Failed to extrude gable roof or not Brep.")
            else: rs.DeleteObjects(srf_l); print("Warning: Failed planar srf for gable.")
            rs.DeleteObject(prof_c)
        elif prof_c: rs.DeleteObject(prof_c); print("Warning: Gable roof profile not closed.")
        else: print("Warning: Failed gable roof profile curve.")
    if roof_obj_guid and rs.IsBrep(roof_obj_guid): rs.ObjectColor(roof_obj_guid,color_roof); final_geometry_guids.append(roof_obj_guid)
    else: print("Warning: Roof gen failed for '{roof_type}'. Final roof_guid: {roof_obj_guid}"); rs.DeleteObject(roof_obj_guid)
    # Capture the footprint box of the finished walls
    house_bb = rs.BoundingBox(processed_walls_obj_guid)
    # Capture the footprint box of the roof we just created
    roof_bb  = rs.BoundingBox(roof_obj_guid)

    # If both boxes exist, compute their XY centres
    if house_bb and roof_bb:
        house_c = rs.PointDivide(rs.PointAdd(house_bb[0], house_bb[6]), 2.0)  # walls centre
        roof_c  = rs.PointDivide(rs.PointAdd(roof_bb[0],  roof_bb[6]),  2.0)  # roof centre

        # Build a move vector equal to the XY offset (ignore Z)
        delta = Rhino.Geometry.Vector3d(house_c.X - roof_c.X,
                                        house_c.Y - roof_c.Y,
                                        0)

        # If the offset is bigger than numerical noise, shove the roof into place
        if delta.Length > Rhino.RhinoMath.ZeroTolerance * 10:
            rs.MoveObject(roof_obj_guid, delta)

        print("DEBUG 6: Finalizing walls. processed_walls_obj_guid: {processed_walls_obj_guid}, IsBrep: {rs.IsBrep(processed_walls_obj_guid)}")
        if processed_walls_obj_guid and rs.IsBrep(processed_walls_obj_guid):
            rs.ObjectColor(processed_walls_obj_guid,color_walls); final_geometry_guids.append(processed_walls_obj_guid)
        elif rs.IsObject(processed_walls_obj_guid): rs.DeleteObject(processed_walls_obj_guid); print("Error: Final wall obj GUID existed but not valid Brep.")
        else: print("Error: Final processed_walls_obj_guid was invalid or None.")

        rs.EnableRedraw(True)
        return final_geometry_guids

params = {
    "width": 15,
    "depth": 18,
    "floors": 4,
    "roof_type": "gable",
    "window_style": "square",
    "door_position": "left",
    "has_balcony": True
}

if __name__ == '__main__':
    generated_objects = generate_house(params)
    if generated_objects: print("House gen complete. {len(generated_objects)} final GUIDs.")
    else: print("House gen failed or produced no objects.")