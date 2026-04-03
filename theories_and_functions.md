# CS 218 Assignment 2: Theory and Function Map

Date: April 3, 2026

## Purpose
This document separates the independent ideas used in the project from the code that implements them.
It is organized in two layers:
1. the underlying theory or algorithm idea,
2. the functions in each file that realize that idea.

## Independent Theories

### 1. Polygon representation and orientation
This is the base geometry layer.
It covers storing points and polygon rings, removing duplicate vertices, and forcing a consistent clockwise or counterclockwise order.

### 2. Basic planar geometry
This includes orientation tests, signed area, point-on-segment checks, and segment intersection.
These routines are the foundation for visibility, containment, and triangulation.

### 3. Point-in-polygon and point-in-region testing
This theory checks whether a point lies inside an outer boundary and outside all holes.
It is used to validate bridges, diagonals, and triangle interiors.

### 4. Hole bridging
Hole bridging converts a polygon with holes into one merged simple boundary by choosing visible bridge edges.
This is the step that lets a simple-polygon triangulation routine handle holes.

### 5. Sweep-line decomposition
This theory detects split, merge, start, end, and regular vertices while sweeping from top to bottom.
It adds diagonals that decompose a polygon into monotone pieces.

### 6. Monotone polygon triangulation
Once a piece is monotone, it can be triangulated with a stack-based linear-time process.
This is the classic monotone triangulation step after decomposition.

### 7. Ear clipping triangulation
Ear clipping is a simpler polygon triangulation method that repeatedly removes valid ears.
It is not the main path in every file, but it is the active triangulation strategy in the simpler prototype.

### 8. Guard selection by coloring
After triangulation, the code builds an adjacency graph and colors it with three colors.
The smallest color class is then used as a guard set bound.

### 9. Plotting and output visualization
This theory is not geometric in itself, but it visualizes the boundaries, bridges, triangulation, and selected guards.
It is mainly a reporting and debugging layer.

## Theory to Function Map by File

### main.py
This is the most structured Python implementation.

#### 1. Polygon representation and orientation
- Vertex, Polygon, Triangle: core geometry data containers.
- same: compares two vertices by coordinates.
- dedup: removes consecutive duplicate vertices.
- area2: computes the signed area of a ring.
- ccw and cw: normalize ring orientation.

#### 2. Basic planar geometry
- orient: orientation test for three points.
- on_seg: checks whether a point lies on a segment.
- seg_inter: checks whether two segments intersect.

#### 3. Point-in-polygon and point-in-region testing
- in_ring: ray-casting test for one polygon ring.
- in_region: checks outer boundary membership and hole exclusion.
- visible: tests whether a candidate bridge or diagonal is unobstructed and lies inside the region.

#### 4. Hole bridging
- rightmost: chooses the rightmost vertex in a ring.
- stitch: inserts a hole connection into the outer boundary.
- bridge_holes: picks visible bridges and merges all holes into one boundary.

#### 5. Sweep-line decomposition
- vtype: classifies a vertex as start, end, split, merge, or regular.
- x_at: computes where an edge intersects the current sweep line.
- crosses: checks whether an edge spans the sweep level.
- left_edge: finds the edge immediately to the left of a sweep vertex.
- sweep_diagonals: generates diagonals using the sweep-line classification.
- split_piece: splits a polygon piece along a diagonal.
- decompose: applies all diagonals to produce pieces.

#### 6. Monotone polygon triangulation
- triangulate_monotone: triangulates one monotone piece using a stack.

#### 7. Triangle validation and guard selection
- tri_ok: rejects degenerate or invalid triangles against the original polygon with holes.
- triangulate_with_holes: runs bridging, decomposition, and triangulation together.
- guard_vertices: extracts unique vertices from triangles.
- choose_guards: colors the triangulation graph and selects a small guard set.

#### 8. Input parsing and output visualization
- parse: reads all test cases from standard input.
- plot: draws boundaries, holes, bridges, triangles, and guards.
- solve: drives the full pipeline and writes the final text output.

### main2.py
This is the simpler Python prototype.

#### 1. Polygon representation and basic geometry
- Vertex, Polygon: light class-based data structures with prev and next links.
- cross: orientation helper.
- intersect: segment intersection test.
- is_visible: checks whether a bridge candidate crosses any polygon edge.

#### 2. Hole bridging
- bridge_holes: attaches each hole to the outer polygon using a visible outer vertex.

#### 3. Placeholder decomposition
- decompose_monotone_placeholder: reserved stub for future sweep-line decomposition work.
- It is intentionally not used in the current execution path.

