from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo

STAMP=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
E=[]
def timed(uid,s,utc,min=120):
 d=datetime.strptime(utc,'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc); e=d+timedelta(minutes=min)
 E.append((d,["BEGIN:VEVENT",f"UID:{uid}",f"DTSTAMP:{STAMP}",f"SUMMARY:{s}",f"DTSTART:{d.strftime('%Y%m%dT%H%M%SZ')}",f"DTEND:{e.strftime('%Y%m%dT%H%M%SZ')}","END:VEVENT"]))
def day(uid,s,ymd):
 d=datetime.strptime(ymd,'%Y%m%d').date(); E.append((datetime.combine(d,datetime.min.time(),tzinfo=timezone.utc),["BEGIN:VEVENT",f"UID:{uid}",f"DTSTAMP:{STAMP}",f"SUMMARY:{s}",f"DTSTART;VALUE=DATE:{d:%Y%m%d}",f"DTEND;VALUE=DATE:{d+timedelta(days=1):%Y%m%d}","END:VEVENT"]))
# F1 UTC times from Formula1.com official 2026 race pages
F={
'spain':('Spanish GP (Madrid)', [('20260911T113000Z','Practice 1',60),('20260911T150000Z','Practice 2',60),('20260912T103000Z','Practice 3',60),('20260912T140000Z','Qualifying',60),('20260913T130000Z','Race',150)]),
'azerbaijan':('Azerbaijan GP',[('20260924T083000Z','Practice 1',60),('20260924T120000Z','Practice 2',60),('20260925T083000Z','Practice 3',60),('20260925T120000Z','Qualifying',60),('20260926T110000Z','Race',150)]),
'singapore':('Singapore GP',[('20261009T083000Z','Practice 1',60),('20261009T123000Z','Sprint Qualifying',44),('20261010T090000Z','Sprint',60),('20261010T130000Z','Qualifying',60),('20261011T120000Z','Race',150)]),
'united-states':('United States GP',[('20261023T173000Z','Practice 1',60),('20261023T210000Z','Practice 2',60),('20261024T173000Z','Practice 3',60),('20261024T210000Z','Qualifying',60),('20261025T200000Z','Race',150)]),
'mexico':('Mexico City GP',[('20261030T183000Z','Practice 1',60),('20261030T220000Z','Practice 2',60),('20261031T173000Z','Practice 3',60),('20261031T210000Z','Qualifying',60),('20261101T200000Z','Race',150)]),
'brazil':('São Paulo GP',[('20261106T153000Z','Practice 1',60),('20261106T190000Z','Practice 2',60),('20261107T143000Z','Practice 3',60),('20261107T180000Z','Qualifying',60),('20261108T170000Z','Race',150)]),
'las-vegas':('Las Vegas GP',[('20261120T003000Z','Practice 1',60),('20261120T040000Z','Practice 2',60),('20261121T003000Z','Practice 3',60),('20261121T040000Z','Qualifying',60),('20261122T040000Z','Race',150)]),
'qatar':('Qatar GP',[('20261127T133000Z','Practice 1',60),('20261127T170000Z','Practice 2',60),('20261128T143000Z','Practice 3',60),('20261128T180000Z','Qualifying',60),('20261129T160000Z','Race',150)]),
'abu-dhabi':('Abu Dhabi GP',[('20261204T093000Z','Practice 1',60),('20261204T130000Z','Practice 2',60),('20261205T103000Z','Practice 3',60),('20261205T140000Z','Qualifying',60),('20261206T130000Z','Race',150)])}
for slug,(gp,ss) in F.items():
 for t,n,m in ss: timed(f"f1-2026-{slug}-{n.lower().replace(' ','-')}@jackallege17-sports",f"🏎️ F1 — {gp} — {n}",t,m)
# Michigan
for uid,s,t in [('umich-2026-09-12-oklahoma@jackallege17-sports','〽️ Michigan Football — vs #11 Oklahoma','20260912T160000Z'),('umich-2026-09-19-utep@jackallege17-sports','〽️ Michigan Football — vs UTEP','20260919T193000Z')]: timed(uid,s,t,240)
for y,slug,s in [('20260926','iowa','vs Iowa'),('20261003','minnesota','at Minnesota'),('20261017','penn-state','vs Penn State'),('20261024','indiana','vs Indiana'),('20261031','rutgers','at Rutgers'),('20261107','michigan-state','vs Michigan State'),('20261114','oregon','at Oregon'),('20261121','ucla','vs UCLA'),('20261128','ohio-state','at Ohio State')]: day(f"umich-2026-{y[4:6]}-{y[6:]}-{slug}@jackallege17-sports",f"〽️ Michigan Football — {s} — TBA",y)
# Maryland
for uid,s,t in [('umd-2026-09-12-uconn@jackallege17-sports','🐢 Maryland Football — at UConn','20260912T193000Z'),('umd-2026-09-19-tech@jackallege17-sports','🐢 Maryland Football — vs Virginia Tech','20260919T233000Z')]: timed(uid,s,t,240)
for y,slug,s in [('20260926','ucla','vs UCLA'),('20261003','nebraska','at Nebraska'),('20261010','state','at Ohio State'),('20261017','rutgers','vs Rutgers'),('20261031','illinois','vs Illinois'),('20261107','purdue','at Purdue'),('20261114','wisconsin','vs Wisconsin'),('20261121','usc','at USC'),('20261128','penn-state','vs Penn State')]: day(f"umd-2026-{y[4:6]}-{y[6:]}-{slug}@jackallege17-sports",f"🐢 Maryland Football — {s} — TBA",y)
# Tottenham men's first team. Sep/Oct reflect confirmed broadcast/cup changes; later PL fixtures remain provisional.
L=ZoneInfo('Europe/London')
def sp(y,hm,opp,home=True,comp='Premier League'):
 d=datetime.strptime(y+hm,'%Y%m%d%H:%M').replace(tzinfo=L).astimezone(timezone.utc); slug=opp.lower().replace(' ','-').replace('&','and').replace('.','').replace("'",'')
 timed(f"spurs-{y[:4]}-{y[4:6]}-{y[6:]}-{slug}@jackallege17-sports",f"⚽ Tottenham — {'vs' if home else 'at'} {opp} ({comp})",d.strftime('%Y%m%dT%H%M%SZ'),135)
for r in [('20260912','17:30','Everton',1,'Premier League'),('20260915','20:00','Liverpool',0,'Carabao Cup'),('20260919','12:30','Aston Villa',1,'Premier League'),('20261010','17:30','Manchester United',0,'Premier League'),('20261019','20:00','Coventry City',1,'Premier League'),('20261024','17:30','Chelsea',0,'Premier League'),('20261031','17:30','Crystal Palace',1,'Premier League')]: sp(*r)
R=[('20261107','15:00','Leeds United',0),('20261121','15:00','Ipswich Town',1),('20261128','15:00','Sunderland',0),('20261202','20:00','Fulham',1),('20261205','15:00','Arsenal',1),('20261212','15:00','Hull City',0),('20261219','15:00','Liverpool',0),('20261226','15:00','AFC Bournemouth',1),('20261230','20:00','Brighton & Hove Albion',1),('20270102','15:00','Manchester City',0),('20270106','20:00','Fulham',0),('20270116','15:00','Leeds United',1),('20270123','15:00','Crystal Palace',0),('20270130','15:00','Sunderland',1),('20270206','15:00','Ipswich Town',0),('20270210','20:00','Manchester City',1),('20270220','15:00','Brighton & Hove Albion',0),('20270227','15:00','Liverpool',1),('20270303','20:00','AFC Bournemouth',0),('20270313','15:00','Nottingham Forest',1),('20270320','15:00','Everton',0),('20270410','15:00','Brentford',1),('20270417','15:00','Newcastle United',0),('20270424','15:00','Hull City',1),('20270501','15:00','Arsenal',0),('20270508','15:00','Chelsea',1),('20270515','15:00','Coventry City',0),('20270523','15:00','Manchester United',1),('20270530','16:00','Aston Villa',0)]
for r in R: sp(*r)
E.sort(key=lambda x:x[0])
H=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Jackallege17//Sports Calendar//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Sports — F1 / Spirit / Michigan / Maryland / Tottenham','X-WR-TIMEZONE:America/Detroit','REFRESH-INTERVAL;VALUE=DURATION:PT1H','X-PUBLISHED-TTL:PT1H']
out=H[:]
for _,b in E: out+=b
out+=['END:VCALENDAR','']
open('sports-calendar.ics','w',encoding='utf-8',newline='').write('\r\n'.join(out))
