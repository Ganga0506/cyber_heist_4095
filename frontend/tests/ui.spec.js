import { test, expect } from "@playwright/test";
async function mockGame(page, { coding = false } = {}) {
  let started = false,
    solved = [],
    expired = false;
  const drafts = {};
  const purchased = {};
  let coins = 20;
  const missions = [1, 2, 3, 4, 5].map((id) => ({
    id,
    mission_order: id,
    title: `MISSION ${id}`,
    description: "Investigate the clues and find the access key.",
    topic: "Encoding and investigation",
    is_mvp: [1, 2, 5].includes(id),
    puzzle_count: 2,
  }));
  const puzzles = [1, 2].map((id) => ({
    id,
    puzzle_order: id,
    title: `Puzzle ${id}`,
    description: "Decode the access note.",
    instructions: "Find the key in this fictional evidence. Submit ACCESS.",
    points: 100,
    ...(coding && {
      lesson: {
        title: `Coding lesson ${id}`,
        concept: "Function calls",
        objective: "Decode the input.",
        explanation: "Pass a variable to decode64.",
        starter: 'decode64("SEVMTE8=")',
        hint_count: 3,
        recap: `Concept practiced in lesson ${id}.`,
      },
    }),
  }));
  const hintPrices = { 1: [3, 5, 8], 2: [4, 7, 10] };
  const puzzleRewards = { 1: 6, 2: 9 };
  let earned = 0;
  function completePuzzle(id) {
    if (solved.includes(id)) return 0;
    solved.push(id);
    const reward = puzzleRewards[id] + (solved.length === 2 ? 10 : 0);
    coins += reward;
    earned += reward;
    return reward;
  }
  const missionProgress = (id) => ({
    mission_id: id,
    title: `MISSION ${id}`,
    mission_order: id,
    status:
      id === 1
        ? solved.length === 2
          ? "completed"
          : started
            ? "in_progress"
            : "available"
        : id === 2 && solved.length === 2
          ? "available"
          : "locked",
    puzzles:
      id === 1
        ? puzzles.map((p) => ({
            puzzle_id: p.id,
            solved: solved.includes(p.id),
            points_earned: solved.includes(p.id) ? 100 : 0,
            draft: drafts[p.id],
            purchased_hints: purchased[p.id] ?? [],
            hint_prices: hintPrices[p.id],
            coin_reward: puzzleRewards[p.id],
          }))
        : [],
  });
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname,
      method = route.request().method();
    let body = {},
      status = 200;
    if (expired && route.request().headers().authorization) {
      status = 401;
      body = { detail: "Session missing or expired" };
    } else if (path.endsWith("/health")) body = { status: "ok" };
    else if (path === "/api/missions") body = missions;
    else if (path.endsWith("/leaderboard"))
      body = {
        entries: [
          {
            rank: 1,
            username: "test.agent",
            score: solved.length * 100,
            puzzles_solved: solved.length,
            coins_earned: earned,
          },
        ],
      };
    else if (path.endsWith("/auth/register")) {
      status = 201;
      body = { id: 10, username: "test.agent" };
    } else if (path.endsWith("/auth/login"))
      body = {
        access_token: "test-token",
        user: { id: 10, username: "test.agent" },
      };
    else if (path.endsWith("/auth/logout")) {
      status = 204;
    } else if (path.endsWith("/me/progress"))
      body = {
        username: "test.agent",
        score: solved.length * 100,
        puzzles_solved: solved.length,
        missions: missions.map((m) => missionProgress(m.id)),
        coins,
        mission_coin_reward: 10,
      };
    else if (path.endsWith("/start")) {
      const id = Number(path.split("/")[3]);
      if (id !== 1) {
        status = 403;
        body = { detail: "Mission locked" };
      } else {
        started = true;
        body = missionProgress(1);
      }
    } else if (path === "/api/missions/1") body = { ...missions[0], puzzles };
    else if (/\/hints\/[1-3]$/.test(path) && method === "POST") {
      const id = Number(path.split("/")[3]);
      const index = Number(path.split("/").at(-1)) - 1;
      purchased[id] ??= [];
      if (!purchased[id][index]) {
        coins -= hintPrices[id][index];
        purchased[id].push(
          [
            "Pass the input variable.",
            "Use the provided function.",
            "Leave the variable unquoted.",
          ][index],
        );
      }
      body = { hint: purchased[id][index], coins };
    } else if (path.endsWith("/code") && method === "POST") {
      const id = Number(path.split("/")[3]);
      const { action, code } = route.request().postDataJSON();
      const blocked = code.startsWith("import ");
      drafts[id] = code;
      const passed = code === "decode64(encoded)";
      body =
        action === "save"
          ? { saved: true }
          : {
              passed,
              ...(blocked && {
                status: "blocked",
                error: "Imports are blocked in this lesson (line 1).",
              }),
              cases: [
                {
                  inputs: { encoded: "Tk9URQ==" },
                  ...(blocked
                    ? { status: "skipped" }
                    : { output: passed ? "NOTE" : "<em>fixture output</em>" }),
                  expected: "NOTE",
                  passed,
                },
              ],
            };
      if (action === "submit") {
        const reward = passed ? completePuzzle(id) : 0;
        body.attempt = {
          is_correct: passed,
          points_awarded: passed ? 100 : 0,
          coins_awarded: reward,
          unlocked_mission_ids: solved.length === 2 ? [2] : [],
        };
      }
    } else if (path.endsWith("/attempts") && method === "POST") {
      const id = Number(path.split("/")[3]),
        correct = route.request().postDataJSON().answer === "ACCESS";
      const reward = correct ? completePuzzle(id) : 0;
      body = {
        is_correct: correct,
        already_solved: false,
        points_awarded: correct ? 100 : 0,
        coins_awarded: reward,
        mission: missionProgress(1),
        unlocked_mission_ids: solved.length === 2 ? [2] : [],
      };
    } else {
      status = 404;
      body = { detail: "Not found" };
    }
    await route.fulfill({
      status,
      contentType: "application/json",
      body: status === 204 ? "" : JSON.stringify(body),
    });
  });
  return {
    expire: () => {
      expired = true;
    },
  };
}
async function login(page) {
  await page.goto("/#/login");
  await page.getByLabel("Agent username").fill("test.agent");
  await page.getByLabel("Password", { exact: true }).fill("password-12345");
  await page.getByRole("button", { name: "Enter the operation" }).click();
  await expect(
    page.getByRole("heading", { name: "Mission control." }),
  ).toBeVisible();
}
async function noOverflow(page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
}
test("browser completes Google handoff and password recovery", async ({
  page,
}) => {
  await mockGame(page);
  await page.route("**/api/auth/google/session", async (route) => {
    expect(route.request().method()).toBe("POST");
    await route.fulfill({
      json: {
        access_token: "test-token",
        user: { id: 10, username: "test.agent" },
      },
    });
  });
  await page.goto("/#/google");
  await expect(
    page.getByRole("heading", { name: "Mission control." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back, agent" }),
  ).toBeVisible();

  await page.route("**/api/auth/recovery/request", async (route) => {
    expect(route.request().postDataJSON()).toEqual({
      email: "agent@example.net",
    });
    await route.fulfill({ status: 202, json: { accepted: true } });
  });
  await page.goto("/#/recover-password");
  await page.getByLabel("Account email").fill("agent@example.net");
  await page.getByRole("button", { name: "Send recovery email" }).click();
  await expect(page.getByText(/If an eligible account exists/)).toBeVisible();

  const ticket = "x".repeat(43);
  await page.route("**/api/auth/recovery/complete", async (route) => {
    expect(route.request().postDataJSON()).toEqual({
      token: ticket,
      password: "replacement-passphrase",
    });
    await route.fulfill({ status: 204 });
  });
  await page.goto(`/#/reset-password/${ticket}`);
  await page.getByLabel("New password").fill("replacement-passphrase");
  await page.getByRole("button", { name: "Update password" }).click();
  await expect(
    page.getByRole("heading", { name: "Password updated" }),
  ).toBeVisible();
  await expect(page).toHaveURL(/#\/password-updated$/);
});

test("enroll and disable an authenticator from account settings", async ({
  page,
}) => {
  await mockGame(page);
  await login(page);
  await page.route("**/api/auth/mfa", (route) =>
    route.fulfill({ json: { available: true, enabled: false } }),
  );
  await page.route("**/api/auth/mfa/start", async (route) => {
    expect(route.request().postDataJSON()).toEqual({
      password: "password-12345",
    });
    await route.fulfill({ json: { secret: "FIXTURE_SETUP_KEY" } });
  });
  await page.route("**/api/auth/mfa/confirm", async (route) => {
    expect(route.request().postDataJSON()).toEqual({ code: "123456" });
    await route.fulfill({ json: { recovery_codes: ["fixture-backup-code"] } });
  });
  await page.route("**/api/auth/mfa/disable", async (route) => {
    expect(route.request().postDataJSON()).toEqual({
      password: "password-12345",
      code: "fixture-backup-code",
    });
    await route.fulfill({ status: 204 });
  });
  await page.goto("/#/security");
  await page.getByLabel("Current password").fill("password-12345");
  await page.getByRole("button", { name: "Set up authenticator" }).click();
  await expect(
    page.getByText("FIXTURE_SETUP_KEY", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Six-digit authenticator code").fill("123456");
  await page.getByRole("button", { name: "Confirm authenticator" }).click();
  await expect(
    page.getByText("fixture-backup-code", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Current password").fill("password-12345");
  await page
    .getByLabel("Authenticator or backup code")
    .fill("fixture-backup-code");
  await page.getByRole("button", { name: "Disable authenticator" }).click();
  await expect(
    page.getByRole("button", { name: "Set up authenticator" }),
  ).toBeVisible();
  await noOverflow(page);
});

test("coding lessons guide, save, unlock and replay", async ({ page }) => {
  await mockGame(page, { coding: true });
  await login(page);
  await page.goto("/#/missions/1");
  const editor = page.getByLabel("Python expression");
  await expect(editor).toHaveValue('decode64("SEVMTE8=")');
  await expect(
    page.getByRole("button", { name: /Coding lesson 2/ }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Run tests" }).click();
  await expect(
    page.getByText("Review the test results and try again."),
  ).toBeVisible();
  const report = page.locator(".code-lesson pre");
  await expect(report).toContainText("<em>fixture output</em>");
  await expect(report.locator("em")).toHaveCount(0);
  await editor.fill("import os");
  await page.getByRole("button", { name: "Run tests" }).click();
  await expect(page.getByText("Blocked by console safety rules")).toBeVisible();
  await expect(report).toContainText("Skipped before evaluation");
  const wallet = page.locator(".lobby-account");
  await expect(
    wallet.getByRole("img", { name: "20 coins", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Buy hint 2 for 5 coins" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Buy hint 1 for 3 coins" }).click();
  await expect(
    wallet.getByRole("img", { name: "17 coins", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Buy hint 2 for 5 coins" }),
  ).toBeEnabled();
  await expect(
    page.getByRole("button", { name: "Buy hint 3 for 8 coins" }),
  ).toBeDisabled();
  await expect(page.getByText("Pass the input variable.")).toBeVisible();
  await editor.fill("decode64(encoded)");
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page.getByText("Draft saved.")).toBeVisible();
  await page.getByRole("link", { name: "Back to mission control" }).click();
  await page.getByRole("link", { name: "Continue operation" }).click();
  await expect(editor).toHaveValue("decode64(encoded)");
  await expect(page.getByText("Pass the input variable.")).toBeVisible();
  await page.getByRole("button", { name: "Submit code" }).click();
  await expect(page.getByText("1 of 2 lessons complete")).toBeVisible();
  await page.getByRole("button", { name: "Replay from starter" }).click();
  await expect(editor).toHaveValue('decode64("SEVMTE8=")');
  await page.getByRole("button", { name: "Next puzzle" }).click();
  await expect(
    page.getByRole("button", { name: "Buy hint 1 for 4 coins" }),
  ).toBeEnabled();
  await editor.fill("decode64(encoded)");
  await page.getByRole("button", { name: "Submit code" }).click();
  await expect(
    page.getByRole("heading", { name: "Mission accomplished." }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Next mission" }),
  ).toHaveAttribute("href", "#/missions/2");
  await expect(
    page.getByText("Your next mission is now unlocked.", { exact: false }),
  ).toBeVisible();
  await expect(
    wallet.getByRole("img", { name: "42 coins", exact: true }),
  ).toBeVisible();
  await noOverflow(page);
});
test("pages, puzzle feedback, completion, rankings and logout", async ({
  page,
}) => {
  await mockGame(page);
  await login(page);
  await noOverflow(page);
  await page.screenshot({
    path: `test-results/dashboard-${page.viewportSize().width}.png`,
    fullPage: true,
  });
  await page.getByRole("link", { name: "Continue operation" }).click();
  await expect(
    page.getByRole("heading", { name: "Puzzle 1", exact: true }),
  ).toBeVisible();
  await noOverflow(page);
  await page.getByLabel("Submit your answer").fill("wrong");
  await page.getByRole("button", { name: "Check answer" }).click();
  await expect(page.getByText("Access denied.")).toBeVisible();
  await page.getByLabel("Submit your answer").fill("ACCESS");
  await page.getByRole("button", { name: "Check answer" }).click();
  await expect(
    page.getByText("✓ Puzzle solved.", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next puzzle" }).click();
  await page.getByLabel("Submit your answer").fill("ACCESS");
  await page.getByRole("button", { name: "Check answer" }).click();
  await expect(
    page.getByRole("heading", { name: "Mission accomplished." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Leaderboard", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Leaderboard." }),
  ).toBeVisible();
  await expect(
    page.getByRole("table").getByRole("img", { name: "25 coins" }),
  ).toBeVisible();
  await noOverflow(page);
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back, agent" }),
  ).toBeVisible();
});
test("registration, locked route, browser back and expired session", async ({
  page,
}) => {
  const game = await mockGame(page);
  await page.goto("/#/register");
  await page.getByLabel("Agent username").fill("test.agent");
  await page.getByLabel("Email address").fill("test@example.com");
  await page.getByLabel("Password", { exact: true }).fill("password-12345");
  await noOverflow(page);
  await page.getByRole("button", { name: "Create account & enter" }).click();
  await expect(
    page.getByRole("heading", { name: "Mission control." }),
  ).toBeVisible();
  await page.goto("/#/missions/3");
  await expect(
    page.getByRole("heading", { name: "Mission unavailable" }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Mission control." }),
  ).toBeVisible();
  game.expire();
  await page.getByRole("link", { name: "Continue operation" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back, agent" }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("session expired");
});
test("offline retry, keyboard access and labels", async ({ page }) => {
  await page.route("**/api/**", (route) => route.abort());
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Connection lost");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  await page.unroute("**/api/**");
  await mockGame(page);
  await page.getByRole("button", { name: "Retry connection" }).click();
  await expect(
    page.getByRole("heading", { name: "The city holds secrets." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Log in", exact: true }).click();
  await expect(page.getByLabel("Agent username")).toBeVisible();
  await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
  await noOverflow(page);
});

test("guest welcome hides missions and rankings, including direct links", async ({
  page,
}) => {
  const privateRequests = [];
  page.on("request", (request) => {
    if (/\/api\/(missions|leaderboard|me)/.test(request.url()))
      privateRequests.push(request.url());
  });
  await mockGame(page);
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "The city holds secrets." }),
  ).toBeVisible();
  await expect(page.locator(".sidebar")).toHaveCount(0);
  await expect(
    page.getByRole("region", { name: "Interactive mission map" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Leaderboard", exact: true }),
  ).toHaveCount(0);
  await noOverflow(page);
  await page.screenshot({
    path: `test-results/welcome-${page.viewportSize().width}.png`,
    fullPage: true,
  });
  for (const route of ["/leaderboard", "/missions/1"]) {
    await page.goto(`/#${route}`);
    await expect(
      page.getByRole("heading", { name: "Welcome back, agent" }),
    ).toBeVisible();
    await expect(page.getByRole("table")).toHaveCount(0);
    await expect(
      page.getByRole("region", { name: "Interactive mission map" }),
    ).toHaveCount(0);
  }
  expect(privateRequests).toEqual([]);
});

test("map selection explains locks and opens available locations", async ({
  page,
}) => {
  await mockGame(page);
  await login(page);
  const map = page.getByRole("region", { name: "Interactive mission map" });
  const detail = page.getByRole("complementary", { name: "Selected location" });
  await expect(map).toBeVisible();
  await map.getByRole("button", { name: "Location 02:" }).click();
  await expect(
    detail.getByRole("heading", { name: "MISSION 2", exact: true }),
  ).toBeVisible();
  await expect(detail).toContainText("Clear location 01");
  await expect(detail.getByRole("link", { name: "Enter mission" })).toHaveCount(
    0,
  );
  await map.getByRole("button", { name: "Location 03:" }).click();
  await expect(detail).toContainText("future chapter");
  const available = map.getByRole("button", { name: "Location 01:" });
  await available.focus();
  await page.keyboard.press("Enter");
  await expect(available).toHaveAttribute("aria-pressed", "true");
  await expect(
    detail.getByRole("heading", { name: "MISSION 1", exact: true }),
  ).toBeVisible();
  await noOverflow(page);
  await page.screenshot({
    path: `test-results/map-${page.viewportSize().width}.png`,
    fullPage: true,
  });
  await detail.getByRole("link", { name: "Enter mission" }).click();
  await expect(
    page.getByRole("heading", { name: "Puzzle 1", exact: true }),
  ).toBeVisible();
});
