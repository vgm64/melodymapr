from pylab import *
ion()
f,ax = subplots(figsize=(10,10))
ax.set_aspect("equal")

data = [
"Religious", 2803,
"Adult Contemporary",  1753,
"Country", 1631,
"Christian", 865,
"News", 777,
"Classic Rock",  570,
"Spanish", 412,
"Oldies",  371,
"Rock",  349,
"Classic Hits",  344,
"Classical", 329,
"Alternative", 315,
"Hip Hop", 312,
"Variety", 302,
"College", 257,
"Sports",  210,
"Adult Hits",  159,
"Gospel",  158,
"Jazz",  139 ]


labels = data[::2]
fracs = data[1::2]

N=8
labels = labels[:N]
fracs = fracs[:N]

fracs = array(fracs)
fracs = 1.*fracs/fracs.sum() * 100.

colors = []
colors = 1-arange(N)*1./N/1.
colors = [(i, 1-i, 1-i) for i in colors]
# From http://colorbrewer2.org/
colors = array([241,238,246,
    189,201,225,
    116,169,207,
    43,140,190,
    4,90,141])
colors = colors/255.
colors = colors.reshape(5, 3)
#for i in xrange(N):
  #colors.append( (.5./N * i, 0, 0))
  #colors.append( (1-i*.1, 1-i*.1, )) 
#for i in range(N)[::-1]:
  #colors.append( (1./N * i, .2, .2)) 
pie(fracs, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
#pie(fracs, labels=labels, autopct='%1.1f%%', startangle=90)
subplots_adjust(left=0,  right=1)
xlim(-2, 2)
ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)
import mpld3
html = mpld3.fig_to_html(f)
open("/tmp/d3.html", "w").write(html)
import os
os.system("cat /tmp/d3.html | pbcopy")
