import socket
import time
import subprocess
import select

# Config
DASHCAM_IP = '192.168.0.1'
DASHCAM_RTSP_URL = f'rtsp://{DASHCAM_IP}:554/livestream/1'
USER_AGENT = 'Lavf57.83.100'
PORT = 554
RECONNECT_DELAY = 5  # seconds
HEARTBEAT_INTERVAL = 3  # seconds
VIDEO_TIMEOUT = 10  # seconds to wait for video after PLAY
RELAY_COMMAND = [
    'ffmpeg', '-rtsp_transport', 'tcp', '-i', DASHCAM_RTSP_URL,
    '-c', 'copy', '-f', 'rtsp', 'rtsp://0.0.0.0:8554/stream'
]

def send_rtsp(sock, request):
    sock.sendall(request.encode())
    print(f"📤 Sent:\n{request}")

def recv_rtsp(sock):
    response = sock.recv(4096).decode()
    print(f"📥 Received:\n{response}")
    return response

def start_session():
    print(f"📡 Connecting to {DASHCAM_IP}:{PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((DASHCAM_IP, PORT))
    return sock

def build_rtsp_request(method, url, cseq, session=None, extra_headers=None):
    headers = [
        f"{method} {url} RTSP/1.0",
        f"CSeq: {cseq}",
        f"User-Agent: {USER_AGENT}",
    ]
    if session:
        headers.append(f"Session: {session}")
    if extra_headers:
        headers.extend(extra_headers)
    headers.append("")  # Blank line
    headers.append("")
    return "\r\n".join(headers)

def wait_for_video(sock):
    print(f"🎥 Waiting for video packets (timeout {VIDEO_TIMEOUT}s)...")
    sock.setblocking(0)
    ready = select.select([sock], [], [], VIDEO_TIMEOUT)
    if ready[0]:
        try:
            data = sock.recv(4096)
            if data:
                print("✅ Video detected.")
                return True
            else:
                print("❌ No data received after PLAY.")
                return False
        except Exception as e:
            print(f"❌ Error while waiting for video: {e}")
            return False
    else:
        print("❌ Timeout: No video received.")
        return False

def start_relay():
    print("🚀 Starting relay subprocess...")
    return subprocess.Popen(RELAY_COMMAND)

def main():
    relay_process = None
    while True:
        try:
            sock = start_session()
            cseq = 1

            # OPTIONS
            request = build_rtsp_request("OPTIONS", DASHCAM_RTSP_URL, cseq)
            send_rtsp(sock, request)
            recv_rtsp(sock)
            cseq += 1

            # DESCRIBE
            request = build_rtsp_request("DESCRIBE", DASHCAM_RTSP_URL, cseq, extra_headers=["Accept: application/sdp"])
            send_rtsp(sock, request)
            recv_rtsp(sock)
            cseq += 1

            # SETUP
            track_url = f"{DASHCAM_RTSP_URL}/trackID=0"
            request = build_rtsp_request(
                "SETUP",
                track_url,
                cseq,
                extra_headers=["Transport: RTP/AVP/TCP;unicast;interleaved=0-1"]
            )
            send_rtsp(sock, request)
            response = recv_rtsp(sock)
            session_id = None
            for line in response.splitlines():
                if line.lower().startswith('session:'):
                    session_id = line.split(":", 1)[1].strip().split(";")[0]
                    break
            if not session_id:
                raise Exception("No session ID received!")
            cseq += 1

            # PLAY
            request = build_rtsp_request(
                "PLAY",
                DASHCAM_RTSP_URL,
                cseq,
                session=session_id,
                extra_headers=["Range: npt=0.000-"]
            )
            send_rtsp(sock, request)
            recv_rtsp(sock)
            cseq += 1

            # Wait for actual video
            if not wait_for_video(sock):
                raise Exception("No video received. Reconnecting...")

            # If we got video, start relay
            if relay_process is None or relay_process.poll() is not None:
                relay_process = start_relay()

            print("✅ Stream active. Maintaining keepalive...")

            last_heartbeat = time.time()

            # Keepalive loop
            while True:
                time.sleep(1)
                if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
                    request = build_rtsp_request("OPTIONS", DASHCAM_RTSP_URL, cseq, session=session_id)
                    send_rtsp(sock, request)
                    recv_rtsp(sock)
                    cseq += 1
                    last_heartbeat = time.time()

        except Exception as e:
            print(f"⚠️ Error: {e}")
            if relay_process:
                print("🛑 Stopping relay subprocess...")
                relay_process.terminate()
                relay_process.wait()
                relay_process = None
            print(f"🔄 Reconnecting in {RECONNECT_DELAY} seconds...")
            time.sleep(RECONNECT_DELAY)
            continue

if __name__ == "__main__":
    main()
