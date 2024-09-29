import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 640
    height: 480
    TabBar {
        anchors.fill: parent
        TabButton {
            text: "Files"
            ListView {
                id: mListViewId
                clip: true
                anchors.fill: parent
                model: backend.model
                delegate: Text{
                    text: model.display
                }
                ScrollBar.vertical: ScrollBar {}
            }
        }
    }
    Component.onCompleted: console.log("ListView model count: " + mListViewId.count)
}