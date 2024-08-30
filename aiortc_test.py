import asyncio
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Function to adjust SDP to ensure compatibility with aiortc
def adjust_sdp(sdp):
    # Example adjustment: replace H264 with VP8, which is widely supported by aiortc
    sdp = sdp.replace('H264/90000', 'VP8/90000')
    # Additional adjustments can be made here if needed
    return sdp

async def connect_to_offer(sdp_offer):
    # Create RTCPeerConnection
    pc = RTCPeerConnection()

    # Adjust the SDP offer for codec compatibility
    adjusted_sdp = adjust_sdp(sdp_offer.sdp)

    # Create RTCSessionDescription with the adjusted SDP
    offer = RTCSessionDescription(sdp=adjusted_sdp, type='offer')

    # Set the remote description
    await pc.setRemoteDescription(offer)

    # Create an answer to the offer
    answer = await pc.createAnswer()

    # Set the local description with the answer
    await pc.setLocalDescription(answer)

    # Print the SDP answer
    print("SDP Answer:\n", pc.localDescription.sdp)

    # Close the peer connection
    await pc.close()

# Example SDP offer (replace with your actual SDP data)
sdp_offer = RTCSessionDescription(
    sdp='''v=0
o=- 1724983026637859 1 IN IP4 35.88.126.90
s=Mountpoint 4030112802777430
t=0 0
a=group:BUNDLE a v d
a=ice-options:trickle
a=fingerprint:sha-256 13:C7:A6:6E:23:C7:3F:85:F6:80:E3:74:7A:82:8A:8B:98:B8:5E:10:81:3E:48:80:0C:7F:3E:15:BB:D6:5D:BE
a=extmap-allow-mixed
a=msid-semantic: WMS *
m=audio 9 UDP/TLS/RTP/SAVPF 111
c=IN IP4 35.88.126.90
a=sendonly
a=mid:a
a=rtcp-mux
a=ice-ufrag:Lhtc
a=ice-pwd:FpNCVyLmtL0+AT7MhCvnx1
a=ice-options:trickle
a=setup:actpass
a=rtpmap:111 opus/48000/2
a=rtcp-fb:111 transport-cc
a=extmap:2 http://www.webrtc.org/experiments/rtp-hdrext/abs-send-time
a=extmap:4 urn:ietf:params:rtp-hdrext:sdes:mid
a=msid:janus janusa
a=ssrc:2282073439 cname:janus
a=candidate:1 1 udp 2015363327 172.18.0.3 34046 typ host
a=candidate:2 1 udp 1679819007 35.88.126.90 34046 typ srflx raddr 172.18.0.3 rport 34046
a=end-of-candidates
m=video 9 UDP/TLS/RTP/SAVPF 102 103
c=IN IP4 35.88.126.90
a=sendonly
a=mid:v
a=rtcp-mux
a=ice-ufrag:Lhtc
a=ice-pwd:FpNCVyLmtL0+AT7MhCvnx1
a=ice-options:trickle
a=setup:actpass
a=rtpmap:102 H264/90000
a=rtcp-fb:102 ccm fir
a=rtcp-fb:102 nack
a=rtcp-fb:102 nack pli
a=rtcp-fb:102 goog-remb
a=rtcp-fb:102 transport-cc
a=extmap:2 http://www.webrtc.org/experiments/rtp-hdrext/abs-send-time
a=extmap:4 urn:ietf:params:rtp-hdrext:sdes:mid
a=rtpmap:103 rtx/90000
a=fmtp:103 apt=102
a=ssrc-group:FID 941056429 2945195263
a=msid:janus janusv
a=ssrc:941056429 cname:janus
a=ssrc:2945195263 cname:janus
a=candidate:1 1 udp 2015363327 172.18.0.3 34046 typ host
a=candidate:2 1 udp 1679819007 35.88.126.90 34046 typ srflx raddr 172.18.0.3 rport 34046
a=end-of-candidates
m=application 9 UDP/DTLS/SCTP webrtc-datachannel
c=IN IP4 35.88.126.90
a=sendrecv
a=mid:d
a=sctp-port:5000
a=ice-ufrag:Lhtc
a=ice-pwd:FpNCVyLmtL0+AT7MhCvnx1
a=ice-options:trickle
a=setup:actpass
a=candidate:1 1 udp 2015363327 172.18.0.3 34046 typ host
a=candidate:2 1 udp 1679819007 35.88.126.90 34046 typ srflx raddr 172.18.0.3 rport 34046
a=end-of-candidates
''',
    type='offer'
)

# Run the connection function
asyncio.run(connect_to_offer(sdp_offer))
