#!/usr/bin/env node

/**
 * Design Token Validator
 *
 * Scans codebase for CSS variable usage and validates that all variables
 * are properly defined in globals.css
 *
 * Usage: node scripts/validate-design-tokens.js
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

// Files and directories to ignore
const IGNORE_PATTERNS = [
  'node_modules',
  '.next',
  'dist',
  'build',
  '.git',
  'scripts', // Don't scan this script itself
];

// CSS variable pattern: var(--variable-name)
const CSS_VAR_PATTERN = /var\(--([a-zA-Z0-9-]+)\)/g;

// File extensions to scan
const SCAN_EXTENSIONS = ['.tsx', '.ts', '.jsx', '.js', '.css', '.scss'];

/**
 * Read and parse globals.css to extract defined CSS variables
 */
function getDefinedVariables(globalsPath) {
  if (!fs.existsSync(globalsPath)) {
    console.error(`${colors.red}Error: globals.css not found at ${globalsPath}${colors.reset}`);
    process.exit(1);
  }

  const content = fs.readFileSync(globalsPath, 'utf-8');
  const definedVars = new Set();

  // Match CSS variable definitions: --variable-name: value;
  const definePattern = /--([a-zA-Z0-9-]+)\s*:/g;
  let match;

  while ((match = definePattern.exec(content)) !== null) {
    definedVars.add(match[1]);
  }

  return definedVars;
}

/**
 * Recursively scan directory for files
 */
function scanDirectory(dir, files = []) {
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    // Skip ignored patterns
    if (IGNORE_PATTERNS.some(pattern => fullPath.includes(pattern))) {
      continue;
    }

    if (stat.isDirectory()) {
      scanDirectory(fullPath, files);
    } else if (SCAN_EXTENSIONS.some(ext => item.endsWith(ext))) {
      files.push(fullPath);
    }
  }

  return files;
}

/**
 * Extract CSS variables used in a file
 */
function extractVariablesFromFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const variables = new Map(); // variable -> [line numbers]

  const lines = content.split('\n');
  lines.forEach((line, index) => {
    let match;
    while ((match = CSS_VAR_PATTERN.exec(line)) !== null) {
      const varName = match[1];
      if (!variables.has(varName)) {
        variables.set(varName, []);
      }
      variables.get(varName).push(index + 1); // 1-indexed line numbers
    }
  });

  return variables;
}

/**
 * Main validation logic
 */
function validateDesignTokens() {
  console.log(`${colors.bold}${colors.cyan}Design Token Validator${colors.reset}\n`);

  const projectRoot = path.join(__dirname, '..');
  const globalsPath = path.join(projectRoot, 'app', 'globals.css');

  // Step 1: Get all defined variables from globals.css
  console.log(`${colors.blue}→${colors.reset} Reading defined variables from globals.css...`);
  const definedVars = getDefinedVariables(globalsPath);
  console.log(`  Found ${colors.green}${definedVars.size}${colors.reset} defined variables\n`);

  // Step 2: Scan all files for variable usage
  console.log(`${colors.blue}→${colors.reset} Scanning files for CSS variable usage...`);
  const files = scanDirectory(projectRoot);
  console.log(`  Scanning ${colors.green}${files.length}${colors.reset} files\n`);

  // Step 3: Extract and validate variables
  const undefinedVars = new Map(); // variable -> [{file, lines}]
  const definedUsage = new Map(); // variable -> count

  for (const file of files) {
    const fileVars = extractVariablesFromFile(file);

    for (const [varName, lines] of fileVars) {
      if (definedVars.has(varName)) {
        // Track usage of defined variables
        definedUsage.set(varName, (definedUsage.get(varName) || 0) + lines.length);
      } else {
        // Track undefined variables
        if (!undefinedVars.has(varName)) {
          undefinedVars.set(varName, []);
        }
        undefinedVars.get(varName).push({
          file: path.relative(projectRoot, file),
          lines,
        });
      }
    }
  }

  // Step 4: Report results
  console.log(`${colors.bold}Results:${colors.reset}\n`);

  if (undefinedVars.size === 0) {
    console.log(`${colors.green}✓ All CSS variables are properly defined!${colors.reset}\n`);

    // Show usage stats
    console.log(`${colors.bold}Usage Statistics:${colors.reset}`);
    const sortedUsage = Array.from(definedUsage.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    console.log(`  Top 10 most used variables:`);
    sortedUsage.forEach(([varName, count]) => {
      console.log(`    ${colors.cyan}--${varName}${colors.reset}: ${count} usages`);
    });
    console.log('');

    const unusedVars = Array.from(definedVars).filter(v => !definedUsage.has(v));
    if (unusedVars.length > 0) {
      console.log(`${colors.yellow}⚠ Warning: ${unusedVars.length} defined variables are unused${colors.reset}`);
      console.log('  Consider removing unused variables to keep the design system clean.');
      console.log('  Unused variables:');
      unusedVars.slice(0, 10).forEach(varName => {
        console.log(`    ${colors.yellow}--${varName}${colors.reset}`);
      });
      if (unusedVars.length > 10) {
        console.log(`    ... and ${unusedVars.length - 10} more`);
      }
      console.log('');
    }

    process.exit(0);
  } else {
    console.log(`${colors.red}✗ Found ${undefinedVars.size} undefined CSS variables${colors.reset}\n`);

    // Group by frequency
    const sortedUndefined = Array.from(undefinedVars.entries())
      .sort((a, b) => {
        const aCount = a[1].reduce((sum, loc) => sum + loc.lines.length, 0);
        const bCount = b[1].reduce((sum, loc) => sum + loc.lines.length, 0);
        return bCount - aCount;
      });

    sortedUndefined.forEach(([varName, locations]) => {
      const totalUsages = locations.reduce((sum, loc) => sum + loc.lines.length, 0);
      console.log(`${colors.red}--${varName}${colors.reset} (${totalUsages} usages)`);

      locations.forEach(({ file, lines }) => {
        const lineStr = lines.length === 1
          ? `line ${lines[0]}`
          : `lines ${lines.join(', ')}`;
        console.log(`  ${colors.magenta}${file}${colors.reset}:${lineStr}`);
      });
      console.log('');
    });

    console.log(`${colors.bold}Fix:${colors.reset}`);
    console.log(`Add the following variables to ${colors.cyan}app/globals.css${colors.reset}:\n`);

    sortedUndefined.forEach(([varName]) => {
      console.log(`  --${varName}: /* define value */;`);
    });
    console.log('');

    process.exit(1);
  }
}

// Run validator
try {
  validateDesignTokens();
} catch (error) {
  console.error(`${colors.red}Error: ${error.message}${colors.reset}`);
  process.exit(1);
}
