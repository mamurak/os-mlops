from os import environ
from socket import create_connection
from urllib.parse import urlparse

from OpenSSL.SSL import Connection, Context, SSLv23_METHOD
from cryptography.hazmat.primitives import serialization


def prepare_certs(inference_server_url):
    hostname = urlparse(inference_server_url).netloc
    environ["SSL_CERT_FILE"] = _save_srv_cert(hostname, port=443)


def _save_srv_cert(host, port=443):
    dst = (host, port)
    sock = create_connection(dst)
    context = Context(SSLv23_METHOD)
    connection = Connection(context, sock)
    connection.set_tlsext_host_name(host.encode('utf-8'))
    connection.set_connect_state()
    try:
        connection.do_handshake()
        certificate = connection.get_peer_certificate()
    except:
        certificate = connection.get_peer_certificate()
    pem_file = certificate.to_cryptography().public_bytes(
        serialization.Encoding.PEM
    )
    cert_filename = f"cert-{host}.cer"
    with open(cert_filename, "w") as fout:
        fout.write(pem_file.decode('utf8'))
    return cert_filename
