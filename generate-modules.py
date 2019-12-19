
from yaml import load
from yaml import dump
from yaml import SafeLoader

import os
import asyncio
from asyncio import create_subprocess_shell


COMMANDS = [
    { 'cmd': 'git init', 'cwd': '{name}' },
    { 'cmd': 'git remote add origin {url}', 'cwd': '{name}' },
    { 'cmd': 'git fetch origin {commit}', 'cwd': '{name}' },
    { 'cmd': 'git reset --hard FETCH_HEAD', 'cwd': '{name}' },
    { 'cmd': 'node jamovi-compiler/index.js --build {name} --home jamovi-1.1.7.0-win64', 'cwd': '.' },
]

async def generate_modules():

    with open('modules.yaml', 'r') as stream:
        library = load(stream, Loader=SafeLoader)

        for module in library['modules']:
            dir = module['name']
            os.makedirs(dir, exist_ok=True)

            for cmd in COMMANDS:
                cwd = cmd['cwd']
                cwd = cwd.format(**module)
                cmd = cmd['cmd']
                cmd = cmd.format(**module)
                proc = await create_subprocess_shell(cmd, cwd=cwd)
                rc = await proc.wait()
                if rc != 0:
                    raise RuntimeError('Command failed')


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(generate_modules())
finally:
    loop.close()
    asyncio.set_event_loop(None)
