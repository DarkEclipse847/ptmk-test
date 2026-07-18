import datetime
import random
import time
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
import models

def wait_for_db():
    print("Ожидание полной готовности PostgreSQL...")
    retries = 30  # Даем базе до 60 секунд на запуск
    while retries > 0:
        try:
            db = SessionLocal()
            # Выполняем самый сырой и быстрый тестовый запрос
            db.execute(text("SELECT 1"))
            db.close()
            print("База данных успешно подключена и готова к работе!")
            return
        except Exception as e:
            retries -= 1
            print(f"   БД еще не принимает подключения. Повтор через 2 сек... (Осталось попыток: {retries})")
            time.sleep(2)
    raise Exception("Не удалось дождаться запуска базы данных PostgreSQL.")



# Списки для генерации реалистичных справочников
DEPARTMENTS = ["IT", "HR", "Бухгалтерия", "Маркетинг", "Продажи", "Юридический", "Логистика", "Безопасность"]
POSITIONS = ["Стажер", "Специалист", "Ведущий специалист", "Главный специалист", "Руководитель направления", "Директор"]
FIRST_NAMES = ["Иван", "Алексей", "Сергей", "Михаил", "Дмитрий", "Илья", "Анна", "Елена", "Ольга", "Мария", "Татьяна", "Анастасия", "Елизавета"]
LAST_NAMES = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Соколов", "Новиков"]


FEMALE_NAMES = {"Анна", "Елена", "Ольга", "Мария", "Татьяна", "Анастасия", "Елизавета"} # Для O(1) проверки пола
# Простой regex для базовой проверки окончания фамилий. Его можно доработать для несклоняемых фамилий, но у нас таковых нет
# Вообще можно в данной ситуации просто докидывать букву "а" в конец, но это меньший уровень гибкости и возможности изменения в будущем
# И хоть на regex расходуется больше ресурсов, все равно считаю это грамотным решением для "scalability".
SURNAME_REGEX = re.compile(r"([^ьйъаеёиоуыэ])$")  


def seed_data():
    db: Session = SessionLocal()
    start_time = time.time()
    
    print("Пересоздание таблиц...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Заполнение справочников...")
    dept_objs = [models.Department(name=name) for name in DEPARTMENTS]
    pos_objs = [models.Position(name=name) for name in POSITIONS]
    db.add_all(dept_objs)
    db.add_all(pos_objs)
    db.commit()

    dept_ids = [d.id for d in dept_objs]
    pos_ids = [p.id for p in pos_objs]

    print("Генерация 1 000 сотрудников...")
    employees_data = []
    for _ in range(1000):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        if first_name in FEMALE_NAMES:
            last_name = SURNAME_REGEX.sub(r"\1а", last_name)
        full_name = f"{last_name} {first_name}"
        employees_data.append({
            "full_name": full_name,
            "department_id": random.choice(dept_ids),
            "position_id": random.choice(pos_ids)
        })
    
    db.bulk_insert_mappings(models.Employee, employees_data)
    db.commit()

    employee_ids = [e_id for (e_id,) in db.query(models.Employee.id).all()]

    print("Генерация 1 000 000 заявок...")
    statuses = ["Новая", "В работе", "Выполнена"]
    descriptions = [
        "Не работает интернет на рабочем месте",
        "Предоставить доступ к корпоративной почте",
        "Заказать канцелярию для отдела",
        "Согласовать договор на поставку оборудования",
        "Проверить отчет за прошлый квартал",
        "Настроить резервное копирование данных"
    ]
    
    now = datetime.datetime.utcnow()
    total_requests = 1_000_000
    batch_size = 50_000
    requests_batch = []

    for i in range(1, total_requests + 1):
        created_at = now - datetime.timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        deadline = created_at + datetime.timedelta(days=random.randint(-5, 10))
        author_id = random.choice(employee_ids)
        executor_id = random.choice(employee_ids) if random.random() > 0.15 else None
        status_choice = random.choice(statuses)

        requests_batch.append({
            "created_at": created_at,
            "deadline": deadline,
            "description": f"{random.choice(descriptions)} #{i}",
            "status": status_choice,
            "author_id": author_id,
            "executor_id": executor_id
        })

        if i % batch_size == 0:
            db.bulk_insert_mappings(models.Request, requests_batch)
            db.commit()
            requests_batch.clear()
            print(f"   Добавлено {i} из {total_requests}...")

    db.close()
    end_time = time.time()
    print(f"База данных успешно заполнена за {end_time - start_time:.2f} сек.!")

if __name__ == "__main__":
    seed_data()
