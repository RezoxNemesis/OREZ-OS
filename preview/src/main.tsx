import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Screen = 'Workspace' | 'Settings' | 'Connect' | 'Installation';
type Preferences = { glass: boolean; motion: boolean; contrast: boolean };
const defaults: Preferences = { glass: true, motion: !matchMedia('(prefers-reduced-motion: reduce)').matches, contrast: false };
function readPreferences(): Preferences {
  try {
    const value = JSON.parse(localStorage.getItem('orez.preview.preferences.v1') || '{}');
    return Object.fromEntries(Object.entries(defaults).map(([key, fallback]) => [key, typeof value?.[key] === 'boolean' ? value[key] : fallback])) as Preferences;
  } catch { return { ...defaults }; }
}
function Icon({ name }: { name: Screen | 'Arrow' | 'Folder' }) {
  const paths = {
    Workspace: 'M3 4h18v16H3z M9 4v16',
    Settings: 'M4 6h16 M4 12h16 M4 18h16 M8 3v6 M16 9v6 M10 15v6',
    Connect: 'M8 8V4h8v16H8v-4 M4 12h8 M10 10l2 2-2 2',
    Installation: 'M12 3v12 M7 10l5 5 5-5 M4 16v5h16v-5',
    Arrow: 'M5 19 19 5 M6 5h13v13',
    Folder: 'M3 6h7l2 3h9v11H3z'
  };
  return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
const icons: Record<Screen, React.ReactNode> = { Workspace: <Icon name="Workspace" />, Settings: <Icon name="Settings" />, Connect: <Icon name="Connect" />, Installation: <Icon name="Installation" /> };

function App() {
  const [screen, setScreen] = useState<Screen>('Workspace');
  const [preferences, setPreferences] = useState(readPreferences);
  const [notice, setNotice] = useState('');
  const [paired, setPaired] = useState(false);
  const [clipboard, setClipboard] = useState(false);
  const [filter, setFilter] = useState('');
  const [update, setUpdate] = useState<ServiceWorker | null>(null);
  React.useEffect(() => {
    if (import.meta.env.PROD && !document.documentElement.dataset.portable && /^https?:$/.test(location.protocol) && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register('./sw.js').then(registration => {
        if (registration.waiting) setUpdate(registration.waiting);
        registration.addEventListener('updatefound', () => {
          const worker = registration.installing;
          worker?.addEventListener('statechange', () => {
            if (worker.state === 'installed' && navigator.serviceWorker.controller) setUpdate(worker);
          });
        });
      }).catch(() => setNotice('Offline preview unavailable in this browser; the online preview still works.'));
      const reload = () => { if (sessionStorage.getItem('orez.preview.update')) { sessionStorage.removeItem('orez.preview.update'); location.reload(); } };
      navigator.serviceWorker.addEventListener('controllerchange', reload);
      return () => navigator.serviceWorker.removeEventListener('controllerchange', reload);
    }
  }, []);
  function save(next: Preferences) {
    setPreferences(next);
    try { localStorage.setItem('orez.preview.preferences.v1', JSON.stringify(next)); setNotice('Preview appearance saved on this device.'); }
    catch { setNotice('Storage unavailable. Changes last until this page closes.'); }
  }
  function navigate(next: Screen) { setScreen(next); setNotice(''); }
  function toggle(key: keyof Preferences) { save({ ...preferences, [key]: !preferences[key] }); }
  const matches = (text: string) => text.toLowerCase().includes(filter.toLowerCase().trim());
  return <div className={`app ${preferences.glass ? '' : 'opaque'} ${preferences.motion ? '' : 'still'} ${preferences.contrast ? 'contrast' : ''}`}>
    <a className="skip" href="#main">Skip to workspace</a>
    <header className="topbar">
      <a className="wordmark" href="#" onClick={e => { e.preventDefault(); navigate('Workspace'); }}>OREZ<span>静</span></a>
      <span className="preview-badge"><i /> Design preview</span>
      <span className="edition">INK / 01</span>
    </header>
    <div className="disclosure">Interactive browser preview · No access to your disks, phone, clipboard or system settings.</div>
    {update && <div className="update">A preview update is ready. <button onClick={() => { sessionStorage.setItem('orez.preview.update', '1'); update.postMessage('ACTIVATE_UPDATE'); }}>Apply update</button></div>}
    <main id="main" tabIndex={-1}>
      {screen === 'Workspace' && <section className="workspace" aria-label="Desktop design preview">
        <div className="intro"><span className="eyebrow">A little space to think.</span><h1>Make room<br />for what matters.</h1><p>A quiet workspace for your ideas.<br />Built around your control.</p></div>
        <div className="workspace-grid">
          <article className="glass welcome"><div className="card-heading"><span className="eyebrow">YOUR WORKSPACE</span><span className="small-tag">Preview</span></div><h2>Begin anywhere.</h2><p>Explore OREZ’s visual direction on your phone or computer.</p>
            <div className="quick-actions"><button onClick={() => navigate('Settings')}><Icon name="Settings" /> Personalize <Icon name="Arrow" /></button><button onClick={() => navigate('Connect')}><Icon name="Connect" /> Explore Connect <Icon name="Arrow" /></button></div>
          </article>
          <article className="glass files"><div className="card-heading"><span className="eyebrow">A PLACE FOR YOUR IDEAS</span><span aria-hidden="true">▤</span></div><h2>Everyday essentials</h2><div className="file-row"><span className="folder"><Icon name="Folder" /></span><div>Projects<small>Example folder</small></div><Icon name="Arrow" /></div><div className="file-row"><span className="folder"><Icon name="Folder" /></span><div>Studio<small>Example folder</small></div><Icon name="Arrow" /></div><p className="caption">Illustrative folders. Your real files stay private.</p></article>
          <article className="glass status"><div className="card-heading"><span className="eyebrow">ENGINEERING STATUS</span><span className="status-dot" /></div><h2>Taking shape.</h2><p>Source components exist. A usable ISO desktop and safe installation still need verification.</p><button className="text-button" onClick={() => navigate('Installation')}>View installation gates <span>→</span></button></article>
        </div>
        <span className="wallpaper-caption">PAPER / INK / STILLNESS</span>
      </section>}
      {screen === 'Settings' && <section className="panel glass"><div className="section-heading"><div><span className="eyebrow">MAKE IT YOURS</span><h1>Settings</h1></div><span className="section-icon"><Icon name="Settings" /></span></div><p>These preferences only affect this browser preview.</p><label className="search-label" htmlFor="settings-search">Search preview settings</label><input id="settings-search" type="search" value={filter} onChange={e => setFilter(e.target.value)} placeholder="Appearance, motion, contrast…" />
        <div className="settings-list">{([
          ['glass', 'Frosted panels', 'Translucency and soft blur. Disable for solid, lighter panels.'],
          ['motion', 'Gentle motion', 'Short interface transitions. Your system’s reduced-motion preference always takes priority.'],
          ['contrast', 'High contrast', 'Solid panels, darker borders and stronger text contrast.']
        ] as [keyof Preferences, string, string][]).filter(([, label, help]) => matches(`${label} ${help}`)).map(([key, label, help]) => <div className="setting" key={key}><div><h2 id={`${key}-label`}>{label}</h2><p id={`${key}-help`}>{help}</p></div><button className="toggle" role="switch" aria-checked={preferences[key]} aria-labelledby={`${key}-label`} aria-describedby={`${key}-help`} onClick={() => toggle(key)}><span /><span className="sr-only">{preferences[key] ? 'On' : 'Off'}</span></button></div>)}</div>
        <div className="info-box"><strong>Visible. Reversible. Yours.</strong><p>Saved locally in this browser. No account or administrator access is used. Clear site data to remove all preview data.</p></div><button className="secondary" onClick={() => { save({ ...defaults }); setFilter(''); setNotice('Preview preferences restored to defaults.'); }}>Reset preview preferences</button>
      </section>}
      {screen === 'Connect' && <section className="panel glass"><div className="section-heading"><div><span className="eyebrow">CLOSER, BY DESIGN</span><h1>OREZ Connect</h1></div><span className="section-icon" aria-hidden="true">⌁</span></div><p>A local-first connection between your phone and desktop.</p><div className="info-box"><strong>Interactive demonstration</strong><p>This screen does not discover devices, create a connection, transfer files, or read your clipboard. Native integration will use KDE Connect.</p></div>
        <div className="device"><span className="phone-outline" aria-hidden="true">▯</span><div><h2>Realme P1 Speed</h2><p>{paired ? 'Example device · simulated pairing' : 'Example device · not connected'}</p></div><span className="small-tag">Demo</span></div>
        {!paired ? <button className="primary" onClick={() => { setPaired(true); setNotice('Demo device paired. No real connection was made.'); }}>Try demo pairing</button> : <><div className="setting"><div><h2 id="clipboard-label">Clipboard permission</h2><p>Demonstrates consent only. No clipboard API is called.</p></div><button className="toggle" role="switch" aria-checked={clipboard} aria-labelledby="clipboard-label" onClick={() => setClipboard(!clipboard)}><span /></button></div><div className="info-box"><strong>Transfers are unavailable in this preview.</strong><p>Production pairing, encrypted transfers, Android permissions and device revocation require separate tests on real devices.</p></div><button className="secondary" onClick={() => { setPaired(false); setClipboard(false); setNotice('Demo pairing and permissions revoked.'); }}>Revoke demo device</button></>}
        <p className="caption">USB 2.0 file transfer is planned. USB-C video output is not assumed.</p>
      </section>}
      {screen === 'Installation' && <section className="panel glass"><div className="section-heading"><div><span className="eyebrow">CONFIDENCE BEFORE COMMITMENT</span><h1>Installation</h1></div><span className="section-icon" aria-hidden="true">↓</span></div><p>The real installer remains blocked until safety gates pass.</p><div className="blocked"><span aria-hidden="true">⊘</span><div><h2>Not ready for installation</h2><p>No drive has been detected or selected. This preview cannot write to disks.</p></div></div><ul className="gate-list"><li><span>01</span><div>Visible desktop in a qualified virtual machine<small>Pending</small></div></li><li><span>02</span><div>Disposable-disk installation and reboot<small>Pending</small></div></li><li><span>03</span><div>Backup, recovery and encryption tests<small>Pending</small></div></li><li><span>04</span><div>RTX 3050, networking and Secure Boot<small>Physical hardware validation pending</small></div></li></ul><button className="primary" disabled>Installation unavailable</button><p className="caption">Keep your Windows recovery USB. Future testing uses a separate USB and explicit disk confirmation.</p></section>}
      <div className="notice" role="status" aria-live="polite">{notice}</div>
    </main>
    <nav className="dock glass" aria-label="Main navigation">{(Object.keys(icons) as Screen[]).map(name => <button key={name} aria-current={screen === name ? 'page' : undefined} onClick={() => navigate(name)}><span aria-hidden="true">{icons[name]}</span><span>{name}</span></button>)}</nav>
    <footer>OREZ / Design study <span>No telemetry · No system access</span></footer>
  </div>;
}

createRoot(document.getElementById('root')!).render(<App />);
