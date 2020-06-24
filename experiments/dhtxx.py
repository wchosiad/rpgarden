import time
import RPi

class DHTXXResult:
    'DHTXX sensor result returned by DHTXX.read() method'

    ERR_NO_ERROR = 0
    ERR_NO_DATA = 1
    ERR_MISSING_DATA = 2
    ERR_CRC = 3
    ERR_OUT_OF_RANGE = 4
    ERR_WRONG_SENSOR = 5
    ERR_RETRIES_EXCEEDED = 6

    error_messages = [None] * 7
    error_messages[ERR_NO_ERROR] = ""
    error_messages[ERR_NO_DATA] = "DHT returned no data. Are you connecected to the correct pin?"
    error_messages[ERR_MISSING_DATA] = "DHT returned the wrong amount of data"
    error_messages[ERR_CRC] = "DHT returned invalid CRC"
    error_messages[ERR_OUT_OF_RANGE] = "Temperature or humidity out of expected range"
    error_messages[ERR_WRONG_SENSOR] = "Invalid value. Are you really using a DHT11? It looks like it might be a DHT22"
    error_messages[ERR_RETRIES_EXCEEDED] = "Exceeded number of retries without getting a valid reading"

    error_code = ERR_NO_ERROR
    error_msg = error_messages[error_code]

    temperature = None
    humidity = None
    
    def __init__(self, error_code, temperature, humidity):
        self.error_code = error_code
        self.temperature = temperature
        self.humidity = humidity
        self.error_msg = self.error_messages[error_code]

    def is_valid(self):
        return self.error_code == DHTXXResult.ERR_NO_ERROR


