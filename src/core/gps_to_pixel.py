import json
import math
from math import atan2, sqrt
from src.display.ili934xnew import color565
from src.core.kalman_filter import KalmanFilter


def draw_circle(xpos0, ypos0, rad,display, col=color565(255, 255, 255)):
    x = rad - 1
    y = 0
    dx = 1
    dy = 1
    err = dx - (rad << 1)
    while x >= y:
        display.pixel(xpos0 + x, ypos0 + y, col)
        display.pixel(xpos0 + y, ypos0 + x, col)
        display.pixel(xpos0 - y, ypos0 + x, col)
        display.pixel(xpos0 - x, ypos0 + y, col)
        display.pixel(xpos0 - x, ypos0 - y, col)
        display.pixel(xpos0 - y, ypos0 - x, col)
        display.pixel(xpos0 + y, ypos0 - x, col)
        display.pixel(xpos0 + x, ypos0 - y, col)
        if err <= 0:
            y += 1
            err += dy
            dy += 2
        if err > 0:
            x -= 1
            dx += 2
            err += dx - (rad << 1)
            
# Bresenham’s Line Algorithm         
def draw_line(x0, y0, x1, y1,display, col=color565(255, 255, 0)):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0

    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1

    if dx > dy:
        err = dx / 2.0
        while x != x1:
            display.pixel(x, y, col)
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            display.pixel(x, y, col)
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    display.pixel(x, y, col)  # Draw final pixel


def distance_points(points):
    R = 6371000  # Earth radius in meters
    
    for i in range(0,len(points)-1):
        lat1,lon1 = points[i]
        lat2,lon2 = points[i+1]
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        d = R * c
        
        return d

