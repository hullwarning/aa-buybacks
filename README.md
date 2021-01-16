<!-- omit in toc -->
# Buybacks for Alliance Auth

This is a buyback program management app for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) (AA).

![License](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.6-informational) ![django](https://img.shields.io/badge/django-3.1-informational)

<!-- omit in toc -->
## Contents

1. [Key Features](#key-features)
2. [Installation](#installation)
   1. [Install app](#install-app)
   2. [Update Eve Online app](#update-eve-online-app)
   3. [Configure AA settings](#configure-aa-settings)
   4. [Finalize installation into AA](#finalize-installation-into-aa)
   5. [Data import](#data-import)
   6. [Setup permissions](#setup-permissions)
   7. [Setup corp](#setup-corp)
   8. [Define programs](#define-programs)
   9. [Calculating](#calculating)
3. [Updating](#updating)
4. [Tips & Tricks](#tips--tricks)
5. [TODO](#todo)

<!-- omit in toc -->
## Overview

This app helps running buyback programs for an alliance or corporation.

## Key Features

It offers the following main features:

* Manage corporation buyback programs
* Calculate value of the items that will be sent to the buyback program
* Store statistics on the usage of buyback programs

## Installation

### Install app

Install into your Alliance Auth virtual environment from PyPI:

```bash
pip install aa-buybacks
```

### Update Eve Online app

Update the Eve Online app used for authentication in your AA installation to include the following scopes:

```plain
esi-universe.read_structures.v1
esi-contracts.read_corporation_contracts.v1
esi-assets.read_corporation_assets.v1
```

### Configure AA settings

Configure your AA settings (`local.py`) as follows:

- Add `'eveuniverse'` and `'buybacks'` to `INSTALLED_APPS`
- Add these lines to bottom of your settings file:

   ```python
   # settings for buybacks
   CELERYBEAT_SCHEDULE['buybacks_update_all_offices'] = {
       'task': 'buybacks.tasks.update_all_offices',
       'schedule': crontab(minute=0, hour='*/12'),
   }
   CELERYBEAT_SCHEDULE['buybacks_sync_all_contracts'] = {
       'task': 'buybacks.tasks.sync_all_contracts',
       'schedule': crontab(minute=0, hour='*'),
   }
   ```

### Finalize installation into AA

Run migrations & copy static files

```bash
python manage.py migrate
python manage.py collectstatic
```

Restart your supervisor services for AA

### Data import

Load EVE Online type data from ESI:

```bash
python manage.py buybacks_load_types
```

### Setup permissions

Now you can access Alliance Auth and setup permissions for your users. This is an overview of all permissions used by this app:

Name | Purpose | Code
-- | -- | --
Can access this app and view buyback programs |Enabling the app for a user. This permission should be enabled for everyone who is allowed to use the app (e.g. Member state) | `basic_access`
Can setup corporation | Add or updates the character for syncing offices and contracts. This should be limited to users with admins / leadership privileges. | `setup_retriever`
Can manage buyback programs | User with this permission can manage the buyback programs and view the cumulative statistics | `manage_programs`

### Setup corp

Finally you need to set a corporation with the character that will be used for fetching the corporation offices, contracts and related structures. Just click on **Setup Corp** and add the requested token.

> Note that only users with the appropriate permission will be able to see and use this button.

> Note that the respective character needs to be a **director** for the corporation.

### Define programs

Let's say your corp has an ORE buyback program and you want to use this tool for that. First, you need to click on **Create Program** and fill the name of the program.

> Note that only users with the appropriate permission will be able to see and use this button.

Once it is created, you should be able to add all the locations (where your corp has an office) denoting the structures or stations to create the contracts for. You might only accept the ores in certain corp refineries and don't want people to send it other structures.

You should also be able to add all the items and the percentage the corp skims on top of the price. For example, for your ORE buyback program, add **Plagioclase** with brokerage set at 20%.

That's it. The buybacks program is fully created and ready to be used.

### Calculating

Any character can use one of the buyback programs by clicking on **Use** button on one of the program. Once done, they need to select the location and can copy-paste the items they want to send to the corp. When they click on **Calculate**, the app calculates the exact amount based on the prices defined in the program and shows them that total value.

Once they see the total value, they would need to send an in-game contract for the exact amount and then click on **Notify** to notify the app about it.

Once the corp accepts a contract, our contracts sync feature would automatically match the corresponding notification (based on the total price, items with quantities and the location of the contract) and store it in the statistics.

## Updating

To update your existing installation of Buybacks first enable your virtual environment.

Then run the following commands from your AA project directory (the one that contains `manage.py`).

```bash
pip install -U aa-buybacks
```

```bash
python manage.py migrate
python manage.py collectstatic
```

Finally restart your AA supervisor services.

## Tips & Tricks

* If you want to edit the brokerage of an item in a program, you can just add the item with the new brokerage and it will update the existing one.

## TODO

* Use refined value to calculate OREs
* Set refining percentage per item
* Statistics filtering
