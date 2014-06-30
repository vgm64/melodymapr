from flask import render_template, request, redirect, url_for, send_from_directory
from app import app, host, port, user, passwd, db
from app.helpers.database import con_db, query_db, find_radio_stations
from app.helpers.graphics import render_webfigure
from app.helpers.maps import get_directions, get_route_from_directions
from app.helpers.maps import leg_to_js, consolidate_tunes, render_legs, get_bounding_box
from app.helpers.maps import render_contours, assign_colors, render_contours_and_legs
from app.helpers.misc import Timer
import matplotlib.pyplot as plt

# To create a database connection, add the following
# within your view functions:
# con = con_db(host, port, user, passwd, db)

@app.route("/clip")
def clip():
  import os
  return open("app/static/js/test/test.html").read()

@app.route("/visuals")
def visuals():
  return render_template("results.html")


# ROUTING/VIEW FUNCTIONS
@app.route('/')
@app.route('/index')
def index():
  con = con_db(host, port, user, passwd, db)
  cur = con.cursor()

  query = """ SELECT cat, COUNT(cat) FROM fmlist WHERE cat != 'SILENT' GROUP BY cat HAVING COUNT(cat) > 100 ORDER BY cat """
  cur.execute(query)
  results = cur.fetchall()
  genres, counts = zip(*results)

  # Look to see if we failed the previous query
  failed = request.args.get("failed")

  # Renders index.html.
  return render_template('index.html', genres=genres, failed=failed)

@app.route('/out')
def out():
  # WORK!!
  timer = Timer()
  # Create database connection
  con = con_db(host, port, user, passwd, db)

  var_dict = {
    "origin": request.args.get("origin"),
    "destination": request.args.get("destination"),
    "genre": request.args.get("genre", ''),
    "subgenre": request.args.get("subgenre", ''),
    "failed": request.args.get("failed")
  }
  # Fail gracefully
  if not var_dict['origin'] or not var_dict['destination']:
    cur = con.cursor()
    query = """ SELECT cat, COUNT(cat) FROM fmlist WHERE cat != 'SILENT' GROUP BY cat HAVING COUNT(cat) > 100 ORDER BY cat """
    cur.execute(query)
    results = cur.fetchall()
    genres, counts = zip(*results)
    return render_template('index.html', failed=True, genres=genres)
  
  # Get google directions.
  directions = get_directions(var_dict['origin'], var_dict['destination'])
  timer('Finished directions JSON call')
  bbox = get_bounding_box(directions)
  var_dict['bbox'] = bbox

  route, durations = get_route_from_directions(directions)
  timer('Finished getting route from directions')
  print "--> Route has %d nodes" % len(route)
  var_dict['route'] = route

  # HEAVY LIFTING: Split the route into radio stations
  route_tunes = find_radio_stations(con, route, var_dict)
  timer('Finished db query to find antennas')
  print "--> %d nodes don't seem to have a station" % (len([i for i in route_tunes if i is None]))


  # Create colored legs for the route.
  grouped_nodes = consolidate_tunes(route, route_tunes, durations)
  var_dict['legs'] = grouped_nodes
  timer('Finished consolidation of towers')

  # Great. Add colors
  assign_colors(grouped_nodes)

  # Add contours to the map
  javascript_contours = render_contours(grouped_nodes)
  var_dict['contour_js'] = javascript_contours

  # Add the legs to the map. They will be on top of contours
  javascript_legs = render_legs(grouped_nodes)
  var_dict['route_js'] = javascript_legs
  timer('Finished creating js')

  javascript_legs_and_contours = render_contours_and_legs(grouped_nodes)
  var_dict['leg_and_contour_js'] = javascript_legs_and_contours

  # Close db connection.
  con.close()

  #print var_dict.keys()
  #print var_dict['genre']
  # Render the template w/ user input, query result, and figure included!
  return render_template('output.html', settings=var_dict)

@app.route('/contour')
def show_contour():
  # Just show a contour.
  con = con_db(host, port, user, passwd, db)
  cur = con.cursor()

  var_dict = {
    "scs": request.args.get("scs", None),
    "genre": request.args.get("genre", None),
  }

  if var_dict['scs'] and var_dict['genre']:
    where_str = 'WHERE scs = "%s" AND cat = "%s"' % (var_dict['scs'], var_dict['genre'])
  elif var_dict['scs']:
    where_str = 'WHERE scs = "%s" ' % (var_dict['scs'])
  elif var_dict['genre']:
    where_str = 'WHERE cat = "%s"' % (var_dict['genre'])
  else:
    where_str = ''
  base_query = """
  SELECT b.antlon, b.antlat, b.scs, map.cat, b.lons, b.lats
  FROM contours b
  JOIN contour_cat_map map
  ON b.id = map.contour_id
  {0} """
  query = base_query.format( where_str )

  cur.execute(query)

  route_results = []

  raw_results = cur.fetchall()

  import numpy as np
  if len(raw_results) == 0:
    return None
  results = zip(*raw_results)
  antlons = np.array(results[0], dtype=float)
  antlats = np.array(results[1], dtype=float)
  scss = np.array(results[2])
  cats = np.array(results[3])
  contour_lons = [np.fromstring(i, sep=',') for i in results[4]]
  contour_lats = [np.fromstring(i, sep=',') for i in results[5]]  
  contours = zip(contour_lons, contour_lats)

  #print contours[0]
  
  var_dict['scss'] = scss
  var_dict['contours'] = contours

  def good_contour_to_js(lats, lons, scs):
    list_of_LatLngs = []
    for i in xrange(len(lats)):
      list_of_LatLngs.append('new google.maps.LatLng(%f, %f)'%(lats[i], lons[i]))
    LatLngs = ','.join(list_of_LatLngs)
    js = """
    var paths = [{0}];
    var shape = new google.maps.Polygon({{
      paths: paths,
      strokeColor: '#ff0000',
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillColor: '#ff0000',
      fillOpacity: 0.15
    }});
    shape.setMap(map);
    var infoWindow = new google.maps.InfoWindow({{paths: paths}});
    google.maps.event.addListener(shape, 'click', (function(shape) {{
      return function() {{
        infoWindow.setContent('{2}');
        infoWindow.setPosition( this.paths[0] );
        infoWindow.open(map);
      }}
    }})(shape));
    
    """.format( LatLngs, scs, get_wiki_table(scs))
    return js

  def get_wiki_table(page):
    return page
    import urllib2
    from bs4 import BeautifulSoup
    url = 'http://en.wikipedia.org/wiki/'+page
    try:
      bs = BeautifulSoup(urllib2.urlopen(url).read())
    except:
      return page
    table = bs.find('table', attrs={'class':'infobox vcard'})
    return str(table).decode("ascii", "ignore").replace("\n", "").replace("'", "\\'")

  js = []
  for i in xrange(len(contour_lons)):
    js.append( good_contour_to_js(contour_lats[i], contour_lons[i], scss[i]))

  var_dict['js'] = "\n".join(js)

  
  #print len(contours)

  return render_template('contour.html', settings = var_dict)


@app.route('/home')
def home():
    # Renders home.html.
    return render_template('home.html')

@app.route('/slides')
def about():
    # Renders slides.html.
    return render_template('slides.html')

@app.route('/author')
def contact():
    # Renders author.html.
    return render_template('author.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
 
@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
      return send_from_directory(app.static_folder, request.path[1:])
