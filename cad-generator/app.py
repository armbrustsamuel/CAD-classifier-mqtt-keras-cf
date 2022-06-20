
import os
import base64
import paho.mqtt.client as paho
from paho import mqtt
from flask import Flask, request, render_template

CAD_FOLDER = os.path.join('static', 'cad')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = CAD_FOLDER

# port = int(os.getenv('VCAP_APP_PORT', 8080))
subscribed_topic = "cad-predict/2"
publishing_topic = "cad-predict/1"

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
	print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
	render_page(msg)

def render_page(msg):
	print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
	filename = "./imgs/stenosis/positive_1.png"
	return render_template("index.html", user_image = filename, prediction = msg.payload)
	


@app.route("/predict", methods=['GET'])
def predict():
	args = request.args
	filename = args.get('img')

	img_prefix = "./static/cad/"
	
	img_fullpath = img_prefix + filename + ".png"
	image = open(img_fullpath, 'rb')
	image_read = image.read()
	image_64_encode = base64.b64encode(image_read)

	result = client.publish(topic=publishing_topic, payload=image_64_encode)
	# result = client.publish(publishing_topic, image_64_encode)
	# result: [0, 1]
	status = result[0]
	if status == 0:
		print(f"Send `{image_64_encode}` to topic `{publishing_topic}`")
	else:
		print(f"Failed to send message to topic {publishing_topic}")
	
	full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename + '.png')
	return render_template("index.html", user_image = full_filename)	
	
if __name__ == "__main__":

	# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
	# userdata is user defined data of any type, updated by user_data_set()
	# client_id is the given name of the client
	client = paho.Client(client_id="generator", userdata=None, protocol=paho.MQTTv5)
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

	client.loop_start()

	osPort = os.getenv("PORT")
	if osPort == None:
		port = 5000
	else:
		port = int(osPort)
	app.run(host="0.0.0.0", port=port)