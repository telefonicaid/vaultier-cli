# vaultcli
Awesome CLI client for Vaultier password manager

## Installation

For security reasons, this software depends of Python 3.6 or higher.

Ubuntu users
```bash
sudo add-apt-repository ppa:jonathonf/python-3.6
sudo apt install python3.6 python3.6-venv
```


```bash
git clone https://github.com/Telefonica/vaultier-cli.git
virtualenv ./vaultcli
source ./vaultcli/bin/activate
cd vaultier-cli
python setup.py install
```

## Configure

Before run, you need to configure _vaultcli_. By default it looks for config
file in your home dir in two valid locations.

* `~/.config/vaultcli/vaultcli.conf`
* `~/.vaultcli.conf`

You can copy the sample config file to one of these locations and edit it,
or use the following fancy method to make configuration.

```bash
touch ~/.config/vaultcli/vaultcli.conf
vaultcli config email your.login.email@example.com
vaultcli config server https://your.vaultier.server.example.com
vaultcli config key /location/of/your/vaultier.key
```

Optionally, if your server have a self signed certificate, you can disable
the certificate check.

```bash
vaultcli config verify false
```

## Run

Simply run `vaultcli` command with `-h` or `--help` to read the help of
command. It's self explanatory.

Happy secring!!!


## FUSE / Vault as file system

See `contrib/fuse/`
