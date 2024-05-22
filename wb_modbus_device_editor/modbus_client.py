import logging
import traceback

try:
    from pymodbus.client import ModbusSerialClient, ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusSerialClient, ModbusTcpClient

from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer


class ModbusClient:

    def __init__(self, mb_params):
        self.client = None

    def connect(self):
        return self.client.connect()

    def disconnect(self):
        self.client.close()

    def read_holding(self, slave_id, reg_address):
        data = self.client.read_holding_registers(address=reg_address, unit=slave_id, slave=slave_id)
        if isinstance(data, Exception):  # in case pymodbus experiences an internal error (wrong slave id)
            raise data
        if data.isError():  # in case device reports a problem (wrong reg addr)
            return None
        return data.registers[0]

    def write_holding(self, slave_id, reg_address, value):
        data = self.client.write_register(
            address=reg_address, unit=slave_id, slave=slave_id, value=int(value)
        )
        if isinstance(data, Exception):  # in case pymodbus experiences an internal error (wrong slave id)
            raise data
        if data.isError():  # in case device reports a problem (wrong reg addr)
            return None
        return data.value


class ModbusRTUClient(ModbusClient):
    def __init__(self, mb_params):
        self.client = ModbusSerialClient(
            method="rtu",
            port=mb_params["port"],
            baudrate=mb_params["baudrate"],
            bytesize=mb_params["bytesize"],
            parity=mb_params["parity"],
            stopbits=mb_params["stopbits"],
            strict=True,
        )


class ModbusTCPClient(ModbusClient):
    def __init__(self, mb_params):
        self.client = ModbusTcpClient(host=mb_params["ip"], port=mb_params["port"], framer=ModbusSocketFramer)


class ModbusRTUoverTCPClient(ModbusClient):
    def __init__(self, mb_params):
        self.client = ModbusTcpClient(host=mb_params["ip"], port=mb_params["port"], framer=ModbusRtuFramer)
