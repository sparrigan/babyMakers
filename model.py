# Imports needed
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
from sqlalchemy import *



# To start postgres server from terminal
# postgres -D /usr/local/var/postgres
#USER: test_user
#PW: testpw
#md5??? 'md52cc83a98108669b4ebbcf263ef065ab6'

engine = create_engine("postgresql://test_user:testpw@localhost/test", echo=True)
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

# Create empty dict to store ORM classes
class_dict = {}

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

def _create_tables(names_list):
	"""Create tables for every name in DF"""
	#Loop over names and create table for each
	i = 0
	total = len(names_list)
	for name in names_list:
		#TODO: Drop all tables we might want to make here in case exist
		# Name of primary key column for this tables year columns
		pk_name = name+'_ID'
		#Create classes for our tables. Note that by subclassing Base
		#sqlalchemy mapper automatically creates assoc. Table objects for us.
		class_dict[name] = type(str(name), (Base,), {
			'__tablename__': name,
			pk_name: Column(Integer, primary_key=True),
			'm': Column(Integer, nullable=True),
			'f': Column(Integer, nullable=True)})
		if (i%1000 == 0):
			print '%r of %r' %(i, total)
		i += 1

	#Create all tables we have generated mappers for
	Base.metadata.create_all(engine)
	#Return dict of classes mapped to Table objects
	return class_dict

	# NOTE: If wanted to dynamically generate columns instead then follow this:
	# http://stackoverflow.com/questions/2574105/sqlalchemy-dynamic-mapping/2575016#2575016

	#NOTE: How do we chunk table creation so don't have lots of python classes
	# in memory.
	# rewrite the variable value for the classes and call on the next chunk
	#  (ie class_dict



def _populate_tables(class_dict, names_df):
	"""Fill tables with values from DF
	class_dict: dictionary of ORM classes for each table in DB"""
	# Group names_df by name
	names_gb = names_df.groupby(names_df.name)
	year_values = np.arange(1880,2011)
	# Loop over tables objects and assign values from csv
	i=0
	total = len(class_dict.keys())
	for name in class_dict.keys():
		#Get male and female values for this name
		m_values, f_values = _get_csv_name_vals(name, names_gb)
		#Test values to practise with...
		# m_values = [3, 3]#TODO: GET LIST OF M AND F VALUES
		# f_values = [3, 4]
		# year_values = [1880, 1881]
		pk_name = name+'_ID'
		#Generate list of row instances of our mapper classes to add
		add_list = []
		for i,j,k in zip(year_values, m_values.births.values, f_values.births.values):
			#Note: pass keywords as an unpacked dict for dyanmic pk keyword
			add_list.append(class_dict[name](**{pk_name: i, 'm':j, 'f': k}))
		#Add all rows using add_all command
		session.add_all(add_list)
		#Force commit of all changes
		session.commit()
		if (i%1000 == 0):
			print '%r of %r' %(i, total)

# class test_class(Base):
# 	__tablename__ = 'test_tab'
# 	id = Column(Integer, primary_key=True)
# 	la = Column(Integer)
#
# test_class2 = type('test_class2', (Base,), {
# 	'__tablename__': 'test_tab2',
# 	'id': Column(Integer, primary_key=True),
# 	'ra': Column(Integer, nullable=True)})
#
#
# def test():
# 	ttt = session.query(test_class).filter_by(id=2).first()
# 	print ttt.la
#
# def test2():
# 	ttt2 = session.query(test_class2).filter_by(id=2).first()
# 	print ttt2.ra

# def test_reflect()


if __name__ == '__main__':

	# _drop_tabs(session)
	#
	# Base.metadata.create_all(engine)
	# aa = test_class(id=1, la=10)
	# bb = test_class(id=2, la=20)
	# session.add_all([aa,bb])
	# session.commit()
	#
	# aaa = test_class2(id=1, ra=100)
	# bbb = test_class2(id=2, ra=200)
	# session.add_all([aaa,bbb])
	# session.commit()

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
	#names_list = names_df.name.unique()
	names_list = ['Alan','Betty']
	print 'Creating tables...'
	tabs = _create_tables(names_list)
	#Populate new tables and commit to db
	print 'Populating tables...'
	_populate_tables(tabs, names_df)
