# PalauteDjango

QR-tokeniin perustuva moniasiakas (multi-tenant) palautesovellus Django + admin -toteutuksena.

## Perusidea

- `Client`: yritys/asiakas (sisältää `public_token` + mahdollisen `google_review_url`)
- `Feedback`: yksittäinen palaute (arvosana 1–5, kommentti, metadata)
- `CustomerProfile`: liittää Django-käyttäjän yhteen `Client`iin

Superuser hallitsee kaikkea `admin/`-näkymän kautta. Asiakaskäyttäjät kirjautuvat sisään ja näkevät oman yrityksensä palautteet `dashboard/`-näkymässä.

## Käynnistys (dev)

```powershell
cd PalauteDjango
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Admin: `http://127.0.0.1:8000/admin/`
- Asiakasnäkymä: `http://127.0.0.1:8000/dashboard/`

## Julkinen palautelinkki (QR)

Julkinen palaute annetaan URLilla:

- `http://127.0.0.1:8000/f/<public_token>/`

Jos asetat ympäristömuuttujan `PUBLIC_BASE_URL`, adminissa ja dashboardissa näkyy myös täysi URL.

```powershell
$env:PUBLIC_BASE_URL="https://example.com"
```

## Asiakastunnukset

1) Luo adminissa `Client`.
2) Luo `User` (ei tarvitse olla staff).
3) Lisää käyttäjälle `CustomerProfile` ja valitse oikea `Client`.

Tämän jälkeen käyttäjä näkee `dashboard/`-näkymässä vain oman `Client`in palautteet.

