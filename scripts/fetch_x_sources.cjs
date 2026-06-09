#!/usr/bin/env node
/* Fetch authenticated X bookmarks and top posts for the morning brief.
 *
 * Public sources should still use curl/Python. X needs authenticated browser
 * state, so this launches real Chrome with a temporary copy of the current
 * Chrome profile's cookie files and captures X's own GraphQL responses.
 */

const fs = require("fs");
const os = require("os");
const path = require("path");
const { chromium } = require("playwright");

const DEFAULT_QUERIES = [
  '(AI OR "artificial intelligence" OR LLM OR agents OR "AI agents" OR Claude OR OpenAI) (thread OR "1/" OR "deep dive" OR analysis OR tips OR guide) min_faves:50 -is:retweet',
  '(startup OR startups OR SaaS OR founder OR founders OR "venture capital" OR "go to market" OR GTM) (thread OR "1/" OR lessons OR learnings OR analysis OR guide) min_faves:50 -is:retweet',
  '(AI OR agents OR automation) (business OR SaaS OR startup OR agency OR "service business" OR SMB) (thread OR "1/" OR lessons OR analysis OR playbook) min_faves:50 -is:retweet',
  '("open source" OR OSS OR github) (AI OR agents OR "dev tools" OR infrastructure) (launch OR released OR built OR show) min_faves:50 -is:retweet',
  '(paper OR research OR benchmark OR eval) (LLM OR agents OR "language model" OR transformer) (results OR findings OR "deep dive" OR explained) min_faves:50 -is:retweet',
  '(Claude OR Codex OR Cursor OR Copilot OR "coding agent") (workflow OR setup OR tips OR guide OR lessons) min_faves:50 -is:retweet',
];

const CAPTURED_OPS = new Set(["Bookmarks", "BookmarkSearchTimeline", "SearchTimeline"]);

function parseArgs(argv) {
  const args = {
    bookmarks: 10,
    topPosts: 20,
    lookbackHours: 72,
    profile: "Default",
    chromeUserDataDir: path.join(os.homedir(), "Library/Application Support/Google/Chrome"),
    timeoutMs: 45000,
    settleMs: 3000,
    headless: true,
    keepTemp: false,
    queries: [],
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      i += 1;
      if (i >= argv.length) throw new Error(`Missing value for ${arg}`);
      return argv[i];
    };
    if (arg === "--bookmarks") args.bookmarks = Number(next());
    else if (arg === "--top-posts") args.topPosts = Number(next());
    else if (arg === "--lookback-hours") args.lookbackHours = Number(next());
    else if (arg === "--profile") args.profile = next();
    else if (arg === "--chrome-user-data-dir") args.chromeUserDataDir = next();
    else if (arg === "--timeout-ms") args.timeoutMs = Number(next());
    else if (arg === "--settle-ms") args.settleMs = Number(next());
    else if (arg === "--query") args.queries.push(next());
    else if (arg === "--headed") args.headless = false;
    else if (arg === "--keep-temp") args.keepTemp = true;
    else if (arg === "--help") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!Number.isFinite(args.bookmarks) || args.bookmarks < 1) throw new Error("--bookmarks must be positive");
  if (!Number.isFinite(args.topPosts) || args.topPosts < 1) throw new Error("--top-posts must be positive");
  if (!Number.isFinite(args.lookbackHours) || args.lookbackHours < 1) throw new Error("--lookback-hours must be positive");
  if (!Number.isFinite(args.timeoutMs) || args.timeoutMs < 5000) throw new Error("--timeout-ms must be at least 5000");
  return args;
}

function printHelp() {
  console.log(`Usage: node scripts/fetch_x_sources.js [options]

Options:
  --bookmarks N              Latest bookmarks to return. Default: 10
  --top-posts N              Top X posts to return. Default: 20
  --lookback-hours N         Search lookback window. Default: 72
  --profile NAME             Chrome profile directory. Default: Default
  --chrome-user-data-dir DIR Chrome user data directory
  --query QUERY              Replacement search query. Repeatable
  --headed                   Show the temporary Chrome window
  --timeout-ms N             Navigation/capture timeout. Default: 45000
  --keep-temp                Keep the temporary profile for debugging`);
}

