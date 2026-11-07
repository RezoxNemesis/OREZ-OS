/* OREZ default desktop: Kubuntu's tested bottom taskbar (Start menu, pinned
 * apps, system tray, clock) plus the OREZ wallpaper. Runs once for a new user. */
const plasma_obj = getApiVersion(1);
loadTemplate('org.kubuntu.desktop.defaultPanel');
const desktops_list = desktopsForActivity(currentActivity());
for (let i = 0; i < desktops_list.length; i++) {
  const d = desktops_list[i];
  d.wallpaperPlugin = 'org.kde.image';
  d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
  d.writeConfig('Image', 'file:///usr/share/wallpapers/OREZ-Rest/');
}

// Taskbar: OREZ apps and Brave pinned (the template pins the snap browser).
panels().forEach(function (p) {
  p.widgets().forEach(function (w) {
    if (w.type === 'org.kde.plasma.icontasks' || w.type === 'org.kde.plasma.taskmanager') {
      w.currentConfigGroup = ['General'];
      w.writeConfig('launchers', ['applications:orez-settings.desktop', 'applications:org.kde.dolphin.desktop',
        'applications:brave-browser.desktop', 'applications:org.kde.konsole.desktop', 'applications:orez-store.desktop']);
    }
  });
});
