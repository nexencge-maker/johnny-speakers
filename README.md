# Johnny Speakers

Public music storefront and portfolio for JDP / John da Poet. Plain Next.js (App Router), deployable on Netlify. Previews, cover art and archive videos are in `public/media`. Full purchased masters are never placed in public assets.

This is a public site with no login: anyone can browse, listen to previews, and send a contact/collaboration message. There is no admin dashboard — the track catalog, prices and license terms are edited directly in [lib/catalog.ts](lib/catalog.ts) and deployed via git.

## Stack

- **Framework:** Next.js 16 (App Router), deployed on Netlify via `@netlify/plugin-nextjs`.
- **Database:** Postgres via [Netlify DB](https://docs.netlify.com/build/data-and-storage/netlify-database/) (Neon), accessed with Drizzle ORM over HTTP (`@neondatabase/serverless`). Used only for `orders` (purchase records, for verified downloads) and `inquiries` (contact/collaboration messages). Public browsing never touches the database.
- **File storage:** [Netlify Blobs](https://docs.netlify.com/build/data-and-storage/netlify-blobs/) holds the private, full-quality delivery files customers pay for. Public previews/cover art/video are static files committed to `public/media`.
- **Payments:** Stripe hosted Checkout, with server-verified file/license delivery on the `/success` page.

## Managing the catalog

Edit `initialTracks` and `initialSettings` in [lib/catalog.ts](lib/catalog.ts):

- Add a track's title, genre, description, price and a `preview`/`cover` path under `public/media`.
- Set `enabled: true`, write the `terms` (license text shown at checkout), and set `master` to the private Blobs key of the uploaded delivery file (see below) to make it purchasable.
- Commit and push — Netlify redeploys automatically.

### Uploading a private delivery file

Delivery files never go in `public/`. Upload them to the `masters` Netlify Blobs store, e.g. with the Netlify CLI:

```bash
netlify blobs:set masters "private/my-track.wav" --input ./my-track.wav
```

Use the same key (`private/my-track.wav`) as the track's `master` field in `lib/catalog.ts`.

## Payments

Set `STRIPE_SECRET_KEY` as a Netlify environment variable before enabling sales. Start with a Stripe test key and verify checkout, cancellation and file delivery before switching to a live key. A track is only purchasable when it is `enabled`, has `master` and `terms` set, its delivery file exists in Blobs, and `STRIPE_SECRET_KEY` is configured — otherwise the site shows it as preview-only with a "contact" call to action. Orders snapshot the file key, price and terms at checkout time, so editing a track later never changes what an existing customer already bought. Automatic purchase emails are not implemented; configure receipts through Stripe.

## Configuration

Set these as environment variables in the Netlify site dashboard (Site configuration → Environment variables):

- `DATABASE_URL`: Postgres connection string (Netlify DB / Neon).
- `STRIPE_SECRET_KEY`: Stripe test or live secret key.
- `SITE_URL`: your deployed site origin (update if you connect a custom domain).

Copy `.env.example` to `.env` for local development.

## Development

```bash
npm install
cp .env.example .env   # fill in DATABASE_URL / STRIPE_SECRET_KEY as needed
npm run dev
```

Database schema lives in [db/schema.ts](db/schema.ts). After setting `DATABASE_URL`, apply it with:

```bash
npm run db:push       # quick one-time sync, good for getting started
# or
npm run db:generate && npm run db:migrate   # versioned migrations
```

## Deploying to Netlify

1. Push this repository to GitHub (already connected to `nexencge-maker/johnny-speakers`).
2. In Netlify: **Add new site → Import an existing project**, pick the repo. Netlify auto-detects Next.js and uses [netlify.toml](netlify.toml) / `@netlify/plugin-nextjs`.
3. Provision a database: **Extensions → Netlify DB** (or connect your own Postgres) and set `DATABASE_URL`.
4. Set `STRIPE_SECRET_KEY` and `SITE_URL` in environment variables.
5. Run `npm run db:push` once (locally, pointed at the production `DATABASE_URL`, or via `netlify dev`) to create the `orders`/`inquiries` tables.
6. Upload any private delivery files to the `masters` Blobs store (see above), then flip the corresponding tracks to `enabled: true` in `lib/catalog.ts` and push.

## Current limitations

Custom domain registration and Stripe onboarding are not complete. No confirmed music email or social-profile URLs were found, so those fields remain empty in `lib/catalog.ts`. Proposed prices ($29 MP3 / $49 WAV / $79 trackouts) shown on the Pricing tab are illustrative; checkout only ever uses each enabled track's saved price and terms. AI-assisted archive visuals are labeled; type-beat references are not artist endorsements.

## Home-screen app

The public `/install` page explains installation on iOS, Android and desktop and offers a native browser install prompt when supported. The web manifest, PNG app icons and Apple metadata enable standalone launches. The service worker caches only a generic offline page: music, payments and API responses are never stored in its cache. An internet connection is required for store features.
