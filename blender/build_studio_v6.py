
import bpy, math, os
from mathutils import Vector
from pathlib import Path

# Reuse V4 arc/plaza as base geometry (rebuild for texture workflow), add image projection
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'

REF = "/Users/whypuss/.hermes/profiles/puss_profile/cache/scratch/macau-3d-city/ref-hero1.jpg"

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

# Create photo-textured material using REF
def photo_mat(name, image_path, tint=(1,1,1,1)):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(500,0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location=(180,0)
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.location=(-220,0)
    coord = nt.nodes.new('ShaderNodeTexCoord'); coord.location=(-420,0)
    mapping = nt.nodes.new('ShaderNodeMapping'); mapping.location=(-320,0)
    # load image
    try:
        img = bpy.data.images.load(image_path, check_existing=True)
        img.colorspace_settings.name = 'sRGB'
        tex.image = img
        # Use UV by default, but we also wire Object/Generated for quick projection
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        # keep moderate roughness/metallic for photo wall
        if 'Roughness' in bsdf.inputs: bsdf.inputs['Roughness'].default_value = 0.72
        if 'Metallic' in bsdf.inputs: bsdf.inputs['Metallic'].default_value = 0.02
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    except Exception as e:
        print(f"photo_mat load failed {image_path}: {e}")
        # fallback solid
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

mat_photo = photo_mat("Photo_Tower", REF)

# Secondary mats tuned to hero palette
mat_fin = new_mat("Fin_Bronze", (0.74,0.64,0.48,1), 0.44, 0.34)
mat_fin_dark = new_mat("Fin_Dark", (0.36,0.32,0.28,1), 0.28, 0.55)
mat_glass = new_mat("Glass_Blue", (0.13,0.25,0.58,1), 0.0, 0.10)
mat_glass_dark = new_mat("Glass_Dark", (0.07,0.12,0.24,1), 0.0, 0.22)
try: mat_glass.blend_method='BLEND'; mat_glass_dark.blend_method='BLEND'
except: pass
mat_podium = new_mat("Podium", (0.89,0.87,0.83,1), 0.05, 0.58)
mat_band = new_mat("Band", (1,1,1,1), emission_color=(1,0.93,0.58,1), emission_strength=5.5)
mat_ring_gold = new_mat("Ring_Gold", (1,0.87,0.34,1), 0.60, 0.26, emission_color=(1,0.60,0.10,1), emission_strength=2.8)
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
mat_lawn = new_mat("Lawn", (0.18,0.42,0.18,1), 0.0, 0.82)
mat_gold_hero = new_mat("GoldHero", (1,0.88,0.32,1), 0.72, 0.22, emission_color=(1,0.72,0.18,1), emission_strength=3.2)

def bevel(o,w=0.14,seg=3):
    m=o.modifiers.new(name="Bevel",type='BEVEL'); m.width=w; m.segments=seg; m.limit_method='ANGLE'; m.angle_limit=math.radians(28)

# Ground
bpy.ops.mesh.primitive_plane_add(size=560, location=(0,0,0))
g=bpy.context.active_object; g.name="Ground"; g.data.materials.append(mat_ground)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,-22,0.02))
road=bpy.context.active_object; road.name="Avenue"; road.scale=(340,26,1); road.data.materials.append(mat_road)
for i in range(-158, 162, 12):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(i,-22,0.04))
    lm=bpy.context.active_object; lm.name=f"Mark_{i}"; lm.scale=(5.6,0.42,1); lm.data.materials.append(mat_line)
for side in (-1,1):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -22+side*15.5, 0.03))
    sw=bpy.context.active_object; sw.name=f"Sidewalk_{side}"; sw.scale=(340,5.2,1); sw.data.materials.append(mat_concrete)

# Arc towers (6 bays) with photo texture on south face
arc_center = Vector((0, 22, 0))
arc_R = 62.0
thetas = [-0.62, -0.46, -0.30, 0.30, 0.46, 0.62]
heights = [46, 52, 48, 48, 52, 46]
def point_on_arc(theta):
    return Vector((arc_R*math.sin(theta), arc_center.y - arc_R*math.cos(theta), 0))

