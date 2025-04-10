from flask import Flask, render_template, request
from flask_sock import Sock
import asyncio
from websocket_server import WebSocketServer
import socket

app = Flask(__name__, template_folder='../client/templates')
sock = Sock(app)
ws_server = WebSocketServer()

@app.route('/')
def index():
    return render_template('index.html')

@sock.route('/ws')
def websocket_route(ws):
    try:
        # Verify origin if needed
        if request.headers.get('Origin'):
            if not any(origin in request.headers['Origin'] for origin in ['localhost', '127.0.0.1']):
                return
        
        # Accept all WebSocket connections
        ws.headers = [
            ('Upgrade', 'websocket'),
            ('Connection', 'Upgrade'),
            ('Sec-WebSocket-Accept', '...'),
            ('Access-Control-Allow-Origin', '*'),
        ]
        
        asyncio.run(ws_server.register(ws))
    except Exception as e:
        print(f"WebSocket error: {e}")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"\nServer running on:")
    print(f"Local: http://localhost:5000")
    print(f"Network: http://{local_ip}:5000")
    print(f"WebSocket: ws://{local_ip}:5000/ws\n")
    
    # Run Flask development server
    app.run(host='0.0.0.0', port=5000)
