from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def say_hello():
    print("Hello Airflow")



with DAG(
    dag_id="hello_airflow",
    start_date=datetime(2026, 2, 4),
    schedule=None,
    catchup=False,
    tags=["test", "hello"],


) as dag:
    
    hello_task = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello,
    )


hello_task