# Create a reusable UV-projected photo tower helper
def build_tower_photo(name, pos2d, h_total):
    col=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)
    cx, cy = pos2d.x, pos2d.y
    # podium
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, 2.7))
    slab=bpy.context.active_object; slab.name=f"{name}_Slab"; slab.scale=(13.5,12.5,5.4)
    slab.data.materials.append(mat_podium); bevel(slab,0.32,3)
    col.objects.link(slab); bpy.context.scene.collection.objects.unlink(slab)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, 5.5))
    band=bpy.context.active_object; band.name=f"{name}_Band"; band.scale=(14,13,0.52)
    band.data.materials.append(mat_band)
    col.objects.link(band); bpy.context.scene.collection.objects.unlink(band)

    levels=[(10.2, h_total*0.55), (8.4, h_total*0.28), (6.2, h_total*0.19)]
    z=5.7
    for idx,(w,h) in enumerate(levels):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, z+h/2))
        blk=bpy.context.active_object; blk.name=f"{name}_Blk_{idx}"; blk.scale=(w,w,h)
        # South face uses photo texture, other faces keep cream/gold for fallback
        # We assign photo to slot 0, fins/windows overlay south face, so photo will peep through
        if idx==0:
            blk.data.materials.append(mat_photo)
        else:
            blk.data.materials.append(mat_photo)
        bevel(blk,0.22,3)
        col.objects.link(blk); bpy.context.scene.collection.objects.unlink(blk)
        if idx==0:
            # fins on south face (overlay, will partially cover photo for realism)
            for f in range(9):
                fx=cx + (f-4)*1.05
                bpy.ops.mesh.primitive_cube_add(size=1, location=(fx, cy+ w/2+0.10, z+h/2))
                fin=bpy.context.active_object; fin.name=f"{name}_FinF_{f}"; fin.scale=(0.18,0.42,h*0.93)
                fin.data.materials.append(mat_fin)
                col.objects.link(fin); bpy.context.scene.collection.objects.unlink(fin)
            # window bays with glass overlay (recessed, photo shows through behind)
            import random as _r
            for fy in range(9):
                wz=z+2.0+fy*2.50
                bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy+ w/2+0.02, wz+1.05))
                span=bpy.context.active_object; span.name=f"{name}_Span_{fy}"; span.scale=(10.2-0.8,0.12,0.10)
                span.data.materials.append(mat_podium)
                col.objects.link(span); bpy.context.scene.collection.objects.unlink(span)
                for bay in range(4):
                    bx=cx + (bay-1.5)*2.10
                    # glass plane slightly in front of photo wall
                    bpy.ops.mesh.primitive_plane_add(size=1, location=(bx, cy+ w/2+0.14, wz))
                    pane=bpy.context.active_object; pane.name=f"{name}_Pane_{fy}_{bay}"; pane.scale=(1.75,1,1.38)
                    pane.rotation_euler=(math.radians(90),0,0)
                    pane.data.materials.append(mat_glass if _r.random()>0.20 else mat_glass_dark)
                    col.objects.link(pane); bpy.context.scene.collection.objects.unlink(pane)
        z+=h
    cz=z
    for k in range(4):
        s=5.6 - k*1.0
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz+0.42))
        cr=bpy.context.active_object; cr.name=f"{name}_Crown_{k}"; cr.scale=(s,s,0.84)
        cr.data.materials.append(mat_podium)
        col.objects.link(cr); bpy.context.scene.collection.objects.unlink(cr)
        cz+=0.92
    bpy.ops.mesh.primitive_cone_add(radius1=0.88, radius2=0.08, depth=3.2, location=(cx, cy, cz+1.4))
    sp=bpy.context.active_object; sp.name=f"{name}_Spire"; sp.data.materials.append(mat_fin)
    col.objects.link(sp); bpy.context.scene.collection.objects.unlink(sp)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.48, location=(cx, cy, cz+3.1))
    tip=bpy.context.active_object; tip.name=f"{name}_Tip"; tip.data.materials.append(mat_hub)
    col.objects.link(tip); bpy.context.scene.collection.objects.unlink(tip)
    return col

for idx, th in enumerate(thetas):
    pos=point_on_arc(th)
    build_tower_photo(f"ArcTower_{idx}", pos, heights[idx])

