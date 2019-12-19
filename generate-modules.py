
from yaml import load
from yaml import dump
from yaml import SafeLoader

import os
import sys
import asyncio
from asyncio import create_subprocess_shell


COMMANDS = [
    { 'cmd': 'git init', 'cwd': '{name}' },
    { 'cmd': 'git remote add origin {url}', 'cwd': '{name}' },
    { 'cmd': 'git fetch origin {commit}', 'cwd': '{name}' },
    { 'cmd': 'git reset --hard FETCH_HEAD', 'cwd': '{name}' },
    { 'cmd': 'node jamovi-compiler/index.js --build {name} --home jamovi-1.1.9.0-R3.6-win64 --jmo {name}.jmo' },
    { 'cmd': 'appveyor PushArtifact {name}.jmo -FileName {outdir}/{name}.jmo -DeploymentName Modules' },
]

async def generate_modules():

    with open('modules.yaml', 'r') as stream:
        library = load(stream, Loader=SafeLoader)

        for module in library['modules']:
            dir = module['name']
            os.makedirs(dir, exist_ok=True)

            for cmd in COMMANDS:
                cwd = cmd.get('cwd', '.')
                cwd = cwd.format(outdir='win64/R3.6', **module)
                cmd = cmd['cmd']
                cmd = cmd.format(outdir='win64/R3.6', **module)
                proc = await create_subprocess_shell(cmd, cwd=cwd)
                rc = await proc.wait()
                if rc != 0:
                    raise RuntimeError('Command failed: "{}"'.format(cmd))

asyncio.run(generate_modules())
