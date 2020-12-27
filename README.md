# Buybacks for Alliance Auth

This is a buyback program management app for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) (AA).

![License](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.6-informational) ![django](https://img.shields.io/badge/django-3.1-informational)

## Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Updating](#updating)
- [Settings](#settings)
- [Operation Mode](#operation-mode)
- [Permissions](#permissions)
- [Pricing](#pricing)
- [Contract Check](#contract-check)
- [Change Log](CHANGELOG.md)

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

### 2 Update Eve Online app

Update the Eve Online app used for authentication in your AA installation to include the following scopes:

```plain
esi-universe.read_structures.v1
esi-contracts.read_corporation_contracts.v1
```

### 3. Configure AA settings

Configure your AA settings (`local.py`) as follows:

- Add `'buybacks'` to `INSTALLED_APPS`
- Add these lines add to bottom of your settings file:

   ```python
   # settings for freight
   CELERYBEAT_SCHEDULE['freight_run_contracts_sync'] = {
       'task': 'freight.tasks.run_contracts_sync',
       'schedule': crontab(minute='*/10'),
   }
   ```

If you want to setup notifications for Discord you can now also add the required settings. Check out section **Settings** for details.

### 4. Finalize installation into AA

Run migrations & copy static files

```bash
python manage.py migrate
python manage.py collectstatic
```

Restart your supervisor services for AA

### 5. Setup permissions

Now you can access Alliance Auth and setup permissions for your users. See section **Permissions** below for details.

### 6. Setup contract handler

Finally you need to set the contract handler with the character that will be used for fetching the corporation or alliance contracts and related structures. Just click on "Set Contract Handler" and add the requested token. Note that only users with the appropriate permission will be able to see and use this function. However, the respective character does not need any special corporation roles. Any corp member will work.

Once a contract handler is set the app will start fetching contracts. Wait a minute and then reload the contract list page to see the result.

### 7. Define pricing

Finally go ahead and define the first pricing of a courier route. See section **Pricing** for details.

That's it. The Freight app is fully installed and ready to be used.

## Updating

To update your existing installation of Freight first enable your virtual environment.

Then run the following commands from your AA project directory (the one that contains `manage.py`).

```bash
pip install -U aa-freight
```

```bash
python manage.py migrate
```

```bash
python manage.py collectstatic
```

Finally restart your AA supervisor services.

## Settings

Here is a list of available settings for this app. They can be configured by adding them to your AA settings file (`local.py`). If they are not set the defaults are used.

Name | Description | Default
-- | -- | --
`FREIGHT_APP_NAME`| Name of this app as shown in the Auth sidebar, page titles and as default avatar name for notifications. | `'Freight'`
`FREIGHT_CONTRACT_SYNC_GRACE_MINUTES`| Sets the number minutes until a delayed sync will be recognized as error  | `30`
`FREIGHT_DISCORD_DISABLE_BRANDING`| Turns off setting the name and avatar url for the webhook. Notifications will be posted by a bot called "Freight" with the logo of your organization as avatar image | `False`
`FREIGHT_DISCORD_MENTIONS`| Optional mention string put in front of every notification to create pings: Typical values are: `@here` or `@everyone`. You can also mention roles, however you will need to add the role ID for that. The format is: `<@&role_id>` and you can get the role ID by entering `_<@role_name>` in a channel on Discord. See [this link](https://www.reddit.com/r/discordapp/comments/580qib/how_do_i_mention_a_role_with_webhooks/) for details. | `''`
`FREIGHT_DISCORD_WEBHOOK_URL`| Webhook URL for the Discord channel where contract notifications for pilots should appear. | `None`
`FREIGHT_DISCORD_CUSTOMERS_WEBHOOK_URL`| Webhook URL for the Discord channel where contract notifications for customers should appear. | `None`
`FREIGHT_FULL_ROUTE_NAMES`| Show full name of locations in route, e.g on calculator drop down  | `False`
`FREIGHT_HOURS_UNTIL_STALE_STATUS`| Defines after how many hours the status of a contract is considered to be stale. Customer notifications will not be sent for a contract status that has become stale. This settings also prevents the app from sending out customer notifications for old contracts. | `24`
`FREIGHT_OPERATION_MODE`| See section [Operation Mode](#operation-mode) for details.<br> Note that switching operation modes requires you to remove the existing contract handler with all its contracts and then setup a new contract handler | `'my_alliance'`
`FREIGHT_STATISTICS_MAX_DAYS`| Sets the number of days that are considered for creating the statistics  | `90`

## Operation Mode

The operation mode defines which contracts are processed by the Freight. For example you can define that only contracts assigned to your alliance are processed. Any courier contract that is  not in scope of the configured operation mode will be ignored by the freight app and e.g. not show up in the contract list or generate notifications.

The following operation modes are available:

Name | Description
-- | --
`'my_alliance'`| courier contracts assigned to configured alliance by an alliance member
`'my_corporation'`| courier contracts assigned to configured corporation by a corp member
`'corp_in_alliance'`| courier contracts assigned to configured corporation by an alliance member
`'corp_public'`| any courier contract assigned to the configured corporation

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
