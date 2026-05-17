"use client";

import { useEffect } from "react";

function ship(level: string, message: string, stack?: string) {
  fetch("/api/debug/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      level,
      source: "client",
      message,
      stack: stack ?? "",
      url: typeof window !== "undefined" ? window.location.pathname : "",
    }),
  }).catch(() => {});
}

export default function DevLogger() {
  useEffect(() => {
    const origError = console.error.bind(console);
    console.error = (...args: unknown[]) => {
      origError(...args);
      const message = args.map((a) => (typeof a === "string" ? a : JSON.stringify(a))).join(" ");
      const stack = args.find((a) => a instanceof Error) instanceof Error
        ? (args.find((a) => a instanceof Error) as Error).stack
        : undefined;
      ship("error", message, stack);
    };

    const onError = (e: ErrorEvent) => {
      ship("error", e.message, e.error?.stack);
    };

    const onUnhandled = (e: PromiseRejectionEvent) => {
      const reason = e.reason;
      ship(
        "error",
        reason instanceof Error ? reason.message : String(reason),
        reason instanceof Error ? reason.stack : undefined
      );
    };

    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onUnhandled);

    return () => {
      console.error = origError;
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onUnhandled);
    };
  }, []);

  return null;
}
