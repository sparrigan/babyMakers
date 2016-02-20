import model
import os
from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify
import json
import urllib2
from urllib import quote
import time
import pandas as pd
import numpy as np
from numpy import random
from numpy.random import random_sample
from scipy import ndimage as nd
import math
from math import sqrt

# TODO: add wtfworms import wtforms

#Create flask instance
application = Flask(__name__)

# Import environment configuration settings for API
API_KEY = os.environ['API_KEY']

#T= themoviedb base URL
base_url = "http://api.themoviedb.org/3/"


def get_celeb_score(data, celeb_years, alpha=0.95):
	"""Takes a dict of year:births *for years wanted*, and a list of movie years within
	this range"""
	# Convert birth data dict to a pandas Series
	birth_data = pd.Series(data)
	birth_data.sort_index()
	all_yrs = birth_data.index
	print 'birth_data = ', birth_data
	print 'birth_data.values = ', birth_data.values
	# Differentiate series
	name_diff = pd.Series(np.append(np.diff(birth_data.values),0))
	name_diff.index = all_yrs
	# KDE on values
	kde_vals = nd.filters.gaussian_filter(birth_data.values, sigma=2)
	# Differentiate values smoothed by kde
	kde_diff = pd.Series(np.append(np.diff(kde_vals),0))
	kde_diff.index = all_yrs
	# Get celebs score
	celeb_score = calc_celeb_score(celeb_years, name_diff, kde_diff, pos_only=True)
	print 'celeb_years = ', celeb_years
	print 'celeb_score = ', celeb_score
	print 'name diff = ', name_diff
	print 'kde_diff = ', kde_diff
	# Get values for random distribution
	mc_samp = []
	min_yr = min(all_yrs)
	max_yr = max(all_yrs)
	for i in range(10000):
		rand_yrs = get_rand_years(5,min_yr,max_yr)
		mc_samp.append(calc_celeb_score(rand_yrs,name_diff, kde_diff, pos_only=True))
	# Generate histogram data:
	wts = np.ones_like(mc_samp)/float(len(mc_samp))
	hist_vals, hist_bins = np.histogram(mc_samp, bins=int(sqrt(len(mc_samp))), weights=wts)
	# Get list of hist vals within given significance
	celeb_pval, percentiles = get_percentile_points(hist_vals, hist_bins, alpha, celeb_score=celeb_score)
	# Return celebrity score, hist_vals, and percentile data
	return celeb_pval, celeb_score, hist_vals.tolist(), hist_bins.tolist(), percentiles.value.tolist()

def calc_celeb_score(celeb_yrs, name_diff, smooth_diff, pos_only=False):
	"""Rule for scoring a celebrities years based on derivatives"""
	all_yrs = name_diff.index
	scores_next = [name_diff[yr] - smooth_diff[yr] for yr in celeb_yrs]
	scores_current = [name_diff[x-1] - smooth_diff[x-1] if x in all_yrs+1 else 0 for x in celeb_yrs]
	# Remove negative scores if option set
	if pos_only:
		scores_next = [x if x>0 else 0 for x in scores_next]
		scores_current = [x if x>0 else 0 for x in scores_current]
	return max(sum(scores_next), sum(scores_current))

def get_rand_years(n, min_yr, max_yr):
	"""Return n random years from the range [min_year, max_year]"""
	rnd_yr_list = [int(np.ceil((max_yr-min_yr)*random_sample() + min_yr)) \
					for a in range(0,n)]
	return np.array(rnd_yr_list)

def get_percentile_points(hist_vals, hist_bins, percentile_value, celeb_score=None):
	"""Return dataframe of histogram points that fall within given percentile
	with columns 'value' and 'weight'. If passed a celebrity score, also returns
	p-value of that particular celebrities score.
	hist_vals: Result of assignment to a plt.hist instance
	percential_value: The percentile to find"""
	# Create Series of bin values and weights from the histogram (so can sort and retain indices)
	hist_df = pd.DataFrame(zip(hist_bins, hist_vals), columns=['value', 'weight'])
	# Sort the histogram values by weight
	hist_df_sort = hist_df.sort(columns='weight', ascending=False)
	# Get cumulative sum of weights
	hist_df_sort['cumsum'] = hist_df_sort['weight'].cumsum()
	# Get all values for which cumsum falls below percentile value required
	percentile_vals = hist_df_sort['cumsum'][hist_df_sort['weight'] < percentile_value]
	# If passed celebrity score, then also work out and return it's p-value
	if celeb_score:
		sortbyval = hist_df_sort.sort('value')
		max_vals = sortbyval['value'] >= celeb_score
		min_vals = sortbyval['value'] <= celeb_score
		max_idx = sortbyval.ix[max_vals, 'value'].idxmin()
		min_idx = sortbyval.ix[min_vals, 'value'].idxmax()
		# Take average of elements closest to celeb_score and return
		# prob of getting more extreme val (p-val)
		celeb_pval = 1-sortbyval.ix[min_idx:max_idx, 'cumsum'].mean()
	else:
		celeb_pval = None
	return celeb_pval, hist_df.ix[percentile_vals.index]

