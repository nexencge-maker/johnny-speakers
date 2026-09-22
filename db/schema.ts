import { pgTable, text, integer, timestamp } from "drizzle-orm/pg-core";

// Orders record a completed Stripe checkout so downloads can be verified and
// so a customer's purchased license/file never changes after the fact.
export const orders = pgTable("orders", {
  id: text("id").primaryKey(), // Stripe checkout session id (cs_...)
  trackId: text("track_id").notNull(),
  fileKey: text("file_key").notNull(),
  title: text("title").notNull(),
  terms: text("terms").notNull(),
  amount: integer("amount").notNull(),
  created: timestamp("created", { mode: "date" }).notNull().defaultNow(),
});

// Inquiries are public contact/collaboration messages. No account system:
// anyone can send one, identified only by the name/email they type in.
export const inquiries = pgTable("inquiries", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull(),
  kind: text("kind").notNull(),
  body: text("body").notNull(),
  created: timestamp("created", { mode: "date" }).notNull().defaultNow(),
});
