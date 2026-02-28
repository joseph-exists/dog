# Force-Directed Visualization Index for Tesserax

This index prioritizes force-directed/network visualizations that are compelling for Tesserax users.

## Tier 1: Build Now (Existing Primitives)

These are high-value with current capabilities (`ForceLayout`, `HierarchicalLayout`, `Arrow`, `KeyframeAnimation`, camera modes, physics overlays, scenario/policy/report patterns).

1. Service Dependency Blast Radius Map
- Why compelling: clear operations context; maps incident impact and recovery over topology.
- Current fit: very strong (reuse patterns from `animation_incident_response_playbook.py`).

2. Supply Chain Network Stress Graph
- Why compelling: tangible business narrative for reroute and congestion effects.
- Current fit: very strong (already close to `animation_supply_chain_resilience.py`).

3. Grid Reliability Topology (Static Snapshot Variant)
- Why compelling: communicates contingency posture quickly in static form.
- Current fit: strong (derived from `animation_grid_contingency_cascade.py`).

4. CI/CD Pipeline Dependency Network
- Why compelling: broadly relatable to engineering orgs; highlights bottlenecks and critical paths.
- Current fit: strong (DAG + stress overlays).

5. Data Lineage/ETL Dependency Graph
- Why compelling: useful for debugging and governance communication.
- Current fit: strong (node criticality + edge throughput styling).

6. Microservice Call Graph with SLO Risk Overlay
- Why compelling: direct production relevance and easy metric interpretation.
- Current fit: strong (risk halos, edge thickness, packet traffic).

7. Knowledge/Concept Graph Explorer (Curated Subgraphs)
- Why compelling: pedagogical and product documentation value.
- Current fit: medium-high (works best with moderate graph sizes).

8. Org/Ownership Network with Escalation Paths
- Why compelling: clarifies on-call and ownership boundaries.
- Current fit: medium-high (static + light animation).

## Tier 2: High-Value if Added to Core Library

These become significantly better with targeted core improvements.

1. Port-Constrained Architecture Graphs
- Value: precise semantic routing (input/output ports, side-specific edges).
- Needed core additions: node ports, port-side constraints, port-aware edge anchors.

2. Orthogonal Routing for Dense Technical Diagrams
- Value: dramatically better readability in infrastructure and workflow maps.
- Needed core additions: orthogonal/obstacle-avoiding edge router.

3. Edge Bundling for Large Relationship Graphs
- Value: declutters high-edge-count visualizations.
- Needed core additions: geometric/semantic bundling primitives.

4. Incremental Stable Relayout for Time-Varying Graphs
- Value: prevents layout jitter and improves story continuity.
- Needed core additions: stability-weighted incremental layout API.

5. Constraint Editing and Locked Subgraphs
- Value: enables user-guided narrative layouts that remain stable on reruns.
- Needed core additions: pin/lock constraints, layer/order constraints.

6. Cluster/Community Containers with Auto Hulls
- Value: contextual grouping for domains, teams, or subsystems.
- Needed core additions: cluster hull shapes + layout-aware grouping.

7. Label Collision Avoidance for Dense Graphs
- Value: improves publication-quality outputs.
- Needed core additions: label placement/collision solver.

8. Multi-Pass Crossing Minimization Controls
- Value: gets closer to best-in-class Sugiyama/graph layout quality.
- Needed core additions: multi-sweep barycenter/median/sifting controls.

## Best Next Example Set (Recommended)

If the goal is maximum user value with current stack:

1. `animation_service_blast_radius.py`
2. `animation_cicd_dependency_risk.py`
3. `static_data_lineage_map.py`
4. `static_microservice_slo_graph.py`

Current scaffold implementations added:
- `examples-other/animation/operations/animation_service_blast_radius.py`
- `examples-other/animation/operations/animation_supply_chain_network_stress.py`
- `examples-other/animation/operations/animation_service_blast_radius_runner.py`
- `examples-other/animation/operations/animation_supply_chain_network_stress_runner.py`
- `examples-other/animation/topology/animation_cicd_dependency_risk.py`
- `examples-other/animation/topology/animation_cicd_dependency_risk_runner.py`

If the goal is core-library differentiation:

1. Add orthogonal routing + simple ports
2. Add incremental stable relayout
3. Add edge bundling (heuristic first pass)
4. Publish a force-directed routing showcase comparing modes on one graph

## Practical Interpretation

- Today: Tesserax already supports compelling network storytelling and operations-grade graph narratives.
- Highest ROI additions: routing constraints, stability controls, and dense-graph readability features.
- Differentiator path: combine topology + state + animation + reproducible scenario runners (already proven in current examples).
