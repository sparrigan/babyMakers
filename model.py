# Imports needed
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Text, func, inspect
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
from sqlalchemy import *
import time
import json
import os

# Get environment variables needed to access DB
PG_USERNAME = os.environ.get('PG_USERNAME')
PG_PASSWORD = os.environ.get('PG_PASSWORD')
DATABASE = os.environ.get('DATABASE')

#Connect to DB with SQLA
engine = create_engine("postgresql://"+PG_USERNAME+":"+PG_PASSWORD+"@"+DATABASE, echo=False)
# Setup declarative base
Base = declarative_base(engine)
# Session for connection
Session = sessionmaker(bind=engine)
session = Session()

# TODO: Change this to dynamically find years so can update with latests csv's of data from web
year_vals = np.arange(1880,2011)

#Create classes for male and female tables
col_dic_m = {'__tablename__': 'male', 'name': Column('name', String(32), primary_key=True)}
col_dic_f = {'__tablename__': 'female', 'name': Column('name', String(32), primary_key=True)}
for year in year_vals:
	col_dic_m['col'+str(year)] = Column(str(year), Integer)
	col_dic_f['col'+str(year)] = Column(str(year), Integer)
Male = type('Male', (Base,), col_dic_m)
Female = type('Female', (Base,), col_dic_f)

# Create table for storing total births each year for M/F
class TotalBirthsMale(Base):
	__tablename__ = 'total_births_male'
	year = Column(Integer, primary_key=True)
	births = Column(Integer)

class TotalBirthsFemale(Base):
	__tablename__ = 'total_births_female'
	year = Column(Integer, primary_key=True)
	births = Column(Integer)

def _update_total_births():
	"""Reads DB to find total births each year and updates Total tables"""
	tabs = [[Male, TotalBirthsMale],[Female, TotalBirthsFemale]]
	for tab in tabs:
		mapper = inspect(tab[0])
		# Iterate over columns of table (note: iterator returns object, key
		# property gives name of column)
		for col in mapper.attrs:
			# Don't include name column in sum
			if (col.key != 'name'):
				# Dynamically call method on table class corresponding to col
				qry = session.query(func.sum(getattr(tab[0], col.key))).first()
				# Insert into TotalBirthsMale table
				yr = int(col.key[3:])
				session.add(tab[1](year=yr, births=int(qry[0])))
		# Commit changes to table
		session.commit()

def _csv_df(path):
	"""Import CSV to dataframe in correct format, including filling NAs
	path: where to find csv
	returns df and groupby object"""
	#Get csv files for each year and compile into single DF
	sep_names = []
	for year in year_vals:
	    fname = path + ('yob%s.txt' %year)
	    temp = pd.read_csv(fname,names=['name','sex','births'])
	    temp['year'] = year
	    sep_names.append(temp)
	names_df = pd.concat(sep_names);
	#Return groupby object that groups df by names
	return names_df

def _get_csv_name_vals(name, names_groupby):
	"""Returns time series for given name and sex
	name: string - name to return data for
	sex: string - sex to return data for (M/F)
	names_groupby: pandas groupby object sorting df by name"""
	# Extract male and female values from initial DF
	both_sex = names_groupby.get_group(name)
	male_sex = both_sex[both_sex.sex == 'M']
	fmale_sex = both_sex[both_sex.sex == 'F']
	male_vals = male_sex[['births','year']].set_index('year')
	fmale_vals = fmale_sex[['births','year']].set_index('year')
	#Return reindexed df (to check have all year values). Fill NA with zero
	return male_vals.reindex(year_vals, fill_value=0), \
		fmale_vals.reindex(year_vals, fill_value=0)

def _drop_tabs(s):
	"""Drop all tables from DB using SQLA expression language
	s: SQLA session to emmit SQL with"""
	# WARNING: Drops all tables in DB
	# NOTE: If many tables then may exceed lock limit with this method
	s.execute("DROP SCHEMA public CASCADE;")
	s.commit()
	s.execute("CREATE SCHEMA public;")
	s.commit()

