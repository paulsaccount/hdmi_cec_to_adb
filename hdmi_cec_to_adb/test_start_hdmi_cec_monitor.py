from unittest import mock, TestCase

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

