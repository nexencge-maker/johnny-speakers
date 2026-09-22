import { masterStore } from "@/lib/blobs";
import { createInquiry, createOrder, getOrder, recentInquiryFrom } from "@/lib/orders";
import { runtime, sameOrigin, stripe, textValue } from "@/lib/server";
import { initialTracks } from "@/lib/catalog";

export const dynamic = "force-dynamic";

const json = (x: unknown, status = 200) =>
  Response.json(x, { status, headers: { "Cache-Control": "no-store" } });

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const action = url.searchParams.get("action");

    if (action === "download") {
      const sid = url.searchParams.get("session") || "";
      if (!/^cs_(test_|live_)?[a-zA-Z0-9_]+$/.test(sid))
        return json({ error: "Invalid order" }, 400);
      const session = await stripe("checkout/sessions/" + sid);
      const order = await getOrder(sid);
      if (
        !order ||
        session.payment_status !== "paid" ||
        session.amount_total !== order.amount ||
        session.metadata?.store !== "johnny-speakers"
      )
        return json(
          { error: "Payment is not confirmed yet. Please retry after checkout." },
          403
        );
      if (url.searchParams.get("license") === "1")
        return new Response(order.title + "\nOrder " + sid + "\n\n" + order.terms, {
          headers: {
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Disposition": 'attachment; filename="JDP-license.txt"',
            "Cache-Control": "no-store",
          },
        });
      const file = await masterStore().get(order.fileKey, { type: "stream" });
      if (!file)
        return json(
          { error: "Your file is unavailable. Contact JDP with your receipt." },
          404
        );
      return new Response(file, {
        headers: {
          "Content-Type": "application/octet-stream",
          "Content-Disposition":
            'attachment; filename="' + order.fileKey.split("/").pop() + '"',
          "Cache-Control": "private, no-store",
          "Referrer-Policy": "no-referrer",
        },
      });
    }

    // Default: tell the client which tracks are actually purchasable right
    // now (delivery file uploaded, terms written, Stripe configured) without
    // ever exposing the Stripe secret key itself.
    const payments = !!runtime().STRIPE_SECRET_KEY;
    const available = payments
      ? initialTracks.filter((t) => t.enabled && t.master && t.terms).map((t) => t.id)
      : [];
    return json({ available, payments });
  } catch (e) {
    console.error(e);
    return json(
      { error: e instanceof Error ? e.message : "Store temporarily unavailable" },
      503
    );
  }
}

export async function POST(req: Request) {
  try {
    sameOrigin(req);
    const url = new URL(req.url);
    const action = url.searchParams.get("action");
    const b: any = await req.json();

    if (action === "checkout") {
      const t = initialTracks.find((t) => t.id === b.id);
      if (!t || !t.enabled || !t.master || !t.terms || !runtime().STRIPE_SECRET_KEY)
        throw new Error("This beat is preview-only. Contact JDP for availability.");
      const meta = await masterStore().getMetadata(t.master);
      if (!meta)
        throw new Error("The delivery file is unavailable. No payment was taken.");
      const origin = runtime().SITE_URL || url.origin;
      const p = new URLSearchParams({
        mode: "payment",
        "payment_method_types[0]": "card",
        "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][unit_amount]": String(Math.round(t.price * 100)),
        "line_items[0][price_data][product_data][name]": t.title + " — JDP license",
        "line_items[0][quantity]": "1",
        success_url: origin + "/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url: origin + "/?cancelled=1",
        "metadata[store]": "johnny-speakers",
        "metadata[track]": t.id,
      });
      const s = await stripe("checkout/sessions", p);
      await createOrder({
        id: s.id,
        trackId: t.id,
        fileKey: t.master,
        title: t.title,
        terms: t.terms,
        amount: Math.round(t.price * 100),
      });
      return json({ url: s.url });
    }

    if (action === "inquiry" || action === "contact") {
      const email = textValue(b.email, 250);
      const name = textValue(b.name, 80) || "Music fan";
      const body = textValue(b.body);
      if (!EMAIL_RE.test(email)) throw new Error("Enter a valid reply email.");
      if (body.length < 5) throw new Error("Please write at least 5 characters.");
      if (await recentInquiryFrom(email))
        throw new Error("Please wait 30 seconds before sending another message.");
      await createInquiry({
        id: crypto.randomUUID(),
        name,
        email,
        kind: textValue(b.kind, 50) || "contact",
        body,
      });
      return json({ ok: true, message: "Your message is in JDP’s inbox." });
    }

    return json({ error: "Unknown action" }, 400);
  } catch (e) {
    console.error(e);
    return json(
      { error: e instanceof Error ? e.message : "Unable to save. Please try again." },
      400
    );
  }
}
