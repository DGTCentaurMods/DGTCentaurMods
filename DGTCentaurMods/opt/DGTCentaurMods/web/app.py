# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from flask import Flask, render_template, Response, request, redirect, send_file
from DGTCentaurMods.db import models
from DGTCentaurMods.display.ui_components import AssetManager
from chessboard import LiveBoard
import centaurflask
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import func
from sqlalchemy import select
from sqlalchemy import delete
import os
import time
import pathlib
import io
import chess
import chess.pgn
import json

app = Flask(__name__)
app.config['UCI_UPLOAD_EXTENSIONS'] = ['.txt']
app.config['UCI_UPLOAD_PATH'] = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/"

@app.before_request
def handle_preflight():
    # Override the OPTIONS response so that the webdav methods are available
    if request.method == "OPTIONS":
        res = Response()
        res.headers['Allow'] = 'OPTIONS, GET, HEAD, PROPFIND, DELETE, PUT, MOVE, MKCOL, LOCK, UNLOCK, PROPPATCH'
        res.headers['DAV'] = "1,2"
        return res

    # Override PROPFIND
    if request.method == "PROPFIND":                            
        res = Response()
        #if request.headers["Depth"] == 0:            
        thispath = request.path.replace("\n","")        
        if thispath != "/" and thispath[-1:] == "/":            
            thispath = thispath[:len(thispath)-1]        
        if request.path == "/":            
            response = '<?xml version=\"1.0\" encoding=\"utf-8\" ?><D:multistatus xmlns:D=\"DAV:\">\n'
            response = response + '<D:response>\n'
            response = response + '<D:href>/</D:href>\n'
            response = response + '<D:propstat>\n'
            response = response + '<D:prop>\n'
            response = response + '<D:getcontentlength>'
            response = response + '0'
            response = response + '</D:getcontentlength>\n'
            response = response + '<D:resourcetype>\n'
            response = response + '<D:collection/>\n'
            response = response + '</D:resourcetype>\n'
            response = response + '<D:creationdate>'
            response = response + time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(os.path.getctime("/home/pi")));            
            response = response + '</D:creationdate>\n'
            response = response + '<D:lastmodified>'
            response = response + time.strftime('%a, %d %b %Y %H:%M:%S %Z',time.localtime(os.path.getctime("/home/pi")));
            response = response + '</D:lastmodified>\m'
            response = response + '</D:prop>\n'
            response = response + '<D:status>HTTP/1.1 200 OK</D:status>\n'
            response = response + '</D:propstat>\n'
            response = response + '</D:response>\n'
            if int(request.headers["Depth"]) == 1:
                if os.path.isdir("/home/pi" + thispath):
                    for fn in os.listdir("/home/pi" + thispath):                    
                        response = response + "<D:response>\n"
                        response = response + '<D:href>' + thispath + fn + '</D:href>\n'
                        response = response + "<D:propstat>\n"
                        response = response + "<D:prop>\n"
                        if os.path.isfile("/home/pi" + thispath + fn):
                            response = response + "<D:getcontentlength>"
                            response = response + str(os.path.getsize("/home/pi" + thispath + fn))
                            response = response + "</D:getcontentlength>\n"
                        response = response + "<D:resourcetype>\n"
                        if os.path.isdir("/home/pi" + thispath + fn):
                            response = response + "<D:collection/>\n"
                        response = response + "</D:resourcetype>\n"
                        response = response + "<D:creationdate>"
                        response = response + time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(os.path.getctime("/home/pi" + thispath + fn)))
                        response = response + "</D:creationdate>\n"
                        response = response + "<D:lastmodified>"
                        response = response + time.strftime('%a, %d %b %Y %H:%M:%S %Z',time.localtime(os.path.getmtime("/home/pi" + thispath + fn)))
                        response = response + "</D:lastmodified>\n"
                        response = response + "</D:prop>\n"
                        response = response + "<D:status>HTTP/1.1 200 OK</D:status>\n"
                        response = response + "</D:propstat>\n"
                        response = response + "</D:response>\n"; 
                    # Now also here create a fake PNGs directory
                    response = response + "<D:response>\n"
                    response = response + '<D:href>' + "/PGNs" + '</D:href>\n'
                    response = response + "<D:propstat>\n"
                    response = response + "<D:prop>\n"                                       
                    response = response + "<D:resourcetype>\n"
                    response = response + "<D:collection/>\n"
                    response = response + "</D:resourcetype>\n"
                    response = response + "<D:creationdate>"
                    response = response + '2003-07-01T01:01:00Z'
                    response = response + "</D:creationdate>\n"
                    response = response + "<D:lastmodified>"
                    response = response + 'Thu, 21 Sep 2023 18:50:14 BST'
                    response = response + "</D:lastmodified>\n"
                    response = response + "</D:prop>\n"
                    response = response + "<D:status>HTTP/1.1 200 OK</D:status>\n"
                    response = response + "</D:propstat>\n"
                    response = response + "</D:response>\n"
            response = response + '</D:multistatus>\n'                       
            return Response(response, mimetype='application/xml', status=207)
        elif thispath == "/PGNs":
            # Return a list of PGN games
            response = '<?xml version=\"1.0\" encoding=\"utf-8\" ?><D:multistatus xmlns:D=\"DAV:\">\n'
            response = response + "<D:response>\n"
            response = response + '<D:href>' + "/PGNs" + '</D:href>\n'
            response = response + "<D:propstat>\n"
            response = response + "<D:prop>\n"                               
            response = response + "<D:resourcetype>\n"
            response = response + "<D:collection/>\n"
            response = response + "</D:resourcetype>\n"
            response = response + "<D:creationdate>"
            response = response + '2003-07-01T01:01:00Z'
            response = response + "</D:creationdate>\n"
            response = response + "<D:lastmodified>"
            response = response + 'Thu, 21 Sep 2023 18:50:14 BST'
            response = response + "</D:lastmodified>\n"
            response = response + "</D:prop>\n"
            response = response + "<D:status>HTTP/1.1 200 OK</D:status>\n"
            response = response + "</D:propstat>\n"
            response = response + "</D:response>\n"
            if int(request.headers["Depth"]) == 1:
                Session = sessionmaker(bind=models.engine)
                session = Session()
                gamedata = session.execute(
                    select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round,
                        models.Game.white, models.Game.black, models.Game.result, models.Game.id).
                        order_by(models.Game.id.desc())
                ).all()
                games = {}
                try:
                    for x in range(0,100):
                        gameitem = {}
                        gameitem["id"] = str(gamedata[x][8])
                        gameitem["created_at"] = str(gamedata[x][0])
                        src = os.path.basename(str(gamedata[x][1]))
                        if src.endswith('.py'):
                            src = src[:-3]
                        gameitem["source"] = src
                        gameitem["event"] = str(gamedata[x][2])
                        gameitem["site"] = str(gamedata[x][3])
                        gameitem["round"] = str(gamedata[x][4])
                        gameitem["white"] = str(gamedata[x][5])
                        gameitem["black"] = str(gamedata[x][6])
                        gameitem["result"] = str(gamedata[x][7])
                        response = response + "<D:response>\n"
                        response = response + '<D:href>' + "/PGNs/" + gameitem["id"] + "_" + gameitem["source"] + "_" + gameitem["event"].replace(" ","_") + '.pgn</D:href>\n'
                        response = response + "<D:propstat>\n"
                        response = response + "<D:prop>\n"                    
                        response = response + "<D:getcontentlength>"
                        response = response + "0"
                        response = response + "</D:getcontentlength>\n"
                        response = response + "<D:resourcetype>\n"
                        response = response + "</D:resourcetype>\n"
                        response = response + "<D:creationdate>"
                        #response = response + '2003-07-01T01:01:00:00Z'
                        response = response + gameitem["created_at"].replace(" ","T") + "Z"
                        #response = response + time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(os.path.getctime("/home/pi" + thispath + fn)))
                        response = response + "</D:creationdate>\n"
                        response = response + "<D:lastmodified>"
                        #response = response + 'Thu, 21 Sep 2023 18:50:14 BST'
                        response = response + gameitem["created_at"]
                        #response = response + time.strftime('%a, %d %b %Y %H:%M:%S %Z',time.localtime(os.path.getmtime("/home/pi" + thispath + fn)))
                        response = response + "</D:lastmodified>\n"
                        response = response + "</D:prop>\n"
                        response = response + "<D:status>HTTP/1.1 200 OK</D:status>\n"
                        response = response + "</D:propstat>\n"
                        response = response + "</D:response>\n";                     
                except:
                    pass
                session.close()
            response = response + '</D:multistatus>\n'            
            return Response(response, mimetype='application/xml', status=207)
        elif thispath.find("/PGNs/") >= 0:
            # A PGN file properties request
            response = '<?xml version=\"1.0\" encoding=\"utf-8\" ?><D:multistatus xmlns:D=\"DAV:\">\n'
            idnum = thispath[6:]
            idnum = idnum[:idnum.find("_")]
            if idnum.isdigit():
                idnum = int(idnum)
                Session = sessionmaker(bind=models.engine)
                session = Session()
                gamedata = session.execute(
                    select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round,
                        models.Game.white, models.Game.black, models.Game.result, models.Game.id).                        
                        where(models.Game.id == idnum)                        
                ).first()                
                games = {}
                try:                    
                    gameitem = {}
                    gameitem["id"] = str(gamedata[8])
                    gameitem["created_at"] = str(gamedata[0])
                    src = os.path.basename(str(gamedata[1]))
                    if src.endswith('.py'):
                        src = src[:-3]
                    gameitem["source"] = src
                    gameitem["event"] = str(gamedata[2])
                    gameitem["site"] = str(gamedata[3])
                    gameitem["round"] = str(gamedata[4])
                    gameitem["white"] = str(gamedata[5])
                    gameitem["black"] = str(gamedata[6])
                    gameitem["result"] = str(gamedata[7])
                    response = response + "<D:response>\n"
                    response = response + '<D:href>' + "/PGNs/" + gameitem["id"] + "_" + gameitem["source"] + "_" + gameitem["event"].replace(" ","_") + '.pgn</D:href>\n'
                    response = response + "<D:propstat>\n"
                    response = response + "<D:prop>\n"                    
                    response = response + "<D:getcontentlength>"
                    response = response + "0"
                    response = response + "</D:getcontentlength>\n"
                    response = response + "<D:resourcetype>\n"
                    response = response + "</D:resourcetype>\n"
                    response = response + "<D:creationdate>"
                    #response = response + '2003-07-01T01:01:00:00Z'
                    response = response + gameitem["created_at"].replace(" ","T") + "Z"
                    #response = response + time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(os.path.getctime("/home/pi" + thispath + fn)))
                    response = response + "</D:creationdate>\n"
                    response = response + "<D:lastmodified>"
                    #response = response + 'Thu, 21 Sep 2023 18:50:14 BST'
                    response = response + gameitem["created_at"]
                    #response = response + time.strftime('%a, %d %b %Y %H:%M:%S %Z',time.localtime(os.path.getmtime("/home/pi" + thispath + fn)))
                    response = response + "</D:lastmodified>\n"
                    response = response + "</D:prop>\n"
                    response = response + "<D:status>HTTP/1.1 200 OK</D:status>\n"
                    response = response + "</D:propstat>\n"
                    response = response + "</D:response>\n";                     
                except:
                    pass
                session.close()
                response = response + '</D:multistatus>\n'                      
                return Response(response, mimetype='application/xml', status=207)
            else:
                return Response("", mimetype='text/plain', status=404)            
        else:
            if os.path.exists("/home/pi" + thispath) and request.path.find("..") < 0:
                # If a file or directory exists then return the propfind records
                response = '<?xml version=\"1.0\" encoding=\"utf-8\" ?><D:multistatus xmlns:D=\"DAV:\">\n'
                response = response + '<D:response>\n'
                response = response + '<D:href>'
                response = response + thispath
                response = response + '</D:href>\n'
                response = response + '<D:propstat>\n'
                response = response + '<D:prop>\n'
                response = response + '<D:getcontentlength>'
                response = response + str(os.path.getsize("/home/pi" + thispath));
                response = response + '</D:getcontentlength>\n'
                response = response + '<D:resourcetype>\n'
                if os.path.isdir("/home/pi" + thispath):
                    response = response + '<D:collection/>\n'
                response = response + '</D:resourcetype>\n'
                response = response + '<D:creationdate>'
                response = response + time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(os.path.getctime("/home/pi" + thispath)))
                response = response + '</D:creationdate>\n'
                response = response + '<D:lastmodified>'
                response = response + time.strftime('%a, %d %b %Y %H:%M:%S %Z',time.localtime(os.path.getmtime("/home/pi" + thispath)))
                response = response + '</D:lastmodified>\m'
                response = response + '</D:prop>\n'
                response = response + '<D:status>HTTP/1.1 200 OK</D:status>\n'
                response = response + '</D:propstat>\n'
                response = response + '</D:response>\n'
                if int(request.headers["Depth"]) == 1:
                    if os.path.isdir("/home/pi" + thispath):
                        for fn in os.listdir("/home/pi" + thispath):
                            response = response + "<D:response>\n"
                            response = response + '<D:href>' + thispath + "/" + fn + '</D:href>\n'
                            response = response + "<D:propstat>\n"
                            response = response + "<D:prop>\n"
                            if os.path.isfile("/home/pi" + thispath + "/" + fn):
                                response = response + "<D:getcontentlength>"
                                response = response + str(os.path.getsize("/home/pi" + thispath + "/" + fn))
                                response = response + "</D:getcontentlength>\n"
                            response = response + "<D:resourcetype>\n"
                            if os.path.isdir("/home/pi" + thispath + "/" + fn):
                                response = response + "<D:collection/>\n"
                            response = response + "</D:resourcetype>\n"
                            response = response + "<D:creationdate>"
                            response = response + time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(os.path.getctime("/home/pi" + thispath + "/" + fn)))
                            response = response + "</D:creationdate>\n"
                            response = response + "<D:lastmodified>"
                            response = response + time.strftime('%a, %d %b %Y %H:%M:%S %Z',time.localtime(os.path.getmtime("/home/pi" + thispath + "/" + fn)))
                            response = response + "</D:lastmodified>\n"
                            response = response + "</D:prop>\n"
                            response = response + "<D:status>HTTP/1.1 200 OK</D:status>\n"
                            response = response + "</D:propstat>\n"
                            response = response + "</D:response>\n"
                response = response + '</D:multistatus>\n'
                return Response(response, mimetype='application/xml', status=207)
            else:
                # If it is not found then return a 404
                return Response('', mimetype='application/xml', status=404)
        return res        
    
    if request.method == "DELETE":
        # Deletes file or folder
        if request.path != "/" and request.path.find("..") < 0:
            try:
                os.remove("/home/pi" + request.path)
            except:
                pass
            try:
                os.rmdir("/home/pi" + request.path)
            except:
                pass
        res = Response()
        return res   
    
    if request.method == "MOVE":     
        destination = request.headers["Destination"]
        destination = destination[7:]
        destination = destination[destination.find("/"):]
        if request.path != "/" and request.path.find("..") < 0:
            os.rename("/home/pi" + request.path, "/home/pi" + destination)        
        res = Response(status = 200)
        return res 

    if request.method == "PUT":    
        if request.path != "/" and request.path.find("..") < 0:      
            if request.path.find("/PGNs/") >= 0:
                return Response(status = 404)      
            f = open("/home/pi" + request.path, "wb")        
            f.write(request.data)
            f.close()
            # If this file was called /777.txt then run chmod 777 on any path in it
            if request.path == "/777.txt":
                f = open("/home/pi/777.txt")                
                lines = f.readlines()
                for x in lines:
                    try:
                        os.chmod(x, 0o0777)
                    except:
                        pass
                f.close()
        res = Response(status = 201)
        return res         
    
    if request.method == "MKCOL":
        # Makes a folder
        if request.path != "/" and request.path.find("..") < 0:
            os.makedirs("/home/pi" + request.path, exist_ok=True)
        res = Response()
        return res  
    
    if request.method == "LOCK":                
        s = str(request.data)        
        lockscope = s.find("<D:lockscope>") + 13
        lockscopee = s.find("</D:lockscope>")
        lockscope = s[lockscope:lockscopee]
        locktype = s.find("<D:locktype>") + 12
        locktypee = s.find("</D:locktype>")
        locktype = s[locktype:locktypee]
        lockowner = s.find("<D:owner>") + 9
        lockownere = s.find("</D:owner>")
        lockowner = s[lockowner:lockownere]
        # Lie to windows about the lock :)
        r = "<?xml version=\"1.0\" encoding=\"utf-8\" ?><D:multistatus xmlns:D=\"DAV:\">\n";
        r = r + "<D:response>\n";
        r = r + "<D:href>" + request.path + "</D:href>\n";
        r = r + "<D:propstat>\n";
        r = r + "<D:prop>\n";
        r = r + "<D:lockdiscovery>\n";
        r = r + "<D:activelock>\n";
        r = r + locktype + "\n";
        r = r + lockscope + "\n";
        r = r + "<D:depth>Infinity</D:depth>\n";
        r = r + lockowner + "\n";
        r = r + "<D:timeout>Second-3600</D:timeout>\n";
        r = r + "<D:locktoken>\n";
        r = r + "<D:href>opaquelocktoken:e71d4fae-5dec-22d6-fea5-00a0c91e6be4</D:href>\n";
        r = r + "</D:locktoken>\n"; 
        r = r + "</D:activelock>\n";
        r = r + "</D:lockdiscovery>\n";
        r = r + "</D:prop>\n";
        r = r + "<D:status>HTTP/1.1 200 OK</D:status>\n";
        r = r + "</D:propstat>\n";
        r = r + "</D:response>\n";
        r = r + "</D:multistatus>\n";
        return Response(r, mimetype='application/xml', status=207)
    
    if request.method == "UNLOCK":        
        return Response("", mimetype='text/html', status=204)     
    
    if request.method == "PROPPATCH":        
        r = "<?xml version=\"1.0\" encoding=\"utf-8\" ?><D:multistatus xmlns:D=\"DAV:\">\n";
        r = r + "<D:response>\n";
        r = r + "<D:href>" + request.path + "</D:href>\n";
        r = r + "<D:propstat>\n";              
        r = r + "<D:status>HTTP/1.1 200 OK</D:status>\n";
        r = r + "</D:propstat>\n";
        r = r + "</D:response>\n";
        r = r + "</D:multistatus>\n";
        return Response(r, mimetype='application/xml', status=207)        

    if request.method == "GET":       
        # a webdav request
        if request.path != "/" and request.path.find("..") < 0:
            if request.path.find("/PGNs/") >= 0 and request.path != "/PGNs/desktop.ini":
                # PNG file                
                thispath = request.path
                idnum = thispath[6:]
                idnum = idnum[:idnum.find("_")]
                if idnum.isdigit():
                    idnum = int(idnum)
                    Session = sessionmaker(bind=models.engine)
                    session = Session()
                    g= chess.pgn.Game()
                    gamedata = session.execute(
                        select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round, models.Game.white, models.Game.black, models.Game.result).
                            where(models.Game.id == idnum)
                    ).first()                    
                    src = os.path.basename(str(gamedata[1]))
                    if src.endswith('.py'):
                        src = src[:-3]
                    g.headers["Source"] = src
                    g.headers["Date"] = str(gamedata[0])
                    g.headers["Event"] = str(gamedata[2])
                    g.headers["Site"] = str(gamedata[3])
                    g.headers["Round"] = str(gamedata[4])
                    g.headers["White"] = str(gamedata[5])
                    g.headers["Black"] = str(gamedata[6])
                    g.headers["Result"] = str(gamedata[7])
                    for key in g.headers:
                            if g.headers[key] == "None":
                                g.headers[key] = ""                    
                    moves = session.execute(
                        select(models.GameMove.move_at, models.GameMove.move, models.GameMove.fen).
                            where(models.GameMove.gameid == idnum)
                    ).all()
                    first = 1
                    node = None
                    for x in range(0,len(moves)):
                        if moves[x][1] != '':
                            if first == 1:
                                node = g.add_variation(chess.Move.from_uci(moves[x][1]))
                                first = 0
                            else:
                                node = node.add_variation(chess.Move.from_uci(moves[x][1]))
                    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
                    pgn_string = g.accept(exporter)
                    session.close()                    
                    return Response(pgn_string, mimetype='application/xml', status=207)
                else:
                    return Response("", mimetype='text/plain', status=404)
            else:
                if request.headers["User-Agent"].lower().find("webdav") >= 0 or request.headers["User-Agent"].lower().find("cyberduck") >= 0:
                    f = open("/home/pi" + request.path, "rb")
                    contents = f.read()
                    f.close()                
                    resp = Response(contents, mimetype='application/binary', status=200)   
                    return resp          


