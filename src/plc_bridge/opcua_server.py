import asyncio
import logging
from asyncua import Server, ua

logging.basicConfig(level=logging.WARNING)


class VirtualIndustrialPLC:
    def __init__(self, endpoint: str = 'opc.tcp://127.0.0.1:4840/freeopcua/server/'):
        self.endpoint = endpoint
        self.server = Server()
        self.is_running = False

    async def init(self):
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name('Production_Industrial_PLC')

        uri = 'http://industrial.ai/sorting_line'
        idx = await self.server.register_namespace(uri)

        objects = self.server.nodes.objects
        self.line_obj = await objects.add_object(idx, 'ProductionLine_1')

        # Live State & Telemetry
        self.tag_line_running = await self.line_obj.add_variable(idx, 'Line_Running', True, ua.VariantType.Boolean)
        self.tag_belt_speed = await self.line_obj.add_variable(idx, 'Belt_Speed_MM_S', 1200.0, ua.VariantType.Float)
        self.tag_inspected = await self.line_obj.add_variable(idx, 'Total_Inspected_Count', 0, ua.VariantType.Int32)
        self.tag_rejected = await self.line_obj.add_variable(idx, 'Total_Rejected_Count', 0, ua.VariantType.Int32)

        # Actuation & Physical Hardware Tags
        self.tag_ejector = await self.line_obj.add_variable(idx, 'Ejector_Solenoid_Active', False, ua.VariantType.Boolean)

        # Industrial Handshake Tags
        self.tag_watchdog = await self.line_obj.add_variable(idx, 'Edge_Watchdog_Heartbeat', 0, ua.VariantType.Int32)
        self.tag_last_inspected_id = await self.line_obj.add_variable(idx, 'Last_Inspected_ID', '', ua.VariantType.String)
        self.tag_last_verdict = await self.line_obj.add_variable(idx, 'Last_Verdict_Pass', True, ua.VariantType.Boolean)
        self.tag_last_defect_code = await self.line_obj.add_variable(idx, 'Last_Defect_Code', 'NONE', ua.VariantType.String)

        # Make variables writable by client
        for tag in [
            self.tag_inspected,
            self.tag_rejected,
            self.tag_ejector,
            self.tag_watchdog,
            self.tag_last_inspected_id,
            self.tag_last_verdict,
            self.tag_last_defect_code,
            self.tag_line_running,
        ]:
            await tag.set_writable()

    async def start(self):
        await self.init()
        await self.server.start()
        self.is_running = True

    async def stop(self):
        if self.is_running:
            await self.server.stop()
            self.is_running = False

    async def fire_ejector_pulse(self, pulse_duration_s: float = 0.05):
        await self.tag_ejector.write_value(True)
        await asyncio.sleep(pulse_duration_s)
        await self.tag_ejector.write_value(False)
