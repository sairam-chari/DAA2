import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import math
from collections import defaultdict

# ----------------------------
# Data Structures
# ----------------------------
class Vertex:
    def __init__(self, x, y, is_hole=False):
        self.x = x
        self.y = y
        self.is_hole = is_hole
        self.prev = None
        self.next = None
    def __repr__(self):
        return f"({self.x},{self.y}){'H' if self.is_hole else ''}"

class Polygon:
    def __init__(self, vertices):
        self.vertices = vertices
        n = len(vertices)
        for i in range(n):
            vertices[i].next = vertices[(i+1)%n]
            vertices[i].prev = vertices[(i-1+n)%n]

# ----------------------------
# Geometry Utilities
# ----------------------------
def cross(a, b, c):
    return (b.x - a.x)*(c.y - a.y) - (b.y - a.y)*(c.x - a.x)

def same(a, b):
    return a.x == b.x and a.y == b.y

def polygon_area2(vertices):
    s = 0
    n = len(vertices)
    for i in range(n):
        a = vertices[i]
        b = vertices[(i + 1) % n]
        s += a.x * b.y - a.y * b.x
    return s

def normalize_ccw(vertices):
    if polygon_area2(vertices) < 0:
        return list(reversed(vertices))
    return vertices[:]

def normalize_cw(vertices):
    if polygon_area2(vertices) > 0:
        return list(reversed(vertices))
    return vertices[:]

def on_segment(a, b, p):
    return cross(a, b, p) == 0 and min(a.x, b.x) <= p.x <= max(a.x, b.x) and min(a.y, b.y) <= p.y <= max(a.y, b.y)

def intersect(p1, p2, q1, q2):
    def sign(v):
        return 1 if v > 0 else (-1 if v < 0 else 0)

    o1 = sign(cross(p1, p2, q1))
    o2 = sign(cross(p1, p2, q2))
    o3 = sign(cross(q1, q2, p1))
    o4 = sign(cross(q1, q2, p2))

    if o1 == 0 and on_segment(p1, p2, q1):
        return True
    if o2 == 0 and on_segment(p1, p2, q2):
        return True
    if o3 == 0 and on_segment(q1, q2, p1):
        return True
    if o4 == 0 and on_segment(q1, q2, p2):
        return True

    return o1 * o2 < 0 and o3 * o4 < 0

def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    for i in range(n):
        a = ring[i]
        b = ring[(i + 1) % n]
        if on_segment(a, b, Vertex(x, y)):
            return True
        if ((a.y > y) != (b.y > y)) and x < (b.x - a.x) * (y - a.y) / (b.y - a.y + 0.0) + a.x:
            inside = not inside
    return inside

def point_in_region(x, y, outer, holes):
    if not point_in_ring(x, y, outer.vertices):
        return False
    for hole in holes:
        if point_in_ring(x, y, hole.vertices):
            return False
    return True

def triangle_ok(a, b, c, outer, holes):
    cx = (a.x + b.x + c.x) / 3.0
    cy = (a.y + b.y + c.y) / 3.0
    if not point_in_region(cx, cy, outer, holes):
        return False

    edges = [(a, b), (b, c), (c, a)]
    rings = [outer.vertices] + [hole.vertices for hole in holes]
    for ring in rings:
        for i in range(len(ring)):
            p = ring[i]
            q = ring[(i + 1) % len(ring)]
            for u, v in edges:
                if same(u, p) or same(u, q) or same(v, p) or same(v, q):
                    continue
                if intersect(u, v, p, q):
                    return False
    return True

def edge_visible(a, b, outer, holes):
    if same(a, b):
        return False
    rings = [outer.vertices] + [hole.vertices for hole in holes]
    for ring in rings:
        for i in range(len(ring)):
            c = ring[i]
            d = ring[(i + 1) % len(ring)]
            if same(a, c) or same(a, d) or same(b, c) or same(b, d):
                continue
            if intersect(a, b, c, d):
                return False
    midx = (a.x + b.x) / 2.0
    midy = (a.y + b.y) / 2.0
    return point_in_region(midx, midy, outer, holes)

