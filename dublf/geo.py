import numpy as np
import math
import mathutils as mu
from collections import defaultdict
import bmesh


def dist_point_line(p, l1, l2):
    x0, y0 = p
    x1, y1 = l1
    x2, y2 = l2
    y21 = y2 - y1
    x21 = x2 - x1
    if l1[0] == l2[0] and l1[1] == l2[1]:
        return math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
    return abs(y21 * x0 - x21 * y0 + x2 * y1 - y2 * x1) / math.sqrt(y21 ** 2 + x21 ** 2)


# if HAS_NUMBA:
#     dist_point_line = numba.njit(dist_point_line)


def _dpcall3(chain, eps):
    stack = [(0, len(chain) - 1)]
    result = []
    while stack:
        pl0, pl1 = stack.pop()

        dmax = 0
        index = 0

        x1, y1 = chain[pl0]
        x2, y2 = chain[pl1]
        y21 = y2 - y1
        x21 = x2 - x1
        tsq2 = math.sqrt(y21 ** 2 + x21 ** 2)
        xyyx = x2 * y1 - y2 * x1
        for i in range(pl0 + 1, pl1):
            x0, y0 = chain[i]
            d = 0.0

            # if x1 == x2 and y1 == y2:
            #     d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            # else:
            d = abs(y21 * x0 - x21 * y0 + xyyx) / tsq2

            if d > dmax:
                index = i
                dmax = d

        if dmax <= eps:
            result.append(chain[pl0])
        else:
            stack.append((index, pl1))
            stack.append((pl0, index - 1))

    # result.append(chain[-1])
    return result


# @numba.jit
def douglas_peucker(ch, margin):
    # t = ch[:]
    # res = _dpcall2(ch, margin)
    # assert len(res) <= len(t)
    return _dpcall3(ch, margin)


