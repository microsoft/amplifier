-- Studio Database Schema
-- Run this in your Supabase SQL editor

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Projects table
create table projects (
  id uuid primary key default uuid_generate_v4(),
  user_id text not null, -- Using text for demo, will be uuid with real auth
  name text not null,
  status text not null default 'discovery', -- discovery, expression, completed
  context jsonb default '{}'::jsonb, -- Discovery context (audience, purpose, etc)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Messages table (conversation history)
create table messages (
  id uuid primary key default uuid_generate_v4(),
  project_id uuid references projects(id) on delete cascade not null,
  role text not null check (role in ('user', 'ai')),
  content text not null,
  metadata jsonb default '{}'::jsonb, -- Additional data (tokens, model, etc)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Design versions table
create table design_versions (
  id uuid primary key default uuid_generate_v4(),
  project_id uuid references projects(id) on delete cascade not null,
  version_number integer not null,
  snapshot jsonb not null, -- Complete design state
  action text not null, -- Description of what changed
  user_action boolean default false, -- User-initiated vs AI-generated
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Indexes for performance
create index messages_project_id_idx on messages(project_id);
create index messages_created_at_idx on messages(created_at);
create index design_versions_project_id_idx on design_versions(project_id);
create index projects_user_id_idx on projects(user_id);
create index projects_updated_at_idx on projects(updated_at);

-- Row Level Security (RLS) - Disabled for demo
-- Enable these when adding real authentication
-- alter table projects enable row level security;
-- alter table messages enable row level security;
-- alter table design_versions enable row level security;

-- RLS Policies commented out for demo
-- Uncomment and configure when adding authentication

-- create policy "Users can view own messages"
--   on messages for select
--   using (
--     exists (
--       select 1 from projects
--       where projects.id = messages.project_id
--       and projects.user_id = auth.uid()::text
--     )
--   );

-- create policy "Users can insert own messages"
--   on messages for insert
--   with check (
--     exists (
--       select 1 from projects
--       where projects.id = messages.project_id
--       and projects.user_id = auth.uid()::text
--     )
--   );

-- create policy "Users can view own design versions"
--   on design_versions for select
--   using (
--     exists (
--       select 1 from projects
--       where projects.id = design_versions.project_id
--       and projects.user_id = auth.uid()::text
--     )
--   );

-- create policy "Users can insert own design versions"
--   on design_versions for insert
--   with check (
--     exists (
--       select 1 from projects
--       where projects.id = design_versions.project_id
--       and projects.user_id = auth.uid()::text
--     )
--   );

-- Updated_at trigger function
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$ language plpgsql;

-- Apply trigger to projects table
create trigger update_projects_updated_at
  before update on projects
  for each row
  execute function update_updated_at_column();
