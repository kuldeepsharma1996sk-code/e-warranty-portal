-- 1. Table for Internal Companies (TRIAD Marketing, TRIAD Tech, etc.)
create table internal_companies (
  id uuid default uuid_generate_v4() primary key,
  name text not null,
  logo_url text, -- URL to the image in Supabase Storage
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc', now())
);

-- 2. Table for Client Projects (Rajasthan Gramin Bank, etc.)
create table client_projects (
  id uuid default uuid_generate_v4() primary key,
  company_id uuid references internal_companies(id),
  client_name text not null,
  terms_conditions text, -- HTML or plain text from the editor
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc', now())
);

-- 3. Storage Bucket Policy (Run this to allow public reading of logos)
insert into storage.buckets (id, name, public) values ('logos', 'logos', true);
