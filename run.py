#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import psutil
import signal
from subprocess import Popen, PIPE
import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def install_dependencies():
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def kill_process_on_port(port):
    if not is_port_in_use(port):
        print(f"Port {port} is free")
        return
    
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    print(f"Killing process {proc.pid} on port {port}")
                    os.kill(proc.pid, signal.SIGTERM)
                    time.sleep(1)  # Give the process time to terminate
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

def run_flask_app():
    port = int(os.getenv('PORT', 5001))
    
    # Kill any process running on the port
    kill_process_on_port(port)
    
    # Double check if port is free
    if is_port_in_use(port):
        print(f"Port {port} is still in use. Please free up the port manually.")
        sys.exit(1)
    
    # Set Flask development mode
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    print(f"Starting Flask app on port {port}...")
    try:
        # Import and run the Flask app
        from app import app
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # First install dependencies
    install_dependencies()
    
    # Then run the Flask app
    run_flask_app()
