import csv
import hashlib
import requests
import argparse
cache = {}

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_hashes(prefix: str):
	if prefix in cache:
		return cache[prefix]

	assert len(prefix) == 5
	attempts = 0
	success = False
	resp = None
	while attempts < 5 and not success:
		try:
			resp = requests.get("https://api.pwnedpasswords.com/range/{}".format(prefix))
			success = True
		except requests.exceptions.ConnectionError:
			attempts += 1
			print("Connection to pwnedpasswords failed, retrying...")

	pass_with_freq = []
	for password in resp.text.split("\n"):
		if len(password) == 0:
			continue

		parts = password.split(":")
		pass_with_freq.append((prefix + parts[0].lower(), int(parts[1])))

	cache[prefix] = pass_with_freq
	return pass_with_freq

def find_password_hash(pass_sha1: str):
	for pass_hash, freq in get_hashes(pass_sha1[0:5]):
		if pass_hash == pass_sha1:
			return (pass_hash, freq)
	return None, None

def sha1(plain: str):
	return hashlib.sha1(plain.encode()).hexdigest()

def lastpass(file: str):
	with open(file) as f:
		reader = csv.DictReader(f)
		for row in reader:
			password = row["password"]
			if len(password) == 0:
				continue

			pass_sha = sha1(password)
			pass_hash, freq = find_password_hash(pass_sha)
			if freq is not None and freq > 0:
				print("{}{}Password pwned!{} Password for site {}{}{} found in {} password dumps.".format(Colors.FAIL, Colors.BOLD, Colors.ENDC, Colors.BOLD, row["name"], Colors.ENDC, freq))


def main():
	parser = argparse.ArgumentParser(description='Check if passwords have been pwned using haveibeenpwned.com')
	parser.add_argument('--lastpass', metavar="file", help="Check lastpass passwords from export CSV file")
	parser.add_argument('rest', nargs=argparse.REMAINDER)
	args = parser.parse_args()

	if args.lastpass:
		lastpass(args.lastpass)
	elif len(args.rest) == 1:
		pass_hash, freq = find_password_hash(sha1(args.rest[0]))
		if freq == None or freq == 0:
			print("{}{}Password safe!{} Password has not been found in any passsword dumps".format(Colors.OKGREEN, Colors.BOLD, Colors.ENDC))
		else:
			print("{}{}Password pwned!{} Password found in {} password dumps.".format(Colors.FAIL, Colors.BOLD, Colors.ENDC, freq))
	else:
		parser.print_help()


if __name__=="__main__":
	main()
