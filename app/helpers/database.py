import pymysql
import sys
import numpy as np
from matplotlib.path import Path


# Returns MySQL database connection
def con_db(host, port, user, passwd, db):
    try:
        con = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)

    except pymysql.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)

    return con

# Make a query based on a given lon/lat

def query_db(con, lon, lat, genre):
  data_array = []

  # Query database
  cur = con.cursor()
  query = get_haversine_query(lon, lat, genre=genre)
  cur.execute(query)

  route_results = []

  raw_results = cur.fetchall()

  if len(raw_results) == 0:
    return None
  results = zip(*raw_results)
  antlons = np.array(results[2], dtype=float)
  antlats = np.array(results[3], dtype=float)
  scss = np.array(results[4])
  cats = np.array(results[5])
  separations = np.array(results[6], dtype=float)
  geodesics = np.array(results[7], dtype=float)
  contour_lons = [np.fromstring(i, sep=',') for i in results[8]]
  contour_lats = [np.fromstring(i, sep=',') for i in results[9]]
  frequencies = np.array(results[10], dtype=float)

  cur.close()
  #con.close()
  return antlons, antlats, scss, cats, separations, geodesics, contour_lons, contour_lats, frequencies

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
  # Try a variation without the great circle
  base_query = """
  SELECT {0} , {1}, b.antlon, b.antlat, b.scs, map.cat, 
  1 AS geod,
  2 AS separation,
  b.lons, b.lats, map.frequency
  FROM contours b
  JOIN contour_cat_map map
  ON b.id = map.contour_id
  WHERE 
      {1} > b.minlat
  AND {1} < b.maxlat
  AND {0} > b.minlon
  AND {0} < b.maxlon
  """
  # If there's a genre query, put that down as well.
  query = base_query.format(lon, lat)
  if genre:
    query += 'AND cat = "'+genre + '" '

  # Limit!
  #query += 'ORDER BY geod LIMIT 1'

  #print query
  return query

def find_radio_stations(con, route, var_dict):
  """ This is the meatiest and most heavy lifting-est method in this project.
  This will loop over each point in the route (node) and determine the radio
  stations (if any) that it can receive.
  """
  antennas_for_each_node = []
  i = -1
  for node in route:
    #print "Considering node:", i, 'of', len(route)
    i+= 1
    result = query_db(con, node[0], node[1], var_dict['genre'])
    # No radio towers exist near this node (based on the rectangular contour
    # approximation:
    if not result: 
      antennas_for_each_node.append(None)
      #print 'XX', i, result
      continue
    #print '>>', i, str(result[:3]).replace('\n', '')

    # There is at least one station whos rectangular coverage includes the node.
    found_in_contour=False
    antlons, antlats, scss, cats, separations, geodesics, contour_lons, contour_lats, frequencies = result
    antenna_dict = {}
    for antenna_num in xrange(len(contour_lons)):
      #print 'antenna_num', antenna_num
      lons = contour_lons[antenna_num]
      lats = contour_lats[antenna_num]
      path = Path(zip(lons, lats))
      #if i > 53 and i < 62:
        #print '\t', antenna_num, 'of', len(contour_lons), 'antennas.',
        #print '\tContour LonLat:', lons[0], lats[0], 'Node LonLat:', node[0], node[1]
      if path.contains_point(node) and scss[antenna_num] != 'NA':
        #print '\tQQQ'
        antennas_for_each_node.append(zip(*result)[antenna_num])
        found_in_contour = True
        #print '\tBreaking!'
        break
    if not found_in_contour:
      #print '\tDid not find found_in_contour'
      antennas_for_each_node.append(None)
    #print str(antennas_for_each_node[-1])[0]
  return antennas_for_each_node

#def in
