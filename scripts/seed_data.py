"""Заполняет БД демо-задачами и админом.

Запуск: python -m scripts.seed_data
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Task, User
from app.services.gamification import ensure_achievements_seeded
from app.services.schema import ensure_schema_updates

DEMO_TASKS = [
    {
        "title": "Перевод в двоичную систему",
        "description": "Переведите число 45 из десятичной системы в двоичную. В ответе укажите полученное число без пробелов.",
        "topic": "Системы счисления",
        "difficulty": 800,
        "answer": "101101",
        "explanation": "45 = 32 + 8 + 4 + 1 = 101101₂",
        "xp_reward": 10,
    },
    {
        "title": "Логические выражения",
        "description": "Сколько различных решений имеет уравнение (A∨B)∧(¬A∨C)=1, где A, B, C — логические переменные?",
        "topic": "Логика",
        "difficulty": 1100,
        "answer": "5",
        "explanation": "Полный перебор 8 наборов: подходят (0,1,0),(0,1,1),(1,0,1),(1,1,1),(1,1,0) — итого 5.",
        "xp_reward": 15,
    },
    {
        "title": "Скорость передачи данных",
        "description": "Файл размером 5 Мбайт передаётся по каналу со скоростью 2^20 бит/с. Сколько секунд займёт передача?",
        "topic": "Информация",
        "difficulty": 900,
        "answer": "40",
        "explanation": "5 Мбайт = 5·2^23 бит. Делим на 2^20 = 5·2^3 = 40 с.",
        "xp_reward": 12,
    },
    {
        "title": "Алгоритм Евклида",
        "description": "Найдите НОД(252, 198) с помощью алгоритма Евклида.",
        "topic": "Алгоритмы",
        "difficulty": 700,
        "answer": "18",
        "explanation": "252 mod 198 = 54; 198 mod 54 = 36; 54 mod 36 = 18; 36 mod 18 = 0 → НОД = 18.",
        "xp_reward": 10,
    },
    {
        "title": "Кодирование Хаффмана",
        "description": "Для кодирования сообщения используется неравномерный двоичный код. А=0, Б=10, В=110. Какова минимальная длина кода для буквы Г, чтобы код оставался префиксным?",
        "topic": "Кодирование",
        "difficulty": 1200,
        "answer": "3",
        "explanation": "111 — единственный свободный префикс длины 3.",
        "xp_reward": 18,
    },
    {
        "title": "Циклы — сумма",
        "description": "Что выведет программа:\n s = 0\n for i in range(1, 11):\n   s += i\n print(s)",
        "topic": "Программирование",
        "difficulty": 600,
        "answer": "55",
        "explanation": "Сумма 1+2+...+10 = 55.",
        "xp_reward": 8,
    },
    {
        "title": "Графы — кратчайший путь",
        "description": "В графе 5 вершин. Веса рёбер: A-B=3, A-C=1, B-D=2, C-D=5, C-E=4, D-E=1. Найдите длину кратчайшего пути из A в E.",
        "topic": "Графы",
        "difficulty": 1300,
        "answer": "6",
        "explanation": "A→B→D→E = 3+2+1 = 6.",
        "xp_reward": 20,
    },
    {
        "title": "Рекурсия — факториал",
        "description": "Сколько раз будет вызвана функция f(5), где f(n) = n*f(n-1), f(0)=1? Считая сам внешний вызов.",
        "topic": "Программирование",
        "difficulty": 1000,
        "answer": "6",
        "explanation": "f(5), f(4), f(3), f(2), f(1), f(0) — 6 вызовов.",
        "xp_reward": 14,
    },
    {
        "title": "Маски подсети",
        "description": "В IPv4 для адреса 192.168.10.130 используется маска 255.255.255.192. Какой номер подсети?",
        "topic": "Сети",
        "difficulty": 1400,
        "answer": "192.168.10.128",
        "explanation": "AND по маске /26 даёт 192.168.10.128.",
        "xp_reward": 22,
    },
    {
        "title": "Базы данных — запрос",
        "description": "В таблице Students 1000 записей. Запрос SELECT COUNT(*) FROM Students WHERE Score >= 80 вернёт 250 строк? Введите количество фактически возвращаемых записей.",
        "topic": "Базы данных",
        "difficulty": 500,
        "answer": "1",
        "explanation": "COUNT(*) всегда возвращает одну строку — количество.",
        "xp_reward": 7,
    },
    {
        "title": "Криптография — Цезарь",
        "description": "Сообщение 'PLZG' зашифровано шифром Цезаря со сдвигом +3. Расшифруйте его. Ответ — слово заглавными буквами.",
        "topic": "Кодирование",
        "difficulty": 800,
        "answer": "MIWD",
        "explanation": "Сдвиг назад на 3: P→M, L→I, Z→W, G→D.",
        "xp_reward": 11,
    },
    {
        "title": "Big O — сортировка",
        "description": "Какова асимптотическая сложность алгоритма сортировки слиянием в худшем случае? Ответьте в виде N*log(N) — записывайте как nlogn (без пробелов и маленькими буквами).",
        "topic": "Алгоритмы",
        "difficulty": 1500,
        "answer": "nlogn",
        "explanation": "Merge sort всегда O(N log N).",
        "xp_reward": 25,
    },
    {
        "title": "Перевод в шестнадцатеричную",
        "description": "Переведите число 255 из десятичной в шестнадцатеричную систему. В ответе укажите без префикса 0x, заглавными буквами.",
        "topic": "Системы счисления",
        "difficulty": 600,
        "answer": "FF",
        "explanation": "255 = 15·16 + 15 = FF₁₆.",
        "xp_reward": 8,
    },
    {
        "title": "Таблицы истинности",
        "description": "Сколько строк имеет таблица истинности логической функции от 4 переменных?",
        "topic": "Логика",
        "difficulty": 400,
        "answer": "16",
        "explanation": "2^4 = 16 наборов.",
        "xp_reward": 5,
    },
    {
        "title": "Количество информации",
        "description": "В алфавите 32 символа. Сколько бит несёт один символ при равновероятном появлении?",
        "topic": "Информация",
        "difficulty": 500,
        "answer": "5",
        "explanation": "log₂(32) = 5 бит.",
        "xp_reward": 7,
    },
    {
        "title": "Список Python — срез",
        "description": "Дан список a = [10, 20, 30, 40, 50, 60]. Что вернёт a[1:5:2]? Запишите как [x,y] без пробелов.",
        "topic": "Программирование",
        "difficulty": 800,
        "answer": "[20,40]",
        "explanation": "Срез [1:5:2] → индексы 1, 3 → 20, 40.",
        "xp_reward": 10,
    },
    {
        "title": "Битовые операции",
        "description": "Вычислите результат: 0b1101 & 0b1011. Ответ — в двоичной системе без префикса.",
        "topic": "Системы счисления",
        "difficulty": 900,
        "answer": "1001",
        "explanation": "1101 AND 1011 = 1001.",
        "xp_reward": 12,
    },
    {
        "title": "DFS — обход графа",
        "description": "Граф: A→B, A→C, B→D, C→D, D→E. Запишите порядок посещения вершин при обходе DFS из A (брать соседей в алфавитном порядке). Ответ — слитно без пробелов.",
        "topic": "Графы",
        "difficulty": 1300,
        "answer": "ABDEC",
        "explanation": "DFS: A→B→D→E (вернулись), затем C.",
        "xp_reward": 20,
    },
    {
        "title": "Регулярные выражения",
        "description": "Сколько раз сработает регулярное выражение r'\\d+' в строке 'abc12 de34 f5 6 g'?",
        "topic": "Программирование",
        "difficulty": 1100,
        "answer": "4",
        "explanation": "Совпадения: '12', '34', '5', '6' — 4 шт.",
        "xp_reward": 15,
    },
    {
        "title": "Условная сложность",
        "description": "Какова сложность бинарного поиска в отсортированном массиве из N элементов? Ответ в форме logn (маленькими, без пробелов).",
        "topic": "Алгоритмы",
        "difficulty": 800,
        "answer": "logn",
        "explanation": "На каждом шаге пространство поиска делится пополам — O(log N).",
        "xp_reward": 10,
    },
    {
        "title": "Хэш-таблицы",
        "description": "Средняя сложность вставки в хэш-таблицу при равномерном хэшировании? Ответ: O(?). Введите цифру.",
        "topic": "Алгоритмы",
        "difficulty": 1000,
        "answer": "1",
        "explanation": "Амортизированно O(1).",
        "xp_reward": 13,
    },
    {
        "title": "SQL JOIN",
        "description": "Какой тип JOIN вернёт все строки из левой таблицы и совпавшие из правой (со значениями NULL для несовпавших)? Ответ: одним словом на английском.",
        "topic": "Базы данных",
        "difficulty": 900,
        "answer": "LEFT",
        "explanation": "LEFT JOIN (LEFT OUTER JOIN).",
        "xp_reward": 12,
    },
    {
        "title": "Стек — постфикс",
        "description": "Вычислите значение постфиксного выражения: 3 4 + 2 *",
        "topic": "Алгоритмы",
        "difficulty": 1100,
        "answer": "14",
        "explanation": "(3+4)*2 = 14.",
        "xp_reward": 15,
    },
    {
        "title": "HTTP-коды",
        "description": "Какой HTTP-код возвращается, когда ресурс не найден?",
        "topic": "Сети",
        "difficulty": 300,
        "answer": "404",
        "explanation": "404 Not Found.",
        "xp_reward": 5,
    },
    {
        "title": "Динамическое программирование",
        "description": "Сколько различных путей из левого верхнего в правый нижний угол сетки 3x3 (ходы только вправо и вниз)?",
        "topic": "Алгоритмы",
        "difficulty": 1200,
        "answer": "6",
        "explanation": "C(4,2) = 6.",
        "xp_reward": 18,
    },
    {
        "title": "Простые числа",
        "description": "Сколько простых чисел между 1 и 20 (включительно)?",
        "topic": "Математика",
        "difficulty": 500,
        "answer": "8",
        "explanation": "2, 3, 5, 7, 11, 13, 17, 19 — 8 чисел.",
        "xp_reward": 7,
    },
    {
        "title": "Хэш SHA-256",
        "description": "Какова длина хэша SHA-256 в битах?",
        "topic": "Кодирование",
        "difficulty": 700,
        "answer": "256",
        "explanation": "По названию — 256 бит = 32 байта.",
        "xp_reward": 9,
    },
    {
        "title": "Очередь vs Стек",
        "description": "По принципу LIFO работает стек или очередь? Ответ: одним словом.",
        "topic": "Алгоритмы",
        "difficulty": 400,
        "answer": "стек",
        "explanation": "LIFO — Last In, First Out — это стек.",
        "xp_reward": 6,
    },
    {
        "title": "Объём растрового изображения",
        "description": "Изображение 200×100 пикселей кодируется 24 битами на пиксель. Сколько килобайт (КБ) занимает несжатый файл? Округлите до целого. Считайте 1 КБ = 1024 байт.",
        "topic": "Информация",
        "difficulty": 1000,
        "answer": "59",
        "explanation": "200·100·24/8 = 60000 байт ≈ 58.59 КБ ≈ 59.",
        "xp_reward": 14,
    },
    {
        "title": "Очень лёгкая арифметика",
        "description": "Вычислите 2 + 2.",
        "topic": "Математика",
        "difficulty": 150,
        "answer": "4",
        "explanation": "2 + 2 = 4.",
        "xp_reward": 3,
    },
    {
        "title": "Очень лёгкий бит",
        "description": "Сколько разных значений может принимать один бит?",
        "topic": "Информация",
        "difficulty": 250,
        "answer": "2",
        "explanation": "Бит принимает значения 0 или 1.",
        "xp_reward": 4,
    },
    {
        "title": "Сложная динамика",
        "description": "Сколько способов набрать сумму 10 монетами 1, 2 и 5, если порядок монет не важен?",
        "topic": "Алгоритмы",
        "difficulty": 1800,
        "answer": "10",
        "explanation": "Перебираем количество монет 5: 0, 1, 2. Для остатка считаем варианты монетами 1 и 2: 6 + 3 + 1 = 10.",
        "xp_reward": 32,
    },
    {
        "title": "Очень сложная логика",
        "description": "Сколько наборов A, B, C, D делают выражение (A or B) and (C or D) and not (A and C) истинным?",
        "topic": "Логика",
        "difficulty": 2100,
        "answer": "5",
        "explanation": "Из 16 наборов условиям удовлетворяют 5 наборов.",
        "xp_reward": 40,
    },
]


def main():
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    db = SessionLocal()
    try:
        ensure_achievements_seeded(db)

        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            admin.email = "admin@reshulyceum.ru"
        else:
            db.add(User(
                email="admin@reshulyceum.ru",
                username="admin",
                hashed_password=hash_password("admin123"),
                is_admin=True,
            ))
            print("Создан админ: admin / admin123")

        added = 0
        for t in DEMO_TASKS:
            if not db.query(Task).filter(Task.title == t["title"]).first():
                db.add(Task(**t))
                added += 1
        db.commit()
        print(f"Добавлено задач: {added}")
        print(f"Всего задач в БД: {db.query(Task).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
