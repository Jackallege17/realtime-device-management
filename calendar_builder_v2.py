from datetime import datetime, timezone
from pathlib import Path

p = Path('sports-calendar.ics')
raw = p.read_text(encoding='utf-8')
text = raw.replace('\r\n', '\n')
uid = 'f1-2026-bahrain-in-malaysia-race@jackallege17-sports'

if uid not in text:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    event = f'''BEGIN:VEVENT
UID:{uid}
DTSTAMP:{stamp}
SUMMARY:🏎️ F1 — Bahrain GP in Malaysia (Sepang) — Race
DTSTART:20261004T070000Z
DTEND:20261004T093000Z
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:🏎️ F1 — Bahrain GP in Malaysia (Sepang) — Race — 5 days before
TRIGGER:-P5D
END:VALARM
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:🏎️ F1 — Bahrain GP in Malaysia (Sepang) — Race — 1 day before
TRIGGER:-P1D
END:VALARM
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:🏎️ F1 — Bahrain GP in Malaysia (Sepang) — Race — 2 hours before
TRIGGER:-PT2H
END:VALARM
END:VEVENT
'''
    # Keep chronological order: Oct 4 race precedes the first Oct 10 event.
    marker = 'BEGIN:VEVENT\nUID:umd-2026-10-10-ohio-state@jackallege17-sports'
    if marker in text:
        text = text.replace(marker, event + marker, 1)
    else:
        text = text.replace('END:VCALENDAR', event + 'END:VCALENDAR', 1)
    p.write_text(text.replace('\n', '\r\n'), encoding='utf-8', newline='')
