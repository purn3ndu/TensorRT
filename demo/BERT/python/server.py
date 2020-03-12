from multiprocessing import Process, Queue
import json
import re
import requests

input_queue = Queue()
output_queue = Queue()

jarvis_profile_file = "http://docs.google.com/document/d/17HJL7vrax6FiF1zW_Vzqk9FTfmATeq5i3UemtagM8RY/export?format=txt"
jarvis_profile = requests.get(jarvis_profile_file).text


# rules
replacement_rules = {"what's": "what is", "who's": "who is", "?": ""}
starting_phrases = ["tell me", "can you", "please"]
relation_words = ["from"]
question_words = ["what", "why", "who", "how old", "how long", "how", "do", "does", "where"]
verb_words = ["is", "are", "do", "does"]
belonging_word_convertor = {"my": "your", "your": "my", "yours": "my", "you": "i", "i" : "you",
                            "can you": "i can", "could you": "i could", "have you": "i have"}


# Function that extends the precise answer based on the question
def extend_answer(question, answer):
    print(question + " (" + answer + ") => ", end = " ")

    # Heuristics for long factual answer, where there is no need to copy question into the answer
    if len(answer.split()) >= 5:
        return answer

    # move to lower case
    question = question.lower()

    # extend shortcuts in the question word and remove question sign
    for key in replacement_rules:
        question = question.replace(key, replacement_rules[key])

    # find possible relation word, like "from"
    relation_word = None
    for word in relation_words:
        if question.startswith(word):
            relation_word = word
            question = question[len(word) + 1:]
            break

    # find starting question word
    question_word = None
    for word in question_words:
        if question.startswith(word):
            question_word = word
            question = question[len(word)+1:]
            break

    # Try to find possible relation word like "from" for a second fime in case they are coming after the question
    if relation_word is None:
        for word in relation_words:
            if question.startswith(word):
                relation_word = word
                question = question[len(word) + 1:]
                break

    # in this case you do not add question to the answer
    if question_word is None:
        return answer

    # find starting verb word
    verb_word = None
    for word in verb_words:
        if question.startswith(word):
            if word is not "do" and word is not "does":
                if word == "are":
                    verb_word = "am"
                else:
                    verb_word = word
            question = question[len(word) + 1:]
            break

    # check if a phrase start with a belonging word that should be converted to the opposite one
    for key in belonging_word_convertor:
        if question.startswith(key):
            question = question.replace(key, belonging_word_convertor[key])
            break

    # create full answer
    full_answer = question

    if relation_word is not None:
        full_answer += " " + relation_word

    if verb_word is not None:
        full_answer += " " + verb_word

    full_answer += " " + answer

    # Capitalize the first letter
    full_answer = full_answer[0].upper() + full_answer[1:]

    return full_answer


def run_server(input_queue, output_queue):
    import cherrypy

    cherrypy.config.update({'server.socket_port': 5000,
#        'environment': 'production',
        'engine.autoreload.on': False,
#        'server.thread_pool':  1,
        'server.socket_host': '0.0.0.0'})

    class HelloWorld(object):
        import cherrypy
        @cherrypy.expose
        def index(self):
         return """<html>
              <head>

    <script>
    function clicked() {
      var xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
         console.log(this.responseText);
         var jsonResponse = JSON.parse(this.responseText);
         document.getElementById("answer").value = jsonResponse['result'];
         //document.getElementById("probability").value = jsonResponse['p']
        }
      };

      xhttp.open("POST", "infer", true);
      xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
      var context_doc = document.getElementById("context").value;
      var question_doc = document.getElementById("question").value;
      xhttp.send(JSON.stringify({ "context": context_doc, "question": question_doc }));
    }

    function selected(){
    document.getElementById("question").value = document.getElementById("examples").value;
    };

    </script>

              </head>
              <body>
              <h1 style="text-align:center;"><font color="green">Jarvis QA - WIP</font></h1>
              <div style="width=800 margin:0 auto;" align="center">

              <p>
    <textarea rows="30" cols="100" id="context">
    %s
   </textarea>
   </p>
   <input type="radio" id="full_sentence_switch" name="gender" value="full">
    <label for="full">Return full sentence</label><br>
    <label for="span">Return answer span only</label><br>
   <p>
    Example questions:
    </p>
    <p>
    <select onchange="selected()" id="examples">

    <option value="Who are you?">"Who are you?"</option>
    <option value="What can you do?">"What can you do?"</option>
    </select>
    </p>

   <p>
    Question:<input type="text" id="question" value="Who are you?" size=50>
    </p>
    <p>
    <button type="button" onclick="clicked()">Submit</button>
    </p>
    <p>
    Answer:<input type="text" id="answer" size=50 disabled=true>
    </p>
    </div>
    </body>
            </html>""" % (jarvis_profile,)

        @cherrypy.expose
        @cherrypy.tools.json_out()
        @cherrypy.tools.json_in()
        def infer(self):
            input_json = cherrypy.request.json
            input_queue.put((input_json['context'], input_json['question']))
            return output_queue.get()

        @cherrypy.expose
        @cherrypy.tools.json_out()
        @cherrypy.tools.json_in()
        def infer_api(self):
            input_json = cherrypy.request.json
            input_question = re.sub(r'[^\x00-\x7F]+',' ', input_json['question'])
            input_context = re.sub(r'[^\x00-\x7F]+',' ', input_json['context'])
            print("Question received -> ", input_json['question'])
            input_queue.put((input_context, input_question))
            r = output_queue.get()
            # Return the full sentence in which the answer span is present if full sentence flag is on in document.
            if r['result'] != '' and input_context.find('RETURN_FULL_SENTENCE_CONTAINING_ANSWER_SPAN') != -1:
                ans_sentences = [sentence + '.' for sentence in input_context.split('.') if r['result'] in sentence]
                r['result'] = ans_sentences[0].strip()
            return r

    cherrypy.quickstart(HelloWorld())

if __name__ == '__main__':
    p = Process(target=run_server, args=(input_queue, output_queue))
    p.start()

    from tr_infer import Model
    m = Model()
    while True:
        inputs = input_queue.get()
        r = m.inference(inputs[0], inputs[1])
        print(r)
        # If result contains answer span and full sentence flag is not present then use answer extender
        # If full sentence flag is present then don't use answer extender as full sentence containing answer span
        # will be returned
        if r['result'] != '' and inputs[0].find('RETURN_FULL_SENTENCE_CONTAINING_ANSWER_SPAN') == -1:
            output_queue.put({'result':extend_answer(inputs[1], r['result']), 'p': r['p']})
        else:
            output_queue.put(r)