# ----------------------------
# Step 1: Bridge Holes
# ----------------------------
def bridge_holes(outer, holes):
    outer.vertices = normalize_ccw(outer.vertices)
    for hole in holes:
        hole.vertices = normalize_cw(hole.vertices)

    for hole in holes:
        best = None
        for vh_index, vh in enumerate(hole.vertices):
            candidates = [v for v in outer.vertices if edge_visible(vh, v, outer, holes)]
            for vp in candidates:
                score = (vp.x - vh.x) ** 2 + (vp.y - vh.y) ** 2
                key = (score, vp.x, vp.y, vh.x, vh.y, vh_index)
                if best is None or key < best[0]:
                    best = (key, vh_index, vh, vp)

        if best is None:
            raise ValueError("No visible vertex for bridging")

        _, vh_index, vh, vp = best
        idx = outer.vertices.index(vp)

        m = len(hole.vertices)
        hole_path = [hole.vertices[(vh_index + step) % m] for step in range(1, m)]

        outer.vertices = outer.vertices[:idx + 1] + [vh] + hole_path + [vh, vp] + outer.vertices[idx + 1:]
        outer.vertices = normalize_ccw(outer.vertices)
    return outer

# ----------------------------
# Step 2: Placeholder Decomposition (unused for now)
# ----------------------------
def decompose_monotone_placeholder(polygon):
    # Placeholder for future sweep-line monotone decomposition work.
    # Not used in current execution path.
    return [polygon.vertices]

# ----------------------------
# Step 3: Ear Clipping Triangulation
# ----------------------------
def polygon_area2(vertices):
    s = 0
    n = len(vertices)
    for i in range(n):
        a = vertices[i]
        b = vertices[(i + 1) % n]
        s += a.x * b.y - a.y * b.x
    return s


def point_in_triangle_strict(p, a, b, c):
    c1 = cross(a, b, p)
    c2 = cross(b, c, p)
    c3 = cross(c, a, p)
    if c1 == 0 or c2 == 0 or c3 == 0:
        return False
    return (c1 > 0 and c2 > 0 and c3 > 0) or (c1 < 0 and c2 < 0 and c3 < 0)


def triangulate_ear(vertices, outer, holes):
    vertices = vertices[:]
    if len(vertices) < 3:
        return []

    if polygon_area2(vertices) < 0:
        vertices.reverse()

    idx = list(range(len(vertices)))
    triangles = []

    def is_ear(pos):
        i_prev = idx[(pos - 1) % len(idx)]
        i_curr = idx[pos]
        i_next = idx[(pos + 1) % len(idx)]
        a = vertices[i_prev]
        b = vertices[i_curr]
        c = vertices[i_next]

        if cross(a, b, c) <= 0:
            return False
        if not triangle_ok(a, b, c, outer, holes):
            return False

        for j in idx:
            if j in (i_prev, i_curr, i_next):
                continue
            if point_in_triangle_strict(vertices[j], a, b, c):
                return False
        return True

    while len(idx) > 3:
        clipped = False
        for p in range(len(idx)):
            if is_ear(p):
                i_prev = idx[(p - 1) % len(idx)]
                i_curr = idx[p]
                i_next = idx[(p + 1) % len(idx)]
                triangles.append([vertices[i_prev], vertices[i_curr], vertices[i_next]])
                idx.pop(p)
                clipped = True
                break
        if not clipped:
            break

    if len(idx) == 3:
        triangles.append([vertices[idx[0]], vertices[idx[1]], vertices[idx[2]]])

    return triangles

def guard_vertices(triangles):
    seen = set()
    verts = []
    for tri in triangles:
        for v in tri:
            key = (v.x, v.y)
            if key not in seen:
                seen.add(key)
                verts.append(v)
    return verts

