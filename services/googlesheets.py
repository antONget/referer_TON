import gspread
import logging
# TEST
gp = gspread.service_account(filename='services/test.json')
gsheet = gp.open('Referal')
sheet = gsheet.worksheet("Лист1")
# gp = gspread.service_account(filename='services/retnav.json')
# gsheet = gp.open('TelegramBot')
# sheet = gsheet.worksheet("list1")


def append_anketa(id_anketa: int,
                  id_telegram_refer: int,
                  username_refer: str,
                  id_telegram_referer: int,
                  username_referer: str,
                  username: str,
                  phone: str,
                  city: str,
                  link_post: str,
                  status: str) -> None:
    logging.info(f'append_order')
    sheet.append_row([id_anketa,
                      id_telegram_refer,
                      username_refer,
                      id_telegram_referer,
                      username_referer,
                      username,
                      phone,
                      city,
                      link_post,
                      status])


def get_list_all_anketa() -> list:
    logging.info(f'get_list_anketa')
    values = sheet.get_all_values()
    list_product = []
    for item in values:
        list_product.append(item)
    return list_product


def get_list_anketa(id_anketa: int) -> list:
    logging.info(f'get_list_anketa')
    username_referer = sheet.row_values(row=id_anketa+1)
    return username_referer


def update_status_anketa(status: str, telegram_id: int) -> None:
    logging.info(f'update_status_anketa: {telegram_id}')
    values = sheet.get_all_values()
    id_anketa = 0
    for i, row in enumerate(values[1:]):
        if int(row[1]) == telegram_id:
            id_anketa = i
    sheet.update_cell(row=id_anketa+2, col=10, value=status)
