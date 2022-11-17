import time
from flask import Flask, Response, stream_with_context
import multiprocessing

app = Flask(__name__)

def daemon():
    for j in range(10):
        data = '\t this is sub line {}'.format(j)
        print(data)
        j+=1
        time.sleep(1)

@app.route('/stream')
def index():
    def gen():
        p = multiprocessing.current_process()
        print('Starting:', p.name, p.pid)
        i = 0
        while True:
            data = 'this is main line {}'.format(i)
            print(data)
            yield data + '<br>'
            d = multiprocessing.Process(name='daemon', target=daemon)
            d.daemon = True
 
            d.start()
            d.terminate()
            i += 1
            time.sleep(1)
    response = Response(stream_with_context(gen()))
    print("Response!!!:",response)
    return response
    



if __name__ == "__main__":
    

    # debug mode
    app.run(host='0.0.0.0', debug=False, port=5000)