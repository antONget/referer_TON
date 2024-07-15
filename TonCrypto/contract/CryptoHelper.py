import asyncio

from pytonlib import TonlibClient
from tonsdk.contract.wallet import Wallets

from tonsdk.utils import to_nano, from_nano
from tonsdk.boc import Cell

import requests
from pathlib import Path
import logging
from fake_useragent import UserAgent

class BotWallet:
    def __init__(self):
        # testnet
        self.mnemonics = ['plastic', 'middle', 'retire', 'parent', 'various', 'differ', 'bike', 'volume', 'morning', 'crush', 'tell', 'motion', 'much', 'carbon', 'pitch', 'divorce', 'veteran', 'define', 'prosper', 'toss', 'charge', 'amused', 'divorce', 'melt']
        self.addr = "kQATX9u9PdL3hU1LrjFQcUUBuOAO95tNCRA77HriftbH_l51"  # test addr
        self.url = 'https://ton.org/testnet-global.config.json'
        # realnet
        # self.mnemonics = ['dream', 'horse', 'reunion', 'crater', 'rocket', 'able', 'element', 'allow', 'picnic', 'material', 'deliver', 'hedgehog', 'monster', 'junk', 'garbage', 'honey', 'glare', 'milk', 'pizza', 'city', 'receive', 'horse', 'inside', 'online']
        # self.addr = "EQA2v-pA4Nh0nmhD8Js1iAcZpq0qxFUZV5P1tnghj0YZfGGX" # bot real addr
        # self.url = 'https://ton.org/global-config.json'
        self.wallet = Wallets.from_mnemonics(mnemonics=self.mnemonics)[-1]
        



        
        # self.dest_addr = ""      # "UQDJ3RtNDffN5YdRxqnEfGgzJcGGvQD6Qr-XWgKB4CD5HBci" # real test addr

        # self.dest_addr =   "0QAUw4xCyZiFFIBE4GjbKm1ji2D7u7rvJjM3viW2UWismGzn" # my CryptoTestBot test addr





        self.amount = None

        self.config = requests.get(self.url).json()

        self.keystore_dir = 'tmp/ton_keystore'
        Path(self.keystore_dir).mkdir(parents=True, exist_ok=True)
        self.client = TonlibClient(ls_index=2, config=self.config, keystore=self.keystore_dir, tonlib_timeout=20)

        self.last_balance1 = ''
        self.last_balance2 = ''

        
        
        


    async def _deploy_contract(self):
        await self.client.init()
        query = self.wallet.create_init_external_message()

        deploy_message = query["message"].to_boc(False)

        await self.client.raw_send_message(deploy_message)

    async def _get_seqno(self):
        data = await self.client.raw_run_method(method='seqno', stack_data=[], address=self.addr)
        return int(data['stack'][0][1], 16)
    

    async def check_balance(self):
        
        my_balance = (await self.client.raw_get_account_state(self.addr))['balance']
        if float(my_balance) - self.amount < 0:
            # print(float(my_balance), self.amount)
            return False
        return True




    async def get_last_balances(self) -> tuple[str, str]:
        # await self.client.init() # for tests
        self.last_balance1 = (await self.client.raw_get_account_state(self.addr))['balance']
        self.last_balance2 = (await self.client.raw_get_account_state(self.dest_addr))['balance']
        return from_nano(int(self.last_balance1), 'ton'), from_nano(int(self.last_balance2), 'ton')


    async def is_success(self):
        # await self.client.init() # for test
        new_balance1 = (await self.client.raw_get_account_state(self.addr))['balance']
        new_balance2 = (await self.client.raw_get_account_state(self.dest_addr))['balance']
        # print(new_balance1, new_balance2)
        return self.last_balance1 != new_balance1 and self.last_balance2 != new_balance2


    async def transfer(self, amount: int | float, to_addr: str):
        await self.client.init()
        seqno = await self._get_seqno()
        # print(seqno)
        if isinstance(to_addr, str):
            self.dest_addr = to_addr
        else:
            return "wrong addr"
        
        result = self.wallet.create_init_external_message()
        # print(result)
        self.amount = to_nano(amount, 'ton')

        try:
            if await self.check_balance():
                transfer_query = self.wallet.create_transfer_message(to_addr=self.dest_addr,
                                                amount=self.amount, seqno=seqno, payload='hello from pasha')

                boc: Cell = transfer_query['message'].to_boc(False)            

                ans = await self.client.raw_send_message(boc)

                await asyncio.sleep(3)

                if ans["@type"] != 'ok':
                    return ans
                else:
                    if await self.is_success():
                        return 'ok'
                    else:
                        return 'false'
            else:
                return 'not enough money'
        except Exception as e:
            return f'error: {e}'

        

async def check_valid_addr(addr: str):
    return requests.get(f"https://toncenter.com/api/v2/getWalletInformation?address={addr}").json()['ok']


async def get_ton_in_rub(amount:  int | float):
    """
    Конвертация рубли в TON по курсу
    """
    try:
        return amount/(lambda response: response.json() if response.status_code == 200 else None)(requests.get(f"https://walletbot.me/api/v1/transfers/price_for_fiat/?crypto_currency=TON&local_currency=RUB&amount=1",
                                                                                            headers={'Content-Type': 'application/json',
                                                                                                      'user-agent': UserAgent().random}))['rate']
    except Exception as e:
        logging.error("PARSING ERROR: %s" % e)
        return None

TonWallet = BotWallet()






# Example

'''
from ...CryptoHelper import TonWallet



async def ...:
    resp = await TonWallet.transfer(amount = 0.001, to_addr='0QAUw4xCyZiFFIBE4GjbKm1ji2D7u7rvJjM3viW2UWismGzn')

    if resp == 'ok':
        ('success')

    elif resp == 'not enough money':
        ('not enough money')

    elif resp.startswith('error'):
        'error'

    else:  (false)
        smth went wrong
        

    
'''









# async def main():
    # botwal = BotWallet()
    
    # print(await botwal.transfer(4))
#     # await asyncio.sleep()
#     # print(await botwal.get_last_balances())

    



# if __name__ == '__main__':
#     asyncio.get_event_loop().run_until_complete(main())
