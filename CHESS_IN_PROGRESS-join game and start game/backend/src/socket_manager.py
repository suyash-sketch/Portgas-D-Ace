import asyncio
from typing import Dict, List, Set
from websockets import WebSocketServerProtocol

class SocketManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SocketManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not SocketManager._initialized:
            self.interested_sockets: Dict[str, List[dict]] = {}
            self.user_room_mapping: Dict[str, str] = {}
            SocketManager._initialized = True

    def add_user(self, user: dict, room_id: str) -> None:
        """Add a user to a room and track their mapping."""
        if room_id not in self.interested_sockets:
            self.interested_sockets[room_id] = []
        self.interested_sockets[room_id].append(user)
        self.user_room_mapping[user['user_id']] = room_id

    async def broadcast(self, room_id: str, message: str) -> None:
        """Broadcast a message to all users in a room."""
        users = self.interested_sockets.get(room_id)
        if not users:
            print('No users in room?')
            return

        for user in users:
            try:
                await user['socket'].send(message)
            except Exception as e:
                print(f"Error broadcasting to user: {e}")

    def remove_user(self, user: dict) -> None:
        """Remove a user from their room and clean up mappings."""
        room_id = self.user_room_mapping.get(user['user_id'])
        if not room_id:
            print('User was not interested in any room?')
            return

        room = self.interested_sockets.get(room_id, [])
        remaining_users = [u for u in room if u['user_id'] != user['user_id']]
        
        if remaining_users:
            self.interested_sockets[room_id] = remaining_users
        else:
            self.interested_sockets.pop(room_id, None)
            
        self.user_room_mapping.pop(user['user_id'], None)

socket_manager = SocketManager()
