import asyncio
import websockets
import json
import os
from urllib.parse import parse_qs, urlparse
from game_manager import GameManager
from auth import Auth, extract_auth_user
from socket_manager import socket_manager
from aiohttp import web, web_ws
from grid import create_grid, remove_numbers, SUB_GRID_SIZE

# Initialize game manager and auth
game_manager = GameManager()
auth = Auth()

# Initialize Sudoku game state
sudoku_grid = None

# Initialize Tic Tac Toe game state
tictactoe_players = []
tictactoe_games = []

# Get the absolute path to the frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'src')

async def handle_static_file(request):
    try:
        path = request.path
        if path == '/':
            path = '/index.html'  # Serve index.html as the main page
            
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

async def handle_sudoku_game(request):
    try:
        file_path = os.path.join(FRONTEND_DIR, 'templates', 'sudoku.html')
        if os.path.exists(file_path):
            return web.FileResponse(file_path)
        return web.Response(status=404)
    except Exception as e:
        print(f"Error serving Sudoku game: {e}")
        return web.Response(status=500)

async def handle_new_sudoku_game(request):
    global sudoku_grid
    grid = create_grid(SUB_GRID_SIZE)
    remove_numbers(grid)
    sudoku_grid = grid
    return web.json_response({
        'grid': grid,
        'status': 'success'
    })

async def handle_sudoku_move(request):
    global sudoku_grid
    data = await request.json()
    row = data.get('row')
    col = data.get('col')
    value = data.get('value')
    
    if sudoku_grid is None:
        return web.json_response({'error': 'No active game'}, status=400)
        
    if 0 <= row < 9 and 0 <= col < 9 and 1 <= value <= 9:
        sudoku_grid[row][col] = value
        return web.json_response({
            'grid': sudoku_grid,
            'status': 'success'
        })
    return web.json_response({'error': 'Invalid move'}, status=400)

async def handle_check_sudoku_win(request):
    global sudoku_grid
    if sudoku_grid is None:
        return web.json_response({'error': 'No active game'}, status=400)
        
    # Check if the grid is complete and valid
    for row in range(9):
        for col in range(9):
            if sudoku_grid[row][col] == 0:
                return web.json_response({'win': False})
                
    # Check rows, columns, and subgrids
    for i in range(9):
        # Check row
        if len(set(sudoku_grid[i])) != 9:
            return web.json_response({'win': False})
            
        # Check column
        column = [sudoku_grid[j][i] for j in range(9)]
        if len(set(column)) != 9:
            return web.json_response({'win': False})
            
        # Check subgrid
        subgrid_row = (i // 3) * 3
        subgrid_col = (i % 3) * 3
        subgrid = []
        for r in range(3):
            for c in range(3):
                subgrid.append(sudoku_grid[subgrid_row + r][subgrid_col + c])
        if len(set(subgrid)) != 9:
            return web.json_response({'win': False})
            
    return web.json_response({'win': True})

async def handle_tictactoe_game(request):
    try:
        file_path = os.path.join(FRONTEND_DIR, 'templates', 'tictactoe.html')
        if os.path.exists(file_path):
            return web.FileResponse(file_path)
        return web.Response(status=404)
    except Exception as e:
        print(f"Error serving Tic Tac Toe game: {e}")
        return web.Response(status=500)

async def handle_tictactoe_find(request):
    data = await request.json()
    name = data.get('name')
    
    if name is not None:
        tictactoe_players.append(name)
        
        if len(tictactoe_players) >= 2:
            p1obj = {
                'p1name': tictactoe_players[0],
                'p1value': 'X',
                'p1move': ''
            }
            p2obj = {
                'p2name': tictactoe_players[1],
                'p2value': 'O',
                'p2move': ''
            }
            
            game = {
                'p1': p1obj,
                'p2': p2obj,
                'sum': 1
            }
            tictactoe_games.append(game)
            
            tictactoe_players.pop(0)
            tictactoe_players.pop(0)
            
            return web.json_response({
                'status': 'success',
                'allPlayers': tictactoe_games
            })
    
    return web.json_response({
        'status': 'waiting',
        'message': 'Waiting for another player...'
    })

async def handle_tictactoe_move(request):
    data = await request.json()
    name = data.get('name')
    value = data.get('value')
    move_id = data.get('id')
    
    game_to_update = None
    for game in tictactoe_games:
        if game['p1']['p1name'] == name or game['p2']['p2name'] == name:
            game_to_update = game
            break
    
    if game_to_update:
        if value == 'X':
            game_to_update['p1']['p1move'] = move_id
            game_to_update['sum'] += 1
        elif value == 'O':
            game_to_update['p2']['p2move'] = move_id
            game_to_update['sum'] += 1
            
        return web.json_response({
            'status': 'success',
            'allPlayers': tictactoe_games
        })
    
    return web.json_response({
        'status': 'error',
        'message': 'Game not found'
    }, status=400)

async def handle_tictactoe_game_over(request):
    data = await request.json()
    name = data.get('name')
    
    global tictactoe_games
    tictactoe_games = [game for game in tictactoe_games if game['p1']['p1name'] != name]
    
    return web.json_response({
        'status': 'success',
        'message': 'Game removed'
    })

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

async def start_http_server():
    """Start the HTTP + WebSocket server on a single port."""
    app = web.Application()
    
    # Add routes for static files and WebSocket
    app.router.add_get('/ws', websocket_aiohttp_handler)
    app.router.add_get('/{tail:.*}', handle_static_file)
    
    # Add Sudoku routes
    app.router.add_get('/sudoku', handle_sudoku_game)
    app.router.add_post('/api/new-game', handle_new_sudoku_game)
    app.router.add_post('/api/make-move', handle_sudoku_move)
    app.router.add_get('/api/check-win', handle_check_sudoku_win)
    
    # Add Tic Tac Toe routes
    app.router.add_get('/tictactoe', handle_tictactoe_game)
    app.router.add_post('/api/tictactoe/find', handle_tictactoe_find)
    app.router.add_post('/api/tictactoe/move', handle_tictactoe_move)
    app.router.add_post('/api/tictactoe/game-over', handle_tictactoe_game_over)

    runner = web.AppRunner(app)
    await runner.setup()

    # Serve everything on one port (8080 or whatever ngrok exposes)
    port = int(os.environ.get('PORT', 8080))

    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🚀 Starting HTTP+WebSocket server on port {port}...")
    return runner

async def main():
    http_server = await start_http_server()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        await http_server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())