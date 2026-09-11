from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
STAMP=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); E=[]
def alarms(s,day=False):
 x=[]
 for t,d in [('-P5D','5 days before'),('-P1D','1 day before'),('PT9H' if day else '-PT2H','Today at 9:00 AM' if day else '2 hours before')]: x += ['BEGIN:VALARM','ACTION:DISPLAY',f'DESCRIPTION:{s} — {d}',f'TRIGGER:{t}','END:VALARM']
 return x
def timed(uid,s,t,m=120):
 d=datetime.strptime(t,'%Y%m%dT%H%MZ').replace(tzinfo=timezone.utc); e=d+timedelta(minutes=m); E.append((d,['BEGIN:VEVENT',f'UID:{uid}',f'DTSTAMP:{STAMP}',f'SUMMARY:{s}',f'DTSTART:{d:%Y%m%dT%H%M%SZ}',f'DTEND:{e:%Y%m%dT%H%M%SZ}']+alarms(s)+['END:VEVENT']))
def day(uid,s,y):
 d=datetime.strptime(y,'%Y%m%d').date(); E.append((datetime.combine(d,datetime.min.time(),tzinfo=timezone.utc),['BEGIN:VEVENT',f'UID:{uid}',f'DTSTAMP:{STAMP}',f'SUMMARY:{s}',f'DTSTART;VALUE=DATE:{d:%Y%m%d}',f'DTEND;VALUE=DATE:{d+timedelta(days=1):%Y%m%d}']+alarms(s,True)+['END:VEVENT']))
# F1: Formula1.com official race starts; race only.
for slug,name,t in [('spain','Spanish GP (Madrid)','20260913T1300Z'),('azerbaijan','Azerbaijan GP','20260926T1100Z'),('bahrain-in-malaysia','Bahrain GP in Malaysia (Sepang)','20261004T0700Z'),('singapore','Singapore GP','20261011T1200Z'),('united-states','United States GP','20261025T2000Z'),('mexico','Mexico City GP','20261101T2000Z'),('brazil','São Paulo GP','20261108T1700Z'),('las-vegas','Las Vegas GP','20261122T0400Z'),('qatar','Qatar GP','20261129T1600Z'),('abu-dhabi','Abu Dhabi GP','20261206T1300Z')]: timed(f'f1-2026-{slug}-race@jackallege17-sports',f'🏎️ F1 — {name} — Race',t,150)
# Michigan
for u,s,t in [('umich-2026-09-12-oklahoma@jackallege17-sports','〽️ Michigan Football — vs Oklahoma','20260912T1600Z'),('umich-2026-09-19-utep@jackallege17-sports','〽️ Michigan Football — vs UTEP','20260919T1930Z')]: timed(u,s,t,240)
for y,slug,s in [('20260926','iowa','vs Iowa'),('20261003','minnesota','at Minnesota'),('20261017','penn-state','vs Penn State'),('20261024','indiana','vs Indiana'),('20261031','rutgers','at Rutgers'),('20261107','michigan-state','vs Michigan State'),('20261114','oregon','at Oregon'),('20261121','ucla','vs UCLA')]: day(f'umich-2026-{y[4:6]}-{y[6:]}-{slug}@jackallege17-sports',f'〽️ Michigan Football — {s} — TBA',y)
timed('umich-2026-11-28-ohio-state@jackallege17-sports','〽️ Michigan Football — at Ohio State','20261128T1700Z',240)
# Maryland
for u,s,t in [('umd-2026-09-12-uconn@jackallege17-sports','🐢 Maryland Football — at UConn','20260912T1930Z'),('umd-2026-09-19-virginia-tech@jackallege17-sports','🐢 Maryland Football — vs Virginia Tech','20260919T2330Z')]: timed(u,s,t,240)
for y,slug,s in [('20260926','ucla','vs UCLA'),('20261003','nebraska','at Nebraska'),('20261010','ohio-state','at Ohio State'),('20261017','rutgers','vs Rutgers'),('20261031','illinois','vs Illinois'),('20261107','purdue','at Purdue'),('20261114','wisconsin','vs Wisconsin'),('20261121','usc','at USC'),('20261128','penn-state','vs Penn State')]: day(f'umd-2026-{y[4:6]}-{y[6:]}-{slug}@jackallege17-sports',f'🐢 Maryland Football — {s} — TBA',y)
# Tottenham men's first team: Sep/Oct confirmed changes; later PL fixtures provisional.
UK=ZoneInfo('Europe/London')
def sp(y,h,o,home=True,c='Premier League'):
 d=datetime.strptime(y+h,'%Y%m%d%H:%M').replace(tzinfo=UK).astimezone(timezone.utc); slug=o.lower().replace('&','and').replace(' ','-').replace("'",'').replace('.',''); timed(f'spurs-{y[:4]}-{y[4:6]}-{y[6:]}-{slug}@jackallege17-sports',f"⚽ Tottenham — {'vs' if home else 'at'} {o} ({c})",d.strftime('%Y%m%dT%H%MZ'),135)
for r in [('20260912','17:30','Everton',1,'Premier League'),('20260915','20:00','Liverpool',0,'Carabao Cup'),('20260919','12:30','Aston Villa',1,'Premier League'),('20261010','17:30','Manchester United',0,'Premier League'),('20261019','20:00','Coventry City',1,'Premier League'),('20261024','17:30','Chelsea',0,'Premier League'),('20261031','17:30','Crystal Palace',1,'Premier League')]: sp(*r)
for r in [('20261107','15:00','Leeds United',0),('20261121','15:00','Ipswich Town',1),('20261128','15:00','Sunderland',0),('20261202','20:00','Fulham',1),('20261205','15:00','Arsenal',1),('20261212','15:00','Hull City',0),('20261219','15:00','Liverpool',0),('20261226','15:00','AFC Bournemouth',1),('20261230','20:00','Brighton & Hove Albion',1),('20270102','15:00','Manchester City',0),('20270106','20:00','Fulham',0),('20270116','15:00','Leeds United',1),('20270123','15:00','Crystal Palace',0),('20270130','15:00','Sunderland',1),('20270206','15:00','Ipswich Town',0),('20270210','20:00','Manchester City',1),('20270220','15:00','Brighton & Hove Albion',0),('20270227','15:00','Liverpool',1),('20270303','20:00','AFC Bournemouth',0),('20270313','15:00','Nottingham Forest',1),('20270320','15:00','Everton',0),('20270410','15:00','Brentford',1),('20270417','15:00','Newcastle United',0),('20270424','15:00','Hull City',1),('20270501','15:00','Arsenal',0),('20270508','15:00','Chelsea',1),('20270515','15:00','Coventry City',0),('20270523','15:00','Manchester United',1),('20270530','16:00','Aston Villa',0)]: sp(*r)
E.sort(key=lambda z:z[0]); out=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Jackallege17//Sports Calendar//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Sports — F1 / Spirit / Michigan / Maryland / Tottenham','X-WR-TIMEZONE:America/Detroit','REFRESH-INTERVAL;VALUE=DURATION:PT1H','X-PUBLISHED-TTL:PT1H']
for _,b in E: out += b
out += ['END:VCALENDAR','']; open('sports-calendar.ics','w',encoding='utf-8',newline='').write('\r\n'.join(out))
