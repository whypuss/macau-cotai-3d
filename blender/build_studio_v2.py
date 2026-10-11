
import bpy, math, os
from mathutils import Vector

# Fresh scene for v2
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.render.resolution_x = 2560
scene.render.resolution_y = 1440
scene.render.film_transparent = False

def new_mat(name, base_color, metallic=0.0, roughness=0.5, emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(400,0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location=(0,0)
    def si(k,v):
        if k in bsdf.inputs: bsdf.inputs[k].default_value=v
    si('Base Color', base_color); si('Metallic', metallic); si('Roughness', roughness)
    if emission_color is not None and 'Emission Color' in bsdf.inputs:
        si('Emission Color', emission_color)
    if 'Emission Strength' in bsdf.inputs:
        si('Emission Strength', emission_strength)
    if emission_color is not None and 'Emission' in bsdf.inputs and 'Emission Color' not in bsdf.inputs:
        si('Emission', emission_color)
    try: nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    except: pass
    return mat

def bevel(o,w=0.12,seg=3):
    m=o.modifiers.new(name="Bevel",type='BEVEL'); m.width=w; m.segments=seg; m.limit_method='ANGLE'; m.angle_limit=math.radians(28)

# --- Mats ---
mat_wall = new_mat("Wall_Cream", (0.93,0.89,0.81,1), 0.02, 0.68)
mat_gold = new_mat("Wall_Gold", (0.91,0.81,0.57,1), 0.08, 0.58)
mat_fin = new_mat("Fin_Bronze", (0.66,0.56,0.40,1), 0.38, 0.42)
mat_glass = new_mat("Glass_Blue", (0.16,0.26,0.60,1), 0.0, 0.12)
mat_glass_dark = new_mat("Glass_Dark", (0.09,0.14,0.28,1), 0.0, 0.18)
try: mat_glass.blend_method='BLEND'; mat_glass_dark.blend_method='BLEND'
except: pass
mat_podium = new_mat("Podium_Stone", (0.87,0.83,0.77,1), 0.05, 0.62)
mat_band = new_mat("Band_Light", (1,1,1,1), emission_color=(1,0.92,0.52,1), emission_strength=5.0)
mat_ring_gold = new_mat("Ring_Gold", (1,0.86,0.38,1), 0.55, 0.30, emission_color=(1,0.62,0.12,1), emission_strength=2.6)
mat_ring_blue = new_mat("Ring_Blue", (0.70,0.83,1,1), 0.48, 0.32, emission_color=(0.22,0.54,1,1), emission_strength=2.4)
mat_truss = new_mat("Truss_Dark", (0.14,0.14,0.16,1), 0.35, 0.55)
mat_cabin = new_mat("Cabin_Gold", (0.94,0.88,0.62,1), 0.18, 0.38)
mat_cabin_glass = new_mat("Cabin_Glass", (0.18,0.28,0.55,1), 0.0, 0.10)
try: mat_cabin_glass.blend_method='BLEND'
except: pass
mat_hub = new_mat("Hub", (1,1,1,1), emission_color=(1,1,1,1), emission_strength=7.0)
mat_ground = new_mat("Ground_Asphalt", (0.08,0.10,0.14,1), 0.0, 0.82)
mat_road = new_mat("Road", (0.11,0.13,0.18,1), 0.12, 0.48)
mat_line = new_mat("Line", (1,0.96,0.62,1), emission_color=(1,0.80,0.18,1), emission_strength=1.8)
mat_lake = new_mat("Lake", (0.10,0.28,0.50,1), 0.45, 0.22)
mat_concrete = new_mat("Concrete", (0.82,0.82,0.80,1), 0.0, 0.85)

# --- Ground + Cotai avenue ---
bpy.ops.mesh.primitive_plane_add(size=520, location=(0,0,0))
g=bpy.context.active_object; g.name="Ground"; g.data.materials.append(mat_ground)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0.02))
road=bpy.context.active_object; road.name="Avenue"; road.scale=(260,22,1); road.data.materials.append(mat_road)
for i in range(-118, 122, 12):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(i,0,0.04))
    lm=bpy.context.active_object; lm.name=f"Mark_{i}"; lm.scale=(5.2,0.42,1); lm.data.materials.append(mat_line)