class Chain:
    def __init__(self):
        self.verts = []
        self.inner = False
        self.bm_verts = []
        self.invalid = False

        self._pvert = None
        self._cvert = None

        self._minx = None
        self._minx_id = 0

        self._miny = None
        self._miny_id = 0

        self._maxx = None
        self._maxx_id = 0

        self._maxy = None
        self._maxy_id = 0

        self._segments = None
        self._np_segments = None

        self.parent = None
        self.children = []

    def __len__(self):
        return len(self.verts)

    def verify(self):
        for i in range(len(self.verts)):
            v0 = self.verts[i]
            v1 = self.verts[(i + 1) % len(self.verts)]
            if v0 == v1:
                return False
        if self.verts[0] == self.verts[-1]:
            return False
        return True

    def add_vert(self, vert):
        if self._cvert == None:
            self._pvert = vert
            self._cvert = vert
            self._miny = vert[1]
            self._minx = vert[0]
            self._maxy = vert[1]
            self._maxx = vert[0]

        self._pvert = self._cvert
        self._cvert = vert

        if self._cvert[0] < self._minx:
            self._minx = self._cvert[0]
            self._minx_id = len(self.verts)

        if self._cvert[1] < self._miny:
            self._miny = self._cvert[1]
            self._miny_id = len(self.verts)

        if self._cvert[0] > self._maxx:
            self._maxx = self._cvert[0]
            self._maxx_id = len(self.verts)

        if self._cvert[1] > self._maxy:
            self._maxy = self._cvert[1]
            self._maxy_id = len(self.verts)

        self.verts.append(vert)

    def get_end_location(self, loc="BOTTOM"):
        if loc == "CENTER":
            # x, y = 0.0, 0.0
            # for v in self.verts:
            #     x += v[0]
            #     y += v[1]
            # return (x / len(self.verts), y / len(self.verts))
            maxx = self.verts[self._maxx_id][0]
            minx = self.verts[self._minx_id][0]
            maxy = self.verts[self._maxy_id][1]
            miny = self.verts[self._miny_id][1]
            return ((maxx + minx) / 2, (maxy + miny) / 2)

        return self.verts[
            {
                "LEFT": self._miny_id,
                "RIGHT": self._maxy_id,
                "BOTTOM": self._minx_id,
                "TOP": self._maxx_id,
            }[loc]
        ]

    def _recalc_bb(self):
        self._miny = self.verts[0][1]
        self._minx = self.verts[0][0]
        self._maxy = self.verts[0][1]
        self._maxx = self.verts[0][0]
        self._miny_id = 0
        self._minx_id = 0
        self._maxy_id = 0
        self._maxx_id = 0
        for i in range(len(self.verts)):
            cvert = self.verts[i]
            if cvert[0] < self._minx:
                self._minx = cvert[0]
                self._minx_id = i

            if cvert[1] < self._miny:
                self._miny = cvert[1]
                self._miny_id = i

            if cvert[0] > self._maxx:
                self._maxx = cvert[0]
                self._maxx_id = i

            if cvert[1] > self._maxy:
                self._maxy = cvert[1]
                self._maxy_id = i

    def get_segments(self):
        if self._segments == None:
            self._segments = list(zip(self.verts, list(self.verts[1:]) + [self.verts[0]]))
            self._np_segments = np.array(self._segments)
        return (self._segments, self._np_segments)

    def inside(self, other):
        if (
            self._minx > other._maxx
            or self._miny > other._maxy
            or self._maxx < other._minx
            or self._maxy < other._miny
        ):
            return False

        mp = self.verts[self._miny_id]
        tlp = mp[0] + 0.001
        test_line = ((tlp, other._miny - 1.0), (tlp, mp[1]))
        isect_count = 0

        # ...if segment points at opposite sides of the tested line
        np_segs = other.get_segments()[1]
        seg_ids = (np_segs[:, 0, 0] - tlp) * (np_segs[:, 1, 0] - tlp) <= 0.0
        np_segs_line = np_segs[seg_ids]
        for s in np_segs_line:
            if mu.geometry.intersect_line_line_2d(test_line[0], test_line[1], s[0], s[1]):
                isect_count += 1
        return isect_count % 2 != 0

    def simplify(self, error):
        tmp = douglas_peucker(self.verts, error)
        if len(tmp) > 3:
            self.verts = tmp
            self._recalc_bb()
        else:
            self.invalid = True

    def smooth(self, amount, t):
        ch = self.verts
        for _ in range(t):
            for i in range(len(ch)):
                vl = ch[(i - 1) % len(ch)]
                vr = ch[(i + 1) % len(ch)]
                x = ((vl[0] + vr[0]) * 0.5) * amount + ch[i][0] * (1.0 - amount)
                y = ((vl[1] + vr[1]) * 0.5) * amount + ch[i][1] * (1.0 - amount)
                ch[i] = (x, y)
        self.verts = ch


def lines_square(img, cutoff):
    nm = img > cutoff

    # make black borders
    nm[0, :] = False
    nm[-1, :] = False
    nm[:, 0] = False
    nm[:, -1] = False

    # break one vert corners
    one_vert = ~nm[:-1, :-1] & nm[1:, :-1] & nm[:-1, 1:] & ~nm[1:, 1:]
    nm[:-1, :-1] = np.where(one_vert, True, nm[:-1, :-1])
    one_vert = nm[:-1, :-1] & ~nm[1:, :-1] & ~nm[:-1, 1:] & nm[1:, 1:]
    nm[:-1, :-1] = np.where(one_vert, False, nm[:-1, :-1])

    # fill singles
    not_single = nm[:-2, 1:-1] & nm[2:, 1:-1] & nm[1:-1, :-2] & nm[1:-1, 2:]
    nm[1:-1, 1:-1] = np.where(not_single * (~nm[1:-1, 1:-1]), True, nm[1:-1, 1:-1])

    # edge: l[x,y] -> l[x,y-1]
    ylocs = np.argwhere(nm[1:, :] != nm[:-1, :])
    y_verts = [((l[0], l[1]), (l[0], l[1] - 1)) for l in ylocs]

    nmt = nm.copy()
    nmt[1:-1, :] = False
    ylocs = np.argwhere(nmt)
    y_verts.extend([((l[0], l[1]), (l[0], l[1] - 1)) for l in ylocs])

    # edge: l[x,y] -> l[x-1,y]
    xlocs = np.argwhere(nm[:, 1:] != nm[:, :-1])
    x_verts = [((l[0], l[1]), (l[0] - 1, l[1])) for l in xlocs]

    nmt = nm.copy()
    nmt[:, 1:-1] = False
    xlocs = np.argwhere(nmt)
    x_verts.extend([((l[0], l[1]), (l[0] - 1, l[1])) for l in xlocs])

    return x_verts + y_verts


