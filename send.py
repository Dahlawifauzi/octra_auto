#!/usr/bin/env python3
import json, base64, hashlib, time, sys, re, asyncio, aiohttp
import nacl.signing

# --- Configuration ---
ADDRESS_FILE = 'address.txt'
AMOUNT_TO_SEND = 1
DEFAULT_RPC = 'https://octra.network'
# --- End Configuration ---

c = {'g': '\033[92m', 'R': '\033[91m', 'w': '\033[97m', 'y': '\033[93m', 'c': '\033[96m'}

def print_c(color, *args):
    """Prints colored text."""
    print(color + ' '.join(map(str, args)) + c['w'])

def load_wallet():
    """Loads wallet configuration from wallet.json."""
    try:
        with open('wallet.json', 'r') as f:
            d = json.load(f)
        priv = d.get('priv')
        addr = d.get('addr')
        rpc = d.get('rpc', DEFAULT_RPC)
        sk = nacl.signing.SigningKey(base64.b64decode(priv))
        pub = base64.b64encode(sk.verify_key.encode()).decode()
        return priv, addr, rpc, sk, pub
    except FileNotFoundError:
        print_c(c['R'], "[ERROR] wallet.json not found. Please create it.")
    except Exception as e:
        print_c(c['R'], f"[ERROR] Failed to load wallet: {e}")
    return None, None, None, None, None

async def make_request(session, method, rpc, path, data=None, timeout=10):
    """Makes a single asynchronous HTTP request."""
    url = f"{rpc}{path}"
    try:
        async with session.request(method, url, json=data, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            text = await resp.text()
            try:
                # Be more lenient with JSON parsing, regardless of content-type
                json_data = json.loads(text)
            except json.JSONDecodeError:
                json_data = None
            return resp.status, text, json_data
    except asyncio.TimeoutError:
        return 0, "timeout", None
    except aiohttp.ClientConnectorError as e:
        return 0, f"connection error: {e}", None
    except Exception as e:
        return 0, str(e), None

async def get_account_state(session, rpc, addr):
    """Fetches the current balance and nonce from the network."""
    status, text, json_data = await make_request(session, 'GET', rpc, f'/balance/{addr}')
    if status == 200 and json_data:
        return int(json_data.get('nonce', 0)), float(json_data.get('balance', 0))
    elif status == 404:
        return 0, 0.0
    
    print_c(c['R'], f"Could not fetch balance/nonce. Status: {status}, Response: {text}")
    return None, None

def create_transaction(addr, pub_key, sk, to, amount, nonce):
    """Creates and signs a transaction."""
    tx = {
        "from": addr,
        "to_": to,
        "amount": str(int(amount * 1_000_000)),
        "nonce": int(nonce),
        "ou": "1",
        "timestamp": time.time()
    }
    tx_bytes = json.dumps(tx, separators=(",", ":")).encode('utf-8')
    signature = base64.b64encode(sk.sign(tx_bytes).signature).decode()
    tx.update(signature=signature, public_key=pub_key)
    tx_hash = hashlib.sha256(tx_bytes).hexdigest()
    return tx, tx_hash

async def send_transaction(session, rpc, tx):
    """Sends a transaction to the network."""
    status, text, json_data = await make_request(session, 'POST', rpc, '/send-tx', data=tx)
    if status == 200 and ((json_data and json_data.get('status') == 'accepted') or 'ok' in text.lower()):
        tx_hash = json_data.get('tx_hash') if json_data else text.split()[-1]
        return True, tx_hash
    return False, json_data.get('error', text) if json_data else text

async def main():
    priv, addr, rpc, sk, pub = load_wallet()
    if not addr:
        return

    print_c(c['y'], f"Wallet loaded for address: {addr}")

    try:
        with open(ADDRESS_FILE, 'r') as f:
            recipients = [line.strip() for line in f if line.strip() and re.match(r"^oct[1-9A-HJ-NP-Za-km-z]{44}$", line.strip())]
        if not recipients:
            print_c(c['R'], f"No valid addresses found in {ADDRESS_FILE}.")
            return
        print_c(c['c'], f"Found {len(recipients)} valid addresses in {ADDRESS_FILE}.")
    except FileNotFoundError:
        print_c(c['R'], f"[ERROR] The file '{ADDRESS_FILE}' was not found.")
        return

    async with aiohttp.ClientSession() as session:
        current_nonce, balance = await get_account_state(session, rpc, addr)
        if current_nonce is None:
            return

        total_cost = len(recipients) * AMOUNT_TO_SEND
        print_c(c['y'], f"Current Balance: {balance:.6f} OCT")
        print_c(c['y'], f"Total to send:   {total_cost:.6f} OCT to {len(recipients)} addresses.")

        if balance < total_cost:
            print_c(c['R'], "Insufficient balance to complete all transactions.")
            return

        confirm = input(f"Proceed with sending? (y/n): ").lower()
        if confirm != 'y':
            print_c(c['R'], "Aborted by user.")
            return

        s_total, f_total = 0, 0
        next_nonce = current_nonce + 1

        for i, to_address in enumerate(recipients):
            print_c(c['w'], f"[{i+1}/{len(recipients)}] Sending {AMOUNT_TO_SEND} OCT to {to_address[:15]}...")
            
            transaction, _ = create_transaction(addr, pub, sk, to_address, AMOUNT_TO_SEND, next_nonce)
            ok, result_msg = await send_transaction(session, rpc, transaction)

            if ok:
                print_c(c['g'], f"  ✓ Success! Hash: {result_msg}")
                s_total += 1
                next_nonce += 1
            else:
                print_c(c['R'], f"  ✗ Failed! Reason: {result_msg}")
                f_total += 1
            
            await asyncio.sleep(0.5)

        print_c(c['c'], "\n--- Sending Complete ---")
        print_c(c['g'], f"Successful transactions: {s_total}")
        print_c(c['R'], f"Failed transactions:     {f_total}")
        print_c(c['y'], "------------------------")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
