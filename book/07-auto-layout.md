# Chapter 7: The Auto-Layout Algorithm

When an MSD file is converted to a Merisio project, entities and associations need positions on the canvas. Unlike the GUI, where users place elements manually, the MSD pipeline must compute positions automatically. This chapter describes the force-directed layout algorithm used for this purpose.

## 7.1 The Problem

Given a set of entities, associations, and links between them, find (x, y) positions for every element such that:

1. Connected elements are near each other (links should be short)
2. Unconnected elements are far apart (avoid visual clutter)
3. No elements overlap (labels must be readable)
4. The result is visually balanced (not clumped in one corner)

This is a classic **graph drawing** problem, and force-directed algorithms are the most widely used solution.

## 7.2 Fruchterman-Reingold Algorithm

The layout module (`src/msd/layout.py`) implements the **Fruchterman-Reingold** algorithm (1991), one of the most popular force-directed placement algorithms. The idea is simple: treat the graph as a physical system.

### The Physical Analogy

- **Nodes** (entities and associations) are charged particles that repel each other
- **Edges** (links) are springs that attract connected nodes
- The system evolves over time, with forces moving nodes until an equilibrium is reached

### Forces

Two types of forces act on every node:

**Repulsive force** (between all pairs of nodes):

```
F_repulsive = k² / distance
```

Every node pushes every other node away. The force is inversely proportional to distance — close nodes repel strongly, distant nodes repel weakly. The constant `k` is the ideal edge length.

**Attractive force** (along edges only):

```
F_attractive = distance² / k
```

Connected nodes pull each other closer. The force grows quadratically with distance — very distant connected nodes experience a strong pull.

### The Ideal Length

The constant `k` represents the ideal distance between connected nodes:

```python
area = max(n * 200 * 200, 400 * 400)
k = math.sqrt(area / n)
```

It is computed from the number of nodes, scaled so that the graph occupies a reasonable area.

## 7.3 Implementation Walkthrough

### Initial Placement

Nodes are placed in a circle to give the algorithm a reasonable starting configuration:

```python
random.seed(42)
radius = k * math.sqrt(n) / 2
for i, node in enumerate(nodes):
    angle = 2 * math.pi * i / n
    node.x = radius * math.cos(angle)
    node.y = radius * math.sin(angle)
```

The seed is fixed at 42 for **deterministic results** — the same MSD file always produces the same layout. This is important for version control: running `merisio-cli parse` twice on the same file should produce identical output.

### The Main Loop

The algorithm runs for 100 iterations with **simulated annealing** (linear cooling):

```python
temp = k * 2       # initial temperature
cooling = temp / iterations

for _ in range(iterations):
    # Reset displacements
    # Compute repulsive forces (all pairs)
    # Compute attractive forces (edges only)
    # Apply displacements (clamped by temperature)
    temp -= cooling
```

The **temperature** limits how far nodes can move in each iteration. It starts high (allowing large movements) and decreases linearly (allowing fine adjustments). This prevents oscillation.

### Repulsive Forces

```python
for i in range(n):
    for j in range(i + 1, n):
        diffx = nodes[i].x - nodes[j].x
        diffy = nodes[i].y - nodes[j].y
        dist = math.sqrt(diffx * diffx + diffy * diffy)
        if dist < 0.01:
            dist = 0.01
            diffx = random.uniform(-0.1, 0.1)
            diffy = random.uniform(-0.1, 0.1)
        force = (k * k) / dist
        fx = (diffx / dist) * force
        fy = (diffy / dist) * force
        dx[i] += fx
        dy[i] += fy
        dx[j] -= fx
        dy[j] -= fy
```

Key details:

- **O(n²)** complexity — acceptable for MCD models (typically < 50 nodes)
- **Minimum distance** of 0.01 prevents division by zero
- When nodes coincide, a **random perturbation** is applied to break symmetry
- Forces are applied symmetrically (Newton's third law: `dx[i] += fx`, `dx[j] -= fx`)

### Attractive Forces

```python
for ei, ai in edges:
    diffx = nodes[ei].x - nodes[ai].x
    diffy = nodes[ei].y - nodes[ai].y
    dist = math.sqrt(diffx * diffx + diffy * diffy)
    if dist < 0.01:
        dist = 0.01
    force = (dist * dist) / k
    fx = (diffx / dist) * force
    fy = (diffy / dist) * force
    dx[ei] -= fx
    dy[ei] -= fy
    dx[ai] += fx
    dy[ai] += fy
```

Attractive forces only act between connected nodes (entities and their associations). This pulls linked elements together while unlinked elements drift apart from repulsion.

### Displacement Application

```python
for i in range(n):
    disp = math.sqrt(dx[i] * dx[i] + dy[i] * dy[i])
    if disp > 0:
        scale = min(disp, temp) / disp
        nodes[i].x += dx[i] * scale
        nodes[i].y += dy[i] * scale
```

The displacement is **clamped** to the current temperature. Early iterations allow large movements; later iterations only allow small adjustments.

## 7.4 Post-Processing

After the force-directed phase, two post-processing steps clean up the result.

### Overlap Removal

```python
for _ in range(20):
    moved = False
    for i in range(n):
        wi, hi = node_sizes[i]
        for j in range(i + 1, n):
            wj, hj = node_sizes[j]
            ox = (wi + wj) / 2 + 30 - abs(nodes[i].x - nodes[j].x)
            oy = (hi + hj) / 2 + 30 - abs(nodes[i].y - nodes[j].y)
            if ox > 0 and oy > 0:
                # Push apart along the axis with less overlap
                if ox < oy:
                    shift = ox / 2 + 1
                    # ... push horizontally ...
                else:
                    shift = oy / 2 + 1
                    # ... push vertically ...
                moved = True
    if not moved:
        break
```

The force-directed algorithm does not account for node sizes — it treats nodes as points. The overlap removal pass checks for bounding box collisions (with a 30-pixel margin) and pushes overlapping nodes apart along the axis of least overlap.

This runs for up to 20 iterations, stopping early if no overlaps remain.

### Node Size Estimation

Node sizes are estimated from attribute counts:

```python
ENTITY_BASE_W = 140
ENTITY_BASE_H = 60
ENTITY_ATTR_H = 18  # per attribute

ASSOC_BASE_W = 120
ASSOC_BASE_H = 50
ASSOC_ATTR_H = 18
```

An entity with 4 attributes has an estimated height of `60 + 4 * 18 = 132` pixels. These estimates match the rendering sizes in the Merisio canvas.

### Centring

```python
if n > 0:
    cx = sum(nd.x for nd in nodes) / n
    cy = sum(nd.y for nd in nodes) / n
    for nd in nodes:
        nd.x -= cx
        nd.y -= cy
```

The entire layout is centred on the origin (0, 0). This ensures the diagram appears in the middle of the canvas when opened in the GUI.

### Rounding

```python
for nd in nodes:
    nd.x = round(nd.x)
    nd.y = round(nd.y)
```

Positions are rounded to integers for cleaner JSON output and pixel-aligned rendering.

## 7.5 Edge Resolution

The layout engine needs to know which nodes are connected by edges. Since it operates on Entity and Association objects (which use UUIDs for links), the builder creates lightweight proxy objects:

```python
class _LayoutLink:
    def __init__(self, entity_name, association_name):
        self.entity_name = entity_name
        self.association_name = association_name
```

The layout engine supports both name-based and ID-based lookups:

```python
name_to_idx[getattr(e, "name", getattr(e, "id", ""))] = idx
if hasattr(e, "id"):
    name_to_idx[e.id] = idx
```

This flexibility means the layout engine can work with both parsed link objects (name-based) and model link objects (ID-based).

## 7.6 Complexity

| Operation | Complexity |
|-----------|------------|
| Initial placement | O(n) |
| Repulsive forces per iteration | O(n²) |
| Attractive forces per iteration | O(e) |
| Total (100 iterations) | O(100 * (n² + e)) |
| Overlap removal | O(20 * n²) |

For typical MCD models with 5–20 entities, this completes in under a millisecond. Even for large models with 100+ entities, it finishes in well under a second.

## 7.7 Determinism

The layout is **deterministic** — the same input always produces the same output. This is achieved by:

1. `random.seed(42)` before initial placement
2. Fixed iteration count (100)
3. Linear cooling schedule (no random perturbation in the main loop)
4. Rounding to integers

This determinism is important for CI/CD pipelines and version control: running `merisio-cli parse` on the same MSD file twice produces byte-identical `.merisio` files (modulo the timestamp in metadata).

## 7.8 Design Decisions

### Why Fruchterman-Reingold?

Several alternatives were considered:

| Algorithm | Pros | Cons |
|-----------|------|------|
| Grid layout | Simple, predictable | No edge awareness, wastes space |
| Tree layout | Clean for hierarchies | MCD is not a tree |
| Kamada-Kawai | Better global optimum | Requires matrix operations |
| Fruchterman-Reingold | Simple, good results, edge-aware | May get stuck in local optima |

Fruchterman-Reingold was chosen for its simplicity (pure Python maths, no dependencies), good results for small-medium graphs, and natural handling of the bipartite structure of MCDs (entities connected to associations via links).

### Why 100 Iterations?

Empirically determined. For MCD-sized graphs (5–50 nodes), 100 iterations consistently produce stable, visually pleasing layouts. More iterations do not meaningfully improve results; fewer iterations sometimes leave nodes in suboptimal positions.

### Why Fixed Seed?

Reproducibility. If the user runs the same command twice, they should get the same result. This also makes testing straightforward — layout tests can assert exact positions.
