# Imports needed
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
from sqlalchemy import *
import time

# To start postgres server from terminal
# postgres -D /usr/local/var/postgres
#USER: test_user
#PW: testpw
#md5??? 'md52cc83a98108669b4ebbcf263ef065ab6'
#Drop all tables one at a time:
# psql -U 'test_user' 'test' -t -c "select 'drop table \"' || tablename || '\" cascade;' from pg_tables where schemaname = 'public'"  | psql -U 'test_user' 'test'


engine = create_engine("postgresql://test_user:testpw@localhost/test", echo=False)
Base = declarative_base(engine)
# TODO: does each individual table need it's own metadata
# metadata = MetaData(engine)
Session = sessionmaker(bind=engine)
session = Session()



def _csv_df(path):
	"""Import CSV to dataframe in correct format, including filling NAs
	path: where to find csv
	returns df and groupby object"""
	#Get csv files for each year and compile into single df
	sep_names = []
	years = np.arange(1880,2011)
	for year in years:
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
	#TODO: Get unique year values from df and create range from min and max
	years = np.arange(1880,2011)
	both_sex = names_groupby.get_group(name)
	male_sex = both_sex[both_sex.sex == 'M']
	fmale_sex = both_sex[both_sex.sex == 'F']
	male_vals = male_sex[['births','year']].set_index('year')
	fmale_vals = fmale_sex[['births','year']].set_index('year')
	#Return reindexed df (to check have all year values). Fill NA with zero
	return male_vals.reindex(years, fill_value=0), \
		fmale_vals.reindex(years, fill_value=0)


def _drop_tabs(s):
	"""Drop all tables from DB using SQLA expression language
	s: SQLA session to emmit SQL with"""
	s.execute("DROP SCHEMA public CASCADE;")
	s.commit()
	s.execute("CREATE SCHEMA public;")
	s.commit()

#ONE FUNCTION THAT CREATES ALL CLASSES AND COMMITS TO TABLES AND IS CALLED IN NAME==MAIN
#(PUT CREATE TABLES IN SEPERATE FUNCTION)

#ANOTHER FUNCTION THAT CREATES REQUIRED CLASS OF REQUIRED NAME. THIS IS CALLED EXTERNALLY
#(OR GLOBALLY IF WANTED TO ENSURE CLASS AVAILABLE AS PACKAGE IMPORTED)

def create_tab_class(name):
	"""Creates class mapped to table in db with given name"""
	# Use declarative and autoload to construct a class for the table we want
	# Alternatively could make Table obj and link to class with mapper or
	# define all table columns etc explicitly if known
	# http://tinyurl.com/2allx6z
	return type(str(name), (Base,), {
		'__tablename__': name,
		'__table_args__': {'autoload':True}})


def get_name_data(name, sex=None):
	"""Returns series/df of births for given name. If sex specified then returns
	series of this only. Otherwise returns df with both sexes"""
	#This function will create ORM class for this name, but pandas can get
	#table just given it's name and engine connection! So don't need it.
	# name_class = create_tab_class(name)
	pk_name = name+'_ID'
	#Use pandas to return df from named table
	name_df = pd.read_sql_table(name, engine)
	#Set primary key years as index
	name_df = name_df.set_index(pk_name)
	name_df.index.name = 'Year'
	#If only one sex requested then select it out
	if (sex=='M' or sex=='m'):
		return name_df.m
	elif (sex=='F' or sex=='f'):
		return name_df.f
	else:
		return name_df


def _create_tables_core(names_list, names_df):
	"""Use core settings"""
	year_values = np.arange(1880,2011)
	names_gb = names_df.groupby(names_df.name)
	chunk_size = 1000
	time_df = pd.DataFrame(columns=['time_class', 'time_insert'],
		index=range(chunk_size,chunk_size*300,chunk_size))
	chunker = chunks(names_list, chunk_size)
	# connection = engine.connect()
	ii=0
	for chunk in chunker:
		print 'Chunk: %r to %r' %(ii*chunk_size, (ii+1)*chunk_size)
		start = time.time()
		# 1. Create table objects for current chunk
		table_list = []
		for name in chunk:
			pkname = name+'_ID'
			table_list.append(Table(name, Base.metadata,
				Column(pkname, Integer, primary_key=True),
				Column('m', Integer),
				Column('f', Integer)
			))

		Base.metadata.create_all(engine)
		print 'Time to create tables: %r' %int((time.time() - start))
		time_df.ix[(ii+1)*chunk_size].time_class = int((time.time() - start) * 1000)

		# Insert values into tables
		start = time.time()
		for tab in table_list:
			tabname = tab.name
			m_values, f_values = _get_csv_name_vals(tabname, names_gb)
			pkname = tabname+'_ID'
			#Construct string for insert containing all entries for this table
			ins_vals = zip(year_values, m_values.births.values, f_values.births.values)
			ins_vals_str = str(ins_vals)[1:-1]
			ins_statement = 'INSERT INTO "%s" VALUES %s' %(tabname, ins_vals_str)
			session.execute(ins_statement)
			#Note: *DO* need to commit after an execute statement
			session.commit()
			# for i,j,k in zip(year_values, m_values.births.values, f_values.births.values):
			# 	#Note: pass keywords as an unpacked dict for dyanmic pk keyword
			# 	# post = name_class(**{pk_name: i, 'm':j, 'f': k})
			# 	session.execute('INSERT INTO "%s" VALUES (%r, %r, %r)' %(tabname, i, j, k))
		# session.commit()
			# connection.execute(
			# 	tab.insert(),
			# 	#TODO: Rewrite this to insert rows with year, m, f values
			# 	[{pkname: i, 'm': j, 'f': k} for i,j,k in zip(year_values, m_values.births.values, f_values.births.values)]
			# )
		print 'Time to insert values: %r' %int((time.time() - start))
		time_df.ix[(ii+1)*chunk_size].time_insert = int((time.time() - start) * 1000)

		time_df.to_csv('/Users/nicholasharrigan/code/babyMakers/times.csv')
		ii+=1
	# connection.close()

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