def nmea_to_decimal(nmea_str):
    nmea = float(nmea_str)
    degrees = int(nmea // 100)
    minutes = nmea - degrees * 100
    return degrees + minutes / 60

def load_gps_points(file_path):
    points = []
    count = 0
    with open(file_path, 'r') as file:
        for line in file:
            json_data = json.loads(line)
            print(json_data)
            try:
                lat_in_decimal = nmea_to_decimal(json_data["raw_latitude"])
                lon_in_decimal = nmea_to_decimal(json_data["raw_longitude"])
                utc_time = json_data["utc_time"]
                ground_heading_in_degrees = float(json_data["ground_heading"])
                magnetic_heading_in_degrees = float(json_data["magnetic_heading_in_degrees"])
                ground_speed_knots = json_data["ground_speed_knots"]
                points.append((lat_in_decimal, lon_in_decimal,utc_time,ground_heading_in_degrees,magnetic_heading_in_degrees,ground_speed_knots))

            except ValueError:
                continue  # skip invalid lines
    return points

def gps_to_screen_coords(points, width, height):
    # Get min and max of lat/lon for scaling
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    min_lat = min(lats)
    max_lat = max(lats)
    min_lon = min(lons)
    max_lon = max(lons)

    # Avoid divide-by-zero in case all points are same
    lat_range = max_lat - min_lat if max_lat != min_lat else 1
    lon_range = max_lon - min_lon if max_lon != min_lon else 1

    screen_coords = []
    for lat, lon in points:
        # Normalize to 0 - width/height
        x = int((lon - min_lon) / lon_range * (width - 1))
        y = int((lat - min_lat) / lat_range * (height - 1))
        y = height - 1 - y  # Flip vertically if needed
        screen_coords.append((x, y))
    return screen_coords



def draw_gps_track(file_path, display,color, width=240, height=320):
    gps_points_with_additional_data = load_gps_points(file_path)
    _draw_magnetic_heading_path_using_saved_data(gps_points_with_additional_data,display,color)
    
    gps_points = []
    for point in gps_points_with_additional_data:
        gps_points.append((point[0],point[1]))
    if(len(gps_points)== 0):
        print("ERROR - No points yet saved in flash. Exiting")
        return
    
    screen_points = gps_to_screen_coords(gps_points, width, height)
    for i in range(len(screen_points) - 1):
        x0, y0 = screen_points[i]
        x1, y1 = screen_points[i+1]
        draw_line(x0, y0, x1, y1,display, col=color565(0, 255, 255))
    
    total_distance_covered = 0
    for i in range(0,len(gps_points)-2):
        print(gps_points[i])
        total_distance_covered += distance_points([gps_points[i], gps_points[i+1]])

    for x, y in screen_points:
        draw_circle(x, y, 2,display, color565(0, 255, 0))
        
    
    draw_line(0, 160, 240, 160,display, col=color565(0, 255, 0))
    draw_line(120, 0, 120, 320,display, col=color565(0, 255, 0))
    
#     display.set_pos(0,50)
#     display.print("Total distance covered : {} m ".format(total_distance_covered))
    
    
def draw_osm_file_points(gps_points,display,color, width=240, height=320):
    if(len(gps_points) <= 2):
        print("ERROR - Less than 3 points , cannot form a polygon")
        return
    screen_points = gps_to_screen_coords(gps_points, width, height)
    for x, y in screen_points:
        draw_circle(x, y, 1,display, color565(0, 255, 0))
        

def _draw_magnetic_heading_path_using_saved_data(gps_points_with_additional_data,display,color):
    # Arrow end point (length L in pixels)
    L = 20
    magnetic_heading_correction = 165
#     magnetic_heading_correction = 0
    SCR_WIDTH = const(320)
    SCR_HEIGHT = const(240)
    CENTER_Y = int(SCR_WIDTH/2)
    CENTER_X = int(SCR_HEIGHT/2)
    
    start_x = 240
    start_y = 280
    try:
        for point in gps_points_with_additional_data:
            gps_acquired_ground_heading = point[3]
            magnetic_heading = point[4]
#             magnetic_heading = gps_acquired_ground_heading
            end_x = int(start_x + L * math.sin(math.radians(magnetic_heading + magnetic_heading_correction)))
            end_y = int(start_y - L * math.cos(math.radians(magnetic_heading + magnetic_heading_correction)))  # minus because y grows down on screens
            
            print(end_x,end_y)
            draw_line(start_x, start_y, end_x, end_y,display, col=color)
            start_x = end_x
            start_y = end_y
    except Exception as e :
        print(e)
        
    print("Completed magnetic heading drawing")

             
def get_points_from_osm_file(osm_file_path,display,color):
    nodes = []
    polygon_list = []
    try:
        with open(osm_file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.startswith("<bounds") and line.endswith("/>"):
                    parts = line.split()
                    for part in parts:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            value = value.strip('"').strip('/>')
                            if(key == "minlat"):
                                minlat = nmea_to_decimal(value.replace('"',""))
                            elif(key == "minlon" ):
                                minlon = nmea_to_decimal(value.replace('"',""))
                            elif(key == "maxlat"):
                                maxlat = nmea_to_decimal(value.replace('"',""))
                            elif(key == "maxlon"):
                                maxlon = nmea_to_decimal(value.replace('"',""))
                                
                elif line.startswith("<node") and line.endswith("/>"):
                    node = {}
                    parts = line.split()
                    for part in parts:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            value = value.strip('"').strip('/>')
                            if(key == "lat"):
                                lat = nmea_to_decimal(value.replace('"',""))
                            elif(key == "lon" ):
                                lon = nmea_to_decimal(value.replace('"',""))
                            elif(key == "id"):
                                id = int(value)
                    if(len(nodes) < 256):
                        nodes.append((lat,lon))
                    
                    if(len(nodes) == 256 ):
                        print("More than 256 points . Discarding node ")
                        nodes = []
                
                    
                elif line.startswith("</node>"):
                    if(len(nodes) >= 0):
                        print(len(nodes))
                        nodes.append((minlat,minlon))
                        nodes.append((maxlat,maxlon))
                        draw_osm_file_points(nodes,display,color, width=240, height=320)
                        
                    nodes = []
                              
    except Exception as e:
        print(len(nodes))
        print(e)
        
    
    return polygon_list,[(minlat,minlon),(maxlat,maxlon)]
        

        

















