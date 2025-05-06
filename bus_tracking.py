import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from google.transit import gtfs_realtime_pb2
from dotenv import load_dotenv
import os
import subprocess
import threading
import time
import asyncio

load_dotenv(dotenv_path=".env")

# API key of telegram bot
# Replace with your actual Telegram bot token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

TIMEZONE = pytz.timezone('America/Toronto')

ROUTES = {
    "gym" : {"stop_id": "1168",
             "route_id": "19"}
}

active_monitors = {}

# Fetches the gtfs pb from the url(in this case from the grt opendata)
def fetch_gtfs_pb(url):
    result = subprocess.run(
        ["curl", "-s", "--ciphers", "DEFAULT@SECLEVEL=1", url],
        capture_output=True
    )
    print(f"[DEBUG] Downloaded {len(result.stdout)} bytes from GTFS feed")
    return result.stdout


def get_next_arrivals(stop_id, route_id):
    # Fetches the real time trip updates from the grt opendata
    url = "https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates"
    response_content = fetch_gtfs_pb(url)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response_content)
    now = datetime.datetime.now(TIMEZONE)
    arrivals = []
    
    # Loops through the entities in the feed and checks if they have a trip_update field
    # If the field exists, it checks the route_id and stop_id
    # If those match, it gets the arrival time of the bus and adds it to the arrivals array
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        
        trip = entity.trip_update
        if str(trip.trip.route_id) != route_id:
            continue
        
        for stop_time in trip.stop_time_update:
            if stop_time.stop_id == stop_id:
                dep_time = datetime.datetime.fromtimestamp(
                    stop_time.arrival.time, tz=TIMEZONE
                )
                if dep_time > now:
                    arrivals.append(dep_time)
                    
    return sorted(arrivals)


def bus_monitor(context, chat_id, stop_id, route_id, loop, location):
    already_sent = set()
    # Stops the while loop after 70 minutes
    end_time = datetime.datetime.now(TIMEZONE) + datetime.timedelta(minutes=70)
    
    # Continously loops until the end_time is reached or the user stops the tracker
    # Gets the next arrivals and checks if they are within 9-11 minutes of the current time
    # If one is, it sends a message to the user then adds the time to already_sent
    # It sleeps for 1 minute between checks to not fetch too often.
    while datetime.datetime.now(TIMEZONE) < end_time:
        
        if active_monitors.get((chat_id, location)) is False:
            break
        
        arrivals = get_next_arrivals(stop_id, route_id)
        now = datetime.datetime.now(TIMEZONE)
        for dept_time in arrivals:
            mins = (dept_time - now).total_seconds() / 60
            rounded = int(dept_time.timestamp())
            
            if 9 <= mins <= 11 and rounded not in already_sent:
                already_sent.add(rounded)
                asyncio.run_coroutine_threadsafe(
                    context.bot.send_message(chat_id=chat_id, text=f"Bus {route_id} arriving in around {int(mins)} minutes, at {dept_time.strftime('%I:%M %p')}."),
                    loop
                )
    
        for i in range(60):
            if active_monitors.get((chat_id, location)) is False:
                break
            time.sleep(1)
    
    # Removes the chat_id from active_monitors since the tracker is done
    active_monitors.pop((chat_id, location), None)

