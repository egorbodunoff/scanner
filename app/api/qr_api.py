from logger_config import logger
import time
import serial


def read_from_port(port, baudrate=115200, timeout=1):
    ser = None
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        logger.info(f"Подключен к {port} на скорости {baudrate}")


        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').rstrip()
                print(data)
                return data
            else:
                time.sleep(0.1)

    except serial.SerialException as e:
        logger.error(f"Ошибка: {e}")

        return None
    except KeyboardInterrupt:
        logger.warning("Прерывание программы.")

        return None
    finally:
        if ser is not None and ser.is_open:
            ser.close()
            logger.info(f"Порт {port} закрыт.")



if __name__ == '__main__':
    read_from_port('/dev/ttyS4')

