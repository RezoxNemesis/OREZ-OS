# OREZ interactive design preview

React/TypeScript, Vite, responsive CSS and a small service worker. This is an interactive **browser design preview**, not Linux, an APK, an Android replacement, a real file manager, an AI agent, or a remote administration tool.

Working interactions: screen navigation; searchable appearance controls; local preference persistence and reset; demo-device pairing/consent/revocation; blocked installation screen; keyboard access and reduced motion. Only appearance preferences persist. Demo phone state resets on reload. No clipboard, filesystem, camera, notification, discovery, pairing or shell APIs are used. Fonts/assets are local; no telemetry or remote services.

## Run and test

Use Node 24 and run `npm ci --ignore-scripts` at repository root. `npm run preview:dev` serves on loopback. Build with `npm run preview:build`. Run browser acceptance with the evidence wrapper described in `docs/TESTING_AND_SCREENSHOTS.md`.

Production output is `dist/preview/`; deploy this directory only to an explicitly selected static HTTPS host. Relative paths support a repository subdirectory such as `/OREZ-OS/`. No website deployment or domain is assumed. Service-worker updates offer a visible Apply update button; caches are scoped to this preview's URL. Clear browser site data to remove cached assets and preferences.

The production bundle includes `THIRD_PARTY_NOTICES.txt` with the installed React, React DOM, Scheduler and Vite licence notices. The portable HTML embeds the same notices in its source. Original OREZ source and artwork remain owner-reserved; no public OS distribution is authorized by generating these development previews.

## Try on Android

The build also exports **`dist/OREZ-Preview.html`**, a single file with its scripts, style and wallpaper embedded. Download it and open it in a browser that supports local HTML. Some Android file viewers suppress JavaScript; those viewers will not run this preview. For normal PWA installation and offline caching, use the HTTPS-hosted version and the browser's Install/Add to Home screen control. The downloaded file itself is not an installable Android app. Realme device testing is still pending.

Phone viewport tests use Chromium at 412×915; this proves layout behavior in an emulator viewport, not Realme hardware. Desktop tests use 1440×960. Real mobile touch, browser installation, OS back navigation and accessibility services still require device testing.

The wallpaper is the existing original OREZ SVG. The preview does not modify the native Plasma theme. Native design work, including glass settings, launcher, login, installer, and accessible KCMs, remains separately tracked.

References: [React](https://react.dev/), [Vite production builds](https://vite.dev/guide/build), [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API), [Web app manifests](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest).
