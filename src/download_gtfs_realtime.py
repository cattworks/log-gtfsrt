import argparse
import requests
import datetime
import pandas as pd
import pytz
import os
import json
import sys
import multiprocessing
from multiprocessing import Pool
from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import ParseDict
from dotenv import load_dotenv

## Assumes file named .env
load_dotenv()

def main(out_dir, config_json):

    # Load config file as dictionary
    with open(config_json, "r") as file:
        config = json.load(file)

    l_data = []

    # Iterate over each agency in the config file
    for agency_info in config:
        agency = agency_info['agency']
        local_tz = agency_info['tz-local']
        
        # Get today's date in local time
        now = datetime.datetime.now(tz=pytz.timezone(local_tz))
        datestr = now.strftime('%Y%m%d')

        # Establish final output directory for agency
        outdir_final = os.path.join(out_dir, agency)
        if not os.path.exists(outdir_final):
            os.makedirs(outdir_final)

        if agency_info.get('gtfs-rt'):
            # Note: any rt feeds may have single entity type or combined
            for rt_feed in agency_info['gtfs-rt']:
                url = rt_feed['url']
                auth_header = rt_feed.get('auth-header')
                if auth_header:  # need to look up API key in dot file 
                    apikey_label = rt_feed['apikey-label']
                    api_key = os.getenv(apikey_label)
                    headers = {auth_header: api_key}
                else:
                    headers=None

                # Prep data from this agency feed to be processed in parallel
                data = (url, headers,agency, datestr, outdir_final)
                l_data.append(data)

        # ---
        ## 
        with Pool(processes=multiprocessing.cpu_count()) as pool:
            # issue tasks to the process pool
            pool.imap_unordered(_process_single_agency_feed, l_data)
            # shutdown the process pool
            pool.close()
            # wait for all issued task to complete
            pool.join()
                


def _process_single_agency_feed(data_tup):
    url, headers, agency, datestr, outdir_final = data_tup
    response = requests.get(url, headers=headers)
    
    ##----------------------
    ## Trip Updates
    ## ----------------------

    df_updates = _gtfsrt_df(response.content, entity_type='trip_updates')
    if df_updates is not None:
        outfile_updates = os.path.join(outdir_final, '{}-tripupdates-{}.csv.gz'.format(agency, datestr))   
        _write_csv_gzip(df_updates, outfile_updates)


    ##----------------------
    ## VEHICLE POSITIONS
    ## ----------------------            
    df_vehpos = _gtfsrt_df(response.content, entity_type='vehicle_positions')
    if df_vehpos is not None:
        outfile_vehpos = os.path.join(outdir_final, '{}-vehpos-{}.csv.gz'.format(agency, datestr))   
        _write_csv_gzip(df_vehpos, outfile_vehpos)

    ##----------------------
    ## Alerts
    ## ----------------------
    df_alert = _gtfsrt_df(response.content, entity_type='alerts')
    if df_alert is not None:
        outfile_alert = os.path.join(outdir_final, '{}-alert-{}.csv.gz'.format(agency, datestr))   
        _write_csv_gzip(df_alert, outfile_alert)


def _gtfsrt_df(bytes, entity_type):

    """bytes: raw GTFS protobuf
       entity_type: specify which entity type to extract ['vehicle_positions', 'alerts', 'trip_updates']
                    (if protobuf contains multiple entity types, only the selected one is extracted)
    """

    if entity_type not in ['vehicle_positions', 'alerts', 'trip_updates']:
            sys.exit('Invalid entity_type')

    try:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(bytes)
        # preserving_proto_field_name=True preserves snake case, and is assumed later
        feed_dict = MessageToDict(feed,preserving_proto_field_name=True, always_print_fields_with_no_presence=True)

        
        if entity_type == 'vehicle_positions':
            entities = [e for e in feed_dict.get("entity") if 'vehicle' in e]
        elif entity_type == 'alerts':
            entities = [e for e in feed_dict.get("entity") if 'alert' in e]
        elif entity_type == 'trip_updates':
            entities = [e for e in feed_dict.get("entity") if 'trip_update' in e]

        if len(entities) > 0:
            df = pd.json_normalize(entities, sep='.')
            df.insert(0, 'header.gtfs_realtime_version', feed_dict['header']['gtfs_realtime_version'])
            df.insert(1, 'header.incrementality', feed_dict['header']['incrementality'])
            df.insert(2, 'header.timestamp', feed_dict['header']['timestamp'])
            df = df.sort_values('header.timestamp').reset_index(drop=True)
        else:
            df = None
        return df
    except:
        return None
    

def _write_csv_gzip(df, outfile):
    if not os.path.exists(outfile):
        df.to_csv(outfile, index=False, header=True, mode='w', compression={'method': 'gzip', 'compresslevel':1})
    else: # if it already exists
        # Append to existing file and don't use header
        columns_ordered = pd.read_csv(outfile, nrows=0).columns.tolist()
        df[columns_ordered].to_csv(outfile, index=False, header=False, mode='a', compression={'method': 'gzip', 'compresslevel':1})


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir", help="Output directory")
    parser.add_argument("config_json", help="JSON config file with feed info")
    args = parser.parse_args()

    main(args.out_dir, args.config_json)
