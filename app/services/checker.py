def normalize(s: str) -> str:
    return s.strip().lower().replace(",", ".").replace(" ", "")


def check_answer(submitted: str, correct: str) -> bool:
    """Сравнивает ответы пользователя и эталонный.
    Допускает разный регистр, лишние пробелы и запятую вместо точки.
    Если оба числовые — сравнивает как числа с точностью 1e-6."""
    a, b = normalize(submitted), normalize(correct)
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) < 1e-6
    except ValueError:
        return False
