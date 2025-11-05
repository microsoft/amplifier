# AI Working Directory

The purpose of this directory is to provide a working space for AI-tools to create, modify, and execute plans for implementing changes in a project. It serves as a collaborative space where AI can generate plans, execute them, and document the process for future reference.

This directory name was chosen instead of a dot-prefixed name to allow it to be easily referenced inside AI-tools that otherwise ignore dot-prefixed directories, such as Claude Code.

For temporary files that you do not want checked in, use the `tmp` subdirectory.

This allows for a choice between storing files in a version-controlled manner (for lifetime of branch and clearing before PR, or longer lived if needed) or keeping them temporary and not checked in.
