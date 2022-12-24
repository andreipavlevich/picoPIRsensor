import machine  # библиотека для доступа к железу платы
import utime  # библиотека времени, адаптированная под микропитон

#моргаем диодом при включении
machine.Pin(25,machine.Pin.OUT).value(1) #включаем синий диод
utime.sleep(0.25) #пауза 0.25с
machine.Pin(25,machine.Pin.OUT).value(0) #выключаем синий диод
isMovement = 0
#настраиваем аппаратную часть
uart0 = machine.UART(0, baudrate=115200) #настраиваем порт 0 на передачу/прием данных по UART c esp8266

#получение ответа от esp8266
def Rx_ESP_Data(uart=uart0):
    recv=bytes() #класс массив байтов
    while uart.any()>0: #если получает байты, то
        recv+=uart.read(1) #пишет байты последовательностью в массив
    try: #тут какие-то ошибки декодинга, поэтому это обработчик ошибок
        res=recv.decode('utf-8') #декодируем байты в текст
    except UnicodeError: #если ошибка декодирования, то
        res="" #назначаем пустышку
    return res #возвращаем значение

#отправка команд типа CMD: AT... на esp8266
def Send_AT_Cmd(cmd, timeout, uart=uart0): #cmd - команда, uart=uart0 (порт по умолчанию 0), timeout - задержка на отклик (в милисек)
    uart.write(cmd) #отправка команды по uart
    utime.sleep(timeout) #задержка для стабильной работы
    print(Rx_ESP_Data())
    
Send_AT_Cmd('AT\r\n', 5)          #Test AT startup
Send_AT_Cmd('AT+GMR\r\n', 5)      #Check version information
Send_AT_Cmd('AT+CIPSERVER=0\r\n', 5)      #Check version information
Send_AT_Cmd('AT+RST\r\n', 5)      #Check version information
Send_AT_Cmd('AT+RESTORE\r\n', 5)  #Restore Factory Default Settings
Send_AT_Cmd('AT+CWMODE?\r\n', 5)  #Query the WiFi mode
Send_AT_Cmd('AT+CWMODE=1\r\n', 5) #Set the WiFi mode = Station mode
Send_AT_Cmd('AT+CWMODE?\r\n', 5)  #Query the WiFi mode again
Send_AT_Cmd('AT+CWLAP\r\n', 5) #List available APs
Send_AT_Cmd('AT+CWJAP="###","###"\r\n', 5) #Connect to AP using SSID & Password
Send_AT_Cmd('AT+CIFSR\r\n', 5)    #Obtain the Local IP Address
Send_AT_Cmd('AT+CIPMUX=0\r\n', 5)    #Provide multiple connection (up to 4)
machine.Pin(25,machine.Pin.OUT).value(1) #Когда сеть настроена и готова к работе включаем синий диод
#ядро отправки данных на вебсервер
while True:
    while machine.Pin(29, machine.Pin.IN).value(): #когда получаем сигнал с датчика движения запускаем процедуру отправки POST на сервер
        machine.Pin(25,machine.Pin.OUT).toggle() #вкл/выкл диод - индикатор, что условие сработало
        #send data
        Send_AT_Cmd('AT+CIPSTART="TCP","192.168.88.22",3030\r\n', 0.1) #подключаемся к серверу
        body="PICO" #тело запроса, определив которй будет произведена отработка сценария реакции на датчик движения
        body_len=str(len(body)) #длина тела ответа       
        h1="POST / HTTP/1.1\r\n" #запрос POST и его хедер
        h2="Host: 192.168.88.22:3030\r\n"
        h3="Content-Type: text/plain\r\n"
        h4="Content-Length: "+body_len+"\r\n" #здесь следует указать длину тела ответа
        h5="Connection: keep-alive\r\n\r\n"
        resp_len=str(len(h1)+len(h2)+len(h3)+len(h4)+len(h5)+len(body)) #определяем длину всего ответа   
        Send_AT_Cmd('AT+CIPSEND='+resp_len+'\r\n', 0.1) # type: ignore #перед тем как отправить ответ, нужно отправить команду на esp8266 с информацией о соединении и длине всего ответа    
        #с небольшими паузами сначала отправляем на esp8266 строки header
        Send_AT_Cmd(h1, 0.1)
        Send_AT_Cmd(h2, 0.1)
        Send_AT_Cmd(h3, 0.1)
        Send_AT_Cmd(h4, 0.1)
        Send_AT_Cmd(h5, 0.1)
        Send_AT_Cmd(body, 0.1) #отправляем на esp8266 тело ответа
        utime.sleep(3) #пауза для стабильности работы