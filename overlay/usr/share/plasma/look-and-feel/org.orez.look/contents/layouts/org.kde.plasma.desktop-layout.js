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
