from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.api import Assets, Balance, Check, Invoice

# from settings.config import CRYPTO_TOKEN


from asyncio import run



CRYPTO_TOKEN = "14190:AA2b4nBwnFXoIMANNLS6kCvDAERb9Kh99Nq"

CryptoHelper : AioCryptoPay = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.TEST_NET)



async def pay_ton_to(user_id: int, amount: int | float):
    await CryptoHelper.transfer(user_id=user_id, asset=Assets.TON, amount=amount,  spend_id=1029384756)  # method to send coins to user
    await CryptoHelper.close()



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

# print(run(create_invoice_link(2)))
# print(run(create_check_link()))






# print(run(get_paid_invoices())) 
# async def 

# print(run(get_stats()))
# run(get_balance())



async def f():
    # profile = await CryptoHelper.get_me()
    # currencies = await CryptoHelper.get_currencies()
    balance = await CryptoHelper.get_balance()
    # rates = await CryptoHelper.get_exchange_rates()
    stats = await CryptoHelper.get_stats()

    # invoice = await CryptoHelper.create_invoice(amount=1, asset=Assets.TON, description='Оплата 1 тон')  # methos to make a check

    # await CryptoHelper.transfer(user_id=1060834219, asset=Assets.TON, amount=0.8,  spend_id=123)  # method to send coins to user


    # CryptoHelper.
    # e = await CryptoHelper.get_exchange_rates()  # курс
    # o = await CryptoHelper.get_invoices()
    await CryptoHelper.delete_invoice(215445)
    # for i in o:
    #     try:
    #         await CryptoHelper.delete_invoice(i.invoice_id)
    #     except Exception as e:
    #         print(e)
    #         continue
    await CryptoHelper.close()

    # print(*[i for i in o], sep='\n')



#     # print(*[i for i in currencies], sep='\n')
#     # print(stats)
#     # print(invoice)
#     # print(ch)
#     print(*[i for i in balance], sep='\n')

# run(f())
