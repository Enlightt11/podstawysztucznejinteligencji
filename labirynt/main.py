#!/usr/bin/env python3
"""
Główny program wyszukiwania drogi w labiryncie (BFS / DFS).
Podstawy sztucznej inteligencji - Ćwiczenia 1.
"""

import os
import re
import sys
import time
import argparse
from typing import Tuple, Optional, List

from maze import (
    Maze,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_BLUE,
    COLOR_RESET,
    COLOR_CYAN,
    COLOR_BOLD,
    COLOR_GRAY,
)
from solver import search_generator, SearchStep


def clear_screen() -> None:
    """Czyści ekran terminala i ustawia kursor na pozycji początkowej."""
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def move_cursor_home() -> None:
    """Przenosi kursor na początek ekranu bez czyszczenia bufora (płynna animacja)."""
    if sys.stdout.isatty():
        sys.stdout.write("\033[H")
        sys.stdout.flush()


def hide_cursor() -> None:
    """Ukrywa kursor w terminalu na czas trwania animacji."""
    if sys.stdout.isatty():
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


def show_cursor() -> None:
    """Przywraca widoczność kursora w terminalu."""
    if sys.stdout.isatty():
        sys.stdout.write("\033[?25h\033[0m")
        sys.stdout.flush()


def parse_coords_input(prompt_text: str, maze: Maze, default: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
    """Pobiera od użytkownika współrzędne (wiersz, kolumna) i przeprowadza walidację."""
    default_str = f" [{default[0]} {default[1]}]" if default else ""
    while True:
        try:
            raw = input(f"{prompt_text}{default_str}: ").strip()
            if not raw and default is not None:
                return default

            numbers = re.findall(r'-?\d+', raw)
            if len(numbers) != 2:
                print(f"{COLOR_RED}Błąd: Podaj dokładnie dwie liczby: wiersz i kolumnę (np. '2 7' lub '2, 7').{COLOR_RESET}")
                continue

            r, c = int(numbers[0]), int(numbers[1])

            if not maze.is_in_bounds(r, c):
                print(
                    f"{COLOR_RED}Błąd: Współrzędne ({r}, {c}) leżą poza granicami labiryntu! "
                    f"Dozwolony zakres: wiersze 0..{maze.height - 1}, kolumny 0..{maze.width - 1}.{COLOR_RESET}"
                )
                continue

            if not maze.is_passable(r, c):
                print(
                    f"{COLOR_RED}Błąd: Pole ({r}, {c}) to ściana lub puste pole ('{maze.get_tile(r, c)}'). "
                    f"Wybierz pole będące korytarzem labiryntu.{COLOR_RESET}"
                )
                continue

            return r, c
        except (KeyboardInterrupt, EOFError):
            print("\nPrzerwano wprowadzanie danych.")
            sys.exit(0)


def prompt_algorithm() -> str:
    """Pobiera od użytkownika wybór algorytmu (BFS lub DFS)."""
    while True:
        try:
            choice = input(f"Wybierz rodzaj algorytmu ({COLOR_BOLD}BFS{COLOR_RESET} / {COLOR_BOLD}DFS{COLOR_RESET}) [1 - BFS, 2 - DFS]: ").strip().upper()
            if choice in ('BFS', '1', ''):
                return 'BFS'
            if choice in ('DFS', '2'):
                return 'DFS'
            print(f"{COLOR_RED}Błąd: Nieprawidłowy wybór. Wpisz BFS lub DFS.{COLOR_RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\nPrzerwano wprowadzanie danych.")
            sys.exit(0)


def resolve_maze_path(path_arg: Optional[str]) -> str:
    """Wyszukuje plik mapy w bieżącym katalogu lub podkatalogu 'mazes'."""
    if path_arg:
        # 1. Ścieżka bezpośrednia
        if os.path.isfile(path_arg):
            return path_arg

        # 2. W podkatalogu mazes/ względem skryptu
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cand_in_mazes = os.path.join(script_dir, "mazes", path_arg)
        if os.path.isfile(cand_in_mazes):
            return cand_in_mazes

        # 3. Względem skryptu
        cand_script = os.path.join(script_dir, path_arg)
        if os.path.isfile(cand_script):
            return cand_script

        raise FileNotFoundError(f"Nie znaleziono pliku mapy: {path_arg}")

    # Jeśli nie podano argumentu, spróbuj znaleźć mapy w podkatalogu mazes/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mazes_dir = os.path.join(script_dir, "mazes")
    candidates = []
    if os.path.isdir(mazes_dir):
        candidates = sorted([os.path.join(mazes_dir, f) for f in os.listdir(mazes_dir) if f.endswith('.txt')])

    if candidates:
        print(f"{COLOR_CYAN}Dostępne mapy:{COLOR_RESET}")
        for idx, cand in enumerate(candidates, start=1):
            print(f"  {idx}. {os.path.basename(cand)}")
        try:
            ans = input("Wybierz numer mapy lub podaj ścieżkę do pliku [1]: ").strip()
            if not ans or ans == '1':
                return candidates[0]
            if ans.isdigit() and 1 <= int(ans) <= len(candidates):
                return candidates[int(ans) - 1]
            return resolve_maze_path(ans)
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

    raise ValueError("Nie podano ścieżki do pliku z mapą labiryntu.")


def run_animation(
    maze: Maze,
    start: Tuple[int, int],
    end: Tuple[int, int],
    algo: str,
    delay: float = 0.100,
    animate: bool = True
) -> SearchStep:
    """Uruchamia animację przeszukiwania z kolorowaniem ANSI."""
    last_step: Optional[SearchStep] = None

    if animate and sys.stdout.isatty():
        clear_screen()
        hide_cursor()

    try:
        for step in search_generator(maze, start, end, algo):
            last_step = step

            if animate and sys.stdout.isatty():
                move_cursor_home()
                status_header = (
                    f"{COLOR_BOLD}Algorytm: {algo}{COLOR_RESET} | "
                    f"Krok: {step.step_num:4d} | "
                    f"Odwiedzone: {len(step.visited):4d} | "
                    f"W kolejce: {len(step.frontier):4d}\n"
                    f"Legenda: {COLOR_RED}[■] Start{COLOR_RESET}  "
                    f"{COLOR_BLUE}[■] Koniec{COLOR_RESET}  "
                    f"{COLOR_GREEN}[■] Odwiedzone{COLOR_RESET}  "
                    f"{COLOR_YELLOW}[■] W kolejce{COLOR_RESET}  "
                    f"[■] Normalne"
                )
                print(status_header)
                print(
                    maze.render_view(
                        start=start,
                        end=end,
                        visited=step.visited,
                        frontier=step.frontier,
                        show_coords=True
                    )
                )
                sys.stdout.flush()
                if delay > 0 and not step.is_done:
                    time.sleep(delay)

    finally:
        if animate and sys.stdout.isatty():
            show_cursor()

    assert last_step is not None
    return last_step


def display_summary(
    maze: Maze,
    start: Tuple[int, int],
    end: Tuple[int, int],
    algo: str,
    final_step: SearchStep
) -> None:
    """Wyświetla podsumowanie poszukiwania ścieżki i ostateczny widok labiryntu."""
    print("\n" + "=" * 62)
    if final_step.found:
        print(f"{COLOR_GREEN}{COLOR_BOLD}✓ SUKCES: ZNALEZIONO ŚCIEŻKĘ MIĘDZY WYBRANYMI POLAMI!{COLOR_RESET}")
    else:
        print(f"{COLOR_RED}{COLOR_BOLD}✗ BRAK ŚCIEŻKI MIĘDZY WYBRANYMI POLAMI!{COLOR_RESET}")
    print("-" * 62)
    print(f"  • Zastosowany algorytm:            {COLOR_BOLD}{algo}{COLOR_RESET}")
    print(f"  • Współrzędne startowe (czerwony): {start}")
    print(f"  • Współrzędne końcowe (niebieski): {end}")
    print(f"  • Ilość wykonanych kroków:          {COLOR_BOLD}{final_step.step_num}{COLOR_RESET}")
    print(f"  • Łączna liczba odwiedzonych pól:   {len(final_step.visited)}")

    if final_step.found:
        path = final_step.path
        path_len = len(path) - 1
        print(f"  • Długość znalezionej ścieżki:     {COLOR_CYAN}{COLOR_BOLD}{path_len}{COLOR_RESET} kroków ({len(path)} pól)")
        
        # Formatowanie listy współrzędnych ścieżki
        if len(path) <= 15:
            path_str = " -> ".join(f"({r},{c})" for r, c in path)
        else:
            head = " -> ".join(f"({r},{c})" for r, c in path[:6])
            tail = " -> ".join(f"({r},{c})" for r, c in path[-6:])
            path_str = f"{head} -> ... -> {tail}"
        print(f"  • Przebieg ścieżki: {path_str}")

        print("\n" + f"{COLOR_CYAN}Końcowa mapa z zaznaczoną odnalezioną trasą (turkusowy):{COLOR_RESET}")
        print(
            maze.render_view(
                start=start,
                end=end,
                visited=final_step.visited,
                frontier=final_step.frontier,
                path=path,
                show_coords=True
            )
        )
    else:
        print(f"  • Przyczyna: Brak połączenia w labiryncie (różne składowe spójności).")

    print("=" * 62 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Szukanie drogi w labiryncie za pomocą BFS i DFS (PSI - Ćwiczenia 1)."
    )
    parser.add_argument("map", nargs="?", help="Ścieżka do pliku z mapą labiryntu (np. maze1.txt)")
    parser.add_argument("--start", nargs=2, type=int, metavar=("ROW", "COL"), help="Współrzędne startowe (wiersz kolumna)")
    parser.add_argument("--end", nargs=2, type=int, metavar=("ROW", "COL"), help="Współrzędne końcowe (wiersz kolumna)")
    parser.add_argument("--algo", choices=["BFS", "DFS", "bfs", "dfs"], help="Rodzaj algorytmu (BFS lub DFS)")
    parser.add_argument("--delay", type=float, default=0.100, help="Opóźnienie animacji w sekundach (domyślnie 0.100s = 100 ms)")
    parser.add_argument("--no-anim", action="store_true", help="Wyłącza animację i wyświetla od razu wynik")
    parser.add_argument("--gui", action="store_true", help="Uruchamia graficzny interfejs użytkownika (GUI)")

    args = parser.parse_args()

    # Opcjonalne uruchomienie wersji GUI
    if args.gui:
        try:
            import gui
            map_path = resolve_maze_path(args.map) if args.map else None
            gui.run_gui(map_path)
            return
        except Exception as e:
            print(f"{COLOR_RED}Nie udało się uruchomić GUI ({e}). Uruchamiam wersję terminalową.{COLOR_RESET}")

    # Wczytanie mapy
    map_path = resolve_maze_path(args.map)
    try:
        maze = Maze.load_from_file(map_path)
    except Exception as e:
        print(f"{COLOR_RED}Błąd podczas wczytywania pliku mapy: {e}{COLOR_RESET}")
        sys.exit(1)

    # Wyświetlenie mapy i informacji wstępnych
    print(f"\n{COLOR_BOLD}=== Podstawy sztucznej inteligencji - Ćwiczenia 1 ==={COLOR_RESET}")
    print(f"Wczytano mapę: {COLOR_CYAN}{os.path.basename(map_path)}{COLOR_RESET}")
    print(f"Rozmiar labiryntu: {maze.height} wierszy x {maze.width} kolumn\n")
    print(maze.render_view(show_coords=True))
    print()

    # Pobranie współrzędnych i algorytmu (z argumentów CLI lub interaktywnie)
    if args.start:
        start_coord = (args.start[0], args.start[1])
        if not maze.is_in_bounds(*start_coord) or not maze.is_passable(*start_coord):
            print(f"{COLOR_RED}Błąd: Podany start {start_coord} jest nieprawidłowy.{COLOR_RESET}")
            sys.exit(1)
    else:
        start_coord = parse_coords_input("Podaj współrzędne startowe (wiersz kolumna)", maze)

    if args.end:
        end_coord = (args.end[0], args.end[1])
        if not maze.is_in_bounds(*end_coord) or not maze.is_passable(*end_coord):
            print(f"{COLOR_RED}Błąd: Podany koniec {end_coord} jest nieprawidłowy.{COLOR_RESET}")
            sys.exit(1)
    else:
        end_coord = parse_coords_input("Podaj współrzędne końcowe (wiersz kolumna)", maze)

    if args.algo:
        algo_choice = args.algo.upper()
    else:
        algo_choice = prompt_algorithm()

    animate = not args.no_anim
    delay = args.delay

    print(f"\nRozpoczynanie poszukiwania ścieżki za pomocą {COLOR_BOLD}{algo_choice}{COLOR_RESET}...")
    time.sleep(0.5)

    final_step = run_animation(
        maze=maze,
        start=start_coord,
        end=end_coord,
        algo=algo_choice,
        delay=delay,
        animate=animate
    )

    display_summary(maze, start_coord, end_coord, algo_choice, final_step)


if __name__ == "__main__":
    main()
