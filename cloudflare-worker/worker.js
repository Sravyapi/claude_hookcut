/**
 * HookCut YouTube Transcript Worker
 *
 * Fetches YouTube captions from Cloudflare's edge network (CDN IPs),
 * bypassing YouTube's cloud-provider IP blocks.
 *
 * Strategy (in order):
 *   1. Scrape watch page HTML → extract ytInitialPlayerResponse → get caption URLs
 *   2. Innertube get_transcript API
 *   3. Player API (WEB client)
 *   4. Player API (ANDROID client)
 *
 * Endpoint: GET /transcript?v={videoId}&lang=en
 * Returns:  { "text": "[0:00.00] line...\n...", "language": "en" }
 */

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";
const CONSENT_COOKIE = "CONSENT=YES+cb.20210328-17-p0.en+FX+435; SOCS=CAESEwgDEgk2NDcwNTI0NjAaAmVuIAEaBgiA_LyaBg";

export default {
  async fetch(request, env) {
    if (!env.API_KEY) {
      return new Response(JSON.stringify({ error: "Worker not configured" }), { status: 503, headers: { "Content-Type": "application/json" } });
    }

    const requestOrigin = request.headers.get("Origin");
    const allowedOrigin = getAllowedOrigin(requestOrigin);

    if (request.method === "OPTIONS") {
      if (!allowedOrigin) return new Response(null, { status: 403 });
      return new Response(null, { status: 204, headers: corsHeaders(allowedOrigin) });
    }

    if (!allowedOrigin) {
      return jsonResp({ error: "Forbidden" }, 403, allowedOrigin);
    }

    const auth = request.headers.get("Authorization") || "";
    if (auth !== `Bearer ${env.API_KEY}`) {
      return jsonResp({ error: "Unauthorized" }, 401, allowedOrigin);
    }

    const url = new URL(request.url);
    if (url.pathname === "/transcript") return handleTranscript(url, env, allowedOrigin);
    if (url.pathname === "/proxy-caption") return handleProxyCaption(url, allowedOrigin);
    if (url.pathname === "/health") return jsonResp({ status: "ok" }, 200, allowedOrigin);
    return jsonResp({ error: "Not found" }, 404, allowedOrigin);
  },
};

// ─── Main handler ───────────────────────────────────────────────────────────

async function handleTranscript(url, env, allowedOrigin) {
  const videoId = url.searchParams.get("v");
  const lang = url.searchParams.get("lang") || "en";

  if (!videoId || !/^[a-zA-Z0-9_-]{11}$/.test(videoId)) {
    return jsonResp({ error: "Invalid or missing video ID" }, 400, allowedOrigin);
  }

  const errors = [];

  const apiKey = env.YOUTUBE_DATA_API_KEY || "";

  // Strategy 1: ANDROID player API with YouTube Data API key (most reliable)
  if (apiKey) {
    try {
      const result = await fetchViaPlayerAPI(videoId, lang, "ANDROID", apiKey);
      if (result) {
        return jsonResp({ text: result.text, language: result.language, track_name: result.trackName || "", method: "android_apikey" }, 200, allowedOrigin);
      }
      errors.push("android_apikey: no result");
    } catch (e) {
      errors.push(`android_apikey: ${e.message}`);
    }
  }

  // Strategy 2: Scrape watch page (mimics a real browser visit)
  try {
    const result = await fetchViaWatchPage(videoId, lang);
    if (result) {
      return jsonResp({ text: result.text, language: result.language, track_name: result.trackName || "", method: "watch_page" }, 200, allowedOrigin);
    }
    errors.push("watch_page: no result");
  } catch (e) {
    errors.push(`watch_page: ${e.message}`);
  }

  // Strategy 3: Innertube get_transcript API
  try {
    const text = await fetchViaInnertube(videoId, lang);
    if (text) {
      return jsonResp({ text, language: lang, track_name: "", method: "innertube" }, 200, allowedOrigin);
    }
    errors.push("innertube: no result");
  } catch (e) {
    errors.push(`innertube: ${e.message}`);
  }

  // Strategy 4: Player API (ANDROID without API key)
  try {
    const result = await fetchViaPlayerAPI(videoId, lang, "ANDROID", null);
    if (result) {
      return jsonResp({ text: result.text, language: result.language, track_name: result.trackName || "", method: "player_android" }, 200, allowedOrigin);
    }
    errors.push("player_android: no result");
  } catch (e) {
    errors.push(`player_android: ${e.message}`);
  }

  // Strategy 5: Player API (WEB client)
  try {
    const result = await fetchViaPlayerAPI(videoId, lang, "WEB", apiKey || null);
    if (result) {
      return jsonResp({ text: result.text, language: result.language, track_name: result.trackName || "", method: "player_web" }, 200, allowedOrigin);
    }
    errors.push("player_web: no result");
  } catch (e) {
    errors.push(`player_web: ${e.message}`);
  }

  return jsonResp({ error: "All transcript methods failed", details: errors }, 404, allowedOrigin);
}

