import model
from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify
import urllib2
from urllib import quote
import pandas
import json
import time

from numpy import random
import math
# TODO: add wtfworms import wtforms
#Create flask instance
app = Flask(__name__)

def check_str(name):
	#Make sure camel case
	new_name = name.lower().capitalize()
	return new_name

# def get_movie_ids(json_vals):
# 	"""Takes a json page and returns dict with movie names and ids"""
# 	ret_dict = {}
# 	for movie in json_vals['results']:
# 		ret_dict[movie['title']] = [movie['id'], int(movie['release_date'][:4])]
# 	return ret_dict

def get_movie_ids(json_vals):
	"""Takes a json page and returns list of dicts with movie names and ids"""
	ret_list = []
	for movie in json_vals['results']:
		ret_list.append({'movie': movie['title'], 'values': [movie['id'], int(movie['release_date'][:4])]})
	return ret_list

base_url = "http://api.themoviedb.org/3/"
api_key = '&api_key=e5fae0ea529d524430820812b15b9521'

# TODO: Upadate to return suggestions if not unique result for name
def get_movieapi_results(full_name):
	"""Takes full name string (not URL encoded) and returns dict of movies"""
	# Convert name to URL encoded string
	full_name = quote(full_name)
	name_url = "http://api.themoviedb.org/3/search/person?api_key=e5fae0ea529d524430820812b15b9521&query=%s" %full_name
	response = urllib2.urlopen(name_url)
	data = json.load(response)
	actor_id = data['results'][0]['id']
	query = 'movie?with_cast=%i&sort_by=revenue.desc' %(actor_id)
	url = base_url + 'discover/' + query + api_key
	# Response for query for actors films will contain multiple pages.
	# Get first page to find num of pages
	response2 = urllib2.urlopen(url)
	pg1 = json.load(response2)
	num_pages = pg1['total_pages']
	movie_dict = get_movie_ids(pg1)
	print movie_dict
	#Now iterate over all remaining pages, adding movies to movie_dict dictionary
	temp = []
	for page in range(2,num_pages+1):
		#Get current page
		pagereq = '&page=%i' %page
		url = base_url + 'discover/' + query + pagereq + api_key
		current_pg = json.load(urllib2.urlopen(url))
		temp.append(current_pg)
		#Combine dict of movies from this page with previously found ones
		movie_dict += get_movie_ids(current_pg)
	return movie_dict

# TODO: Way to refactor that reduces the number of movies we query for
# more detailed information?
# TODO: Replace this with a neural network!

def get_cast_pos(actor_id, movie_id, cast_id_min):
	"""Returns T/F for whether actor in top n of cast list"""
	query = base_url + 'movie/' + str(movie_id) + '/credits?' + api_key
	movie_cast = json.load(urllib2.urlopen(query))
	if movie_cast['cast']:
		castid = [act for act in movie_cast['cast'] if act['id']==actor_id][0]['order']
		# If no cast data then assume this movie isn't worth considering and force a False return
	else:
		# If no cast information then assume this movie isn't worth considering
		return False
	if (castid < cast_id_min):
		return True
	else:
		return False

# This has rest of logic for deciding on film
def get_movie_rank(actor_id, movie_id):
	"""Checks whether movie passed satsifies criteria for being significant
	in actors career
	If actor in top n credits, returns revenue, average vote and popularity"""
	# Only consider film if actor in top 2 cast order
	# TODO: refactor to have this defined more globally
	cast_id_min = 2
	# Check position of actor in cast listing, giving cast_id
	query = base_url + 'movie/' + str(movie_id) + '/credits?' + api_key
	movie_cast = json.load(urllib2.urlopen(query))
	query = base_url + 'movie/' + str(movie_id) +'?' + api_key
	movie_json = json.load(urllib2.urlopen(query))
	if movie_cast['cast']:
		castid = [act for act in movie_cast['cast'] if act['id']==actor_id][0]['order']
		# If no cast data then assume this movie isn't worth considering and force a False return
	else:
		castid = n+1
	# Get poularity ranking from omdb:
	if 'popularity' in movie_json:
		pop = movie_json['popularity']
	else:
		pop = 0
	# Get average vote on omdb:
	if 'vote_average' in movie_json:
		vote = movie_json['vote_average']
	else:
		vote = 0
	# Only return value if actor/actress listed high in cast listing
	if (castid < cast_id_min):
		# Need a better way of generating a measure here
		return movie_json['revenue'], pop, vote
	else:
		return None


def top_n_movies(full_name, actor_id, n, score_func):
	"""Returns movies ranked top n according to a score function,
	func(revenue, vote, popularity) that returns a float score from
	features"""
	# Pandas series for storing scores
	valid_movies = pd.Series(name='Score')
	valid_movies.index.name = 'Movie'
	# Get all movies for actor
	all_movies = get_movieapi_results(full_name)
	for name, movie_id in all_movies.items():
		check = get_movie_rank(actor_id, movie_id)
		if check:
			# If movie valid, pass data to score_func and store score
			valid_movies[name] = score_func(*check)






# TODO: Create route for index page
@app.route('/', methods=['GET'])
def index():
	print "running"
	return render_template('index.html')

@app.route('/return_list', methods=['GET'])
def return_list():
	return render_template('list.html')

@app.route('/get_d3_data/<name>/<sex>', methods=['GET', 'POST'])
def get_d3_data(name, sex):
	print 'here'
	print sex
	# name = 'John'
	print name
	data_list = model.get_name_data(name, sex, 'python_dict')
	# TODO: Note that this does not return a second error parameter,
	# which d3.json function expects normally (eg: see use of d3.json here:
	# http://www.brettdangerfield.com/post/realtime_data_tag_cloud/)
	return jsonify(**data_list)

@app.route('/get_movie_data/', methods=['GET', 'POST'])
def get_movie_data():
	movie_dict = get_movieapi_results('Humphrey Bogart')
	json = {'results': movie_dict}
	return jsonify(json)

# @app.route('/promise_test/<idstr>', methods=['GET', 'POST'])
# def promise_test(idstr):
# 	print "Promise route fired"
# 	# Wait a random time
# 	slp_time = int(math.floor(random.rand()*5))+1
# 	time.sleep(slp_time)
# 	modstr = 'oh my, '+idstr+', how nice'
# 	ret = bool(int(round(random.rand())))
# 	json = {'result': ret}
# 	return jsonify(json)


@app.route('/cast_check/<actor_id>/<movie_id>', methods=['GET', 'POST'])
def cast_check(actor_id, movie_id):
	# make cast_pos calls async with grequest if can't get promises
	# to work async with nginx etc...
	cast_pos = get_cast_pos(actor_id, movie_id, 2)
	json = {'result': cast_pos}
	return jsoniy(json)



# TODO: Create route for getting data on user input
# Only need route for talking to my own backend
@app.route('/get_data', methods=["GET", "POST"])
def get_data():
	name = request.form['name']
	print name
	#Validate input
	name = check_str(name)
	data_list = model.get_name_data(name, 'F', 'python')
	print data_list
	return render_template('data_viz.html', data_list=data_list)


if __name__ == '__main__':
	app.debug = True
	app.run()