def _insert_all_rows(names_df, chunk_size):
	"""Inserts rows into male and female tables for each name"""
	#Get list of names for DB from pandas DF
	names_list = names_df.name.unique()
	#Groupby dataframe for easy access to each name's time series
	names_gb = names_df.groupby(names_df.name)
	#Iterate over names and add rows and build query
	i=1
	start = time.time()
	for name in names_list:
		m_values, f_values = _get_csv_name_vals(name, names_gb)
		name_str = "'"+name+"'"
		col_names = '(name, %s)' %(str([yr for yr in year_vals])[1:-1])
		#Only insert values if non-zero
		if (sum(m_values.births>0) > 0):
			ins_vals_m = '('+name_str+', '+str(m_values.births.values.tolist())[1:-1]+')'
			ins_string_m = 'INSERT INTO "male" VALUES %s;' %ins_vals_m
			session.execute(ins_string_m)
		if (sum(f_values.births>0) > 0):
			ins_vals_f = '('+name_str+', '+str(f_values.births.values.tolist())[1:-1]+')'
			ins_string_f = 'INSERT INTO "female" VALUES %s;' %ins_vals_f
			session.execute(ins_string_f)
		session.commit()
		if (i%1000 == 0):
			print '%r names done in %r ms' %(i, int((time.time() - start) * 1000))
			start = time.time()
		i+=1

def get_name_data(name, sex, start_yr, ret_type = 'json'):
	"""Returns history of births for name in requested format
	name: name to query in DB
	sex: sex of name
	start_yr: first year to query DB from (>1880)
	ret_type: format to return birth history in"""
	if sex in ['m', 'M', 'male', 'Male']:
		# Query Male DB for name
		qry = session.query(Male).filter_by(name=name)
		if qry.first():
			# Get list from dict that is returned
			q_dict = qry.first().__dict__
			# Remove non-column entries that might be passed by SQLA
			# and remove col prefix from others
			for keyval in q_dict.keys():
				if ((keyval[:3] != 'col') or (keyval[3:]<start_yr)):
					q_dict.pop(keyval)
				else:
					q_dict[keyval[3:]] = q_dict.pop(keyval)
			# Return required type
			if ret_type=='python':
				return [q_dict[yr] for yr in range(start_yr,2011)]
			elif ret_type=='json':
				return json.dumps(q_dict)
			elif ret_type=='python_dict':
				return q_dict
			else:
				return None
		else:
			return None
	elif sex in ['f', 'F', 'female', 'Female']:
		# Query Female DB for name
		qry = session.query(Female).filter_by(name=name)
		if qry.first():
			# Get list from dict that is returned
			q_dict = qry.first().__dict__
			# Remove non-column entries that might be passed by SQLA
			# and remove col prefix from others
			for keyval in q_dict.keys():
				if ((keyval[:3] != 'col') or (keyval[3:]<start_yr)):
					q_dict.pop(keyval)
				else:
					q_dict[keyval[3:]] = q_dict.pop(keyval)
			if ret_type=='python':
				return [q_dict['col'+str(yr)] for yr in range(start_yr,2011)]
			elif ret_type=='json':
				return json.dumps(q_dict)
			elif ret_type=='python_dict':
				return q_dict
			else:
				return None
		else:
			return None

def get_total_births(sex):
	"""Return total number of births each year for given sex"""
	results_dict = {}
	# Query relevant ORM class for M/F total births
	if sex in ['m', 'M', 'male', 'Male']:
		qry = session.query(TotalBirthsMale)
	elif sex in ['f', 'F', 'female', 'Female']:
		qry = session.query(TotalBirthsFemale)
	# Unpack results into a dict
	for vals in qry:
		results_dict[vals.year] = vals.births
	return results_dict

if __name__ == '__main__':
	#WARNING! Clear db
	# _drop_tabs(session)

	# If run as script then populate tables with CSV values...

	#Create corresponding tables in database
	Base.metadata.create_all(engine)

	#Get CSV path from environment variable
	path = os.environ['CSV_PATH']
	print 'Importing CSV...'
	names_df = _csv_df(path)

	#Insert rows
	print 'Inserting rows'
	_insert_all_rows(names_df, 0)
