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
get_samsung_price_data = False
if get_samsung_price_data:
    df = kiwoom.get_price_data(code="005930", date="20220211")
    print(df)

# 예수금을 확인하겠다.
get_deposit = True
if get_deposit:
    deposit = kiwoom.get_deposit()

# 주문 접수 및 채결 확인
    # send_buy_order: rqname
    # '1001' : 화면 번호
    # 1: 신규 매수 주문 / 2: 신규 매도 주문 / 3: 매수 취소 / 4: 매도 취소 / 5: 매수 정정 / 6: 매도 정정
    # '007000': 매수할 종목 코드
    # 1: 주문 수량
    # 35000: 주문 가격
    # '00' : 지정가 주문 방식
send_order = True
if send_order:
    order_result = kiwoom.send_order('send_buy_order', '1001', 1, '007700', 1, 35000, '00')

app.exec_()