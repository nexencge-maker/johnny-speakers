// Server-only helpers shared by API routes. No Cloudflare bindings and no
// "sign in with ChatGPT" identity here — this is a plain public site.

export const runtime = () =>
  process.env as NodeJS.ProcessEnv & {
    STRIPE_SECRET_KEY?: string;
    SITE_URL?: string;
  };

export function textValue(x: unknown, max = 3000) {
  return typeof x === "string" ? x.trim().slice(0, max) : "";
}

export function sameOrigin(req: Request) {
  const origin = req.headers.get("origin");
  if (!origin || origin !== new URL(req.url).origin)
    throw new Error("Request origin rejected.");
}

export async function stripe(path: string, body?: URLSearchParams) {
  const key = runtime().STRIPE_SECRET_KEY;
  if (!key)
    throw new Error(
      "Purchases are not open yet. Please contact JDP to reserve this beat."
    );
  const r = await fetch("https://api.stripe.com/v1/" + path, {
    method: body ? "POST" : "GET",
    headers: {
      Authorization: "Bearer " + key,
      ...(body ? { "Content-Type": "application/x-www-form-urlencoded" } : {}),
    },
    body,
  });
  const data: any = await r.json();
  if (!r.ok) {
    console.error("Stripe request failed", r.status);
    throw new Error("Payment service is unavailable. Please try again.");
  }
  return data;
}
