/**
 * HookCut YouTube Transcript Worker
 *
 * Fetches YouTube captions from Cloudflare's edge network (CDN IPs),
 * bypassing YouTube's cloud-provider IP blocks.
 *
 * Endpoint: GET /transcript?v={videoId}&lang=en
 * Returns:  { "text": "[0:00.00] line...\n...", "language": "en" }
 *
 * Deploy: wrangler deploy
 * Set secret: wrangler secret put API_KEY
 */

const BROWSER_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    // Auth check (optional — only if API_KEY secret is set)
    if (env.API_KEY) {
      const auth = request.headers.get("Authorization") || "";
      if (auth !== `Bearer ${env.API_KEY}`) {
        return jsonResponse({ error: "Unauthorized" }, 401);
      }
    }

    const url = new URL(request.url);

    if (url.pathname === "/transcript") {
      return handleTranscript(url);
    }

    if (url.pathname === "/health") {
      return jsonResponse({ status: "ok" });
    }

    return jsonResponse({ error: "Not found" }, 404);
  },
};

async function handleTranscript(url) {
  const videoId = url.searchParams.get("v");
  const lang = url.searchParams.get("lang") || "en";

  if (!videoId || !/^[a-zA-Z0-9_-]{11}$/.test(videoId)) {
    return jsonResponse({ error: "Invalid or missing video ID" }, 400);
  }

  try {
    // Step 1: Fetch the YouTube watch page
    const ytResp = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
      headers: {
        "User-Agent": BROWSER_UA,
        "Accept-Language": "en-US,en;q=0.9",
      },
    });

    if (!ytResp.ok) {
      return jsonResponse(
        { error: `YouTube returned ${ytResp.status}` },
        502
      );
    }

    const html = await ytResp.text();

    // Step 2: Extract ytInitialPlayerResponse from page HTML
    const playerMatch = html.match(
      /var\s+ytInitialPlayerResponse\s*=\s*(\{.+?\});/s
    );
    if (!playerMatch) {
      // Fallback: try the embedded JSON format
      const embeddedMatch = html.match(
        /ytInitialPlayerResponse"\s*:\s*(\{.+?\})\s*,\s*"/s
      );
      if (!embeddedMatch) {
        return jsonResponse(
          { error: "Could not extract player response" },
          404
        );
      }
      return processCaptions(JSON.parse(embeddedMatch[1]), lang);
    }

    return processCaptions(JSON.parse(playerMatch[1]), lang);
  } catch (err) {
    return jsonResponse({ error: `Worker error: ${err.message}` }, 500);
  }
}

async function processCaptions(playerResponse, lang) {
  // Step 3: Extract caption tracks
  const captionTracks =
    playerResponse?.captions?.playerCaptionsTracklistRenderer?.captionTracks;

  if (!captionTracks || captionTracks.length === 0) {
    return jsonResponse({ error: "No captions available" }, 404);
  }

  // Step 4: Find best matching track
  const langCodes = expandLangCodes(lang);
  let track = null;

  for (const code of langCodes) {
    track = captionTracks.find(
      (t) => t.languageCode === code || t.languageCode.startsWith(code + "-")
    );
    if (track) break;
  }

  // Fall back to English, then first available
  if (!track) {
    track =
      captionTracks.find((t) => t.languageCode.startsWith("en")) ||
      captionTracks[0];
  }

  if (!track?.baseUrl) {
    return jsonResponse({ error: "No usable caption track found" }, 404);
  }

  // Step 5: Fetch caption content in json3 format
  const captionUrl = track.baseUrl + "&fmt=json3";
  const captionResp = await fetch(captionUrl, {
    headers: { "User-Agent": BROWSER_UA },
  });

  if (!captionResp.ok) {
    return jsonResponse(
      { error: `Caption fetch returned ${captionResp.status}` },
      502
    );
  }

  const captionData = await captionResp.json();

  // Step 6: Parse json3 → timestamped text
  const text = parseJson3(captionData);

  if (!text || text.trim().length < 50) {
    return jsonResponse({ error: "Caption text too short" }, 404);
  }

  return jsonResponse({
    text,
    language: track.languageCode,
    track_name: track.name?.simpleText || "",
  });
}

function parseJson3(data) {
  const lines = [];
  for (const event of data.events || []) {
    const startMs = event.tStartMs || 0;
    const startSec = startMs / 1000;
    const minutes = Math.floor(startSec / 60);
    const seconds = startSec % 60;

    const segs = event.segs || [];
    const text = segs
      .map((s) => s.utf8 || "")
      .join("")
      .trim();

    if (text && text !== "\n") {
      const ts = `[${minutes}:${seconds.toFixed(2).padStart(5, "0")}]`;
      lines.push(`${ts} ${text}`);
    }
  }
  return lines.join("\n");
}

function expandLangCodes(lang) {
  const mapping = {
    en: ["en", "en-US", "en-GB", "en-IN"],
    hi: ["hi", "hi-IN"],
    ta: ["ta", "ta-IN"],
    te: ["te", "te-IN"],
    kn: ["kn", "kn-IN"],
    ml: ["ml", "ml-IN"],
    mr: ["mr", "mr-IN"],
    gu: ["gu", "gu-IN"],
    pa: ["pa", "pa-IN"],
    bn: ["bn", "bn-IN"],
    or: ["or", "or-IN"],
  };
  return mapping[lang] || [lang, "en"];
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(),
    },
  });
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
  };
}
