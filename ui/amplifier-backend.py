#!/usr/bin/env python3
"""
Amplifier UI Backend Integration
Demonstrates how the UI would integrate with actual Microsoft Amplifier sessions
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
AMPLIFIER_PATH = "/home/ubuntu/amplifier"
SESSIONS_DIR = "/tmp/amplifier-sessions"
WORKTREE_BASE = "/tmp/amplifier-worktrees"

# Ensure directories exist
Path(SESSIONS_DIR).mkdir(exist_ok=True)
Path(WORKTREE_BASE).mkdir(exist_ok=True)

class AmplifierSession:
    def __init__(self, session_id, name, project_path):
        self.session_id = session_id
        self.name = name
        self.project_path = project_path
        self.worktree = f"session-{session_id}"
        self.agents = []
        self.status = "idle"
        self.cost = 0.0
        self.tokens = 0
        self.requests = 0
        self.start_time = time.time()
        self.messages = []
        
    def to_dict(self):
        return {
            "id": self.session_id,
            "name": self.name,
            "status": self.status,
            "agents": self.agents,
            "cost": self.cost,
            "duration": int((time.time() - self.start_time) / 60),
            "worktree": self.worktree,
            "lastActivity": "Just now",
            "projectPath": self.project_path,
            "tokens": self.tokens,
            "requests": self.requests,
            "messages": self.messages
        }

# In-memory session storage (would be database in production)
sessions = {}

def run_amplifier_command(command, cwd=None):
    """Execute an Amplifier command and return the result"""
    try:
        if cwd is None:
            cwd = AMPLIFIER_PATH
            
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def create_worktree(session_id, branch_name):
    """Create a git worktree for the session"""
    worktree_path = f"{WORKTREE_BASE}/{branch_name}"
    
    # Create worktree using Amplifier's create_worktree.py script
    if os.path.exists(f"{AMPLIFIER_PATH}/tools/create_worktree.py"):
        command = f"python3 tools/create_worktree.py {branch_name} {worktree_path}"
        result = run_amplifier_command(command)
        
        if result["success"]:
            return worktree_path
        else:
            print(f"Failed to create worktree: {result['stderr']}")
            return None
    else:
        # Fallback: create worktree manually
        command = f"git worktree add {worktree_path} -b {branch_name}"
        result = run_amplifier_command(command)
        
        if result["success"]:
            return worktree_path
        else:
            print(f"Failed to create worktree: {result['stderr']}")
            return None

def start_amplifier_session(session):
    """Start an actual Amplifier session"""
    try:
        # Create worktree for the session
        worktree_path = create_worktree(session.session_id, session.worktree)
        
        if not worktree_path:
            return False
            
        # Initialize Amplifier session
        session_file = f"{SESSIONS_DIR}/{session.session_id}.json"
        session_data = {
            "session_id": session.session_id,
            "name": session.name,
            "worktree_path": worktree_path,
            "project_path": session.project_path,
            "agents": session.agents,
            "created_at": time.time()
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        session.status = "active"
        return True
        
    except Exception as e:
        print(f"Failed to start Amplifier session: {e}")
        return False

def deploy_agent_to_session(session, agent_id):
    """Deploy an agent to an Amplifier session"""
    try:
        # Add agent to session
        if agent_id not in session.agents:
            session.agents.append(agent_id)
            
        # Update session file
        session_file = f"{SESSIONS_DIR}/{session.session_id}.json"
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
            session_data["agents"] = session.agents
            session_data["updated_at"] = time.time()
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        # In a real implementation, this would start the agent process
        print(f"Agent {agent_id} deployed to session {session.session_id}")
        return True
        
    except Exception as e:
        print(f"Failed to deploy agent: {e}")
        return False

@app.route('/api/amplifier/sessions', methods=['POST'])
def create_session():
    """Create a new Amplifier session"""
    try:
        data = request.json
        session_id = str(int(time.time() * 1000))  # Use timestamp as ID
        
        session = AmplifierSession(
            session_id=session_id,
            name=data.get('name', f'Session {len(sessions) + 1}'),
            project_path=data.get('projectPath', AMPLIFIER_PATH)
        )
        
        # Start the actual Amplifier session
        if start_amplifier_session(session):
            sessions[session_id] = session
            return jsonify(session.to_dict()), 201
        else:
            return jsonify({"error": "Failed to start Amplifier session"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/amplifier/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions"""
    return jsonify([session.to_dict() for session in sessions.values()])

@app.route('/api/amplifier/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get a specific session"""
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
        
    return jsonify(sessions[session_id].to_dict())

@app.route('/api/amplifier/sessions/<session_id>/agents', methods=['POST'])
def deploy_agent(session_id):
    """Deploy an agent to a session"""
    try:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
            
        data = request.json
        agent_id = data.get('agentId')
        
        if not agent_id:
            return jsonify({"error": "Agent ID required"}), 400
            
        session = sessions[session_id]
        
        if deploy_agent_to_session(session, agent_id):
            return jsonify(session.to_dict())
        else:
            return jsonify({"error": "Failed to deploy agent"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/amplifier/sessions/<session_id>/chat', methods=['POST'])
def send_message(session_id):
    """Send a message to the session agents"""
    try:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
            
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({"error": "Message required"}), 400
            
        session = sessions[session_id]
        
        # Add user message
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": time.strftime("%H:%M:%S")
        }
        session.messages.append(user_message)
        
        # Simulate agent processing (in real implementation, this would call Amplifier agents)
        time.sleep(1)  # Simulate processing time
        
        # Generate agent response
        agent_response = {
            "role": "assistant",
            "content": f"I'll help you with: {message}. Let me coordinate with the active agents ({', '.join(session.agents)}) to provide the best solution.",
            "timestamp": time.strftime("%H:%M:%S")
        }
        session.messages.append(agent_response)
        
        # Update session metrics
        session.requests += 1
        session.tokens += len(message.split()) * 4  # Rough token estimation
        session.cost += 0.01  # Rough cost estimation
        
        return jsonify({"response": agent_response["content"]})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/amplifier/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session"""
    try:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
            
        session = sessions[session_id]
        
        # Clean up worktree
        worktree_path = f"{WORKTREE_BASE}/{session.worktree}"
        if os.path.exists(worktree_path):
            command = f"git worktree remove {worktree_path}"
            run_amplifier_command(command)
            
        # Clean up session file
        session_file = f"{SESSIONS_DIR}/{session_id}.json"
        if os.path.exists(session_file):
            os.remove(session_file)
            
        # Remove from memory
        del sessions[session_id]
        
        return jsonify({"message": "Session deleted successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/amplifier/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "amplifier_path": AMPLIFIER_PATH,
        "amplifier_available": os.path.exists(AMPLIFIER_PATH),
        "active_sessions": len(sessions)
    })

if __name__ == '__main__':
    print("🚀 Starting Amplifier UI Backend...")
    print(f"📁 Amplifier Path: {AMPLIFIER_PATH}")
    print(f"💾 Sessions Directory: {SESSIONS_DIR}")
    print(f"🌳 Worktree Base: {WORKTREE_BASE}")
    print("🌐 Server running on http://localhost:5000")
    
    # Check if Amplifier is available
    if os.path.exists(AMPLIFIER_PATH):
        print("✅ Microsoft Amplifier detected")
    else:
        print("⚠️  Microsoft Amplifier not found - running in demo mode")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
