# Telegram Bots Collection
======================

A collection of Telegram bots implemented in Python, each serving a specific purpose.

## Table of Contents
-----------------

1. [Project Overview](#project-overview)
2. [Available Bots](#available-bots)
3. [Requirements](#requirements)
4. [Setup Instructions](#setup-instructions)

## Project Overview
---------------

This repository contains multiple Telegram bots organized in separate folders, each with its own functionality   
and configuration. The structure allows for easy maintenance and updates of individual bots while keeping related   
projects together.

## Available Bots
--------------

### Bot 1: Telegram_mysql_bot
- **Description**: The program is intended for interacting with the user to further collect information and  
- transfer it to the database of the site.
- **Commands**: `/start`, `/register`, `/start `
- **Features**: Processing the name and last name of the user. Getting a phone number. Record of specialization. 
- Collection of information about yourself. Photo download. Preservation of all data in the WordPress database.
- **Status**: Production-ready

### Bot 2: TelegrambotWorkTasks
- **Description**: Allows you to set tasks for drivers, forwarders, couriers.
- **Commands**: `/start`, `/knight`, `/mouse`, `/tasks`, `/kostroma`, `/msk`, `/filter`, `/basic_menu`, 
- `/set_a_task`, `/status`, `/take_task`, `/to_mark`, `/accept`, `/reject`
- **Features**: Testing user access. Registration of new users. The purpose of the roles (driver/manager). 
- Task management. Filtering tasks by cities. Management status management.
- **Status**: Production-ready

### Bot 3: Telegrambot_time_manager
- **Description**: Notifies customers about the time of time.
- **Commands**: `/start`
- **Status**: Production-ready

## Requirements
------------

Before running any bot:

```bash
pip install python-telegram-bot
pip install python-dotenv
```

## Setup Instructions
-------------------

1. Clone the repository:
   ```bash
   git clone https://github.com/NikolayChegivarov/Telegam_bots.git
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Update `.env` with your bot token and other settings.

3. Install dependencies:
   ```bash
   cd bot_name
   pip install -r requirements.txt
   ```

4. Run the bot:
   ```bash
   python main.py
   ```
