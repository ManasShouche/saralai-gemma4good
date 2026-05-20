const CACHE = "saralai-v2";
const STATIC_ASSETS = ["/manifest.json", "/icon-192.png", "/icon-512.png"];

self.addEventListener("install", (e) => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(STATIC_ASSETS.filter(Boolean)))
  );
});

self.addEventListener("activate", (e) => {
  // Delete old cache versions so stale HTML never serves wrong chunk URLs
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);

  // Never intercept API calls or Chrome DevTools probes
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/.well-known/")) {
    return;
  }

  // Never cache Next.js chunk files — they change on every recompile
  if (url.pathname.startsWith("/_next/")) {
    return;
  }

  // HTML navigation: network-first so new builds are always loaded fresh
  if (e.request.mode === "navigate") {
    e.respondWith(
      fetch(e.request).catch(() => caches.match("/") || caches.match(e.request))
    );
    return;
  }

  // Static assets (icons, manifest): cache-first
  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request))
  );
});
