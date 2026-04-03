# CS 218 Assignment 2: Verification and Full Function/Theorem Explanation

**Date:** April 3, 2026

## Goal
This note does two things:
1. Verifies whether the current Python implementation in `main.py` is correct.
2. Documents every theorem used and every defined function in the implementation.

## Verification Result (Current Code State)
### Invariant Checks Used
For a polygon with holes, a valid triangulation should satisfy:
1. Triangle interiors are inside walkable space.
2. No triangle edge intersects blocked boundary edges except at shared endpoints.
3. Area conservation: total triangle area equals walkable area.
4. Triangle count formula (after hole-bridging to a simple polygon) should be consistent with the vertex count of the bridged simple polygon.

### Executed Counterexample
Tested case:
- Outer square: `(0,0), (20,0), (20,20), (0,20)`
- One hole: `(7,7), (13,7), (13,13), (7,13)`

Observed from program output and direct area audit:
- Reported triangles: `4`
- Walkable doubled-area: `728`
- Sum of triangle doubled-areas: `560`

Hence area conservation fails.

**Conclusion:** the current implementation is **not fully correct yet** for general polygons with holes.

## Theorems and Mathematical Facts Used
### Jordan Curve Theorem (algorithmic use)
A simple closed polygonal chain partitions the plane into interior and exterior regions.

Use in code: basis for ray-casting in `point_in_ring` and region membership in `point_in_region`.

### Orientation and Segment Intersection Test (lemma)
Given points `a, b, c, d`, orientation predicates and on-segment checks determine whether segments `ab` and `cd` intersect.

Use in code: `orientation`, `on_segment`, `segments_intersect`.

### Ear Existence Theorem
Every simple polygon with at least 4 vertices has at least two ears.

Use in code: justifies iterative ear clipping in `ear_clip_triangulation`.

### Art Gallery Upper Bound with Holes
For a polygon with `n` total vertices and `h` holes, an upper bound on point guards is:

`floor((n + 2h) / 3)`

Use in code: computed in `solve` as output metric `k`.

### 3-Coloring of Triangulation Graph (lemma)
A maximal outerplanar triangulation graph is 3-colorable; choosing the smallest color class gives an upper bound guard set for simple polygons.

Use in code: heuristic guard selection via `color_outerplanar_graph` and `choose_guard_positions`.

## Function-by-Function Explanation
All functions below are from `main.py`.

### Geometry Primitives
- `same_point`: Exact coordinate equality check for two vertices.
- `cross`: Signed 2D cross product of vectors `(b-a)` and `(c-a)`.
- `orientation`: Returns turn sign: left/right/collinear via cross product sign.
- `polygon_area2`: Computes doubled signed area of a polygon.
- `ensure_ccw`: Reorients vertex order to counter-clockwise if needed.
- `ensure_cw`: Reorients vertex order to clockwise if needed.
- `remove_consecutive_duplicates`: Removes repeated adjacent points and closing duplicate.
- `on_segment`: Tests if collinear point lies on segment bounds.
- `segments_intersect`: Full segment-segment intersection test including collinear overlap.
- `point_in_ring`: Ray-casting point-in-polygon test on one ring.
- `point_in_region`: Inside outer ring and outside all holes check.

### Hole Bridging to a Simple Boundary
- `visible_bridge`: Checks if candidate bridge segment crosses existing edges and stays in valid region.
- `rightmost_vertex_index`: Selects rightmost vertex (tie by higher y).
- `choose_bridge_vertex`: Picks outer boundary vertex visible from selected hole vertex.
- `stitch_hole_into_polygon`: Splices hole cycle and bridge duplicates into outer boundary walk.
- `bridge_holes`: Repeats bridge-and-stitch for all holes, returns merged boundary and bridge list.

### Monotone Decomposition Helpers
- `classify_vertex`: Classifies vertex as start/end/split/merge/regular for sweep logic.
- `edge_x_at_y`: Computes x-coordinate where edge intersects horizontal sweep line y.
- `edge_crosses_sweep`: Checks if an edge crosses current sweep y-level.
- `sort_status`: Sorts sweep status edges by intersection x-value.
- `find_left_edge`: Finds nearest status edge strictly to the left of current vertex.
- `sweep_line_monotone_diagonals`: Produces diagonals intended to partition polygon into y-monotone pieces.
- `split_polygon_by_diagonal`: Splits one polygonal piece into two along a chosen diagonal.
- `decompose_to_monotone_pieces`: Applies all decomposition diagonals to build monotone pieces.

### Triangulation and Validity Filtering
- `triangulate_y_monotone`: Stack-based triangulation routine for one monotone piece.
- `triangulate_polygon_with_holes`: Current main triangulation pipeline: bridge holes, triangulate merged polygon, filter triangles.
- `triangle_vertices`: Extracts unique vertices used by produced triangles.
- `point_in_triangle`: Non-strict point-in-triangle test (boundary allowed).
- `point_strictly_in_triangle`: Strict interior test (boundary excluded).
- `triangle_is_walkable`: Rejects triangles outside valid region or with invalid boundary intersections.
- `ear_clip_triangulation`: Ear clipping triangulation of a simple polygon.

### Guard Computation
- `build_graph_from_triangles`: Builds adjacency graph from triangle edges.
- `color_outerplanar_graph`: Computes a 3-coloring-like assignment using degeneracy-style order.
- `choose_guard_positions`: Chooses up to `k` guard vertices, preferring smallest color class.

### I/O and Plotting
- `parse_input`: Parses all test cases from standard input format in assignment statement.
- `plot_case`: Draws outer boundary, holes, triangle edges, bridge edges, and guards using matplotlib.
- `format_triangle`: String formatter for one triangle output line.
- `format_vertex`: String formatter for one guard coordinate output line.
- `solve`: Main orchestrator for parse, triangulate, guard bound, output, and plotting.

## Complexity Notes
- Primitive tests are constant time each.
- Sweep-line helper section is designed around sorted status operations, but implemented with list scans/sorts in places; practical complexity can exceed strict `O(n log n)`.
- Ear clipping is typically `O(n^2)` in worst case.

## What Must Be Fixed for Full Correctness
To make the implementation correct for all valid assignment inputs:
1. Ensure bridged polygon is strictly simple and triangulated completely (no dropped ears, no missing regions).
2. Re-run area and coverage invariants for each test case.
3. Confirm generated triangles are disjoint in interior and exactly cover walkable region.
