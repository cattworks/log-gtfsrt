## Overview

This repository is intended to generalize the process of logging GTFS-Realtime data (Alerts, Vehicle Positions, and Trip Updates).  Desired GTFS feed information is added to a configuration file, and then two command line python scripts (```src/download_gtfs_schedule.py``` and ```src/download_gtfs_realtime.py```) are used to parse the config file and download both Schedule and Realtime data from the included feeds into an appropriate folder structure. 

In a typical setup, runner scripts (```runner_gtfs_schedule.sh``` and ```runner_gtfs_realtime.sh```) are used to call the command line python scripts.  These shell scripts are executed as cron jobs on a server -- for example,  with GFTS-schedule files downloaded once a day and GTFS-realtime data downloaded every 30 seconds. 

```
# Download GTFS-Schedule every day at 12:01 AM
0 1 * * * /path/to/runner_gtfs_schedule.sh

# Download GTFS-Realtime every 30 seconds
* * * * * /path/to/download_sched.sh
* * * * * sleep 30; /path/to/download_rt.sh
```

## Explanation
To use this repository, do the following: 

* Create ```config.json``` (following format for feeds shown in ```demo/config_example.json```)  
* If any RT feeds require an API Key, create a ```.env``` file at the root of the repository and specify using AGENCY_LABEL=API_KEY (following example shown in ```demo/.env.example```).  In the configuration file (```config.json```), make sure the corresponding feed specifies the appropriate label to look for (i.e., "apikey-label") and what this parameter should be called in the corresponding HTTP header ("auth-header").  For example, if the ```.env``` file specifies ```WMATA_KEY=XYZ123``` and WAMATA's API expects the API Key to be specified using "api_key" parameter in the header, an example feed in the config file could be:

```
{
    "url": "https://api.wmata.com/gtfs/rail-gtfsrt-alerts.pb",
    "auth-header": "api_key",
    "apikey-label": "WMATA_KEY"
}  
```   

## TODO
Add logging for cases where error is encountered.  Right now RT data is processed in parallel using multiprocessing so logging strategy requires a bit more thought.
* 