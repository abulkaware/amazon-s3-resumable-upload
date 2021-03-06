#!/usr/bin/env python3

from aws_cdk import core

from cdk.cdk_vpc_stack import CdkVpcStack
from cdk.cdk_ec2_stack import CdkEc2Stack
from cdk.cdk_resource_stack import CdkResourceStack

############
# Define bucket before deploy
bucket_para = [{
    "src_bucket": "huangzb-s3-migration-test",
    "src_prefix": "first-1",
    "des_bucket": "hawkey999",
    "des_prefix": "s3-migration-test-cdk-deploy1",
    }, {
    "src_bucket": "huangzb-tokyo-video",
    "src_prefix": "small",
    "des_bucket": "hawkey999",
    "des_prefix": "s3-migration-test-cdk-deploy1",
    }]
# key_name = "id_rsa"  # Optional if use SSM-SessionManager

# CDK会在在ssm parameter store配置名为 "s3_migrate_credentials" 的 parameter，请去修改里面的参数：
# 这个是跟EC2不在一个Account体系下的另一个Account的access_key
# 例如EC2在Global，则这个是China Account access_key，反之EC2在中国，这就是Global Account
# EC2本Account的权限会从 IAM Role 获取。以下是这个参数的例子：
# {
#     "aws_access_key_id": "your_aws_access_key_id",
#     "aws_secret_access_key": "your_aws_secret_access_key",
#     "region": "cn-northwest-1"
# }

############

app = core.App()
vpc_stack = CdkVpcStack(app, "s3-migration-cluster-vpc")
vpc = vpc_stack.vpc

resource_stack = CdkResourceStack(app, "s3-migration-cluster-resource", bucket_para)

ec2_stack = CdkEc2Stack(app, "s3-migration-cluster-ec2", vpc,
                        # key_name,   # Optional if use SSM-SessionManager
                        resource_stack.ddb_file_list,
                        resource_stack.sqs_queue,
                        resource_stack.sqs_queue_DLQ,
                        resource_stack.ssm_bucket_para,
                        resource_stack.ssm_credential_para)

app.synth()