// ─── Caption URL proxy ──────────────────────────────────────────────────────

async function handleProxyCaption(url, allowedOrigin) {
  const captionUrl = url.searchParams.get("url");
  if (!captionUrl || !captionUrl.includes("youtube.com/api/timedtext")) {
    return jsonResp({ error: "Invalid caption URL" }, 400, allowedOrigin);
  }

  try {
    const resp = await fetch(captionUrl, {
      headers: {
        "User-Agent": UA,
        "Referer": "https://www.youtube.com/",
      },
    });

    if (!resp.ok) {
      return jsonResp({ error: `Caption fetch failed: ${resp.status}` }, resp.status, allowedOrigin);
    }

    // Pass through the raw response
    const body = await resp.text();
    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        ...corsHeaders(allowedOrigin),
      },
    });
  } catch (e) {
    return jsonResp({ error: `Proxy error: ${e.message}` }, 500, allowedOrigin);
  }
}

// ─── Strategy 1: Watch page scraping ────────────────────────────────────────

async function fetchViaWatchPage(videoId, lang) {
  // Fetch the YouTube watch page like a regular browser
  const watchUrl = `https://www.youtube.com/watch?v=${videoId}&hl=en`;
  const resp = await fetch(watchUrl, {
    headers: {
      "User-Agent": UA,
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.5",
      "Cookie": CONSENT_COOKIE,
    },
    redirect: "follow",
  });

  if (!resp.ok) throw new Error(`Watch page returned ${resp.status}`);
  const html = await resp.text();

  // Find ytInitialPlayerResponse and extract JSON via brace counting (regex is too slow on 1MB+ HTML)
  const marker = "ytInitialPlayerResponse";
  const idx = html.indexOf(marker);
  if (idx === -1) throw new Error("ytInitialPlayerResponse not found in page");

  // Find the opening brace after the marker
  const braceStart = html.indexOf("{", idx + marker.length);
  if (braceStart === -1) throw new Error("No opening brace after ytInitialPlayerResponse");

  // Count braces to find the matching close
  let depth = 0;
  let end = -1;
  for (let i = braceStart; i < html.length; i++) {
    if (html[i] === "{") depth++;
    else if (html[i] === "}") depth--;
    if (depth === 0) { end = i + 1; break; }
  }
  if (end === -1) throw new Error("Could not find matching closing brace");

  const jsonStr = html.substring(braceStart, end);
  return extractCaptionsFromPlayerResponse(jsonStr, lang);
}

function extractCaptionsFromPlayerResponse(jsonStr, lang) {
  let data;
  try {
    data = JSON.parse(jsonStr);
  } catch (e) {
    throw new Error(`JSON parse failed: ${e.message.substring(0, 100)}`);
  }

  const playStatus = data?.playabilityStatus?.status;
  if (playStatus && playStatus !== "OK") {
    const reason = data?.playabilityStatus?.reason || "unknown";
    throw new Error(`Video status: ${playStatus} — ${reason}`);
  }

  const tracks = data?.captions?.playerCaptionsTracklistRenderer?.captionTracks;
  if (!tracks || tracks.length === 0) {
    throw new Error("No caption tracks in player response");
  }

  return fetchCaptionTrack(tracks, lang);
}

// ─── Strategy 2: Innertube get_transcript ───────────────────────────────────

async function fetchViaInnertube(videoId, langCode) {
  const payload = {
    context: {
      client: {
        clientName: "WEB",
        clientVersion: "2.20240313.05.00",
        hl: langCode || "en",
      },
    },
    params: btoa(`\n\x0b${videoId}`),
  };

  const resp = await fetch(
    "https://www.youtube.com/youtubei/v1/get_transcript?prettyPrint=false",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": UA,
        "Referer": "https://www.youtube.com/",
        "Cookie": CONSENT_COOKIE,
      },
      body: JSON.stringify(payload),
    }
  );

  if (!resp.ok) return null;
  const data = await resp.json();

  const actions = data?.actions;
  if (!actions?.length) return null;

  // Try multiple response paths (YouTube changes these periodically)
  const paths = [
    actions[0]?.updateEngagementPanelAction?.content?.transcriptRenderer?.content?.transcriptSearchPanelRenderer?.body?.transcriptSegmentListRenderer,
    actions[0]?.updateEngagementPanelAction?.content?.transcriptRenderer?.body?.transcriptBodyRenderer?.transcriptSegmentListRenderer,
  ];

  for (const renderer of paths) {
    const text = parseInnertubeSegments(renderer);
    if (text) return text;
  }
  return null;
}

function parseInnertubeSegments(renderer) {
  if (!renderer?.initialSegments?.length) return null;
  const lines = [];
  for (const seg of renderer.initialSegments) {
    const segment = seg.transcriptSegmentRenderer;
    if (!segment) continue;
    const startMs = parseInt(segment.startMs || "0", 10);
    const sec = startMs / 1000;
    const min = Math.floor(sec / 60);
    const s = sec % 60;
    const text = segment.snippet?.runs?.map(r => r.text || "").join("").trim();
    if (text && text !== "\n") {
      lines.push(`[${min}:${s.toFixed(2).padStart(5, "0")}] ${text}`);
    }
  }
  const result = lines.join("\n");
  return result.trim().length >= 50 ? result : null;
}

