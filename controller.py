import model
from flask import Flask
from flask import render_template, request, redirect, url_for, flash

#Create flask instance
app = Flask(__name__)

# TODO: Create route for index page
@app.route('/', methods=['GET'])
def index():
	return render_template('index.html')

# TODO: Create route for getting data on user input
# Only need route for talking to my own backend


if __name__ == '__main__':
	app.run()
