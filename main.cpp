#include <bits/stdc++.h>
using namespace std;

struct Point {
	long long x = 0;
	long long y = 0;
};

struct Triangle {
	Point a, b, c;
};

struct Polygon {
	vector<Point> vertices;
	bool isHole = false;
};

static constexpr long double EPS = 1e-12L;

long double toLD(long long value) {
	return static_cast<long double>(value);
}

bool pointEqual(const Point& a, const Point& b) {
	return a.x == b.x && a.y == b.y;
}

bool pointGreater(const Point& a, const Point& b) {
	return (a.x > b.x) || (a.x == b.x && a.y > b.y);
}

long double cross(const Point& a, const Point& b, const Point& c) {
	return (toLD(b.x - a.x) * toLD(c.y - a.y)) - (toLD(b.y - a.y) * toLD(c.x - a.x));
}

long double dot(const Point& a, const Point& b, const Point& c) {
	return (toLD(b.x - a.x) * toLD(c.x - a.x)) + (toLD(b.y - a.y) * toLD(c.y - a.y));
}

int signLD(long double value) {
	if (value > EPS) {
		return 1;
	}
	if (value < -EPS) {
		return -1;
	}
	return 0;
}

long double signedArea2(const vector<Point>& polygon) {
	long double area = 0.0L;
	int n = static_cast<int>(polygon.size());
	for (int i = 0; i < n; ++i) {
		const Point& p = polygon[i];
		const Point& q = polygon[(i + 1) % n];
		area += toLD(p.x) * toLD(q.y) - toLD(p.y) * toLD(q.x);
	}
	return area;
}

bool isCounterClockwise(const vector<Point>& polygon) {
	return signedArea2(polygon) > 0.0L;
}

bool onSegment(const Point& a, const Point& b, const Point& p) {
	if (signLD(cross(a, b, p)) != 0) {
		return false;
	}
	return min(a.x, b.x) <= p.x && p.x <= max(a.x, b.x) &&
		   min(a.y, b.y) <= p.y && p.y <= max(a.y, b.y);
}

bool segmentsProperlyIntersect(const Point& a, const Point& b, const Point& c, const Point& d) {
	int o1 = signLD(cross(a, b, c));
	int o2 = signLD(cross(a, b, d));
	int o3 = signLD(cross(c, d, a));
	int o4 = signLD(cross(c, d, b));

	if (o1 == 0 && onSegment(a, b, c)) return true;
	if (o2 == 0 && onSegment(a, b, d)) return true;
	if (o3 == 0 && onSegment(c, d, a)) return true;
	if (o4 == 0 && onSegment(c, d, b)) return true;

	return (o1 * o2 < 0) && (o3 * o4 < 0);
}

bool pointInRing(const Point& p, const vector<Point>& ring) {
	bool inside = false;
	int n = static_cast<int>(ring.size());
	for (int i = 0, j = n - 1; i < n; j = i++) {
		const Point& a = ring[i];
		const Point& b = ring[j];
		if (onSegment(a, b, p)) {
			return true;
		}
		bool intersect = ((a.y > p.y) != (b.y > p.y)) &&
						 (toLD(p.x) < (toLD(b.x - a.x) * toLD(p.y - a.y)) / toLD(b.y - a.y) + toLD(a.x));
		if (intersect) {
			inside = !inside;
		}
	}
	return inside;
}

bool pointInRegion(const Point& p, const vector<Polygon>& polygons) {
	if (polygons.empty()) {
		return false;
	}
	if (!pointInRing(p, polygons[0].vertices)) {
		return false;
	}
	for (size_t i = 1; i < polygons.size(); ++i) {
		if (pointInRing(p, polygons[i].vertices)) {
			return false;
		}
	}
	return true;
}

long double squaredDistance(const Point& a, const Point& b) {
	long double dx = toLD(a.x - b.x);
	long double dy = toLD(a.y - b.y);
	return dx * dx + dy * dy;
}

vector<Point> removeConsecutiveDuplicates(vector<Point> points) {
	vector<Point> cleaned;
	for (const auto& p : points) {
		if (cleaned.empty() || !pointEqual(cleaned.back(), p)) {
			cleaned.push_back(p);
		}
	}
	if (cleaned.size() > 1 && pointEqual(cleaned.front(), cleaned.back())) {
		cleaned.pop_back();
	}
	return cleaned;
}

