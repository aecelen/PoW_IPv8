from asyncio import run
from binascii import unhexlify
from dataclasses import dataclass

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import DataClassPayload, type_from_format
from ipv8.peer import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8
from dotenv import load_dotenv
import os

load_dotenv()

COMMUNITY_ID = unhexlify("2c1cc6e35ff484f99ebdfb6108477783c0102881")
SERVER_PUBLIC_KEY = unhexlify("4c69624e61434c504b3a86b23934a28d669c390e2d1fc0b0870706c4591cc0cb178bc5a811da6d87d27ef319b2638ef60cc8d119724f4c53a1ebfad919c3ac4136c501ce5c09364e0ebb")

EMAIL = os.getenv("EMAIL")
GITHUB_URL = os.getenv("GITHUB_URL")

with open("nonce.txt", "r") as f:
    NONCE = int(f.read().strip())


INT64 = type_from_format("q")


@dataclass
class SubmissionPayload(DataClassPayload[1]):
    email: str
    github_url: str
    nonce: INT64


@dataclass
class ResponsePayload(DataClassPayload[2]):
    success: bool
    message: str


_ = SubmissionPayload("", "", 0)
_ = ResponsePayload(False, "")


class LabCommunity(Community):
    community_id = COMMUNITY_ID

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.add_message_handler(ResponsePayload, self.on_response)
        self.submitted = False

    def started(self) -> None:
        self.register_task("find_and_send", self.find_and_send, interval=2.0, delay=0)

    async def find_and_send(self) -> None:
        if self.submitted:
            return
        peers = self.get_peers()
        print(f"Known peers: {len(peers)}")
        for peer in peers:
            print(f"  Peer key: {peer.public_key.key_to_bin().hex()}")
            if peer.public_key.key_to_bin() == SERVER_PUBLIC_KEY:
                print("Found server, sending submission...")
                self.ez_send(peer, SubmissionPayload(EMAIL, GITHUB_URL, NONCE))
                self.submitted = True
                return
        print("Server not found yet, waiting...")

    @lazy_wrapper(ResponsePayload)
    def on_response(self, peer: Peer, payload: ResponsePayload) -> None:
        if peer.public_key.key_to_bin() != SERVER_PUBLIC_KEY:
            print("Ignoring response from unknown peer")
            return
        print(f"Response from server: success={payload.success}, message={payload.message}")


async def main() -> None:
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "curve25519", "../my_key.pem")
    builder.add_overlay("LabCommunity", "my peer",
                        [WalkerDefinition(Strategy.RandomWalk, 10, {"timeout": 3.0})],
                        default_bootstrap_defs, {}, [("started",)])

    await IPv8(builder.finalize(), extra_communities={"LabCommunity": LabCommunity}).start()
    await run_forever()


run(main())