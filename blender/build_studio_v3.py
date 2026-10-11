
import bpy, math, os
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.render.resolution_x = 2560
scene.render.resolution_y = 1440

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

# Mats tuned to hero1.jpg: warm cream, deeper champagne, cool glass
mat_wall = new_mat("Wall_Cream", (0.945,0.915,0.845,1), 0.02, 0.64)
mat_gold = new_mat("Wall_Gold", (0.925,0.835,0.595,1), 0.08, 0.56)
mat_fin = new_mat("Fin_Bronze", (0.70,0.60,0.44,1), 0.42, 0.38)
mat_fin_dark = new_mat("Fin_Dark", (0.42,0.38,0.32,1), 0.32, 0.48)
mat_glass = new_mat("Glass_Blue", (0.15,0.28,0.62,1), 0.0, 0.12)
mat_glass_dark = new_mat("Glass_Dark", (0.08,0.13,0.26,1), 0.0, 0.20)
try: mat_glass.blend_method='BLEND'; mat_glass_dark.blend_method='BLEND'
except: pass
mat_podium = new_mat("Podium_Stone", (0.88,0.86,0.80,1), 0.05, 0.58)
mat_band = new_mat("Band_Light", (1,1,1,1), emission_color=(1,0.93,0.55,1), emission_strength=5.5)
mat_ring_gold = new_mat("Ring_Gold", (1,0.86,0.36,1), 0.58, 0.28, emission_color=(1,0.60,0.10,1), emission_strength=2.8)
mat_ring_blue = new_mat("Ring_Blue", (0.68,0.82,1,1), 0.50, 0.30, emission_color=(0.20,0.52,1,1), emission_strength=2.6)
mat_truss = new_mat("Truss", (0.16,0.16,0.18,1), 0.38, 0.52)
mat_cabin = new_mat("Cabin_Gold", (0.96,0.91,0.66,1), 0.20, 0.36)
mat_cabin_glass = new_mat("Cabin_Glass", (0.18,0.30,0.58,1), 0.0, 0.08)
try: mat_cabin_glass.blend_method='BLEND'
except: pass
mat_hub = new_mat("Hub", (1,1,1,1), emission_color=(1,1,1,1), emission_strength=7.5)
mat_ground = new_mat("Ground", (0.08,0.10,0.14,1), 0.0, 0.82)
mat_road = new_mat("Road", (0.11,0.13,0.18,1), 0.12, 0.48)
mat_line = new_mat("Line", (1,0.96,0.62,1), emission_color=(1,0.81,0.18,1), emission_strength=2.0)
mat_concrete = new_mat("Concrete", (0.84,0.84,0.82,1), 0.0, 0.85)

# --- Ground ---
bpy.ops.mesh.primitive_plane_add(size=520, location=(0,0,0))
g=bpy.context.active_object; g.name="Ground"; g.data.materials.append(mat_ground)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0.02))
road=bpy.context.active_object; road.name="Avenue"; road.scale=(300,24,1); road.data.materials.append(mat_road)
for i in range(-138, 142, 12):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(i,0,0.04))
    lm=bpy.context.active_object; lm.name=f"Mark_{i}"; lm.scale=(5.4,0.42,1); lm.data.materials.append(mat_line)
for side in (-1,1):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, side*15, 0.03))
    sw=bpy.context.active_object; sw.name=f"Sidewalk_{side}"; sw.scale=(300,5.0,1); sw.data.materials.append(mat_concrete)

# --- Curved podium: use cylinder segment for true curve ---
def build_curved_podium(cx, cy, w=26, d=18, h=5.8):
    # approximate curve with scaled cylinder (half)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=h, location=(cx, cy- d*0.35, h/2))
    pod=bpy.context.active_object; pod.name="CurvedPodium_Base"
    pod.scale=(w*0.52, d*0.55, 1)
    pod.data.materials.append(mat_podium)
    # flatten bottom
    # add bevel
    bevel(pod,0.35,3)
    return pod

