+++
authors = ["Shengtuo Hu"]
title = "X11 forwarding over SSH"
description = "Setting up X11 forwarding over SSH from Linux to macOS"
date = 2025-10-05T21:48:00-07:00
[taxonomies]
tags = ["Tutorial", "X11"]
[extra]
toc = true
toc_sidebar = true
+++

I am debugging a GUI application, running on my remote Linux machine, and want to stay in my macOS development environment. This tutorial briefly goes through SSH configurations on both sides (Linux, macOS) for X11 forwarding.

## Linux Setup

Of course, please ensure we have SSH server installed on the Linux machine at first.

```bash
sudo apt install openssh-server

# Check its status
sudo systemctl status ssh
```

Then, edit `/etc/ssh/sshd_config` to at least enable the following entries:

```/etc/ssh/sshd_config
AllowTcpForwarding yes
X11Forwarding yes
X11DisplayOffset 10
X11UseLocalhost yes
```

After that, restart `sshd` service to apply our configuration changes.

```bash
sudo systemctl restart ssh
```

## macOS Setup

On the other side, we need to install [XQuartz](https://www.xquartz.org/), an open-source X11 server for macOS. Note that, we have to log out and login again to enable xquartz after the installation.

```bash
brew install --cask xquartz
```

Now, we can connect to the remote Linux machine via SSH.

```bash
ssh -X foo@your.host.ip.addr
```

Usually, I would prefer saving the host and options in `~/.ssh/config` as shown below:

```~/.ssh/config
Host your-host-name*
    HostName your.host.ip.addr
    User foo
    Port 22
    IdentityFile ~/.ssh/id_rsa

Host your-host-name
    ForwardX11 no

Host your-host-name-x11
    ForwardX11 yes
```

I do not want X11 forwarding everytime, so I add two host entries. The second entry with `-x11` suffix has the X11 forwarding option, while the first one does not. Now, we can simply use `ssh your-host-name-x11` to connect the remote machine. If X11 is not needed, we can use `ssh your-host-name`.

## Reference

- [A quick and dirty guide to X11 forwarding over SSH](https://some-natalie.dev/blog/ssh-x11-forwarding/)