def lines_marching(img, cutoff, nm):
    # make black borders
    nm[0, :] = False
    nm[-1, :] = False
    nm[:, 0] = False
    nm[:, -1] = False

    zz = nm[:-1, :-1]
    oz = nm[1:, :-1]
    zo = nm[:-1, 1:]
    oo = nm[1:, 1:]

    verts = []

    ct_img = np.abs(cutoff - img)

    def _dif_y(v, pos):
        xpos = pos[0] + v[0]
        da = ct_img[xpos, pos[1]]
        db = ct_img[xpos, pos[1] + 1]
        td = da + db
        x, y = v[0], 0.0
        if td != 0:
            y = da * 0.999 / td
        return (x, y)

    def _dif_x(v, pos):
        ypos = pos[1] + v[1]
        da = ct_img[pos[0], ypos]
        db = ct_img[pos[0] + 1, ypos]
        td = da + db
        x, y = 0.0, v[1]
        if td != 0:
            x = da * 0.999 / td
        return (x, y)

    def _add(ia, da, check=None):
        ad0 = (da[0], da[1])
        ad1 = (da[2], da[3])

        locs = np.argwhere(ia)

        # make sure we are dealing with the same data we think we are
        # if check:
        #     for l in locs[:10]:
        #         ta = []
        #         ta.append(img[l[0], l[1]] > cutoff)
        #         ta.append(img[l[0] + 1, l[1]] > cutoff)
        #         ta.append(img[l[0], l[1] + 1] > cutoff)
        #         ta.append(img[l[0] + 1, l[1] + 1] > cutoff)
        #         assert sum(check[i] == v for i, v in enumerate(ta)) == 4

        f0 = _dif_y if ad0[0] == 0 or ad0[0] == 1 else _dif_x
        f1 = _dif_y if ad1[0] == 0 or ad1[0] == 1 else _dif_x

        for l in locs:
            m0x, m0y = f0(ad0, l)
            p0 = (l[0] + m0x, l[1] + m0y)

            m1x, m1y = f1(ad1, l)
            p1 = (l[0] + m1x, l[1] + m1y)

            verts.append((p0, p1))

    _add(zz & ~oz & ~zo & ~oo, [0, 0.5, 0.5, 0])
    _add(~zz & oz & ~zo & ~oo, [0.5, 0, 1, 0.5])
    _add(~zz & ~oz & zo & ~oo, [0, 0.5, 0.5, 1])
    _add(~zz & ~oz & ~zo & oo, [0.5, 1, 1, 0.5])

    _add(~zz & oz & zo & oo, [0, 0.5, 0.5, 0])
    _add(zz & ~oz & zo & oo, [0.5, 0, 1, 0.5])
    _add(zz & oz & ~zo & oo, [0, 0.5, 0.5, 1])
    _add(zz & oz & zo & ~oo, [0.5, 1, 1, 0.5])

    # _add(zz & oz & ~zo & ~oo, [0, 0.5, 1, 0.5], check=[1, 1, 0, 0])
    # _add(~zz & oz & ~zo & oo, [0.5, 0, 0.5, 1], check=[0, 1, 0, 1])
    # _add(~zz & ~oz & zo & oo, [0, 0.5, 1, 0.5], check=[0, 0, 1, 1])
    # _add(zz & ~oz & zo & ~oo, [0.5, 0, 0.5, 1], check=[1, 0, 1, 0])

    _add(zz & oz & ~zo & ~oo, [0, 0.5, 1, 0.5])
    _add(~zz & oz & ~zo & oo, [0.5, 0, 0.5, 1])

    _add(~zz & ~oz & zo & oo, [0, 0.5, 1, 0.5])
    _add(zz & ~oz & zo & ~oo, [0.5, 0, 0.5, 1])

    # \
    cross_a = ~zz & oz & zo & ~oo
    _add(cross_a, [0, 0.5, 0.5, 1])
    _add(cross_a, [0.5, 0, 1, 0.5])

    # /
    cross_b = zz & ~oz & ~zo & oo
    _add(cross_b, [0, 0.5, 0.5, 0])
    _add(cross_b, [0.5, 1, 1, 0.5])

    return verts


