
from oyaml import load
from oyaml import dump
from oyaml import SafeLoader

from collections import OrderedDict
from zipfile import ZipFile
from os import scandir
from os.path import basename

import os
import sys
import asyncio
from asyncio import create_subprocess_shell


async def generate_modules():

    PREP_COMMANDS = [
        'git init',
        'git remote add origin {url}',
        'git pull origin master',
        'git checkout {commit}',
        ('RD build /Q /S & echo ""' if os.name == 'nt' else 'rm -rf build'),
        # { 'cmd': 'git fetch origin {commit}', 'cwd': '{name}' },
        # { 'cmd': 'git reset --hard FETCH_HEAD', 'cwd': '{name}' },
    ]

    BUILD_COMMANDS = [
        'node jamovi-compiler/index.js --build {name} --home jamovi-1.1.9.0-R3.6-win64 --jmo {name}.jmo',
        'appveyor PushArtifact {name}.jmo -FileName {outdir}/{name}-{version}.jmo -DeploymentName Modules',
    ]

    with open('modules.yaml', 'r') as stream:
        library = load(stream, Loader=SafeLoader)

    for module in library['modules']:
        dir = module['name']
        os.makedirs(dir, exist_ok=True)

        for cmd in PREP_COMMANDS:
            cmd = cmd.format(outdir='win64/R3.6', **module)
            proc = await create_subprocess_shell(cmd, cwd=dir)
            rc = await proc.wait()
            if rc != 0:
                raise RuntimeError('Command failed: "{}"'.format(cmd))

        with open('{}/jamovi/0000.yaml'.format(dir), 'r') as stream:
            defn = load(stream, Loader=SafeLoader)
            module['version'] = defn['version']

        for cmd in BUILD_COMMANDS:
            cmd = cmd.format(outdir='win64/R3.6', **module)
            proc = await create_subprocess_shell(cmd)
            rc = await proc.wait()
            if rc != 0:
                raise RuntimeError('Command failed: "{}"'.format(cmd))

async def generate_index():

    keep_info = [
        'name',
        'title',
        'version',
        'authors',
        'description'
    ]

    with open('modules.yaml', 'r') as stream:
        library = load(stream, Loader=SafeLoader)

    modules = [ ]

    for module in library['modules']:
        name = module['name']
        jmo = '{}.jmo'.format(name)
        zip = ZipFile(jmo)
        with zip.open('{}/jamovi.yaml'.format(name)) as stream:
            content = stream.read()
            data = load(content, Loader=SafeLoader)
            final = OrderedDict()
            for key in keep_info:
                final[key] = data.get(key)
            modules.append(final)

    modules = sorted(modules, key=lambda x: x['name'])

    index = {
        'jds': '1.4',
        'modules': modules,
    }

    with open('index', 'w', encoding='utf-8') as file:
        dump(index, file)

asyncio.run(generate_modules())
asyncio.run(generate_index())
