import os
import requests
import datetime

from flask import Flask, jsonify, render_template, request,session,flash,redirect
from flask_socketio import SocketIO, emit
from flask_session import Session
from flask_socketio import join_room, leave_room
from decorators import signin_required

app = Flask(__name__,static_url_path='/static')
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



channels=[]
messages={}

active_users = []
channel_users = {}
private_messages={}

channels.append("CS50 web")
now = datetime.datetime.now()
time = now.strftime("%b %d %Y %H hrs %M min")
messages.setdefault("CS50 web", []).append(["",f"{time}","Group created"])



@app.route("/",methods=["GET"])
@signin_required
def index():
    if session.get('currentchannel') :
        if session.get('username') not in active_users:
            active_users.append(session.get('username'))
        if session.get('username') not in channel_users.setdefault(session.get('currentchannel'), []):
            channel_users.setdefault(session.get('currentchannel'), []).append(session.get('username'))
        msgs = messages.setdefault(session.get('currentchannel'), [])

        return render_template("index.html",channels = channels,users = active_users,msgs=msgs,channel_users=channel_users.setdefault(session.get('currentchannel'), []))
    else :
        return render_template("index.html",channels = channels,users = active_users)

@app.route("/signin",methods=["POST","GET"])
def signin():

    if request.method =='POST':
        username = request.form.get("username")
        if not username :
            flash("error","please enter a username!")
            return redirect("/signin")
        else :
            for user in active_users:
                if username == user:
                    flash("error","The username already exists")
                    return redirect("/signin")


            session["username"] = username
            active_users.append(username)
            session.permanent = True
            return redirect("/")
    else:
        return render_template("signin.html")

@socketio.on("user joined")
def join(data):
    emit("announce user connected",{'username':data["username"]},broadcast=True)

@socketio.on('new channel')
def makenewchannel(data):
    channelname = data["channelname"]
    for channel in channels:
        if channelname == channel:
            flash("error","The channel already exists")
            return redirect("/")

    channels.append(channelname)
    now = datetime.datetime.now()
    time = now.strftime("%b %d %Y %H hrs %M mins")
    messages.setdefault(channelname, []).append(["",f"{time}","Group created"])
    channel_users.setdefault(channelname, []).append(f"Author:{session.get('username')}")
    emit('announce channel created',{'channel':channelname},broadcast=True)

@socketio.on('new message')
def message(data):
    username = session.get('username')
    now = datetime.datetime.now()
    time = now.strftime("%b %d %Y %H hrs %M mins")
    room = data["channel"]
    if len(messages.setdefault(room, [])) >= 100 :
        messages.setdefault(room, []).pop
    messages.setdefault(room, []).append([f"{username}",f"{time}",f"{data['msg']}"])
    emit('new message',{'msg':data["msg"],'time':time,'username':username,'channel':room},broadcast=True)


@app.route('/channels/<channelname>',methods=['GET'])
def join_channel(channelname):
    for user in channel_users.setdefault(session.get('currentchannel'), []):
        if (user==session.get('username')):
            channel_users.setdefault(session.get("currentchannel"), []).remove(f"{user}")

    channel_users.setdefault(channelname, []).append(f"{session.get('username')}")
    session["currentchannel"] = channelname
    msgs = messages.setdefault(channelname,[])
    return render_template("index.html",channels = channels,users = active_users,msgs=msgs,channel_users=channel_users[channelname])


@app.route('/logout',methods=['GET'])
def logout():

    try :
        active_users.remove(session.get('username'))
    except ValueError:
        pass

    session.clear()

    return redirect("/")
