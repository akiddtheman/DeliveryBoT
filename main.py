from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor
from aiogram.types import ReplyKeyboardRemove
from geopy.geocoders import Nominatim

import database
import buttons
import states
import config

# Создание подключения к боту
bot = Bot(config.BOT_TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
geolocator = Nominatim(user_agent=config.USER_AGENT)


# # Добавление продуктов в базу
# database.add_product_to_sklad('Яблоки',
#                                12, 12000,
#                                'Сорт Golden',
#                                'https://www.google.com/imgres?imgurl=https%3A%2F%2Fwww.applesfromny.com%2Fwp-content%2Fuploads%2F2020%2F05%2F20Ounce_NYAS-Apples2.png&tbnid=ktcxvF5LaXyVXM&vet=12ahUKEwiF4uu0oZP_AhUJwyoKHUtdC-AQMygBegUIARDDAQ..i&imgrefurl=https%3A%2F%2Fwww.applesfromny.com%2Fvarieties%2F&docid=C0ERe9pIHvHfgM&w=2400&h=1889&q=apples&ved=2ahUKEwiF4uu0oZP_AhUJwyoKHUtdC-AQMygBegUIARDDAQ')

# database.add_product_to_sklad('Груши',
#                               13, 13000,
#                               'Самые лучшие',
#                               'https://www.google.com/url?sa=i&url=https%3A%2F%2Frastenievod.com%2Fsorta-grush.html&psig=AOvVaw33NUIEzUs-JK1DyHtzv490&ust=1690623265097000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCIi1m8uMsYADFQAAAAAdAAAAABAE')
#
# database.add_product_to_sklad('Помидоры',
#                               7, 7500,
#                               'Помидоры Розовые',
#                               'https://www.google.com/url?sa=i&url=https%3A%2F%2Fxn--80adalk6a2b9h.xn--p1ai%2Fproducts%2Fpomidory-rozovye-tashkent-ves&psig=AOvVaw0Q_-XFIiA0urFdMJ4bcXdb&ust=1690623416633000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCPCfnZONsYADFQAAAAAdAAAAABAE')
#
# database.add_product_to_sklad('Огурцы',
#                               9, 9000,
#                               'Огурцы Кураж',
#                               'https://www.google.com/url?sa=i&url=https%3A%2F%2Fapeti.ru%2Fproduct%2Fogurtsy_kurazh_srednie.html&psig=AOvVaw1_OgXcBc-37nM9sKZgc8Ow&ust=1690623483571000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCMjBwbONsYADFQAAAAAdAAAAABAE')


# Обработка команды старт
@dp.message_handler(commands=['start'])
async def start_message(message):
    # Получение телеграм айди
    user_id = message.from_user.id
    print(user_id)
    # Проверка пользователя
    checker = database.check_user(user_id)

    # Проверка есть-ли пользователь в базе
    if checker:
        # Получение актуального списка продуктов
        products = database.get_pr_name_id()

        # Отправка сообщения с меню
        await bot.send_message(user_id, 'Здравствуйте! Доставка-бот готов к вашим услугам 🚗', reply_markup=ReplyKeyboardRemove())
        await bot.send_message(user_id,
                               'Выберите пункт меню 📲', reply_markup=buttons.main_menu_kb(products))

    # Если пользователя нет в базе
    elif not checker:
        await bot.send_message(user_id, 'Здравствуйте, вас приветствует доставка-бот от Akidd 🤖\n\n'
                                        'Для начала процесса отправьте пожалуйста ваше имя')

        # Переход на этап получения имени
        await states.RegisterUser.waiting_for_name.set()

# Этап получения имени
@dp.message_handler(state=states.RegisterUser.waiting_for_name)
async def get_name(message):
    # Сохранение телеграм айди в переменную
    user_id = message.from_user.id
    # Сохранение имени в переменную
    username = message.text

    # Отправка ответа
    await bot.send_message(user_id,'Отправьте теперь ваш контактный номер 📱', reply_markup=buttons.phone_number_kb())
    # Сохранение данных
    await dp.current_state(user=user_id).update_data(username=username)
    # Переход на этап получения номера
    await states.RegisterUser.waiting_for_phone_number.set()

# Этап получения номера телефона
@dp.message_handler(state=states.RegisterUser.waiting_for_phone_number, content_types=['contact'])
async def get_number(message):
    user_id = message.from_user.id

    # Проверка отправил-ли пользователь номер
    if message.contact:
        # Сохранение контакта
        phone_number = message.contact.phone_number
        # Получение данных
        user_data = await dp.current_state(user=user_id).get_data()
        # Сохранение пользователя в базе данных
        database.register_user(user_id, user_data['username'], phone_number, 'Not yet')
        # Отправка ответа
        await bot.send_message(user_id, 'Поздравляем вас с успешной регистрацией!', reply_markup=ReplyKeyboardRemove())

        # Открытие меню
        products = database.get_pr_name_id()
        await bot.send_message(user_id,'Выберите пункт меню 📲', reply_markup=buttons.main_menu_kb(products))

        await dp.current_state(user=user_id).finish()

    # Если пользователь не отправил номер
    elif not message.contact:
        await bot.send_message(user_id,'Отправьте контакт используя кнопку 📲',reply_markup=buttons.phone_number_kb())

# Обработчик выбора количества
@dp.callback_query_handler(lambda call: call.data in ['increment', 'decrement', 'to_cart', 'back'])
async def get_user_product_count(call):
    # Сохранение айди пользователя
    user_id = call.message.chat.id

    # Если пользователь нажал на +
    if call.data == 'increment':
        user_data = await dp.current_state(user=user_id).get_data()
        actual_count = user_data['pr_count']

        # Обновление значения количества
        await dp.current_state(user=user_id).update_data(pr_count=user_data['pr_count'] + 1)

        # Изменение значения кнопок
        await bot.edit_message_reply_markup(chat_id=user_id,
                                            message_id=call.message.message_id,
                                            reply_markup=buttons.choose_product_count('increment', actual_count))

    # Если пользователь нажал на -
    elif call.data == 'decrement':
        user_data = await dp.current_state(user=user_id).get_data()
        actual_count = user_data['pr_count']

        # Обновление значения количества
        await dp.current_state(user=user_id).update_data(pr_count=user_data['pr_count'] - 1)

        # Изменение значения кнопок
        await bot.edit_message_reply_markup(chat_id=user_id,
                                            message_id=call.message.message_id,
                                            reply_markup=buttons.choose_product_count('decrement', actual_count))

    # Если пользователь нажал кнопку 'назад'
    elif call.data == 'back':
        # Получение меню
        products = database.get_pr_name_id()
        # Изменение на меню
        await bot.edit_message_text('Выберите пункт меню 📲',
                                    user_id,
                                    call.message.message_id,
                                    reply_markup=buttons.main_menu_kb(products))

    # Если пользователь нажал на 'Добавить в корзину'
    elif call.data == 'to_cart':
        # Получение данных
        user_data = await dp.current_state(user=user_id).get_data()
        product_count = user_data['pr_count']
        user_product = user_data['pr_name']

        # Добавление в базу (корзина пользователя)
        database.add_product_to_cart(user_id, user_product, product_count)

        # Получение обратно меню
        products = database.get_pr_name_id()
        # Изменение на меню
        await bot.edit_message_text('Выбранный вами продукт добавлен в корзину 🛒\n\nХотите заказать что-нибудь еще?)',
                                    user_id,
                                    call.message.message_id,
                                    reply_markup=buttons.main_menu_kb(products))

# Обработчик кнопок (Оформить заказ, Корзина)
@dp.callback_query_handler(lambda call: call.data in ['order', 'cart', 'clear_cart'])
async def main_menu_handle(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id

    # Если пользователь нажал на кнопку 'Оформить заказ'
    if call.data == 'order':
        # Удаление сообщения с верхними кнопками
        await bot.delete_message(user_id, message_id)

        # Отправка текста на 'Отправьте локацию'
        await bot.send_message(user_id,'Отправьте теперь ваше местоположение 📍', reply_markup=buttons.location_kb())

        # Переход на этап сохранения локации
        await states.AcceptOrder.waiting_for_location.set()

    # Если пользователь нажал на кнопку 'Корзина'
    elif call.data == 'cart':
        # Получение корзины пользователя
        user_cart = database.get_exact_user_cart(user_id)

        # Формирование сообщения со всеми данными
        full_text = 'Ваша корзина:\n\n'
        total_amount = 0

        for i in user_cart:
            full_text += f'{i[0]} x {i[1]} = {i[2]}\n\n'
            total_amount += i[2]

        # Итог
        full_text += f'\nИтог: {total_amount}'

        # Отправка ответа пользователю
        await bot.edit_message_text(full_text, user_id, message_id, reply_markup=buttons.get_cart_kb())

    # Если пользователь нажал на 'Очистить корзину'
    elif call.data == 'clear_cart':
        # Вызов функции очистки корзины
        database.delete_product_from_cart(user_id)

        # Отправка ответа
        await bot.edit_message_text('Ваша корзина очищена 🛒', user_id, message_id, reply_markup=buttons.main_menu_kb(database.get_pr_name_id()))

# Функция сохранения локации пользователя
@dp.message_handler(state=states.AcceptOrder.waiting_for_location, content_types=['location', 'text'])
async def get_location(message):
    user_id = message.from_user.id

    # Проверка отправил-ли пользователь локацию
    if message.location:
        # Сохранение координат в переменные
        latitude = message.location.latitude
        longitude = message.location.longitude
        # Преобразование координат на нормальный адрес
        try:
            address = geolocator.reverse((latitude, longitude)).address
        except:
            address = 'Ошибка в модуле geopy'

        # Запрос подтверждения заказа
        # Получение корзины пользователя
        user_cart = database.get_exact_user_cart(user_id)

        # Формирование сообщения со всеми данными
        full_text = '⬇ Ваш заказ ⬇\n\n'
        user_info = database.get_user_number_name(user_id)
        full_text += f'📑 Ваше имя: {user_info[0]}\n\n📱 Ваш контактный номер: {user_info[1]}\n\n'
        total_amount = 0

        for i in user_cart:
            full_text += f'{i[0]} x {i[1]} = {i[2]}\n'
            total_amount += i[2]

        # Итог и Адрес
        full_text += f'\n🛒 Итог: {total_amount}\n\n📍 Адрес: {address}'

        await bot.send_message(user_id, full_text, reply_markup=buttons.get_accept_kb())

        # Переход на этап подтверждения
        await dp.current_state(user=user_id).update_data(address=address, full_text=full_text)
        await states.AcceptOrder.waiting_for_accept.set()

# Функция сохранения статуса заказа
@dp.message_handler(state=states.AcceptOrder.waiting_for_accept)
async def get_accept(message):
    user_id = message.from_user.id
    user_answer = message.text
    user_data = await dp.current_state(user=user_id).get_data()
    full_text = user_data.get('full_text')

    # Получение всех продуктов из базы для кнопок
    products = database.get_pr_name_id()

    # Если пользователь нажал на "Подтвердить"
    if user_answer == 'Подтвердить':
        admin_id = config.ADMIN_ID
        # Очистка корзины пользователя
        database.delete_product_from_cart(user_id)

        # Отправка админу сообщения о новом заказе
        await bot.send_message(admin_id, full_text.replace("Ваш", "Новый"))
        # Отправка ответа
        await bot.send_message(user_id, 'Ваш заказ оформлен.\n\nЗа дополнительной информацией обратитесь по номеру +Х (ХХХ) ХХХ-ХХ-ХХ\n\n'
                                        'Мы рады, что вы пользуетесь нашим сервисом 😊', reply_markup=ReplyKeyboardRemove())

    elif user_answer == 'Отменить':
        # Отправка ответа
        await bot.send_message(user_id, 'Заказ отменен', reply_markup=ReplyKeyboardRemove())

    # Обратно в меню
    await dp.current_state(user=user_id).finish()
    await bot.send_message(user_id, 'Меню', reply_markup=buttons.main_menu_kb(products))

# Обработчик выбора товара
@dp.callback_query_handler(lambda call: int(call.data) in database.get_pr_id())
async def get_user_product(call):
    user_id = call.message.chat.id

    # Сохранение продукта во временный словарь
    await dp.current_state(user=user_id).update_data(pr_name=call.data, pr_count=1)

    # Сохранение айди сообщения
    message_id = call.message.message_id

    # Смена кнопки на выбор количества
    await bot.edit_message_text('Выберите количество',
                                chat_id=user_id, message_id=message_id,
                                reply_markup=buttons.choose_product_count())

# Запуск
executor.start_polling(dp)