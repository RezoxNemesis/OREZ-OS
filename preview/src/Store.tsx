import React, { useState } from 'react';
import catalog from '../../overlay/usr/share/orez/store-catalog.json';

export function Store() {
  const [query, setQuery] = useState('');
  const [format, setFormat] = useState('all');
  const [selected, setSelected] = useState('youtube');
  const apps = catalog.apps.filter(app => (format === 'all' || app.kind === format) && `${app.name} ${app.publisher} ${app.category}`.toLowerCase().includes(query.trim().toLowerCase()));
  const app = apps.find(item => item.id === selected) || apps[0];
  return <section className="panel glass store-panel" aria-label="OREZ Store preview">
    <div className="section-heading"><div><span className="eyebrow">YOUR APPS. YOUR CHOICE.</span><h1>OREZ Store</h1></div><span className="small-tag">Catalog preview</span></div>
    <p>Free to use. Clear permissions. One place for your everyday essentials.</p>
    <div className="store-disclosure">This browser preview cannot install or launch apps. YouTube, Instagram and the requested games are actual Android app targets, not web apps. Official Linux desktop editions are preferred unchanged. Android installation, direct keyboard/mouse support and gameplay remain pending.</div>
    <div className="store-filters"><div><label htmlFor="app-search">Search apps</label><input id="app-search" type="search" placeholder="YouTube, games, browsers…" value={query} onChange={event => setQuery(event.target.value)} /></div><div><label htmlFor="app-format">App format</label><select id="app-format" value={format} onChange={event => setFormat(event.target.value)}><option value="all">All apps</option><option value="native">Native Linux</option><option value="android">Android</option></select></div></div>
    <div className="store-layout"><div className="store-apps" aria-label="App catalog">{apps.map(item => <button key={item.id} className={`store-app ${app?.id === item.id ? 'selected' : ''}`} aria-pressed={app?.id === item.id} onClick={() => setSelected(item.id)}><span className="store-monogram" aria-hidden="true">{item.name.slice(0,1)}</span><span><strong>{item.name}</strong><small>{item.kind === 'native' ? 'Native Linux' : 'Android · pending'}</small></span></button>)}{!apps.length && <p role="status">No matching apps. Try another search.</p>}</div>
      {app && <article className="store-detail" aria-label={`${app.name} details`}><span className="eyebrow">{app.publisher}</span><h2>{app.name}</h2><p>{app.summary}</p><div className="store-price">Free entry option <small>Optional paid features remain publisher-controlled.</small></div>
        <h3>Compatibility</h3><p>{app.compatibility}</p><h3>Access & your data</h3><p>{app.privacy}</p><h3>Owner control</h3><p>No automatic administrator grants or purchases. Other software sources and your terminal remain available.</p>
        <button className="primary" disabled>{app.kind === 'android' ? 'Android runtime pending' : 'Use the native OREZ Store'}</button><a className="store-source" href={app.url} target="_blank" rel="noopener noreferrer">Official website for {app.name} ↗</a>
      </article>}
    </div>
  </section>;
}
