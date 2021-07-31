import boto3


def instance_create(n_ins: int, dryrun=False):
    n_ins = max(n_ins, 1)
    if dryrun:
        return ["i-03f84b51b151876f0", "i-0a30c0a5d76bb8962"]
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    result = ec2_client.run_instances(
        ImageId='ami-0747bdcabd34c712a',
        MinCount=n_ins,
        MaxCount=n_ins,
        InstanceType='t2.micro',
        KeyName='lab1-demo'
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


def instance_terminate(ins_id):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    response = ec2_client.terminate_instances(InstanceIds=[ins_id])
    return response['TerminatingInstances']
