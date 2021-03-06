#!/usr/bin/env python3
from aws_cdk import core
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_dynamodb as ddb
import aws_cdk.aws_sqs as sqs
import aws_cdk.aws_lambda as lam
from aws_cdk.aws_lambda_event_sources import SqsEventSource
import aws_cdk.aws_s3_notifications as s3n

Des_bucket_default = 'your_des_bucket'
Des_prefix_default = 'my_prefix'
Des_region = 'cn-northwest-1'
StorageClass = 'STANDARD'
aws_access_key_id = 'xxxxxxxxx'
aws_secret_access_key = 'xxxxxxxxxxxxxxx'
# 请在CDK部署完成后，到Lambda的环境变量中修改 access key 配置，以便让Lambda又权限访问目标S3


class CdkResourceStack(core.Stack):

    def __init__(self, scope: core.Construct, _id: str, **kwargs) -> None:
        super().__init__(scope, _id, **kwargs)

        ddb_file_list = ddb.Table(self, "ddb",
                                  partition_key=ddb.Attribute(name="Key", type=ddb.AttributeType.STRING),
                                  billing_mode=ddb.BillingMode.PAY_PER_REQUEST)

        sqs_queue_DLQ = sqs.Queue(self, "sqs_DLQ",
                                  visibility_timeout=core.Duration.minutes(15),
                                  retention_period=core.Duration.days(14)
                                  )
        sqs_queue = sqs.Queue(self, "sqs_queue",
                              visibility_timeout=core.Duration.minutes(15),
                              retention_period=core.Duration.days(14),
                              dead_letter_queue=sqs.DeadLetterQueue(
                                  max_receive_count=100,
                                  queue=sqs_queue_DLQ
                              )
                              )
        handler = lam.Function(self, "lambdaFunction",
                               code=lam.Code.asset("./lambda"),
                               handler="lambda_function.lambda_handler",
                               runtime=lam.Runtime.PYTHON_3_8,
                               memory_size=1024,
                               timeout=core.Duration.minutes(15),
                               environment={
                                   'table_name': ddb_file_list.table_name,
                                   'queue_name': sqs_queue.queue_name,
                                   'Des_bucket_default': Des_bucket_default,
                                   'Des_prefix_default': Des_prefix_default,
                                   'Des_region': Des_region,
                                   'StorageClass': StorageClass,
                                   'aws_access_key_id': aws_access_key_id,
                                   'aws_secret_access_key': aws_secret_access_key
                               })
        ddb_file_list.grant_read_write_data(handler)
        handler.add_event_source(SqsEventSource(sqs_queue))

        s3bucket = s3.Bucket(self, "s3bucket")
        s3bucket.grant_read(handler)
        s3bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                        s3n.SqsDestination(sqs_queue))

        # You can import an existing bucket and grant access to lambda
        # exist_s3bucket = s3.Bucket.from_bucket_name(self, "import_bucket",
        #                                             bucket_name="you_bucket_name")
        # exist_s3bucket.grant_read(handler)

        # But You have to add sqs as imported bucket event notification manually, it doesn't support by CloudFormation
        # An work around is to add on_cloud_trail_event for the bucket, but will trigger could_trail first
        # 因为是导入的Bucket，需要手工建Bucket Event Trigger SQS，以及设置SQS允许该bucekt触发的Permission

        core.CfnOutput(self, "DynamoDB_Table", value=ddb_file_list.table_name)
        core.CfnOutput(self, "SQS_Job_Queue", value=sqs_queue.queue_name)
        core.CfnOutput(self, "SQS_Job_Queue_DLQ", value=sqs_queue_DLQ.queue_name)
        core.CfnOutput(self, "Worker_Lambda_Function", value=handler.function_name)
        core.CfnOutput(self, "New_S3_Bucket", value=s3bucket.bucket_name)


###############
app = core.App()
CdkResourceStack(app, "s3-migration-serverless")
# MyStack(app, "MyStack", env=core.Environment(region="REGION",account="ACCOUNT")
app.synth()
