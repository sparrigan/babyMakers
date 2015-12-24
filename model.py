# Imports needed
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
import pandas as pd
from sqlalchemy import *

ENGINE = create_engine("sqlite:///allYourDatabaseAreBelongToMeme.db", echo=False)
Base = declarative_base()
# TODO: does each individual table need it's own metadata
metadata = MetaData()

def create_tables():


csv = pd.DataFrame.from_csv('test.csv')
print csv
# Create empty dict to store ORM classes
class_dict = {}
# Iterate over names in CSV
# For each name (iteration):
for name in csv.index.unique():
	# Create Table object with required metadata (columns= M F)
	tab = Table(str(name), metadata,
		Column('year', Integer, primary_key=True),
		Column('m', Integer, nullable=True),
		Column('f', Integer, nullable=True))
	# Use type to create ORM object and append to dict with name as key
	class_dict[name] = type(str(name), (Base,), dict(__table__=tab))

# NOTE: If wanted to dynamically generate columns instead then follow this:
# http://stackoverflow.com/questions/2574105/sqlalchemy-dynamic-mapping/2575016#2575016




if __name__ == '__main__':
	create_tables()

	# 	# Creates db
	#   load the data into the tables
	#
	# def create_sess():
	# 	# Creates session for connecting to db

	#TODO: Import CSV into db
