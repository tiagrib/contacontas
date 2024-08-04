import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: mainWindow
    width: 800
    height: 800
    visible: true
    title: "ConCoWin"

    TabBar {
        id: tabBar
        width: parent.width

        TabButton {
            text: "Classifier"
        }
        TabButton {
            text: "Movements"
        }
        TabButton {
            text: "Summary"
        }
    }

    StackLayout {
        id: stackLayout
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        currentIndex: tabBar.currentIndex

        Loader {
            source: "classifier_tab.qml"
        }
        Item {
            id: movementsTab
            ColumnLayout {
                spacing: 10
                anchors.fill: parent

                Button {
                    text: "Show Non-Internal Only"
                    onClicked: movs_backend.setNonInternalFilter()
                }
                Button {
                    text: "Show Internal Only"
                    onClicked: movs_backend.setInternalOnlyFilter()
                }
                Button {
                    text: "Show All"
                    onClicked: movs_backend.setAllFilter()
                }

                Text { text: "Filter by account:" }
                ListView {
                    id: accountsList
                    property int hovered_index: -1
                    clip: true
                    Layout.fillWidth: true
                    height: 150
                    model: movs_backend.accountsModel

                    delegate: Item {
                        id: delegateItem
                        width: accountsList.width
                        height: Math.max(textItem.implicitHeight, mouseArea.implicitHeight) + 10
                        Rectangle {
                            anchors.fill: parent
                            color: accountsList.hovered_index === index ? "cadetblue" : (accountsList.currentIndex === index ? "darkcyan" : "lightgray")
                        }
                        Text {
                            id: textItem
                            text: model.display
                            color: "black"
                        }
                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: accountsList.currentIndex = index
                            onEntered: accountsList.hovered_index = index
                            onExited: if (accountsList.hovered_index === index) { accountsList.hovered_index = -1}
                        }
                    }
                    
                    ScrollBar.vertical: ScrollBar {}
                }

                Text { text: "Filter by tag:" }
                ListView {
                    id: tagsList
                    property int hovered_index: -1
                    clip: true
                    Layout.fillWidth: true
                    height: 300
                    model: movs_backend.tagsModel

                    delegate: Item {
                        id: delegateItem
                        width: tagsList.width
                        height: Math.max(textItem.implicitHeight, mouseArea.implicitHeight) + 10
                        Rectangle {
                            anchors.fill: parent
                            color: tagsList.hovered_index === index ? "cadetblue" : (tagsList.currentIndex === index ? "darkcyan" : "lightgray")
                        }
                        Text {
                            id: textItem
                            text: model.display
                            color: "black"
                        }
                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: tagsList.currentIndex = index
                            onEntered: tagsList.hovered_index = index
                            onExited: if (tagsList.hovered_index === index) { tagsList.hovered_index = -1}
                        }
                    }
                    
                    ScrollBar.vertical: ScrollBar {}
                }

                Text { text: "end" }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"
                }
            }

            Component.onCompleted: {
                console.log("ListView model count: " + accountsList.count)
                console.log("movsBackend: " + movs_backend)
                console.log("ListView width: " + accountsList.width)
            }
        }
        Loader {
            source: "summary_tab.qml"
        }
    }
}