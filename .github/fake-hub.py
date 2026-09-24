"""Fake VU1 hub for CI: seeds the app config, serves a pty hub with no dials, then execs /init.

Run as the container entrypoint so the config exists before cont-init runs and the server finds the hub on first start.
"""
import os
import re

# Keep upstream's default server.hostname; blanking it is what cont-init must do.
with open('/opt/vu-server/config.yaml.default') as f:
    config = re.sub(r'(?m)^([ \t]+port:)[ \t]*$', r'\1 /dev/ttyUSB0', f.read())
os.makedirs('/data/vu-server', exist_ok=True)
with open('/data/vu-server/config.yaml', 'w') as f:
    f.write(config)

master, slave = os.openpty()
# pyserial's comports() lists /dev/ttyUSB* but not /dev/pts/*.
os.symlink(os.ttyname(slave), '/dev/ttyUSB0')

if os.fork():
    os.execv('/init', ['/init'])

buf = b''
while True:
    *lines, buf = (buf + os.read(master, 4096)).split(b'\r\n')
    for line in lines:
        if line.startswith(b'>'):
            # One zero byte: an empty dial map for GET_DEVICES_MAP, a truthy reply for every other command.
            os.write(master, b'<' + line[1:3] + b'02000100\r\n')