def check_str(name):
	#Make sure camel case for DB
	new_name = name.lower().capitalize()
	return new_name


def get_movie_ids(json_vals):
	"""Takes a json page and returns list of dicts with movie names and ids"""
	ret_list = []
	for movie in json_vals['results']:
		# Only add movie to list if json contains info needed in right format
		if ((len(movie['title'])>0) & (isInt_str(movie['id'])) & (isInt_str(movie['release_date'][:4]))):
			#NOTE: REMOVE THIS WHEN UPDATE DATABASE!?!?!?
			if (int(movie['release_date'][:4]) <= 2010):
				mov_inf = {'info': {'title': movie['title'], 'm_id': movie['id'], 'release': int(movie['release_date'][:4]), 'poster': None}}
				# Add on poster_path if it exists otherwise leave as None
				if ('poster_path' in movie):
					if (movie['poster_path'] and (len(movie['poster_path'])>0)):
						mov_inf['info']['poster'] = movie['poster_path']
				ret_list.append(mov_inf)
	return ret_list


def isInt_str(v):
	"""Checks if a string contains an int"""
	v = str(v).strip()
	return v=='0' or (v if v.find('..') > -1 else v.lstrip('-+').rstrip('0').rstrip('.')).isdigit()


def remove_repeats(movie_dict):
	"""Removes any repeated entries in json received from themoviedb API"""
	# Get list of ids in same order as list of movie dics
	id_list = [x['info']['m_id'] for x in movie_dict]
	# Create dict of occurences of each number
	y = np.bincount(id_list)
	ii = np.nonzero(y)[0]
	count_dic = dict(zip(ii,y[ii]))
	del_idx = []
	# Now loop through movie_dict entries, remove if >1 occurences
	for idx, mov in enumerate(movie_dict):
		if count_dic[mov['info']['m_id']] > 1:
			# log entry for delete
			del_idx.append(idx)
			# Reduce counts for this entry
			count_dic[mov['info']['m_id']] -= 1
	# Now delete those entries from list in reverse
	for index in sorted(del_idx, reverse=True):
		del movie_dict[index]
	return movie_dict

# TODO: Upadate to return suggestions if not unique result for name
def get_movieapi_results(full_name):
	"""Takes full name string (not URL encoded) and returns dict of movies"""
	# Convert name to URL encoded string
	full_name = quote(full_name)
	# Get actor_id for movie star searched for
	name_url = "http://api.themoviedb.org/3/search/person?&api_key="+API_KEY+"&query=%s" %full_name
	response = urllib2.urlopen(name_url)
	data = json.load(response)
	actor_id = data['results'][0]['id']
	profile_url = None
	# Assign movie-star profile pic url if it exists
	if ('profile_path' in data['results'][0]):
		if data['results'][0]['profile_path']:
			profile_url = data['results'][0]['profile_path']
	# Get list of all movies for movie-star using actor_id
	query = 'movie?with_cast=%i' %(actor_id)
	url = base_url + 'discover/' + query + "&api_key=" + API_KEY
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
		url = base_url + 'discover/' + query + pagereq + "&api_key=" + API_KEY
		current_pg = json.load(urllib2.urlopen(url))
		temp.append(current_pg)
		#Combine dict of movies from this page with previously found ones
		movie_dict += get_movie_ids(current_pg)
	# Remove entries with repeated movie_id (themoviedb confirmed bug)
	movie_dict = remove_repeats(movie_dict)
	# Return movie_dict, actor_id and profile picture url
	return movie_dict, actor_id, profile_url

def get_cast_pos(actor_id, movie_id, cast_id_min):
	"""Returns T/F for whether actor in top n of cast list"""
	# Get full credit list for movie in question from themoviedb
	query = base_url + 'movie/' + str(movie_id) + '/credits?' + "&api_key=" + API_KEY
	try:
		page = urllib2.urlopen(query)
	except urllib2.HTTPError, err:
		api_error = err.code
		page = None
	except urllib2.URLError, err:
		api_error = err.reason
		page = None
	# Allow for possibility that no entry
	if page:
		try:
			movie_cast = json.load(page)
		except ValueError:
			error = 'ValueError loading json'
			movie_cast = None
		# If received list of cast members, search for desired movie-star
		if movie_cast:
			# Extract cast data needed for check from json into list
			if movie_cast['cast']:
				castid = [act for act in movie_cast['cast'] if act['id']==actor_id][0]['order']
			else:
				# If no cast data then assume movie not worth considering
				return False, None
			# If movie-star high enough in cast ret True, else ret False
			if (castid < cast_id_min):
				return True, None
			else:
				return False, None
		else:
			# Error decoding JSON
			return None, error
	else:
		# Error in connection
		return None, api_error


