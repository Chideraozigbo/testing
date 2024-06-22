from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
import pandas as pd
import json
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects


time_format = '%Y-%m-%d %H-%M-%S'

def hello_world():
    print('hello world')

def extract(ti):
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    parameters = {
        'slug': 'bitcoin',
        'convert': 'USD'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '9af647f6-55fa-4193-93db-6e69f1af611a',
    }
    session = Session()
    session.headers.update(headers)
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
        return None
    
    pd.set_option('display.max_columns', None)
    df = pd.json_normalize(data['data'])
    ti.xcom_push(key='extracted_data', value=df.to_json())

def transform(ti):
    df_json = ti.xcom_pull(key='extracted_data', task_ids='extract_data_task')
    if df_json is None:
        raise ValueError("No data available from the extract task")
    
    df = pd.read_json(df_json)

    # Remove '1.' prefix from column names
    df.columns = df.columns.str.replace('1.', '')
    
    # Drop unnecessary columns
    columns_to_drop = ['tags', 'infinite_supply', 'platform', 'cmc_rank', 'is_fiat',
                       'self_reported_circulating_supply', 'self_reported_market_cap',
                       'tvl_ratio', 'quote.USD.tvl']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
    
    columns_to_convert = ['quote.USD.volume_24h', 'quote.USD.market_cap', 'quote.USD.fully_diluted_market_cap']
    for col in columns_to_convert:
        df[col] = df[col].apply(lambda x: '{:.0f}'.format(x))
    
    # Convert date columns to datetime format
    columns_to_convert_datatypes = ['date_added', 'last_updated', 'quote.USD.last_updated']
    for col in columns_to_convert_datatypes:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    now = datetime.now()
    time = now.strftime(time_format)
    csv_path = f'/Users/user/airflow/dags/Crypto_data_as_at_{time}.csv'
    df.to_csv(csv_path, index=False)
    print(f"CSV saved to {csv_path}")

default_args = {
    'owner': 'Chidera',
    'email': ['chideraozigbo@gmail.com', 'femi.eddy@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}

crypto_dag = DAG(
    'crypto_dag',
    default_args=default_args,
    schedule_interval='*/5 * * * *',  # Runs every 5 minutes
    start_date=datetime(2024, 6, 21),
    catchup=False
)

hello_task = PythonOperator(
    task_id='hello_data_task',
    python_callable=hello_world,
    dag=crypto_dag
)

extract_task = PythonOperator(
    task_id='extract_data_task',
    python_callable=extract,
    provide_context=True,
    dag=crypto_dag
)

transform_task = PythonOperator(
    task_id='transform_data_task',
    python_callable=transform,
    provide_context=True,
    dag=crypto_dag
)

hello_task >> extract_task >> transform_task
