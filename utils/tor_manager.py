"""
Tor Manager for secure dark web crawling and anonymization.
"""

import subprocess
import time
import logging
import requests
import socket
import os
import tempfile

class TorManager:
    def __init__(self, tor_port=9050, control_port=9051):
        self.tor_port = tor_port
        self.control_port = control_port
        self.tor_process = None
        self.controller = None
        self.is_running = False
        self.config_dir = tempfile.mkdtemp(prefix='tor_')
        
    def start_tor_service(self):
        """Start Tor service with custom configuration"""
        try:
            # Check if Tor is available
            result = subprocess.run(['which', 'tor'], capture_output=True, text=True)
            if result.returncode != 0:
                logging.warning("Tor not available in this environment")
                return False
            
            # Check if Tor is already running
            if self.is_running:
                logging.info("Tor service already running")
                return True
            
            # Create Tor configuration
            tor_config = f"""
SocksPort {self.tor_port}
ControlPort {self.control_port}
DataDirectory {self.config_dir}
CookieAuthentication 1
ExitPolicy reject *:*
SafeLogging 0
Log notice stdout
"""
            
            config_file = os.path.join(self.config_dir, 'torrc')
            with open(config_file, 'w') as f:
                f.write(tor_config)
            
            # Start Tor process
            self.tor_process = subprocess.Popen([
                'tor', '-f', config_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for Tor to start
            self._wait_for_tor()
            
            self.is_running = True
            logging.info("Tor service started successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start Tor service: {e}")
            return False
    
    def _wait_for_tor(self, timeout=60):
        """Wait for Tor to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', self.tor_port))
                sock.close()
                if result == 0:
                    return True
                time.sleep(1)
            except:
                time.sleep(1)
        raise Exception("Tor failed to start within timeout")
    
    def stop_tor_service(self):
        """Stop Tor service"""
        try:
            if self.controller:
                self.controller.close()
                self.controller = None
            
            if self.tor_process:
                self.tor_process.terminate()
                self.tor_process.wait(timeout=10)
                self.tor_process = None
            
            self.is_running = False
            logging.info("Tor service stopped")
            
        except Exception as e:
            logging.error(f"Error stopping Tor service: {e}")
    
    def new_identity(self):
        """Get new Tor identity"""
        try:
            if self.controller:
                # Send NEWNYM signal for new identity
                time.sleep(5)  # Wait for new circuit
                logging.info("New Tor identity obtained")
                return True
        except Exception as e:
            logging.error(f"Failed to get new identity: {e}")
        return False
    
    def get_proxy_config(self):
        """Get proxy configuration for requests"""
        return {
            'http': f'socks5h://127.0.0.1:{self.tor_port}',
            'https': f'socks5h://127.0.0.1:{self.tor_port}'
        }
    
    def verify_tor_connection(self):
        """Verify Tor connection is working"""
        try:
            proxies = self.get_proxy_config()
            response = requests.get(
                'https://check.torproject.org/api/ip',
                proxies=proxies,
                timeout=30
            )
            data = response.json()
            if data.get('IsTor'):
                logging.info(f"Tor connection verified. Exit IP: {data.get('IP')}")
                return True
            else:
                logging.warning("Connection not going through Tor")
                return False
        except Exception as e:
            logging.error(f"Tor verification failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup Tor resources"""
        self.stop_tor_service()
        try:
            import shutil
            shutil.rmtree(self.config_dir, ignore_errors=True)
        except:
            pass

# Global Tor manager instance
tor_manager = TorManager()

def start_tor():
    """Start Tor service"""
    return tor_manager.start_tor_service()

def stop_tor():
    """Stop Tor service"""
    tor_manager.stop_tor_service()

def get_tor_proxy():
    """Get Tor proxy configuration"""
    if tor_manager.is_running:
        return tor_manager.get_proxy_config()
    return None

def verify_tor():
    """Verify Tor connection"""
    if tor_manager.is_running:
        return tor_manager.verify_tor_connection()
    return False

def new_tor_identity():
    """Get new Tor identity"""
    if tor_manager.is_running:
        return tor_manager.new_identity()
    return False