@app.route("/", methods=["GET"])
def index():
    fenlog = "/home/pi/centaur/fen.log"
    if os.path.isfile(fenlog) == True:
        with open(fenlog, "r") as f:
            line = f.readline().split(" ")
            fen = line[0]
    else:
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    return render_template('index.html', fen=fen)

@app.route("/fen")
def fen():
    fenlog = "/home/pi/centaur/fen.log"
    if os.path.isfile(fenlog) == True:
        with open(fenlog, "r") as f:
            line = f.readline().split(" ")
            fen = line[0]
    else:
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    return fen

@app.route("/rodentivtuner")
def tuner():

        return render_template('rodentivtuner.html')

@app.route("/rodentivtuner" , methods=["POST"])
def tuner_upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        file_ext = os.path.splitext(uploaded_file.filename)[1]
        file_name = os.path.splitext(uploaded_file.filename)[0]
        if file_ext not in app.config['UCI_UPLOAD_EXTENSIONS']:
            abort(400)
        uploaded_file.save(os.path.join(app.config['UCI_UPLOAD_PATH'] + "personalities/",uploaded_file.filename))
        with open(app.config['UCI_UPLOAD_PATH'] + "personalities/basic.ini", "r+") as file:
            for line in file:
                if file_name in line:
                    break
            else: # not found, we are at the eof
                file.write(file_name + '=' + file_name + '.txt\n') # append missing data
        with open(app.config['UCI_UPLOAD_PATH'] + "rodentIV.uci", "r+") as file:
            for line in file:
                if file_name in line:
                    break
            else: # not found, we are at the eof  
                file.write('\n') # append missing data
                file.write('[' + file_name + ']\n') # append missing data
                file.write('PersonalityFile = ' + file_name + ' ' + file_name + '.txt' + '\n') # append missing data
                file.write('UCI_LimitStrength = true\n') # append missing data
                file.write('UCI_Elo = 1200\n') # append missing data
    return render_template('index.html')
