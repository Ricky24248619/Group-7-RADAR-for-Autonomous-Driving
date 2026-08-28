# Traversability mapping — contested assignments

Checkpoint notes for R3. The CSV is deliberately conservative: an assignment means
what can be inferred from the semantic class alone, without assuming favourable depth,
geometry, traction, vehicle clearance, or legal access.

| Class | Current assignment | Why it is contested | Checkpoint question |
|---|---|---|---|
| `snow` | Potentially Traversable | Depth, ice and hidden terrain are unknown. | Keep conditional, or classify all unknown snow as non-traversable? |
| `moss` | Potentially Traversable | Usually shallow, but grip and substrate are unknown. | Does the project model physical passability or operational safety? |
| `sidewalk` | Traversable | Physically driveable but ordinarily not a legal vehicle route. | Keep legality outside the mapping? |
| `curb` | Potentially Traversable | Vehicle clearance and curb height determine the result. | Should geometry override the semantic prior later? |
| `rail_track` | Potentially Traversable | Crossable in some orientations, hazardous in others. | Is a semantic-only map sufficiently conservative? |
| `debris` | Potentially Traversable | The class spans shallow litter and damaging objects. | Split only if geometry or subclasses become available? |
| `crops` | Potentially Traversable | Physically passable, but conceals terrain and has operational constraints. | Treat crop damage as outside physical traversability? |
| `soil` | Traversable | Mud, slope and moisture are not represented by the class. | Keep the normal-condition assumption? |
| `bridge` | Potentially Traversable | The label may cover deck, sides or structure. | Require geometry before upgrading deck points? |
| `tunnel` | Potentially Traversable | The label may cover floor, walls and ceiling. | Require geometry before upgrading floor points? |
| `high_grass` | Potentially Traversable | It can hide holes, rocks or debris. | This is the key client-facing uncertainty; keep explicit. |
| `scenery_vegetation` | Potentially Traversable | Density and substrate are unspecified. | Is a generic vegetation class too ambiguous to use? |
| `water` | Non-Traversable | Shallow water can be crossed, but depth is absent. | Keep the conservative unknown-depth rule? |
| `tree_root` | Potentially Traversable | Clearance depends on root size and vehicle geometry. | Should visible roots default to non-traversable? |

Assignments should change in `traversability_map.csv`, never as hard-coded exceptions in
Damien's renderer. A changed row must retain its rationale so the decision stays
reviewable.
