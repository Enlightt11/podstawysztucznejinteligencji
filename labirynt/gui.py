"""
Graficzny interfejs użytkownika (GUI) oparty na standardowej bibliotece tkinter.
Zgodny ze specyfikacją: Podstawy sztucznej inteligencji - Ćwiczenia 1.
Umożliwia wizualizację BFS i DFS, wybór punktu startowego i końcowego myszą lub z pól tekstowych,
regulację prędkości animacji oraz kontrolę kroków (Start, Pauza, Krok, Reset).
"""

import os
import sys
from typing import Optional, Tuple, Set, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from maze import Maze, TILE_ACTIONS
from solver import search_generator, SearchStep


# Kolory zgodne ze specyfikacją zadania
COLOR_BG = "#1E1E2E"
COLOR_CANVAS_BG = "#181825"
COLOR_START = "#F38BA8"      # czerwony
COLOR_END = "#89B4FA"        # niebieski
COLOR_VISITED = "#A6E3A1"    # zielony
COLOR_FRONTIER = "#F9E2AF"   # żółty
COLOR_PATH = "#94E2D5"       # turkusowy / cyan
COLOR_NORMAL = "#CDD6F4"     # domyślny / jasny
COLOR_WALL = "#313244"       # tło pustych pól
COLOR_GRID = "#45475A"


