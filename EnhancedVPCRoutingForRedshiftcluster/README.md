Description:
------------
Currently its not supported to enable/disable "Enhanced VPC Routing" for a Redshift Cluster via CloudFormation. However, the ModifyCluster[1] API itself supports this feature.

Enhanced VPC Routing:
---------------------
When you use Amazon Redshift Enhanced VPC Routing, Amazon Redshift forces all COPY and UNLOAD traffic between your cluster and your data repositories through your Amazon VPC. By using Enhanced VPC Routing, you can use standard VPC features, such as VPC security groups, network access control lists (ACLs), VPC endpoints, VPC endpoint policies, internet gateways, and Domain Name System (DNS) servers, as described in the Amazon VPC User Guide. You use these features to tightly manage the flow of data between your Amazon Redshift cluster and other resources. When you use Enhanced VPC Routing to route traffic through your VPC, you can also use VPC flow logs to monitor COPY and UNLOAD traffic.

Workaround:
-----------
Lambda-backed custom resource can be used in this regard however, code logic should be able to determine the cluster status before it proceeds with invoking ModifyCluster API.

The "enhanVPCRoutingRedshiftcluster.zip" contains a file named "function.py", that has all the code logic required to invoke DescribeClusters[2] API and ModifyCluster API, with an addition to modules including "cfnrespoonse" and "logging" to log events back to CloudWatch LogGroup.

Considerations:
---------------
1. ModifyCluster API will be failed if Redshift Cluster itself is in some other status than "available".
2. ModifyCluster API for enabling/disabling "Enhanced VPC Routing" will fail if its already enabled/disabled respectively.
3. Thus, Lambda function code itself should perform "DescribeClusters" API to determine the cluster status and then, depending on the cluster status should proceed with invoking ModifyCluster API.

Steps:
------
1. Please upload this enhanVPCRoutingRedshiftcluster.zip to an S3 bucket and make sure its accessible by CloudFormation.
2. Use the "template.yaml" file as a template for your stack and provide appropriate parameters values.
3. This stack will create following resources:
    - Redshift Cluster
        - The redshift cluster with as minimum as required specification to launch a Redshift cluster within the default VPC in the respective region in your account.
    - Custom Resource
        - The custom resource with required property specifications.
        - CloudFormation will pass the specified values any properties, to backing Lambda function and these values can be accessed inside the lambda function code using same name as they are specified under Custom Resource specification. A corresponding event is passed to Lambda function handler upon every invocation that includes all the request info including values for custom resource specific properties and thus, can be used to retrieve these values inside code.
        -  Similarly, for a custom resource, return values are defined by the custom resource provider, and can be retrieved by calling "Fn::GetAtt" on the provider-defined attributes.
    - Lambda Execution Role
        - This role is to give lambda service permissions to interact with Cloudwatch logs and above created Redshift Cluster.
        - Lambda function execution logs will be available as Cloudwatch log groups as per below hierarchy and any specified debug strings in the code will publish info to this log group. This will surely come in handy in case you face any problems when applying create/update/delete actions to custom resource as well as lambda function code debugging:
        ```bash
        |--' aws/lambda/Lambda_function_Name' - A log group in 'Log Groups' section on CloudWatch console.
              |-----' DATE/[$LATEST]CUSTOM_RESOURCE_PHYSICAL_ID' - A log stream with the same name as the physical id for Cloudformation stack's custom resource.
        ```
    - Lambda Function  
        - Python code hosted on S3 bucket that will handle enabling/disabling "EnhancedVpcRouting" for the Redshift cluster.
        - On a high level: code will make a "DescribeClusters" call first to get the cluster status[3] as well as the status of Enhanced VPC routing i-e whether its enabled or not and will then make "ModifyCluster" API accordingly.
        - I used Python Boto3[4] SDK to write this code.
        - My code has the logic to identify the current status of "Enhanced VPC routing" and will prohibit enabling "EnhancedVpcRouting" in case its already enabled for the Redshift cluster in question and vice versa.
        - Please see the code from function.py file attached.

References:
-----------
- [1] ModifyCluster - https://docs.aws.amazon.com/redshift/latest/APIReference/API_ModifyCluster.html
- [2] DescribeClusters - https://docs.aws.amazon.com/redshift/latest/APIReference/API_DescribeClusters.html
- [3] Amazon Redshift Clusters - Cluster Status - https://docs.aws.amazon.com/redshift/latest/mgmt/working-with-clusters.html#rs-mgmt-cluster-status
