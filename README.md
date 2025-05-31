### Update this every week to show report

# **Andrei Vince** for Week 2
- Implemented voxel limit enforcement (`max_voxels_per_tower = 400`) with early stopping
- Integrated seed-based randomness for reproducibility
- Created a rule-based prompt classification system:
  - Describes tower forms based on structure (exemple: "tapered", "fragmented")
- Generated clean prompt strings for each tower:

2D_CA_tower, fragmented form, b=2, s=2–6, 25 layers

### Prompt Classification Logic

| Condition                                      | Label        |
| --------------------------------------------- | ------------ |
| Survive min ≤ 2 and survive max ≥ 6           | fragmented   |
| Layers ≥ 25 and birth ≥ 3                     | tapered      |
| Voxel count ≥ 380                             | dense        |
| Layers ≥ 20 and voxel count < 300             | eroded       |
| Otherwise                                     | mixed        |

### Example Generated Prompt

2D_CA_tower, tapered form, b=3, s=2–5, 30 layers

### Example Visual
```markdown
![Tower Sample](images/Tower%20Sample%20Week%202.png)

# **Aidan** for Week 2
