# The Workspace Pattern: Building Serious Projects with Amplifier

## Quick Start

Already convinced? Here's how to set it up:

```bash
# 1. Create your Amplifier workspace
git clone https://github.com/microsoft/amplifier.git my-workspace
cd my-workspace

# 2. Add your project (existing or new)
git submodule add <your-project-git-url> my-project
# OR: git submodule add git@github.com:yourname/your-project.git my-project

# 3. Set up project context
cd my-project
cat > AGENTS.md << 'EOF'
# My Project Context

This file provides guidance to AI assistants working with this project.

## Project Overview
[Brief description of what this project does]

## Working in This Project

When working on this project:
- All project files belong in this directory
- Use `ai_working/` for temporary files
- Reference files with `@my-project/` prefix
- Follow our design principles at @my-project/docs/DESIGN.md

## Key Technologies
- [List your main technologies/frameworks]

## Development Workflow
- [Your specific workflow notes]
EOF

# 4. Start working
cd ..
claude
```

In Claude Code, start with:

```
I'm working on the @my-project/ project within this Amplifier workspace.
Please read @my-project/AGENTS.md for project-specific guidance.
```

That's it. Read on for why this matters and how to use it effectively.

---

## Why This Pattern Exists

When you start using Amplifier, the simplest approach is to work directly in the `ai_working/` directory. Create a folder, drop in your code, and go. This works great for experiments, prototypes, and small projects.

But as projects grow, you'll hit friction points:

**Version control gets messy.** Your project files mix with Amplifier's structure. When you pull Amplifier updates, you worry about conflicts. When you commit project changes, they're tangled with workspace changes.

**Context doesn't persist.** Each new Claude session starts fresh. You find yourself re-explaining your project's architecture, conventions, and goals. The AI is helpful but forgetful.

**Boundaries blur.** Project-specific documentation ends up in Amplifier's docs. Project utilities creep into Amplifier's scripts. It becomes unclear what belongs where.

**Scaling is awkward.** Want to work on multiple projects? You end up with `ai_working/project1/`, `ai_working/project2/`, each fighting for the same namespace.

The workspace pattern solves these problems by inverting the relationship: instead of projects living inside Amplifier, Amplifier becomes a dedicated workspace that hosts projects as first-class citizens.

## The Architecture

Think of it like a workshop. Amplifier is your workbench with all your tools organized and ready. Your projects are the pieces you're actively working on, each with its own space on the bench but sharing the same tool set.

```bash
my-workspace/               # Your Amplifier workspace
├── .claude/                # Agent + command definitions
├── docs/                   # Amplifier docs
├── scenarios/              # Amplifier tools
│
├── my-blog/                # Your first project
│   ├── AGENTS.md           # Project context (AI guidance)
│   ├── docs/               # Project documentation
│   ├── src/                # Project code
│   └── ai_working/         # Temporary work files
│
└── client-portal/          # Your second project
    ├── AGENTS.md           # Different project, different context
    ├── backend/
    ├── frontend/
    └── ai_working/
```

Each project maintains its own git history, documentation, and context. Amplifier stays pristine and updatable. Everything has a clear home.

## Setting Up Your Workspace

### Fork or Clone Amplifier

Start by creating your personal Amplifier workspace:

```bash
# Option 1: Fork and clone (recommended if you'll customize Amplifier)
# Fork microsoft/amplifier on GitHub, then:
git clone https://github.com/yourusername/amplifier.git my-workspace

# Option 2: Direct clone (simpler if you won't customize)
git clone https://github.com/microsoft/amplifier.git my-workspace
```

Why make it your own? Because you might want to add custom agents, adjust configurations, or experiment with changes without affecting upstream Amplifier.

### Add Your Project as a Submodule

A git submodule is just a way to include one git repository inside another while keeping their histories separate. Think of it as a bookmark: the outer repository (workspace) remembers which commit of the inner repository (project) to use, but the inner repository maintains its own version control.

For an existing project:

```bash
cd my-workspace
git submodule add git@github.com:yourname/your-project.git my-project
```

For a new project:

```bash
cd my-workspace
mkdir my-project
cd my-project
git init
git remote add origin git@github.com:yourname/your-project.git
cd ..
git submodule add ./my-project my-project
```

