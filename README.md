# Porsche Banner Agent

Spletno orodje, ki samodejno posodobi "small print" (veljavnost akcije) na
Meta banner kreativah - brez Photoshopa, brez ročnega urejanja.

## Kaj naredi

1. Naložiš eno ali več banner slik (PNG/JPG) - lahko vseh 16 hkrati.
2. Agent za vsako sliko:
   - z OCR-jem poišče vrstico z datumom veljavnosti,
   - teksturno "izbriše" star datum (ohrani ozadje - tlakovci, asfalt, beton ...),
   - na novo izriše vrstico s posodobljenim datumom, v pravi velikosti in
     poravnavi, natančno na sredini med 1. in 3. vrstico (da se nič ne prekriva).
3. Slike, ki small printa nimajo (npr. čisto vizualne kartice iz carousela),
   se v izhodnem paketu vrnejo nespremenjene - dobiš nazaj celoten komplet.
4. Prenese vse popravljene slike kot en ZIP.

## Namestitev in zagon (lokalno)

Potreben je tudi sistemski paket `tesseract-ocr` (in slovenski jezikovni
paket zanj), poleg Python odvisnosti:

```
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-slv

# nato v mapi projekta:
pip install -r requirements.txt
python3 app.py
```

Odpri brskalnik na `http://localhost:5000`.

## Prilagoditev za drugo kampanjo / drug datum

V vmesniku preprosto vpišeš star in nov datum (privzeto `30.9.2026` →
`31.12.2026`) - polje ni vezano samo na to kampanjo. Če bo Porsche v
prihodnje spremenil kaj drugega kot samo datum (npr. celotno besedilo
pogojev), je treba prilagoditi predlogo v `fixer/fix_smallprint.py`
(spremenljivka `template_line`).

## Znane omejitve

- Pisava je nastavljena na Liberation Sans (vizualno zelo blizu izvirni
  Porsche pisavi pri majhnih velikostih), ne dejanska korporativna pisava.
- Pri nekaterih zelo kompleksnih ozadjih (npr. dolga diagonalna arhitekturna
  linija skozi besedilo) je popravek lahko rahlo opazen - priporočamo hiter
  vizualni pregled izhoda pred objavo.
- Trenutno ni prijave/gesla - za širšo uporabo v agenciji priporočamo dodati
  osnovno avtentikacijo, če bo orodje gostovano javno.

## Testirano na

Vseh 6 dejanskih Porsche bannerjev iz te kampanje (Finder_1 v obeh
dimenzijah, Financiranje_6 carousel v vseh 4 karticah) - rezultati vizualno
potrjeni, brez prekrivanja besedila, brez vidnih sledi popravka (razen ene
manjše izjeme na sliki z diagonalno arhitekturno linijo v ozadju).
