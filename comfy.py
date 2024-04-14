import io
import os
import websocket # pip install websocket-client
import uuid
import json
import urllib.request
import urllib.parse
from requests_toolbelt import MultipartEncoder # pip install requests-toolbelt
from PIL import Image

# prompt
workflow = {}
with open('static/workflow.json') as f:
    workflow = json.load(f)

#
# Start of normal call
#
server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            continue #previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for o in history['outputs']:
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            images_output = []
            if 'images' in node_output:
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images

def init_ws():
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    return ws

def upload_image(input_path, name, image_type="input", overwrite=False):
  with open(input_path, 'rb') as file:
    multipart_data = MultipartEncoder(
      fields= {
        'image': (name, file, 'image/png'),
        'type': image_type,
        'overwrite': str(overwrite).lower()
      }
    )

    data = multipart_data
    headers = { 'Content-Type': multipart_data.content_type }
    request = urllib.request.Request("http://{}/upload/image".format(server_address), data=data, headers=headers)
    with urllib.request.urlopen(request) as response:
      return response.read()


# The directory of `ComfyUI/input`,` Tricks for quickly 'upload' image in case we are in the same host 
comfy_input="${HOME}/ComfyUI/input/"
# for just copy to target
def fake_upload_image(imgpath):
    os.system("mv %s %s"%(imgpath, comfy_input))

def gen_image(ws, face_image, lora, prompt):
    # lora model
    global workflow
    workflow['46']['inputs']['lora_name'] = lora['model']
    # negative prompt
    workflow['32']['inputs']['text'] = lora['negative']
    # added positive prompt
    workflow['42']['inputs']['text_b'] = lora['positive']
    # prompt, user input
    workflow['66']['inputs']['text'] = prompt
    # face image
    workflow['77']['inputs']['image'] = face_image
    #pprint.pprint(workflow)
    imgs = get_images(ws, workflow)
    outimg = None
    for node_id in imgs:
        for image_data in imgs[node_id]:
            outimg = Image.open(io.BytesIO(image_data))
    return outimg