# side walks
for side in (-1,1):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, side*14, 0.03))
    sw=bpy.context.active_object; sw.name=f"Sidewalk_{side}"; sw.scale=(260,4.2,1); sw.data.materials.append(mat_concrete)
# curb lines
for i in range(-118, 122, 6):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(i, 11, 0.035))
    cb=bpy.context.active_object; cb.name=f"Curb_{i}"; cb.scale=(0.8,0.8,1); cb.data.materials.append(mat_line)

# --- Tower v2: stepped Art Deco with window bays + fins ---
def build_tower_v2(name, cx, cy, h_total=46):
    col=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)
    # Podium - larger with chamfer and entrance canopy
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, 2.8))
    pod=bpy.context.active_object; pod.name=f"{name}_Podium"; pod.scale=(22,22,5.6)
    pod.data.materials.append(mat_podium); bevel(pod,0.45,3)
    col.objects.link(pod); bpy.context.scene.collection.objects.unlink(pod)
    # entrance canopy (front face)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy+10.5, 3.2))
    can=bpy.context.active_object; can.name=f"{name}_Canopy"; can.scale=(10,4,0.55)
    can.data.materials.append(mat_concrete); bevel(can,0.08,2)
    col.objects.link(can); bpy.context.scene.collection.objects.unlink(can)
    # pillars under canopy
    for sx in (-3.2, 0, 3.2):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.32, depth=3.0, location=(cx+sx, cy+12.2, 1.6))
        pil=bpy.context.active_object; pil.name=f"{name}_Pillar_{sx}"; pil.data.materials.append(mat_podium)
        col.objects.link(pil); bpy.context.scene.collection.objects.unlink(pil)
    # light band
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, 5.7))
    band=bpy.context.active_object; band.name=f"{name}_Band"; band.scale=(22.8,22.8,0.62)
    band.data.materials.append(mat_band)
    col.objects.link(band); bpy.context.scene.collection.objects.unlink(band)

    levels=[(11.2, h_total*0.58), (8.6, h_total*0.27), (6.4, h_total*0.18)]
    z=5.95
    for idx,(w,h) in enumerate(levels):
        # main block
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, z+h/2))
        blk=bpy.context.active_object; blk.name=f"{name}_Blk_{idx}"; blk.scale=(w,w,h)
        blk.data.materials.append(mat_wall if idx==0 else mat_gold); bevel(blk,0.22,3)
        col.objects.link(blk); bpy.context.scene.collection.objects.unlink(blk)
        # bronze fins on front + sides (more dense than v1)
        if idx==0:
            # front fins (7 nos, deeper)
            for f in range(7):
                fx=cx + (f-3)*1.45
                bpy.ops.mesh.primitive_cube_add(size=1, location=(fx, cy+ w/2+0.05, z+h/2))
                fin=bpy.context.active_object; fin.name=f"{name}_FinF_{f}"; fin.scale=(0.28,0.55,w*0.05)
                # actually scale: width 0.28, depth 0.55, height h*0.93
                fin.scale=(0.28,0.55,h*0.93)
                fin.data.materials.append(mat_fin)
                col.objects.link(fin); bpy.context.scene.collection.objects.unlink(fin)
            # side fins
            for f in range(5):
                fz=z+1.8+f*2.6
                for side in (-1,1):
                    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx+side*(w/2+0.22), cy, fz))
                    # placeholder to be removed, will do side vertical strips via planes
                    bpy.context.active_object.data.materials.append(mat_fin)
                    # keep but small
                    o=bpy.context.active_object; o.scale=(0.5, w*0.85, 0.18); o.name=f"{name}_SideFin_{f}_{side}"
                    col.objects.link(o); bpy.context.scene.collection.objects.unlink(o)
            # window bays: recessed - create frames + glass
            floors=10
            for fy in range(floors):
                wz=z+2.0+fy*2.55
                # continuous horizontal mullion
                bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy+ w/2+0.02, wz+0.85))
                mull=bpy.context.active_object; mull.name=f"{name}_MullH_{fy}"; mull.scale=(w-0.8,0.12,0.10)
                mull.data.materials.append(mat_podium)
                col.objects.link(mull); bpy.context.scene.collection.objects.unlink(mull)
                # vertical bays (4 bays)
                for bay in range(4):
                    bx=cx + (bay-1.5)*2.35
                    # glass pane recessed
                    bpy.ops.mesh.primitive_plane_add(size=1, location=(bx, cy+ w/2+0.06, wz))
                    pane=bpy.context.active_object; pane.name=f"{name}_Pane_{fy}_{bay}"; pane.scale=(1.85,1,1.45)
                    pane.rotation_euler=(0, math.radians(90), 0)
                    # plane orientation: need to face +Y
                    pane.rotation_euler=(math.radians(90),0,0)
                    # fix: plane default normal +Z, rotate to +Y
                    pane.rotation_euler=(math.radians(90),0,0)
                    # alternate lit/dark randomly
                    import random as _r
                    pane.data.materials.append(mat_glass if _r.random()>0.22 else mat_glass_dark)
                    col.objects.link(pane); bpy.context.scene.collection.objects.unlink(pane)
        z+=h
    # crown Art Deco ziggurat (4 steps, more refined)
    cz=z
    for k in range(4):
        s=5.8 - k*1.0
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz+0.42))
        cr=bpy.context.active_object; cr.name=f"{name}_Crown_{k}"; cr.scale=(s,s,0.84)
        cr.data.materials.append(mat_gold); bevel(cr,0.14,2)
        col.objects.link(cr); bpy.context.scene.collection.objects.unlink(cr)
        cz+=0.92
    # pinnacle spire
    bpy.ops.mesh.primitive_cone_add(radius1=0.9, radius2=0.08, depth=3.2, location=(cx, cy, cz+1.4))
    spire=bpy.context.active_object; spire.name=f"{name}_Spire"; spire.data.materials.append(mat_fin)
    col.objects.link(spire); bpy.context.scene.collection.objects.unlink(spire)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.48, location=(cx, cy, cz+3.1))
    tip=bpy.context.active_object; tip.name=f"{name}_Tip"; tip.data.materials.append(mat_hub)
    col.objects.link(tip); bpy.context.scene.collection.objects.unlink(tip)
    return col

