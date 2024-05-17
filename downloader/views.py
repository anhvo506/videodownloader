from django.shortcuts import render, redirect
from django.http import HttpResponse
from pytube import YouTube
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from google.auth.transport.requests import Request
from decouple import config

# Cài đặt API của Google
CLIENT_SECRET_FILE = config('CLIENT_SECRET_FILE')
API_NAME = 'youtube'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
YOUTUBE_EMAIL = config('YOUTUBE_EMAIL')

# Trang thành công khi tải xuống video
def download_success(request):
    return render(request, 'download_success.html')

# Trang lỗi khi tải xuống video
def download_failure(request):
    return render(request, 'download_failure.html')

# Trang chính của ứng dụng
def home(request):
    if request.method == 'POST':
        if 'download' in request.POST:
            # Xử lý yêu cầu tải xuống video
            video_urls = request.POST.get('video_urls').split('\n')
            try:
                for video_url in video_urls:
                    youtube = YouTube(video_url.strip())
                    video = youtube.streams.first()
                    video.download('./videos')
                # Chuyển hướng người dùng đến trang download_success
                return redirect('download_success')
            except Exception as e:
                print(e)
                # Chuyển hướng người dùng đến trang download_failure
                return redirect('download_failure')

        elif 'download_reupload' in request.POST:
            # Xử lý yêu cầu tải xuống và tải lên lại video
            video_urls = request.POST.get('video_urls').split('\n')
            try:
                for video_url in video_urls:
                    youtube = YouTube(video_url.strip())
                    video = youtube.streams.first()
                    video.download('./videos')

                    title = video.title  # Lấy tên của video đã được download
                    description = request.POST.get('description')
                    privacy_status = request.POST.get('privacy_status')

                    # Tạo dịch vụ Google API
                    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

                    # Tạo yêu cầu tải lên video
                    request_body = {
                        'snippet': {
                            'title': title,
                            'description': description,
                            'tags': None
                        },
                        'status': {
                            'privacyStatus': privacy_status,
                        },
                        'notifySubscribers': True
                    }

                    media_file = MediaFileUpload('./videos/' + title + '.mp4')
                    response_upload = service.videos().insert(
                        part='snippet,status',
                        body=request_body,
                        media_body=media_file
                    ).execute()

                # Chuyển hướng người dùng đến trang download_success
                return redirect('download_success')
            except Exception as e:
                print(e)
                # Chuyển hướng người dùng đến trang download_failure
                return redirect('download_failure')

    return render(request, 'home.html')

# Hàm này được sử dụng để tạo và trả về một dịch vụ API Google đã xây dựng
# dựa trên thông tin xác thực và cấu hình được cung cấp.
def Create_Service(client_secret_file, api_name, api_version, *scopes):
    # Thiết lập các thông số API
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]

    # Khởi tạo thông tin xác thực là None
    cred = None

    # Tạo tệp pickle để lưu thông tin xác thực
    pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'

    # Kiểm tra xem tệp pickle chứa thông tin xác thực có tồn tại không
    if os.path.exists(pickle_file):
        # Nếu tồn tại, tải thông tin xác thực từ tệp pickle
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    # Nếu thông tin xác thực không hợp lệ hoặc không tồn tại
    if not cred or not cred.valid:
        # Nếu thông tin xác thực đã hết hạn và có refresh token, làm mới thông tin xác thực
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            # Nếu không, khởi tạo luồng OAuth2 để lấy thông tin xác thực mới
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        # Lưu thông tin xác thực mới vào tệp pickle
        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        # Xây dựng và trả về dịch vụ API Google với thông tin xác thực đã có
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        print(API_SERVICE_NAME, 'service created successfully')
        return service
    except Exception as e:
        # In thông báo lỗi nếu không thể kết nối
        print('Unable to connect.')
        print(e)
        return None
