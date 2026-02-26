 **Containment**,



1. **Primary concept: Surface + Children**
- Every panel/block is a surface.
- A surface can optionally host child surfaces.
- Children render inside named slots (`header`, `body`, `footer`, `sidebar`, etc.).

2. **Editor UX: “Add Child” instead of raw JSON nesting**
- On each panel/block card: `Add Child` and `Manage Children`.
- Show child chips/list with type, title, order.
- Support drag reorder, remove, clone-from-source directly into this parent.

3. **Visibility model in UI**
- Add a breadcrumb/tree view:
- `Page > Panel A > Block X > Block Y`
- Keep current flat editors, but add a “Composition Tree” pane as the navigation spine.

4. **Contract language**
- Expose this as:
- `children[]` + `slot` + `order` + `visibility`
- Avoid “nested panel inside block” wording in UI; users choose *child type* and *placement slot*.

5. **Guardrails**
- Prevent cycles (parent cannot become descendant).
- Soft depth guidance (warn after depth 2/3).
- Inherited theme/presentation badges (“inherits from parent” vs “override”).
