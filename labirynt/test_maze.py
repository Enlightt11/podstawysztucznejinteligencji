"""
Zestaw testów jednostkowych i integracyjnych dla zadania z labiryntem (BFS / DFS).
Testuje:
- poprawność definicji znaków Unicode i ich akcji
- wczytywanie i wyrównywanie map
- relację sąsiedztwa i wzajemność połączeń
- poprawność i optymalność BFS (najkrótsza ścieżka)
- działanie DFS (LIFO)
- przypadek braku ścieżki (rozłączne składowe)
- przypadek trywialny (start == end)
- walidację współrzędnych i pól pustych
"""

import os
import unittest
from maze import Maze, TILE_ACTIONS, UP, DOWN, LEFT, RIGHT, OPPOSITE
from solver import solve, search_generator


class TestMazeBasics(unittest.TestCase):
    def setUp(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.maze1_path = os.path.join(self.script_dir, "mazes", "maze1.txt")
        self.maze2_path = os.path.join(self.script_dir, "mazes", "maze2.txt")
        self.maze3_path = os.path.join(self.script_dir, "mazes", "maze3.txt")

    def test_unicode_tiles_registered(self):
        """Weryfikuje, czy wszystkie 16 znaków ze specyfikacji są zarejestrowane."""
        expected_tiles = {
            '┼', '│', '─', ' ', '┐', '┘', '└', '┌',
            '┤', '┴', '├', '┬', '╵', '╷', '╴', '╶'
        }
        self.assertEqual(set(TILE_ACTIONS.keys()), expected_tiles)

        # Sprawdzenie przykładowych akcji
        self.assertEqual(TILE_ACTIONS['┼'], {UP, DOWN, LEFT, RIGHT})
        self.assertEqual(TILE_ACTIONS['│'], {UP, DOWN})
        self.assertEqual(TILE_ACTIONS['─'], {LEFT, RIGHT})
        self.assertEqual(TILE_ACTIONS[' '], set())
        self.assertEqual(TILE_ACTIONS['┌'], {DOWN, RIGHT})
        self.assertEqual(TILE_ACTIONS['┘'], {UP, LEFT})
        self.assertEqual(TILE_ACTIONS['╵'], {UP})
        self.assertEqual(TILE_ACTIONS['╷'], {DOWN})
        self.assertEqual(TILE_ACTIONS['╴'], {LEFT})
        self.assertEqual(TILE_ACTIONS['╶'], {RIGHT})

    def test_load_and_padding(self):
        """Weryfikuje automatyczne wykrywanie rozmiaru i dopełnianie spacjami."""
        maze = Maze.load_from_file(self.maze2_path)
        self.assertEqual(maze.height, 16)
        self.assertEqual(maze.width, 16)
        for row in maze.grid:
            self.assertEqual(len(row), 16)

    def test_passable_and_bounds(self):
        """Weryfikuje sprawdzanie granic i pól korytarza."""
        maze = Maze.load_from_file(self.maze2_path)
        self.assertTrue(maze.is_in_bounds(0, 0))
        self.assertFalse(maze.is_in_bounds(-1, 0))
        self.assertFalse(maze.is_in_bounds(0, 100))

        # Pole (1, 1) w maze2 to puste pole ' '
        self.assertEqual(maze.get_tile(1, 1), ' ')
        self.assertFalse(maze.is_passable(1, 1))

        # Pole (2, 7) w maze2 to '╷'
        self.assertEqual(maze.get_tile(2, 7), '╷')
        self.assertTrue(maze.is_passable(2, 7))


class TestSearchAlgorithms(unittest.TestCase):
    def setUp(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.maze1_path = os.path.join(self.script_dir, "mazes", "maze1.txt")
        self.maze2_path = os.path.join(self.script_dir, "mazes", "maze2.txt")
        self.maze3_path = os.path.join(self.script_dir, "mazes", "maze3.txt")

    def test_trivial_start_equals_end(self):
        """Przypadek, gdy start == end."""
        maze = Maze.load_from_file(self.maze2_path)
        res_bfs = solve(maze, (2, 7), (2, 7), algo='BFS')
        self.assertTrue(res_bfs.found)
        self.assertEqual(res_bfs.path, [(2, 7)])

        res_dfs = solve(maze, (2, 7), (2, 7), algo='DFS')
        self.assertTrue(res_dfs.found)
        self.assertEqual(res_dfs.path, [(2, 7)])

    def test_bfs_shortest_path_maze1(self):
        """W pełnej siatce maze1, BFS musi znaleźć najkrótszą drogę o długości Manhattanu."""
        maze = Maze.load_from_file(self.maze1_path)
        start = (0, 0)
        end = (5, 5)
        res = solve(maze, start, end, algo='BFS')
        self.assertTrue(res.found)
        # Długość ścieżki (liczba krawędzi) z (0,0) do (5,5) w siatce to 10
        self.assertEqual(len(res.path) - 1, 10)
        self.assertEqual(res.path[0], start)
        self.assertEqual(res.path[-1], end)

    def test_bfs_vs_dfs_maze2(self):
        """Test na prostej mapie maze2 z (2, 7) do (5, 12)."""
        maze = Maze.load_from_file(self.maze2_path)
        start = (2, 7)
        end = (5, 12)

        res_bfs = solve(maze, start, end, algo='BFS')
        res_dfs = solve(maze, start, end, algo='DFS')

        self.assertTrue(res_bfs.found)
        self.assertTrue(res_dfs.found)

        # Obie ścieżki muszą zaczynać się w starcie i kończyć w celu
        self.assertEqual(res_bfs.path[0], start)
        self.assertEqual(res_bfs.path[-1], end)
        self.assertEqual(res_dfs.path[0], start)
        self.assertEqual(res_dfs.path[-1], end)

        # BFS eksploruje mniej kroków (21) niż DFS (79), który obchodzi obrzeża
        self.assertLess(res_bfs.steps, res_dfs.steps)

    def test_path_continuity(self):
        """Weryfikuje, czy każdy kolejny krok w znalezionej ścieżce jest poprawnym ruchem."""
        maze = Maze.load_from_file(self.maze2_path)
        res = solve(maze, (2, 7), (5, 12), algo='BFS')
        self.assertTrue(res.found)
        path = res.path
        for i in range(len(path) - 1):
            curr = path[i]
            nxt = path[i + 1]
            neighbors = maze.get_neighbors(*curr)
            self.assertIn(nxt, neighbors, f"Krok z {curr} do {nxt} nie jest dozwolonym przejściem!")

    def test_disconnected_components_maze3(self):
        """W skomplikowanej mapie maze3 istnieją rozłączne składowe (brak ścieżki)."""
        maze = Maze.load_from_file(self.maze3_path)
        # (0, 1) leży w składowej 0, a (28, 29) w innej składowej
        start = (0, 1)
        end = (28, 29)

        res_bfs = solve(maze, start, end, algo='BFS')
        self.assertFalse(res_bfs.found)
        self.assertEqual(res_bfs.path, [])
        self.assertGreater(res_bfs.steps, 0)

        res_dfs = solve(maze, start, end, algo='DFS')
        self.assertFalse(res_dfs.found)
        self.assertEqual(res_dfs.path, [])
        self.assertGreater(res_dfs.steps, 0)


if __name__ == "__main__":
    unittest.main()
