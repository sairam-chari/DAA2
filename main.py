from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from math import floor
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import sys

try:
	import matplotlib

	matplotlib.use("Agg")
	import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - plotting is optional at runtime
	plt = None


_uid_gen = count()


@dataclass(frozen=True)
class Vertex:
	x: int
	y: int
	uid: int


@dataclass
class Polygon:
	vertices: List[Vertex]
	is_hole: bool = False


@dataclass(frozen=True)
class Triangle:
	a: Vertex
	b: Vertex
	c: Vertex


def same_point(a: Vertex, b: Vertex) -> bool:
	return a.x == b.x and a.y == b.y


def cross(a: Vertex, b: Vertex, c: Vertex) -> int:
	return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def orientation(a: Vertex, b: Vertex, c: Vertex) -> int:
	value = cross(a, b, c)
	if value > 0:
		return 1
	if value < 0:
		return -1
	return 0


def polygon_area2(vertices: Sequence[Vertex]) -> int:
	area = 0
	n = len(vertices)
	for i in range(n):
		a = vertices[i]
		b = vertices[(i + 1) % n]
		area += a.x * b.y - a.y * b.x
	return area


def ensure_ccw(vertices: List[Vertex]) -> List[Vertex]:
	if polygon_area2(vertices) < 0:
		return list(reversed(vertices))
	return vertices


def ensure_cw(vertices: List[Vertex]) -> List[Vertex]:
	if polygon_area2(vertices) > 0:
		return list(reversed(vertices))
	return vertices


def remove_consecutive_duplicates(vertices: List[Vertex]) -> List[Vertex]:
	cleaned: List[Vertex] = []
	for v in vertices:
		if not cleaned or not same_point(cleaned[-1], v):
			cleaned.append(v)
	if len(cleaned) > 1 and same_point(cleaned[0], cleaned[-1]):
		cleaned.pop()
	return cleaned


def on_segment(a: Vertex, b: Vertex, p: Vertex) -> bool:
	if orientation(a, b, p) != 0:
		return False
	return (
		min(a.x, b.x) <= p.x <= max(a.x, b.x)
		and min(a.y, b.y) <= p.y <= max(a.y, b.y)
	)


def segments_intersect(a: Vertex, b: Vertex, c: Vertex, d: Vertex) -> bool:
	o1 = orientation(a, b, c)
	o2 = orientation(a, b, d)
	o3 = orientation(c, d, a)
	o4 = orientation(c, d, b)

	if o1 == 0 and on_segment(a, b, c):
		return True
	if o2 == 0 and on_segment(a, b, d):
		return True
	if o3 == 0 and on_segment(c, d, a):
		return True
	if o4 == 0 and on_segment(c, d, b):
		return True

	return (o1 * o2 < 0) and (o3 * o4 < 0)


def point_in_ring(point: Vertex, ring: Sequence[Vertex]) -> bool:
	inside = False
	n = len(ring)
	for i in range(n):
		a = ring[i]
		b = ring[(i + 1) % n]
		if on_segment(a, b, point):
			return True
		intersects = ((a.y > point.y) != (b.y > point.y)) and (
			point.x
			< (b.x - a.x) * (point.y - a.y) / (b.y - a.y + 0.0) + a.x
		)
		if intersects:
			inside = not inside
	return inside


def point_in_region(point: Vertex, polygons: Sequence[Polygon]) -> bool:
	if not polygons:
		return False
	if not point_in_ring(point, polygons[0].vertices):
		return False
	for hole in polygons[1:]:
		if point_in_ring(point, hole.vertices):
			return False
	return True


