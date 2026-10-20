"""
Moduł implementujący algorytmy przeszukiwania BFS i DFS.
Zgodny ze specyfikacją: FIFO dla BFS, LIFO dla DFS.
Generuje stany krok po kroku do animacji w terminalu oraz GUI.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple, Set, Dict, Optional, Iterator
from maze import Maze


@dataclass
class SearchStep:
    """Stan poszukiwania w pojedynczym kroku algorytmu."""
    step_num: int
    current: Tuple[int, int]
    visited: Set[Tuple[int, int]]
    frontier: Set[Tuple[int, int]]
    is_done: bool = False
    found: bool = False
    path: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class SearchResult:
    """Końcowy wynik działania algorytmu przeszukiwania."""
    found: bool
    steps: int
    path: List[Tuple[int, int]]
    visited_count: int
    algorithm: str
    start: Tuple[int, int]
    end: Tuple[int, int]


def reconstruct_path(
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]],
    end: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """Odtwarza pełną ścieżkę od startu do celu za pomocą słownika poprzedników."""
    path: List[Tuple[int, int]] = []
    curr: Optional[Tuple[int, int]] = end
    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)
    path.reverse()
    return path


def search_generator(
    maze: Maze,
    start: Tuple[int, int],
    end: Tuple[int, int],
    algo: str = 'BFS'
) -> Iterator[SearchStep]:
    """
    Generator kroków przeszukiwania labiryntu.
    
    Parametry:
    - maze: instancja Maze
    - start: (wiersz, kolumna) pola startowego
    - end: (wiersz, kolumna) pola końcowego
    - algo: 'BFS' (FIFO) lub 'DFS' (LIFO)
    
    W każdym kroku zwraca obiekt SearchStep zawierający:
    - aktualny numer kroku
    - aktualnie przetwarzane pole
    - zbiór pól odwiedzonych (zielony)
    - zbiór pól w kolejce / na stosie (żółty)
    - flagę zakończenia oraz odnalezioną ścieżkę
    """
    algo_upper = algo.upper().strip()
    if algo_upper not in ('BFS', 'DFS'):
        raise ValueError(f"Nieobsługiwany algorytm: {algo}. Dostępne: BFS, DFS.")

    # Sprawdzenie trywialnego przypadku: start == end
    if start == end:
        yield SearchStep(
            step_num=1,
            current=start,
            visited={start},
            frontier=set(),
            is_done=True,
            found=True,
            path=[start]
        )
        return

    # Inicjalizacja struktur danych
    # BFS: FIFO (deque.popleft)
    # DFS: LIFO (list.pop)
    is_bfs = (algo_upper == 'BFS')
    frontier_collection = deque([start]) if is_bfs else [start]
    frontier_set: Set[Tuple[int, int]] = {start}
    visited_set: Set[Tuple[int, int]] = set()
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}

    step_counter = 0

    while frontier_collection:
        step_counter += 1

        if is_bfs:
            curr = frontier_collection.popleft()  # FIFO
        else:
            curr = frontier_collection.pop()      # LIFO

        frontier_set.discard(curr)
        visited_set.add(curr)

        # Sprawdzenie warunku celu
        if curr == end:
            final_path = reconstruct_path(parent, end)
            yield SearchStep(
                step_num=step_counter,
                current=curr,
                visited=set(visited_set),
                frontier=set(frontier_set),
                is_done=True,
                found=True,
                path=final_path
            )
            return

        # Rozwijanie sąsiadów
        neighbors = maze.get_neighbors(*curr)

        # Dla DFS odwracamy listę sąsiadów przed wrzuceniem na stos LIFO,
        # dzięki czemu pierwszy sąsiad w kolejności (UP, DOWN, RIGHT, LEFT)
        # trafi na wierzchołek stosu i zostanie pobrany jako pierwszy.
        ordered_neighbors = neighbors if is_bfs else list(reversed(neighbors))

        for nxt in ordered_neighbors:
            if nxt not in visited_set and nxt not in frontier_set:
                parent[nxt] = curr
                frontier_collection.append(nxt)
                frontier_set.add(nxt)

        # Emisja stanu pośredniego dla animacji
        yield SearchStep(
            step_num=step_counter,
            current=curr,
            visited=set(visited_set),
            frontier=set(frontier_set),
            is_done=False,
            found=False,
            path=[]
        )

    # Przeszukano całą osiągalną przestrzeń i nie znaleziono celu
    yield SearchStep(
        step_num=step_counter,
        current=curr if 'curr' in locals() else start,
        visited=set(visited_set),
        frontier=set(),
        is_done=True,
        found=False,
        path=[]
    )


def solve(
    maze: Maze,
    start: Tuple[int, int],
    end: Tuple[int, int],
    algo: str = 'BFS'
) -> SearchResult:
    """Wykonuje całe przeszukiwanie i zwraca końcowy SearchResult."""
    last_step = None
    for step in search_generator(maze, start, end, algo):
        last_step = step

    if last_step is None:
        return SearchResult(
            found=False,
            steps=0,
            path=[],
            visited_count=0,
            algorithm=algo.upper(),
            start=start,
            end=end
        )

    return SearchResult(
        found=last_step.found,
        steps=last_step.step_num,
        path=last_step.path,
        visited_count=len(last_step.visited),
        algorithm=algo.upper(),
        start=start,
        end=end
    )
