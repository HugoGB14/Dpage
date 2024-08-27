from flask import Flask, Response, render_template, request
import requests
import os

app = Flask(__name__)
APIPORT = 55
APIHOST = os.getenv('API_HOST', 'localhost')
TARGET_SERVER_URL = f'http://{APIHOST}:{APIPORT}'

@app.route('/api/<path:path>', methods=['GET', 'POST', 'DELETE'])
def APIproxy(path):
    # Construye la URL completa del servidor de destino
    url = f'{TARGET_SERVER_URL}/{path}'

    # Copia los encabezados, excepto el Content-Type si es una solicitud POST con archivos
    headers = {key: value for key, value in request.headers.items() if key.lower() != 'content-type'}

    if request.method == 'GET':
        resp = requests.get(url, headers=headers, params=request.args)
    elif request.method == 'POST':
        if 'multipart/form-data' in request.content_type:
            # Transfiere archivos y datos del formulario
            files = {key: (file.filename, file.stream, file.content_type) for key, file in request.files.items()}
            data = request.form.to_dict()
            resp = requests.post(url, headers=headers, files=files, data=data)
        elif request.content_type == 'application/x-www-form-urlencoded':
            resp = requests.post(url, headers=headers, data=request.form)
        else:
            resp = requests.post(url, headers=headers, json=request.json)
    elif request.method == 'DELETE':
        resp = requests.delete(url, headers=headers, params=request.args)
    
    # Crea una respuesta con los datos del servidor de destino
    return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))


@app.route('/')
def home():
    route = request.args.get('path', '.')
    fileList = requests.get(f'http://localhost:{APIPORT}/list?route={route}').json().get('items')
    newFileList = []
    for file in fileList:
        
        print(file)
        if file.get('type') == 'file':
            newFileList.append(requests.get(f'http://localhost:{APIPORT}/file/details?route={route}&filename={file.get("name")}').json())
        elif file.get('type') == 'directory':
            newFileList.append(requests.get(f'http://localhost:{APIPORT}/directory/details?route={os.path.join(route, file.get("name"))}').json())
        else:
            newFileList.append(file)
            
    print(newFileList)
            
    return render_template('index.html', files=newFileList, os=os, curDir=route)

if __name__ == '__main__':
    app.run(debug=False, port=80, host='0.0.0.0')