# TODO: Include error catching for these api calls too (put error catching into function)

def get_movie_score(movie_id):
	"""Checks whether movie passed satsifies criteria for being significant
	in actors career
	Returns revenue, average vote and popularity"""
	# Get movie info from api call
	query = base_url + 'movie/' + str(movie_id) +'?' + "&api_key=" + API_KEY
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
	# Return vals
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

# Flask routing:

@application.route('/', methods=['GET'])
def index():
	"""Render index template"""
	return render_template('index.html')

# @application.route('/test', methods=['GET'])
# def test():
# 	return render_template('test.html')

# @application.route('/return_list', methods=['GET'])
# def return_list():
# 	return render_template('list.html')

@application.route('/get_name_data/<name>/<sex>/<start_yr>', methods=['GET', 'POST'])
def get_name_data(name, sex, start_yr):
	"""Return normed DB info for name history"""
	# Get raw name data from database
	data_list = model.get_name_data(name, sex, start_yr, 'python_dict')
	# Get total birth data to normalise
	totals = model.get_total_births(sex)
	# Pass normed data into dict comprehension
	data_dict ={}
	data_dict['raw'] = {yr:data_list[yr] for yr in data_list.keys()}
	data_dict['normed'] = {yr:(data_list[yr]/float(totals[int(yr)]))*100 for yr in data_list.keys()}
	# TODO: Note that this does not return a second error parameter,
	# which d3.json function expects normally (eg: see use of d3.json here:
	# http://www.brettdangerfield.com/post/realtime_data_tag_cloud/)
	return jsonify(**data_dict)

@application.route('/get_movie_data/<f_name>/<l_name>', methods=['GET', 'POST'])
def get_movie_data(f_name, l_name):
	"""Return movies and profile pic for movie-star using themoviedb"""
	movie_dict, actor_id, profile_url = get_movieapi_results(f_name+" "+l_name)
	json = {'results': movie_dict, 'actor_id': actor_id, 'profile_url': profile_url}
	return jsonify(json)

@application.route('/cast_check/<actor_id>/<movie_id>', methods=['GET', 'POST'])
def cast_check(actor_id, movie_id):
	"""Return cast position of movie-star in given movie"""
	#NOTE: Does not currently deal with 429 errrors
	cast_pos, error = get_cast_pos(int(actor_id), int(movie_id), 2)
	# Sleep to prevent 429 themoviedb API limit errors
	time.sleep(0.2)
	json = {'result': cast_pos, 'error':error}
	return jsonify(json)


@application.route('/movie_score/<movie_id>', methods=['GET', 'POST'])
def movie_score(movie_id):
	"""Scores a movie given its movie_id"""
	score = get_movie_score(movie_id)
	# Add movie_id to score for returning
	score['movie_id'] = int(movie_id)
	# Sleep to prevent 429 themoviedb API limit errors
	time.sleep(0.2)
	return jsonify(score)

@application.route('/get_celeb_score', methods=["GET", "POST"])
def celeb_score_route():
	"""Takes json that contains name history and also movie-star top five yrs"""
	# Use get_json to return dict from json received by POST
	celeb_json = request.get_json(force=True)
	# Put births from POST json into dict
	births_dict = {year:births for year,births in celeb_json['baby_vals']}
	# Get score, p-value and histogram data for celebrity
	celeb_pval, score, hv, hb, perc = get_celeb_score(births_dict, celeb_json['celeb_yrs'])
	return jsonify({'celeb_pval': celeb_pval, 'celeb_score': score, 'hist_vals':hv, 'hist_bins':hb, 'perc':perc})




# !!! Start temporary voting app !!!

dict_of_responses = {"True": {"feb 3rd, 2015": [1,2,3,3,3,3,2,2,1]}, "False":[{"april 18th, 2015": [1,2,3,3,2,1]}]}

chardic = {'a':1, 'b':2, 'c':3}
def txtparse(string):
	"""Parse input sms to detect a,b,c"""
	PATTERN = "([a-cA-C])"
	string.strip(" ")
	if len(string) > 3:
		return None
	match = re.findall(PATTERN, string)
	if len(match) == 1:
		return chardic[match[0].lower()]

