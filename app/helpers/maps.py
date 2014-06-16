import urllib2
import json
from app.helpers.secrets import get_API_key
from app.helpers.gmap_encoder import decode

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

  encoded_route_data = data['routes'][0]['overview_polyline']['points']
  route_data = decode(encoded_route_data)

  return route_data

def get_route_from_directions(directions):
  """ Take a JSON object and return a tuple of lon/lats """
  encoded_route_data = directions['routes'][0]['overview_polyline']['points']
  route_data = decode(encoded_route_data)
  return route_data

def leg_to_js(route, settings):
  """ I need to take input like:
      (21.291982, -157.821856),
      (-18.142599, 178.431),
      (23.982, -137.21856)
  and turn that into:
      var path = [new google.maps.LatLng(21.291982, -157.821856),
      new google.maps.LatLng(-18.142599, 178.431),
      new google.maps.LatLng(23.982, -137.21856)]

      var line = new google.maps.Polyline({
          path: path,
          strokeColor: '#ff0000',
          strokeOpacity: 1.0,
          strokeWeight: 2
      });
  """

  make_LatLng_str = lambda x: 'new google.maps.LatLng'+str(x[::-1])
  path_strings = map(make_LatLng_str, route)
  path_var = ', '.join(path_strings)
  path_var = 'var path = [' + path_var + '];' + '\n'
  print path_var

  color = settings.get('strokeColor', '#ff0000')
  opacity = settings.get('stokeOpacity', 1.0)
  weight = settings.get('stokeWeight', 2)
  print color, opacity, weight

  #colo

  #path_var = 'var path = [{}]'
    #var path = [{{settings['test_js']}}];

  line_var = """var line = new google.maps.Polyline({{
  path: path,
  strokeColor: '{0}',
  strokeOpacity: {1},
  strokeWeight: {2}
}});
line.setMap(map)
  """.format(color, opacity, weight)

  return path_var + line_var
