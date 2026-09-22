# Johnny Speakers — source download

This archive contains the latest website source, imported audio previews and videos, and installable web-app files. Start with README.md for the feature overview.

## What you can do with this ZIP

Unzip it on your computer and upload the project to your own Git repository. It contains source code rather than a static drag-and-drop website. node_modules and build output are intentionally excluded.

## Local setup

1. Install Node.js 22.13 or later and the pnpm version specified in package.json.
2. In the extracted folder, run `pnpm install --frozen-lockfile`.
3. Copy `.env.example` to `.env` and provide your own runtime values. Never commit credentials.
4. Run `pnpm dev` for local development; run `pnpm build` to create the Worker build.

## Before deploying outside ChatGPT Sites

The current application uses Cloudflare Workers, D1 database binding DB, and R2 file binding BUCKET. It is not a plain HTML site and cannot be deployed unchanged to GitHub Pages. Other server platforms require adapting the Cloudflare-specific server code.

Create your own database and bucket, configure their deployment bindings, and apply the SQL migrations in drizzle/ to the new database. The exported hosting.json retains logical bindings but has its existing Site project ID removed, so this export does not identify the live Site.

CRITICAL: Authentication currently relies on ChatGPT Sites' trusted identity headers and sign-in routes. Those are NOT provided by ordinary hosting. Implement a verified authentication provider/session layer in app/chatgpt-auth.ts and the sign-in/sign-out flow before enabling uploads, messages, community posts or owner activation on another host. Never trust client-supplied oai-authenticated-user-* headers. The app's database owner ID is tied to the original authentication system and must be re-established with the new provider.

Set SITE_URL to your new origin. Create a new OWNER_SETUP_CODE. Configure STRIPE_SECRET_KEY securely and test payment and download flows before accepting purchases. No credentials are included.

## Included and excluded

Included: React/Vinext source, styling, components, lockfile, migrations, public previews, two archive music videos, app icons, manifest, service worker and offline screen.
Excluded: live database records, private R2 uploads, customer submissions, owner account state, payment keys and Git history. This is a code/media export, not a live-data backup. Migrate those resources separately if needed.

## Deployment status

The original public website remains unchanged. This exported source has not been deployed or tested on an independent hosting account. Choose a hosting provider before adapting its production configuration; the authentication integration is the main required portability change.
