import sys
import os
import struct
from Crypto.Cipher import Salsa20

from utils import wincrypt,tools

class one_click_decrypt:
    def __init__(self,threat_note_path):
        self.ransom_path = threat_note_path
        self.priv_user_rsa_key = b""
        self.out_path =  os.path.join(os.path.dirname(os.path.realpath(__file__)),"user_priv_rsa")
    
    def decrypt_all(self):
        self.dec_priv_user_rsa()
        for file in tools.scan_crypted_file(ext = tools.get_ransom_ext(self.ransom_path)):
            print("[+] Found crypted file: "+file,flush=True)
            try:
                self.decr_file(file)
            except EnvironmentError:
                print("Error: Failed to decrypt.")
        
    def dec_priv_user_rsa(self):
        ransom_ver = tools.get_ransom_ver(self.ransom_path, "GANDCRAB KEY")
        print("[+] GandCrab version: V"+ str(ransom_ver),flush=True)
        # load master key
        if(4 <= ransom_ver < 5.04):
            rsa_master_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "rsa_keys","rsa_master_priv_4-5")
        elif(5.04 <= ransom_ver <5.2):
            rsa_master_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "rsa_keys","rsa_master_priv_5_0_4-5_1")
        elif(5.2 <= ransom_ver):
            rsa_master_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"rsa_keys", "rsa_master_priv_5_2")
        else:
            raise EnvironmentError("ERROR: Not supported version gandcrab file inputted.")

        priv = wincrypt.CryptImportKey(open(rsa_master_path, "rb").read())

        if priv is None:
            raise FileNotFoundError("ERROR: unable to read private RSA master key")

        rkey = tools.get_ransom_data(self.ransom_path, "GANDCRAB KEY")
        privateKeySize = struct.unpack("<I", rkey[:4])[0]
        print("[+] Priv key size: %d" % privateKeySize)
        # Next 256 bytes are RSA-encrypted salsa key
        salsakey = rkey[4:(4+256)]

        salsakey = wincrypt.CryptDecrypt(priv, salsakey)[:32]
        print("[+] Salsa key: %s" % salsakey.hex())
        # Next 256 bytes are RSA-encrypted
        salsanonce = rkey[(4+256):(4+2*256)]

        salsanonce = wincrypt.CryptDecrypt(priv, salsanonce)[:8]
        print("[+] Salsa nonce: %s" % salsanonce.hex())

        print("[+] Decrypting RSA private user key...")
        encrRsaPriv = rkey[(4+2*256):]

        assert(len(encrRsaPriv) == privateKeySize)

        rsaPriv = Salsa20.new(key=salsakey, nonce=salsanonce).decrypt(encrRsaPriv)
        PK = wincrypt.CryptImportKey(rsaPriv)
        if not PK.valid:
            raise ValueError("ERROR: invalid RSA private key after decryption. Has this ransom been generated by Gandcrab V4-V5.4?")

        print("[+] RSA private key details:")
        print("[+] p  = %s" % hex(PK.p))
        print("[+] q  = %s" % hex(PK.q))
        print("[+] d  = %s" % hex(PK.d))
        print("[+] dp = %s" % hex(PK.dP))
        print("[+] dq = %s" % hex(PK.dQ))
        print("[+] iq = %s" % hex(PK.iQ))
        print("[+] N  = %s" % hex(PK.N))

        self.priv_user_rsa_key = rsaPriv
    
    def file_iterator(self,f, block_size, size):
        f.seek(0, 0)
        pos = 0
        while pos < size:
            rem = size-pos
            rs = min(rem, block_size)
            yield f.read(rs)
            pos += rs

    def decr_file(self,fencrname):
        privUserRsaFile = self.out_path
        
        privUserRsa = wincrypt.CryptImportKey(self.priv_user_rsa_key)
        assert(privUserRsa)

        padding_end = 28
        pos_nonce = padding_end+256
        pos_key = padding_end+256*2

        fencr = open(fencrname, "rb")
        fencr.seek(-padding_end, 2)
        pad = fencr.read(padding_end)

        # V4-V5.2 GandCarb have same sample byte, because their filemaker code is same.
        # https://twitter.com/demonslay335/status/1097902970182819840 
        if (pad[20:] != bytes.fromhex("1829899381820300")):
            raise EnvironmentError("Error: This file doesn't seem to be encrypted with Gandcrab V4-V5.2!")

        fdecrname = ".".join(fencrname.split(".")[:-1])
        fdecr = open(fdecrname, "wb")

        fencr.seek(-pos_nonce, 2)
        encrNonceData = fencr.read(256)
        nonceData = wincrypt.CryptDecrypt(privUserRsa, encrNonceData)
        nonce = nonceData[:8]

        keyData = fencr.seek(-pos_key, 2)
        encrKeyData = fencr.read(256)
        keyData = wincrypt.CryptDecrypt(privUserRsa, encrKeyData)
        key = keyData[:32]

        print("[+] Salsa20 key = %s" % key.hex())
        print("[+] Salsa20 nonce = %s" % nonce.hex())

        fencr.seek(0, 2)
        size = fencr.tell()

        print("[+] Decrypting file...")
        # Decrypt
        S = Salsa20.new(key=key, nonce=nonce)
        for encrData in self.file_iterator(fencr, 2048, size-pos_key):
            data = S.decrypt(encrData)
            fdecr.write(data)

        fdecr.close()
        fencr.close()

        print("[+] Decrypted file written to '%s'." % fdecrname)

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: %s ransom.txt" %sys.argv[0], file=sys.stderr)
        sys.exit(1)
    else:
        run = one_click_decrypt(sys.argv[1]).decrypt_all()