import QtQuick

// OREZ sign-in splash: shown while the desktop loads after login.
Rectangle {
    id: root
    color: "#F6F4EF"
    property int stage

    Image {
        id: enso
        source: "images/enso.svg"
        width: 150; height: 150
        sourceSize.width: 300; sourceSize.height: 300
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -30
        RotationAnimator on rotation { from: 0; to: 360; duration: 6000; loops: Animation.Infinite }
    }
    Image {
        source: "images/wordmark.png"
        anchors.top: enso.bottom
        anchors.topMargin: 26
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