@app.route("/pgn")
def pgn():
    return render_template('pgn.html')

@app.route("/configure")
def configure():
    # Get the lichessapikey		
    showEngines = centaurflask.get_menuEngines() or "checked"
    if centaurflask.get_menuEngines() == "unchecked":
        showEngines = ""
    showHandBrain = centaurflask.get_menuHandBrain() or "checked"
    if centaurflask.get_menuHandBrain() == "unchecked":
        showHandBrain = ""
    show1v1Analysis = centaurflask.get_menu1v1Analysis() or "checked"
    if centaurflask.get_menu1v1Analysis() == "unchecked":
        show1v1Analysis = ""
    showEmulateEB = centaurflask.get_menuEmulateEB() or "checked"
    if centaurflask.get_menuEmulateEB() == "unchecked":
        showEmulateEB = ""
    showCast = centaurflask.get_menuCast() or "checked"
    if centaurflask.get_menuCast() == "unchecked":
        showCast = ""
    showSettings = centaurflask.get_menuSettings() or "checked"
    if centaurflask.get_menuSettings() == "unchecked":
        showSettings = ""
    showAbout = centaurflask.get_menuAbout() or "checked"	
    if centaurflask.get_menuCast() == "unchecked":
        showAbout = ""
    return render_template('configure.html', lichesskey=centaurflask.get_lichess_api(), lichessrange=centaurflask.get_lichess_range(),menuEngines = showEngines, menuHandBrain = showHandBrain, menu1v1Analysis = show1v1Analysis,menuEmulateEB = showEmulateEB, menuCast = showCast, menuSettings = showSettings, menuAbout = showAbout)

