import QtQuick

// OREZ installation slideshow (slideshowAPI 2): one calm, static page.
Item {
    id: root
    function onActivate() { }
    function onLeave() { }
    Rectangle { anchors.fill: parent; color: "#F6F4EF" }
    Image {
        anchors.fill: parent
        source: "welcome.png"
        fillMode: Image.PreserveAspectCrop
        opacity: 0.9
    }
    Text {
        anchors { left: parent.left; bottom: parent.bottom; margins: 28 }
        text: "Installing OREZ OS…\nYour files stay only where you chose to install."
        color: "#161616"
        font.pixelSize: 18
    }
}
