import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";
import * as schema from "./schema";

// Netlify DB (Neon Postgres) is reachable over HTTP, which is what makes it
// safe to call from serverless/edge functions without pooled TCP connections.
export function getDb() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    throw new Error(
      "DATABASE_URL is not set. Provision Netlify DB (or any Postgres) and set DATABASE_URL before using the database."
    );
  }
  return drizzle(neon(url), { schema });
}
