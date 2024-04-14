# demo app for 1 face phone generating

## deps

deps on `ComfyUI` running locally

## install
```
pip install -r requirements.txt
```

## usage

```
# directly run
python app.py 

# or by uvicorn 
uvicorn "app:app" --host "127.0.0.1" --port 61080 --reload
```
