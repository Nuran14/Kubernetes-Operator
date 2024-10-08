# Kubernetes Operator
*This operator performs the following functions:* 

**Deployment Management:** Creates, updates, and deletes a deployment for the Flask application.

**Service Management:** Creates, updates, and deletes a Kubernetes service linked to the deployment.

**ConfigMap Management:** Creates and updates a ConfigMap containing the configuration for the Flask application.

**PVC (Persistent Volume Claim) Management:** Creates and manages Persistent Volume Claims.

**Monitoring CRD Events:** Automatically responds when a Custom Resource of type FlaskApp is created, updated, or deleted.

### Requirements
*To use this operator, the following requirements must be met:*
1. Kubernetes cluster (Minikube)
2. Python 3.6+
3. KOPF (Kubernetes Operator Framework) library

## Kubernetes Operator Installation
This guide explains how to set up a Kubernetes Operator using the Kubernetes Operator Framework (KOPF) to manage Custom Resource Definitions (CRD). The operator automatically creates and manages deployments and services based on the resources defined in the CRD. It also ensures that related Kubernetes resources are deleted when the Custom Resource (CR) is removed.
#### 1. Apply the CRD:
To add the CRD to the Kubernetes API, you need to apply the CRD manifest using the kubectl apply command:

``` kubectl apply -f <crd-name> ``` 
#### 2. Apply the Service Account and Operator Deployment:
To allow the operator to function correctly in the Kubernetes environment, you need to define a Service Account to grant the necessary permissions. Then, apply the deployment manifest to run the operator:

```kubectl apply -f <service-account-name> ```

```kubectl apply -f <operator-deployment-name> ```
#### 3. Verify the Operator Pod:
To ensure that the operator is running correctly, you can check the status of the deployment and pods with the following commands:

```kubectl get deployments```

```kubectl get pods```

To check if the pod is running properly, you can view the logs:

```kubectl logs <pod-name>```
#### 4. Apply the Custom Resource (CR):
A deployment will be created based on the definitions in the CR. You can check the status of the deployment and related pods with the following commands:

```kubectl get deployments```

```kubectl get pods```
#### 6. Check the Service Creation:
The operator will also create a service. To verify if the service was created successfully:

```kubectl get svc```

You can access your application through this service.



