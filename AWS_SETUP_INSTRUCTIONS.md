# Konfiguracja AWS dla DynamoDB

Kompletny przewodnik konfiguracji AWS od rejestracji do gotowości na uruchomienie projektów DynamoDB.

## Założenie konta AWS

### Rejestracja

1. Wejdź na **https://aws.amazon.com/free/**
2. "Create Free Account"
3. Wypełnij formularz:
   - Email i hasło
   - Nazwa konta AWS (może być twoja firma/projekt)
4. Dane kontaktowe + karta kredytowa (potrzebna do weryfikacji, ale nie będzie obciążona)
5. Weryfikacja telefonu (SMS lub połączenie)
6. Wybierz **Basic Support Plan (Free)**

### Ważne informacje o Free Tier

AWS Free Tier obejmuje:

- **DynamoDB**: 25 GB storage + 25 RCU/WCU miesięcznie na zawsze
- **Lambda**: 1M bezpłatnych wywołań miesięcznie
- **CloudWatch**: podstawowe metryki za darmo
- **EC2**: 750 godzin t2.micro miesięcznie przez rok

## Logowanie do konsoli AWS

### Pierwsze logowanie

1. Otwórz **https://console.aws.amazon.com**
2. Wybierz **"Root user"**
3. Wpisz email i hasło z rejestracji
4. Kliknij **"Sign In"**

## Nawigacja w AWS Console

### Znajdowanie DynamoDB

1. W górnym pasku wyszukiwania wpisz **"DynamoDB"**
2. Kliknij pierwszą opcję z listy
3. Trafiasz do konsoli DynamoDB

### Ustawienie regionu (BARDZO WAŻNE!)

1. **Sprawdź region** w prawym górnym rogu konsoli
2. Kliknij na nazwę regionu i wybierz **"Europe (Stockholm) eu-north-1"**
3. **Wszystkie zasoby AWS są powiązane z regionem**
4. Kod w projekcie używa `eu-north-1`, więc to musi się zgadzać

**Dlaczego region ma znaczenie?**

- Każdy region to fizycznie oddzielne datacenter
- Tabele stworzone w `us-east-1` nie będą widoczne w `eu-north-1`
- Latencja jest niższa gdy region jest bliżej użytkowników

## Uzyskanie kluczy dostępu (credentials)

1. W prawym górnym rogu kliknij na nickname
2. Menu → Security credentials
3. "Add user"
4. Acess keys → Create access keys
5. Zapisz klucze

## Konfiguracja lokalnego środowiska

### Instalacja AWS CLI

```bash
# macOS
brew install awscli

# Linux/WSL
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Lub przez pip
pip install awscli
```

### Konfiguracja credentials

```bash
aws configure

# Wprowadź gdy zostaniesz poproszony:
# AWS Access Key ID: [wklej swój klucz]
# AWS Secret Access Key: [wklej swój sekretny klucz]
# Default region name: eu-north-1
# Default output format: json
```

### Test konfiguracji

```bash
# Sprawdź czy działa
aws sts get-caller-identity

# Powinieneś zobaczyć:
# {
#     "UserId": "AIDACKCEVSQ6C2EXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/developer"
# }
```

## Przygotowanie środowiska Python

Po skonfigurowaniu AWS musisz przygotować lokalne środowisko Python do pracy z boto3 (biblioteką AWS dla Pythona).

### Tworzenie i aktywacja środowiska

```bash
# Przejdź do katalogu projektu
cd AWS_DynamoDB

# Stwórz wirtualne środowisko
python -m venv venv

# Aktywuj środowisko (macOS/Linux)
source venv/bin/activate

# Na Windows byłoby:
# venv\Scripts\activate

# Zainstaluj wymagane biblioteki
pip install -r requirements.txt
```

## Pierwsze kroki w DynamoDB Console

### Eksploracja interfejsu

1. W konsoli DynamoDB zobaczysz:
   - **Tables** - lista twoich tabel
   - **Explore items** - przeglądanie danych w tabelach
   - **Backups** - kopie zapasowe

## Rozwiązywanie problemów

### "Unable to locate credentials"

```bash
# Sprawdź konfigurację
aws configure list

# Jeśli puste, uruchom ponownie
aws configure
```

### "Access Denied" lub "UnauthorizedOperation"

- Sprawdź czy klucze są poprawne
- Sprawdź czy użytkownik ma odpowiednie uprawnienia IAM
- Dla testów można dodać `AmazonDynamoDBFullAccess`

### "Region not found" lub inne błędy regionu

```bash
# Sprawdź aktualną konfigurację
aws configure get region

# Ustaw właściwy region
aws configure set region eu-north-1
```

### Karta kredytowa zostanie obciążona?

**Nie**, jeśli:

- Pozostajesz w limitach Free Tier
- Nie korzystasz z płatnych usług
- Nie przekroczysz 25 GB w DynamoDB

AWS zawsze najpierw wyśle email z ostrzeżeniem przed naliczeniem opłat.

## Co dalej?

Po skonfigurowaniu AWS możesz:

1. **[CODE_EXPLANATION.md](CODE_EXPLANATION.md)** - zrozumieć jak działa kod
2. **[README.md](README.md)** - przegląd całego projektu
