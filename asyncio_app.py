import asyncio
import time
from flask import Flask, jsonify
import threading

print(f"In flask global level: {threading.current_thread().name}")
app = Flask(__name__)

@app.route("/test", methods=["GET"])
def index():
    print(f"Inside flask function: {threading.current_thread().name}")
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(hello())
    return jsonify({"result": result})

async def hello():
    print("one")
    await asyncio.sleep(15)
    print("two")
    return 1


if __name__ == '__main__':
    app.run(debug=True)