@application.route('/voting', methods=['GET'])
def voting_index():
	"""Render voting app index template"""
	return render_template('voting.html')

@application.route('/recieve_data', methods=["GET","POST"])
def recieve_data():
	"""Recieves incoming text data, if "True" is not None, add to list"""
	if dict_of_responses["True"] != None:
		sms_body = request.values.get("Body")
		#Parse body of sms text
		sms_body = txtparse(sms_body)
		#get the name of the recording
		recording_name = dict_of_responses["True"].keys()[0]
		#look up by name of recording and add the sms to the list
		dict_of_responses["True"][recording_name].append(sms_body)
	resp = twilio.twiml.Response()
	resp.message()
	print dict_of_responses
	return str(resp)

@application.route('/list_of_recordings')
def list_of_recordings():
    """ Returns all names of recordings and which ones are active"""
    #name of the active recording
    active = dict_of_responses["True"].keys()[0]
    #name of all other recordings
    inactive = []
    for recording_name in dict_of_responses["False"]:
        inactive.append(recording_name.keys()[0])

    all_recordings = {"active": active, "inactive": inactive}
    return json.dumps(all_recordings)

@application.route('/start_recording/<name_of_recording>')
def start_recording(name_of_recording):
    """ Given a name, check to see if there's a recording in the dict
    with that name, if so, set to active, if not, move current active to
    false and set new name to active """
    active = dict_of_responses["True"].keys()[0]
    print "I am the active: %s" % active
    print "I am the name passed in the url: %s" % name_of_recording
    inactive = []
    for recording_name in dict_of_responses["False"]:
        inactive.append(recording_name.keys()[0])

    if active == name_of_recording:
        return "You're recording : %r" % name_of_recording
    elif name_of_recording in inactive:
        #save current name_of_recording (and data) within inactive to a variable
        #iterate through the list of "False" recordings
        for n in dict_of_responses["False"]:
            print "woah n: %s" % dict_of_responses["False"].index(n)
            # if that item is the same as the one we are looking for
            if n.keys()[0] == name_of_recording:
                # save it in a temp variable
                print "The name given was in the false dict, which right now looks like: %r" % dict_of_responses["True"]
                new_active = {name_of_recording:n[name_of_recording]}
                # reset the value to whatever is in the active spot
                old_active = dict_of_responses["True"]
                if old_active.keys()[0] not in dict_of_responses["False"]:
                    print " old is not in inactive, so add it: %s" % old_active.keys()[0]
                    #delete the one that is getting promoted to active from false
                    indice = dict_of_responses["False"].index(n)
                    dict_of_responses["False"][indice]= old_active
                print "Tried to add %s to the false dict:" % old_active
                print "Did it work? : %s" % dict_of_responses["False"]
                # reset the active spot to the one with the name we are looking for
                dict_of_responses["True"] = new_active
                return "I have changed the active to %r " % new_active
    else:
        #if active not None
        if active != None:
            print "before adding to false dict: %r" % dict_of_responses["False"]
            dict_of_responses["False"].append(dict_of_responses["True"])
            print "this is what I've added to the false dicts: %r" % dict_of_responses["True"]
            print "This is what it looks like now: %r" % dict_of_responses["False"]
            # add active to inactive (False)
        dict_of_responses["True"] = {name_of_recording: []}
    #return render_template("start_recording.json", recording_name=name_of_recording)
        return "Yay, name of recording is %s" % name_of_recording

@application.route('/stop_recording')
def stop_recording():
    """ Given a name of a recording, if that name is in "True", move it to
    "False" and set "True" to None, if it is not in "True", return an error """
    active = dict_of_responses["True"].keys()[0]

    # if active is not None
    if active != None:
        #add active to false (inactive)
        old_active = dict_of_responses["True"]
        dict_of_responses["False"].append(old_active)
        #set active to None
        dict_of_responses["True"] = {None: "" }
        return "We have stopped recording WOOT!"
    return "You were not actively recording anything.. Whoops?"

@application.route('/get_vote_data')
def get_vote_data():
	""" Returns all vote data in records for currently active recording
	if a recording is active. Else returns None """
	if "True" in dict_of_responses:
		active = dict_of_responses["True"].keys()[0]
		data = dict_of_responses["True"][active]
		# Get counts of occurence of each number in data
		hist_data = [[x,data.count(x)] for x in np.unique(data)]
		return json.dumps({"name": active, "data": hist_data})
	else:
		return None



# !!! End temporary voting app !!!











if __name__ == '__main__':
	application.debug = True
	application.run()
	# Use below for serving to all IPs when deploying
	# application.run(host = '0.0.0.0')
