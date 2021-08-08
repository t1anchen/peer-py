import paramiko
import os
from io import StringIO

SSH_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0gFNsJhY8+Cb0x+j7o5eHMUX7ja8qBRvtRShx2nEnWYXKpSZ
KA8GCBKP461r9z8C/NoPG6ak4RuGL9rZ235VoWf96IhwGMdbsEboHyxMT6MkEX9I
NdPMofbM/xOhFiM/MGMdTbW6obCTL6HFdQGC1kuMnd0nglTauongCdN5IYZ4uUbc
Awnxv0uNHQBylQCfp2d0TwZi7npLXZcduqjlFH2ogV4o4hXvhGFb2N7t2TAlw3Pz
7X1EpENF1cYwSBzV/emKyasxXbSV9NbyOmR4ukVeTNcYMpCREQ7Pzs5hvDSQIu8N
qzlEJPVv/9+PaUQ7OS2GHXnV5WjblH3T6/XpqwIDAQABAoIBAFfQ3bjj7AaHPQHq
8DUYaXhkXp5pWzh520CAkSn/K42aHEPdAbKDncUQZgUSBtzMB6bOVJT+eWH8jX9D
Z+hmCs7E2qM7MozaCJhM/lHSx1Jh6Po8HGkN2Ts9JfngLnNAZ/MG70EIpjNo0BOR
9Sz5ZcnQq8tzqErSyuhIMVxKhxOiEnzMlokIFOUBPnm4f7iBduc1hcarGtaZi73I
Eq8cZn2mMv1PnTlx2h/8pURqETOGUhygEuXp+BPTq2L+sFm79rWx33LnL+4bjp0y
HHjAd4g7EfilDiRlSPtTFF3vhxI3rtES/Dg0/CmoQ35/LLk7/N0maM4E62e61Iks
lJxSHakCgYEA8/LPJIWFlcfcETSqlSELeSHIB9dJrOQJwqdmVcXzScI5VwwtTOzx
bZF8NqKzQCJtxs1A85VRmy7r1+yhUYW8OtnZAg4MczVKijR2AQG7Xoa/F/h2A+wv
n1nC5Rt6o1ZX8hMniIFnDuTHc192jv7+hKmePw+osP29dNiuDv82ercCgYEA3GE3
RuSha8Cs1WXrwJ26/yazgf0KG9+r1tIym44AFtBNrBoBErm2T8S92AhgSu7NdASE
jk4hPLCAso3ebt1Qnmnd/JYnwQ0KHNuaGuwlYvH9PpHRLXIXns5EMcKVIhnCkGXC
VT2J8JXwTe08knHemi4xLrTVb+2/odiB1hX25K0CgYEA7qEaF/O01OuIThxisTZ9
7qQo8+KY41K+aXcvF8BnWENxq8Dxn0o4cKHcC+XjylzjXZDydFQgW9juQ23p78EO
e9MWAHiVnS0IGWFv/VQgYTsWOvCFIRktDIfVqh/TO2v+44HxLgrHMT6CDE3Zv8+Y
UVVKww0iSuArL921hl4IgMkCgYEAh5+ccRiK7tEojDupFmT7i8K5finHatf/3LiH
RIvjKicPZfaq6mc392dQnf6po/PKpLeTDDCw67SDv17noLq6voLQhn2yAXCQ5KmQ
8Tia2YWrIDKE1L7+IlE2Tpk9RjssLckyC1tP5Kuhs5NoT4ecQq5iviezoqph4Kxp
WuMxihECgYAVfh6eaPF2zaSQ2SB7I4uKrleOb+HhHLiMU8B2r/9EiWoHwDTH+i+n
zzsggJce8xOu6aVykBeH87fMY/Sg1kAPu3NHZVHd7TZmAdzE4JB7H2FOOlOpB1Ez
RbySb5kswlahIvQ0lnSYO32NBJ3+AYoMrZHCOujXxQZCuzGTLnG89g==
-----END RSA PRIVATE KEY-----
"""


def get_conn(ip_addr, user="ubuntu"):
    key = paramiko.RSAKey.from_private_key(StringIO(SSH_KEY))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip_addr, username=user, pkey=key)
    return client


def disconn(ssh_client: paramiko.SSHClient):
    ssh_client.close()
