import boto3, json, time
import cfnresponse     ###### AWS provided CFN response Module to send signal back to CloudFromation
import logging         ###### Module to log info to CloudWatch log stream
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
  response_data = {}
  cluster_state = ""
  enhanced_vpc_routing = ""
  response = {}
  try:
      client = boto3.client('redshift')
      ############# Processing "Create"/"Update" event #############
      if event["RequestType"] == "Create" or event["RequestType"] == "Update":
          logger.info("Processing CREATE or UPDATE event - " + json.dumps(event))
          ######### Checking if Cluster exists ###########
          cluster_exists = client.describe_clusters(ClusterIdentifier=event['ResourceProperties']['RedshiftClusterIdentifier'])
          clusters = cluster_exists['Clusters']
          for item in clusters:
            if isinstance(item, dict):
              if 'ClusterStatus' in item.keys():
                cluster_state = item['ClusterStatus']
                enhanced_vpc_routing = item['EnhancedVpcRouting']
          ######### Checking if cluster is in the right status to accept Modify request ##########
          if cluster_state == 'available':
              if event['ResourceProperties']['EnableEnhancedVPCRouting'] == 'True':
                  if enhanced_vpc_routing == 'True':
                      response_data['Data'] = "Enhanced VPC Routing is already enabled"
                      cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
                  else:
                      response = client.modify_cluster(
                          ClusterIdentifier=event['ResourceProperties']['RedshiftClusterIdentifier'],
                          EnhancedVpcRouting= True
                       )
                      if response['Cluster']['ClusterStatus'] == 'modifying':
                          logger.info(response['Cluster']['ClusterStatus'])
                          response_data['Data'] = response['Cluster']['ClusterStatus']
                          cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
                      else:
                          response_data['Data'] = response['Cluster']['ClusterStatus']
                          cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
              elif event['ResourceProperties']['EnableEnhancedVPCRouting'] == 'False':
                  if enhanced_vpc_routing == 'False':
                      response_data['Data'] = "Enhanced VPC Routing is already disabled"
                      cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
                  else:
                      response = client.modify_cluster(
                          ClusterIdentifier=event['ResourceProperties']['RedshiftClusterIdentifier'],
                          EnhancedVpcRouting= False
                       )
                      if response['Cluster']['ClusterStatus'] == 'modifying':
                        logger.info(response['Cluster']['ClusterStatus'])
                        response_data['Data'] = response['Cluster']['ClusterStatus']
                        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
                      else:
                          response_data['Data'] = response['Cluster']['ClusterStatus']
                          cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
              else:
                  response_data['Data'] = "Nothing to modify"
                  cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
          else:
              cfnresponse.send(event, context, cfnresponse.FAILED, {"Failure": "Redshift Cluster is not in the state to run a modify action"})
      ############# Processing "Delete" event #############
      elif event["RequestType"] == "Delete":
          logger.info("Processing DELETE event - " + json.dumps(event))
          cfnresponse.send(event, context, cfnresponse.SUCCESS,response_data)

      else:
          logger.info("Event Body - " + json.dumps(event))
          cfnresponse.send(event, context, cfnresponse.FAILED,response_data)
  except Exception as e:
      cfnresponse.send(event, context, cfnresponse.FAILED, {"Failure": "Some Exception Occured"})
