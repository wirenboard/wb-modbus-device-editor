import logging
import traceback

try:
    from pymodbus.client import ModbusSerialClient
except ImportError:
    from pymodbus.client.sync import ModbusSerialClient


class ModbusRTUClient:
    client = None

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
