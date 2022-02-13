from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import pandas as pd
from util.const import *
"""
- PyQt
    - Kiwoom API 는 ActiveX Control인 OCX 방식으로 API 연결을 제공
    - 우리도 OCX 방식으로 API를 이용해야 함
        - OCX
            - OLE(Object Linking and Embedding) 을 제어할 수 있는 controller
            - 응용 프로그램끼리 데이터를 공유하고 제어할 수 있도록 개발한 기술
"""

class Kiwoom(QAxWidget):
    def __init__(self):
        """
        - QAxWidget
            - open API 를 사용할 수 있도록 연결
        """
        super().__init__()
        # 우리 컴퓨터에서 키움 API 를 사용할 수 있도록 설정
        self._make_kiwoom_instance()
        # API로 보내는 요청들을 받아올 slot을 등록하는 함수
        self._set_signal_slots()
        # 로그인 요청 보내기
        self._comm_connect()
        # 내 계좌 번호 받아오기 -> self.account_number
        self.account_number = self.get_account_number()

        # tr 요청에 대한 응답 대기를 위한 변수
        self.tr_event_loop = QEventLoop()

        self.order = {}
        self.balance = {}
        self.universe_realtime_transaction_info = {}

    def _make_kiwoom_instance(self):
        """
        - Objectives
            - 우리 컴퓨터에서 키움 API 를 사용할 수 있도록 설정
            - 로그인 / 주식 부분 /  TR 요청

        - setControl
            - PyQt5.QAxContainer.py 안 QAxWidget 클래스 내부 메서드

        - "KHOPENAPI.KHOpenAPICtrl.1"
            - 키움증권 웹 사이트에 접속하여 Open API를 설치하면 우리 컴퓨터에 설치되는 API 식별자 (프로그램 ID / ProgID)
            - Open API를 설치한 컴퓨터라면 레지스트리에 모두 동일한 이름으로 저장
        """
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        """
        - Objectives
            - API로 보내는 요청들을 받아올 slot을 등록하는 함수
        - 로그인
            - OnEventConnect.connect
                - 로그인 응답 처리를 받을 때 사용하는 slot 함수는 _login_slot 이다.

        """
        # 로그인 응답의 결과를 _on_login_connect을 통해 받도록 설정
        self.OnEventConnect.connect(self._login_slot)

        # TR의 응답 결과를 _on_receive_tr_data 함수를 통해 받도록 설정
        self.OnReceiveTrData.connect(self._on_receive_tr_data)

        # TR/주문 메시지를 _on_receive_msg을 통해 받도록 설정
        self.OnReceiveMsg.connect(self._on_receive_msg)

        # 주문 접수/체결 결과를 _on_chejan_slot을 통해 받도록 설정
        self.OnReceiveChejanData.connect(self._on_chejan_slot)

        # 실시간 체결 데이터를 _on_receive_real_data을 통해 받도록 설정
        self.OnReceiveRealData.connect(self._on_receive_real_data)

    def _login_slot(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("not connected")

        self.login_event_loop.exit()

    def _comm_connect(self):
        """
        - Objectives
            - 로그인 요청 신호를 보낸 이후, 응답 대기를 설정하는 함수

            - dynamicCall
                - PyQt5.QAxContainer.py 안 QAxWidget 클래스 내부 메서드
                - API 서버로 로그인 요청을 보냄
                - "CommConnect()"
                    - API 에서 제공하는 함수
                    - 키움증권 로그인 화면을 팝업하는 기능
        """
        self.dynamicCall("CommConnect()")

        # 동기화 처리를 위함 (로그인 될 때까지 기다리기)
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_number(self, tag="ACCNO"):
        """
        - dynamicCall
            - PyQt5.QAxContainer.py 안 QAxWidget 클래스 내부 메서드
            - API 서버로 요청을 보냄
            - "GetLoginInfo(QString)"
                - 키움증권 로그인에 성공한 사용자 정보를 얻어 오는 API 함수
            - tag
                - "ACCNO" : 구분자 ; 로 연결된 보유 계좌 목록을 반환
                    - 국내 해외 주식 / 선물/ 옵션 등의 계좌번호가 저장될 수 있음
                - "USER_ID" / "USER_NAME"
                - "GetServerGubun" : 1: 모의 투자, 나머지: 실거래 서버
                - "KEY_BSECGB" : 키보드 보안 해지 여부 (0: 정상, 1: 해지)
                - "FIREW_SECGB" : 방화벽 설정 여부 반환 (0: 미설정 / 1: 설정 / 2: 해지)
        """
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)  # tag로 전달한 요청에 대한 응답을 받아옴
        account_number = account_list.split(';')[0] # TODO: 국내 가상 계좌만 있다고 가장한 코드
        print('account_list:', account_list)
        print('account_number:', account_number)
        return account_number

    def get_code_list_by_market(self, market_type):
        """
        Objectives
            - 특정 market의 code list를 받는다.
        # TODO: market_type 을 바꿔가며 전략을 만들자.
        Parameter: market_type("_")
            - 0: 코스피
            - 10: 코스닥
            - 3: ELW
            - 8: ETF
            - 50: KONEX
            - 4: 뮤츄얼 펀드
            - 5: 신주인수권
            - 6: 리츠
            - 9: 하이얼펀드
            - 30: K-OTC
        """
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1]
        return code_list

    def get_master_code_name(self, code):
        """
        Objectives
            - 특정 code의 종목명을 받는다.
        """
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_price_data(self, code, date):
        """
        Objectives
            - 종목의 상장일부터 가장 최근 일자까지 일봉 정보를 가져오는 함수
            - TODO: "기준 일자" 를 이용하여, 주식 상장일 ~ 기준 일자 의 데이터를 받아올 수도 있다.
        """
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        # 사용자 구분 명 / TR 이름 / 연속 조회 여부 = 0 ( 600개만 딱 받아오기) / 화면 번호
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")

        # TR 요청을 보낸 후, 응답 대기 상태로 만드는 코드 (이 아래 코드는 TR에 대한 응답이 도착한 후 실행될 수 있다.)
        self.tr_event_loop.exec_()

        # 한 번에 호출로 받아 올 수 있는 데이터의 최대 개수 600개치가 ohlcv에 저장됨
        ohlcv = self.tr_data

        # 여러 번 호출된 데이터를 합칩니다.
        while self.has_next_tr_data:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            # 사용자 구분 명 / TR 이름 / 연속 조회 여부 = 2 / 화면 번호
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 2, "0001")
            self.tr_event_loop.exec_()

            for key, val in self.tr_data.items():
                ohlcv[key] += val # ohlcv[key][-1:] = val
        """
        DataFrame
            - 행과 열을 가진 자료 구조
        """
        df = pd.DataFrame(ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=ohlcv['date'])

        return df[::-1] # 날짜 뒤집기

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        """
        Objectives
            - TR조회의 응답 결과를 얻어오는 함수
        Parameter
            - screen_no: 화면 번호
            - rqname: 사용자 구분 명
            - trcode: TR 이름
            - record_name: 레코드 이름 (안 씀)
            - next: 연속 조회 유무를 판단하는 값 ( 0: 연속(추가 조회) 데이터 없음 / 2: 연속(추가 조회) 데이터 있음 )
            - unused1, unused2, unused3, unused4
        """
        print("[Kiwoom] _on_receive_tr_data is called {} / {} / {}".format(screen_no, rqname, trcode))
        # 이번 요청에서 받아 온 데이터 개수(tr_data_cnt) 확인 요청
        tr_data_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

        if next == '2':
            self.has_next_tr_data = True
        else:
            self.has_next_tr_data = False

        if rqname == "opt10081_req":
            ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

            for i in range(tr_data_cnt):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "일자")
                open = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시가")
                high = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "고가")
                low = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "저가")
                close = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "거래량")

                ohlcv['date'].append(date.strip())
                ohlcv['open'].append(int(open))
                ohlcv['high'].append(int(high))
                ohlcv['low'].append(int(low))
                ohlcv['close'].append(int(close))
                ohlcv['volume'].append(int(volume))

            self.tr_data = ohlcv

        elif rqname == "opw00001_req":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, "주문가능금액")
            self.tr_data = int(deposit)
            print(self.tr_data)

        elif rqname == "opt10075_req":
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                order_number = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문가격")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                order_type = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문구분")
                left_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "미체결수량")
                executed_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "체결량")
                ordered_at = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시간")
                fee = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매수수료")
                tax = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매세금")

                # 데이터 형변환 및 가공
                code = code.strip()
                code_name = code_name.strip()
                order_number = str(int(order_number.strip()))
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())

                current_price = int(current_price.strip().lstrip('+').lstrip('-'))
                order_type = order_type.strip().lstrip('+').lstrip('-')  # +매수,-매도처럼 +,- 제거
                left_quantity = int(left_quantity.strip())
                executed_quantity = int(executed_quantity.strip())
                ordered_at = ordered_at.strip()
                fee = int(fee)
                tax = int(tax)

                # code를 key값으로 한 딕셔너리 변환
                self.order[code] = {
                    '종목코드': code,
                    '종목명': code_name,
                    '주문번호': order_number,
                    '주문상태': order_status,
                    '주문수량': order_quantity,
                    '주문가격': order_price,
                    '현재가': current_price,
                    '주문구분': order_type,
                    '미체결수량': left_quantity,
                    '체결량': executed_quantity,
                    '주문시간': ordered_at,
                    '당일매매수수료': fee,
                    '당일매매세금': tax
                }

            self.tr_data = self.order

        elif rqname == "opw00018_req":
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목번호")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "보유수량")
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "매입가")
                return_rate = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                total_purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,"매입금액")
                available_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,"매매가능수량")

                # 데이터 형변환 및 가공
                code = code.strip()[1:]
                code_name = code_name.strip()
                quantity = int(quantity)
                purchase_price = int(purchase_price)
                return_rate = float(return_rate)
                current_price = int(current_price)
                total_purchase_price = int(total_purchase_price)
                available_quantity = int(available_quantity)

                # code를 key값으로 한 딕셔너리 변환
                self.balance[code] = {
                    '종목명': code_name,
                    '보유수량': quantity,
                    '매입가': purchase_price,
                    '수익률': return_rate,
                    '현재가': current_price,
                    '매입금액': total_purchase_price,
                    '매매가능수량': available_quantity
                }

            self.tr_data = self.balance
        # 응답 대기 상태에서 해제 시켜주기
        self.tr_event_loop.exit()
        # 키움 API 를 이용할 때, 1초에 최대 5회의 요청만 허용하는 정책 떄문
        # 0.2초에 한번 데이터를 요청할 수 있지만, 여기서는 여유 있게 0.5초의 대기 시잔을 두었다.
        time.sleep(0.5)

    def get_deposit(self):
        """
        Objectives
            - 조회 대상 계좌의 예수금을 얻어오는 함수
        """
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00001_req", "opw00001", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price, order_classification, origin_order_number=""):
        order_result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",[rqname, screen_no, self.account_number, order_type, code, order_quantity, order_price,order_classification, origin_order_number])
        return order_result

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        print("[Kiwoom] _on_receive_msg is called {} / {} / {} / {}".format(screen_no, rqname, trcode, msg))

    def _on_chejan_slot(self, s_gubun, n_item_cnt, s_fid_list):
        print("[Kiwoom] _on_chejan_slot is called {} / {} / {}".format(s_gubun, n_item_cnt, s_fid_list))

        # 9201;9203;9205;9001;912;913;302;900;901;처럼 전달되는 fid 리스트를 ';' 기준으로 구분함
        for fid in s_fid_list.split(";"):
            if fid in FID_CODES:
                # 9001-종목코드 얻어오기, 종목코드는 A007700처럼 앞자리에 문자가 오기 때문에 앞자리를 제거함
                code = self.dynamicCall("GetChejanData(int)", '9001')[1:]

                # fid를 이용해 data를 얻어오기(ex: fid:9203를 전달하면 주문번호를 수신해 data에 저장됨)
                data = self.dynamicCall("GetChejanData(int)", fid)

                # 데이터에 +,-가 붙어있는 경우 (ex: +매수, -매도) 제거
                data = data.strip().lstrip('+').lstrip('-')

                # 수신한 데이터는 전부 문자형인데 문자형 중에 숫자인 항목들(ex:매수가)은 숫자로 변형이 필요함
                if data.isdigit():
                    data = int(data)

                # fid 코드에 해당하는 항목(item_name)을 찾음(ex: fid=9201 > item_name=계좌번호)
                item_name = FID_CODES[fid]

                # 얻어온 데이터를 출력(ex: 주문가격 : 37600)
                print("{}: {}".format(item_name, data))

                # 접수/체결(s_gubun=0)이면 self.order, 잔고이동이면 self.balance에 값을 저장
                if int(s_gubun) == 0:
                    # 아직 order에 종목코드가 없다면 신규 생성하는 과정
                    if code not in self.order.keys():
                        self.order[code] = {}

                    # order 딕셔너리에 데이터 저장
                    self.order[code].update({item_name: data})
                elif int(s_gubun) == 1:
                    # 아직 balance에 종목코드가 없다면 신규 생성하는 과정
                    if code not in self.balance.keys():
                        self.balance[code] = {}

                    # order 딕셔너리에 데이터 저장
                    self.balance[code].update({item_name: data})

        # s_gubun값에 따라 저장한 결과를 출력
        if int(s_gubun) == 0:
            print("* 주문 출력(self.order)")
            print(self.order)
        elif int(s_gubun) == 1:
            print("* 잔고 출력(self.balance)")
            print(self.balance)

    def get_order(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")  # 0:전체, 1:미체결, 2:체결
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")  # 0:전체, 1:매도, 2:매수
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075_req", "opt10075", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def get_balance(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018_req", "opw00018", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def set_real_reg(self, str_screen_no, str_code_list, str_fid_list, str_opt_type):
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", str_screen_no, str_code_list, str_fid_list, str_opt_type)
        time.sleep(0.5)

    def _on_receive_real_data(self, s_code, real_type, real_data):
        if real_type == "장시작시간":
            pass

        elif real_type == "주식체결":
            signed_at = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("체결시간"))

            close = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("현재가"))
            close = abs(int(close))

            high = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('고가'))
            high = abs(int(high))

            open = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('시가'))
            open = abs(int(open))

            low = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('저가'))
            low = abs(int(low))

            top_priority_ask = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('(최우선)매도호가'))
            top_priority_ask = abs(int(top_priority_ask))

            top_priority_bid = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('(최우선)매수호가'))
            top_priority_bid = abs(int(top_priority_bid))

            accum_volume = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('누적거래량'))
            accum_volume = abs(int(accum_volume))

            # print(s_code, signed_at, close, high, open, low, top_priority_ask, top_priority_bid, accum_volume)

            # universe_realtime_transaction_info 딕셔너리에 종목코드가 키값으로 존재하지 않는다면 생성(해당 종목 실시간 데이터 최초 수신시)
            if s_code not in self.universe_realtime_transaction_info:
                self.universe_realtime_transaction_info.update({s_code: {}})

            # 최초 수신 이후 계속 수신되는 데이터는 update를 이용해서 값 갱신
            self.universe_realtime_transaction_info[s_code].update({
                "체결시간": signed_at,
                "시가": open,
                "고가": high,
                "저가": low,
                "현재가": close,
                "(최우선)매도호가": top_priority_ask,
                "(최우선)매수호가": top_priority_bid,
                "누적거래량": accum_volume
            })