vector<Point> removeCollinearVertices(vector<Point> points) {
	points = removeConsecutiveDuplicates(points);
	if (points.size() <= 3) {
		return points;
	}

	bool changed = true;
	while (changed && points.size() > 3) {
		changed = false;
		vector<Point> filtered;
		int n = static_cast<int>(points.size());
		for (int i = 0; i < n; ++i) {
			const Point& prev = points[(i - 1 + n) % n];
			const Point& curr = points[i];
			const Point& next = points[(i + 1) % n];
			if (signLD(cross(prev, curr, next)) == 0) {
				changed = true;
				continue;
			}
			filtered.push_back(curr);
		}
		points.swap(filtered);
	}
	return points;
}

void normalizePolygonOrientation(Polygon& polygon) {
	polygon.vertices = removeCollinearVertices(polygon.vertices);
	if (polygon.vertices.size() < 3) {
		return;
	}
	bool ccw = isCounterClockwise(polygon.vertices);
	if (!polygon.isHole && !ccw) {
		reverse(polygon.vertices.begin(), polygon.vertices.end());
	}
	if (polygon.isHole && ccw) {
		reverse(polygon.vertices.begin(), polygon.vertices.end());
	}
}

int rightmostVertexIndex(const vector<Point>& ring) {
	int best = 0;
	for (int i = 1; i < static_cast<int>(ring.size()); ++i) {
		if (pointGreater(ring[i], ring[best])) {
			best = i;
		}
	}
	return best;
}

bool segmentVisibleFromHole(const Point& a, const Point& b, const vector<Polygon>& polygons) {
	if (pointEqual(a, b)) {
		return false;
	}

	for (const auto& polygon : polygons) {
		const auto& ring = polygon.vertices;
		int n = static_cast<int>(ring.size());
		for (int i = 0; i < n; ++i) {
			Point c = ring[i];
			Point d = ring[(i + 1) % n];
			if (pointEqual(c, a) || pointEqual(d, a) || pointEqual(c, b) || pointEqual(d, b)) {
				continue;
			}
			if (segmentsProperlyIntersect(a, b, c, d)) {
				return false;
			}
		}
	}

	Point mid{static_cast<long long>((a.x + b.x) / 2), static_cast<long long>((a.y + b.y) / 2)};
	return pointInRegion(mid, polygons);
}

pair<int, int> chooseBridge(const Polygon& outer, const Polygon& hole, const vector<Polygon>& allPolygons) {
	int hIndex = rightmostVertexIndex(hole.vertices);
	Point hPoint = hole.vertices[hIndex];

	int chosenOuter = -1;
	long double bestDistance = numeric_limits<long double>::infinity();

	for (int i = 0; i < static_cast<int>(outer.vertices.size()); ++i) {
		const Point& candidate = outer.vertices[i];
		if (!segmentVisibleFromHole(hPoint, candidate, allPolygons)) {
			continue;
		}
		if (candidate.x < hPoint.x) {
			continue;
		}
		long double dist = squaredDistance(hPoint, candidate);
		if (dist < bestDistance - EPS) {
			bestDistance = dist;
			chosenOuter = i;
		} else if (fabsl(dist - bestDistance) <= EPS && chosenOuter != -1 && pointGreater(candidate, outer.vertices[chosenOuter])) {
			chosenOuter = i;
		}
	}

	if (chosenOuter == -1) {
		for (int i = 0; i < static_cast<int>(outer.vertices.size()); ++i) {
			const Point& candidate = outer.vertices[i];
			if (!segmentVisibleFromHole(hPoint, candidate, allPolygons)) {
				continue;
			}
			long double dist = squaredDistance(hPoint, candidate);
			if (dist < bestDistance - EPS) {
				bestDistance = dist;
				chosenOuter = i;
			} else if (fabsl(dist - bestDistance) <= EPS && chosenOuter != -1 && pointGreater(candidate, outer.vertices[chosenOuter])) {
				chosenOuter = i;
			}
		}
	}

	return {chosenOuter, hIndex};
}

