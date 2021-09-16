import itertools
import logging
import sys

import numpy as np
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Slot, QStandardPaths
from PySide6.QtGui import (
    QMouseEvent,
    QPaintEvent,
    QPen,
    QPainter,
    QPixmap,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QApplication,
    QFileDialog,
    QStyle,
    QListWidget,
)
from scipy.spatial import Delaunay

from edges_intersec import check_intersection
from Node_operations import cut_nodes_outside


class PainterWidget(QWidget):
    """A widget where user can draw with their mouse
    The user draws on a QPixmap which is itself paint from paintEvent()"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(400, 300)
        self.pixmap = QPixmap(self.size())
        self.pixmap.fill(Qt.white)

        self.previous_pos = None
        self.points = []
        self.grid = []
        self.edges = []
        self.nodes_to_cut = []
        self.mesh_size = 30  # size of mesh in pixels

        self.painter = QPainter()
        self.pen5 = QPen()
        self.pen2 = QPen()
        self.pen3 = QPen()
        self.pen1 = QPen()
        self.penWhite = QPen()

        self.pen5.setWidth(5)
        self.pen5.setCapStyle(Qt.RoundCap)
        self.pen5.setJoinStyle(Qt.RoundJoin)
        self.pen2.setWidth(2)
        self.pen2.setCapStyle(Qt.RoundCap)
        self.pen2.setJoinStyle(Qt.RoundJoin)
        self.pen3.setWidth(3)
        self.pen3.setCapStyle(Qt.RoundCap)
        self.pen3.setJoinStyle(Qt.RoundJoin)
        self.pen1.setWidth(1)
        self.pen1.setCapStyle(Qt.RoundCap)
        self.pen1.setJoinStyle(Qt.RoundJoin)
        self.penWhite.setWidth(5)
        self.penWhite.setCapStyle(Qt.RoundCap)
        self.penWhite.setJoinStyle(Qt.RoundJoin)
        self.penWhite.setColor(Qt.white)

    #
    def paintEvent(self, event: QPaintEvent):
        """Override method from QWidget
        Paint the Pixmap into the widget"""

        painter = QPainter()
        painter.begin(self)
        painter.drawPixmap(0, 0, self.pixmap)
        painter.end()

    #
    def mousePressEvent(self, event: QMouseEvent):
        """Override from QWidget
       Called when user clicks on the mouse"""

        self.previous_pos = event.position().toPoint()

        self.painter.begin(self.pixmap)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.setPen(self.pen5)
        self.painter.drawPoint(event.position().toPoint())
        self.points.append(event.position().toTuple())
        self.painter.setPen(self.pen2)
        if len(self.points) > 1:
            self.painter.drawLine(self.points[-2][0], self.points[-2][1], self.points[-1][0], self.points[-1][1])
        self.painter.end()
        self.update()
        # QWidget.mousePressEvent(self, event)

    def chain(self):
        """Функция по замыканию контура из точек. Если контур самопересекается,
         выводит сообщение и очищает холст"""
        logging.info('all points: %s', self.points)
        connected = False
        self.painter.begin(self.pixmap)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.setPen(self.pen2)
        if len(self.points) > 2:
            self.painter.drawLine(self.points[-1][0], self.points[-1][1], self.points[0][0], self.points[0][1])
            connected = True
        else:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage("More then two vertices needed!")
            print("More then two vertices needed!")
        self.painter.end()
        self.update()

        """Создание рёбер"""
        if connected:
            cycle = itertools.cycle(self.points)
            point1 = next(cycle)
            point2 = next(cycle)
            for i in range(len(self.points)):
                self.edges.append((point1, point2))
                point1, point2 = point2, next(cycle)
        logging.info('all edges: %s', self.edges)

        """Проверка самопересечений"""
        if len(self.points) >= 4:
            for i in range(0, len(self.edges)):
                for j in range(i + 2, len(self.edges)):
                    base_edge = self.edges[i]
                    second_edge = self.edges[j]
                    status = check_intersection(base_edge, second_edge)
                    if status[0]:
                        error_dialog = QtWidgets.QErrorMessage()
                        error_dialog.showMessage("Intersection detected! Clearing the canvas")
                        print("Intersection detected! Clearing the canvas")
                        i, j = len(self.edges) - 1, len(self.edges) - 1
                        self.clear()

    @Slot()
    def clear(self):
        self.pixmap.fill(Qt.white)
        self.points.clear()
        self.grid.clear()
        self.edges.clear()
        self.nodes_to_cut.clear()
        self.update()

    #     def mouseReleaseEvent(self, event: QMouseEvent):
    #         """Override method from QWidget
    #         Called when user releases the mouse"""
    #
    #         self.previous_pos = None
    #         QWidget.mouseReleaseEvent(self, event)

    def save(self, filename: str):
        """ save pixmap to filename """
        self.pixmap.save(filename)

    def nodeGrid(self):
        """Функция создания равномерно разбросанных узлов
        по поверхности на которой нарисован контур"""
        self.painter.begin(self.pixmap)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.setPen(self.pen5)
        min_x, min_y = self.points[0][0], self.points[0][1]
        max_x, max_y = self.points[0][0], self.points[0][1]
        """Получение границ, в которых будут создаваться узлы"""
        for node in self.points:
            if min_x > node[0]: min_x = node[0] - 1
            if max_x < node[0]: max_x = node[0] + 1
            if max_y < node[1]: max_y = node[1] + 1
            if min_y > node[1]: min_y = node[1] - 1
        logging.info('borders: min_x=%s, min_y=%s, max_x=%s, max_y=%s', min_x, min_y, max_x, max_y)
        number = self.mesh_size
        num_x = (max_x - min_x) / self.mesh_size
        num_y = (max_y - min_y) / self.mesh_size
        step_x = (max_x - min_x) / num_x
        step_y = (max_y - min_y) / num_y

        logging.info('step for nodes in grid (x, y): %s, %s. It\'s for %s mesh size', step_x, step_y, number)
        """Раскидыаем узлы по полученным границам"""
        i = 0
        x = min_x
        y = min_y
        while x <= max_x + 1:
            y = min_y
            while y <= max_y + 1:
                self.painter.drawPoint(x, y)
                self.grid.append((x, y))
                y += step_y
            x += step_x
        logging.info('all nodes in grid: %s', self.grid)
        self.painter.end()
        self.update()

    def cutNodes(self):
        self.painter.begin(self.pixmap)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.setPen(self.penWhite)
        logging.info("number of nodes before cut: %s", len(self.grid))
        self.nodes_to_cut = cut_nodes_outside(self.grid, self.edges)
        logging.info("number of nodes to cut: %s", len(self.nodes_to_cut))
        """Удаляем потёртые узлы из массива всех узлов"""
        for node in self.nodes_to_cut:
            self.painter.drawPoint(node[0], node[1])
            if node in self.grid:
                self.grid.pop(self.grid.index(node))
        logging.info("number of nodes after cut: %s", len(self.grid))
        self.painter.end()
        self.update()

    def createNodesOnContour(self):
        """Функция, которая создаёт узлы в вершинах контура и на его рёбрах"""
        self.painter.begin(self.pixmap)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.setPen(self.pen5)
        for point in self.points:
            self.grid.append(point)
        for edge in self.edges:
            length = ((edge[1][1] - edge[0][1]) ** 2 + (edge[1][0] - edge[0][0]) ** 2) ** 0.5
            intervals = round(length / self.mesh_size) + 1
            delta_x = (edge[1][0] - edge[0][0]) / intervals
            delta_y = (edge[1][1] - edge[0][1]) / intervals
            for i in range(1, intervals):
                self.grid.append((edge[0][0] + delta_x * i, edge[0][1] + delta_y * i))
        logging.info("number of nodes with contour nodes: %s", len(self.grid))
        self.pixmap.fill(Qt.white)
        for node in self.grid:
            self.painter.drawPoint(node[0], node[1])
        self.painter.end()
        self.update()

    def triangulate(self):
        """Создаёт треугольники по имеещемуся набору узлов в grid"""
        self.painter.begin(self.pixmap)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.setPen(self.pen1)
        pointNumber = len(self.grid)
        points = np.zeros((pointNumber, 2))
        points[:, 0] = [self.grid[i][0] for i in range(pointNumber)]
        points[:, 1] = [self.grid[i][1] for i in range(pointNumber)]
        # print(points)
        triangulated = Delaunay(points)
        # print(triangulated.points, triangulated.simplices)
        for element in triangulated.simplices:
            node1, node2, node3 = [self.grid[i] for i in element]
            # print(node1, node2, node3)
            self.painter.drawLine(node1[0], node1[1], node2[0], node2[1])
            self.painter.drawLine(node1[0], node1[1], node3[0], node3[1])
            self.painter.drawLine(node3[0], node3[1], node2[0], node2[1])
        self.painter.end()
        self.update()


