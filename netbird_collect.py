#!/usr/bin/python3
import json
import requests
import sys
import time

# Keys:
# poll_time
# nb_url
# nb_token
# last_log

CONFIG: dict[str, str | int] = {"poll_time": 300, "last_log": -1}
CONFIG_PATH: str = "/etc/netbird_collect.json"
ENDPOINT: str = "/api/events/audit"

def reload_config() -> None:
    global CONFIG
    global CONFIG_PATH
    with open(CONFIG_PATH) as f:
        CONFIG.update(json.load(f))

def update_latest_log(last_log: int) -> None:
    global CONFIG
    global CONFIG_PATH
    reload_config()
    CONFIG["last_log"] = last_log
    with open(CONFIG_PATH, "w+") as f:
        json.dump(CONFIG, f)

def json_log(data: dict) -> None:
    print(json.dumps(data))

def main() -> None:
    global CONFIG
    global CONFIG_PATH
    if len(sys.argv) > 1:
        CONFIG_PATH = sys.argv[1]
    reload_config()

    while True:
        try:
            headers: dict[str, str] = {
                "Authorization": "Token " + CONFIG["nb_token"],
                "Accept": "application/json"
            }
            r = requests.get(CONFIG["nb_url"] + ENDPOINT, headers=headers)
            if r.status_code != 200:
                raise ValueError(f"Unexpected status code querying logs: {r.status_code}")
            events: list[dict] = r.json()
            events.sort(key=lambda x: int(x["id"]))
            max_evt: int = -1
            last_log: int = CONFIG["last_log"]
            for event in events:
                try:
                    evt_id: int = int(event["id"])
                    if evt_id > last_log:
                        json_log(event)
                    if evt_id > max_evt:
                        max_evt = evt_id
                except Exception as e:
                    json_log({"netbird_parse_error": str(e), "log": str(event)})
            if max_evt > last_log:
                update_latest_log(max_evt)
            time.sleep(CONFIG["poll_time"])
        except KeyboardInterrupt:
            break
        except Exception as e:
            json_log({"netbird_collect_error": str(e)})
        reload_config()
        

if __name__ == "__main__":
    main()