vector<Point> stitchHoleIntoOuter(const vector<Point>& outer, const vector<Point>& hole, int outerIndex, int holeIndex) {
	vector<Point> stitched;
	int n = static_cast<int>(outer.size());
	int m = static_cast<int>(hole.size());

	for (int i = 0; i < n; ++i) {
		int idx = (outerIndex + i) % n;
		stitched.push_back(outer[idx]);
		if (idx == outerIndex) {
			stitched.push_back(hole[holeIndex]);
			for (int j = 1; j < m; ++j) {
				int hidx = (holeIndex - j + m) % m;
				stitched.push_back(hole[hidx]);
			}
			stitched.push_back(hole[holeIndex]);
		}
	}

	return removeConsecutiveDuplicates(stitched);
}

bool isConvexVertex(const Point& prev, const Point& curr, const Point& next, bool ccw) {
	long double turn = cross(prev, curr, next);
	return ccw ? turn > EPS : turn < -EPS;
}

bool pointStrictlyInsideTriangle(const Point& p, const Point& a, const Point& b, const Point& c) {
	long double c1 = cross(a, b, p);
	long double c2 = cross(b, c, p);
	long double c3 = cross(c, a, p);
	bool hasNeg = (c1 < -EPS) || (c2 < -EPS) || (c3 < -EPS);
	bool hasPos = (c1 > EPS) || (c2 > EPS) || (c3 > EPS);
	return !(hasNeg && hasPos) && fabsl(c1) > EPS && fabsl(c2) > EPS && fabsl(c3) > EPS;
}

bool isEar(const vector<Point>& polygon, int prev, int curr, int next, bool ccw, const vector<int>& active) {
	const Point& a = polygon[prev];
	const Point& b = polygon[curr];
	const Point& c = polygon[next];

	if (!isConvexVertex(a, b, c, ccw)) {
		return false;
	}

	for (int idx : active) {
		if (idx == prev || idx == curr || idx == next) {
			continue;
		}
		if (pointStrictlyInsideTriangle(polygon[idx], a, b, c)) {
			return false;
		}
	}

	return true;
}

vector<Triangle> triangulateSimplePolygon(vector<Point> polygon) {
	vector<Triangle> result;
	polygon = removeConsecutiveDuplicates(polygon);
	polygon = removeCollinearVertices(polygon);
	if (polygon.size() < 3) {
		return result;
	}

	if (!isCounterClockwise(polygon)) {
		reverse(polygon.begin(), polygon.end());
	}

	vector<int> active(polygon.size());
	iota(active.begin(), active.end(), 0);

	auto activePrev = [&](int pos) {
		return active[(pos - 1 + static_cast<int>(active.size())) % static_cast<int>(active.size())];
	};

	auto activeNext = [&](int pos) {
		return active[(pos + 1) % static_cast<int>(active.size())];
	};

	int guard = 0;
	while (active.size() > 3 && guard < 100000) {
		bool clipped = false;
		int m = static_cast<int>(active.size());
		for (int i = 0; i < m; ++i) {
			int prev = activePrev(i);
			int curr = active[i];
			int next = activeNext(i);

			if (!isEar(polygon, prev, curr, next, true, active)) {
				continue;
			}

			result.push_back({polygon[prev], polygon[curr], polygon[next]});
			active.erase(active.begin() + i);
			clipped = true;
			break;
		}

		if (!clipped) {
			break;
		}
		++guard;
	}

	if (active.size() == 3) {
		result.push_back({polygon[active[0]], polygon[active[1]], polygon[active[2]]});
	}

	return result;
}

enum class VertexKind {
	Start,
	End,
	Split,
	Merge,
	Regular
};

struct EdgeRef {
	int from = -1;
	int to = -1;
};

bool sweepHigher(const Point& a, const Point& b) {
	return (a.y > b.y) || (a.y == b.y && a.x > b.x);
}

bool sweepLower(const Point& a, const Point& b) {
	return sweepHigher(b, a);
}

bool horizontalEdge(const Point& a, const Point& b) {
	return a.y == b.y;
}

long double edgeIntersectionX(const Point& a, const Point& b, long double y) {
	if (a.y == b.y) {
		return static_cast<long double>(min(a.x, b.x));
	}
	return toLD(a.x) + (y - toLD(a.y)) * (toLD(b.x - a.x)) / toLD(b.y - a.y);
}

int edgeUpperEndpoint(const EdgeRef& edge, const vector<Point>& polygon) {
	return sweepHigher(polygon[edge.from], polygon[edge.to]) ? edge.from : edge.to;
}