The key is that `my-project` maintains its own `.git` directory and history. Changes you make in `my-project/` are tracked by your project's repository, not by the Amplifier workspace.

### Create Your AGENTS.md

This file is your project's persistent memory. Every time Claude starts working with your project, it reads this file first. Think of it as the onboarding document for a new team member—except this team member has perfect memory within a session but starts fresh each time.

```bash
cd my-project
```

Create `AGENTS.md` with your project's context:

# My Blog Platform Context

This file provides guidance to AI assistants working on this blog platform.

## Project Overview

A personal blog platform built with Next.js and Markdown, focused on fast static
generation and rich media support. The architecture prioritizes simplicity over
flexibility—we'd rather have less features done well than many features done poorly.

## Core Principles

- **Ruthless simplicity**: Every feature must justify its existence
- **Static-first**: Generate at build time, serve static HTML
- **Markdown is truth**: Blog posts live in `/content` as Markdown files
- **No database**: File system is our storage layer

## Key Technologies

- Next.js 14 (App Router)
- TypeScript (strict mode)
- TailwindCSS for styling
- gray-matter for frontmatter parsing
- remark/rehype for Markdown processing

## Project Structure

```bash
src/
├── app/            # Next.js app router pages
├── components/     # React components
├── lib/            # Utilities and shared logic
└── types/          # TypeScript type definitions

content/            # Blog posts (Markdown)
public/             # Static assets
```

## Development Workflow

1. Run dev server: `pnpm dev`
2. Posts go in `content/posts/YYYY-MM-DD-slug.md`
3. Images go in `public/images/`
4. Test builds with `pnpm build`

## Common Tasks

- **Add new post**: Create Markdown file in `content/posts/`
- **Add component**: Create in `src/components/`, export from index
- **Update types**: Modify `src/types/blog.ts`
- **Deploy**: Push to main, Vercel auto-deploys

## Things to Avoid

- Don't add a database (we're committed to file-based)
- Don't create complex state management (keep it simple)
- Don't add build-time external API calls (they slow builds)

The key is making this document useful for both AI assistants and human developers. It should answer: What is this project? How is it architected? What conventions do we follow? What should I avoid?

### Optional: Add Philosophy Documents

For larger projects, consider documenting your architectural principles separately:

```bash
mkdir -p docs
```

Create `docs/DESIGN_PHILOSOPHY.md`:

```markdown
# Blog Platform Design Philosophy

## Core Beliefs

**Static generation is superior to dynamic rendering** for content that doesn't
change often. Our blog posts are timeless once published. Pre-rendering them at
build time means instant page loads for readers and lower hosting costs.

**The file system is the database.** Instead of a PostgreSQL table of blog posts,
we have a directory of Markdown files. This makes the content portable, version-
controllable, and debuggable. You can read a blog post without starting the
application.

**Convention over configuration.** We don't need a CMS with ten different ways to
structure a post. We have one way: frontmatter for metadata, Markdown for content.
This constraint is freeing, not limiting.

## Decision Framework

When adding features, ask:

1. **Does this need to be dynamic?** If not, do it at build time.
2. **Can we do this with files?** If yes, avoid adding a database.
3. **Is this the simplest approach?** If not, simplify.
4. **Does this align with our principles?** If not, reconsider.
```

These philosophy documents act as decision filters. When the AI proposes something complex, it checks against these principles and often finds a simpler path.

## Working in the Workspace

### Starting a Session

When you open Claude Code in your workspace, set context immediately:

```
I'm working on the @my-blog/ project within this Amplifier workspace.
Please read @my-blog/AGENTS.md for project-specific guidance.
All changes should be scoped to the @my-blog/ directory.
Use @my-blog/ai_working/ for temporary files.
```

This establishes boundaries from the start. The `@` prefix creates namespace clarity—it's always obvious which files belong to which context.

### Using @ Syntax Consistently

Reference files with their full workspace path:

- `@my-blog/src/components/Header.tsx`
- `@my-blog/docs/DESIGN_PHILOSOPHY.md`
- `@my-blog/content/posts/2024-01-15-hello.md`

