#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as PKCS_sign

import binascii

class WorkspaceCypher(object):
    def __init__(self, priv_key=None, pub_key=None):
        """
        priv_key: texto ascii con la clave privada
        pub_key: texto ascii con la clave publica
        """
        if priv_key:
            self.set_priv_key(priv_key)
        if pub_key:
            self.set_pub_key(pub_key)

    def set_priv_key(self, priv_key):
        key = RSA.importKey(priv_key)
        self.priv = PKCS1_v1_5.new(key)
        self.priv_sign = PKCS_sign.new(key)

    def set_pub_key(self, pub_key):
        key = RSA.importKey(pub_key)
        self.pub = PKCS1_v1_5.new(key)
        self.pub_sign = PKCS_sign.new(key)

    def sign(self, text):
        signed = self.priv_sign.sign(text)
        return signed

    def verify(self, text, sign):
        verify = self.pub_sign.verify(text, sign)
        return verify

    def encrypt(self, text):
        """
        Retorna una string en base64 de los datos codificados
        """
        crypted = self.pub.encrypt(text)
        crypted_b64 = binascii.b2a_base64(crypted)
        return crypted_b64

    def decrypt(self, base64_text):
        """
        Retorna una string con el texto desencryptado
        """
        raw_cipher_data = binascii.a2b_base64(base64_text)
        try:
            decrypted = self.priv.decrypt(raw_cipher_data,'')
        except ValueError as ex:
            if ex.message == "Message too large":
                raise Exception("Parece que no estas usando la clave privada adecuada")
            raise ex
        return decrypted
