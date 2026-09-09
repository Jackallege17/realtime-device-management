from pathlib import Path
import re
p=Path('sports-calendar.ics')
s=p.read_text(encoding='utf-8')
pat=r'BEGIN:VEVENT\r?\nUID:umich-2026-11-28-ohio-state@jackallege17-sports\r?\n.*?\r?\nEND:VEVENT'
m=re.search(pat,s,re.S)
if not m:
    raise SystemExit('Ohio State event not found')
stamp='20260909T065251Z'
summary='〽️ Michigan Football — at Ohio State'
lines=[
'BEGIN:VEVENT',
'UID:umich-2026-11-28-ohio-state@jackallege17-sports',
f'DTSTAMP:{stamp}',
f'SUMMARY:{summary}',
'DTSTART:20261128T170000Z',
'DTEND:20261128T210000Z',
'BEGIN:VALARM','ACTION:DISPLAY',f'DESCRIPTION:{summary} — 5 days before','TRIGGER:-P5D','END:VALARM',
'BEGIN:VALARM','ACTION:DISPLAY',f'DESCRIPTION:{summary} — 1 day before','TRIGGER:-P1D','END:VALARM',
'BEGIN:VALARM','ACTION:DISPLAY',f'DESCRIPTION:{summary} — 2 hours before','TRIGGER:-PT2H','END:VALARM',
'END:VEVENT']
newline='\r\n' if '\r\n' in s else '\n'
new=s[:m.start()]+newline.join(lines)+s[m.end():]
p.write_text(new,encoding='utf-8',newline='')
