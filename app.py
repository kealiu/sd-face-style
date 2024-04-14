import os

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import gradio as gr
import json
# our comfy
import comfy

#
# create a FastAPI app
#
app = FastAPI()
ws = comfy.init_ws()

# create a static directory to store the static files
static_dir = Path('./static')
static_dir.mkdir(parents=True, exist_ok=True)

# mount FastAPI StaticFiles server
app.mount("/static", StaticFiles(directory=static_dir), name="static")

loras = {}
with open('static/lora.json') as f:
    loras = json.load(f)

#
# Gradio code
#

def get_lora(style):
    for st in loras:
        if style == st['name']:
            return st
    return None

def gallery_select(evt: gr.SelectData):
    if evt.selected:
        return evt.value['caption']
    else:
        return None

def get_new_image(face_image, style, prompt):
    comfy.fake_upload_image(face_image)
    return comfy.gen_image(ws, os.path.basename(face_image), get_lora(style), prompt)

with gr.Blocks() as demo:
    with gr.Row():
        gallery = gr.Gallery([(l['sample'], l['name']) for l in loras], columns=5, label="Choose A Style")

    with gr.Row():
        with gr.Column():
            face_image = gr.Image(type="filepath", label="Face Image")
            style = gr.Radio([l['name'] for l in loras], label="Choose Style", visible=False)
            prompt = gr.Textbox(label="Prompt", placeholder="1个女孩，屋顶或阳台，动态构图，优雅的姿势")
        with gr.Column():
            gen_image = gr.Image(label="Generated Image", interactive=False)

    gallery.select(gallery_select, None, style)

    btn = gr.Button("Go Generate!")
    btn.click(get_new_image, inputs=[face_image, style, prompt], outputs=[gen_image])

#
# main related mount Gradio app to FastAPI app
#
app = gr.mount_gradio_app(app, demo, path="/")

# serve the app
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=61080)

# `python app.py` or `uvicorn "app:app" --host "127.0.0.1" --port 61080 --reload`