function copyIfExists(src, dst) {
  if (!fs.existsSync(src)) return false;
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
  return true;
}

function prepareTemporaryChromeProfile(args) {
  const sourceRoot = path.resolve(args.chromeUserDataDir);
  const sourceProfile = path.join(sourceRoot, args.profile);
  const cookiesPath = path.join(sourceProfile, "Cookies");
  if (!fs.existsSync(sourceRoot)) throw new Error(`Chrome user data directory not found: ${sourceRoot}`);
  if (!fs.existsSync(sourceProfile)) throw new Error(`Chrome profile not found: ${sourceProfile}`);
  if (!fs.existsSync(cookiesPath)) throw new Error(`Chrome Cookies database not found: ${cookiesPath}`);

  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "morning-brief-x-profile-"));
  const tempProfile = path.join(tempRoot, args.profile);
  fs.mkdirSync(tempProfile, { recursive: true });

  const required = [
    ["Local State", "Local State"],
    [path.join(args.profile, "Cookies"), path.join(args.profile, "Cookies")],
  ];
  for (const [srcRel, dstRel] of required) {
    const copied = copyIfExists(path.join(sourceRoot, srcRel), path.join(tempRoot, dstRel));
    if (!copied) throw new Error(`Required Chrome profile file missing: ${path.join(sourceRoot, srcRel)}`);
  }

  const optional = [
    [path.join(args.profile, "Cookies-wal"), path.join(args.profile, "Cookies-wal")],
    [path.join(args.profile, "Cookies-shm"), path.join(args.profile, "Cookies-shm")],
    [path.join(args.profile, "Preferences"), path.join(args.profile, "Preferences")],
  ];
  for (const [srcRel, dstRel] of optional) {
    copyIfExists(path.join(sourceRoot, srcRel), path.join(tempRoot, dstRel));
  }

  return { tempRoot, sourceRoot, sourceProfile };
}

async function launchContext(tempRoot, args) {
  return chromium.launchPersistentContext(tempRoot, {
    channel: "chrome",
    headless: args.headless,
    viewport: { width: 1280, height: 900 },
    args: [`--profile-directory=${args.profile}`],
    ignoreDefaultArgs: ["--use-mock-keychain", "--password-store=basic"],
  });
}

function captureGraphqlResponses(page, captures) {
  page.on("response", async (response) => {
    const match = /\/graphql\/([^/]+)\/([^?]+)/.exec(response.url());
    if (!match) return;
    const queryId = match[1];
    const op = decodeURIComponent(match[2]);
    if (!CAPTURED_OPS.has(op)) return;

    const capture = {
      op,
      queryId,
      status: response.status(),
      rawQuery: rawQueryFromUrl(response.url()),
      receivedAt: new Date().toISOString(),
      tweets: [],
      errors: [],
    };
    try {
      const json = await response.json();
      capture.tweets = extractTweets(json);
      capture.errors = extractErrors(json);
    } catch (error) {
      capture.errors = [`Could not parse JSON response: ${error.message}`];
    }
    captures.push(capture);
  });
}

function rawQueryFromUrl(url) {
  try {
    const parsed = new URL(url);
    const variables = JSON.parse(parsed.searchParams.get("variables") || "{}");
    return variables.rawQuery || "";
  } catch {
    return "";
  }
}

function extractErrors(json) {
  if (!json || !Array.isArray(json.errors)) return [];
  return json.errors.map((error) => error.message || JSON.stringify(error)).filter(Boolean);
}

async function waitForCapture(captures, startIndex, predicate, timeoutMs) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    for (let i = startIndex; i < captures.length; i += 1) {
      if (predicate(captures[i])) return captures[i];
    }
    await delay(250);
  }
  return null;
}

