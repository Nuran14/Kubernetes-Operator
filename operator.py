# kopf: Kubernetes Operator Framework 
# kopf kullanarak Kubernetes CRD (Custom Resource Definitions) kaynaklarına tepki veren bir Operator 
import kopf
# client --> Kubernetes API ile etkileşime geçmek için 
# config --> Kubernetes konfigürasyonunu yüklemek için
from kubernetes import client, config
import logging
import base64

# Kubernetes config yükleme
try:
    # cluster içi bir kübernetes konfigürasyonu yüklüyor
    config.load_incluster_config()
except:
    # dışarıdan küme yönetmek için kullanılıyor.
    config.load_kube_config()

def createDeployment(deployment_name, replicas, image, labels, service_account_name, configmap_name, pvc_name):
    # Kubernetes'in AppsV1Api arayüzünü kullanarak Deployment gibi uygulama nesneleri üzerinde işlem yapabilmeyi sağlar.
    apps_v1 = client.AppsV1Api()
    
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=deployment_name, labels=labels),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels=labels),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=labels),
                spec=client.V1PodSpec(
                    service_account_name=service_account_name,  # ServiceAccount burada belirtiliyor
                    containers=[
                        client.V1Container(
                            name=deployment_name,
                            image=image,
                            ports=[client.V1ContainerPort(container_port=5000)],  # için 5000 numaralı port kullanılıyor
                            env=[  # ConfigMap'ten çevresel değişkenleri ekliyoruz
                                client.V1EnvVar(
                                    name="FLASK_SECRET_KEY",
                                    value_from=client.V1EnvVarSource(
                                        config_map_key_ref=client.V1ConfigMapKeySelector(
                                            name=configmap_name,
                                            key="FLASK_SECRET_KEY"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="SQLALCHEMY_DATABASE_URI",
                                    value_from=client.V1EnvVarSource(
                                        config_map_key_ref=client.V1ConfigMapKeySelector(
                                            name=configmap_name,
                                            key="SQLALCHEMY_DATABASE_URI"
                                        )
                                    )
                                )
                            ],
                            volume_mounts=[  # PVC'yi mount etmek için volumeMounts ekliyoruz
                                client.V1VolumeMount(
                                    mount_path="/data",  # PVC'nin mount edileceği yol
                                    name="pvc-storage"  # volumes kısmındaki adı
                                ),
                                client.V1VolumeMount(
                                    mount_path="/configmap",
                                    name="configmap-name" #mount edilecek configmapin adı

                                )

                            ]
                        )
                    ],
                    volumes=[  # PVC'yi volume olarak ekliyoruz
                        client.V1Volume(
                            name="pvc-storage",  # Bu adı volumeMounts kısmında kullanıyoruz
                            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                claim_name=pvc_name  # Oluşturduğunuz PVC'yi burada kullanıyorsunuz
                            )
                        ),
                        client.V1Volume(
                            name="configmap-name",
                            config_map=client.V1ConfigMapVolumeSource(
                                name=configmap_name
                            )

                        )
                    ]
                )
            )
        )
    )

    try:
        # belirtilen namespace içinde bir deployment oluşturur
        apps_v1.create_namespaced_deployment(namespace='default', body=deployment)
        # deployment başarıyla oluşturulursa alınacak mesaj
        logging.info(f"Deployment {deployment_name} created successfully.")
    except client.exceptions.ApiException as e:
        logging.error(f"Error creating deployment: {e}")





