import matplotlib.pyplot as plt
import math

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

def intersect(p1,p2,q1,q2):
    def ccw(a,b,c):
        return (c.y - a.y)*(b.x - a.x) > (b.y - a.y)*(c.x - a.x)
    return ccw(p1,q1,q2)!=ccw(p2,q1,q2) and ccw(p1,p2,q1)!=ccw(p1,p2,q2)

def is_visible(vh, vp, polygon):
    for i in range(len(polygon.vertices)):
        a = polygon.vertices[i]
        b = polygon.vertices[(i+1)%len(polygon.vertices)]
        if a==vh or b==vh or a==vp or b==vp:
            continue
        if intersect(vh,vp,a,b):
            return False
    return True

# ----------------------------
# Step 1: Bridge Holes
# ----------------------------
def bridge_holes(outer, holes):
    for hole in holes:
        vh = max(hole.vertices, key=lambda v:v.x)
        vp = next((v for v in outer.vertices if is_visible(vh,v,outer)), None)
        if vp is None:
            raise ValueError("No visible vertex for bridging")
        idx = outer.vertices.index(vp)
        outer.vertices = outer.vertices[:idx+1] + hole.vertices + outer.vertices[idx+1:]
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


def triangulate_ear(vertices):
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

# ----------------------------
# Step 4: Compute Guards
# ----------------------------
def compute_guards(polygon, holes):
    n=len(polygon.vertices)
    h=len(holes)
    k=math.floor((n+2*h)/3)
    guards = polygon.vertices[:k]
    return k, guards

# ----------------------------
# Step 5: Plot
# ----------------------------
def plot_polygon(outer, holes, triangles, guards):
    plt.figure()
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
        plt.plot(tx,ty,'b--')
    # Guards
    gx=[v.x for v in guards]
    gy=[v.y for v in guards]
    plt.scatter(gx,gy,c='g',s=50,label='Guards')
    plt.axis('equal')
    plt.show()

# ----------------------------
# Step 6: Main
# ----------------------------
def main():
    T=int(input())
    for _ in range(T):
        data=list(map(int,input().split()))
        v0 = data[0]
        outer_vertices=[Vertex(data[i],data[i+1]) for i in range(1,2*v0+1,2)]
        outer = Polygon(outer_vertices)
        h=int(input())
        holes=[]
        for _ in range(h):
            hd=list(map(int,input().split()))
            vi=hd[0]
            hole_vertices=[Vertex(hd[i],hd[i+1],True) for i in range(1,2*vi+1,2)]
            holes.append(Polygon(hole_vertices))
        simple_poly = bridge_holes(outer, holes)
        triangles = triangulate_ear(simple_poly.vertices)
        k, guards = compute_guards(simple_poly, holes)
        # Output
        print("Triangles:")
        for tri in triangles:
            print([(v.x,v.y) for v in tri])
        print("Guards:", k, [(v.x,v.y) for v in guards])
        plot_polygon(outer, holes, triangles, guards)

if __name__=="__main__":
    main()