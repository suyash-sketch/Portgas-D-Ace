import asyncio
import websockets
import json
import os
from urllib.parse import parse_qs, urlparse
from game_manager import GameManager
from auth import Auth, extract_auth_user
from socket_manager import socket_manager
from aiohttp import web
from websockets.legacy.server import serve

# Initialize game manager and auth
game_manager = GameManager()
auth = Auth()

# Get the absolute path to the frontend directory
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
        
        # Parse query parameters
        query = parse_qs(urlparse(path).query)
        token = query.get('token', [None])[0]
        role = query.get('role', ['unknown'])[0]
        
        print(f"Received token: {token}, role: {role}")
        
        if not token:
            print("No token provided")
            await websocket.close(1008, "No token provided")
            return
        
        # Create a user object with token as game ID and role info
        user = {
            'id': token.split('-')[1] if '-' in token else token,  # Extract user ID part if using format
            'game_token': token,                                   # Full game token
            'role': role,                                          # creator or joiner
            'websocket': websocket
        }
        
        # Check if this is a game creator or joiner
        if role == 'creator':
            # This user is creating a new game, add to waiting list
            game_manager.add_creator(user, token)
            await websocket.send(json.dumps({
                "type": "CONNECTION_SUCCESS",
                "message": "Game created successfully. Waiting for opponent to join."
            }))
        elif role == 'joiner':
            # This user is joining an existing game
            joined = game_manager.add_joiner(user, token)
            if joined:
                await websocket.send(json.dumps({
                    "type": "CONNECTION_SUCCESS",
                    "message": "Successfully joined the game."
                }))
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Game not found or already full."
                }))
        else:
            # Legacy connection - use previous behavior
            game_manager.add_user(user)
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


async def start_websocket_server():
    server = await serve(
        websocket_handler,
        '0.0.0.0',  # Changed from 'localhost' to listen on all interfaces
        8080,
    )
    print("🚀 Starting WebSocket server on port 8080...")
    return server

async def start_http_server():
    app = web.Application()
    app.router.add_get('/{tail:.*}', handle_static_file)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8081)  # Changed from 'localhost'
    await site.start()
    print("🚀 Starting HTTP server on port 8081...")
    return runner

async def main():
    # Start both servers
    websocket_server = await start_websocket_server()
    http_server = await start_http_server()
    
    try:
        # Keep the servers running
        await websocket_server.wait_closed()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        websocket_server.close()
        await http_server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())