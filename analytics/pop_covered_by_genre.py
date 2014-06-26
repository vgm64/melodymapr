from pylab import *
ion()
import mpl_defaults
mpl_defaults.plot_for_talks_smaller()
from matplotlib.path import Path
import pymysql
import pandas as pd
import cPickle as pickle
execfile("/Users/mwoods/Work/OldJobs/JobSearch/Pre-Insight/plotUSA.py")

def get_contours(where = ""):
  print "Getting contours with conditional:", where
  con = pymysql.connect(host='localhost', user='mwoods', database='insight', port=3306)
  results = pd.read_sql('SELECT b.antlon, b.antlat, b.scs, map.cat, b.lons, b.lats, map.frequency   FROM contours b   JOIN contour_cat_map map   ON b.id = map.contour_id {0} ORDER BY b.size DESC'.format(where), con)
  results['lats'] = results['lats'].map(eval)
  results['lons'] = results['lons'].map(eval)

  return results
  con.close()

def plot_contours(data):
  for irow in xrange(len(data)):
    plot( data['lons'][irow], data['lats'][irow])


def draw_heatmap(x,y,X,Y,cover, blot=True, interpolation='nearest', log=False):
  cover = cover.copy()
  xmin = np.min(x)
  xmax = np.max(x)
  ymin = np.min(y)
  ymax = np.max(y)

  extent = [xmin, xmax, ymin, ymax]

  if blot:
    cover[cover == 0] = nan
  if log and not blot:
    print log10(cover).min()
    cover[cover == 0] = cover[cover > 0].min()
  if log:
    norm = matplotlib.colors.LogNorm()
  else:
    norm = matplotlib.colors.Normalize()
  print cover.shape
  im = imshow(cover, norm=norm, extent=extent, origin='lower', aspect='auto', interpolation=interpolation)
  del cover
  return im, extent

def compute_grid(x, y, X, Y, xs, ys, data):
  print 'Computing grid with', len(x)*len(y), 'points and', len(data), 'contours.'
  grid = array([xs, ys]).T
  covered = zeros_like(xs)
  for icontour in xrange(len(data)):
    la, lo = data[['lons', 'lats']].values[icontour]
    vertices = array([la, lo]).T
    p = Path(vertices)
    covered += p.contains_points(grid)
  return covered

def smart_plotUSA(c):
  print "Drawing USA"
  xl = xlim()
  yl = ylim()
  plotUSA(c)
  xlim(xl[0], xl[1])
  ylim(yl[0], yl[1])

# ========== Population info ==========

def read_pop_file():
  # csv of population by county
  data = pd.read_csv('Population_By_County_in_U.S._50_States_2010-12.csv')
  data['lat'] = data['Location 1'].map(lambda x: eval(x)[0])
  data['lon'] = data['Location 1'].map(lambda x: eval(x)[1])
  return data

def smear_pop(xs, ys, binx, biny, popsdf):
  # xs, ys:   grid over which to smear the county populations
  # They are ravelled!
  
  print "Smearing the population"
  bin_populations = zeros_like(xs)

  lats, lons, pops = popsdf['lat'], popsdf['lon'], popsdf['Total population 18 and over']
  print "Bin size is:", binx, biny

  #for lon, lat, pop in zip(lons, lats, pops):
    #counties_contained = lon < upper_x
    #counties_contained = counties_contained & (lon > lower_x)
    #counties_contained = counties_contained & (lat < upper_y)
    #counties_contained = counties_contained & (lat > lower_y)
    #print '--->'
    #print counties_contained.shape
    #print bin_populations.shape
    #bin_populations += pop * counties_contained

  binx = xs[1] - xs[0]
  biny = ys[1] - ys[0]
  lower_x = xs - binx/2.
  lower_y = ys - biny/2.
  upper_x = xs + binx/2.
  upper_y = ys + biny/2.
  bin_populations = zeros_like(xs)
  for i in xrange(len(xs)):
    for lon, lat, pop in zip(lons, lats, pops):
      if lon < upper_x[i] and lon > lower_x[i] and lat < upper_y[i] and lat > lower_y[i]:
        print lon, upper_x[i]
        bin_populations[i] += pop
  return bin_populations

if __name__ == '__main__':
  #bone()
  autumn()
  figure(figsize=(12,8))
  # I Have them stored!
  #all_data = get_contours()
  #country = get_contours("WHERE cat='Country'")
  
  print "Making heatmap"
  x = arange(-130, -65, 0.5)
  y = arange(20, 55, 0.5)
  X,Y = meshgrid(x,y)
  xs, ys = X.ravel(), Y.ravel()
  # I have them stored!
  #covered = compute_grid(x,y,X,Y,xs, ys, all_data)
  #covered_country = compute_grid(x,y,X,Y,xs, ys, country)
  covered = pickle.load(open("covered.pkl"))
  covered_country = pickle.load(open("covered_country.pkl"))
  covered = covered.reshape(X.shape)
  covered_country = covered_country.reshape(X.shape)
  print "Drawing contours"
  #plot_contours(all_data)
  #show()
  print "Drawing heatmap"
  figure(figsize=(12,8))
  draw_heatmap(x,y,X,Y,covered, log=True, interpolation='bicubic')
  print "Drawing USA"
  xl = xlim()
  yl = ylim()
  plotUSA((.5, .5, .9))
  xlim(xl[0], xl[1])
  ylim(yl[0], yl[1])
  title("All Radio Station Coverage")
  print "Done"

  figure(figsize=(12,8))
  draw_heatmap(x,y,X,Y,covered_country/covered, log=True, interpolation='bicubic')
  print "Drawing USA"
  xl = xlim()
  yl = ylim()
  smart_plotUSA((.5, .5, .9))
  xlim(xl[0], xl[1])
  ylim(yl[0], yl[1])
  title("All Radio Station Coverage")
  print "Done"

  pops = read_pop_file()
  binx = x[1] - x[0]
  biny = y[1] - y[0]
  smear_pop(xs, ys, binx, biny, pops)
