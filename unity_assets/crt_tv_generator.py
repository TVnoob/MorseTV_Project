import math

# ---------------------------------------------------------------- mesh core
class Mesh:
    def __init__(self):
        self.v = []
        self.vt = []
        self.vn = []
        self.groups = []
        self.cur = None

    def mat(self, name):
        self.cur = [name, []]
        self.groups.append(self.cur)

    def _nrm(self, pts):
        ax = [pts[1][i] - pts[0][i] for i in range(3)]
        bx = [pts[2][i] - pts[0][i] for i in range(3)]
        n = [ax[1]*bx[2]-ax[2]*bx[1], ax[2]*bx[0]-ax[0]*bx[2], ax[0]*bx[1]-ax[1]*bx[0]]
        L = math.sqrt(sum(c*c for c in n)) or 1.0
        return [c/L for c in n]

    def face(self, pts, uvs, expect):
        """Add a flat-shaded polygon. `expect` = rough outward direction;
        winding is auto-corrected so the normal points that way."""
        n = self._nrm(pts)
        if sum(n[i]*expect[i] for i in range(3)) < 0:
            pts = list(reversed(pts)); uvs = list(reversed(uvs))
            n = self._nrm(pts)
        vi = []
        for p in pts:
            self.v.append(p); vi.append(len(self.v))
        ti = []
        for t in uvs:
            self.vt.append(t); ti.append(len(self.vt))
        self.vn.append(n); ni = len(self.vn)
        self.cur[1].append([(vi[k], ti[k], ni) for k in range(len(pts))])

    def add_shared(self, p, uv, n):
        self.v.append(p); self.vt.append(uv); self.vn.append(n)
        return (len(self.v), len(self.vt), len(self.vn))

    def raw_face(self, refs):
        self.cur[1].append(list(refs))

    def write(self, path, mtlname):
        L = ["# Vintage CRT television - generated for VRChat",
             "mtllib " + mtlname]
        for p in self.v:  L.append("v %.5f %.5f %.5f" % tuple(p))
        for t in self.vt: L.append("vt %.5f %.5f" % tuple(t))
        for n in self.vn: L.append("vn %.5f %.5f %.5f" % tuple(n))
        for name, faces in self.groups:
            L.append("g " + name); L.append("usemtl " + name)
            for f in faces:
                L.append("f " + " ".join("%d/%d/%d" % r for r in f))
        open(path, "w").write("\n".join(L) + "\n")

    def tris(self):
        return sum(len(f) - 2 for _, fs in self.groups for f in fs)


# ---------------------------------------------------------------- primitives
def box(m, x0, y0, z0, x1, y1, z1):
    m.face([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)], [(0,0),(1,0),(1,1),(0,1)], (0,0,1))
    m.face([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)], [(0,0),(1,0),(1,1),(0,1)], (0,0,-1))
    m.face([(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)], [(0,0),(1,0),(1,1),(0,1)], (-1,0,0))
    m.face([(x1,y0,z0),(x1,y0,z1),(x1,y1,z1),(x1,y1,z0)], [(0,0),(1,0),(1,1),(0,1)], (1,0,0))
    m.face([(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)], [(0,0),(1,0),(1,1),(0,1)], (0,1,0))
    m.face([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)], [(0,0),(1,0),(1,1),(0,1)], (0,-1,0))


def frame(m, out, inn, z, expect):
    """Flat rectangular ring (a bezel with a hole) at plane z."""
    x0, x1, y0, y1 = out
    a0, a1, b0, b1 = inn
    for q in ([(x0,y0),(x1,y0),(x1,b0),(x0,b0)],
              [(x0,b1),(x1,b1),(x1,y1),(x0,y1)],
              [(x0,b0),(a0,b0),(a0,b1),(x0,b1)],
              [(a1,b0),(x1,b0),(x1,b1),(a1,b1)]):
        pts = [(p[0], p[1], z) for p in q]
        uvs = [((p[0]-x0)/(x1-x0), (p[1]-y0)/(y1-y0)) for p in q]
        m.face(pts, uvs, expect)


