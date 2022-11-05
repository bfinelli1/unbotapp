from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
import requests, io, os, re, zipfile
from PIL import Image, ImageDraw, ImageFont
from django.utils.encoding import smart_str
from dotenv import load_dotenv
load_dotenv()

font_name="fonts/arial.ttf"
name_size=20
side_margin=40
top_margin=40
Red=150
Green=150
Blue=150


def index(request):
    return render(request, 'caption/index.html')

def upload(request):
    if request.method == 'POST':
        if request.POST.get("fileupload"):
            file = request.FILES['file']
            lines=""
            for line in file:
                try:
                    lines+=line.decode('utf8', 'strict')
                except:
                    return HttpResponseBadRequest('Not a text file or not utf-8 encoded. try using the text field below.')
            lines = lines.split('\n')
        elif request.POST.get("text"):
            lines = request.POST['text-body'].split('\n')

        try:
            num_images = request.POST['dropdown']
        except:
            num_images = 1
        try:
            search_term = request.POST['searchterm']
        except:
            search_term = "space"
        try:
            color = request.POST['color']
        except:
            color = "#949494"
        try:
            fontsize = int(request.POST['fontsize'])
            if fontsize > 100 or fontsize < 10:
                fontsize = 70
        except:
            fontsize = 70
        try:
            fonttype = request.POST['fonttype']
            fonttype = "fonts/"+fonttype
        except:
            fonttype = "fonts/arial.ttf"
        return process(lines, num_images, search_term, color, fontsize, fonttype)
    else:
        return HttpResponseBadRequest('Only POST requests are allowed')

def process(lines, num_images, search_term, color, fontsize, fonttype):
    images = []
    images_tuple = []
    count = 1
    r = requests.get(f'https://api.unsplash.com/photos/random?query={search_term}&count={num_images}',
    headers={'Authorization': f'Client-ID {os.getenv("Client-ID")}'})
    if not r:
        response = HttpResponseBadRequest(r.text)
        return response
    lenlines = len(lines)
    lineidx=0
    for entry in r.json():
        img_data = requests.get(entry['urls']['regular']).content

        #download_location
        download_loc = entry['links']['download_location']
        dreq = requests.get(download_loc, headers={'Authorization': f'Client-ID {os.getenv("Client-ID")}'})

        img = Image.open(io.BytesIO(img_data), mode='r')
        I1 = ImageDraw.Draw(img)
        myFont = ImageFont.truetype(font=fonttype, size=fontsize)

        offset=top_margin
        line = lines[lineidx]
        for line in wrapword(line, img.width-(side_margin*2), myFont):
            I1.text((side_margin,offset), line, color, font=myFont)
            offset+=myFont.getsize(line)[1]+10
        lineidx+=1
        if lineidx >= lenlines:
            lineidx=0
        name = entry['user']['name']
        
        desc=""
        if entry['alt_description'] is None:
            desc = search_term
        else:
            desc = entry['alt_description']
        name = re.sub(r'[^a-zA-Z -.]', '', name)
        myFont = ImageFont.truetype(font=font_name, size=name_size)
        I1.text((10,10), f"image by: {name}", (Red,Green,Blue), font=myFont)
        name = desc[:100] + " " + name
        if int(num_images) == 1:
            response = HttpResponse(content_type='application/force-download') 
            img.save(response, "JPEG")
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(f"{name[:120]}.jpg")
            return response
        else:
            images_tuple.append(
                (str(count) + " " + name + ".jpg", get_image_buffer(img))
            )
            count+=1

    # put images into a zip file
    full_zip_in_memory = generate_zip(images_tuple)
    response = HttpResponse(full_zip_in_memory, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(f'{search_term[:100]}Images.zip')
    return response

def get_image_buffer(image):
    img_buffer = io.BytesIO()
    image.save(img_buffer, 'JPEG')
    img_buffer.seek(0)
    return img_buffer

def generate_zip(list_of_tuples):
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in list_of_tuples:
            zf.writestr(f[0], f[1].read())
    return mem_zip.getvalue()

def wrapword(text, width, myFont):
    lines=['']
    for word in text.split():
        line = f'{lines[-1]} {word}'.strip()
        if myFont.getsize(line)[0] < width:
            lines[-1] = line
        elif myFont.getsize(word)[0] > width:
            return ""
        else:
            lines.append(word)
    return lines