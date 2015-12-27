# Imports needed
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
import pandas as pd
from sqlalchemy import *


# To start postgres server from terminal
# postgres -D /usr/local/var/postgres
#USER: test_user
#PW: testpw
#md5??? 'md52cc83a98108669b4ebbcf263ef065ab6'

engine = create_engine("postgresql://test_user:testpw@localhost/test", echo=True)
Base = declarative_base()
# TODO: does each individual table need it's own metadata
# metadata = MetaData(engine)
Session = sessionmaker(bind=engine)
session = Session()
csv = pd.DataFrame.from_csv('test.csv')
print csv

def drop_tabs(s):
	s.execute("DROP SCHEMA public CASCADE;")
	s.commit()
	s.execute("CREATE SCHEMA public;")
	s.commit()


def create_tables():

	# Create empty dict to store ORM classes
	class_dict= {}

	for name in csv.index.unique():
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

	#Create all tables we have generated mappers for
	Base.metadata.create_all(engine)
	#Return dict of classes mapped to Table objects
	return class_dict

	# NOTE: If wanted to dynamically generate columns instead then follow this:
	# http://stackoverflow.com/questions/2574105/sqlalchemy-dynamic-mapping/2575016#2575016


def populate_tables(class_dict):

	# Loop over tables objects and assign values from csv
	for name in class_dict.keys():
		#Test values to practise with...
		m_values = [3, 3]#TODO: GET LIST OF M AND F VALUES
		f_values = [3, 4]
		year_values = [1880, 1881]
		pk_name = name+'_ID'
		#Generate list of row instances of our mapper classes to add
		add_list = []
		for i,j,k in zip(year_values, m_values, f_values):
			#Note: pass keywords as an unpacked dict for dyanmic pk keyword
			add_list.append(class_dict[name](**{pk_name: i, 'm':j, 'f': k}))
		#Add all rows using add_all command
		session.add_all(add_list)
		#Force commit of all changes
		session.commit()



if __name__ == '__main__':

	#WARNING! Clear db
	drop_tabs(session)
	#Create classes and mappings for new tables based on CSV entries
	tabs = create_tables()
	#Populate new tables and commit to db
	populate_tables(tabs)