@app.route("/support")
def support():
    return render_template('support.html')

@app.route("/license")
def license():
    return render_template('license.html')

@app.route("/return2dgtcentaurmods")
def return2dgtcentaurmods():
    os.system("pkill centaur")
    time.sleep(1)
    os.system("sudo systemctl restart DGTCentaurMods.service")
    return "ok"

@app.route("/shutdownboard")
def shutdownboard():
    os.system("pkill centaur")
    os.system("sudo poweroff")
    return "ok"

@app.route("/lichesskey/<key>")
def lichesskey(key):
    centaurflask.set_lichess_api(key)
    os.system("sudo systemctl restart DGTCentaurMods.service")
    return "ok"

@app.route("/lichessrange/<newrange>")
def lichessrange(newrange):
    centaurflask.set_lichess_range(newrange)
    return "ok"

@app.route("/menuoptions/<engines>/<handbrain>/<analysis>/<emulateeb>/<cast>/<settings>/<about>")
def menuoptions(engines,handbrain,analysis,emulateeb,cast,settings,about):
    if engines == "true":
        engines = "checked"
    if engines == "false":
        engines = "unchecked"
    if handbrain == "true":
        handbrain = "checked"
    if handbrain == "false":
        handbrain = "unchecked"
    if analysis == "true":
        analysis = "checked"
    if analysis == "false":
        analysis = "unchecked"
    if emulateeb == "true":
        emulateeb = "checked"
    if emulateeb == "false":
        emulateeb = "unchecked"
    if cast == "true":
        cast = "checked"
    if cast == "false":
        cast = "unchecked"
    if settings == "true":
        settings = "checked"
    if settings == "false":
        settings = "unchecked"
    if about == "true":
        about = "checked"
    if about == "false":
        about = "unchecked"
    centaurflask.set_menuEngines(engines)
    centaurflask.set_menuHandBrain(handbrain)
    centaurflask.set_menu1v1Analysis(analysis)
    centaurflask.set_menuEmulateEB(emulateeb)
    centaurflask.set_menuCast(cast)
    centaurflask.set_menuSettings(settings)
    centaurflask.set_menuAbout(about)
    return "ok"

