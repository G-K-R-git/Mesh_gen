import itertools


def constants_for_point(point1, point2):
    """Функция для нахождения констант для уравнения линии"""
    a = point2[1] - point1[1]
    b = point1[0] - point2[0]
    c = a * point1[0] + b * point1[1]
    return a, b, c


def check_intersection(line1, line2):
    """Функция для нахождени точки пересечения двух линий
    Если линии пересекаются, то определить пересекаются ли отрезки на этих линиях
    line1 line2 - линии. line1[0] - первая точка. line[0][0] - координата Х первой точки линии"""
    a1, b1, c1 = constants_for_point(line1[0], line1[1])
    a2, b2, c2 = constants_for_point(line2[0], line2[1])
    det = a1 * b2 - a2 * b1
    if det == 0:
        return False, 0, 0
    intersection_x = (b2 * c1 - b1 * c2) / det
    intersection_y = (c2 * a1 - c1 * a2) / det
    x_min1, x_min2 = min(line1[0][0], line1[1][0]), min(line2[0][0], line2[1][0])
    x_max1, x_max2 = max(line1[0][0], line1[1][0]), max(line2[0][0], line2[1][0])
    y_min1, y_min2 = min(line1[0][1], line1[1][1]), min(line2[0][1], line2[1][1])
    y_max1, y_max2 = max(line1[0][1], line1[1][1]), max(line2[0][1], line2[1][1])

    if (x_min1 < intersection_x < x_max1) and (x_min2 < intersection_x < x_max2):
        if (y_min1 < intersection_y < y_max1) and (y_min2 < intersection_y < y_max2):
            return True, intersection_x, intersection_y

    return False, intersection_x, intersection_y


if __name__ == '__main__':

    points = [(58.0, 78.0), (124.0, 260.0), (206.0, 119.0), (131.0, 172.0)]
    print("points ", points)
    """Проверка на пересечение линий"""
    cycler = itertools.cycle(points)
    point1 = next(cycler)
    point2 = next(cycler)
    edges = []
    for i in range(len(points)):
        edges.append((point1, point2))
        point1, point2 = point2, next(cycler)
    print("edges", edges)
    for i in range(0, len(edges)):
        for j in range(i + 2, len(edges)):
            base_edge = edges[i]
            second_edge = edges[j]
            print("edges checked for intersection: ", base_edge, second_edge)
            print(check_intersection(base_edge, second_edge))
