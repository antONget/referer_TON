import gspread
import logging
gp = gspread.service_account(filename='services/test.json')

gsheet = gp.open('Referal')
sheet = gsheet.worksheet("Лист1")


def append_anketa(id_anketa: int, id_telegram_refer: int, username_refer: str, id_telegram_referer: int,
                  username_referer: str, link_post: str, status: str) -> None:
    logging.info(f'append_order')
    sheet.append_row([id_anketa, id_telegram_refer, username_refer, id_telegram_referer,
                      username_referer, link_post, status])


def get_list_all_anketa() -> list:
    logging.info(f'get_list_anketa')
    values = sheet.get_all_values()
    list_product = []
    for item in values:
        list_product.append(item)
    return list_product


def get_list_anketa(id_anketa: int) -> list:
    logging.info(f'get_list_anketa')
    username_referer = sheet.row_values(row=id_anketa)
    return username_referer


def update_status_anketa(id_anketa: int, status: str) -> None:
    logging.info(f'update_status_anketa')
    sheet.update_cell(id_anketa, 6, status)