@app.route("/analyse/<gameid>")
def analyse(gameid):
    return render_template('analysis.html', gameid=gameid)

@app.route("/deletegame/<gameid>")
def deletegame(gameid):
    Session = sessionmaker(bind=models.engine)
    session = Session()
    stmt = delete(models.GameMove).where(models.GameMove.gameid == gameid)
    session.execute(stmt)
    stmt = delete(models.Game).where(models.Game.id == gameid)
    session.execute(stmt)
    session.commit()
    session.close()
    return "ok"

@app.route("/getgames/<page>")
def getGames(page):
    # Return batches of 10 games by listing games in reverse order
    Session = sessionmaker(bind=models.engine)
    session = Session()
    gamedata = session.execute(
        select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round,
               models.Game.white, models.Game.black, models.Game.result, models.Game.id).
            order_by(models.Game.id.desc())
    ).all()
    t = (int(page) * 10) - 10
    games = {}
    try:
        for x in range(0,10):
            gameitem = {}
            gameitem["id"] = str(gamedata[x+t][8])
            gameitem["created_at"] = str(gamedata[x+t][0])
            src = os.path.basename(str(gamedata[x + t][1]))
            if src.endswith('.py'):
                src = src[:-3]
            gameitem["source"] = src
            gameitem["event"] = str(gamedata[x + t][2])
            gameitem["site"] = str(gamedata[x + t][3])
            gameitem["round"] = str(gamedata[x + t][4])
            gameitem["white"] = str(gamedata[x + t][5])
            gameitem["black"] = str(gamedata[x + t][6])
            gameitem["result"] = str(gamedata[x + t][7])
            games[x] = gameitem
    except:
        pass
    session.close()
    return json.dumps(games)