def loft(m, ra, za, rb, zb, flip=False):
    """Connect two axis-aligned rectangles at different depths (tapered shell)."""
    ax0, ax1, ay0, ay1 = ra
    bx0, bx1, by0, by1 = rb
    A = [(ax0,ay0),(ax1,ay0),(ax1,ay1),(ax0,ay1)]
    B = [(bx0,by0),(bx1,by0),(bx1,by1),(bx0,by1)]
    exp = [(0,-1,0),(1,0,0),(0,1,0),(-1,0,0)]
    if flip: exp = [tuple(-c for c in e) for e in exp]
    for i in range(4):
        j = (i+1) % 4
        pts = [(A[i][0],A[i][1],za),(A[j][0],A[j][1],za),
               (B[j][0],B[j][1],zb),(B[i][0],B[i][1],zb)]
        m.face(pts, [(0,0),(1,0),(1,1),(0,1)], exp[i])


def cylinder_z(m, cx, cy, z0, z1, r0, r1, seg=14, cap_front=True):
    """Smooth-sided cylinder/cone along Z (used for knobs)."""
    ring0, ring1 = [], []
    for i in range(seg):
        a = 2*math.pi*i/seg
        c, s = math.cos(a), math.sin(a)
        n = (c, s, 0.0)
        ring0.append(m.add_shared((cx+r0*c, cy+r0*s, z0), (i/seg, 0.0), n))
        ring1.append(m.add_shared((cx+r1*c, cy+r1*s, z1), (i/seg, 1.0), n))
    for i in range(seg):
        j = (i+1) % seg
        m.raw_face([ring0[i], ring0[j], ring1[j], ring1[i]])
    if cap_front:
        n = (0, 0, 1 if z1 > z0 else -1)
        cap = [m.add_shared((cx+r1*math.cos(2*math.pi*i/seg),
                             cy+r1*math.sin(2*math.pi*i/seg), z1),
                            (0.5+0.5*math.cos(2*math.pi*i/seg),
                             0.5+0.5*math.sin(2*math.pi*i/seg)), n)
               for i in range(seg)]
        if n[2] < 0: cap.reverse()
        m.raw_face(cap)


def rod(m, p0, p1, r, seg=8):
    """Thin cylinder between two arbitrary points (antenna)."""
    d = [p1[i]-p0[i] for i in range(3)]
    L = math.sqrt(sum(c*c for c in d)) or 1.0
    d = [c/L for c in d]
    up = (0,0,1) if abs(d[2]) < 0.9 else (1,0,0)
    u = [d[1]*up[2]-d[2]*up[1], d[2]*up[0]-d[0]*up[2], d[0]*up[1]-d[1]*up[0]]
    lu = math.sqrt(sum(c*c for c in u)); u = [c/lu for c in u]
    w = [d[1]*u[2]-d[2]*u[1], d[2]*u[0]-d[0]*u[2], d[0]*u[1]-d[1]*u[0]]
    A, B = [], []
    for i in range(seg):
        a = 2*math.pi*i/seg
        off = [r*(math.cos(a)*u[k] + math.sin(a)*w[k]) for k in range(3)]
        n = [off[k]/r for k in range(3)]
        A.append(m.add_shared([p0[k]+off[k] for k in range(3)], (i/seg, 0), n))
        B.append(m.add_shared([p1[k]+off[k] for k in range(3)], (i/seg, 1), n))
    for i in range(seg):
        j = (i+1) % seg
        m.raw_face([A[i], A[j], B[j], B[i]])


# ---------------------------------------------------------------- dimensions
W, H, D = 0.44, 0.38, 0.46          # cabinet width / height / depth (metres)
FOOT = 0.035                         # foot height
x0, x1 = -W/2, W/2
y0, y1 = FOOT, FOOT + H
zf, zb = D/2, -D/2                   # front / rear plane
z_straight = -0.10                   # cabinet stays boxy until here, then tapers

SX0, SX1 = -0.185, 0.095               # screen opening (4:3)
SY0, SY1 = 0.12, 0.33
ZS = zf - 0.028                      # screen sits recessed behind the bezel
BULGE = 0.016                        # convex tube curvature