class DHTXX:
    'DHTXX sensor reader class for Raspberry'
    DHT11 = 11
    DHT22 = 22
    FAHRENHEIT = 1
    CELCIUS = 2

    __pin = 0

    def __init__(self, pin, sensorType=DHT22, scale=FAHRENHEIT):
        self.__pin = pin
        self.__sensorType = sensorType
        self.__scale = scale

    def read(self):
        RPi.GPIO.setup(self.__pin, RPi.GPIO.OUT)

        # send initial high
        self.__send_and_sleep(RPi.GPIO.HIGH, 0.05)

        # pull down to low
        self.__send_and_sleep(RPi.GPIO.LOW, 0.02)

        # change to input using pull up
        RPi.GPIO.setup(self.__pin, RPi.GPIO.IN, RPi.GPIO.PUD_UP)

        # collect data into an array
        data = self.__collect_input()

        # parse lengths of all data pull up periods
        pull_up_lengths = self.__parse_data_pull_up_lengths(data)

        # if no data found, return error
        if len(pull_up_lengths) == 0:
            return DHTXXResult(DHTXXResult.ERR_NO_DATA, None, None)

        # if bit count mismatch, return error (4 byte data + 1 byte checksum)
        if len(pull_up_lengths) != 40:
            return DHTXXResult(DHTXXResult.ERR_MISSING_DATA, None, None)

        # calculate bits from lengths of the pull up periods
        bits = self.__calculate_bits(pull_up_lengths)

        # we have the bits, calculate bytes
        the_bytes = self.__bits_to_bytes(bits)

        # calculate checksum and check
        checksum = self.__calculate_checksum(the_bytes)
        if the_bytes[4] != checksum:
            return DHTXXResult(DHTXXResult.ERR_CRC, None, None)

        # ok, we have valid data

        # The meaning of the return sensor values
        #                    DHT11              DHT22
        #               ---------------    ---------------
        # the_bytes[0]:     humidity         humidity (MSB) 
        # the_bytes[1]:        0             humidity (LSB) 
        # the_bytes[2]:   temperature        temperature (MSB) (Note: if bit 8 is set, temperature is negative)
        # the_bytes[3]:        0             temperature (LSB) 
        # the_bytes[4]:     checksum         checksum (lower 8 bits of the sum of bytes 0-3)

        validationError = DHTXXResult.ERR_NO_ERROR
        if (self.__sensorType == self.DHT11):
            temperature = the_bytes[2]
            humidity = the_bytes[0]
            if (the_bytes[1] != 0) or (the_bytes[3] != 0):
                validationError = DHTXXResult.ERR_WRONG_SENSOR
            if (temperature <= 60) and (humidity >= 9) and (humidity <= 90):
                validationError = DHTXXResult.ERR_OUT_OF_RANGE
        else:
            temperature = the_bytes[2]
            negativeFlag = False
            if (temperature >= 128):
                negativeFlag = True
                temperature = temperature - 128
            temperature =  (temperature << 8) + the_bytes[3]
            if (negativeFlag):
                temperature = -1 * temperature

            temperature = float(temperature) / 10.0
            
            humidity = (the_bytes[0] << 8) + the_bytes[1]    
            humidity = float(humidity) / 10.0
            if (temperature < -50.0) or (temperature > 135.0) or (humidity > 110.0):
                validationError = DHTXXResult.ERR_OUT_OF_RANGE
        
        if validationError != DHTXXResult.ERR_NO_ERROR:
            return DHTXXResult(validationError, None, None)

        if (self.__scale == self.FAHRENHEIT):
            temperature = (temperature * 9 / 5) + 32
            
        return DHTXXResult(DHTXXResult.ERR_NO_ERROR, temperature, humidity)

    def read_and_retry(self, attempts=10):
        for i in range(attempts):
            result = self.read()
            if result.is_valid():
                return result
            else:
                time.sleep(2)
        return DHTXXResult(DHTXXResult.ERR_RETRIES_EXCEEDED, None, None)

    def __send_and_sleep(self, output, sleep):
        RPi.GPIO.output(self.__pin, output)
        time.sleep(sleep)

    def __collect_input(self):
        # collect the data while unchanged found
        unchanged_count = 0

        # this is used to determine where is the end of the data
        max_unchanged_count = 100

        last = -1
        data = []
        while True:
            current = RPi.GPIO.input(self.__pin)
            data.append(current)
            if last != current:
                unchanged_count = 0
                last = current
            else:
                unchanged_count += 1
                if unchanged_count > max_unchanged_count:
                    break

        return data

    def __parse_data_pull_up_lengths(self, data):
        STATE_INIT_PULL_DOWN = 1
        STATE_INIT_PULL_UP = 2
        STATE_DATA_FIRST_PULL_DOWN = 3
        STATE_DATA_PULL_UP = 4
        STATE_DATA_PULL_DOWN = 5

        state = STATE_INIT_PULL_DOWN

        lengths = [] # will contain the lengths of data pull up periods
        current_length = 0 # will contain the length of the previous period

        for i in range(len(data)):

            current = data[i]
            current_length += 1

            if state == STATE_INIT_PULL_DOWN:
                if current == RPi.GPIO.LOW:
                    # ok, we got the initial pull down
                    state = STATE_INIT_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_INIT_PULL_UP:
                if current == RPi.GPIO.HIGH:
                    # ok, we got the initial pull up
                    state = STATE_DATA_FIRST_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_FIRST_PULL_DOWN:
                if current == RPi.GPIO.LOW:
                    # we have the initial pull down, the next will be the data pull up
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_UP:
                if current == RPi.GPIO.HIGH:
                    # data pulled up, the length of this pull up will determine whether it is 0 or 1
                    current_length = 0
                    state = STATE_DATA_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_DOWN:
                if current == RPi.GPIO.LOW:
                    # pulled down, we store the length of the previous pull up period
                    lengths.append(current_length)
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue

        return lengths

    def __calculate_bits(self, pull_up_lengths):
        # find shortest and longest period
        shortest_pull_up = 1000
        longest_pull_up = 0

        for i in range(0, len(pull_up_lengths)):
            length = pull_up_lengths[i]
            if length < shortest_pull_up:
                shortest_pull_up = length
            if length > longest_pull_up:
                longest_pull_up = length

        # use the halfway to determine whether the period it is long or short
        halfway = shortest_pull_up + (longest_pull_up - shortest_pull_up) / 2
        bits = []

        for i in range(0, len(pull_up_lengths)):
            bit = False
            if pull_up_lengths[i] > halfway:
                bit = True
            bits.append(bit)

        return bits

    def __bits_to_bytes(self, bits):
        the_bytes = []
        byte = 0

        for i in range(0, len(bits)):
            byte = byte << 1
            if (bits[i]):
                byte = byte | 1
            else:
                byte = byte | 0
            if ((i + 1) % 8 == 0):
                the_bytes.append(byte)
                byte = 0

        return the_bytes

    def __calculate_checksum(self, the_bytes):
        return the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3] & 255


# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.