from unittest import mock, TestCase
from email.message import Message
from app.bot.tv_mt4 import generate_nonce, log, TradeHandler, EmailHandler, SubjectInfo, TradeData


# 2. Set up the test environment
class TestTradingScript(TestCase):

    def setUp(self) -> None:
        self.trade_handler = TradeHandler()
        self.email_handler = EmailHandler(self.trade_handler)

    def tearDown(self) -> None:
        pass

    # 3. Define the test cases

    def test_generate_nonce(self):
        """
        Test generate_nonce function
        """
        nonce = generate_nonce()
        self.assertIsInstance(nonce, str)
        self.assertEqual(len(nonce), 8)

        nonce = generate_nonce(12)
        self.assertIsInstance(nonce, str)
        self.assertEqual(len(nonce), 12)

    def test_log(self):
        """
        Test log function
        """
        with mock.patch('builtins.print') as mocked_print:
            # Test debug = 0
            with mock.patch('app.bot.tv_mt4.config.debug', '0'):
                log("hello")
                mocked_print.assert_not_called()
            # Test debug = 1
            with mock.patch('app.bot.tv_mt4.config.debug', '1'):
                log("hello")
                mocked_print.assert_called_once_with("hello")

    @mock.patch('app.bot.tv_mt4.Trade.find')
    def test_determine_trade_action(self, mock_trade_find):
        """
        Test determine_trade_action function
        """
        trade_data = {'pair': 'EURUSD', 'signal': 'Buy', 'nonce': '12345678', 'volume': '0.01', 'target_symbol': None, 'action': None}
        trade_data_buy = TradeData(**trade_data)
        trade_data_sell = TradeData(**trade_data)

        # Test TRADE when setup is None
        mock_trade_find.return_value = None

        trade_action = self.trade_handler.determine_trade_action(trade_data_buy)
        self.assertEqual(trade_action, 'trade')

        trade_action = self.trade_handler.determine_trade_action(trade_data_sell)
        self.assertEqual(trade_action, 'trade')

        # Test TRADE when setup has no nonce
        mock_trade_find.reset_mock()
        mock_trade_find.return_value = {'nonce': None}

        trade_action = self.trade_handler.determine_trade_action(trade_data_buy)
        self.assertEqual(trade_action, 'trade')

        trade_action = self.trade_handler.determine_trade_action(trade_data_sell)
        self.assertEqual(trade_action, 'trade')

        # Test TRADE when hedging is True
        with mock.patch('app.bot.tv_mt4.config.hedging', True):
            mock_trade_find.reset_mock()

            trade_action = self.trade_handler.determine_trade_action(trade_data_buy)
            self.assertEqual(trade_action, 'trade')

            trade_action = self.trade_handler.determine_trade_action(trade_data_sell)
            self.assertEqual(trade_action, 'trade')

        # Test CNR when trading Buy
        with mock.patch('app.bot.tv_mt4.config.hedging', False):
            mock_trade_find.reset_mock()
            mock_trade_find.return_value = {'nonce': '12345678'}

            trade_action = self.trade_handler.determine_trade_action(trade_data_buy)
            self.assertEqual(trade_action, 'close_reverse')

        # Test CNR when trading Sell
        mock_trade_find.reset_mock()
        mock_trade_find.return_value = {'nonce': '12345678'}

        trade_action = self.trade_handler.determine_trade_action(trade_data_sell)
        self.assertEqual(trade_action, 'close_reverse')

        # Test CLOSE
        mock_trade_find.reset_mock()
        mock_trade_find.return_value = {'nonce': '12345678', 'signal': 'Sell'}

        trade_data_sell['signal'] = 'Close Sell'

        trade_action = self.trade_handler.determine_trade_action(trade_data_sell)
        self.assertEqual(trade_action, 'close')

        trade_data_buy['signal'] = 'Close Buy'

        trade_action = self.trade_handler.determine_trade_action(trade_data_buy)
        self.assertEqual(trade_action, 'close')

    @mock.patch('app.bot.tv_mt4.Trade.create')
    @mock.patch('app.bot.tv_mt4.TradeHandler.create_trade_payload')
    def test_trade(self, mock_create_trade_payload, mock_trade_create):
        """
        Test trade function
        """

        trade_data_buy = {'pair': 'EURUSD', 'signal': 'Buy', 'nonce': '12345678', 'volume': '0.01', 'target_symbol': None, 'action': None}
        trade_data_buy = TradeData(**trade_data_buy)
        trade_data_sell = {'pair': 'EURUSD', 'signal': 'Sell', 'nonce': '12345678', 'volume': '0.01', 'target_symbol': None, 'action': None}
        trade_data_sell = TradeData(**trade_data_sell)

        with mock.patch('app.bot.tv_mt4.Trade.find') as mock_trade_find:
            # Test trade
            mock_create_trade_payload.return_value = 'test_trade_payload'
            self.trade_handler.trade(trade_data_buy)
            mock_trade_find.assert_called_once_with('EURUSD')
            mock_create_trade_payload.assert_called_once()
            self.trade_handler.server.send.assert_called_once_with('test_trade_payload')

            # Test CNR
            mock_trade_find.return_value = {'nonce': '12345678'}

            self.trade_handler.trade(trade_data_sell)
            self.trade_handler.server.send.assert_called_with('test_trade_payload')

    @mock.patch('app.bot.tv_mt4.Trade.create')
    @mock.patch('app.bot.tv_mt4.TradeHandler.create_trade_payload')
    def test_close(self, mock_create_trade_payload, mock_trade_create):
        """
        Test close function
        """

        trade_data_buy = {'pair': 'EURUSD', 'signal': 'Buy', 'nonce': '12345678', 'volume': '0.01', 'target_symbol': None, 'action': None}
        trade_data_buy = TradeData(**trade_data_buy)
        trade_data_sell = {'pair': 'EURUSD', 'signal': 'Sell', 'nonce': '12345678', 'volume': '0.01', 'target_symbol': None, 'action': None}
        trade_data_sell = TradeData(**trade_data_sell)

        with mock.patch('app.bot.tv_mt4.Trade.find') as mock_trade_find:
            # Test close
            mock_create_trade_payload.return_value = 'test_trade_payload'
            mock_trade_find.return_value = {'nonce': '12345678', 'signal': 'Sell'}

            self.trade_handler.close(trade_data_sell)
            mock_trade_find.assert_called_once_with('EURUSD')
            mock_create_trade_payload.assert_called_once()
            self.trade_handler.server.send.assert_called_once_with('test_trade_payload')
            mock_trade_create.return_value.flush.assert_called_once()

            # Test close when nonce is None
            mock_trade_find.return_value = None
            trade_data_sell.nonce = None
            self.trade_handler.close(trade_data_sell)
            mock_create_trade_payload.assert_not_called()
            self.trade_handler.server.send.assert_not_called()
            mock_trade_create.return_value.flush.assert_not_called()

    @mock.patch('app.bot.tv_mt4.TradeHandler.create_trade_payload')
    def test_execute_trade_action(self, mock_create_trade_payload):
        """
        Test execute_trade_action function
        """
        trade_data = {'pair': 'EURUSD', 'signal': 'Buy', 'nonce': '12345678', 'volume': '0.01', 'target_symbol': None, 'action': None}
        trade_data = TradeData(**trade_data)
        # Test TRADE
        mock_create_trade_payload.return_value = 'test_trade_payload'
        self.trade_handler.execute_trade_action('trade', trade_data)
        mock_create_trade_payload.assert_called_once_with(trade_data)
        self.trade_handler.server.send.assert_called_once_with('test_trade_payload')

        # Test CLOSE
        self.trade_handler.execute_trade_action('close', trade_data)
        self.trade_handler.server.send.assert_called_with('test_trade_payload')

        # Test CLOSE_REVERSE
        self.trade_handler.execute_trade_action('close_reverse', trade_data)
        self.trade_handler.server.send.assert_called_with('test_trade_payload')

    def test_create_trade_payload(self):
        """
        Test create_trade_payload function
        """
        trade_data = {'pair': 'EURUSD', 'signal': 'Buy', 'nonce': '12345678', 'volume': '0.01', 'target_symbol': None, 'action': None}
        trade_data = TradeData(**trade_data)
        trade_payload = self.trade_handler.create_trade_payload(trade_data)
        self.assertEqual(trade_payload, "TRADE||0|0|0|0|IcarusBot Trade|12345678|0.01")

    @mock.patch('app.bot.tv_mt4.Trade.find')
    def test_read_email(self, mock_trade_find):
        """
        Test read_email function
        """
        # Test process_email_subject for Buy trade
        with mock.patch('app.bot.tv_mt4.EmailHandler.process_email_subject') as mock_process_email_subject:
            mail = Message()
            mail['Subject'] = 'Signal Alert: Sell EURUSD'
            self.email_handler.parse_subject(mail)
            mock_process_email_subject.assert_called_once()

        # Test process_email_subject for Sell trade
        with mock.patch('app.bot.tv_mt4.EmailHandler.process_email_subject') as mock_process_email_subject:
            mail = Message()
            mail['Subject'] = 'Signal Alert: Buy EURUSD'
            self.email_handler.parse_subject(mail)
            mock_process_email_subject.assert_called_once()
