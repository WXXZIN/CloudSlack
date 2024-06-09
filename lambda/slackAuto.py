import json
import os
import boto3
import random
from urllib import request
from urllib.error import HTTPError

def lambda_handler(event, context):
    channel_id = os.environ.get('CHANNEL_ID')
    bot_token = os.environ.get('BOT_TOKEN')
    
    if not bot_token or not channel_id:
        print("Error: Slack 토큰 또는 채널 ID가 설정되지 않았습니다.")
        return {
            'statusCode': 500,
            'body': json.dumps('Slack 토큰 또는 채널 ID가 설정되지 않았습니다.')
        }

    eat_list = get_random_data_from_s3()
    fields = []
        
    for data in eat_list:
        tmp_title = data['NAME']
        fields.append({
            "title": tmp_title,
            "value": "{}\n{}\n".format(data['MENU'], data['ADDR']),
            "short": False
        })

    title = f"안녕하세요! 오늘의 점심 메뉴 추천입니다!"
    message = {
        "attachments": [{
            "pretext": title,
            "color": "#0099A6",
            "fields": fields
        }]
    }
    
    post_message_to_slack(channel_id, message, bot_token)
        
    return {
        'statusCode': 200,
        'body': json.dumps('Command processed')
    }

def get_random_data_from_s3():
    s3 = boto3.client('s3')
    bucket_name = os.environ.get('BUCKET_NAME')
    object_key = 'data.json'

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        datas = json.loads(response['Body'].read())
        random.shuffle(datas)
        random_selection = random.sample(datas, 3)
        return random_selection
    except Exception as e:
        print("Error:", e)
        return []

def post_message_to_slack(channel_id, response_text, bot_token):
    url = 'https://slack.com/api/chat.postMessage'
    
    payload = {
        'channel': channel_id,
    }
    
    if isinstance(response_text, str):
        payload['text'] = response_text
    else:
        payload.update(response_text)
    
    headers = {
        'Authorization': f'Bearer {bot_token}',
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    req = request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    
    try:
        response = request.urlopen(req)
        response_data = response.read().decode('utf-8')
        response_json = json.loads(response_data)
        
        if not response_json.get('ok'):
            print("Error posting to Slack:", response_json.get('error'))
        else:
            print("Message posted to Slack successfully:", response_json)
    except HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")