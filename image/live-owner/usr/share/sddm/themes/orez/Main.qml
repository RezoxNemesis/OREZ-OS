import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#eeeae3"
    property bool waiting: false
    property string feedback: ""
    property date now: new Date()

    function submit() {
        if (waiting) return;
        if (!username.text.trim() || !password.text) {
            feedback = qsTr("Enter your username and password.");
            password.forceActiveFocus();
            return;
        }
        if (session.count === 0 || session.currentIndex < 0) {
            feedback = qsTr("No desktop session is available. Restart with verified media.");
            return;
        }
        waiting = true;
        feedback = qsTr("Signing in…");
        sddm.login(username.text.trim(), password.text, session.currentIndex);
    }

    Image {
        anchors.fill: parent
        source: config.stringValue("Background")
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    Timer { interval: 60000; running: true; repeat: true; onTriggered: root.now = new Date() }
    Column {
        anchors { right: parent.right; top: parent.top; margins: 32 }
        spacing: 4
        Label { text: Qt.formatTime(root.now, "hh:mm"); color: "#222"; font.pixelSize: 32; font.weight: Font.Light }
        Label { text: Qt.formatDate(root.now, Qt.DefaultLocaleLongDate); color: "#333"; font.pixelSize: 14 }
    }

    Rectangle {
        width: Math.min(440, root.width - 48)
        height: form.implicitHeight + 64
        anchors.left: parent.left
        anchors.leftMargin: Math.max(24, Math.min(100, root.width * 0.07))
        anchors.verticalCenter: parent.verticalCenter
        radius: 20
        color: config.boolValue("SolidPanel") ? "#faf9f6" : "#effaf9f6"
        border.color: "#bdb9b1"
        border.width: 1

        ColumnLayout {
            id: form
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 32 }
            spacing: 14
            Label { text: "O R E Z   O S"; color: "#333"; font.pixelSize: 15; font.weight: Font.DemiBold }
            Label { text: qsTr("Welcome home."); color: "#151515"; font.pixelSize: 34; font.weight: Font.Light }
            Label { text: qsTr("Your workspace. Your control."); color: "#454545"; font.pixelSize: 14; Layout.bottomMargin: 10 }

            Label { text: qsTr("Username"); color: "#242424"; font.pixelSize: 14 }
            TextField {
                id: username
                objectName: "ownerUsername"
                Layout.fillWidth: true
                text: userModel.lastUser
                enabled: !root.waiting
                font.pixelSize: 16
                color: "#111"
                padding: 12
                Accessible.name: qsTr("Username")
                background: Rectangle { color: "#fff"; radius: 8; border.color: username.activeFocus ? "#222" : "#999"; border.width: username.activeFocus ? 2 : 1 }
                KeyNavigation.tab: password
                onTextEdited: root.feedback = ""
                onAccepted: password.forceActiveFocus()
            }
            Label { text: qsTr("Password"); color: "#242424"; font.pixelSize: 14 }
            TextField {
                id: password
                objectName: "ownerPassword"
                Layout.fillWidth: true
                enabled: !root.waiting
                echoMode: TextInput.Password
                inputMethodHints: Qt.ImhHiddenText | Qt.ImhNoPredictiveText | Qt.ImhSensitiveData
                placeholderText: qsTr("Your owner password")
                placeholderTextColor: "#666"
                color: "#111"
                font.pixelSize: 16
                padding: 12
                Accessible.name: qsTr("Password")
                background: Rectangle { color: "#fff"; radius: 8; border.color: password.activeFocus ? "#222" : "#999"; border.width: password.activeFocus ? 2 : 1 }
                KeyNavigation.tab: session
                onTextEdited: root.feedback = ""
                onAccepted: root.submit()
            }
            Label { text: qsTr("Caps Lock is on"); visible: keyboard.capsLock; color: "#222"; font.pixelSize: 13 }
            Label { text: qsTr("Desktop session"); color: "#242424"; font.pixelSize: 14 }
            ComboBox {
                id: session
                objectName: "desktopSession"
                Layout.fillWidth: true
                enabled: !root.waiting
                model: sessionModel
                textRole: "name"
                currentIndex: count > 0 ? Math.max(0, Math.min(sessionModel.lastIndex, count - 1)) : -1
                displayText: count > 0 && currentIndex >= 0 ? currentText : qsTr("No desktop session found")
                Accessible.name: qsTr("Desktop session")
                KeyNavigation.tab: signIn
            }
            Button {
                id: signIn
                objectName: "ownerSignIn"
                Layout.fillWidth: true
                text: root.waiting ? qsTr("Signing in…") : qsTr("Sign in")
                enabled: !root.waiting && session.count > 0 && session.currentIndex >= 0
                Accessible.name: text
                contentItem: Text { text: signIn.text; color: "#fff"; font.pixelSize: 16; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { color: signIn.down ? "#444" : "#222"; radius: 8; border.color: signIn.activeFocus ? "#777" : "#222"; border.width: signIn.activeFocus ? 3 : 1; implicitHeight: 48 }
                KeyNavigation.tab: username
                onClicked: root.submit()
            }
            Label {
                objectName: "loginFeedback"
                text: root.feedback
                visible: text.length > 0
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#252525"
                Accessible.name: text
                font.pixelSize: 14
            }
            Label { text: qsTr("Sign-in uses your local OREZ account."); color: "#555"; font.pixelSize: 12; Layout.topMargin: 4 }
        }
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            root.waiting = false;
            root.feedback = qsTr("Sign-in failed. Check your details and try again.");
            password.clear();
            password.forceActiveFocus();
        }
        function onLoginSucceeded() { password.clear(); }
    }
    Component.onCompleted: {
        if (username.text.length) password.forceActiveFocus();
        else username.forceActiveFocus();
    }
}
