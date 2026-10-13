import sys, numpy as np
from rembg import remove, new_session
from PIL import Image
from scipy import ndimage as ndi
src, dst, models = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
im = Image.open(src).convert("RGB")
# union of model masks (one model misses bright clothing, another misses hair)
a = np.zeros((im.height, im.width), np.float32)
for m in models:
    a = np.maximum(a, np.asarray(remove(im, session=new_session(m), only_mask=True), np.float32))
solid = a > 128
lab, n = ndi.label(solid)
if n:
    sizes = ndi.sum(solid, lab, range(1, n + 1))
    keep = 1 + int(np.argmax(sizes))
    main = lab == keep
    # drop disconnected scraps, fill enclosed holes (cap, shirt)
    if len(sys.argv) < 5: main = ndi.binary_fill_holes(ndi.binary_closing(main, iterations=6))
    a = np.where(main, np.maximum(a, 255 * ndi.binary_erosion(main, iterations=3)), 0)
alpha = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(1.2))
out = im.copy(); out.putalpha(alpha)
bb = alpha.point(lambda v: 255 if v > 20 else 0).getbbox()
out.crop(bb).save(dst); print(dst, out.crop(bb).size)
