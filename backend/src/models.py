# from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum, func
# from sqlalchemy.orm import relationship
# from database import Base
# from database import get_db_connection

# def create_tables():
#     db = get_db_connection()
#     cursor = db.cursor()

#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             id VARCHAR(255) PRIMARY KEY,
#             name VARCHAR(255),
#             is_guest BOOLEAN
#         )
#     """)

#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS games (
#             id VARCHAR(255) PRIMARY KEY,
#             player1_id VARCHAR(255),
#             player2_id VARCHAR(255),
#             status ENUM('IN_PROGRESS', 'COMPLETED', 'ABANDONED', 'TIME_UP', 'PLAYER_EXIT'),
#             result ENUM('WHITE_WINS', 'BLACK_WINS', 'DRAW'),
#             start_at DATETIME,
#             current_fen TEXT,
#             FOREIGN KEY (player1_id) REFERENCES users(id),
#             FOREIGN KEY (player2_id) REFERENCES users(id)
#         )
#     """)

#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS moves (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             game_id VARCHAR(255),
#             move_number INT,
#             from_square VARCHAR(10),
#             to_square VARCHAR(10),
#             created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (game_id) REFERENCES games(id)
#         )
#     """)

#     db.commit()
#     cursor.close()
#     db.close()

# if __name__ == "__main__":
#     create_tables()

# class User(Base):
#     __tablename__ = "users"

#     id = Column(String(36), primary_key=True)  # UUID
#     name = Column(String(255), nullable=False)
#     provider = Column(String(50), nullable=False, default="guest")  # Auth provider

#     games_as_white = relationship("Game", foreign_keys="Game.white_player_id", back_populates="white_player")
#     games_as_black = relationship("Game", foreign_keys="Game.black_player_id", back_populates="black_player")

# class Game(Base):
#     __tablename__ = "games"

#     id = Column(String(36), primary_key=True)  # UUID
#     white_player_id = Column(String(36), ForeignKey("users.id"), nullable=False)
#     black_player_id = Column(String(36), ForeignKey("users.id"), nullable=True)
#     status = Column(Enum("IN_PROGRESS", "COMPLETED", "ABANDONED", "TIME_UP", "PLAYER_EXIT", name="game_status"), default="IN_PROGRESS")
#     result = Column(Enum("WHITE_WINS", "BLACK_WINS", "DRAW", name="game_result"), nullable=True)
#     start_at = Column(DateTime, default=func.now())
#     current_fen = Column(String(255), default="startpos")  # Store the latest board position

#     white_player = relationship("User", foreign_keys=[white_player_id], back_populates="games_as_white")
#     black_player = relationship("User", foreign_keys=[black_player_id], back_populates="games_as_black")
#     moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")

# class Move(Base):
#     __tablename__ = "moves"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     game_id = Column(String(36), ForeignKey("games.id"), nullable=False)
#     move_number = Column(Integer, nullable=False)
#     from_square = Column(String(5), nullable=False)  # Example: "e2"
#     to_square = Column(String(5), nullable=False)  # Example: "e4"
#     san = Column(String(10), nullable=True)  # Standard Algebraic Notation
#     created_at = Column(DateTime, default=func.now())

#     game = relationship("Game", back_populates="moves")
