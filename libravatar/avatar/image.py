import Image

def crop(image,x=0,y=0,w=0,h=0):
    try:
        img = Image.open(image)
    except:
        return
    junk,junk,a,b=img.getbbox()
    if w == 0 and h == 0:
        w,h = a,b
        i = min(w,h)
        w,h = i,i
    else:
        if w < 0 or x+w > a or h < 0 or y+h > b:
            raise ValueError("crop dimensions outside of original image bounding box")
    cropped = img.crop((x,y,x+w,y+h)) 
    cropped.load()
    cropped.save(image)

def resize(image,w=512,h=None):
    try:
        img = Image.open(image)
    except:
        return
    if not h:
        h=w
    img.resize((w,h))
    img.save(image)
