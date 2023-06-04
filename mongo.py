import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from constants import MONGO_URI

def connect_to_mongodb():
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return client

def create_database(client, database_name):
    database_names = client.list_database_names()
    if database_name not in database_names:
        client[database_name]
        print(f"Database '{database_name}' created successfully!")
    else:
        print(f"Database '{database_name}' already exists.")

def create_collection(db, collection_name):
    collection_names = db.list_collection_names()
    if collection_name not in collection_names:
        db.create_collection(collection_name)
        print(f"Collection '{collection_name}' created successfully!")
    else:
        print(f"Collection '{collection_name}' already exists.")

def check_if_song_exists(collection, song_id):
    existing_song = collection.find_one({'id': song_id})
    return existing_song is not None

def load_db(collection, id):
    print('Loading database')
    documents = collection.find({'id': {'$ne': id}})
    dict_list = list(documents)
    return pd.DataFrame(dict_list)

def remove_persisting_duplicates(collection):
    """
    Even though I check all the ids before inserting a song into the db, there are sometimes same songs(same song name + 
    same song artist) with different ids on Spotify, so I remove duplicates by aggregating those two values, otherwise
    user would sometimes get multiple same recommendations
    """
    print('Removing duplicates')
    pipeline = [
        {
            '$group': {
                '_id': {
                    'name': '$name',
                    'artist': '$artist'
                },
                'duplicates': {'$push': '$_id'},
                'count': {'$sum': 1}
            }
        },
        {
            '$match': {
                'count': {'$gt': 1}
            }
        }
    ]

    duplicate_docs = collection.aggregate(pipeline)
    for duplicate in duplicate_docs:
        duplicate_ids = duplicate['duplicates']
        collection.delete_many({'_id': {'$in': duplicate_ids[1:]}})



def save_song(collection, track, audio_feature):
    if audio_feature is None:
        return

    song_data = {
        'id': track['id'],
        'name': track['name'],
        'artist': track['artists'][0]['name']
    }

    audio_features_list = [
        'danceability', 'energy', 'key', 'loudness', 'mode',
        'speechiness', 'acousticness', 'instrumentalness',
        'liveness', 'valence', 'tempo'
    ]

    for feature in audio_features_list:
        if audio_feature and isinstance(audio_feature, dict):
            value = audio_feature.get(feature)
            song_data[feature] = value

    # Add song_data to the collection
    if check_if_song_exists(collection, song_data['id']):
        print(f"{track['name']} - {track['artists'][0]['name']} already exists in the database.")
    else:
        collection.insert_one(song_data)
        print(f"Stored {track['name']} - {track['artists'][0]['name']} in MongoDB.")