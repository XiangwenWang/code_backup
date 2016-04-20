#!/usr/bin/env python
# Author: Xiangwen Wang
# License: GPL v3
import sys
import math
import random


class trajectory:
    R = 6371000  # Earth radius in meters
    time_gap_limit = 20  # seconds
    ajac_dist_limit = 2000  # meters
    indicator_list = ('rural', 'urban', 'intermediate', 'all',
                      'urban-rural', 'rural-urban',
                      'urban-rural-urban', 'rural-urban-rural',
                      'mixxed')

    _time_between_stays_limit = 300  # seconds
    _time_interval = 60  # seconds, time interval between d_i calculations
    _stay_duration_condition = 300  # seconds
    _stay_radius_threshold = 200  # meters

    _trip_time_limit = _stay_duration_condition * 2 + _time_between_stays_limit
    traj_len_limit = int(_trip_time_limit/time_gap_limit)
    _resolution_limit = _stay_radius_threshold
    _speed_upper_limit = 340
    # m/s, currently, there is no supersonic transport in commercial service (after 2003)
    _trip_length_limit = _stay_radius_threshold  # meters, abandon shorter trips
    # m/s, which is 1000mph, roughly the top speed for current commercial airplanes

    def __init__(self, data):
        self.data = data
        self.len = len(data)
        self.indicator = self.cal_indicator(data)
        self.l0 = self.get_lt0()
        self.trip_lt_limit_fail = self.check_lt_limit()

    def __str__(self):
        return str(self.data)

    def check_lt_limit(self):
        l_fail = self.l0[0][0] < self._trip_length_limit or self.l0[0][0] > 80060347
        # 80060347 (2*Pi*R * 2) is the upper limit of valid trip length
        t_fail = self.l0[0][1] < self._trip_time_limit
        v_fail = self.l0[0][0] / self.l0[0][1] > self._speed_upper_limit if not t_fail else True
        return t_fail or l_fail or v_fail

    def cal_indicator(self, data):
        indicator_array = set()
        # original indicator:
        # 1 = rural, 2 = urban, 0 = water zone
        for txyi in data:
            indicator_array.add(txyi[3])
        indicator_index = (1 + (1.0 in indicator_array or 0.0 in indicator_array)
                           ) * (2.0 in indicator_array)
        if indicator_index == 2:
            if data[0][3] == 2.0:
                if data[-1][3] == 2.0:
                    indicator_index = 6
                else:
                    indicator_index = 4
            else:
                if data[-1][3] == 2.0:
                    indicator_index = 5
                else:
                    indicator_index = 7
        return self.indicator_list[indicator_index]

    def r_m(self):
        def FindDiaEdge(d_ABC):
            # if it is an obtuse triangle or a right triangle
            if d_ABC[0]**2 >= d_ABC[1]**2 + d_ABC[2]**2:  # edge AB would be the diameter
                return 0
            elif d_ABC[1]**2 >= d_ABC[0]**2 + d_ABC[2]**2:  # edge BC
                return 1
            elif d_ABC[2]**2 >= d_ABC[1]**2 + d_ABC[0]**2:  # edge CA
                return 2
            return -1  # if it is an acute triangle

        def VectorLen(a):
            return math.sqrt(sum(map(lambda x: x**2, a)))

        def CalLatLon(P):
            x, y, z = P
            curr_R = VectorLen(P)
            lat_rad = math.asin(z / curr_R)
            lon_rad = math.atan2(y, x)
            lat = math.degrees(lat_rad)
            lon = math.degrees(lon_rad)
            return (lat, lon)

        def findMidEdge(pointpair):
            P1, P2 = pointpair
            P = map(lambda x, y: (x + y) / 2.0, P1, P2)
            return CalLatLon(P)

        def Cir2Pts(A_s, B_s):
            A, B = convToCart(A_s), convToCart(B_s)
            O = findMidEdge((A, B))
            r = distance(A_s, B_s) / 2.0
            return (O, r)

        def VectorPlus(a, b):
            return map(lambda x, y: x + y, a, b)

        def VectorMinus(a, b):
            return map(lambda x, y: x - y, a, b)

        def VectorTimesScaler(a, k):
            return map(lambda x: x * k, a)

        def VectorDivScaler(a, k):
            return map(lambda x: x / k, a) if k else []

        def VectorCross(a, b):
            x = a[1] * b[2] - a[2] * b[1]
            y = a[2] * b[0] - a[0] * b[2]
            z = a[0] * b[1] - a[1] * b[0]
            return (x, y, z)

        def VectorDot(a, b):
            return sum(map(lambda x, y: x * y, a, b))

        def Print_outlier(data, mincircle):
            NoError = True
            for i in data:
                if not InCircle(i, mincircle):
                    print distance(i, mincircle[0]),
                    # print i,
                    NoError = False
            if not NoError:
                print '\n%.2f\n' % mincircle[1]

        def MinCirTri(A_s, B_s, C_s):
            A, B, C = convToCart(A_s), convToCart(B_s), convToCart(C_s)
            a = VectorMinus(A, C)
            b = VectorMinus(B, C)
            P1_denom = 2 * (VectorLen(VectorCross(a, b))**2)
            if P1_denom:
                P1_part1_1 = VectorTimesScaler(b, VectorLen(a)**2 / P1_denom)
                P1_part1_2 = VectorTimesScaler(a, VectorLen(b)**2 / P1_denom)
                P1_part1 = VectorMinus(P1_part1_1, P1_part1_2)
                P1 = VectorCross(P1_part1, VectorCross(a, b))
                P = VectorPlus(P1, C)
                O = CalLatLon(P)
                r = distance(O, A_s)
            else:
                dist_ABC = (distance(A_s, B_s), distance(B_s, C_s), distance(C_s, A_s))
                dia_edge = FindDiaEdge(dist_ABC)
                edges = ((A, B), (B, C), (C, A))
                O = findMidEdge(edges[dia_edge])
                r = dist_ABC[dia_edge] / 2.0
            return (O, r)

        def InCircle(A, minimum_circle):
            _precision = 1e-6  # precision is 1e-6 meters
            return distance(A, minimum_circle[0]) <= (minimum_circle[1] + _precision)

        def MinCir_2PtsKnown(data_piece2):
            minimum_circle2 = Cir2Pts(data_piece2[-2], data_piece2[-1])
            all_in_circle = True
            for i in xrange(0, len(data_piece2) - 2):
                if not InCircle(data_piece2[i], minimum_circle2):
                    all_in_circle = False
                    break
            if all_in_circle:
                return minimum_circle2
            farthest = [minimum_circle2, 0]
            for i in xrange(0, len(data_piece2) - 2):
                if InCircle(data_piece2[i], minimum_circle2):
                    continue
                curr_circle = MinCirTri(data_piece2[i], data_piece2[-2], data_piece2[-1])
                dist_pt_line = distance(curr_circle[0], minimum_circle2[0])
                if dist_pt_line > farthest[1]:
                        farthest = (curr_circle, dist_pt_line)
            minimum_circle2 = farthest[0]
            # Print_outlier(data_piece2, minimum_circle2)
            # print data_piece2[-2], data_piece2[-1]
            return minimum_circle2

        def MinCir_1PtKnown(data_piece1):
            minimum_circle1 = Cir2Pts(data_piece1[0], data_piece1[-1])
            for i in xrange(1, len(data_piece1)-1):
                if not InCircle(data_piece1[i], minimum_circle1):
                    minimum_circle1 = MinCir_2PtsKnown(data_piece1[0: i+1] + data_piece1[-1:])
                    # print data_piece1[i], data_piece1[-1], minimum_circle1
                    # Print_outlier(data_piece1[0: i + 1] + data_piece1[-1:], minimum_circle1)
            # Print_outlier(data_piece1, minimum_circle1)
            return minimum_circle1

        def MinCir(data):
            data = reduce(lambda x, y: x if y in x else x + [y], [[], ] + data)
            # print len(data)
            data_num = len(data)
            if not data_num:
                return ((0.0, 0.0), 0.0)
            elif data_num == 1:
                return ((data[0][0], data[0][1]), 0.0)
            elif data_num == 2:
                return Cir2Pts(data[0], data[1])
            random.shuffle(data)
            # print data
            minimum_circle = Cir2Pts(data[0], data[1])
            for i in xrange(2, data_num):
                if not InCircle(data[i], minimum_circle):
                    minimum_circle = MinCir_1PtKnown(data[0: i + 1])
            # Print_outlier(data, minimum_circle)
            return minimum_circle

        ptsnum = self.len
        if self.trip_lt_limit_fail:
            return []
        indicator = self.indicator
        t = 0
        latlon_pairs = []
        if ptsnum <= self.traj_len_limit:
            for i in xrange(ptsnum):
                latlon_pairs.append([self.data[i][1], self.data[i][2]])
        else:
            for i in xrange(self.traj_len_limit):
                j = i * (ptsnum / self.traj_len_limit)
                latlon_pairs.append([self.data[j][1], self.data[j][2]])
            latlon_pairs.append([self.data[-1][1], self.data[-1][2]])
        for i in xrange(1, ptsnum):
            delta_t = self.data[i][0] - self.data[i - 1][0]
            t += delta_t
        r = MinCir(latlon_pairs)[1]
        return [(r, t, indicator)] * (r > 1.0 and r < 40075000.0)

    def r_g(self):
        ptsnum = self.len
        if self.trip_lt_limit_fail:
            return []
        indicator = self.indicator
        t = 0
        mid_x, mid_y, mid_z = 0.0, 0.0, 0.0
        R_g2 = 0.0
        for i in xrange(ptsnum):
            (x, y, z) = convToCart(self.data[i][1:3])
            mid_x += x / ptsnum
            mid_y += y / ptsnum
            mid_z += z / ptsnum
        mid_latlon = CalLatLon((mid_x, mid_y, mid_z))
        for i in xrange(ptsnum):
            R_g2 += distance(self.data[i][1:3], mid_latlon)**2 / ptsnum
        for i in xrange(1, ptsnum):
            delta_t = self.data[i][0] - self.data[i - 1][0]
            t += delta_t
        r = math.sqrt(R_g2)
        return [(r, t, indicator)] * (r > 1.0 and r < 40075000.0)

    def ds_temp(self):
        ptsnum = self.len
        if self.trip_lt_limit_fail:
            return []
        stays_raw = []
        for i in xrange(0, ptsnum - 1):
            if stays_raw:
                j = stays_raw[-1][1]
                # print j, ptsnum
                if j == ptsnum - 1:
                    continue
                dist = distance((self.data[i][1], self.data[i][2]),
                                (self.data[j+1][1], self.data[j+1][2]))
                if dist > self._stay_radius_threshold:
                    continue
            j, flag = i+1, False
            while j < ptsnum:
                dist = distance((self.data[i][1], self.data[i][2]),
                                (self.data[j][1], self.data[j][2]))
                if dist < self._stay_radius_threshold:
                    j, flag = j+1, True
                else:
                    break
            delta_t = self.data[j - 1][0] - self.data[i][0]
            if delta_t > self._stay_duration_condition and flag is True:
                if not stays_raw:
                    stays_raw.append([i, j - 1, delta_t])
                else:
                    if stays_raw[-1][1] > i:
                        if delta_t > stays_raw[-1][2]:
                            stays_raw[-1] = [i, j-1, delta_t]
                    else:
                        stays_raw.append([i, j-1, delta_t])
        if stays_raw:
            first = stays_raw[0][0]
            last = stays_raw[-1][1]
            if self.data[first][0] - self.data[0][0] > self._stay_duration_condition:
                stays_raw.insert(0, [0, 0, 0])
            if self.data[-1][0] - self.data[last][0] > self._stay_duration_condition:
                stays_raw.append([ptsnum-1, ptsnum-1, 0])
        # print stays_raw
        stays = []
        for x in stays_raw:
            mid_posi = aver_position(self.data[x[0]: x[1] + 1])
            if not stays:
                stays.append(mid_posi + [(x[0]+x[1])/2])
            else:
                if distance((stays[-1][0], stays[-1][1]),
                            (mid_posi[0], mid_posi[1])) > self._resolution_limit \
                            and mid_posi[2] - stays[-1][3] > self._time_between_stays_limit:
                    stays.append(mid_posi + [(x[0]+x[1])/2])
        return stays

    def d(self):
        if self.trip_lt_limit_fail:
            return []
        stays = self.ds_temp()
        if len(stays) < 2:
            return []
        indicator = self.indicator
        d_list = []
        for i in xrange(1, len(stays)):
            d = distance((stays[i-1][0], stays[i-1][1]), (stays[i][0], stays[i][1]))
            delta_t = stays[i][4] - stays[i-1][4]
            d_list.append([d, delta_t, indicator])
        return d_list

    def s(self):
        if self.trip_lt_limit_fail:
            return []
        stays = self.ds_temp()
        if len(stays) < 2:
            return []
        indicator = self.indicator
        s_list = []
        for i in xrange(1, len(stays)):
            start, end = stays[i-1][5], stays[i][5]
            s = 0
            delta_t = self.data[end][0] - self.data[start][0]
            while start < end:
                s += distance((self.data[start][1], self.data[start][2]),
                              (self.data[start+1][1], self.data[start+1][2]))
                start += 1
            s_list.append([s, delta_t, indicator])
        return s_list

    def get_lt0(self):
        ptsnum = self.len
        l, t = 0, 0
        indicator = self.indicator
        for i in xrange(1, ptsnum):
            delta_d = distance((self.data[i-1][1], self.data[i-1][2]),
                               (self.data[i][1], self.data[i][2]))
            delta_t = self.data[i][0] - self.data[i - 1][0]
            l += delta_d
            t += delta_t
        return [(l, t, indicator)]

    def l(self):
        if self.trip_lt_limit_fail:
            return []
        return self.l0

    def r_t(self):
        ptsnum = self.len
        if self.trip_lt_limit_fail:
            return []
        if self.data[ptsnum - 1][0] - self.data[0][0] < self._time_interval:
            return []
        indicator = self.indicator
        r_t_list = []
        r_t_num = 1
        for i in xrange(1, ptsnum):
            if self.data[i][0] - self.data[0][0] >= r_t_num * self._time_interval:
                delta_r = distance((self.data[i][1], self.data[i][2]),
                                   (self.data[0][1], self.data[0][2]))
                r_t_list.append([delta_r, r_t_num * self._time_interval, indicator])
                r_t_num += 1
        return r_t_list

    def d_i(self):
        ptsnum = self.len
        if self.trip_lt_limit_fail:
            return []
        indicator = self.indicator
        d_list = []
        last_index = 0
        for i in xrange(1, ptsnum):
            if self.data[i][0] - self.data[last_index][0] >= self._time_interval:
                d = distance((self.data[i][1], self.data[i][2]),
                             (self.data[last_index][1], self.data[last_index][2]))
                d_list.append([d, self._time_interval, indicator])
                last_index = i
        return d_list

    def t(self):
        dti_list = self.d()
        n = len(dti_list)
        for i in xrange(n):
            temp = dti_list[i][0]
            dti_list[i][0] = dti_list[i][1]
            dti_list[i][1] = temp
        return dti_list

    def cleaning(self):
        ptsnum = len(self.data)
        if self.trip_lt_limit_fail:
            return []
        data = [self.data[0]]
        for i in xrange(1, ptsnum):
            delta_t = self.data[i][0] - self.data[i-1][0]
            if delta_t != 0:
                data.append(self.data[i])
        if len(data) > self.traj_len_limit:
            tot = ''
            for txyi in data:
                tot += '%d %.8f %.8f %s,' % (txyi[0], txyi[1], txyi[2], txyi[3])
            print tot
        return []