#     def load(self, filename: str):
#         """ load pixmap from filename """
#         self.pixmap.load(filename)
#         self.pixmap = self.pixmap.scaled(self.size(), Qt.KeepAspectRatio)
#         self.update()


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.centralWidget = QWidget()
        self.painter_widget = PainterWidget()
        self.points_list = QListWidget()

        self.btnConnect = QtWidgets.QPushButton("&Connect")
        self.btnClear = QtWidgets.QPushButton("&Clear")
        self.btnCreateNodes = QtWidgets.QPushButton("&Create nodes")
        self.btnCutOutsideNodes = QtWidgets.QPushButton("&Cut nodes outside borders")
        self.btnOnContour = QtWidgets.QPushButton("&Create nodes on contour")
        self.btnTriangulate = QtWidgets.QPushButton("&TRIANGULATE!!")

        self.bar = self.addToolBar("Menu")
        self.bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._save_action = self.bar.addAction(qApp.style().standardIcon(QStyle.SP_DialogSaveButton), "Save",
                                               self.on_save)
        self._save_action.setShortcut(QKeySequence.Save)

        #         self._open_action = self.bar.addAction(
        #             qApp.style().standardIcon(QStyle.SP_DialogOpenButton), "Open", self.on_open
        #         )
        #         self._open_action.setShortcut(QKeySequence.Open)
        #         self.bar.addAction(
        #             qApp.style().standardIcon(QStyle.SP_DialogResetButton),
        #             "Clear",
        #             self.painter_widget.clear,
        #         )
        #         self.bar.addSeparator()
        #
        #         self.color_action = QAction(self)
        #         self.color_action.triggered.connect(self.on_color_clicked)
        #         self.bar.addAction(self.color_action)

        self.setCentralWidget(self.centralWidget)
        main_layout = QtWidgets.QVBoxLayout(self.centralWidget)
        main_layout.addWidget(self.painter_widget)
        main_layout.addWidget(self.btnConnect)
        main_layout.addWidget(self.btnClear)
        main_layout.addWidget(self.btnCreateNodes)
        main_layout.addWidget(self.btnCutOutsideNodes)
        main_layout.addWidget(self.btnOnContour)
        main_layout.addWidget(self.btnTriangulate)
        main_layout.addWidget(self.points_list)
        self.setLayout(main_layout)
        self.mime_type_filters = ["image/png", "image/jpeg"]

        self.btnConnect.clicked.connect(self.connect_dots)
        self.btnClear.clicked.connect(self.clear)
        self.btnCreateNodes.clicked.connect(self.createNodes)
        self.btnCutOutsideNodes.clicked.connect(self.cutNodes)
        self.btnOnContour.clicked.connect(self.createNodesOnContour)
        self.btnTriangulate.clicked.connect(self.triangulate)

    @Slot()
    def connect_dots(self):
        self.painter_widget.chain()

    @Slot()
    def createNodes(self):
        self.painter_widget.nodeGrid()

    @Slot()
    def clear(self):
        self.painter_widget.clear()

    @Slot()
    def cutNodes(self):
        self.painter_widget.cutNodes()

    @Slot()
    def createNodesOnContour(self):
        self.painter_widget.createNodesOnContour()

    @Slot()
    def triangulate(self):
        self.painter_widget.triangulate()

    @Slot()
    def on_save(self):
        dialog = QFileDialog(self, "Save File")
        dialog.setMimeTypeFilters(self.mime_type_filters)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix("png")
        dialog.setDirectory(
            QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        )

        if dialog.exec() == QFileDialog.Accepted:
            if dialog.selectedFiles():
                self.painter_widget.save(dialog.selectedFiles()[0])

    # @Slot()
    # def update_points(self):
    #     self.painter_widget.update_points()


#
#     @Slot()
#     def on_open(self):
#
#         dialog = QFileDialog(self, "Save File")
#         dialog.setMimeTypeFilters(self.mime_type_filters)
#         dialog.setFileMode(QFileDialog.ExistingFile)
#         dialog.setAcceptMode(QFileDialog.AcceptOpen)
#         dialog.setDefaultSuffix("png")
#         dialog.setDirectory(
#             QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
#         )
#
#         if dialog.exec() == QFileDialog.Accepted:
#             if dialog.selectedFiles():
#                 self.painter_widget.load(dialog.selectedFiles()[0])


if __name__ == "__main__":
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    logging.info('Started')
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
