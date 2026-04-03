from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import count
from math import floor
from typing import Dict, List, Sequence, Tuple

import sys

try:
	import matplotlib

	matplotlib.use("Agg")
	import matplotlib.pyplot as plt
except Exception:
	plt = None

_id = count()


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


def orient(a: Vertex, b: Vertex, c: Vertex) -> int:
	v = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
	return 1 if v > 0 else (-1 if v < 0 else 0)


def area2(poly: Sequence[Vertex]) -> int:
	return sum(poly[i].x * poly[(i + 1) % len(poly)].y - poly[i].y * poly[(i + 1) % len(poly)].x for i in range(len(poly)))


def same(a: Vertex, b: Vertex) -> bool:
	return a.x == b.x and a.y == b.y


def dedup(poly: List[Vertex]) -> List[Vertex]:
	out: List[Vertex] = []
	for p in poly:
		if not out or not same(out[-1], p):
			out.append(p)
	if len(out) > 1 and same(out[0], out[-1]):
		out.pop()
	return out


def ccw(poly: List[Vertex]) -> List[Vertex]:
	poly = dedup(poly)
	return list(reversed(poly)) if area2(poly) < 0 else poly


def cw(poly: List[Vertex]) -> List[Vertex]:
	poly = dedup(poly)
	return list(reversed(poly)) if area2(poly) > 0 else poly


def on_seg(a: Vertex, b: Vertex, p: Vertex) -> bool:
	return orient(a, b, p) == 0 and min(a.x, b.x) <= p.x <= max(a.x, b.x) and min(a.y, b.y) <= p.y <= max(a.y, b.y)


def seg_inter(a: Vertex, b: Vertex, c: Vertex, d: Vertex) -> bool:
	o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
	if o1 == 0 and on_seg(a, b, c):
		return True
	if o2 == 0 and on_seg(a, b, d):
		return True
	if o3 == 0 and on_seg(c, d, a):
		return True
	if o4 == 0 and on_seg(c, d, b):
		return True
	return o1 * o2 < 0 and o3 * o4 < 0


def in_ring(p: Vertex, ring: Sequence[Vertex]) -> bool:
	inside = False
	for i in range(len(ring)):
		a, b = ring[i], ring[(i + 1) % len(ring)]
		if on_seg(a, b, p):
			return True
		if ((a.y > p.y) != (b.y > p.y)) and p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y + 0.0) + a.x:
			inside = not inside
	return inside


def in_region(p: Vertex, polys: Sequence[Polygon]) -> bool:
	return bool(polys) and in_ring(p, polys[0].vertices) and all(not in_ring(p, h.vertices) for h in polys[1:])


