from google.transit import gtfs_realtime_pb2
import subprocess

headers = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_gtfs_pb(url):
    result = subprocess.run(
        ["curl", "-s", url],
        capture_output=True
    )
    return result.stdout

url = "https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates"
response_content = fetch_gtfs_pb(url)
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response_content)

# Print the entire protobuf message
with open("gtfs_feed.txt", "w") as f:
    f.write(str(feed))