#!/bin/bash
# Master script to run all Amplifier feature demos

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║             🚀 AMPLIFIER - COMPLETE FEATURE TOUR 🚀               ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "This will show you all 6 major Amplifier features:"
echo "  1. Memory System"
echo "  2. Semantic Search"
echo "  3. Knowledge Extraction"
echo "  4. Specialized AI Agents"
echo "  5. Parallel Worktrees"
echo "  6. Knowledge Graph"
echo ""
read -p "Press ENTER to start the tour, or Ctrl+C to exit..."

# Feature 1: Memory System
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "📍 FEATURE 1/6: Memory System"
echo "════════════════════════════════════════════════════════════════════"
python feature_demo_1_memory.py 2>&1 | grep -v "^INFO:" | grep -v "UserWarning" | grep -v "warnings.warn"
echo ""
read -p "Press ENTER to continue to next feature..."

# Feature 2: Semantic Search
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "📍 FEATURE 2/6: Semantic Search"
echo "════════════════════════════════════════════════════════════════════"
python feature_demo_2_search.py 2>&1 | grep -v "^INFO:" | grep -v "UserWarning" | grep -v "Batches:" | grep -v "warnings.warn" | grep -v "NumExpr" | grep -v "torchvision"
echo ""
read -p "Press ENTER to continue to next feature..."

# Feature 3: Knowledge Extraction
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "📍 FEATURE 3/6: Knowledge Extraction"
echo "════════════════════════════════════════════════════════════════════"
python feature_demo_3_extraction.py 2>&1 | grep -v "^INFO:" | grep -v "UserWarning" | grep -v "warnings.warn"
echo ""
read -p "Press ENTER to continue to next feature..."

# Feature 4: Specialized Agents
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "📍 FEATURE 4/6: Specialized AI Agents"
echo "════════════════════════════════════════════════════════════════════"
python feature_demo_4_agents.py
echo ""
read -p "Press ENTER to continue to next feature..."

# Feature 5: Worktrees
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "📍 FEATURE 5/6: Parallel Worktrees"
echo "════════════════════════════════════════════════════════════════════"
python feature_demo_5_worktrees.py
echo ""
read -p "Press ENTER to continue to final feature..."

# Feature 6: Knowledge Graph
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "📍 FEATURE 6/6: Knowledge Graph & Synthesis"
echo "════════════════════════════════════════════════════════════════════"
python feature_demo_6_knowledge_graph.py
echo ""

# Completion
echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║                    🎉 TOUR COMPLETE! 🎉                           ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "You've seen all 6 major Amplifier features!"
echo ""
echo "📚 What's next?"
echo "  • Read: ALL_FEATURES_SUMMARY.md (complete reference)"
echo "  • Read: QUICKSTART.md (getting started guide)"
echo "  • Run: make help (see all available commands)"
echo "  • Start: claude (begin using Amplifier)"
echo ""
echo "🔍 Rerun specific demos:"
echo "  python feature_demo_1_memory.py"
echo "  python feature_demo_2_search.py"
echo "  python feature_demo_3_extraction.py"
echo "  python feature_demo_4_agents.py"
echo "  python feature_demo_5_worktrees.py"
echo "  python feature_demo_6_knowledge_graph.py"
echo ""
echo "Happy amplifying! 🚀"
echo ""
