from datetime import datetime, timezone, timedelta
import zoneinfo
import json


def get_mt_date(utc_string):
    utc_date = datetime.fromisoformat(utc_string.replace('Z', '+00:00'))
    mt_date = utc_date.astimezone(zoneinfo.ZoneInfo('America/Denver'))
    return mt_date.replace(hour=0, minute=0, second=0, microsecond=0)


def process_data(input_file, output_file):
    # Load raw data
    with open(input_file, 'r') as f:
        raw = json.load(f)

    # Get today's date in Mountain Time
    today_mt = datetime.now(zoneinfo.ZoneInfo(
        'America/Denver')).replace(hour=0, minute=0, second=0, microsecond=0)

    # Set the start date to June 2nd, 2024 at 00:00 MT
    start_date = datetime(2024, 6, 2, tzinfo=zoneinfo.ZoneInfo(
        'America/Denver')).replace(hour=0, minute=0, second=0, microsecond=0)

    # Create a map to store the highest AQI data for each site and day
    daily_map = {}

    for d in raw:
        if d.get('AgencyName') == 'Montana DEQ':
            mt_date = get_mt_date(d['UTC'])
            if mt_date >= today_mt or mt_date < start_date:
                continue
            site_key = f"{mt_date.date()}-{d.get('SiteName', 'Unknown')}"
            if 'AQI' in d and 'Category' in d and d.get('Value') != -999 and d.get('AQI') != -999:
                if site_key not in daily_map or d.get('AQI') > daily_map[site_key]['aqi_value']:
                    # Store the date as 12:00 UTC of the same day
                    utc_date = mt_date.replace(
                        hour=12, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
                    daily_map[site_key] = {
                        'date': utc_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                        'aqsid': d.get('IntlAQSCode'),
                        'sitename': d.get('SiteName'),
                        'parameter': d.get('Parameter'),
                        'units': d.get('Unit'),
                        'agency': d.get('AgencyName'),
                        'aqi_value': d.get('AQI'),
                        'aqi_category': d.get('Category'),
                        'latitude': float(d.get('Latitude', 0)),
                        'longitude': float(d.get('Longitude', 0)),
                    }

    # Save the processed data
    with open(output_file, 'w') as f:
        json.dump(list(daily_map.values()), f, indent=2)


if __name__ == "__main__":
    import sys
    input_file = 'aggregate-mt-aqi-data.json'
    output_file = 'aggregate-mt-aqi-highest.json'
    process_data(input_file, output_file)