def visible(a: Vertex, b: Vertex, polys: Sequence[Polygon]) -> bool:
	if same(a, b):
		return False
	for poly in polys:
		for i in range(len(poly.vertices)):
			c, d = poly.vertices[i], poly.vertices[(i + 1) % len(poly.vertices)]
			if same(c, a) or same(c, b) or same(d, a) or same(d, b):
				continue
			if seg_inter(a, b, c, d):
				return False
	m = Vertex((a.x + b.x) // 2, (a.y + b.y) // 2, next(_id))
	return in_region(m, polys)


def rightmost(r: Sequence[Vertex]) -> int:
	return max(range(len(r)), key=lambda i: (r[i].x, r[i].y))


def stitch(outer: List[Vertex], hole: List[Vertex], oi: int, hi: int) -> List[Vertex]:
	o, h = outer[oi], hole[hi]
	cycle = [Vertex(h.x, h.y, next(_id))]
	j = (hi - 1) % len(hole)
	while j != hi:
		cycle.append(hole[j])
		j = (j - 1) % len(hole)
	cycle += [Vertex(h.x, h.y, next(_id)), Vertex(o.x, o.y, next(_id))]
	return dedup(outer[: oi + 1] + cycle + outer[oi + 1 :])


def bridge_holes(polys: List[Polygon]) -> Tuple[List[Vertex], List[Tuple[Vertex, Vertex]]]:
	merged = ccw(polys[0].vertices)
	state = [Polygon(list(merged), False)] + [Polygon(list(h.vertices), True) for h in polys[1:]]
	bridges: List[Tuple[Vertex, Vertex]] = []
	for h in polys[1:]:
		hole = cw(h.vertices)
		hi = rightmost(hole)
		hv = hole[hi]
		cand = [(v.x, v.y, i) for i, v in enumerate(merged) if v.x >= hv.x and visible(hv, v, state)]
		oi = min(cand)[2]
		bridges.append((merged[oi], hv))
		merged = stitch(merged, hole, oi, hi)
		state[0] = Polygon(list(merged), False)
	return merged, bridges


def vtype(i: int, p: Sequence[Vertex]) -> str:
	n = len(p)
	pr, cu, nx = p[(i - 1) % n], p[i], p[(i + 1) % n]
	ab = lambda u, v: (u.y > v.y) or (u.y == v.y and u.x < v.x)
	pa, na, t = ab(pr, cu), ab(nx, cu), orient(pr, cu, nx)
	if not pa and not na:
		return "start" if t > 0 else "split"
	if pa and na:
		return "end" if t > 0 else "merge"
	return "regular"


def x_at(p: Sequence[Vertex], e: int, y: float) -> float:
	a, b = p[e], p[(e + 1) % len(p)]
	return float(min(a.x, b.x)) if a.y == b.y else a.x + (y - a.y) * (b.x - a.x) / (b.y - a.y)


def crosses(a: Vertex, b: Vertex, y: float) -> bool:
	return min(a.y, b.y) < y < max(a.y, b.y)


def left_edge(status: List[int], p: Sequence[Vertex], y: float, x: float) -> int | None:
	best, bestx = None, float("-inf")
	for e in status:
		a, b = p[e], p[(e + 1) % len(p)]
		if not crosses(a, b, y):
			continue
		ex = x_at(p, e, y)
		if ex <= x and ex > bestx:
			best, bestx = e, ex
	return best


def sweep_diagonals(p: Sequence[Vertex]) -> List[Tuple[int, int]]:
	n = len(p)
	order = sorted(range(n), key=lambda i: (-p[i].y, p[i].x, p[i].uid))
	helper: Dict[int, int] = {}
	status: List[int] = []
	ds: List[Tuple[int, int]] = []

	def add(a: int, b: int) -> None:
		if a != b:
			ds.append((a, b) if a < b else (b, a))

	for i in order:
		y = p[i].y - 0.5
		status.sort(key=lambda e: x_at(p, e, y))
		pr, nx, t = (i - 1) % n, (i + 1) % n, vtype(i, p)
		if t == "start":
			status.append(i)
			helper[i] = i
		elif t == "split":
			le = left_edge(status, p, y, p[i].x)
			if le is not None and le in helper:
				add(i, helper[le])
				helper[le] = i
			status.append(i)
			helper[i] = i
		elif t == "end":
			if pr in helper and vtype(helper[pr], p) == "merge":
				add(i, helper[pr])
			if pr in status:
				status.remove(pr)
		elif t == "merge":
			if pr in helper and vtype(helper[pr], p) == "merge":
				add(i, helper[pr])
			if pr in status:
				status.remove(pr)
			le = left_edge(status, p, y, p[i].x)
			if le is not None:
				if le in helper and vtype(helper[le], p) == "merge":
					add(i, helper[le])
				helper[le] = i
		else:
			down = p[nx].y < p[i].y or (p[nx].y == p[i].y and p[nx].x > p[i].x)
			if down:
				if pr in helper and vtype(helper[pr], p) == "merge":
					add(i, helper[pr])
				if pr in status:
					status.remove(pr)
				status.append(i)
				helper[i] = i
			else:
				le = left_edge(status, p, y, p[i].x)
				if le is not None:
					if le in helper and vtype(helper[le], p) == "merge":
						add(i, helper[le])
					helper[le] = i
	return list(dict.fromkeys(ds))


def split_piece(piece: List[Vertex], a_uid: int, b_uid: int) -> Tuple[List[Vertex], List[Vertex]] | None:
	ia = next((i for i, v in enumerate(piece) if v.uid == a_uid), None)
	ib = next((i for i, v in enumerate(piece) if v.uid == b_uid), None)
	if ia is None or ib is None or ia == ib:
		return None
	n = len(piece)
	a, i = [], ia
	while True:
		a.append(piece[i])
		if i == ib:
			break
		i = (i + 1) % n
	b, i = [], ib
	while True:
		b.append(piece[i])
		if i == ia:
			break
		i = (i + 1) % n
	return dedup(a), dedup(b)


def decompose(poly: List[Vertex]) -> List[List[Vertex]]:
	poly = ccw(poly)
	pieces = [poly]
	for a, b in sweep_diagonals(poly):
		ua, ub = poly[a].uid, poly[b].uid
		next_pieces: List[List[Vertex]] = []
		split_done = False
		for pc in pieces:
			if split_done or not any(v.uid == ua for v in pc) or not any(v.uid == ub for v in pc):
				next_pieces.append(pc)
				continue
			s = split_piece(pc, ua, ub)
			if s is None:
				next_pieces.append(pc)
			else:
				next_pieces.extend(s)
				split_done = True
		pieces = next_pieces
	return [p for p in pieces if len(p) >= 3]


def triangulate_monotone(piece: List[Vertex]) -> List[Triangle]:
	piece = ccw(piece)
	n = len(piece)
	if n < 3:
		return []
	if n == 3:
		return [Triangle(piece[0], piece[1], piece[2])]
	top = max(range(n), key=lambda i: (piece[i].y, -piece[i].x, -piece[i].uid))
	bot = min(range(n), key=lambda i: (piece[i].y, piece[i].x, piece[i].uid))
	left, i = set(), top
	while i != bot:
		left.add(i)
		i = (i + 1) % n
	left.add(bot)
	right = set(range(n)) - left
	ordv = sorted(range(n), key=lambda i: (-piece[i].y, piece[i].x, piece[i].uid))
	st, tris = [ordv[0], ordv[1]], []

	def same_chain(u: int, v: int) -> bool:
		return (u in left and v in left) or (u in right and v in right)

	for k in range(2, n - 1):
		cur = ordv[k]
		if not same_chain(cur, st[-1]):
			while len(st) > 1:
				u = st.pop()
				tris.append(Triangle(piece[cur], piece[u], piece[st[-1]]))
			st = [ordv[k - 1], cur]
		else:
			u = st.pop()
			while st:
				v = st[-1]
				turn = orient(piece[cur], piece[u], piece[v])
				ok = (cur in left and turn > 0) or (cur in right and turn < 0)
				if not ok:
					break
				tris.append(Triangle(piece[cur], piece[u], piece[v]))
				u = st.pop()
			st += [u, cur]
	last = ordv[-1]
	st.pop()
	while len(st) > 1:
		u = st.pop()
		tris.append(Triangle(piece[last], piece[u], piece[st[-1]]))
	return [t for t in tris if orient(t.a, t.b, t.c) != 0]


def tri_ok(t: Triangle, polys: Sequence[Polygon]) -> bool:
	if orient(t.a, t.b, t.c) == 0:
		return False
	m = Vertex((t.a.x + t.b.x + t.c.x) // 3, (t.a.y + t.b.y + t.c.y) // 3, -1)
	if not in_region(m, polys):
		return False
	edges = [(t.a, t.b), (t.b, t.c), (t.c, t.a)]
	for poly in polys:
		for i in range(len(poly.vertices)):
			p1, p2 = poly.vertices[i], poly.vertices[(i + 1) % len(poly.vertices)]
			for e1, e2 in edges:
				if seg_inter(e1, e2, p1, p2):
					shared = same(e1, p1) or same(e1, p2) or same(e2, p1) or same(e2, p2)
					if not shared:
						return False
	return True


def triangulate_with_holes(polys: List[Polygon]) -> Tuple[List[Triangle], List[Vertex], List[Tuple[Vertex, Vertex]]]:
	merged, bridges = bridge_holes(polys)
	tris: List[Triangle] = []
	for pc in decompose(merged):
		tris.extend(triangulate_monotone(pc))
	return [t for t in tris if tri_ok(t, polys)], merged, bridges


def guard_vertices(tris: Sequence[Triangle]) -> List[Vertex]:
	seen, out = set(), []
	for t in tris:
		for v in (t.a, t.b, t.c):
			if v.uid not in seen:
				seen.add(v.uid)
				out.append(v)
	return out


def choose_guards(verts: Sequence[Vertex], tris: Sequence[Triangle], k: int) -> List[Vertex]:
	g: Dict[int, set[int]] = defaultdict(set)
	for t in tris:
		for u, v in ((t.a, t.b), (t.b, t.c), (t.c, t.a)):
			g[u.uid].add(v.uid)
			g[v.uid].add(u.uid)
	uids = {v.uid for v in verts}
	for u in uids:
		g.setdefault(u, set())
	rem, order = set(uids), []
	while rem:
		u = min(rem, key=lambda x: (len(g[x]), x))
		order.append(u)
		rem.remove(u)
		for nb in list(g[u]):
			g[nb].discard(u)
		g[u].clear()
	# rebuild and color back
	g2: Dict[int, set[int]] = defaultdict(set)
	for t in tris:
		for u, v in ((t.a.uid, t.b.uid), (t.b.uid, t.c.uid), (t.c.uid, t.a.uid)):
			g2[u].add(v)
			g2[v].add(u)
	col: Dict[int, int] = {}
	for u in reversed(order):
		used = {col[v] for v in g2[u] if v in col}
		col[u] = next((c for c in range(3) if c not in used), 0)
	b = defaultdict(list)
	for v in verts:
		b[col.get(v.uid, 0)].append(v)
	out = b[min(b, key=lambda c: len(b[c]))][:k] if b else []
	if len(out) < k:
		used = {v.uid for v in out}
		for v in verts:
			if v.uid not in used:
				out.append(v)
				used.add(v.uid)
				if len(out) == k:
					break
	return out[:k]


def parse() -> List[List[Polygon]]:
	arr = list(map(int, sys.stdin.buffer.read().split()))
	if not arr:
		return []
	i, t, cases = 0, arr[0], []
	i += 1
	for _ in range(t):
		v0 = arr[i]
		i += 1
		outer = [Vertex(arr[i + 2 * j], arr[i + 2 * j + 1], next(_id)) for j in range(v0)]
		i += 2 * v0
		h = arr[i]
		i += 1
		polys = [Polygon(outer, False)]
		for _ in range(h):
			m = arr[i]
			i += 1
			hole = [Vertex(arr[i + 2 * j], arr[i + 2 * j + 1], next(_id)) for j in range(m)]
			i += 2 * m
			polys.append(Polygon(hole, True))
		cases.append(polys)
	return cases


def plot(case_id: int, polys: Sequence[Polygon], merged: Sequence[Vertex], tris: Sequence[Triangle], guards: Sequence[Vertex], bridges: Sequence[Tuple[Vertex, Vertex]]) -> str:
	if plt is None:
		return "plotting unavailable"
	fig, ax = plt.subplots(figsize=(10, 8))
	ax.set_aspect("equal", adjustable="box")
	ax.set_title(f"Polygon triangulation - case {case_id}")

	def draw_ring(vs: Sequence[Vertex], color: str, ls: str) -> None:
		ax.plot([v.x for v in vs] + [vs[0].x], [v.y for v in vs] + [vs[0].y], color=color, linestyle=ls, linewidth=2)

	draw_ring(polys[0].vertices, "black", "-")
	for h in polys[1:]:
		draw_ring(h.vertices, "#b22222", "--")
	for t in tris:
		ax.plot([t.a.x, t.b.x, t.c.x, t.a.x], [t.a.y, t.b.y, t.c.y, t.a.y], color="#1f77b4", linewidth=1)
	for a, b in bridges:
		ax.plot([a.x, b.x], [a.y, b.y], color="#888888", linestyle=":", linewidth=1)
	if guards:
		ax.scatter([g.x for g in guards], [g.y for g in guards], color="#2ca02c", s=60, zorder=5)
	allx = [v.x for p in polys for v in p.vertices] + [v.x for v in merged]
	ally = [v.y for p in polys for v in p.vertices] + [v.y for v in merged]
	if allx:
		px = max(1, (max(allx) - min(allx)) // 10 + 1)
		py = max(1, (max(ally) - min(ally)) // 10 + 1)
		ax.set_xlim(min(allx) - px, max(allx) + px)
		ax.set_ylim(min(ally) - py, max(ally) + py)
	ax.grid(True, linestyle="--", alpha=0.25)
	path = f"triangulation_case_{case_id}.png"
	fig.tight_layout()
	fig.savefig(path, dpi=200)
	plt.close(fig)
	return path


def solve() -> None:
	cases = parse()
	if not cases:
		return
	out: List[str] = []
	for ci, polys in enumerate(cases, 1):
		tris, merged, bridges = triangulate_with_holes(polys)
		verts = guard_vertices(tris)
		n = sum(len(p.vertices) for p in polys)
		h = max(0, len(polys) - 1)
		k = floor((n + 2 * h) / 3)
		guards = choose_guards(verts, tris, k)
		img = plot(ci, polys, merged, tris, guards, bridges)
		out += [f"Case {ci}", f"Triangles: {len(tris)}"]
		out += [f"({t.a.x}, {t.a.y}) ({t.b.x}, {t.b.y}) ({t.c.x}, {t.c.y})" for t in tris]
		out += [f"k = {k}", f"Guards: {len(guards)}"]
		out += [f"({g.x}, {g.y})" for g in guards]
		out += [f"Plot: {img}"]
		if ci != len(cases):
			out.append("")
	sys.stdout.write("\n".join(out))


if __name__ == "__main__":
	solve()
