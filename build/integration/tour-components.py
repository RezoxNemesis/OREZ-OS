"""Real component tour. Ordinary account, isolated offline Xvfb, never a boot claim."""
import json,os,subprocess,sys,time
from pathlib import Path
assert os.getuid()==1500 and Path('/.dockerenv').exists()
E=Path('/evidence/tour-components');E.mkdir(exist_ok=False)
results=[];children=[]
def run(*args):return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT,timeout=20).strip()
def shot(name):run('scrot',str(E/(name+'.png')))
def launch(name,args):
    with (E/(name+'.log')).open('w') as log:p=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT)
    children.append(p);return p
def visible(name):
    for _ in range(40):
        p=subprocess.run(['xdotool','search','--onlyvisible','--name',name],text=True,capture_output=True)
        if p.returncode==0 and p.stdout.strip():return p.stdout.splitlines()[-1]
        time.sleep(.1)
    raise AssertionError('Visible window missing: '+name)
def keys(*args):run('xdotool','key','--clearmodifiers',*args)
def greeter():
    p=launch('greeter',['sddm-greeter-qt6','--test-mode','--theme','/input/orez-theme']);time.sleep(3)
    assert p.poll() is None;shot('01-login-test-mode')
    run('xdotool','mousemove','220','360','click','1');keys('ctrl+a');run('xdotool','type','--clearmodifiers','orez-owner');keys('Tab','Return');time.sleep(.5)
    shot('02-login-empty-password');run('xdotool','type','--clearmodifiers','UI-test-only');time.sleep(.5);shot('03-login-password-masked');keys('ctrl+a','BackSpace')
    p.terminate();p.wait(timeout=10)
    return {'scope':'Actual SDDM test-mode rendering; input requires visual review','authentication_tested':False,'session_unavailable_without_render_device':True,'full_boot':False}
def installer():
    p=launch('installer-guard',['bash','/input/orez-installer-guard']);w=visible('Installer Unavailable');run('xdotool','windowfocus','--sync',w);shot('04-installer-current-safety-block');keys('Return');p.wait(timeout=10)
    assert p.returncode==78,p.returncode
    return {'guard_exit':78,'installation_performed':False,'storage_accessed':False,'scope':'Actual live-media safety guard only; no functional installer claimed'}
def connect():
    p=launch('connect',['kdeconnect-app']);time.sleep(3);assert p.poll() is None
    assert run('xdotool','search','--onlyvisible','--pid',str(p.pid))
    shot('05-phone-connect-no-devices');p.terminate();p.wait(timeout=10)
    return {'scope':'Native KDE Connect window; offline test container','paired_phone':False,'transfer_mirroring_tested':False}
def game():
    files=run('dpkg-query','-L','supertux-data').splitlines();level=next(p for p in files if p.endswith('/welcome_antarctica.stl'))
    p=launch('supertux',['/usr/games/supertux2','--fullscreen','--geometry','1440x900','--show-pos','--show-fps','--disable-sound','--disable-music',level]);time.sleep(6)
    assert p.poll() is None;w=visible('SuperTux');run('xdotool','windowfocus','--sync',w)
    # SDL polls keys per frame: hold the real key across software-rendered
    # frames, as the existing everyday game test does.
    run('xdotool','keydown','space');time.sleep(.4);run('xdotool','keyup','space')
    from PIL import Image
    # Wait for the packaged snowy level, not just its black introduction.
    for attempt in range(12):
        time.sleep(.5);shot('06-game-scene-wait-'+str(attempt))
        pixels=Image.open(E/('06-game-scene-wait-'+str(attempt)+'.png')).convert('RGB')
        histogram=pixels.convert('L').histogram()
        bright=sum(histogram[61:])/(pixels.width*pixels.height)
        if bright>.4:break
    else:raise AssertionError('Playable scene was not established')
    shot('06-game-fullscreen-before')
    geometry=dict(line.split('=',1) for line in run('xdotool','getwindowgeometry','--shell',w).splitlines());assert geometry['WIDTH']=='1440' and geometry['HEIGHT']=='900',geometry
    run('xdotool','keydown','Right');time.sleep(1.1);keys('space');time.sleep(.4);run('xdotool','keyup','Right');time.sleep(.5);shot('07-game-fullscreen-after-input')
    keys('Escape');time.sleep(.5);shot('08-game-pause-menu');assert p.poll() is None
    p.terminate();p.wait(timeout=10)
    return {'fullscreen_geometry':geometry,'keys':'Right/Space/Escape delivered; position/scene reviewed in screenshots','audio_tested':False,'gpu_performance_tested':False,'scope':'Native SuperTux on software rendering; not Android or AAA qualification'}
try:
    for name,fn in [('login-theme',greeter),('installer-guard',installer),('phone-connect',connect),('fullscreen-game',game)]:
        selection=os.environ.get('OREZ_TOUR_COMPONENT_FILTER')
        if selection and selection!=name:continue
        try:r={'name':name,'status':'passed','detail':fn()}
        except Exception as error:r={'name':name,'status':'failed','error':repr(error)}
        results.append(r);shot(name+'-result');print(json.dumps(r),flush=True)
finally:
    for p in children:
        if p.poll() is None:p.terminate()
    (E/'results.json').write_text(json.dumps(results,indent=2)+'\n')
sys.exit(any(r['status']=='failed' for r in results))
