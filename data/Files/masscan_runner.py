import subprocess
import os
import signal
import sys

class MasscanRunner:
    def __init__(self, ip_file, output_file="masscanResults.txt", rate=10000):
        self.ip_file = ip_file
        self.output_file = output_file
        self.rate = rate

    def cleanup(self):
        if os.path.exists(self.output_file):
            print("🧹 Deleting", self.output_file)
            os.remove(self.output_file)

    def run(self):
        if not os.path.exists(self.ip_file):
            print("❌ IP range file not found:", self.ip_file)
            sys.exit(1)

        cmd = f"sudo masscan -p443 --rate {self.rate} --wait 0 -iL {self.ip_file} -oH {self.output_file}"
        print("Running:", cmd)

        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print("Masscan error:", e)
            self.cleanup()
            sys.exit(1)