# We'll keep per-tower podium but with curved front via boolean-like shape: use cube + cylinder for curve
def build_tower_v3(name, cx, cy, h_total=48):
    col=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)

    # Podium: flat top + curved front bulge
    # Base slab
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, 2.9))
    slab=bpy.context.active_object; slab.name=f"{name}_Slab"; slab.scale=(26, 18, 5.8)
    slab.data.materials.append(mat_podium); bevel(slab,0.38,3)
    col.objects.link(slab); bpy.context.scene.collection.objects.unlink(slab)
    # Curved front bulge (half cylinder along X)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=6.2, depth=26, location=(cx, cy+9.8, 2.9))
    bulge=bpy.context.active_object; bulge.name=f"{name}_Bulge"; bulge.rotation_euler=(0, math.radians(90), 0)
    # Actually cylinder axis Z, we want bulge facing +Y: rotate 90 around X then half
    bulge.rotation_euler=(math.radians(90), 0, 0)
    bulge.scale=(1,0.45,1)
    bulge.data.materials.append(mat_podium)
    col.objects.link(bulge); bpy.context.scene.collection.objects.unlink(bulge)
    # Horizontal metal band (thinner, sharper)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, 5.9))
    band=bpy.context.active_object; band.name=f"{name}_Band"; band.scale=(27,19,0.55)
    band.data.materials.append(mat_band)
    col.objects.link(band); bpy.context.scene.collection.objects.unlink(band)
    # Entrance canopy
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy+10.2, 3.6))
    can=bpy.context.active_object; can.name=f"{name}_Canopy"; can.scale=(12,5.2,0.62)
    can.data.materials.append(mat_concrete); bevel(can,0.10,2)
    col.objects.link(can); bpy.context.scene.collection.objects.unlink(can)
    for sx in (-4.0, 0, 4.0):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.34, depth=3.2, location=(cx+sx, cy+12.4, 1.7))
        pil=bpy.context.active_object; pil.name=f"{name}_Pillar_{sx}"; pil.data.materials.append(mat_podium)
        col.objects.link(pil); bpy.context.scene.collection.objects.unlink(pil)

    # Tower massing - keep stepped but with narrower top steps
    levels=[(12.0, h_total*0.56), (9.2, h_total*0.28), (6.8, h_total*0.18)]
    z=6.1
    for idx,(w,h) in enumerate(levels):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, z+h/2))
        blk=bpy.context.active_object; blk.name=f"{name}_Blk_{idx}"; blk.scale=(w,w,h)
        blk.data.materials.append(mat_wall if idx==0 else mat_gold); bevel(blk,0.24,3)
        col.objects.link(blk); bpy.context.scene.collection.objects.unlink(blk)
        if idx==0:
            # Dense fins: 11 on front, 7 on each side return
            for f in range(11):
                fx=cx + (f-5)*1.02
                bpy.ops.mesh.primitive_cube_add(size=1, location=(fx, cy+ w/2+0.08, z+h/2))
                fin=bpy.context.active_object; fin.name=f"{name}_FinF_{f}"; fin.scale=(0.22,0.48,h*0.93)
                fin.data.materials.append(mat_fin)
                col.objects.link(fin); bpy.context.scene.collection.objects.unlink(fin)
            # vertical reveals between bays (deep shadow)
            for bay in range(5):
                bx=cx + (bay-2)*2.38
                bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, cy+ w/2+0.04, z+h/2))
                rev=bpy.context.active_object; rev.name=f"{name}_Reveal_{bay}"; rev.scale=(0.10,0.22,h*0.94)
                rev.data.materials.append(mat_fin_dark)
                col.objects.link(rev); bpy.context.scene.collection.objects.unlink(rev)
            # Window bays: 10 floors x 4 bays, recessed + mullions
            import random as _r
            floors=10
            for fy in range(floors):
                wz=z+2.2+fy*2.45
                # horizontal spandrel
                bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy+ w/2+0.02, wz+1.05))
                span=bpy.context.active_object; span.name=f"{name}_Span_{fy}"; span.scale=(w-0.9,0.14,0.12)
                span.data.materials.append(mat_podium)
                col.objects.link(span); bpy.context.scene.collection.objects.unlink(span)
                for bay in range(4):
                    bx=cx + (bay-1.5)*2.38
                    # recessed glass plane
                    bpy.ops.mesh.primitive_plane_add(size=1, location=(bx, cy+ w/2+0.10, wz))
                    pane=bpy.context.active_object; pane.name=f"{name}_Pane_{fy}_{bay}"; pane.scale=(1.92,1,1.42)
                    pane.rotation_euler=(math.radians(90),0,0)
                    # random dark windows ~20%
                    pane.data.materials.append(mat_glass if _r.random()>0.20 else mat_glass_dark)
                    col.objects.link(pane); bpy.context.scene.collection.objects.unlink(pane)
                    # vertical mullion between panes
                    if bay<3:
                        mx=bx+1.19
                        bpy.ops.mesh.primitive_cube_add(size=1, location=(mx, cy+ w/2+0.06, wz))
                        vm=bpy.context.active_object; vm.name=f"{name}_VMull_{fy}_{bay}"; vm.scale=(0.10,0.10,1.45)
                        vm.data.materials.append(mat_fin)
                        col.objects.link(vm); bpy.context.scene.collection.objects.unlink(vm)
        z+=h
    # Crown: 4 steps + spire
    cz=z
    for k in range(4):
        s=6.0 - k*1.05
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz+0.42))
        cr=bpy.context.active_object; cr.name=f"{name}_Crown_{k}"; cr.scale=(s,s,0.84)
        cr.data.materials.append(mat_gold); bevel(cr,0.14,2)
        col.objects.link(cr); bpy.context.scene.collection.objects.unlink(cr)
        cz+=0.92
    bpy.ops.mesh.primitive_cone_add(radius1=0.95, radius2=0.08, depth=3.4, location=(cx, cy, cz+1.45))
    sp=bpy.context.active_object; sp.name=f"{name}_Spire"; sp.data.materials.append(mat_fin)
    col.objects.link(sp); bpy.context.scene.collection.objects.unlink(sp)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.52, location=(cx, cy, cz+3.25))
    tip=bpy.context.active_object; tip.name=f"{name}_Tip"; tip.data.materials.append(mat_hub)
    col.objects.link(tip); bpy.context.scene.collection.objects.unlink(tip)
    return col

