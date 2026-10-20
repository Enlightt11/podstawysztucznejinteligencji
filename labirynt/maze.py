"""
Moduł odpowiedzialny za reprezentację labiryntu i reguły poruszania się.
Zgodny ze specyfikacją zadania: Podstawy sztucznej inteligencji - Ćwiczenia 1.
"""

from typing import List, Tuple, Set, Dict, Optional

# Kierunki ruchu i ich przesunięcia (wiersz, kolumna)
UP = 'UP'
DOWN = 'DOWN'
RIGHT = 'RIGHT'
LEFT = 'LEFT'

DIR_SYMBOLS = {
    UP: '↑',
    DOWN: '↓',
    RIGHT: '→',
    LEFT: '←'
}

DELTAS: Dict[str, Tuple[int, int]] = {
    UP: (-1, 0),
    DOWN: (1, 0),
    RIGHT: (0, 1),
    LEFT: (0, -1)
}

OPPOSITE: Dict[str, str] = {
    UP: DOWN,
    DOWN: UP,
    RIGHT: LEFT,
    LEFT: RIGHT
}

# Kolejność przeglądania akcji zgodna z tabelą z treści zadania (↑, ↓, →, ←)
ACTION_ORDER = [UP, DOWN, RIGHT, LEFT]

# Tabela akcji dla znaków Unicode określonych w zadaniu
TILE_ACTIONS: Dict[str, Set[str]] = {
    '┼': {UP, DOWN, RIGHT, LEFT},  # \u253C
    '│': {UP, DOWN},               # \u2502
    '─': {RIGHT, LEFT},            # \u2500
    ' ': set(),                    # \u0020 (brak akcji / ściana / pustka)
    '┐': {DOWN, LEFT},             # \u2510
    '┘': {UP, LEFT},               # \u2518
    '└': {UP, RIGHT},              # \u2514
    '┌': {DOWN, RIGHT},            # \u250C
    '┤': {UP, DOWN, LEFT},         # \u2524
    '┴': {UP, RIGHT, LEFT},        # \u2534
    '├': {UP, DOWN, RIGHT},        # \u251C
    '┬': {DOWN, RIGHT, LEFT},      # \u252C
    '╵': {UP},                     # \u2575
    '╷': {DOWN},                   # \u2577
    '╴': {LEFT},                   # \u2574
    '╶': {RIGHT},                  # \u2576
}

# Sekwencje ANSI dla kolorów określonych w zadaniu
COLOR_RED = "\033[1;31m"      # pole startowe
COLOR_GREEN = "\033[1;32m"    # pole odwiedzone
COLOR_YELLOW = "\033[1;33m"   # pole oczekujące w kolejce
COLOR_BLUE = "\033[1;34m"     # pole końcowe
COLOR_RESET = "\033[0m"       # kolor domyślny

# Dodatkowe style dla czytelności podsumowania
COLOR_CYAN = "\033[1;36m"
COLOR_BOLD = "\033[1m"
COLOR_GRAY = "\033[90m"