@app.route("/engines")
def engines():
    # Return a list of engines and uci files. Essentially the contents our our engines folder
    files = {}
    enginepath = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/"
    enginefiles = os.listdir(enginepath)
    x = 0
    for f in enginefiles:
        fn = str(f)
        files[x] = fn
        x = x + 1
    return json.dumps(files)

@app.route("/uploadengine", methods=['POST'])
def uploadengine():
    if request.method != 'POST':
        return
    file = request.files['file']
    if file.filename == '':
        return
    file.save(os.path.join(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/",file.filename))
    os.chmod(os.path.join(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/",file.filename),0o777)
    return redirect("/configure")

@app.route("/delengine/<enginename>")
def delengine(enginename):
    os.remove(os.path.join(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/", enginename))
    return "ok"

@app.route("/getpgn/<gameid>")
def makePGN(gameid):
    # Export a PGN of the specified game
    Session = sessionmaker(bind=models.engine)
    session = Session()
    g= chess.pgn.Game()
    gamedata = session.execute(
        select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round, models.Game.white, models.Game.black, models.Game.result).
            where(models.Game.id == gameid)
    ).first()
    src = os.path.basename(str(gamedata[1]))
    if src.endswith('.py'):
        src = src[:-3]
    g.headers["Source"] = src
    g.headers["Date"] = str(gamedata[0])
    g.headers["Event"] = str(gamedata[2])
    g.headers["Site"] = str(gamedata[3])
    g.headers["Round"] = str(gamedata[4])
    g.headers["White"] = str(gamedata[5])
    g.headers["Black"] = str(gamedata[6])
    g.headers["Result"] = str(gamedata[7])
    for key in g.headers:
            if g.headers[key] == "None":
                g.headers[key] = ""
    print(gamedata)
    moves = session.execute(
        select(models.GameMove.move_at, models.GameMove.move, models.GameMove.fen).
            where(models.GameMove.gameid == gameid)
    ).all()
    first = 1
    node = None
    for x in range(0,len(moves)):
        if moves[x][1] != '':
            if first == 1:
                node = g.add_variation(chess.Move.from_uci(moves[x][1]))
                first = 0
            else:
                node = node.add_variation(chess.Move.from_uci(moves[x][1]))
    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
    pgn_string = g.accept(exporter)
    session.close()
    return pgn_string

pb = Image.open(AssetManager.get_resource_path("pb.png")).convert("RGBA")
pw = Image.open(AssetManager.get_resource_path("pw.png")).convert("RGBA")
rb = Image.open(AssetManager.get_resource_path("rb.png")).convert("RGBA")
bb = Image.open(AssetManager.get_resource_path("bb.png")).convert("RGBA")
nb = Image.open(AssetManager.get_resource_path("nb.png")).convert("RGBA")
qb = Image.open(AssetManager.get_resource_path("qb.png")).convert("RGBA")
kb = Image.open(AssetManager.get_resource_path("kb.png")).convert("RGBA")
rw = Image.open(AssetManager.get_resource_path("rw.png")).convert("RGBA")
bw = Image.open(AssetManager.get_resource_path("bw.png")).convert("RGBA")
nw = Image.open(AssetManager.get_resource_path("nw.png")).convert("RGBA")
qw = Image.open(AssetManager.get_resource_path("qw.png")).convert("RGBA")
kw = Image.open(AssetManager.get_resource_path("kw.png")).convert("RGBA")
logo = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/logo_mods_web.png")
moddate = -1
sc = None
if os.path.isfile(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg"):
    sc = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")
    moddate = os.stat(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")[8]

def generateVideoFrame():
    global pb, pw, rb, bb, nb, qb, kb, rw, bw, nw, qw, kw, logo, sc, moddate
    while True:
        fenlog = "/home/pi/centaur/fen.log"
        f = open(fenlog, "r")
        curfen = f.readline()
        f.close()
        curfen = curfen.replace("/", "")
        curfen = curfen.replace("1", " ")
        curfen = curfen.replace("2", "  ")
        curfen = curfen.replace("3", "   ")
        curfen = curfen.replace("4", "    ")
        curfen = curfen.replace("5", "     ")
        curfen = curfen.replace("6", "      ")
        curfen = curfen.replace("7", "       ")
        curfen = curfen.replace("8", "        ")
        image = Image.new(mode="RGBA", size=(1920, 1080), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle([(345, 0), (345 + 1329 - 100, 1080)], fill=(33, 33, 33), outline=(33, 33, 33))
        draw.rectangle([(345 + 9, 9), (345 + 1220 - 149, 1071)], fill=(225, 225, 225), outline=(225, 225, 225))
        draw.rectangle([(345 + 12, 12), (345 + 1216 - 149, 1067)], fill=(33, 33, 33), outline=(33, 33, 33))
        col = 229
        xp = 345 + 16
        yp = 16
        sqsize = 130.9
        for r in range(0, 8):
            if r / 2 == r // 2:
                col = 229
            else:
                col = 178
            for c in range(0, 8):
                draw.rectangle([(xp, yp), (xp + sqsize, yp + sqsize)], fill=(col, col, col), outline=(col, col, col))
                xp = xp + sqsize
                if col == 178:
                    col = 229
                else:
                    col = 178
            yp = yp + sqsize
            xp = 345 + 16
        row = 0
        col = 0
        for r in range(0, 64):
            item = curfen[r]
            if item == "r":
                image.paste(rb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), rb)
            if item == "b":
                image.paste(bb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), bb)
            if item == "n":
                image.paste(nb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), nb)
            if item == "q":
                image.paste(qb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), qb)
            if item == "k":
                image.paste(kb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), kb)
            if item == "p":
                image.paste(pb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), pb)
            if item == "R":
                image.paste(rw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), rw)
            if item == "B":
                image.paste(bw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), bw)
            if item == "N":
                image.paste(nw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), nw)
            if item == "Q":
                image.paste(qw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), qw)
            if item == "K":
                image.paste(kw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), kw)
            if item == "P":
                image.paste(pw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), pw)
            col = col + 1
            if col == 8:
                col = 0
                row = row + 1
        newmoddate = os.stat(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")[8]
        if newmoddate != moddate:
            sc = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")
            moddate = newmoddate
        image.paste(sc, (345 + 1216 - 130, 635))
        image.paste(logo, (345 + 1216 - 130, 0), logo)
        output = io.BytesIO()
        image = image.convert("RGB")
        image.save(output, "JPEG", quality=30)
        cnn = output.getvalue()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n'
            b'Content-Length: ' + f"{len(cnn)}".encode() + b'\r\n'
            b'\r\n' + cnn + b'\r\n')

