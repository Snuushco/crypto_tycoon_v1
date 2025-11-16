# Crypto Tycoon v1

Een lichtgewicht, terminal-based tycoon game waarin je een crypto-imperium runt. Handel in digitale assets, koop mining rigs en versnel de tijd om te zien hoe je portfolio groeit.

## Kenmerken
- **Marktsimulatie** met volatiliteit en trends per coin.
- **Handel & mining**: koop coins of rigs, ontvang dagelijkse mining rewards en betaal upkeep.
- **Snelle feedbackloop**: sla dagen over om marktschokken te ervaren.
- **Zero dependencies**: draait direct met de Python-standaardbibliotheek.

## Installatie
1. Zorg voor Python 3.10+.
2. Clone deze repo en navigeer naar de root.
3. (Optioneel) activeer een virtualenv.

## Gebruik
Start het spel vanuit de root van de repo:

```bash
py main.py
```

Navigatie gebeurt via de menu-opties. Koop coins, investeer in rigs en versnel de tijd om rijkdom te vergaren.

## Tests draaien

```bash
py -m unittest discover -s tests
```

## Roadmap ideeën
- Persistentie van saves.
- Dagelijkse events en quests.
- UI-upgrade via Rich/Textual.
- Leaderboards met seeds.
