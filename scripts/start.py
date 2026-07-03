#!/usr/bin/env python3
"""
MetaPilot AI - Start Script

Starts the MetaPilot AI backend server.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(
        description='Start MetaPilot AI backend server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start.py                    # Start with default settings
  python scripts/start.py --debug          # Start in debug mode
  python scripts/start.py --host 0.0.0.0   # Start with specific host
  python scripts/start.py --port 8080      # Start with specific port
        """
    )
    
    parser.add_argument(
        '--host', '-H',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='Port to listen on (default: 8000)'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--reload', '-r',
        action='store_true',
        help='Enable auto-reload on code changes'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='',
        help='Path to a custom configuration file'
    )
    
    parser.add_argument(
        '--env', '-e',
        default='development',
        choices=['development', 'staging', 'production'],
        help='Environment mode (default: development)'
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ['METAPILOT_HOST'] = args.host
    os.environ['METAPILOT_PORT'] = str(args.port)
    os.environ['METAPILOT_ENV'] = args.env
    
    if args.debug:
        os.environ['METAPILOT_DEBUG'] = 'true'
    
    if args.reload:
        os.environ['METAPILOT_RELOAD'] = 'true'
    
    # Start the server
    print(f"Starting MetaPilot AI server on {args.host}:{args.port}")
    print(f"Environment: {args.env}")
    print(f"Debug mode: {args.debug}")
    print(f"Auto-reload: {args.reload}")
    print(f"Log level: {args.log_level}")
    
    if args.config:
        print(f"Config file: {args.config}")
    
    print("\nPress Ctrl+C to stop the server\n")
    
    # Change to project root
    os.chdir(project_root)
    
    # Run the main application
    try:
        from backend.main import app
        import uvicorn
        
        uvicorn.run(
            'backend.main:app',
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level.lower(),
            env_file=args.config if args.config else None
        )
    except ImportError as e:
        print(f"Error: Could not import the application: {e}")
        print("Make sure you're running from the project root directory.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
