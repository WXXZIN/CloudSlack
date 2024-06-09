import json
import os
import boto3
import base64
import random
from urllib import request
from urllib.parse import unquote

def parse_slack_payload(data):
    decoded_data_raw = base64.b64decode(data).decode('utf-8').split('&')
    decoded_data_formatted = {}
    for item in decoded_data_raw:
        key, value = item.split('=')
        decoded_data_formatted[unquote(key)] = unquote(value)
    
    return decoded_data_formatted

def lambda_handler(event, context):
    # 환경 변수에서 Slack 토큰 읽기
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        print("Error: 토큰이 없습니다.")
        return {
            'statusCode': 500,
            'body': json.dumps('토큰이 없습니다.')
        }

    # print(f"Bot token: {bot_token}")
    
    # Slack 슬래시 커맨드 데이터 파싱
    body = parse_slack_payload(event['body'])
    print(f"body: {body}")
    
    command = body['command']
    print(f"command: {command}")
    
    option = body['text']
    print(f"option: {option}")
    
    option_count = len(option.split('+'))
    print(f"option_count: {option_count}")
    
    response_url = body['response_url']
    print(f"response_url: {response_url}")
    
    channel_id = body['channel_id']
    print(f"channel_id: {channel_id}")
    
    user_id = body['user_id']
    print(f"user_id: {user_id}")
    
    if not option:
        response_text = "구(군)을 입력해주세요!"
        post_message_to_slack(response_url, response_text, channel_id, bot_token)
    
    elif option_count > 1:
        response_text = "하나의 파라미터만 입력해주세요!"
        post_message_to_slack(response_url, response_text, channel_id, bot_token)
    
    else:
        # 슬래시 커맨드 처리
        if command == '/맛집추천':
            eat_list = get_random_data_from_s3(option)
            fields = []
            
            if not eat_list:
                response_text = "파라미터 입력 규칙을 준수해주세요!"
                post_message_to_slack(response_url, response_text, channel_id, bot_token)
                
            else:
                for data in eat_list:
                    tmp_title = data['NAME']
                    fields.append({
                        "title": tmp_title,
                        "value": "{}\n{}\n".format(data['MENU'], data['ADDR']),
                        "short": False
                    })
        
                title = f"안녕하세요, <@{user_id}>님! 오늘의 메뉴 추천입니다!"
                message = {
                    "attachments": [{
                        "pretext": title,
                        "color": "#0099A6",
                        "fields": fields
                    }]
                }
                
                post_message_to_slack(response_url, message, channel_id, bot_token)
        
    return {
        'statusCode': 200,
        'body': json.dumps('Command processed')
    }

def get_random_data_from_s3(option):
    # S3 클라이언트 생성
    s3 = boto3.client('s3')

    # S3 버킷 및 객체 키 설정
    bucket_name = os.environ.get('BUCKET_NAME')  # 실제 버킷 이름으로 변경
    object_key = 'data.json'

    try:
        # S3에서 data.json 객체 가져오기
        response = s3.get_object(Bucket=bucket_name, Key=object_key)

        # 객체 내용을 읽고 JSON으로 파싱
        datas = json.loads(response['Body'].read())

        # 옵션에 맞는 데이터 필터링
        filtered_data = [data for data in datas if data['GUGUN'] == option]

        # 필터링된 데이터를 섞고 무작위로 3개 선택
        random.shuffle(filtered_data)
        random_selection = random.sample(filtered_data, 3)

        return random_selection
    except Exception as e:
        print("Error:", e)
        return []

def post_message_to_slack(response_url, response_text, channel_id, bot_token):
    # response_text가 문자열이 아니라면, 이미 JSON 형식으로 가정하고 직접 인코딩하지 않음
    if isinstance(response_text, str):
        payload = json.dumps({
            "response_type": "in_channel",
            'channel': channel_id,
            'text': response_text
        }).encode('utf-8')
    else:
        # response_text가 JSON 객체라면, 직접 인코딩
        payload = json.dumps(response_text).encode('utf-8')
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    req = request.Request(response_url, data=payload, headers=headers)
    try:
        response = request.urlopen(req)
        response_data = response.read()
        print("Message posted to Slack successfully")
    except HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")