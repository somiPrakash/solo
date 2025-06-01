import machine
import ujson
from time import sleep


def parse_lat_lon(lat, lat_dir, lon, lon_dir):
    def convert(coord, direction):
        if not coord:
            return None
        degrees = int(coord[:2]) if len(coord.split('.')[0]) <= 4 else int(coord[:3])
        minutes = float(coord[2:]) if degrees < 100 else float(coord[3:])
        decimal = degrees + minutes / 60
        if direction in ['S', 'W']:
            decimal *= -1
        return round(decimal, 7)
    return convert(lat, lat_dir), convert(lon, lon_dir)

def parse_nmea(sentence):
    fields = sentence.split(',')

    if sentence.startswith('$GNRMC') and len(fields) >= 12:
        return {
            'type': 'RMC',
            'utc_time': fields[1],
            'satellite_positioning_status': fields[2],
            'raw_latitude': fields[3],
            'raw_lat_dir': fields[4],
            'raw_longitude': fields[5],
            'raw_lon_dir': fields[6],
            'ground_speed_knots': float(fields[7]) if fields[7] else None,
            'ground_heading': float(fields[8]) if fields[8] else None,
            'date': fields[9],
            'magnetic_declination': fields[10] if len(fields) > 10 else None,
            'magnetic_declination_direction': fields[11] if len(fields) > 11 else None,
            'positioning_mode': fields[12] if len(fields) > 12 else None,
            'nav_status': fields[13].split('*')[0] if len(fields) > 13 else None
        }

    elif sentence.startswith('$GNGGA') and len(fields) >= 15:
        return {
            'type': 'GGA',
            'utc_time': fields[1],
            'raw_latitude': fields[2],
            'raw_lat_dir': fields[3],
            'raw_longitude': fields[4],
            'raw_lon_dir': fields[5],
            'latitude': parse_lat_lon(fields[2], fields[3], fields[4], fields[5])[0],
            'longitude': parse_lat_lon(fields[2], fields[3], fields[4], fields[5])[1],
            'fix_quality': int(fields[6]) if fields[6].isdigit() else None,
            'num_satellites': int(fields[7]) if fields[7].isdigit() else None,
            'hdop': float(fields[8]) if fields[8] else None,
            'altitude_m': float(fields[9]) if fields[9] else None,
            'altitude_units': fields[10],
            'geoid_sep': float(fields[11]) if fields[11] else None,
            'geoid_sep_units': fields[12],
            'dgps_age': fields[13],
            'dgps_station_id': fields[14].split('*')[0] if '*' in fields[14] else fields[14]
        }

    return None


# Main loop
def get_nmea_data(gps_serial):
    
    if gps_serial.any():
        line = gps_serial.readline()
        if line:
            try:
                line = line.decode('utf-8').strip()
                parsed = parse_nmea(line)
                return parsed
            except Exception as e:
                # print("Count : {} | Null".format(count))
                return None
    
    sleep(0.1)
    
    
if __name__ == "__main__":
    count = 0
    gps_serial = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))
    while(1):
        
        data = get_nmea_data(gps_serial)
        if(data):
            print(data)
        count += 1
        sleep(0.5)
    