# Plaza (same as V4)
plaza_center = Vector((0, -18, 0))
plaza_R = 38
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=plaza_R, depth=1.2, location=(plaza_center.x, plaza_center.y, 0.6))
plaza=bpy.context.active_object; plaza.name="Plaza_Base"; plaza.scale=(1,0.52,1); plaza.data.materials.append(mat_podium)
for r, h in [(32, 1.6), (24, 2.2), (14, 2.8)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=r, depth=0.35, location=(plaza_center.x, plaza_center.y, h))
    step=bpy.context.active_object; step.name=f"Plaza_Tier_{r}"; step.scale=(1,0.52,1); step.data.materials.append(mat_concrete)
for i in range(12):
    ang = (i/12)*math.pi + math.pi/2
    mx = plaza_center.x + math.cos(ang)*18
    my = plaza_center.y + math.sin(ang)*18*0.52
    bpy.ops.mesh.primitive_cube_add(size=1, location=(mx, my, 1.05))
    lawn=bpy.context.active_object; lawn.name=f"Lawn_{i}"; lawn.scale=(4.2,12,0.12)
    lawn.rotation_euler=(0,0,ang)
    lawn.data.materials.append(mat_lawn)
for i in range(24):
    ang = (i/24)*math.pi + math.pi/2
    cx = plaza_center.x + math.cos(ang)*plaza_R*0.92
    cy = plaza_center.y + math.sin(ang)*plaza_R*0.92*0.52
    bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=4.2, location=(cx, cy, 2.4))
    col=bpy.context.active_object; col.name=f"Colonnade_{i}"; col.data.materials.append(mat_podium)
for sx in (-12, 12):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(sx, plaza_center.y - 20, 3.2))
    gate=bpy.context.active_object; gate.name=f"Gateway_{sx}"; gate.scale=(5.5,2.2,5.2)
    gate.data.materials.append(mat_podium); bevel(gate,0.18,2)
    bpy.ops.mesh.primitive_cylinder_add(radius=2.4, depth=2.3, location=(sx, plaza_center.y - 20, 5.2))
    arch=bpy.context.active_object; arch.name=f"GatewayArch_{sx}"; arch.rotation_euler=(math.radians(90),0,0)
    arch.data.materials.append(mat_podium)

# Figure-8 hero wheel (reuse V5 wheel, slightly larger)
center_v=Vector((0, 0.8, 29.8))
center=(center_v.x, center_v.y, center_v.z)
R=14.6
def make_ring(name, ctr, tilt_x, tilt_y, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.72, major_segments=108, minor_segments=28, location=ctr)
    r=bpy.context.active_object; r.name=name; r.rotation_euler=(math.radians(tilt_x), math.radians(tilt_y), 0)
    r.data.materials.append(mat)
    wf=r.modifiers.new(name="Wire", type='WIREFRAME'); wf.thickness=0.070; wf.use_replace=False; wf.material_offset=1
    if len(r.data.materials)<2: r.data.materials.append(bpy.data.materials["Truss"])
    return r
rA=make_ring("RingA_Gold", (center_v.x, center_v.y, center_v.z+8.8), 3, 6, mat_gold_hero)
rB=make_ring("RingB_Blue", (center_v.x, center_v.y, center_v.z-8.8), -3, -6, mat_ring_gold)
for ctr in [(center_v.x, center_v.y, center_v.z+8.8), (center_v.x, center_v.y, center_v.z-8.8)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=R+0.22, minor_radius=0.18, major_segments=96, minor_segments=16, location=ctr)
    rim=bpy.context.active_object; rim.name=f"RimGlow_{ctr[2]:.0f}"
    rim.rotation_euler=(math.radians(3 if ctr[2]>center_v.z else -3), math.radians(6 if ctr[2]>center_v.z else -6), 0)
    rim.data.materials.append(new_mat(f"RimGlowMat_{ctr[2]:.0f}", (1,0.92,0.55,1), emission_color=(1,0.82,0.22,1), emission_strength=4.0))
