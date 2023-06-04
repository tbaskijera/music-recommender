# https://github.com/tbaskijera/music-recommender
import spotipy
import argparse
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from constants import DATABASE_NAME, COLLECTION_NAME, CLIENT_ID, CLIENT_SECRET, AUDIO_FEATURES_LIST
from mongo import connect_to_mongodb, load_db, remove_persisting_duplicates
from api import fetch_api, fetch_user_playlist

def main():

    client = connect_to_mongodb()
    database = client[DATABASE_NAME]
    collection = database[COLLECTION_NAME]

    client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    fetch = args.fetch
    if fetch:
        fetch_api(sp, client, database, args.iterations)
        remove_persisting_duplicates(collection)  

    # To get playlist id from spotify app, click share and copy the string inside playlist/...?
    # example: https://open.spotify.com/user/tbaski/playlist/45tyEi7AhkJeLQ6RWTxGqd?si=lkALLKMiTy-jCCQS3rko4A
    playlist_id = args.playlist
    user_playlist_data, track_id = fetch_user_playlist(sp, playlist_id)
    user_features = pd.DataFrame(user_playlist_data, columns=AUDIO_FEATURES_LIST)
    
    db_dataset = load_db(collection, track_id)
    db_dataset_features = db_dataset.drop(columns=['_id', 'id', 'name', 'artist'])

    scaler = MinMaxScaler()
    scaled_user_features = scaler.fit_transform(user_features)
    scaled_db_dataset_features = scaler.transform(db_dataset_features)

    weights = [1.0, 1.5, 0.8, 1.2, 1.0, 0.5, 0.7, 0.5, 0.8, 1.2, 1.0]
    weighted_user_features = scaled_user_features * weights
    weighted_db_dataset_features = scaled_db_dataset_features * weights

    similarity_scores = cosine_similarity(weighted_user_features, weighted_db_dataset_features)
    db_dataset['similarity'] = similarity_scores[0]

    print("Recommendations:")
    recommendations = db_dataset.sort_values(by='similarity', ascending=False).head(10)
    print(recommendations[['name', 'artist', 'similarity']])

    client.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-fetch', type=bool, default = False, help='Fetch new songs or not (default = False)')
    parser.add_argument('-iterations', type=int, default=1, help='Number of times to fetch songs (default = 1)')
    parser.add_argument('-playlist', type=str, default='62vZL7XfkRNEd8K6wjGABT', help='Playlist id') # 45tyEi7AhkJeLQ6RWTxGqd


    args = parser.parse_args()
    main()