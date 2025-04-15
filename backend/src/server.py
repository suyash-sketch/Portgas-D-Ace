import asyncio
import websockets
import json
from urllib.parse import urlparse, parse_qs
from game_manager import GameManager
import socket

# Initialize Game Manager
game_manager = GameManager()

async def connection_handler(websocket):
    """Handles new WebSocket connections by creating a user object."""
    # Extract query parameters from the websocket path
    path = websocket.path if hasattr(websocket, 'path') else '/'
    query = parse_qs(urlparse(path).query)
    token = query.get('token', [None])[0]
    
    if not token:
        await websocket.close(1008, "No token provided")
        return
    
    # Create a user dictionary with the token and websocket
    user = {
        'id': token,
        'websocket': websocket
    }
    
    # Pass the user object to the game manager
    await game_manager.add_user(user)

async def start_server():
    """Starts the WebSocket server on 0.0.0.0:8080."""
    server = await websockets.serve(connection_handler, "0.0.0.0", 8080)
    
    # Print your local IP address for clients to connect
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"WebSocket Server started on ws://{local_ip}:8080")
    
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_server())
