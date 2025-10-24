# Studio Interface Setup

This guide will help you set up the Studio Interface with Supabase and Claude API integration.

## Prerequisites

- Node.js 18+ installed
- A Supabase account ([supabase.com](https://supabase.com))
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

## 1. Install Dependencies

```bash
npm install
```

Dependencies installed:
- `@supabase/supabase-js` - Supabase client
- `@anthropic-ai/sdk` - Claude API client
- `zustand` - State management
- Next.js 14 with React 18

## 2. Set Up Supabase

### Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to finish setting up

### Run the Database Schema

1. In your Supabase project, go to the SQL Editor
2. Copy the contents of `supabase/schema.sql`
3. Paste and run the SQL to create:
   - `projects` table
   - `messages` table
   - `design_versions` table
   - Row Level Security policies
   - Indexes for performance

### Get Your Supabase Credentials

1. Go to Project Settings > API
2. Copy your Project URL
3. Copy your anon/public key

## 3. Set Up Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.local.example .env.local
   ```

2. Edit `.env.local` and add your credentials:
   ```bash
   # Supabase Configuration
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

   # Anthropic Claude API
   ANTHROPIC_API_KEY=sk-ant-your-api-key-here
   ```

## 4. Run the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Architecture

### Application Flow

1. **Empty State** → User starts a new project
2. **Discovery Phase** → AI conversation to understand requirements
3. **Expression Phase** → Design workspace with live preview
4. **Export Phase** → Generate production-ready code (coming soon)

### Key Files

- `app/page.tsx` - Main router that switches between phases
- `components/EmptyState.tsx` - Initial landing screen
- `components/DiscoveryConversation.tsx` - AI discovery conversation
- `components/ExpressionWorkspace.tsx` - Full design workspace
- `state/store.ts` - Zustand state management
- `lib/supabase.ts` - Supabase client configuration
- `lib/hooks/useProject.ts` - Project persistence hooks
- `app/api/chat/route.ts` - Claude API endpoint

### Database Schema

**projects**
- Stores project metadata, status, and discovery context
- Links to user via `user_id`

**messages**
- Conversation history for each project
- Supports both 'user' and 'ai' roles

**design_versions**
- Version history of design changes
- Tracks user-initiated vs AI-generated changes

All tables have Row Level Security enabled to ensure users only access their own data.

## Authentication (Coming Soon)

Currently, the app uses a placeholder user ID (`demo-user-id`). In production, you'll need to:

1. Enable Supabase Auth
2. Add sign-in/sign-up UI
3. Replace placeholder user IDs with real authenticated users
4. Use `auth.uid()` in RLS policies (already configured)

## Design System

Studio implements a 9-dimensional design framework:

1. **Style** - German car facility aesthetic (Porsche/Braun)
2. **Behaviors (Motion)** - Purposeful, choreographed animations
3. **Voice** - Conversational, intelligent, collaborative
4. **Space** - 8px grid, generous whitespace
5. **Color** - Muted palette with precise accents
6. **Typography** - Sora (headings), Geist (body)
7. **Proportion** - Mathematical harmony
8. **Texture** - Glassmorphism, subtle depth
9. **Body** - Responsive, adaptive layouts

See `FRAMEWORK.md` and `IMPLEMENTATION-SPEC.md` for detailed design guidance.

## Troubleshooting

### Fonts not loading
- Check that font variables are properly referenced in `globals.css`
- Ensure fonts are loaded in `app/layout.tsx`

### Supabase connection errors
- Verify your environment variables are set correctly
- Check that the SQL schema was run successfully
- Ensure your Supabase project is active

### Claude API errors
- Verify your Anthropic API key is valid
- Check your API usage limits
- Review the console for detailed error messages

## Next Steps

1. Add authentication with Supabase Auth
2. Implement design generation in Expression phase
3. Add export functionality
4. Create inspiration panel with reference images
5. Add collaborative features

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Anthropic Claude API](https://docs.anthropic.com)
- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