int edgeLowerEndpoint(const EdgeRef& edge, const vector<Point>& polygon) {
	return sweepHigher(polygon[edge.from], polygon[edge.to]) ? edge.to : edge.from;
}

bool edgeCrossesSweep(const EdgeRef& edge, long double y, const vector<Point>& polygon) {
	const Point& a = polygon[edge.from];
	const Point& b = polygon[edge.to];
	if (horizontalEdge(a, b)) {
		return false;
	}
	long double hi = max(toLD(a.y), toLD(b.y));
	long double lo = min(toLD(a.y), toLD(b.y));
	return lo < y && y < hi;
}

int findLeftStatusEdge(const vector<int>& status, long double sweepY, long double vertexX, const vector<EdgeRef>& edges, const vector<Point>& polygon) {
	int best = -1;
	long double bestX = -numeric_limits<long double>::infinity();
	for (int edgeId : status) {
		if (!edgeCrossesSweep(edges[edgeId], sweepY, polygon)) {
			continue;
		}
		long double x = edgeIntersectionX(polygon[edges[edgeId].from], polygon[edges[edgeId].to], sweepY);
		if (x <= vertexX + EPS && x > bestX + EPS) {
			bestX = x;
			best = edgeId;
		}
	}
	return best;
}

void removeEdgeFromStatus(vector<int>& status, int edgeId) {
	auto it = find(status.begin(), status.end(), edgeId);
	if (it != status.end()) {
		status.erase(it);
	}
}

void insertEdgeIntoStatus(vector<int>& status, int edgeId, const vector<EdgeRef>& edges, const vector<Point>& polygon, long double sweepY) {
	if (!edgeCrossesSweep(edges[edgeId], sweepY, polygon)) {
		return;
	}
	status.push_back(edgeId);
}

void sortStatus(vector<int>& status, long double sweepY, const vector<EdgeRef>& edges, const vector<Point>& polygon) {
	sort(status.begin(), status.end(), [&](int lhs, int rhs) {
		long double x1 = edgeIntersectionX(polygon[edges[lhs].from], polygon[edges[lhs].to], sweepY);
		long double x2 = edgeIntersectionX(polygon[edges[rhs].from], polygon[edges[rhs].to], sweepY);
		if (fabsl(x1 - x2) > EPS) {
			return x1 < x2;
		}
		return lhs < rhs;
	});
}

VertexKind classifyVertex(int index, const vector<Point>& polygon) {
	int n = static_cast<int>(polygon.size());
	int prev = (index - 1 + n) % n;
	int next = (index + 1) % n;
	bool prevAbove = sweepHigher(polygon[prev], polygon[index]);
	bool nextAbove = sweepHigher(polygon[next], polygon[index]);
	bool convex = cross(polygon[prev], polygon[index], polygon[next]) > EPS;

	if (!prevAbove && !nextAbove) {
		return convex ? VertexKind::Start : VertexKind::Split;
	}
	if (prevAbove && !nextAbove) {
		return VertexKind::Regular;
	}
	if (!prevAbove && nextAbove) {
		return VertexKind::Regular;
	}
	return convex ? VertexKind::End : VertexKind::Merge;
}

