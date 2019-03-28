EESchema Schematic File Version 4
LIBS:swap_pins_test-cache
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 4 4
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L MCU_Microchip_PIC18:PIC18F452-IP U301
U 1 1 5B293B60
P 3200 3800
AR Path="/5B293A86/5B293B3E/5B293B60" Ref="U301"  Part="1" 
AR Path="/5B293A86/5C9CB8DC/5B293B60" Ref="U2"  Part="1" 
F 0 "U2" H 3300 5150 50  0000 C CNN
F 1 "PIC18F452-IP" H 3550 5050 50  0000 C CNN
F 2 "Package_DIP:DIP-40_W15.24mm" H 3200 3800 50  0001 C CIN
F 3 "http://ww1.microchip.com/downloads/en/DeviceDoc/39564c.pdf" H 3200 3450 50  0001 C CNN
	1    3200 3800
	1    0    0    -1  
$EndComp
Wire Wire Line
	3100 5100 3100 5200
Wire Wire Line
	3100 5200 3200 5200
Wire Wire Line
	3200 5200 3200 5300
Wire Wire Line
	3200 5100 3200 5200
Connection ~ 3200 5200
$Comp
L power:GND #PWR0302
U 1 1 5B29480A
P 3200 5300
AR Path="/5B293A86/5B293B3E/5B29480A" Ref="#PWR0302"  Part="1" 
AR Path="/5B293A86/5C9CB8DC/5B29480A" Ref="#PWR03"  Part="1" 
F 0 "#PWR03" H 3200 5050 50  0001 C CNN
F 1 "GND" H 3205 5127 50  0000 C CNN
F 2 "" H 3200 5300 50  0001 C CNN
F 3 "" H 3200 5300 50  0001 C CNN
	1    3200 5300
	1    0    0    -1  
$EndComp
Wire Wire Line
	3200 2500 3200 2400
Wire Wire Line
	3200 2400 3100 2400
Wire Wire Line
	3100 2400 3100 2300
Wire Wire Line
	3100 2500 3100 2400
Connection ~ 3100 2400
$Comp
L power:+5V #PWR0301
U 1 1 5B294D9E
P 3100 2300
AR Path="/5B293A86/5B293B3E/5B294D9E" Ref="#PWR0301"  Part="1" 
AR Path="/5B293A86/5C9CB8DC/5B294D9E" Ref="#PWR02"  Part="1" 
F 0 "#PWR02" H 3100 2150 50  0001 C CNN
F 1 "+5V" H 3115 2473 50  0000 C CNN
F 2 "" H 3100 2300 50  0001 C CNN
F 3 "" H 3100 2300 50  0001 C CNN
	1    3100 2300
	1    0    0    -1  
$EndComp
Text HLabel 4200 2900 2    50   Input ~ 0
RC1
Text HLabel 4200 3000 2    50   Input ~ 0
RC2
Text HLabel 4200 3100 2    50   Input ~ 0
RC3
Text HLabel 4200 3200 2    50   Input ~ 0
RC4
$Comp
L Amplifier_Operational:LM324 U1
U 3 1 5B34BA87
P 4550 5550
AR Path="/5B293A86/5B293B3E/5B34BA87" Ref="U1"  Part="3" 
AR Path="/5B293A86/5C9CB8DC/5B34BA87" Ref="U3"  Part="3" 
F 0 "U3" H 4550 5750 50  0000 L CNN
F 1 "LM324" H 4550 5350 50  0000 L CNN
F 2 "" H 4500 5650 50  0001 C CNN
F 3 "http://www.ti.com/lit/ds/symlink/lm2902-n.pdf" H 4600 5750 50  0001 C CNN
	3    4550 5550
	1    0    0    -1  
$EndComp
Wire Wire Line
	4250 5650 4050 5650
Text GLabel 4050 5650 0    50   Input ~ 0
A4
Wire Wire Line
	4250 5450 4050 5450
Text GLabel 4050 5450 0    50   Input ~ 0
A5
$EndSCHEMATC
