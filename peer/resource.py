import boto3


def instance_create(n_ins: int, dryrun=False):
    n_ins = max(n_ins, 1)
    if dryrun:
        return ["i-03f42e9709f04f213"]
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    result = ec2_client.run_instances(
        ImageId='ami-0747bdcabd34c712a',
        MinCount=n_ins,
        MaxCount=n_ins,
        InstanceType='t2.micro',
        KeyName='lab1-demo',
        SecurityGroupIds=['sg-05ac9b7d5cf8a6e26']
    )
    return [instance['InstanceId'] for instance in result["Instances"]]


def instance_public_ip(ins_id):
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    reservations = ec2_client.describe_instances(
        InstanceIds=[ins_id]).get("Reservations")
    ret = ""
    for reserv in reservations:
        for ins in reserv['Instances']:
            ret = ins['PublicIpAddress']
    return ret


def instance_desc():
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    reservations = ec2_client.describe_instances(Filters=[{
        'Name': 'instance-state-name',
        'Values': [
            'running'
        ]
    }]).get("Reservations")
    ret = {}
    for reserv in reservations:
        for ins in reserv['Instances']:
            ins_id = ins['InstanceId']
            print(f'[DEBUG] instance_desc:ins = {ins_id}')
            ret[ins_id] = {
                'public_ip': ins['PublicIpAddress']
            }
    return ret


def instance_terminate(ins_id):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    response = ec2_client.terminate_instances(InstanceIds=[ins_id])
    return response['TerminatingInstances']
