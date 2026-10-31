import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "../../tests/browser",
  testMatch: "**/*.spec.ts",
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:8766",
    viewport: { width: 1440, height: 1100 },
    trace: "retain-on-failure",
    headless: true,
  },
  webServer: {
    command:
      "..\\..\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --app-dir ../../services/backend --host 127.0.0.1 --port 8766",
    env: { ...process.env, SCST_DATA_DIR: `${process.env.TEMP || "."}/scst-playwright-${process.pid}` },
    url: "http://127.0.0.1:8766/api/health",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