async function loadBookmarks(page, captures, args) {
  const startIndex = captures.length;
  await page.goto("https://x.com/i/bookmarks", { waitUntil: "domcontentloaded", timeout: args.timeoutMs });
  await waitForCapture(
    captures,
    startIndex,
    (capture) => ["Bookmarks", "BookmarkSearchTimeline"].includes(capture.op),
    args.timeoutMs,
  );
  await page.waitForTimeout(args.settleMs);

  if (countTweets(captures, ["Bookmarks", "BookmarkSearchTimeline"], startIndex) < args.bookmarks) {
    await page.mouse.wheel(0, 2200);
    await page.waitForTimeout(args.settleMs);
  }

  return collectTweets(captures, ["Bookmarks", "BookmarkSearchTimeline"], startIndex).slice(0, args.bookmarks);
}

async function loadSearches(page, captures, args) {
  const cutoffMs = Date.now() - args.lookbackHours * 60 * 60 * 1000;
  const sinceTime = Math.floor(cutoffMs / 1000);
  const queries = args.queries.length > 0 ? args.queries : DEFAULT_QUERIES;
  const allTweets = new Map();
  const attempts = [];

  for (const baseQuery of queries) {
    const query = `${baseQuery} since_time:${sinceTime}`;
    const startIndex = captures.length;
    const url = `https://x.com/search?q=${encodeURIComponent(query)}&src=typed_query&f=top`;
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: args.timeoutMs });
    await waitForCapture(
      captures,
      startIndex,
      (capture) => capture.op === "SearchTimeline",
      args.timeoutMs,
    );
    await page.waitForTimeout(args.settleMs);
    await page.mouse.wheel(0, 2000);
    await page.waitForTimeout(Math.min(args.settleMs, 2500));

    const tweets = collectTweets(captures, ["SearchTimeline"], startIndex);
    attempts.push({ query, tweets: tweets.length });
    for (const tweet of tweets) {
      if (!isUsefulTopPost(tweet)) continue;
      const createdMs = Date.parse(tweet.created_at || "");
      if (Number.isFinite(createdMs) && createdMs < cutoffMs) continue;
      const existing = allTweets.get(tweet.id);
      const tagged = { ...tweet, matched_query: query };
      if (!existing || tweetScore(tagged) > tweetScore(existing)) allTweets.set(tweet.id, tagged);
    }
  }

  const ranked = [...allTweets.values()].sort((a, b) => tweetScore(b) - tweetScore(a));
  return { posts: ranked.slice(0, args.topPosts), attempts, cutoffUtc: new Date(cutoffMs).toISOString() };
}

function countTweets(captures, ops, startIndex) {
  return collectTweets(captures, ops, startIndex).length;
}

function collectTweets(captures, ops, startIndex) {
  const opSet = new Set(ops);
  const byId = new Map();
  for (let i = startIndex; i < captures.length; i += 1) {
    const capture = captures[i];
    if (!opSet.has(capture.op) || capture.status !== 200) continue;
    for (const tweet of capture.tweets) {
      if (!byId.has(tweet.id)) byId.set(tweet.id, tweet);
    }
  }
  return [...byId.values()];
}

function extractTweets(json) {
  const tweets = [];
  const seen = new Set();

  function walk(node) {
    if (!node) return;
    if (Array.isArray(node)) {
      for (const value of node) walk(value);
      return;
    }
    if (typeof node !== "object") return;

    const tweet = unwrapTweet(node);
    if (tweet) {
      const parsed = parseTweet(tweet);
      if (parsed && !seen.has(parsed.id)) {
        seen.add(parsed.id);
        tweets.push(parsed);
      }
    }

    for (const value of Object.values(node)) walk(value);
  }

  walk(json);
  return tweets;
}

function unwrapTweet(node) {
  if (!node || typeof node !== "object") return null;
  if (node.__typename === "Tweet" && node.rest_id) return node;
  if (node.__typename === "TweetWithVisibilityResults" && node.tweet) return unwrapTweet(node.tweet);
  if (node.tweet_results && node.tweet_results.result) return unwrapTweet(node.tweet_results.result);
  if (node.tweet) return unwrapTweet(node.tweet);
  if (node.result) return unwrapTweet(node.result);
  return null;
}