# for chunk in chunker:
# 	#print 'chunk: %r' %chunk
# 	class_list = []
# 	for num in chunk:
# 		class_list.append('num '+str(num))
# 	print class_list
# 	print ''

def _create_tables(names_list, names_df):
	"""Create tables for every name in DF"""
	#Create groupby object of names
	names_gb = names_df.groupby(names_df.name)
	#Loop over batches of names and create class,write,table for each
	i = 0
	total = len(names_list)
	chunker = chunks(names_list, 1000)
	for chunk in chunker:
		start = time.time()
		class_list = []
		# 1. Create declarative based classes
		for name in chunk:
			# Name of primary key column for this tables year columns
			pk_name = name+'_ID'
			#Create classes for our tables. Note that by subclassing Base
			#sqlalchemy mapper automatically creates assoc. Table objects for us.
			class_list.append(type(str(name), (Base,), {
				'__tablename__': name,
				pk_name: Column(Integer, primary_key=True),
				'm': Column(Integer, nullable=True),
				'f': Column(Integer, nullable=True)}))
		# 2. Create tables for this batch of classes in DB
		Base.metadata.create_all(engine)
		# 3. Commit values to this batch of tables
		_populate_tables(class_list, names_gb)
		i += 1
		print str(i)+'000 out of %r' %total
		print 'Time this iteration: %r' %int((time.time() - start) * 1000)

	# NOTE: If wanted to dynamically generate columns instead then follow this:
	# http://stackoverflow.com/questions/2574105/sqlalchemy-dynamic-mapping/2575016#2575016

	#NOTE: How do we chunk table creation so don't have lots of python classes
	# in memory.
	# rewrite the variable value for the classes and call on the next chunk
	#  (ie class_dict



def _populate_tables(class_list, names_gb):
	"""Fill tables with values from DF
	class_dict: dictionary of ORM classes for each table in DB
	names_gb: groupby object of names_df"""
	# Years we will consider
	year_values = np.arange(1880,2011)
	# Loop over tables objects and assign values from csv
	for name_class in class_list:
		name = name_class.__tablename__
		#Get male and female values for this name
		m_values, f_values = _get_csv_name_vals(name, names_gb)
		pk_name = name+'_ID'
		#Generate list of row instances of our mapper classes to add
		add_list = []
		for i,j,k in zip(year_values, m_values.births.values, f_values.births.values):
			#Note: pass keywords as an unpacked dict for dyanmic pk keyword
			#add_list.append(name_class(**{pk_name: i, 'm':j, 'f': k}))
			post = name_class(**{pk_name: i, 'm':j, 'f': k})
			session.add(post)

		# #Add all rows using add_all command
		# session.add_all(add_list)
		#Force commit of all changes
	session.commit()

if __name__ == '__main__':

	#CSV path
	path = '/Users/nicholasharrigan/pydata-book-master/ch02/names/'
	#Import CSV file and put into pandas df
	print 'Importing CSV...'
	names_df = _csv_df(path)
	#WARNING! Clear db
	print 'Dropping tables...'
	_drop_tabs(session)
	#Create classes and mappings for new tables based on CSV entries
	#TODO: Modify create_tables to work with pandas df instead of simple csv
	#Get list of unique names and create tables in db with these names
	print 'Generating names list'
	names_list = names_df.name.unique()
	# names_list = ['Alan','Betty']
	print 'Creating tables...'
	_create_tables_core(names_list, names_df)
	# _create_tables(names_list, names_df)
	#Populate new tables and commit to db
	# print 'Populating tables...'
	# _populate_tables(tabs, names_df)