# verilen service_name ve labels'a göre bir Kubernetes service oluşturur 
# deployment_uid --> servisin hangi Deployment'a ait olduğunu belirtmek için kullanılan benzersiz bir kimlik
def createService(service_name, labels, deployment_uid):
    
    #OWNER REFERENCE EKLEME
    owner_reference =client.V1OwnerReference(   #V1OwnerReference nesnesi oluşturuluyor
        api_version="apps/v1",
        kind="Deployment",
        name=service_name, #sahip deploymentın adı aynı zamanda service adı
        uid=deployment_uid,
        block_owner_deletion=True, # service silinmeden önce bağlı olduğu deploymentın silnmesini engeller 
        controller=True #nesnenin controlcü olduğunu belirtir --> Servisin sahibi edployment demek 
    )

    #kubernetes temel API arayüzünü kullanma
    core_v1 = client.CoreV1Api()
    # bir service nesnesi tanımladım
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=service_name, labels=labels, owner_references=[owner_reference]),
        spec=client.V1ServiceSpec(
            selector=labels,
            ports=[client.V1ServicePort(protocol='TCP', port=5000, target_port=5000)]  # Port 5000
        )
    )
    try:
        core_v1.create_namespaced_service(namespace='default', body=service)
        print(f"Service {service_name} created successfully.")
    except client.exceptions.ApiException as e:
        print(f"Error creating service: {e}")


def createConfigMap(configmap_name,config_data,namespace):
    v1 = client.CoreV1Api()

    configMap = client.V1ConfigMap(
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(name=configmap_name, namespace=namespace),
        data=config_data
    )

    try:
        v1.create_namespaced_config_map(namespace=namespace, body=configMap)
        print(f"ConfigMap '{configmap_name}' namespace '{namespace}' altında başarıyla oluşturuldu.")
    except client.exceptions.ApiException as e:
        print(f"ConfigMap oluşturulamadı: {e}")




    

def createPVC(pvc_name, storage_class_name, storage_size, access_modes, namespace):
    v1 = client.CoreV1Api()

    pvc = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(name=pvc_name),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=access_modes,  
            resources=client.V1ResourceRequirements(
                requests={"storage": storage_size}  
            ),
            storage_class_name=storage_class_name
        )
    )

    try:
        v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc)
        print(f"PersistentVolumeClaim {pvc_name} başarıyla oluşturuldu.")
    except client.exceptions.ApiException as e:
        print(f"PersistentVolumeClaim oluşturulurken hata oluştu: {e}")


#CUStOM RESOURCE OLUŞUNCA ÇALIŞAN FONKSİYON
# bu dekaratör crd.domain isimli CRD'nin v1 versiyonunda flaskapps türünde bir nesne oluşturulduğunda on_create fonksiyonunu çağırır
@kopf.on.create('crd.domain', 'v1', 'flaskapps')
#bu fonksiyon yeni bir custom resource oluşturulduğunda çalışır
def on_create(spec, meta, namespace, name, **kwargs):
    # CRD'deki deploymentName bilgisini alır. Eğer deploymentName belirtilmemişse, bunun yerine CRD'nin adını kullanır.
    deployment_name = spec.get('deploymentName', name)
    # replicas alanını alır; belirtilmemişse, varsayılan olarak 2 kullanır.
    replicas = spec.get('replicas', 2)
    #bunun belirlenmesi zorunlu 
    image = spec.get('image')
    #labels alanını alır; belirtilmemişse, varsayılan olarak {'app': 'admin-panel'} kullanır.
    #labels = spec.get('labels', {'app': 'admin-panel-' + deployment_name})
    labels = {'app': 'admin-panel-' + deployment_name}
     # serviceAccountName alanını alır; belirtilmemişse, varsayılan olarak 'default' kullanır.
    service_account_name = spec.get('serviceAccountName', 'default')

    configmap_name = spec.get('configMapName','default')

    config_data = spec.get('configData', {
        'FLASK_SECRET_KEY': "default",
        'SQLALCHEMY_DATABASE_URI': "sqlite:///admin.db",
        
    })

   
    pvc_name = spec.get('pvcName',name + '-pvc')
    storage_class_name = spec.get('storageClassName','standard')
    storage_size = spec.get('storageSize','1Gi')
    access_modes = spec.get('accessModes', ['ReadWriteOnce'])
    

    createPVC(pvc_name, storage_class_name, storage_size, access_modes, namespace)

    v1=client.CoreV1Api() #CoreV1Api sınıfı, Kubernetes'in temel nesneleri (ConfigMap, Pod, Service, vb.) ile işlem yapmayı sağlayan fonksiyonları içerir.
    try:
        v1.read_namespaced_config_map(configmap_name, namespace)    #belirli bir configmapin var olup olmadığını kontrol ediyoruz 
        print(f"configmap {configmap_name}zaten var")

    except client.exceptions.ApiException as e: #Configmap yoksa veya bir hata oluşursa ApiException yakalanır
        #ApiException, Kubernetes API'sine yapılan bir isteğin başarısız olduğunu gösteren bir hata sınıfıdır.
        if "Not Found" in str(e): 
            print(f"Configmap {configmap_name} not found!")
            createConfigMap(configmap_name,config_data,namespace) #create configmap çağrılarak yeni configmap oluşturulur

    
    # fonksiyonlar çağrılarak deployment ve service oluşturulur
    createDeployment(deployment_name, replicas, image, labels,service_account_name,configmap_name,pvc_name)

    apps_v1 =client.AppsV1Api()
    # read_namespaced_deployment fonksiyonu çağrılarak oluşturulan deployment nesnesi alınır
    deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
    #deployment'a ait UID alınır  (benzersiz kimlik)

    # UID --> OLUŞTURULACAK SERVİCE'İN DEPLOYMENT İLE BAĞLANTISINI KURMAK İÇİ KULLANILIR

    deployment_uid =deployment.metadata.uid
    
    createService(deployment_name, labels,deployment_uid)






