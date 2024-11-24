#!/usr/bin/env python3
import os
import sys
import psutil
import signal
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)

class ServerManager:
    def __init__(self, port=5001):
        self.port = port
        self.process = None
        self.logger = logging.getLogger(__name__)

    def install_dependencies(self):
        """Install or upgrade all required dependencies."""
        try:
            self.logger.info("Installing/upgrading dependencies...")
            requirements = [
                "flask==2.0.1",
                "python-dotenv==0.19.0",
                "openai==0.27.8",
                "python-crontab==2.7.1",
                "requests==2.26.0",
                "schedule==1.1.0",
                "flask-cors==3.0.10",
                "numpy==1.21.0",
                "psutil==5.9.5",
                "watchdog==3.0.0",
                "wikipedia-api==0.6.0",
                "beautifulsoup4==4.12.2",
                "newspaper3k==0.2.8"
            ]
            
            # Write requirements to file
            with open('requirements.txt', 'w') as f:
                f.write('\n'.join(requirements))
            
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            self.logger.info("Dependencies installed successfully!")
        except Exception as e:
            self.logger.error(f"Error installing dependencies: {e}")
            sys.exit(1)

    def kill_process_on_port(self):
        """Kill any process running on the specified port."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.connections():
                        if conn.laddr.port == self.port:
                            self.logger.info(f"Killing process {proc.pid} on port {self.port}")
                            os.kill(proc.pid, signal.SIGTERM)
                            time.sleep(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error killing process: {e}")

    def start_server(self):
        """Start the Flask server."""
        try:
            self.kill_process_on_port()
            self.logger.info(f"Starting server on port {self.port}...")
            
            # Set environment variables
            os.environ['FLASK_ENV'] = 'development'
            os.environ['FLASK_DEBUG'] = '1'
            
            # Start the server process
            self.process = subprocess.Popen(
                [sys.executable, 'app.py'],
                env=os.environ.copy()
            )
            
            self.logger.info("Server started successfully!")
            return True
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            return False

    def restart_server(self):
        """Restart the Flask server."""
        self.logger.info("Restarting server...")
        self.kill_process_on_port()
        return self.start_server()

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server_manager):
        self.server_manager = server_manager
        self.last_restart = datetime.now()
        self.cooldown = 2  # Cooldown period in seconds

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            now = datetime.now()
            if (now - self.last_restart).total_seconds() > self.cooldown:
                self.server_manager.restart_server()
                self.last_restart = now

def main():
    # Initialize server manager
    server_manager = ServerManager()
    
    # Install dependencies
    server_manager.install_dependencies()
    
    # Start server
    if not server_manager.start_server():
        sys.exit(1)
    
    # Set up file watcher
    event_handler = FileChangeHandler(server_manager)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        server_manager.kill_process_on_port()
    observer.join()

if __name__ == "__main__":
    main()
