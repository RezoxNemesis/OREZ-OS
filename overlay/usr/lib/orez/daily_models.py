"""Local-only Calendar and Reuz desktop data. No network or privileged operations."""
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def private_root(name, root=None):
    if os.getuid()==0 or os.geteuid()==0:
        raise ValueError('Open desktop applications as your ordinary user, never root.')
    path=Path(root) if root else Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'orez'/name
    if not path.is_absolute(): raise ValueError('Application storage must be an absolute path.')
    for item in [path,*path.parents]:
        if item.is_symlink(): raise ValueError('Application storage must not contain symlinks.')
    path.mkdir(parents=True,mode=0o700,exist_ok=True)
    if path.stat().st_uid!=os.getuid(): raise ValueError('Application storage must belong to you.')
    path.chmod(0o700)
    return path


class Calendar:
    """All-day local events. Timed events/reminders and account sync are not offered."""
    def __init__(self, root=None):
        self.root=private_root('calendar',root)
        path=self.root/'events.sqlite3'
        if path.is_symlink(): raise ValueError('Refusing an aliased calendar database.')
        fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);os.close(fd)
        path.chmod(0o600)
        self.db=sqlite3.connect(path,timeout=2)
        version=self.db.execute('PRAGMA user_version').fetchone()[0]
        tables=self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if version==0 and not tables:
            with self.db:
                self.db.execute('CREATE TABLE events (id INTEGER PRIMARY KEY, uid TEXT NOT NULL UNIQUE, day TEXT NOT NULL, title TEXT NOT NULL, notes TEXT NOT NULL)')
                self.db.execute('PRAGMA user_version=1')
        elif version!=1 or tables!=[('events',)]:
            self.db.close();raise ValueError('Unrecognized calendar schema; preserve the file and inspect it.')

    def events(self, day):
        dt.date.fromisoformat(day)
        return self.db.execute('SELECT id,day,title,notes FROM events WHERE day=? ORDER BY id',(day,)).fetchall()

    def save(self, day, title, notes='', event_id=None):
        date=dt.date.fromisoformat(day)
        if date==dt.date.max:raise ValueError('Choose a date before 31 December 9999.')
        day=date.isoformat();title=title.strip()
        if not title or len(title)>160 or any(ord(c)<32 for c in title):
            raise ValueError('Use a title of 1–160 characters without control characters.')
        if len(notes)>10000 or '\x00' in notes: raise ValueError('Notes must be at most 10,000 characters and contain no NUL.')
        with self.db:
            if event_id is None:
                return self.db.execute('INSERT INTO events(uid,day,title,notes) VALUES(?,?,?,?)',(str(uuid.uuid4())+'@orez.local',day,title,notes)).lastrowid
            changed=self.db.execute('UPDATE events SET day=?,title=?,notes=? WHERE id=?',(day,title,notes,event_id))
            if changed.rowcount!=1: raise ValueError('The selected event no longer exists.')
        return event_id

    def delete(self, event_id):
        with self.db:
            if self.db.execute('DELETE FROM events WHERE id=?',(event_id,)).rowcount!=1:
                raise ValueError('The selected event no longer exists.')

    def export_ics(self):
        def escaped(value):
            return value.replace('\\','\\\\').replace('\r\n','\n').replace('\r','\n').replace('\n','\\n').replace(';','\\;').replace(',','\\,')
        def folded(value):
            lines=[];line=''
            for char in value:
                if len((line+char).encode('utf-8'))>75:
                    lines.append(line);line=' '
                line+=char
            return '\r\n'.join([*lines,line])
        lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//OREZ//Local Calendar//EN','CALSCALE:GREGORIAN']
        stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        for uid,day,title,notes in self.db.execute('SELECT uid,day,title,notes FROM events ORDER BY day,id'):
            date=dt.date.fromisoformat(day)
            lines+=['BEGIN:VEVENT','UID:'+uid,'DTSTAMP:'+stamp,
                    'DTSTART;VALUE=DATE:'+date.isoformat().replace('-',''),
                    'DTEND;VALUE=DATE:'+(date+dt.timedelta(days=1)).isoformat().replace('-',''),
                    'SUMMARY:'+escaped(title),'DESCRIPTION:'+escaped(notes),'END:VEVENT']
        return '\r\n'.join(folded(line) for line in [*lines,'END:VCALENDAR'])+'\r\n'

    def close(self): self.db.close()


