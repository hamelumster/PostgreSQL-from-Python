import psycopg2


#Функция, создающая структуру БД (таблицы).
def create_db(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(40) NOT NULL,
            last_name VARCHAR(40) NOT NULL,
            email VARCHAR(100) NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS phone (
            id SERIAL PRIMARY KEY,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
            phone VARCHAR(20)
        );
        """)
    conn.commit()

#Функция, позволяющая добавить нового клиента.
def add_client(conn, first_name, last_name, email, phones=None):
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO clients (first_name, last_name, email) VALUES (%s, %s, %s) RETURNING id;
        """, (first_name, last_name, email))
        client_id = cursor.fetchone()[0]
        if phones:
            for phone in phones:
                add_phone(conn, client_id, phone)
    conn.commit()
    return client_id

#Функция, позволяющая добавить телефон для существующего клиента.
def add_phone(conn, client_id, phone):
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO phone (client_id, phone) VALUES (%s, %s);
        """, (client_id, phone))
    conn.commit()

#Функция, позволяющая изменить данные о клиенте.
def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    with conn.cursor() as cursor:
        if first_name is not None:
            cursor.execute("""
            UPDATE clients SET first_name=%s WHERE id=%s;
            """, (first_name, client_id))
        if last_name is not None:
            cursor.execute("""
            UPDATE clients SET last_name=%s WHERE id=%s;
            """, (last_name, client_id))
        if email is not None:
            cursor.execute("""
            UPDATE clients SET email=%s WHERE id=%s;
            """, (email, client_id))
        if phones is not None:
            cursor.execute("""
            DELETE FROM phone WHERE client_id=%s;
            """, (client_id,))
            for phone in phones:
                add_phone(conn, client_id, phone)
    conn.commit()

#Функция, позволяющая удалить телефон для существующего клиента.
def delete_phone(conn, client_id, phone):
    with conn.cursor() as cursor:
        cursor.execute("""
        DELETE FROM phone WHERE client_id=%s AND phone=%s;
        """, (client_id, phone))
    conn.commit()

#Функция, позволяющая удалить существующего клиента.
#Также при удалении клиента будут удаляться и все телефоны, которые были за ним "закреплены".
def delete_client(conn, client_id):
    with conn.cursor() as cursor:
        cursor.execute("""
        DELETE FROM clients WHERE id=%s;
        """, (client_id,))
    conn.commit()

#Функция, позволяющая найти клиента по его данным: имени, фамилии, email или телефону.
def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    results = []
    with conn.cursor() as cursor:
        if first_name is not None:
            cursor.execute("""
            SELECT clients.id, clients.first_name, clients.last_name, clients.email, 
                   COALESCE(phone.phone, 'Нет номера телефона') as phone
            FROM clients LEFT JOIN phone ON clients.id = phone.client_id
            WHERE clients.first_name=%s;
            """, (first_name,))
            results.extend(cursor.fetchall())
        if last_name is not None:
            cursor.execute("""
            SELECT clients.id, clients.first_name, clients.last_name, clients.email, 
                   COALESCE(phone.phone, 'Нет номера телефона') as phone
            FROM clients LEFT JOIN phone ON clients.id = phone.client_id
            WHERE clients.last_name=%s;
            """, (last_name,))
            results.extend(cursor.fetchall())
        if email is not None:
            cursor.execute("""
            SELECT clients.id, clients.first_name, clients.last_name, clients.email, 
                   COALESCE(phone.phone, 'Нет номера телефона') as phone
            FROM clients LEFT JOIN phone ON clients.id = phone.client_id
            WHERE clients.email=%s;
            """, (email,))
            results.extend(cursor.fetchall())
        if phone is not None:
            cursor.execute("""
            SELECT clients.id, clients.first_name, clients.last_name, clients.email, 
                   COALESCE(phone.phone, 'Нет номера телефона') as phone
            FROM clients LEFT JOIN phone ON clients.id = phone.client_id
            WHERE phone.phone=%s;
            """, (phone,))
            results.extend(cursor.fetchall())
    return results


with psycopg2.connect(database="clients", user="postgres", password="password", client_encoding='UTF8') as conn:
    create_db(conn)

    # Добавление нового клиента
    client_id = add_client(conn, "Иван", "Иванов", "ivan_ivanov@example.com", phones=["+79111111111"])
    print(f"Новый клиент с ID {client_id} добавлен")

    # Добавление телефона для клиента
    add_phone(conn, client_id, "+79222222222")
    print("Телефон добавлен")

    # Обновление данных клиента
    change_client(conn, client_id, email="ivanivanoff@example2.com", phones=["+79333333333", "+79444444444"])
    print("Данные клиента обновлены")

    # Удаление телефона по его значению
    delete_phone(conn, client_id, "+79444444444")
    print("Телефон удален")

    # Удаление клиента по его ID
    delete_client(conn, client_id)
    print("Клиент удален")

    # Так как клиента удалили, чтобы что-то найти, добавим клиента еще раз и добавим ему номер телефона
    client_id = add_client(conn, "Иван", "Иванов", "ivan_ivanov@example.com", phones=["+79991231212"])
    print(f"Новый клиент с ID {client_id} добавлен")

    # Поиск клиента
    clients = find_client(conn, first_name="Иван")
    print(f"Найденные клиенты: {clients}")

conn.close()