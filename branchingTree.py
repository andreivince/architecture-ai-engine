import rhinoscriptsyntax as rs
import math

def draw_branch(start_point, direction, length, angle, depth):
    if depth == 0:
        return

    end_point = rs.PointAdd(start_point, rs.VectorScale(direction, length))
    rs.AddLine(start_point, end_point)

    vec1 = rs.VectorRotate(direction, angle, [0, 0, 1])
    vec2 = rs.VectorRotate(direction, -angle, [0, 0, 1])

    draw_branch(end_point, vec1, length * 0.7, angle, depth - 1)
    draw_branch(end_point, vec2, length * 0.7, angle, depth - 1)

origin = [0, 0, 0]
initial_direction = [0, 1, 0]  
initial_length = 10
branch_angle = 35  
max_depth = 10

draw_branch(origin, initial_direction, initial_length, branch_angle, max_depth)
