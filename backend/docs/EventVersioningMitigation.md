<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

## Critical Gaps in Event Versioning Strategy

### Missing Infrastructure

**No Version Metadata in Event Schema**
The `roomevents` table lacks a `version` field, contradicting established event sourcing best practices. The current schema only stores `eventtype VARCHAR(50)` and `payload JSONB`, providing no way to distinguish between v1 and v2 of the same event type during replay.[^3][^4]

**No Schema Registry or Validation**
Unlike production event sourcing systems that use Avro/JSON Schema registries, Minimog has no mechanism to:

- Validate event payloads against formal schemas
- Detect breaking changes during development
- Provide backward compatibility guarantees
- Support blue-green deployments with mixed event versions

**Contradiction: Immutability vs. Evolution**
The design correctly states events are immutable (DG1.1), but provides no strategy for evolving the *schema* without mutating existing events. This creates an unsolvable conflict: when you add a required field to `message.user`, how do you replay old events that lack it?

### Expert Architect Assessment

**Phase 1 Decomposition: Required Versioning Infrastructure**

1. **Event Version Field (Mandatory)**

```sql
ALTER TABLE roomevents ADD COLUMN eventversion INT NOT NULL DEFAULT 1;
CREATE INDEX idx_roomevents_version ON roomevents(eventtype, eventversion);
```

2. **Upcasting Layer**
    - Implement `EventUpcaster` service that transforms old event versions to current version during replay
    - Each event type needs explicit upcasters: `v1→v2`, `v2→v3`, etc.
    - Upcasters must be idempotent and reversible for debugging
3. **Schema Registry**
    - Store JSON Schemas for each event type/version in `eventschemas` table
    - Enforce payload validation on `emitevent()` calls
    - Provide schema evolution compatibility checks in CI/CD
4. **Versioning Strategy Rules**
    - **Additive changes only** (new optional fields) = increment minor version
    - **Breaking changes** (required field removal/type change) = new event type
    - **Event type deprecation** = mark old type, create new type, provide migration guide

**Risk Mitigation for Phase 1**

- **Short-term**: Add `eventversion` field immediately; all events start at v1
- **Medium-term**: Implement upcasting before any schema changes occur
- **Long-term**: Build schema registry and compatibility validation into deployment pipeline

**Contradictions to Resolve**

- The "PENDING REVIEW" status on schema definitions  indicates immaturity, yet the document claims "Implementation-Ready System Specification"[^1]
- No snapshotting strategy is defined, despite the event log growth assumption of 10M events[^1]
- The 4-5 day Phase 1 timeline is unrealistic given the missing versioning infrastructure[^5][^1]

**Expert Recommendation**: Delay Phase 1 until event versioning strategy is fully specified and prototyped. The current design will create technical debt that becomes exponentially harder to fix after production deployment.[^6][^7]

<div align="center">⁂</div>

[^1]: Minimog.md

[^2]: https://martinfowler.com/eaaDev/EventSourcing.html

[^3]: https://www.baytechconsulting.com/blog/event-sourcing-explained-2025

[^4]: https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing

[^5]: MasterImplementationPlan.md

[^6]: https://news.ycombinator.com/item?id=29390483

[^7]: https://www.dennisdoomen.com/2020/06/guidelines-event-sourcing.html