class ClockSettings:
    # Same UTC / 24-hour defaults as the verified Reuz clock logic. This desktop
    # edition does not import the web Worker's MCP endpoint or Android services.
    def __init__(self, root=None):
        self.root=private_root('reuz',root);self.path=self.root/'settings.json'
        self.timezone='UTC';self.format='24h'
        if self.path.is_symlink(): raise ValueError('Refusing aliased Reuz settings.')
        if self.path.exists():
            value=json.loads(self.path.read_text())
            if not isinstance(value,dict) or set(value)!={'timezone','format'}: raise ValueError('Invalid Reuz settings; preserve and inspect settings.json.')
            self.validate(value['timezone'],value['format'])
            self.timezone=value['timezone'];self.format=value['format']

    @staticmethod
    def validate(timezone, format):
        if not isinstance(timezone,str) or len(timezone)>64 or format not in ['12h','24h']:
            raise ValueError('Choose an IANA timezone and 12h or 24h format.')
        try: ZoneInfo(timezone)
        except (ValueError,ZoneInfoNotFoundError): raise ValueError('Unknown timezone.') from None

    def save(self, timezone, format):
        self.validate(timezone,format)
        if self.path.is_symlink(): raise ValueError('Refusing aliased Reuz settings.')
        name=None
        try:
            with tempfile.NamedTemporaryFile(mode='w',dir=self.root,prefix='.settings-',delete=False) as stream:
                name=stream.name;json.dump({'timezone':timezone,'format':format},stream);stream.write('\n')
                stream.flush();os.fsync(stream.fileno())
            os.replace(name,self.path)
        finally:
            if name:Path(name).unlink(missing_ok=True)
        self.timezone=timezone;self.format=format

    def display(self, now=None):
        current=(now or dt.datetime.now(dt.timezone.utc)).astimezone(ZoneInfo(self.timezone))
        return current.strftime('%H:%M:%S' if self.format=='24h' else '%I:%M:%S %p'),current.strftime('%A, %d %B %Y')


def elapsed_clock():
    # CLOCK_BOOTTIME includes suspend on Linux. Timers cannot wake a sleeping PC.
    return time.clock_gettime(time.CLOCK_BOOTTIME)


class Stopwatch:
    def __init__(self, clock=elapsed_clock):
        self.clock=clock;self.accumulated=0.;self.started=None;self.laps=[]
    def elapsed(self):return self.accumulated+(self.clock()-self.started if self.started is not None else 0)
    def start(self):
        if self.started is None:self.started=self.clock()
    def pause(self):
        self.accumulated=self.elapsed();self.started=None
    def reset(self):self.accumulated=0.;self.started=None;self.laps=[]
    def lap(self):
        value=self.elapsed();self.laps.append(value);return value


class Countdown:
    def __init__(self, clock=elapsed_clock):
        self.clock=clock;self.deadline=None;self.left=0.;self.finished=False
    def start(self, seconds=None):
        if seconds is not None:
            if not 0<seconds<=86400:raise ValueError('Choose a timer between 1 second and 24 hours.')
            self.left=float(seconds);self.finished=False
        if self.left<=0:raise ValueError('Set a timer duration first.')
        self.deadline=self.clock()+self.left
    def remaining(self):return max(0.,self.deadline-self.clock()) if self.deadline is not None else self.left
    def pause(self):self.left=self.remaining();self.deadline=None
    def reset(self):self.deadline=None;self.left=0.;self.finished=False
    def check_finished(self):
        if self.deadline is not None and self.remaining()==0 and not self.finished:
            self.finished=True;self.deadline=None;self.left=0.;return True
        return False


def duration(seconds):
    tenths=max(0,int(seconds*10));hours,rest=divmod(tenths,36000);minutes,rest=divmod(rest,600)
    return f'{hours:02d}:{minutes:02d}:{rest//10:02d}.{rest%10}'
