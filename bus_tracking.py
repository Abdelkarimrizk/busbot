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

def fetch_gtfs_pb(url):
    result = subprocess.run(
        ["curl", "-s", url],
        capture_output=True
    )
    return result.stdout

def get_next_arrivals(stop_id, route_id):
    url = "https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates"
    response_content = fetch_gtfs_pb(url)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response_content)
    print(feed)
    now = datetime.datetime.now(TIMEZONE)
    arrivals = []
    
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

def bus_monitor(context, chat_id, stop_id, route_id):
    already_sent = set()
    end_time = datetime.datetime.now(TIMEZONE) + datetime.timedelta(minutes=70)
    
    while datetime.datetime.now(TIMEZONE) < end_time:
        
        if active_monitors.get(chat_id) is False:
            break
        
        arrivals = get_next_arrivals(stop_id, route_id)
        now = datetime.datetime.now(TIMEZONE)
        for dept_time in arrivals:
            mins = (dept_time - now).total_seconds() / 60
            rounded = int(dept_time.timestamp())
            
            if 9 <= mins <= 11 and rounded not in already_sent:
                already_sent.add(rounded)
                context.bot.send_message(chat_id=chat_id, text=f"Bus {route_id} arriving in around {int(mins)} minutes")
    
        for i in range(60):
            if active_monitors.get(chat_id) is False:
                break
            time.sleep(1)
    
    active_monitors.pop(chat_id, None)
        
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
                                        f"{locations_str}\n")
        return
    
    chat_id = update.message.chat_id
    if active_monitors.get(chat_id) is True:
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
    for time in arrivals[:3]:
        reply += f"- {time.strftime('%I:%M %p')}\n"
    await update.message.reply_text(reply)
    
    active_monitors[chat_id] = True
    
    thread = threading.Thread(
        target = bus_monitor,
        args = (context, update.message.chat_id, stop_id, route_id)
    )
    thread.start()
    
    
async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in active_monitors:
        active_monitors[chat_id] = False
        await update.message.reply_text("Bus tracker stopped.")
    else:
        await update.message.reply_text("No active bus tracker found.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Use /help for a list of commands.")
    
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in active_monitors:
        await update.message.reply_text("Bus tracker is active.")
    else:
        await update.message.reply_text("No active bus tracker found.")

USER_ID = os.getenv("USER_ID")

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != USER_ID:
        await update.message.reply_text("You are not authorized to shut down the bot.")
        return
    await update.message.reply_text("Shutting down the bot.")
    os._exit(0)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Available commands:\n"
                                      "/route [location] - Start tracking bus arrivals for a location\n"
                                      "/stop - Stop tracking bus arrivals\n"
                                      "/help - Show this help message\n"
                                      "/status - Check if a bus tracker is active\n")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    # command handling
    app.add_handler(CommandHandler("route", route_handler))
    app.add_handler(CommandHandler("stop", stop_handler))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("shutdown", shutdown))
    
    # unknown handling
    app.add_handler(MessageHandler(filters.TEXT, unknown))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.run_polling()
    

if __name__ == "__main__":
    main()