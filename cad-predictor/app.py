from lib2to3.pgen2.pgen import generate_grammar
import paho.mqtt.client as paho
from paho import mqtt
import base64
from flask import Flask, render_template
import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import Model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.imagenet_utils import preprocess_input
import numpy as np
import PIL.Image as Image
import io
from skimage import transform

CAD_FOLDER = os.path.join('static', 'cad')

app = Flask(__name__)
subscribed_topic = "cad-predict/#"
publishing_topic = "cad-predict/2"

app.config['UPLOAD_FOLDER'] = CAD_FOLDER

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def evaluate_result(arr):
  if arr[0][0] == 1:
    return "stenosis" 
  else:
    return "non-stenosis"

# model_predict --> https://www.fullstackpython.com/flask-templating-render-template-examples.html

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    if 'test message' not in str(msg.payload):
		# https://code.tutsplus.com/tutorials/base64-encoding-and-decoding-using-python--cms-25588
        try:
            image_64_decode = base64.b64decode(msg.payload)
            print(image_64_decode)
            print("Success converting the image")
        except TypeError:
            print("Error converting the input")
        image_result = open('./static/cad/img.png', 'wb') # create a writable image and write the decoding result
        image_result.write(image_64_decode)

# https://code.tutsplus.com/tutorials/base64-encoding-and-decoding-using-python--cms-25588
    # image_64_decode = base64.b64decode(str(msg.payload)) 
    # # image_result = open('./restore001.png', 'wb') # create a writable image and write the decoding result
    # # image_result.write(image_64_decode)

    # print("data arrived in the predictor")

        base_model = keras.applications.ResNet50(weights='imagenet',input_shape=(224, 224, 3),include_top=True) 
        # print("model setup")
        x = tf.keras.layers.Dense(2,activation='softmax')(base_model.layers[-2].output) 
        print("top layer changed")
        model = Model(base_model.inputs,outputs=x)
        print("model created")
        # to save the weights, as you've displayed. To load the weights, you would first need to build your model, and then call load_weights on the model, as in
        model.load_weights("./model/model_resnet50_1.h5")
        print("Loaded Model from disk")

        # result=model_predict(image_64_decode, model)
        image_from_bytes = Image.open(io.BytesIO(image_64_decode))
        np_image = image_from_bytes.convert("RGB")
        np_image = np.array(np_image).astype('float32')
        np_image = transform.resize(np_image, (224, 224, 3))
        np_image = np.expand_dims(np_image, axis=0)/255
        
        # img = img.resize((224, 224))
        

        # img=cv2.imread('0.png')
        # img=cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # x = image.img_to_array(img)
        # x = np.expand_dims(x, axis=0)
        # x = preprocess_input(x, mode='tf')

        preds = model.predict(np_image)

        print(str(preds))
        global general_prediction 
        threshold = 0.5
        general_prediction = evaluate_result(np.where(preds > threshold, 1,0))


@app.route("/result")
def result():
	full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'img.png')
	return render_template("index.html", user_image = full_filename, prediction = general_prediction)

if __name__ == "__main__":

    # using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
    # userdata is user defined data of any type, updated by user_data_set()
    # client_id is the given name of the client
    client = paho.Client(client_id="predictor", userdata=None, protocol=paho.MQTTv5)
    client.on_connect = on_connect

    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set("cad-user", "CAD-password1")
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect("222ad3477f1e4dc495f8fb0253766b63.s1.eu.hivemq.cloud", 8883)

    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_publish = on_publish

    # subscribe to all topics of encyclopedia by using the wildcard "#"
    client.subscribe(subscribed_topic, qos=1)

    # loop_forever for simplicity, here you need to stop the loop manually
    # you can also use loop_start and loop_stop
    client.loop_start()

    osPort = os.getenv("PORT")
    if osPort == None:
        port = 8080
    else:
        port = int(osPort)
    app.run(host="0.0.0.0", port=port)