vector<pair<Point, Point>> sweepLineDecompositionDiagonals(const vector<Point>& polygon) {
	int n = static_cast<int>(polygon.size());
	vector<EdgeRef> edges(n);
	for (int i = 0; i < n; ++i) {
		edges[i] = {i, (i + 1) % n};
	}

	vector<int> order(n);
	iota(order.begin(), order.end(), 0);
	sort(order.begin(), order.end(), [&](int lhs, int rhs) {
		if (polygon[lhs].y != polygon[rhs].y) {
			return polygon[lhs].y > polygon[rhs].y;
		}
		if (polygon[lhs].x != polygon[rhs].x) {
			return polygon[lhs].x > polygon[rhs].x;
		}
		return lhs < rhs;
	});

	vector<int> helper(n, -1);
	vector<int> status;
	vector<pair<Point, Point>> diagonals;

	auto addDiagonal = [&](int a, int b) {
		if (a == b) {
			return;
		}
		if (pointEqual(polygon[a], polygon[b])) {
			return;
		}
		diagonals.push_back({polygon[a], polygon[b]});
	};

	for (int vertexIndex : order) {
		long double sweepY = toLD(polygon[vertexIndex].y) - 0.5L;
		sortStatus(status, sweepY, edges, polygon);

		int prev = (vertexIndex - 1 + n) % n;
		int next = (vertexIndex + 1) % n;
		int prevEdge = (vertexIndex - 1 + n) % n;
		int nextEdge = vertexIndex;

		VertexKind kind = classifyVertex(vertexIndex, polygon);

		if (kind == VertexKind::Start) {
			insertEdgeIntoStatus(status, nextEdge, edges, polygon, sweepY);
			helper[nextEdge] = vertexIndex;
		} else if (kind == VertexKind::Split) {
			int leftEdge = findLeftStatusEdge(status, sweepY, toLD(polygon[vertexIndex].x), edges, polygon);
			if (leftEdge != -1 && helper[leftEdge] != -1) {
				addDiagonal(vertexIndex, helper[leftEdge]);
			}
			if (leftEdge != -1) {
				helper[leftEdge] = vertexIndex;
			}
			insertEdgeIntoStatus(status, nextEdge, edges, polygon, sweepY);
			helper[nextEdge] = vertexIndex;
		} else if (kind == VertexKind::End) {
			if (helper[prevEdge] != -1 && classifyVertex(helper[prevEdge], polygon) == VertexKind::Merge) {
				addDiagonal(vertexIndex, helper[prevEdge]);
			}
			removeEdgeFromStatus(status, prevEdge);
		} else if (kind == VertexKind::Merge) {
			if (helper[prevEdge] != -1 && classifyVertex(helper[prevEdge], polygon) == VertexKind::Merge) {
				addDiagonal(vertexIndex, helper[prevEdge]);
			}
			removeEdgeFromStatus(status, prevEdge);
			int leftEdge = findLeftStatusEdge(status, sweepY, toLD(polygon[vertexIndex].x), edges, polygon);
			if (leftEdge != -1 && helper[leftEdge] != -1 && classifyVertex(helper[leftEdge], polygon) == VertexKind::Merge) {
				addDiagonal(vertexIndex, helper[leftEdge]);
			}
			if (leftEdge != -1) {
				helper[leftEdge] = vertexIndex;
			}
		} else {
			if (!sweepHigher(polygon[next], polygon[vertexIndex])) {
				if (helper[prevEdge] != -1 && classifyVertex(helper[prevEdge], polygon) == VertexKind::Merge) {
					addDiagonal(vertexIndex, helper[prevEdge]);
				}
				removeEdgeFromStatus(status, prevEdge);
				insertEdgeIntoStatus(status, nextEdge, edges, polygon, sweepY);
				helper[nextEdge] = vertexIndex;
			} else {
				int leftEdge = findLeftStatusEdge(status, sweepY, toLD(polygon[vertexIndex].x), edges, polygon);
				if (leftEdge != -1 && helper[leftEdge] != -1 && classifyVertex(helper[leftEdge], polygon) == VertexKind::Merge) {
					addDiagonal(vertexIndex, helper[leftEdge]);
				}
				if (leftEdge != -1) {
					helper[leftEdge] = vertexIndex;
				}
			}
		}
	}

	return diagonals;
}

vector<vector<Point>> splitPieceByDiagonal(const vector<Point>& piece, const Point& a, const Point& b) {
	int n = static_cast<int>(piece.size());
	int ia = -1;
	int ib = -1;
	for (int i = 0; i < n; ++i) {
		if (pointEqual(piece[i], a)) {
			ia = i;
		}
		if (pointEqual(piece[i], b)) {
			ib = i;
		}
	}
	if (ia == -1 || ib == -1 || ia == ib) {
		return {piece};
	}

	vector<Point> first;
	for (int i = ia; i != ib; i = (i + 1) % n) {
		first.push_back(piece[i]);
	}
	first.push_back(piece[ib]);

	vector<Point> second;
	for (int i = ib; i != ia; i = (i + 1) % n) {
		second.push_back(piece[i]);
	}
	second.push_back(piece[ia]);

	first = removeConsecutiveDuplicates(first);
	second = removeConsecutiveDuplicates(second);
	return {first, second};
}

