CREATE TABLE `inquiries` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`name` text NOT NULL,
	`email` text NOT NULL,
	`kind` text NOT NULL,
	`body` text NOT NULL,
	`created` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `orders` (
	`id` text PRIMARY KEY NOT NULL,
	`track_id` text NOT NULL,
	`file_key` text NOT NULL,
	`title` text NOT NULL,
	`terms` text NOT NULL,
	`amount` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `posts` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`name` text NOT NULL,
	`kind` text NOT NULL,
	`body` text NOT NULL,
	`rating` integer,
	`parent` text,
	`created` integer NOT NULL,
	`approved` integer DEFAULT 0 NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_posts_approved_created` ON `posts` (`approved`,`created`);--> statement-breakpoint
CREATE TABLE `settings` (
	`key` text PRIMARY KEY NOT NULL,
	`value` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `tracks` (
	`id` text PRIMARY KEY NOT NULL,
	`data` text NOT NULL
);
