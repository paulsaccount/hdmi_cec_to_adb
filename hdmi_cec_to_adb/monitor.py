import logging
import asyncio
import os

from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner


'''
TRAFFIC: [          130873] >> 4f:36
DEBUG:   [          130874] >> Playback 1 (4) -> Broadcast (F): standby (36)
DEBUG:   [          130874] Playback 1 (4): power status changed from 'on' to 'standby'
TRAFFIC: [          131237] >> 4f:90:01
DEBUG:   [          131237] >> Playback 1 (4) -> Broadcast (F): report power status (90)
'''

logger = logging.getLogger(__name__)


def setup_logging():
    logging_config = {'level': logging.INFO,
                      'format': '%(asctime)s [%(levelname)s] %(message)s',
                      'handlers': [
                          logging.StreamHandler()
                      ]}
    logging.basicConfig(**logging_config)


def turn_off_tv(tv_ip_address, adb_port=5555):
    # Load the public and private keys
    adbkey = os.path.expanduser('~/.android/adbkey')
    with open(adbkey) as f:
        priv = f.read()
    with open(adbkey + '.pub') as f:
        pub = f.read()
    signer = PythonRSASigner(pub, priv)

    # Connect
    device1 = AdbDeviceTcp(tv_ip_address, adb_port, default_transport_timeout_s=9.)
    device1.connect(rsa_keys=[signer], auth_timeout_s=0.1)

    # Send a shell command
    response = device1.shell('input keyevent 26')
    logger.info(response)


# def run_command(command):
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
#     should_continue = True
#     while should_continue:
#         output = process.stdout.readline()
#         if not output:
#             print('sleeping')
#             time.sleep(5)
#         output = output.decode('utf-8')
#         if output == '' and process.poll() is not None:
#             break
#         if output:
#             print(output.strip())
#         if output and 'TRAFFIC' in output and ':36' in output:
#             print('shutting down TV')
#     rc = process.poll()
#     return rc


async def _read_stream(stream, cb):
    while True:
        line = await stream.readline()
        if line:
            cb(line)
        else:
            break


async def _stream_subprocess(cmd, stdout_cb, stderr_cb):
    process = await asyncio.create_subprocess_exec(*cmd,
                                                   stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    await asyncio.wait([
        _read_stream(process.stdout, stdout_cb),
        _read_stream(process.stderr, stderr_cb)
    ])
    return await process.wait()


def monitor_command(line):
    output = line.decode('utf-8').rstrip()
    logger.info(output)
    if output and 'TRAFFIC' in output and ':36' in output:
        logger.info('shutting down TV')
        turn_off_tv(os.getenv('TV_IP_ADDRESS'))


def execute(cmd, stdout_cb, stderr_cb):
    loop = asyncio.get_event_loop()
    rc = loop.run_until_complete(
        _stream_subprocess(
            cmd,
            stdout_cb,
            stderr_cb,
        ))
    loop.close()
    return rc


if __name__ == '__main__':
    setup_logging()

    execute(
        ['bash', '-c', 'cec-client --monitor'],
        monitor_command,
        lambda line: logger.error(line),
    )

    # run_command('sleep 1; echo 'finished sleeping'; sleep 1; echo 'XE:FA'; sleep 1; echo 'broadcast';')
    # run_command('cec-client --monitor')