#### 4. Ear clipping triangulation
- polygon_area2: determines polygon orientation.
- point_in_triangle_strict: checks whether a point lies strictly inside a triangle.
- triangulate_ear: performs ear clipping until the polygon is fully triangulated.

#### 5. Guard bound and visualization
- compute_guards: computes the bound and returns a prefix of vertices as guards.
- plot_polygon: draws the polygon, holes, triangulation, and selected guards.

#### 6. Input and execution
- main: reads the test cases, bridges holes, triangulates, prints results, and plots.

### main.cpp
This is the C++ implementation of the same problem.

#### 1. Polygon representation and numeric geometry
- Point, Triangle, Polygon: the C++ geometry data types.
- toLD: converts integer coordinates to long double.
- pointEqual, pointGreater: coordinate comparison helpers.
- cross, dot: core vector geometry operations.
- signLD: epsilon-aware sign test.
- signedArea2, isCounterClockwise: area and orientation checks.

#### 2. Containment and intersection
- onSegment: checks whether a point lies on a segment.
- segmentsProperlyIntersect: segment intersection test.
- pointInRing: ray casting on one ring.
- pointInRegion: point containment against outer boundary and holes.

#### 3. Polygon cleanup and normalization
- squaredDistance: helper for bridge selection.
- removeConsecutiveDuplicates: removes repeated vertices.
- removeCollinearVertices: removes redundant collinear vertices.
- normalizePolygonOrientation: enforces outer CCW and hole CW orientation.

#### 4. Hole bridging
- rightmostVertexIndex: finds the rightmost hole vertex.
- segmentVisibleFromHole: tests if a bridge segment is valid.
- chooseBridge: selects the best outer vertex for a hole bridge.
- stitchHoleIntoOuter: merges a hole into the outer ring.

#### 5. Ear clipping triangulation
- isConvexVertex: checks whether a vertex is convex.
- pointStrictlyInsideTriangle: tests strict triangle containment.
- isEar: checks whether a candidate vertex forms an ear.
- triangulateSimplePolygon: performs ear clipping on a simple polygon.

#### 6. Sweep-line decomposition
- VertexKind, EdgeRef: sweep-line bookkeeping types.
- sweepHigher, sweepLower, horizontalEdge: sweep-line ordering helpers.
- edgeIntersectionX, edgeUpperEndpoint, edgeLowerEndpoint, edgeCrossesSweep: status-line edge helpers.
- findLeftStatusEdge, removeEdgeFromStatus, insertEdgeIntoStatus, sortStatus: sweep status maintenance.
- classifyVertex: classifies each vertex for the sweep algorithm.
- sweepLineDecompositionDiagonals: computes the diagonals that decompose the polygon.
- splitPieceByDiagonal: splits one piece by a diagonal.
- decomposeToMonotonePieces: applies diagonals and normalizes the resulting pieces.

#### 7. Full polygon-with-holes pipeline
- triangulatePolygonWithHoles: normalizes inputs, bridges holes, decomposes pieces, and triangulates them.

#### 8. Input and output
- readPolygon: reads a polygon ring from input.
- printTriangle: prints one triangle.
- main: reads the full test set and writes the triangulation output.

## File-Level Differences

### main.py vs main2.py
- main.py follows the more complete sweep-line decomposition pipeline.
- main2.py is intentionally simpler and currently uses ear clipping as the active triangulation path.
- main.py includes stronger validation and graph-based guard selection.
- main2.py is shorter and easier to read, but less algorithmically complete.

### main.py vs main.cpp
- main.py is the Python version with easier plotting and quicker iteration.
- main.cpp is the typed C++ version with explicit sweep-line and triangulation machinery.
- main.cpp keeps more low-level control over geometry and numeric robustness.

### main2.py vs main.cpp
- main2.py is the prototype-style file.
- main.cpp is the more complete reference implementation.
- main2.py is useful for experimenting with simpler triangulation logic.

## Supporting Files

### verification_and_explanation.md
This is the earlier file-level guide.
It explains what each file does and how the files differ.

### verification_and_explanation.tex
This is the LaTeX version of the explanation report.
It is the more formal companion to the Markdown notes.

### triangulation_case_1.png
This is an output artifact generated by the plotting code.
It is useful for checking whether the geometry pipeline is behaving as expected.

### .gitignore, .git, .venv, __pycache__
These are repository and environment support files.
They are not part of the algorithm, but they matter for local development.

## Short Summary
The project uses the same geometric theory in three different forms.
main.py is the structured sweep-line Python version, main2.py is the smaller ear-clipping prototype, and main.cpp is the explicit C++ reference implementation.
The remaining files are documentation, output, or workspace support.