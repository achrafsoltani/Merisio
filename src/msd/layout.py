import math
import random
from typing import List, Protocol


class Positionable(Protocol):
    x: float
    y: float
    name: str


# Node size estimates (pixels)
ENTITY_BASE_W = 140
ENTITY_BASE_H = 60
ENTITY_ATTR_H = 18  # per attribute
ASSOC_BASE_W = 120
ASSOC_BASE_H = 50
ASSOC_ATTR_H = 18


def _estimate_size(node, attr_count: int, is_entity: bool):
    if is_entity:
        return ENTITY_BASE_W, ENTITY_BASE_H + attr_count * ENTITY_ATTR_H
    return ASSOC_BASE_W, ASSOC_BASE_H + attr_count * ASSOC_ATTR_H


def auto_layout(entities: list, associations: list, links: list,
                iterations: int = 100) -> None:
    """Fruchterman-Reingold force-directed layout.

    Mutates x, y on entity and association objects.
    ``links`` must have ``entity_name`` and ``association_name`` attributes
    (parsed link objects) OR ``entity_id`` and ``association_id`` (model objects).
    """
    # Build a unified node list
    nodes = []
    node_sizes = []
    name_to_idx = {}

    for e in entities:
        idx = len(nodes)
        nodes.append(e)
        ac = len(e.attributes) if hasattr(e, "attributes") else 0
        node_sizes.append(_estimate_size(e, ac, True))
        name_to_idx[getattr(e, "name", getattr(e, "id", ""))] = idx
        if hasattr(e, "id"):
            name_to_idx[e.id] = idx

    for a in associations:
        idx = len(nodes)
        nodes.append(a)
        ac = len(a.attributes) if hasattr(a, "attributes") else 0
        node_sizes.append(_estimate_size(a, ac, False))
        name_to_idx[getattr(a, "name", getattr(a, "id", ""))] = idx
        if hasattr(a, "id"):
            name_to_idx[a.id] = idx

    n = len(nodes)
    if n == 0:
        return

    # Build edge list
    edges = []
    for lnk in links:
        ename = getattr(lnk, "entity_name", None) or getattr(lnk, "entity_id", "")
        aname = getattr(lnk, "association_name", None) or getattr(lnk, "association_id", "")
        ei = name_to_idx.get(ename)
        ai = name_to_idx.get(aname)
        if ei is not None and ai is not None:
            edges.append((ei, ai))

    # Area and ideal spring length
    area = max(n * 200 * 200, 400 * 400)
    k = math.sqrt(area / n)

    # Initial circular placement
    random.seed(42)
    radius = k * math.sqrt(n) / 2
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n
        node.x = radius * math.cos(angle)
        node.y = radius * math.sin(angle)

    # Displacement arrays
    dx = [0.0] * n
    dy = [0.0] * n

    temp = k * 2  # initial temperature
    cooling = temp / iterations

    for _ in range(iterations):
        # Reset displacements
        for i in range(n):
            dx[i] = 0.0
            dy[i] = 0.0

        # Repulsive forces (all pairs)
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

        # Attractive forces (edges only)
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

        # Apply displacements clamped by temperature
        for i in range(n):
            disp = math.sqrt(dx[i] * dx[i] + dy[i] * dy[i])
            if disp > 0:
                scale = min(disp, temp) / disp
                nodes[i].x += dx[i] * scale
                nodes[i].y += dy[i] * scale

        temp -= cooling
        if temp < 0.1:
            temp = 0.1

    # Post-processing: overlap removal nudge
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
                        if nodes[i].x < nodes[j].x:
                            nodes[i].x -= shift
                            nodes[j].x += shift
                        else:
                            nodes[i].x += shift
                            nodes[j].x -= shift
                    else:
                        shift = oy / 2 + 1
                        if nodes[i].y < nodes[j].y:
                            nodes[i].y -= shift
                            nodes[j].y += shift
                        else:
                            nodes[i].y += shift
                            nodes[j].y -= shift
                    moved = True
        if not moved:
            break

    # Centre result on (0, 0)
    if n > 0:
        cx = sum(nd.x for nd in nodes) / n
        cy = sum(nd.y for nd in nodes) / n
        for nd in nodes:
            nd.x -= cx
            nd.y -= cy

    # Round to integers for cleaner positions
    for nd in nodes:
        nd.x = round(nd.x)
        nd.y = round(nd.y)
