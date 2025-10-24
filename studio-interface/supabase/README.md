# Supabase Database Setup

## Prerequisites

You need a Supabase account and project. If you don't have one yet:
1. Go to [https://supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

## Running the Migration

There are two ways to run the migration:

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy the contents of `migrations/001_initial_schema.sql`
5. Paste it into the SQL editor
6. Click **Run** to execute the migration

### Option 2: Using Supabase CLI

If you have the Supabase CLI installed:

```bash
# From the studio-interface directory
supabase db push
```

## Verify the Migration

After running the migration, verify that the tables were created:

1. Go to **Table Editor** in Supabase dashboard
2. You should see three tables:
   - `projects` - Stores user projects
   - `messages` - Stores conversation history
   - `design_versions` - Stores design version snapshots

## What the Migration Does

The migration creates:

### Tables
- **projects**: Stores project metadata, status, and context (discovery data, artifacts, phase)
- **messages**: Stores conversation messages linked to projects
- **design_versions**: Stores design snapshots for version history

### Security
- **Row Level Security (RLS)** enabled on all tables
- Users can only access their own data
- Policies enforce user_id matching for all operations

### Indexes
- Optimized queries for common access patterns
- User ID and timestamp indexes for performance

### Triggers
- Auto-updates `updated_at` timestamp on project changes

## Environment Variables

Make sure your `.env.local` has:

```env
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## Testing the Setup

Once the migration is complete and environment variables are set:

1. Start the app: `npm run dev`
2. Navigate to http://localhost:3000
3. Click **Start New Project**
4. Sign in with email (magic link or OAuth)
5. Create a project - it should save to Supabase
6. Refresh the page - your project should load automatically

## Troubleshooting

### Migration fails with permission error
- Make sure you're using the dashboard SQL editor or have the Supabase CLI properly authenticated

### Tables not appearing
- Check the SQL editor for any error messages
- Verify you ran the complete migration script

### Projects not saving
- Check browser console for errors
- Verify your Supabase URL and anon key are correct
- Check the Supabase dashboard **Authentication** section to confirm users are being created

### RLS policy errors
- The policies require users to be authenticated
- Make sure you're signed in before creating projects
- Check Supabase logs in the dashboard for detailed error messages
