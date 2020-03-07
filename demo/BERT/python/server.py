from multiprocessing import Process, Queue

input_queue = Queue()
output_queue = Queue()
f = open('plan_doc.txt','r')
paragraph_text = f.read()

def run_server(input_queue, output_queue):
    import cherrypy

    cherrypy.config.update({'server.socket_port': 8880,
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
      var para_doc = document.getElementById("para").value;
      var question_doc = document.getElementById("question").value;
      xhttp.send(JSON.stringify({ "para": para_doc, "question": question_doc }));
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
    <textarea rows="30" cols="100" id="para">
    %s
   </textarea>
   </p>
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
    Question:<input type="text" id="question" value="Did Mozart and Beethoven meet?" size=50>
    </p>
    <p>
    <button type="button" onclick="clicked()">Submit</button>
    </p>
    <p>
    Answer:<input type="text" id="answer" size=50 disabled=true>
    </p>
    </div>
    </body>
            </html>""" % (paragraph_text,)

        @cherrypy.expose
        @cherrypy.tools.json_out()
        @cherrypy.tools.json_in()
        def infer(self):
            input_json = cherrypy.request.json
            input_queue.put((input_json['para'], input_json['question']))
            return output_queue.get()
    cherrypy.quickstart(HelloWorld())

if __name__ == '__main__':
    p = Process(target=run_server, args=(input_queue, output_queue))
    p.start()

    from tr_infer import Model
    m = Model()
    while True:
        inputs = input_queue.get()
        r = m.inference(inputs[0], inputs[1])
        output_queue.put(r)
