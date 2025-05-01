<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

This Telegram bot tracks bus arrivals for specific routes using the Waterloo Region Transit (GRT) GTFS reel time feed. It returns the bus schedule for a given stop and trip, and it sends notifications when buses are about to arrive.

This was made with the intention of running on a cloud server (Hetzner), but it can also be deployed locally on any server.

**Key Features:**
- Track bus arrivals in real time
- Receive notifications when buses are about 10 minutes away
- Handle multiple trackers for the same user simultaneously
- Run continuously in the background, with automatic restarts if the bot crashes

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

These instructions will help you set up the project locally. Follow these steps to run the bot on your machine.

### Prerequisites

Make sure you have python 3.8 or above and pip installed on your machine.

- **Get a Telegram bot token:**
  - Open @BotFather on Telegram
  - Type /newbot
  - Follow the instructions and create your bot
  - Copy the token given to you
- **Find your user ID on telegram:**
  - Open @userinfobot on Telegram
  - Type /start
  - Copy the Id given to you

### Installation

1. Clone the repo:
   ```sh
   git clone https://github.com/Abdelkarimrizk/busbot.git
   ```
2. Enter the project folder:
   ```sh
   cd busbot
   ```
3. Set up a virtual environment(This was done on powershell):
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install the requirments:
   ```sh
   pip install -r requirements.txt
   ```
5. Create the .env file and write:
   ```ini
   TELEGRAM_TOKEN=your_telegram_bot_token
   USER_ID=your_user_id
   ```
6. Edit bus_tracking.py and add the routes you'd like to follow to ROUTES
7. Run the bot:
   ```sh
   python bus_tracking.py
   ```

**Sidenote:**
Instead of manually running the bot, you can use the Bash scripts that are given to have the bot continuously run in the background.

**This is for a cloud server!!! If you are running the bot on your machine, you would need to follow a different set of steps that are specific to your os**

To have it run continuously on a cloud server:

1. Start the bot using screen:
   - Make `start_busbot.sh` executable:
       ```sh
       chmod +x start_busbot.sh
       ```
   - Make `start_screen.sh` executable:
       ```sh
       chmod +x start_screen.sh
       ```
   - Run the `start_screen.sh` script to create the screen:
       ```sh
       ./start_screen.sh
       ```
2. Check if the bot is running (trust me, check)
   - Run:
       ```sh
       screen -ls
       ```
   - It should return:
       ```ini
       There is a screen on:
           *****.busbot ... (Detached)
       ```
     (if you can't see that, gl)
3. Set it to automatically start on server reboot:
   - Add a cron job to automatically start the bot on a server reboot:
     ```sh
     crontab -e
     ```
     - Add the following line to the end of ^:
      ```sh
      @reboot /path/to/your/busbot/start_screen.sh
      ```
4. To stop the bot from running:
   - Run:
     ```sh
     screen -S busbot -X quit
     ```
   - And if you'd like to stop it from running on reboot, remove:
     ```sh
      @reboot /path/to/your/busbot/start_screen.sh
      ```
     from the crontab.


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Once the bot is running, you can use the following commands to interact with it:

- /route [location]: Start tracking bus arrivals for the given location
- /stop [location]: Stop tracking bus arrivals for the given location
- /status: View all active bus trackers
- /shutdown: Shuts the bot down (admin only)
- /testmsg: Tests sending a message from a background thread
- /help: Sends a message similar to this list

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>





