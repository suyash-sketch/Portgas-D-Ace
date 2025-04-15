import asyncio
import websockets
import json
import os
from urllib.parse import parse_qs, urlparse
from game_manager import GameManager
from auth import Auth, extract_auth_user
from socket_manager import socket_manager
from aiohttp import web

# Initialize game manager and auth
game_manager = GameManager()
auth = Auth()

# Get the absolute path to the frontend directoryz
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'src')

async def handle_static_file(request):
    try:
        path = request.path
        if path == '/':
            path = '/index.html'  # Serve game.html as the main page
            
        file_path = os.path.join(FRONTEND_DIR, path.lstrip('/'))
        if os.path.exists(file_path):
            response = web.FileResponse(file_path)
            if file_path.endswith('.html'):
                response.headers['Content-Type'] = 'text/html'
            elif file_path.endswith('.css'):
                response.headers['Content-Type'] = 'text/css'
            elif file_path.endswith('.js'):
                response.headers['Content-Type'] = 'application/javascript'
            elif file_path.endswith('.ico'):
                response.headers['Content-Type'] = 'image/x-icon'
            return response
        print(f"File not found: {file_path}")  # Add debug logging
        return web.Response(status=404)
    except Exception as e:
        print(f"Error serving static file: {e}")
        return web.Response(status=500)

# In main.py, update the websocket_handler function

async def websocket_handler(websocket):
    """Handle WebSocket connections."""
    user = None
    try:
        # Get the path from the websocket
        path = websocket.path if hasattr(websocket, 'path') else '/ws'
        print(f"New WebSocket connection request from: {path}")
        
        # Extract token from query parameters
        query = parse_qs(urlparse(path).query)
        token = query.get('token', [None])[0]
        
        print(f"Received token: {token}")  # Debug log
        
        if not token:
            print("No token provided")
            await websocket.close(1008, "No token provided")
            return
            
        # For testing, accept any token that starts with 'test-token-'
        if not token.startswith('test-token-'):
            print("Invalid token format")
            await websocket.close(1008, "Invalid token")
            return
            
        # Create a simple user object for testing
        user = {
            'id': token,
            'websocket': websocket
        }
            
        # Add user to game manager
        game_manager.add_user(user)
        print(f"User {user['id']} connected successfully")
        
        # Send initial connection success message
        await websocket.send(json.dumps({
            "type": "CONNECTION_SUCCESS",
            "message": "Connected to server successfully"
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"Received message from {user['id']}: {data}")
                await game_manager.handle_message(user, data)
            except json.JSONDecodeError:
                print(f"Invalid JSON received from {user['id']}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed for user {user.get('id', 'unknown')}: {e.code} - {e.reason}")
        if user:
            game_manager.remove_user(websocket)
    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
        if user:
            game_manager.remove_user(websocket)

from aiohttp import web_ws

async def websocket_aiohttp_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    class WSWrapper:
        def __init__(self, ws, path):
            self._ws = ws
            self.path = path
        async def send(self, data):
            await self._ws.send_str(data)
        async def __aiter__(self):
            async for msg in self._ws:
                if msg.type == web_ws.WSMsgType.TEXT:
                    yield msg.data
        async def close(self, code=1000, reason=''):
            await self._ws.close(code=code, message=reason.encode())

    wrapped = WSWrapper(ws, request.path_qs)
    await websocket_handler(wrapped)
    return ws


async def start_websocket_server():
    """Start the WebSocket server."""
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8080))
    
    # Use legacy API for websockets 15.0+
    from websockets.legacy.server import serve
    server = await serve(
        websocket_handler,
        '0.0.0.0',  # Listen on all interfaces
        port,
        # Add these options for ngrok compatibility
        ping_interval=20,
        ping_timeout=20,
        close_timeout=10,
        max_size=2**20,
        max_queue=2**5
    )
    print(f"🚀 Starting WebSocket server on port {port}...")
    return server

async def start_http_server():
    """Start the HTTP + WebSocket server on a single port."""
    app = web.Application()
    app.router.add_get('/ws', websocket_aiohttp_handler)  # ✅ Updated handler for WebSocket
    app.router.add_get('/{tail:.*}', handle_static_file)  # Static file handler

    runner = web.AppRunner(app)
    await runner.setup()

    # Serve everything on one port (8080 or whatever ngrok exposes)
    port = int(os.environ.get('PORT', 8080))

    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🚀 Starting HTTP+WebSocket server on port {port}...")
    return runner

async def main():
    # Start both servers
    # websocket_server = await start_websocket_server()
    # http_server = await start_http_server()
    
    # try:
    #     # Keep the servers running
    #     await websocket_server.wait_closed()
    # except KeyboardInterrupt:
    #     print("\nShutting down servers...")
    #     websocket_server.close()
    #     await http_server.cleanup()

    http_server = await start_http_server()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        await http_server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())