def parse_segments(self, l_verts):
    # create verts and connect edges
    edges = set()
    verts = []
    vert_ids = {}
    vert_edges = defaultdict(list)
    for l in l_verts:
        v0, v1 = l
        ev0, ev1 = 0, 0

        # limit to bounds
        if v0[0] < 0 or v0[1] < 0 or v1[0] < 0 or v1[1] < 0:
            continue

        if v0 in vert_ids:
            ev0 = vert_ids[v0]
        else:
            verts.append(v0)
            ev0 = len(verts) - 1
            vert_ids[v0] = ev0

        if v1 in vert_ids:
            ev1 = vert_ids[v1]
        else:
            verts.append(v1)
            ev1 = len(verts) - 1
            vert_ids[v1] = ev1

        edges.add((ev0, ev1))

        vert_edges[ev0].append(ev1)
        vert_edges[ev1].append(ev0)

    # parse chains
    chains = []
    remaining = set(list(range(len(verts))))
    failures = 0
    while len(remaining) > 0:
        chains.append(Chain())
        head = remaining.pop()
        prev = head
        start = head
        chains[-1].add_vert(verts[head])
        while True:
            # connected vert ids
            veh = vert_edges[head]

            if len(veh) == 1:
                head = veh[0]
                remaining.discard(head)
                chains[-1].add_vert(verts[head])
                failures += 1
                # added.add(head)
                break

            if len(veh) > 2:
                chains.pop()
                remaining.discard(head)
                failures += 1
                break

            here = veh[0] if veh[0] != head and veh[0] != prev else veh[1]
            prev = head
            head = here

            if head == start:
                break

            remaining.discard(head)
            chains[-1].add_vert(verts[head])

        # dist = np.linalg.norm(np.array(verts[prev]) - np.array(verts[start]))
        # if dist <= 0.0:
        #     print("too small:", dist)
        #     assert False
        # if dist >= 2.0:
        #     print("too big:", dist)
        #     assert False

        # if chains and (len(chains[-1]) < 6 or head != start):
        if chains and head != start:
            failures += 1
            chains.pop()

    # TODO: return codes instead
    if len(chains) == 0:
        print("Leafig: No polygons found at this cutoff value")
        return

    if failures > 0:
        print("Leafig: Chain failures:", failures)
    else:
        print("Successful parse.")

    return chains


def tri_ori(p1, p2, p3):
    # skip colinearity test
    return (p2[1] - p1[1]) * (p3[0] - p2[0]) - (p2[0] - p1[0]) * (p3[1] - p2[1]) > 0


def radial_edges(iv):
    loop = iv.link_loops[0]
    eg = []
    while True:
        eg.append(loop.edge)
        loop = loop.link_loop_radial_next.link_loop_next
        if loop.edge == eg[0]:
            break
    return eg