# This function is called when the user sends the /route [location] command
# It first checks if the user gave a location and if its valid
# If it is not valid, it sends a message to the user with the available locations
# If it is valid, it checks if the user already has a tracker running
# If not, it gets the next arrivals, sends them to the user if they exist
#   and starts the bus tracker in a new thread
async def route_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /route [location]")
        return
    
    location = context.args[0].lower()
    locations = [loc.lower() for loc in ROUTES.keys()]
    locations_str = "\n".join(locations)
    if location not in ROUTES:
        await update.message.reply_text("Location not found.\n")
        await update.message.reply_text("Available locations:\n"
                                        f"- {locations_str}\n")
        return
    
    chat_id = update.message.chat_id
    if active_monitors.get((chat_id, location)) is True:
        await update.message.reply_text(f"You already have a {location} tracker running. Use /stop to stop it.")
        return
    
    config = ROUTES[location]
    stop_id = config["stop_id"]
    route_id = config["route_id"]
    
    arrivals = get_next_arrivals(stop_id, route_id)
    if not arrivals:
        await update.message.reply_text("No upcoming buses found. No tracker started.")
        return
    
    reply = f"Upcoming buses for {location}:\n"
    for time in arrivals[:7]:
        reply += f"- {time.strftime('%I:%M %p')}\n"
    await update.message.reply_text(reply)
    
    active_monitors[(chat_id, location)] = True
    
    loop = context.bot_data["loop"]
    thread = threading.Thread(
        target = bus_monitor,
        args = (context, update.message.chat_id, stop_id, route_id, loop, location)
    )
    thread.start()
    

# This function is called when the user sends the /stop [location] command
# It checks if the user has a tracker running and stops it if they do
async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    if not context.args:
        await update.message.reply_text("Usage: /stop [location]")
        return
    
    location = context.args[0].lower()
    if (chat_id, location) in active_monitors:
        active_monitors[(chat_id, location)] = False
        await update.message.reply_text(f"Bus tracker for {location} stopped.")
    else:
        await update.message.reply_text(f"No bus tracker for {location} found.")

# This function is called when the user sends an unknown command or message
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Use /help for a list of commands.")

# This function is called when the user sends the /status command
# It checks if there is a tracker running and sends a message to the user
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    locations = [loc for (cid, loc), active in active_monitors.items() if active and cid == chat_id]
    if locations:
        locations_str = "\n".join(locations)
        await update.message.reply_text(f"Active bus trackers:\n{locations_str}")
    else:
        await update.message.reply_text("No active bus trackers found.")

USER_ID = os.getenv("USER_ID")

# This function is called when the admin(USER_ID) sends the /shutdown command
# It shuts down the bot, stopping the program
async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != USER_ID:
        await update.message.reply_text("You are not authorized to shut down the bot.")
        return
    await update.message.reply_text("Shutting down the bot.")
    os._exit(0)

# This function is called when the user sends the /help command
# It sends a message to the user with the available commands
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Available commands:\n"
                                      "/route [location] - Start tracking bus arrivals for the given location\n"
                                      "/stop [location] - Stop tracking bus arrivals for the given location\n"
                                      "/status - View all active bus trackers\n"
                                      "/shutdown - Shuts the bot down (admin only)\n"
                                      "/testmsg - Test sending a message from a background thread\n"
                                      "/help - Show this help message\n")


# This function is called when the user sends the /testmsg command
# It sends a message to the user from a background thread
# This was used to make sure bus_monitor can actually send a message 10 minutes before the bus arrives
async def testmsg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    loop = context.bot_data["loop"]

    def threaded_send():
        asyncio.run_coroutine_threadsafe(
            context.bot.send_message(
                chat_id=chat_id,
                text="This message was sent from a background thread."),
                loop
            )

    threading.Thread(target=threaded_send).start()
    await update.message.reply_text("Started background thread.")

# This is used when the but is started to create the loop
async def on_startup(app):
    # This will run once the app is fully initialized and async-safe
    app.bot_data["loop"] = asyncio.get_running_loop()

def main():
    # Creates the application(bot) and sets the token
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(on_startup).build()
    
    # Command handling
    app.add_handler(CommandHandler("route", route_handler))
    app.add_handler(CommandHandler("stop", stop_handler))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("shutdown", shutdown))
    app.add_handler(CommandHandler("testmsg", testmsg))
    app.add_handler(CommandHandler("help", help))
    
    # Unknown handling
    app.add_handler(MessageHandler(filters.TEXT, unknown))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.run_polling()
    

if __name__ == "__main__":
    main()
