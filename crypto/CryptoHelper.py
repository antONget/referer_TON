from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.api import Assets, Balance, Check, Invoice, Transfer
from aiocryptopay.exceptions import CodeErrorFactory
# from settings.config import CRYPTO_TOKEN


from asyncio import run
from datetime import datetime


CRYPTO_TOKEN = "14190:AA2b4nBwnFXoIMANNLS6kCvDAERb9Kh99Nq"

CryptoHelper : AioCryptoPay = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.TEST_NET)



async def pay_ton_to(user_id: int, amount: int | float) -> Transfer:
    tr = await CryptoHelper.transfer(user_id=user_id, asset=Assets.TON, amount=amount,  spend_id=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))  # method to send coins to user
    await CryptoHelper.close()
    return tr



""" ------------------------ FOR ADMINS ------------------------"""

async def get_balance():
    balance = await CryptoHelper.get_balance()
    balance_ton = [i.available for i in balance if i.currency_code == Assets.TON][0]
    await CryptoHelper.close()

    return balance_ton

async def get_stats():
    stats = await CryptoHelper.get_stats()
    await CryptoHelper.close()
    s = f'''Оборот: ${stats.volume}\nКонверсия: {stats.conversion} %\n\nКоличество созданных счетов: {stats.created_invoice_count}\nКоличество оплат: {stats.paid_invoice_count}\nКоличество пользователей: {stats.unique_users_count}
    '''

    return s

async def get_paid_invoices():
    invoices = await CryptoHelper.get_invoices()
    otv = 'Оплаченые инвойсы:\n\n'
    for invoice in invoices:
        if invoice.status == "paid":
            otv += f'ID: {invoice.invoice_id}\nСумма: {invoice.amount} {invoice.asset}\nСозданно: {invoice.created_at.strftime("%d/%m/%Y; %H:%M:%S")}\nОплачено: {invoice.paid_at.strftime("%d/%m/%Y; %H:%M:%S")}\n\n'

    await CryptoHelper.close()
    return otv


async def create_check_link(amount: int | float, description = None | str):
    check: Check = await CryptoHelper.create_check(amount=1, asset=Assets.TON, description=description)  # methos to make a check
    await CryptoHelper.close()
    return check.bot_check_url


async def create_invoice_link(amount: int | float):
    invoice: Invoice = await CryptoHelper.create_invoice(amount=amount, asset=Assets.TON)  # methos to make a check
    await CryptoHelper.close()
    print(invoice)
    return invoice.bot_invoice_url

# async def get_me():
#     profile = await CryptoHelper.get_me()
#     await CryptoHelper.close()
#     return profile

# print(run(get_me()))

# print(run(create_invoice_link(4)))
# print(run(create_check_link()))



# run(pay_ton_to(1060834219, 0.14))


# print(run(get_paid_invoices()))
# print()
# print(run(get_stats()))
# print()
# print(run(get_balance()))




