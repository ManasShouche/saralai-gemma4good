const CACHE = "saralai-v1";
const ASSETS = ["/", "/scan", "/speak", "/manifest.json", "/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
});

self.addEventListener("fetch", (e) => {
  // Never cache API calls
  if (e.request.url.includes("/api/")) return;
  e.respondWith(
    caches
      .match(e.request)
      .then((r) => r || fetch(e.request))
      .catch(() => {
        // Offline fallback: return cached root for navigation requests
        if (e.request.mode === "navigate") {
          return caches.match("/");
        }
        return new Response("Offline", { status: 503, statusText: "Service Unavailable" });
      })
  );
});
