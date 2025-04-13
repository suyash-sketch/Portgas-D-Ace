import asyncio
import websockets
import json
import random
import time
from urllib.parse import quote

# Generate two different tokens for the two players
TOKEN_1 = 'test-token-' + str(random.randint(1000, 9999))
TOKEN_2 = 'test-token-' + str(random.randint(1000, 9999))

async def connect_player(token, player_name):
    # Properly encode the token in the URL
    encoded_token = quote(token)
    uri = f'ws://localhost:8080?token={encoded_token}'  # Remove the /ws part
    print(f"\n{player_name} connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"{player_name} connected successfully")
            
            # Send INIT_GAME message
            await websocket.send(json.dumps({"type": "INIT_GAME"}))
            print(f"{player_name} sent INIT_GAME")
            
            # Wait for game assignment
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"{player_name} received: {data}")
                
                if data["type"] == "GAME_ASSIGNED":
                    role = data["role"]
                    print(f"{player_name} assigned role: {role}")
                    break
                elif data["type"] == "WAITING":
                    print(f"{player_name} waiting for opponent...")
                elif data["type"] == "error":
                    print(f"{player_name} received error: {data['message']}")
                    return
                elif data["type"] == "CONNECTION_SUCCESS":
                    print(f"{player_name} connection successful")
            
            # Wait for game to start
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"{player_name} received: {data}")
                
                if data["type"] == "GAME_JOINED":
                    print(f"{player_name} game started!")
                    break
            
            # Simulate moves
            moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "e1g1", "e8g8"]
            for move in moves:
                if (role == "white" and moves.index(move) % 2 == 0) or \
                   (role == "black" and moves.index(move) % 2 == 1):
                    print(f"\n{player_name} ({role}) making move: {move}")
                    await websocket.send(json.dumps({
                        "type": "MOVE",
                        "move": move,
                        "role": role
                    }))
                    time.sleep(1)  # Wait a bit between moves
                
                # Wait for move confirmation
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"{player_name} received: {data}")
                    
                    if data["type"] == "MOVE":
                        print(f"{player_name} received move: {data['move']}")
                        break
                    elif data["type"] == "error":
                        print(f"{player_name} received error: {data['message']}")
                        break
            
            # Wait for game end
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"{player_name} received: {data}")
                
                if data["type"] == "GAME_OVER":
                    print(f"{player_name} game ended!")
                    break
    except websockets.exceptions.ConnectionClosed as e:
        print(f"{player_name} connection closed: {e.code} - {e.reason}")
    except Exception as e:
        print(f"{player_name} error: {e}")

async def main():
    # Create tasks for both players
    player1 = asyncio.create_task(connect_player(TOKEN_1, "Player 1"))
    player2 = asyncio.create_task(connect_player(TOKEN_2, "Player 2"))
    
    # Wait for both players to finish
    await asyncio.gather(player1, player2)

if __name__ == "__main__":
    print("Starting WebSocket test client...")
    asyncio.run(main()) 