#CUSTOM RESOURCE SİLİNDİĞİNDE ÇALIŞACAK OLAN FONKSİYON
# crd.domain isimli CRD'nin v1 versiyonunda tanımlı flaskapps türünde bir nesne silindiğinde, on_delete fonksiyonu çalıştırılacak.
@kopf.on.delete("crd.domain","v1","flaskapps")    # v1 --> CRD'nin versiyonu
def on_delete(spec, meta, namespace, name, **kwargs):

    #deployment_name: CRD'de tanımlı deploymentName özelliğini alır. Eğer bu özellik belirtilmemişse, CRD'nin adını kullanır.
    deployment_name = spec.get('deploymentName', name)
    # service veployment nesnelerini etiketlemek için
    labels = {'app': 'admin-panel-' + deployment_name} 

    # Kubernetes AppsV1Api arayüzünü kullanır. Deployment üzerinde işlem yapmamızı sağlar.
    apps_v1 = client.AppsV1Api()

    # Kubernetes CoreV1Api arayüzünü kullanır. Service üzerinde işlem yapmamızı sağlar.
    core_v1 = client.CoreV1Api()

    try:
        # Deployment silmek için
        apps_v1.delete_namespaced_deployment(name=deployment_name, namespace=namespace)
        print(f"Deployment {deployment_name} deleted successfully.")
    except client.exceptions.ApiException as e:
        print(f"Error deleting deployment: {e}")

    try:
        # Service silme işlemi
        core_v1.delete_namespaced_service(name=deployment_name, namespace=namespace)
        print(f"Service {deployment_name} deleted successfully.")
    except client.exceptions.ApiException as e:
        print(f"Error deleting service: {e}")


