import ipfshttpclient

def upload_to_ipfs(file_path):
    try:
        client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
        res = client.add(file_path)
        print("IPFS response:", res)  
        ipfs_hash = res.get('Hash')
        return ipfs_hash
    except Exception as e:
        print(f"IPFS upload error: {e}")
        return None
