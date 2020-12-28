<!-- omit in toc -->
# Buybacks for Alliance Auth

This is a buyback program management app for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) (AA).

![License](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.6-informational) ![django](https://img.shields.io/badge/django-3.1-informational)

<!-- omit in toc -->
## Contents

1. [Key Features](#key-features)
2. [Installation](#installation)
   1. [1. Install app](#1-install-app)
   2. [2. Update Eve Online app](#2-update-eve-online-app)
   3. [3. Configure AA settings](#3-configure-aa-settings)
   4. [4. Finalize installation into AA](#4-finalize-installation-into-aa)
   5. [5. Data import](#5-data-import)
   6. [6. Setup permissions](#6-setup-permissions)
   7. [7. Setup corp](#7-setup-corp)
   8. [8. Define programs](#8-define-programs)
3. [Updating](#updating)
4. [Settings](#settings)
5. [Permissions](#permissions)
6. [Contract Check](#contract-check)

<!-- omit in toc -->
## Overview

This app helps running buyback programs for an alliance or corporation.

## Key Features

It offers the following main features:


## Installation

### 1. Install app

Install into your Alliance Auth virtual environment from PyPI:

```bash
pip install aa-buybacks
```

### 2. Update Eve Online app

Update the Eve Online app used for authentication in your AA installation to include the following scopes:

```plain
esi-universe.read_structures.v1
esi-contracts.read_corporation_contracts.v1
esi-assets.read_corporation_assets.v1
```

### 3. Configure AA settings

Configure your AA settings (`local.py`) as follows:

- Add `'buybacks'` to `INSTALLED_APPS`
- Add these lines add to bottom of your settings file:

   ```python
   # settings for buybacks
   CELERYBEAT_SCHEDULE['buybacks_update_all_offices'] = {
       'task': 'buybacks.tasks.update_all_offices',
       'schedule': crontab(minute=0, hour='*/12'),
   }
   CELERYBEAT_SCHEDULE['buybacks_sync_contracts'] = {
       'task': 'buybacks.tasks.sync_all_contracts',
       'schedule': crontab(minute=0, hour='*'),
   }
   ```

### 4. Finalize installation into AA

Run migrations & copy static files

```bash
python manage.py migrate
python manage.py collectstatic
```

Restart your supervisor services for AA

### 5. Data import

Load EVE Online type data from ESI:

```bash
python manage.py buybacks_load_types
```

### 6. Setup permissions

Now you can access Alliance Auth and setup permissions for your users. See section **Permissions** below for details.

### 7. Setup corp

Finally you need to set a corporation with the character that will be used for fetching the corporation offices, contracts and related structures. Just click on "Setup Corp" and add the requested token.

> Note that only users with the appropriate permission will be able to see and use this function.

> Note that the respective character needs to be a director for the corporation.

### 8. Define programs


That's it. The Buybacks app is fully installed and ready to be used.

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

## Settings

Here is a list of available settings for this app. They can be configured by adding them to your AA settings file (`local.py`). If they are not set the defaults are used.

Name | Description | Default
-- | -- | --
`FREIGHT_STATISTICS_MAX_DAYS`| Sets the number of days that are considered for creating the statistics  | `90`

## Permissions

This is an overview of all permissions used by this app:

Name | Purpose | Code
-- | -- | --
Can add / update locations | User can add and update Eve Online contract locations, e.g. stations and upwell structures |  `add_location`
Can access this app |Enabling the app for a user. This permission should be enabled for everyone who is allowed to use the app (e.g. Member state) |  `basic_access`
Can setup contract handler | Add or updates the character for syncing contracts. This should be limited to users with admins / leadership privileges. |  `setup_contract_handler`
Can use the calculator | Enables using the calculator page and the "My Contracts" page. This permission is usually enabled for every user with the member state. |  `use_calculator`
Can view the contracts list | Enables viewing the page with all outstanding courier contracts  |  `view_contracts`
Can see statistics | User with this permission can view the statistics page  |  `view_statistics`

> **How to add new locations**:<br>If you are creating a pricing for a new route you may need to first add the locations (stations and/or structures).<br>The easiest way is to create a courier contract between those locations in game and then run contract sync. Those locations will then be added automatically.<br>Alternatively you can use the "Add Location" feature on the main page of the app. This will require you to provide the respective station or structure eve ID.

## Contract Check

The app will automatically check if a newly issued contract complies with the pricing parameters for the respective route.

Compliant contracts will have a green checkmark (✓) in the "Contract Check" column on the contract list. Related notifications on Discord will be colored in green.

Non-compliant contracts will have a red warning sign in the "Contract Check" column on the contract list. And related notifications on Discord will be colored in red. In addition the first customer notification will inform the customer about the issues and ask him to correct the issues.

The following parameters will be checked (if they have been defined):

- reward in contract >= calculated reward
- volume min <= volume in contract <= volume max
- collateral min <= collateral in contract <= collateral max

Deviations on "Days to expire" and "Days to complete" are currently not part of the contract check and only used to show the recommended contract parameters in the calculator.
