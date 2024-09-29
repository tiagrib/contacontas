import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Matplotlib 1.0

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
            Layout.fillHeight: true
            Layout.fillWidth: true

            RowLayout {
                spacing: 10
                Layout.fillHeight: true
                Layout.fillWidth: true

                ColumnLayout {                    
                    Layout.preferredWidth: 200

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

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "transparent"
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true

                    RowLayout {
                        Label {
                            text: "Filter by Date:"
                        }

                        Label {
                            id: fbds_minLabel
                            text: "ALL"
                        }

                        Slider {
                            id: filterByDateSlider
                            Layout.fillWidth: true
                            Layout.preferredWidth: parent.width * 0.7
                            from: 0
                            to: 30
                            stepSize: 1.0
                            value: 0
                            onValueChanged: {
                                let intValue = Math.round(value);
                                movs_backend.setfilterByDate(intValue)
                                dateSegmentText.text = movs_backend.getMonthStrByIndex(intValue)
                            }
                        }

                        Label {
                            id: fbds_maxLabel
                            text: "Latest"
                        }
                    }

                    RowLayout {
                        Text { text: "Date Segment: " }
                        Text { 
                            id: dateSegmentText
                            text: "<ALL>" 
                        }
                    }

                    TableView {
                        id: tableView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: movs_backend.movementsModel

                        delegate: Rectangle {
                            implicitWidth: 100
                            implicitHeight: 30
                            color: selected ? "blue" : "lightgray"

                            required property bool selected

                            Text { text: display }
                        }
                    }

                    SelectionRectangle { 
                        selectionMode: SelectionRectangle.PressAndHold 
                    }
                }
            }

            Component.onCompleted: {
                console.log("accountsList ListView model count: " + accountsList.count)
                console.log("movsBackend: " + movs_backend)
                console.log("accountsList ListView width: " + accountsList.width)
            }
        }
        Item {
            // Add your Classifier tab content here
            Text {
                text: "Summary Content"
                anchors.centerIn: parent
            }

            ColumnLayout {
                id: col1
                spacing: 10
                anchors.fill: parent

                MatplotlibItem {
                    id: matplotlibItem1
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    display_width: 500
                    display_height: 150
                }
            }

            Connections {
                target: ccqt
                function onSummaryPlotUpdated(index) {
                    console.log("Update summary plot", index)
                    if (index == 0) {
                        matplotlibItem1.update_figure(ccwin, 0, col1.width, col1.height*0.25)
                    } else if (index == 1) {
                        //matplotlibItem2.update_figure(nnutty, 1, col1.width, col1.height*0.25)
                    } else if (index == 2) {
                        //matplotlibItem3.update_figure(nnutty, 2, col1.width, col1.height*0.40)
                    }
                }
            }

            Component.onCompleted: {
                console.log(ccqt)
                Qt.callLater(function() {
                    matplotlibItem1.update_figure(ccqt, 0, col1.width, col1.height*0.25)
                })
            }
        }
    }
}