def triangle_strip_intersect(bm, v0, limit_len=0.0):
    # tstrip core point
    if not v0.is_valid:
        return True

    e_idx = [i for i, e in enumerate(v0.link_edges) if e.select]
    if len(e_idx) == 0:
        return True

    e_idx = e_idx[0]
    s_edge = v0.link_edges[e_idx]
    ov = s_edge.other_vert(v0)
    ovc = ov.co + (v0.co - ov.co) * 0.001

    edges = radial_edges(v0)

    if limit_len > 0.0:
        loc = edges.index(s_edge)
        e_left = edges[(loc + 1) % len(edges)]
        e_right = edges[(loc - 1) % len(edges)]
        avg_len = 0.0
        for e in edges:
            avg_len += e.calc_length()
        avg_len /= len(edges)

        if (e_left.calc_length() + e_right.calc_length()) * limit_len * 0.5 < avg_len:
            return True

    for i, e in enumerate(edges):
        # link_edges isn't in radial order dT_Tb
        # assert len(set(p1v.link_edges) & set(p2v.link_edges)) > 0
        p1 = e.other_vert(v0).co.xz
        p2 = edges[(i + 1) % len(edges)].other_vert(v0).co.xz
        if tri_ori(ovc.xz, p1, p2) != tri_ori(v0.co.xz, p1, p2):
            return True

    return False


def triangle_strip2(bm, v0):
    """ Tstrip based on v0 and connected, selected edge """
    ce = next(e for e in v0.link_edges if e.select)
    bmesh.ops.pointmerge(bm, verts=ce.verts, merge_co=ce.other_vert(v0).co)
    return True


