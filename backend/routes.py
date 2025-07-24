from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# RETURN HEALTH OF THE APP
######################################################################
@app.route("/health")
def health():
    return jsonify({"status": "OK"}), 200


######################################################################
# COUNT THE NUMBER OF SONGS
######################################################################
@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})
    return jsonify({"count": count}), 200
    # return {"message": "Internal server error"}, 500


######################################################################
# GET ALL SONGS
######################################################################
@app.route("/song", methods=["GET"])
def songs():
    result_set = list(db.songs.find({}))
    print(result_set)
    return jsonify({"songs": parse_json(result_set)}), 200


######################################################################
# GET A SONG
######################################################################
@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    result_set = db.songs.find_one({"id": id})
    if not result_set or len(result_set) < 1:
        return jsonify({"message": "song with id not found"}), 404
    return jsonify(parse_json(result_set)), 200


######################################################################
# CREATE A SONG
######################################################################
@app.route("/song", methods=["POST"])
def create_song():
    song = request.get_json()
    print(f"{song=}")
    find_song = db.songs.find_one({"id": song["id"]})
    if find_song:
        return jsonify({"Message": f"song with id {song['id']} already present"}), 302
    db.songs.insert_one(song)
    return jsonify(parse_json(song)), 201


######################################################################
# UPDATE A SONG
######################################################################
@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    update_data = request.get_json()
    song = db.songs.find_one({"id": id})
    if song:
        result_set = db.songs.update_one(song, {"$set": update_data})
        if result_set.modified_count == 0:
            return jsonify({"message":"song found, but nothing updated"}), 200
        else:
            return jsonify(parse_json(db.songs.find_one({"id": id}))), 201
    return jsonify({"message": "song not found"}), 404


######################################################################
# DELETE A SONG
######################################################################
@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result_set = db.songs.delete_one({"id": id})
    if result_set.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404
    else:
        return jsonify(), 204
