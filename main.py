import serial
import psycopg2
import os

def connect_db():
    conn = psycopg2.connect("host='localhost' dbname='solar' user='solarslave' password='solarslave'")
    return conn

def disconnect_db(conn):
    conn.close()

def test_select(conn): 
    cur = conn.cursor()
    cur.execute('select * from POWER_USAGE_MIN')

    results = cur.fetchall() 

    rows = 0
    lastrow = ""
    for result in results:
        lastrow = result
        rows += 1
        #print(result)
    print("rows:"+str(rows))
    print(lastrow)

def insert(cur, values, plan):
    cur.execute("execute "+plan+" (%s,%s,%s,%s,%s,%s,%s,%s,%s)", values)


if __name__ == "__main__":
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=5)
    #ser.write("AT\r")
    conn = connect_db()

    cur = conn.cursor()
    query = """ prepare insertplan as 
                 INSERT INTO
                  "POWER_USAGE_SEC"
                 VALUES
                  (current_timestamp, $1, $2, $3, $4, $5, $6, $7, $8, $9) """
    cur.execute(query)
   
    query = """ prepare curveplan as 
                 INSERT INTO
                  "CURVES"
                 VALUES
                  (current_timestamp, $1, $2, $3, $4, $5, $6, $7, $8, $9) """
    cur.execute(query)

    startfound = False
    #try:
    while(startfound == False):
        response = ser.readline()
        print response
        if 'READY' in response:
            startfound = True
            break
    uploadcounter = 0

    curvemeasure = 999
    operation_mode = 'NORMAL'
    while(True):
        response = ser.readline()
        response = response.replace('\n','')
        if len(response) > 5:
 #           if curvemeasure == 1050:
#                ser.write('C\n')

            if response == 'CURVE_START':
                operation_mode = 'CURVE'
                print "Curve mode start"
            elif response == 'CURVE_STOP':
                operation_mode = 'NORMAL'
                print "Curve mode stop"
            elif response[:2] == 'S;' or response[:2] == 'C;': #Normal or curve update
                resp, volts, current, power, pwm, temp1, temp2, temp3 = response.replace('\n','').split(';')
                pwm1, pwm2, pwm3 = 0,0,0
                
                pwm = int(pwm)
                if pwm >= (0x3FF+0xFF):
                    pwm1 = int(pwm) - (0x3FF + 0xFF)
                    pwm2 = 0xFF
                    pwm3 = 0xFF

                elif pwm >= 0x3FF:
                    pwm1 = 0
                    pwm2 = int(pwm) - 0x3FF
                    pwm3 = 0xFF

                else:
                    pwm1 = 0 
                    pwm2 = 0
                    pwm3 = int(pwm)/4 #10bit => 8bit

                print "Volts:{V}V Cur:{A}mA PWR:{P}W PWM:{PWM} T1:{T1} T2:{T2} T3:{T3} Record {OPMODE}".format(
                    V = volts,
                    A = current,
                    P = power,
                    PWM = int(pwm),
                    T1 = temp1,
                    T2 = temp2,
                    T3 = temp3,
                    OPMODE = operation_mode
                )
                values = (volts, current, pwm1, pwm2, pwm3, temp1, temp2, temp3, power)
                if resp == 'C': #Insert all curve values by using curveplan
                    insert(cur, values, 'curveplan')
                else:
                    insert(cur, values, 'insertplan') #Normal values use inserplan
                
                conn.commit()
                if operation_mode == 'NORMAL':
                    if uploadcounter > 60:
                        commands = "'echo "+str(power)+" > /mnt/ramdisk/power.txt"
                        commands += " && echo "+str(volts)+" > /mnt/ramdisk/volts.txt"
                        commands += " && echo "+str(float(current)/1000)+" > /mnt/ramdisk/amps.txt"
                        commands += " && echo "+str(power)+"W "+str(volts)+"V "+str(round(float(current)/1000,2))+"A > /mnt/ramdisk/annotate.txt'"
                        os.system("ssh -i ~/.ssh/id_rsa_nopass pi@192.168.1.19 "+commands)
                        uploadcounter = 0
                    uploadcounter += 1
            else: #Debug print only
                try:
                    volts, current, power, pwm, temp1, temp2, temp3 = response.replace('\n','').split(';')
                    print "Volts:{V}V Cur:{A}mA PWR:{P}W PWM:{PWM} T1:{T1} T2:{T2} T3:{T3}".format(
                        V = volts,
                        A = current,
                        P = power,
                        PWM = int(pwm),
                        T1 = temp1,
                        T2 = temp2,
                        T3 = temp3
                    )
                except:
                    print "Some kind of error"
                    print response
            curvemeasure += 1
        else:
            print response
    #except:
    #    conn.commit()
    #    ser.close()
    #    disconnect_db(conn)

    ser.close()
    disconnect_db(conn)
                           



