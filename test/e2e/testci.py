import requests
import time

ENDPOINT = 'http://localhost:5000'


def list_res():
    res = requests.get(ENDPOINT).json()
    print(res)
    res = requests.get(ENDPOINT + "/client").json()
    print(res)
    res = requests.get(ENDPOINT + "/server").json()
    print(res)


def resource_e2e():
    res = requests.get(ENDPOINT + "/resource/scale/2").json()
    instances = res['result']
    print(instances)
    print('Waiting for initializing new instances ...')
    time.sleep(30)
    for instance in instances:
        pub_ret = requests.get(
            ENDPOINT + f"/resource/{instance}").json()
    res = requests.get(ENDPOINT + '/resource').json()
    print(res)
    for instance in instances:
        ter_ret = requests.delete(
            ENDPOINT + f"/resource/{instance}").json()
    res = requests.get(ENDPOINT + '/resource').json()
    print(res)


def main():
    # list_res()
    resource_e2e()


main()
