import { eq, and, gt } from "drizzle-orm";
import { getDb } from "@/db";
import { orders, inquiries } from "@/db/schema";

export async function createOrder(order: {
  id: string;
  trackId: string;
  fileKey: string;
  title: string;
  terms: string;
  amount: number;
}) {
  await getDb().insert(orders).values(order);
}

export async function getOrder(id: string) {
  const rows = await getDb().select().from(orders).where(eq(orders.id, id)).limit(1);
  return rows[0] ?? null;
}

export async function createInquiry(inquiry: {
  id: string;
  name: string;
  email: string;
  kind: string;
  body: string;
}) {
  await getDb().insert(inquiries).values(inquiry);
}

// Simple abuse guard: block a second inquiry from the same email within 30s.
export async function recentInquiryFrom(email: string) {
  const since = new Date(Date.now() - 30_000);
  const rows = await getDb()
    .select({ id: inquiries.id })
    .from(inquiries)
    .where(and(eq(inquiries.email, email), gt(inquiries.created, since)))
    .limit(1);
  return rows.length > 0;
}
