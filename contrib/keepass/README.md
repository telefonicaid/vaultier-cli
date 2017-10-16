# Keepass importer
Import a ``.kdbx`` file to a Vaultier server

This app will import all keepass data inside a Workspace.

## Install
```
pip install -r requirements.txt
```

## Use
You need to have ``~/.config/vaultcli/vaultcli.conf`` correctly configured before using the importer.

```
python keepass_to_vault.py -f file.kdbx -p "pass" -w "WorkspaceName"
```

Vaults and cards will be unique respect its name.

Several secrets could exists with the same name.

If you try to reimport a keepass file you will get all already existent secrets duplicated.

## How it is mapped
### Folders
Keepass allow any number of subfolders, meanwhile inside a Vault Workspace we only have ``vault`` and ``card`` level.

This is solved mapping first level folders to vaults and the rest of subfolders will be flattened joinen the names with dots.

Example:
 keepass:
  - Icinga/Production/Puppet/foo

 vaultier
  - Vault=Icinga, Card=Production.Puppet, Secret=foo

### Names
If some folder or secret name contains an slash ("/") it will be substituted by a underscore ("_").

If some secret doesn't have a name, the user will be used as the name.

If there is no name neither user, a sequential number will be used.
