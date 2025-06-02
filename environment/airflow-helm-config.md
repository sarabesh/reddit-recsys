Setting up to run Airflow Helm Chart in Minikube k8s setup.

#install minikube, Helm

ref : https://airflow.apache.org/docs/helm-chart/stable/index.html

#install airflow helm Chart
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow --namespace airflow --create-namespace

kubectl apply -f environment/secrets.yaml #create this file with secrets and install