vector<vector<Point>> decomposeToMonotonePieces(vector<Point> polygon) {
	polygon = removeConsecutiveDuplicates(polygon);
	polygon = removeCollinearVertices(polygon);
	if (polygon.size() < 3) {
		return {};
	}

	if (!isCounterClockwise(polygon)) {
		reverse(polygon.begin(), polygon.end());
	}

	vector<pair<Point, Point>> diagonals = sweepLineDecompositionDiagonals(polygon);
	vector<vector<Point>> pieces = {polygon};

	for (const auto& diagonal : diagonals) {
		bool splitDone = false;
		for (size_t i = 0; i < pieces.size(); ++i) {
			int hitA = -1;
			int hitB = -1;
			for (int j = 0; j < static_cast<int>(pieces[i].size()); ++j) {
				if (pointEqual(pieces[i][j], diagonal.first)) {
					hitA = j;
				}
				if (pointEqual(pieces[i][j], diagonal.second)) {
					hitB = j;
				}
			}
			if (hitA != -1 && hitB != -1) {
				auto splitPieces = splitPieceByDiagonal(pieces[i], diagonal.first, diagonal.second);
				if (splitPieces.size() == 2) {
					pieces[i] = splitPieces[0];
					pieces.push_back(splitPieces[1]);
				}
				splitDone = true;
				break;
			}
		}
		if (!splitDone) {
			continue;
		}
	}

	for (auto& piece : pieces) {
		piece = removeConsecutiveDuplicates(piece);
		piece = removeCollinearVertices(piece);
		if (piece.size() >= 3 && !isCounterClockwise(piece)) {
			reverse(piece.begin(), piece.end());
		}
	}

	vector<vector<Point>> filtered;
	for (const auto& piece : pieces) {
		if (piece.size() >= 3) {
			filtered.push_back(piece);
		}
	}
	return filtered;
}

vector<Triangle> triangulatePolygonWithHoles(vector<Polygon> polygons) {
	if (polygons.empty()) {
		return {};
	}

	for (auto& polygon : polygons) {
		normalizePolygonOrientation(polygon);
	}

	vector<Point> merged = polygons[0].vertices;
	polygons[0].vertices = merged;
	for (size_t i = 1; i < polygons.size(); ++i) {
		polygons[0].vertices = merged;
		auto [outerIndex, holeIndex] = chooseBridge(polygons[0], polygons[i], polygons);
		if (outerIndex == -1) {
			continue;
		}
		merged = stitchHoleIntoOuter(merged, polygons[i].vertices, outerIndex, holeIndex);
		polygons[0].vertices = merged;
	}

	vector<vector<Point>> monotonePieces = decomposeToMonotonePieces(merged);
	vector<Triangle> triangles;
	for (auto piece : monotonePieces) {
		vector<Triangle> local = triangulateSimplePolygon(piece);
		triangles.insert(triangles.end(), local.begin(), local.end());
	}
	return triangles;
}

void readPolygon(Polygon& polygon, int vertexCount) {
	polygon.vertices.resize(vertexCount);
	for (int i = 0; i < vertexCount; ++i) {
		cin >> polygon.vertices[i].x >> polygon.vertices[i].y;
	}
}

void printTriangle(const Triangle& triangle) {
	cout << triangle.a.x << ' ' << triangle.a.y << ' ';
	cout << triangle.b.x << ' ' << triangle.b.y << ' ';
	cout << triangle.c.x << ' ' << triangle.c.y << '\n';
}

int main() {
	ios::sync_with_stdio(false);
	cin.tie(nullptr);

	int T;
	if (!(cin >> T)) {
		return 0;
	}

	for (int tc = 0; tc < T; ++tc) {
		int outerVertices;
		cin >> outerVertices;

		vector<Polygon> polygons;
		polygons.reserve(outerVertices + 8);

		Polygon outer;
		outer.isHole = false;
		readPolygon(outer, outerVertices);
		polygons.push_back(outer);

		int holeCount;
		cin >> holeCount;

		for (int i = 0; i < holeCount; ++i) {
			int vertexCount;
			cin >> vertexCount;
			Polygon hole;
			hole.isHole = true;
			readPolygon(hole, vertexCount);
			polygons.push_back(hole);
		}

		vector<Triangle> triangles = triangulatePolygonWithHoles(polygons);

		cout << triangles.size() << '\n';
		for (const auto& triangle : triangles) {
			printTriangle(triangle);
		}

		if (tc + 1 < T) {
			cout << '\n';
		}
	}

	return 0;
}
