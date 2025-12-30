### Risk: Backend Delete Endpoint Missing

**issue**: `deleteRoom` needs design post phase 4
**Mitigation**:
1. currently stubbed


### Risk: User Lookup Performance

**Impact**: additional API calls for user details
**Mitigation**:
1. Implement simple in-memory cache (`Map`)
2. Batch fetch user details for all messages at once
3. Monitor performance, optimize if needed
4. Future: Add user details to message response in backend

### Risk: Agent List Hardcoded

**Impact**: Task 4 hardcodes agent list (not fetched from backend)
**Mitigation**:
1. Acceptable for Phase 3.2 MVP
2. Document for Phase 4 enhancement
3. Backend agent registry endpoint can be added later

### Risk: Design Changes

**Impact**: UX review may change component structure
**Mitigation**:
1. Components are minimal and focused
2. Easy to refactor based on feedback
3. Data layer (hooks, services) remains stable
4. Only UI layer needs adjustment