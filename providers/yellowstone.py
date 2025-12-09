import asyncio
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, Tuple
import base58
import grpc
from grpc.aio._channel import Channel
#from grpc_health.v1 import health_pb2, health_pb2_grpc
import time
from proto import geyser_pb2, geyser_pb2_grpc
from proto.geyser_pb2 import CommitmentLevel
from .base import BaseProvider, ProviderContext
from utils import get_current_timestamp, write_log_entry, TransactionData

class GeyserClient(BaseProvider):
    def create_channel(self, grpc_options=None):
        self.channel = None
        if self.x_token == "":
            self.channel = grpc.aio.insecure_channel(
                self.endpoint.replace("http://", "").replace("https://", ""),
                options=grpc_options
            )
        else:
            auth_creds = grpc.metadata_call_credentials(
                lambda context, callback: callback((("x-token", self.x_token),), None)
            )
            ssl_creds = grpc.ssl_channel_credentials()
            combined_creds = grpc.composite_channel_credentials(ssl_creds, auth_creds)
            self.channel = grpc.aio.secure_channel(
                self.endpoint.replace("http://", "").replace("https://", ""),
                credentials=combined_creds,
                options=grpc_options
            )

    async def run(self, ctx: ProviderContext) -> None:
        # Delayed import to show a helpful message if stubs are missing
        _endpoint = ctx.endpoint
        _cfg = ctx.config
        _comparator = ctx.comparator
        self.set_signs = set()
        self.endpoint = _endpoint.url
        self.x_token = _endpoint.x_token
        self.create_channel()
        self.geyser = geyser_pb2_grpc.GeyserStub(self.channel)
        if self.x_token != "":
            self.metadata = (('x-token', self.x_token),)
        else:
            self.metadata = ()
        self.queue_responses = asyncio.Queue()
        self._outgoing_requests = asyncio.Queue()

        await self.update_subscription(["pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"])
        asyncio.create_task(self.subscribe())
        await asyncio.sleep(2)
        async for message in self.responses():
            try:
                raw_sig = message.transaction.transaction.signature
                sig = None
                if len(raw_sig) == 64:
                    sig = raw_sig
                if len(raw_sig) == 65:
                    sig = raw_sig[1:]

                signature = base58.b58encode(sig).decode()
                if signature in self.set_signs:
                    continue
                self.set_signs.add(signature)
                ts = time.time()

                _comparator.add(
                        _endpoint.name,
                        TransactionData(timestamp=ts, signature=signature, start_time=ctx.start_time),
                    )
                
                if int(_comparator.get_all_seen_count()) % 100 == 0:
                    print(f"{ctx.endpoint.name} : {_comparator.get_all_seen_count()}")
                if _comparator.get_all_seen_count() >= _cfg.transactions:
                    ctx.shutdown_event.set()
                    break
            except:
                continue

    async def responses(self):
        while True:
            data = await self.queue_responses.get()
            yield data

    async def update_subscription(self, accounts: list[str]):
        req = geyser_pb2.SubscribeRequest()
        req.transactions['benchmark_transactions'].account_include.extend(accounts)
        req.transactions['benchmark_transactions'].vote = False
        req.transactions['benchmark_transactions'].failed = False
        req.commitment = geyser_pb2.CommitmentLevel.PROCESSED
        await self._outgoing_requests.put(req)

    async def subscribe(
        self,
    ) -> Tuple[
        asyncio.Queue[geyser_pb2.SubscribeRequest],
        AsyncGenerator[geyser_pb2.SubscribeUpdate, None],
    ]:
        async def request_iterator() -> AsyncGenerator[geyser_pb2.SubscribeRequest, None]:
            while True:
                req = await self._outgoing_requests.get()
                yield req
        while True:
            call = self.geyser.Subscribe(request_iterator(), compression=grpc.Compression.NoCompression)
            try:
                async for response in call:
                    await self.queue_responses.put(response)
            except Exception as e:
                print(f"-" * 100)
                print(f"grpc error : {e}")
                print(f"-" * 100)
                await asyncio.sleep(3)
                raise e

    async def ping(self, count: int) -> geyser_pb2.PongResponse:
        request = geyser_pb2.PingRequest(count=count)
        return await self.geyser.Ping(request)

    async def get_latest_blockhash(
        self, commitment: Optional[CommitmentLevel] = None
    ) -> geyser_pb2.GetLatestBlockhashResponse:
        request = geyser_pb2.GetLatestBlockhashRequest()
        if commitment is not None:
            request.commitment = commitment.value
        proto_response = await self.geyser.GetLatestBlockhash(request)
        return geyser_pb2.GetLatestBlockhashResponse(
            slot=proto_response.slot,
            blockhash=proto_response.blockhash,
            last_valid_block_height=proto_response.last_valid_block_height,
        )

    async def get_block_height(
        self, commitment: Optional[CommitmentLevel] = None
    ) -> geyser_pb2.GetBlockHeightResponse:
        request = geyser_pb2.GetBlockHeightRequest()
        if commitment is not None:
            request.commitment = commitment.value
        proto_response = await self.geyser.GetBlockHeight(request)
        return geyser_pb2.GetBlockHeightResponse(
            block_height=proto_response.block_height
        )

    async def get_slot(
        self, commitment: Optional[CommitmentLevel] = None
    ) -> geyser_pb2.GetSlotResponse:
        request = geyser_pb2.GetSlotRequest()
        if commitment is not None:
            request.commitment = commitment.value
        proto_response = await self.geyser.GetSlot(request)
        return geyser_pb2.GetSlotResponse(slot=proto_response.slot)

    async def is_blockhash_valid(
        self, blockhash: str, commitment: Optional[CommitmentLevel] = None
    ) -> geyser_pb2.IsBlockhashValidResponse:
        request = geyser_pb2.IsBlockhashValidRequest(blockhash=blockhash)
        if commitment is not None:
            request.commitment = commitment.value
        proto_response = await self.geyser.IsBlockhashValid(request)
        return geyser_pb2.IsBlockhashValidResponse(
            slot=proto_response.slot,
            valid=proto_response.valid,
        )

    async def get_version(self) -> geyser_pb2.GetVersionResponse:
        request = geyser_pb2.GetVersionRequest()
        proto_response = self.geyser.GetVersion(request)
        return geyser_pb2.GetVersionResponse(version=proto_response.version)