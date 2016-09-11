from flask import Flask, render_template, request, url_for, redirect, g
import sqlite3
from wtforms import *


DATABASE = 'user.db'
app = Flask(__name__)


def setup_db():
    query_db('CREATE TABLE IF NOT EXISTS user (ID INTEGER PRIMARY KEY AUTOINCREMENT,story_title TEXT, user_story TEXT, acceptance_criteria TEXT, business_value INT, estimation REAL, status TEXT)')


# DB connector
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# The default query runner spiced up a little.This way it returns a dictionary
def query_db(query, args=(), one=False):
    db = get_db()
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    db.commit()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# if the app shuts down it closes the db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# the form creator class(I could not applied the validator functions thats
# why I placed them in the html code)
class MyForm(Form):
    title = TextField('Title')
    story = TextAreaField('Story')
    criteria = TextAreaField('Criteria')
    value = IntegerField('Business Value')
    estimation = FloatField('Estimation(h)')
    status = SelectField('Status', choices=[('Planning', 'Planning'), ('To Do', 'To Do'), (
        'In Progress', 'In Progress'), ('Review', 'Review'), ('Done', 'Done')])
    submit = SubmitField()


# root redirection to the list function
@app.route('/')
def start():
    return redirect(url_for('list'))

# as I told before...


@app.route('/list')
def list():
    rows = query_db("select * from user")
    return render_template('list.html', rows=rows)

# deletes entry based on it' id


@app.route('/list', methods=['POST'])
def delete_entry():
    data = request.form['_id']
    query_db("DELETE FROM user WHERE ID = {0}".format(data))
    return redirect(url_for('list'))


# new entry creation based on the form action
@app.route('/story', methods=['GET', 'POST'])
def register():
    form = MyForm(request.form, csrf_enabled=False)
    if request.method == 'POST':
        data = (form.title.data, form.story.data, form.criteria.data,
                form.value.data, form.estimation.data, form.status.data)
        query_db("INSERT INTO user (story_title,user_story,acceptance_criteria,business_value,estimation,status) VALUES (?,?,?,?,?,?)", (data))
        return redirect(url_for('list'))
    return render_template('form.html', form=form)


# reloads the form and populates with the corresponding data and updates
# the entry
@app.route('/story/<int:story_id>', methods=['GET', 'POST'])
def edit(story_id):
    id_to_edit = story_id
    if request.method == 'GET':
        rows = query_db("select * from user where ID = {0}".format(story_id))
        form = MyForm(request.form, csrf_enabled=False)
        for row in rows:
            form.title.data = row["story_title"]
            form.story.data = row["user_story"]
            form.criteria.data = row["acceptance_criteria"]
            form.value.data = row['business_value']
            form.estimation.data = row['estimation']
            form.status.data = row['status']
            form.submit.name = "EDIT"
            form.submit.id = id_to_edit
        return render_template('form.html', form=form)
    if request.method == 'POST':
        form = MyForm(request.form, csrf_enabled=False)
        data = [form.title.data, form.story.data, form.criteria.data,
                form.value.data, form.estimation.data, form.status.data, id_to_edit]
        query_db("UPDATE user SET story_title=?,user_story=?,acceptance_criteria=?,business_value=?,estimation=?,status=? WHERE ID=?", (data))
        return redirect(url_for('list'))


if __name__ == '__main__':
    app.run()


with app.app_context():
    setup_db()
