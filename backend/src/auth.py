import jwt
import asyncio
import websockets
import uuid
import os

# Use environment variable for secret key or fallback to a secure default
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-key-change-this-in-production')

class AuthError(Exception):
    pass

class Auth:
    def __init__(self):
        self.users = {}

    def login(self, username, password):
        # For demo purposes, accept any username/password
        user_id = str(uuid.uuid4())
        self.users[user_id] = {
            "user_id": user_id,
            "username": username,
            "is_guest": False
        }
        return self.users[user_id]

    def get_user(self, user_id):
        return self.users.get(user_id)

def extract_auth_user(token, websocket):
    """
    Extract user details from the JWT token.
    """
    if not token:
        print("No token provided")
        return None
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {
            "user_id": payload["user_id"],
            "name": payload["name"],
            "is_guest": payload.get("is_guest", False),
            "socket": websocket,
        }
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

async def authenticate(websocket, path):
    """
    WebSocket authentication handler.
    """
    try:
        query_params = path.split("?")[-1]  # Extract query string
        token = query_params.split("token=")[-1]  # Extract token
        user = extract_auth_user(token, websocket)
        if user:
            print(f"User {user['name']} authenticated successfully.")
            return user
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

# Run WebSocket server (Test this file directly)
async def start_server():
    async with websockets.serve(authenticate, "localhost", 8080):
        await asyncio.Future()  # Keeps the server running

if __name__ == "__main__":
    asyncio.run(start_server())
