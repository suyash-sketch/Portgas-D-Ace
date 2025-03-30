import asyncio
import websockets
from game_manager import GameManager

# Initialize Game Manager
game_manager = GameManager()

async def connection_handler(websocket):
    """Handles new WebSocket connections."""
    await game_manager.add_user(websocket)

async def start_server():
    """Starts the WebSocket server on localhost:8080."""
    server = await websockets.serve(connection_handler, "localhost", 8080)
    print("WebSocket Server started on ws://localhost:8080")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_server())
