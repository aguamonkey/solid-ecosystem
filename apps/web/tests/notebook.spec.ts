import { expect, test, type Page } from "@playwright/test";

async function fill(page: Page, identity: string, station = "North ridge") {
  await page.getByLabel("Observation identity").fill(identity);
  await page.getByLabel("Station name").fill(station);
  await page.getByLabel("Temperature Kelvin").fill("281.25");
}

test("real API records, lists, exports, and processes a receipt", async ({
  page,
}) => {
  await page.goto("/");
  await fill(page, "browser-001");
  await page.getByRole("button", { name: "Record observation" }).click();
  await expect(page.locator("#submission-status")).toContainText(
    "confirmed and stored",
  );
  await expect(
    page.locator(".record").filter({ hasText: "browser-001" }),
  ).toContainText("8.10 °C");
  const exported = await page.request.get("/api/export?format=json&limit=100");
  expect(
    (await exported.json()).some(
      (row) => row.observation.identity === "browser-001",
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Process one receipt" }).click();
  await expect(page.locator("#receipt-status")).toContainText(
    "Receipt acknowledged",
  );
});

test("lost acknowledgement retries identical intent without creating another row", async ({
  page,
}) => {
  let calls = 0;
  let initialKey: string | undefined;
  let initialBody: string | null;
  await page.route("**/api/readings", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    calls += 1;
    if (calls === 1) {
      initialKey = route.request().headers()["idempotency-key"];
      initialBody = route.request().postData();
      await route.fetch(); // Commit in the REAL backend, then lose its response.
      return route.abort("failed");
    }
    expect(route.request().headers()["idempotency-key"]).toBe(initialKey);
    expect(route.request().postData()).toBe(initialBody);
    return route.continue();
  });
  await page.goto("/");
  await fill(page, "lost-ack-001");
  await page.getByRole("button", { name: "Record observation" }).click();
  await expect(page.getByLabel("Observation identity")).toBeDisabled();
  await page.getByRole("button", { name: "Retry same submission" }).click();
  await expect(page.locator("#submission-status")).toContainText(
    "No duplicate was created",
  );
  const response = await page.request.get("/api/readings?limit=100");
  expect(
    (await response.json()).readings.filter(
      (row) => row.observation.identity === "lost-ack-001",
    ),
  ).toHaveLength(1);
});

test("failed refresh keeps confirmed records visible and reports the error", async ({
  page,
}) => {
  await page.request.post("/api/readings", {
    data: { identity: "refresh-001", station: "Refresh station", kelvin: 280 },
    headers: { "Idempotency-Key": "refresh-001" },
  });
  await page.goto("/");
  await expect(page.locator("#read-status")).toContainText(
    "Confirmed observations",
  );
  const before = await page.locator(".record").count();
  await page.route("**/api/readings?*", (route) =>
    route.fulfill({ status: 503, body: "{}" }),
  );
  await page.getByRole("button", { name: "Refresh" }).click();
  await expect(page.locator("#read-status")).toContainText("Could not refresh");
  await expect(page.locator(".record")).toHaveCount(before);
});

test("user text renders as text and a conflicting intent leaves original data intact", async ({
  page,
}) => {
  await page.goto("/");
  await fill(page, "escaped-001", "<img src=x onerror=alert(1)>");
  await page.getByRole("button", { name: "Record observation" }).click();
  await expect(
    page.locator(".record").filter({ hasText: "escaped-001" }),
  ).toContainText("<img");
  await expect(page.locator(".records img")).toHaveCount(0);
  await page.getByRole("button", { name: "Start a new submission" }).click();
  await page.getByLabel("Temperature Kelvin").fill("282");
  await page.getByRole("button", { name: "Record observation" }).click();
  await expect(page.locator("#submission-status")).toContainText(
    "already in use",
  );
  const original = await page.request.get("/api/readings/escaped-001");
  expect((await original.json()).observation.kelvin).toBe(281.25);
});

test("mobile layout fits the viewport and marks future components honestly", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Make an observation." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await expect(page.getByText("Planned · not connected yet")).toHaveCount(1);
  await expect(page.getByText("Planned · collector agent")).toHaveCount(1);
});

test("interactive API schema uses the proxy base", async ({ page }) => {
  const response = await page.request.get("/api/openapi.json");
  expect((await response.json()).servers).toContainEqual({ url: "/api" });
  await page.goto("/api/docs");
  await expect(
    page.getByRole("heading", { name: "Field Notebook" }),
  ).toBeVisible();
});

test("an acknowledgement for another observation is not treated as confirmation", async ({
  page,
}) => {
  await page.route("**/api/readings", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    return route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        outcome: "created",
        reading: {
          sequence: 1,
          observation: {
            identity: "somebody-else",
            station: "Wrong station",
            kelvin: 280,
          },
        },
      }),
    });
  });
  await page.goto("/");
  await fill(page, "ack-check-001");
  await page.getByRole("button", { name: "Record observation" }).click();
  await expect(page.locator("#submission-status")).toContainText(
    "did not match",
  );
  await expect(
    page.getByRole("button", { name: "Retry same submission" }),
  ).toBeEnabled();
});

test("pagination reaches records beyond the first page without duplicates", async ({
  page,
}) => {
  for (let index = 0; index < 26; index += 1) {
    const identity = `page-${index}`;
    const response = await page.request.post("/api/readings", {
      data: { identity, station: "Page station", kelvin: 280 },
      headers: { "Idempotency-Key": identity },
    });
    expect([200, 201]).toContain(response.status());
  }
  await page.goto("/");
  await expect(page.locator(".record")).toHaveCount(25);
  await page.getByRole("button", { name: "Load next page" }).click();
  await expect(
    page.locator(".record").filter({ hasText: "page-25" }),
  ).toHaveCount(1);
  const identities = await page.locator(".record p").allTextContents();
  expect(new Set(identities).size).toBe(identities.length);
});