def distance(A, B):
    lat1, lon1 = A
    lat2, lon2 = B
    R = 6371000
    Haversine = (math.sin(math.radians((lat2 - lat1) / 2)))**2 + \
        math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * \
        (math.sin(math.radians((lon2 - lon1) / 2)))**2
    d = R * 2 * math.atan2(math.sqrt(Haversine), math.sqrt(1 - Haversine))
    return d


def CalLatLon(P):
    x, y, z = P
    curr_R = math.sqrt(x**2 + y**2 + z**2)
    lat_rad = math.asin(z / curr_R)
    lon_rad = math.atan2(y, x)
    lat = math.degrees(lat_rad)
    lon = math.degrees(lon_rad)
    return (lat, lon)


def aver_position(stay_slice):
    count = len(stay_slice)
    mid_lat, mid_lon = 0, 0
    for latlon in stay_slice:
        mid_lat += latlon[1] / count
        mid_lon += latlon[2] / count
    return [mid_lat, mid_lon, stay_slice[0][0], stay_slice[-1][0],
            (stay_slice[0][0] + stay_slice[-1][0]) * 0.5]


def convToCart(latlon):
    R = 6371000  # Earth radius in meters
    lat, lon = math.radians(latlon[0]), math.radians(latlon[1])
    x = R * math.cos(lon) * math.cos(lat)
    y = R * math.sin(lon) * math.cos(lat)
    z = R * math.sin(lat)
    return (x, y, z)


