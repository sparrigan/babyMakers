import model
from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify
import urllib2
from urllib import quote
import pandas
import json
import time
import numpy as np

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

def remove_repeats(movie_dict):
	# Get list of ids in same order as list of movie dics
	id_list = [x['values'][0] for x in movie_dict]

	# Create dict of occurences of each number
	y = np.bincount(id_list)
	ii = np.nonzero(y)[0]
	count_dic = dict(zip(ii,y[ii]))
	del_idx = []
	# Now loop through movie_dict entries, remove if more than one occurences
	for idx, mov in enumerate(movie_dict):
		if count_dic[mov['values'][0]] > 1:
			# log entry for delete
			del_idx.append(idx)
			# Reduce counts for this entry
			count_dic[mov['values'][0]] -= 1
	# Now delete those entries from list in reverse
	for index in sorted(del_idx, reverse=True):
		del movie_dict[index]

	return movie_dict

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

	# Remove repeated entries by movie_id and return
	return remove_repeats(movie_dict), actor_id

# TODO: Way to refactor that reduces the number of movies we query for
# more detailed information?
# TODO: Replace this with a neural network!

def get_cast_pos(actor_id, movie_id, cast_id_min):
	"""Returns T/F for whether actor in top n of cast list"""
	query = base_url + 'movie/' + str(movie_id) + '/credits?' + api_key

	try:
		page = urllib2.urlopen(query)
	except urllib2.HTTPError, err:
		api_error = err.code
		page = None
	except urllib2.URLError, err:
		api_error = err.reason
		page = None

	if page:
		try:
			movie_cast = json.load(page)
		except ValueError:
			error = 'ValueError loading json'
			movie_cast = None


		if movie_cast:
			if movie_cast['cast']:
				castid = [act for act in movie_cast['cast'] if act['id']==actor_id][0]['order']
				# If no cast data then assume this movie isn't worth considering and force a False return
			else:
				# If no cast information then assume this movie isn't worth considering
				return False, None
			if (castid < cast_id_min):
				return True, None
			else:
				return False, None
		else:
			# Error decoding JSON, return None
			return None, error
	else:
		return None, api_error

# This has rest of logic for deciding on film
# TODO: Include error catching for these api calls too (put error catching into function)

def get_movie_score(movie_id):
	"""Checks whether movie passed satsifies criteria for being significant
	in actors career
	If actor in top n credits, returns revenue, average vote and popularity"""
	# Get movie info from api call
	print movie_id
	query = base_url + 'movie/' + str(movie_id) +'?' + api_key
	score_json = json.load(urllib2.urlopen(query))

	# Get poularity ranking from themoviedb:
	if 'popularity' in score_json:
		pop = score_json['popularity']
	else:
		pop = 0
	# Get average vote the themoviedb:
	if 'vote_average' in score_json:
		vote = score_json['vote_average']
	else:
		vote = 0
	# Get revenue from themoviedb
	if 'revenue' in score_json:
		rev = score_json['revenue']
	else:
		rev = 0
	# Return values
	return {'revenue': rev, 'pop': pop, 'vote': vote}


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
	return render_template('index.html')

@app.route('/test', methods=['GET'])
def test():
	return render_template('test.html')

@app.route('/return_list', methods=['GET'])
def return_list():
	return render_template('list.html')

@app.route('/get_d3_data/<name>/<sex>', methods=['GET', 'POST'])
def get_d3_data(name, sex):
	data_list = model.get_name_data(name, sex, 'python_dict')
	# TODO: Note that this does not return a second error parameter,
	# which d3.json function expects normally (eg: see use of d3.json here:
	# http://www.brettdangerfield.com/post/realtime_data_tag_cloud/)
	return jsonify(**data_list)

@app.route('/get_movie_data/', methods=['GET', 'POST'])
def get_movie_data():
	movie_dict, actor_id = get_movieapi_results("Humphrey Bogart")
	json = {'results': movie_dict, 'actor_id': actor_id}
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
	# TODO: Deal with 429 errors by addding to list and retrying at end
	cast_pos, error = get_cast_pos(int(actor_id), int(movie_id), 2)
	# Sleep to prevent 429 (TODO: Need a better solution for promises)
	time.sleep(0.2)
	json = {'result': cast_pos, 'error':error}
	return jsonify(json)


@app.route('/movie_score/<movie_id>', methods=['GET', 'POST'])
def movie_score(movie_id):
	outcome = get_movie_score(movie_id)
	outcome['movie_id'] = int(movie_id)
	time.sleep(0.2)
	return jsonify(outcome)



# TODO: Create route for getting data on user input
# Only need route for talking to my own backend
@app.route('/get_data', methods=["GET", "POST"])
def get_data():
	name = request.form['name']
	#Validate input
	name = check_str(name)
	data_list = model.get_name_data(name, 'F', 'python')
	return render_template('data_viz.html', data_list=data_list)


if __name__ == '__main__':
	app.debug = True
	app.run()
