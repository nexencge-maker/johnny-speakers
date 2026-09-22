# Johnny Speakers

Public music storefront for JDP / John da Poet. Built with React, Vinext and Cloudflare Workers, D1 and R2. Original imported previews and two archive videos are in public/media. Full purchased masters are never placed in public assets.

## Owner workflow

Open /studio, sign in with ChatGPT, and activate once using the private setup code supplied at handoff. The studio binds to that authenticated account. Upload short public previews, cover art and private delivery files (25 MB each), edit pricing and exact license terms, then enable sales. Contact details and social links are editable. Private inquiries and community moderation appear in the studio.

## Payments

Stripe hosted Checkout and server-verified file/license delivery are implemented. Set STRIPE_SECRET_KEY as a runtime secret before enabling purchases. Start with Stripe test mode and verify payment, cancellation and file delivery before using a live key. No Stripe credentials have been supplied. Imported tracks are preview-only by default; upload delivery files and supply license terms before enabling sales. Orders snapshot file keys, amounts and terms so later edits do not change a customer's purchased license. Fulfillment is on the checkout return page; automatic purchase emails are not implemented. Configure receipts through Stripe and retain the order URL.

## Configuration

OWNER_SETUP_CODE: random one-time owner-claim secret.
STRIPE_SECRET_KEY: Stripe test or live secret key.
SITE_URL: deployed site origin (update when connecting a custom domain).

Production values are configured outside source. Copy .env.example to .env for local development. The logical DB and BUCKET declarations in .openai/hosting.json are provisioned by Sites. Public visitors can browse without signing in. Submitting messages and posts uses platform ChatGPT sign-in. Only the claimed owner can upload or manage content. Rehosting elsewhere requires configuring equivalent trusted identity forwarding; never expose identity-header-based authorization behind an untrusted proxy.

## Development

Use the package manager declared in package.json and pnpm-lock.yaml. Run the dev and build scripts. D1 schema lives in db/schema.ts, migrations in drizzle/. Apply migrations when starting a standalone local database. Site source is retained in its connected repository for future edits.

## Current limitations

Custom domain registration and Stripe onboarding are not complete. No confirmed music email or social-profile URLs were found, so those fields remain empty. Proposed prices ($29 MP3 / $49 WAV / $79 trackouts) come from the earlier store draft; public checkout uses only each enabled track's saved price and terms. AI-assisted archive visuals are labeled; type-beat references are not artist endorsements. WebMCP filter registration is optional and its execution could not be verified in the preview browser because modelContext was unavailable.

## Home-screen app

The public /install page explains installation on iOS, Android and desktop and offers a native browser install prompt when supported. The web manifest, PNG app icons and Apple metadata enable standalone launches. The service worker caches only a generic offline page: music, account pages, payments and API responses are never stored in its cache. An internet connection is required for store features. This is an installable web app, not an App Store or Google Play listing. Installation on physical devices has not been verified in this environment.
