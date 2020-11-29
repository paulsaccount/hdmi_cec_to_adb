import argparse
import logging
import os
import subprocess
import time
from threading import Thread

import cec
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

logger = logging.getLogger(__name__)


class Monitor:
    tv_ip_address = None
    adb_key_filepath = None
    adb_port = None

    def __init__(self, tv_ip_address, adb_key_filepath, adb_port=5555, verbose=False, log_to_disk=False) -> None:
        super().__init__()
        self.tv_ip_address = tv_ip_address
        self.adb_key_filepath = adb_key_filepath
        self.adb_port = adb_port

        self.setup_logging(verbose, log_to_disk)
        self.validate_configuration()

    @staticmethod
    def setup_logging(verbose, log_to_disk):
        log_level = logging.DEBUG if verbose else logging.INFO

        handlers = [
            logging.StreamHandler(),
        ]
        if log_to_disk:
            handlers.append(logging.FileHandler('/tmp/hdmi_cec_to_adb.log'))
        logging_config = {'level': log_level,
                          'format': '%(asctime)s [%(levelname)s] %(message)s',
                          'handlers': handlers}
        logging.basicConfig(**logging_config)

    def validate_configuration(self):
        if not self.adb_key_filepath:
            raise ValueError('adb_key_filepath must not be None')

        if self.tv_ip_address is None:
            raise ValueError('tv_ip_address must be set')

        if self.adb_port is None:
            raise ValueError('adb_port must be set')

        if not os.path.exists(self.adb_key_filepath):
            raise ValueError('Adb private key not found, adb key must exist for ADB to work')

        if not os.path.exists(self.adb_key_filepath + '.pub'):
            raise ValueError('Adb public key not found, adb key must exist for ADB to work')

    @staticmethod
    def check_existing_processes():
        """
        Check for existing processes by ps grepping. Filter out grep itself, matches with current PID, and /dev/null
        for cron jobs. If another process is found, logs the found processes and exit the script
        """
        pid = os.getpid()
        pipe = subprocess.Popen(
            'ps aux | grep %s | grep -v grep | grep -v "/dev/null" | grep -v "bash -c" | grep -v %s ' % (
                'start_hdmi_cec_monitor', pid), shell=True, stdout=subprocess.PIPE).stdout
        output = pipe.read().decode('utf-8')
        if output != '':
            logging.error('%s is already running, existing process: \n %s' % (__file__, output))
            raise SystemExit()

    def turn_off_tv(self):
        # Load the public and private keys
        with open(self.adb_key_filepath) as f:
            priv = f.read()
        with open(self.adb_key_filepath + '.pub') as f:
            pub = f.read()
        signer = PythonRSASigner(pub, priv)

        # Connect
        android_tv = AdbDeviceTcp(self.tv_ip_address, self.adb_port, default_transport_timeout_s=9.)
        android_tv.connect(rsa_keys=[signer], auth_timeout_s=0.1)

        # Send a shell command
        logger.info('Shutting off TV via shell command')
        tv_off_command_key = '26'
        android_tv.shell('input keyevent %s' % tv_off_command_key)

        android_tv.close()

    def cec_callback(self, event, *args):
        logger.debug('[event=%s][args=%s]', event, args)
        if (event == cec.EVENT_COMMAND
                and args
                and args[0]['opcode'] == cec.CEC_OPCODE_STANDBY
                and args[0]['destination'] == cec.CECDEVICE_BROADCAST):
            logger.debug('Standby command received')
            self.turn_off_tv()

    def configure_cec(self):
        cec.init()
        cec.add_callback(self.cec_callback, cec.EVENT_ALL)

    @staticmethod
    def timer():
        count = 0
        while True:
            time.sleep(5)
            count += 1
            logger.debug('Current uptime ' + str(count * 5) + ' seconds.')

    def run_forever(self):
        self.check_existing_processes()
        self.configure_cec()
        logger.info('Starting background thread')
        background_thread = Thread(target=Monitor.timer)
        background_thread.start()


def main():
    parser = argparse.ArgumentParser(description='Start the HDMI CEC Monitor.')
    parser.add_argument('--tv_ip_address', type=str, help='The IP address of the Android TV')
    parser.add_argument('--adb_port', default=5555, type=int, help='The adb port used to connect')
    parser.add_argument('--adb_key_filepath', type=str, help='The path to the adb private key, usually '
                                                             'located in ~/.android/adbkey after adb is installed')
    parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
    parser.add_argument('-l', '--log_to_disk', default=False,
                        help='Log to /tmp/hdmi_cec_to_adb.log', action='store_true')

    args = parser.parse_args()

    monitor = Monitor(args.tv_ip_address,
                      args.adb_key_filepath,
                      args.adb_port,
                      args.verbose,
                      args.log_to_disk)
    try:
        monitor.run_forever()
    except:
        logger.exception('Unhandled exception')


if __name__ == '__main__':
    main()
