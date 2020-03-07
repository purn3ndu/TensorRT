from flask import Flask, request, jsonify, json
import os

app = Flask(__name__)

# endpoint to do qa inference and return answer
@app.route("/qa", methods=["POST"])
def add_user():
    try:
        context = str(request.json['context'])
        question = str(request.json['question'])

        from tr_infer import Model
        m = Model()
        r = m.inference(context, question)

        return jsonify({"code": 200, "message": r})

    except Exception as e:
        return jsonify({"code": 500, "message": type(e).__name__})


if __name__ == '__main__':
    # check_db()
    app.run(host='0.0.0.0', port=5001, debug=True)