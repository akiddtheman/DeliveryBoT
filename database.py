import sqlite3

from datetime import datetime

# Создание подключения
connection = sqlite3.connect('dostavka.db')
# Исполнитель
sql = connection.cursor()

# Создание таблицы пользователей
sql.execute('CREATE TABLE IF NOT EXISTS users (tg_id INTEGER, name TEXT, '
            'phone_number TEXT, address TEXT, reg_date DATETIME);')

# Создаем таблицы для склада
sql.execute('CREATE TABLE IF NOT EXISTS '
            'products (pr_id INTEGER PRIMARY KEY AUTOINCREMENT, pr_name TEXT,'
            'pr_price REAL, pr_quantity INTEGER, pr_des TEXT, pr_photo TEXT,'
            'reg_date DATETIME);')

# Создание таблицы для корзины
sql.execute('CREATE TABLE IF NOT EXISTS user_cart (user_id INTEGER, '
            'user_product TEXT, quantity INTEGER, total_for_product REAL);')



# Функция для регистрации пользователей
def register_user(tg_id, name, phone_number, address):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    # Добавление в базу пользователей
    sql.execute('INSERT INTO users '
                '(tg_id, name, phone_number, address, reg_date) VALUES'
                '(?, ?, ?, ?, ?);', (tg_id, name, phone_number, address, datetime.now()))

    # Запись обновлений
    connection.commit()

# Проверка пользователя в базе
def check_user(user_id):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    checker = sql.execute('SELECT tg_id FROM users WHERE tg_id=?;', (user_id, ))

    if checker.fetchone():
        return True

    else:
        return False

# Добавление продукта в таблицу products
def add_product_to_sklad(pr_name, pr_count, pr_price, pr_des, pr_photo):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    # Добавление в базу пользователя
    sql.execute('INSERT INTO products '
                '(pr_name, pr_price, pr_quantity, pr_des, pr_photo, reg_date) '
                'VALUES (?, ?, ?, ?, ?, ?);',
                (pr_name, pr_price, pr_count, pr_des, pr_photo, datetime.now()))

    connection.commit()

# Получение всех продуктов из базы
def get_pr_name_id():
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    # Получение всех продуктов из базы (name, id)
    products = sql.execute('SELECT pr_name, pr_id, pr_quantity FROM products;').fetchall()

    # Сортировка того, что осталось на складе
    sorted_product = [(i[0], i[1]) for i in products if i[2] > 0]

    # Чистый список продуктов [(name, id), (name, id) ..... (name, id)]
    return sorted_product


# Получить все id товаров
def get_pr_id():
    # Создаем подключения
    connection = sqlite3.connect('dostavka.db')
    # переводчик/исполнитель
    sql = connection.cursor()

    # Получаем все продукты из базы (name, id)
    products = sql.execute('SELECT pr_name, pr_id, pr_quantity FROM products;').fetchall()

    # сортируем только те что остались на складе
    sorted_product = [i[1] for i in products if i[2] > 0]
    print(sorted_product)
    # чистый список продуктов [id, id ..... id]
    return sorted_product


# Получение информации про определенный продукт (через pr_id) -> (photo, des, price)
def get_exact_product(pr_id):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    exact_product = sql.execute('SELECT pr_photo, pr_des, pr_price '
                                'FROM products WHERE pr_id=?;', (pr_id, )).fetchone()

    return exact_product

# Добавление продуктов в корзину пользователя
def add_product_to_cart(user_id, product, quantity):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    # Получение цены продукта из базы
    product_price = get_exact_product(product)[2]

    sql.execute('INSERT INTO user_cart '
                '(user_id, user_product, quantity, total_for_product) '
                'VALUES (?, ?, ?, ?);',
                (user_id, product, quantity, quantity*product_price))

    connection.commit()

# Удаление продуктов из корзины
def delete_exact_product_from_cart(pr_id, user_id):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    # Удаление продукта из корзины через pr_id
    sql.execute('DELETE FROM user_cart WHERE user_product=? AND user_id=?;',
                (pr_id, user_id))

    connection.commit()

def delete_product_from_cart(user_id):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    # Удаление продукта из корзины через pr_id
    sql.execute('DELETE FROM user_cart WHERE user_id=?;',
                (user_id, ))

    connection.commit()

# Вывод корзины пользователя через (user_id) -> [(product, quantity, total_for_pr), (product, quantity, total_for_pr)]
def get_exact_user_cart(user_id):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    user_cart = sql.execute('SELECT '
                            'products.pr_name, '
                            'user_cart.quantity, '
                            'user_cart.total_for_product '
                            'FROM user_cart  '
                            'INNER JOIN products ON products.pr_id=user_cart.user_product '
                            'WHERE user_id=?;',
                            (user_id, )).fetchall()

    return user_cart

# Получение номера телефона и имени пользователя
def get_user_number_name(user_id):
    connection = sqlite3.connect('dostavka.db')
    sql = connection.cursor()

    exact_user = sql.execute('SELECT name, phone_number FROM users WHERE tg_id=?;', (user_id, ))

    return exact_user.fetchone()