def Get_quantity(traj):
    quantity = 'd' if len(sys.argv) < 3 else sys.argv[2]
    # print sys.argv[2]
    quantity_func = {'d': traj.d, 's': traj.s, 'r_g': traj.r_g,
                     'l': traj.l, 't': traj.t, 'r_m': traj.r_m,
                     'r_t': traj.r_t, 'd_i': traj.d_i, 'clean': traj.cleaning,
                     }
    if quantity not in quantity_func:
        exit(0)
    else:
        return quantity_func[quantity]()


def cut_pieces(data):
    start = 0
    last_t = data[0][0]
    quantity_list = []
    for i in xrange(0, len(data)):
        if data[i][0] - last_t > trajectory.time_gap_limit or \
                distance((data[i - 1][1], data[i - 1][2]),
                         (data[i][1], data[i][2])) > trajectory.ajac_dist_limit:
            if i - start > trajectory.traj_len_limit:
                traj = trajectory(data[start: i])
                quantity_list += Get_quantity(traj)
            start = i
        last_t = data[i][0]
    if i + 1 - start > trajectory.traj_len_limit:
        traj = trajectory(data[start: i])
        quantity_list += Get_quantity(traj)
    return quantity_list


def GPXparse(content):
    content1 = content.split(',')[:-1]
    data = []
    for strtxyi in content1:
        if strtxyi[0] == ' ':
            strtxyi = strtxyi[1:]
        txyi = strtxyi.split(' ')
        data.append(
            [int(txyi[0]), float(txyi[1]), float(txyi[2]), int(txyi[3])])
    if len(data) < trajectory.traj_len_limit:
        return 1
    quantity_list = cut_pieces(data)
    if quantity_list:
        for pair in quantity_list:
            print '%s\t%.8f\t%.8f' % (pair[2], pair[0], pair[1])
            print '%s\t%.8f\t%.8f' % (trajectory.indicator_list[3], pair[0], pair[1])
    return 1


