from form import *
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtWidgets import QRubberBand, QFileDialog
from PyQt5.QtCore import QRect, QSize
from scipy.signal import savgol_filter as sg_filter
from PIL import Image
import matplotlib.pyplot as plt
from operator import itemgetter
import sys


class MyWin(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)
        self.ui.action.triggered.connect(self.get_image)  # файл -> открыть
        self.ui.pushButton.clicked.connect(self.show_plot)  # Кнопка График
        self.ui.pushButton_2.clicked.connect(self.crop_image)  # кнопка Обрезать
        self.path = ""  # здесь будет путь к изображению
        self.rubberBand = None  # здесь будет выделяющий прямоугольник (объект)
        self.origin = None  # поможет задать позицию прямоугольника
        self.rect = None  # координаты прямоугольника типа QRect
        self.im = None  # здесь будет изображение
        self.coords = []  # список координат прямоугольника
        self.real_coords = []  # список реальных координат для изображения

    def borders(self, obj, value):
        return value if obj > value else obj  # проверка выхода за рамки при выделении прямоугольником

    def rgb2e(self, i):
        r, g, b = i[0], i[1], i[2]
        e = r*0.3 + g*0.59 + b*0.11  # преобразование цвета в яркость
        return round(e, 2)

    def wind(self, n):
        return n+1 if n % 2 == 0 else n  # всегда нечетное число

    def not_zero(self, ls):
        for i in range(len(ls)):
            if ls[i] < 0:
                ls[i] = 0  # только положительные числа
        return ls

    def unique(self, ls):  # уникализация
        d = {i: [] for i, j in ls}
        for i, j in ls:
            d[i] = d[i] + [j]
        for i in d:
            d[i] = sum(d[i])
        return list([i, d[i]] for i in d)  # уникальный список

    def depthc(self, mod):
        depth_color = {
            "1": 1,       # black and white
            "L": 8,       # black and white (8 bit)
            "P": 8,       # color (256 colors)
            "RGB": 24,    # color
            "RGBA": 32,   # color and alpha
            "CMYK": 32,   # color
            "YCbCr": 24,  # color, the video format
            "I": 32,      # integer, color
            "F": 32       # real, color
            }
        return depth_color.get(mod)

    def mpe(self, event):  # функция нажатия мыши
        self.origin = event.pos()
        if not self.rubberBand:
            self.rubberBand = QRubberBand(QRubberBand.Rectangle, self.ui.graphicsView)
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()  # показать прямоугольник

    def mme(self, event):  # функция перемещения мыши
        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mre(self, event):  # функция отпускания мыши
        im_width, im_height = int(self.im.size[0]), int(self.im.size[1])  # ширина и высота изображения
        gv_width = list(QRect.getRect(self.ui.graphicsView.geometry()))[2]  # ширина обозревателя graphicsView
        gv_height = list(QRect.getRect(self.ui.graphicsView.geometry()))[3]  # высота обозревателя graphicsView
        self.rect = self.rubberBand.geometry()
        self.coords = list(QRect.getCoords(self.rect))  # координаты выделенного прямоугольника
        self.coords[2] = self.borders(self.coords[2], gv_width)
        self.coords[3] = self.borders(self.coords[3], gv_height)
        c = self.coords
        self.rubberBand.hide()  # скрыть прямоугольник
        self.ui.label_7.setText("select coords: {} ".format(str(self.coords)))
        scr_v = int(self.ui.graphicsView.verticalScrollBar().sliderPosition())  # позиция вертикального скрола
        scr_h = int(self.ui.graphicsView.horizontalScrollBar().sliderPosition())  # позиция горизонтального скрола
        self.real_coords = [c[0]+scr_h, c[1]+scr_v, c[2]+scr_h, c[3]+scr_v]  # реальные координаты
        self.real_coords[2] = self.borders(self.real_coords[2], im_width)
        self.real_coords[3] = self.borders(self.real_coords[3], im_height)
        self.ui.label_8.setText("real coords: {} ".format(str(self.real_coords)))

    def get_image(self):  # p.s. изображение желательно кидать в папку с проектом, для удобства
        file = QFileDialog.getOpenFileName()[0]  # откроется папка, в которой лежит проект
        self.path = file  # в path пропишется путь к изображению, которое мы выбрали
        self.im = Image.open(self.path)  # в im будет лежать открытое изображение
        pix = QtGui.QPixmap(self.path)  # в pix грузим путь
        scene = QGraphicsScene()  # создаём сцену для обозревателя graphicsView
        item = QGraphicsPixmapItem(pix)  # создаём объект, в который загружаем pix
        scene.addItem(item)  # добавляем в сцену объект item
        self.ui.graphicsView.mousePressEvent = self.mpe  # функция для мыши
        self.ui.graphicsView.mouseMoveEvent = self.mme  # функция для мыши
        self.ui.graphicsView.mouseReleaseEvent = self.mre  # функция для мыши
        self.ui.graphicsView.setScene(scene)  # устанавливаем сцену в обозреватель graphicsView
        self.ui.label.setText("Формат: {}".format(self.im.format))
        self.ui.label_2.setText("Размеры: {}x{}".format(int(self.im.size[0]), int(self.im.size[1])))
        self.ui.label_3.setText("Глубина цвета: {}-bit".format(self.depthc(self.im.mode)))

    def crop_image(self):
        c = self.real_coords  # реальные координаты в с
        im_coords = (c[0], c[1], c[2], c[3])  # box для обрезки
        new_im = self.im.crop(im_coords).copy()  # обрезанное изображение из копии оригинального
        ext = str(self.im.format).lower()  # расширение изображения
        lst = [i[1] for i in new_im.getcolors(maxcolors=2**24)]  # список со всеми цветами
        lst.sort()  # сортировка списка от тёмного к светлому
        self.ui.label_4.setText("Светлый: {}".format(lst[-1]))  # самый светлый цвет
        self.ui.label_5.setText("Средний: {}".format(lst[int(len(lst)/2)]))  # средний цвет
        self.ui.label_6.setText("Темный: {}".format(lst[0]))  # самый тёмный цвет
        # new_im.show()  # показать обрезанное изображение
        new_im.save("{}_crop.{}".format(self.path, ext))  # сохранить обрезанное изображение "ImageName_crop"
        print("image saved")

    def show_plot(self):
        max_clr = 133  # ограничение по цвету
        min_frq = 0.05  # ограничение по частоте
        lst = [i for i in self.im.getcolors(maxcolors=2**24)]  # (color, freq)
        lst = list(filter(lambda i: i[1][0] < max_clr and i[1][1] < max_clr and i[1][2] < max_clr, lst))
        lst = [[self.rgb2e(i[1]), i[0]] for i in lst]
        lst = self.unique(lst)  # уникальный список яркостей
        lst.sort(key=itemgetter(0), reverse=True)  # сортировка списка по яркости
        mf = max(list(i[1] for i in lst))  # максимальная частота
        lst = [[i[0], round(i[1]/mf, 2)] for i in lst]  # максимальная частота равна единице
        lst = list(filter(lambda i: i[1] > min_frq, lst))  # сортировка по частоте
        x = list(i[0] for i in lst)  # список из яркостей
        y = list(i[1] for i in lst)  # список из частот
        y_new = sg_filter(y, self.wind(int(len(lst)/2)), 1)  # интерполяция и сглаживание
        y_new = self.not_zero(y_new)  # избавление от отрицательных элементов
        fig = plt.figure()  # создание фигуры (окна с графиком)
        fig.canvas.set_window_title(self.path)  # имя окна - это путь к файлу
        plt.plot(x, y, "o")  # отрисовка точек
        plt.plot(x, y_new, "-", color='r', linewidth=4)  # линия интерполяции
        plt.legend(['Points','Interpolation'])  # легенда
        plt.xlabel("Brightness")  # подпись оси x
        plt.ylabel("Frequency")  # подпись оси y
        plt.show()  # вывод графика на экран


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    my_app = MyWin()
    my_app.show()
    sys.exit(app.exec_())