def visible_bridge(a: Vertex, b: Vertex, polygons: Sequence[Polygon]) -> bool:
	if same_point(a, b):
		return False

	for polygon in polygons:
		ring = polygon.vertices
		n = len(ring)
		for i in range(n):
			c = ring[i]
			d = ring[(i + 1) % n]
			if c.uid in {a.uid, b.uid} or d.uid in {a.uid, b.uid}:
				continue
			if same_point(c, a) or same_point(c, b) or same_point(d, a) or same_point(d, b):
				continue
			if segments_intersect(a, b, c, d):
				return False

	midpoint = Vertex((a.x + b.x) // 2, (a.y + b.y) // 2, next(_uid_gen))
	return point_in_region(midpoint, polygons)


def rightmost_vertex_index(ring: Sequence[Vertex]) -> int:
	best = 0
	for i in range(1, len(ring)):
		if (ring[i].x > ring[best].x) or (ring[i].x == ring[best].x and ring[i].y > ring[best].y):
			best = i
	return best


def choose_bridge_vertex(outer: Sequence[Vertex], hole_vertex: Vertex, polygons: Sequence[Polygon]) -> int:
	candidates: List[Tuple[Tuple[int, int], int]] = []
	for i, candidate in enumerate(outer):
		if not visible_bridge(hole_vertex, candidate, polygons):
			continue
		# Prefer a vertex to the right of the hole vertex; otherwise any visible one.
		if candidate.x >= hole_vertex.x:
			candidates.append(((candidate.x, candidate.y), i))
	candidates.sort(key=lambda item: item[0])
	return candidates[0][1]


def stitch_hole_into_polygon(outer: List[Vertex], hole: List[Vertex], outer_index: int, hole_index: int) -> List[Vertex]:
	# We duplicate the bridge endpoints as distinct boundary occurrences.
	outer_vertex = outer[outer_index]
	hole_vertex = hole[hole_index]

	hole_cycle: List[Vertex] = [Vertex(hole_vertex.x, hole_vertex.y, next(_uid_gen))]
	j = (hole_index - 1) % len(hole)
	while j != hole_index:
		hole_cycle.append(hole[j])
		j = (j - 1) % len(hole)
	hole_cycle.append(Vertex(hole_vertex.x, hole_vertex.y, next(_uid_gen)))
	hole_cycle.append(Vertex(outer_vertex.x, outer_vertex.y, next(_uid_gen)))

	stitched = list(outer[: outer_index + 1]) + hole_cycle + list(outer[outer_index + 1 :])
	return remove_consecutive_duplicates(stitched)


def bridge_holes(polygons: List[Polygon]) -> Tuple[List[Vertex], List[Tuple[Vertex, Vertex]]]:
	outer = ensure_ccw(remove_consecutive_duplicates(polygons[0].vertices))
	current_polygons = [Polygon(list(outer), False)] + [Polygon(list(h.vertices), True) for h in polygons[1:]]
	bridges: List[Tuple[Vertex, Vertex]] = []

	merged = list(outer)
	for hole in polygons[1:]:
		hole_vertices = ensure_cw(remove_consecutive_duplicates(hole.vertices))
		hole_vertex_index = rightmost_vertex_index(hole_vertices)
		hole_vertex = hole_vertices[hole_vertex_index]

		bridge_index = choose_bridge_vertex(merged, hole_vertex, current_polygons)

		outer_vertex = merged[bridge_index]
		bridges.append((outer_vertex, hole_vertex))

		merged = stitch_hole_into_polygon(merged, hole_vertices, bridge_index, hole_vertex_index)
		current_polygons[0] = Polygon(list(merged), False)

	return merged, bridges


def classify_vertex(index: int, polygon: Sequence[Vertex]) -> str:
	n = len(polygon)
	prev_v = polygon[(index - 1) % n]
	curr = polygon[index]
	next_v = polygon[(index + 1) % n]

	prev_above = (prev_v.y > curr.y) or (prev_v.y == curr.y and prev_v.x < curr.x)
	next_above = (next_v.y > curr.y) or (next_v.y == curr.y and next_v.x < curr.x)
	turn = orientation(prev_v, curr, next_v)

	if not prev_above and not next_above:
		return "start" if turn > 0 else "split"
	if prev_above and next_above:
		return "end" if turn > 0 else "merge"
	return "regular"


def edge_x_at_y(a: Vertex, b: Vertex, y: float) -> float:
	if a.y == b.y:
		return float(min(a.x, b.x))
	return a.x + (y - a.y) * (b.x - a.x) / (b.y - a.y)


def edge_crosses_sweep(a: Vertex, b: Vertex, y: float) -> bool:
	lo = min(a.y, b.y)
	hi = max(a.y, b.y)
	return lo < y < hi


def sort_status(status: List[int], polygon: Sequence[Vertex], sweep_y: float) -> None:
	status.sort(key=lambda edge_start: edge_x_at_y(polygon[edge_start], polygon[(edge_start + 1) % len(polygon)], sweep_y))


def find_left_edge(status: List[int], polygon: Sequence[Vertex], sweep_y: float, x: float) -> Optional[int]:
	left_edge: Optional[int] = None
	left_x = float("-inf")
	for edge_start in status:
		a = polygon[edge_start]
		b = polygon[(edge_start + 1) % len(polygon)]
		if not edge_crosses_sweep(a, b, sweep_y):
			continue
		ex = edge_x_at_y(a, b, sweep_y)
		if ex <= x and ex > left_x:
			left_x = ex
			left_edge = edge_start
	return left_edge


def sweep_line_monotone_diagonals(polygon: Sequence[Vertex]) -> List[Tuple[int, int]]:
	# Standard sweep-line partitioning. We keep the status as an ordered list,
	# which is practical and clear for assignment-sized inputs.
	n = len(polygon)
	order = sorted(range(n), key=lambda i: (-polygon[i].y, polygon[i].x, polygon[i].uid))
	helper: Dict[int, int] = {}
	status: List[int] = []
	diagonals: List[Tuple[int, int]] = []

	def add_diagonal(a: int, b: int) -> None:
		if a == b:
			return
		if a > b:
			a, b = b, a
		pair = (a, b)
		if pair not in diagonals:
			diagonals.append(pair)

	def remove_edge(edge_start: int) -> None:
		if edge_start in status:
			status.remove(edge_start)

	for idx in order:
		y = polygon[idx].y - 0.5
		sort_status(status, polygon, y)

		prev_idx = (idx - 1) % n
		next_idx = (idx + 1) % n
		prev_edge = prev_idx
		next_edge = idx
		kind = classify_vertex(idx, polygon)

		if kind == "start":
			status.append(next_edge)
			helper[next_edge] = idx
		elif kind == "split":
			left_edge = find_left_edge(status, polygon, y, polygon[idx].x)
			if left_edge is not None and left_edge in helper:
				add_diagonal(idx, helper[left_edge])
				helper[left_edge] = idx
			status.append(next_edge)
			helper[next_edge] = idx
		elif kind == "end":
			if prev_edge in helper and classify_vertex(helper[prev_edge], polygon) == "merge":
				add_diagonal(idx, helper[prev_edge])
			remove_edge(prev_edge)
		elif kind == "merge":
			if prev_edge in helper and classify_vertex(helper[prev_edge], polygon) == "merge":
				add_diagonal(idx, helper[prev_edge])
			remove_edge(prev_edge)
			left_edge = find_left_edge(status, polygon, y, polygon[idx].x)
			if left_edge is not None:
				if left_edge in helper and classify_vertex(helper[left_edge], polygon) == "merge":
					add_diagonal(idx, helper[left_edge])
				helper[left_edge] = idx
		else:
			# Regular vertices are processed depending on whether the outgoing edge goes downward.
			if polygon[next_idx].y < polygon[idx].y or (
				polygon[next_idx].y == polygon[idx].y and polygon[next_idx].x > polygon[idx].x
			):
				if prev_edge in helper and classify_vertex(helper[prev_edge], polygon) == "merge":
					add_diagonal(idx, helper[prev_edge])
				remove_edge(prev_edge)
				status.append(next_edge)
				helper[next_edge] = idx
			else:
				left_edge = find_left_edge(status, polygon, y, polygon[idx].x)
				if left_edge is not None:
					if left_edge in helper and classify_vertex(helper[left_edge], polygon) == "merge":
						add_diagonal(idx, helper[left_edge])
					helper[left_edge] = idx

	return diagonals


def split_polygon_by_diagonal(piece: List[Vertex], a_uid: int, b_uid: int) -> Optional[Tuple[List[Vertex], List[Vertex]]]:
	indices = [i for i, v in enumerate(piece) if v.uid in {a_uid, b_uid}]
	if len(indices) < 2:
		return None
	ia = next((i for i, v in enumerate(piece) if v.uid == a_uid), None)
	ib = next((i for i, v in enumerate(piece) if v.uid == b_uid), None)
	if ia is None or ib is None or ia == ib:
		return None

	n = len(piece)
	first: List[Vertex] = []
	i = ia
	while True:
		first.append(piece[i])
		if i == ib:
			break
		i = (i + 1) % n

	second: List[Vertex] = []
	i = ib
	while True:
		second.append(piece[i])
		if i == ia:
			break
		i = (i + 1) % n

	first = remove_consecutive_duplicates(first)
	second = remove_consecutive_duplicates(second)
	return first, second


def decompose_to_monotone_pieces(polygon: List[Vertex]) -> List[List[Vertex]]:
	polygon = ensure_ccw(remove_consecutive_duplicates(polygon))
	diagonals = sweep_line_monotone_diagonals(polygon)
	pieces = [polygon]

	for a_idx, b_idx in diagonals:
		a_uid = polygon[a_idx].uid
		b_uid = polygon[b_idx].uid
		new_pieces: List[List[Vertex]] = []
		split_done = False
		for piece in pieces:
			if split_done:
				new_pieces.append(piece)
				continue
			has_a = any(v.uid == a_uid for v in piece)
			has_b = any(v.uid == b_uid for v in piece)
			if not (has_a and has_b):
				new_pieces.append(piece)
				continue
			split = split_polygon_by_diagonal(piece, a_uid, b_uid)
			if split is None:
				new_pieces.append(piece)
				continue
			left, right = split
			new_pieces.append(left)
			new_pieces.append(right)
			split_done = True
		pieces = new_pieces

	return [p for p in pieces if len(p) >= 3]


def triangulate_y_monotone(piece: List[Vertex]) -> List[Triangle]:
	piece = ensure_ccw(remove_consecutive_duplicates(piece))
	n = len(piece)
	if n < 3:
		return []
	if n == 3:
		return [Triangle(piece[0], piece[1], piece[2])]

	# Top-most and bottom-most vertices for chain extraction.
	top = max(range(n), key=lambda i: (piece[i].y, -piece[i].x, -piece[i].uid))
	bottom = min(range(n), key=lambda i: (piece[i].y, piece[i].x, piece[i].uid))

	left_chain: set[int] = set()
	i = top
	while i != bottom:
		left_chain.add(i)
		i = (i + 1) % n
	left_chain.add(bottom)

	right_chain = set(range(n)) - left_chain

	order = sorted(range(n), key=lambda i: (-piece[i].y, piece[i].x, piece[i].uid))
	stack: List[int] = [order[0], order[1]]
	triangles: List[Triangle] = []

	def same_chain(u: int, v: int) -> bool:
		return (u in left_chain and v in left_chain) or (u in right_chain and v in right_chain)

	for k in range(2, n - 1):
		curr = order[k]
		if not same_chain(curr, stack[-1]):
			while len(stack) > 1:
				u = stack.pop()
				triangles.append(Triangle(piece[curr], piece[u], piece[stack[-1]]))
			stack = [order[k - 1], curr]
		else:
			u = stack.pop()
			while stack:
				v = stack[-1]
				turn = orientation(piece[curr], piece[u], piece[v])
				if curr in left_chain:
					if turn > 0:
						triangles.append(Triangle(piece[curr], piece[u], piece[v]))
						u = stack.pop()
					else:
						break
				else:
					if turn < 0:
						triangles.append(Triangle(piece[curr], piece[u], piece[v]))
						u = stack.pop()
					else:
						break
			stack.append(u)
			stack.append(curr)

	last = order[-1]
	stack.pop()
	while len(stack) > 1:
		u = stack.pop()
		triangles.append(Triangle(piece[last], piece[u], piece[stack[-1]]))

	# Filter accidental collinear triangles from degenerate monotone pieces.
	filtered: List[Triangle] = []
	for tri in triangles:
		if orientation(tri.a, tri.b, tri.c) != 0:
			filtered.append(tri)
	return filtered


def triangulate_polygon_with_holes(polygons: List[Polygon]) -> Tuple[List[Triangle], List[Vertex], List[Tuple[Vertex, Vertex]]]:
	merged, bridges = bridge_holes(polygons)
	triangles = ear_clip_triangulation(merged)

	valid_triangles: List[Triangle] = []
	for tri in triangles:
		if triangle_is_walkable(tri, polygons):
			valid_triangles.append(tri)

	return valid_triangles, merged, bridges


def triangle_vertices(triangles: Sequence[Triangle]) -> List[Vertex]:
	seen: set[int] = set()
	result: List[Vertex] = []
	for tri in triangles:
		for v in (tri.a, tri.b, tri.c):
			if v.uid not in seen:
				seen.add(v.uid)
				result.append(v)
	return result


def point_in_triangle(p: Vertex, a: Vertex, b: Vertex, c: Vertex) -> bool:
	c1 = orientation(a, b, p)
	c2 = orientation(b, c, p)
	c3 = orientation(c, a, p)
	has_neg = c1 < 0 or c2 < 0 or c3 < 0
	has_pos = c1 > 0 or c2 > 0 or c3 > 0
	return not (has_neg and has_pos)


def point_strictly_in_triangle(p: Vertex, a: Vertex, b: Vertex, c: Vertex) -> bool:
	c1 = orientation(a, b, p)
	c2 = orientation(b, c, p)
	c3 = orientation(c, a, p)
	if c1 == 0 or c2 == 0 or c3 == 0:
		return False
	all_pos = c1 > 0 and c2 > 0 and c3 > 0
	all_neg = c1 < 0 and c2 < 0 and c3 < 0
	return all_pos or all_neg


def triangle_is_walkable(tri: Triangle, polygons: Sequence[Polygon]) -> bool:
	if orientation(tri.a, tri.b, tri.c) == 0:
		return False

	cx = (tri.a.x + tri.b.x + tri.c.x) // 3
	cy = (tri.a.y + tri.b.y + tri.c.y) // 3
	centroid = Vertex(cx, cy, -1)
	if not point_in_region(centroid, polygons):
		return False

	tri_edges = [(tri.a, tri.b), (tri.b, tri.c), (tri.c, tri.a)]
	for poly in polygons:
		rv = poly.vertices
		for i in range(len(rv)):
			p1 = rv[i]
			p2 = rv[(i + 1) % len(rv)]
			for e1, e2 in tri_edges:
				if segments_intersect(e1, e2, p1, p2):
					shared = same_point(e1, p1) or same_point(e1, p2) or same_point(e2, p1) or same_point(e2, p2)
					if not shared:
						return False

	return True


def ear_clip_triangulation(polygon: List[Vertex]) -> List[Triangle]:
	polygon = ensure_ccw(remove_consecutive_duplicates(polygon))
	if len(polygon) < 3:
		return []

	idxs = list(range(len(polygon)))
	triangles: List[Triangle] = []

	def is_ear(i_pos: int) -> bool:
		prev_i = idxs[(i_pos - 1) % len(idxs)]
		cur_i = idxs[i_pos]
		next_i = idxs[(i_pos + 1) % len(idxs)]
		a, b, c = polygon[prev_i], polygon[cur_i], polygon[next_i]
		if orientation(a, b, c) <= 0:
			return False
		tri = (a, b, c)
		for j in idxs:
			if j in {prev_i, cur_i, next_i}:
				continue
			if point_strictly_in_triangle(polygon[j], *tri):
				return False
		return True

	while len(idxs) > 3:
		clipped = False
		for i in range(len(idxs)):
			if is_ear(i):
				prev_i = idxs[(i - 1) % len(idxs)]
				cur_i = idxs[i]
				next_i = idxs[(i + 1) % len(idxs)]
				triangles.append(Triangle(polygon[prev_i], polygon[cur_i], polygon[next_i]))
				idxs.pop(i)
				clipped = True
				break
		if not clipped:
			break

	if len(idxs) == 3:
		triangles.append(Triangle(polygon[idxs[0]], polygon[idxs[1]], polygon[idxs[2]]))
	return triangles


def build_graph_from_triangles(triangles: Sequence[Triangle]) -> Dict[int, set[int]]:
	graph: Dict[int, set[int]] = defaultdict(set)
	for tri in triangles:
		verts = [tri.a, tri.b, tri.c]
		for i in range(3):
			for j in range(i + 1, 3):
				u, v = verts[i], verts[j]
				graph[u.uid].add(v.uid)
				graph[v.uid].add(u.uid)
	return graph


def color_outerplanar_graph(vertices: Sequence[Vertex], triangles: Sequence[Triangle]) -> Dict[int, int]:
	graph = build_graph_from_triangles(triangles)
	all_uids = {v.uid for v in vertices}
	for uid in all_uids:
		graph.setdefault(uid, set())

	# Degeneracy-style removal; outerplanar triangulation graphs are 2-degenerate.
	remaining = set(all_uids)
	removal_order: List[int] = []
	while remaining:
		picked = min(remaining, key=lambda uid: (len(graph[uid]), uid))
		removal_order.append(picked)
		remaining.remove(picked)
		for nbr in list(graph[picked]):
			graph[nbr].discard(picked)
		graph[picked].clear()

	color_of: Dict[int, int] = {}
	graph = build_graph_from_triangles(triangles)
	for uid in all_uids:
		graph.setdefault(uid, set())

	for uid in reversed(removal_order):
		used = {color_of[nbr] for nbr in graph[uid] if nbr in color_of}
		for color in range(3):
			if color not in used:
				color_of[uid] = color
				break
		else:
			color_of[uid] = 0
	return color_of


def choose_guard_positions(vertices: Sequence[Vertex], triangles: Sequence[Triangle], k: int) -> List[Vertex]:
	color_of = color_outerplanar_graph(vertices, triangles)
	buckets: Dict[int, List[Vertex]] = defaultdict(list)
	seen: set[int] = set()
	for v in vertices:
		if v.uid in seen:
			continue
		seen.add(v.uid)
		buckets[color_of.get(v.uid, 0)].append(v)

	best_color = min(buckets, key=lambda c: len(buckets[c])) if buckets else 0
	guards = buckets.get(best_color, [])[:k]
	if len(guards) < k:
		used = {v.uid for v in guards}
		for v in vertices:
			if v.uid not in used:
				guards.append(v)
				used.add(v.uid)
				if len(guards) == k:
					break
	return guards[:k]


def parse_input() -> List[List[Polygon]]:
	data = list(map(int, sys.stdin.buffer.read().split()))
	if not data:
		return []

	idx = 0
	t = data[idx]
	idx += 1
	cases: List[List[Polygon]] = []

	for _ in range(t):
		v0 = data[idx]
		idx += 1
		outer_vertices: List[Vertex] = []
		for _ in range(v0):
			x, y = data[idx], data[idx + 1]
			idx += 2
			outer_vertices.append(Vertex(x, y, next(_uid_gen)))

		h = data[idx]
		idx += 1
		polygons = [Polygon(outer_vertices, False)]

		for _ in range(h):
			vi = data[idx]
			idx += 1
			hole_vertices: List[Vertex] = []
			for _ in range(vi):
				x, y = data[idx], data[idx + 1]
				idx += 2
				hole_vertices.append(Vertex(x, y, next(_uid_gen)))
			polygons.append(Polygon(hole_vertices, True))

		cases.append(polygons)
	return cases


def plot_case(
	case_id: int,
	polygons: Sequence[Polygon],
	merged: Sequence[Vertex],
	triangles: Sequence[Triangle],
	guards: Sequence[Vertex],
	bridges: Sequence[Tuple[Vertex, Vertex]],
) -> str:
	if plt is None:
		return "plotting unavailable"

	fig, ax = plt.subplots(figsize=(10, 8))
	ax.set_aspect("equal", adjustable="box")
	ax.set_title(f"Polygon triangulation - case {case_id}")

	def draw_ring(vertices: Sequence[Vertex], color: str, linestyle: str, alpha: float = 1.0) -> None:
		xs = [v.x for v in vertices] + [vertices[0].x]
		ys = [v.y for v in vertices] + [vertices[0].y]
		ax.plot(xs, ys, color=color, linestyle=linestyle, linewidth=2, alpha=alpha)

	# Original geometry.
	draw_ring(polygons[0].vertices, "black", "-", 1.0)
	for hole in polygons[1:]:
		draw_ring(hole.vertices, "#b22222", "--", 0.9)

	# Triangles.
	for tri in triangles:
		xs = [tri.a.x, tri.b.x, tri.c.x, tri.a.x]
		ys = [tri.a.y, tri.b.y, tri.c.y, tri.a.y]
		ax.plot(xs, ys, color="#1f77b4", linewidth=1, alpha=0.7)

	# Bridging segments.
	for a, b in bridges:
		ax.plot([a.x, b.x], [a.y, b.y], color="#888888", linestyle=":", linewidth=1)

	# Guard positions.
	if guards:
		ax.scatter([g.x for g in guards], [g.y for g in guards], color="#2ca02c", s=60, zorder=5)

	all_x = [v.x for poly in polygons for v in poly.vertices] + [v.x for v in merged]
	all_y = [v.y for poly in polygons for v in poly.vertices] + [v.y for v in merged]
	if all_x and all_y:
		pad_x = max(1, (max(all_x) - min(all_x)) // 10 + 1)
		pad_y = max(1, (max(all_y) - min(all_y)) // 10 + 1)
		ax.set_xlim(min(all_x) - pad_x, max(all_x) + pad_x)
		ax.set_ylim(min(all_y) - pad_y, max(all_y) + pad_y)

	ax.grid(True, linestyle="--", alpha=0.25)
	output_path = f"triangulation_case_{case_id}.png"
	fig.tight_layout()
	fig.savefig(output_path, dpi=200)
	plt.close(fig)
	return output_path


def format_triangle(tri: Triangle) -> str:
	return f"({tri.a.x}, {tri.a.y}) ({tri.b.x}, {tri.b.y}) ({tri.c.x}, {tri.c.y})"


def format_vertex(v: Vertex) -> str:
	return f"({v.x}, {v.y})"


def solve() -> None:
	cases = parse_input()
	if not cases:
		return

	out_lines: List[str] = []
	for case_id, polygons in enumerate(cases, start=1):
		triangles, merged, bridges = triangulate_polygon_with_holes(polygons)
		guard_vertices = triangle_vertices(triangles)

		n = sum(len(poly.vertices) for poly in polygons)
		h = max(0, len(polygons) - 1)
		k = floor((n + 2 * h) / 3)
		guards = choose_guard_positions(guard_vertices, triangles, k)
		plot_path = plot_case(case_id, polygons, merged, triangles, guards, bridges)

		out_lines.append(f"Case {case_id}")
		out_lines.append(f"Triangles: {len(triangles)}")
		for tri in triangles:
			out_lines.append(format_triangle(tri))
		out_lines.append(f"k = {k}")
		out_lines.append(f"Guards: {len(guards)}")
		for guard in guards:
			out_lines.append(format_vertex(guard))
		out_lines.append(f"Plot: {plot_path}")
		if case_id != len(cases):
			out_lines.append("")

	sys.stdout.write("\n".join(out_lines))


if __name__ == "__main__":
	solve()
