
### E2E Tests (Playwright)

**Critical User Journeys**:

1. **Full Authoring Flow**:
```typescript
test('author creates and publishes story', async ({ page }) => {
  // Login as author
  await page.goto('/login');
  await page.fill('[name="email"]', 'author@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  // Navigate to stories
  await page.click('a[href="/stories"]');

  // Create new story
  await page.click('text=+ New Story');
  await page.fill('[name="title"]', 'Test Story');
  await page.fill('[name="description"]', 'A test adventure');
  await page.click('text=Create');

  // Verify story appears
  await expect(page.locator('text=Test Story')).toBeVisible();

  // Click edit
  await page.click('text=Edit');

  // Add start node
  await page.click('text=+ Node');
  await page.fill('[name="title"]', 'Beginning');
  await page.fill('[name="content"]', 'Your journey begins...');
  await page.check('[name="is_start_node"]');
  await page.click('text=Save Node');

  // Publish
  await page.click('text=Publish');
  await page.click('text=Confirm'); // In publish modal

  // Verify published
  await expect(page.locator('text=Published v1')).toBeVisible();
});
```

2. **Version Management**:
```typescript
test('author creates new version of published story', async ({ page }) => {
  // ... navigate to published story ...

  // Create new version
  await page.click('text=Create New Version');
  await expect(page.locator('text=Draft v2')).toBeVisible();

  // Edit node
  await page.click('text=Beginning'); // Select node
  await page.fill('[name="content"]', 'Your NEW journey begins...');
  await page.click('text=Save');

  // Verify v1 still published
  await expect(page.locator('text=Published v1')).toBeVisible();
  await expect(page.locator('text=Draft v2')).toBeVisible();

  // Publish v2
  await page.click('text=Publish');
  await page.click('text=Confirm');

  // Verify now on v2
  await expect(page.locator('text=Published v2')).toBeVisible();
});
```
