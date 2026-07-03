#!/usr/bin/env python3
"""
MetaPilot AI - Development Script

Starts both backend and frontend development servers.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_backend():
    """Start the backend server."""
    print("Starting backend server...")
    
    backend_process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'backend.main:app', 
         '--host', '127.0.0.1', 
         '--port', '8000',
         '--reload'],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, 'PYTHONPATH': str(project_root)}
    )
    
    return backend_process


def run_frontend():
    """Start the frontend development server."""
    print("Starting frontend development server...")
    
    frontend_process = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd=project_root / 'frontend',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, 'VITE_API_URL': 'http://localhost:8000'}
    )
    
    return frontend_process


def main():
    print("=" * 60)
    print("MetaPilot AI - Development Mode")
    print("=" * 60)
    print()
    print("Starting both backend and frontend servers...")
    print()
    
    # Start backend
    backend = run_backend()
    
    # Give backend a moment to start
    time.sleep(2)
    
    # Start frontend
    frontend = run_frontend()
    
    print()
    print("=" * 60)
    print("Development servers are running:")
    print("  Backend: http://localhost:8000")
    print("  Frontend: http://localhost:3000")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop both servers")
    print()
    
    # Function to handle termination
    def handle_terminate(signum, frame):
        print("\nShutting down development servers...")
        
        # Terminate both processes
        if backend.poll() is None:
            backend.terminate()
        if frontend.poll() is None:
            frontend.terminate()
        
        # Wait for processes to finish
        backend.wait(timeout=5)
        frontend.wait(timeout=5)
        
        print("Development servers stopped")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_terminate)
    signal.signal(signal.SIGTERM, handle_terminate)
    
    # Wait for processes to finish
    try:
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            backend_alive = backend.poll() is None
            frontend_alive = frontend.poll() is None
            
            if not backend_alive and not frontend_alive:
                print("\nBoth servers have stopped")
                break
            elif not backend_alive:
                print("\nBackend server has stopped")
                frontend.terminate()
                frontend.wait()
                break
            elif not frontend_alive:
                print("\nFrontend server has stopped")
                backend.terminate()
                backend.wait()
                break
    except KeyboardInterrupt:
        handle_terminate(signal.SIGINT, None)


if __name__ == '__main__':
    main()
