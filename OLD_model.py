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

def create_tables():

	# Create empty dict to store ORM classes
	class_dict= {}
	# Iterate over names in CSV
	# For each name (iteration):
	# for name in csv.index.unique():
	# 	# Name of primary key column for this tables year columns
	# 	pk_name = name+'_ID'
	# 	# Create Table object with required metadata (columns= M F)
	# 	tab = Table(str(name), metadata,
	# 		# TODO: USE AUTOINCREMENT WITH AN OFFSET TO INITIALISE YEARS
	# 		Column(pk_name,
	# 			Integer,
	# 			#Sequence(seq_name, start=1880, increment=1, optional=True),
	# 			primary_key=True),
	# 		Column('m', Integer, nullable=True),
	# 		Column('f', Integer, nullable=True))
	# 	# Use type to create ORM object and append to dict with name as key
	# 	class_dict[name] = type(str(name), (Base,), dict(__table__=tab))

	for name in csv.index.unique():
		# Name of primary key column for this tables year columns
		pk_name = name+'_ID'
		# Create Table object with required metadata (columns= M F)
		# tab = Table(str(name), metadata,
		# 	# TODO: USE AUTOINCREMENT WITH AN OFFSET TO INITIALISE YEARS
		# 	Column(pk_name,
		# 		Integer,
		# 		#Sequence(seq_name, start=1880, increment=1, optional=True),
		# 		primary_key=True),
		# 	Column('m', Integer, nullable=True),
		# 	Column('f', Integer, nullable=True))
		# # Use type to create ORM object and append to dict with name as key
		class_dict[name] = type(str(name), (Base,), dict(
			__tablename__=name,
			id = Column(Integer, primary_key=True),
			m = Column(Integer, nullable=True),
			f = Column(Integer, nullable=True)))
		print 'CREATE....'
		Base.metadata.create_all(engine)
		print 'DDDONNEE'



	return class_dict

	# NOTE: If wanted to dynamically generate columns instead then follow this:
	# http://stackoverflow.com/questions/2574105/sqlalchemy-dynamic-mapping/2575016#2575016


#def create_tables():

def populate_tables(class_dict):



	# Loop over tables objects and assign values form csv using core
	for name in class_dict.keys():
		# print 'this'
		# print session.query(class_dict[name].__table__).column_descriptions
		m_values = [3, 3]#TODO: GET LIST OF M AND F VALUES
		f_values = [3, 4]
		year_values = [1880, 1881]
		pk_name = name+'_ID'
		engine.execute(
			class_dict[name].__table__.insert(),
			[{'Betty_ID': i, 'm': j, 'f': k} for i,j,k in zip(year_values, m_values, f_values)]
#			[{'year': ,'m': ,'f':} for i in zip(xrange(1880,2011,1), m_values, f_values)}]
		)

	# print session.query(class_dict['Alan'].__table__).all()







if __name__ == '__main__':

	c_d = create_tables()

	# populate_tables(c_d)



	# 	# Creates db
	#   load the data into the tables
	#
	# def create_sess():
	# 	# Creates session for connecting to db

	#TODO: Import CSV into db
