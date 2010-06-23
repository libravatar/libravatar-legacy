import Image

def crop(image,x=None,y=None,w=None,h=None):
    try:
        img = Image.open(image)
    except:
        return
    if not x and y:
        x,y = 0,0
    if not w and h:
        w,h = img.getbbox()[2:3]
        i = min(w,h)
        w,h = i,i
    cropped = img.crop((x,y,x+w,y+h)) 
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
