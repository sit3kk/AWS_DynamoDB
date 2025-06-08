import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from decimal import Decimal
import time

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
client = boto3.client('dynamodb', region_name='eu-north-1')

def setup_tables():
    """Setup tables for music app"""
    
    # Users table
    try:
        table = dynamodb.create_table(
            TableName='Users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'email-index',
                'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Users table created")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Users table exists")
        else:
            print(f"Error: {e}")

    # Playlists
    try:
        table = dynamodb.create_table(
            TableName='Playlists',
            KeySchema=[{'AttributeName': 'playlist_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'playlist_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'user-playlists-index',
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Playlists table created")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Playlists table exists")

    # Listening history
    try:
        table = dynamodb.create_table(
            TableName='UserListeningHistory',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("History table created")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("History table exists")

    # Artists table  
    try:
        table = dynamodb.create_table(
            TableName='Artists',
            KeySchema=[{'AttributeName': 'artist_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'artist_id', 'AttributeType': 'S'},
                {'AttributeName': 'genre', 'AttributeType': 'S'},
                {'AttributeName': 'popularity_score', 'AttributeType': 'N'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'genre-popularity-index',
                'KeySchema': [
                    {'AttributeName': 'genre', 'KeyType': 'HASH'},
                    {'AttributeName': 'popularity_score', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Artists table created")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Artists table exists")

    # Concerts
    try:
        table = dynamodb.create_table(
            TableName='Concerts',
            KeySchema=[{'AttributeName': 'concert_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'concert_id', 'AttributeType': 'S'},
                {'AttributeName': 'city', 'AttributeType': 'S'},
                {'AttributeName': 'date', 'AttributeType': 'S'},
                {'AttributeName': 'artist_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'city-date-index',
                    'KeySchema': [
                        {'AttributeName': 'city', 'KeyType': 'HASH'},
                        {'AttributeName': 'date', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'artist-concerts-index',
                    'KeySchema': [{'AttributeName': 'artist_id', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Concerts table created")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Concerts table exists")

    # Music
    try:
        table = dynamodb.create_table(
            TableName='Music',
            KeySchema=[
                {'AttributeName': 'Artist', 'KeyType': 'HASH'},
                {'AttributeName': 'SongTitle', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'Artist', 'AttributeType': 'S'},
                {'AttributeName': 'SongTitle', 'AttributeType': 'S'},
                {'AttributeName': 'genre', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'genre-index',
                'KeySchema': [{'AttributeName': 'genre', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Music table created")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Music table exists")

def wait_for_tables():
    tables = ['Users', 'Playlists', 'UserListeningHistory', 'Artists', 'Concerts', 'Music']
    for name in tables:
        try:
            table = dynamodb.Table(name)
            table.wait_until_exists()
            print(f"{name} ready")
        except Exception as e:
            print(f"Warning: {name} - {e}")

def add_test_data():
    # Users
    users_table = dynamodb.Table('Users')
    users = [
        {
            'user_id': 'user_001',
            'email': 'john.doe@example.com',
            'username': 'johndoe',
            'subscription_type': 'premium',
            'created_at': '2024-01-15T10:30:00Z',
            'preferences': {
                'favorite_genres': ['rock', 'pop', 'jazz'],
                'language': 'en'
            },
            'following_artists': ['artist_001', 'artist_002']
        },
        {
            'user_id': 'user_002',
            'email': 'jane.smith@example.com',
            'username': 'janesmith',
            'subscription_type': 'free',
            'created_at': '2024-02-20T14:45:00Z',
            'preferences': {
                'favorite_genres': ['classical', 'ambient'],
                'language': 'en'
            },
            'following_artists': ['artist_003']
        }
    ]
    
    for user in users:
        users_table.put_item(Item=user)
    print("Added users")

    # Artists
    artists_table = dynamodb.Table('Artists')
    artists = [
        {
            'artist_id': 'artist_001',
            'name': 'The Beatles',
            'genre': 'rock',
            'popularity_score': 95,
            'country': 'United Kingdom',
            'formed_year': 1960,
            'followers': 50000000
        },
        {
            'artist_id': 'artist_002',
            'name': 'Pink Floyd',
            'genre': 'rock',
            'popularity_score': 92,
            'country': 'United Kingdom',
            'formed_year': 1965,
            'followers': 35000000
        },
        {
            'artist_id': 'artist_003',
            'name': 'Mozart',
            'genre': 'classical',
            'popularity_score': 88,
            'country': 'Austria',
            'formed_year': 1756,
            'followers': 15000000
        }
    ]
    
    for artist in artists:
        artists_table.put_item(Item=artist)
    print("Added artists")

    # Music
    music_table = dynamodb.Table('Music')
    songs = [
        {
            'Artist': 'The Beatles',
            'SongTitle': 'Hey Jude',
            'album': 'The Beatles 1967-1970',
            'duration': 431,
            'genre': 'rock',
            'release_year': 1968,
            'play_count': 150000,
            'artist_id': 'artist_001'
        },
        {
            'Artist': 'Pink Floyd',
            'SongTitle': 'Comfortably Numb',
            'album': 'The Wall',
            'duration': 382,
            'genre': 'rock',
            'release_year': 1979,
            'play_count': 89000,
            'artist_id': 'artist_002'
        }
    ]
    
    for song in songs:
        music_table.put_item(Item=song)
    print("Added music")

    # Concerts
    concerts_table = dynamodb.Table('Concerts')
    concerts = [
        {
            'concert_id': 'concert_001',
            'artist_id': 'artist_001',
            'artist_name': 'The Beatles',
            'city': 'London',
            'venue': 'Wembley Stadium',
            'date': '2025-07-15',
            'ticket_price': Decimal('150.00'),
            'capacity': 90000,
            'tickets_sold': 87500,
            'status': 'upcoming'
        }
    ]
    
    for concert in concerts:
        concerts_table.put_item(Item=concert)
    print("Added concerts")

    # Listening history
    history_table = dynamodb.Table('UserListeningHistory')
    now = datetime.now()
    history = [
        {
            'user_id': 'user_001',
            'timestamp': (now - timedelta(hours=2)).isoformat(),
            'artist': 'The Beatles',
            'song_title': 'Hey Jude',
            'artist_id': 'artist_001',
            'duration_listened': 431,
            'completed': True,
            'device': 'mobile'
        },
        {
            'user_id': 'user_001',
            'timestamp': (now - timedelta(hours=1)).isoformat(),
            'artist': 'Pink Floyd',
            'song_title': 'Comfortably Numb',
            'artist_id': 'artist_002',
            'duration_listened': 200,
            'completed': False,
            'device': 'web'
        }
    ]
    
    for record in history:
        history_table.put_item(Item=record)
    print("Added history")

def get_user_playlists(user_id):
    table = dynamodb.Table('Playlists')
    try:
        response = table.query(
            IndexName='user-playlists-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        print(f"Playlists for {user_id}:")
        for playlist in response['Items']:
            print(f"  {playlist['name']}")
        return response['Items']
    except ClientError as e:
        print(f"Error: {e}")
        return []

def get_listening_history(user_id, limit=10):
    table = dynamodb.Table('UserListeningHistory')
    try:
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False,
            Limit=limit
        )
        print(f"Recent history for {user_id}:")
        for record in response['Items']:
            status = "Complete" if record['completed'] else "Partial"
            print(f"  {record['artist']} - {record['song_title']} [{status}]")
        return response['Items']
    except ClientError as e:
        print(f"Error: {e}")
        return []

def search_by_genre(genre):
    table = dynamodb.Table('Music')
    try:
        response = table.scan(
            FilterExpression=Attr('genre').eq(genre),
            ProjectionExpression='Artist, SongTitle, play_count'
        )
        print(f"Songs in {genre}:")
        for song in response['Items']:
            print(f"  {song['Artist']} - {song['SongTitle']} ({song['play_count']} plays)")
        return response['Items']
    except ClientError as e:
        print(f"Error: {e}")
        return []

def update_play_count(artist, song_title):
    table = dynamodb.Table('Music')
    try:
        response = table.update_item(
            Key={'Artist': artist, 'SongTitle': song_title},
            UpdateExpression='ADD play_count :val',
            ExpressionAttributeValues={':val': 1},
            ReturnValues='UPDATED_NEW'
        )
        print(f"Updated {artist} - {song_title}, new count: {response['Attributes']['play_count']}")
    except ClientError as e:
        print(f"Error: {e}")

def batch_get_songs(song_keys):
    try:
        response = client.batch_get_item(
            RequestItems={
                'Music': {
                    'Keys': [
                        {'Artist': {'S': key['Artist']}, 'SongTitle': {'S': key['SongTitle']}}
                        for key in song_keys
                    ]
                }
            }
        )
        print("Batch results:")
        for item in response['Responses']['Music']:
            artist = item['Artist']['S']
            title = item['SongTitle']['S']
            duration = item.get('duration', {}).get('N', 'Unknown')
            print(f"  {artist} - {title} ({duration}s)")
        return response['Responses']['Music']
    except ClientError as e:
        print(f"Error: {e}")
        return []

def get_top_artists(genre, limit=5):
    table = dynamodb.Table('Artists')
    try:
        response = table.query(
            IndexName='genre-popularity-index',
            KeyConditionExpression=Key('genre').eq(genre),
            ScanIndexForward=False,
            Limit=limit
        )
        print(f"Top {limit} {genre} artists:")
        for artist in response['Items']:
            print(f"  {artist['name']}: {artist['popularity_score']} pts ({artist['followers']:,} followers)")
        return response['Items']
    except ClientError as e:
        print(f"Error: {e}")
        return []

def get_concerts_in_city(city):
    table = dynamodb.Table('Concerts')
    try:
        response = table.query(
            IndexName='city-date-index',
            KeyConditionExpression=Key('city').eq(city)
        )
        print(f"Concerts in {city}:")
        for concert in response['Items']:
            status = "Available" if concert['status'] == 'upcoming' else "Sold out"
            print(f"  {concert['artist_name']} at {concert['venue']} ({concert['date']}) - {status}")
        return response['Items']
    except ClientError as e:
        print(f"Error: {e}")
        return []

def get_artist_concerts(artist_id):
    table = dynamodb.Table('Concerts')
    try:
        response = table.query(
            IndexName='artist-concerts-index',
            KeyConditionExpression=Key('artist_id').eq(artist_id)
        )
        print(f"Concerts for {artist_id}:")
        for concert in response['Items']:
            print(f"  {concert['city']} - {concert['venue']} ({concert['date']})")
        return response['Items']
    except ClientError as e:
        print(f"Error: {e}")
        return []

def run_tests():
    print("Setting up tables...")
    setup_tables()
    
    print("Waiting for tables...")
    time.sleep(5)
    wait_for_tables()
    
    print("Adding test data...")
    add_test_data()
    
    print("\n" + "="*40)
    print("Running queries...")
    
    get_user_playlists('user_001')
    print("-" * 20)
    
    get_listening_history('user_001')
    print("-" * 20)
    
    search_by_genre('rock')
    print("-" * 20)
    
    update_play_count('The Beatles', 'Hey Jude')
    print("-" * 20)
    
    songs = [
        {'Artist': 'The Beatles', 'SongTitle': 'Hey Jude'},
        {'Artist': 'Pink Floyd', 'SongTitle': 'Comfortably Numb'}
    ]
    batch_get_songs(songs)
    print("-" * 20)
    
    get_top_artists('rock')
    print("-" * 20)
    
    get_concerts_in_city('London')
    print("-" * 20)
    
    get_artist_concerts('artist_001')
    
    print("\nDone!")

if __name__ == "__main__":
    run_tests()
