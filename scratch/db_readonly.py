from pymongo import MongoClient
from pymongo.errors import PyMongoError
try:
 c=MongoClient('mongodb://127.0.0.1:27017/',serverSelectionTimeoutMS=1500)
 print(c.admin.command('ping'))
 d=c['weather_analytics']; print('collections',d.list_collection_names())
 for n in ('weather_observations','ingestion_runs'):
  col=d[n]; print(n,'count',col.count_documents({}))
  if n=='weather_observations':
   print('cities',col.distinct('city')); print('sample',col.find_one({}, {'_id':0,'city':1,'timestamp':1,'temperature_c':1,'precipitation_mm':1}))
except Exception as e: print(type(e).__name__,str(e)[:300])
