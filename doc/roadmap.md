# Project Roadmap

Meilenstein 1:
- Erstellung von Data Pipelines und Datenbanken zur Beschaffung und Speicherung von bestehenden Gesetzestexten und aktueller Änderungsgesetze.
  - Scraping von aktuellen Gesetzesänderungstexten automatisieren.
  - Aufsetzten einer Infrastruktur zur Seipeicherung der Daten. (textfiles mit sqlight/Postgres-Verzeichnis)
  - Beschaffung von bestehenden Gesetzestexten.

Meilenstein 2:
- Erste Iteration zum automatischen Parsen von Änderungsbefehlen und finden der Änderungen in bestehenden Gesetzten. Damit wird dann eine Vorher-Nachher-Version (Synopse) des Gesetzes erstellt.
  - Finden von Gesetzen auf die sich das Änderungsgesetz bezieht.
  - Entwerfen von regulären Ausdrücken um Verweise auf zuändernde Textstellen zu parsen.
  - Finden der geänderten Textstelle im Ursprungsgesetz.
  - Anwenden der Änderung.
  - Erste Version von Synopsen wird möglich.

Meilenstein 3:
- Web-App zur Darstellung der Änderungsgesetze.
  - Statische Website um Synopsen anzuzeigen.
  - aktuelle Synopsen liegen als Markdown vor und werden visualisiert.
  - Erste Version der Seite ist live.

Meilenstein 4:
- User-Research mit interessierten Journalist*innen und Jurist*innen.
  - Finden von interessierten Jurist*innen und/oder Journalist*innen. (tagesspiegel, lage der nation, ...)
  - Schwachstellen im aktuellen Ansatz verstehen und Verbesserungen erarbeiten.

Meilenstein 5:
- Such- und Filterfunktionalität wird bereitgestellt.
  - Filter nach Zeitraum und Schlagworten wird ermöglicht.

Meilenstein 6:
- Weitere Verbesserung des Parsers von Änderungsvorhaben und des Erstellens von Synopsen.
