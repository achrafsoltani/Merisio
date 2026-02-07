# Chapter 6: The Builder

The builder is the third stage of the MSD pipeline. It takes the intermediate representation produced by the parser (`ParseResult`) and creates a fully-formed Merisio `Project` with UUIDs, resolved references, and validated semantics.

## 6.1 Architecture Overview

The builder lives in `src/msd/builder.py` and contains:

| Component | Description |
|-----------|-------------|
| `MSDProjectBuilder` | Main builder class |
| `_levenshtein()` | Edit distance function |
| `_suggest()` | "Did you mean?" suggestion engine |

The public API is a single method:

```python
builder = MSDProjectBuilder()
project, errors = builder.build(parse_result)
```

It returns a tuple of `(Project, List[MSDError])`. The project is always returned (even if partially populated), and the error list includes both syntax errors from the parser and semantic errors from the builder.

## 6.2 The Build Pipeline

The `build()` method executes six steps in order:

1. **Collect existing errors** from the parse result
2. **Apply metadata** to the project
3. **Build entities** — create `Entity` objects with `Attribute` objects
4. **Build associations** — create `Association` objects with carrying attributes
5. **Build links** — resolve name references to UUIDs
6. **Run auto-layout** — position all elements on the canvas

### Step 1: Error Collection

```python
errors: List[MSDError] = list(parse_result.errors)
filename = parse_result.filename
```

The builder starts with a copy of the parser's error list. Any new errors discovered during building are appended to this same list, so the caller gets a unified list of all errors from all stages.

### Step 2: Metadata

```python
if parse_result.metadata:
    m = parse_result.metadata
    if m.name:
        project.name = m.name
    if m.author:
        project.author = m.author
    if m.description:
        project.description = m.description
```

Metadata is optional. If a `project {}` block was present, its values are applied to the `Project` object. Empty strings are not applied, preserving defaults.

### Step 3: Entity Construction

```python
for pe in parse_result.entities:
    if pe.name in entity_names:
        errors.append(MSDError(
            message=f"duplicate entity name: '{pe.name}'",
            ...
        ))
        continue

    entity = Entity(name=pe.name)
    has_pk = False
    for pa in pe.attributes:
        attr = Attribute(
            name=pa.name,
            data_type=pa.data_type,
            size=pa.size,
            is_primary_key=pa.is_primary_key,
        )
        entity.add_attribute(attr)
        if pa.is_primary_key:
            has_pk = True

    if not has_pk:
        errors.append(MSDError(
            message=f"entity '{pe.name}' has no primary key",
            severity="warning",
            ...
        ))

    entity_names[pe.name] = entity
    project.add_entity(entity)
```

For each parsed entity:

1. **Duplicate check** — if an entity with this name already exists, report an error and skip it
2. **Create Entity** — a new `Entity` with a generated UUID (via the default factory in the dataclass)
3. **Create Attributes** — each `ParsedAttribute` becomes an `Attribute` model object
4. **Primary key check** — if no attribute is marked as PK, emit a warning
5. **Register** — add to both the name lookup table and the project

The `Entity` constructor automatically generates a UUID via `field(default_factory=lambda: str(uuid.uuid4()))`. No explicit UUID management is needed.

### Step 4: Association Construction

```python
for pa in parse_result.associations:
    if pa.name in assoc_names:
        errors.append(MSDError(message=f"duplicate association name: '{pa.name}'", ...))
        continue

    if pa.name in entity_names:
        errors.append(MSDError(
            message=f"association name '{pa.name}' conflicts with an entity of the same name",
            ...
        ))
        continue

    assoc = Association(name=pa.name)
    for attr_parsed in pa.attributes:
        attr = Attribute(
            name=attr_parsed.name,
            data_type=attr_parsed.data_type,
            size=attr_parsed.size,
            is_primary_key=attr_parsed.is_primary_key,
        )
        assoc.add_attribute(attr)

    assoc_names[pa.name] = assoc
    project.add_association(assoc)
```

Similar to entities, with an additional check: association names must not conflict with entity names. This prevents ambiguity in link references.

### Step 5: Link Resolution

```python
for pl in parse_result.links:
    entity = entity_names.get(pl.entity_name)
    if entity is None:
        msg = f"unknown entity: '{pl.entity_name}'"
        suggestion = _suggest(pl.entity_name, all_entity_names)
        if suggestion:
            msg += f" (did you mean '{suggestion}'?)"
        errors.append(MSDError(message=msg, ...))
        continue

    assoc = assoc_names.get(pl.association_name)
    if assoc is None:
        msg = f"unknown association: '{pl.association_name}'"
        suggestion = _suggest(pl.association_name, all_assoc_names)
        if suggestion:
            msg += f" (did you mean '{suggestion}'?)"
        errors.append(MSDError(message=msg, ...))
        continue

    link = Link(
        entity_id=entity.id,
        association_id=assoc.id,
        cardinality_min=pl.cardinality_min,
        cardinality_max=pl.cardinality_max,
    )
    project.add_link(link)
```