class Maze:
    """Reprezentacja labiryntu wczytanego z pliku tekstowego."""

    def __init__(self, grid: List[str], filepath: Optional[str] = None):
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0]) if self.height > 0 else 0
        self.filepath = filepath

    @classmethod
    def load_from_file(cls, filepath: str) -> "Maze":
        """
        Wczytuje mapę labiryntu z pliku.
        Automatycznie wykrywa ilość wierszy i maksymalną liczbę znaków w linii,
        uzupełniając krótsze linie spacjami do równej szerokości.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\r\n') for line in f]

        if not lines:
            raise ValueError(f"Plik mapy '{filepath}' jest pusty.")

        # Wykrycie maksymalnej długości linii
        max_width = max(len(line) for line in lines)

        # Uzupełnienie krótszych linii spacjami do równej długości
        normalized_grid = [line.ljust(max_width, ' ') for line in lines]

        return cls(normalized_grid, filepath=filepath)

    def is_in_bounds(self, r: int, c: int) -> bool:
        """Sprawdza, czy współrzędne (r, c) leżą w granicach labiryntu."""
        return 0 <= r < self.height and 0 <= c < self.width

    def get_tile(self, r: int, c: int) -> str:
        """Zwraca znak znajdujący się na pozycji (r, c)."""
        if not self.is_in_bounds(r, c):
            return ' '
        return self.grid[r][c]

    def is_passable(self, r: int, c: int) -> bool:
        """Sprawdza, czy pole jest polem korytarza (posiada jakiekolwiek akcje, nie jest spacją)."""
        if not self.is_in_bounds(r, c):
            return False
        tile = self.grid[r][c]
        return tile != ' ' and len(TILE_ACTIONS.get(tile, set())) > 0

    def get_actions(self, r: int, c: int) -> Set[str]:
        """Zwraca zbiór akcji dozwolonych na danym polu."""
        if not self.is_in_bounds(r, c):
            return set()
        return TILE_ACTIONS.get(self.grid[r][c], set())

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """
        Zwraca listę sąsiadów, do których można przejść z pola (r, c).
        Przejście jest poprawne, gdy:
        1. Bieżące pole pozwala na ruch w danym kierunku.
        2. Nowe pole mieści się w granicach labiryntu.
        3. Nowe pole nie jest pustym polem (ścianą).
        4. Nowe pole ma połączenie zwrotne w przeciwnym kierunku.
        """
        curr_tile = self.get_tile(r, c)
        available_actions = TILE_ACTIONS.get(curr_tile, set())
        neighbors: List[Tuple[int, int]] = []

        for action in ACTION_ORDER:
            if action in available_actions:
                dr, dc = DELTAS[action]
                nr, nc = r + dr, c + dc
                if self.is_in_bounds(nr, nc):
                    neighbor_tile = self.grid[nr][nc]
                    if neighbor_tile != ' ':
                        neighbor_actions = TILE_ACTIONS.get(neighbor_tile, set())
                        if OPPOSITE[action] in neighbor_actions:
                            neighbors.append((nr, nc))

        return neighbors

    def render_view(
        self,
        start: Optional[Tuple[int, int]] = None,
        end: Optional[Tuple[int, int]] = None,
        visited: Optional[Set[Tuple[int, int]]] = None,
        frontier: Optional[Set[Tuple[int, int]]] = None,
        path: Optional[List[Tuple[int, int]]] = None,
        show_coords: bool = True
    ) -> str:
        """
        Generuje tekstową reprezentację labiryntu z nałożonymi kolorami ANSI
        oraz pełną, jednowierszową numeracją kolumn (0, 1, ..., 10, 11, ...).
        Zgodnie z wymaganiami zadania:
        - domyślny kolor: pole normalne
        - czerwony kolor: pole startowe (\033[1;31m)
        - niebieski kolor: pole końcowe (\033[1;34m)
        - zielony kolor: pole odwiedzone (\033[1;32m)
        - żółty kolor: pole oczekujące w kolejce (\033[1;33m)
        """
        visited_set = visited or set()
        frontier_set = frontier or set()
        path_set = set(path) if path else set()

        lines: List[str] = []

        if show_coords:
            # Pełne numery kolumn w jednym wierszu (każda kolumna ma szerokość 3 znaków)
            col_header = "    " + "".join(f"{c:^3d}" for c in range(self.width))
            lines.append(f"{COLOR_GRAY}{col_header}{COLOR_RESET}")
            lines.append(f"{COLOR_GRAY}   ┌{'───' * self.width}┐{COLOR_RESET}")

        for r in range(self.height):
            row_chars: List[str] = []
            if show_coords:
                row_chars.append(f"{COLOR_GRAY}{r:2d} │{COLOR_RESET}")

            for c in range(self.width):
                pos = (r, c)
                ch = self.grid[r][c]

                # Przedłużenie poziomych korytarzy do szerokości 3 znaków,
                # aby zachować ciągłość ścian i przejść
                actions = TILE_ACTIONS.get(ch, set())
                left_pad = "─" if LEFT in actions else " "
                right_pad = "─" if RIGHT in actions else " "
                cell_str = f"{left_pad}{ch}{right_pad}"

                # Hierarchia kolorowania
                if pos == start:
                    color = COLOR_RED
                elif pos == end:
                    color = COLOR_BLUE
                elif path_set and pos in path_set:
                    # Podświetlenie ścieżki w widoku końcowym (cyjan)
                    color = COLOR_CYAN
                elif pos in visited_set:
                    color = COLOR_GREEN
                elif pos in frontier_set:
                    color = COLOR_YELLOW
                else:
                    color = COLOR_RESET

                row_chars.append(f"{color}{cell_str}{COLOR_RESET}")

            if show_coords:
                row_chars.append(f"{COLOR_GRAY}│{COLOR_RESET}")

            lines.append("".join(row_chars))

        if show_coords:
            lines.append(f"{COLOR_GRAY}   └{'───' * self.width}┘{COLOR_RESET}")

        return "\n".join(lines)