for i in range(24):
    ang=(i/24)*math.pi*2
    x=math.cos(ang)*R*0.75; y=math.sin(ang)*R*0.75
    bpy.ops.mesh.primitive_cube_add(size=1, location=(center_v.x+x*0.5, center_v.y+y*0.08, center_v.z+y*0.44))
    ray=bpy.context.active_object; ray.name=f"Sunburst_{i}"; ray.scale=(0.10,0.10,R*0.68)
    ray.rotation_euler=(math.radians(90),0,ang)
    ray.data.materials.append(mat_fin)
for ring_ctr, tilt, prefix in [((center_v.x, center_v.y, center_v.z+8.8),(3,6),"SpokeA"), ((center_v.x, center_v.y, center_v.z-8.8),(-3,-6),"SpokeB")]:
    for i in range(18):
        ang=(i/18)*math.pi*2
        x=math.cos(ang)*R; y=math.sin(ang)*R
        sx=ring_ctr[0]+x*0.5; sy=ring_ctr[1]+y*0.08; sz=ring_ctr[2]+y*0.44
        bpy.ops.mesh.primitive_cylinder_add(radius=0.068, depth=R, location=(sx, sy, sz))
        sp=bpy.context.active_object; sp.name=f"{prefix}_{i:02d}"
        sp.rotation_euler=(math.radians(90),0,ang)
        sp.data.materials.append(bpy.data.materials["Truss"])
def cabin(name, x,y,z):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.78, location=(x,y,z))
    c=bpy.context.active_object; c.name=name; c.scale=(1,0.68,1.55)
    c.data.materials.append(mat_cabin)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y+0.24, z+0.20))
    win=bpy.context.active_object; win.name=name+"_Win"; win.scale=(1.10,0.14,0.72)
    win.data.materials.append(mat_cabin_glass)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z-0.42))
    fl=bpy.context.active_object; fl.name=name+"_Floor"; fl.scale=(0.92,0.72,1)
    fl.data.materials.append(mat_cabin_glass)
    return c
for i in range(9):
    ang=(i/9)*math.pi*2; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin(f"CabinA_{i:02d}", center_v.x+x*0.985, center_v.y+y*0.08, center_v.z+8.8+y)
for i in range(8):
    ang=(i/8)*math.pi*2 + math.pi/8; x=math.cos(ang)*R; y=math.sin(ang)*R
    cabin(f"CabinB_{i:02d}", center_v.x+x*0.985, center_v.y+y*0.08, center_v.z-8.8+y)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.05, location=center_v)
hub=bpy.context.active_object; hub.name="Hub"; hub.data.materials.append(mat_hub)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.8, 25.4))
br=bpy.context.active_object; br.name="SkyBridge"; br.scale=(38,2.8,0.85); br.data.materials.append(mat_fin)
for cx, cy in [(point_on_arc(th).x, point_on_arc(th).y) for th in thetas]:
    ld=bpy.data.lights.new(name=f"TopLight_{cx:.0f}", type='POINT'); ld.energy=1400; ld.color=(1,0.89,0.62)
    lo=bpy.data.objects.new(name=f"TopLightObj_{cx:.0f}", object_data=ld); lo.location=(cx, cy, 48); bpy.context.collection.objects.link(lo)
ld=bpy.data.lights.new(name="HubLight", type='POINT'); ld.energy=3200; ld.color=(1,1,1)
lo=bpy.data.objects.new(name="HubLightObj", object_data=ld); lo.location=center_v; bpy.context.collection.objects.link(lo)

cam_data=bpy.data.cameras.new(name="PreviewCam"); cam_obj=bpy.data.objects.new(name="PreviewCamObj", object_data=cam_data)
cam_obj.location=(52, -52, 34)
direction=center_v-cam_obj.location; cam_obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
bpy.context.scene.collection.objects.link(cam_obj); bpy.context.scene.camera=cam_obj

out_dir="/Users/whypuss/.hermes/profiles/puss_profile/cache/scratch/macau-3d-city/exports"
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir,"studio-v6.blend"))
glb=os.path.join(out_dir,"studio-v6.glb")
try:
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_texcoords=True, export_normals=True, export_materials='EXPORT')
    print(f"GLB v6 exported: {glb} size={os.path.getsize(glb)}")
except Exception as e:
    import traceback; traceback.print_exc()
print(f"Objects v6: {len(bpy.data.objects)}")
print("DONE V6")
