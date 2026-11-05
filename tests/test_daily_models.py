import datetime as dt
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('daily_models',ROOT/'overlay/usr/lib/orez/daily_models.py')
daily=importlib.util.module_from_spec(spec);spec.loader.exec_module(daily)


class DailyModelsTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_calendar_persists_unicode_and_parameterized_titles(self):
        model=daily.Calendar(self.root/'calendar')
        title="日本語'); DROP TABLE events; --"
        event=model.save('2026-11-05',title,'local notes')
        model.close();model=daily.Calendar(self.root/'calendar')
        self.assertEqual(model.events('2026-11-05')[0][2],title)
        model.save('2026-11-06','Edited','new notes',event)
        self.assertEqual(model.events('2026-11-05'),[])
        self.assertEqual(model.events('2026-11-06')[0][2],'Edited')
        model.delete(event);self.assertEqual(model.events('2026-11-06'),[]);model.close()
    def test_unknown_events_invalid_dates_and_empty_titles_are_rejected(self):
        model=daily.Calendar(self.root/'calendar')
        for day,title in [('2026-02-30','ok'),('9999-12-31','ok'),('2026-11-05',''),('2026-11-05','Injected\nSUMMARY:bad')]:
            with self.assertRaises(ValueError):model.save(day,title)
        with self.assertRaises(ValueError):model.delete(444)
        with self.assertRaises(ValueError):model.save('2026-11-05','unknown',event_id=444)
        self.assertEqual(model.events('2026-11-05'),[]);model.close()
    def test_calendar_export_escapes_folds_utf8_and_ends_next_day(self):
        model=daily.Calendar(self.root/'calendar')
        model.save('2024-02-29','日本語'*35,'Line one\nBEGIN:VEVENT\ncomma,semi;backslash\\')
        text=model.export_ics();unfolded=text.replace('\r\n ','')
        self.assertIn('DTEND;VALUE=DATE:20240301',unfolded)
        self.assertIn('DESCRIPTION:Line one\\nBEGIN:VEVENT\\ncomma\\,semi\\;backslash\\\\',unfolded)
        self.assertEqual(unfolded.count('\r\nBEGIN:VEVENT\r\n'),1)
        self.assertTrue(all(len(line.encode())<=75 for line in text.split('\r\n')))
        model.close()
    def test_root_and_aliased_storage_are_refused(self):
        with patch.object(daily.os,'geteuid',return_value=0),self.assertRaises(ValueError):daily.Calendar(self.root/'bad')
        target=self.root/'target';target.mkdir();alias=self.root/'alias';alias.symlink_to(target)
        with self.assertRaises(ValueError):daily.ClockSettings(alias)
        self.assertEqual(list(target.iterdir()),[])
    def test_existing_foreign_database_is_not_replaced(self):
        root=self.root/'calendar';root.mkdir();path=root/'events.sqlite3'
        db=sqlite3.connect(path);db.execute('CREATE TABLE keep_me(value)');db.close();before=path.read_bytes()
        with self.assertRaises(ValueError):daily.Calendar(root)
        self.assertEqual(path.read_bytes(),before)
    def test_private_database_and_settings_permissions(self):
        calendar=daily.Calendar(self.root/'calendar');calendar.close()
        settings=daily.ClockSettings(self.root/'time');settings.save('Asia/Kolkata','12h')
        for path in [self.root/'calendar/events.sqlite3',settings.path]:self.assertEqual(path.stat().st_mode&0o777,0o600)
        for path in [self.root/'calendar',self.root/'time']:self.assertEqual(path.stat().st_mode&0o777,0o700)
    def test_reuz_timezone_formats_and_day_boundary_persist(self):
        settings=daily.ClockSettings(self.root/'time');self.assertEqual(settings.timezone,'UTC')
        settings.save('Asia/Kolkata','12h');settings=daily.ClockSettings(self.root/'time')
        time,date=settings.display(dt.datetime(2026,11,5,20,0,tzinfo=dt.timezone.utc))
        self.assertEqual(time,'01:30:00 AM');self.assertIn('06 November 2026',date)
    def test_invalid_clock_preferences_do_not_overwrite_previous_choice(self):
        settings=daily.ClockSettings(self.root/'time');settings.save('UTC','24h');before=settings.path.read_bytes()
        for zone,format in [('/etc/shadow','24h'),('not-a-zone','24h'),('UTC','other')]:
            with self.assertRaises(ValueError):settings.save(zone,format)
        self.assertEqual(settings.path.read_bytes(),before)
    def test_corrupt_clock_configuration_is_not_silently_reset(self):
        root=self.root/'time';root.mkdir();path=root/'settings.json';path.write_text('broken')
        with self.assertRaises(ValueError):daily.ClockSettings(root)
        self.assertEqual(path.read_text(),'broken')
    def test_stopwatch_pause_resume_laps_and_reset(self):
        clock=[0.];watch=daily.Stopwatch(lambda:clock[0]);watch.start();clock[0]=12.5
        self.assertEqual(watch.lap(),12.5);watch.pause();clock[0]=40.;self.assertEqual(watch.elapsed(),12.5)
        watch.start();clock[0]=42.;self.assertEqual(watch.elapsed(),14.5)
        watch.reset();self.assertEqual(watch.elapsed(),0);self.assertEqual(watch.laps,[])
    def test_timer_suspended_elapsed_time_and_exactly_one_completion(self):
        clock=[0.];timer=daily.Countdown(lambda:clock[0]);timer.start(60);clock[0]=120
        self.assertEqual(timer.remaining(),0);self.assertTrue(timer.check_finished());self.assertFalse(timer.check_finished())
        timer.start(10);clock[0]=125;timer.pause();clock[0]=190;self.assertEqual(timer.remaining(),5)
        timer.start();clock[0]=195;self.assertTrue(timer.check_finished())
        timer.reset();self.assertEqual(timer.remaining(),0)
    def test_timer_rejects_unbounded_or_zero_duration(self):
        timer=daily.Countdown()
        for seconds in [0,-1,86401,float('nan')]:
            with self.assertRaises(ValueError):timer.start(seconds)
    def test_web_youtube_is_explicit_and_preserves_browser_sandbox(self):
        script=(ROOT/'overlay/usr/bin/orez-youtube').read_text()
        self.assertIn('https://www.youtube.com/',script)
        self.assertIn('"$EUID" == 0',script)
        for unsafe in ['--no-sandbox','sudo ','curl ','--disable-web-security']:
            self.assertNotIn(unsafe,script)
        self.assertIn('Name=YouTube (Web)',(ROOT/'overlay/usr/share/applications/orez-youtube.desktop').read_text())