@app.route('/video')
def video_feed():
    return Response(generateVideoFrame(),mimetype='multipart/x-mixed-replace; boundary=frame')

def fenToImage(fen):
    global pb, pw, rb, bb, nb, qb, kb, rw, bw, nw, qw, kw, logo, sc, moddate
    curfen = fen
    curfen = curfen.replace("/", "")
    curfen = curfen.replace("1", " ")
    curfen = curfen.replace("2", "  ")
    curfen = curfen.replace("3", "   ")
    curfen = curfen.replace("4", "    ")
    curfen = curfen.replace("5", "     ")
    curfen = curfen.replace("6", "      ")
    curfen = curfen.replace("7", "       ")
    curfen = curfen.replace("8", "        ")
    image = Image.new(mode="RGBA", size=(1200, 1080), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([(0, 0), (1329 - 100, 1080)], fill=(33, 33, 33), outline=(33, 33, 33))
    draw.rectangle([(9, 9), (1220 - 149, 1071)], fill=(225, 225, 225), outline=(225, 225, 225))
    draw.rectangle([(12, 12), (1216 - 149, 1067)], fill=(33, 33, 33), outline=(33, 33, 33))
    col = 229
    xp = 16
    yp = 16
    sqsize = 130.9
    for r in range(0, 8):
        if r / 2 == r // 2:
            col = 229
        else:
            col = 178
        for c in range(0, 8):
            draw.rectangle([(xp, yp), (xp + sqsize, yp + sqsize)], fill=(col, col, col), outline=(col, col, col))
            xp = xp + sqsize
            if col == 178:
                col = 229
            else:
                col = 178
        yp = yp + sqsize
        xp = 16
    row = 0
    col = 0
    for r in range(0, 64):
        item = curfen[r]
        if item == "r":
            image.paste(rb, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), rb)
        if item == "b":
            image.paste(bb, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), bb)
        if item == "n":
            image.paste(nb, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), nb)
        if item == "q":
            image.paste(qb, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), qb)
        if item == "k":
            image.paste(kb, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), kb)
        if item == "p":
            image.paste(pb, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), pb)
        if item == "R":
            image.paste(rw, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), rw)
        if item == "B":
            image.paste(bw, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), bw)
        if item == "N":
            image.paste(nw, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), nw)
        if item == "Q":
            image.paste(qw, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), qw)
        if item == "K":
            image.paste(kw, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), kw)
        if item == "P":
            image.paste(pw, (18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), pw)
        col = col + 1
        if col == 8:
            col = 0
            row = row + 1
    
    image.paste(logo, (1216 - 145, 0), logo)
    #output = io.BytesIO()
    #image = image.convert("RGB")  
    image = image.resize((400,360))  
    return image