class MazeGUI:
    def __init__(self, root: tk.Tk, initial_map_path: Optional[str] = None):
        self.root = root
        self.root.title("PSI - Ćwiczenia 1: Labirynt (BFS / DFS)")
        self.root.geometry("1024x768")
        self.root.configure(bg=COLOR_BG)

        self.maze: Optional[Maze] = None
        self.start_coord: Optional[Tuple[int, int]] = None
        self.end_coord: Optional[Tuple[int, int]] = None
        self.search_gen = None
        self.is_running = False
        self.after_id = None

        self.visited_set: Set[Tuple[int, int]] = set()
        self.frontier_set: Set[Tuple[int, int]] = set()
        self.path: List[Tuple[int, int]] = []
        self.current_step: int = 0

        self.cell_size = 24

        self._build_ui()

        # Załaduj początkową mapę jeśli podano
        if initial_map_path and os.path.isfile(initial_map_path):
            self.load_maze(initial_map_path)
        else:
            default_map = os.path.join(os.path.dirname(__file__), "mazes", "maze2.txt")
            if os.path.isfile(default_map):
                self.load_maze(default_map)

    def _build_ui(self) -> None:
        # Pasek boczny ze sterowaniem
        control_panel = tk.Frame(self.root, bg=COLOR_BG, width=280, padx=12, pady=12)
        control_panel.pack(side=tk.LEFT, fill=tk.Y)

        title_lbl = tk.Label(
            control_panel,
            text="Wyszukiwanie drogi\nw labiryncie",
            font=("Helvetica", 14, "bold"),
            bg=COLOR_BG,
            fg="#BAC2DE"
        )
        title_lbl.pack(pady=(0, 15))

        # Wybór mapy
        map_btn = tk.Button(
            control_panel,
            text="📁 Wczytaj inną mapę...",
            command=self.open_file_dialog,
            bg="#313244",
            fg="#CDD6F4",
            activebackground="#45475A",
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        map_btn.pack(fill=tk.X, pady=(0, 15))

        self.map_info_lbl = tk.Label(
            control_panel,
            text="Brak mapy",
            font=("Helvetica", 9),
            bg=COLOR_BG,
            fg="#A6ADC8"
        )
        self.map_info_lbl.pack(pady=(0, 15))

        # Wybór algorytmu
        algo_frame = tk.LabelFrame(
            control_panel,
            text=" Algorytm ",
            bg=COLOR_BG,
            fg="#CDD6F4",
            padx=8,
            pady=8
        )
        algo_frame.pack(fill=tk.X, pady=(0, 15))

        self.algo_var = tk.StringVar(value="BFS")
        rb_bfs = tk.Radiobutton(
            algo_frame,
            text="BFS (wszerz - FIFO)",
            variable=self.algo_var,
            value="BFS",
            bg=COLOR_BG,
            fg="#CDD6F4",
            selectcolor="#313244",
            activebackground=COLOR_BG
        )
        rb_bfs.pack(anchor=tk.W)

        rb_dfs = tk.Radiobutton(
            algo_frame,
            text="DFS (w głąb - LIFO)",
            variable=self.algo_var,
            value="DFS",
            bg=COLOR_BG,
            fg="#CDD6F4",
            selectcolor="#313244",
            activebackground=COLOR_BG
        )
        rb_dfs.pack(anchor=tk.W)

        # Współrzędne Start / Koniec
        coords_frame = tk.LabelFrame(
            control_panel,
            text=" Punkty (wiersz, kolumna) ",
            bg=COLOR_BG,
            fg="#CDD6F4",
            padx=8,
            pady=8
        )
        coords_frame.pack(fill=tk.X, pady=(0, 15))

        # Start
        start_row_frame = tk.Frame(coords_frame, bg=COLOR_BG)
        start_row_frame.pack(fill=tk.X, pady=2)
        tk.Label(start_row_frame, text="Start (czerwony):", bg=COLOR_BG, fg=COLOR_START, width=14, anchor=tk.W).pack(side=tk.LEFT)
        self.start_entry = tk.Entry(start_row_frame, width=8, bg="#313244", fg="#CDD6F4", insertbackground="white")
        self.start_entry.pack(side=tk.RIGHT)

        # Koniec
        end_row_frame = tk.Frame(coords_frame, bg=COLOR_BG)
        end_row_frame.pack(fill=tk.X, pady=2)
        tk.Label(end_row_frame, text="Koniec (niebieski):", bg=COLOR_BG, fg=COLOR_END, width=14, anchor=tk.W).pack(side=tk.LEFT)
        self.end_entry = tk.Entry(end_row_frame, width=8, bg="#313244", fg="#CDD6F4", insertbackground="white")
        self.end_entry.pack(side=tk.RIGHT)

        hint_lbl = tk.Label(
            coords_frame,
            text="Wskazówka: Kliknij LPM na labiryncie,\naby ustawić Start, PPM dla Końca.",
            font=("Helvetica", 8),
            bg=COLOR_BG,
            fg="#6C7086",
            justify=tk.LEFT
        )
        hint_lbl.pack(anchor=tk.W, pady=(4, 0))

        # Prędkość animacji
        speed_frame = tk.LabelFrame(
            control_panel,
            text=" Opóźnienie animacji (ms) ",
            bg=COLOR_BG,
            fg="#CDD6F4",
            padx=8,
            pady=8
        )
        speed_frame.pack(fill=tk.X, pady=(0, 15))

        self.delay_slider = tk.Scale(
            speed_frame,
            from_=10,
            to=300,
            orient=tk.HORIZONTAL,
            bg=COLOR_BG,
            fg="#CDD6F4",
            highlightthickness=0,
            troughcolor="#313244"
        )
        self.delay_slider.set(100)  # 100 ms zgodnie ze specyfikacją zadania
        self.delay_slider.pack(fill=tk.X)

        # Przyciski akcji
        btn_frame = tk.Frame(control_panel, bg=COLOR_BG)
        btn_frame.pack(fill=tk.X, pady=(0, 15))

        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start",
            command=self.toggle_run,
            bg="#A6E3A1",
            fg="#11111B",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=6
        )
        self.start_btn.pack(fill=tk.X, pady=2)

        self.step_btn = tk.Button(
            btn_frame,
            text="⏭ Krok",
            command=self.single_step,
            bg="#89B4FA",
            fg="#11111B",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=4
        )
        self.step_btn.pack(fill=tk.X, pady=2)

        self.reset_btn = tk.Button(
            btn_frame,
            text="↺ Reset",
            command=self.reset_search,
            bg="#F38BA8",
            fg="#11111B",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=4
        )
        self.reset_btn.pack(fill=tk.X, pady=2)

        # Statystyki i status
        stats_frame = tk.LabelFrame(
            control_panel,
            text=" Statystyki ",
            bg=COLOR_BG,
            fg="#CDD6F4",
            padx=8,
            pady=8
        )
        stats_frame.pack(fill=tk.X)

        self.step_stat_lbl = tk.Label(stats_frame, text="Kroki: 0", bg=COLOR_BG, fg="#CDD6F4", anchor=tk.W)
        self.step_stat_lbl.pack(fill=tk.X)

        self.visited_stat_lbl = tk.Label(stats_frame, text="Odwiedzone: 0", bg=COLOR_BG, fg=COLOR_VISITED, anchor=tk.W)
        self.visited_stat_lbl.pack(fill=tk.X)

        self.frontier_stat_lbl = tk.Label(stats_frame, text="W kolejce: 0", bg=COLOR_BG, fg=COLOR_FRONTIER, anchor=tk.W)
        self.frontier_stat_lbl.pack(fill=tk.X)

        self.status_lbl = tk.Label(
            stats_frame,
            text="Status: Gotowy",
            font=("Helvetica", 9, "bold"),
            bg=COLOR_BG,
            fg="#89DCEB",
            anchor=tk.W,
            wraplength=230
        )
        self.status_lbl.pack(fill=tk.X, pady=(6, 0))

        # Główny obszar z płótnem Canvas
        main_canvas_frame = tk.Frame(self.root, bg=COLOR_CANVAS_BG)
        main_canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            main_canvas_frame,
            bg=COLOR_CANVAS_BG,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

    def load_maze(self, filepath: str) -> None:
        """Ładuje nową mapę labiryntu i odświeża interfejs."""
        try:
            self.maze = Maze.load_from_file(filepath)
            self.map_info_lbl.config(
                text=f"{os.path.basename(filepath)}\n{self.maze.height} wierszy x {self.maze.width} kolumn"
            )
            # Znajdź domyślne punkty start i koniec
            self.start_coord = None
            self.end_coord = None
            for r in range(self.maze.height):
                for c in range(self.maze.width):
                    if self.maze.is_passable(r, c):
                        if self.start_coord is None:
                            self.start_coord = (r, c)
                        else:
                            self.end_coord = (r, c)

            if self.start_coord:
                self.start_entry.delete(0, tk.END)
                self.start_entry.insert(0, f"{self.start_coord[0]} {self.start_coord[1]}")
            if self.end_coord:
                self.end_entry.delete(0, tk.END)
                self.end_entry.insert(0, f"{self.end_coord[0]} {self.end_coord[1]}")

            self.reset_search()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać mapy:\n{e}")

    def open_file_dialog(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        init_dir = os.path.join(script_dir, "mazes")
        path = filedialog.askopenfilename(
            initialdir=init_dir,
            title="Wybierz plik labiryntu",
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        if path:
            self.load_maze(path)

    def on_left_click(self, event) -> None:
        """Ustawia punkt startowy lewym przyciskiem myszy."""
        pos = self._get_coord_at(event.x, event.y)
        if pos and self.maze and self.maze.is_passable(*pos):
            self.start_coord = pos
            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, f"{pos[0]} {pos[1]}")
            self.reset_search()

    def on_right_click(self, event) -> None:
        """Ustawia punkt końcowy prawym przyciskiem myszy."""
        pos = self._get_coord_at(event.x, event.y)
        if pos and self.maze and self.maze.is_passable(*pos):
            self.end_coord = pos
            self.end_entry.delete(0, tk.END)
            self.end_entry.insert(0, f"{pos[0]} {pos[1]}")
            self.reset_search()

    def _get_coord_at(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        if not self.maze:
            return None
        # Uwzględnienie marginesu (1 kratka) na nagłówki wierszy i kolumn
        c = (px // self.cell_size) - 1
        r = (py // self.cell_size) - 1
        if self.maze.is_in_bounds(r, c):
            return r, c
        return None

    def draw_maze(self) -> None:
        """Rysuje labirynt na płótnie Canvas wraz z numeracją osi i kolorowaniem pól."""
        self.canvas.delete("all")
        if not self.maze:
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w > 10 and canvas_h > 10:
            max_cs_w = max(12, canvas_w // (self.maze.width + 2))
            max_cs_h = max(12, canvas_h // (self.maze.height + 2))
            self.cell_size = min(max_cs_w, max_cs_h, 36)

        cs = self.cell_size
        font_size = max(8, int(cs * 0.7))
        coord_font_size = max(7, int(cs * 0.4))

        # Rysowanie pełnych numerów kolumn na górze (0 .. width-1)
        for c in range(self.maze.width):
            cx = (c + 1) * cs + cs // 2
            cy = cs // 2
            self.canvas.create_text(
                cx, cy,
                text=str(c),
                fill="#A6ADC8",
                font=("Helvetica", coord_font_size, "bold")
            )

        # Rysowanie pełnych numerów wierszy po lewej (0 .. height-1)
        for r in range(self.maze.height):
            cx = cs // 2
            cy = (r + 1) * cs + cs // 2
            self.canvas.create_text(
                cx, cy,
                text=str(r),
                fill="#A6ADC8",
                font=("Helvetica", coord_font_size, "bold")
            )

        path_set = set(self.path)

        for r in range(self.maze.height):
            for c in range(self.maze.width):
                pos = (r, c)
                tile = self.maze.grid[r][c]
                x1 = (c + 1) * cs
                y1 = (r + 1) * cs
                x2 = x1 + cs
                y2 = y1 + cs

                # Ustalenie koloru tła i tekstu
                if pos == self.start_coord:
                    bg_col = COLOR_START
                    fg_col = "#11111B"
                elif pos == self.end_coord:
                    bg_col = COLOR_END
                    fg_col = "#11111B"
                elif pos in path_set:
                    bg_col = COLOR_PATH
                    fg_col = "#11111B"
                elif pos in self.visited_set:
                    bg_col = COLOR_VISITED
                    fg_col = "#11111B"
                elif pos in self.frontier_set:
                    bg_col = COLOR_FRONTIER
                    fg_col = "#11111B"
                elif tile != ' ':
                    bg_col = "#313244"
                    fg_col = COLOR_NORMAL
                else:
                    bg_col = COLOR_CANVAS_BG
                    fg_col = COLOR_GRID

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_col, outline=COLOR_GRID, width=1)
                if tile != ' ':
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=tile,
                        fill=fg_col,
                        font=("DejaVu Sans", font_size, "bold")
                    )

    def _parse_entry_coords(self) -> bool:
        if not self.maze:
            return False
        try:
            st_parts = [int(x) for x in self.start_entry.get().replace(',', ' ').split()]
            en_parts = [int(x) for x in self.end_entry.get().replace(',', ' ').split()]
            if len(st_parts) != 2 or len(en_parts) != 2:
                messagebox.showerror("Błąd", "Podaj współrzędne w formacie 'wiersz kolumna'.")
                return False
            self.start_coord = (st_parts[0], st_parts[1])
            self.end_coord = (en_parts[0], en_parts[1])
            return True
        except ValueError:
            messagebox.showerror("Błąd", "Współrzędne muszą być liczbami całkowitymi.")
            return False

    def toggle_run(self) -> None:
        if self.is_running:
            self.pause_search()
        else:
            self.start_search()

    def start_search(self) -> None:
        if not self._parse_entry_coords():
            return
        if not self.search_gen:
            algo = self.algo_var.get()
            self.search_gen = search_generator(self.maze, self.start_coord, self.end_coord, algo)

        self.is_running = True
        self.start_btn.config(text="⏸ Pauza", bg="#FAB387")
        self.status_lbl.config(text=f"Szukanie ({self.algo_var.get()})...", fg="#F9E2AF")
        self._step_loop()

    def pause_search(self) -> None:
        self.is_running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.start_btn.config(text="▶ Wznów", bg="#A6E3A1")
        self.status_lbl.config(text="Wstrzymano", fg="#F9E2AF")

    def single_step(self) -> None:
        if not self.search_gen:
            if not self._parse_entry_coords():
                return
            algo = self.algo_var.get()
            self.search_gen = search_generator(self.maze, self.start_coord, self.end_coord, algo)

        self._execute_one_step()

    def _step_loop(self) -> None:
        if not self.is_running:
            return

        is_finished = self._execute_one_step()
        if not is_finished and self.is_running:
            delay = int(self.delay_slider.get())
            self.after_id = self.root.after(delay, self._step_loop)

    def _execute_one_step(self) -> bool:
        if not self.search_gen:
            return True

        try:
            step: SearchStep = next(self.search_gen)
            self.current_step = step.step_num
            self.visited_set = step.visited
            self.frontier_set = step.frontier

            self.step_stat_lbl.config(text=f"Kroki: {step.step_num}")
            self.visited_stat_lbl.config(text=f"Odwiedzone: {len(step.visited)}")
            self.frontier_stat_lbl.config(text=f"W kolejce: {len(step.frontier)}")

            if step.is_done:
                self.is_running = False
                self.start_btn.config(text="▶ Start", bg="#A6E3A1")
                if step.found:
                    self.path = step.path
                    self.status_lbl.config(
                        text=f"✓ Znaleziono ścieżkę!\nDługość: {len(step.path) - 1} kroków",
                        fg="#A6E3A1"
                    )
                else:
                    self.path = []
                    self.status_lbl.config(
                        text="✗ Brak ścieżki między polami!",
                        fg="#F38BA8"
                    )
                self.draw_maze()
                return True

            self.draw_maze()
            return False

        except StopIteration:
            self.is_running = False
            self.start_btn.config(text="▶ Start", bg="#A6E3A1")
            return True

    def reset_search(self) -> None:
        self.is_running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.search_gen = None
        self.visited_set.clear()
        self.frontier_set.clear()
        self.path.clear()
        self.current_step = 0
        self.step_stat_lbl.config(text="Kroki: 0")
        self.visited_stat_lbl.config(text="Odwiedzone: 0")
        self.frontier_stat_lbl.config(text="W kolejce: 0")
        self.status_lbl.config(text="Status: Gotowy", fg="#89DCEB")
        self.start_btn.config(text="▶ Start", bg="#A6E3A1")
        self.draw_maze()


def run_gui(initial_map_path: Optional[str] = None) -> None:
    """Uruchamia aplikację graficzną."""
    root = tk.Tk()
    app = MazeGUI(root, initial_map_path)
    root.mainloop()


if __name__ == "__main__":
    map_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_gui(map_arg)