This prevents ambiguity. When Claude sees `@my-blog/`, it knows these files belong to your project, not to Amplifier.

### Scoping File Operations

Tell Claude explicitly when scoping matters:

```
Please review all TypeScript files in @my-blog/src/ for type safety.

Add error handling to the functions in @my-blog/lib/markdown.ts.

Create a new component at @my-blog/src/components/PostList.tsx.
```

Being explicit prevents accidental changes to Amplifier itself.

### Managing Temporary Files

Use the project's `ai_working/` directory for drafts, experiments, and temporary work:

```bash
my-blog/
├── ai_working/                # Temporary work
│   ├── refactor-ideas.md      # Planning documents
│   ├── test-output/           # Test artifacts
│   └── experiments/           # Code experiments
├── src/                       # Real project code
└── content/                   # Real blog posts
```

This keeps your project clean while giving Claude space to work. The `ai_working/` directory should be in your `.gitignore`.

### Version Control Workflow

Your workspace and project have independent git histories:

```bash
# Working on your project
cd my-blog
git add src/components/Header.tsx
git commit -m "Add responsive header"
git push origin main

# Updating Amplifier in your workspace
cd ..                   # Back to workspace root
git pull origin main    # Updates Amplifier
git submodule update    # Syncs submodule references
```

The workspace tracks which version of your project it expects, but your project's git history is entirely separate. This means you can:

- Update Amplifier without affecting your project
- Version your project independently
- Share your project without sharing your workspace
- Collaborate with others who might use different workspaces

## The AGENTS.md Contract

Think of AGENTS.md as a contract between you and the AI. Each session, Claude reads this contract and agrees to work within its terms. The contract establishes:

**What this project is.** Not just technically (a Next.js blog), but philosophically (a static-first, simplicity-focused platform). This shapes every suggestion the AI makes.

**How we work here.** Where do files go? What's our naming convention? What commands do we run? These conventions prevent the AI from reinventing the wheel each session.

**What we avoid.** Just as important as what we do. "Don't add a database" is a guardrail that prevents well-meaning but misguided complexity.

**Our current state.** Technologies, structure, recent changes. This context means the AI doesn't suggest outdated patterns or incompatible tools.

The beauty of AGENTS.md is that it compounds over time. Each session, you might add a new insight, clarify a convention, or document a decision. The next session benefits from all previous sessions' learning. Context doesn't reset—it accumulates.

## When to Use This Pattern

The workspace pattern isn't always the right choice. Here's a decision framework:

**Use `ai_working/` for:**

- Quick experiments and prototypes
- Learning exercises and tutorials
- Throwaway code and one-off scripts
- When you need something fast and don't care about long-term maintenance

**Use the workspace pattern for:**

- Projects that will live for months or years
- Codebases with their own git repository
- Work you'll share with others or deploy to production
- Projects where you want persistent AI context
- When you're working on multiple projects simultaneously

Think of `ai_working/` as your scratch pad and the workspace pattern as your filing cabinet. Both have their place.

## Migrating from ai_working/

Already have a project in `ai_working/` that's outgrown it? Here's how to migrate:

### 1. Initialize Git in Your Project

```bash
cd ai_working/my-project
git init
git add .
git commit -m "Initial commit - migrating to workspace pattern"
```

### 2. Push to Remote Repository

Create a repository on GitHub/GitLab/etc, then:

```bash
git remote add origin git@github.com:yourname/my-project.git
git push -u origin main
```

### 3. Move to Workspace Root

```bash
cd ../..  # Back to workspace root
git submodule add git@github.com:yourname/my-project.git my-project
```

### 4. Copy Working Files

If you have useful temporary files in the old location:

```bash
cp -r ai_working/my-project/ai_working my-project/ai_working
```

### 5. Create AGENTS.md

Document what you've learned about this project:

```bash
cd my-project
cat > AGENTS.md << 'EOF'
# My Project Context

[Document your project's architecture, conventions, and principles]
EOF
git add AGENTS.md
git commit -m "Add AGENTS.md for workspace pattern"
git push
```

### 6. Update Your Workspace

