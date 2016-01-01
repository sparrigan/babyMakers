import model
from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify
# TODO: add wtfworms import wtforms
#Create flask instance
app = Flask(__name__)

def check_str(name):
	#Make sure camel case
	new_name = name.lower().capitalize()
	return new_name

# TODO: Create route for index page
@app.route('/', methods=['GET'])
def index():
	print "running"
	return render_template('index.html')

@app.route('/return_list', methods=['GET'])
def return_list():
	return render_template('list.html')

@app.route('/get_d3_data/<name>', methods=['GET', 'POST'])
def get_d3_data(name):
	print 'here'
	# name = 'John'
	print name
	data_list = model.get_name_data(name, 'M', 'python_dict')
	# TODO: Note that this does not return a second error parameter,
	# which d3.json function expects normally (eg: see use of d3.json here:
	# http://www.brettdangerfield.com/post/realtime_data_tag_cloud/)
	return jsonify(**data_list)


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
