import random
import sys

# Parametry (możesz zmienić N w konsoli: python3 hetman.py 4)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
POP_SIZE = 100    # Rozmiar populacji
MAX_ITER = 10000  # Maksymalna liczba iteracji
CX_RATE = 0.8     # 80% populacji do krzyżowania
MUT_RATE = 0.25   # 25% populacji do mutacji

if N in (2, 3):
    print(f"Dla N={N} brak rozwiązań problemu N-hetmanów!")
    sys.exit()

# 1. Funkcja oceny: liczba par atakujących się hetmanów (chcemy błąd = 0)
def count_conflicts(board):
    conflicts = 0
    for i in range(N):
        for j in range(i + 1, N):
            # ta sama kolumna lub ta sama przekątna
            if board[i] == board[j] or abs(board[i] - board[j]) == (j - i):
                conflicts += 1
    return conflicts

# Funkcja rysująca szachownicę w konsoli
def print_board(board):
    print("   " + "".join(chr(ord('A') + i) for i in range(N)))
    for r in range(N):
        row = "".join("X" if board[r] == c else "." for c in range(N))
        print(f"{r + 1:2d} {row}")

# 2. Inicjalizacja: losowa populacja konfiguracji hetmanów
# Każdy osobnik to lista N liczb: indeks = wiersz, wartość = kolumna
population = [[random.randint(0, N - 1) for _ in range(N)] for _ in range(POP_SIZE)]

# Główna pętla algorytmu genetycznego
for it in range(1, MAX_ITER + 1):
    # 3. Krzyżowanie (jednopunktowe)
    offspring = []
    for _ in range(int(POP_SIZE * CX_RATE / 2)):
        p1, p2 = random.choice(population), random.choice(population)
        cut = random.randint(1, N - 1)
        offspring.append(p1[:cut] + p2[cut:])
        offspring.append(p2[:cut] + p1[cut:])
    population.extend(offspring)

    # 4. Mutacja: losowy wiersz otrzymuje losową nową kolumnę
    for _ in range(int(POP_SIZE * MUT_RATE)):
        idx = random.randrange(len(population))
        population[idx] = list(population[idx])
        population[idx][random.randint(0, N - 1)] = random.randint(0, N - 1)

    # 5. Ocena przystosowania każdej konfiguracji
    evaluated = [(ind, count_conflicts(ind)) for ind in population]

    # 6. Selekcja: sortowanie od najmniejszego błędu i obcięcie do rozmiaru populacji
    evaluated.sort(key=lambda x: x[1])
    min_error = evaluated[0][1]
    best_board = evaluated[0][0]
    population = [ind for ind, _ in evaluated[:POP_SIZE]]

    print(f"Iteracja: {it}. Minimalny błąd: {min_error}")

    # Warunek stopu: znaleziono konfigurację bez żadnych ataków
    if min_error == 0:
        print(f"Iteracja: {it} - odnaleziono ustawienie!")
        print("Lista:", ", ".join(map(str, best_board)))
        print()
        print_board(best_board)
        break

