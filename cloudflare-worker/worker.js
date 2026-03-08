/**
 * HookCut YouTube Transcript Worker
 *
 * Fetches YouTube captions from Cloudflare's edge network (CDN IPs),
 * bypassing YouTube's cloud-provider IP blocks.
 *
 * Endpoint: GET /transcript?v={videoId}&lang=en
 * Returns:  { "text": "[0:00.00] line...\n...", "language": "en" }
 */

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";
const CONSENT_COOKIE = "CONSENT=PENDING+987; SOCS=CAESEwgDEgk2NDcwNTI0NjAaAmVuIAEaBgiA_LyaBg";

// Required secrets — set via: wrangler secret put API_KEY / wrangler secret put INNERTUBE_API_KEY
export default {
  async fetch(request, env) {
    // Fail fast if required secrets are not configured
    if (!env.API_KEY) {
      return new Response(JSON.stringify({ error: "Worker not configured" }), { status: 503, headers: { "Content-Type": "application/json" } });
    }
    if (!env.INNERTUBE_API_KEY) {
      return new Response(JSON.stringify({ error: "Worker not configured" }), { status: 503, headers: { "Content-Type": "application/json" } });
    }

    const requestOrigin = request.headers.get("Origin");
    const allowedOrigin = getAllowedOrigin(requestOrigin);

    if (request.method === "OPTIONS") {
      if (!allowedOrigin) return new Response(null, { status: 403 });
      return new Response(null, { status: 204, headers: corsHeaders(allowedOrigin) });
    }

    if (!allowedOrigin) {
      return new Response(JSON.stringify({ error: "Forbidden" }), { status: 403, headers: { "Content-Type": "application/json" } });
    }

    // Authentication is mandatory — API_KEY must always be deployed
    const auth = request.headers.get("Authorization") || "";
    if (auth !== `Bearer ${env.API_KEY}`) {
      return jsonWithOrigin({ error: "Unauthorized" }, 401, allowedOrigin);
    }

    const url = new URL(request.url);
    if (url.pathname === "/transcript") return handleTranscript(url, env, allowedOrigin);
    if (url.pathname === "/health") return jsonWithOrigin({ status: "ok" }, 200, allowedOrigin);
    return jsonWithOrigin({ error: "Not found" }, 404, allowedOrigin);
  },
};

async function handleTranscript(url, env, allowedOrigin) {
  const videoId = url.searchParams.get("v");
  const lang = url.searchParams.get("lang") || "en";

  if (!videoId || !/^[a-zA-Z0-9_-]{11}$/.test(videoId)) {
    return jsonWithOrigin({ error: "Invalid or missing video ID" }, 400, allowedOrigin);
  }

  try {
    // Stage 1: Get caption tracks via YouTube Player API (Android Client)
    const playerResp = await fetch(
      `https://www.youtube.com/youtubei/v1/player?key=${env.INNERTUBE_API_KEY}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "User-Agent": "com.google.android.youtube/20.10.38 (Linux; U; Android 10; en_US)",
          "X-Goog-Api-Format-Version": "2",
        },
        body: JSON.stringify({
          context: {
            client: {
              clientName: "ANDROID",
              clientVersion: "20.10.38",
              hl: "en",
            },
          },
          videoId: videoId,
        }),
      }
    );

    if (!playerResp.ok) {
      // Player API failed — fall back to Innertube get_transcript API
      const innertubeText = await fetchViaInnertube(videoId, lang);
      if (innertubeText) {
        return jsonWithOrigin({ text: innertubeText, language: lang, track_name: "" }, 200, allowedOrigin);
      }
      return jsonWithOrigin({ error: `Player API returned ${playerResp.status}` }, 502, allowedOrigin);
    }

    const data = await playerResp.json();

    // Check playability
    const playStatus = data?.playabilityStatus?.status;
    if (playStatus !== "OK") {
      return jsonWithOrigin({ error: `Video unplayable: ${playStatus}` }, 404, allowedOrigin);
    }

    // Extract caption tracks
    const tracks = data?.captions?.playerCaptionsTracklistRenderer?.captionTracks;
    if (!tracks || tracks.length === 0) {
      return jsonWithOrigin({ error: "No captions available" }, 404, allowedOrigin);
    }

    // Find best language match
    const langCodes = expandLangCodes(lang);
    let track = null;
    for (const code of langCodes) {
      track = tracks.find(t => t.languageCode === code || t.languageCode.startsWith(code + "-"));
      if (track) break;
    }
    if (!track) {
      track = tracks.find(t => t.languageCode.startsWith("en")) || tracks[0];
    }
    if (!track?.baseUrl) {
      return jsonWithOrigin({ error: "No usable caption track" }, 404, allowedOrigin);
    }

    // Stage 2: Fetch the actual caption content
    // The player API returns baseUrl params which are properly signed and IP-agnostic.
    let fetchUrl = track.baseUrl;
    fetchUrl = fetchUrl.replace("&fmt=srv3", ""); // Remove default formatting if present
    fetchUrl += fetchUrl.includes("?") ? "&fmt=json3" : "?fmt=json3";

    let text = await fetchJson3(fetchUrl);
    if (!text) {
      // Stage 2 fetch failed — fall back to Innertube get_transcript API
      text = await fetchViaInnertube(videoId, track.languageCode || lang);
    }
    if (!text) {
      return jsonWithOrigin({ error: "Caption content unavailable / could not fetch" }, 404, allowedOrigin);
    }

    return jsonWithOrigin({
      text,
      language: track.languageCode,
      track_name: track?.name?.runs?.[0]?.text || "",
    }, 200, allowedOrigin);
  } catch (err) {
    return jsonWithOrigin({ error: `Worker error: ${err.message}` }, 500, allowedOrigin);
  }
}

async function fetchViaInnertube(videoId, langCode) {
  // YouTube innertube API — same API that youtube-transcript-api uses internally.
  // Does not use IP-signed URLs, so works from any edge node.
  try {
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

    // Navigate innertube response structure
    const actions = data?.actions;
    if (!actions?.length) return null;

    const renderer = actions[0]?.updateEngagementPanelAction
      ?.content?.transcriptRenderer
      ?.content?.transcriptSearchPanelRenderer
      ?.body?.transcriptSegmentListRenderer;

    if (!renderer) {
      // Try alternate path
      const altRenderer = actions[0]?.updateEngagementPanelAction
        ?.content?.transcriptRenderer
        ?.body?.transcriptBodyRenderer;
      if (altRenderer) {
        return parseInnertubeSegments(altRenderer.transcriptSegmentListRenderer);
      }
      return null;
    }

    return parseInnertubeSegments(renderer);
  } catch {
    return null;
  }
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
  const allowed = ["https://api.hookcut.nyxpath.com", "https://hookcut.nyxpath.com"];
  return allowed.includes(requestOrigin) ? requestOrigin : null;
}

function jsonWithOrigin(data, status = 200, allowedOrigin) {
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