function parseTweet(tweet) {
  const legacy = tweet.legacy || {};
  const id = String(tweet.rest_id || legacy.id_str || "");
  const text = normalizeText(tweetText(tweet, legacy));
  if (!id || !text) return null;

  const user = parseUser(tweet);
  const screenName = user.screen_name || "i";
  const url = screenName === "i" ? `https://x.com/i/web/status/${id}` : `https://x.com/${screenName}/status/${id}`;
  const item = {
    id,
    url,
    text,
    created_at: legacy.created_at || "",
    author_name: user.name || "",
    author_screen_name: user.screen_name || "",
    favorite_count: Number(legacy.favorite_count || 0),
    retweet_count: Number(legacy.retweet_count || 0),
    reply_count: Number(legacy.reply_count || 0),
    quote_count: Number(legacy.quote_count || 0),
    bookmark_count: Number(legacy.bookmark_count || 0),
  };
  item.score = tweetScore(item);
  return item;
}

function tweetText(tweet, legacy) {
  const noteResult = tweet.note_tweet?.note_tweet_results?.result;
  if (noteResult?.text) return noteResult.text;
  return legacy.full_text || legacy.text || "";
}

function parseUser(tweet) {
  let result = tweet.core?.user_results?.result || {};
  if (result.result) result = result.result;
  const core = result.core || {};
  const legacy = result.legacy || {};
  return {
    name: core.name || legacy.name || "",
    screen_name: core.screen_name || legacy.screen_name || "",
  };
}

function normalizeText(text) {
  return String(text || "").replace(/\s+/g, " ").trim();
}

function isUsefulTopPost(tweet) {
  const text = stripUrls(tweet.text || "");
  if (text.length < 80) return false;
  const lower = text.toLowerCase();
  if (/\b(escort|escorts|monogamous|sex drive)\b/.test(lower)) return false;
  const hasTopic =
    /\b(ai|llm|agent|agents|claude|openai|model|models|automation|startup|startups|saas|gtm|business|company|companies|agency|ecom|founder|founders|venture|smb)\b/.test(lower) ||
    lower.includes("artificial intelligence") ||
    lower.includes("go to market") ||
    lower.includes("small biz") ||
    lower.includes("small business");
  const hasUsefulShape =
    /\b(thread|lessons?|learnings?|analysis|guide|playbook|deep dive|tips?|why|how|introducing|meet|recap|manifesto)\b/.test(lower) ||
    lower.includes("1/") ||
    text.length >= 220;
  return hasTopic && hasUsefulShape;
}

function stripUrls(text) {
  return String(text || "").replace(/https?:\/\/\S+/g, "").replace(/\s+/g, " ").trim();
}

function tweetScore(tweet) {
  return (
    Number(tweet.favorite_count || 0) +
    2 * Number(tweet.retweet_count || 0) +
    2 * Number(tweet.quote_count || 0) +
    Number(tweet.reply_count || 0) +
    Number(tweet.bookmark_count || 0)
  );
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function run() {
  const args = parseArgs(process.argv.slice(2));
  const { tempRoot, sourceRoot, sourceProfile } = prepareTemporaryChromeProfile(args);
  const captures = [];
  let context;
  try {
    context = await launchContext(tempRoot, args);
    const page = await context.newPage();
    captureGraphqlResponses(page, captures);

    const bookmarks = await loadBookmarks(page, captures, args);
    const { posts, attempts, cutoffUtc } = await loadSearches(page, captures, args);
    const operations = {};
    for (const capture of captures) operations[capture.op] = capture.queryId;

    console.log(JSON.stringify({
      generated_at: new Date().toISOString(),
      access: {
        method: "playwright-temporary-chrome-profile",
        chrome_profile: args.profile,
        source_profile: sourceProfile,
        chrome_user_data_dir: sourceRoot,
        operation_ids: operations,
      },
      x_bookmarks: bookmarks,
      top_x_posts: posts,
      meta: {
        lookback_hours: args.lookbackHours,
        top_posts_cutoff_utc: cutoffUtc,
        search_attempts: attempts,
        capture_count: captures.length,
        capture_summary: captures.map((capture) => ({
          op: capture.op,
          status: capture.status,
          queryId: capture.queryId,
          rawQuery: capture.rawQuery,
          tweets: capture.tweets.length,
          errors: capture.errors,
        })),
      },
    }, null, 2));
  } finally {
    if (context) await context.close().catch(() => {});
    if (!args.keepTemp) fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

run().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});
