from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import io,zipfile,json,hashlib
src=Path('/mnt/data/rain_v4_source/Ten_Years_Of_Rain_Image_Pack.zip')
out=Path('/mnt/data/rain30/assets');out.mkdir(exist_ok=True,parents=True)
# Original plates, mask-defined independent architectural/foreground depth, exact original source pixels.
scenes={
 'street':('E03_', [
   [(.43,.00),(.85,.00),(.86,.20),(.77,.23),(.76,.49),(.58,.51),(.52,.72),(.42,.71)],
   [(.22,.07),(.39,.0),(.60,.0),(.54,.23),(.45,.29),(.30,.28),(.30,.75),(.19,.84)]],
   [[(0,0),(.31,0),(.24,.12),(.18,.38),(.12,.53),(.14,.87),(.0,.92)],
    [(.74,.45),(1,.45),(1,1),(.70,1),(.71,.75)]]),
 'atmos':('E04_', [[(.51,.52),(1,.50),(1,1),(.48,1)]],
    [[(0,0),(.34,0),(.29,.12),(.22,.12),(.14,.43),(.12,.75),(.35,1),(0,1)],[(0,.86),(1,.85),(1,1),(0,1)]]),
 'flood':('E23_', [[(0,0),(.30,0),(.27,.53),(.20,.81),(0,.91)],[(.66,0),(1,0),(1,.91),(.80,.84),(.75,.50)]],
   [[(0,.80),(.30,.75),(.52,.84),(.80,.78),(1,.80),(1,1),(0,1)]]),
 'cold':('E15_', [[(.13,.21),(.39,.17),(.42,.57),(.14,.62)],[(.61,.38),(.90,.35),(.94,.58),(.59,.64)]],
   [[(0,0),(.18,0),(.14,.48),(.11,.67),(.22,.93),(.34,1),(0,1)],[(0,.73),(.29,.73),(.52,.85),(1,.85),(1,1),(0,1)]]),
 'hunger':('E06_', [[(0,0),(.68,0),(.65,.74),(.34,.86),(0,.93)]],
   [[(.81,.20),(1,.16),(1,1),(.77,1),(.73,.76)],[(0,.82),(.50,.78),(.67,1),(0,1)]]),
 'tower':('E10_', [[(.07,0),(.43,0),(.43,.69),(.15,.77),(.11,.43)],[(.60,.07),(.83,.01),(.88,.64),(.62,.71)]],
   [[(0,.72),(.30,.70),(.43,.82),(.51,1),(0,1)],[(.74,.82),(1,.69),(1,1),(.70,1)]]),
 'rope':('E32_', [[(.07,0),(.43,0),(.43,.70),(.15,.78)],[(.60,0),(.82,0),(.85,.71),(.60,.75)]],
   [[(0,.81),(.31,.72),(.41,.88),(.47,1),(0,1)],[(.75,.86),(1,.75),(1,1),(.73,1)]]),
}
index=[]
with zipfile.ZipFile(src) as z:
 for key,(prefix,midpolys,frontpolys) in scenes.items():
  name=next(n for n in z.namelist() if n.startswith('scenes/'+prefix))
  im=Image.open(io.BytesIO(z.read(name))).convert('RGB')
  im.save(out/f'{key}_far.webp',quality=88,method=4)
  for label,polys in [('mid',midpolys),('front',frontpolys)]:
   m=Image.new('L',im.size,0);d=ImageDraw.Draw(m)
   for poly in polys:d.polygon([(round(x*im.width),round(y*im.height)) for x,y in poly],fill=255)
   m=m.filter(ImageFilter.GaussianBlur(5.0))
   rgba=im.convert('RGBA');rgba.putalpha(m)
   rgba.save(out/f'{key}_{label}.webp',quality=87,method=4)
  index.append({'name':key,'source':name,'size':im.size})
 # Isolated approved prop atlas elements, no new generation.
 def crop_sprite(prefix,rect,name):
  source=next(n for n in z.namelist() if n.startswith('props/'+prefix));im=Image.open(io.BytesIO(z.read(source))).convert('RGBA')
  # Region in normalized xy.
  box=(round(im.width*rect[0]),round(im.height*rect[1]),round(im.width*rect[2]),round(im.height*rect[3]));outim=im.crop(box)
  outim.save(out/name,quality=92,method=4)
  index.append({'name':name,'source':source,'crop_px':box})
 crop_sprite('P05_',(.013,.48,.981,.548),'rope_intact.webp')
 crop_sprite('P05_',(.013,.594,.982,.687),'rope_broken.webp')
 crop_sprite('P10_',(.0,.005,.35,.267),'knife.webp')
# Reuse unaltered previously prepared genuine independent depth source; same SHA in original GitHub branch.
with zipfile.ZipFile('/mnt/data/rain30/source/continuation_assets.zip','w',zipfile.ZIP_DEFLATED,compresslevel=4) as a:
 for p in sorted(out.glob('*.webp')):a.write(p,arcname=p.name)
(Path('/mnt/data/rain30/source/asset_manifest.json')).write_text(json.dumps({'origin_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'generation_model_calls':0,'assets':index},indent=2)+'\n')
print('asset bytes',sum(p.stat().st_size for p in out.glob('*.webp')),'count',len(list(out.glob('*.webp'))))
print('zip bytes',Path('/mnt/data/rain30/source/continuation_assets.zip').stat().st_size)