BX0, BX1 = -0.185, 0.065             # narrow rear of the picture-tube housing
BY0, BY1 = 0.135, 0.315

m = Mesh()

# --- cabinet -------------------------------------------------------------
m.mat("TV_Body")
frame(m, (x0, x1, y0, y1), (SX0, SX1, SY0, SY1), zf, (0, 0, 1))   # front bezel
loft(m, (SX0, SX1, SY0, SY1), zf, (SX0, SX1, SY0, SY1), ZS, flip=True)       # bezel inner wall
loft(m, (x0, x1, y0, y1), zf, (x0, x1, y0, y1), z_straight)        # boxy section
loft(m, (x0, x1, y0, y1), z_straight, (BX0, BX1, BY0, BY1), zb)    # taper to rear
m.face([(BX0,BY0,zb),(BX1,BY0,zb),(BX1,BY1,zb),(BX0,BY1,zb)],
       [(0,0),(1,0),(1,1),(0,1)], (0,0,-1))                        # rear panel

# --- feet ----------------------------------------------------------------
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx*(W/2-0.055), sz*(D/2-0.06)
        box(m, cx-0.028, 0.0, cz-0.028, cx+0.028, FOOT+0.002, cz+0.028)

# --- screen (shared verts, analytic normals -> smooth curvature) ----------
m.mat("TV_Screen")
NX, NY = 14, 11
grid = []
for j in range(NY+1):
    row = []
    tv = j/NY
    for i in range(NX+1):
        tu = i/NX
        nx, ny = 2*tu-1, 2*tv-1
        px = SX0 + (SX1-SX0)*tu
        py = SY0 + (SY1-SY0)*tv
        pz = ZS + BULGE*(1-nx*nx)*(1-ny*ny)
        dzx = BULGE*(-2*nx)*(1-ny*ny) / ((SX1-SX0)/2)
        dzy = BULGE*(1-nx*nx)*(-2*ny) / ((SY1-SY0)/2)
        n = [-dzx, -dzy, 1.0]
        L = math.sqrt(sum(c*c for c in n)); n = [c/L for c in n]
        row.append(m.add_shared((px, py, pz), (tu, tv), n))
    grid.append(row)
for j in range(NY):
    for i in range(NX):
        m.raw_face([grid[j][i], grid[j][i+1], grid[j+1][i+1], grid[j+1][i]])

# --- control knobs -------------------------------------------------------
m.mat("TV_Knob")
panel_cx = (SX1 + x1)/2
for cy, r in ((0.305, 0.033), (0.225, 0.033), (0.145, 0.021)):
    cylinder_z(m, panel_cx, cy, zf-0.004, zf+0.021, r, r*0.88)

# --- rabbit-ear antenna (own group: delete it if you don't want it) -------
m.mat("TV_Antenna")
for sx in (-1, 1):
    base = (sx*0.035, y1, -0.13)
    rod(m, base, (sx*0.30, y1+0.33, -0.26), 0.005)
    box(m, sx*0.035-0.018, y1-0.006, -0.148, sx*0.035+0.018, y1+0.016, -0.112)

m.write("/mnt/user-data/outputs/crt_tv.obj", "crt_tv.mtl")

mtl = """# Materials for crt_tv.obj
newmtl TV_Body
Kd 0.42 0.36 0.30
Ks 0.05 0.05 0.05
Ns 12

newmtl TV_Screen
Kd 0.06 0.07 0.07
Ks 0.60 0.60 0.60
Ns 90

newmtl TV_Knob
Kd 0.20 0.18 0.16
Ks 0.25 0.25 0.25
Ns 40

newmtl TV_Antenna
Kd 0.55 0.55 0.58
Ks 0.60 0.60 0.60
Ns 70
"""
open("/mnt/user-data/outputs/crt_tv.mtl", "w").write(mtl)
print("triangles:", m.tris(), " verts:", len(m.v), " groups:", [g[0] for g in m.groups])
