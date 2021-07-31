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
    # Create instances and get ip
    res = requests.get(ENDPOINT + "/resource/scale/2").json()
    instances = res['result']
    print(instances)
    print('Waiting for initializing new instances ...')
    wait(30)
    for instance in instances:
        pub_ret = requests.get(
            ENDPOINT + f"/resource/{instance}/public_ip").json()

    # get active instance
    res = requests.get(ENDPOINT + '/resource').json()
    active_instances = [k for k in res['result'].keys(
    ) if res['result'][k]['state'] == 'running']
    print(res)

    # run command via ssh
    print('Waiting for provisioning ssh connections ...')
    wait(30)
    for instance in active_instances:
        res = requests.get(ENDPOINT + f"/resource/{instance}/cpu").json()
        print(res)

    # terminating
    for instance in active_instances:
        ter_ret = requests.delete(
            ENDPOINT + f"/resource/{instance}").json()
    res = requests.get(ENDPOINT + '/resource').json()
    print(res)


def wait(timeout: int):
    click = 0
    while click < timeout:
        localtime = time.localtime()
        print(f"remaining {(timeout - click):02d} secs", end='\r')
        click += 1
        time.sleep(1)
    print()


def main():
    # list_res()
    resource_e2e()
    # resource_e2e()


main()
