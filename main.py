import random as rd
from flask import Flask ,render_template ,redirect, url_for, session, jsonify , request

app = Flask(__name__)

titles = []
@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        title = request.form.get('title','')
        if title:
            titles.append({'Title_name':title})
        return redirect(url_for('index'))
    #title = request.args.get('name','') #'CodingByAmp'
    return  render_template('index.html',titles=titles)


@app.route('/delete',methods=['POST'])
def delete():
    if request.method == 'POST':
        item_index = request.form.get('itemid')
        print(item_index)
        # titles.remove(item_index)
        del titles[int(item_index)]
        return redirect(url_for('index'))
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(port=5000,host='127.0.0.1',debug=True)