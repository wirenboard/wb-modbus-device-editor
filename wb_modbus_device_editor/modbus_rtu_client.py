import logging
import traceback

from pymodbus.client.sync import ModbusSerialClient

from . import ui_manager


class ModbusRTUClient:
    client = None

    def __init__(self, mb_params):
        self.client = ModbusSerialClient(
            port=mb_params["port"],
            baudrate=mb_params["baudrate"],
            bytesize=mb_params["bytesize"],
            parity=mb_params["parity"],
            stopbits=mb_params["stopbits"],
        )

    def connect(self):
        return self.client.connect()

    def disconnect(self):
        self.client.close()

    def read_holding(self, slave_id, reg_address):
        try:
            data = self.client.read_holding_registers(address=reg_address, slave=slave_id)
            value = data.registers
        except Exception as e:
            msg = "%s" % e.args
            if "ModbusIOException" in msg:
                raise Exception("ModbusIOException")
            if "ExceptionResponse" in msg:
                raise Exception("ExceptionResponse")

        return value

    def write_holding(self, slave_id, reg_address, value):
        try:
            res = self.client.write_register(address=reg_address, slave=slave_id, value=int(value))

            if "IllegalValue" in "%s" % res:
                raise Exception("IllegalValue")
            if "Invalid Message" in "%s" % res:
                raise Exception("Invalid Message")
        except Exception as e:
            raise Exception(e)

        return "WriteRegisterResponse" in "%s" % res
