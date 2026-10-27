#!/usr/bin/env python3
"""
System ekspercki: Diagnostyka samochodu
=======================================
Program oparty na regułach IF-THEN.
Parsuje bazę wiedzy z pliku JSON, zadaje pytania użytkownikowi
i wyświetla pasujące diagnozy.
"""

import json
import sys
import os


def load_knowledge_base(filepath: str) -> dict:
    """Wczytuje bazę wiedzy z pliku JSON."""
    if not os.path.exists(filepath):
        print(f"BŁĄD: Plik '{filepath}' nie istnieje.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def ask_question(question_id: str, question_data: dict) -> str:
    """Zadaje pytanie użytkownikowi i zwraca wybraną odpowiedź."""
    print(f"\n{'='*60}")
    print(f"  {question_id}: {question_data['text']}")
    print(f"{'='*60}")

    answers = question_data["answers"]
    for i, answer in enumerate(answers, 1):
        # Zamień podkreślniki na spacje dla czytelności
        display = answer.replace("_", " ")
        print(f"  [{i}] {display}")

    while True:
        try:
            choice = input(f"\nTwój wybór (1-{len(answers)}): ").strip()
            idx = int(choice)
            if 1 <= idx <= len(answers):
                selected = answers[idx - 1]
                print(f"  ➜ Wybrano: {selected.replace('_', ' ')}")
                return selected
            else:
                print(f"  ⚠ Podaj liczbę od 1 do {len(answers)}.")
        except ValueError:
            print(f"  ⚠ Podaj liczbę od 1 do {len(answers)}.")
        except (EOFError, KeyboardInterrupt):
            print("\n\nPrzerwano działanie programu.")
            sys.exit(0)


def match_rules(rules: list, user_answers: dict) -> list:
    """
    Dopasowuje reguły IF-THEN do odpowiedzi użytkownika.
    Reguła pasuje, gdy WSZYSTKIE warunki w 'if' zgadzają się z odpowiedziami.
    """
    matched = []
    for rule in rules:
        conditions = rule["if"]
        # Sprawdź, czy każdy warunek reguły zgadza się z odpowiedzią użytkownika
        all_match = True
        for question_id, expected_answer in conditions.items():
            if user_answers.get(question_id) != expected_answer:
                all_match = False
                break

        if all_match:
            matched.append(rule)

    return matched


def display_results(matched_rules: list):
    """Wyświetla wyniki dopasowania reguł."""
    print(f"\n{'#'*60}")
    print(f"  WYNIKI DIAGNOSTYKI")
    print(f"{'#'*60}")

    if not matched_rules:
        print("""
  Nie znaleziono pasujących reguł dla podanych odpowiedzi.

  Możliwe przyczyny:
  • Problem nie jest objęty bazą wiedzy systemu
  • Kombinacja objawów jest nietypowa

  Zalecenie: Odwiedź autoryzowany serwis w celu dokładnej diagnostyki.
""")
        return

    print(f"\n  Znaleziono {len(matched_rules)} pasującą(-e/-ych) regułę(-y):\n")

    for i, rule in enumerate(matched_rules, 1):
        result = rule["then"]
        rule_id = rule.get("id", f"R{i}")

        # Wyświetl warunki reguły
        conditions = rule["if"]
        conditions_str = ", ".join(
            f"{qid}={val.replace('_', ' ')}" for qid, val in conditions.items()
        )

        print(f"  ┌─────────────────────────────────────────────────────────")
        print(f"  │ Reguła {rule_id}")
        print(f"  │ Warunki: {conditions_str}")
        print(f"  ├─────────────────────────────────────────────────────────")
        print(f"  │ 🔍 Diagnoza:")
        print(f"  │    {result['diagnosis']}")
        print(f"  │")
        print(f"  │ 🔧 Zalecane działanie:")
        # Zawijaj długie linie akcji
        action = result["action"]
        words = action.split()
        line = "  │    "
        for word in words:
            if len(line) + len(word) + 1 > 70:
                print(line)
                line = "  │    " + word
            else:
                line += " " + word if line.strip() != "│" else word
        if line.strip() != "│":
            print(line)
        print(f"  └─────────────────────────────────────────────────────────\n")


def main():
    """Główna funkcja programu."""
    # Ustal ścieżkę do bazy wiedzy (obok skryptu)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(script_dir, "knowledge_base.json")

    print("""
╔══════════════════════════════════════════════════════════╗
║       SYSTEM EKSPERCKI: DIAGNOSTYKA SAMOCHODU           ║
║       ──────────────────────────────────────             ║
║       Oparty na regułach IF-THEN                        ║
╚══════════════════════════════════════════════════════════╝

  Odpowiedz na poniższe pytania, aby zdiagnozować
  problem z Twoim samochodem.
""")

    # Wczytaj bazę wiedzy
    kb = load_knowledge_base(kb_path)
    questions = kb["questions"]
    rules = kb["rules"]

    print(f"  📋 Załadowano {len(questions)} pytań i {len(rules)} reguł.\n")

    # Zbierz odpowiedzi od użytkownika
    user_answers = {}
    for qid in sorted(questions.keys(), key=lambda x: int(x[1:])):
        answer = ask_question(qid, questions[qid])
        user_answers[qid] = answer

    # Dopasuj reguły
    matched = match_rules(rules, user_answers)

    # Wyświetl wyniki
    display_results(matched)

    # Podsumowanie odpowiedzi
    print(f"\n{'─'*60}")
    print("  Twoje odpowiedzi:")
    for qid in sorted(user_answers.keys(), key=lambda x: int(x[1:])):
        q_text = questions[qid]["text"]
        a_text = user_answers[qid].replace("_", " ")
        print(f"    {qid}: {q_text}")
        print(f"         ➜ {a_text}")
    print(f"{'─'*60}")


if __name__ == "__main__":
    main()