This is where name-to-UUID resolution happens. The parser stored entity and association names in links; the builder resolves them to the UUIDs of the actual `Entity` and `Association` objects.

If a name cannot be resolved, the builder:
1. Reports an error with the unknown name
2. Attempts to find a similar name using Levenshtein distance
3. Includes a "did you mean?" suggestion if a close match exists
4. Skips the link

### Step 6: Auto-Layout

```python
if all_entities or all_associations:
    # Build name-based proxies for the layout engine
    class _LayoutLink:
        def __init__(self, entity_name, association_name):
            self.entity_name = entity_name
            self.association_name = association_name

    layout_links = []
    for lnk in all_links:
        en = id_to_name.get(lnk.entity_id, "")
        an = id_to_name.get(lnk.association_id, "")
        layout_links.append(_LayoutLink(en, an))

    auto_layout(all_entities, all_associations, layout_links)
```

After all model objects are created, the builder calls the auto-layout engine. The layout engine works with name-based references, so the builder creates lightweight proxy objects that translate UUIDs back to names.

See Chapter 7 for details on the layout algorithm.

## 6.3 The "Did You Mean?" System

One of the builder's most user-friendly features is its typo suggestions. When a link references an entity or association that does not exist, the builder searches for close matches.

### Levenshtein Distance

The edit distance between two strings is computed using the classic dynamic programming algorithm:

```python
def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        return _levenshtein(b, a)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]
```

This is an optimised version that uses O(min(m,n)) space rather than O(m*n), by always making `a` the longer string and using two rows instead of a full matrix.

### Suggestion Logic

```python
def _suggest(name: str, candidates: list, max_distance: int = 3) -> Optional[str]:
    best = None
    best_dist = max_distance + 1
    for c in candidates:
        d = _levenshtein(name.lower(), c.lower())
        if d < best_dist:
            best_dist = d
            best = c
    return best if best_dist <= max_distance else None
```

The suggestion engine:
1. Compares case-insensitively (so `tourits` matches `Tourist`)
2. Returns the closest match within a maximum distance of 3 edits
3. Returns `None` if no match is close enough

### Example

```msd
entity Tourist { *id: INT }
association voyager { }
link Tourits (0,N) voyager    # Typo: "Tourits" instead of "Tourist"
```

Output:
```
schema.msd:3: error: unknown entity: 'Tourits' (did you mean 'Tourist'?)
```

The Levenshtein distance between "tourits" and "tourist" is 2 (swap `i` and `s`, add `t` → actually it is a transposition), which is within the threshold of 3.

## 6.4 Semantic Validations

The builder performs five types of semantic validation:

| Validation | Severity | Message |
|------------|----------|---------|
| Duplicate entity name | Error | `duplicate entity name: 'X'` |
| Duplicate association name | Error | `duplicate association name: 'X'` |
| Entity/association name conflict | Error | `association name 'X' conflicts with an entity of the same name` |
| Unknown entity in link | Error | `unknown entity: 'X'` (with suggestion) |
| Unknown association in link | Error | `unknown association: 'X'` (with suggestion) |
| Entity without primary key | Warning | `entity 'X' has no primary key` |

Errors prevent the link from being created but do not abort the build. Warnings are informational — the entity is still created.

## 6.5 UUID Generation

The builder does not explicitly generate UUIDs. Instead, it relies on the `Entity`, `Association`, and `Link` dataclasses, which all have:

```python
id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

Every time a model object is created with `Entity(name="Tourist")`, a new UUID is automatically generated. This is a clean separation of concerns — the builder does not need to know about UUID generation.

## 6.6 Error Propagation

The builder's error handling design is worth highlighting:

1. **Parser errors are preserved** — the builder starts with `list(parse_result.errors)`, copying all parser errors
2. **Builder errors are appended** — semantic errors are added to the same list
3. **Filename is propagated** — the builder reads `parse_result.filename` and includes it in all error objects
4. **Build always completes** — even with errors, the builder returns a (possibly partial) project

This means the caller always gets a single, unified error list:

```python
project, errors = builder.build(parse_result)
for err in errors:
    print(err)  # Includes both syntax and semantic errors
```

## 6.7 Design Decisions

### Why Not Validate During Parsing?

The parser could check for duplicate names or unknown references. However:

1. **Links may reference entities defined later** — the parser would need a two-pass approach
2. **Separation of concerns** — the parser handles syntax, the builder handles semantics
3. **Error quality** — the builder has access to all entities and associations, enabling suggestions

### Why Return a Partial Project on Error?

Some users may want to inspect the valid parts of a model even when some links are broken. Returning a partial project also makes debugging easier — you can see what was successfully parsed.

### Why Copy Errors Instead of Sharing?

The builder creates a new error list with `list(parse_result.errors)` rather than modifying the original. This ensures the `ParseResult` remains immutable after parsing, which is important for testability and debugging.