def read_input(file):
    for line in file:
        yield line.strip()


def mapper():
    content = read_input(sys.stdin)
    for line in content:
        GPXparse(line)


def reducer():
    logres = 10.0
    min_resolution = 1  # min = 1m
    base = 10.0  # or use math.e
    maxloglen = 100

    content = read_input(sys.stdin)
    if len(sys.argv) == 3 and sys.argv[2] == 'U':
        for line in content:
            print line
        return 0
    distrib = {}
    total_count = 0.0
    for i in trajectory.indicator_list:
        distrib[i] = ([0.0] * maxloglen)
    for line in content:
        line = line.strip()
        content = line.split()
        indicator = content[0]
        quantity = float(content[1])
        if quantity < min_resolution:
            continue
        quantity_index = int(math.log(quantity / min_resolution, base) * logres)
        distrib[indicator][quantity_index] += 1.0
        total_count += 1
        # print indicator, d_index, distrib[indicator][d_index] + '\n'
    for i in trajectory.indicator_list:
        count = sum(distrib[i])
        if not count:
            continue
        print i, '%.1f%%' % (count / total_count * 200)
        for j in xrange(maxloglen):
            if distrib[i][j] > 0.5:
                x = math.pow(base, (j + 0.5) / logres)
                p = (distrib[i][j] / count /
                     (math.pow(base, (j+1.0) / logres) -
                      math.pow(base, float(j) / logres)))
                print '%.12f\t%.12f' % (x, p)
        print
    return 1


def main():
    mapreducer = {'mapper': mapper, 'reducer': reducer}
    if len(sys.argv) < 2 or sys.argv[1] not in mapreducer:
        exit(0)
    return mapreducer[sys.argv[1]]()


if __name__ == '__main__':
    main()
