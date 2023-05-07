from flask import Flask,render_template,request,session,redirect,Response,jsonify
from app import _theb as theb
from app import _forefront as ff
import json
from typing import Any

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/gpt4')
def gpt4page():
    return render_template('gpt4page.html')

@app.route('/gpt3')
def gpt3page():

    return render_template('gpt3page.html')

@app.route('/converse/gpt3',methods=['POST'])
def gpt3():
    x = request.get_data().decode('utf-8')
    data = json.loads(x)
    # data = request.get_json()
    prompt = data['prompt']

    gpt3Comp = theb.Completion

    def stream_resp():
        for token in gpt3Comp.create(prompt):
            yield token
        print(gpt3Comp.last_msg_id)
    

    
    return app.response_class(stream_resp(),mimetype='text/event-stream')

@app.route('/converse/gpt4',methods=['POST'])
def gpt4():
    x = request.get_data().decode('utf-8')
    data = json.loads(x)
    # data = request.get_json()
    prompt = data['prompt']

    email = ff.Email()
    res:Any = email.CreateAccount()
    
    client = res.client
    sessionID = res.sessionID

    forefront = ff.Model(sessionID=sessionID, client=client, model="gpt-4")
    forefront.SetupConversation(prompt)

    def stream_resp():
        for r in forefront.SendConversation():
            yield r.choices[0].delta.content
    
    return app.response_class(stream_resp(),mimetype='text/event-stream')

    

