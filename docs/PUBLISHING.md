# Veröffentlichung des vorbereiteten Ordners

Dieser Ordner ist als eigenständiges Repository vorbereitet. Er enthält keine Git-Historie und keinen Verweis auf das private Projekt. Die ZIP-Datei daneben enthält denselben freigegebenen Dateibestand ohne Laufzeitdateien oder Python-Caches.

## Auf GitHub bringen

1. Ein neues, leeres GitHub-Repository anlegen, zum Beispiel `multimodal-device-inspection`. Kein zusätzliches README und keine Lizenzdatei automatisch anlegen.
2. Den vorbereiteten Ordner an einen eigenen Projektort kopieren oder die ZIP-Datei dort entpacken.
3. Im neuen Ordner ausführen:

```bash
git init -b main
git add .
git commit -m "Add public multimodal inspection portfolio"
git remote add origin <URL-DES-NEUEN-REPOSITORIES>
git push -u origin main
```

Die URL muss durch die tatsächliche Repository-Adresse ersetzt werden. Alternativ kann der vorbereitete Ordner mit einer Git-Oberfläche veröffentlicht werden. Den kompletten Ordner als neues Repository verwenden; die Historie des privaten Projekts nicht übernehmen.

**Vorgeschlagene GitHub-Beschreibung:**

> Local multimodal device inspection: text classification, trained image-view recognition and evidence-aware human review.

**Vorgeschlagene Topics:** `python`, `machine-learning`, `computer-vision`, `nlp`, `pytorch`, `human-in-the-loop`.

## Inhalt und Grenzen

- Englisches README mit direkt eingebundenen Screenshots und Startanleitung.
- Textmodell mit ausschließlich erfundenen Trainingsbeispielen.
- Bildmodell als ausgewählte Tensoren; keine Originalfotos oder Trainingsmetadaten.
- Vereinfachter Modell- und Reviewcode; keine Anbieteranbindungen oder Geschäftsregeln.
- Keine Zugangsdaten erforderlich. Die Demo kommuniziert mit ihrem lokalen Python-Server.

Die Bildansichten sind echte Modellinferenz. Die standardmäßig angezeigten Geräteszenen und Schadensmarkierungen sind Illustrationen. Diese Unterscheidung ist im README und in der Oberfläche sichtbar.

## Vorbereitete Prüfungen

`python scripts/audit_public.py` sucht nach typischen Tokenformaten, privaten Heimatverzeichnissen, E-Mail-Adressen, Marktplatz-URLs und unerwünschten Dateitypen. Es prüft auch den Inhalt des Tensorarchivs. Ein Mustercheck ist keine vollständige Garantie für Geheimnisfreiheit.

`RELEASE_MANIFEST.json` enthält SHA-256-Prüfsummen der geprüften Dateien. Mit `python scripts/audit_public.py --package` werden Manifest und ZIP neu erstellt.

Nach Veröffentlichung sollte der erste GitHub-Actions-Lauf geprüft werden. Die Third-Party-Hinweise liegen bei. Für den eigenen Projektcode ist noch keine allgemeine Open-Source-Lizenz gewählt; für ein Bewerbungsrepo kann der Code zunächst zur Einsicht bereitstehen. Eine spätere Freigabe zur allgemeinen Nachnutzung ist eine eigene Entscheidung.

## Screenshots neu erstellen

Demo starten und in einem separaten Chrome-Profil Headless-Debugging auf Port 9237 aktivieren. Anschließend mit Node 22 oder neuer ausführen:

```bash
node scripts/capture_screenshots.mjs
```

Das Skript verwendet ausschließlich den lokalen Chrome-Debugging-Endpunkt und die lokale Demo. Es erstellt vier Desktop-PNG-Dateien im bestehenden Dashboard-Design: Action Board, Textprüfung, Bildprüfung und Modellübersicht. Es prüft außerdem Board-Suche und Filter, Hell-/Dunkelmodus, Ansichtsauswahl, Navigation, Fallwechsel und die Sperre veralteter Ergebnisse. Es ist kein Bestandteil der Python-Laufzeit.
