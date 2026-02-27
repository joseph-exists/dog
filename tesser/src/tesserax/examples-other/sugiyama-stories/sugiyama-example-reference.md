Sugiyama-style hierarchical drawings excel at visualizing DAGs like workflows or dependencies by layering nodes top-to-bottom, minimizing edge crossings via multi-pass heuristics.

Required Inputs
Directed acyclic graphs (DAGs) serve as primary input, with nodes (vertices) and directed edges; cycles must be broken by feedback arc sets to enforce acyclicity.

Optional node/edge attributes include labels, sizes, ports, groups (subhierarchies), and roots/sources for layer seeding.

The real-world data formats: GraphML, DOT, JSON, or adjacency lists, supporting 100s-1000s of nodes.  Start with JSON, potential expansion.
​
​

Core Parameters & Controls
Layer assignment: Node-to-layer mapping (e.g., longest path, BFS levels); controls like layer distance, max layers, dummy node insertion for spans >1.

Crossing minimization: Sweep passes (1-10+ iterations, up-down sweeps), barycenter/median heuristics, sibling swaps; tolerance for local optima.

Node positioning: Uniform/attribute-based spacing, alignment (left/center/right), port models (fixed side positions).

Edge routing: Straight/polyline/orthogonal; bend minimization, splines for curves.
​
User controls: Direction (TB/LR), constraints (fixed order/positions), stability weights for incremental reruns.

Best-in-Class Functionality
Multi-iteration sweeps (phase 1: layer-by-layer sort/swap; phase 2: global sifting) reduce crossings to near-optimal via NP-hard heuristics, escaping local minima.

Interactive previews, constraint editing (model order, port sides), and stability for dynamic graphs (e.g., yFiles auto-rerun).

High-quality output: SVG export, labels without overlap, scalable rendering (zoom/filter), animations for layout transition.


For future reference:

| Aspect             | Compelling Minimum     | Best-in-Class        |
| ------------------ | ---------------------- | ----------------------------------------------- |
| Crossing Reduction | 1-2 sweeps, barycenter | 10+ passes, sifting, 90%+ optimal terrastruct+1 |
| Scalability        | 500 nodes              | 10k+ nodes, incremental yfiles​                 |
| Interactivity      | Basic zoom             | Constraints, undo, live edit ​             |
| Styling            | Basic shapes           | Ports, bundling, themes yfiles​                 |