tA=build_tower_v3("TowerA", -11.6, -4.0, 48)
tB=build_tower_v3("TowerB", 11.6, -4.0, 45)

# Bridge
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -4.0, 24.8))
br=bpy.context.active_object; br.name="SkyBridge"; br.scale=(25.5,3.6,1.18); br.data.materials.append(mat_fin); bevel(br,0.14,2)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -4.0, 25.25))
bg=bpy.context.active_object; bg.name="BridgeGlass"; bg.scale=(23.5,2.2,0.24); bg.data.materials.append(mat_glass)

# --- Figure-8 lattice ---
center=(0, -4.0, 27.8)
R=11.8
def make_ring(name, ctr, tilt_x, tilt_y, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.52, major_segments=96, minor_segments=24, location=ctr)
    r=bpy.context.active_object; r.name=name; r.rotation_euler=(math.radians(tilt_x), math.radians(tilt_y), 0)
    r.data.materials.append(mat)
    wf=r.modifiers.new(name="Wire", type='WIREFRAME'); wf.thickness=0.062; wf.use_replace=False; wf.material_offset=1
    if len(r.data.materials)<2: r.data.materials.append(mat_truss)
    else: r.data.materials[1]=mat_truss
    return r

rA=make_ring("RingA_Gold", (center[0], center[1], center[2]+7.6), 5, 8, mat_ring_gold)
rB=make_ring("RingB_Blue", (center[0], center[1], center[2]-7.6), -5, -8, mat_ring_blue)

# 18 spokes per ring for denser lattice look (closer to hero)
for ring_ctr, tilt, prefix in [((center[0],center[1],center[2]+7.6),(5,8),"SpokeA"), ((center[0],center[1],center[2]-7.6),(-5,-8),"SpokeB")]:
    for i in range(18):
        ang=(i/18)*math.pi*2
        x=math.cos(ang)*R; y=math.sin(ang)*R
        sx=ring_ctr[0]+x*0.5; sy=ring_ctr[1]+y*0.10; sz=ring_ctr[2]+y*0.5
        bpy.ops.mesh.primitive_cylinder_add(radius=0.058, depth=R, location=(sx, sy, sz))
        sp=bpy.context.active_object; sp.name=f"{prefix}_{i:02d}"
        sp.rotation_euler=(math.radians(90),0,ang)
        sp.data.materials.append(mat_truss)

# 17 cabins total (Golden Reel spec) -> 9+8
def cabin(name, x,y,z):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.62, location=(x,y,z))
    c=bpy.context.active_object; c.name=name; c.scale=(1,0.70,1.40)
    c.data.materials.append(mat_cabin)
    # glass strip
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y+0.20, z+0.15))
    win=bpy.context.active_object; win.name=name+"_Win"; win.scale=(0.96,0.14,0.62)
    win.data.materials.append(mat_cabin_glass)
    return c

for i in range(9):
    ang=(i/9)*math.pi*2; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin(f"CabinA_{i:02d}", center[0]+x*0.985, center[1]+y*0.10, center[2]+7.6+y)
for i in range(8):
    ang=(i/8)*math.pi*2 + math.pi/8; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin(f"CabinB_{i:02d}", center[0]+x*0.985, center[1]+y*0.10, center[2]-7.6+y)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.95, location=center)
hub=bpy.context.active_object; hub.name="Hub"; hub.data.materials.append(mat_hub)
for cx in (-11.6, 11.6):
    ld=bpy.data.lights.new(name=f"TopLight_{cx}", type='POINT'); ld.energy=1600; ld.color=(1,0.89,0.62)
    lo=bpy.data.objects.new(name=f"TopLightObj_{cx}", object_data=ld); lo.location=(cx, -4.0, 47); bpy.context.collection.objects.link(lo)
ld=bpy.data.lights.new(name="HubLight", type='POINT'); ld.energy=2400; ld.color=(1,1,1)
lo=bpy.data.objects.new(name="HubLightObj", object_data=ld); lo.location=center; bpy.context.collection.objects.link(lo)

cam_data=bpy.data.cameras.new(name="PreviewCam"); cam_obj=bpy.data.objects.new(name="PreviewCamObj", object_data=cam_data)
cam_obj.location=(44, -42, 31)
from mathutils import Vector
direction=Vector(center)-cam_obj.location; cam_obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
bpy.context.scene.collection.objects.link(cam_obj); bpy.context.scene.camera=cam_obj

out_dir="/Users/whypuss/.hermes/profiles/puss_profile/cache/scratch/macau-3d-city/exports"
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir,"studio-v3.blend"))
glb=os.path.join(out_dir,"studio-v3.glb")
try:
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_texcoords=True, export_normals=True, export_materials='EXPORT')
    print(f"GLB v3 exported: {glb} size={os.path.getsize(glb)}")
except Exception as e:
    import traceback; traceback.print_exc()
print(f"Objects v3: {len(bpy.data.objects)}")
print("DONE V3")
