import time
import json
import uuid
import chess
from socket_manager import socket_manager
from messages import INIT_GAME, MOVE, GAME_ENDED
import asyncio
import random

GAME_TIME_MS = 10 * 60 * 60 * 1000

# In-memory storage
games = {}
moves = {}

class Game:
    def __init__(self, player1_user_id, player2_user_id=None, game_id=None, start_time=None):
        self.game_id = game_id or str(uuid.uuid4())
        self.player1_user_id = player1_user_id
        self.player2_user_id = player2_user_id
        self.board = chess.Board()
        self.move_count = 0
        self.timer = None
        self.move_timer = None
        self.result = None
        self.player1_time_consumed = 0
        self.player2_time_consumed = 0
        self.start_time = start_time or time.time()
        self.last_move_time = self.start_time
        self.status = 'IN_PROGRESS'
        
        # Store game in memory
        games[self.game_id] = self
        moves[self.game_id] = []

    def is_promoting(self, from_square, to_square):
        piece = self.board.piece_at(chess.parse_square(from_square))
        if not piece or piece.piece_type != chess.PAWN:
            return False
        if piece.color != self.board.turn:
            return False
        return to_square.endswith("1") or to_square.endswith("8")

    def seed_moves(self, moves_list):
        for move in moves_list:
            if self.is_promoting(move['from'], move['to']):
                self.board.push(chess.Move.from_uci(move['from'] + move['to'] + 'q'))
            else:
                self.board.push(chess.Move.from_uci(move['from'] + move['to']))
        self.move_count = len(moves_list)
        self.last_move_time = moves_list[-1]['createdAt'] if moves_list else self.start_time
        self.reset_abandon_timer()
        self.reset_move_timer()

    def update_second_player(self, player2_user_id):
        self.player2_user_id = player2_user_id
        self.status = 'IN_PROGRESS'
        
        socket_manager.broadcast(self.game_id, json.dumps({
            "type": INIT_GAME,
            "payload": {
                "gameId": self.game_id,
                "whitePlayer": self.player1_user_id,
                "blackPlayer": self.player2_user_id,
                "fen": self.board.fen(),
                "moves": []
            }
        }))

    def make_move(self, user, move):
        if self.board.turn == chess.WHITE and user.user_id != self.player1_user_id:
            return
        if self.board.turn == chess.BLACK and user.user_id != self.player2_user_id:
            return
        if self.result:
            print(f"User {user.user_id} is making a move post game completion")
            return

        move_timestamp = time.time()
        try:
            # Validate if the move is legal before applying it
            chess_move = chess.Move.from_uci(move['from'] + move['to'])
            if not self.board.is_legal(chess_move):
                print("❌ Illegal move attempted")
                return

            self.board.push(chess_move)
            
            # Store move in memory
            moves[self.game_id].append({
                'from': move['from'],
                'to': move['to'],
                'createdAt': move_timestamp,
                'timeTaken': move_timestamp - self.last_move_time
            })
        except ValueError:
            print("Invalid move attempted")
            return

        if self.board.turn == chess.BLACK:
            self.player1_time_consumed += move_timestamp - self.last_move_time
        else:
            self.player2_time_consumed += move_timestamp - self.last_move_time

        self.last_move_time = move_timestamp
        socket_manager.broadcast(self.game_id, json.dumps({
            "type": MOVE,
            "payload": {
                "move": move,
                "player1TimeConsumed": self.player1_time_consumed,
                "player2TimeConsumed": self.player2_time_consumed
            }
        }))

        if self.board.is_game_over():
            result = "DRAW" if self.board.is_stalemate() else "WHITE_WINS" if self.board.turn == chess.BLACK else "BLACK_WINS"
            self.end_game("COMPLETED", result)

        self.move_count += 1
        self.reset_abandon_timer()
        self.reset_move_timer()

    def reset_abandon_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = time.time() + 60

    def reset_move_timer(self):
        if self.move_timer:
            self.move_timer.cancel()
        turn = self.board.turn
        time_left = GAME_TIME_MS - (self.player1_time_consumed if turn == chess.WHITE else self.player2_time_consumed)
        self.move_timer = time.time() + (time_left / 1000)

    def exit_game(self, user):
        self.end_game("PLAYER_EXIT", "WHITE_WINS" if user.user_id == self.player2_user_id else "BLACK_WINS")

    def end_game(self, status, result):
        self.status = status
        self.result = result
        
        socket_manager.broadcast(self.game_id, json.dumps({
            "type": GAME_ENDED,
            "payload": {
                "result": result,
                "status": status,
                "moves": moves[self.game_id]
            }
        }))
        self.clear_timers()

    def clear_timers(self):
        self.timer = None
        self.move_timer = None

    @staticmethod
    def get_game(game_id):
        return games.get(game_id)

    @staticmethod
    def get_user_game(user_id):
        for game in games.values():
            if game.player1_user_id == user_id or game.player2_user_id == user_id:
                return game
        return None

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
        
        # Notify both players of the move
        for player in [game['white'], game['black']]:
            print(f"Sending move to player {player['id']}: {move}")
            await player['websocket'].send(json.dumps({
                "type": "MOVE",
                "move": move,
                "role": "white" if player == game['white'] else "black"
            }))

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
