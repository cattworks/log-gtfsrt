import argparse
import requests
import datetime
import pytz
import os
import json
from dotenv import load_dotenv

## Assumes file named .env
load_dotenv()

def main(out_dir, config_json):

    # Load config file as dictionary
    with open(config_json, "r") as file:
        config = json.load(file)

    # Iterate over each agency in the config file
    for agency_info in config:
        agency = agency_info['agency']
        local_tz = agency_info['tz-local']
        url = agency_info['gtfs-schedule']['url']

        # Get today's date in local time
        now = datetime.datetime.now(tz=pytz.timezone(local_tz))
        datestr = now.strftime('%Y%m%d')

        # Establish final output directory for date
        outdir_final = os.path.join(out_dir, datestr)
        if not os.path.exists(outdir_final):
            os.makedirs(outdir_final)

        # Download to output file
        outfile = os.path.join(outdir_final, '{}-gtfs-{}.zip'.format(agency, datestr))
        r = requests.get(url, headers=None)
        with open(outfile, "wb") as f:
            f.write(r.content)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir", help="Output directory")
    parser.add_argument("config_json", help="JSON config file with feed info")
    args = parser.parse_args()

    main(args.out_dir, args.config_json)
