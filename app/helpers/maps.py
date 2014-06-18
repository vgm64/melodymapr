import urllib2
import json
from app.helpers.secrets import get_API_key
from app.helpers.gmap_encoder import decode
import itertools

def geocode(search_term):
  API_KEY = get_API_key()
  base_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}"
  query = base_url.format( urllib2.quote(search_term), API_KEY)
  resp = urllib2.urlopen(query)
  data = json.load(resp)
  
  formatted_address = data['results'][0]['formatted_address'] 
  geom = data['results'][0]['geometry']
  lat, lon = geom['location']['lat'], geom['location']['lng']
  return lat, lon, formatted_address, data

def get_directions(origin, destination):
  API_KEY = get_API_key()

  base_url = "https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&key={}"
  query = base_url.format(urllib2.quote(origin), urllib2.quote(destination), API_KEY)
  resp = urllib2.urlopen(query)
  data = json.load(resp)
  return data
  #encoded_route_data = data['routes'][0]['overview_polyline']['points']
  #route_data = decode(encoded_route_data)
  #return route_data

def get_route_from_directions(directions):
  """ Take a JSON object and return a tuple of lon/lats """
  encoded_route_data = directions['routes'][0]['overview_polyline']['points']
  route_data = decode(encoded_route_data)
  #print '################'
  #print route_data[0:3]

  #print type(route_data)
  steps = directions['routes'][0]['legs'][0]['steps']
  step_polylines = [step['polyline']['points'] for step in steps]
  #print "\n-->".join(step_polylines)
  decoded_route_data = map(decode, step_polylines)
  #print decoded_route_data
  route_data = itertools.chain.from_iterable(decoded_route_data)
  #for d in decoded_route_data:
    #print '\n==>', d
  #print "\n==>".join(decoded_route_data)
  #route_data = []
  #map(route_data.extend, decoded_route_data)
  route_data = list(route_data)
  desired_num_nodes = 100
  if desired_num_nodes > len(route_data):
    return route_data

  resampled_route_data = route_data[::(len(route_data) // desired_num_nodes)]
  print '--> Down sampled from', len(route_data), 'to', len(resampled_route_data), 'nodes'
  return resampled_route_data

def leg_to_js(route, settings = {}):
  """ I need to take input like:
      (21.291982, -157.821856),
      (-18.142599, 178.431),
      (23.982, -137.21856)
  and turn that into:
      var path1 = [new google.maps.LatLng(21.291982, -157.821856),
      new google.maps.LatLng(-18.142599, 178.431),
      new google.maps.LatLng(23.982, -137.21856)]

      var line1 = new google.maps.Polyline({
          path: path1,
          strokeColor: '#ff0000',
          strokeOpacity: 1.0,
          strokeWeight: 2
      });
  """

  make_LatLng_str = lambda x: 'new google.maps.LatLng'+str(x[::-1])
  path_strings = map(make_LatLng_str, route)
  path_var = ', '.join(path_strings)
  path_var = 'var path = [ {0} ]; \n'.format(path_var)
  color = settings.get('strokeColor', '#ff0000')
  opacity = settings.get('stokeOpacity', 1.0)
  weight = settings.get('stokeWeight', 10)
  line_var = """var line = new google.maps.Polyline({{
  path: path,
  strokeColor: '{0}',
  strokeOpacity: {1},
  strokeWeight: {2}
}});
// Add a new marker at the new plotted point on the polyline.
var infoWindow = new google.maps.InfoWindow();
for (i = 0; i < path.length; i++) {{ 
    var marker = new google.maps.Marker({{
        position: path[i],
        map: map,
        title: String(path[i])
    }});
    google.maps.event.addListener(marker, 'click', (function(marker) {{
      return function() {{
        infoWindow.setContent(marker.getTitle());
        infoWindow.open(map, marker);
      }}
    }})(marker));
}};
line.setMap(map);
  """.format(color, opacity, weight)

  return path_var + line_var


def contour_to_js(contour, settings = {}):
  """ I need to take input like:
      (21.291982, -157.821856),
      (-18.142599, 178.431),
      (23.982, -137.21856)
  and turn that into:
      var path1 = [new google.maps.LatLng(21.291982, -157.821856),
      new google.maps.LatLng(-18.142599, 178.431),
      new google.maps.LatLng(23.982, -137.21856)]

      var line1 = new google.maps.Polyline({
          path: path1,
          strokeColor: '#ff0000',
          strokeOpacity: 1.0,
          strokeWeight: 2
      });
  """

  make_LatLng_str = lambda x: 'new google.maps.LatLng'+str(x[::-1])
  path_strings = map(make_LatLng_str, contour)
  path_var = ', '.join(path_strings)
  path_var = 'var path = [ {0} ]; \n'.format(path_var)
  color = settings.get('strokeColor', '#ff0000')
  opacity = settings.get('stokeOpacity', 1.0)
  weight = settings.get('stokeWeight', 10)
  line_var = """var line = new google.maps.Polyline({{
  path: path,
  strokeColor: '{0}',
  strokeOpacity: {1},
  strokeWeight: {2}
}});
line.setMap(map);
  """.format(color, opacity, weight)

  return path_var + line_var

def get_bounding_box(directions):
  bounding_NE = directions['routes'][0]['bounds']['northeast']
  bounding_SW = directions['routes'][0]['bounds']['southwest']
  NE_lat, NE_lon = bounding_NE['lat'], bounding_NE['lng']
  SW_lat, SW_lon = bounding_SW['lat'], bounding_SW['lng']
  bbox = 'var bbox = new google.maps.LatLngBounds( ' + \
      'new google.maps.LatLng( {0}, {1} ), ' + \
      'new google.maps.LatLng( {2}, {3} )); '
  bbox = bbox.format(SW_lat, SW_lon, NE_lat, NE_lon)
  return bbox


def consolidate_tunes(route, route_tunes):
  num_nodes = len(route)
  legs = []
  current_leg = None
  first_node = route[0]
  first_tune = route_tunes[0]
  if first_tune == None:
    current_leg = {'scs':'NA', 'nodes':[], 'empty':True, 'contour':None}
  else:
    contour = zip(*first_tune[6:8])
    current_leg = {'scs':first_tune[2], 'nodes':[], 'empty':False, 'contour':contour}


  # Loop over all each node. Add to group.
  for inode in xrange(1,num_nodes):
    print '#>> ', inode, 'LatLng', route[inode],
    if route_tunes[inode]:
      print route_tunes[inode][:4]
    else:
      print route_tunes[inode]
    # Remember, some nodes don't have radio reception (set to None):
    if not route_tunes[inode]:
      # This has the same station as the previous station
      if current_leg['empty']:
        current_leg['nodes'].append(route[inode])
      # This has a new station name.
      else:
        current_leg['nodes'].append(route[inode])
        legs.append(current_leg)
        current_leg = {'scs':'NA', 'nodes':[], 'empty':True, 'contour':None}
    # But if they do have radio reception:
    else:
      # This has the same station as the previous station
      if current_leg['scs'] == route_tunes[inode][2]:
        current_leg['nodes'].append(route[inode])
      # This has a new station name.
      else:
        current_leg['nodes'].append(route[inode])
        legs.append(current_leg)
        contour = zip(*route_tunes[inode][6:8])
        current_leg = {'scs':route_tunes[inode][2], 'nodes':[], 'empty':False, 'contour':contour}
    legs.append(current_leg)

  # This is just to print stuff out!
  num_nodes = 0
  num_legs = 0
  for i, node in enumerate(legs):
    #print i, len(legs), node['scs'], node['nodes'][0], node['nodes'][-1]
    if num_nodes == 0:
      current_node = node
    if node['scs'] == current_node['scs']:
      num_nodes += 1
    else:
      print "--> Leg %d: %s nodes and has call sign %s" % (num_legs, num_nodes, current_node['scs'])
      num_legs += 1
      current_node = node
      num_nodes = 1
  print "--> Leg %d: %s nodes and has call sign %s" % (num_legs, num_nodes, current_node['scs'])
  print route[::-1][:10]
  print legs[-1]['nodes']
  return legs

def render_legs(grouped_nodes):
  """ The argument of this method is a dictionary that looks like:
  'scs':    Short call sign e.g. KITS
  'nodes':  A list of the LonLats
  'empty':  A boolean to indicate no radio station available.
  """
  full_js_string = ''
  #colors = ['#ff0000', '#09CA32', '#00ff00', '#03C11D']
  colors = ['#2E16B1',  '#640CAB',  '#FFF500',  '#FFCB00']
  # http://colorschemedesigner.com/#
  colors = ['#00AB6F', '#0C5AA6', '#FF9700', '#FF5300']
  #colors = ['#444444']

  for group in grouped_nodes:
    leg = group['nodes']
    #print '--#', len(leg)
    if group['scs'] == 'NA':
      color = '#0C090A'
    else:
      color= colors[0]
      colors = colors[1:] + [colors[0]]
    full_js_string += leg_to_js(leg, {'strokeColor':color})
  return full_js_string

def render_contours(grouped_nodes):
  """ The argument of this method is a dictionary that looks like:
  #'scs':    Short call sign e.g. KITS
  #'nodes':  A list of the LonLats
  #'empty':  A boolean to indicate no radio station available.
  """
  full_js_string = ''
  colors = ['#ff0000', '#00ffff', '#00ff00', '#0f0f00']
  colors = ['#00AB6F', '#0C5AA6', '#FF9700', '#FF5300']
  for group in grouped_nodes:
    leg = group['contour']
    #print '--#', len(leg)
    colors = colors[1:] + [colors[0]]
    if not leg:
      continue
    full_js_string += contour_to_js(leg, {'strokeColor':colors[0]})
  return full_js_string