def choose_guards(vertices, triangles, k):
    graph = defaultdict(set)
    for tri in triangles:
        a, b, c = tri
        for u, v in ((a, b), (b, c), (c, a)):
            graph[(u.x, u.y)].add((v.x, v.y))
            graph[(v.x, v.y)].add((u.x, u.y))

    for v in vertices:
        graph.setdefault((v.x, v.y), set())

    remaining = set(graph.keys())
    order = []
    while remaining:
        key = min(remaining, key=lambda p: (len(graph[p]), p[0], p[1]))
        order.append(key)
        remaining.remove(key)
        for nb in list(graph[key]):
            graph[nb].discard(key)
        graph[key].clear()

    graph = defaultdict(set)
    for tri in triangles:
        a, b, c = tri
        for u, v in ((a, b), (b, c), (c, a)):
            graph[(u.x, u.y)].add((v.x, v.y))
            graph[(v.x, v.y)].add((u.x, u.y))

    color = {}
    for key in reversed(order):
        used = {color[nb] for nb in graph[key] if nb in color}
        for c in range(3):
            if c not in used:
                color[key] = c
                break

    buckets = defaultdict(list)
    for v in vertices:
        buckets[color.get((v.x, v.y), 0)].append(v)

    if not buckets:
        return []

    chosen = buckets[min(buckets, key=lambda c: (len(buckets[c]), c))][:k]
    seen = {(v.x, v.y) for v in chosen}
    if len(chosen) < k:
        for v in vertices:
            key = (v.x, v.y)
            if key not in seen:
                chosen.append(v)
                seen.add(key)
                if len(chosen) == k:
                    break
    return chosen[:k]

# ----------------------------
# Step 4: Compute Guards
# ----------------------------
def compute_guards(polygon, holes):
    n=len(polygon.vertices)
    h=len(holes)
    return math.floor((n+2*h)/3)

# ----------------------------
# Step 5: Plot
# ----------------------------
def plot_polygon(case_index, outer, holes, triangles, guards):
    fig = plt.figure()
    # Outer
    x=[v.x for v in outer.vertices]+[outer.vertices[0].x]
    y=[v.y for v in outer.vertices]+[outer.vertices[0].y]
    plt.plot(x,y,'k-')
    # Holes
    for hole in holes:
        hx=[v.x for v in hole.vertices]+[hole.vertices[0].x]
        hy=[v.y for v in hole.vertices]+[hole.vertices[0].y]
        plt.plot(hx,hy,'r-')
    # Triangles
    for tri in triangles:
        tx=[v.x for v in tri]+[tri[0].x]
        ty=[v.y for v in tri]+[tri[0].y]
        plt.plot(tx,ty,color='#7f8c8d',linestyle='--',linewidth=1)
    # Guards
    gx=[v.x for v in guards]
    gy=[v.y for v in guards]
    plt.scatter(gx,gy,c='g',s=50,label='Guards')
    plt.axis('equal')
    fig.tight_layout()
    fig.savefig(f'main2_plot_{case_index}.png', dpi=200)
    plt.close(fig)

# ----------------------------
# Step 6: Main
# ----------------------------
def main():
    T=int(input())
    for case_index in range(1, T + 1):
        data=list(map(int,input().split()))
        v0 = data[0]
        outer_vertices=[Vertex(data[i],data[i+1]) for i in range(1,2*v0+1,2)]
        outer = Polygon(outer_vertices)
        plot_outer = Polygon([Vertex(v.x, v.y, v.is_hole) for v in outer_vertices])
        h=int(input())
        holes=[]
        plot_holes=[]
        for _ in range(h):
            hd=list(map(int,input().split()))
            vi=hd[0]
            hole_vertices=[Vertex(hd[i],hd[i+1],True) for i in range(1,2*vi+1,2)]
            holes.append(Polygon(hole_vertices))
            plot_holes.append(Polygon([Vertex(v.x, v.y, v.is_hole) for v in hole_vertices]))
        simple_poly = bridge_holes(outer, holes)
        triangles = triangulate_ear(simple_poly.vertices, outer, holes)
        k = compute_guards(simple_poly, holes)
        guard_pool = guard_vertices(triangles)
        guards = choose_guards(guard_pool, triangles, k)
        for tri in triangles:
            print([(v.x,v.y) for v in tri])
        print(k)
        for guard in guards:
            print((guard.x, guard.y))
        if case_index != T:
            print()
        plot_polygon(case_index, plot_outer, plot_holes, triangles, guards)

if __name__=="__main__":
    main()