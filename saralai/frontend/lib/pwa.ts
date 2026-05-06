/**
 * PWA registration and lifecycle management.
 */

export function registerServiceWorker(): void {
  if (typeof window === "undefined") return;
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", async () => {
    try {
      const registration = await navigator.serviceWorker.register("/sw.js");
      if (process.env.NODE_ENV === "development") {
        console.log("[PWA] Service worker registered:", registration.scope);
      }
    } catch (error) {
      console.error("[PWA] Service worker registration failed:", error);
    }
  });
}

export function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (window.navigator as any).standalone === true
  );
}