def updateDeployment(deployment_name, replicas, image, labels,service_account_name,configmap_name):
    
    # Kubernetes'in AppsV1Api arayüzünü kullanarak Deployment gibi uygulama nesneleri üzerinde işlem yapabilmeyi sağlar.
    apps_v1 = client.AppsV1Api()
    
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=deployment_name, labels=labels),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels=labels),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=labels),
                spec=client.V1PodSpec(
                    service_account_name=service_account_name,  # ServiceAccount burada belirtiliyor
                    containers=[
                        client.V1Container(
                            name=deployment_name,
                            image=image,
                            ports=[client.V1ContainerPort(container_port=5000)],  # Admin paneli için 5000 numaralı port kullanılıyor
                            env=[  # ConfigMap'ten çevresel değişkenleri ekliyoruz
                                client.V1EnvVar(
                                    name="FLASK_SECRET_KEY",
                                    value_from=client.V1EnvVarSource(
                                        config_map_key_ref=client.V1ConfigMapKeySelector(
                                            name=configmap_name,
                                            key="FLASK_SECRET_KEY"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="SQLALCHEMY_DATABASE_URI",
                                    value_from=client.V1EnvVarSource(
                                        config_map_key_ref=client.V1ConfigMapKeySelector(
                                            name=configmap_name,
                                            key="SQLALCHEMY_DATABASE_URI"
                                        )
                                    )
                                )
                            ]
                        )
                    ]
                )
            )
        )
    )
    try:
        # Mevcut Deployment'ı yeni tanımla değiştirir (update işlemi için)
        apps_v1.replace_namespaced_deployment(
            name=deployment_name,       # Güncellenmek istenen Deployment'ın adı
            namespace='default',         # Deployment'ın bulunduğu namespace
            body=deployment              # Yeni Deployment tanımı
        )
        print(f"Deployment '{deployment_name}' başarıyla güncellendi.")
    
    except client.exceptions.ApiException as e:
        print(f"Deployment güncellenirken hata oluştu: {e}")



def updateConfigMap(configmap_name, config_data, namespace):
    v1 = client.CoreV1Api()

    configMap = client.V1ConfigMap(
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(name=configmap_name, namespace=namespace),
        data=config_data
    )
        
    try:
        # Mevcut ConfigMap'i yeni değerlerle değiştirmek için 
        v1.replace_namespaced_config_map(name=configmap_name, namespace=namespace, body=configMap) 
        print(f"ConfigMap '{configmap_name}' başarıyla güncellendi.")
    except client.exceptions.ApiException as e:
        print(f"ConfigMap güncellenirken hata oluştu: {e}")




def update_pvc(pvc_name, storage_size, access_modes, namespace):
    core_v1 = client.CoreV1Api()

    pvc = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(name=pvc_name),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=access_modes,
            resources=client.V1ResourceRequirements(
                requests={"storage": storage_size}
            )
        )
    )

    try:
        core_v1.replace_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace, body=pvc)
        print(f" {pvc_name} güncellendi.")
    except client.exceptions.ApiException as e:
        print(f" hata oluştu: {e}")


 

# CRD ÜZERİNDE BİR DEĞİŞİKLİK YAPILDIĞINDA BU FONKSİYON TETİKLENİR
@kopf.on.update('crd.domain', 'v1', 'flaskapps')   
# mevcut olan bir custom resource güncellendiğinde çalışır
def on_update(spec, meta, namespace, name,**kwargs):
    #CRD içinde deploymentName adlı bir alan tanımlıysa, bu alanın değerini alır. Değilse CRD'nin adını (name) kullanır.
    deployment_name = spec.get('deploymentName', name)
    replicas = spec.get('replicas', 2)
    image = spec.get('image')
    labels = {'app': 'admin-panel-' + deployment_name}

    service_account_name = spec.get('serviceAccountName', 'default')  # service account ekleniyor
    configmap_name = spec.get('configMapName', 'default')

    print(f"ConfigMap adı: {configmap_name}")

    # CRD içinden configData bilgisi alınır
    config_data = spec.get('configData', {
        'FLASK_SECRET_KEY': "default",
        'SQLALCHEMY_DATABASE_URI': "sqlite:///admin.db",
    })

    
    
    updateDeployment(deployment_name,replicas,image,labels,service_account_name,configmap_name)
    updateConfigMap(configmap_name, config_data, namespace)





   

# operatörü başlatmak için kullanılır
if __name__ == "__main__":
    kopf.run()