tA=build_tower_v2("TowerA", -11.4, -4.0, 46)
tB=build_tower_v2("TowerB", 11.4, -4.0, 43)

# sky bridge
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -4.0, 24.5))
br=bpy.context.active_object; br.name="SkyBridge"; br.scale=(25,3.4,1.15); br.data.materials.append(mat_fin); bevel(br,0.14,2)
# bridge glass walkway
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -4.0, 24.9))
bg=bpy.context.active_object; bg.name="BridgeGlass"; bg.scale=(23,2.0,0.22); bg.data.materials.append(mat_glass)
# bridge support cables (4)
for sx in (-7, -2.5, 2.5, 7):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=7.5, location=(sx, -4.0, 21.2))
    cab=bpy.context.active_object; cab.name=f"Cable_{sx}"; cab.data.materials.append(mat_truss)

# --- Figure-8 Golden Reel: true truss ---
center=(0, -4.0, 27.2)
R=11.6
# Two rings using torus with thicker tube + wireframe for lattice
def make_ring(name, ctr, tilt_x, tilt_y, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.46, major_segments=96, minor_segments=22, location=ctr)
    r=bpy.context.active_object; r.name=name; r.rotation_euler=(math.radians(tilt_x), math.radians(tilt_y), 0)
    r.data.materials.append(mat)
    wf=r.modifiers.new(name="Wire", type='WIREFRAME'); wf.thickness=0.055; wf.use_replace=False; wf.material_offset=1
    if len(r.data.materials)<2: r.data.materials.append(mat_truss)
    else: r.data.materials[1]=mat_truss
    return r

