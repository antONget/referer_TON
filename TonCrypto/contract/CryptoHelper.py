import asyncio

from pytonlib import TonlibClient
from tonsdk.contract.wallet import Wallets, WalletVersionEnum

from tonsdk.utils import to_nano, from_nano
from tonsdk.boc import Cell

import requests
from pathlib import Path
import logging
from fake_useragent import UserAgent
from config_data.config import Config, load_config

config: Config = load_config()


class BotWallet:
    def __init__(self):

        # uncommen to use mainnet
        self.mnemonics = config.tg_bot.mnemonics.split(',')
        self.addr = 'UQAUygHnpvBlLqpg40x7u6O5SNqHUTsNpz0LUoeV4oYL1-5e'

        # self.mnemonics = config.tg_bot.mnemonics.split(',')
        self.url = 'https://ton.org/global-config.json'

        # Getting wallet from mnemonics
        mnemonics, pub_k, priv_k, self.wallet = Wallets.from_mnemonics(mnemonics=self.mnemonics,
                                                                       version=WalletVersionEnum.v4r2)

        self.amount = None
        self.config = requests.get(self.url).json()

        # Making a keystore for the proper operation of the library
        self.keystore_dir = 'tmp/ton_keystore'
        Path(self.keystore_dir).mkdir(parents=True, exist_ok=True)

        # make a client
        self.client = TonlibClient(ls_index=4, config=self.config, keystore=self.keystore_dir, tonlib_timeout=30)
        self.last_balance1 = None
        self.last_balance2 = None

    # Function to deploy smart contract (use it once)
    async def _deploy_contract(self):
        await self.client.init()
        query = self.wallet.create_init_external_message()
        deploy_message = query["message"].to_boc(False)
        await self.client.raw_send_message(deploy_message)

    # Возвращает порядковый номер транзакции в определенном кошельке. Этот метод в основном используется для защиты
    # от повторного воспроизведения .
    async def _get_seqno(self):
        # await self.client.init()

        data = await self.client.raw_run_method(address=self.addr,
                                                method='seqno',
                                                stack_data=[]
                                                )
        return int(data['stack'][0][1], 16)

    # Function to check balance for valid payment
    async def check_balance(self):
        logging.info('check_balance')
        my_balance = (await self.client.raw_get_account_state(self.addr))['balance']
        if float(my_balance) - self.amount < 0:
            # print(float(my_balance), self.amount)
            return False
        return True

    # Function that checks the previous balance for comparison with the new one
    async def get_last_balances(self, dest_addr: str = None):
        # await self.client.init()
        logging.info(f'get_last_balances')
        if isinstance(dest_addr, str):
            self.dest_addr = dest_addr
        else:
            return "wrong addr"
        # получаем баланс в нанотонах на заказчика
        last_b1 = await self.client.raw_get_account_state(self.addr)
        self.last_balance1 = int((last_b1)['balance'])
        logging.info(f'last_balance1: {self.last_balance1}')

        # получаем баланс на кошельке получателя
        last_b2 = await self.client.raw_get_account_state(self.dest_addr)
        self.last_balance2 = int((last_b2)['balance'])
        logging.info(f'last_balance2: {self.last_balance2}')
        # print(last_b1, last_b2)
        return

    async def is_success(self, amount: int | float):
        # await self.client.init() # for test

        amount = to_nano(amount, 'ton')

        new_balance1 = int((await self.client.raw_get_account_state(self.addr))['balance'])
        new_balance2 = int((await self.client.raw_get_account_state(self.dest_addr))['balance'])

        # print(new_balance1, new_balance2)
        # print(self.last_balance1, self.last_balance2)
        # print(self.last_balance1 - amount, self.last_balance2 + amount)

        # Checking for debiting funds
        return (self.last_balance1 - amount <= new_balance1) and (self.last_balance2 + amount >= new_balance2)

    # transfers amount to address
    async def transfer(self, amount: int | float, to_addr: str):
        """
        Перевод тонов
        """
        logging.info(f'BotWallet.transfer: amount - {amount}, to_addr - {to_addr}')
        # Initialize a client
        await self.client.init()
        # await self.client.sync_tonlib()
        # Возвращает порядковый номер транзакции в определенном кошельке.
        # Этот метод в основном используется для защиты от повторного воспроизведения .
        seqno = await self._get_seqno()

        # Checking type of address
        if isinstance(to_addr, str):
            self.dest_addr = to_addr
        else:
            return "wrong addr"

        # Конвертируйте заданную сумму из указанной единицы в нанограммы, наименьшую единицу криптовалюты TON.
        # logging.info(f'amount: {amount} type(amount): {type(amount)}')
        self.amount = to_nano(amount, 'ton')
        # logging.info(f'amount_to_nano: {amount}')
        # try:
        # проверка что, на кошельке достаточно для списания amount TON
        # logging.info(f'check_balance(): {await self.check_balance()}')
        if await self.check_balance():

            # getting last balances before transaction
            await self.get_last_balances(dest_addr=to_addr)

            # make transaction query
            transfer_query = self.wallet.create_transfer_message(to_addr=self.dest_addr,
                                                                 amount=self.amount,
                                                                 seqno=seqno)
            # getting boc data
            boc: Cell = transfer_query['message'].to_boc(False)

            # sending information to blockchain
            ans = await self.client.raw_send_message(boc)

            # await asyncio.sleep(2)
            # print(ans)
            # checking the result of transaction
            if ans["@type"] != 'ok':
                return ans
            else:
                if await self.is_success(amount=amount):
                    return 'ok'
                else:
                    return 'false'
        else:
            return 'not enough money'
        # except Exception as e:
        #     return f'!error: {e}'


async def check_valid_addr(addr: str):
    """
    Проверка валидности кошелька пользователя
    """
    return requests.get(f"https://toncenter.com/api/v2/getWalletInformation?address={addr}").json()['ok']


async def get_ton_in_rub(amount: int | float):
    """
    Конвертация рубли в TON по курсу
    """
    try:
        return amount / (lambda response: response.json() if response.status_code == 200 else None)(requests.get(
            f"https://walletbot.me/api/v1/transfers/price_for_fiat/?crypto_currency=TON&local_currency=RUB&amount=1",
            headers={'Content-Type': 'application/json',
                     'user-agent': UserAgent().random}))['rate']
    except Exception as e:
        logging.error("PARSING ERROR: %s" % e)
        return None


TonWallet = BotWallet()

# for tests
# print(asyncio.get_event_loop().run_until_complete(TonWallet.transfer(0.05, '0QAFe_UHOda_RqEn5TSpijG0ZeSN6r7vqtSE36yzMnumMx92')))