def build_spine(bm):
    border = set([e for e in bm.edges if e.is_boundary])
    border_verts = set()
    for e in border:
        border_verts.add(e.verts[0])
        border_verts.add(e.verts[1])
    created_edges = set()
    dist_to_border = {v: 0.0 for v in bm.verts}

    # split non-boundary edges, move verts by edge_len / 2
    new_verts = set()
    vert_seg = {}
    for e in bm.edges[:]:
        if e not in border:
            el = e.calc_length()
            dist = el

            e_vec = (e.verts[0].co, e.verts[1].co)
            ne, v = bmesh.utils.edge_split(e, e.verts[0], 0.5)

            # calc min distance to border
            c_faces = list(e.link_faces)
            b_edges = []

            # check connected faces border edges for minimun distance to border
            for f in c_faces:
                b_edges.extend([i for i in f.edges if i in border])

            for be in b_edges:
                v0, v1 = be.verts
                pt = mu.geometry.intersect_point_line(v.co, v0.co, v1.co)[0]
                d = (pt - v.co).length * 2.0
                if d < dist:
                    dist = d

            new_verts.add(v)
            vert_seg[v] = e_vec
            dist_to_border[v] = dist

    # connect the new verts from the previous edge splits
    f_verts = set()
    f_connect = defaultdict(list)

    new_border = set()
    for f in bm.faces[:]:
        vloop = [v for v in f.verts if v in new_verts]
        if len(vloop) > 1:
            nedges = list(zip(vloop, vloop[1:] + [vloop[0]]))
            if len(nedges) == 2:
                nedges = [nedges[0]]

            # Check for duplicate edges, move to next face if exists
            dupe_exists = False
            for ne in nedges:
                if not tuple(ne) in created_edges:
                    created_edges.add(tuple(ne))
                    created_edges.add(tuple(ne[::-1]))
                else:
                    dupe_exists = True
                    break
            if dupe_exists:
                continue

            bedges = [bm.edges.new((ne[0], ne[1])) for ne in nedges]
            if len(bedges) > 1:
                # add longest edges to be split later
                be_len = [be.calc_length() for be in bedges]
                max_idx = be_len.index(max(be_len))
                # min_idx = be_len.index(min(be_len))

                for i in range(len(bedges)):
                    tbe = bedges[i]

                    # add all except the longest edge to the border
                    if max_idx != i:
                        v0, v1 = tbe.verts
                        f_verts.add(v0)
                        f_connect[v1].append(v0)
                        f_verts.add(v1)
                        f_connect[v0].append(v1)
                        new_border.add(tbe)
            else:
                # only 1 edge
                v0, v1 = bedges[0].verts

                f_verts.add(v0)
                f_connect[v1].append(v0)
                f_verts.add(v1)
                f_connect[v0].append(v1)
                new_border.add(bedges[0])

            for e in new_border:
                e.select = True

            # split face according to new_verts
            bmesh.utils.face_split_edgenet(f, bedges)
        elif len(vloop) == 1:
            # only 1 vert
            f_verts.add(vloop[0])

            # split quads
            if len(f.verts) == 4:
                vertl = f.loops[list(f.verts).index(vloop[0])]
                bmesh.utils.face_split(f, vloop[0], vertl.link_loop_next.link_loop_next.vert)

    # smooth result
    for _ in range(0):
        for v in f_verts:
            c_verts = f_connect[v]

            # check overlap
            # if len(c_verts) == 2:
            #     p00, p01 = [mu.Vector((i.y, i.z)) for i in vert_seg[v]]
            #     p10, p11 = [mu.Vector((i.co.y, i.co.z)) for i in c_verts]
            #     ipt = mu.geometry.intersect_line_line_2d(p00, p01, p10, p11)
            #     if ipt is None:
            #         continue

            if len(c_verts) > 1:
                # regular smoothing
                tt = mu.Vector((0, 0, 0))
                for cv in c_verts:
                    tt += cv.co
                v.co = tt / len(c_verts) * 0.5 + v.co * 0.5

    # iter from leafs
    count = 0
    skiplist = set()
    while count < 20:
        leafs = set(v for v in bm.verts if v.select and sum(e.select for e in v.link_edges) == 1)
        print(len(leafs))
        if len(leafs) == 0 or len(skiplist) == len(leafs):
            print("broke out")
            break

        for v in leafs:
            if v in skiplist:
                continue

            if not triangle_strip_intersect(bm, v, limit_len=1.2):
                triangle_strip2(bm, v)
            else:
                skiplist.add(v)

        count += 1

    # while tree:
    #     count = 0
    #     for e in list(tree):
    #         for i in range(2):
    #             if e.verts[i] in leafs:
    #                 v0 = e.verts[1 - i]
    #                 if sum(1 for e in v0.link_edges if e.select) == 2:
    #                     leafs.add(e.verts[1 - i])
    #                 leafs.discard(e.verts[i])
    #                 e.select = False
    #                 tree.discard(e)
    #                 faces.extend(e.verts[i].link_faces)
    #                 count += 1
    #     if count == 0:
    #         break

    # for f in faces:
    #     f.select = True

    # traversed = set()
    # for lv in leafs:
    #     traversed.add(lv)
    #     lv.select = True
    # lv = [e.other_vert(lv) for e in lv.link_edges if e.select][0]
    # traversed.add(lv)
    # while True:
    #     c_edges = [e for e in lv.link_edges if e.select == True]
    #     if len(c_edges) != 2:
    #         break
    #     lv = [v for v in [e.other_vert(lv) for e in c_edges] if v not in traversed]
    #     if len(lv) == 0:
    #         break
    #     lv = lv[0]
    #     traversed.add(lv)


def apply_transfrom(ob, use_location=False, use_rotation=False, use_scale=False):
    mb = ob.matrix_basis
    I = mu.Matrix()
    loc, rot, scale = mb.decompose()

    # rotation
    T = mu.Matrix.Translation(loc)
    #R = rot.to_matrix().to_4x4()
    R = mb.to_3x3().normalized().to_4x4()
    S = mu.Matrix.Diagonal(scale).to_4x4()

    transform = [I, I, I]
    basis = [T, R, S]

    def swap(i):
        transform[i], basis[i] = basis[i], transform[i]

    if use_location:
        swap(0)
    if use_rotation:
        swap(1)
    if use_scale:
        swap(2)
        
    M = transform[0] @ transform[1] @ transform[2]
    if hasattr(ob.data, "transform"):
        ob.data.transform(M)
    for c in ob.children:
        c.matrix_local = M @ c.matrix_local
        
    ob.matrix_basis = basis[0] @ basis[1] @ basis[2]