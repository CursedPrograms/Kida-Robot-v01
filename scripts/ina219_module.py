import smbus
import time

_REG_CONFIG = 0x00
_REG_SHUNTVOLTAGE = 0x01
_REG_BUSVOLTAGE = 0x02
_REG_POWER = 0x03
_REG_CURRENT = 0x04
_REG_CALIBRATION = 0x05

class BusVoltageRange:
    RANGE_16V = 0x00
    RANGE_32V = 0x01

class Gain:
    DIV_1_40MV = 0x00
    DIV_2_80MV = 0x01
    DIV_4_160MV = 0x02
    DIV_8_320MV = 0x03

class ADCResolution:
    ADCRES_9BIT_1S = 0x00
    ADCRES_10BIT_1S = 0x01
    ADCRES_11BIT_1S = 0x02
    ADCRES_12BIT_1S = 0x03
    ADCRES_12BIT_2S = 0x09
    ADCRES_12BIT_4S = 0x0A
    ADCRES_12BIT_8S = 0x0B
    ADCRES_12BIT_16S = 0x0C
    ADCRES_12BIT_32S = 0x0D
    ADCRES_12BIT_64S = 0x0E
    ADCRES_12BIT_128S = 0x0F

class Mode:
    POWERDOW = 0x00
    SVOLT_TRIGGERED = 0x01
    BVOLT_TRIGGERED = 0x02
    SANDBVOLT_TRIGGERED = 0x03
    ADCOFF = 0x04
    SVOLT_CONTINUOUS = 0x05
    BVOLT_CONTINUOUS = 0x06
    SANDBVOLT_CONTINUOUS = 0x07

class INA219:
    def __init__(self, i2c_bus=1, addr=0x40):
        self.bus = smbus.SMBus(i2c_bus)
        self.addr = addr
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_16V_5A()

    def read(self, address):
        data = self.bus.read_i2c_block_data(self.addr, address, 2)
        return (data[0] << 8) + data[1]

    def write(self, address, data):
        temp = [(data >> 8) & 0xFF, data & 0xFF]
        self.bus.write_i2c_block_data(self.addr, address, temp)

    def set_calibration_32V_2A(self):
        self._current_lsb = 0.1
        self._cal_value = 4096
        self._power_lsb = 0.002
        self.write(_REG_CALIBRATION, self._cal_value)
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = (self.bus_voltage_range << 13 |
                       self.gain << 11 |
                       self.bus_adc_resolution << 7 |
                       self.shunt_adc_resolution << 3 |
                       self.mode)
        self.write(_REG_CONFIG, self.config)

    def set_calibration_16V_5A(self):
        self._current_lsb = 0.1524
        self._cal_value = 26868
        self._power_lsb = 0.003048
        self.write(_REG_CALIBRATION, self._cal_value)
        self.bus_voltage_range = BusVoltageRange.RANGE_16V
        self.gain = Gain.DIV_2_80MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = (self.bus_voltage_range << 13 |
                       self.gain << 11 |
                       self.bus_adc_resolution << 7 |
                       self.shunt_adc_resolution << 3 |
                       self.mode)
        self.write(_REG_CONFIG, self.config)

    def getShuntVoltage_mV(self):
        self.write(_REG_CALIBRATION, self._cal_value)
        value = self.read(_REG_SHUNTVOLTAGE)
        if value > 32767:
            value -= 65535
        return value * 0.01

    def getBusVoltage_V(self):
        self.write(_REG_CALIBRATION, self._cal_value)
        self.read(_REG_BUSVOLTAGE)
        return (self.read(_REG_BUSVOLTAGE) >> 3) * 0.004

    def getCurrent_mA(self):
        value = self.read(_REG_CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb

    def getPower_W(self):
        self.write(_REG_CALIBRATION, self._cal_value)
        value = self.read(_REG_POWER)
        if value > 32767:
            value -= 65535
        return value * self._power_lsb

if __name__ == '__main__':
    ina219 = INA219(addr=0x41)
    while True:
        bus_voltage = ina219.getBusVoltage_V()
        shunt_voltage = ina219.getShuntVoltage_mV() / 1000
        current = ina219.getCurrent_mA()
        power = ina219.getPower_W()
        percent = (bus_voltage - 9) / 3.6 * 100
        percent = max(0, min(100, percent))

        print(f"Load Voltage:  {bus_voltage:6.3f} V")
        print(f"Current:       {current / 1000:9.6f} A")
        print(f"Power:         {power:6.3f} W")
        print(f"Percent:       {percent:3.1f}%\n")

        time.sleep(2)
