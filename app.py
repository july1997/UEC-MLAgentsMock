import os
import subprocess
import sys
import random
import string
import shutil
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from pyngrok import ngrok

UPLOAD_FOLDER = './results/'
ALLOWED_EXTENSIONS = {'nn'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits)
               for i in range(n)]
    return ''.join(randlst)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            #filename = secure_filename(file.filename)
            filename = randomname(10)
            #ファイル作成
            os.makedirs(app.config['UPLOAD_FOLDER'] + filename + '/', exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + filename + "/", "SelfPlayEx.nn"))
            return redirect(url_for('judge_file', name=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/judge/<string:name>', methods=['GET'])
def judge_file(name):

    res = subprocess.run([
        "mlagents-learn",
        "./config/SelfPlayEx.yaml",
        "--run-id={}".format(name),
        "--force",
        "--env=application/Judge.app",
        "--inference",
        "--no-graphics",
    ], stdout=subprocess.PIPE)
    sys.stdout.buffer.write(res.stdout)
    
    with open(app.config['UPLOAD_FOLDER'] + name + "/run_logs/Player-0.log") as f:
        lines = f.readlines()
    l_X = [line for line in lines if 'Winner Agent A' in line]

    # フォルダ削除
    shutil.rmtree(app.config['UPLOAD_FOLDER'] + name + '/')

    if(len(l_X) != 0):
        return '''
        <!doctype html>
        <title>Upload File Name</title>
        <h1>You Loose!</h1>
        '''
    else:
        return '''
        <!doctype html>
        <title>Upload File Name</title>
        <h1>You Win!</h1>
        '''


if __name__ == "__main__":
    http_tunnel = ngrok.connect(5000, "http")
    print(http_tunnel)
    app.run(debug=True)
