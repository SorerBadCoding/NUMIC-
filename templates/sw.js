{% load static %}// NUM Student Portal — service worker.
//
// To ship an update that all installed clients pick up cleanly, bump
// CACHE_VERSION (e.g. "num-cache-v1" -> "num-cache-v2"). The activate handler
// below deletes any cache whose name doesn't match the current version, so
// stale precached assets never linger.
const CACHE_VERSION = "num-cache-v1";

// Matches STATIC_URL's resolved path (numportal/settings.py: STATIC_URL =
// "static/", which Django/WhiteNoise serve from the site root as "/static/").
const STATIC_PREFIX = "/static/";

const OFFLINE_URL = "{% url 'offline' %}";

// Small static app shell only — no HTML pages besides the offline fallback,
// and nothing authenticated or per-user.
const PRECACHE_URLS = [
  "{% static 'css/theme.css' %}",
  "{% static 'css/animations.css' %}",
  "{% static 'js/app.js' %}",
  "{% static 'js/animations.js' %}",
  "{% static 'img/logo.png' %}",
  "{% static 'img/icon-192.png' %}",
  "{% static 'img/icon-512.png' %}",
  OFFLINE_URL,
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_VERSION)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;

  // Non-GET requests — form POSTs, CSRF-protected actions, attendance
  // submissions, gradebook saves, calendar admin actions, login/logout —
  // are never intercepted. Let the browser handle them natively.
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Cross-origin requests (Bootstrap/Google Fonts/GSAP/Maps/FullCalendar
  // CDNs, etc.) are left entirely to the browser's own handling.
  if (url.origin !== self.location.origin) return;

  // Explicit bypass for Django admin, as specified.
  if (url.pathname.startsWith("/admin/")) return;

  // Cache-first for hashed static assets: WhiteNoise's
  // CompressedManifestStaticFilesStorage means the filename itself changes
  // whenever the file's content does, so a cached response for a given
  // hashed URL is always correct — no freshness check ever needed.
  if (url.pathname.startsWith(STATIC_PREFIX)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Network-first for page navigations — the dashboard, calendar, gradebook,
  // attendance pages, login, everything. Always try the network first for
  // correctly-authenticated, current HTML; only fall back to the static
  // offline page if the network is truly unreachable. The navigation
  // response itself is never cached, so nothing authenticated or per-user
  // can ever be served stale or to the wrong person.
  if (request.mode === "navigate") {
    event.respondWith(networkFirstNavigation(request));
    return;
  }

  // Everything else (calendar events.json, attendance qr.json/roster.json,
  // media files, and any other dynamic GET) goes straight to the network,
  // uncached — the default browser fetch applies since we don't call
  // event.respondWith() here.
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(CACHE_VERSION);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    return cached || Response.error();
  }
}

async function networkFirstNavigation(request) {
  try {
    return await fetch(request);
  } catch (err) {
    const offline = await caches.match(OFFLINE_URL);
    return offline || Response.error();
  }
}
