import asyncio
import random
import os
from aiohttp import ClientSession, ClientResponseError
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the DID API key from environment variables
DID_API_KEY = os.getenv('DID_API_KEY')

# Define API endpoint
DID_API = {
    'url': 'https://api.d-id.com',
    'service': 'talks',
    'key': DID_API_KEY
}

# Define presenter inputs
presenter_input_by_service = {
    'talks': {
        'source_url': 'https://d-id-public-bucket.s3.amazonaws.com/or-roman.jpg'
    },
    'clips': {
        'presenter_id': 'rian-lZC6MmWfC1',
        'driver_id': 'mXra4jY38i'
    }
}

# Global variables
peer_connection = None
pc_data_channel = None
stream_id = None
session_id = None
session_client_answer = None
is_stream_ready = False
stream_warmup = True
last_bytes_received = 0
video_is_playing = False
stream_video_opacity = 0

async def fetch_with_retries(session, url, method='GET', json_data=None, retries=1):
    try:
        async with session.request(method, url, json=json_data, headers={
            'Authorization': f'Basic {DID_API["key"]}',
            'Content-Type': 'application/json'
        }) as response:
            response.raise_for_status()
            return await response.json()
    except (ClientResponseError, asyncio.TimeoutError) as e:
        if retries <= 3:
            delay = min(2 ** retries / 4 + random.random(), 4)  # Exponential backoff
            await asyncio.sleep(delay)
            return await fetch_with_retries(session, url, method, json_data, retries + 1)
        else:
            raise e

async def connect():
    global peer_connection, session_client_answer, stream_id, session_id, is_stream_ready

    if peer_connection:
        if peer_connection.connectionState == 'connected':
            return

    await stop_all_streams()
    await close_pc()

    async with ClientSession() as session:
        try:
            response = await fetch_with_retries(
                session,
                f"{DID_API['url']}/{DID_API['service']}/streams",
                'POST',
                {
                    **presenter_input_by_service[DID_API['service']],
                    'stream_warmup': stream_warmup
                }
            )

            data = response
            stream_id = data['id']
            session_id = data['session_id']
            offer = RTCSessionDescription(data['offer']['sdp'], data['offer']['type'])
            ice_servers = [RTCIceServer(ice.get('urls'), ice.get('username'), ice.get('credential')) for ice in data['ice_servers']]

            try:
                session_client_answer = await create_peer_connection(offer, ice_servers)
            except Exception as e:
                print('Error during streaming setup:', e)
                await stop_all_streams()
                await close_pc()
                return

            try:
                await fetch_with_retries(
                    session,
                    f"{DID_API['url']}/{DID_API['service']}/streams/{stream_id}/sdp",
                    'POST',
                    {
                        'answer': session_client_answer.sdp,
                        'session_id': session_id
                    }
                )
            except Exception as e:
                print('Error sending SDP answer to service:', e)

        except Exception as e:
            print('Error connecting to service:', e)

async def destroy():
    async with ClientSession() as session:
        await fetch_with_retries(
            session,
            f"{DID_API['url']}/{DID_API['service']}/streams/{stream_id}",
            'DELETE',
            {'session_id': session_id}
        )
    await stop_all_streams()
    await close_pc()

async def create_peer_connection(offer, ice_servers):
    global peer_connection, pc_data_channel
    peer_connection = RTCPeerConnection(RTCConfiguration(ice_servers))

    pc_data_channel = peer_connection.createDataChannel('JanusDataChannel')

    peer_connection.on('icegatheringstatechange', on_ice_gathering_state_change)
    peer_connection.on('icecandidate', on_ice_candidate)
    peer_connection.on('iceconnectionstatechange', on_ice_connection_state_change)
    peer_connection.on('connectionstatechange', on_connection_state_change)
    peer_connection.on('signalingstatechange', on_signaling_state_change)
    peer_connection.on('track', on_track)
    pc_data_channel.on('message', on_stream_event)
    print('Created peer connection OK')

    try:
        await peer_connection.setRemoteDescription(offer)
        print('Set remote SDP OK')
    except Exception as e:
        print('Failed to set remote SDP:', e)
        raise e

    try:
        session_client_answer = await peer_connection.createAnswer()
        print('Created local SDP OK')
        await peer_connection.setLocalDescription(session_client_answer)
        print('Set local SDP OK')
    except Exception as e:
        print('Error creating or setting local SDP:', e)
        raise e

    return session_client_answer

def on_ice_gathering_state_change():
    print(f"ICE gathering state changed: {peer_connection.iceGatheringState}")

async def on_ice_candidate(event):
    print('Received ICE candidate')
    if event.candidate:
        candidate = event.candidate.get('candidate')
        sdp_mid = event.candidate.get('sdpMid')
        sdp_mline_index = event.candidate.get('sdpMLineIndex')

        url = f"https://api.d-id.com/{DID_API['service']}/streams/{stream_id}/ice"
        body = {
            'candidate': candidate,
            'sdpMid': sdp_mid,
            'sdpMLineIndex': sdp_mline_index,
            'session_id': session_id,
        }

        async with ClientSession() as session:
            try:
                await fetch_with_retries(
                    session,
                    url,
                    'POST',
                    body
                )
            except Exception as e:
                print(f"Error sending ICE candidate: {e}")
    else:
        # Handle null ICE candidate for initial 2 sec idle stream
        print('Received null ICE candidate.')

def on_ice_connection_state_change():
    if peer_connection.iceConnectionState in ['failed', 'closed']:
        asyncio.create_task(stop_all_streams())
        asyncio.create_task(close_pc())

def on_connection_state_change():
    # Handle connection state change
    pass

def on_signaling_state_change():
    print(f"Signaling state changed: {peer_connection.signalingState}")

def on_track(event):
    # Handle track event
    pass

def on_stream_event(message):
    # Handle stream events
    pass

async def stop_all_streams():
    global stream_video_opacity
    if peer_connection:
        print('Stopping video streams')
        stream_video_opacity = 0

async def close_pc():
    global peer_connection
    if peer_connection:
        print('Stopping peer connection')
        await peer_connection.close()  # Tambahkan await di sini
        peer_connection = None

if __name__ == '__main__':
    asyncio.run(connect())
    # asyncio.run(destroy())
