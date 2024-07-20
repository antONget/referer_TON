import asyncio

from pytonlib import TonlibClient
from tonsdk.contract.wallet import Wallets

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
        # testnet
        # self.mnemonics = ['plastic', 'middle', 'retire', 'parent', 'various', 'differ', 'bike', 'volume', 'morning',
        #                   'crush', 'tell', 'motion', 'much', 'carbon', 'pitch', 'divorce', 'veteran', 'define',
        #                   'prosper', 'toss', 'charge', 'amused', 'divorce', 'melt']
        # self.addr = "kQATX9u9PdL3hU1LrjFQcUUBuOAO95tNCRA77HriftbH_l51"  # test addr
        # self.url = 'https://ton.org/testnet-global.config.json'

        # uncommen to use mainnet
        # self.mnemonics = ['dream', 'horse', 'reunion', 'crater', 'rocket', 'able', 'element', 'allow', 'picnic', 'material', 'deliver', 'hedgehog', 'monster', 'junk', 'garbage', 'honey', 'glare', 'milk', 'pizza', 'city', 'receive', 'horse', 'inside', 'online']
        # self.addr = "EQA2v-pA4Nh0nmhD8Js1iAcZpq0qxFUZV5P1tnghj0YZfGGX" # bot real addr
        # self.url = 'https://ton.org/global-config.json'
        self.mnemonics = config.tg_bot.mnemonics.split(',')
        self.addr = "EQA2v-pA4Nh0nmhD8Js1iAcZpq0qxFUZV5P1tnghj0YZfGGX"  # bot real addr
        self.url = 'https://ton.org/global-config.json'
        # Getting wallet from mnemonics
        self.wallet = Wallets.from_mnemonics(mnemonics=self.mnemonics)[-1]

        self.amount = None
        self.config = requests.get(self.url).json()

        # Making a keystore for the proper operation of the library
        self.keystore_dir = 'tmp/ton_keystore'
        Path(self.keystore_dir).mkdir(parents=True, exist_ok=True)

        # make a client
        self.client = TonlibClient(ls_index=2, config=self.config, keystore=self.keystore_dir, tonlib_timeout=20)

        # for further work with transaction verification
        self.last_balance1 = None
        self.last_balance2 = None

    # Function to deploy smart contract (use it once)
    async def _deploy_contract(self):
        await self.client.init()
        query = self.wallet.create_init_external_message()
        deploy_message = query["message"].to_boc(False)
        await self.client.raw_send_message(deploy_message)

    # Function to get seqno for transactions
    async def _get_seqno(self):
        data = await self.client.raw_run_method(method='seqno', stack_data=[], address=self.addr)
        return int(data['stack'][0][1], 16)

    # Function to check balance for valid payment
    async def check_balance(self):
        my_balance = (await self.client.raw_get_account_state(self.addr))['balance']
        if float(my_balance) - self.amount < 0:
            # print(float(my_balance), self.amount)
            return False
        return True

    # Function that checks the previous balance for comparison with the new one
    async def get_last_balances(self):
        # await self.client.init() # for tests

        # getting balances
        self.last_balance1 = from_nano(int((await self.client.raw_get_account_state(self.addr))['balance']), 'ton')
        self.last_balance2 = from_nano(int((await self.client.raw_get_account_state(self.dest_addr))['balance']), 'ton')

        # making them from nanocoins to coins
        return from_nano(int(self.last_balance1), 'ton'), from_nano(int(self.last_balance2), 'ton')

    async def is_success(self, amount: int | float):
        # await self.client.init() # for test

        amount = from_nano(amount, 'ton')

        new_balance1 = from_nano(int((await self.client.raw_get_account_state(self.addr))['balance']), 'ton')
        new_balance2 = from_nano(int((await self.client.raw_get_account_state(self.dest_addr))['balance']), 'ton')

        # print(new_balance1, new_balance2)
        # print(self.last_balance1, self.last_balance2)

        # Checking for debiting funds
        return self.last_balance1 - amount <= new_balance1 and self.last_balance2 + amount >= new_balance2

    # transfers amount to address
    async def transfer(self, amount: int | float, to_addr: str):
        """
        Перевод тонов
        """
        # Initialize a client
        await self.client.init()

        # get seqno
        seqno = await self._get_seqno()

        # Checking type of address
        if isinstance(to_addr, str):
            self.dest_addr = to_addr
        else:
            return "wrong addr"

        # maiking amount from coin to nanocoin
        self.amount = to_nano(amount, 'ton')

        try:
            # check that we have enough money
            if await self.check_balance():

                # getting last balances before transaction
                await self.get_last_balances()

                # make transaction query
                transfer_query = self.wallet.create_transfer_message(to_addr=self.dest_addr,
                                                                     amount=self.amount,
                                                                     seqno=seqno,
                                                                     payload='hello from pasha')

                # getting boc data
                boc: Cell = transfer_query['message'].to_boc(False)

                # sending information to blockchain
                ans = await self.client.raw_send_message(boc)

                await asyncio.sleep(2)

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
        except Exception as e:
            return f'error: {e}'


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
