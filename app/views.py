from flask import render_template, request
from app import app, host, port, user, passwd, db
from app.helpers.database import con_db, query_db
from app.helpers.graphics import render_webfigure
import matplotlib.pyplot as plt
import mpld3


# To create a database connection, add the following
# within your view functions:
# con = con_db(host, port, user, passwd, db)


# ROUTING/VIEW FUNCTIONS
@app.route('/')
@app.route('/index')
def index():
    # Renders index.html.
    return render_template('index.html')

@app.route('/out')
def out():
  # WORK!!
  # Create database connection
  con = con_db(host, port, user, passwd, db)

  var_dict = {
    "userlon": request.args.get("userlon"),
    "userlat": request.args.get("userlat"),
    "genre": request.args.get("genre", 'No Genre')
  }

  # Query the database
  data = query_db(con, var_dict)

  # Add the results of the query.
  var_dict['data'] = data

  # Make the plot.
  fig_html = render_webfigure(var_dict)
  var_dict['fig_html'] = fig_html

  # Render the template w/ user input, query result, and figure included!
  return render_template('output.html', settings=var_dict)

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
