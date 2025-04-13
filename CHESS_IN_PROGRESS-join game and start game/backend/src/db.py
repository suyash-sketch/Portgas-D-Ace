# In-memory storage
games = {}
users = {}

def get_db_connection():
    # This is a mock connection that returns the in-memory storage
    class MockConnection:
        def cursor(self):
            return MockCursor()
        def commit(self):
            pass
        def close(self):
            pass
    return MockConnection()

class MockCursor:
    def execute(self, query, params=None):
        if "INSERT INTO games" in query:
            game_id = params[0]
            games[game_id] = {
                'id': game_id,
                'player1_id': params[1],
                'player2_id': params[2],
                'status': params[3],
                'start_at': params[4],
                'current_fen': params[5]
            }
        elif "UPDATE games" in query:
            game_id = params[2]
            if game_id in games:
                games[game_id]['status'] = params[0]
                games[game_id]['result'] = params[1]
        elif "SELECT" in query:
            if "FROM games" in query:
                return list(games.values())
            elif "FROM users" in query:
                return list(users.values())
        return []

    def fetchall(self):
        return [] 