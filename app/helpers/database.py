import pymysql
import sys
import numpy as np


# Returns MySQL database connection
def con_db(host, port, user, passwd, db):
    try:
        con = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)

    except pymysql.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)

    return con

# Make a query based on a given lon/lat

def query_db(con, dict):
  data_array = []

  # Request args
  origin = dict['origin']
  destination = dict['destination']
  genre = dict['genre']
  route = dict['route']
  userlon = -122.33
  userlat = 37.82

  # Query database
  cur = con.cursor()
  query = get_haversine_query(userlon, userlat, genre=genre)
  cur.execute(query)

  route_results = []
  import time
  start = time.time()
  for lon,lat in route:
    #print lon, lat
    query = get_haversine_query(lon, lat, genre=genre)
    #cur.execute(query)


  #data = cur.fetchall()
  #for country in data:
  #  index = {}

  #  index["id"] = country[0]
  #  index["country"] = country[1]
  #  index["median_age"] = float(json.dumps(country[2]))
  #  index["gdp"] = country[3]
  #  index["edu_index"] = float(json.dumps(country[4]))

  #  data_array.append(index)
  raw_results = cur.fetchall()
  results = zip(*raw_results)
  antlons = np.array(results[2], dtype=float)
  antlats = np.array(results[3], dtype=float)
  scss = np.array(results[4])
  cats = np.array(results[5])
  separations = np.array(results[6], dtype=float)
  geodesics = np.array(results[7], dtype=float)
  contour_lons = [np.fromstring(i, sep=',') for i in results[8]]
  contour_lats = [np.fromstring(i, sep=',') for i in results[9]]

  cur.close()
  con.close()
  #return 'query_db ran'
  return antlons, antlats, scss, cats, separations, geodesics, contour_lons, contour_lats

def get_haversine_query(lon, lat, genre=None):
  """
  r is in units of miles. Maybe not needed?
  """

  base_query = """
  SELECT {0} , {1}, b.antlon, b.antlat, b.scs, map.cat,
  2 * ASIN( 
  SQRT( 
      POW( SIN(   (b.antlat - {1})/360*2*PI()/2  )  , 2)
      + COS({1}/360*2*PI()) 
      * COS(b.antlat/360*2*PI()) 
      * POW(SIN( (b.antlon - {0})/360*2*PI()/2), 2)
    )
  ) * 3956.27 AS geod,
  SQRT(POW(({1} - b.antlat)*75.8, 2) + POW(({0} - b.antlon)*60,2)) AS separation,
  b.lons, b.lats
  FROM contours b
  JOIN contour_cat_map map
  ON b.id = map.contour_id
  WHERE 
      {1} > b.minlat
  AND {1} < b.maxlat
  AND {0} > b.minlon
  AND {0} < b.maxlon
  """
  query = base_query.format(lon, lat)
  if genre:
    query += 'AND genre == '+genre

  return query

def find_radio_stations(con, route, var_dict):
  """ This is the meatiest and most heavy lifting-est method in this project.
  This will loop over each point in the route (node) and determine the radio
  station (if any) that it can receive. If it is the same station as the
  previous node, then group them together.
  """
  results = []
  #for node in route:
    #query_db(con, n
    
  pass
