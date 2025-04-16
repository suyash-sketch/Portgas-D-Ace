import asyncio
import json
import os
from aiohttp import web
from grid import create_grid, remove_numbers, SUB_GRID_SIZE

# Initialize game state
game_grid = None

# Get the absolute paths to the frontend and backend directories
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'src')
BACKEND_DIR = os.path.dirname(__file__)

async def handle_static_file(request):
    try:
        path = request.path
        if path == '/':
            path = '/index.html'
            file_path = os.path.join(FRONTEND_DIR, path.lstrip('/'))
        elif path == '/sudoku':
            file_path = os.path.join(BACKEND_DIR, 'templates', 'sudoku.html')
        else:
            file_path = os.path.join(FRONTEND_DIR, path.lstrip('/'))
            
        if os.path.exists(file_path):
            response = web.FileResponse(file_path)
            if file_path.endswith('.html'):
                response.headers['Content-Type'] = 'text/html'
            elif file_path.endswith('.css'):
                response.headers['Content-Type'] = 'text/css'
            elif file_path.endswith('.js'):
                response.headers['Content-Type'] = 'application/javascript'
            return response
        print(f"File not found: {file_path}")  # Debug log
        return web.Response(status=404)
    except Exception as e:
        print(f"Error serving static file: {e}")
        return web.Response(status=500)

async def handle_new_game(request):
    global game_grid
    grid = create_grid(SUB_GRID_SIZE)
    remove_numbers(grid)
    game_grid = grid
    return web.json_response({
        'grid': grid,
        'status': 'success'
    })

async def handle_make_move(request):
    global game_grid
    data = await request.json()
    row = data.get('row')
    col = data.get('col')
    value = data.get('value')
    
    if game_grid is None:
        return web.json_response({'error': 'No active game'}, status=400)
        
    if 0 <= row < 9 and 0 <= col < 9 and 1 <= value <= 9:
        game_grid[row][col] = value
        return web.json_response({
            'grid': game_grid,
            'status': 'success'
        })
    return web.json_response({'error': 'Invalid move'}, status=400)

async def handle_check_win(request):
    global game_grid
    if game_grid is None:
        return web.json_response({'error': 'No active game'}, status=400)
        
    # Check if the grid is complete and valid
    for row in range(9):
        for col in range(9):
            if game_grid[row][col] == 0:
                return web.json_response({'win': False})
                
    # Check rows, columns, and subgrids
    for i in range(9):
        # Check row
        if len(set(game_grid[i])) != 9:
            return web.json_response({'win': False})
            
        # Check column
        column = [game_grid[j][i] for j in range(9)]
        if len(set(column)) != 9:
            return web.json_response({'win': False})
            
        # Check subgrid
        subgrid_row = (i // 3) * 3
        subgrid_col = (i % 3) * 3
        subgrid = []
        for r in range(3):
            for c in range(3):
                subgrid.append(game_grid[subgrid_row + r][subgrid_col + c])
        if len(set(subgrid)) != 9:
            return web.json_response({'win': False})
            
    return web.json_response({'win': True})

async def start_http_server():
    """Start the HTTP server."""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/{tail:.*}', handle_static_file)
    app.router.add_post('/api/new-game', handle_new_game)
    app.router.add_post('/api/make-move', handle_make_move)
    app.router.add_get('/api/check-win', handle_check_win)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🚀 Starting HTTP server on port {port}...")
    return runner

async def main():
    http_server = await start_http_server()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        await http_server.cleanup()

if __name__ == '__main__':
    asyncio.run(main()) 