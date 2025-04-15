import asyncio
import json
import random
# from websockets import WebSocketServerProtocol
from socket_manager import socket_manager
from messages import (
    INIT_GAME, MOVE, GAME_ADDED, GAME_ALERT, GAME_JOINED,
    GAME_NOT_FOUND, GAME_ENDED, EXIT_GAME, JOIN_ROOM
)

class GameManager:
    def __init__(self):
        self.users = {}  # websocket -> user
        self.games = {}  # game_id -> game
        self.waiting_users = []  # List of users waiting for a game
        self.next_game_id = 1

    def add_user(self, user):
        """Add a new user to the game manager."""
        self.users[user['websocket']] = user
        print(f"User {user['id']} added to game manager")
        
        # If there's a waiting user, create a new game
        if self.waiting_users:
            opponent = self.waiting_users.pop(0)
            self.create_game(user, opponent)
        else:
            # Add user to waiting list
            self.waiting_users.append(user)
            # Notify user they're waiting for an opponent
            asyncio.create_task(self.notify_waiting(user))

    def remove_user(self, websocket):
        """Remove a user from the game manager."""
        if websocket in self.users:
            user = self.users[websocket]
            print(f"User {user['id']} removed from game manager")
            
            # Remove from waiting list if present
            if user in self.waiting_users:
                self.waiting_users.remove(user)
            
            # End any active games
            for game_id, game in list(self.games.items()):
                if user in [game['white'], game['black']]:
                    self.end_game(game_id)
            
            del self.users[websocket]

    async def notify_waiting(self, user):
        """Notify a user they're waiting for an opponent."""
        await user['websocket'].send(json.dumps({
            "type": "WAITING",
            "message": "Waiting for an opponent..."
        }))

    def create_game(self, player1, player2):
        """Create a new game between two players."""
        game_id = self.next_game_id
        self.next_game_id += 1
        
        # Randomly assign colors
        if random.random() < 0.5:
            white, black = player1, player2
        else:
            white, black = player2, player1
        
        game = {
            'id': game_id,
            'white': white,
            'black': black,
            'moves': [],
            'status': 'active'
        }
        
        self.games[game_id] = game
        
        # Notify both players
        asyncio.create_task(self.notify_game_start(game))

    async def notify_game_start(self, game):
        """Notify both players that the game has started."""
        # Notify white player
        await game['white']['websocket'].send(json.dumps({
            "type": "GAME_ASSIGNED",
            "role": "white",
            "game_id": game['id']
        }))
        
        # Notify black player
        await game['black']['websocket'].send(json.dumps({
            "type": "GAME_ASSIGNED",
            "role": "black",
            "game_id": game['id']
        }))
        
        # Notify both players that the game has started
        for player in [game['white'], game['black']]:
            await player['websocket'].send(json.dumps({
                "type": "GAME_JOINED",
                "game_id": game['id']
            }))

    async def handle_message(self, user, data):
        """Handle incoming messages from users."""
        message_type = data.get('type')
        
        if message_type == "MOVE":
            await self.handle_move(user, data)
        elif message_type == "EXIT_GAME":
            await self.handle_exit_game(user)
        elif message_type == "INIT_GAME":
            # Simply acknowledge the message
            await user['websocket'].send(json.dumps({
                "type": "INIT_GAME_ACK",
                "message": "Game initialization acknowledged"
            }))
            # You don't need to do anything else as the user has already been added to the waiting list
            print(f"INIT_GAME received from {user['id']}")
        else:
            print(f"Unknown message type: {message_type}")

    async def handle_move(self, user, data):
        """Handle a move from a user."""
        # Find the game this user is playing
        game = None
        for g in self.games.values():
            if user in [g['white'], g['black']]:
                game = g
                break
        
        if not game:
            print(f"User {user['id']} attempted to make a move but no active game found")
            await user['websocket'].send(json.dumps({
                "type": "error",
                "message": "No active game found"
            }))
            return
        
        # Verify it's the user's turn
        is_white = user == game['white']
        if len(game['moves']) % 2 == 0 and not is_white:
            print(f"User {user['id']} attempted to move out of turn (white's turn)")
            await user['websocket'].send(json.dumps({
                "type": "error",
                "message": "Not your turn"
            }))
            return
        if len(game['moves']) % 2 == 1 and is_white:
            print(f"User {user['id']} attempted to move out of turn (black's turn)")
            await user['websocket'].send(json.dumps({
                "type": "error",
                "message": "Not your turn"
            }))
            return
        
        # Add move to game history
        move = data.get('move')
        game['moves'].append(move)
        print(f"Move added to game {game['id']}: {move} by {'white' if is_white else 'black'}")
        
        # Prepare move data with check information
        move_data = {
            "type": "MOVE",
            "move": move,
            "role": "white" if is_white else "black"
        }
        
        # Add check information if present
        if 'isCheck' in data:
            move_data['isCheck'] = data['isCheck']
        if 'isCheckmate' in data:
            move_data['isCheckmate'] = data['isCheckmate']
        if 'checkingPiece' in data:
            move_data['checkingPiece'] = data['checkingPiece']
        
        # Notify both players of the move
        for player in [game['white'], game['black']]:
            print(f"Sending move to player {player['id']}: {move_data}")
            await player['websocket'].send(json.dumps(move_data))

    async def handle_exit_game(self, user):
        """Handle a user exiting the game."""
        # Find and end any active games for this user
        for game_id, game in list(self.games.items()):
            if user in [game['white'], game['black']]:
                self.end_game(game_id)
                break

    def end_game(self, game_id):
        """End a game and clean up."""
        if game_id in self.games:
            game = self.games[game_id]
            print(f"Game {game_id} ended")
            del self.games[game_id]
            
            # Notify both players
            for player in [game['white'], game['black']]:
                asyncio.create_task(player['websocket'].send(json.dumps({
                    "type": "GAME_OVER",
                    "message": "Game ended"
                })))

    def get_game(self, game_id):
        """Get a game by ID."""
        return self.games.get(game_id)

    def get_user_game(self, user):
        """Get the active game for a user."""
        for game in self.games.values():
            if user in [game['white'], game['black']]:
                return game
        return None