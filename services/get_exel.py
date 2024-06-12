import pandas as pd
from module.data_base import get_list_user

def list_users_to_exel():
    dict_stat = {"№ п/п": [], "ID_telegram": [], "username": []}
    i = 0
    list_user = get_list_user()
    for order in list_user:
        i += 1
        dict_stat["№ п/п"].append(i)
        dict_stat["ID_telegram"].append(order[1])
        dict_stat["username"].append(order[2])
    df_stat = pd.DataFrame(dict_stat)
    with pd.ExcelWriter(path='./list_user.xlsx', engine='xlsxwriter') as writer:
        df_stat.to_excel(writer, sheet_name=f'Список пользователей', index=False)

