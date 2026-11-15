import os
import atexit
import random
import chess.engine

# ===== Stockfish =====
# Đường dẫn tới engine Stockfish đi kèm dự án
STOCKFISH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish.exe")
STOCKFISH_TIME = 1.0  # thời gian Stockfish suy nghĩ cho mỗi nước đi (giây)

_engine = None  # tiến trình Stockfish dùng chung, chỉ mở một lần


def _getEngine():
    """Mở Stockfish một lần duy nhất rồi tái sử dụng cho các nước đi sau."""
    global _engine
    if _engine is None:
        _engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    return _engine


def closeEngine():
    """Đóng tiến trình Stockfish khi thoát chương trình."""
    global _engine
    if _engine is not None:
        _engine.quit()
        _engine = None


atexit.register(closeEngine)


def boardToFEN(gs):
    """Chuyển trạng thái bàn cờ của GameState sang chuỗi FEN để đưa cho Stockfish."""
    rows = []
    for r in range(8):
        rowStr = ""
        empty = 0
        for c in range(8):
            piece = gs.board[r][c]
            if piece == "--":
                empty += 1
            else:
                if empty:
                    rowStr += str(empty)
                    empty = 0
                # quân trắng viết HOA, quân đen viết thường theo chuẩn FEN
                rowStr += piece[1].upper() if piece[0] == 'w' else piece[1].lower()
        if empty:
            rowStr += str(empty)
        rows.append(rowStr)

    activeColor = "w" if gs.whiteToMove else "b"

    cr = gs.currentCastlingRight
    castling = ""
    if cr.wks:
        castling += "K"
    if cr.wqs:
        castling += "Q"
    if cr.bks:
        castling += "k"
    if cr.bqs:
        castling += "q"
    if not castling:
        castling = "-"

    enPassant = "-"
    if gs.enpassantPossilbe:
        r, c = gs.enpassantPossilbe
        enPassant = chr(ord('a') + c) + str(8 - r)

    return "{} {} {} {} 0 1".format("/".join(rows), activeColor, castling, enPassant)


def findBestMove(gs, validMoves):
    """Trả về nước đi tốt nhất do Stockfish tính toán (đổi từ định dạng UCI sang Move của dự án)."""
    if not validMoves:
        return None

    fen = boardToFEN(gs)
    try:
        board = chess.Board(fen)
    except ValueError:
        # một số thế cờ có ô bắt tốt qua đường không hợp lệ với chuẩn FEN -> bỏ trường đó
        parts = fen.split(" ")
        parts[3] = "-"
        board = chess.Board(" ".join(parts))

    result = _getEngine().play(board, chess.engine.Limit(time=STOCKFISH_TIME))
    if result.move is None:
        return None

    uci = result.move.uci()
    startRow, startCol = 8 - int(uci[1]), ord(uci[0]) - ord('a')
    endRow, endCol = 8 - int(uci[3]), ord(uci[2]) - ord('a')

    for move in validMoves:
        if (move.startRow == startRow and move.startCol == startCol
                and move.endRow == endRow and move.endCol == endCol):
            return move
    return None


def findRandomMove(validMoves):
    return validMoves[random.randint(0, len(validMoves) - 1)]
