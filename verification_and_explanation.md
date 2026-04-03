# CS 218 Assignment 2: File-Level Guide and Differences

Date: April 3, 2026

## Goal
This document explains:
1. What each file in the project folder is for.
2. How the main implementation files differ from each other.

## File-by-File Overview

### Assignment-2.pdf
- Source assignment handout.
- Defines the problem statement, expected algorithmic ideas, and I/O format.

### main.py
- Current primary Python implementation.
- Implements full pipeline structure:
1. parse input test cases,
2. represent outer boundary + holes,
3. bridge holes into one merged boundary,
4. run sweep-line style diagonal generation and decomposition,
5. triangulate pieces,
6. compute guard bound and pick guard vertices,
7. generate plot image.
- Uses dataclasses and stable vertex ids for topology tracking.
- Writes a plot image file path in output (non-interactive plotting backend).

### main2.py
- Alternative/simplified Python variant.
- Currently uses ear clipping as active triangulation.
- Contains a placeholder decomposition function for future sweep-line work, but it is intentionally unused.
- Uses simpler class-based objects (`Vertex`, `Polygon`) with direct links (`prev`, `next`).
- Calls `plt.show()` in plotting, which is interactive-style behavior.

### main.cpp
- C++ implementation variant of the same assignment idea.
- Includes robust geometric primitives, hole bridging, sweep-line decomposition helpers, and triangulation logic.
- Kept as a parallel implementation path for comparison/performance exploration.

### verification_and_explanation.tex
- LaTeX technical note.
- Earlier report explaining verification approach, theory references, and implementation notes.

### verification_and_explanation.md
- Markdown version of project notes.
- This file is now the file-level guide (current document).

### triangulation_case_1.png
- Example generated output image from a run.
- Visualizes boundaries, holes, triangulation lines, and guard points.

### .gitignore
- Ignore rules to keep environment/cache files out of version control.
- Currently includes virtual environment and Python cache folders.

### .venv/
- Local Python virtual environment.
- Stores interpreter and installed packages for this workspace.

### __pycache__/
- Python bytecode cache directory.
- Auto-generated, not source code.

### .git/
- Git metadata and history for the repository.

## Differences Between Core Code Files

### main.py vs main2.py
- `main.py` is the structured main path with sweep-decomposition-driven flow and non-interactive plotting output.
- `main2.py` is shorter/simpler, currently ear-clipping-based, with a placeholder decomposition function not yet wired in.
- `main.py` is better for assignment structure coverage; `main2.py` is better for quick prototype readability.

### main.py vs main.cpp
- Both target the same geometric problem.
- `main.py` is easier to iterate and visualize quickly.
- `main.cpp` is more explicit and typed for performance-oriented implementation.

### main2.py vs main.cpp
- `main2.py` is lightweight and currently less complete algorithmically.
- `main.cpp` is more complete and detailed in geometry + decomposition machinery.

## Practical Recommendation
1. Use `main.py` as the primary submission codebase if you need the full pipeline in Python.
2. Keep `main2.py` as a compact experimental file for trying ideas quickly.
3. Keep `main.cpp` as the C++ reference/backup implementation path.
