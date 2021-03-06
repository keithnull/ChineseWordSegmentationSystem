from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, abort
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_script import Manager
from wtforms import SubmitField, StringField, TextField, RadioField, FileField, TextAreaField
from wtforms.validators import Required, Optional, DataRequired
import sys
sys.path.append("../")
from Segmentation import init, cut_into_sentence, segment_for_sentence, segment_for_text
from re import sub
app = Flask(__name__)
app.config["SECRET_KEY"] = "The beacon."

bootstrap = Bootstrap(app)
manage = Manager(app)


class TextForm(FlaskForm):
    raw_text = TextAreaField("Please input the raw text here.", validators=[Required(), ])
    mode = RadioField("Please select the mode.",
                      choices=(("0", "Cut into sentences first"), ("1", "Segment directly")),
                      validators=[DataRequired()]
                      )
    submit = SubmitField("Segment")


class FileForm(FlaskForm):
    file = FileField("Please upload your file.", validators=[Required()])
    mode = RadioField("Please select the mode.",
                      choices=(("0", "Cut into sentences first"), ("1", "Segment directly")),
                      validators=[DataRequired()]
                      )
    submit = SubmitField("Segment")


class ResultForm(FlaskForm):
    result_text = TextAreaField()


class SettingsForm(FlaskForm):
    settings = TextAreaField()
    submit = SubmitField("Modify")


def segment(text):
    global user_settings
    rules = dict()
    result = segment_for_text(text, mode="sentence")
    try:
        rules = {from_: to for from_, to in [(a.split("》》")[0], a.split('》》')[1])for a in user_settings.split('\n')]}
    except:
        flash("There're some errors in the user settings! So the settings are ignored.")
    # print(rules)
    for key in rules.keys():
        result = sub(r"[\s]*".join(key), rules[key], result)
    return result


@app.route("/download", methods=["GET"])
def download():
    global result_text
    try:
        response = make_response(result_text)
    except:
        abort(404)
    response.headers["Content-Disposition"] = "attachment; filename=result.utf8;"
    return response


@app.route("/sentence", methods=["GET", "POST"])
def sentence():
    global raw_text
    # print(raw_text)
    try:
        sentences = cut_into_sentence(raw_text)
    except:
        abort(404)
    # print(sentences)
    num = len(sentences)
    if num > 50:
        flash("Too many sentences to display. Only display the first 50 sentences.")
        num = 50
    result_sentences = [segment_for_sentence(sentences[i]) for i in range(num)]
    return render_template("sentence.html", sentences=sentences[0:num], result_sentences=result_sentences, num=num)


@app.route("/", methods=["GET", "POST"])
def index():
    by_file = request.args.get('by_file', False, type=bool)
    input_form = FileForm() if by_file else TextForm()
    result_form = ResultForm()
    download = False
    if input_form.validate_on_submit():
        mode = input_form.mode.data
        #print(mode, type(mode))
        global raw_text
        global result_text
        raw_text = ""
        if isinstance(input_form, TextForm):
            raw_text = input_form.raw_text.data
        else:
            try:
                raw_text = input_form.file.data.read().decode("utf-8")
            except:
                flash("Failed to decode the file! Make sure that it's encoded in UTF-8.")
                raw_text = "出错啦！请检查输入文件编码格式！"
        #print("raw_text", raw_text)
        if mode == "0":
            return redirect(url_for("sentence"))
        result_text = segment(raw_text)
        result_form.result_text.data = result_text
        download = True
    else:
        try:
            if input_form.raw_text.data:
                flash("Please select whether to cut into sentences first!")
        except:
            pass
        try:
            if input_form.file.data:
                flash("Please select whether to cut into sentences first!")
        except:
            pass
    return render_template("index.html", by_file=by_file, input_form=input_form, result_form=result_form, download=download)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    settings_form = SettingsForm()
    new_settings = settings_form.settings.data
    global user_settings
    if new_settings is not None and user_settings != new_settings.strip():
        flash("You have modified the settings successfully.")
        user_settings = new_settings.strip()
    settings_form.settings.data = user_settings
    return render_template("settings.html", settings_form=settings_form)


@app.route("/copyright", methods=["GET", "POST"])
def copyright():
    return render_template("copyright.html")


@app.route("/help", methods=["GET", "POST"])
def help():
    return render_template("help.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    if not init(folder="../Result/MM/MM_TrainingResult/"):
        exit()
    global user_settings
    user_settings = "生生灯火》》生生  灯火\n明暗无辄》》明暗  无辄"
    manage.run()
