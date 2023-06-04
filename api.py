import spotipy
import random
from constants import DATABASE_NAME, COLLECTION_NAME,AUDIO_FEATURES_LIST
from utils import getRandomCategory
from mongo import create_database, create_collection, save_song

def fetch_api(sp, client, database, iterations):
    create_database(client, DATABASE_NAME)
    create_collection(database, COLLECTION_NAME)

    collection = database[COLLECTION_NAME]

    results = fetch_songs(sp)
    for _ in range(iterations-1):
        results.extend(fetch_songs(sp))

    track_ids = [track['id'] for track in results]
    audio_features = []

    for i in range(0, len(track_ids), 100):
        batch_ids = track_ids[i:i + 100]
        batch_audio_features = sp.audio_features(batch_ids)
        audio_features.extend(batch_audio_features)

    for track, audio_feature in zip(results, audio_features):
        save_song(collection, track, audio_feature)

def fetch_songs(sp):
    """
    Spotify API does not have an option to fetch random songs, so I had to improvise
    """
    print("Fetching songs")
    limit = 50
    results = []
    characters = 'abcdefghijklmnopqrstuvwxyz'
    
    for char in characters:
        genre = getRandomCategory(sp)
        try:
            response = sp.search(q=char+'%'+ genre, type='track', limit=limit, offset=random.randint(0, 1000))
            results.extend(response['tracks']['items'])
        except spotipy.SpotifyException as e:
            continue
    print('End of fetching iteration')
    return results

def fetch_user_playlist(sp, playlist_id):
    print('Fetching user playlist')
    results = sp.playlist_tracks(playlist_id=playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    data = []
    
    for track in tracks:
        track_id = track['track']['id']
        track_uri = track['track']['uri']
        audio_features = sp.audio_features(track_uri)[0]
        data.append([audio_features[field] for field in AUDIO_FEATURES_LIST])
    
    return data, track_id

def fetch_user_track(sp, track_id):
    print('Fetching track audio features')
    track_uri = sp.track(track_id)['uri']
    audio_features = sp.audio_features(track_uri)[0]
    data = [audio_features[field] for field in AUDIO_FEATURES_LIST]
    return data, track_id