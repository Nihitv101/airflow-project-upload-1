
import json 
import pathlib 

import requests
import airflow
from airflow import DAG 
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator 
import requests.exceptions as requests_exceptions

dag = DAG(
    dag_id = "download_rocket_launch_dag",
    start_date=airflow.utils.dates.days_ago(14),
    schedule_interval = None,
)

download_launches = BashOperator(
    task_id="download_launches",
    bash_command="curl -o /output/launches.json -L 'https://ll.thespacedevs.com/2.0.0/launch/upcoming'",
    dag=dag,
)

#https://spacelaunchnow-prod-east.nyc3.digitaloceanspaces.com/media/images/atlas_v_n22_on__image_20240602164247.jpg
def _get_pictures():
    pathlib.Path("/output/images").mkdir(parents=True, exist_ok=True)

    with open("/output/launches.json") as f:
        launches = json.load(f)
        image_urls = [launch["image"] for launch in launches["results"]]
        for image_url in image_urls:
            try:
                response = requests.get(image_url)
                image_filename = image_url.split("/")[-1]
                target_file = f"/output/images/{image_filename}"
                with open(target_file, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {image_url} to {target_file}")
                      
            except requests_exceptions.MissingSchema:
                print(f"{image_url} appears to be an invalid URL.")

            except requests_exceptions.ConnectionError:
                print(f"Could not connect to {image_url}.")

get_pictures = PythonOperator(
    task_id="get_pictures",
    python_callable = _get_pictures,
    dag=dag
)

notify = BashOperator(
    task_id="notify",
    bash_command='echo "There are now $(ls /tmp/images/ | wc -l) images."',
    dag=dag
)

download_launches >> get_pictures >> notify    
                
