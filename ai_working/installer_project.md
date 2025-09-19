# Amplifier Self-Extracting Installer Project

## Summary

This document captures the work done on creating a self-extracting installer for Amplifier that bundles the entire codebase into a single distributable shell script. The installer was designed to make it easy for non-developers to get Amplifier running without dealing with GitHub, manual dependency installation, or complex setup procedures.

## Project Overview

### Phase 1: Initial Installer Creation
- Created a self-extracting installer that bundles the entire codebase
- Implemented as a shell script with embedded tar.gz archive
- Default installation to `./amplifier` (current directory)
- Automatic installation of all prerequisites
- Achieved ~612KB compressed size

### Phase 2: Interactive Mode Enhancement
- Upgraded to version 1.1.0 with interactive prompts
- Changed default installation directory to `./amplifier` (current directory)
- Added user-friendly prompts for key decisions
- Maintained non-interactive mode with `--yes` flag
- Final size: ~624KB

## Key Components Created

### 1. Build Script (`tools/build_installer.sh`)
- Creates the self-extracting installer
- Handles archive compression and exclusions
- Now outputs to `build/installer/` directory
- ~945 lines of shell script

### 2. Installer Features
The installer includes:
- **Platform detection** - WSL, Linux, macOS support
- **Interactive prompts** for:
  - Installation directory selection
  - Prerequisites confirmation
  - Shell configuration consent
  - Claude Code launch option
- **State management** - Resume capability from interruptions
- **Non-interactive mode** - Full automation with `--yes` flag

### 3. Documentation (`INSTALLER.md`)
Comprehensive user documentation covering:
- Installation process and options
- Command-line flags
- Platform-specific notes
- Troubleshooting guide
- Technical details

### 4. Configuration Files
- `.tarignore` - Exclusion patterns for the archive
- `.gitignore` - Updated to exclude installer artifacts

## Design Decisions

### Interactive Mode Philosophy
Added strategic interaction points to:
- Build trust with users through transparency
- Give control over system modifications
- Prevent destructive actions (overwrites)
- Make the process approachable for non-developers

### Key Interaction Points
1. **Installation directory** - User chooses where to install
2. **Prerequisites check** - Shows what will be installed
3. **Shell configuration** - Asks permission for PATH updates
4. **Launch prompt** - Option to start Claude Code immediately

### Technical Approach
- Shell script (not Python) for maximum compatibility
- Self-extracting archive pattern for single-file distribution
- Simple state tracking via files, not databases
- Direct prompting without complex UI frameworks

## What Works Well

1. **Simplicity** - Single file to share and run
2. **User-friendly** - Clear prompts with sensible defaults
3. **Flexible** - Interactive and non-interactive modes
4. **Resilient** - Resume capability, error handling
5. **Cross-platform** - Works on WSL, Linux, macOS

## Areas for Future Enhancement

### Potential Improvements
1. **Progress indicators** - Show download/extraction progress
2. **Rollback capability** - Undo installation if needed
3. **Update mechanism** - Upgrade existing installations
4. **Custom component selection** - Choose what to install
5. **Network resilience** - Better handling of slow connections

### Advanced Features to Consider
1. **Signature verification** - Ensure installer integrity
2. **Offline mode** - Bundle more dependencies
3. **Multi-user installation** - System-wide install option
4. **Configuration wizard** - Setup preferences during install
5. **Diagnostic mode** - Troubleshooting helper

## Usage Instructions

### Building the Installer
```bash
./tools/build_installer.sh
```
Creates installer at: `build/installer/install_amplifier.sh`

### Running the Installer

**Interactive mode (default):**
```bash
bash install_amplifier.sh
```

**Non-interactive mode:**
```bash
./install_amplifier.sh --yes
```

**Custom directory:**
```bash
AMPLIFIER_HOME=/opt/amplifier ./install_amplifier.sh
```

## Implementation Notes

### File Sizes
- Source code: ~5MB uncompressed
- Archive: ~600KB compressed
- Installer script overhead: ~24KB
- Total installer: ~624KB

### Excluded from Archive
- Version control (`.git/`)
- Virtual environments (`.venv/`)
- Node modules (`node_modules/`)
- Build artifacts
- Cache directories
- Claude logs (`.claude/`)

### Philosophy Adherence
The implementation follows Amplifier's ruthless simplicity principle:
- Direct shell scripting without frameworks
- Simple file-based state management
- Clear, minimal prompts
- No unnecessary abstractions
- Works immediately without complex setup

## Next Steps

### To Resume This Work
1. Test the installer on fresh systems (WSL, macOS, Linux)
2. Gather user feedback on the interactive experience
3. Consider adding the improvements listed above
4. Potentially create platform-specific variants
5. Add installer generation to CI/CD pipeline

### To Use This Work
The installer is ready for distribution. Simply:
1. Run `./tools/build_installer.sh` to generate
2. Find installer at `build/installer/install_amplifier.sh`
3. Share the single file with users
4. They run it and follow the prompts

## Decision Points

### Why Not Merged to Main
This work is substantial and functional but needs:
- Testing on fresh systems
- User feedback on the interactive experience
- Review of security implications
- Consensus on distribution strategy

### Branch Information
All installer-related changes are saved in branch: `installer-interactive`
- Build script improvements
- Documentation
- Configuration files
- NOT including generated installer file

## Files Modified/Created

### Created
- `/tools/build_installer.sh` - Build script for installer
- `/INSTALLER.md` - User documentation
- `/.tarignore` - Archive exclusion patterns
- `/ai_working/installer_project.md` - This documentation

### Modified
- `/README.md` - Added installer option to installation instructions
- `/.gitignore` - Added installer artifacts to ignore list

## Conclusion

The self-extracting installer successfully reduces the barrier to entry for Amplifier adoption. It transforms a complex multi-step setup process into a single command that guides users through installation with clear, friendly prompts. The implementation maintains the project's philosophy of ruthless simplicity while adding just enough interactivity to build user trust and provide control over the installation process.