// ─── Strategy 3 & 4: Player API ─────────────────────────────────────────────

async function fetchViaPlayerAPI(videoId, lang, clientType, apiKey) {
  const isAndroid = clientType === "ANDROID";
  const headers = isAndroid
    ? {
        "Content-Type": "application/json",
        "User-Agent": "com.google.android.youtube/20.10.38 (Linux; U; Android 10; en_US)",
        "X-Goog-Api-Format-Version": "2",
      }
    : {
        "Content-Type": "application/json",
        "User-Agent": UA,
        "Referer": "https://www.youtube.com/",
        "Cookie": CONSENT_COOKIE,
      };

  const client = isAndroid
    ? { clientName: "ANDROID", clientVersion: "20.10.38", hl: "en" }
    : { clientName: "WEB", clientVersion: "2.20240313.05.00", hl: "en" };

  // Use YouTube Data API key if available — adds legitimacy to the request
  const playerUrl = apiKey
    ? `https://www.youtube.com/youtubei/v1/player?key=${apiKey}`
    : "https://www.youtube.com/youtubei/v1/player";

  const resp = await fetch(playerUrl, {
    method: "POST",
    headers,
    body: JSON.stringify({ context: { client }, videoId }),
  });

  if (!resp.ok) return null;
  const data = await resp.json();

  if (data?.playabilityStatus?.status !== "OK") return null;

  const tracks = data?.captions?.playerCaptionsTracklistRenderer?.captionTracks;
  if (!tracks || tracks.length === 0) return null;

  return fetchCaptionTrack(tracks, lang);
}

// ─── Shared: fetch a caption track ──────────────────────────────────────────

async function fetchCaptionTrack(tracks, lang) {
  const langCodes = expandLangCodes(lang);
  let track = null;
  for (const code of langCodes) {
    track = tracks.find(t => t.languageCode === code || t.languageCode.startsWith(code + "-"));
    if (track) break;
  }
  if (!track) {
    track = tracks.find(t => t.languageCode.startsWith("en")) || tracks[0];
  }
  if (!track?.baseUrl) return null;

  let fetchUrl = track.baseUrl;
  fetchUrl = fetchUrl.replace("&fmt=srv3", "");
  fetchUrl += fetchUrl.includes("?") ? "&fmt=json3" : "?fmt=json3";

  const text = await fetchJson3(fetchUrl);
  if (!text) return null;

  return { text, language: track.languageCode, trackName: track?.name?.runs?.[0]?.text || "" };
}

async function fetchJson3(url) {
  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": UA, "Referer": "https://www.youtube.com/", "Cookie": CONSENT_COOKIE },
    });
    if (!resp.ok) return null;
    const body = await resp.text();
    if (!body || body.length < 10) return null;
    const data = JSON.parse(body);
    return parseJson3(data);
  } catch {
    return null;
  }
}

function parseJson3(data) {
  const lines = [];
  for (const event of data.events || []) {
    const startMs = event.tStartMs || 0;
    const sec = startMs / 1000;
    const min = Math.floor(sec / 60);
    const s = sec % 60;
    const segs = event.segs || [];
    const text = segs.map(s => s.utf8 || "").join("").trim();
    if (text && text !== "\n") {
      lines.push(`[${min}:${s.toFixed(2).padStart(5, "0")}] ${text}`);
    }
  }
  const result = lines.join("\n");
  return result.trim().length >= 50 ? result : null;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function expandLangCodes(lang) {
  const mapping = {
    en: ["en", "en-US", "en-GB", "en-IN"],
    hi: ["hi", "hi-IN"], ta: ["ta", "ta-IN"], te: ["te", "te-IN"],
    kn: ["kn", "kn-IN"], ml: ["ml", "ml-IN"], mr: ["mr", "mr-IN"],
    gu: ["gu", "gu-IN"], pa: ["pa", "pa-IN"], bn: ["bn", "bn-IN"],
    or: ["or", "or-IN"],
  };
  return mapping[lang] || [lang, "en"];
}

function getAllowedOrigin(requestOrigin) {
  if (!requestOrigin) return "https://api.hookcut.nyxpath.com";
  const allowed = ["https://api.hookcut.nyxpath.com", "https://hookcut.nyxpath.com", "http://localhost:8000", "http://localhost:3000"];
  return allowed.includes(requestOrigin) ? requestOrigin : null;
}

function jsonResp(data, status = 200, allowedOrigin) {
  return new Response(JSON.stringify(data), {
    status, headers: { "Content-Type": "application/json", ...corsHeaders(allowedOrigin) },
  });
}

function corsHeaders(allowedOrigin) {
  return {
    "Access-Control-Allow-Origin": allowedOrigin,
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
  };
}