rA=make_ring("RingA_Gold", (center[0], center[1], center[2]+7.4), 6, 9, mat_ring_gold)
rB=make_ring("RingB_Blue", (center[0], center[1], center[2]-7.4), -6, -9, mat_ring_blue)
# radial spokes (16 per ring)
for ring_ctr, tilt in [((center[0],center[1],center[2]+7.4),(6,9)), ((center[0],center[1],center[2]-7.4),(-6,-9))]:
    name_prefix="SpokeA" if ring_ctr[2]>center[2] else "SpokeB"
    for i in range(16):
        ang=(i/16)*math.pi*2
        x=math.cos(ang)*R; y=math.sin(ang)*R
        # spoke from center to rim: cylinder
        sx=ring_ctr[0]+x*0.5; sy=ring_ctr[1]+y*0.12; sz=ring_ctr[2]+y*0.5
        # approximate: place thin cylinder along radial
        bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=R, location=(sx, sy, sz))
        sp=bpy.context.active_object; sp.name=f"{name_prefix}_{i}"
        # orient radial in YZ plane
        sp.rotation_euler=(math.radians(90), 0, ang)
        sp.data.materials.append(mat_truss)
        # apply tilt of ring roughly: rotate around X/Y
        sp.rotation_euler=(math.radians(tilt[0]), math.radians(tilt[1]), ang)

# cabins: real Golden Reel has 17, we do 17 per ring? Actually 17 total figure-8, but for animation we place 17 on combined path
# We'll place 17 cabins distributed on the 8: 9 on A, 8 on B alternating
import random
# Use capsules (UV sphere scaled) for cabins
def cabin(name, x,y,z):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.58, location=(x,y,z))
    c=bpy.context.active_object; c.name=name; c.scale=(1,0.72,1.35)
    c.data.materials.append(mat_cabin)
    # small glass window on cabin
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y+0.18, z))
    win=bpy.context.active_object; win.name=name+"_Win"; win.scale=(0.9,0.12,0.55)
    win.data.materials.append(mat_cabin_glass)
    return c

nA=9; nB=8
for i in range(nA):
    ang=(i/nA)*math.pi*2; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin(f"CabinA_{i:02d}", center[0]+x*0.985, center[1]+y*0.10, center[2]+7.4+y)
for i in range(nB):
    ang=(i/nB)*math.pi*2 + math.pi/nB; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin(f"CabinB_{i:02d}", center[0]+x*0.985, center[1]+y*0.10, center[2]-7.4+y)

# hub
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.92, location=center)
hub=bpy.context.active_object; hub.name="Hub"; hub.data.materials.append(mat_hub)
ld=bpy.data.lights.new(name="HubLight", type='POINT'); ld.energy=2200; ld.color=(1,1,1)
lo=bpy.data.objects.new(name="HubLightObj", object_data=ld); lo.location=center; bpy.context.collection.objects.link(lo)
# additional point lights on tower tops
for cx in (-11.4, 11.4):
    ld2=bpy.data.lights.new(name=f"TowerTopLight_{cx}", type='POINT'); ld2.energy=1400; ld2.color=(1,0.88,0.62)
    lo2=bpy.data.objects.new(name=f"TowerTopLightObj_{cx}", object_data=ld2); lo2.location=(cx, -4.0, 46); bpy.context.collection.objects.link(lo2)

# Camera
cam_data=bpy.data.cameras.new(name="PreviewCam"); cam_obj=bpy.data.objects.new(name="PreviewCamObj", object_data=cam_data)
cam_obj.location=(42, -38, 30)
direction=Vector(center)-cam_obj.location; cam_obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
bpy.context.scene.collection.objects.link(cam_obj); bpy.context.scene.camera=cam_obj

# World keep default (factory has none)

out_dir="/Users/whypuss/.hermes/profiles/puss_profile/cache/scratch/macau-3d-city/exports"
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir,"studio-v2.blend"))
glb=os.path.join(out_dir,"studio-v2.glb")
try:
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_texcoords=True, export_normals=True, export_materials='EXPORT')
    print(f"GLB v2 exported: {glb} size={os.path.getsize(glb)}")
except Exception as e:
    import traceback; traceback.print_exc()
print(f"Objects v2: {len(bpy.data.objects)}")
print("DONE V2")
