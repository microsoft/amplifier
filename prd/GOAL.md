# GOAL
The goal of this repo is to provide a supercharger to agentic software development for employees of Larridin

# Features
**fma** command line tool
- The fma command line tool is a tool that should help enable maximum agentic coding in any code repo. 

fma Features
- When run in a directory it should check if a .fma file exists, if not it should create one
- fma build [number] should build the PRD that it finds at repo/prd/[number]\_prd\_description.md

# Design
- There should be a root directory that contains the folders (hopefully we can make a daemon soon to serve all this information)
- .database (this is a temporary solution until we can build a real server) - this should contain all the information about currently running servers and allow them orchestration powers
- .claude - all the files needed for claude to be as powerful as possible
- .codex  - all the files needed for codex to be as powerful as possible (I don't think they can always be in a hidden folder)

- There should also be a command xfma that is designed to be used by the agent to orchestrate with the .database
-

# When fma build [number] is run 
- this can be a bash command, use pwd as an argument
- It should look for the PRD that it finds at repo/prd/[number]\_prd\_description.md
- It should make a new worktree with all the superpower tools it needs, and then make an .xfma folder containing config about it making the change
- It should then boot up the agent in that directory with a script telling it to execute the PRD until it solves the issue set out it in
- Then it should call xfma to let the orchestrator know that it needs a review
- A fresh agent is then triggered to review the worktree and the git diff and the prd on the worktree
- After that agent is done it calls xfma reviewed and then it goes back to the first agent, who is also in charge of updating the prd
- They keep going back and forth until the judge agent calls xfma LGTM which then causes a PR to pushed from that worktree to the upstream branch

# Functions Needed
- create the new worktree from the PRD (repo-prdname-timestamp-claude)
- copy all the super charger files to the new worktree
- copy the .env to the worktree?
- xfma command
    - adds all changes and commits with empty message
    - Check PWD xfma for config.json
    - parse it
    - pass it to repo_called_xfma.py (which runs in $LAMP_HOME)
    - repo_called_xfma.py looks at config.json for worktree name
    - checks state in .database for that worktree
    - starts new agent in that repo depending on the state it sees

    - once agent calls xfma LGTM when state='judge',
    - we analyze the PRD and total gitdiff of the worktree, generate good commit message and push to make PR
