Szczegółowe wyjaśnienie implementacji aplikacji muzycznej w DynamoDB.

## Spis treści

1. [Architektura ogólna](#architektura-ogólna)
2. [Konfiguracja połączenia](#konfiguracja-połączenia)
3. [Definicje tabel](#definicje-tabel)
4. [Funkcje główne](#funkcje-główne)
5. [Wzorce zapytań](#wzorce-zapytań)
6. [Najlepsze praktyki](#najlepsze-praktyki)
7. [Zarządzanie przez AWS CLI](#zarządzanie-przez-aws-cli)

## Architektura ogólna

Aplikacja implementuje model danych dla serwisu muzycznego. Wykorzystuje następujące koncepcje DynamoDB:

- **Single Table Design** - gdzie to możliwe
- **Global Secondary Indexes (GSI)** - dla alternatywnych wzorców dostępu
- **Composite Keys** - dla hierarchicznych relacji
- **Sparse Indexes** - dla opcjonalnych pól

## Konfiguracja połączenia

```python
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Resource API - wyższego poziomu, łatwiejsze w użyciu
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')

# Client API - niższego poziomu, pełna kontrola
client = boto3.client('dynamodb', region_name='eu-north-1')
```

**Dlaczego dwa API?**

- **Resource API**: Prostsze operacje CRUD, automatyczna konwersja typów
- **Client API**: Zaawansowane operacje jak batch_get_item, pełna kontrola

## Definicje tabel

### 1. Tabela Users

```python
TableName='Users',
KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
GlobalSecondaryIndexes=[{
    'IndexName': 'email-index',
    'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
    'Projection': {'ProjectionType': 'ALL'}
}]
```

**Wzorzec dostępu**:

- Główny: Pobierz użytkownika po `user_id`
- GSI: Znajdź użytkownika po `email` (logowanie)

**Dlaczego GSI?**

- Email jest unikalny ale nie jest kluczem głównym
- Pozwala na szybkie wyszukiwanie podczas logowania

### 2. Tabela Music (Composite Key)

```python
KeySchema=[
    {'AttributeName': 'Artist', 'KeyType': 'HASH'},      # Partition Key
    {'AttributeName': 'SongTitle', 'KeyType': 'RANGE'}   # Sort Key
]
```

**Wzorce dostępu**:

- Pobierz konkretny utwór: `Artist = "Beatles" AND SongTitle = "Hey Jude"`
- Wszystkie utwory artysty: `Artist = "Beatles"`
- Utwory z gatunku: GSI `genre-index`

**Zalety klucza złożonego**:

- Naturalne grupowanie utworów według artysty
- Wydajne zapytania typu "wszystkie utwory artysty"
- Unikalna identyfikacja bez sztucznych ID

### 3. Tabela UserListeningHistory (Time Series)

```python
KeySchema=[
    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
]
```

**Wzorce dostępu**:

- Historia użytkownika: `user_id = "user_001"`
- Ostatnie odtworzenia: `user_id = "user_001"` + `ScanIndexForward=False`
- Zakres czasowy: `user_id = "user_001" AND timestamp BETWEEN t1 AND t2`

**Time Series Pattern**:

- Klucz partycji grupuje po użytkowniku
- Klucz sortujący chronologicznie porządkuje wpisy
- Auto-expire można zaimplementować przez TTL

### 4. Tabela Artists z indeksem złożonym

```python
GlobalSecondaryIndexes=[{
    'IndexName': 'genre-popularity-index',
    'KeySchema': [
        {'AttributeName': 'genre', 'KeyType': 'HASH'},
        {'AttributeName': 'popularity_score', 'KeyType': 'RANGE'}
    ]
}]
```

**Wzorce dostępu**:

- Top artyści z gatunku: `genre = "rock"` + sortowanie po `popularity_score`
- Filtrowanie po zakresie popularności
- Ranking artystów w kategoriach

## Funkcje główne

### 1. setup_tables() - Tworzenie infrastruktury

```python
def setup_tables():
    try:
        table = dynamodb.create_table(...)
        print("Table created")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Table exists")
```

**Wzorzec idempotentny**:

- Funkcja może być uruchomiona wielokrotnie
- Graceful handling istniejących tabel
- Nie przerywa procesu przy duplikatach

### 2. wait_for_tables() - Synchronizacja

```python
def wait_for_tables():
    for name in tables:
        table = dynamodb.Table(name)
        table.wait_until_exists()
```

**Dlaczego potrzebne?**

- Tworzenie tabel w DynamoDB jest asynchroniczne
- GSI mogą być w stanie CREATING przez kilka minut
- Operacje na niepełnych tabelach mogą się nie powieść

### 3. add_test_data() - Dane testowe

```python
def add_test_data():
    users_table = dynamodb.Table('Users')
    for user in users:
        users_table.put_item(Item=user)
```

**Wzorce danych**:

- Nested objects dla preferencji użytkownika
- Lists dla wielowartościowych pól
- Decimal dla precyzyjnych liczb (ceny)
- ISO timestamps dla dat

## Wzorce zapytań

### 1. Query vs Scan

```python
# QUERY - wydajne, używa indeksów
response = table.query(
    KeyConditionExpression=Key('user_id').eq('user_001')
)

# SCAN - kosztowne, przegląda całą tabelę
response = table.scan(
    FilterExpression=Attr('genre').eq('rock')
)
```

**Kiedy używać Query**:

- Znasz klucz partycji
- Potrzebujesz wydajności
- Pracujesz z dużymi tabelami

**Kiedy używać Scan**:

- Adhoc analytics
- Małe tabele
- Nie masz indeksu dla wzorca dostępu

### 2. GSI Queries

```python
# Query na GSI
response = table.query(
    IndexName='genre-popularity-index',
    KeyConditionExpression=Key('genre').eq('rock'),
    ScanIndexForward=False,  # Sortowanie descending
    Limit=5
)
```

**Zalety GSI**:

- Alternatywne klucze dostępu
- Różne sortowanie niż w tabeli głównej
- Sparse indexing (tylko rekordy z atrybutem)

### 3. Batch Operations

```python
# Batch Get - pobieranie wielu rekordów jednym zapytaniem
response = client.batch_get_item(
    RequestItems={
        'Music': {
            'Keys': [
                {'Artist': {'S': 'Beatles'}, 'SongTitle': {'S': 'Hey Jude'}}
            ]
        }
    }
)
```

**Kiedy używać**:

- Pobieranie wielu rekordów o znanych kluczach
- Redukcja liczby round-tripów do AWS
- Limit: 100 rekordów lub 16MB na request

### 4. Update Operations

```python
# Atomic increment
response = table.update_item(
    Key={'Artist': artist, 'SongTitle': song_title},
    UpdateExpression='ADD play_count :val',
    ExpressionAttributeValues={':val': 1},
    ReturnValues='UPDATED_NEW'
)
```

**Wzorce Update**:

- **ADD**: Atomiczne incrementy/decrementy
- **SET**: Ustawianie wartości
- **REMOVE**: Usuwanie atrybutów
- **LIST APPEND**: Dodawanie do list

## Najlepsze praktyki

### 1. Error Handling

```python
try:
    # DynamoDB operation
    response = table.get_item(Key={'id': 'test'})
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'ResourceNotFoundException':
        print("Table doesn't exist")
    elif error_code == 'ThrottlingException':
        print("Rate limited - implement backoff")
```

**Główne błędy**:

- **ResourceNotFoundException**: Tabela nie istnieje
- **ThrottlingException**: Przekroczenie limitów RCU/WCU
- **ValidationException**: Nieprawidłowe parametry
- **ConditionalCheckFailedException**: Warunek nie spełniony

### 2. Efficient Data Modeling

```python
# ✅ Dobry wzorzec - composite key
{
    'Artist': 'Beatles',
    'SongTitle': 'Hey Jude',
    'album': 'The Beatles 1967-1970'
}

# ❌ Anty-wzorzec - brak klucza sortującego
{
    'song_id': 'uuid-random-string',
    'artist': 'Beatles',
    'title': 'Hey Jude'
}
```

**Dlaczego composite keys są lepsze**:

- Naturalne grupowanie danych
- Mniej GSI potrzebnych
- Wydajniejsze zapytania zakresu
- Lepsze wykorzystanie partycji

### 3. Index Strategy

```python
# GSI dla częstych wzorców dostępu
'genre-popularity-index'  # Artyści per gatunek, sortowani po popularności
'user-playlists-index'    # Playlisty użytkownika
'city-date-index'         # Koncerty w mieście po dacie
```

**Zasady GSI**:

- Projektuj pod konkretne queries
- Unikaj hot partitions
- Sparse indexes dla opcjonalnych danych
- Monitor costs - GSI kosztują dodatkowo

### 4. Data Types

```python
# Decimal dla pieniędzy (nie float!)
'ticket_price': Decimal('150.00')

# String Sets dla tagów
'tags': {'rock', 'classic', '60s'}

# Maps dla zagnieżdżonych obiektów
'preferences': {
    'favorite_genres': ['rock', 'pop'],
    'language': 'en'
}
```

**Kiedy używać każdego typu**:

- **String**: Identyfikatory, tekst
- **Number**: Countery, scores, rankings
- **Decimal**: Ceny, precyzyjne kalkulacje
- **Boolean**: Flagi, status
- **List**: Ordered collections
- **Set**: Unique collections
- **Map**: Nested objects

## Wzorce wydajności

### 1. Hot Partition Avoidance

```python
# ❌ Hot partition - wszyscy użytkownicy w jednej partycji
{
    'entity_type': 'USER',  # Wszyscy mają to samo
    'user_id': 'user_001'
}

# ✅ Dobrze rozłożone partycje
{
    'user_id': 'user_001',  # Naturalnie rozproszone
    'timestamp': '2024-01-15T10:30:00Z'
}
```

### 2. Read Patterns

```python
# Eventually Consistent Reads (default) - tańsze, szybsze
response = table.get_item(Key={'id': 'test'})

# Strongly Consistent Reads - droższe, ale aktualne
response = table.get_item(
    Key={'id': 'test'},
    ConsistentRead=True
)
```

### 3. Projection Types

```python
# KEYS_ONLY - tylko klucze
'Projection': {'ProjectionType': 'KEYS_ONLY'}

# INCLUDE - wybrane atrybuty
'Projection': {
    'ProjectionType': 'INCLUDE',
    'NonKeyAttributes': ['name', 'genre']
}

# ALL - wszystkie atrybuty (droższe)
'Projection': {'ProjectionType': 'ALL'}
```

## Debugowanie i monitoring

### 1. CloudWatch Metrics

- **ConsumedReadCapacityUnits**: Wykorzystanie RCU
- **ConsumedWriteCapacityUnits**: Wykorzystanie WCU
- **ThrottledRequests**: Zablokowane zapytania
- **SystemErrors**: Błędy po stronie AWS

### 2. Lokalne debugowanie

```python
# Szczegółowe logi boto3
import logging
boto3.set_stream_logger('boto3', logging.DEBUG)

# Response inspection
response = table.query(...)
print(f"Consumed Capacity: {response.get('ConsumedCapacity')}")
print(f"Scanned Count: {response.get('ScannedCount')}")
print(f"Count: {response.get('Count')}")
```

### 3. Performance tuning

```python
# Limit dla kontroli kosztów
response = table.query(
    KeyConditionExpression=Key('user_id').eq('user_001'),
    Limit=50,  # Maksymalnie 50 rekordów
    ScanIndexForward=False  # Najnowsze pierwsze
)

# Pagination dla dużych wyników
last_key = None
while True:
    kwargs = {'KeyConditionExpression': Key('user_id').eq('user_001')}
    if last_key:
        kwargs['ExclusiveStartKey'] = last_key

    response = table.query(**kwargs)
    # Process items...

    last_key = response.get('LastEvaluatedKey')
    if not last_key:
        break
```

## Zarządzanie przez AWS CLI

Po uruchomieniu aplikacji możesz sprawdzić i zarządzać tabelami przez AWS CLI. Oto najważniejsze komendy:

### Wyświetlanie tabel

```bash
# Lista wszystkich tabel w regionie
aws dynamodb list-tables --region eu-north-1

# Szczegóły konkretnej tabeli
aws dynamodb describe-table --table-name Users --region eu-north-1

# Tylko podstawowe info o tabeli
aws dynamodb describe-table --table-name Users --region eu-north-1 --query 'Table.{Name:TableName,Status:TableStatus,Items:ItemCount}'
```

### Przeglądanie zawartości tabel

```bash
# Wszystkie użytkownicy
aws dynamodb scan --table-name Users --region eu-north-1

# Konkretny użytkownik
aws dynamodb get-item \
  --table-name Users \
  --key '{"user_id": {"S": "user_001"}}' \
  --region eu-north-1

# Utwory konkretnego artysty
aws dynamodb query \
  --table-name Music \
  --key-condition-expression "Artist = :artist" \
  --expression-attribute-values '{":artist": {"S": "The Beatles"}}' \
  --region eu-north-1

# Historia odtworzeń użytkownika (najnowsze pierwsze)
aws dynamodb query \
  --table-name UserListeningHistory \
  --key-condition-expression "user_id = :uid" \
  --expression-attribute-values '{":uid": {"S": "user_001"}}' \
  --scan-index-forward false \
  --region eu-north-1
```

### Zapytania na Global Secondary Indexes

```bash
# Top artyści rocka (przez GSI)
aws dynamodb query \
  --table-name Artists \
  --index-name genre-popularity-index \
  --key-condition-expression "genre = :genre" \
  --expression-attribute-values '{":genre": {"S": "rock"}}' \
  --scan-index-forward false \
  --region eu-north-1

# Koncerty w Londynie
aws dynamodb query \
  --table-name Concerts \
  --index-name city-date-index \
  --key-condition-expression "city = :city" \
  --expression-attribute-values '{":city": {"S": "London"}}' \
  --region eu-north-1
```

### Przydatne flagi i filtry

```bash
# Tylko wybrane atrybuty (projection)
aws dynamodb scan \
  --table-name Artists \
  --projection-expression "artist_id, #n, genre, popularity_score" \
  --expression-attribute-names '{"#n": "name"}' \
  --region eu-north-1

# Z filtrem (scan + filter po stronie AWS)
aws dynamodb scan \
  --table-name Music \
  --filter-expression "genre = :genre" \
  --expression-attribute-values '{":genre": {"S": "rock"}}' \
  --region eu-north-1

# Limit wyników
aws dynamodb scan \
  --table-name Music \
  --max-items 5 \
  --region eu-north-1

# Czytelniejszy output (tylko Items)
aws dynamodb scan \
  --table-name Users \
  --query 'Items' \
  --region eu-north-1
```

### Monitorowanie i debugowanie

```bash
# Status wszystkich tabel
aws dynamodb list-tables --region eu-north-1 | jq -r '.TableNames[]' | while read table; do
  echo "=== $table ==="
  aws dynamodb describe-table --table-name "$table" --region eu-north-1 --query 'Table.{Status:TableStatus,Items:ItemCount,Size:TableSizeBytes}'
done

# Sprawdzenie pojemności i throttling
aws dynamodb describe-table \
  --table-name Music \
  --region eu-north-1 \
  --query 'Table.{BillingMode:BillingModeSummary.BillingMode,RCU:ProvisionedThroughput.ReadCapacityUnits,WCU:ProvisionedThroughput.WriteCapacityUnits}'

# Sprawdzenie GSI
aws dynamodb describe-table \
  --table-name Artists \
  --region eu-north-1 \
  --query 'Table.GlobalSecondaryIndexes[*].{IndexName:IndexName,Status:IndexStatus}'
```

### Czyszczenie środowiska

```bash
# Lista tabel do usunięcia
echo "Users Playlists UserListeningHistory Artists Concerts Music" | tr ' ' '\n'

# Usunięcie konkretnej tabeli
aws dynamodb delete-table --table-name Users --region eu-north-1

# Usunięcie wszystkich tabel projektu (ostrożnie!)
for table in Users Playlists UserListeningHistory Artists Concerts Music; do
  echo "Deleting $table..."
  aws dynamodb delete-table --table-name "$table" --region eu-north-1 2>/dev/null || echo "$table doesn't exist"
done
```

---

Ta implementacja pokazuje praktyczne zastosowanie DynamoDB w rzeczywistej aplikacji, demonstrując wzorce projektowe, optymalizacje wydajności i najlepsze praktyki bezpieczeństwa.
