import { getStore } from "@netlify/blobs";

// Private delivery files (full-quality masters customers pay for) live in a
// Netlify Blobs store instead of a public folder. In Netlify Functions this
// authenticates automatically — no siteID/token needed at runtime.
export function masterStore() {
  return getStore({ name: "masters", consistency: "strong" });
}
