import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:5181", trace: "retain-on-failure" },
  webServer: [
    {
      command:
        "../../services/api/.venv/bin/python ../../scripts/browser_api.py",
      url: "http://127.0.0.1:8011/ready",
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command:
        "npx vite --host 127.0.0.1 --port 5181 --strictPort --config vite.test.config.ts",
      url: "http://127.0.0.1:5181",
      reuseExistingServer: false,
      timeout: 30000,
    },
  ],
});
