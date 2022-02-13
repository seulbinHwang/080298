from api.Kiwoom import *
import sys

"""
- QApplication
    - PyQt5 를 이용하여 API 를 제어하는 메인 루프
    - OCX 방식인 API를 사용할 수 있게 됨
"""
app = QApplication(sys.argv)
kiwoom = Kiwoom()


# kospi code list/code_name 를 받겠다.
get_kospi_code_list = False
if get_kospi_code_list:
    kopsi_code_list = kiwoom.get_code_list_by_market("0") # list # "10": KOSDAQ
    print("kopsi_code_list:", kopsi_code_list)
    for code in kopsi_code_list:
        code_name = kiwoom.get_master_code_name(code)
        print('kospi_code:', code, ' / kospi_code_name:', code_name)
#
#
# 삼성전자(005930)의 일봉 정보를 출력하겠다.
get_samsung_price_data = True
if get_samsung_price_data:
    df = kiwoom.get_price_data(code="005930", date="20220211")
    print(df)

get_deposit = True
if get_deposit:
    deposit = kiwoom.get_deposit()

app.exec_()