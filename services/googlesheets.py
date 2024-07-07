import gspread
import logging
# gp = gspread.service_account(filename='services/test.json')
# gsheet = gp.open('Referal')
# sheet = gsheet.worksheet("Лист1")
gp = gspread.service_account(filename='services/retnav.json')
gsheet = gp.open('TelegramBot')
sheet = gsheet.worksheet("list1")


def append_anketa(id_anketa: int,
                  id_telegram_refer: int,
                  username_refer: str,
                  id_telegram_referer: int,
                  username_referer: str,
                  name: str,
                  phone: str,
                  city: str,
                  email: str,
                  link_post: str,
                  vacancy: str,
                  status: str,
                  date_anketa: str) -> None:
    """
    Добавление данных анкеты в гугл таблицу
    param: id_anketa - порядковый номер анкеты в таблице
    param: id_telegram_refer - id телеграм пользователя
    param: username_refer - username телеграм пользователя
    param: id_telegram_referer - id телеграм реферера (пользователь который пригласил)
    param: username_referer - username телеграм реферера
    param: name - имя пользователя
    param: phone - телефон пользователя
    param: city - город пользователя
    param: email - электронная почта пользователя
    param: link_post - ссылка на вакансию
    param: vacancy - категория вакансии
    param: status - статус анкеты (создана, оплачена, отмена оплаты)
    param: date_anketa - дата создания анкеты
    """
    logging.info(f'append_order')
    sheet.append_row([id_anketa,
                      id_telegram_refer,
                      username_refer,
                      id_telegram_referer,
                      username_referer,
                      name,
                      phone,
                      city,
                      email,
                      link_post,
                      vacancy,
                      status,
                      date_anketa])


def get_list_all_anketa() -> list:
    """
    Получение всех записей из таблицы
    """
    logging.info(f'get_list_anketa')
    values = sheet.get_all_values()
    list_product = []
    for item in values:
        list_product.append(item)
    return list_product


def get_list_anketa(id_anketa: int) -> list:
    """
    Получаем информацию об анкете по ее id
    """
    logging.info(f'get_list_anketa')
    info_anketa = sheet.row_values(row=id_anketa+1)
    return info_anketa


def get_info_user(id_telegram: int) -> dict | bool:
    """
    Получаем информацию об анкете пользователя по его id телеграм если она есть
    """
    logging.info(f'get_info_user')
    # получаем все строки из таблицы
    values = sheet.get_all_values()
    # создаем словарь для строки пользователя
    dict_anketa_user = {}
    # проходим по всем строкам с конца
    for item in values[::-1]:
        # если пользователь заполнил и отправил анкету в таблицу
        if item[1] == str(id_telegram):
            # формируем словарь с ключами из первой строки
            for i, v in enumerate(item):
                dict_anketa_user[values[0][i]] = item[i]
            return dict_anketa_user
    return False


def update_status_anketa(status: str, telegram_id: int) -> None:
    """
    Обновление статуса анкеты по id телеграм пользователя заполнившего анкету
    param: status - статус анкеты на который требуется произвести изменение
    param: telegram_id - id телеграм пользователя
    """
    logging.info(f'update_status_anketa: {telegram_id}')
    values = sheet.get_all_values()
    col_status = values[0].index('status') + 1
    id_anketa = 0
    for i, row in enumerate(values[1:]):
        if int(row[1]) == telegram_id:
            id_anketa = i
    sheet.update_cell(row=id_anketa+2, col=col_status, value=status)