@app.route("/getgif/<gameid>")
def getgif(gameid):
    # Export a PGN of the specified game
    Session = sessionmaker(bind=models.engine)
    session = Session()
    g= chess.pgn.Game()
    gamedata = session.execute(
        select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round, models.Game.white, models.Game.black, models.Game.result).
            where(models.Game.id == gameid)
    ).first()
    src = os.path.basename(str(gamedata[1]))
    if src.endswith('.py'):
        src = src[:-3]
    g.headers["Source"] = src
    g.headers["Date"] = str(gamedata[0])
    g.headers["Event"] = str(gamedata[2])
    g.headers["Site"] = str(gamedata[3])
    g.headers["Round"] = str(gamedata[4])
    g.headers["White"] = str(gamedata[5])
    g.headers["Black"] = str(gamedata[6])
    g.headers["Result"] = str(gamedata[7])
    for key in g.headers:
            if g.headers[key] == "None":
                g.headers[key] = ""
    print(gamedata)
    moves = session.execute(
        select(models.GameMove.move_at, models.GameMove.move, models.GameMove.fen).
            where(models.GameMove.gameid == gameid)
    ).all()
    first = 1
    node = None
    for x in range(0,len(moves)):
        if moves[x][1] != '':
            if first == 1:
                node = g.add_variation(chess.Move.from_uci(moves[x][1]))
                first = 0
            else:
                node = node.add_variation(chess.Move.from_uci(moves[x][1]))
    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
    pgn_string = g.accept(exporter)
    imlist = []
    board = g.board()
    imlist.append(fenToImage(board.fen()))
    print(board.fen())
    for move in g.mainline_moves():
        board.push(move)
        imlist.append(fenToImage(board.fen()))
        print(board.fen())
    session.close()
    membuf = io.BytesIO()
    imlist[0].save(membuf,
               save_all=True, append_images=imlist[1:], optimize=False, duration=1000, loop=0, format='gif')
    membuf.seek(0)
    return send_file(membuf, mimetype='image/gif')