import math

from scipy.spatial import Delaunay

from edges_intersec import *


def cut_nodes_outside_first(all_nodes, contour, relative_size, meat):
    """Функция для удаления узлов вне контура с помощью определения знака нормали от точки к ребру
    Первая инкарнация, не очень рабочая, не используется!!!"""
    nodes_to_cut = []
    print("len1", len(all_nodes))
    for node in all_nodes:
        for edge in contour:
            x_min = min(edge[0][0], edge[1][0]) - 2
            x_max = max(edge[0][0], edge[1][0]) + 2
            y_min = min(edge[0][1], edge[1][1]) - 2
            y_max = max(edge[0][1], edge[1][1]) + 2
            if (x_min <= node[0] <= x_max) and (y_min <= node[1] <= y_max):
                upper = (edge[1][0] - edge[0][0]) * (edge[0][1] - node[1]) - (edge[0][0] - node[0]) * (edge[1][1] - edge[0][1])
                lower = ((edge[1][0] - edge[0][0]) ** 2 + (edge[1][1] - edge[0][1]) ** 2) ** 0.5
                if lower == 0:  # Случай если 0
                    lower = 1
                distance = upper / lower * meat
                if distance < 0:
                    if node not in nodes_to_cut:
                        nodes_to_cut.append(node)
    print("len2", len(nodes_to_cut))
    return nodes_to_cut

def cut_nodes_outside(all_nodes, contour):
    """Функция для удаления узлов вне контура
    Вторая версия алгоритма. Если луч от начала координат до точки пересекает контур
    нечётное кокличество раз, то точка вовне. Если чётное - внутри
    Должно работать с многосвязными контурами, наверное....."""
    zero_point = (0, 0)
    intersections = {}
    nodes_to_cut = []
    for node in all_nodes:
        intersections[node] = 0
        for edge in contour:
            line_1 = (zero_point, node)
            if check_intersection(line_1, edge)[0]:
                intersections[node] += 1
    for node in intersections:
        if intersections[node]%2 == 0:
            nodes_to_cut.append(node)
    return nodes_to_cut


if __name__ == '__main__':
    edges = [((150.0, 84.0), (115.0, 227.0)), ((115.0, 227.0), (224.0, 168.0)), ((224.0, 168.0), (150.0, 84.0))]
    nodes = [(114.0, 84.0), (114.0, 124.0), (114.0, 164.0), (114.0, 204.0), (154.0, 84.0), (154.0, 124.0), (154.0, 164.0), (154.0, 204.0), (194.0, 84.0), (194.0, 124.0), (194.0, 164.0), (194.0, 204.0)]
    relative_size = 5
    # print(cut_nodes_outside(nodes, edges))
    tri = Delaunay(nodes)
    print(tri.simplices, tri.points)
