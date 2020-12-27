from unittest import mock, TestCase
from unittest.mock import mock_open, MagicMock, call

from hdmi_cec_to_adb.bin.start_hdmi_cec_monitor import Monitor


class TestStartHdmiCecMonitor(TestCase):

    def setUp(self) -> None:
        super().setUp()

    @mock.patch('os.path.exists')
    def test_init_given_valid_adb_keys_and_ip_address_does_not_raise_exception(self, mock_exists):
        # arrange
        mock_exists.return_value = True

        # act
        Monitor('127.0.0.1', '/tmp/exists')

        # assert
        mock_exists.called_once()

    @mock.patch('os.path.exists')
    def test_init_given_invalid_ip_address_raises_exception(self, mock_exists):
        # arrange
        mock_exists.return_value = True

        # act / assert
        with self.assertRaises(ValueError):
            Monitor(None, '/tmp/exists')

    @mock.patch('os.path.exists')
    def test_init_given_valid_ip_address_and_invalid_key_raises_exception(self, mock_exists):
        # arrange
        mock_exists.return_value = True

        # act / assert
        with self.assertRaises(ValueError):
            Monitor('127.0.0.1', None)

    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock_open, read_data='data')
    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.PythonRSASigner')
    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.AdbDeviceTcp')
    def test_turn_off_tv_given_configuration_turns_off_tv_and_closes_connection(self,
                                                                                mock_adb_device_tcp,
                                                                                mock_python_rsa_signer,
                                                                                mock_open_file,
                                                                                mock_exists):
        # arrange
        mock_exists.return_value = True
        android_tv_mock = MagicMock()
        mock_adb_device_tcp.return_value = android_tv_mock
        python_rsa_signer_mock = MagicMock()
        mock_python_rsa_signer.return_value = python_rsa_signer_mock
        monitor = Monitor('127.0.0.1', '/tmp/exists')

        # act
        monitor.turn_off_tv()

        # assert
        mock_open_file.assert_has_calls([call('/tmp/exists'), call('/tmp/exists.pub')], any_order=True)
        mock_python_rsa_signer.assert_called_once_with('data', 'data')
        mock_adb_device_tcp.assert_called_once_with('127.0.0.1', 5555, default_transport_timeout_s=9.)
        android_tv_mock.connect.assert_called_once_with(rsa_keys=[python_rsa_signer_mock], auth_timeout_s=0.1)
        android_tv_mock.shell.assert_called_once_with('input keyevent 26')
        android_tv_mock.close.assert_called_once()

    @mock.patch('os.path.exists')
    def test_cec_callback_given_standby_event_calls_turn_off_tv(self,
                                                                mock_exists):
        # arrange
        mock_exists.return_value = True
        monitor = Monitor('127.0.0.1', '/tmp/exists')
        turn_off_tv_mock = MagicMock()
        monitor.turn_off_tv = turn_off_tv_mock
        event = 4
        event_data = ({'opcode': 54, 'destination': 15})

        # act
        monitor.cec_callback(event, event_data)

        # assert
        mock_exists.called_once()
        turn_off_tv_mock.assert_called_once()

    @mock.patch('os.path.exists')
    def test_cec_callback_given_non_standby_event_calls_turn_off_tv(self,
                                                                    mock_exists):
        # arrange
        mock_exists.return_value = True
        monitor = Monitor('127.0.0.1', '/tmp/exists')
        turn_off_tv_mock = MagicMock()
        monitor.turn_off_tv = turn_off_tv_mock
        event = 4
        event_data = ({'opcode': 54, 'destination': 15})

        # act
        monitor.cec_callback(event, event_data)

        # assert
        mock_exists.called_once()
        turn_off_tv_mock.assert_called_once()

    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.Monitor.validate_configuration')
    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.Monitor.turn_off_tvservice')
    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.cec')
    def test_configure_cec_given_turns_off_tv_service_and_setups_callback(self,
                                                                          mock_cec,
                                                                          mock_turn_off_tvservice,
                                                                          mock_validate_configuration):
        # arrange
        monitor = Monitor('127.0.0.1', '/tmp/exists')

        # act
        monitor.configure_cec()

        # assert
        mock_validate_configuration.assert_called_once()
        mock_turn_off_tvservice.assert_called_once()
        mock_cec.init.assert_called_once()
        mock_cec.add_callback.assert_called_once_with(monitor.cec_callback, mock_cec.EVENT_ALL)

    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.Monitor.validate_configuration')
    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.subprocess')
    def test_turn_off_tvservice_given_running_tvservice_does_not_raise_exception(self,
                                                                                 mock_subprocess,
                                                                                 mock_validate_configuration):
        # arrange
        monitor = Monitor('127.0.0.1', '/tmp/exists')
        run_magic_mock = MagicMock()
        run_magic_mock.returncode = 0
        mock_subprocess.run.return_value = run_magic_mock

        # act
        monitor.turn_off_tvservice()

        # assert
        mock_validate_configuration.assert_called_once()
        mock_subprocess.run.assert_called_once_with(['tvservice', '--off'], stdout=mock_subprocess.PIPE, text=True)

    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.Monitor.validate_configuration')
    @mock.patch('hdmi_cec_to_adb.bin.start_hdmi_cec_monitor.subprocess')
    def test_turn_off_tvservice_given_non_zero_return_raise_exception(self,
                                                                      mock_subprocess,
                                                                      mock_validate_configuration):
        # arrange
        monitor = Monitor('127.0.0.1', '/tmp/exists')
        run_magic_mock = MagicMock()
        run_magic_mock.returncode = 1
        mock_subprocess.run.return_value = run_magic_mock

        # act / assert
        with self.assertRaises(ValueError):
            monitor.turn_off_tvservice()

        # assert
        mock_validate_configuration.assert_called_once()
        mock_subprocess.run.assert_called_once_with(['tvservice', '--off'], stdout=mock_subprocess.PIPE, text=True)