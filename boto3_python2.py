import boto3
import base64
import json
import sys


def main(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
        launch_template_name = ""
        KeyName = ""
        instanceRole = ""
        Access_key_ID = ""
        Secret_access_key = ""
        s3fs_mount = ""
    # Launch Template:
    ec2 = boto3.client('ec2', region_name="us-east-1")
    client = boto3.client('batch')

    def launch_template():

        user_data = "MIME-Version: 1.0\nContent-Type: multipart/mixed; boundary=""==MYBOUNDARY==""\n\n --==MYBOUNDARY" \
                    "==\nContent-Type: text/x-shellscript; charset=""us-ascii""\n\n#!/bin/bash\n#!/bin/bash -xe\nsudo " \
                    "amazon-linux-extras install epel -y\nsudo yum install s3fs-fuse -y\necho " \
                    "AKIAS32ILWBSGEL6GM6V:7/FN10SHvZPC5qkTZ21zIOkwV+hVxl8xFpb9ayLS > /tmp/passwd-s3fs\nchmod 600 " \
                    "/tmp/passwd-s3fs\nmkdir " \
                    "/test\nchmod 777 /test\nsudo s3fs harshal-redshift-training /test -o allow_other -o " \
                    "passwd_file=/tmp/passwd-s3fs -o " \
                    "umask=000""\n\n--==MYBOUNDARY==--"

        encoded_user_data = base64.b64encode(user_data.encode()).decode()

        response = ec2.create_launch_template(
            LaunchTemplateName='test_demo',
            VersionDescription='this is test',
            LaunchTemplateData={
                'KeyName': 'harshal_nextflow_ec2_test',
                'UserData': encoded_user_data
            }
        )

        print(response)

    def create_compute():

        response1 = client.create_compute_environment(
            computeEnvironmentName='new_environment',
            type='MANAGED',
            state='ENABLED',
            computeResources={
                'type': 'EC2',
                'allocationStrategy': 'BEST_FIT',
                'minvCpus': 0,
                'maxvCpus': 256,
                # 'imageId': 'string',
                'subnets': [
                    'subnet-fac7fca3',
                    'subnet-d49e41e9',
                    'subnet-0831746d',
                    'subnet-c3557ee8',
                    'subnet-935abbe5',
                    'subnet-e89604e4'
                ],
                'instanceRole': 'Test_hd',
                'securityGroupIds': [
                    'sg-97b165f1',
                ],
                'instanceTypes': [
                    'optimal',
                ]
            }
        )

        print(response1)

    def create_queue():

        response = client.create_job_queue(
            jobQueueName='new_import_queue',
            state='ENABLED',
            priority=1,
            computeEnvironmentOrder=[
                {
                    'order': 100,
                    'computeEnvironment': 'new_environment'
                },
            ],
        )

        print(response)

    def create_instance():

        instances = ec2.run_instances(
            ImageId="ami-0b0dcb5067f052a63",
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            KeyName="harshal_nextflow_ec2_test",
            IamInstanceProfile={'Name': 'Test_hd'},
            UserData="""#!/bin/bash sudo rpm --import https://yum.corretto.aws/corretto.key sudo curl -L -o 
        /etc/yum.repos.d/corretto.repo https://yum.corretto.aws/corretto.repo sudo yum install -y  
        java-11-amazon-corretto-devel aws s3 sync s3://harshal-redshift-training/nextflow/nextflow_batch/ 
        /home/ec2-user/ sudo chmod 777 /home/ec2-user/nextflow cd /home/ec2-user ./nextflow run 
        /home/ec2-user/RNASeq.nf -c nextflow.config_updated_new -bucket-dir s3://harshal-redshift-training/temp 
        --outdir=s3://harshal-redshift-training/batch """
        )

        print(instances["Instances"][0]["InstanceId"])

    def check_job():
        job_name = "my-batch-job"

        # Get the job details
        job = client.describe_jobs(jobs=[job_name])

        # Check if the job has failed
        if job['jobs'][0]['status'] == 'FAILED':
            print("The job has failed.")

        # Check if the job has succeeded
        elif job['jobs'][0]['status'] == 'SUCCEEDED':
            ec2.terminate_instances(InstanceIds=[instance_id])

        # Handle other job statuses
        else:
            print("The job is in progress.")

    launch_template()
    create_compute()
    create_queue()
    create_instance()
    check_job()


if __name__ == "__main__":
    main()