```bash
cd ..  # Back to workspace root
git add .gitmodules my-project
git commit -m "Add my-project as submodule"
```

### 7. Clean Up Old Location

```bash
rm -rf ai_working/my-project
```

Now your project has clean git history, persistent context, and clear boundaries.

## Multiple Projects

The workspace pattern shines when you're working on several projects. Each project gets its own submodule with its own AGENTS.md:

```
my-workspace/
├── personal-blog/           # Personal project
│   └── AGENTS.md           # "This is a casual blog..."
├── client-portal/          # Client work
│   └── AGENTS.md           # "Enterprise security requirements..."
└── ml-experiment/          # Research project
    └── AGENTS.md           # "Experimental ML approaches..."
```

When you switch projects, just tell Claude which context to load:

```
Switch to working on @client-portal/. Read @client-portal/AGENTS.md.
```

The AI instantly adapts to that project's conventions, technologies, and constraints. No cross-contamination between projects.

## Practical Tips

**Keep AGENTS.md current.** When you make architectural decisions, document them. When you adopt new conventions, add them. Treat it as a living document.

**Use philosophy docs for big decisions.** If you find yourself making the same architectural argument repeatedly, write it down in a philosophy document. Then reference it: "Review this against our principles at @my-project/docs/DESIGN_PHILOSOPHY.md."

**Namespace with @.** Always use the `@project-name/` prefix in Claude conversations. It prevents ambiguity and makes transcripts clearer.

**Separate concerns clearly.** Project code in the project directory. Amplifier customizations in the workspace. Temporary work in `ai_working/`. Clear boundaries prevent confusion.

**Update Amplifier regularly.** Since your projects are isolated submodules, you can pull Amplifier updates without fear:

```bash
cd my-workspace
git pull origin main
git submodule update
```

Your projects remain untouched while you get the latest Amplifier features.

**Commit project changes frequently.** Since your project has its own git history, commit often. This creates restore points and makes collaboration easier.

## Common Questions

**Q: Can I use this pattern without git submodules?**

Yes, but you lose the version control isolation. You could symlink your project directory into the workspace, but then you don't get the clean separation of git histories. The submodule approach is recommended precisely because it maintains that separation.

**Q: What if I want to customize Amplifier?**

That's why you fork it first. Make your workspace repository your own fork, then customize away. Add custom agents, modify configurations, experiment with new features. Your projects continue working because they're isolated submodules.

**Q: How do I share my project with someone using a different workspace?**

Just share the project repository. They add it as a submodule to their workspace. The project code is fully portable—it doesn't depend on any specific workspace configuration.

**Q: Can I have nested projects?**

Technically yes, but it gets complicated. Better to keep projects flat at the workspace level. If you need related projects, make them siblings rather than nested.

**Q: What goes in the workspace's `ai_working/` vs the project's?**

Workspace-level experiments and notes that span multiple projects. Project-specific temporary files in the project's `ai_working/`. When in doubt, put it in the project's directory.

## The Pattern in Practice

Here's what a typical session looks like once you've internalized the pattern:

```bash
cd my-workspace
claude
```

In Claude:

```
Working on @personal-blog/. Read @personal-blog/AGENTS.md.

I want to add a new feature: automatically generate social media preview images
for blog posts. This should happen at build time and follow our static-first
philosophy. What's the best approach?
```

Claude reads your AGENTS.md, understands your tech stack (Next.js) and principles (static-first, simple), and proposes a solution that fits your architecture. No need to re-explain your project every time.

When you're done:

```bash
cd personal-blog
git add .
git commit -m "Add social media preview generation"
git push
```

Clean git history, persistent context, clear boundaries. The workspace pattern working as intended.

## Conclusion

The workspace pattern is about treating your development environment as seriously as your code. By inverting the relationship—making Amplifier the host rather than the container—you get clean separation, persistent context, and a scalable foundation for multiple projects.

It's more setup than dropping code in `ai_working/`, but the payoff grows over time. Each project accumulates context through AGENTS.md. Amplifier stays updatable. Version control stays clean. And you can work on multiple projects without them interfering with each other.

Start simple with `ai_working/` for experiments. Graduate to the workspace pattern when projects get serious. Your future self will thank you.
