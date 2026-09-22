import {sqliteTable,text,integer,index} from 'drizzle-orm/sqlite-core';
export const settings=sqliteTable('settings',{key:text('key').primaryKey(),value:text('value').notNull()});
export const tracks=sqliteTable('tracks',{id:text('id').primaryKey(),data:text('data').notNull()});
export const posts=sqliteTable('posts',{id:text('id').primaryKey(),userId:text('user_id').notNull(),name:text('name').notNull(),kind:text('kind').notNull(),body:text('body').notNull(),rating:integer('rating'),parent:text('parent'),created:integer('created').notNull(),approved:integer('approved').notNull().default(0)},t=>[index('idx_posts_approved_created').on(t.approved,t.created)]);
export const inquiries=sqliteTable('inquiries',{id:text('id').primaryKey(),userId:text('user_id').notNull(),name:text('name').notNull(),email:text('email').notNull(),kind:text('kind').notNull(),body:text('body').notNull(),created:integer('created').notNull()});
export const orders=sqliteTable('orders',{id:text('id').primaryKey(),trackId:text('track_id').notNull(),fileKey:text('file_key').notNull(),title:text('title').notNull(),terms:text('terms').notNull(),amount:integer('amount').notNull()});
