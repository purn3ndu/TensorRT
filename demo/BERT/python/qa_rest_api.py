from multiprocessing import Process, Queue

input_queue = Queue()
output_queue = Queue()

def run_server(input_queue, output_queue):

    from flask import Flask, request, jsonify, json
    app = Flask(__name__)
    app.run(host='0.0.0.0', port=8880, debug=True)

    # endpoint to do qa inference and return answer
    @app.route("/qa", methods=["POST"])
    def add_user():
        try:
            context = str(request.json['context'])
            question = str(request.json['question'])

            input_queue.put(context, question)
            result = output_queue.get()

            return jsonify({"code": 200, "message": result})

        except Exception as e:
            return jsonify({"code": 500, "message": type(e).__name__})


if __name__ == '__main__':
    p = Process(target=run_server, args=(input_queue, output_queue))
    p.start()

    from tr_infer import Model
    m = Model()
    while True:
        inputs = input_queue.get()
        r = m.inference(inputs[0], inputs[1])
        output_queue.put(r)