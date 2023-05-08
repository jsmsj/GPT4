from flask import Flask,render_template,request,session,redirect,Response,jsonify
import _theb as theb
import _forefront as ff
import json
from typing import Any
from datetime import datetime,timedelta


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

def get_time():
    return round(datetime.now().timestamp())


def datetime_to_relative(time):
    x = str(timedelta(seconds=round(datetime.now().timestamp()-time))).split(':')
    return  x[0]+ ' hours, ' +  x[1] + ' minutes ago' 

@app.route('/')
def home():

    return render_template('home.html')

@app.route('/gpt4')
def gpt4page():
    with open('db.json') as f:
        db = json.load(f)
    
    accs = db['accounts']

    final = []

    for i,v in enumerate(accs):
        #pos,last_used_relative_time,
        final.append(
            (i+1,datetime_to_relative(v['last_timestamp']))
        )

    return render_template('gpt4page.html',acc = final)

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
        # print(gpt3Comp.last_msg_id)

    
    return app.response_class(stream_resp(),mimetype='text/event-stream')

@app.route('/converse/gpt4',methods=['POST'])
def gpt4():
    x = request.get_data().decode('utf-8')
    data = json.loads(x)
    print(data)
    # data = request.get_json()
    prompt = data['prompt']
    make_new = data['make_new']
    try:
        account_num_to_use = int(data['account_num'])
    except ValueError:
        def x():
                yield 'Account number must be an integer ....'

        return app.response_class(x(),mimetype='text/event-stream')

    with open('db.json') as f:
        db = json.load(f)

    if len(db['accounts']) == 0:
        email = ff.Email()
        res:Any = email.CreateAccount()
        db['accounts'].append({'client':res.client,'sessionID':res.sessionID,'last_timestamp':0})
        with open('db.json','w') as f:
            f.write(json.dumps(db,indent=4))
        
        redirect('/gpt4')
    
    if make_new:
        try:
            print('MAKING A ACCOUNT')
            email = ff.Email()
            res:Any = email.CreateAccount()
            db['accounts'].append({'client':res.client,'sessionID':res.sessionID,'last_timestamp':0})

            with open('db.json','w') as f:
                f.write(json.dumps(db,indent=4))

            def x():
                yield 'Successfully created account!\nRefresh to see it in accounts section'

            return app.response_class(x(),mimetype='text/event-stream')
        except Exception as e:
            print(e)
            def x():
                yield 'Unable to create account, retrying might help'

            return app.response_class(x(),mimetype='text/event-stream')


    with open('db.json') as f:
        db = json.load(f)

    if account_num_to_use > len(db['accounts']):
        def x():
                yield f'Account out of range!!!. Max account number = {len(db["accounts"])}'

        return app.response_class(x(),mimetype='text/event-stream')

    res:Any = db['accounts'][account_num_to_use-1]
    print(res)
    client = res['client']
    sessionID = res['sessionID']
    # try:
    forefront = ff.Model(sessionID=sessionID, client=client, model="gpt-4",conversationID=db['accounts'][account_num_to_use-1].get('convo_id',None))
    forefront.SetupConversation(prompt)
    # except Exception as e:
    #     print(e)
    #     def err():
    #         content_sent=False
    #         yield f'ENDENDENDENDENDREASONREASONABRAKA {content_sent}'

    #     return app.response_class(err(),mimetype='text/event-stream')

    def stream_resp():
        content_sent = False
        # print(2)
        for r in forefront.SendConversation():
            # print(r)
            content_sent = True
            yield r.choices[0].delta.content.encode()

        yield f'ENDENDENDENDENDREASONREASONABRAKA {content_sent}'

    db['accounts'][account_num_to_use-1].update({'last_timestamp':get_time()})
    db['accounts'][account_num_to_use-1].update({'convo_id':forefront.CONVERSATION_ID})
    with open('db.json','w') as f:
        f.write(json.dumps(db,indent=4))
    return app.response_class(stream_resp(),mimetype='text/event-stream')

if __name__ =='__main__':
    app.run(port=5000,debug=True) 