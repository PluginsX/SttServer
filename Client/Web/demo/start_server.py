import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 9999
DEMO_DIR = Path(__file__).parent
LIB_DIR = DEMO_DIR.parent / "lib"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DEMO_DIR, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def translate_path(self, path):
        path = super().translate_path(path)
        
        if path.startswith(str(DEMO_DIR)):
            rel_path = Path(path).relative_to(DEMO_DIR)
            
            if str(rel_path).startswith('lib/'):
                lib_file = LIB_DIR / rel_path.relative_to('lib')
                if lib_file.exists():
                    return str(lib_file)
        
        return path

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print(f"Demo page: http://localhost:{PORT}/index.html")
        print("Press Ctrl+C to stop the server")
        
        webbrowser.open(f"http://localhost:{PORT}/index.html")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")

if __name__ == "__main__":
    start_server()
