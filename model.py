# Imports needed
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
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

#Connect to DB with SQLA
engine = create_engine("postgresql://test_user:testpw@localhost/test", echo=False)
Base = declarative_base(engine)
Session = sessionmaker(bind=engine)
session = Session()

year_vals = np.arange(1880,2011)

# def chunks(l, n):
#     """Yield successive n-sized chunks from l."""
#     for i in xrange(0, len(l), n):
#         yield l[i:i+n]

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
	#TODO: Add alternate that deletes each table individually if too many locks

def _insert_all_rows(names_df, chunk_size):
	"""Inserts rows into male and female tables for each name"""
	#Get list of names (each form a record) for DB from pandas DF
	names_list = names_df.name.unique()
	#Groupby dataframe for easy access to each names time series
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
		# if  (i == chunk_size):
		# 	session.execute(insert_string)
		# 	session.commit()
		# 	i += 1

def get_name_data(name, sex):
	if sex in ['m', 'M', 'male', 'Male']:
		qry = session.query(Male).filter_by(name=name)
		if qry.first():
			return qry.first().__dict__
		else:
			return None
	elif sex in ['f', 'F', 'female', 'Female']:
		qry = session.query(Female).filter_by(name=name)
		if qry.first():
			return qry.first().__dict__
		else:
			return None
	#Code to get ordered list (by year) instead of dict
	#q_dict = qry.first().__dict__
	#[q_dict['col'+str(yr)] for yr in range(1880,2011)]

#Create classes for male and female tables
col_dic_m = {'__tablename__': 'male', 'name': Column('name', String(32), primary_key=True)}
col_dic_f = {'__tablename__': 'female', 'name': Column('name', String(32), primary_key=True)}
for year in year_vals:
	col_dic_m['col'+str(year)] = Column(str(year), Integer)
	col_dic_f['col'+str(year)] = Column(str(year), Integer)
Male = type('Male', (Base,), col_dic_m)
Female = type('Female', (Base,), col_dic_f)
# TODO: Could optimize by only creating m/f class when m/f requested


if __name__ == '__main__':
	#WARNING! Clear db
	# print 'Dropping tables...'
	# _drop_tabs(session)

	#Create corresponding tables in database
	Base.metadata.create_all(engine)

	#Import CSV data in pandas DF
	#CSV path
	path = '/Users/nicholasharrigan/pydata-book-master/ch02/names/'
	print 'Importing CSV...'
	names_df = _csv_df(path)

	#Insert rows
	print 'Inserting rows'
	_insert_all_rows(names_df, 0)
